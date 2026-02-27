"""Feature flag API endpoints — E2-S1 (Iteration 7: Scale Prep).

GET  /api/v1/feature-flags          — list all flags (admin JWT required)
GET  /api/v1/feature-flags/{key}    — evaluate a flag for a customer
POST /api/v1/feature-flags          — create/update a flag (admin JWT required)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from core.routing import waooaw_router  # P-3
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_read_db_session, get_db_session
from core.security import verify_token
from services.feature_flag_service import FeatureFlagService

router = waooaw_router(prefix="/feature-flags", tags=["feature-flags"])

# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

def _require_admin_jwt(request: Request) -> Dict[str, Any]:
    auth = (
        request.headers.get("X-Original-Authorization")
        or request.headers.get("Authorization")
        or ""
    )
    parts = auth.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token",
        )
    claims = verify_token(parts[1])
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    roles = claims.get("roles") or []
    if isinstance(roles, str):
        roles = [roles]
    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return claims

# ---------------------------------------------------------------------------
# Dependency factories
# ---------------------------------------------------------------------------

def get_flag_service(db: AsyncSession = Depends(get_read_db_session)) -> FeatureFlagService:
    """Read-only flag service (uses read replica — E1-S2 It-7)."""
    return FeatureFlagService(db)

def get_write_flag_service(db: AsyncSession = Depends(get_db_session)) -> FeatureFlagService:
    """Write flag service (uses primary DB)."""
    return FeatureFlagService(db)

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class FeatureFlagUpsert(BaseModel):
    key: str
    enabled: bool = False
    rollout_percentage: int = 100
    enabled_for_customer_ids: Optional[List[UUID]] = None
    scope: str = "all"
    description: Optional[str] = None

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=List[Dict[str, Any]],
    summary="List all feature flags (admin JWT required)",
)
async def list_feature_flags(
    scope: Optional[str] = None,
    _claims: Dict[str, Any] = Depends(_require_admin_jwt),
    svc: FeatureFlagService = Depends(get_flag_service),
) -> List[Dict[str, Any]]:
    """Return all feature flags, optionally filtered by scope.

    Requires admin JWT. Results served from read replica.
    """
    return await svc.list_flags(scope=scope)

@router.get(
    "/{key}/evaluate",
    response_model=Dict[str, Any],
    summary="Evaluate a feature flag for an optional customer",
)
async def evaluate_flag(
    key: str,
    customer_id: Optional[UUID] = None,
    svc: FeatureFlagService = Depends(get_flag_service),
) -> Dict[str, Any]:
    """Check whether flag `key` is enabled for `customer_id`.

    No auth required — consumers supply customer_id from their session.
    Returns ``{"key": key, "enabled": bool}``.
    """
    enabled = await svc.is_enabled(key, customer_id=customer_id)
    return {"key": key, "enabled": enabled}

@router.post(
    "",
    status_code=status.HTTP_200_OK,
    summary="Create or update a feature flag (admin JWT required)",
)
async def upsert_feature_flag(
    payload: FeatureFlagUpsert,
    _claims: Dict[str, Any] = Depends(_require_admin_jwt),
    svc: FeatureFlagService = Depends(get_write_flag_service),
) -> Dict[str, str]:
    """Create or update a feature flag. Idempotent (upsert by key)."""
    await svc.upsert_flag(payload.model_dump())
    return {"status": "ok", "key": payload.key}
