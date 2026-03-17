from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Literal

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.auth.dependencies import get_current_user
from core.routing import waooaw_router
from models.user import User
from services.plant_gateway_client import PlantGatewayClient, ServiceUnavailableError


router = waooaw_router(prefix="/cp/hired-agents", tags=["cp-hired-agent-studio"])

StudioMode = Literal["activation", "edit"]
StudioStepKey = Literal["identity", "connection", "operating_plan", "review"]


def _customer_id_from_user(user: User) -> str:
    return f"CUST-{user.id}"


def get_plant_gateway_client() -> PlantGatewayClient:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base_url:
        raise HTTPException(status_code=503, detail="PLANT_GATEWAY_URL not configured")
    return PlantGatewayClient(base_url=base_url)


def _forward_headers(request: Request) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    auth = request.headers.get("authorization")
    if auth:
        headers["Authorization"] = auth
    correlation = request.headers.get("x-correlation-id")
    if correlation:
        headers["X-Correlation-ID"] = correlation
    debug = request.headers.get("x-debug-trace")
    if debug:
        headers["X-Debug-Trace"] = debug
    return headers


def _unwrap_gateway_error_detail(detail: Any) -> Any:
    if isinstance(detail, str):
        try:
            import json

            return json.loads(detail)
        except Exception:
            return detail
    return detail


def _raise_for_gateway_response(resp: Any) -> None:
    if resp.status_code >= 500:
        raise HTTPException(status_code=503, detail="UPSTREAM_ERROR")
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=_unwrap_gateway_error_detail(resp.json))


class StudioStepResponse(BaseModel):
    key: StudioStepKey
    title: str
    complete: bool
    blocked: bool = False
    summary: str


class IdentityState(BaseModel):
    nickname: str | None = None
    theme: str | None = None
    complete: bool


class ConnectionState(BaseModel):
    platform_key: str | None = None
    skill_id: str | None = None
    connection_id: str | None = None
    customer_platform_credential_id: str | None = None
    status: str
    complete: bool
    summary: str


class OperatingPlanState(BaseModel):
    complete: bool
    goals_completed: bool
    goal_count: int
    skill_config_count: int
    summary: str


class ReviewState(BaseModel):
    complete: bool
    summary: str


class HiredAgentStudioResponse(BaseModel):
    hired_instance_id: str
    subscription_id: str
    agent_id: str
    agent_type_id: str
    customer_id: str | None = None
    mode: StudioMode
    selection_required: bool = False
    current_step: StudioStepKey
    steps: list[StudioStepResponse] = Field(default_factory=list)
    identity: IdentityState
    connection: ConnectionState
    operating_plan: OperatingPlanState
    review: ReviewState
    configured: bool
    goals_completed: bool
    trial_status: str
    subscription_status: str | None = None
    updated_at: datetime


class StudioIdentityUpdate(BaseModel):
    nickname: str | None = None
    theme: str | None = None


class StudioConnectionUpdate(BaseModel):
    platform_key: str = "youtube"
    skill_id: str = "default"
    customer_platform_credential_id: str | None = None
    secret_ref: str | None = None
    mark_connected: bool = False


class StudioOperatingPlanUpdate(BaseModel):
    config_patch: dict[str, Any] | None = None
    skill_id: str | None = None
    customer_fields: dict[str, Any] | None = None
    goals_completed: bool | None = None


class StudioReviewUpdate(BaseModel):
    goals_completed: bool | None = None
    finalize: bool = False


class StudioUpdateRequest(BaseModel):
    identity: StudioIdentityUpdate | None = None
    connection: StudioConnectionUpdate | None = None
    operating_plan: StudioOperatingPlanUpdate | None = None
    review: StudioReviewUpdate | None = None


@router.get("/{hired_instance_id}/studio", response_model=HiredAgentStudioResponse)
async def get_hired_agent_studio(
    hired_instance_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(get_plant_gateway_client),
) -> HiredAgentStudioResponse:
    try:
        resp = await plant.request_json(
            method="GET",
            path=f"api/v1/hired-agents/{hired_instance_id}/studio",
            headers=_forward_headers(request),
            params={"customer_id": _customer_id_from_user(current_user)},
        )
    except ServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    _raise_for_gateway_response(resp)
    payload = resp.json if isinstance(resp.json, dict) else {}
    return HiredAgentStudioResponse.model_validate(payload)


@router.patch("/{hired_instance_id}/studio", response_model=HiredAgentStudioResponse)
async def update_hired_agent_studio(
    hired_instance_id: str,
    body: StudioUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(get_plant_gateway_client),
) -> HiredAgentStudioResponse:
    payload = body.model_dump(mode="json", exclude_none=True)
    try:
        resp = await plant.request_json(
            method="PATCH",
            path=f"api/v1/hired-agents/{hired_instance_id}/studio",
            headers=_forward_headers(request),
            json_body={
                **payload,
                "customer_id": _customer_id_from_user(current_user),
            },
        )
    except ServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    _raise_for_gateway_response(resp)
    response_payload = resp.json if isinstance(resp.json, dict) else {}
    return HiredAgentStudioResponse.model_validate(response_payload)