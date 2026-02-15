from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.auth.dependencies import get_current_user
from models.user import User


router = APIRouter(prefix="/cp/hired-agents", tags=["cp-hired-agents"])


def _plant_base_url() -> str:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base_url:
        raise RuntimeError("PLANT_GATEWAY_URL not configured")
    return base_url


async def _plant_get_json(*, url: str, authorization: str | None, correlation_id: str | None) -> dict:
    headers: dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
    except httpx.RequestError as exc:
        raise RuntimeError(f"Plant call failed (network): {exc}")

    if 400 <= resp.status_code < 500:
        raise HTTPException(status_code=resp.status_code, detail=f"Plant call failed ({resp.status_code})")
    if resp.status_code >= 500:
        raise RuntimeError(f"Plant call failed ({resp.status_code})")

    data = resp.json()
    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="Unexpected Plant response")
    return data


async def _plant_put_json(
    *,
    url: str,
    authorization: str | None,
    correlation_id: str | None,
    payload: dict[str, Any],
) -> dict:
    headers: dict[str, str] = {"content-type": "application/json"}
    if authorization:
        headers["Authorization"] = authorization
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.put(url, headers=headers, json=payload)
    except httpx.RequestError as exc:
        raise RuntimeError(f"Plant call failed (network): {exc}")

    if 400 <= resp.status_code < 500:
        raise HTTPException(status_code=resp.status_code, detail=f"Plant call failed ({resp.status_code})")
    if resp.status_code >= 500:
        raise RuntimeError(f"Plant call failed ({resp.status_code})")

    data = resp.json()
    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="Unexpected Plant response")
    return data


async def _plant_post_json(
    *,
    url: str,
    authorization: str | None,
    correlation_id: str | None,
    payload: dict[str, Any],
) -> dict:
    headers: dict[str, str] = {"content-type": "application/json"}
    if authorization:
        headers["Authorization"] = authorization
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
    except httpx.RequestError as exc:
        raise RuntimeError(f"Plant call failed (network): {exc}")

    if 400 <= resp.status_code < 500:
        raise HTTPException(status_code=resp.status_code, detail=f"Plant call failed ({resp.status_code})")
    if resp.status_code >= 500:
        raise RuntimeError(f"Plant call failed ({resp.status_code})")

    data = resp.json()
    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="Unexpected Plant response")
    return data


async def _plant_delete_json(*, url: str, authorization: str | None, correlation_id: str | None) -> dict:
    headers: dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.delete(url, headers=headers)
    except httpx.RequestError as exc:
        raise RuntimeError(f"Plant call failed (network): {exc}")

    if 400 <= resp.status_code < 500:
        raise HTTPException(status_code=resp.status_code, detail=f"Plant call failed ({resp.status_code})")
    if resp.status_code >= 500:
        raise RuntimeError(f"Plant call failed ({resp.status_code})")

    data = resp.json()
    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="Unexpected Plant response")
    return data


class HiredAgentDraftUpsertRequest(BaseModel):
    subscription_id: str = Field(..., min_length=1)
    agent_id: str = Field(..., min_length=1)
    agent_type_id: str = Field(..., min_length=1)

    nickname: str | None = None
    theme: str | None = None
    config: dict[str, Any] | None = None


class HiredAgentInstanceResponse(BaseModel):
    hired_instance_id: str
    subscription_id: str
    agent_id: str

    agent_type_id: str | None = None

    nickname: str | None = None
    theme: str | None = None
    config: dict[str, Any] | None = None

    configured: bool | None = None
    goals_completed: bool | None = None
    trial_status: str | None = None


class GoalInstanceUpsertRequest(BaseModel):
    goal_instance_id: str | None = None
    goal_template_id: str = Field(..., min_length=1)
    frequency: str = Field(..., min_length=1)
    settings: dict[str, Any] = Field(default_factory=dict)


class GoalInstanceResponse(BaseModel):
    goal_instance_id: str
    hired_instance_id: str
    goal_template_id: str
    frequency: str
    settings: dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None


class GoalsListResponse(BaseModel):
    hired_instance_id: str
    goals: list[GoalInstanceResponse] = Field(default_factory=list)


class DeliverableResponse(BaseModel):
    deliverable_id: str
    hired_instance_id: str
    goal_instance_id: str
    goal_template_id: str

    title: str
    payload: dict[str, Any] = Field(default_factory=dict)

    review_status: str
    review_notes: str | None = None
    approval_id: str | None = None

    execution_status: str
    executed_at: str | None = None

    created_at: str | None = None
    updated_at: str | None = None


class DeliverablesListResponse(BaseModel):
    hired_instance_id: str
    deliverables: list[DeliverableResponse] = Field(default_factory=list)


class ReviewDeliverableRequest(BaseModel):
    decision: str = Field(..., min_length=1)
    notes: str | None = None
    approval_id: str | None = None


class ReviewDeliverableResponse(BaseModel):
    deliverable_id: str
    review_status: str
    approval_id: str | None = None
    updated_at: str | None = None


class ExecuteDeliverableRequest(BaseModel):
    approval_id: str = Field(..., min_length=1)


