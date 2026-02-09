from __future__ import annotations

from typing import Literal, Optional

import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.auth.dependencies import get_current_user
from api.payments_config import _get_payments_mode
from models.user import User
from services.cp_subscriptions_simple import create_subscription_for_user


router = APIRouter(prefix="/cp/payments/coupon", tags=["cp-payments"])


def _bool_env(name: str, default: str = "false") -> bool:
    return (os.getenv(name) or default).strip().lower() in {"1", "true", "yes", "on"}


class CouponCheckoutRequest(BaseModel):
    coupon_code: str = Field(..., min_length=1)
    agent_id: str = Field(..., min_length=1)
    duration: str = Field(..., min_length=1, description="e.g. monthly, quarterly")


PaymentProvider = Literal["coupon"]


class CouponCheckoutResponse(BaseModel):
    order_id: str
    subscription_id: str | None = None
    payment_provider: PaymentProvider = "coupon"
    amount: int = 0
    currency: str = "INR"

    coupon_code: str
    agent_id: str
    duration: str

    subscription_status: str = "active"
    trial_status: str = "not_started"


def _require_coupon_mode() -> None:
    mode = _get_payments_mode()
    if mode != "coupon":
        raise HTTPException(status_code=403, detail="Coupon checkout is disabled when PAYMENTS_MODE is not 'coupon'.")


def _require_valid_coupon(code: str) -> str:
    normalized = (code or "").strip()
    if normalized != "WAOOAW100":
        raise HTTPException(status_code=400, detail="Invalid coupon code.")
    return normalized


async def _coupon_checkout_in_plant(
    *,
    coupon_code: str,
    agent_id: str,
    duration: str,
    customer_id: str | None,
    authorization: str | None,
    idempotency_key: str | None,
) -> dict:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base_url:
        raise RuntimeError("PLANT_GATEWAY_URL not configured")

    payload = {
        "coupon_code": coupon_code,
        "agent_id": agent_id,
        "duration": duration,
        "customer_id": customer_id,
    }

    headers: dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{base_url}/api/v1/payments/coupon/checkout",
            json=payload,
            headers=headers,
        )

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=f"Plant coupon checkout failed ({resp.status_code})")

    return resp.json()


@router.post("/checkout", response_model=CouponCheckoutResponse)
async def coupon_checkout(
    body: CouponCheckoutRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> CouponCheckoutResponse:
    # required for auth; tie order/subscription to customer once Plant customer_id is available in CP tokens.
    _ = current_user

    _require_coupon_mode()
    coupon_code = _require_valid_coupon(body.coupon_code)

    plant_customer_id = current_user.id
    authorization = request.headers.get("Authorization")
    idempotency_key = request.headers.get("Idempotency-Key")

    if _bool_env("CP_PAYMENTS_USE_PLANT", "false"):
        try:
            plant = await _coupon_checkout_in_plant(
                coupon_code=coupon_code,
                agent_id=body.agent_id,
                duration=body.duration,
                customer_id=plant_customer_id,
                authorization=authorization,
                idempotency_key=idempotency_key,
            )

            return CouponCheckoutResponse(
                order_id=plant["order_id"],
                subscription_id=plant.get("subscription_id"),
                coupon_code=coupon_code,
                agent_id=body.agent_id,
                duration=body.duration,
            )
        except RuntimeError:
            pass

    # Fallback stub (default) to keep CP independent.
    import uuid

    order_id = f"ORDER-{uuid.uuid4()}"
    subscription_id = f"SUB-{uuid.uuid4()}"

    create_subscription_for_user(
        subscription_id=subscription_id,
        owner_user_id=current_user.id,
        agent_id=body.agent_id,
        duration=body.duration,
    )

    return CouponCheckoutResponse(
        order_id=order_id,
        subscription_id=subscription_id,
        coupon_code=coupon_code,
        agent_id=body.agent_id,
        duration=body.duration,
    )
