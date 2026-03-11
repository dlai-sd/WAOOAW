"""CP BackEnd — Campaign proxy routes (PLANT-CONTENT-1 Iteration 4, Epic E8).

Thin proxy: forwards all campaign requests to Plant BackEnd.
No business logic here — CP BackEnd is a proxy only.

Routes (prefix /cp/campaigns):
  POST   /cp/campaigns                                              → POST   /api/v1/campaigns
  GET    /cp/campaigns/{campaign_id}                               → GET    /api/v1/campaigns/{id}
  GET    /cp/campaigns/{campaign_id}/theme-items                   → GET    /api/v1/campaigns/{id}/theme-items
  POST   /cp/campaigns/{campaign_id}/theme-items/approve           → POST   /api/v1/campaigns/{id}/theme-items/approve
  PATCH  /cp/campaigns/{campaign_id}/theme-items/{item_id}         → PATCH  /api/v1/campaigns/{id}/theme-items/{item_id}
  POST   /cp/campaigns/{campaign_id}/theme-items/{item_id}/generate-posts
                                                                   → POST   .../generate-posts
  GET    /cp/campaigns/{campaign_id}/posts                         → GET    /api/v1/campaigns/{id}/posts
  PATCH  /cp/campaigns/{campaign_id}/posts/{post_id}               → PATCH  /api/v1/campaigns/{id}/posts/{post_id}
  POST   /cp/campaigns/{campaign_id}/posts/{post_id}/publish       → POST   .../publish
"""
from __future__ import annotations

import os

import httpx
from fastapi import Depends, HTTPException, Query, Request

from api.auth.dependencies import get_current_user
from core.routing import waooaw_router
from models.user import User
from services.audit_dependency import AuditLogger, get_audit_logger

router = waooaw_router(prefix="/cp/campaigns", tags=["cp-campaigns"])


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
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Resource not found")
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


async def _plant_post_json(
    *, url: str, body: dict, authorization: str | None, correlation_id: str | None,
    status_code: int = 200,
) -> dict | list:
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if authorization:
        headers["Authorization"] = authorization
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=body, headers=headers)
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Resource not found")
        if resp.status_code == 409:
            raise HTTPException(status_code=409, detail=resp.text)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


