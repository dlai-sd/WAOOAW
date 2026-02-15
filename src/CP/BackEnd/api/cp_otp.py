"""CP OTP routes.

REG-1.4:
- POST /api/cp/auth/otp/start issues an OTP for a registration_id.
- POST /api/cp/auth/otp/verify verifies OTP and returns CP JWT tokens.

In non-production environments, `/start` returns the OTP code for demo/testing.
Production must integrate a real delivery provider.
"""

from __future__ import annotations

import logging
import os
from typing import Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.auth.user_store import UserStore, get_user_store
from core.jwt_handler import create_tokens
from models.user import Token, UserCreate
from services.cp_otp import FileCPOtpStore, get_cp_otp_store
from services.cp_otp_delivery import deliver_otp
from services.cp_registrations import FileCPRegistrationStore, get_cp_registration_store


router = APIRouter(prefix="/cp/auth/otp", tags=["cp-auth"])

logger = logging.getLogger(__name__)


async def _emit_notification_event_best_effort(*, event_type: str, metadata: dict) -> None:
    """Best-effort notification event emission.

    NOTIF-1.1 gap-closure: record OTP events (sent/verified) in Plant's event store.
    This must never block registration/login flows.
    """

    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    registration_key = (os.getenv("CP_REGISTRATION_KEY") or "").strip()
    if not base_url or not registration_key:
        return

    payload = {"event_type": str(event_type), "metadata": dict(metadata or {})}
    headers = {"X-CP-Registration-Key": registration_key}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(f"{base_url}/api/v1/notifications/events", json=payload, headers=headers)
    except Exception:
        return


async def _upsert_customer_in_plant(record) -> None:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "http://localhost:8000").rstrip("/")
    registration_key = (os.getenv("CP_REGISTRATION_KEY") or "").strip()

    if not registration_key:
        # Production must be strict: without the key we can't persist the customer in Plant.
        if _is_production():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="CP_REGISTRATION_KEY not configured",
            )

        # Dev/test should not be blocked by infra/config gaps.
        logger.warning("CP_REGISTRATION_KEY not configured; skipping Plant customer upsert")
        return

    payload = {
        "fullName": record.full_name,
        "businessName": record.business_name,
        "businessIndustry": record.business_industry,
        "businessAddress": record.business_address,
        "email": record.email,
        "phone": record.phone,
        "website": record.website,
        "gstNumber": record.gst_number,
        "preferredContactMethod": record.preferred_contact_method,
        "consent": record.consent,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{base_url}/api/v1/customers",
                json=payload,
                headers={"X-CP-Registration-Key": registration_key},
            )
    except Exception as exc:
        if _is_production():
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to persist customer in Plant (network error)",
            ) from exc
        logger.warning("Plant customer upsert failed (network error); continuing", exc_info=True)
        return

    if resp.status_code >= 400:
        if _is_production():
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to persist customer in Plant ({resp.status_code})",
            )
        logger.warning(
            "Plant customer upsert failed (%s); continuing in non-production",
            resp.status_code,
        )
        return


def _is_production() -> bool:
    env = (os.getenv("ENVIRONMENT") or "").strip().lower()
    return env in {"prod", "production", "uat", "demo"}


def _mask_destination(destination: str) -> str:
    value = destination.strip()
    if "@" in value:
        name, domain = value.split("@", 1)
        if len(name) <= 2:
            return f"**@{domain}"
        return f"{name[0]}***{name[-1]}@{domain}"
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}***{value[-2:]}"


async def _deliver_otp_in_production(*, channel: str, destination: str, code: str, ttl_seconds: int) -> None:
    if not _is_production():
        return
    try:
        await deliver_otp(channel=channel, destination=destination, code=code, ttl_seconds=ttl_seconds)  # type: ignore[arg-type]
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


class OtpStartRequest(BaseModel):
    registration_id: str = Field(..., min_length=1)
    channel: Literal["email", "phone"] | None = None


class OtpLoginStartRequest(BaseModel):
    email: str | None = None
    phone: str | None = None
    channel: Literal["email", "phone"] | None = None


class OtpStartResponse(BaseModel):
    otp_id: str = Field(..., min_length=1)
    channel: Literal["email", "phone"]
    destination_masked: str
    expires_in_seconds: int
    otp_code: str | None = None