class ExecuteDeliverableResponse(BaseModel):
    deliverable_id: str
    execution_status: str
    executed_at: str | None = None
    updated_at: str | None = None


@router.get("/by-subscription/{subscription_id}", response_model=HiredAgentInstanceResponse)
async def get_by_subscription(
    subscription_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> HiredAgentInstanceResponse:
    authorization = request.headers.get("Authorization")
    correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("x-correlation-id")

    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    data = await _plant_get_json(
        url=f"{base}/api/v1/hired-agents/by-subscription/{subscription_id}?customer_id={current_user.id}",
        authorization=authorization,
        correlation_id=correlation_id,
    )
    return HiredAgentInstanceResponse(**data)


@router.put("/draft", response_model=HiredAgentInstanceResponse)
async def upsert_draft(
    body: HiredAgentDraftUpsertRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> HiredAgentInstanceResponse:
    authorization = request.headers.get("Authorization")
    correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("x-correlation-id")

    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    payload = {
        "subscription_id": body.subscription_id,
        "agent_id": body.agent_id,
        "agent_type_id": body.agent_type_id,
        "customer_id": current_user.id,
        "nickname": body.nickname,
        "theme": body.theme,
        "config": body.config,
    }

    data = await _plant_put_json(
        url=f"{base}/api/v1/hired-agents/draft",
        authorization=authorization,
        correlation_id=correlation_id,
        payload=payload,
    )
    return HiredAgentInstanceResponse(**data)


@router.get("/{hired_instance_id}/goals", response_model=GoalsListResponse)
async def list_goals(
    hired_instance_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> GoalsListResponse:
    authorization = request.headers.get("Authorization")
    correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("x-correlation-id")

    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    data = await _plant_get_json(
        url=f"{base}/api/v1/hired-agents/{hired_instance_id}/goals?customer_id={current_user.id}",
        authorization=authorization,
        correlation_id=correlation_id,
    )
    return GoalsListResponse(**data)


@router.put("/{hired_instance_id}/goals", response_model=GoalInstanceResponse)
async def upsert_goal(
    hired_instance_id: str,
    body: GoalInstanceUpsertRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> GoalInstanceResponse:
    authorization = request.headers.get("Authorization")
    correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("x-correlation-id")

    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    payload = {
        "customer_id": current_user.id,
        "goal_instance_id": body.goal_instance_id,
        "goal_template_id": body.goal_template_id,
        "frequency": body.frequency,
        "settings": body.settings,
    }

    data = await _plant_put_json(
        url=f"{base}/api/v1/hired-agents/{hired_instance_id}/goals",
        authorization=authorization,
        correlation_id=correlation_id,
        payload=payload,
    )
    return GoalInstanceResponse(**data)


@router.delete("/{hired_instance_id}/goals")
async def delete_goal(
    hired_instance_id: str,
    goal_instance_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> dict:
    authorization = request.headers.get("Authorization")
    correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("x-correlation-id")

    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    url = (
        f"{base}/api/v1/hired-agents/{hired_instance_id}/goals"
        f"?customer_id={current_user.id}&goal_instance_id={goal_instance_id}"
    )
    return await _plant_delete_json(url=url, authorization=authorization, correlation_id=correlation_id)


@router.get("/{hired_instance_id}/deliverables", response_model=DeliverablesListResponse)
async def list_deliverables(
    hired_instance_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> DeliverablesListResponse:
    authorization = request.headers.get("Authorization")
    correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("x-correlation-id")

    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    data = await _plant_get_json(
        url=f"{base}/api/v1/hired-agents/{hired_instance_id}/deliverables?customer_id={current_user.id}",
        authorization=authorization,
        correlation_id=correlation_id,
    )
    return DeliverablesListResponse(**data)


@router.post("/deliverables/{deliverable_id}/review", response_model=ReviewDeliverableResponse)
async def review_deliverable(
    deliverable_id: str,
    body: ReviewDeliverableRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> ReviewDeliverableResponse:
    authorization = request.headers.get("Authorization")
    correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("x-correlation-id")

    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    payload: dict[str, Any] = {
        "customer_id": current_user.id,
        "decision": body.decision,
        "notes": body.notes,
        "approval_id": body.approval_id,
    }

    data = await _plant_post_json(
        url=f"{base}/api/v1/deliverables/{deliverable_id}/review",
        authorization=authorization,
        correlation_id=correlation_id,
        payload=payload,
    )
    return ReviewDeliverableResponse(**data)


@router.post("/deliverables/{deliverable_id}/execute", response_model=ExecuteDeliverableResponse)
async def execute_deliverable(
    deliverable_id: str,
    body: ExecuteDeliverableRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> ExecuteDeliverableResponse:
    authorization = request.headers.get("Authorization")
    correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("x-correlation-id")

    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    payload: dict[str, Any] = {"customer_id": current_user.id, "approval_id": body.approval_id}

    data = await _plant_post_json(
        url=f"{base}/api/v1/deliverables/{deliverable_id}/execute",
        authorization=authorization,
        correlation_id=correlation_id,
        payload=payload,
    )
    return ExecuteDeliverableResponse(**data)
