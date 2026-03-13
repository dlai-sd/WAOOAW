"""Agent catalog release management (PP thin proxy to Plant)."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.deps import get_authorization_header
from api.security import require_admin
from clients.plant_client import PlantAPIClient, PlantAPIError, ValidationError, get_plant_client
from core.routing import waooaw_router
from services.audit_dependency import AuditLogger, get_audit_logger


class CatalogReleaseUpsertBody(BaseModel):
    public_name: Optional[str] = None
    short_description: Optional[str] = None
    monthly_price_inr: Optional[int] = Field(default=None, ge=0)
    trial_days: Optional[int] = Field(default=None, ge=0)
    allowed_durations: Optional[list[str]] = None
    supported_channels: Optional[list[str]] = None
    approval_mode: Optional[str] = None
    external_catalog_version: Optional[str] = None
    agent_type_id: Optional[str] = None
    internal_definition_version_id: Optional[str] = None


router = waooaw_router(prefix="/agent-catalog", tags=["agent-catalog"])


def _correlation_id_from_request(request: Request) -> Optional[str]:
    return request.headers.get("x-correlation-id") or request.headers.get("X-Correlation-ID")


@router.get("", response_model=list[dict[str, Any]])
async def list_catalog_releases(
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
) -> list[dict[str, Any]]:
    correlation_id = _correlation_id_from_request(request)
    try:
        return await plant_client.list_catalog_releases(
            correlation_id=correlation_id,
            auth_header=auth_header,
        )
    except PlantAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{agent_id}/release", response_model=dict[str, Any])
async def upsert_catalog_release(
    agent_id: str,
    body: CatalogReleaseUpsertBody,
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
    audit: AuditLogger = Depends(get_audit_logger),
) -> dict[str, Any]:
    correlation_id = _correlation_id_from_request(request)
    try:
        result = await plant_client.upsert_catalog_release(
            agent_id,
            body.model_dump(mode="json", exclude_none=True),
            correlation_id=correlation_id,
            auth_header=auth_header,
        )
        await audit.log(
            screen="pp_agent_catalog",
            action="catalog_release_updated",
            outcome="success",
            detail=f"agent_id={agent_id}",
        )
        return result
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PlantAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/{agent_id}/approve", response_model=dict[str, Any])
async def approve_catalog_release(
    agent_id: str,
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
    audit: AuditLogger = Depends(get_audit_logger),
) -> dict[str, Any]:
    correlation_id = _correlation_id_from_request(request)
    try:
        result = await plant_client.approve_catalog_release(
            agent_id,
            correlation_id=correlation_id,
            auth_header=auth_header,
        )
        await audit.log(
            screen="pp_agent_catalog",
            action="catalog_release_approved",
            outcome="success",
            detail=f"agent_id={agent_id}",
        )
        return result
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PlantAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/releases/{release_id}/retire", response_model=dict[str, Any])
async def retire_catalog_release(
    release_id: str,
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
    audit: AuditLogger = Depends(get_audit_logger),
) -> dict[str, Any]:
    correlation_id = _correlation_id_from_request(request)
    try:
        result = await plant_client.retire_catalog_release(
            release_id,
            correlation_id=correlation_id,
            auth_header=auth_header,
        )
        await audit.log(
            screen="pp_agent_catalog",
            action="catalog_release_retired",
            outcome="success",
            detail=f"release_id={release_id}",
        )
        return result
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PlantAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))