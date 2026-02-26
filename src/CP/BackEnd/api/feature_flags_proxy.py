"""Feature flag proxy — E2-S2 (Iteration 7: Scale Prep).

Proxies CP-scoped feature flags from Plant's feature-flags API so the CP
frontend can poll flags without a direct Plant reference.

GET /api/cp/feature-flags              — list CP-scoped flags (auth optional)
GET /api/cp/feature-flags/{key}        — evaluate a single flag for logged-in customer
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request

from api.auth.dependencies import get_current_user
from models.user import User

router = APIRouter(prefix="/cp/feature-flags", tags=["cp-feature-flags"])


def _plant_base_url() -> str:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base_url:
        raise RuntimeError("PLANT_GATEWAY_URL not configured")
    return base_url


async def _plant_get(url: str, authorization: str | None = None) -> Any:
    headers: Dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers=headers)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Plant unavailable: {exc}") from exc

    if resp.status_code == 200:
        return resp.json()
    raise HTTPException(status_code=resp.status_code, detail=f"Plant error ({resp.status_code})")


@router.get(
    "",
    response_model=List[Dict[str, Any]],
    summary="List CP-scoped feature flags",
)
async def list_cp_feature_flags(request: Request) -> List[Dict[str, Any]]:
    """Return feature flags scoped to 'cp' or 'all'.

    No auth required — flags have no secret value (enabled/disabled booleans only).
    Result should be cached by the client for 60 seconds (matching backend TTL).

    Falls back to empty list if Plant is unreachable so the CP app loads normally.
    """
    try:
        base = _plant_base_url()
    except RuntimeError:
        return []  # unconfigured in dev — safe default

    try:
        return await _plant_get(f"{base}/api/v1/feature-flags?scope=cp")
    except HTTPException:
        return []  # safe default — nothing unexpected shown to users


@router.get(
    "/{key}",
    response_model=Dict[str, Any],
    summary="Evaluate a feature flag for the logged-in customer",
)
async def evaluate_cp_feature_flag(
    key: str,
    current_user: Optional[User] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Evaluate flag `key` for the authenticated customer.

    Returns ``{"key": key, "enabled": bool}``.
    Safe default is ``enabled: false`` when Plant is unreachable.
    """
    try:
        base = _plant_base_url()
    except RuntimeError:
        return {"key": key, "enabled": False}

    customer_id_param = ""
    if current_user is not None and hasattr(current_user, "id"):
        customer_id_param = f"?customer_id={current_user.id}"

    try:
        return await _plant_get(f"{base}/api/v1/feature-flags/{key}/evaluate{customer_id_param}")
    except HTTPException:
        return {"key": key, "enabled": False}
