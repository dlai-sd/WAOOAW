from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from pydantic import BaseModel


def _duration_to_period_end(duration: str, start: datetime) -> datetime:
    normalized = (duration or "").strip().lower()
    if normalized == "monthly":
        return start + timedelta(days=30)
    if normalized == "quarterly":
        return start + timedelta(days=90)
    if normalized == "yearly":
        return start + timedelta(days=365)
    raise HTTPException(status_code=400, detail="Unsupported duration.")


class CPSubscriptionRecord(BaseModel):
    subscription_id: str
    owner_user_id: str
    agent_id: str
    duration: str

    status: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = False


_by_id: dict[str, CPSubscriptionRecord] = {}


def create_subscription_for_user(*, subscription_id: str, owner_user_id: str, agent_id: str, duration: str) -> CPSubscriptionRecord:
    now = datetime.now(timezone.utc)
    record = CPSubscriptionRecord(
        subscription_id=subscription_id,
        owner_user_id=owner_user_id,
        agent_id=agent_id,
        duration=duration,
        status="active",
        current_period_start=now,
        current_period_end=_duration_to_period_end(duration, now),
        cancel_at_period_end=False,
    )
    _by_id[subscription_id] = record
    return record


def list_for_user(owner_user_id: str) -> list[CPSubscriptionRecord]:
    results = [r for r in _by_id.values() if r.owner_user_id == owner_user_id]
    results.sort(key=lambda r: r.current_period_end)
    return results


def get_for_user(*, subscription_id: str, owner_user_id: str) -> CPSubscriptionRecord:
    record = _by_id.get(subscription_id)
    if not record:
        raise HTTPException(status_code=404, detail="Subscription not found")
    if record.owner_user_id != owner_user_id:
        raise HTTPException(status_code=403, detail="Subscription does not belong to user")
    return record


def cancel_for_user(*, subscription_id: str, owner_user_id: str) -> CPSubscriptionRecord:
    record = get_for_user(subscription_id=subscription_id, owner_user_id=owner_user_id)
    if record.status != "active":
        raise HTTPException(status_code=409, detail="Subscription is not active")
    updated = record.model_copy(update={"cancel_at_period_end": True})
    _by_id[subscription_id] = updated
    return updated


def process_period_end(now: datetime) -> int:
    processed = 0
    for sub_id, record in list(_by_id.items()):
        if record.status != "active":
            continue
        if not record.cancel_at_period_end:
            continue
        if record.current_period_end > now:
            continue
        _by_id[sub_id] = record.model_copy(update={"status": "canceled"})
        processed += 1
    return processed
