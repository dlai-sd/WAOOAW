from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from api.auth.dependencies import get_current_user
from core.routing import waooaw_router
from models.user import User
from services.plant_gateway_client import PlantGatewayClient, ServiceUnavailableError


router = waooaw_router(prefix="/cp/youtube-connections", tags=["cp-youtube-connections"])


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


class StartYouTubeConnectRequest(BaseModel):
    redirect_uri: str = Field(..., min_length=1)


class FinalizeYouTubeConnectRequest(BaseModel):
    state: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    redirect_uri: str = Field(..., min_length=1)


class AttachYouTubeConnectionRequest(BaseModel):
    hired_instance_id: str = Field(..., min_length=1)
    skill_id: str = Field(..., min_length=1)
    platform_key: str = Field(default="youtube", min_length=1)


@router.post("/connect/start", status_code=status.HTTP_201_CREATED)
async def start_youtube_connect(
    body: StartYouTubeConnectRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(get_plant_gateway_client),
) -> Dict[str, Any]:
    try:
        resp = await plant.request_json(
            method="POST",
            path="api/v1/customer-platform-connections/youtube/connect/start",
            headers=_forward_headers(request),
            json_body={
                "customer_id": _customer_id_from_user(current_user),
                "redirect_uri": body.redirect_uri,
            },
        )
    except ServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    _raise_for_gateway_response(resp)
    return resp.json if isinstance(resp.json, dict) else {"detail": resp.json}


@router.post("/connect/finalize")
async def finalize_youtube_connect(
    body: FinalizeYouTubeConnectRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(get_plant_gateway_client),
) -> Dict[str, Any]:
    try:
        resp = await plant.request_json(
            method="POST",
            path="api/v1/customer-platform-connections/youtube/connect/finalize",
            headers=_forward_headers(request),
            json_body={
                "customer_id": _customer_id_from_user(current_user),
                "state": body.state,
                "code": body.code,
                "redirect_uri": body.redirect_uri,
            },
        )
    except ServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    _raise_for_gateway_response(resp)
    return resp.json if isinstance(resp.json, dict) else {"detail": resp.json}


@router.get("")
async def list_youtube_connections(
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(get_plant_gateway_client),
) -> List[Dict[str, Any]]:
    try:
        resp = await plant.request_json(
            method="GET",
            path=f"api/v1/customer-platform-connections/{_customer_id_from_user(current_user)}",
            headers=_forward_headers(request),
            params={"platform_key": "youtube"},
        )
    except ServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    _raise_for_gateway_response(resp)
    return resp.json if isinstance(resp.json, list) else []


@router.get("/{credential_id}")
async def get_youtube_connection(
    credential_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(get_plant_gateway_client),
) -> Dict[str, Any]:
    try:
        resp = await plant.request_json(
            method="GET",
            path=f"api/v1/customer-platform-connections/{_customer_id_from_user(current_user)}/{credential_id}",
            headers=_forward_headers(request),
        )
    except ServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    _raise_for_gateway_response(resp)
    return resp.json if isinstance(resp.json, dict) else {"detail": resp.json}


@router.post("/{credential_id}/attach")
async def attach_youtube_connection(
    credential_id: str,
    body: AttachYouTubeConnectionRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(get_plant_gateway_client),
) -> Dict[str, Any]:
    try:
        resp = await plant.request_json(
            method="POST",
            path=f"api/v1/customer-platform-connections/{credential_id}/attach",
            headers=_forward_headers(request),
            json_body={
                "customer_id": _customer_id_from_user(current_user),
                "hired_instance_id": body.hired_instance_id,
                "skill_id": body.skill_id,
                "platform_key": body.platform_key,
            },
        )
    except ServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    _raise_for_gateway_response(resp)
    return resp.json if isinstance(resp.json, dict) else {"detail": resp.json}