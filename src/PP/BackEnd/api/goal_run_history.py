"""Goal Run History and Failure Analysis API - AGP2-PP-3.3

PP admin API for monitoring goal execution history, analyzing failures,
and providing operations team with tools to diagnose and retry failed runs.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field

from api.deps import get_authorization_header
from api.security import require_admin
from clients.plant_client import PlantAPIClient, get_plant_client


router = APIRouter(prefix="/goal-runs", tags=["goal-runs"])


class GoalRunSummary(BaseModel):
    """Summary of a single goal run."""
    
    run_id: str
    goal_instance_id: str
    hired_instance_id: str
    customer_id: str
    agent_id: str
    
    # Goal info
    goal_template_id: str
    goal_name: Optional[str] = None
    frequency: str
    
    # Run status
    status: Literal["pending", "running", "completed", "failed", "retrying"]
    
    # Timing
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Execution details
    deliverable_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 5
    
    # Error details (if failed)
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    is_transient: Optional[bool] = None
    
    # Correlation
    correlation_id: Optional[str] = None


class GoalRunDetail(BaseModel):
    """Detailed information about a goal run with full error context."""
    
    # Basic info (same as summary)
    run_id: str
    goal_instance_id: str
    hired_instance_id: str
    customer_id: str
    agent_id: str
    
    goal_template_id: str
    goal_name: Optional[str]
    frequency: str
    goal_settings: dict = Field(default_factory=dict)
    
    # Status and timing
    status: str
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    
    # Execution
    deliverable_id: Optional[str]
    deliverable_status: Optional[str]
    retry_count: int
    max_retries: int
    next_retry_at: Optional[datetime]
    
    # Full error details
    error_type: Optional[str]
    error_message: Optional[str]
    error_stack_trace: Optional[str]
    is_transient: Optional[bool]
    error_details: Optional[dict] = None
    
    # Retry history
    retry_history: List[dict] = Field(default_factory=list)
    
    # Correlation
    correlation_id: Optional[str]
    
    # Audit
    created_at: datetime
    updated_at: datetime


class FailurePattern(BaseModel):
    """Pattern of failures for analysis."""
    
    error_type: str
    error_message_pattern: str
    occurrence_count: int
    first_seen: datetime
    last_seen: datetime
    affected_agents: List[str]
    is_transient: bool
    suggested_action: Optional[str] = None


class GoalRunStats(BaseModel):
    """Aggregate statistics for goal runs."""
    
    total_runs: int = 0
    completed_runs: int = 0
    failed_runs: int = 0
    running_runs: int = 0
    pending_runs: int = 0
    
    success_rate: float = 0.0
    avg_duration_seconds: Optional[float] = None
    
    # Failures
    transient_failures: int = 0
    permanent_failures: int = 0
    retrying_count: int = 0
    
    # Time period
    period_start: datetime
    period_end: datetime


class GoalRunHistoryResponse(BaseModel):
    """Paginated goal run history."""
    
    runs: List[GoalRunSummary]
    stats: GoalRunStats
    total: int
    page: int
    page_size: int


class FailureAnalysisResponse(BaseModel):
    """Failure analysis with patterns and recommendations."""
    
    failure_patterns: List[FailurePattern]
    total_failures: int
    unique_error_types: int
    
    # Recommendations
    top_issues: List[dict] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)


@router.get(
    "/history",
    response_model=GoalRunHistoryResponse,
    summary="Get goal run history"
)
async def get_goal_run_history(
    # Filters
    hired_instance_id: Optional[str] = Query(None, description="Filter by agent instance"),
    customer_id: Optional[str] = Query(None, description="Filter by customer"),
    agent_id: Optional[str] = Query(None, description="Filter by agent type"),
    goal_template_id: Optional[str] = Query(None, description="Filter by goal template"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter runs after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter runs before this date"),
    
    # Pagination
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    
    # Sorting
    sort_by: str = Query("started_at", description="Sort by: started_at, completed_at, duration_seconds"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    
    # Auth
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Get paginated goal run history with filtering and statistics.
    
    Shows all goal executions across all agents, with ability to filter by:
    - Agent instance
    - Customer
    - Goal type
    - Status (completed, failed, running, etc.)
    - Time period
    
    Includes aggregate statistics:
    - Total runs and success rate
    - Average duration
    - Failure breakdown (transient vs permanent)
    """
    
    try:
        # In production, this would query goal_runs table
        # Placeholder data
        runs_data: List[GoalRunSummary] = []
        
        # Calculate stats
        from datetime import timezone
        now = datetime.now(timezone.utc)
        stats = GoalRunStats(
            total_runs=len(runs_data),
            completed_runs=sum(1 for r in runs_data if r.status == "completed"),
            failed_runs=sum(1 for r in runs_data if r.status == "failed"),
            running_runs=sum(1 for r in runs_data if r.status == "running"),
            pending_runs=sum(1 for r in runs_data if r.status == "pending"),
            success_rate=0.0,
            period_start=start_date or now,
            period_end=end_date or now,
        )
        
        if stats.total_runs > 0:
            stats.success_rate = stats.completed_runs / stats.total_runs
        
        # Apply filters (placeholder)
        filtered_runs = runs_data
        
        # Pagination
        total = len(filtered_runs)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_runs = filtered_runs[start_idx:end_idx]
        
        return GoalRunHistoryResponse(
            runs=paginated_runs,
            stats=stats,
            total=total,
            page=page,
            page_size=page_size,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch goal run history: {str(e)}")


@router.get(
    "/{run_id}/detail",
    response_model=GoalRunDetail,
    summary="Get goal run details"
)
async def get_goal_run_detail(
    run_id: str,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Get detailed information about a specific goal run.
    
    Includes:
    - Full execution timeline
    - Complete error details with stack trace
    - Retry history
    - Related deliverable status
    """
    
    try:
        # In production, fetch from database
        raise HTTPException(status_code=404, detail="Goal run not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch run detail: {str(e)}")


@router.get(
    "/failures",
    response_model=List[GoalRunSummary],
    summary="Get all failed goal runs"
)
async def get_failed_runs(
    is_transient: Optional[bool] = Query(None, description="Filter by transient vs permanent"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Get all failed goal runs for quick troubleshooting.
    
    Filters:
    - `is_transient=true`: Only transient failures (network errors, rate limits)
    - `is_transient=false`: Only permanent failures (config errors, auth failures)
    - No filter: All failures
    """
    
    try:
        # Placeholder
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch failed runs: {str(e)}")


@router.get(
    "/failure-analysis",
    response_model=FailureAnalysisResponse,
    summary="Analyze failure patterns"
)
async def analyze_failures(
    start_date: Optional[datetime] = Query(None, description="Analyze failures after this date"),
    end_date: Optional[datetime] = Query(None, description="Analyze failures before this date"),
    hired_instance_id: Optional[str] = Query(None, description="Analyze specific agent instance"),
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Analyze failure patterns and provide recommendations.
    
    Groups failures by:
    - Error type and message pattern
    - Affected agents
    - Frequency and timing
    
    Provides:
    - Most common failure types
    - Suggested remediation actions
    - Trends (increasing vs decreasing failures)
    """
    
    try:
        # In production, this would:
        # 1. Query failed runs in time period
        # 2. Group by error_type and message pattern
        # 3. Identify trends
        # 4. Generate recommendations
        
        patterns: List[FailurePattern] = []
        
        top_issues = []
        if patterns:
            # Sort by occurrence and take top 5
            sorted_patterns = sorted(patterns, key=lambda p: p.occurrence_count, reverse=True)
            top_issues = [
                {
                    "error_type": p.error_type,
                    "count": p.occurrence_count,
                    "suggested_action": p.suggested_action,
                }
                for p in sorted_patterns[:5]
            ]
        
        recommended_actions = []
        # Generate recommendations based on patterns
        if any(p.error_type == "NetworkTimeout" for p in patterns):
            recommended_actions.append("Increase network timeout configuration")
        if any(p.error_type == "RateLimitExceeded" for p in patterns):
            recommended_actions.append("Review API rate limits and reduce goal frequency")
        if any(p.error_type == "AuthenticationError" for p in patterns):
            recommended_actions.append("Check expired credentials and refresh tokens")
        
        return FailureAnalysisResponse(
            failure_patterns=patterns,
            total_failures=sum(p.occurrence_count for p in patterns),
            unique_error_types=len(set(p.error_type for p in patterns)),
            top_issues=top_issues,
            recommended_actions=recommended_actions,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze failures: {str(e)}")


@router.post(
    "/{run_id}/retry",
    summary="Manually retry a failed goal run"
)
async def retry_failed_run(
    run_id: str,
    force: bool = Query(False, description="Force retry even if max retries reached"),
    reason: str = Query(..., description="Reason for manual retry (for audit)"),
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Manually retry a failed goal run.
    
    Creates a new run attempt with same goal settings.
    Logs the manual retry in audit trail with operator and reason.
    
    **Use Cases**:
    - Failed due to transient error, now resolved
    - Credentials were updated
    - Platform was down, now back up
    """
    
    try:
        # In production, this would:
        # 1. Validate run exists and is failed
        # 2. Check retry count vs max_retries (unless force=true)
        # 3. Create new run attempt
        # 4. Log manual retry in audit trail
        # 5. Trigger goal execution
        
        return {
            "status": "success",
            "message": "Goal run retry initiated",
            "original_run_id": run_id,
            "new_run_id": f"RUN-retry-{run_id}",
            "retry_count": 1,
            "reason": reason,
            "forced": force,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retry run: {str(e)}")


@router.post(
    "/agent/{hired_instance_id}/retry-all-failed",
    summary="Retry all failed runs for an agent"
)
async def retry_all_failed_for_agent(
    hired_instance_id: str,
    only_transient: bool = Query(True, description="Only retry transient failures"),
    reason: str = Query(..., description="Reason for bulk retry"),
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Retry all failed goal runs for a specific agent instance.
    
    Useful when:
    - Agent credentials were updated
    - Configuration issue was fixed
    - External service is back online
    
    **Safety**:
    - By default, only retries transient failures
    - Set `only_transient=false` to retry all failures
    """
    
    try:
        # In production, this would:
        # 1. Find all failed runs for agent
        # 2. Filter by transient/permanent if requested
        # 3. Create retry attempts for each
        # 4. Log bulk retry operation
        
        return {
            "status": "success",
            "message": "Bulk retry initiated",
            "hired_instance_id": hired_instance_id,
            "runs_retried": 0,
            "only_transient": only_transient,
            "reason": reason,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retry failed runs: {str(e)}")


@router.get(
    "/agent/{hired_instance_id}/stats",
    summary="Get goal run statistics for an agent"
)
async def get_agent_goal_stats(
    hired_instance_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Get goal run statistics for a specific agent over a time period.
    
    Returns:
    - Total runs and success rate
    - Run frequency and patterns
    - Failure breakdown
    - Performance metrics (avg duration)
    """
    
    try:
        from datetime import timezone, timedelta
        now = datetime.now(timezone.utc)
        period_start = now - timedelta(days=days)
        
        # Placeholder stats
        stats = GoalRunStats(
            total_runs=0,
            completed_runs=0,
            failed_runs=0,
            running_runs=0,
            pending_runs=0,
            success_rate=0.0,
            transient_failures=0,
            permanent_failures=0,
            retrying_count=0,
            period_start=period_start,
            period_end=now,
        )
        
        return {
            "hired_instance_id": hired_instance_id,
            "period_days": days,
            "stats": stats,
            "daily_breakdown": [],  # Array of daily stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch agent stats: {str(e)}")


@router.delete(
    "/{run_id}",
    summary="Cancel a pending/running goal run"
)
async def cancel_goal_run(
    run_id: str,
    reason: str = Query(..., description="Reason for cancellation"),
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
):
    """Cancel a pending or running goal run.
    
    **Use Cases**:
    - Goal run stuck in running state
    - Need to stop execution immediately
    - Debugging/troubleshooting
    
    **Note**: Cannot cancel completed or failed runs.
    """
    
    try:
        # In production, this would:
        # 1. Validate run is pending or running
        # 2. Mark as cancelled
        # 3. Stop any active execution
        # 4. Log cancellation in audit trail
        
        return {
            "status": "success",
            "message": "Goal run cancelled",
            "run_id": run_id,
            "reason": reason,
            "cancelled_at": datetime.now().isoformat(),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel run: {str(e)}")
