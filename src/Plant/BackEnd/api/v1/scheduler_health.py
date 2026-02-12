"""Scheduler health monitoring API endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from services.scheduler_dlq_service import DLQService
from services.scheduler_health_service import (
    SchedulerHealthService,
    SchedulerStatus,
)


router = APIRouter(prefix="/api/v1", tags=["scheduler"])


# Global health service instance (would be dependency-injected in production)
_health_service: Optional[SchedulerHealthService] = None


def get_health_service(db: Session = Depends(get_db)) -> SchedulerHealthService:
    """Get or create health service instance.
    
    Args:
        db: Database session
        
    Returns:
        SchedulerHealthService instance
    """
    global _health_service
    if _health_service is None:
        dlq_service = DLQService(db)
        _health_service = SchedulerHealthService(dlq_service=dlq_service)
    return _health_service


class SchedulerHealthResponse(BaseModel):
    """Scheduler health response model."""
    
    status: str = Field(..., description="Health status: healthy, degraded, or down")
    pending_goals: int = Field(..., description="Number of pending goals")
    running_goals: int = Field(..., description="Number of currently running goals")
    success_rate_1h: float = Field(..., description="Success rate over last hour (0.0-1.0)")
    failure_rate_1h: float = Field(..., description="Failure rate over last hour (0.0-1.0)")
    total_executions_1h: int = Field(..., description="Total executions in last hour")
    last_run: Optional[str] = Field(None, description="Timestamp of last scheduler run")
    last_success: Optional[str] = Field(None, description="Timestamp of last successful execution")
    last_failure: Optional[str] = Field(None, description="Timestamp of last failed execution")
    dlq_size: int = Field(..., description="Number of items in dead letter queue")
    avg_duration_ms: float = Field(..., description="Average execution duration in milliseconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "pending_goals": 45,
                "running_goals": 3,
                "success_rate_1h": 0.95,
                "failure_rate_1h": 0.05,
                "total_executions_1h": 120,
                "last_run": "2026-02-12T10:30:00Z",
                "last_success": "2026-02-12T10:30:00Z",
                "last_failure": "2026-02-12T09:15:00Z",
                "dlq_size": 2,
                "avg_duration_ms": 1250.5,
            }
        }


@router.get("/scheduler/health", response_model=SchedulerHealthResponse)
async def get_scheduler_health(
    health_service: SchedulerHealthService = Depends(get_health_service),
) -> SchedulerHealthResponse:
    """Get comprehensive scheduler health metrics.
    
    Returns health status, success/failure rates, pending goals, DLQ size, and timing metrics.
    
    Health Status:
    - **healthy**: Success rate > 95%, DLQ < 5 items
    - **degraded**: Success rate 80-95%, DLQ 5-20 items
    - **down**: Success rate < 80%, DLQ > 20 items, or scheduler stopped
    
    Triggers alerts when:
    - Success rate falls below 90% over 1 hour
    - Pending goals exceed 100
    
    Returns:
        SchedulerHealthResponse with current health metrics
    """
    metrics = await health_service.get_health_metrics()
    
    return SchedulerHealthResponse(
        status=metrics.status.value,
        pending_goals=metrics.pending_goals,
        running_goals=metrics.running_goals,
        success_rate_1h=metrics.success_rate_1h,
        failure_rate_1h=metrics.failure_rate_1h,
        total_executions_1h=metrics.total_executions_1h,
        last_run=metrics.last_run.isoformat() if metrics.last_run else None,
        last_success=metrics.last_success.isoformat() if metrics.last_success else None,
        last_failure=metrics.last_failure.isoformat() if metrics.last_failure else None,
        dlq_size=metrics.dlq_size,
        avg_duration_ms=metrics.avg_duration_ms,
    )


@router.get("/scheduler/metrics", response_class=PlainTextResponse)
async def get_scheduler_metrics(
    health_service: SchedulerHealthService = Depends(get_health_service),
) -> str:
    """Export scheduler metrics in Prometheus format.
    
    Provides metrics for Prometheus scraping:
    - scheduler_goals_total: Total goal executions
    - scheduler_goals_success_total: Successful executions
    - scheduler_goals_failure_total: Failed executions
    - scheduler_success_rate: Success rate (0.0-1.0)
    - scheduler_pending_goals: Number of pending goals
    - scheduler_running_goals: Number of running goals
    - scheduler_avg_duration_ms: Average execution duration
    
    Returns:
        Prometheus-formatted metrics text
    """
    return health_service.get_prometheus_metrics()
