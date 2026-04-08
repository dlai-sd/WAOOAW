from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.auth.dependencies import get_current_user
from core.routing import waooaw_router
from models.user import User
from services.plant_gateway_client import PlantGatewayClient, ServiceUnavailableError


router = waooaw_router(prefix="/cp/digital-marketing-activation", tags=["cp-digital-marketing-activation"])


def _customer_id_from_user(user: User) -> str:
    return str(user.id)


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
    return headers


def _unwrap_gateway_error_detail(detail: Any) -> Any:
    if isinstance(detail, str):
        try:
            import json

            return json.loads(detail)
        except Exception:
            return detail
    return detail


def _sanitize_upstream_failure_detail(detail: Any) -> str:
    unwrapped = _unwrap_gateway_error_detail(detail)
    if isinstance(unwrapped, dict):
        candidate = str(
            unwrapped.get("detail")
            or unwrapped.get("message")
            or unwrapped.get("error")
            or ""
        ).strip()
    else:
        candidate = str(unwrapped or "").strip()

    lowered = candidate.lower()
    if not candidate:
        return "Digital marketing activation upstream failure"
    if any(token in lowered for token in ["traceback", "xai_api_key", "api key", "sk-", "bearer ", "password", "secret"]):
        return "UPSTREAM_ERROR"
    if lowered in {"internal server error", "upstream_error"}:
        return "Digital marketing activation upstream failure"
    return candidate[:240]


def _raise_for_gateway_response(resp: Any) -> None:
    if resp.status_code >= 500:
        raise HTTPException(status_code=503, detail=_sanitize_upstream_failure_detail(resp.json))
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=_unwrap_gateway_error_detail(resp.json))


class ActivationWorkspaceUpsertRequest(BaseModel):
    workspace: dict[str, Any] = Field(default_factory=dict)


class ThemePlanGenerateRequest(BaseModel):
    workspace: dict[str, Any] = Field(default_factory=dict)
    campaign_setup: dict[str, Any] = Field(default_factory=dict)


class ThemePlanUpdateRequest(BaseModel):
    master_theme: str = Field(..., min_length=1)
    derived_themes: list[dict[str, Any]] = Field(default_factory=list)
    campaign_setup: dict[str, Any] = Field(default_factory=dict)


@router.get("/{hired_instance_id}")
async def get_activation_workspace(
    hired_instance_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(get_plant_gateway_client),
) -> Dict[str, Any]:
    try:
        resp = await plant.request_json(
            method="GET",
            path=f"api/v1/hired-agents/{hired_instance_id}/digital-marketing-activation",
            headers=_forward_headers(request),
            params={"customer_id": _customer_id_from_user(current_user)},
        )
    except ServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    _raise_for_gateway_response(resp)
    return resp.json if isinstance(resp.json, dict) else {"detail": resp.json}


@router.put("/{hired_instance_id}")
async def upsert_activation_workspace(
    hired_instance_id: str,
    body: ActivationWorkspaceUpsertRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(get_plant_gateway_client),
) -> Dict[str, Any]:
    try:
        resp = await plant.request_json(
            method="PUT",
            path=f"api/v1/hired-agents/{hired_instance_id}/digital-marketing-activation",
            headers=_forward_headers(request),
            json_body={
                "customer_id": _customer_id_from_user(current_user),
                "workspace": body.workspace,
            },
        )
    except ServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    _raise_for_gateway_response(resp)
    return resp.json if isinstance(resp.json, dict) else {"detail": resp.json}


@router.post("/{hired_instance_id}/generate-theme-plan")
async def generate_theme_plan(
    hired_instance_id: str,
    body: ThemePlanGenerateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(get_plant_gateway_client),
) -> Dict[str, Any]:
    try:
        resp = await plant.request_json(
            method="POST",
            path=f"api/v1/digital-marketing-activation/{hired_instance_id}/generate-theme-plan",
            headers=_forward_headers(request),
            json_body={
                **body.model_dump(mode="json", exclude_none=True),
                "customer_id": _customer_id_from_user(current_user),
            },
        )
    except ServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    _raise_for_gateway_response(resp)
    return resp.json if isinstance(resp.json, dict) else {"detail": resp.json}


@router.patch("/{hired_instance_id}/theme-plan")
async def update_theme_plan(
    hired_instance_id: str,
    body: ThemePlanUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(get_plant_gateway_client),
) -> Dict[str, Any]:
    try:
        resp = await plant.request_json(
            method="PATCH",
            path=f"api/v1/digital-marketing-activation/{hired_instance_id}/theme-plan",
            headers=_forward_headers(request),
            json_body={
                **body.model_dump(mode="json", exclude_none=True),
                "customer_id": _customer_id_from_user(current_user),
            },
        )
    except ServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    _raise_for_gateway_response(resp)
    return resp.json if isinstance(resp.json, dict) else {"detail": resp.json}