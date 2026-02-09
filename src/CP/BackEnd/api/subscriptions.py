from __future__ import annotations

import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from api.auth.dependencies import get_current_user
from models.user import User
from services.cp_subscriptions_simple import (
    CPSubscriptionRecord,
    cancel_for_user,
    get_for_user,
    list_for_user,
)


router = APIRouter(prefix="/cp/subscriptions", tags=["cp-subscriptions"])


def _bool_env(name: str, default: str = "false") -> bool:
    return (os.getenv(name) or default).strip().lower() in {"1", "true", "yes", "on"}


class SubscriptionResponse(BaseModel):
    subscription_id: str
    agent_id: str
    duration: str
    status: str
    current_period_start: str
    current_period_end: str
    cancel_at_period_end: bool


def _to_response(record: CPSubscriptionRecord) -> SubscriptionResponse:
    return SubscriptionResponse(
        subscription_id=record.subscription_id,
        agent_id=record.agent_id,
        duration=record.duration,
        status=record.status,
        current_period_start=record.current_period_start.isoformat(),
        current_period_end=record.current_period_end.isoformat(),
        cancel_at_period_end=bool(record.cancel_at_period_end),
    )


async def _plant_get_json(*, url: str, authorization: str | None) -> dict | list:
    headers: dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
    except httpx.RequestError as exc:
        raise RuntimeError(f"Plant call failed (network): {exc}")

    # 4xx means caller error (authz, not found) -> surface.
    if 400 <= resp.status_code < 500:
        raise HTTPException(status_code=resp.status_code, detail=f"Plant call failed ({resp.status_code})")
    # 5xx means Plant unavailable -> allow CP-local fallback.
    if resp.status_code >= 500:
        raise RuntimeError(f"Plant call failed ({resp.status_code})")

    return resp.json()


async def _plant_post_json(*, url: str, authorization: str | None, params: dict | None = None) -> dict:
    headers: dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, params=params)
    except httpx.RequestError as exc:
        raise RuntimeError(f"Plant call failed (network): {exc}")

    if 400 <= resp.status_code < 500:
        raise HTTPException(status_code=resp.status_code, detail=f"Plant call failed ({resp.status_code})")
    if resp.status_code >= 500:
        raise RuntimeError(f"Plant call failed ({resp.status_code})")

    return resp.json()


def _plant_base_url() -> str:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base_url:
        raise RuntimeError("PLANT_GATEWAY_URL not configured")
    return base_url


@router.get("/", response_model=list[SubscriptionResponse])
async def list_subscriptions(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> list[SubscriptionResponse]:
    authorization = request.headers.get("Authorization")

    if _bool_env("CP_SUBSCRIPTIONS_USE_PLANT", "false"):
        try:
            base = _plant_base_url()
            data = await _plant_get_json(
                url=f"{base}/api/v1/payments/subscriptions/by-customer/{current_user.id}",
                authorization=authorization,
            )
            # Plant already returns a safe JSON payload; normalize to our response shape.
            return [
                SubscriptionResponse(
                    subscription_id=item["subscription_id"],
                    agent_id=item["agent_id"],
                    duration=item["duration"],
                    status=item["status"],
                    current_period_start=item["current_period_start"],
                    current_period_end=item["current_period_end"],
                    cancel_at_period_end=bool(item.get("cancel_at_period_end")),
                )
                for item in (data or [])
                if isinstance(item, dict)
            ]
        except RuntimeError:
            pass

    return [_to_response(r) for r in list_for_user(current_user.id)]


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> SubscriptionResponse:
    authorization = request.headers.get("Authorization")

    if _bool_env("CP_SUBSCRIPTIONS_USE_PLANT", "false"):
        try:
            base = _plant_base_url()
            item = await _plant_get_json(
                url=f"{base}/api/v1/payments/subscriptions/{subscription_id}",
                authorization=authorization,
            )
            if not isinstance(item, dict):
                raise HTTPException(status_code=502, detail="Unexpected Plant response")
            # Phase-1 authz: require customer_id match when present.
            if item.get("customer_id") and str(item.get("customer_id")) != current_user.id:
                raise HTTPException(status_code=403, detail="Subscription does not belong to user")
            return SubscriptionResponse(
                subscription_id=item["subscription_id"],
                agent_id=item["agent_id"],
                duration=item["duration"],
                status=item["status"],
                current_period_start=item["current_period_start"],
                current_period_end=item["current_period_end"],
                cancel_at_period_end=bool(item.get("cancel_at_period_end")),
            )
        except RuntimeError:
            pass

    return _to_response(get_for_user(subscription_id=subscription_id, owner_user_id=current_user.id))


@router.post("/{subscription_id}/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    subscription_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> SubscriptionResponse:
    authorization = request.headers.get("Authorization")

    if _bool_env("CP_SUBSCRIPTIONS_USE_PLANT", "false"):
        try:
            base = _plant_base_url()
            item = await _plant_post_json(
                url=f"{base}/api/v1/payments/subscriptions/{subscription_id}/cancel",
                authorization=authorization,
                params={"customer_id": current_user.id},
            )
            if not isinstance(item, dict):
                raise HTTPException(status_code=502, detail="Unexpected Plant response")
            if item.get("customer_id") and str(item.get("customer_id")) != current_user.id:
                raise HTTPException(status_code=403, detail="Subscription does not belong to user")
            return SubscriptionResponse(
                subscription_id=item["subscription_id"],
                agent_id=item["agent_id"],
                duration=item["duration"],
                status=item["status"],
                current_period_start=item["current_period_start"],
                current_period_end=item["current_period_end"],
                cancel_at_period_end=bool(item.get("cancel_at_period_end")),
            )
        except RuntimeError:
            pass

    return _to_response(cancel_for_user(subscription_id=subscription_id, owner_user_id=current_user.id))
