from __future__ import annotations

import os
from typing import Any, Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.auth.dependencies import get_current_user
from models.user import User


router = APIRouter(prefix="/cp/hire/wizard", tags=["cp-hire"])


def _bool_env(name: str, default: str = "false") -> bool:
    return (os.getenv(name) or default).strip().lower() in {"1", "true", "yes", "on"}


TrialStatus = Literal["not_started", "active", "ended_converted", "ended_not_converted"]


class HireWizardDraftRequest(BaseModel):
    subscription_id: str = Field(..., min_length=1)
    agent_id: str = Field(..., min_length=1)
    agent_type_id: str = Field(..., min_length=1)

    nickname: str | None = None
    theme: str | None = None
    config: dict[str, Any] | None = None


class HireWizardFinalizeRequest(BaseModel):
    hired_instance_id: str = Field(..., min_length=1)
    agent_type_id: str = Field(..., min_length=1)
    goals_completed: bool = False


class HireWizardResponse(BaseModel):
    hired_instance_id: str
    subscription_id: str
    agent_id: str
    agent_type_id: str
    nickname: str | None = None
    theme: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)

    configured: bool = False
    goals_completed: bool = False

    subscription_status: str | None = None
    trial_status: TrialStatus = "not_started"
    trial_start_at: str | None = None
    trial_end_at: str | None = None


_drafts_by_subscription: dict[str, HireWizardResponse] = {}


async def _plant_upsert_draft(
    *,
    body: HireWizardDraftRequest,
    customer_id: str,
    authorization: str | None,
) -> dict:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base_url:
        raise RuntimeError("PLANT_GATEWAY_URL not configured")

    payload = {
        "subscription_id": body.subscription_id,
        "agent_id": body.agent_id,
        "agent_type_id": body.agent_type_id,
        "nickname": body.nickname,
        "theme": body.theme,
        "config": body.config,
        "customer_id": customer_id,
    }

    headers: dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.put(f"{base_url}/api/v1/hired-agents/draft", json=payload, headers=headers)

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=f"Plant draft save failed ({resp.status_code})")
    return resp.json()


async def _plant_finalize(
    *,
    hired_instance_id: str,
    agent_type_id: str,
    goals_completed: bool,
    customer_id: str,
    authorization: str | None,
) -> dict:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base_url:
        raise RuntimeError("PLANT_GATEWAY_URL not configured")

    headers: dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{base_url}/api/v1/hired-agents/{hired_instance_id}/finalize",
            json={
                "customer_id": customer_id,
                "agent_type_id": agent_type_id,
                "goals_completed": bool(goals_completed),
            },
            headers=headers,
        )

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=f"Plant finalize failed ({resp.status_code})")
    return resp.json()


@router.put("/draft", response_model=HireWizardResponse)
async def upsert_draft(
    body: HireWizardDraftRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> HireWizardResponse:
    _ = current_user

    authorization = request.headers.get("Authorization")

    if _bool_env("CP_HIRE_USE_PLANT", "false"):
        try:
            plant = await _plant_upsert_draft(body=body, customer_id=current_user.id, authorization=authorization)
            return HireWizardResponse(
                hired_instance_id=plant["hired_instance_id"],
                subscription_id=plant["subscription_id"],
                agent_id=plant["agent_id"],
                agent_type_id=plant.get("agent_type_id") or body.agent_type_id,
                nickname=plant.get("nickname"),
                theme=plant.get("theme"),
                config=plant.get("config") or {},
                configured=bool(plant.get("configured")),
                goals_completed=bool(plant.get("goals_completed")),
                subscription_status=plant.get("subscription_status"),
                trial_status=plant.get("trial_status") or "not_started",
                trial_start_at=plant.get("trial_start_at"),
                trial_end_at=plant.get("trial_end_at"),
            )
        except RuntimeError:
            pass

    # CP-local fallback: store draft so UI can resume, even without Plant wired.
    existing = _drafts_by_subscription.get(body.subscription_id)
    if existing:
        merged = existing.model_copy(
            update={
                "agent_id": body.agent_id,
                "agent_type_id": body.agent_type_id,
                "nickname": body.nickname if body.nickname is not None else existing.nickname,
                "theme": body.theme if body.theme is not None else existing.theme,
                "config": dict(body.config) if body.config is not None else existing.config,
            }
        )
        merged = merged.model_copy(
            update={
                "configured": bool((merged.nickname or "").strip()) and bool((merged.theme or "").strip()),
            }
        )
        _drafts_by_subscription[body.subscription_id] = merged
        return merged

    import uuid

    hired_instance_id = f"HAI-{uuid.uuid4()}"
    created = HireWizardResponse(
        hired_instance_id=hired_instance_id,
        subscription_id=body.subscription_id,
        agent_id=body.agent_id,
        agent_type_id=body.agent_type_id,
        nickname=body.nickname,
        theme=body.theme,
        config=dict(body.config or {}),
        configured=bool((body.nickname or "").strip()) and bool((body.theme or "").strip()),
    )
    _drafts_by_subscription[body.subscription_id] = created
    return created


@router.get("/by-subscription/{subscription_id}", response_model=HireWizardResponse)
async def get_by_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user),
) -> HireWizardResponse:
    _ = current_user

    stored = _drafts_by_subscription.get(subscription_id)
    if not stored:
        raise HTTPException(status_code=404, detail="Wizard draft not found")
    return stored


@router.post("/finalize", response_model=HireWizardResponse)
async def finalize(
    body: HireWizardFinalizeRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> HireWizardResponse:
    _ = current_user
    authorization = request.headers.get("Authorization")

    if _bool_env("CP_HIRE_USE_PLANT", "false"):
        try:
            plant = await _plant_finalize(
                hired_instance_id=body.hired_instance_id,
                agent_type_id=body.agent_type_id,
                goals_completed=body.goals_completed,
                customer_id=current_user.id,
                authorization=authorization,
            )
            return HireWizardResponse(
                hired_instance_id=plant["hired_instance_id"],
                subscription_id=plant["subscription_id"],
                agent_id=plant["agent_id"],
                agent_type_id=plant.get("agent_type_id") or body.agent_type_id,
                nickname=plant.get("nickname"),
                theme=plant.get("theme"),
                config=plant.get("config") or {},
                configured=bool(plant.get("configured")),
                goals_completed=bool(plant.get("goals_completed")),
                subscription_status=plant.get("subscription_status"),
                trial_status=plant.get("trial_status") or "not_started",
                trial_start_at=plant.get("trial_start_at"),
                trial_end_at=plant.get("trial_end_at"),
            )
        except RuntimeError:
            pass

    # CP-local fallback: mark goals completed; trial stays not_started without Plant.
    for sub_id, stored in list(_drafts_by_subscription.items()):
        if stored.hired_instance_id == body.hired_instance_id:
            updated = stored.model_copy(
                update={
                    "goals_completed": bool(body.goals_completed),
                }
            )
            _drafts_by_subscription[sub_id] = updated
            return updated

    raise HTTPException(status_code=404, detail="Wizard draft not found")
