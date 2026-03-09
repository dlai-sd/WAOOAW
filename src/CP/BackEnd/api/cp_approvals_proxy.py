"""CP BackEnd — Approval-queue proxy routes (CP-MOULD-1 Iteration 1, Epic E2).

Thin proxy: forwards deliverable approval requests to Plant BackEnd.
No business logic here — CP BackEnd is a proxy only.

Routes (prefix /cp/hired-agents):
    GET  /cp/hired-agents/{id}/approval-queue                              → GET  /api/v1/hired-agents/{id}/deliverables?status=pending_review&customer_id={user.id}
    POST /cp/hired-agents/{id}/approval-queue/{deliverable_id}/approve     → POST /api/v1/deliverables/{deliverable_id}/review {"decision":"approved","customer_id":user.id}
    POST /cp/hired-agents/{id}/approval-queue/{deliverable_id}/reject      → POST /api/v1/deliverables/{deliverable_id}/review {"decision":"rejected","customer_id":user.id}
"""
from __future__ import annotations

import logging
import os

import httpx
from fastapi import Depends, Header, HTTPException, Request

from api.auth.dependencies import get_current_user
from core.routing import waooaw_router
from models.user import User

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

@router.get("/{hired_agent_id}/approval-queue")
async def get_approval_queue(
    hired_agent_id: str,
    request: Request,
    authorization: str | None = Header(None),
    current_user: User = Depends(get_current_user),
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
        url=f"{base}/api/v1/hired-agents/{hired_agent_id}/deliverables?status=pending_review&customer_id={current_user.id}",
        authorization=authorization,
        correlation_id=request.headers.get("X-Correlation-ID"),
    )


@router.post("/{hired_agent_id}/approval-queue/{deliverable_id}/approve")
async def approve_deliverable(
    hired_agent_id: str,
    deliverable_id: str,
    request: Request,
    authorization: str | None = Header(None),
    current_user: User = Depends(get_current_user),
) -> dict | list:
    """Customer approves a pending deliverable — triggers publish to the channel.

    Proxies to Plant POST /api/v1/deliverables/{deliverable_id}/review
    with body {"decision": "approved", "customer_id": current_user.id}.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return await _plant_post_json(
        url=f"{base}/api/v1/deliverables/{deliverable_id}/review",
        body={
            "customer_id": current_user.id,
            "decision": "approved",
            "notes": "",
        },
        authorization=authorization,
        correlation_id=request.headers.get("X-Correlation-ID"),
    )


@router.post("/{hired_agent_id}/approval-queue/{deliverable_id}/reject")
async def reject_deliverable(
    hired_agent_id: str,
    deliverable_id: str,
    request: Request,
    authorization: str | None = Header(None),
    current_user: User = Depends(get_current_user),
) -> dict | list:
    """Customer rejects a deliverable — marks it as rejected, no publish.

    Proxies to Plant POST /api/v1/deliverables/{deliverable_id}/review
    with body {"decision": "rejected", "customer_id": current_user.id}.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return await _plant_post_json(
        url=f"{base}/api/v1/deliverables/{deliverable_id}/review",
        body={
            "customer_id": current_user.id,
            "decision": "rejected",
            "notes": "",
        },
        authorization=authorization,
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
