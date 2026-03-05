"""Ops proxy routes for hired-agent data.

Thin PP proxy routes that forward requests to Plant Gateway's hired-agent
endpoints. Circuit-breaker protection is inherited from PlantAPIClient._request().
"""

from typing import Optional

from fastapi import Depends, HTTPException, Request

from api.deps import get_authorization_header
from clients.plant_client import PlantAPIClient, PlantAPIError, get_plant_client
from core.routing import waooaw_router  # PP-N3b
from services.audit_dependency import AuditLogger, get_audit_logger  # PP-N4

router = waooaw_router(prefix="/ops/hired-agents", tags=["ops-hired-agents"])


@router.get("", response_model=list)
async def list_hired_agents(
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
    client: PlantAPIClient = Depends(get_plant_client),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """List all hired agent instances — forwards all query params to Plant."""
    params = dict(request.query_params)
    try:
        resp = await client._request(
            method="GET",
            path="/api/v1/hired-agents",
            params=params or None,
            headers={"Authorization": auth_header} if auth_header else None,
        )
        if resp.status_code == 200:
            await audit.log("pp_ops", "hired_agents_listed", "success")
            return resp.json()
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except PlantAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/{hired_instance_id}", response_model=dict)
async def get_hired_agent(
    hired_instance_id: str,
    auth_header: Optional[str] = Depends(get_authorization_header),
    client: PlantAPIClient = Depends(get_plant_client),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """Get a single hired agent instance by ID."""
    try:
        resp = await client._request(
            method="GET",
            path=f"/api/v1/hired-agents/{hired_instance_id}",
            headers={"Authorization": auth_header} if auth_header else None,
        )
        if resp.status_code == 200:
            await audit.log(
                "pp_ops",
                "hired_agent_retrieved",
                "success",
                metadata={"hired_instance_id": hired_instance_id},
            )
            return resp.json()
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except PlantAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/{hired_instance_id}/deliverables", response_model=dict)
async def list_hired_agent_deliverables(
    hired_instance_id: str,
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
    client: PlantAPIClient = Depends(get_plant_client),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """List deliverables for a hired agent instance — forwards query params to Plant."""
    params = dict(request.query_params)
    try:
        resp = await client._request(
            method="GET",
            path=f"/api/v1/hired-agents/{hired_instance_id}/deliverables",
            params=params or None,
            headers={"Authorization": auth_header} if auth_header else None,
        )
        if resp.status_code == 200:
            await audit.log(
                "pp_ops",
                "hired_agent_deliverables_listed",
                "success",
                metadata={"hired_instance_id": hired_instance_id},
            )
            return resp.json()
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except PlantAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/{hired_instance_id}/goals", response_model=dict)
async def list_hired_agent_goals(
    hired_instance_id: str,
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
    client: PlantAPIClient = Depends(get_plant_client),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """List goals for a hired agent instance — forwards query params to Plant."""
    params = dict(request.query_params)
    try:
        resp = await client._request(
            method="GET",
            path=f"/api/v1/hired-agents/{hired_instance_id}/goals",
            params=params or None,
            headers={"Authorization": auth_header} if auth_header else None,
        )
        if resp.status_code == 200:
            await audit.log(
                "pp_ops",
                "hired_agent_goals_listed",
                "success",
                metadata={"hired_instance_id": hired_instance_id},
            )
            return resp.json()
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except PlantAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
