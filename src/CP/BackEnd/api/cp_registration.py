"""CP registration routes.

REG-1.3: POST /api/cp/auth/register validates and normalizes registration input,
then mints a `registration_id` for later OTP verification.

This is intentionally CP-local (not proxied to Plant) so the CP frontend can
ship incremental registration + verification flows.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Literal

import httpx
import phonenumbers
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from pydantic import model_validator

from services.cp_registrations import (
    CPRegistrationRecord,
    FileCPRegistrationStore,
    get_cp_registration_store,
)


router = APIRouter(prefix="/cp/auth", tags=["cp-auth"])

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

    captcha_token: str | None = Field(None, alias="captchaToken", min_length=1)

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


@router.post("/register", response_model=RegistrationResponse, status_code=201)
async def register(
    payload: RegistrationCreate,
    request: Request,
    store: FileCPRegistrationStore = Depends(get_cp_registration_store),
) -> RegistrationResponse:
    if _is_production() and not payload.captcha_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CAPTCHA token is required",
        )

    if payload.captcha_token:
        remote_ip = request.client.host if request.client else None
        await _verify_turnstile_token(token=payload.captcha_token, remote_ip=remote_ip)

    # Enforce uniqueness for account identifiers.
    # CP's registration store is file-backed, so without this check we can mint multiple
    # registration_ids for the same email/phone and later OTP verification will appear
    # to "work" even when the underlying identity should be unique.
    existing_email = store.get_by_email(str(payload.email))
    if existing_email is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered. Please log in.",
        )

    existing_phone = store.get_by_phone(payload.phone)
    if existing_phone is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone already registered. Please log in.",
        )

    record = CPRegistrationRecord(
        registration_id=store.mint_registration_id(),
        full_name=payload.full_name,
        business_name=payload.business_name,
        business_industry=payload.business_industry,
        business_address=payload.business_address,
        email=str(payload.email),
        phone=payload.phone,
        website=payload.website,
        gst_number=payload.gst_number,
        preferred_contact_method=payload.preferred_contact_method,
        consent=payload.consent,
    )
    store.append(record)

    return RegistrationResponse(
        registration_id=record.registration_id,
        email=record.email,
        phone=record.phone,
    )
