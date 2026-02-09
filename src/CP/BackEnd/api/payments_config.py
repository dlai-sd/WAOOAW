from __future__ import annotations

import os
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/cp/payments", tags=["cp-payments"])


PaymentsMode = Literal["razorpay", "coupon"]


class PaymentsConfigResponse(BaseModel):
    mode: PaymentsMode
    coupon_code: Optional[str] = None
    coupon_unlimited: Optional[bool] = None


def _normalize_environment(raw: str) -> str:
    return (raw or "").strip().lower()


def _default_mode_for_environment(environment: str) -> PaymentsMode:
    if environment in {"prod", "production"}:
        return "razorpay"
    return "coupon"


def _get_payments_mode() -> PaymentsMode:
    environment = _normalize_environment(os.getenv("ENVIRONMENT", "development"))
    raw_mode = (os.getenv("PAYMENTS_MODE") or "").strip().lower()

    if not raw_mode:
        mode: PaymentsMode = _default_mode_for_environment(environment)
    elif raw_mode in {"razorpay", "coupon"}:
        mode = raw_mode  # type: ignore[assignment]
    else:
        raise HTTPException(status_code=500, detail="Invalid PAYMENTS_MODE; expected 'razorpay' or 'coupon'.")

    if environment in {"prod", "production"} and mode == "coupon":
        raise HTTPException(status_code=500, detail="PAYMENTS_MODE=coupon is not allowed in production.")

    return mode


@router.get("/config", response_model=PaymentsConfigResponse)
async def get_payments_config() -> PaymentsConfigResponse:
    """Return the single source-of-truth for payment flow selection."""
    mode = _get_payments_mode()

    if mode == "coupon":
        return PaymentsConfigResponse(mode=mode, coupon_code="WAOOAW100", coupon_unlimited=True)

    return PaymentsConfigResponse(mode=mode)
