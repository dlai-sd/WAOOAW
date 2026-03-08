"""CP BackEnd — Flow-run + component-run proxy routes (EXEC-ENGINE-001 Iteration 6, Epic E14-S2).

Thin proxy: forwards flow-run and approval requests to Plant Gateway.
No business logic here — CP BackEnd is a proxy only.

Routes (prefix /cp):
  GET  /cp/flow-runs                                     → GET  /v1/flow-runs?customer_id={user.id}&...
  GET  /cp/flow-runs/{flow_run_id}                       → GET  /v1/flow-runs/{id} (ownership checked)
  POST /cp/approvals/{flow_run_id}/approve               → POST /v1/approvals/{id}/approve (ownership checked)
  POST /cp/approvals/{flow_run_id}/reject                → POST /v1/approvals/{id}/reject (ownership checked)
  GET  /cp/component-runs                                → GET  /v1/component-runs?flow_run_id={id} (ownership checked)
"""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from fastapi import Depends, HTTPException, Request, status

from api.auth.dependencies import get_current_user
from core.routing import waooaw_router
from models.user import User

logger = logging.getLogger(__name__)

router = waooaw_router(prefix="/cp", tags=["flow-runs"])


# ─── Plant connection helpers ─────────────────────────────────────────────────

def _plant_base_url() -> str:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base_url:
        raise RuntimeError("PLANT_GATEWAY_URL not configured")
    return base_url


async def _plant_get_json(
    *,
    url: str,
    authorization: str | None,
    correlation_id: str | None,
    params: dict[str, Any] | None = None,
) -> dict | list:
    headers: dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=headers, params=params)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


async def _plant_post_json(
    *,
    url: str,
    authorization: str | None,
    correlation_id: str | None,
) -> dict | list:
    headers: dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/flow-runs")
async def list_flow_runs(
    request: Request,
    hired_instance_id: str | None = None,
    flow_status: str | None = None,
    current_user: User = Depends(get_current_user),
) -> dict | list:
    """List flow runs owned by the authenticated customer.

    Proxies to Plant GET /v1/flow-runs with customer_id injected automatically.
    """
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    params: dict[str, Any] = {"customer_id": current_user.id}
    if hired_instance_id:
        params["hired_instance_id"] = hired_instance_id
    if flow_status:
        params["status"] = flow_status

    authorization = request.headers.get("Authorization")
    correlation_id = request.headers.get("X-Correlation-ID")
    return await _plant_get_json(
        url=f"{base}/v1/flow-runs",
        authorization=authorization,
        correlation_id=correlation_id,
        params=params,
    )


@router.get("/flow-runs/{flow_run_id}")
async def get_flow_run(
    flow_run_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> dict | list:
    """Get a single flow run — returns 403 if customer does not own it."""
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    authorization = request.headers.get("Authorization")
    correlation_id = request.headers.get("X-Correlation-ID")
    data = await _plant_get_json(
        url=f"{base}/v1/flow-runs/{flow_run_id}",
        authorization=authorization,
        correlation_id=correlation_id,
    )
    if isinstance(data, dict) and data.get("customer_id") != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return data


@router.post("/approvals/{flow_run_id}/approve")
async def approve_flow_run(
    flow_run_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> dict | list:
    """Approve a flow run awaiting customer approval — ownership checked before proxying."""
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    authorization = request.headers.get("Authorization")
    correlation_id = request.headers.get("X-Correlation-ID")

    fr = await _plant_get_json(
        url=f"{base}/v1/flow-runs/{flow_run_id}",
        authorization=authorization,
        correlation_id=correlation_id,
    )
    if isinstance(fr, dict) and fr.get("customer_id") != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return await _plant_post_json(
        url=f"{base}/v1/approvals/{flow_run_id}/approve",
        authorization=authorization,
        correlation_id=correlation_id,
    )


@router.post("/approvals/{flow_run_id}/reject")
async def reject_flow_run(
    flow_run_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> dict | list:
    """Reject a flow run awaiting customer approval — ownership checked before proxying."""
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    authorization = request.headers.get("Authorization")
    correlation_id = request.headers.get("X-Correlation-ID")

    fr = await _plant_get_json(
        url=f"{base}/v1/flow-runs/{flow_run_id}",
        authorization=authorization,
        correlation_id=correlation_id,
    )
    if isinstance(fr, dict) and fr.get("customer_id") != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return await _plant_post_json(
        url=f"{base}/v1/approvals/{flow_run_id}/reject",
        authorization=authorization,
        correlation_id=correlation_id,
    )


@router.get("/component-runs")
async def list_component_runs(
    flow_run_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> dict | list:
    """List component runs for a flow run — ownership verified via parent flow_run."""
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    authorization = request.headers.get("Authorization")
    correlation_id = request.headers.get("X-Correlation-ID")

    fr = await _plant_get_json(
        url=f"{base}/v1/flow-runs/{flow_run_id}",
        authorization=authorization,
        correlation_id=correlation_id,
    )
    if isinstance(fr, dict) and fr.get("customer_id") != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return await _plant_get_json(
        url=f"{base}/v1/component-runs",
        authorization=authorization,
        correlation_id=correlation_id,
        params={"flow_run_id": flow_run_id},
    )
