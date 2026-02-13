"""Scheduler health monitoring service.

Tracks scheduler metrics for health monitoring, alerting, and observability.
Provides health status, success/failure rates, and Prometheus metrics.
"""

import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from services.scheduler_dlq_service import DLQService


logger = logging.getLogger(__name__)


# Alert thresholds
PENDING_GOALS_ALERT_THRESHOLD = 100
SUCCESS_RATE_ALERT_THRESHOLD = 0.90  # 90%
METRICS_RETENTION_HOURS = 1  # Keep 1 hour of metrics


class SchedulerStatus(Enum):
    """Scheduler health status."""
    
    HEALTHY = "healthy"      # Success rate > 95%, DLQ < 5
    DEGRADED = "degraded"    # Success rate 80-95%, DLQ 5-20
    DOWN = "down"           # Success rate < 80%, DLQ > 20, or stopped


@dataclass
class GoalExecutionMetric:
    """Single goal execution metric for tracking."""
    
    goal_instance_id: str
    timestamp: datetime
    success: bool
    duration_ms: int
    error_type: Optional[str] = None


@dataclass
class SchedulerHealthMetrics:
    """Comprehensive scheduler health metrics."""
    
    status: SchedulerStatus
    pending_goals: int
    running_goals: int
    success_rate_1h: float
    failure_rate_1h: float
    total_executions_1h: int
    last_run: Optional[datetime]
    last_success: Optional[datetime]
    last_failure: Optional[datetime]
    dlq_size: int
    avg_duration_ms: float


