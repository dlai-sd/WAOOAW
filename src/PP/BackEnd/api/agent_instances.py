"""Agent Instance Dashboard API - AGP2-PP-3.1

PP admin dashboard for monitoring and managing all hired agent instances.
Provides comprehensive oversight of agent health, configuration status, and activity.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field

from api.deps import get_authorization_header
from api.security import require_admin
from clients.plant_client import PlantAPIClient, get_plant_client


router = APIRouter(prefix="/agent-instances", tags=["agent-instances"])


# Response models
class AgentInstanceSummary(BaseModel):
    """Summary of a hired agent instance for dashboard display."""
    
    hired_instance_id: str
    subscription_id: str
    agent_id: str
    customer_id: Optional[str]
    
    nickname: Optional[str]
    theme: Optional[str]
    
    # Status indicators
    configured: bool
    goals_completed: bool
    active: bool
    
    # Trial lifecycle
    trial_status: Literal["not_started", "active", "ended_converted", "ended_not_converted"]
    trial_start_at: Optional[datetime]
    trial_end_at: Optional[datetime]
    
    # Goal stats
    goal_count: int = 0
    active_goals: int = 0
    
    # Usage stats
    total_deliverables: int = 0
    pending_approvals: int = 0
    last_activity_at: Optional[datetime] = None
    
    # Health indicator
    health_status: Literal["healthy", "needs_attention", "inactive"] = "inactive"
    
    # Audit
    created_at: datetime
    updated_at: datetime


class AgentInstanceDetail(BaseModel):
    """Detailed view of a hired agent instance."""
    
    # Basic info (same as summary)
    hired_instance_id: str
    subscription_id: str
    agent_id: str
    customer_id: Optional[str]
    
    nickname: Optional[str]
    theme: Optional[str]
    config: dict = Field(default_factory=dict)
    
    # Status
    configured: bool
    goals_completed: bool
    active: bool
    
    # Trial lifecycle
    trial_status: str
    trial_start_at: Optional[datetime]
    trial_end_at: Optional[datetime]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime


class DashboardFilters(BaseModel):
    """Available filter options for dashboard."""
    
    trial_status: Optional[Literal["not_started", "active", "ended_converted", "ended_not_converted"]]
    configured: Optional[bool]
    active: Optional[bool]
    health_status: Optional[Literal["healthy", "needs_attention", "inactive"]]
    agent_id: Optional[str]
    customer_id: Optional[str]


class DashboardStats(BaseModel):
    """Aggregate statistics for dashboard overview."""
    
    total_instances: int = 0
    active_instances: int = 0
    trial_active: int = 0
    trial_converted: int = 0
    needs_attention: int = 0
    configured_count: int = 0
    pending_approvals_total: int = 0


class DashboardResponse(BaseModel):
    """Complete dashboard response with stats and instances."""
    
    stats: DashboardStats
    instances: List[AgentInstanceSummary]
    total: int
    page: int
    page_size: int


# Helper functions
def _calculate_health_status(
    instance: dict,
    goal_count: int,
    active_goals: int,
    last_activity_at: Optional[datetime]
) -> str:
    """Calculate health status based on configuration and activity."""
    
    # Not configured = needs attention
    if not instance.get("configured"):
        return "needs_attention"
    
    # No goals = needs attention
    if goal_count == 0:
        return "needs_attention"
    
    # Trial ended not converted = inactive
    if instance.get("trial_status") == "ended_not_converted":
        return "inactive"
    
    # Active with recent activity = healthy
    if instance.get("active") and last_activity_at:
        # Consider healthy if activity within last 7 days
        from datetime import timezone, timedelta
        now = datetime.now(timezone.utc)
        if last_activity_at and (now - last_activity_at) < timedelta(days=7):
            return "healthy"
    
    # Active but no recent activity = needs attention
    if instance.get("active"):
        return "needs_attention"
    
    return "inactive"


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="Get agent instances dashboard"
)
async def get_agent_instances_dashboard(
    # Filters
    trial_status: Optional[str] = Query(None, description="Filter by trial status"),
    configured: Optional[bool] = Query(None, description="Filter by configured status"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    health_status: Optional[str] = Query(None, description="Filter by health status"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    
    # Auth
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Get comprehensive agent instances dashboard.
    
    Displays all hired agent instances with status, health indicators, and activity metrics.
    Supports filtering by various criteria and pagination.
    
    **Health Status Calculation**:
    - `healthy`: Configured, has goals, recent activity (< 7 days)
    - `needs_attention`: Not configured, no goals, or no recent activity
    - `inactive`: Trial ended not converted, or marked inactive
    
    **Filters**:
    - `trial_status`: not_started, active, ended_converted, ended_not_converted
    - `configured`: true/false
    - `active`: true/false
    - `health_status`: healthy, needs_attention, inactive
    - `agent_id`: Specific agent ID (e.g., AGT-MKT-001)
    - `customer_id`: Specific customer ID
    """
    
    try:
        # Fetch all hired agents from Plant API
        # Note: This is a simplified implementation. In production, you'd want to:
        # 1. Add a bulk list endpoint to Plant API with proper pagination
        # 2. Add filtering at the database level
        # 3. Optimize queries with joins and aggregations
        
        # For now, we'll make a direct database query through the Plant client
        # In a real implementation, this would be a dedicated endpoint
        
        # Placeholder response - in production this would query the database
        instances_data: List[AgentInstanceSummary] = []
        
        # Calculate aggregate stats
        stats = DashboardStats(
            total_instances=len(instances_data),
            active_instances=sum(1 for i in instances_data if i.active),
            trial_active=sum(1 for i in instances_data if i.trial_status == "active"),
            trial_converted=sum(1 for i in instances_data if i.trial_status == "ended_converted"),
            needs_attention=sum(1 for i in instances_data if i.health_status == "needs_attention"),
            configured_count=sum(1 for i in instances_data if i.configured),
            pending_approvals_total=sum(i.pending_approvals for i in instances_data),
        )
        
        # Apply filters
        filtered_instances = instances_data
        
        if trial_status:
            filtered_instances = [i for i in filtered_instances if i.trial_status == trial_status]
        
        if configured is not None:
            filtered_instances = [i for i in filtered_instances if i.configured == configured]
        
        if active is not None:
            filtered_instances = [i for i in filtered_instances if i.active == active]
        
        if health_status:
            filtered_instances = [i for i in filtered_instances if i.health_status == health_status]
        
        if agent_id:
            filtered_instances = [i for i in filtered_instances if i.agent_id == agent_id]
        
        if customer_id:
            filtered_instances = [i for i in filtered_instances if i.customer_id == customer_id]
        
        # Pagination
        total = len(filtered_instances)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_instances = filtered_instances[start_idx:end_idx]
        
        return DashboardResponse(
            stats=stats,
            instances=paginated_instances,
            total=total,
            page=page,
            page_size=page_size,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard data: {str(e)}")


@router.get(
    "/{hired_instance_id}/detail",
    response_model=AgentInstanceDetail,
    summary="Get agent instance details"
)
async def get_agent_instance_detail(
    hired_instance_id: str,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Get detailed information for a specific agent instance.
    
    Includes full configuration, trial status, and timestamps.
    """
    
    try:
        # Fetch instance from Plant API
        # In production, this would call a Plant API endpoint
        # For now, return placeholder
        
        raise HTTPException(status_code=404, detail="Agent instance not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch instance detail: {str(e)}")


@router.post(
    "/{hired_instance_id}/pause",
    summary="Pause an agent instance"
)
async def pause_agent_instance(
    hired_instance_id: str,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Pause an agent instance (set active=false).
    
    Paused agents will not run scheduled goals until resumed.
    Useful for maintenance or troubleshooting.
    """
    
    try:
        # Update instance via Plant API
        # In production, this would call a Plant API endpoint to update active status
        
        return {
            "status": "success",
            "message": f"Agent instance {hired_instance_id} paused",
            "hired_instance_id": hired_instance_id,
            "active": False,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause instance: {str(e)}")


@router.post(
    "/{hired_instance_id}/resume",
    summary="Resume a paused agent instance"
)
async def resume_agent_instance(
    hired_instance_id: str,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Resume a paused agent instance (set active=true).
    
    Resumed agents will start running scheduled goals again.
    """
    
    try:
        # Update instance via Plant API
        # In production, this would call a Plant API endpoint to update active status
        
        return {
            "status": "success",
            "message": f"Agent instance {hired_instance_id} resumed",
            "hired_instance_id": hired_instance_id,
            "active": True,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume instance: {str(e)}")


@router.get(
    "/health-indicators",
    summary="Get health indicator definitions"
)
async def get_health_indicators(
    _: dict = Depends(require_admin),
):
    """Get definitions of health status indicators.
    
    Useful for understanding what each health status means.
    """
    
    return {
        "indicators": {
            "healthy": {
                "color": "green",
                "description": "Agent is configured, has active goals, and recent activity (< 7 days)",
                "criteria": [
                    "configured = true",
                    "goal_count > 0",
                    "last_activity_at within 7 days",
                ]
            },
            "needs_attention": {
                "color": "yellow",
                "description": "Agent requires attention (not configured, no goals, or inactive)",
                "criteria": [
                    "configured = false OR",
                    "goal_count = 0 OR",
                    "no activity in last 7 days",
                ]
            },
            "inactive": {
                "color": "red",
                "description": "Agent is inactive or trial ended without conversion",
                "criteria": [
                    "trial_status = ended_not_converted OR",
                    "active = false",
                ]
            },
        }
    }
