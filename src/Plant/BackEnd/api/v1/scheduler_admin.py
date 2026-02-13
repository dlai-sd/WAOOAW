"""Scheduler admin API endpoints for pause/resume/trigger operations."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from services.scheduler_admin_service import SchedulerAdminService
from services.goal_scheduler_service import GoalSchedulerService
from services.idempotency_service import IdempotencyService


router = APIRouter(prefix="/scheduler", tags=["scheduler-admin"])


# Request/Response Models


class PauseSchedulerRequest(BaseModel):
    """Request to pause scheduler."""
    
    operator: str = Field(..., description="Username/ID of operator")
    reason: Optional[str] = Field(None, description="Reason for pausing")
    wait_for_completion: bool = Field(
        True,
        description="Wait for running goals to complete"
    )
    timeout_seconds: int = Field(
        300,
        description="Max wait time for running goals",
        ge=0,
        le=3600,
    )


class ResumeSchedulerRequest(BaseModel):
    """Request to resume scheduler."""
    
    operator: str = Field(..., description="Username/ID of operator")


class TriggerGoalRequest(BaseModel):
    """Request to manually trigger goal run."""
    
    operator: str = Field(..., description="Username/ID of operator")
    scheduled_time: Optional[datetime] = Field(
        None,
        description="Scheduled time (default: now)"
    )


class SchedulerControlResponse(BaseModel):
    """Response for pause/resume operations."""
    
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Human-readable message")
    paused_at: Optional[str] = Field(None, description="Time paused")
    resumed_at: Optional[str] = Field(None, description="Time resumed")
    reason: Optional[str] = Field(None, description="Reason for pause")
    running_goals_at_pause: Optional[int] = Field(
        None,
        description="Running goals when paused"
    )
    running_goals_after_wait: Optional[int] = Field(
        None,
        description="Running goals after wait"
    )


class GoalRunResponse(BaseModel):
    """Response for manual trigger operation."""
    
    status: str = Field(..., description="Trigger status")
    message: str = Field(..., description="Human-readable message")
    goal_instance_id: str = Field(..., description="Goal instance ID")
    scheduled_time: str = Field(..., description="Scheduled time")
    operator: str = Field(..., description="Operator who triggered")


class SchedulerStatusResponse(BaseModel):
    """Response for scheduler status query."""
    
    status: str = Field(..., description="Scheduler status (running/paused)")
    is_paused: bool = Field(..., description="Whether scheduler is paused")
    is_running: bool = Field(..., description="Whether scheduler is running")
    paused_at: Optional[str] = Field(None, description="Time paused")
    paused_by: Optional[str] = Field(None, description="Who paused")
    paused_reason: Optional[str] = Field(None, description="Reason for pause")
    resumed_at: Optional[str] = Field(None, description="Time resumed")
    resumed_by: Optional[str] = Field(None, description="Who resumed")
    updated_at: str = Field(..., description="Last updated time")
    running_goals_count: int = Field(..., description="Currently running goals")


class ActionLogResponse(BaseModel):
    """Response for action log entry."""
    
    log_id: str
    action: str
    operator: str
    timestamp: str
    goal_instance_id: Optional[str] = None
    reason: Optional[str] = None
    action_metadata: dict


# Global service instances
_admin_service: Optional[SchedulerAdminService] = None
_scheduler_service: Optional[GoalSchedulerService] = None
_idempotency_service: Optional[IdempotencyService] = None


def get_admin_service(db: Session = Depends(get_db)) -> SchedulerAdminService:
    """Get scheduler admin service instance.
    
    Args:
        db: Database session
        
    Returns:
        SchedulerAdminService
    """
    global _admin_service
    if _admin_service is None:
        _admin_service = SchedulerAdminService(db)
    return _admin_service


def get_scheduler_service(db: Session = Depends(get_db)) -> GoalSchedulerService:
    """Get goal scheduler service instance.
    
    Args:
        db: Database session
        
    Returns:
        GoalSchedulerService
    """
    global _scheduler_service
    global _idempotency_service
    
    if _idempotency_service is None:
        _idempotency_service = IdempotencyService(db)
    
    if _scheduler_service is None:
        _scheduler_service = GoalSchedulerService(
            idempotency_service=_idempotency_service
        )
    
    return _scheduler_service


# Endpoints


@router.post("/pause", response_model=SchedulerControlResponse)
async def pause_scheduler(
    request: PauseSchedulerRequest,
    admin_service: SchedulerAdminService = Depends(get_admin_service),
) -> SchedulerControlResponse:
    """Pause the scheduler.
    
    Stops scheduling new goal runs. Optionally waits for running goals to complete.
    
    Args:
        request: Pause request with operator and options
        admin_service: Scheduler admin service
        
    Returns:
        SchedulerControlResponse with pause result
    """
    result = await admin_service.pause_scheduler(
        operator=request.operator,
        reason=request.reason,
        wait_for_completion=request.wait_for_completion,
        timeout_seconds=request.timeout_seconds,
    )
    
    return SchedulerControlResponse(**result)


@router.post("/resume", response_model=SchedulerControlResponse)
async def resume_scheduler(
    request: ResumeSchedulerRequest,
    admin_service: SchedulerAdminService = Depends(get_admin_service),
) -> SchedulerControlResponse:
    """Resume the scheduler.
    
    Resumes scheduling goal runs after pause.
    
    Args:
        request: Resume request with operator
        admin_service: Scheduler admin service
        
    Returns:
        SchedulerControlResponse with resume result
    """
    result = await admin_service.resume_scheduler(operator=request.operator)
    
    return SchedulerControlResponse(**result)


@router.post("/trigger/{goal_instance_id}", response_model=GoalRunResponse)
async def trigger_goal_run(
    goal_instance_id: str,
    request: TriggerGoalRequest,
    admin_service: SchedulerAdminService = Depends(get_admin_service),
    scheduler_service: GoalSchedulerService = Depends(get_scheduler_service),
) -> GoalRunResponse:
    """Manually trigger a goal run.
    
    Bypasses normal scheduling to immediately run a specific goal.
    
    Args:
        goal_instance_id: ID of goal instance to trigger
        request: Trigger request with operator and options
        admin_service: Scheduler admin service
        scheduler_service: Goal scheduler service
        
    Returns:
        GoalRunResponse with trigger result
        
    Raises:
        HTTPException: If goal execution fails
    """
    # Log the trigger action
    trigger_result = await admin_service.trigger_goal_run(
        goal_instance_id=goal_instance_id,
        operator=request.operator,
        scheduled_time=request.scheduled_time,
    )
    
    # Execute the goal
    try:
        scheduled_time = request.scheduled_time or datetime.now()
        
        # Register as running
        admin_service.register_running_goal(goal_instance_id)
        
        try:
            goal_result = await scheduler_service.run_goal_with_retry(
                goal_instance_id=goal_instance_id,
                scheduled_time=scheduled_time,
                correlation_id=f"manual-trigger-{goal_instance_id}",
            )
            
            if goal_result.status.value != "completed":
                raise HTTPException(
                    status_code=500,
                    detail=f"Goal execution failed: {goal_result.error_message}",
                )
        finally:
            # Unregister running goal
            admin_service.unregister_running_goal(goal_instance_id)
        
        return GoalRunResponse(**trigger_result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger goal: {str(e)}",
        )


@router.get("/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status(
    admin_service: SchedulerAdminService = Depends(get_admin_service),
) -> SchedulerStatusResponse:
    """Get current scheduler status.
    
    Returns operational status and metadata.
    
    Args:
        admin_service: Scheduler admin service
        
    Returns:
        SchedulerStatusResponse with current status
    """
    status = await admin_service.get_scheduler_status()
    
    return SchedulerStatusResponse(**status)


@router.get("/actions", response_model=list[ActionLogResponse])
async def get_recent_actions(
    limit: int = 100,
    admin_service: SchedulerAdminService = Depends(get_admin_service),
) -> list[ActionLogResponse]:
    """Get recent admin actions.
    
    Returns audit log of recent pause/resume/trigger operations.
    
    Args:
        limit: Maximum number of actions to return
        admin_service: Scheduler admin service
        
    Returns:
        List of ActionLogResponse
    """
    actions = await admin_service.get_recent_actions(limit)
    
    return [ActionLogResponse(**action) for action in actions]


@router.get("/actions/{operator}", response_model=list[ActionLogResponse])
async def get_actions_by_operator(
    operator: str,
    limit: int = 100,
    admin_service: SchedulerAdminService = Depends(get_admin_service),
) -> list[ActionLogResponse]:
    """Get admin actions by specific operator.
    
    Returns audit log of actions by a specific operator.
    
    Args:
        operator: Operator username/ID
        limit: Maximum number of actions to return
        admin_service: Scheduler admin service
        
    Returns:
        List of ActionLogResponse
    """
    actions = await admin_service.get_actions_by_operator(operator, limit)
    
    return [ActionLogResponse(**action) for action in actions]
