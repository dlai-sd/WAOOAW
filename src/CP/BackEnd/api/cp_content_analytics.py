"""CP content analytics proxy — CP-WIZ-1 E1-S2."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict

from fastapi import Depends, HTTPException, Request

from api.auth.dependencies import get_current_user
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from models.user import User
from services.plant_client import ServiceUnavailableError
from services.plant_gateway_client import PlantGatewayClient

router = waooaw_router(prefix="/cp/content-recommendations", tags=["cp-content-recommendations"])

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())


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


@router.get("/{hired_instance_id}")
async def get_content_recommendations(
    hired_instance_id: str,
    request: Request,
    _: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(get_plant_gateway_client),
) -> Dict[str, Any]:
    """Proxy hired-agent content recommendations from Plant."""
    try:
        response = await plant.request_json(
            method="GET",
            path=f"/api/v1/hired-agents/{hired_instance_id}/content-recommendations",
            headers=_forward_headers(request),
        )
    except ServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if response.status_code >= 500:
        raise HTTPException(status_code=503, detail="UPSTREAM_ERROR")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json)
    return response.json if isinstance(response.json, dict) else {}
