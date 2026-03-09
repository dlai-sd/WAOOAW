"""Ops proxy routes for hired-agent data.

Thin PP proxy routes that forward requests to Plant Gateway's hired-agent
endpoints. Circuit-breaker protection is inherited from PlantAPIClient._request().
Responses are cached in Redis (TTL = OPS_CACHE_TTL_SECONDS) to reduce Plant load.
Cache degrades gracefully: if Redis is unavailable every request falls through to Plant.
"""

from typing import Optional

from fastapi import Depends, HTTPException, Query, Request
from pydantic import BaseModel

from api.deps import get_authorization_header
from clients.plant_client import PlantAPIClient, PlantAPIError, get_plant_client
from core.authorization import require_role
from core.routing import waooaw_router  # PP-N3b
from services.audit_dependency import AuditLogger, get_audit_logger  # PP-N4
from services.ops_cache import cache_get, cache_set  # E5: Redis response cache

router = waooaw_router(prefix="/ops/hired-agents", tags=["ops-hired-agents"])


class HookTraceEntry(BaseModel):
    event_id: str
    stage: str
    hired_agent_id: str
    agent_type: str
    result: str
    reason: str
    emitted_at: str
    payload_summary: str


@router.get("", response_model=list)
async def list_hired_agents(
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
    client: PlantAPIClient = Depends(get_plant_client),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """List all hired agent instances — forwards all query params to Plant (Redis-cached)."""
    params = dict(request.query_params)
    subscription_id = params.pop("subscription_id", None)
    customer_id = params.pop("customer_id", None)

    if subscription_id:
        plant_path = f"/api/v1/hired-agents/by-subscription/{subscription_id}"
    elif customer_id:
        plant_path = f"/api/v1/hired-agents/by-customer/{customer_id}"
    else:
        raise HTTPException(status_code=400, detail="subscription_id or customer_id is required")

    cached = await cache_get("hired", plant_path, params)
    if cached is not None:
        return cached

    try:
        resp = await client._request(
            method="GET",
            path=plant_path,
            params=params or None,
            headers={"Authorization": auth_header} if auth_header else None,
        )
        if resp.status_code == 200:
            body = resp.json()
            # by-subscription returns a single object; normalize to list
            if isinstance(body, dict):
                body = [body]
            await cache_set("hired", plant_path, body, params)
            await audit.log("pp_ops", "hired_agents_listed", "success")
            return body
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
    """Get a single hired agent instance by ID (Redis-cached)."""
    plant_path = f"/api/v1/hired-agents/{hired_instance_id}"

    cached = await cache_get("hired_item", plant_path)
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
            await cache_set("hired_item", plant_path, body)
            await audit.log(
                "pp_ops",
                "hired_agent_retrieved",
                "success",
                metadata={"hired_instance_id": hired_instance_id},
            )
            return body
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
    """List deliverables for a hired agent instance — forwards query params to Plant (cached)."""
    params = dict(request.query_params)
    plant_path = f"/api/v1/hired-agents/{hired_instance_id}/deliverables"

    cached = await cache_get("hired_deliverables", plant_path, params)
    if cached is not None:
        return cached

    try:
        resp = await client._request(
            method="GET",
            path=plant_path,
            params=params or None,
            headers={"Authorization": auth_header} if auth_header else None,
        )
        if resp.status_code == 200:
            body = resp.json()
            await cache_set("hired_deliverables", plant_path, body, params)
            await audit.log(
                "pp_ops",
                "hired_agent_deliverables_listed",
                "success",
                metadata={"hired_instance_id": hired_instance_id},
            )
            return body
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except PlantAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/{hired_agent_id}/construct-health", response_model=dict)
async def get_construct_health(
    hired_agent_id: str,
    _auth=Depends(require_role("developer")),
    client: PlantAPIClient = Depends(get_plant_client),
):
    """Returns 6-construct health snapshot for ConstructHealthPanel drawer.

    Proxies to Plant GET /api/v1/hired-agents/{id}/construct-health.
    PP adds RBAC gate (developer+) — no business logic, no data storage.
    """
    try:
        resp = await client._request(
            method="GET",
            path=f"/api/v1/hired-agents/{hired_agent_id}/construct-health",
        )
        if resp.status_code == 200:
            return resp.json()
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except PlantAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/{hired_agent_id}/scheduler-diagnostics", response_model=dict)
async def get_scheduler_diagnostics(
    hired_agent_id: str,
    _auth=Depends(require_role("developer")),
    client: PlantAPIClient = Depends(get_plant_client),
):
    """Returns full scheduler diagnostic state for SchedulerDiagnosticsPanel tab.

    Proxies to Plant GET /api/v1/hired-agents/{id}/scheduler-diagnostics.
    """
    try:
        resp = await client._request(
            method="GET",
            path=f"/api/v1/hired-agents/{hired_agent_id}/scheduler-diagnostics",
        )
        if resp.status_code == 200:
            return resp.json()
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except PlantAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/{hired_agent_id}/scheduler/pause", response_model=dict)
async def pause_scheduler(
    hired_agent_id: str,
    _auth=Depends(require_role("admin")),
    audit: AuditLogger = Depends(get_audit_logger),
    client: PlantAPIClient = Depends(get_plant_client),
):
    """Pause the scheduler for a hired agent.

    Proxies to Plant POST /api/v1/hired-agents/{id}/scheduler/pause.
    Requires admin role. Writes mandatory audit log entry.
    """
    try:
        resp = await client._request(
            method="POST",
            path=f"/api/v1/hired-agents/{hired_agent_id}/scheduler/pause",
        )
        if resp.status_code in (200, 201, 204):
            result = resp.json() if resp.content else {}
            await audit.log(
                screen="ops_hired_agents",
                action="scheduler_pause",
                outcome="success",
                metadata={"hired_agent_id": hired_agent_id},
            )
            return result
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except PlantAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/{hired_agent_id}/scheduler/resume", response_model=dict)
async def resume_scheduler(
    hired_agent_id: str,
    _auth=Depends(require_role("admin")),
    audit: AuditLogger = Depends(get_audit_logger),
    client: PlantAPIClient = Depends(get_plant_client),
):
    """Resume the scheduler for a hired agent.

    Proxies to Plant POST /api/v1/hired-agents/{id}/scheduler/resume.
    Requires admin role. Writes mandatory audit log entry.
    """
    try:
        resp = await client._request(
            method="POST",
            path=f"/api/v1/hired-agents/{hired_agent_id}/scheduler/resume",
        )
        if resp.status_code in (200, 201, 204):
            result = resp.json() if resp.content else {}
            await audit.log(
                screen="ops_hired_agents",
                action="scheduler_resume",
                outcome="success",
                metadata={"hired_agent_id": hired_agent_id},
            )
            return result
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
    """List goals for a hired agent instance — forwards query params to Plant (cached)."""
    params = dict(request.query_params)
    plant_path = f"/api/v1/hired-agents/{hired_instance_id}/goals"

    cached = await cache_get("hired_goals", plant_path, params)
    if cached is not None:
        return cached

    try:
        resp = await client._request(
            method="GET",
            path=plant_path,
            params=params or None,
            headers={"Authorization": auth_header} if auth_header else None,
        )
        if resp.status_code == 200:
            body = resp.json()
            await cache_set("hired_goals", plant_path, body, params)
            await audit.log(
                "pp_ops",
                "hired_agent_goals_listed",
                "success",
                metadata={"hired_instance_id": hired_instance_id},
            )
            return body
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except PlantAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get(
    "/{hired_agent_id}/hook-trace",
    response_model=list,
)
async def get_hook_trace(
    hired_agent_id: str,
    stage: Optional[str] = Query(None),
    result: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    _auth=Depends(require_role("developer")),
    client: PlantAPIClient = Depends(get_plant_client),
):
    """Returns last N hook events for this hired agent.

    Filterable by stage (e.g. "pre_pump") and result ("proceed"/"halt").
    Proxies to Plant GET /api/v1/hired-agents/{id}/hook-trace.
    payload_summary is truncated at 100 chars by Plant — no PII exposure.
    """
    params: dict = {"limit": limit}
    if stage:
        params["stage"] = stage
    if result:
        params["result"] = result
    try:
        resp = await client._request(
            method="GET",
            path=f"/api/v1/hired-agents/{hired_agent_id}/hook-trace",
            params=params,
        )
        if resp.status_code == 200:
            return resp.json()
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except PlantAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