@router.post("/start", response_model=OtpStartResponse)
async def start_otp(
    payload: OtpStartRequest,
    registrations: FileCPRegistrationStore = Depends(get_cp_registration_store),
    otp_store: FileCPOtpStore = Depends(get_cp_otp_store),
) -> OtpStartResponse:
    record = registrations.get_by_id(payload.registration_id)
    if not record:
        raise HTTPException(status_code=404, detail="registration_id not found")

    channel = payload.channel or (record.preferred_contact_method if record.preferred_contact_method in {"email", "phone"} else "email")
    destination = record.email if channel == "email" else record.phone

    if not destination:
        raise HTTPException(status_code=400, detail=f"No destination available for channel: {channel}")

    if not otp_store.can_issue(destination=destination):
        raise HTTPException(status_code=429, detail="Too many OTP requests. Please wait and try again.")

    event, code = otp_store.create_challenge(
        registration_id=record.registration_id,
        channel=channel,  # type: ignore[arg-type]
        destination=destination,
        ttl_seconds=300,
    )

    await _deliver_otp_in_production(
        channel=channel,
        destination=destination,
        code=code,
        ttl_seconds=300,
    )

    await _emit_notification_event_best_effort(
        event_type="otp_sent",
        metadata={
            "otp_id": event.otp_id,
            "registration_id": record.registration_id,
            "channel": channel,
            "to_email": destination if channel == "email" else None,
            "to_phone": destination if channel == "phone" else None,
            "destination_masked": _mask_destination(destination),
            "expires_in_seconds": 300,
            "flow": "registration",
        },
    )

    return OtpStartResponse(
        otp_id=event.otp_id,
        channel=channel,  # type: ignore[arg-type]
        destination_masked=_mask_destination(destination),
        expires_in_seconds=300,
        otp_code=None if _is_production() else code,
    )


@router.post("/login/start", response_model=OtpStartResponse)
async def start_login_otp(
    payload: OtpLoginStartRequest,
    registrations: FileCPRegistrationStore = Depends(get_cp_registration_store),
    otp_store: FileCPOtpStore = Depends(get_cp_otp_store),
) -> OtpStartResponse:
    email = (payload.email or "").strip().lower() or None
    phone = (payload.phone or "").strip() or None

    if not email and not phone:
        raise HTTPException(status_code=400, detail="email or phone is required")

    record = registrations.get_by_email(email) if email else registrations.get_by_phone(phone)  # type: ignore[arg-type]
    if not record:
        raise HTTPException(status_code=404, detail="Account not found")

    channel = payload.channel or (
        record.preferred_contact_method
        if record.preferred_contact_method in {"email", "phone"}
        else "email"
    )
    destination = record.email if channel == "email" else record.phone

    if not destination:
        raise HTTPException(status_code=400, detail=f"No destination available for channel: {channel}")

    if not otp_store.can_issue(destination=destination):
        raise HTTPException(status_code=429, detail="Too many OTP requests. Please wait and try again.")

    event, code = otp_store.create_challenge(
        registration_id=record.registration_id,
        channel=channel,  # type: ignore[arg-type]
        destination=destination,
        ttl_seconds=300,
    )

    await _deliver_otp_in_production(
        channel=channel,
        destination=destination,
        code=code,
        ttl_seconds=300,
    )

    await _emit_notification_event_best_effort(
        event_type="otp_sent",
        metadata={
            "otp_id": event.otp_id,
            "registration_id": record.registration_id,
            "channel": channel,
            "to_email": destination if channel == "email" else None,
            "to_phone": destination if channel == "phone" else None,
            "destination_masked": _mask_destination(destination),
            "expires_in_seconds": 300,
            "flow": "login",
        },
    )

    return OtpStartResponse(
        otp_id=event.otp_id,
        channel=channel,  # type: ignore[arg-type]
        destination_masked=_mask_destination(destination),
        expires_in_seconds=300,
        otp_code=None if _is_production() else code,
    )


class OtpVerifyRequest(BaseModel):
    otp_id: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)


@router.post("/verify", response_model=Token)
async def verify_otp(
    payload: OtpVerifyRequest,
    registrations: FileCPRegistrationStore = Depends(get_cp_registration_store),
    otp_store: FileCPOtpStore = Depends(get_cp_otp_store),
    user_store: UserStore = Depends(get_user_store),
) -> Token:
    ok, reason = otp_store.verify(otp_id=payload.otp_id, code=payload.code)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)

    state = otp_store.get_state(payload.otp_id)
    if not state:
        raise HTTPException(status_code=404, detail="OTP not found")

    record = registrations.get_by_id(state.registration_id)
    if not record:
        raise HTTPException(status_code=404, detail="registration_id not found")

    await _emit_notification_event_best_effort(
        event_type="otp_verified",
        metadata={
            "otp_id": state.otp_id,
            "registration_id": state.registration_id,
            "channel": state.channel,
            "to_email": state.destination if state.channel == "email" else None,
            "to_phone": state.destination if state.channel == "phone" else None,
            "destination_masked": _mask_destination(state.destination),
        },
    )

    await _upsert_customer_in_plant(record)

    user = user_store.get_or_create_user(
        UserCreate(
            provider="otp",
            provider_id=record.registration_id,
            email=record.email,
            name=record.full_name,
            picture=None,
        )
    )

    tokens = create_tokens(user_id=user.id, email=user.email)
    return Token(**tokens)
