"""Goal scheduler service with production-grade error handling.

Provides reliable goal execution with:
- Transient error retry with exponential backoff
- Permanent error fast-fail
- Comprehensive logging and alerting
- Max retry limits
"""

from __future__ import annotations

import asyncio
import logging
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from services.scheduler_dlq_service import DLQService
    from services.idempotency_service import IdempotencyService

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Classification of errors for retry logic."""
    
    TRANSIENT = "transient"  # Temporary failures that should retry
    PERMANENT = "permanent"  # Non-recoverable errors that fail fast


class GoalRunStatus(Enum):
    """Status of a goal run execution."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass(frozen=True)
class GoalRunResult:
    """Result of a goal execution attempt."""
    
    goal_instance_id: str
    status: GoalRunStatus
    deliverable_id: Optional[str] = None
    error_message: Optional[str] = None
    error_type: Optional[ErrorType] = None
    attempts: int = 1
    total_duration_ms: Optional[int] = None


class GoalExecutionError(Exception):
    """Base exception for goal execution failures."""
    
    def __init__(self, message: str, error_type: ErrorType):
        super().__init__(message)
        self.message = message
        self.error_type = error_type


class TransientError(GoalExecutionError):
    """Transient error that should be retried."""
    
    def __init__(self, message: str):
        super().__init__(message, ErrorType.TRANSIENT)


class PermanentError(GoalExecutionError):
    """Permanent error that should not be retried."""
    
    def __init__(self, message: str):
        super().__init__(message, ErrorType.PERMANENT)


