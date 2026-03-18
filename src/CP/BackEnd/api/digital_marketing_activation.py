from __future__ import annotations

import os

import httpx
from fastapi import Depends, HTTPException, Request

from api.auth.dependencies import get_current_user
from core.routing import waooaw_router
from models.user import User

router = waooaw_router(
    prefix="/cp/digital-marketing-activation",
    tags=["cp-digital-marketing-activation"],
)


def _plant_base_url() -> str:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base_url:
        raise RuntimeError("PLANT_GATEWAY_URL not configured")
    return base_url


async def _proxy_json(
    *,
    method: str,
    url: str,
    request: Request,
    body: dict | None = None,
) -> dict:
    headers: dict[str, str] = {}
    if request.headers.get("Authorization"):
        headers["Authorization"] = str(request.headers["Authorization"])
    if request.headers.get("X-Correlation-ID"):
        headers["X-Correlation-ID"] = str(request.headers["X-Correlation-ID"])
    if body is not None:
        headers["Content-Type"] = "application/json"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url, json=body, headers=headers)
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/{hired_instance_id}")
async def get_workspace(
    hired_instance_id: str,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict:
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return await _proxy_json(
        method="GET",
        url=f"{base}/api/v1/digital-marketing-activation/{hired_instance_id}",
        request=request,
    )


@router.patch("/{hired_instance_id}")
async def patch_workspace(
    hired_instance_id: str,
    body: dict,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict:
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return await _proxy_json(
        method="PATCH",
        url=f"{base}/api/v1/digital-marketing-activation/{hired_instance_id}",
        body=body,
        request=request,
    )


@router.post("/{hired_instance_id}/generate-theme-plan")
async def generate_theme_plan(
    hired_instance_id: str,
    body: dict,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict:
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return await _proxy_json(
        method="POST",
        url=f"{base}/api/v1/digital-marketing-activation/{hired_instance_id}/generate-theme-plan",
        body=body,
        request=request,
    )


@router.patch("/{hired_instance_id}/theme-plan")
async def patch_theme_plan(
    hired_instance_id: str,
    body: dict,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict:
    try:
        base = _plant_base_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return await _proxy_json(
        method="PATCH",
        url=f"{base}/api/v1/digital-marketing-activation/{hired_instance_id}/theme-plan",
        body=body,
        request=request,
    )
