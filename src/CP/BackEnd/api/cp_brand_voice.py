"""CP brand voice proxy — CP-WIZ-1 E1-S2."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.auth.dependencies import get_current_user
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from models.user import User
from services.audit_dependency import AuditLogger, get_audit_logger
from services.plant_client import ServiceUnavailableError
from services.plant_gateway_client import PlantGatewayClient

router = waooaw_router(prefix="/cp/brand-voice", tags=["cp-brand-voice"])

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())


class BrandVoiceRequest(BaseModel):
    tone_keywords: list[str] = Field(default_factory=list)
    vocabulary_preferences: list[str] = Field(default_factory=list)
    messaging_patterns: list[str] = Field(default_factory=list)
    example_phrases: list[str] = Field(default_factory=list)
    voice_description: str = ""


def get_plant_gateway_client() -> PlantGatewayClient:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base_url:
        raise HTTPException(status_code=503, detail="PLANT_GATEWAY_URL not configured")
    return PlantGatewayClient(base_url=base_url)


def _forward_headers(request: Request) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    if auth := request.headers.get("authorization"):
        headers["Authorization"] = auth
    if cid := request.headers.get("x-correlation-id"):
        headers["X-Correlation-ID"] = cid
    return headers


@router.get("")
async def get_brand_voice(
    request: Request,
    _: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(get_plant_gateway_client),
) -> Dict[str, Any]:
    """Proxy the current user's brand voice."""
    try:
        response = await plant.request_json(
            method="GET",
            path="/api/v1/brand-voice/me",
            headers=_forward_headers(request),
        )
    except ServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if response.status_code >= 500:
        raise HTTPException(status_code=503, detail="UPSTREAM_ERROR")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json)
    return response.json if isinstance(response.json, dict) else {}


@router.put("")
async def put_brand_voice(
    payload: BrandVoiceRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(get_plant_gateway_client),
    audit: AuditLogger = Depends(get_audit_logger),
) -> Dict[str, Any]:
    """Proxy brand voice upsert for the current user."""
    try:
        response = await plant.request_json(
            method="PUT",
            path="/api/v1/brand-voice/me",
            headers=_forward_headers(request),
            json_body=payload.model_dump(),
        )
    except ServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if response.status_code >= 500:
        raise HTTPException(status_code=503, detail="UPSTREAM_ERROR")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json)

    await audit.log("cp_brand_voice", "brand_voice_updated", "success", user_id=current_user.id)
    return response.json if isinstance(response.json, dict) else {}
