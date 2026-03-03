from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import Depends, HTTPException, Request
from core.routing import waooaw_router  # P-3
from pydantic import BaseModel

from api.auth.dependencies import get_current_user
from models.user import User
from services.cp_subscriptions_simple import CPSubscriptionRecord, list_for_user

router = waooaw_router(prefix="/cp/my-agents", tags=["cp-my-agents"])

def _bool_env(name: str, default: str = "false") -> bool:
    return (os.getenv(name) or default).strip().lower() in {"1", "true", "yes", "on"}

def _plant_base_url() -> str:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base_url:
        raise RuntimeError("PLANT_GATEWAY_URL not configured")
    return base_url

async def _plant_get_json(*, url: str, authorization: str | None) -> dict | list:
    headers: dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers=headers)

    if 400 <= resp.status_code < 500:
        raise HTTPException(status_code=resp.status_code, detail=f"Plant call failed ({resp.status_code})")
    if resp.status_code >= 500:
        raise RuntimeError(f"Plant call failed ({resp.status_code})")

    return resp.json()

class MyAgentInstanceSummary(BaseModel):
    subscription_id: str
    agent_id: str
    duration: str
    status: str
    current_period_start: str
    current_period_end: str
    cancel_at_period_end: bool

    hired_instance_id: str | None = None
    agent_type_id: str | None = None
    nickname: str | None = None

    configured: bool | None = None
    goals_completed: bool | None = None

    trial_status: str | None = None
    trial_start_at: str | None = None
    trial_end_at: str | None = None

    subscription_status: str | None = None
    subscription_ended_at: str | None = None
    retention_expires_at: str | None = None

class MyAgentsSummaryResponse(BaseModel):
    instances: list[MyAgentInstanceSummary]

def _subscription_record_to_summary(record: CPSubscriptionRecord) -> MyAgentInstanceSummary:
    return MyAgentInstanceSummary(
        subscription_id=record.subscription_id,
        agent_id=record.agent_id,
        duration=record.duration,
        status=record.status,
        current_period_start=record.current_period_start.isoformat(),
        current_period_end=record.current_period_end.isoformat(),
        cancel_at_period_end=bool(record.cancel_at_period_end),
    )

async def _list_subscriptions(*, authorization: str | None, customer_id: str) -> list[MyAgentInstanceSummary]:
    if _bool_env("CP_SUBSCRIPTIONS_USE_PLANT", "false"):
        try:
            base = _plant_base_url()
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc))
        data = await _plant_get_json(
            url=f"{base}/api/v1/payments/subscriptions/by-customer/{customer_id}",
            authorization=authorization,
        )
        if not isinstance(data, list):
            raise HTTPException(status_code=502, detail="Unexpected Plant response")
        return [
            MyAgentInstanceSummary(
                subscription_id=item["subscription_id"],
                agent_id=item["agent_id"],
                duration=item["duration"],
                status=item["status"],
                current_period_start=item["current_period_start"],
                current_period_end=item["current_period_end"],
                cancel_at_period_end=bool(item.get("cancel_at_period_end")),
            )
            for item in data
            if isinstance(item, dict)
        ]

    return [_subscription_record_to_summary(r) for r in list_for_user(customer_id)]

