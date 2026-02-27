"""Plant OTP Sessions API.

REG-OTP-2: DB-backed OTP session management.

Endpoints:
- POST /api/v1/otp/sessions   — create a new OTP challenge (CP registration key required)
- POST /api/v1/otp/sessions/{otp_id}/verify — verify a code (CP registration key required)

These endpoints are called exclusively from CP backend, guarded by X-CP-Registration-Key
in the Gateway, so no customer JWT is required.
"""

from __future__ import annotations

import hashlib
import logging
import os
import random
import string
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import BackgroundTasks, Depends, HTTPException, Request, status
from core.routing import waooaw_router  # P-3
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session

router = waooaw_router(prefix="/otp", tags=["otp"])
logger = logging.getLogger(__name__)

_OTP_TTL_SECONDS = 300
_MAX_ATTEMPTS = 3

def _secret_pepper() -> str:
    return (os.getenv("SECRET_KEY") or "dev-insecure-secret").strip()

def _hash_code(code: str) -> str:
    """Deterministic HMAC-SHA256 hash of the OTP code keyed on SECRET_KEY."""
    pepper = _secret_pepper()
    return hashlib.sha256(f"{pepper}:{code}".encode()).hexdigest()

def _generate_code() -> str:
    return "".join(random.choices(string.digits, k=6))

def _is_dev_mode() -> bool:
    env = (os.getenv("ENVIRONMENT") or "").strip().lower()
    return env not in {"prod", "production", "uat"}

# ── Request / Response models ─────────────────────────────────────────────────

class OtpSessionCreateRequest(BaseModel):
    registration_id: str = Field(..., min_length=1)
    channel: Literal["email", "phone"]
    destination: str = Field(..., min_length=1)  # email or E.164 phone

class OtpSessionCreateResponse(BaseModel):
    otp_id: str
    destination_masked: str
    expires_in_seconds: int
    otp_code: str | None = None  # Only present in non-production (dev/demo)

class OtpSessionVerifyRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=10)

class OtpSessionVerifyResponse(BaseModel):
    verified: bool
    registration_id: str

# ── Helpers ───────────────────────────────────────────────────────────────────

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

# ── Endpoints ─────────────────────────────────────────────────────────────────

def _enqueue_otp_email(
    *,
    to_email: str,
    otp_code: str,
    expires_in_seconds: int,
    otp_id: str,
    expires_at_iso: str,
) -> None:
    """Enqueue OTP email via Celery. Runs in a BackgroundTask (after 201 sent)."""
    try:
        from worker.tasks.email_tasks import send_otp_email  # noqa: PLC0415
        send_otp_email.delay(
            to_email=to_email,
            otp_code=otp_code,
            expires_in_seconds=expires_in_seconds,
            otp_id=otp_id,
            expires_at_iso=expires_at_iso,
        )
    except Exception:  # noqa: BLE001
        logger.warning("OTP session %s: could not enqueue email task (broker unavailable?)", otp_id)

@router.post("/sessions", response_model=OtpSessionCreateResponse, status_code=201)
async def create_otp_session(
    payload: OtpSessionCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
) -> OtpSessionCreateResponse:
    """Create a new OTP challenge session.

    Called by CP backend after CAPTCHA verification and duplicate-email check.
    Stores a hashed OTP code in the DB, returns otp_id + masked destination.
    In non-production environments, also returns the raw code for
    testing/demo purposes.
    """
    # Invalidate any previous unexpired sessions for the same destination
    # (prevents OTP spamming — old sessions become unusable after new one is issued)
    await db.execute(
        text(
            "UPDATE otp_sessions SET deleted_at = :now "
            "WHERE destination = :destination "
            "  AND verified_at IS NULL "
            "  AND expires_at > :now "
            "  AND deleted_at IS NULL"
        ),
        {"now": datetime.now(timezone.utc), "destination": payload.destination},
    )

    otp_id = str(uuid.uuid4())
    code = _generate_code()
    code_hash = _hash_code(code)
    now = datetime.now(timezone.utc)
    expires_at = datetime.fromtimestamp(
        now.timestamp() + _OTP_TTL_SECONDS, tz=timezone.utc
    )

    await db.execute(
        text(
            "INSERT INTO otp_sessions "
            "(otp_id, registration_id, channel, destination, code_hash, "
            " attempts, max_attempts, verified_at, expires_at, created_at, deleted_at) "
            "VALUES "
            "(:otp_id, :registration_id, :channel, :destination, :code_hash, "
            " 0, :max_attempts, NULL, :expires_at, :created_at, NULL)"
        ),
        {
            "otp_id": otp_id,
            "registration_id": payload.registration_id,
            "channel": payload.channel,
            "destination": payload.destination,
            "code_hash": code_hash,
            "max_attempts": _MAX_ATTEMPTS,
            "expires_at": expires_at,
            "created_at": now,
        },
    )
    await db.commit()

    logger.info("OTP session created otp_id=%s channel=%s", otp_id, payload.channel)

    # E2-S1: Email dispatch.
    # - Non-prod: skip entirely — otp_code is returned in the response body so
    #   the user can complete registration without email. Avoids blocking on
    #   a Celery/Redis broker that may not be running in dev/demo environments.
    # - Production: enqueue via BackgroundTasks so the 201 is sent to the
    #   caller BEFORE Celery/Redis is contacted. A slow or unavailable broker
    #   never delays or errors the HTTP response.
    if payload.channel == "email" and not _is_dev_mode():
        background_tasks.add_task(
            _enqueue_otp_email,
            to_email=payload.destination,
            otp_code=code,
            expires_in_seconds=_OTP_TTL_SECONDS,
            otp_id=otp_id,
            expires_at_iso=expires_at.isoformat(),
        )

    return OtpSessionCreateResponse(
        otp_id=otp_id,
        destination_masked=_mask_destination(payload.destination),
        expires_in_seconds=_OTP_TTL_SECONDS,
        otp_code=code if _is_dev_mode() else None,
    )

@router.post("/sessions/{otp_id}/verify", response_model=OtpSessionVerifyResponse)
async def verify_otp_session(
    otp_id: str,
    payload: OtpSessionVerifyRequest,
    db: AsyncSession = Depends(get_db_session),
) -> OtpSessionVerifyResponse:
    """Verify an OTP code.

    Increments attempt counter on every call. After max_attempts failures the
    session is locked (returns 429). Correct code marks verified_at.
    """
    result = await db.execute(
        text(
            "SELECT otp_id, registration_id, code_hash, attempts, max_attempts, "
            "       verified_at, expires_at, deleted_at "
            "FROM otp_sessions WHERE otp_id = :otp_id"
        ),
        {"otp_id": otp_id},
    )
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OTP session not found")

    now = datetime.now(timezone.utc)

    if row["deleted_at"] is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP session is no longer valid")

    if row["verified_at"] is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP already verified")

    expires_at = row["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if now > expires_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP has expired")

    if row["attempts"] >= row["max_attempts"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many incorrect attempts. Please request a new OTP.",
        )

    # Increment attempt counter first (before checking the code)
    await db.execute(
        text("UPDATE otp_sessions SET attempts = attempts + 1 WHERE otp_id = :otp_id"),
        {"otp_id": otp_id},
    )
    await db.commit()

    submitted_hash = _hash_code(payload.code.strip())
    if submitted_hash != row["code_hash"]:
        remaining = row["max_attempts"] - (row["attempts"] + 1)
        if remaining <= 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many incorrect attempts. Please request a new OTP.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OTP code. {remaining} attempt(s) remaining.",
        )

    # Mark as verified
    await db.execute(
        text("UPDATE otp_sessions SET verified_at = :now WHERE otp_id = :otp_id"),
        {"otp_id": otp_id, "now": now},
    )
    await db.commit()

    logger.info("OTP verified otp_id=%s", otp_id)

    return OtpSessionVerifyResponse(
        verified=True,
        registration_id=str(row["registration_id"]),
    )
