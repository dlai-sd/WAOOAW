"""CP brand voice proxy — CP-WIZ-1 E1-S2."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

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


class BrandVoicePayload(BaseModel):
    tone_keywords: list[str] = Field(default_factory=list)
    vocabulary_preferences: list[str] = Field(default_factory=list)
    messaging_patterns: list[str] = Field(default_factory=list)
    example_phrases: list[str] = Field(default_factory=list)
    voice_description: str = ""

    model_config = ConfigDict(strict=True)


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


def _raise_for_upstream(resp: Any) -> None:
    if resp.status_code >= 500:
        raise HTTPException(status_code=503, detail="UPSTREAM_ERROR")
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json)


@router.get("")
async def get_brand_voice_proxy(
    request: Request,
    _: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(get_plant_gateway_client),
):
    """Proxy the authenticated customer's brand voice."""
    try:
        resp = await plant.request_json(
            method="GET",
            path="/api/v1/brand-voice/me",
            headers=_forward_headers(request),
        )
    except ServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    _raise_for_upstream(resp)
    return resp.json


@router.put("")
async def put_brand_voice_proxy(
    payload: BrandVoicePayload,
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(get_plant_gateway_client),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """Proxy brand voice upserts to Plant."""
    try:
        resp = await plant.request_json(
            method="PUT",
            path="/api/v1/brand-voice/me",
            headers=_forward_headers(request),
            json_body=payload.model_dump(),
        )
    except ServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    _raise_for_upstream(resp)
    await audit.log(
        "cp_brand_voice",
        "brand_voice_updated",
        "success",
        user_id=current_user.id,
    )
    logger.info("CP proxied brand voice upsert for user_id=%s", current_user.id)
    return resp.json