class SchedulerHealthService:
    """Service for tracking and reporting scheduler health."""
    
    def __init__(self, dlq_service: Optional[DLQService] = None):
        """Initialize health service.
        
        Args:
            dlq_service: DLQ service for checking DLQ size (optional)
        """
        self.dlq_service = dlq_service
        self._metrics: deque[GoalExecutionMetric] = deque()
        self._pending_goals: int = 0
        self._running_goals: int = 0
        self._last_run: Optional[datetime] = None
        self._last_success: Optional[datetime] = None
        self._last_failure: Optional[datetime] = None
        self._last_alert_time: Optional[datetime] = None
    
    def record_goal_execution(
        self,
        goal_instance_id: str,
        success: bool,
        duration_ms: int,
        error_type: Optional[str] = None,
    ) -> None:
        """Record a goal execution for metrics tracking.
        
        Args:
            goal_instance_id: ID of executed goal
            success: Whether execution succeeded
            duration_ms: Execution duration in milliseconds
            error_type: Type of error if failed (optional)
        """
        now = datetime.now(timezone.utc)
        
        metric = GoalExecutionMetric(
            goal_instance_id=goal_instance_id,
            timestamp=now,
            success=success,
            duration_ms=duration_ms,
            error_type=error_type,
        )
        
        self._metrics.append(metric)
        self._last_run = now
        
        if success:
            self._last_success = now
        else:
            self._last_failure = now
        
        # Clean old metrics
        self._cleanup_old_metrics()
        
        logger.debug(
            f"Recorded goal execution: goal={goal_instance_id} "
            f"success={success} duration={duration_ms}ms"
        )
    
    def set_pending_goals(self, count: int) -> None:
        """Update pending goals count.
        
        Args:
            count: Number of pending goals
        """
        self._pending_goals = count
        
        # Alert if threshold exceeded
        if count > PENDING_GOALS_ALERT_THRESHOLD:
            self._trigger_pending_goals_alert(count)
    
    def set_running_goals(self, count: int) -> None:
        """Update running goals count.
        
        Args:
            count: Number of running goals
        """
        self._running_goals = count
    
    async def get_health_metrics(self) -> SchedulerHealthMetrics:
        """Get current scheduler health metrics.
        
        Returns:
            SchedulerHealthMetrics with current health status
        """
        # Calculate rates from last hour
        recent_metrics = self._get_recent_metrics()
        total_executions = len(recent_metrics)
        
        if total_executions > 0:
            successes = sum(1 for m in recent_metrics if m.success)
            success_rate = successes / total_executions
            failure_rate = 1.0 - success_rate
            avg_duration = sum(m.duration_ms for m in recent_metrics) / total_executions
        else:
            success_rate = 1.0  # Assume healthy if no data
            failure_rate = 0.0
            avg_duration = 0.0
        
        # Get DLQ size
        dlq_size = 0
        if self.dlq_service:
            try:
                dlq_size = self.dlq_service.repository.count_active()
            except Exception as e:
                logger.error(f"Failed to get DLQ size: {e}")
        
        # Determine health status
        status = self._calculate_health_status(success_rate, dlq_size)
        
        # Check for alerts
        if success_rate < SUCCESS_RATE_ALERT_THRESHOLD:
            self._trigger_success_rate_alert(success_rate)
        
        metrics = SchedulerHealthMetrics(
            status=status,
            pending_goals=self._pending_goals,
            running_goals=self._running_goals,
            success_rate_1h=success_rate,
            failure_rate_1h=failure_rate,
            total_executions_1h=total_executions,
            last_run=self._last_run,
            last_success=self._last_success,
            last_failure=self._last_failure,
            dlq_size=dlq_size,
            avg_duration_ms=avg_duration,
        )
        
        logger.info(
            f"Scheduler health: status={status.value} "
            f"success_rate={success_rate:.2%} dlq_size={dlq_size}"
        )
        
        return metrics
    
    def get_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format.
        
        Returns:
            Prometheus-formatted metrics string
        """
        recent_metrics = self._get_recent_metrics()
        total = len(recent_metrics)
        successes = sum(1 for m in recent_metrics if m.success)
        failures = total - successes
        
        lines = [
            "# HELP scheduler_goals_total Total number of goal executions",
            "# TYPE scheduler_goals_total counter",
            f"scheduler_goals_total {total}",
            "",
            "# HELP scheduler_goals_success_total Successful goal executions",
            "# TYPE scheduler_goals_success_total counter",
            f"scheduler_goals_success_total {successes}",
            "",
            "# HELP scheduler_goals_failure_total Failed goal executions",
            "# TYPE scheduler_goals_failure_total counter",
            f"scheduler_goals_failure_total {failures}",
            "",
            "# HELP scheduler_success_rate Success rate over last hour",
            "# TYPE scheduler_success_rate gauge",
            f"scheduler_success_rate {successes / total if total > 0 else 1.0}",
            "",
            "# HELP scheduler_pending_goals Number of pending goals",
            "# TYPE scheduler_pending_goals gauge",
            f"scheduler_pending_goals {self._pending_goals}",
            "",
            "# HELP scheduler_running_goals Number of running goals",
            "# TYPE scheduler_running_goals gauge",
            f"scheduler_running_goals {self._running_goals}",
            "",
        ]
        
        if recent_metrics:
            avg_duration = sum(m.duration_ms for m in recent_metrics) / len(recent_metrics)
            lines.extend([
                "# HELP scheduler_avg_duration_ms Average execution duration in milliseconds",
                "# TYPE scheduler_avg_duration_ms gauge",
                f"scheduler_avg_duration_ms {avg_duration}",
                "",
            ])
        
        return "\n".join(lines)
    
    def _get_recent_metrics(self) -> list[GoalExecutionMetric]:
        """Get metrics from the last hour.
        
        Returns:
            List of recent metrics
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=METRICS_RETENTION_HOURS)
        return [m for m in self._metrics if m.timestamp >= cutoff]
    
    def _cleanup_old_metrics(self) -> None:
        """Remove metrics older than retention period."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=METRICS_RETENTION_HOURS)
        
        while self._metrics and self._metrics[0].timestamp < cutoff:
            self._metrics.popleft()
    
    def _calculate_health_status(self, success_rate: float, dlq_size: int) -> SchedulerStatus:
        """Calculate overall health status.
        
        Args:
            success_rate: Success rate (0.0 to 1.0)
            dlq_size: Number of items in DLQ
            
        Returns:
            SchedulerStatus
        """
        # Check if scheduler has run recently (within 10 minutes)
        if self._last_run:
            time_since_run = datetime.now(timezone.utc) - self._last_run
            if time_since_run > timedelta(minutes=10):
                return SchedulerStatus.DOWN
        
        # Determine status based on success rate and DLQ size
        if success_rate >= 0.95 and dlq_size < 5:
            return SchedulerStatus.HEALTHY
        elif success_rate >= 0.80 and dlq_size < 20:
            return SchedulerStatus.DEGRADED
        else:
            return SchedulerStatus.DOWN
    
    def _trigger_success_rate_alert(self, success_rate: float) -> None:
        """Trigger alert for low success rate.
        
        Args:
            success_rate: Current success rate
        """
        # Rate limit alerts (once per 5 minutes)
        now = datetime.now(timezone.utc)
        if self._last_alert_time and (now - self._last_alert_time) < timedelta(minutes=5):
            return
        
        self._last_alert_time = now
        
        logger.error(
            f"⚠️  SCHEDULER HEALTH ALERT: Low success rate {success_rate:.2%} "
            f"(threshold: {SUCCESS_RATE_ALERT_THRESHOLD:.2%}). "
            f"Investigate scheduler failures immediately."
        )
    
    def _trigger_pending_goals_alert(self, pending_count: int) -> None:
        """Trigger alert for high pending goals count.
        
        Args:
            pending_count: Number of pending goals
        """
        # Rate limit alerts (once per 5 minutes)
        now = datetime.now(timezone.utc)
        if self._last_alert_time and (now - self._last_alert_time) < timedelta(minutes=5):
            return
        
        self._last_alert_time = now
        
        logger.error(
            f"⚠️  SCHEDULER PENDING GOALS ALERT: {pending_count} pending goals "
            f"(threshold: {PENDING_GOALS_ALERT_THRESHOLD}). "
            f"Scheduler may be overloaded or stuck."
        )