async def _fallback_from_plant_hired_agents(
    *, authorization: str | None, customer_id: str
) -> list[MyAgentInstanceSummary]:
    """Fallback: when cp_subscriptions_simple has no records (in-memory mode on fresh
    restart), read hired agents directly from Plant by customer_id and synthesise
    MyAgentInstanceSummary objects so My Agents page shows seeded data.

    This path is read-only — it never writes to cp_subscriptions_simple.
    All config values come from env vars injected at runtime (no baked-in env values),
    satisfying the image-promotion / no-baking requirement.
    """
    try:
        base = _plant_base_url()
    except RuntimeError:
        return []

    try:
        data = await _plant_get_json(
            url=f"{base}/api/v1/hired-agents/by-customer/{customer_id}",
            authorization=authorization,
        )
    except Exception:  # HTTPException, httpx errors, RuntimeError — all swallowed
        return []

    if not isinstance(data, dict):
        return []

    raw_instances = data.get("instances") or []
    if not isinstance(raw_instances, list):
        return []

    now = datetime.now(timezone.utc)
    period_end = (now + timedelta(days=30)).isoformat()
    now_iso = now.isoformat()

    results: list[MyAgentInstanceSummary] = []
    for item in raw_instances:
        if not isinstance(item, dict):
            continue
        sub_id = str(item.get("subscription_id") or "").strip()
        agent_id = str(item.get("agent_id") or "").strip()
        if not sub_id or not agent_id:
            continue
        results.append(
            MyAgentInstanceSummary(
                subscription_id=sub_id,
                agent_id=agent_id,
                duration="monthly",
                status="active",
                current_period_start=now_iso,
                current_period_end=period_end,
                cancel_at_period_end=False,
                hired_instance_id=str(item.get("hired_instance_id") or "").strip() or None,
                agent_type_id=str(item.get("agent_type_id") or "").strip() or None,
                nickname=str(item.get("nickname") or "").strip() or None,
                configured=bool(item["configured"]) if item.get("configured") is not None else None,
                goals_completed=bool(item["goals_completed"]) if item.get("goals_completed") is not None else None,
                trial_status=str(item.get("trial_status") or "").strip() or None,
                trial_start_at=item.get("trial_start_at"),
                trial_end_at=item.get("trial_end_at"),
            )
        )
    return results

async def _enrich_with_hired_agent(
    *,
    base_url: str,
    authorization: str | None,
    customer_id: str,
    instance: MyAgentInstanceSummary,
) -> MyAgentInstanceSummary:
    url = f"{base_url}/api/v1/hired-agents/by-subscription/{instance.subscription_id}"
    try:
        data = await _plant_get_json(url=f"{url}?customer_id={customer_id}", authorization=authorization)
    except HTTPException as exc:
        if exc.status_code in {401, 403, 404, 410}:
            return instance
        raise
    except (httpx.RequestError, RuntimeError):
        return instance

    if not isinstance(data, dict):
        return instance

    def _dt_to_iso(value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    return instance.model_copy(
        update={
            "hired_instance_id": data.get("hired_instance_id"),
            "agent_type_id": data.get("agent_type_id"),
            "nickname": data.get("nickname"),
            "configured": bool(data.get("configured")) if data.get("configured") is not None else None,
            "goals_completed": bool(data.get("goals_completed")) if data.get("goals_completed") is not None else None,
            "trial_status": data.get("trial_status"),
            "trial_start_at": _dt_to_iso(data.get("trial_start_at")),
            "trial_end_at": _dt_to_iso(data.get("trial_end_at")),
            "subscription_status": data.get("subscription_status"),
            "subscription_ended_at": _dt_to_iso(data.get("subscription_ended_at")),
            "retention_expires_at": _dt_to_iso(data.get("retention_expires_at")),
        }
    )

@router.get("/summary", response_model=MyAgentsSummaryResponse)
async def get_my_agents_summary(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> MyAgentsSummaryResponse:
    authorization = request.headers.get("Authorization")

    try:
        base_url = _plant_base_url()
    except RuntimeError:
        base_url = ""

    try:
        instances = await _list_subscriptions(authorization=authorization, customer_id=current_user.id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    # Fallback: if subscriptions store is empty (e.g. in-memory mode / fresh restart),
    # read hired_agents directly from Plant so seeded demo data is always visible.
    if not instances and base_url:
        instances = await _fallback_from_plant_hired_agents(
            authorization=authorization,
            customer_id=current_user.id,
        )

    if not base_url or not instances:
        return MyAgentsSummaryResponse(instances=instances)

    async def _enrich(one: MyAgentInstanceSummary) -> MyAgentInstanceSummary:
        return await _enrich_with_hired_agent(
            base_url=base_url,
            authorization=authorization,
            customer_id=current_user.id,
            instance=one,
        )

    enriched = await asyncio.gather(*[_enrich(x) for x in instances], return_exceptions=False)
    return MyAgentsSummaryResponse(instances=list(enriched))
