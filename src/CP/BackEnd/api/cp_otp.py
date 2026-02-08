"""CP OTP routes.

REG-1.4:
- POST /api/cp/auth/otp/start issues an OTP for a registration_id.
- POST /api/cp/auth/otp/verify verifies OTP and returns CP JWT tokens.

In non-production environments, `/start` returns the OTP code for demo/testing.
Production must integrate a real delivery provider.
"""

from __future__ import annotations

import os
from typing import Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.auth.user_store import UserStore, get_user_store
from core.jwt_handler import create_tokens
from models.user import Token, UserCreate
from services.cp_otp import FileCPOtpStore, get_cp_otp_store
from services.cp_registrations import FileCPRegistrationStore, get_cp_registration_store


router = APIRouter(prefix="/cp/auth/otp", tags=["cp-auth"])


async def _upsert_customer_in_plant(record) -> None:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "http://localhost:8000").rstrip("/")
    registration_key = (os.getenv("CP_REGISTRATION_KEY") or "").strip()

    if not registration_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CP_REGISTRATION_KEY not configured",
        )

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

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{base_url}/api/v1/customers",
            json=payload,
            headers={"X-CP-Registration-Key": registration_key},
        )

    if resp.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to persist customer in Plant ({resp.status_code})",
        )


def _is_production() -> bool:
    env = (os.getenv("ENVIRONMENT") or "").strip().lower()
    return env in {"prod", "production"}


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

    if not otp_store.can_issue(destination=destination):
        raise HTTPException(status_code=429, detail="Too many OTP requests. Please wait and try again.")

    event, code = otp_store.create_challenge(
        registration_id=record.registration_id,
        channel=channel,  # type: ignore[arg-type]
        destination=destination,
        ttl_seconds=300,
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

    if not otp_store.can_issue(destination=destination):
        raise HTTPException(status_code=429, detail="Too many OTP requests. Please wait and try again.")

    event, code = otp_store.create_challenge(
        registration_id=record.registration_id,
        channel=channel,  # type: ignore[arg-type]
        destination=destination,
        ttl_seconds=300,
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
