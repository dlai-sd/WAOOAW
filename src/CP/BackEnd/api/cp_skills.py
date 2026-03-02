from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import Depends, HTTPException, Request
from core.routing import waooaw_router
from pydantic import BaseModel, Field

from api.auth.dependencies import get_current_user
from models.user import User

router = waooaw_router(prefix="/cp", tags=["cp-skills"])


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


async def _plant_post_json(
    *, url: str, body: dict, authorization: str | None, correlation_id: str | None
) -> dict:
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if authorization:
        headers["Authorization"] = authorization
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=body, headers=headers)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


async def _plant_delete_json(
    *, url: str, authorization: str | None, correlation_id: str | None
) -> dict:
    headers: dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.delete(url, headers=headers)
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Resource not found")
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        if resp.status_code == 204:
            return {}
        return resp.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


# ─── Pydantic models ─────────────────────────────────────────────────────────

class PlatformConnectionBody(BaseModel):
    platform_name: str
    connection_type: str
    credentials: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.get("/hired-agents/{hired_instance_id}/skills")
async def list_hired_agent_skills(
    hired_instance_id: str,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict | list:
    """
    Two-hop proxy:
    1. Resolve agent_id: GET /api/v1/hired-agents/by-subscription/{hired_instance_id}
       (hired_instance_id is used directly as the identifier)
    2. Fetch skills: GET /api/v1/agents/{agent_id}/skills
    """
    base = _plant_base_url()
    auth = request.headers.get("Authorization")
    cid = request.headers.get("X-Correlation-ID")

    # Hop 1: resolve hired agent to get agent_id
    hired_data = await _plant_get_json(
        url=f"{base}/api/v1/hired-agents/by-id/{hired_instance_id}",
        authorization=auth,
        correlation_id=cid,
    )
    agent_id = (hired_data or {}).get("agent_id") or ""
    if not agent_id:
        raise HTTPException(status_code=404, detail="Hired agent or agent_id not found")

    # Hop 2: fetch skills
    return await _plant_get_json(
        url=f"{base}/api/v1/agents/{agent_id}/skills",
        authorization=auth,
        correlation_id=cid,
    )


@router.get("/skills/{skill_id}")
async def get_skill(
    skill_id: str,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict:
    base = _plant_base_url()
    result = await _plant_get_json(
        url=f"{base}/api/v1/skills/{skill_id}",
        authorization=request.headers.get("Authorization"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
    return result  # type: ignore[return-value]


@router.get("/hired-agents/{hired_instance_id}/platform-connections")
async def list_platform_connections(
    hired_instance_id: str,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict | list:
    base = _plant_base_url()
    return await _plant_get_json(
        url=f"{base}/api/v1/hired-agents/{hired_instance_id}/platform-connections",
        authorization=request.headers.get("Authorization"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )


@router.post("/hired-agents/{hired_instance_id}/platform-connections", status_code=201)
async def create_platform_connection(
    hired_instance_id: str,
    body: PlatformConnectionBody,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict:
    base = _plant_base_url()
    result = await _plant_post_json(
        url=f"{base}/api/v1/hired-agents/{hired_instance_id}/platform-connections",
        body=body.model_dump(),
        authorization=request.headers.get("Authorization"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
    return result


@router.delete(
    "/hired-agents/{hired_instance_id}/platform-connections/{connection_id}",
    status_code=204,
)
async def delete_platform_connection(
    hired_instance_id: str,
    connection_id: str,
    request: Request,
    _user: User = Depends(get_current_user),
) -> None:
    base = _plant_base_url()
    await _plant_delete_json(
        url=f"{base}/api/v1/hired-agents/{hired_instance_id}/platform-connections/{connection_id}",
        authorization=request.headers.get("Authorization"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )


@router.get("/hired-agents/{hired_instance_id}/performance-stats")
async def get_performance_stats(
    hired_instance_id: str,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict | list:
    base = _plant_base_url()
    return await _plant_get_json(
        url=f"{base}/api/v1/hired-agents/{hired_instance_id}/performance-stats",
        authorization=request.headers.get("Authorization"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
