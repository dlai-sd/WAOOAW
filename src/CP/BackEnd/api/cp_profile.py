"""CP Profile routes — E4-S1 (CP-NAV-1 Iteration 2).

GET  /api/cp/profile  — return current user's profile
PATCH /api/cp/profile — update editable profile fields
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Optional

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict

from api.auth.dependencies import get_current_user
from api.auth.user_store import UserStore, get_user_store
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from models.user import User
from services.audit_dependency import AuditLogger, get_audit_logger

# Optional OTel — graceful degradation when package not installed
try:
    from opentelemetry import trace as _otel_trace
    _tracer = _otel_trace.get_tracer(__name__)
    _OTEL = True
except Exception:
    _tracer = None  # type: ignore
    _OTEL = False


@contextmanager
def _span(name: str):  # type: ignore
    """Start an OTel span when OTel is available, otherwise no-op."""
    if _OTEL and _tracer:
        with _tracer.start_as_current_span(name) as span:
            yield span
    else:
        yield None

router = waooaw_router(prefix="/cp/profile", tags=["cp-profile"])

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())


class ProfileResponse(BaseModel):
    """Public profile shape returned to the client."""

    id: str
    email: str
    name: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    business_name: Optional[str] = None
    industry: Optional[str] = None
    picture: Optional[str] = None


class ProfileUpdate(BaseModel):
    """Editable profile fields — all optional for PATCH semantics."""

    model_config = ConfigDict(strict=False)

    full_name: Optional[str] = None
    phone: Optional[str] = None
    business_name: Optional[str] = None
    industry: Optional[str] = None


def _to_response(user: User) -> ProfileResponse:
    return ProfileResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        full_name=user.full_name,
        phone=user.phone,
        business_name=user.business_name,
        industry=user.industry,
        picture=user.picture,
    )


@router.get("", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    """Return the authenticated user's profile."""
    with _span("cp.profile.get") as span:
        if span:
            span.set_attribute("user.id", current_user.id)
        logger.info("Profile fetched for user %s", current_user.id)
        return _to_response(current_user)


@router.patch("", response_model=ProfileResponse)
async def patch_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    user_store: UserStore = Depends(get_user_store),
    audit: AuditLogger = Depends(get_audit_logger),
) -> ProfileResponse:
    """Update editable profile fields for the authenticated user."""
    with _span("cp.profile.patch") as span:
        updates = payload.model_dump(exclude_none=True)
        if span:
            span.set_attribute("user.id", current_user.id)
            span.set_attribute("profile.fields_updated", ",".join(updates.keys()))
        if not updates:
            return _to_response(current_user)

        updated = user_store.update_profile(current_user.id, updates)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        logger.info("Profile updated for user %s", current_user.id)
        await audit.log("cp_profile", "profile_updated", "success", user_id=current_user.id)
        return _to_response(updated)
