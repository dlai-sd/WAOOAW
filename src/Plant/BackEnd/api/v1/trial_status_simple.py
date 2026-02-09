"""Trial status API (Phase-1 simple implementation).

TRIAL-1.1:
Expose a customer-scoped view of trial status and timestamps that matches
Definitions & States used by the Phase-1 hire wizard.

This is intentionally backed by the in-memory hired-agent instance store
(`hired_agents_simple`) used in lower envs.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.v1 import hired_agents_simple


class TrialStatusRecord(BaseModel):
    subscription_id: str
    hired_instance_id: str

    trial_status: str
    trial_start_at: datetime | None = None
    trial_end_at: datetime | None = None

    configured: bool = False
    goals_completed: bool = False


class TrialStatusListResponse(BaseModel):
    trials: list[TrialStatusRecord]


router = APIRouter(prefix="/trial-status", tags=["trial-status"])


def _require_customer_id(customer_id: str | None) -> str:
    normalized = (customer_id or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="customer_id is required")
    return normalized


def _to_trial_status_record(record: hired_agents_simple._HiredAgentRecord) -> TrialStatusRecord:  # type: ignore[name-defined]
    return TrialStatusRecord(
        subscription_id=record.subscription_id,
        hired_instance_id=record.hired_instance_id,
        trial_status=record.trial_status,
        trial_start_at=record.trial_start_at,
        trial_end_at=record.trial_end_at,
        configured=bool(record.configured),
        goals_completed=bool(record.goals_completed),
    )


@router.get("", response_model=TrialStatusListResponse)
async def list_trial_status(customer_id: str | None = None) -> TrialStatusListResponse:
    normalized = _require_customer_id(customer_id)

    results: list[TrialStatusRecord] = []
    for record in hired_agents_simple._by_id.values():  # type: ignore[attr-defined]
        if (record.customer_id or "").strip() != normalized:
            continue
        results.append(_to_trial_status_record(record))

    # Stable ordering for UX/tests
    results.sort(key=lambda r: (r.trial_end_at or datetime.min, r.subscription_id))
    return TrialStatusListResponse(trials=results)


@router.get("/by-subscription/{subscription_id}", response_model=TrialStatusRecord)
async def get_trial_status_by_subscription(subscription_id: str, customer_id: str | None = None) -> TrialStatusRecord:
    normalized = _require_customer_id(customer_id)

    hired_instance_id = hired_agents_simple._by_subscription.get(subscription_id)  # type: ignore[attr-defined]
    if not hired_instance_id:
        raise HTTPException(status_code=404, detail="Trial not found")

    record = hired_agents_simple._by_id.get(hired_instance_id)  # type: ignore[attr-defined]
    if not record:
        raise HTTPException(status_code=404, detail="Trial not found")

    if (record.customer_id or "").strip() != normalized:
        raise HTTPException(status_code=404, detail="Trial not found")

    return _to_trial_status_record(record)
