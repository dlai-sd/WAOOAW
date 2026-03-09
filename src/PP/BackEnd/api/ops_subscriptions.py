"""Ops proxy routes for subscription data.

Thin PP proxy routes that forward requests to Plant Gateway's subscription
endpoints. Circuit-breaker protection is inherited from PlantAPIClient._request().
Responses are cached in Redis (TTL = OPS_CACHE_TTL_SECONDS) to reduce Plant load.
Cache degrades gracefully: if Redis is unavailable every request falls through to Plant.
"""

from typing import Optional

from fastapi import Depends, HTTPException, Request

from api.deps import get_authorization_header
from clients.plant_client import PlantAPIClient, PlantAPIError, get_plant_client
from core.routing import waooaw_router  # PP-N3b: never use bare APIRouter
from services.audit_dependency import AuditLogger, get_audit_logger  # PP-N4
from services.ops_cache import cache_get, cache_set  # E5: Redis response cache

router = waooaw_router(prefix="/ops/subscriptions", tags=["ops-subscriptions"])


@router.get("", response_model=list)
async def list_subscriptions(
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
    client: PlantAPIClient = Depends(get_plant_client),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """List all subscriptions — forwards all query params to Plant (Redis-cached)."""
    params = dict(request.query_params)
    customer_id = params.pop("customer_id", None)
    if not customer_id:
        raise HTTPException(status_code=400, detail="customer_id is required")
    plant_path = f"/api/v1/payments/subscriptions/by-customer/{customer_id}"

    cached = await cache_get("subs", plant_path, params)
    if cached is not None:
        return cached

    try:
        resp = await client._request(  # PP-N1: circuit breaker lives inside _request
            method="GET",
            path=plant_path,
            params=params or None,
            headers={"Authorization": auth_header} if auth_header else None,
        )
        if resp.status_code == 200:
            body = resp.json()
            await cache_set("subs", plant_path, body, params)
            await audit.log("pp_ops", "subscriptions_listed", "success")
            return body
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
    """Get a single subscription by ID (Redis-cached)."""
    plant_path = f"/api/v1/payments/subscriptions/{subscription_id}"

    cached = await cache_get("sub", plant_path)
    if cached is not None:
        return cached

    try:
        resp = await client._request(
            method="GET",
            path=plant_path,
            headers={"Authorization": auth_header} if auth_header else None,
        )
        if resp.status_code == 200:
            body = resp.json()
            await cache_set("sub", plant_path, body)
            await audit.log(
                "pp_ops", "subscription_retrieved", "success",
                metadata={"subscription_id": subscription_id},
            )
            return body
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except PlantAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
