"""Invoice endpoints (CP single-door).

BILL-1 (GST invoicing day-1):
Expose invoice list + retrieval + HTML download through CP backend.

CP must not allow the browser to spoof customer_id; Plant Gateway enforces
customer scoping by injecting the authenticated customer_id into invoice calls.
"""

from __future__ import annotations

import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from api.auth.dependencies import get_current_user
from models.user import User


router = APIRouter(prefix="/cp/invoices", tags=["cp-invoices"])


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
        resp = await client.get(f"{base_url}/{path.lstrip('/')}", headers=headers, params=dict(request.query_params))

    return resp


@router.get("")
async def list_invoices(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    _ = current_user
    try:
        resp = await _proxy_get(request=request, path="/api/v1/invoices")
    except RuntimeError:
        return {"invoices": []}

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail="Plant invoice list failed")
    return resp.json()


@router.get("/by-order/{order_id}")
async def get_invoice_by_order(
    order_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    _ = current_user
    try:
        resp = await _proxy_get(request=request, path=f"/api/v1/invoices/by-order/{order_id}")
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail="Plant invoice lookup failed")
    return resp.json()


@router.get("/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    _ = current_user
    try:
        resp = await _proxy_get(request=request, path=f"/api/v1/invoices/{invoice_id}")
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail="Plant invoice fetch failed")
    return resp.json()


@router.get("/{invoice_id}/html")
async def download_invoice_html(
    invoice_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    _ = current_user
    try:
        resp = await _proxy_get(request=request, path=f"/api/v1/invoices/{invoice_id}/html")
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail="Plant invoice download failed")

    headers: dict[str, str] = {}
    content_disposition = resp.headers.get("content-disposition")
    if content_disposition:
        headers["Content-Disposition"] = content_disposition

    return Response(content=resp.text, media_type="text/html", headers=headers)
