"""CP exchange credentials proxy (TRADER-FULL-1 S3). Pattern B.

Forwards credential upsert/get to Plant BackEnd.
CP injects customer_id from JWT; never stores secrets locally.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.auth.dependencies import get_current_user
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from models.user import User
from services.plant_gateway_client import PlantGatewayClient

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())

router = waooaw_router(prefix="/cp/exchange-credentials", tags=["cp-exchange-credentials"])


def _customer_id(user: User) -> str:
    """Return canonical customer_id — plain UUID string, no prefix."""
    return str(user.id)


def _plant_client() -> PlantGatewayClient:
    base = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base:
        raise HTTPException(status_code=503, detail="PLANT_GATEWAY_URL not configured")
    return PlantGatewayClient(base_url=base)


def _headers(request: Request) -> Dict[str, str]:
    h: Dict[str, str] = {}
    auth = request.headers.get("authorization")
    if auth:
        h["Authorization"] = auth
    correlation = request.headers.get("x-correlation-id")
    if correlation:
        h["X-Correlation-ID"] = correlation
    debug = request.headers.get("x-debug-trace")
    if debug:
        h["X-Debug-Trace"] = debug
    return h


class UpsertExchangeCredentialRequest(BaseModel):
    exchange_provider: str = Field(default="delta_exchange_india")
    api_key: str = Field(..., min_length=1)
    api_secret: str = Field(..., min_length=1)
    default_coin: str = Field(..., min_length=1)
    allowed_coins: Optional[List[str]] = Field(default_factory=list)
    risk_limits: Optional[Dict[str, Any]] = Field(default_factory=dict)


PLACEHOLDER_HIRED_ID = "trader-default"


@router.post("", response_model=Dict[str, Any], status_code=201)
async def upsert_exchange_credential(
    body: UpsertExchangeCredentialRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(_plant_client),
) -> Dict[str, Any]:
    resp = await plant.request_json(
        method="POST",
        path=f"api/v1/hired-agents/{PLACEHOLDER_HIRED_ID}/exchange-credentials",
        headers=_headers(request),
        json_body={
            "customer_id": _customer_id(current_user),
            "exchange_provider": body.exchange_provider,
            "api_key": body.api_key,
            "api_secret": body.api_secret,
            "default_coin": body.default_coin,
            "allowed_coins": body.allowed_coins or [],
            "risk_limits": body.risk_limits or {},
        },
    )
    if resp.status_code >= 500:
        raise HTTPException(status_code=503, detail="UPSTREAM_ERROR")
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=resp.status_code, detail=resp.json)

    payload: Dict[str, Any] = resp.json if isinstance(resp.json, dict) else {}
    # Strip any accidental secret echo from Plant response before returning
    payload.pop("api_key", None)
    payload.pop("api_secret", None)
    payload.pop("encrypted_api_key", None)
    payload.pop("encrypted_api_secret", None)
    return payload


@router.get("", response_model=Optional[Dict[str, Any]])
async def get_exchange_credential(
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(_plant_client),
) -> Optional[Dict[str, Any]]:
    resp = await plant.request_json(
        method="GET",
        path=f"api/v1/hired-agents/{PLACEHOLDER_HIRED_ID}/exchange-credentials",
        headers=_headers(request),
        params={"customer_id": _customer_id(current_user)},
    )
    if resp.status_code >= 500:
        raise HTTPException(status_code=503, detail="UPSTREAM_ERROR")
    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json)
    return resp.json if isinstance(resp.json, dict) else None
