"""CP trading setup proxy (feat/share-trader-setup-chat). Pattern B.

Thin proxy forwarding trading setup GET/POST to Plant BackEnd.
CP injects customer_id from JWT — never stores setup state locally.
"""
from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.auth.dependencies import get_current_user
from core.routing import waooaw_router
from models.user import User
from services.plant_gateway_client import PlantGatewayClient, ServiceUnavailableError

router = waooaw_router(prefix="/cp/trading-setup", tags=["cp-trading-setup"])


def _customer_id(user: User) -> str:
    return str(user.id)


def _plant_client() -> PlantGatewayClient:
    base = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base:
        raise HTTPException(status_code=503, detail="PLANT_GATEWAY_URL not configured")
    return PlantGatewayClient(base_url=base, timeout_seconds=20.0)


def _fwd(request: Request) -> Dict[str, str]:
    h: Dict[str, str] = {}
    for hdr in ("authorization", "x-correlation-id", "x-debug-trace"):
        v = request.headers.get(hdr)
        if v:
            h[hdr.title()] = v
    return h


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


@router.get("/{hired_instance_id}", response_model=Dict[str, Any])
async def get_trading_setup(
    hired_instance_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(_plant_client),
) -> Dict[str, Any]:
    try:
        resp = await plant.request_json(
            method="GET",
            path=f"api/v1/hired-agents/{hired_instance_id}/trading-setup",
            headers=_fwd(request),
            params={"customer_id": _customer_id(current_user)},
        )
    except ServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.json)
    return resp.json


@router.post("/{hired_instance_id}/message", response_model=Dict[str, Any])
async def send_trading_setup_message(
    hired_instance_id: str,
    body: SendMessageRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(_plant_client),
) -> Dict[str, Any]:
    try:
        resp = await plant.request_json(
            method="POST",
            path=f"api/v1/hired-agents/{hired_instance_id}/trading-setup/message",
            headers=_fwd(request),
            json_body={
                "content": body.content,
                "customer_id": _customer_id(current_user),
            },
        )
    except ServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.json)
    return resp.json


@router.post("/{hired_instance_id}/emergency-stop", response_model=Dict[str, Any])
async def cp_emergency_stop(
    hired_instance_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(_plant_client),
) -> Dict[str, Any]:
    """Proxy emergency-stop request to Plant BackEnd (ST-MVP-1 S10). Pattern B."""
    try:
        resp = await plant.request_json(
            method="POST",
            path=f"api/v1/hired-agents/{hired_instance_id}/emergency-stop",
            headers=_fwd(request),
            json_body={"customer_id": _customer_id(current_user)},
        )
    except ServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.json)
    return resp.json
