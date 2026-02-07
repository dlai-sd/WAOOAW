from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.auth.dependencies import get_current_user
from api.payments_config import _get_payments_mode
from models.user import User


router = APIRouter(prefix="/cp/payments/coupon", tags=["cp-payments"])


class CouponCheckoutRequest(BaseModel):
    coupon_code: str = Field(..., min_length=1)
    agent_id: str = Field(..., min_length=1)
    duration: str = Field(..., min_length=1, description="e.g. monthly, quarterly")


PaymentProvider = Literal["coupon"]


class CouponCheckoutResponse(BaseModel):
    order_id: str
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


@router.post("/checkout", response_model=CouponCheckoutResponse)
async def coupon_checkout(
    body: CouponCheckoutRequest,
    current_user: User = Depends(get_current_user),
) -> CouponCheckoutResponse:
    _ = current_user  # required for auth; future: tie order/subscription to customer

    _require_coupon_mode()
    coupon_code = _require_valid_coupon(body.coupon_code)

    # NOTE: This is intentionally a lightweight stub in CP.
    # Plant will become the source-of-truth for subscriptions/orders as HIRE-2.1+ land.
    import uuid

    order_id = f"ORDER-{uuid.uuid4()}"

    return CouponCheckoutResponse(
        order_id=order_id,
        coupon_code=coupon_code,
        agent_id=body.agent_id,
        duration=body.duration,
    )