async def _plant_patch_json(
    *, url: str, body: dict, authorization: str | None, correlation_id: str | None
) -> dict:
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if authorization:
        headers["Authorization"] = authorization
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.patch(url, json=body, headers=headers)
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Resource not found")
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("", status_code=201)
async def create_campaign(
    body: dict,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict | list:
    """Create a campaign. Proxies POST /api/v1/campaigns."""
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    result = await _plant_post_json(
        url=f"{base}/api/v1/campaigns",
        body=body,
        authorization=request.headers.get("Authorization"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
    return result  # type: ignore[return-value]


@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict:
    """Get campaign status. Proxies GET /api/v1/campaigns/{campaign_id}."""
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    result = await _plant_get_json(
        url=f"{base}/api/v1/campaigns/{campaign_id}",
        authorization=request.headers.get("Authorization"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
    return result  # type: ignore[return-value]


@router.get("/{campaign_id}/theme-items")
async def list_theme_items(
    campaign_id: str,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict | list:
    """List theme items. Proxies GET /api/v1/campaigns/{campaign_id}/theme-items."""
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    result = await _plant_get_json(
        url=f"{base}/api/v1/campaigns/{campaign_id}/theme-items",
        authorization=request.headers.get("Authorization"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
    return result  # type: ignore[return-value]


@router.post("/{campaign_id}/theme-items/approve")
async def approve_theme_items(
    campaign_id: str,
    body: dict,
    request: Request,
    _user: User = Depends(get_current_user),
    audit: AuditLogger = Depends(get_audit_logger),
) -> dict | list:
    """Batch approve/reject theme items. Proxies POST /api/v1/campaigns/{id}/theme-items/approve."""
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    result = await _plant_post_json(
        url=f"{base}/api/v1/campaigns/{campaign_id}/theme-items/approve",
        body=body,
        authorization=request.headers.get("Authorization"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
    await audit.log(
        "cp_campaigns",
        "theme_items_reviewed",
        "success",
        user_id=_user.id,
        metadata={"campaign_id": campaign_id, "decision": body.get("decision")},
    )
    return result  # type: ignore[return-value]


@router.patch("/{campaign_id}/theme-items/{item_id}")
async def patch_theme_item(
    campaign_id: str,
    item_id: str,
    body: dict,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict:
    """Approve or reject a single theme item. Proxies PATCH /api/v1/campaigns/{id}/theme-items/{item_id}."""
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return await _plant_patch_json(
        url=f"{base}/api/v1/campaigns/{campaign_id}/theme-items/{item_id}",
        body=body,
        authorization=request.headers.get("Authorization"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )


@router.post("/{campaign_id}/theme-items/{item_id}/generate-posts")
async def generate_posts(
    campaign_id: str,
    item_id: str,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict | list:
    """Generate posts for a theme item. Proxies POST .../generate-posts."""
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    result = await _plant_post_json(
        url=f"{base}/api/v1/campaigns/{campaign_id}/theme-items/{item_id}/generate-posts",
        body={},
        authorization=request.headers.get("Authorization"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
    return result  # type: ignore[return-value]


@router.get("/{campaign_id}/posts")
async def list_posts(
    campaign_id: str,
    request: Request,
    destination_type: str | None = Query(default=None),
    review_status: str | None = Query(default=None),
    _user: User = Depends(get_current_user),
) -> dict | list:
    """List posts (filterable). Proxies GET /api/v1/campaigns/{id}/posts."""
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    url = f"{base}/api/v1/campaigns/{campaign_id}/posts"
    params: list[str] = []
    if destination_type:
        params.append(f"destination_type={destination_type}")
    if review_status:
        params.append(f"review_status={review_status}")
    if params:
        url = f"{url}?{'&'.join(params)}"

    result = await _plant_get_json(
        url=url,
        authorization=request.headers.get("Authorization"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
    return result  # type: ignore[return-value]


@router.patch("/{campaign_id}/posts/{post_id}")
async def patch_post(
    campaign_id: str,
    post_id: str,
    body: dict,
    request: Request,
    _user: User = Depends(get_current_user),
    audit: AuditLogger = Depends(get_audit_logger),
) -> dict:
    """Approve or reject a single post. Proxies PATCH /api/v1/campaigns/{id}/posts/{post_id}."""
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    result = await _plant_patch_json(
        url=f"{base}/api/v1/campaigns/{campaign_id}/posts/{post_id}",
        body=body,
        authorization=request.headers.get("Authorization"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
    await audit.log(
        "cp_campaigns",
        "draft_post_reviewed",
        "success",
        user_id=_user.id,
        metadata={"campaign_id": campaign_id, "post_id": post_id, "decision": body.get("decision")},
    )
    return result


@router.get("/{campaign_id}/upload-eligibility")
async def get_upload_eligibility(
    campaign_id: str,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict:
    """Expose Plant's campaign workflow state for CP upload-readiness surfaces."""

    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    result = await _plant_get_json(
        url=f"{base}/api/v1/campaigns/{campaign_id}",
        authorization=request.headers.get("Authorization"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
    campaign = result if isinstance(result, dict) else {}
    return {
        "campaign_id": campaign.get("campaign_id", campaign_id),
        "workflow_state": campaign.get("workflow_state"),
        "approval_state": campaign.get("approval_state") or {},
        "brief_summary": campaign.get("brief_summary") or {},
        "draft_deliverables": campaign.get("draft_deliverables") or [],
    }


@router.post("/{campaign_id}/posts/{post_id}/publish")
async def publish_post(
    campaign_id: str,
    post_id: str,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict | list:
    """Immediately publish one approved post. Proxies POST .../publish."""
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    result = await _plant_post_json(
        url=f"{base}/api/v1/campaigns/{campaign_id}/posts/{post_id}/publish",
        body={},
        authorization=request.headers.get("Authorization"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
    return result  # type: ignore[return-value]
