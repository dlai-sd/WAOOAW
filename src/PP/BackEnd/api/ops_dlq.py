"""DLQ (Dead-Letter Queue) ops endpoints (PP).

Thin PP proxy routes that surface Plant's scheduler DLQ to platform operators.
PP adds RBAC enforcement — no business logic, no local data storage.
"""

from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, Query

from clients.plant_client import PlantAPIClient, PlantAPIError, get_plant_client
from core.authorization import require_role
from core.logging import PIIMaskingFilter
from core.routing import waooaw_router
from services.audit_dependency import AuditLogger, get_audit_logger

logger = logging.getLogger(__name__)
logger.addFilter(PIIMaskingFilter())

router = waooaw_router(prefix="/ops/dlq", tags=["pp-ops-dlq"])


@router.get("", response_model=list)
async def list_dlq_entries(
    agent_type: str | None = Query(None),
    hired_agent_id: str | None = Query(None),
    limit: int = Query(50, le=200),
    _auth=Depends(require_role("developer")),
    client: PlantAPIClient = Depends(get_plant_client),
):
    """List DLQ entries. Filterable by agent_type and/or hired_agent_id.

    Returns a list of DLQ records from Plant's scheduler dead-letter queue.
    Proxies to Plant GET /api/v1/ops/dlq with query params forwarded.
    Requires developer+ role.
    """
    params: dict = {"limit": limit}
    if agent_type:
        params["agent_type"] = agent_type
    if hired_agent_id:
        params["hired_agent_id"] = hired_agent_id
    try:
        resp = await client._request(
            method="GET",
            path="/api/v1/ops/dlq",
            params=params,
        )
        if resp.status_code == 200:
            return resp.json()
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except PlantAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/{dlq_id}/requeue", response_model=dict)
async def requeue_dlq_entry(
    dlq_id: str,
    _auth=Depends(require_role("admin")),
    audit: AuditLogger = Depends(get_audit_logger),
    client: PlantAPIClient = Depends(get_plant_client),
):
    """Requeue a DLQ entry for retry execution.

    Only admin role can requeue — retries trigger a goal run on Plant.
    Action is audit-logged with dlq_id.
    Proxies to Plant POST /api/v1/ops/dlq/{id}/requeue.
    """
    try:
        resp = await client._request(
            method="POST",
            path=f"/api/v1/ops/dlq/{dlq_id}/requeue",
        )
        if resp.status_code in (200, 201, 202):
            result = resp.json() if resp.content else {}
            await audit.log(
                screen="ops_dlq",
                action="dlq_requeue",
                outcome="success",
                metadata={"dlq_id": dlq_id},
            )
            return result
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    except PlantAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
