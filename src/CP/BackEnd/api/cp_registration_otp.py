"""CP registration OTP start endpoint.

REG-OTP-3: CAPTCHA → duplicate-check → OTP create (OTP-first registration).

Step 3 of the agreed registration flow:
  1. User fills form (nothing saved)
  2. CAPTCHA verified client-side widget
  3. POST /api/cp/auth/register/otp/start  ← this file
     - Validates CAPTCHA token
     - Checks Plant for duplicate email (409 if exists)
     - Creates OTP session in Plant DB
     - Returns otp_id + masked destination
  4. User enters OTP
  5. POST /api/cp/auth/register  (in cp_registration.py) - verify OTP then save
"""

from __future__ import annotations

import logging
import os

import httpx
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/cp/auth/register", tags=["cp-auth"])
logger = logging.getLogger(__name__)


def _get_plant_url() -> str:
    url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Registration service misconfigured (PLANT_GATEWAY_URL not set)",
        )
    return url


def _get_registration_key() -> str:
    return (os.getenv("CP_REGISTRATION_KEY") or "").strip()


def _get_correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", "")


def _is_production() -> bool:
    env = (os.getenv("ENVIRONMENT") or "").strip().lower()
    return env in {"prod", "production", "uat", "demo"}


async def _verify_turnstile_token(*, token: str, remote_ip: str | None) -> None:
    secret = (os.getenv("TURNSTILE_SECRET_KEY") or "").strip()
    if not secret:
        if _is_production():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="CAPTCHA service not configured",
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

    if resp.status_code != 200 or not (resp.json() if resp.content else {}).get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CAPTCHA verification failed")


# ── Models ────────────────────────────────────────────────────────────────────

class RegistrationOtpStartRequest(BaseModel):
    email: EmailStr
    captcha_token: str | None = Field(None, alias="captchaToken")

    class Config:
        populate_by_name = True


class RegistrationOtpStartResponse(BaseModel):
    otp_id: str
    destination_masked: str
    expires_in_seconds: int
    otp_code: str | None = None


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/otp/start", response_model=RegistrationOtpStartResponse)
async def registration_otp_start(
    payload: RegistrationOtpStartRequest,
    request: Request,
) -> RegistrationOtpStartResponse:
    """Start OTP as the first step of registration (before saving customer).

    Flow:
    1. Verify CAPTCHA
    2. Check Plant for duplicate email → 409 if already registered
    3. Create OTP session in Plant DB
    4. Return otp_id for subsequent /register call
    """
    correlation_id = _get_correlation_id(request)
    registration_key = _get_registration_key()
    headers = {
        "X-CP-Registration-Key": registration_key,
        "X-Correlation-ID": correlation_id,
    }
    plant_url = _get_plant_url()

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

    # Step 1 — CAPTCHA
    if _is_production() and not payload.captcha_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CAPTCHA token is required",
        )
    if payload.captcha_token:
        remote_ip = request.client.host if request.client else None
        await _verify_turnstile_token(token=payload.captcha_token, remote_ip=remote_ip)

    email = str(payload.email).strip().lower()

    # Step 2 — Duplicate email check
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            lookup_resp = await client.get(
                f"{plant_url}/api/v1/customers/lookup",
                params={"email": email},
                headers=headers,
            )
    except Exception as exc:
        logger.error("Plant customer lookup failed during registration OTP start: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Registration service temporarily unavailable",
        ) from exc

    if lookup_resp.status_code in (401, 403):
        logger.error(
            "Plant rejected registration key during lookup (status=%s, corr_id=%s)",
            lookup_resp.status_code,
            correlation_id,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Registration service misconfigured (Plant rejected CP_REGISTRATION_KEY)",
        )

    if lookup_resp.status_code == 200:
        # Customer already exists
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email is already registered. Please log in or use a different email.",
        )

    if lookup_resp.status_code >= 500:
        # Plant Backend internal error — most commonly a DB schema mismatch
        # (e.g. a pending Alembic migration was not applied after deploy).
        logger.error(
            "Plant returned %s during customer lookup — possible DB/migration issue "
            "(corr_id=%s): %s",
            lookup_resp.status_code,
            correlation_id,
            lookup_resp.text[:500],
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": {
                    "code": "UPSTREAM_ERROR",
                    "message": "Registration service is temporarily experiencing issues. Please try again in a moment.",
                    "correlation_id": correlation_id,
                }
            },
            headers={"Retry-After": "30"},
        )

    if lookup_resp.status_code not in (404, 200):
        logger.error(
            "Unexpected lookup response %s during registration (corr_id=%s): %s",
            lookup_resp.status_code,
            correlation_id,
            lookup_resp.text,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Registration service temporarily unavailable",
        )

    # Step 3 — Create OTP session in Plant DB
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            otp_resp = await client.post(
                f"{plant_url}/api/v1/otp/sessions",
                json={
                    "registration_id": email,
                    "channel": "email",
                    "destination": email,
                },
                headers=headers,
            )
    except Exception as exc:
        logger.error("Plant OTP session create failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OTP service temporarily unavailable",
        ) from exc

    if otp_resp.status_code in (401, 403):
        logger.error(
            "Plant rejected registration key during OTP create (status=%s, corr_id=%s)",
            otp_resp.status_code,
            correlation_id,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OTP service misconfigured (Plant rejected CP_REGISTRATION_KEY)",
        )

    if otp_resp.status_code >= 500:
        # Plant Backend internal error — most commonly a missing DB table from
        # an unapplied Alembic migration (e.g. otp_sessions table not created yet).
        logger.error(
            "Plant returned %s during OTP session create — possible DB/migration issue "
            "(corr_id=%s): %s",
            otp_resp.status_code,
            correlation_id,
            otp_resp.text[:500],
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": {
                    "code": "UPSTREAM_ERROR",
                    "message": "OTP service is temporarily experiencing issues. Please try again in a moment.",
                    "correlation_id": correlation_id,
                }
            },
            headers={"Retry-After": "30"},
        )

    if otp_resp.status_code != 201:
        logger.error("Plant OTP session returned %s: %s", otp_resp.status_code, otp_resp.text)

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to start OTP verification",
        )

    try:
        otp_data = otp_resp.json()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid response from OTP service",
        ) from exc

    return RegistrationOtpStartResponse(
        otp_id=otp_data["otp_id"],
        destination_masked=otp_data["destination_masked"],
        expires_in_seconds=otp_data["expires_in_seconds"],
        otp_code=otp_data.get("otp_code"),
    )
