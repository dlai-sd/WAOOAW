from __future__ import annotations

import os

import httpx
from fastapi import Depends, HTTPException, Request

from api.auth.dependencies import get_current_user
from core.routing import waooaw_router
from models.user import User


router = waooaw_router(prefix="/cp/catalog", tags=["cp-catalog"])


def _plant_base_url() -> str:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base_url:
        raise RuntimeError("PLANT_GATEWAY_URL not configured")
    return base_url


async def _plant_get_json(
    *, url: str, authorization: str | None, correlation_id: str | None
) -> dict | list:
    headers: dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Resource not found")
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/agents")
async def list_catalog_agents(
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict | list:
    base = _plant_base_url()
    url = f"{base}/api/v1/catalog/agents"
    query = str(request.url.query or "").strip()
    if query:
        url = f"{url}?{query}"
    return await _plant_get_json(
        url=url,
        authorization=request.headers.get("Authorization"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )