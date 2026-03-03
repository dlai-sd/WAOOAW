from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import Depends, HTTPException, Request
from core.routing import waooaw_router
from pydantic import BaseModel, Field

from api.auth.dependencies import get_current_user
from models.user import User
from services.secret_manager import get_secret_manager_adapter

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


async def _plant_patch_json(
    *, url: str, body: dict, authorization: str | None, correlation_id: str | None
) -> dict:
    """PATCH proxy helper — forwards body as JSON, forwards auth + correlation headers."""
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if authorization:
        headers["Authorization"] = authorization
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.patch(url, json=body, headers=headers)
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Resource not found")
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


# ─── Pydantic models ─────────────────────────────────────────────────────────

class PlatformConnectionBody(BaseModel):
    """Legacy body shape — kept for backward compatibility only."""
    platform_name: str = ""
    connection_type: str = "token"
    credentials: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CreatePlatformConnectionBody(BaseModel):
    """New body shape aligned with Plant BackEnd CreateConnectionRequest.

    Credentials are intercepted here, written to GCP Secret Manager,
    and only the opaque secret_ref is forwarded to Plant.
    Raw credentials are NEVER stored in the database.
    """
    skill_id: str
    platform_key: str
    credentials: dict[str, Any] = Field(default_factory=dict)


class GoalConfigBody(BaseModel):
    """Request body for PATCH goal-config. goal_config is an arbitrary JSON object."""
    goal_config: dict[str, Any] = Field(default_factory=dict)


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
    body: CreatePlatformConnectionBody,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict:
    """Create a platform connection.

    Credentials are written to GCP Secret Manager; only the opaque
    secret_ref is forwarded to Plant BackEnd — raw credentials never
    touch the database.

    Secret naming: hired-{hired_instance_id}-{platform_key}
    Stable across all environments; only the GCP project (GCP_PROJECT_ID)
    differs — injected via Terraform (image promotion compliant).
    """
    secret_id = f"hired-{hired_instance_id}-{body.platform_key}"
    adapter = get_secret_manager_adapter()
    secret_ref = await adapter.write_secret(
        secret_id=secret_id,
        payload=body.credentials,
    )

    base = _plant_base_url()
    result = await _plant_post_json(
        url=f"{base}/api/v1/hired-agents/{hired_instance_id}/platform-connections",
        body={
            "skill_id": body.skill_id,
            "platform_key": body.platform_key,
            "secret_ref": secret_ref,
        },
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


@router.patch("/hired-agents/{hired_instance_id}/skills/{skill_id}/goal-config")
async def save_goal_config(
    hired_instance_id: str,
    skill_id: str,
    body: GoalConfigBody,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict:
    """Persist goal config for a specific skill on a hired agent.

    CP-SKILLS-2 E2-S1 — two-hop proxy:
      Hop 1: GET /api/v1/hired-agents/by-id/{hired_instance_id}  → resolve agent_id
      Hop 2: PATCH /api/v1/agents/{agent_id}/skills/{skill_id}/goal-config
    """
    base = _plant_base_url()
    auth = request.headers.get("Authorization")
    cid = request.headers.get("X-Correlation-ID")

    # Hop 1: resolve hired agent → agent_id
    hired_data = await _plant_get_json(
        url=f"{base}/api/v1/hired-agents/by-id/{hired_instance_id}",
        authorization=auth,
        correlation_id=cid,
    )
    agent_id = (hired_data or {}).get("agent_id") or ""
    if not agent_id:
        raise HTTPException(status_code=404, detail="Hired agent or agent_id not found")

    # Hop 2: persist goal config
    return await _plant_patch_json(  # type: ignore[return-value]
        url=f"{base}/api/v1/agents/{agent_id}/skills/{skill_id}/goal-config",
        body={"goal_config": body.goal_config},
        authorization=auth,
        correlation_id=cid,
    )
