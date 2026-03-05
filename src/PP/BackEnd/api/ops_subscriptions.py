"""Ops proxy routes for subscription data.

Thin PP proxy routes that forward requests to Plant Gateway's subscription
endpoints. Circuit-breaker protection is inherited from PlantAPIClient._request().
"""

from typing import Optional

from fastapi import Depends, HTTPException, Request

from api.deps import get_authorization_header
from clients.plant_client import PlantAPIClient, PlantAPIError, get_plant_client
from core.routing import waooaw_router  # PP-N3b: never use bare APIRouter
from services.audit_dependency import AuditLogger, get_audit_logger  # PP-N4

router = waooaw_router(prefix="/ops/subscriptions", tags=["ops-subscriptions"])


@router.get("", response_model=list)
async def list_subscriptions(
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
    client: PlantAPIClient = Depends(get_plant_client),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """List all subscriptions — forwards all query params to Plant."""
    params = dict(request.query_params)
    try:
        resp = await client._request(  # PP-N1: circuit breaker lives inside _request
            method="GET",
            path="/api/v1/subscriptions",
            params=params or None,
            headers={"Authorization": auth_header} if auth_header else None,
        )
        if resp.status_code == 200:
            await audit.log("pp_ops", "subscriptions_listed", "success")
            return resp.json()
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except PlantAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/{subscription_id}", response_model=dict)
async def get_subscription(
    subscription_id: str,
    auth_header: Optional[str] = Depends(get_authorization_header),
    client: PlantAPIClient = Depends(get_plant_client),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """Get a single subscription by ID."""
    try:
        resp = await client._request(
            method="GET",
            path=f"/api/v1/subscriptions/{subscription_id}",
            headers={"Authorization": auth_header} if auth_header else None,
        )
        if resp.status_code == 200:
            await audit.log(
                "pp_ops",
                "subscription_retrieved",
                "success",
                metadata={"subscription_id": subscription_id},
            )
            return resp.json()
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except PlantAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
