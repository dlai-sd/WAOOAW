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


router = APIRouter(prefix="/cp/auth/otp", tags=["cp-auth"])

logger = logging.getLogger(__name__)


async def _get_customer_from_plant(*, customer_id: str | None = None, email: str | None = None, phone: str | None = None) -> dict | None:
    """Fetch customer from Plant using either customer_id or email/phone lookup."""
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "http://localhost:8000").rstrip("/")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if customer_id:
                # Direct lookup by customer_id not available in Plant API,
                # so we can't support fetching by ID. This is OK since registration_id 
                # is the customer_id, and OTP flow is initiated from registration.
                # For now, return None if only ID provided.
                return None
            elif email:
                resp = await client.get(
                    f"{base_url}/api/v1/customers/lookup",
                    params={"email": email},
                )
            elif phone:
                # Plant API doesn't have phone lookup, need to use email
                # For login with phone, we'll need a different approach
                # For now, this is a limitation
                return None
            else:
                return None
                
            if resp.status_code == 404:
                return None
            if resp.status_code >= 400:
                logger.error(f"Plant customer lookup failed: {resp.status_code}")
                return None
                
            return resp.json()
    except Exception as exc:
        logger.error(f"Failed to fetch customer from Plant: {exc}")
        return None


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


def _is_production() -> bool:
    env = (os.getenv("ENVIRONMENT") or "").strip().lower()
    # Demo is intentionally treated as non-production:
    # it should be resilient to missing infra (e.g., Plant persistence) while still
    # allowing end-to-end signup/login flows for evaluation.
    return env in {"prod", "production", "uat"}


def _otp_delivery_mode() -> str:
    """Return OTP delivery mode.

    Modes:
    - provider: attempt delivery via configured provider
    - disabled: skip delivery (demo/dev)

    Defaults:
    - demo => disabled
    - uat/prod/production => provider
    - everything else => disabled
    """

    mode = (os.getenv("OTP_DELIVERY_MODE") or "").strip().lower()
    if mode in {"provider", "disabled"}:
        return mode

    env = (os.getenv("ENVIRONMENT") or "").strip().lower()
    if env in {"uat", "prod", "production"}:
        return "provider"
    # demo + dev defaults to disabled (dev-friendly echo).
    return "disabled"


def _otp_delivery_enabled() -> bool:
    return _otp_delivery_mode() == "provider"


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
    if not _otp_delivery_enabled():
        return
    try:
        await deliver_otp(channel=channel, destination=destination, code=code, ttl_seconds=ttl_seconds)  # type: ignore[arg-type]
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


class OtpStartRequest(BaseModel):
    registration_id: str | None = None
    email: str | None = None
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
    otp_store: FileCPOtpStore = Depends(get_cp_otp_store),
) -> OtpStartResponse:
    """Start OTP flow for registration.
    
    CP now proxies registration to Plant, so customer data is fetched from Plant.
    Use email to lookup customer since Plant exposes email-based lookup.
    registration_id can still be provided for backward compatibility but email is preferred.
    """
    # Determine email from either registration_id or direct email input
    email = None
    registration_id = payload.registration_id
    
    if payload.email:
        email = payload.email.strip().lower()
        # If email provided without registration_id, use it for lookup
        if not registration_id:
            registration_id = email  # We'll store email as a placeholder
    else:
        # Legacy: registration_id was customer_id from Plant
        # We can't look it up without email, so we need email to proceed
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email is required for OTP flow",
        )
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email is required",
        )
    
    # Fetch customer from Plant to get full details
    customer = await _get_customer_from_plant(email=email)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found. Please register first.",
        )
    
    # Use customer_id as registration_id if not provided
    registration_id = registration_id or customer.get("customer_id", email)
    
    channel = payload.channel or customer.get("preferred_contact_method", "email")
    if channel not in {"email", "phone"}:
        channel = "email"
    
    destination = customer.get("email") if channel == "email" else customer.get("phone")
    if not destination:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No {channel} on file for customer",
        )

    if not otp_store.can_issue(destination=destination):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many OTP requests. Please wait and try again.",
        )

    event, code = otp_store.create_challenge(
        registration_id=registration_id,
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
            "registration_id": registration_id,
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
        otp_code=None if _otp_delivery_enabled() else code,
    )


@router.post("/login/start", response_model=OtpStartResponse)
async def start_login_otp(
    payload: OtpLoginStartRequest,
    otp_store: FileCPOtpStore = Depends(get_cp_otp_store),
) -> OtpStartResponse:
    """Start OTP flow for login."""
    email = (payload.email or "").strip().lower() or None
    phone = (payload.phone or "").strip() or None

    if not email and not phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email or phone is required",
        )
    
    # Fetch from Plant by email (preferred) or require email for lookup
    customer = None
    if email:
        customer = await _get_customer_from_plant(email=email)
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    
    registration_id = customer.get("customer_id", email or phone)
    channel = payload.channel or customer.get("preferred_contact_method", "email")
    if channel not in {"email", "phone"}:
        channel = "email"
    
    destination = customer.get("email") if channel == "email" else customer.get("phone")
    if not destination:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No {channel} on file for customer",
        )

    if not otp_store.can_issue(destination=destination):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many OTP requests. Please wait and try again.")

    event, code = otp_store.create_challenge(
        registration_id=registration_id,
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
            "registration_id": registration_id,
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
        otp_code=None if _otp_delivery_enabled() else code,
    )


class OtpVerifyRequest(BaseModel):
    otp_id: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)


@router.post("/verify", response_model=Token)
async def verify_otp(
    payload: OtpVerifyRequest,
    otp_store: FileCPOtpStore = Depends(get_cp_otp_store),
    user_store: UserStore = Depends(get_user_store),
) -> Token:
    """Verify OTP and create CP user for authenticated access."""
    ok, reason = otp_store.verify(otp_id=payload.otp_id, code=payload.code)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)

    state = otp_store.get_state(payload.otp_id)
    if not state:
        raise HTTPException(status_code=404, detail="OTP not found")

    # For registration flows, destination is email. Fetch full customer data from Plant.
    customer = None
    if state.channel == "email":
        customer = await _get_customer_from_plant(email=state.destination)
    
    if not customer:
        logger.warning(f"Could not fetch customer from Plant for {state.destination}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to retrieve customer information",
        )

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

    # Create CP user (local auth store for JWT management)
    # registration_id is the customer_id from Plant
    user = user_store.get_or_create_user(
        UserCreate(
            provider="otp",
            provider_id=state.registration_id,
            email=customer.get("email", state.destination),
            name=customer.get("full_name", ""),
            picture=None,
        )
    )

    tokens = create_tokens(user_id=user.id, email=user.email)
    return Token(**tokens)
