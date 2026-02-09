"""Receipt endpoints (CP single-door).

HIRE-2.9:
Expose receipt list + retrieval + HTML download through CP backend.

CP must not allow the browser to spoof customer_id; Plant Gateway enforces
customer scoping by injecting the authenticated customer_id into receipt calls.
"""

from __future__ import annotations

import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from api.auth.dependencies import get_current_user
from models.user import User


router = APIRouter(prefix="/cp/receipts", tags=["cp-receipts"])


def _plant_gateway_url() -> str:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base_url:
        raise RuntimeError("PLANT_GATEWAY_URL not configured")
    return base_url


async def _proxy_get(*, request: Request, path: str) -> httpx.Response:
    base_url = _plant_gateway_url()

    headers: dict[str, str] = {}
    authorization = request.headers.get("Authorization")
    if authorization:
        headers["Authorization"] = authorization

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{base_url}/{path.lstrip('/')}",
            headers=headers,
            params=dict(request.query_params),
        )

    return resp


@router.get("")
async def list_receipts(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    _ = current_user
    try:
        resp = await _proxy_get(request=request, path="/api/v1/receipts")
    except RuntimeError:
        return {"receipts": []}

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail="Plant receipt list failed")
    return resp.json()


@router.get("/by-order/{order_id}")
async def get_receipt_by_order(
    order_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    _ = current_user
    try:
        resp = await _proxy_get(request=request, path=f"/api/v1/receipts/by-order/{order_id}")
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail="Plant receipt lookup failed")
    return resp.json()


@router.get("/{receipt_id}")
async def get_receipt(
    receipt_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    _ = current_user
    try:
        resp = await _proxy_get(request=request, path=f"/api/v1/receipts/{receipt_id}")
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail="Plant receipt fetch failed")
    return resp.json()


@router.get("/{receipt_id}/html")
async def download_receipt_html(
    receipt_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    _ = current_user
    try:
        resp = await _proxy_get(request=request, path=f"/api/v1/receipts/{receipt_id}/html")
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail="Plant receipt download failed")

    headers: dict[str, str] = {}
    content_disposition = resp.headers.get("content-disposition")
    if content_disposition:
        headers["Content-Disposition"] = content_disposition

    return Response(content=resp.text, media_type="text/html", headers=headers)
