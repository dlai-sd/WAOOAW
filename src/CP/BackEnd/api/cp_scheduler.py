"""CP BackEnd — Scheduler and trial-budget proxy routes (CP-MOULD-1 Iteration 1, Epic E1).

Thin proxy: forwards scheduler and trial-budget requests to Plant BackEnd.
No business logic here — CP BackEnd is a proxy only.

Routes (prefix /cp/hired-agents):
  GET  /cp/hired-agents/{id}/scheduler-summary  → GET  /api/v1/hired-agents/{id}/scheduler-diagnostics
  GET  /cp/hired-agents/{id}/trial-budget        → GET  /api/v1/hired-agents/{id}/trial-budget
  POST /cp/hired-agents/{id}/pause               → POST /api/v1/hired-agents/{id}/pause
  POST /cp/hired-agents/{id}/resume              → POST /api/v1/hired-agents/{id}/resume
"""
from __future__ import annotations

import logging
import os

import httpx
from fastapi import Header, HTTPException, Request

from core.routing import waooaw_router

logger = logging.getLogger(__name__)

router = waooaw_router(
    prefix="/cp/hired-agents",
    tags=["cp-scheduler"],
)


# ─── Plant connection helpers ─────────────────────────────────────────────────

def _plant_base_url() -> str:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base_url:
        raise RuntimeError("PLANT_GATEWAY_URL not configured")
    return base_url


async def _plant_get_json(
    *, url: str, authorization: str | None, correlation_id: str | None
) -> dict | list:
    headers: dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=headers)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


async def _plant_post_json(
    *, url: str, body: dict, authorization: str | None, correlation_id: str | None
) -> dict | list:
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if authorization:
        headers["Authorization"] = authorization
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=body, headers=headers)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/{hired_agent_id}/scheduler-summary")
async def get_scheduler_summary(
    hired_agent_id: str,
    request: Request,
    authorization: str | None = Header(None),
) -> dict | list:
    """Proxy to Plant GET /v1/hired-agents/{id}/scheduler-diagnostics.

    Returns scheduler health snapshot for the mobile SchedulerSummaryCard component.
    CP BackEnd adds no data — it forwards auth and returns Plant's response verbatim.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return await _plant_get_json(
        url=f"{base}/api/v1/hired-agents/{hired_agent_id}/scheduler-diagnostics",
        authorization=authorization,
        correlation_id=request.headers.get("X-Correlation-ID"),
    )


@router.get("/{hired_agent_id}/trial-budget")
async def get_trial_budget(
    hired_agent_id: str,
    request: Request,
    authorization: str | None = Header(None),
) -> dict | list:
    """Proxy to Plant GET /v1/hired-agents/{id}/trial-budget.

    Returns trial_task_limit, tasks_used, trial_ends_at for the mobile TrialGauge.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return await _plant_get_json(
        url=f"{base}/api/v1/hired-agents/{hired_agent_id}/trial-budget",
        authorization=authorization,
        correlation_id=request.headers.get("X-Correlation-ID"),
    )


@router.post("/{hired_agent_id}/pause")
async def pause_agent(
    hired_agent_id: str,
    request: Request,
    authorization: str | None = Header(None),
) -> dict | list:
    """Pause scheduled execution for a hired agent.

    Proxies to Plant POST /v1/hired-agents/{id}/pause.
    Customer can pause their agent from the mobile app — no PP involvement needed.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return await _plant_post_json(
        url=f"{base}/api/v1/hired-agents/{hired_agent_id}/pause",
        body={},
        authorization=authorization,
        correlation_id=request.headers.get("X-Correlation-ID"),
    )


@router.post("/{hired_agent_id}/resume")
async def resume_agent(
    hired_agent_id: str,
    request: Request,
    authorization: str | None = Header(None),
) -> dict | list:
    """Resume scheduled execution for a previously paused agent.

    Proxies to Plant POST /v1/hired-agents/{id}/resume.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return await _plant_post_json(
        url=f"{base}/api/v1/hired-agents/{hired_agent_id}/resume",
        body={},
        authorization=authorization,
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
