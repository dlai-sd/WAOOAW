"""CP BackEnd — Approval-queue proxy routes (CP-MOULD-1 Iteration 1, Epic E2).

Thin proxy: forwards deliverable approval requests to Plant BackEnd.
No business logic here — CP BackEnd is a proxy only.

Routes (prefix /cp/hired-agents):
  GET  /cp/hired-agents/{id}/approval-queue                              → GET  /api/v1/hired-agents/{id}/deliverables?status=pending_review
  POST /cp/hired-agents/{id}/approval-queue/{deliverable_id}/approve     → PATCH /api/v1/deliverables/{deliverable_id}/status {"status":"approved"}
  POST /cp/hired-agents/{id}/approval-queue/{deliverable_id}/reject      → PATCH /api/v1/deliverables/{deliverable_id}/status {"status":"rejected"}
"""
from __future__ import annotations

import logging
import os

import httpx
from fastapi import Header, HTTPException, Request

from core.routing import waooaw_router

logger = logging.getLogger(__name__)

router = waooaw_router(prefix="/cp/hired-agents", tags=["cp-approvals"])


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


async def _plant_patch_json(
    *, url: str, body: dict, authorization: str | None, correlation_id: str | None
) -> dict | list:
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if authorization:
        headers["Authorization"] = authorization
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.patch(url, json=body, headers=headers)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/{hired_agent_id}/approval-queue")
async def get_approval_queue(
    hired_agent_id: str,
    request: Request,
    authorization: str | None = Header(None),
) -> dict | list:
    """Returns deliverables with status=pending_review for this hired agent.

    Proxies to Plant GET /v1/hired-agents/{id}/deliverables?status=pending_review.
    Mobile TrialDashboardScreen calls this to render the approval queue section.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return await _plant_get_json(
        url=f"{base}/api/v1/hired-agents/{hired_agent_id}/deliverables?status=pending_review",
        authorization=authorization,
        correlation_id=request.headers.get("X-Correlation-ID"),
    )


@router.post("/{hired_agent_id}/approval-queue/{deliverable_id}/approve")
async def approve_deliverable(
    hired_agent_id: str,
    deliverable_id: str,
    request: Request,
    authorization: str | None = Header(None),
) -> dict | list:
    """Customer approves a pending deliverable — triggers publish to the channel.

    Proxies to Plant PATCH /v1/deliverables/{deliverable_id}/status
    with body {"status": "approved"}.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return await _plant_patch_json(
        url=f"{base}/api/v1/deliverables/{deliverable_id}/status",
        body={"status": "approved", "hired_agent_id": hired_agent_id},
        authorization=authorization,
        correlation_id=request.headers.get("X-Correlation-ID"),
    )


@router.post("/{hired_agent_id}/approval-queue/{deliverable_id}/reject")
async def reject_deliverable(
    hired_agent_id: str,
    deliverable_id: str,
    request: Request,
    authorization: str | None = Header(None),
) -> dict | list:
    """Customer rejects a deliverable — marks it as rejected, no publish.

    Proxies to Plant PATCH /v1/deliverables/{deliverable_id}/status
    with body {"status": "rejected"}.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return await _plant_patch_json(
        url=f"{base}/api/v1/deliverables/{deliverable_id}/status",
        body={"status": "rejected", "hired_agent_id": hired_agent_id},
        authorization=authorization,
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
