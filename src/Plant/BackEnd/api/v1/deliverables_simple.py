"""Deliverables APIs (Phase-1 simple implementation).

AGP1-PLANT-3.2:
- Generate draft deliverables from GoalInstances for a hired agent instance.
- Allow CP to list drafts and record approve/reject decisions.
- Allow approval-gated "execute" as a state transition (no external side effects yet).

Phase-1 scope: in-memory store intended to unblock CP review UX.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from agent_mold.enforcement import default_hook_bus
from agent_mold.hooks import HookEvent, HookStage
from agent_mold.skills.executor import execute_marketing_multichannel_v1
from agent_mold.skills.loader import load_playbook
from agent_mold.skills.playbook import ChannelName, SkillExecutionInput
from api.v1 import hired_agents_simple
from core.exceptions import PolicyEnforcementError


# Feature flag: DELIVERABLE_PERSISTENCE_MODE (default: "memory" for Phase 1 compatibility)
# Options: "memory" (in-memory dicts), "db" (PostgreSQL via repositories)
# Set DELIVERABLE_PERSISTENCE_MODE=db to use DB-backed deliverable persistence
DELIVERABLE_PERSISTENCE_MODE = os.getenv("DELIVERABLE_PERSISTENCE_MODE", "memory").lower()


DeliverableReviewStatus = Literal["pending_review", "approved", "rejected"]
DeliverableExecutionStatus = Literal["not_executed", "executed"]


class DeliverableRecord(BaseModel):
    deliverable_id: str = Field(..., min_length=1)
    hired_instance_id: str = Field(..., min_length=1)
    goal_instance_id: str = Field(..., min_length=1)
    goal_template_id: str = Field(..., min_length=1)

    title: str = Field(..., min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)

    review_status: DeliverableReviewStatus = "pending_review"
    review_notes: str | None = None
    approval_id: str | None = None

    execution_status: DeliverableExecutionStatus = "not_executed"
    executed_at: datetime | None = None

    created_at: datetime
    updated_at: datetime


class DeliverableResponse(BaseModel):
    deliverable_id: str
    hired_instance_id: str
    goal_instance_id: str
    goal_template_id: str

    title: str
    payload: dict[str, Any] = Field(default_factory=dict)

    review_status: DeliverableReviewStatus
    review_notes: str | None = None
    approval_id: str | None = None

    execution_status: DeliverableExecutionStatus
    executed_at: datetime | None = None

    created_at: datetime
    updated_at: datetime


class DeliverablesListResponse(BaseModel):
    hired_instance_id: str
    deliverables: list[DeliverableResponse] = Field(default_factory=list)


class ReviewDeliverableRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    decision: Literal["approved", "rejected"] = Field(...)
    notes: str | None = None
    approval_id: str | None = None


class ReviewDeliverableResponse(BaseModel):
    deliverable_id: str
    review_status: DeliverableReviewStatus
    approval_id: str | None = None
    updated_at: datetime


class ExecuteDeliverableRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    approval_id: str | None = None


class ExecuteDeliverableResponse(BaseModel):
    deliverable_id: str
    execution_status: DeliverableExecutionStatus
    executed_at: datetime | None = None
    updated_at: datetime


_deliverables_by_hired_instance: dict[str, dict[str, DeliverableRecord]] = {}
_deliverables_by_id: dict[str, DeliverableRecord] = {}
_deliverable_goal_index: dict[tuple[str, str, str], str] = {}


def _safe_str(val: Any) -> str:
    return str(val or "").strip()


def _goal_period_key(
    *,
    record: hired_agents_simple._HiredAgentRecord,
    goal: hired_agents_simple._GoalRecord,
    now: datetime,
) -> str:
    freq = _safe_str(goal.frequency).lower()
    if freq not in {"daily", "weekly", "monthly"}:
        return "on_demand"

    timezone_name = "UTC"
    if isinstance(record.config, dict):
        timezone_name = _safe_str(record.config.get("timezone")) or "UTC"

    try:
        tz = ZoneInfo(timezone_name)
    except Exception:
        tz = ZoneInfo("UTC")

    local = now.astimezone(tz)
    if freq == "daily":
        return f"daily:{local.date().isoformat()}"

    if freq == "weekly":
        iso_year, iso_week, _ = local.isocalendar()
        return f"weekly:{iso_year}-W{iso_week:02d}"

    return f"monthly:{local.year}-{local.month:02d}"


def _marketing_playbook_path() -> Path:
    # Co-locate with existing marketing_drafts playbook.
    return (
        Path(__file__).resolve().parents[2]
        / "agent_mold"
        / "playbooks"
        / "marketing"
        / "multichannel_post_v1.md"
    )


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for v in values:
        k = _safe_str(v)
        if not k or k in seen:
            continue
        seen.add(k)
        ordered.append(k)
    return ordered


def _trading_config_snapshot(config: dict[str, Any]) -> dict[str, Any]:
    allowed_raw = config.get("allowed_coins")
    allowed: list[str] = []
    if isinstance(allowed_raw, list):
        for c in allowed_raw:
            s = _safe_str(c)
            if s:
                allowed.append(s.upper())
    risk_limits = config.get("risk_limits") if isinstance(config.get("risk_limits"), dict) else {}
    max_units_raw = (risk_limits or {}).get("max_units_per_order")
    try:
        max_units = int(max_units_raw)
    except Exception:
        max_units = 0

    return {
        "exchange_provider": _safe_str(config.get("exchange_provider")),
        "exchange_credential_ref": _safe_str(config.get("exchange_credential_ref")),
        "allowed_coins": sorted(set(allowed)),
        "default_coin": _safe_str(config.get("default_coin")).upper(),
        "interval_seconds": int(config.get("interval_seconds") or 0),
        "risk_limits": {"max_units_per_order": max_units},
    }


def _generate_trading_deliverable(
    *,
    record: hired_agents_simple._HiredAgentRecord,
    goal: hired_agents_simple._GoalRecord,
) -> tuple[str, dict[str, Any]]:
    config = dict(record.config or {})
    snap = _trading_config_snapshot(config)

    tmpl = _safe_str(goal.goal_template_id)
    settings = dict(goal.settings or {})

    if tmpl == "trading.trade_intent_draft.v1":
        coin = _safe_str(settings.get("coin")).upper()
        side = _safe_str(settings.get("side")).lower()
        try:
            units = float(settings.get("units"))
        except Exception:
            units = 0.0

        allowed_coins = set(snap.get("allowed_coins") or [])
        max_units = int((snap.get("risk_limits") or {}).get("max_units_per_order") or 0)
        checks = {
            "coin_allowed": bool(coin and coin in allowed_coins),
            "side_valid": side in {"buy", "sell"},
            "units_positive": units > 0,
            "within_max_units": bool(units > 0 and max_units > 0 and units <= max_units),
            "max_units_per_order": max_units,
        }
        errors = [
            key
            for key in ["coin_allowed", "side_valid", "units_positive", "within_max_units"]
            if checks.get(key) is False
        ]

        title = f"Trade intent draft: {coin or 'COIN'} {side or 'side'} {units or 0:g}"
        payload = {
            "type": "trading_intent_plan_v1",
            "draft_only": True,
            "goal_template_id": tmpl,
            "goal_instance_id": goal.goal_instance_id,
            "exchange_provider": snap.get("exchange_provider"),
            "exchange_credential_ref": snap.get("exchange_credential_ref"),
            "coin": coin,
            "side": side,
            "units": units,
            "checks": checks,
            "validation_errors": errors,
            "intent_action": "place_order",
        }
        return title, payload

    if tmpl == "trading.close_position_reminder.v1":
        window = _safe_str(settings.get("window_local_time"))
        title = "Close-position proposal"
        payload = {
            "type": "trading_close_position_proposal_v1",
            "draft_only": True,
            "goal_template_id": tmpl,
            "goal_instance_id": goal.goal_instance_id,
            "exchange_provider": snap.get("exchange_provider"),
            "exchange_credential_ref": snap.get("exchange_credential_ref"),
            "window_local_time": window,
            "intent_action": "close_position",
        }
        return title, payload

    # trading.guardrail_report.v1 and any future templates.
    title = "Guardrail report"
    payload = {
        "type": "trading_guardrail_report_v1",
        "draft_only": True,
        "goal_template_id": tmpl,
        "goal_instance_id": goal.goal_instance_id,
        "snapshot": snap,
    }
    return title, payload


def _marketing_enabled_platforms(config: dict[str, Any]) -> list[str]:
    enabled_raw = config.get("platforms_enabled")
    enabled: list[str] = []
    if isinstance(enabled_raw, list):
        for p in enabled_raw:
            s = _safe_str(p).lower()
            if s:
                enabled.append(s)
    # legacy shape: platforms=[{platform:..}]
    if not enabled:
        platforms_raw = config.get("platforms")
        if isinstance(platforms_raw, list):
            for row in platforms_raw:
                if isinstance(row, dict):
                    s = _safe_str(row.get("platform")).lower()
                    if s:
                        enabled.append(s)
    return _dedupe_preserve_order(enabled)


def _generate_marketing_deliverable(
    *,
    record: hired_agents_simple._HiredAgentRecord,
    goal: hired_agents_simple._GoalRecord,
) -> tuple[str, dict[str, Any]]:
    config = dict(record.config or {})
    brand = _safe_str(config.get("brand_name"))
    location = _safe_str(config.get("location"))
    offerings_raw = config.get("offerings_services")
    offer = None
    if isinstance(offerings_raw, list) and offerings_raw:
        offer = _safe_str(offerings_raw[0]) or None

    tmpl = _safe_str(goal.goal_template_id)
    settings = dict(goal.settings or {})

    if tmpl == "marketing.weekly_multichannel_batch.v1":
        topics = settings.get("topics") if isinstance(settings.get("topics"), list) else []
        theme = _safe_str(topics[0] if topics else "Weekly multichannel batch")
        title = "Weekly multichannel posting batch"
    elif tmpl == "marketing.daily_micro_post.v1":
        theme = _safe_str(settings.get("topic") or "Daily patient-education micro-post")
        title = "Daily micro-post"
    else:
        theme = _safe_str(settings.get("theme") or "Monthly campaign pack")
        title = "Monthly campaign pack"

    # Deterministic draft generator (no LLM).
    playbook = load_playbook(_marketing_playbook_path())

    platform_map: dict[str, ChannelName] = {
        "youtube": ChannelName.YOUTUBE,
        "instagram": ChannelName.INSTAGRAM,
        "facebook": ChannelName.FACEBOOK,
        "linkedin": ChannelName.LINKEDIN,
        "whatsapp": ChannelName.WHATSAPP,
    }
    enabled = _marketing_enabled_platforms(config)
    channels: list[ChannelName] = []
    for p in enabled:
        if p in platform_map:
            channels.append(platform_map[p])

    result = execute_marketing_multichannel_v1(
        playbook,
        SkillExecutionInput(
            theme=theme or "Theme",
            brand_name=brand or "Brand",
            offer=offer,
            location=location,
            audience=None,
            tone=None,
            language=_safe_str(config.get("primary_language")) or None,
            channels=channels if channels else None,
        ),
    )

    variants = [
        {
            "platform": v.channel.value,
            "text": v.text,
            "hashtags": list(v.hashtags or []),
        }
        for v in result.output.variants
    ]
    variants.sort(key=lambda row: (row.get("platform") or ""))

    payload = {
        "type": "marketing_draft_batch_v1",
        "draft_only": True,
        "goal_template_id": tmpl,
        "goal_instance_id": goal.goal_instance_id,
        "brand_name": brand,
        "theme": theme,
        "variants": variants,
        "suggested_schedule_local": ["09:00", "13:00", "18:00"],
        "intent_action": "publish",
        "debug": result.debug,
    }
    return title, payload


def _generate_deliverable_for_goal(
    *,
    record: hired_agents_simple._HiredAgentRecord,
    goal: hired_agents_simple._GoalRecord,
    now: datetime,
) -> DeliverableRecord:
    if hired_agents_simple._is_trading_agent(record.agent_id):
        title, payload = _generate_trading_deliverable(record=record, goal=goal)
    elif hired_agents_simple._is_marketing_agent(record.agent_id):
        title, payload = _generate_marketing_deliverable(record=record, goal=goal)
    else:
        title = "Goal deliverable"
        payload = {
            "type": "generic_deliverable_v1",
            "draft_only": True,
            "goal_template_id": goal.goal_template_id,
            "goal_instance_id": goal.goal_instance_id,
            "intent_action": "publish",
        }

    deliverable_id = f"DEL-{uuid4()}"
    return DeliverableRecord(
        deliverable_id=deliverable_id,
        hired_instance_id=goal.hired_instance_id,
        goal_instance_id=goal.goal_instance_id,
        goal_template_id=goal.goal_template_id,
        title=title,
        payload=payload,
        review_status="pending_review",
        review_notes=None,
        approval_id=None,
        execution_status="not_executed",
        executed_at=None,
        created_at=now,
        updated_at=now,
    )


def _ensure_drafts_generated(record: hired_agents_simple._HiredAgentRecord, *, now: datetime) -> int:
    goals_map = hired_agents_simple._goals_by_hired_instance.get(record.hired_instance_id) or {}
    if not goals_map:
        return 0

    instance_map = _deliverables_by_hired_instance.setdefault(record.hired_instance_id, {})

    # Generate at most one draft per goal per period (daily/weekly/monthly) and
    # one draft total for on_demand goals.
    created = 0
    for goal in goals_map.values():
        period_key = _goal_period_key(record=record, goal=goal, now=now)
        key = (record.hired_instance_id, goal.goal_instance_id, period_key)
        existing_id = _deliverable_goal_index.get(key)
        if existing_id and existing_id in instance_map:
            continue

        d = _generate_deliverable_for_goal(record=record, goal=goal, now=now)
        instance_map[d.deliverable_id] = d
        _deliverables_by_id[d.deliverable_id] = d
        _deliverable_goal_index[key] = d.deliverable_id
        created += 1

    return created


hired_agents_router = APIRouter(prefix="/hired-agents", tags=["hired-agents"])
deliverables_router = APIRouter(prefix="/deliverables", tags=["deliverables"])
scheduler_router = APIRouter(prefix="/scheduler", tags=["scheduler"])


class RunDueGoalDraftsRequest(BaseModel):
    now: datetime | None = None
    hired_instance_id: str | None = None


class RunDueGoalDraftsResponse(BaseModel):
    generated: int
    deliverable_ids: list[str] = Field(default_factory=list)


@scheduler_router.post("/goals/run-due", response_model=RunDueGoalDraftsResponse)
async def run_due_goal_drafts(body: RunDueGoalDraftsRequest) -> RunDueGoalDraftsResponse:
    now = body.now or datetime.now(timezone.utc)
    target = _safe_str(body.hired_instance_id) or None

    created_ids: list[str] = []
    created_count = 0

    for record in list(hired_agents_simple._by_id.values()):
        if target and record.hired_instance_id != target:
            continue
        if not record.active:
            continue
        if not record.configured or not record.goals_completed:
            continue

        before_ids = set((_deliverables_by_hired_instance.get(record.hired_instance_id) or {}).keys())
        created_count += _ensure_drafts_generated(record, now=now)
        after_ids = set((_deliverables_by_hired_instance.get(record.hired_instance_id) or {}).keys())
        created_ids.extend(sorted(after_ids - before_ids))

    return RunDueGoalDraftsResponse(generated=created_count, deliverable_ids=created_ids)


@hired_agents_router.get("/{hired_instance_id}/deliverables", response_model=DeliverablesListResponse)
async def list_deliverables(
    hired_instance_id: str,
    customer_id: str | None = None,
    as_of: datetime | None = None,
) -> DeliverablesListResponse:
    record = hired_agents_simple._by_id.get(hired_instance_id)
    if not record:
        raise HTTPException(status_code=404, detail="Hired agent instance not found.")

    hired_agents_simple._assert_customer_owns_record(record, _safe_str(customer_id))
    await hired_agents_simple._assert_readable(record, db=None, as_of=as_of)

    effective_now = as_of or datetime.now(timezone.utc)
    _ensure_drafts_generated(record, now=effective_now)
    instance_map = _deliverables_by_hired_instance.get(hired_instance_id) or {}
    deliverables = [
        DeliverableResponse(**d.model_dump())
        for d in instance_map.values()
        if d.hired_instance_id == hired_instance_id
    ]
    deliverables.sort(key=lambda d: (d.created_at, d.deliverable_id))
    return DeliverablesListResponse(hired_instance_id=hired_instance_id, deliverables=deliverables)


@deliverables_router.post("/{deliverable_id}/review", response_model=ReviewDeliverableResponse)
async def review_deliverable(deliverable_id: str, body: ReviewDeliverableRequest) -> ReviewDeliverableResponse:
    d = _deliverables_by_id.get(_safe_str(deliverable_id))
    if not d:
        raise HTTPException(status_code=404, detail="Deliverable not found.")

    record = hired_agents_simple._by_id.get(d.hired_instance_id)
    if not record:
        raise HTTPException(status_code=404, detail="Hired agent instance not found.")

    hired_agents_simple._assert_customer_owns_record(record, body.customer_id)
    await hired_agents_simple._assert_readable(record, db=None)

    now = datetime.now(timezone.utc)
    decision = _safe_str(body.decision).lower()
    if decision not in {"approved", "rejected"}:
        raise HTTPException(status_code=400, detail="Unsupported decision.")

    approval_id = d.approval_id
    if decision == "approved":
        requested = _safe_str(body.approval_id)
        approval_id = requested or approval_id or f"APR-{uuid4()}"

    d.review_status = "approved" if decision == "approved" else "rejected"
    d.review_notes = _safe_str(body.notes) or None
    d.approval_id = approval_id if decision == "approved" else None
    d.updated_at = now

    # persist back into per-instance map
    instance_map = _deliverables_by_hired_instance.setdefault(d.hired_instance_id, {})
    instance_map[d.deliverable_id] = d
    _deliverables_by_id[d.deliverable_id] = d

    return ReviewDeliverableResponse(
        deliverable_id=d.deliverable_id,
        review_status=d.review_status,
        approval_id=d.approval_id,
        updated_at=d.updated_at,
    )


@deliverables_router.post("/{deliverable_id}/execute", response_model=ExecuteDeliverableResponse)
async def execute_deliverable(
    deliverable_id: str,
    body: ExecuteDeliverableRequest,
    request: Request,
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-ID"),
) -> ExecuteDeliverableResponse:
    d = _deliverables_by_id.get(_safe_str(deliverable_id))
    if not d:
        raise HTTPException(status_code=404, detail="Deliverable not found.")

    record = hired_agents_simple._by_id.get(d.hired_instance_id)
    if not record:
        raise HTTPException(status_code=404, detail="Hired agent instance not found.")

    hired_agents_simple._assert_customer_owns_record(record, body.customer_id)
    await hired_agents_simple._assert_readable(record, db=None)

    if d.review_status != "approved":
        raise HTTPException(status_code=409, detail="Deliverable is not approved.")

    correlation_id = x_correlation_id or str(id(request))
    provided = _safe_str(body.approval_id)

    action = "publish"
    if isinstance(d.payload, dict):
        action = _safe_str(d.payload.get("intent_action")) or action

    event_payload = dict(d.payload or {}) if isinstance(d.payload, dict) else {}
    if provided:
        event_payload["approval_id"] = provided

    decision = default_hook_bus().emit(
        HookEvent(
            stage=HookStage.PRE_TOOL_USE,
            correlation_id=correlation_id,
            agent_id=record.agent_id,
            customer_id=body.customer_id,
            purpose="deliverable_execute",
            action=action,
            payload=event_payload,
        )
    )

    if not decision.allowed:
        details: dict[str, Any] = dict(decision.details or {})
        details["deliverable_id"] = d.deliverable_id
        details["action"] = action
        if decision.decision_id:
            details["decision_id"] = decision.decision_id

        raise PolicyEnforcementError(
            "Policy denied deliverable execution",
            reason=decision.reason,
            details=details,
        )

    expected = _safe_str(d.approval_id)
    if not expected or provided != expected:
        raise PolicyEnforcementError(
            "Policy denied deliverable execution",
            reason="approval_invalid",
            details={
                "deliverable_id": d.deliverable_id,
                "action": action,
                "message": "Invalid approval_id for execution",
            },
        )

    now = datetime.now(timezone.utc)
    d.execution_status = "executed"
    d.executed_at = now
    d.updated_at = now

    instance_map = _deliverables_by_hired_instance.setdefault(d.hired_instance_id, {})
    instance_map[d.deliverable_id] = d
    _deliverables_by_id[d.deliverable_id] = d

    return ExecuteDeliverableResponse(
        deliverable_id=d.deliverable_id,
        execution_status=d.execution_status,
        executed_at=d.executed_at,
        updated_at=d.updated_at,
    )
