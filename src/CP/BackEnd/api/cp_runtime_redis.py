from __future__ import annotations

import os

from fastapi import HTTPException

from core.routing import waooaw_router
from services.plant_gateway_client import PlantGatewayClient, ServiceUnavailableError

router = waooaw_router(prefix="/cp/runtime/redis", tags=["cp-runtime-redis"])


def _plant_base_url() -> str:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base_url:
        raise HTTPException(status_code=503, detail="PLANT_GATEWAY_URL not configured")
    return base_url


async def _proxy_runtime(path: str):
    client = PlantGatewayClient(base_url=_plant_base_url())
    try:
        response = await client.request_json(method="GET", path=path)
    except ServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail="Plant runtime unavailable") from exc

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.json)
    return response.json


@router.get("/health")
async def get_redis_health():
    return await _proxy_runtime("/api/v1/runtime/redis/health")


@router.get("/config")
async def get_redis_config():
    return await _proxy_runtime("/api/v1/runtime/redis/config")
