from __future__ import annotations

import os
from typing import Any, Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.auth.dependencies import get_current_user
from api.payments_config import _get_payments_mode
from models.user import User


router = APIRouter(prefix="/cp/payments/razorpay", tags=["cp-payments"])


PaymentProvider = Literal["razorpay"]


class RazorpayOrderCreateRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    duration: str = Field(..., min_length=1)


class RazorpayOrderCreateResponse(BaseModel):
    order_id: str
    subscription_id: str

    payment_provider: PaymentProvider = "razorpay"
    currency: str = "INR"
    amount: int

    razorpay_key_id: str
    razorpay_order_id: str


class RazorpayConfirmRequest(BaseModel):
    order_id: str = Field(..., min_length=1)
    razorpay_order_id: str = Field(..., min_length=1)
    razorpay_payment_id: str = Field(..., min_length=1)
    razorpay_signature: str = Field(..., min_length=1)


class RazorpayConfirmResponse(BaseModel):
    order_id: str
    subscription_id: str
    payment_provider: PaymentProvider = "razorpay"
    subscription_status: str


def _bool_env(name: str, default: str = "false") -> bool:
    return (os.getenv(name) or default).strip().lower() in {"1", "true", "yes", "on"}


def _require_razorpay_mode() -> None:
    mode = _get_payments_mode()
    if mode != "razorpay":
        raise HTTPException(status_code=403, detail="Razorpay checkout is disabled when PAYMENTS_MODE is not 'razorpay'.")


async def _razorpay_order_in_plant(
    *,
    agent_id: str,
    duration: str,
    customer_id: str,
    authorization: str | None,
) -> dict[str, Any]:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base_url:
        raise RuntimeError("PLANT_GATEWAY_URL not configured")

    payload = {
        "agent_id": agent_id,
        "duration": duration,
        "customer_id": customer_id,
    }

    headers: dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(f"{base_url}/api/v1/payments/razorpay/order", json=payload, headers=headers)

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=f"Plant Razorpay order create failed ({resp.status_code})")

    data = resp.json()
    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="Plant Razorpay order create returned invalid response")

    return data


async def _razorpay_confirm_in_plant(
    *,
    order_id: str,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    customer_id: str,
    authorization: str | None,
) -> dict[str, Any]:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base_url:
        raise RuntimeError("PLANT_GATEWAY_URL not configured")

    payload = {
        "order_id": order_id,
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_signature": razorpay_signature,
        "customer_id": customer_id,
    }

    headers: dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(f"{base_url}/api/v1/payments/razorpay/confirm", json=payload, headers=headers)

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=f"Plant Razorpay confirm failed ({resp.status_code})")

    data = resp.json()
    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="Plant Razorpay confirm returned invalid response")

    return data


@router.post("/order", response_model=RazorpayOrderCreateResponse)
async def razorpay_order_create(
    body: RazorpayOrderCreateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> RazorpayOrderCreateResponse:
    _require_razorpay_mode()

    authorization = request.headers.get("Authorization")

    if _bool_env("CP_PAYMENTS_USE_PLANT", "true"):
        plant = await _razorpay_order_in_plant(
            agent_id=body.agent_id,
            duration=body.duration,
            customer_id=current_user.id,
            authorization=authorization,
        )

        return RazorpayOrderCreateResponse(
            order_id=plant["order_id"],
            subscription_id=plant["subscription_id"],
            amount=int(plant["amount"]),
            currency=str(plant.get("currency") or "INR"),
            razorpay_key_id=str(plant["razorpay_key_id"]),
            razorpay_order_id=str(plant["razorpay_order_id"]),
        )

    raise HTTPException(status_code=501, detail="Razorpay checkout requires CP_PAYMENTS_USE_PLANT=true")


@router.post("/confirm", response_model=RazorpayConfirmResponse)
async def razorpay_confirm(
    body: RazorpayConfirmRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> RazorpayConfirmResponse:
    _require_razorpay_mode()

    authorization = request.headers.get("Authorization")

    if _bool_env("CP_PAYMENTS_USE_PLANT", "true"):
        plant = await _razorpay_confirm_in_plant(
            order_id=body.order_id,
            razorpay_order_id=body.razorpay_order_id,
            razorpay_payment_id=body.razorpay_payment_id,
            razorpay_signature=body.razorpay_signature,
            customer_id=current_user.id,
            authorization=authorization,
        )

        return RazorpayConfirmResponse(
            order_id=str(plant["order_id"]),
            subscription_id=str(plant["subscription_id"]),
            subscription_status=str(plant.get("subscription_status") or "active"),
        )

    raise HTTPException(status_code=501, detail="Razorpay checkout requires CP_PAYMENTS_USE_PLANT=true")