class GoalSchedulerService:
    """Production-grade goal scheduler with error handling and retry logic."""
    
    def __init__(
        self,
        max_retries: int = 5,
        initial_backoff_seconds: int = 60,
        backoff_multiplier: float = 2.0,
        dlq_service: Optional["DLQService"] = None,
        idempotency_service: Optional["IdempotencyService"] = None,
    ):
        """Initialize goal scheduler service.
        
        Args:
            max_retries: Maximum retry attempts for transient failures
            initial_backoff_seconds: Initial backoff delay in seconds
            backoff_multiplier: Multiplier for exponential backoff
            dlq_service: Dead letter queue service for failed goals (optional)
            idempotency_service: Idempotency service to prevent duplicate runs (optional)
        """
        self.max_retries = max_retries
        self.initial_backoff_seconds = initial_backoff_seconds
        self.backoff_multiplier = backoff_multiplier
        self.dlq_service = dlq_service
        self.idempotency_service = idempotency_service
        self._consecutive_failures: dict[str, int] = {}
    
    async def run_goal_with_retry(
        self,
        goal_instance_id: str,
        scheduled_time: datetime,
        hired_instance_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> GoalRunResult:
        """Execute a goal with automatic retry on transient failures.
        
        Args:
            goal_instance_id: Unique identifier for the goal instance
            scheduled_time: Scheduled execution time (UTC) for idempotency key
            hired_instance_id: ID of hired agent instance (for DLQ tracking)
            correlation_id: Request correlation ID for tracing
            
        Returns:
            GoalRunResult with execution status and details
            
        Raises:
            PermanentError: For non-recoverable errors (no retry)
        """
        log_prefix = f"[{correlation_id}] " if correlation_id else ""
        start_time = datetime.now(timezone.utc)
        
        # Idempotency check - prevent duplicate runs
        run_id: Optional[str] = None
        if self.idempotency_service:
            # Generate idempotency key and get or create run
            idempotency_key = self.idempotency_service.generate_idempotency_key(
                goal_instance_id=goal_instance_id,
                scheduled_time=scheduled_time,
            )
            
            goal_run, is_new = await self.idempotency_service.get_or_create_run(
                goal_instance_id=goal_instance_id,
                idempotency_key=idempotency_key,
            )
            
            run_id = goal_run.run_id
            
            # Check if this run should be executed
            should_execute = await self.idempotency_service.should_execute_run(goal_run)
            
            if not should_execute:
                # Return cached result or indicate duplicate
                if goal_run.status == "completed":
                    logger.info(
                        f"{log_prefix}Returning cached result for idempotent run: "
                        f"run_id={run_id} deliverable_id={goal_run.deliverable_id}"
                    )
                    return GoalRunResult(
                        goal_instance_id=goal_instance_id,
                        status=GoalRunStatus.COMPLETED,
                        deliverable_id=goal_run.deliverable_id,
                        attempts=1,
                        total_duration_ms=goal_run.duration_ms,
                    )
                elif goal_run.status == "running":
                    logger.warning(
                        f"{log_prefix}Duplicate execution attempt detected (run already running): "
                        f"run_id={run_id} key={idempotency_key}"
                    )
                    return GoalRunResult(
                        goal_instance_id=goal_instance_id,
                        status=GoalRunStatus.RUNNING,
                        attempts=1,
                    )
                elif goal_run.status == "failed":
                    # Return the failure
                    error_details = goal_run.error_details or {}
                    return GoalRunResult(
                        goal_instance_id=goal_instance_id,
                        status=GoalRunStatus.FAILED,
                        error_message=error_details.get("message", "Execution failed"),
                        error_type=ErrorType[error_details.get("type", "TRANSIENT")],
                        attempts=1,
                        total_duration_ms=goal_run.duration_ms,
                    )
            
            # Mark run as running
            await self.idempotency_service.mark_run_running(run_id)
            logger.info(
                f"{log_prefix}Starting idempotent goal execution: "
                f"run_id={run_id} key={idempotency_key}"
            )
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    f"{log_prefix}Starting goal execution: "
                    f"goal_instance_id={goal_instance_id} attempt={attempt}/{self.max_retries}"
                )
                
                # Execute the goal
                deliverable_id = await self._execute_goal(goal_instance_id, correlation_id)
                
                # Success - reset failure counter
                self._consecutive_failures.pop(goal_instance_id, None)
                
                duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
                
                # Mark run as completed in idempotency service
                if self.idempotency_service and run_id:
                    await self.idempotency_service.mark_run_completed(
                        run_id=run_id,
                        deliverable_id=deliverable_id,
                        duration_ms=duration_ms,
                    )
                
                logger.info(
                    f"{log_prefix}Goal execution succeeded: "
                    f"goal_instance_id={goal_instance_id} deliverable_id={deliverable_id} "
                    f"attempts={attempt} duration_ms={duration_ms}"
                )
                
                return GoalRunResult(
                    goal_instance_id=goal_instance_id,
                    status=GoalRunStatus.COMPLETED,
                    deliverable_id=deliverable_id,
                    attempts=attempt,
                    total_duration_ms=duration_ms,
                )
            
            except PermanentError as exc:
                # Permanent error - fail fast, no retry
                duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
                
                logger.error(
                    f"{log_prefix}Goal execution failed (permanent error): "
                    f"goal_instance_id={goal_instance_id} error={exc.message} "
                    f"attempts={attempt} duration_ms={duration_ms}"
                )
                
                self._track_consecutive_failure(goal_instance_id)
                
                # Mark run as failed in idempotency service
                if self.idempotency_service and run_id:
                    await self.idempotency_service.mark_run_failed(
                        run_id=run_id,
                        error_message=exc.message,
                        error_type=ErrorType.PERMANENT.value,
                        duration_ms=duration_ms,
                        stack_trace=traceback.format_exc(),
                    )
                
                return GoalRunResult(
                    goal_instance_id=goal_instance_id,
                    status=GoalRunStatus.FAILED,
                    error_message=exc.message,
                    error_type=ErrorType.PERMANENT,
                    attempts=attempt,
                    total_duration_ms=duration_ms,
                )
            
            except TransientError as exc:
                # Transient error - retry with backoff
                logger.warning(
                    f"{log_prefix}Goal execution failed (transient error): "
                    f"goal_instance_id={goal_instance_id} error={exc.message} "
                    f"attempt={attempt}/{self.max_retries}"
                )
                
                if attempt < self.max_retries:
                    backoff_seconds = self._calculate_backoff(attempt)
                    logger.info(
                        f"{log_prefix}Retrying goal after {backoff_seconds}s backoff: "
                        f"goal_instance_id={goal_instance_id} attempt={attempt + 1}/{self.max_retries}"
                    )
                    await asyncio.sleep(backoff_seconds)
                    continue
                else:
                    # Max retries exhausted - move to DLQ if available
                    duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
                    
                    logger.error(
                        f"{log_prefix}Goal execution failed after max retries: "
                        f"goal_instance_id={goal_instance_id} error={exc.message} "
                        f"attempts={attempt} duration_ms={duration_ms}"
                    )
                    
                    self._track_consecutive_failure(goal_instance_id)
                    
                    # Mark run as failed in idempotency service
                    if self.idempotency_service and run_id:
                        await self.idempotency_service.mark_run_failed(
                            run_id=run_id,
                            error_message=f"Max retries exhausted: {exc.message}",
                            error_type=ErrorType.TRANSIENT.value,
                            duration_ms=duration_ms,
                            stack_trace=traceback.format_exc(),
                        )
                    
                    # Move to DLQ if service is available and hired_instance_id provided
                    if self.dlq_service and hired_instance_id:
                        try:
                            stack_trace = traceback.format_exc()
                            await self.dlq_service.move_to_dlq(
                                goal_instance_id=goal_instance_id,
                                hired_instance_id=hired_instance_id,
                                error_type=ErrorType.TRANSIENT,
                                error_message=exc.message,
                                failure_count=attempt,
                                stack_trace=stack_trace,
                            )
                            logger.info(
                                f"{log_prefix}Goal moved to DLQ: goal_instance_id={goal_instance_id}"
                            )
                        except Exception as dlq_error:
                            logger.error(
                                f"{log_prefix}Failed to move goal to DLQ: {str(dlq_error)}",
                                exc_info=True,
                            )
                    
                    return GoalRunResult(
                        goal_instance_id=goal_instance_id,
                        status=GoalRunStatus.FAILED,
                        error_message=f"Max retries exhausted: {exc.message}",
                        error_type=ErrorType.TRANSIENT,
                        attempts=attempt,
                        total_duration_ms=duration_ms,
                    )
            
            except Exception as exc:
                # Unclassified error - treat as transient and retry
                logger.warning(
                    f"{log_prefix}Goal execution failed (unclassified error): "
                    f"goal_instance_id={goal_instance_id} error={str(exc)} "
                    f"attempt={attempt}/{self.max_retries}",
                    exc_info=True,
                )
                
                if attempt < self.max_retries:
                    backoff_seconds = self._calculate_backoff(attempt)
                    logger.info(
                        f"{log_prefix}Retrying goal after {backoff_seconds}s backoff: "
                        f"goal_instance_id={goal_instance_id} attempt={attempt + 1}/{self.max_retries}"
                    )
                    await asyncio.sleep(backoff_seconds)
                    continue
                else:
                    # Max retries exhausted - move to DLQ if available
                    duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
                    
                    logger.error(
                        f"{log_prefix}Goal execution failed after max retries: "
                        f"goal_instance_id={goal_instance_id} error={str(exc)} "
                        f"attempts={attempt} duration_ms={duration_ms}",
                        exc_info=True,
                    )
                    
                    self._track_consecutive_failure(goal_instance_id)
                    
                    # Mark run as failed in idempotency service
                    if self.idempotency_service and run_id:
                        await self.idempotency_service.mark_run_failed(
                            run_id=run_id,
                            error_message=str(exc),
                            error_type=ErrorType.TRANSIENT.value,
                            duration_ms=duration_ms,
                            stack_trace=traceback.format_exc(),
                        )
                    
                    # Move to DLQ if service is available and hired_instance_id provided
                    if self.dlq_service and hired_instance_id:
                        try:
                            stack_trace = traceback.format_exc()
                            await self.dlq_service.move_to_dlq(
                                goal_instance_id=goal_instance_id,
                                hired_instance_id=hired_instance_id,
                                error_type=ErrorType.TRANSIENT,
                                error_message=str(exc),
                                failure_count=attempt,
                                stack_trace=stack_trace,
                            )
                            logger.info(
                                f"{log_prefix}Goal moved to DLQ: goal_instance_id={goal_instance_id}"
                            )
                        except Exception as dlq_error:
                            logger.error(
                                f"{log_prefix}Failed to move goal to DLQ: {str(dlq_error)}",
                                exc_info=True,
                            )
                    
                    return GoalRunResult(
                        goal_instance_id=goal_instance_id,
                        status=GoalRunStatus.FAILED,
                        error_message=str(exc),
                        error_type=ErrorType.TRANSIENT,
                        attempts=attempt,
                        total_duration_ms=duration_ms,
                    )
        
        # Should never reach here
        raise RuntimeError("Unexpected code path in run_goal_with_retry")
    
    async def _execute_goal(
        self,
        goal_instance_id: str,
        correlation_id: Optional[str] = None,
    ) -> str:
        """Execute a single goal instance.
        
        This is a stub that will be implemented with actual goal execution logic.
        Subclasses or dependency injection can provide the real implementation.
        
        Args:
            goal_instance_id: Unique identifier for the goal instance
            correlation_id: Request correlation ID for tracing
            
        Returns:
            Deliverable ID for the created deliverable
            
        Raises:
            TransientError: For temporary failures (network, rate limit, etc.)
            PermanentError: For non-recoverable failures (invalid config, etc.)
        """
        # TODO: Implement actual goal execution logic
        # This should:
        # 1. Load goal instance from database
        # 2. Execute goal logic (create post, place trade, etc.)
        # 3. Create deliverable draft
        # 4. Return deliverable ID
        raise NotImplementedError("Goal execution logic not yet implemented")
    
    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff delay in seconds.
        
        Backoff schedule: 1m, 2m, 4m, 8m, 16m (for default 60s base)
        
        Args:
            attempt: Current attempt number (1-indexed)
            
        Returns:
            Backoff delay in seconds (float to support sub-second delays in tests)
        """
        return self.initial_backoff_seconds * (self.backoff_multiplier ** (attempt - 1))
    
    def _track_consecutive_failure(self, goal_instance_id: str) -> None:
        """Track consecutive failures for alerting.
        
        Args:
            goal_instance_id: Goal instance identifier
        """
        count = self._consecutive_failures.get(goal_instance_id, 0) + 1
        self._consecutive_failures[goal_instance_id] = count
        
        # Alert on 3+ consecutive failures
        if count >= 3:
            logger.error(
                f"ALERT: Goal has {count} consecutive failures: "
                f"goal_instance_id={goal_instance_id}"
            )
    
    def classify_error(self, exc: Exception) -> ErrorType:
        """Classify an exception as transient or permanent.
        
        Args:
            exc: Exception to classify
            
        Returns:
            ErrorType classification
        """
        # Already classified
        if isinstance(exc, GoalExecutionError):
            return exc.error_type
        
        # Classify common exceptions
        exc_message = str(exc).lower()
        exc_type = type(exc).__name__.lower()
        
        # Transient patterns
        transient_patterns = [
            "timeout",
            "connection",
            "network",
            "rate limit",
            "too many requests",
            "service unavailable",
            "gateway timeout",
            "lock",
            "deadlock",
            "retry",
        ]
        
        # Permanent patterns
        permanent_patterns = [
            "not found",
            "invalid",
            "unauthorized",
            "forbidden",
            "credential",
            "authentication",
            "permission denied",
            "bad request",
            "configuration",
        ]
        
        for pattern in transient_patterns:
            if pattern in exc_message or pattern in exc_type:
                return ErrorType.TRANSIENT
        
        for pattern in permanent_patterns:
            if pattern in exc_message or pattern in exc_type:
                return ErrorType.PERMANENT
        
        # Default to transient for safety (allow retry)
        return ErrorType.TRANSIENT
