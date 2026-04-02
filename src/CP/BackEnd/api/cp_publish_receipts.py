"""CP Publish Receipts proxy — CP-WIZ-1 E4-S2."""
from __future__ import annotations

import logging
import os
from typing import Dict

from fastapi import Depends, HTTPException, Request

from api.auth.dependencies import get_current_user
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from models.user import User
from services.plant_client import ServiceUnavailableError
from services.plant_gateway_client import PlantGatewayClient

router = waooaw_router(prefix="/cp/publish-receipts", tags=["cp-publish-receipts"])

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
async def list_publish_receipts(
    hired_instance_id: str,
    request: Request,
    _: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(get_plant_gateway_client),
):
    """Proxy publish receipt history from Plant."""
    try:
        resp = await plant.request_json(
            method="GET",
            path=f"/api/v1/publish-receipts/{hired_instance_id}",
            headers=_forward_headers(request),
        )
    except ServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if resp.status_code >= 500:
        raise HTTPException(status_code=503, detail="UPSTREAM_ERROR")
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json)

    logger.info("CP proxied publish receipts for hired_instance_id=%s", hired_instance_id)
    return resp.json
