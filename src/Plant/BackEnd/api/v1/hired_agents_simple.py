"""Hired agent instance APIs (Phase-1 simple implementation).

HIRE-3.3 + HIRE-3.4:
- Persist a customer-scoped hired agent instance tied to a subscription.
- Allow saving a draft configuration.
- Finalize config and start trial only when:
  1) subscription is active
  2) instance is configured
  3) goals step is completed

This is an in-memory implementation intended to unblock CP Hire wizard flows in lower envs.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.v1 import payments_simple
from services.notification_events import NotificationEventRecord, get_notification_event_store


TrialStatus = Literal["not_started", "active", "ended_converted", "ended_not_converted"]


ALLOWED_THEMES: set[str] = {"default", "dark", "light"}
DEFAULT_TRIAL_DAYS = 7


SUPPORTED_TRADING_EXCHANGES: set[str] = {"delta_exchange_india"}


SUPPORTED_MARKETING_PLATFORMS: set[str] = {"youtube", "instagram", "facebook", "linkedin", "whatsapp", "x", "twitter"}


class HiredAgentDraftUpsertRequest(BaseModel):
    subscription_id: str = Field(..., min_length=1)
    agent_id: str = Field(..., min_length=1)
    customer_id: str = Field(..., min_length=1)

    nickname: str | None = None
    theme: str | None = None

    config: dict[str, Any] | None = None


class HiredAgentFinalizeRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    goals_completed: bool = Field(False)


class HiredAgentInstanceResponse(BaseModel):
    hired_instance_id: str
    subscription_id: str
    agent_id: str
    customer_id: str | None = None

    nickname: str | None = None
    theme: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)

    configured: bool = False
    goals_completed: bool = False

    active: bool = True

    subscription_status: str | None = None
    subscription_ended_at: datetime | None = None
    retention_expires_at: datetime | None = None
    trial_status: TrialStatus = "not_started"
    trial_start_at: datetime | None = None
    trial_end_at: datetime | None = None

    created_at: datetime
    updated_at: datetime


class ProcessTrialEndRequest(BaseModel):
    now: datetime | None = None


class _HiredAgentRecord(BaseModel):
    hired_instance_id: str
    subscription_id: str
    agent_id: str
    customer_id: str | None
    nickname: str | None
    theme: str | None
    config: dict[str, Any]
    configured: bool
    goals_completed: bool
    active: bool
    trial_status: TrialStatus
    trial_start_at: datetime | None
    trial_end_at: datetime | None
    created_at: datetime
    updated_at: datetime


_by_id: dict[str, _HiredAgentRecord] = {}
_by_subscription: dict[str, str] = {}


router = APIRouter(prefix="/hired-agents", tags=["hired-agents"])


def _normalize_theme(theme: str | None) -> str | None:
    if theme is None:
        return None
    normalized = (theme or "").strip().lower()
    if not normalized:
        return None
    if normalized not in ALLOWED_THEMES:
        raise HTTPException(status_code=400, detail="Unsupported theme.")
    return normalized


def _compute_configured(nickname: str | None, theme: str | None) -> bool:
    return bool((nickname or "").strip()) and bool((theme or "").strip())


def _is_trading_agent(agent_id: str | None) -> bool:
    return str(agent_id or "").strip().upper().startswith("AGT-TRD-")


def _is_marketing_agent(agent_id: str | None) -> bool:
    return str(agent_id or "").strip().upper().startswith("AGT-MKT-")


def _as_nonempty_str(value: Any) -> str | None:
    s = str(value or "").strip()
    return s or None


def _trading_config_complete(config: dict[str, Any] | None) -> bool:
    cfg = dict(config or {})
    exchange_provider = _as_nonempty_str(cfg.get("exchange_provider"))
    if not exchange_provider or exchange_provider not in SUPPORTED_TRADING_EXCHANGES:
        return False

    credential_ref = _as_nonempty_str(cfg.get("exchange_credential_ref"))
    if not credential_ref:
        return False

    allowed_coins_raw = cfg.get("allowed_coins")
    allowed_coins: list[str] = []
    if isinstance(allowed_coins_raw, list):
        for c in allowed_coins_raw:
            coin = _as_nonempty_str(c)
            if coin:
                allowed_coins.append(coin.upper())
    if not allowed_coins:
        return False

    interval_raw = cfg.get("interval_seconds")
    try:
        interval_seconds = int(interval_raw)
    except Exception:
        interval_seconds = 0
    if interval_seconds <= 0:
        return False

    return True


def _marketing_config_complete(config: dict[str, Any] | None) -> bool:
    cfg = dict(config or {})
    platforms_raw = cfg.get("platforms")
    if not isinstance(platforms_raw, list) or not platforms_raw:
        return False

    valid_count = 0
    for row in platforms_raw:
        if not isinstance(row, dict):
            continue
        platform = _as_nonempty_str(row.get("platform"))
        credential_ref = _as_nonempty_str(row.get("credential_ref"))
        if not platform or platform.lower() not in SUPPORTED_MARKETING_PLATFORMS:
            continue
        if not credential_ref:
            continue
        valid_count += 1

    return valid_count > 0


def _compute_agent_configured(
    nickname: str | None,
    theme: str | None,
    *,
    agent_id: str | None,
    config: dict[str, Any] | None,
) -> bool:
    base = bool((nickname or "").strip()) and bool((theme or "").strip())
    if not base:
        return False
    if _is_trading_agent(agent_id):
        return _trading_config_complete(config)
    if _is_marketing_agent(agent_id):
        return _marketing_config_complete(config)
    return True


def _retention_days_after_end() -> int:
    raw = (os.getenv("END_RETENTION_DAYS") or "30").strip()
    try:
        days = int(raw)
    except Exception:
        days = 30
    return max(days, 0)


def _to_response(record: _HiredAgentRecord) -> HiredAgentInstanceResponse:
    subscription_status = payments_simple.get_subscription_status(record.subscription_id)
    ended_at = payments_simple.get_subscription_ended_at(record.subscription_id)

    retention_expires_at: datetime | None = None
    if subscription_status == "canceled" and ended_at is not None:
        retention_expires_at = ended_at + timedelta(days=_retention_days_after_end())

    return HiredAgentInstanceResponse(
        hired_instance_id=record.hired_instance_id,
        subscription_id=record.subscription_id,
        agent_id=record.agent_id,
        customer_id=record.customer_id,
        nickname=record.nickname,
        theme=record.theme,
        config=record.config,
        configured=record.configured,
        goals_completed=record.goals_completed,
        active=record.active,
        subscription_status=subscription_status,
        subscription_ended_at=ended_at,
        retention_expires_at=retention_expires_at,
        trial_status=record.trial_status,
        trial_start_at=record.trial_start_at,
        trial_end_at=record.trial_end_at,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.put("/draft", response_model=HiredAgentInstanceResponse)
async def upsert_draft(body: HiredAgentDraftUpsertRequest) -> HiredAgentInstanceResponse:
    now = datetime.now(timezone.utc)
    theme = _normalize_theme(body.theme)

    customer_id = (body.customer_id or "").strip()
    if not customer_id:
        raise HTTPException(status_code=400, detail="customer_id is required.")

    subscription_status = payments_simple.get_subscription_status(body.subscription_id)
    if subscription_status is None:
        raise HTTPException(status_code=404, detail="Subscription not found.")
    if subscription_status != "active":
        raise HTTPException(status_code=409, detail="Subscription is not active; hired agent is read-only.")

    existing_id = _by_subscription.get(body.subscription_id)
    if existing_id and existing_id in _by_id:
        record = _by_id[existing_id]

        existing_customer_id = (record.customer_id or "").strip()
        if existing_customer_id and existing_customer_id != customer_id:
            raise HTTPException(status_code=403, detail="Hired agent instance does not belong to customer.")
        updated_config = dict(record.config)
        if body.config is not None:
            updated_config = dict(body.config)

        nickname = body.nickname if body.nickname is not None else record.nickname
        theme_value = theme if theme is not None else record.theme
        configured = _compute_agent_configured(
            nickname,
            theme_value,
            agent_id=(body.agent_id or record.agent_id),
            config=updated_config,
        )

        record = record.model_copy(
            update={
                "agent_id": body.agent_id or record.agent_id,
                "customer_id": customer_id,
                "nickname": nickname,
                "theme": theme_value,
                "config": updated_config,
                "configured": configured,
                "active": True,
                "updated_at": now,
            }
        )
        _by_id[existing_id] = record
        return _to_response(record)

    hired_instance_id = f"HAI-{uuid4()}"
    record = _HiredAgentRecord(
        hired_instance_id=hired_instance_id,
        subscription_id=body.subscription_id,
        agent_id=body.agent_id,
        customer_id=customer_id,
        nickname=(body.nickname or None),
        theme=theme,
        config=dict(body.config or {}),
        configured=_compute_agent_configured(body.nickname, theme, agent_id=body.agent_id, config=(body.config or {})),
        goals_completed=False,
        active=True,
        trial_status="not_started",
        trial_start_at=None,
        trial_end_at=None,
        created_at=now,
        updated_at=now,
    )

    _by_id[hired_instance_id] = record
    _by_subscription[body.subscription_id] = hired_instance_id
    return _to_response(record)


@router.get("/by-subscription/{subscription_id}", response_model=HiredAgentInstanceResponse)
async def get_by_subscription(
    subscription_id: str,
    as_of: datetime | None = None,
    customer_id: str | None = None,
) -> HiredAgentInstanceResponse:
    hired_instance_id = _by_subscription.get(subscription_id)
    if not hired_instance_id:
        raise HTTPException(status_code=404, detail="Hired agent instance not found.")
    record = _by_id.get(hired_instance_id)
    if not record:
        raise HTTPException(status_code=404, detail="Hired agent instance not found.")

    normalized_customer_id = (customer_id or "").strip()
    if not normalized_customer_id:
        raise HTTPException(status_code=400, detail="customer_id is required.")
    existing_customer_id = (record.customer_id or "").strip()
    if existing_customer_id and existing_customer_id != normalized_customer_id:
        # Use 404 to avoid leaking subscription existence.
        raise HTTPException(status_code=404, detail="Hired agent instance not found.")

    subscription_status = payments_simple.get_subscription_status(record.subscription_id)
    ended_at = payments_simple.get_subscription_ended_at(record.subscription_id)
    if subscription_status == "canceled":
        if ended_at is None:
            raise HTTPException(status_code=410, detail="Hired agent data is no longer available.")
        retention_days = _retention_days_after_end()
        if retention_days <= 0:
            raise HTTPException(status_code=410, detail="Hired agent data is no longer available.")
        effective_now = as_of or datetime.now(timezone.utc)
        if effective_now > ended_at + timedelta(days=retention_days):
            raise HTTPException(status_code=410, detail="Hired agent data is no longer available.")

    return _to_response(record)


@router.post("/{hired_instance_id}/finalize", response_model=HiredAgentInstanceResponse)
async def finalize(hired_instance_id: str, body: HiredAgentFinalizeRequest) -> HiredAgentInstanceResponse:
    record = _by_id.get(hired_instance_id)
    if not record:
        raise HTTPException(status_code=404, detail="Hired agent instance not found.")

    customer_id = (body.customer_id or "").strip()
    if not customer_id:
        raise HTTPException(status_code=400, detail="customer_id is required.")
    existing_customer_id = (record.customer_id or "").strip()
    if existing_customer_id and existing_customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Hired agent instance not found.")

    now = datetime.now(timezone.utc)
    configured = _compute_agent_configured(record.nickname, record.theme, agent_id=record.agent_id, config=record.config)

    trial_status: TrialStatus = record.trial_status
    trial_start_at = record.trial_start_at
    trial_end_at = record.trial_end_at

    subscription_status = payments_simple.get_subscription_status(record.subscription_id)
    if subscription_status is None:
        raise HTTPException(status_code=404, detail="Subscription not found.")
    if subscription_status != "active":
        raise HTTPException(status_code=409, detail="Subscription is not active; hired agent is read-only.")
    should_start_trial = (
        subscription_status == "active" and configured and bool(body.goals_completed)
    )

    if should_start_trial and trial_status != "active":
        trial_status = "active"
        trial_start_at = now
        trial_end_at = now + timedelta(days=DEFAULT_TRIAL_DAYS)

        # NOTIF-1.1: emit trial activated (best-effort).
        try:
            get_notification_event_store().append(
                NotificationEventRecord(
                    event_type="trial_activated",
                    customer_id=(record.customer_id or None),
                    subscription_id=record.subscription_id,
                    hired_instance_id=record.hired_instance_id,
                    metadata={
                        "trial_start_at": trial_start_at.isoformat() if trial_start_at else None,
                        "trial_end_at": trial_end_at.isoformat() if trial_end_at else None,
                    },
                )
            )
        except Exception:
            pass

    updated = record.model_copy(
        update={
            "configured": configured,
            "goals_completed": bool(body.goals_completed),
            "active": record.active,
            "trial_status": trial_status,
            "trial_start_at": trial_start_at,
            "trial_end_at": trial_end_at,
            "updated_at": now,
        }
    )
    _by_id[hired_instance_id] = updated
    return _to_response(updated)


def _process_trial_end(now: datetime) -> int:
    processed = 0
    for hired_instance_id, record in list(_by_id.items()):
        if record.trial_status != "active":
            continue
        if record.trial_end_at is None:
            continue
        if record.trial_end_at > now:
            continue

        subscription_status = payments_simple.get_subscription_status(record.subscription_id)
        next_status: TrialStatus = "ended_not_converted"
        if subscription_status == "active":
            # Product decision: trial auto-converts to paid when it ends.
            next_status = "ended_converted"

        _by_id[hired_instance_id] = record.model_copy(
            update={
                "trial_status": next_status,
                "updated_at": now,
            }
        )

        # NOTIF-1.1: emit trial ended (best-effort).
        try:
            get_notification_event_store().append(
                NotificationEventRecord(
                    event_type="trial_ended",
                    customer_id=(record.customer_id or None),
                    subscription_id=record.subscription_id,
                    hired_instance_id=record.hired_instance_id,
                    metadata={
                        "next_status": next_status,
                        "processed_at": now.isoformat(),
                    },
                )
            )
        except Exception:
            pass
        processed += 1
    return processed


@router.post("/process-trial-end")
async def process_trial_end(body: ProcessTrialEndRequest) -> dict:
    now = body.now or datetime.now(timezone.utc)
    processed = _process_trial_end(now)
    return {"processed": processed, "now": now}


def deactivate_by_subscription(*, subscription_id: str, now: datetime | None = None) -> str | None:
    """Deactivate the hired agent instance tied to a subscription.

    Phase-1 helper called by payments period-end processing.
    """

    hired_instance_id = _by_subscription.get(subscription_id)
    if not hired_instance_id:
        return None
    record = _by_id.get(hired_instance_id)
    if not record:
        return None
    ts = now or datetime.now(timezone.utc)
    updated = record.model_copy(update={"active": False, "updated_at": ts})
    _by_id[hired_instance_id] = updated
    return hired_instance_id
