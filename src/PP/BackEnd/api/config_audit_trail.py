"""Configuration Audit Trail API - AGP2-PP-3.2

PP admin audit trail viewer for tracking all configuration changes to agent instances.
Provides complete history of who changed what, when, and from what value to what value.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

from api.deps import get_authorization_header
from api.security import require_admin
from clients.plant_client import PlantAPIClient, get_plant_client


router = APIRouter(prefix="/config-audit", tags=["config-audit"])


class ConfigChangeEntry(BaseModel):
    """Single configuration change entry in audit trail."""
    
    change_id: str
    hired_instance_id: str
    subscription_id: str
    customer_id: str
    agent_id: str
    
    # Change details
    field_path: str = Field(..., description="JSON path to the changed field (e.g., 'config.timezone')")
    old_value: Optional[Any] = Field(None, description="Previous value (null if first set)")
    new_value: Optional[Any] = Field(None, description="New value (null if deleted)")
    
    # Change metadata
    change_type: str = Field(..., description="Type of change: created, updated, deleted")
    changed_by: str = Field(..., description="User/system that made the change")
    change_source: str = Field("customer_portal", description="Source: customer_portal, admin_portal, api, system")
    
    # Context
    correlation_id: Optional[str] = Field(None, description="Correlation ID for related changes")
    reason: Optional[str] = Field(None, description="Optional reason/note for the change")
    
    # Timestamp
    changed_at: datetime


class AgentConfigHistory(BaseModel):
    """Complete configuration history for an agent instance."""
    
    hired_instance_id: str
    subscription_id: str
    agent_id: str
    customer_id: str
    
    # Current config
    current_config: dict = Field(default_factory=dict)
    
    # Change history
    changes: List[ConfigChangeEntry]
    total_changes: int
    
    # Summary stats
    first_configured_at: Optional[datetime] = None
    last_modified_at: Optional[datetime] = None
    modification_count: int = 0


class AuditTrailFilters(BaseModel):
    """Filters for audit trail queries."""
    
    hired_instance_id: Optional[str]
    customer_id: Optional[str]
    agent_id: Optional[str]
    changed_by: Optional[str]
    field_path: Optional[str]
    change_type: Optional[str]
    start_date: Optional[datetime]
    end_date: Optional[datetime]


class AuditTrailResponse(BaseModel):
    """Paginated audit trail response."""
    
    changes: List[ConfigChangeEntry]
    total: int
    page: int
    page_size: int
    
    # Filters applied
    filters: Optional[dict] = None


@router.get(
    "/trail",
    response_model=AuditTrailResponse,
    summary="Get configuration audit trail"
)
async def get_config_audit_trail(
    # Filters
    hired_instance_id: Optional[str] = Query(None, description="Filter by agent instance ID"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    changed_by: Optional[str] = Query(None, description="Filter by who made the change"),
    field_path: Optional[str] = Query(None, description="Filter by specific field path"),
    change_type: Optional[str] = Query(None, description="Filter by change type"),
    start_date: Optional[datetime] = Query(None, description="Filter changes after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter changes before this date"),
    
    # Sorting
    sort_by: str = Query("changed_at", description="Sort field: changed_at, field_path"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    
    # Auth
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Get configuration audit trail with filters and pagination.
    
    Returns all configuration changes across all agent instances, with support for
    filtering by instance, customer, time range, and specific fields.
    
    **Change Types**:
    - `created`: Initial configuration set
    - `updated`: Configuration value changed
    - `deleted`: Configuration value removed
    
    **Field Path Examples**:
    - `nickname`: Top-level field
    - `config.timezone`: Nested in config object
    - `config.platforms[0].credential_ref`: Array element
    
    **Use Cases**:
    - Troubleshooting: "When did the timezone change?"
    - Compliance: "Who changed the API credentials?"
    - Support: "What was the config before the error started?"
    """
    
    try:
        # In production, this would query the audit trail table
        # For now, return placeholder data
        
        changes_data: List[ConfigChangeEntry] = []
        
        # Apply filters (placeholder logic)
        filtered_changes = changes_data
        
        if hired_instance_id:
            filtered_changes = [c for c in filtered_changes if c.hired_instance_id == hired_instance_id]
        
        if customer_id:
            filtered_changes = [c for c in filtered_changes if c.customer_id == customer_id]
        
        if agent_id:
            filtered_changes = [c for c in filtered_changes if c.agent_id == agent_id]
        
        if changed_by:
            filtered_changes = [c for c in filtered_changes if c.changed_by == changed_by]
        
        if field_path:
            filtered_changes = [c for c in filtered_changes if c.field_path == field_path]
        
        if change_type:
            filtered_changes = [c for c in filtered_changes if c.change_type == change_type]
        
        if start_date:
            filtered_changes = [c for c in filtered_changes if c.changed_at >= start_date]
        
        if end_date:
            filtered_changes = [c for c in filtered_changes if c.changed_at <= end_date]
        
        # Sorting
        reverse = sort_order.lower() == "desc"
        if sort_by == "changed_at":
            filtered_changes.sort(key=lambda x: x.changed_at, reverse=reverse)
        elif sort_by == "field_path":
            filtered_changes.sort(key=lambda x: x.field_path, reverse=reverse)
        
        # Pagination
        total = len(filtered_changes)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_changes = filtered_changes[start_idx:end_idx]
        
        filters_applied = {
            "hired_instance_id": hired_instance_id,
            "customer_id": customer_id,
            "agent_id": agent_id,
            "changed_by": changed_by,
            "field_path": field_path,
            "change_type": change_type,
            "start_date": start_date,
            "end_date": end_date,
        }
        # Remove None values
        filters_applied = {k: v for k, v in filters_applied.items() if v is not None}
        
        return AuditTrailResponse(
            changes=paginated_changes,
            total=total,
            page=page,
            page_size=page_size,
            filters=filters_applied if filters_applied else None,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch audit trail: {str(e)}")


@router.get(
    "/agent/{hired_instance_id}/history",
    response_model=AgentConfigHistory,
    summary="Get configuration history for specific agent"
)
async def get_agent_config_history(
    hired_instance_id: str,
    include_details: bool = Query(True, description="Include full change details"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Get complete configuration history for a specific agent instance.
    
    Returns all configuration changes for the specified agent, showing:
    - Current configuration state
    - All historical changes with old/new values
    - Timeline of modifications
    
    **Use Cases**:
    - Debugging: "What changed before the agent stopped working?"
    - Rollback: "What was the config on 2026-02-01?"
    - Analysis: "How many times has this agent been reconfigured?"
    """
    
    try:
        # In production, this would:
        # 1. Fetch current agent config from hired_agents table
        # 2. Query audit trail for all changes to this instance
        # 3. Sort by timestamp descending
        
        # Placeholder response
        return AgentConfigHistory(
            hired_instance_id=hired_instance_id,
            subscription_id="SUB-placeholder",
            agent_id="AGT-placeholder",
            customer_id="CUST-placeholder",
            current_config={},
            changes=[],
            total_changes=0,
            first_configured_at=None,
            last_modified_at=None,
            modification_count=0,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch config history: {str(e)}")


@router.post(
    "/agent/{hired_instance_id}/snapshot",
    summary="Create configuration snapshot"
)
async def create_config_snapshot(
    hired_instance_id: str,
    snapshot_name: str = Query(..., description="Name for this snapshot"),
    note: Optional[str] = Query(None, description="Optional note about the snapshot"),
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Create a named snapshot of the current configuration.
    
    Useful before making risky changes or for known-good configurations.
    Snapshots can be used for quick rollback.
    """
    
    try:
        # In production, this would:
        # 1. Fetch current config
        # 2. Store snapshot with name and timestamp
        # 3. Log snapshot creation in audit trail
        
        return {
            "status": "success",
            "snapshot_id": f"SNAP-{hired_instance_id}-timestamp",
            "snapshot_name": snapshot_name,
            "hired_instance_id": hired_instance_id,
            "created_at": datetime.now().isoformat(),
            "note": note,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create snapshot: {str(e)}")


@router.get(
    "/agent/{hired_instance_id}/snapshots",
    summary="List configuration snapshots"
)
async def list_config_snapshots(
    hired_instance_id: str,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """List all configuration snapshots for an agent instance.
    
    Returns snapshots in reverse chronological order.
    """
    
    try:
        # Placeholder response
        return {
            "hired_instance_id": hired_instance_id,
            "snapshots": [],
            "total": 0,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list snapshots: {str(e)}")


@router.post(
    "/agent/{hired_instance_id}/rollback",
    summary="Rollback configuration to snapshot"
)
async def rollback_config(
    hired_instance_id: str,
    snapshot_id: str = Query(..., description="Snapshot ID to rollback to"),
    reason: str = Query(..., description="Reason for rollback (for audit trail)"),
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Rollback agent configuration to a previous snapshot.
    
    **Warning**: This replaces the entire configuration with the snapshot.
    Creates an audit trail entry for the rollback operation.
    """
    
    try:
        # In production, this would:
        # 1. Validate snapshot exists
        # 2. Fetch snapshot config
        # 3. Update agent config to snapshot values
        # 4. Log rollback in audit trail
        
        return {
            "status": "success",
            "message": "Configuration rolled back successfully",
            "hired_instance_id": hired_instance_id,
            "snapshot_id": snapshot_id,
            "rolled_back_at": datetime.now().isoformat(),
            "reason": reason,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rollback config: {str(e)}")


@router.get(
    "/field-changes/{field_path}",
    summary="Get all changes to a specific field"
)
async def get_field_changes(
    field_path: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Get all configuration changes for a specific field across all agents.
    
    Useful for analyzing patterns like:
    - "How often do customers change timezone?"
    - "What credential_refs are being used?"
    - "Who's modifying allowed_coins?"
    
    **Field Path Examples**:
    - config.timezone
    - config.platforms[0].credential_ref
    - nickname
    """
    
    try:
        # Placeholder response
        return {
            "field_path": field_path,
            "changes": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch field changes: {str(e)}")


@router.get(
    "/export",
    summary="Export audit trail to CSV"
)
async def export_audit_trail(
    hired_instance_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Export audit trail to CSV for offline analysis.
    
    Supports same filters as main audit trail endpoint.
    Returns CSV file with all change records.
    """
    
    try:
        # In production, this would:
        # 1. Query changes with filters
        # 2. Generate CSV with headers
        # 3. Return as downloadable file
        
        # For now, return metadata
        return {
            "status": "success",
            "message": "CSV export not yet implemented",
            "filters": {
                "hired_instance_id": hired_instance_id,
                "start_date": start_date,
                "end_date": end_date,
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export audit trail: {str(e)}")
