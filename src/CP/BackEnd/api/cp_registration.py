"""CP registration routes.

REG-1.3: POST /api/cp/auth/register validates and normalizes registration input,
then proxies to Plant's customer upsert endpoint.

Validation happens here (CAPTCHA, format), but persistence is handled by Plant.
This ensures CP remains a pure stateless proxy with no local data storage.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Literal

import httpx
import phonenumbers
from fastapi import Depends, HTTPException, Request, status
from core.routing import waooaw_router  # P-3
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from pydantic import model_validator

from api.auth.user_store import UserStore, get_user_store
from core.jwt_handler import create_tokens
from models.user import UserCreate
from services.plant_client import PlantClient, ServiceUnavailableError
from services.audit_dependency import AuditLogger, get_audit_logger  # C2 (NFR It-2)

router = waooaw_router(prefix="/cp/auth", tags=["cp-auth"])

logger = logging.getLogger(__name__)

_GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")

def _is_production() -> bool:
    env = (os.getenv("ENVIRONMENT") or "").strip().lower()
    return env in {"prod", "production", "uat", "demo"}

async def _verify_turnstile_token(*, token: str, remote_ip: str | None) -> None:
    secret = (os.getenv("TURNSTILE_SECRET_KEY") or "").strip()
    if not secret:
        if _is_production():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="TURNSTILE_SECRET_KEY not configured",
            )
        logger.warning("TURNSTILE_SECRET_KEY not configured; skipping CAPTCHA verification")
        return

    data: dict[str, str] = {"secret": secret, "response": token}
    if remote_ip:
        data["remoteip"] = remote_ip

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data=data,
            )
    except Exception as exc:
        if _is_production():
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="CAPTCHA verification failed (network error)",
            ) from exc
        logger.warning("CAPTCHA verification failed (network error); continuing", exc_info=True)
        return

    if resp.status_code != 200:
        if _is_production():
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="CAPTCHA verification failed (provider error)",
            )
        logger.warning("CAPTCHA verification failed (provider error %s); continuing", resp.status_code)
        return

    body = resp.json() if resp.content else {}
    if not body.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CAPTCHA verification failed")

def _normalize_phone(value: str) -> str:
    # Remove common separators to keep a stable representation.
    return re.sub(r"[\s\-()]+", "", value.strip())

def _canonicalize_phone_e164(
    *,
    raw_phone: str,
    region: str,
    enforce_region: bool,
    desired_region: str | None,
) -> str:
    try:
        phone_obj = phonenumbers.parse(raw_phone, region)
    except phonenumbers.NumberParseException as exc:
        raise ValueError("Invalid phone format") from exc

    if not phonenumbers.is_possible_number(phone_obj):
        raise ValueError("Invalid phone format")

    if enforce_region:
        region_upper = (desired_region or region or "").strip().upper() or "IN"
        if raw_phone.startswith("+"):
            actual_region = (phonenumbers.region_code_for_number(phone_obj) or "").strip().upper()
            if actual_region and actual_region != region_upper:
                raise ValueError("Invalid phone format")
            if not phonenumbers.is_valid_number(phone_obj):
                raise ValueError("Invalid phone format")
        else:
            if not phonenumbers.is_valid_number_for_region(phone_obj, region_upper):
                raise ValueError("Invalid phone format")
    else:
        if not phonenumbers.is_valid_number(phone_obj):
            raise ValueError("Invalid phone format")

    return phonenumbers.format_number(phone_obj, phonenumbers.PhoneNumberFormat.E164)

class RegistrationCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    full_name: str = Field(..., alias="fullName", min_length=1)
    business_name: str = Field(..., alias="businessName", min_length=1)
    business_industry: str = Field(..., alias="businessIndustry", min_length=1)
    business_address: str = Field(..., alias="businessAddress", min_length=1)

    email: EmailStr
    # Back-compat: existing clients send a single `phone` value.
    phone: str | None = None
    # New: multi-country phone collection.
    phone_country: str | None = Field(None, alias="phoneCountry", min_length=2, max_length=2)
    phone_national_number: str | None = Field(None, alias="phoneNationalNumber")

    # OTP-first: client must obtain otp_session_id from /register/otp/start before calling this.
    otp_session_id: str = Field(..., alias="otpSessionId", min_length=1)
    otp_code: str = Field(..., alias="otpCode", min_length=1)

    # captcha_token is no longer validated here — CAPTCHA is verified at /register/otp/start.
    captcha_token: str | None = Field(None, alias="captchaToken")

    website: str | None = None
    gst_number: str | None = Field(None, alias="gstNumber")

    preferred_contact_method: Literal["email", "phone"] = Field(..., alias="preferredContactMethod")
    consent: bool

    @field_validator(
        "full_name",
        "business_name",
        "business_industry",
        "business_address",
        mode="before",
    )
    @classmethod
    def _strip_required_strings(cls, v: str) -> str:
        if v is None:
            return v
        return str(v).strip()

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        if v is None:
            return v
        return str(v).strip().lower()

    @field_validator("phone_country", mode="before")
    @classmethod
    def _normalize_phone_country(cls, v: str | None) -> str | None:
        if v is None:
            return None
        value = str(v).strip().upper()
        if not value:
            return None
        if not re.match(r"^[A-Z]{2}$", value):
            raise ValueError("Invalid phone country")
        if phonenumbers.country_code_for_region(value) == 0:
            raise ValueError("Invalid phone country")
        return value

    @field_validator("phone_national_number", mode="before")
    @classmethod
    def _normalize_phone_national_number(cls, v: str | None) -> str | None:
        if v is None:
            return None
        value = _normalize_phone(str(v))
        if not value:
            return None
        if not re.match(r"^\d{4,15}$", value):
            raise ValueError("Invalid phone format")
        return value

    @field_validator("phone", mode="before")
    @classmethod
    def _normalize_phone_field(cls, v: str | None) -> str | None:
        if v is None:
            return None
        value = _normalize_phone(str(v))
        return value or None

    @model_validator(mode="after")
    def _canonicalize_phone(self) -> "RegistrationCreate":
        # Determine the raw input and the region.
        enforce_region = self.phone_country is not None
        if self.phone:
            raw = self.phone
            region = self.phone_country or "IN"
        else:
            if not self.phone_national_number:
                raise ValueError("Phone number is required")
            region = self.phone_country or "IN"
            raw = self.phone_national_number

        # If the user didn't provide a '+'-prefixed number, parse as national using region.
        parse_region = "ZZ" if raw.startswith("+") else region

        self.phone = _canonicalize_phone_e164(
            raw_phone=raw,
            region=parse_region,
            enforce_region=enforce_region,
            desired_region=region,
        )
        return self

    @field_validator("website", mode="before")
    @classmethod
    def _validate_website(cls, v: str | None) -> str | None:
        if v is None:
            return None
        value = str(v).strip()
        if not value:
            return None
        if not re.match(r"^https?://", value, flags=re.IGNORECASE):
            raise ValueError("Website must start with http:// or https://")
        return value

    @field_validator("gst_number", mode="before")
    @classmethod
    def _validate_gst(cls, v: str | None) -> str | None:
        if v is None:
            return None
        value = str(v).strip().upper()
        if not value:
            return None
        if not _GSTIN_RE.match(value):
            raise ValueError("Invalid GST format (GSTIN)")
        return value

    @field_validator("consent")
    @classmethod
    def _require_consent(cls, v: bool) -> bool:
        if v is not True:
            raise ValueError("Consent is required")
        return v

class RegistrationResponse(BaseModel):
    registration_id: str = Field(..., min_length=1)
    email: EmailStr
    phone: str
    full_name: str
    business_name: str
    business_industry: str
    business_address: str
    website: str | None = None
    gst_number: str | None = None
    # JWT tokens — present when registration also authenticates the new user.
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str | None = None
    expires_in: int | None = None

@router.post("/register", response_model=RegistrationResponse, status_code=201)
async def register(
    payload: RegistrationCreate,
    request: Request,
    user_store: UserStore = Depends(get_user_store),
    audit: AuditLogger = Depends(get_audit_logger),  # C2 (NFR It-2)
) -> RegistrationResponse:
    """Register a new customer — OTP-first flow.

    CAPTCHA is verified at /register/otp/start (step 3).
    Here we:
      1. Verify the OTP session (otp_session_id + otp_code)
      2. Check for duplicate email again
      3. Save customer to Plant
    """
    plant_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    registration_key = (os.getenv("CP_REGISTRATION_KEY") or "").strip()
    correlation_id = getattr(request.state, "correlation_id", "")

    if not plant_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Registration service misconfigured (PLANT_GATEWAY_URL not set)",
        )

    # Plant Gateway always gates customer/OTP session endpoints behind X-CP-Registration-Key.
    # Treat missing key as a CP misconfiguration in all environments.
    if not registration_key:
        logger.error(
            "CP_REGISTRATION_KEY is not configured; cannot call Plant for registration (corr_id=%s)",
            correlation_id,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Registration service misconfigured (missing CP_REGISTRATION_KEY)",
        )

    headers = {
        "X-CP-Registration-Key": registration_key,
        "X-Correlation-ID": correlation_id,
    }
    _client = PlantClient(base_url=plant_url)

    # Step 1 — Verify OTP session
    try:
        otp_verify_resp = await _client.post(
            f"/api/v1/otp/sessions/{payload.otp_session_id}/verify",
            json={"code": payload.otp_code},
            headers=headers,
        )
    except ServiceUnavailableError as exc:
        logger.warning("circuit_breaker open — OTP verify blocked: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"error": {
                "code": "SERVICE_TEMPORARILY_UNAVAILABLE",
                "message": "Our service is temporarily unavailable. Please try again in a moment.",
                "correlation_id": correlation_id,
            }},
            headers={"Retry-After": "30"},
        )
    except Exception as exc:
        logger.error("Failed to verify OTP session via Plant: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OTP verification service temporarily unavailable",
        ) from exc

    if otp_verify_resp.status_code == 429:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many incorrect OTP attempts. Please request a new code.",
        )
    if otp_verify_resp.status_code in (401, 403):
        logger.error(
            "Plant rejected registration key during OTP verify (status=%s, corr_id=%s)",
            otp_verify_resp.status_code,
            correlation_id,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Registration service misconfigured (Plant rejected CP_REGISTRATION_KEY)",
        )
    if otp_verify_resp.status_code == 410:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="OTP has expired. Please request a new code.",
        )
    if otp_verify_resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP code.",
        )

    # Step 2 — Prepare payload for Plant
    plant_payload = {
        "fullName": payload.full_name,
        "businessName": payload.business_name,
        "businessIndustry": payload.business_industry,
        "businessAddress": payload.business_address,
        "email": str(payload.email),
        "phone": payload.phone,
        "website": payload.website,
        "gstNumber": payload.gst_number,
        "preferredContactMethod": payload.preferred_contact_method,
        "consent": payload.consent,
    }

    # Step 3 — Save customer to Plant (OTP already verified above).
    # The Plant Gateway guards /api/v1/customers with X-CP-Registration-Key.
    try:
        plant_response = await _client.post(
            "/api/v1/customers",
            json=plant_payload,
            headers=headers,
        )
    except ServiceUnavailableError as exc:
        logger.warning("circuit_breaker open — customer create blocked: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"error": {
                "code": "SERVICE_TEMPORARILY_UNAVAILABLE",
                "message": "Our service is temporarily unavailable. Please try again in a moment.",
                "correlation_id": correlation_id,
            }},
            headers={"Retry-After": "30"},
        )
    except Exception as exc:
        logger.error(f"Failed to reach Plant Gateway at {plant_url}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Registration service temporarily unavailable",
        ) from exc

    if plant_response.status_code == 409:
        detail = "Email or phone already registered."
        try:
            error_detail = plant_response.json().get("detail", detail)
            if error_detail:
                detail = error_detail
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )

    if plant_response.status_code in (401, 403):
        logger.error(
            "Plant rejected registration key during customer create (status=%s, corr_id=%s)",
            plant_response.status_code,
            correlation_id,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Registration service misconfigured (Plant rejected CP_REGISTRATION_KEY)",
        )

    if plant_response.status_code == 429:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Please try again later.",
        )

    if plant_response.status_code >= 400:
        logger.error(f"Plant returned error: {plant_response.status_code} - {plant_response.text}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration validation failed",
        )

    try:
        plant_data = plant_response.json()
    except Exception as exc:
        logger.error(f"Failed to parse Plant response: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid response from registration service",
        ) from exc

    # Return response with customer_id as registration_id + JWT tokens for immediate login
    customer_id = plant_data.get("customer_id", "")
    customer_email = plant_data.get("email", "")
    user = user_store.get_or_create_user(
        UserCreate(
            provider="otp",
            provider_id=customer_id or customer_email,
            email=customer_email,
            name=plant_data.get("full_name", ""),
            picture=None,
        )
    )
    token_data = create_tokens(user_id=user.id, email=user.email)
    await audit.log(
        "cp_registration",
        "registration_complete",
        "success",
        email=customer_email,
        detail=f"customer_id={customer_id}",
    )
    return RegistrationResponse(
        registration_id=customer_id,
        email=customer_email,
        phone=plant_data.get("phone", ""),
        full_name=plant_data.get("full_name", ""),
        business_name=plant_data.get("business_name", ""),
        business_industry=plant_data.get("business_industry", ""),
        business_address=plant_data.get("business_address", ""),
        website=plant_data.get("website"),
        gst_number=plant_data.get("gst_number"),
        access_token=token_data.get("access_token"),
        refresh_token=token_data.get("refresh_token"),
        token_type=token_data.get("token_type", "bearer"),
        expires_in=token_data.get("expires_in"),
    )

