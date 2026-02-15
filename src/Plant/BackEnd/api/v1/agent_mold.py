"""Agent Mold enforcement endpoints.

Goal 2: Wire the hook bus into a real, callable API surface.

This is intentionally minimal: the Gateway can call these endpoints as an
enforcement proxy, and internal services can share the same policy plane.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional
from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Header, Request, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import JSONResponse

from agent_mold.enforcement import default_hook_bus
from agent_mold.hooks import HookEvent, HookStage
from agent_mold.reference_agents import get_reference_agent
from agent_mold.spec import AgentSpec, DimensionName
from agent_mold.skills.executor import execute_marketing_multichannel_v1
from agent_mold.skills.loader import load_playbook
from agent_mold.skills.playbook import ChannelName, SkillExecutionInput, SkillExecutionResult
from core.exceptions import PolicyEnforcementError, UsageLimitError
from core.database import get_db_session
from models.skill import Skill
from api.v1.agent_types_simple import get_agent_type_definition
from api.v1 import hired_agents_simple
from services.metering import (
    compute_effective_estimated_cost_usd,
    enforce_trial_and_budget,
    plan_enforces_budget,
    verify_trusted_metering_envelope_headers,
)
from services.policy_denial_audit import (
    PolicyDenialAuditRecord,
    PolicyDenialAuditStore,
    get_policy_denial_audit_store,
)
from services.usage_ledger import FileUsageLedger, InMemoryUsageLedger, UsageLedger
from services.usage_events import (
    FileUsageEventStore,
    InMemoryUsageEventStore,
    UsageEvent,
    UsageEventStore,
    UsageEventType,
)


router = APIRouter(prefix="/agent-mold", tags=["agent-mold"])

logger = logging.getLogger(__name__)


MARKETING_MULTICHANNEL_POST_V1_SKILL_KEY = "marketing.multichannel-post-v1"


def _safe_str(val: Any) -> str:
    return str(val or "").strip()


def _agent_type_id_for_agent_id(agent_id: str | None) -> str | None:
    """Best-effort mapping from agent_id to AgentTypeDefinition id.

    Phase-1: keep this logic aligned with hired-agent flows.
    """

    normalized = _safe_str(agent_id).upper()
    if normalized.startswith("AGT-TRD-"):
        return "trading.delta_futures.v1"
    if normalized.startswith("AGT-MKT-"):
        return "marketing.healthcare.v1"
    return None


async def _resolve_skill_key(
    *,
    skill_key: str | None,
    skill_id: str | None,
    db: AsyncSession | None,
    default_skill_key: str,
    instance: str,
) -> str | JSONResponse:
    """Resolve skill_key (preferred) with optional DB-backed skill_id compat."""

    normalized_key = _safe_str(skill_key)
    if normalized_key:
        return normalized_key

    normalized_id = _safe_str(skill_id)
    if not normalized_id:
        return default_skill_key

    if db is None:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "type": "https://waooaw.com/errors/validation-error",
                "title": "Validation Error",
                "status": 422,
                "detail": "skill_id resolution requires PERSISTENCE_MODE=db",
                "instance": instance,
                "violations": ["Provide skill_key or enable PERSISTENCE_MODE=db"],
            },
        )

    try:
        parsed = UUID(normalized_id)
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "type": "https://waooaw.com/errors/validation-error",
                "title": "Validation Error",
                "status": 422,
                "detail": "Invalid skill_id",
                "instance": instance,
                "violations": ["skill_id must be a UUID"],
            },
        )

    result = await db.execute(select(Skill).where(Skill.id == parsed))
    skill = result.scalars().first()
    if skill is None:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "type": "https://waooaw.com/errors/validation-error",
                "title": "Validation Error",
                "status": 422,
                "detail": "Unknown skill_id",
                "instance": instance,
                "violations": ["skill_id does not exist"],
            },
        )

    resolved = _safe_str(getattr(skill, "external_id", None))
    if not resolved:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "type": "https://waooaw.com/errors/validation-error",
                "title": "Validation Error",
                "status": 422,
                "detail": "Resolved skill has no skill_key (external_id)",
                "instance": instance,
                "violations": ["Skill.external_id is required for runtime enforcement"],
            },
        )

    return resolved


def _skill_configs_for_record(record: hired_agents_simple._HiredAgentRecord) -> dict[str, Any] | None:
    config = getattr(record, "config", None)
    if not isinstance(config, dict):
        return None
    raw = config.get("skill_configs")
    if isinstance(raw, dict):
        return raw
    return None


def _enforce_skill_allowed_or_raise(
    *,
    agent_type_id: str,
    effective_skill_key: str,
    hired_instance_id: str | None,
    hired_record: hired_agents_simple._HiredAgentRecord | None,
    correlation_id: str,
    customer_id: str | None,
    path: str,
    policy_audit: PolicyDenialAuditStore,
) -> None:
    definition = get_agent_type_definition(agent_type_id)
    if definition is None:
        raise PolicyEnforcementError(
            "Unknown agent type",
            reason="agent_type_not_found",
            details={"agent_type_id": agent_type_id},
        )

    allowed = set([_safe_str(k) for k in (definition.required_skill_keys or []) if _safe_str(k)])
    if effective_skill_key not in allowed:
        details = {
            "agent_type_id": agent_type_id,
            "skill_key": effective_skill_key,
            "required_skill_keys": sorted(allowed),
        }
        if hired_instance_id:
            details["hired_instance_id"] = hired_instance_id

        policy_audit.append(
            PolicyDenialAuditRecord(
                correlation_id=correlation_id,
                decision_id=None,
                agent_id=(hired_record.agent_id if hired_record is not None else None),
                customer_id=customer_id,
                stage=str(HookStage.PRE_TOOL_USE),
                action=f"execute:{effective_skill_key}",
                reason="skill_not_allowed",
                path=path,
                details=details,
            )
        )

        raise PolicyEnforcementError(
            "Skill not allowed for this agent type",
            reason="skill_not_allowed",
            details=details,
        )

    # Optional (SK-3.3): if the hired instance already has skill_configs, enforce that
    # this skill is present in the configured blocks.
    if hired_record is not None:
        skill_configs = _skill_configs_for_record(hired_record)
        if skill_configs is not None and effective_skill_key not in skill_configs:
            details = {
                "agent_type_id": agent_type_id,
                "skill_key": effective_skill_key,
                "hired_instance_id": hired_instance_id,
                "configured_skill_keys": sorted([_safe_str(k) for k in skill_configs.keys() if _safe_str(k)]),
            }
            policy_audit.append(
                PolicyDenialAuditRecord(
                    correlation_id=correlation_id,
                    decision_id=None,
                    agent_id=hired_record.agent_id,
                    customer_id=customer_id,
                    stage=str(HookStage.PRE_TOOL_USE),
                    action=f"execute:{effective_skill_key}",
                    reason="skill_not_configured",
                    path=path,
                    details=details,
                )
            )
            raise PolicyEnforcementError(
                "Skill not configured for this hired instance",
                reason="skill_not_configured",
                details=details,
            )


@lru_cache(maxsize=1)
def agent_spec_json_schema() -> Dict[str, Any]:
    """Return the JSON schema for AgentSpec.

    This is intended for out-of-band validation (e.g., Gateway/clients) without
    having to execute a full runtime compile step.
    """

    return AgentSpec.model_json_schema()


@router.get("/schema/agent-spec")
async def get_agent_spec_schema() -> Dict[str, Any]:
    """Expose the AgentSpec JSON schema for external validation tooling."""

    return agent_spec_json_schema()


class ValidateAgentSpecResponse(BaseModel):
    valid: bool = True


@router.post("/spec/validate", response_model=ValidateAgentSpecResponse)
async def validate_agent_spec(_: AgentSpec) -> ValidateAgentSpecResponse:
    """Validate an AgentSpec and return ok.

    Invalid specs will return 422 automatically via FastAPI/Pydantic.
    """

    return ValidateAgentSpecResponse(valid=True)


@lru_cache(maxsize=1)
def default_usage_ledger() -> UsageLedger:
    path = os.getenv("USAGE_LEDGER_STORE_PATH")
    if path:
        return FileUsageLedger(path)
    return InMemoryUsageLedger()


def get_usage_ledger() -> UsageLedger:
    return default_usage_ledger()


@lru_cache(maxsize=1)
def default_usage_event_store() -> UsageEventStore:
    path = os.getenv("USAGE_EVENTS_STORE_PATH")
    if path:
        return FileUsageEventStore(path)
    return InMemoryUsageEventStore()


def get_usage_event_store() -> UsageEventStore:
    return default_usage_event_store()


def _persistence_mode() -> str:
    return os.getenv("PERSISTENCE_MODE", "memory").strip().lower()


async def _get_agent_mold_db_session() -> AsyncGenerator[AsyncSession | None, None]:
    """Yield a DB session only when DB-backed mode is enabled."""

    if _persistence_mode() != "db":
        yield None
        return

    async for session in get_db_session():
        yield session


class ToolUseEnforceRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    payload: Dict[str, Any] = Field(default_factory=dict)
    approval_id: Optional[str] = None
    customer_id: Optional[str] = None
    purpose: Optional[str] = None
    correlation_id: Optional[str] = None


class ToolUseEnforceResponse(BaseModel):
    allowed: bool
    reason: str
    decision_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@router.post("/tool-use", response_model=ToolUseEnforceResponse)
async def enforce_tool_use(
    body: ToolUseEnforceRequest,
    request: Request,
    x_correlation_id: Optional[str] = Header(default=None, alias="X-Correlation-ID"),
    policy_audit: PolicyDenialAuditStore = Depends(get_policy_denial_audit_store),
) -> ToolUseEnforceResponse:
    """Evaluate pre-tool-use policy and return allow/deny.

    If denied, raises PolicyEnforcementError (RFC 7807 via exception handler).
    """

    correlation_id = body.correlation_id or x_correlation_id or str(id(request))

    event_payload = dict(body.payload or {})
    if body.approval_id:
        event_payload["approval_id"] = body.approval_id

    decision = default_hook_bus().emit(
        HookEvent(
            stage=HookStage.PRE_TOOL_USE,
            correlation_id=correlation_id,
            agent_id=body.agent_id,
            customer_id=body.customer_id,
            purpose=body.purpose,
            action=body.action,
            payload=event_payload,
        )
    )

    if not decision.allowed:
        # Minimal audit signal for now (log-based). Later phases can persist this
        # via the audit service / ledger.
        logger.warning(
            "policy_denied",
            extra={
                "correlation_id": correlation_id,
                "agent_id": body.agent_id,
                "customer_id": body.customer_id,
                "stage": HookStage.PRE_TOOL_USE,
                "action": body.action,
                "reason": decision.reason,
                "details": decision.details,
            },
        )
        details: Dict[str, Any] = dict(decision.details or {})
        if decision.decision_id:
            details["decision_id"] = decision.decision_id

        policy_audit.append(
            PolicyDenialAuditRecord(
                correlation_id=correlation_id,
                decision_id=decision.decision_id,
                agent_id=body.agent_id,
                customer_id=body.customer_id,
                stage=str(HookStage.PRE_TOOL_USE),
                action=body.action,
                reason=decision.reason,
                path=str(request.url.path),
                details=details,
            )
        )

        raise PolicyEnforcementError(
            "Policy denied tool use",
            reason=decision.reason,
            details=details,
        )

    return ToolUseEnforceResponse(
        allowed=True,
        reason=decision.reason,
        decision_id=decision.decision_id,
        details=decision.details,
    )


@lru_cache(maxsize=1)
def _marketing_multichannel_playbook() -> Any:
    path = (
        Path(__file__).resolve().parents[2]
        / "agent_mold"
        / "playbooks"
        / "marketing"
        / "multichannel_post_v1.md"
    )
    return load_playbook(path)


class ExecuteMarketingMultichannelRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)

    # SK-3.3: runtime skill routing and enforcement.
    # skill_key is preferred; skill_id is compat in DB-backed mode.
    skill_key: Optional[str] = None
    skill_id: Optional[str] = None
    hired_instance_id: Optional[str] = None

    # Metering / trial context
    customer_id: Optional[str] = None
    trial_mode: bool = False
    trial_id: Optional[UUID] = None
    plan_id: Optional[str] = None
    estimated_cost_usd: float = 0.0

    # Metering payload (from AI Explorer / LLM front-door)
    meter_tokens_in: int = 0
    meter_tokens_out: int = 0
    meter_model: Optional[str] = None
    meter_cache_hit: bool = False

    # Enforcement intent: if you intend an external action, it must be declared
    # and will be enforced.
    intent_action: Optional[str] = None
    # Optional shortcut: allow the agent to attempt publish automatically.
    # This is disabled by default and only allowed when the agent's AgentSpec
    # explicitly permits it.
    autopublish: bool = False
    approval_id: Optional[str] = None

    purpose: Optional[str] = None
    correlation_id: Optional[str] = None

    # Optional channel selection. If omitted, Plant emits the standard 5-channel set.
    channels: Optional[List[ChannelName]] = None

    # Skill execution input
    theme: str
    brand_name: str
    offer: Optional[str] = None
    location: Optional[str] = None
    audience: Optional[str] = None
    tone: Optional[str] = None
    language: Optional[str] = None


@router.post(
    "/skills/marketing/multichannel-post-v1/execute",
    response_model=SkillExecutionResult,
)
async def execute_marketing_multichannel_post_v1(
    body: ExecuteMarketingMultichannelRequest,
    request: Request,
    x_correlation_id: Optional[str] = Header(default=None, alias="X-Correlation-ID"),
    db: AsyncSession | None = Depends(_get_agent_mold_db_session),
    ledger: UsageLedger = Depends(get_usage_ledger),
    events: UsageEventStore = Depends(get_usage_event_store),
    policy_audit: PolicyDenialAuditStore = Depends(get_policy_denial_audit_store),
) -> SkillExecutionResult:
    """Execute the marketing multichannel playbook.

    Goal 2: make enforcement non-bypassable for real executions.
    - If `intent_action` is provided (e.g. "publish"), it is enforced via hooks.
    """

    correlation_id = body.correlation_id or x_correlation_id or str(id(request))

    # SK-3.3: fail-closed skill availability enforcement.
    # This endpoint is a single-skill executor; callers may optionally pass skill_key/skill_id
    # but it must resolve to the canonical key for this endpoint.
    instance = str(request.url.path)

    hired_record: hired_agents_simple._HiredAgentRecord | None = None
    if _safe_str(body.hired_instance_id):
        hired_record = hired_agents_simple._by_id.get(_safe_str(body.hired_instance_id))
        if hired_record is None:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "type": "https://waooaw.com/errors/validation-error",
                    "title": "Validation Error",
                    "status": 422,
                    "detail": "Unknown hired_instance_id",
                    "instance": instance,
                    "violations": ["hired_instance_id does not exist"],
                },
            )

    effective_agent_id = (hired_record.agent_id if hired_record is not None else body.agent_id)
    agent_type_id = _agent_type_id_for_agent_id(effective_agent_id)
    if not agent_type_id:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "type": "https://waooaw.com/errors/validation-error",
                "title": "Validation Error",
                "status": 422,
                "detail": "Unable to resolve agent_type_id for agent_id",
                "instance": instance,
                "violations": ["agent_id is not eligible for skill execution"],
            },
        )

    # Note: this endpoint currently runs in unit tests without a DB; keep skill_id optional.
    effective_skill_key = await _resolve_skill_key(
        skill_key=body.skill_key,
        skill_id=body.skill_id,
        db=db,
        default_skill_key=MARKETING_MULTICHANNEL_POST_V1_SKILL_KEY,
        instance=instance,
    )
    if isinstance(effective_skill_key, JSONResponse):
        return effective_skill_key

    if effective_skill_key != MARKETING_MULTICHANNEL_POST_V1_SKILL_KEY:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "type": "https://waooaw.com/errors/validation-error",
                "title": "Validation Error",
                "status": 422,
                "detail": "skill_key does not match this endpoint",
                "instance": instance,
                "violations": [
                    f"Expected skill_key={MARKETING_MULTICHANNEL_POST_V1_SKILL_KEY}",
                ],
                "skill_key": effective_skill_key,
            },
        )

    _enforce_skill_allowed_or_raise(
        agent_type_id=agent_type_id,
        effective_skill_key=effective_skill_key,
        hired_instance_id=_safe_str(body.hired_instance_id) or None,
        hired_record=hired_record,
        correlation_id=correlation_id,
        customer_id=body.customer_id,
        path=instance,
        policy_audit=policy_audit,
    )

    metering_verification = verify_trusted_metering_envelope_headers(
        headers=request.headers,
        correlation_id=correlation_id,
    )

    meter_tokens_in = body.meter_tokens_in
    meter_tokens_out = body.meter_tokens_out
    meter_model = body.meter_model
    meter_cache_hit = body.meter_cache_hit
    estimated_cost_usd = body.estimated_cost_usd

    if metering_verification.envelope is not None:
        meter_tokens_in = metering_verification.envelope.tokens_in
        meter_tokens_out = metering_verification.envelope.tokens_out
        meter_model = metering_verification.envelope.model
        meter_cache_hit = metering_verification.envelope.cache_hit
        estimated_cost_usd = metering_verification.envelope.cost_usd

    if (
        metering_verification.enabled
        and body.customer_id
        and plan_enforces_budget(body.plan_id)
        and metering_verification.status != "trusted"
    ):
        reason = "metering_envelope_required"
        if metering_verification.status in {"invalid", "bad_format"}:
            reason = "metering_envelope_invalid"
        elif metering_verification.status == "stale":
            reason = "metering_envelope_expired"

        raise UsageLimitError(
            "Trusted metering envelope required for budget enforcement",
            reason=reason,
            details={
                "customer_id": body.customer_id,
                "plan_id": body.plan_id,
                "metering_status": metering_verification.status,
            },
        )

    effective_estimated_cost_usd = compute_effective_estimated_cost_usd(
        estimated_cost_usd=estimated_cost_usd,
        meter_tokens_in=meter_tokens_in,
        meter_tokens_out=meter_tokens_out,
        meter_model=meter_model,
    )

    intent_action = body.intent_action
    if body.autopublish:
        if intent_action and intent_action.lower() != "publish":
            raise PolicyEnforcementError(
                "Autopublish conflicts with intent_action",
                reason="autopublish_conflicts_intent_action",
                details={
                    "intent_action": intent_action,
                },
            )

        # Only allow autopublish for agents whose AgentSpec explicitly enables it.
        ref = get_reference_agent(body.agent_id)
        allowed = False
        if ref is not None:
            skill_dim = ref.spec.dimensions.get(DimensionName.SKILL)
            allowed = bool(skill_dim and skill_dim.config.get("autopublish_allowed") is True)

        if not allowed:
            policy_audit.append(
                PolicyDenialAuditRecord(
                    correlation_id=correlation_id,
                    decision_id=None,
                    agent_id=body.agent_id,
                    customer_id=body.customer_id,
                    stage=str(HookStage.PRE_TOOL_USE),
                    action="publish",
                    reason="autopublish_not_allowed",
                    path=str(request.url.path),
                    details={"agent_id": body.agent_id},
                )
            )
            raise PolicyEnforcementError(
                "Autopublish not allowed for agent",
                reason="autopublish_not_allowed",
                details={
                    "agent_id": body.agent_id,
                },
            )

        intent_action = "publish"

    enforce_trial_and_budget(
        correlation_id=correlation_id,
        agent_id=body.agent_id,
        customer_id=body.customer_id,
        plan_id=body.plan_id,
        trial_mode=body.trial_mode,
        intent_action=intent_action,
        effective_estimated_cost_usd=effective_estimated_cost_usd,
        meter_tokens_in=meter_tokens_in,
        meter_tokens_out=meter_tokens_out,
        purpose=body.purpose,
        ledger=ledger,
        events=events,
    )

    if intent_action:
        event_payload: Dict[str, Any] = {}
        if body.approval_id:
            event_payload["approval_id"] = body.approval_id
        if body.autopublish:
            event_payload["autopublish"] = True

        decision = default_hook_bus().emit(
            HookEvent(
                stage=HookStage.PRE_TOOL_USE,
                correlation_id=correlation_id,
                agent_id=body.agent_id,
                customer_id=body.customer_id,
                purpose=body.purpose,
                action=intent_action,
                payload=event_payload,
            )
        )

        if not decision.allowed:
            logger.warning(
                "policy_denied",
                extra={
                    "correlation_id": correlation_id,
                    "agent_id": body.agent_id,
                    "customer_id": body.customer_id,
                    "stage": HookStage.PRE_TOOL_USE,
                    "action": body.intent_action,
                    "reason": decision.reason,
                    "details": decision.details,
                },
            )
            details: Dict[str, Any] = dict(decision.details or {})
            if decision.decision_id:
                details["decision_id"] = decision.decision_id

            policy_audit.append(
                PolicyDenialAuditRecord(
                    correlation_id=correlation_id,
                    decision_id=decision.decision_id,
                    agent_id=body.agent_id,
                    customer_id=body.customer_id,
                    stage=str(HookStage.PRE_TOOL_USE),
                    action=intent_action,
                    reason=decision.reason,
                    path=str(request.url.path),
                    details=details,
                )
            )

            raise PolicyEnforcementError(
                "Policy denied tool use",
                reason=decision.reason,
                details=details,
            )

    inp = SkillExecutionInput(
        theme=body.theme,
        brand_name=body.brand_name,
        offer=body.offer,
        location=body.location,
        audience=body.audience,
        tone=body.tone,
        language=body.language,
            channels=body.channels,
    )

    playbook = _marketing_multichannel_playbook()
    result = execute_marketing_multichannel_v1(playbook, inp)
    result.skill_key = MARKETING_MULTICHANNEL_POST_V1_SKILL_KEY

    # Deterministic executor emits zero-token usage for now.
    events.append(
        UsageEvent(
            event_type=UsageEventType.SKILL_EXECUTION,
            correlation_id=correlation_id,
            customer_id=body.customer_id,
            agent_id=body.agent_id,
            purpose=body.purpose,
            action=(body.intent_action or "draft"),
            model=meter_model,
            cache_hit=meter_cache_hit,
            tokens_in=max(0, int(meter_tokens_in)),
            tokens_out=max(0, int(meter_tokens_out)),
            cost_usd=effective_estimated_cost_usd if effective_estimated_cost_usd > 0 else 0.0,
        )
    )

    return result
