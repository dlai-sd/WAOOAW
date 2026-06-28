"""CP trading performance & recommendations proxy (TRADER-FULL-1 It2 S1+S3). Pattern B.

Forwards trade-performance and recommendations reads to Plant BackEnd.
CP injects nothing extra — Plant owns all data.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, Request

from api.auth.dependencies import get_current_user
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from models.user import User
from services.plant_gateway_client import PlantGatewayClient

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())

router = waooaw_router(prefix="/cp/trading", tags=["cp-trading-performance"])


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


@router.get("/performance/{hired_instance_id}", response_model=Dict[str, Any])
async def get_trade_performance(
    hired_instance_id: str,
    period_days: int = 90,
    request: Request = ...,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(_plant_client),
) -> Dict[str, Any]:
    """Proxy GET /api/v1/hired-agents/{id}/trade-performance to Plant BackEnd."""
    resp = await plant.request_json(
        method="GET",
        path=f"api/v1/hired-agents/{hired_instance_id}/trade-performance",
        headers=_headers(request),
        params={"period_days": str(period_days)},
    )
    if resp.status_code >= 500:
        raise HTTPException(status_code=503, detail="UPSTREAM_ERROR")
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json)
    return resp.json if isinstance(resp.json, dict) else {}


@router.get("/recommendations/{hired_instance_id}", response_model=Dict[str, Any])
async def get_recommendations(
    hired_instance_id: str,
    sample_size: int = 20,
    request: Request = ...,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(_plant_client),
) -> Dict[str, Any]:
    """Proxy GET /api/v1/hired-agents/{id}/recommendations to Plant BackEnd."""
    resp = await plant.request_json(
        method="GET",
        path=f"api/v1/hired-agents/{hired_instance_id}/recommendations",
        headers=_headers(request),
        params={"sample_size": str(sample_size)},
    )
    if resp.status_code >= 500:
        raise HTTPException(status_code=503, detail="UPSTREAM_ERROR")
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json)
    return resp.json if isinstance(resp.json, dict) else {}


@router.get("/history/{hired_instance_id}", response_model=Dict[str, Any])
async def get_trade_history(
    hired_instance_id: str,
    page: int = 1,
    page_size: int = 20,
    request: Request = ...,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(_plant_client),
) -> Dict[str, Any]:
    """Proxy GET /api/v1/hired-agents/{id}/trade-history to Plant BackEnd (ST-MVP-1 S11)."""
    resp = await plant.request_json(
        method="GET",
        path=f"api/v1/hired-agents/{hired_instance_id}/trade-history",
        headers=_headers(request),
        params={"page": str(page), "page_size": str(page_size)},
    )
    if resp.status_code >= 500:
        raise HTTPException(status_code=503, detail="UPSTREAM_ERROR")
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json)
    return resp.json if isinstance(resp.json, dict) else {}


@router.get("/tax-report/{hired_instance_id}", response_model=Dict[str, Any])
async def get_tax_report(
    hired_instance_id: str,
    year: int = 2026,
    period: str = "monthly",
    month: Optional[int] = None,
    quarter: Optional[str] = None,
    request: Request = ...,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(_plant_client),
) -> Dict[str, Any]:
    """Proxy GET /api/v1/hired-agents/{id}/tax-report to Plant BackEnd (ST-MVP-1 S12)."""
    params: Dict[str, str] = {"year": str(year), "period": period}
    if month is not None:
        params["month"] = str(month)
    if quarter is not None:
        params["quarter"] = quarter
    resp = await plant.request_json(
        method="GET",
        path=f"api/v1/hired-agents/{hired_instance_id}/tax-report",
        headers=_headers(request),
        params=params,
    )
    if resp.status_code >= 500:
        raise HTTPException(status_code=503, detail="UPSTREAM_ERROR")
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json)
    return resp.json if isinstance(resp.json, dict) else {}
