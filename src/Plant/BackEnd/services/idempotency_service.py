"""Idempotency service for goal execution.

Ensures each goal is executed exactly once by tracking runs with
unique idempotency keys and preventing duplicate/concurrent executions.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from models.goal_run import GoalRunModel, GoalRunRepository


logger = logging.getLogger(__name__)


class IdempotencyService:
    """Service for managing goal run idempotency."""
    
    def __init__(self, db: Session):
        """Initialize idempotency service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.repository = GoalRunRepository(db)
    
    def generate_idempotency_key(
        self,
        goal_instance_id: str,
        scheduled_time: datetime,
    ) -> str:
        """Generate idempotency key for a goal run.
        
        Format: {goal_instance_id}:{scheduled_time_utc_iso}
        
        Args:
            goal_instance_id: ID of the goal instance
            scheduled_time: Scheduled execution time (UTC)
            
        Returns:
            Idempotency key string
        """
        # Ensure scheduled_time is timezone-aware
        if scheduled_time.tzinfo is None:
            scheduled_time = scheduled_time.replace(tzinfo=timezone.utc)
        
        # Format: goal-123:2026-02-12T10:30:00+00:00
        time_str = scheduled_time.isoformat()
        return f"{goal_instance_id}:{time_str}"
    
    async def get_or_create_run(
        self,
        goal_instance_id: str,
        idempotency_key: str,
    ) -> tuple[GoalRunModel, bool]:
        """Get existing run or create new one with idempotency guarantee.
        
        This method is safe for concurrent calls - only one run will be
        created for a given idempotency key, even if called simultaneously.
        
        Args:
            goal_instance_id: ID of the goal instance
            idempotency_key: Unique key for this run
            
        Returns:
            Tuple of (GoalRunModel, is_new) where is_new=True if run was created
        """
        # First, try to get existing run
        existing_run = self.repository.get_by_idempotency_key(idempotency_key)
        
        if existing_run:
            logger.info(
                f"Found existing run: run_id={existing_run.run_id} "
                f"status={existing_run.status} key={idempotency_key}"
            )
            return existing_run, False
        
        # No existing run, create new one with lock
        run_id = str(uuid.uuid4())
        new_run = GoalRunModel.create_pending(
            run_id=run_id,
            goal_instance_id=goal_instance_id,
            idempotency_key=idempotency_key,
        )
        
        try:
            # Use create_with_lock to handle race conditions
            created_run = self.repository.create_with_lock(new_run)
            
            # Check if we created a new run or got existing one
            is_new = created_run.run_id == run_id
            
            if is_new:
                logger.info(
                    f"Created new run: run_id={run_id} key={idempotency_key}"
                )
            else:
                logger.info(
                    f"Concurrent creation detected, using existing run: "
                    f"run_id={created_run.run_id} key={idempotency_key}"
                )
            
            return created_run, is_new
            
        except Exception as e:
            logger.error(
                f"Failed to create goal run: key={idempotency_key} error={str(e)}"
            )
            raise
    
    async def mark_run_running(self, run_id: str) -> GoalRunModel:
        """Mark a run as currently running.
        
        Args:
            run_id: ID of the run to update
            
        Returns:
            Updated GoalRunModel
            
        Raises:
            ValueError: If run not found or already in terminal state
        """
        run = self.repository.get_by_run_id(run_id)
        
        if not run:
            raise ValueError(f"Run not found: {run_id}")
        
        if run.is_terminal_state():
            raise ValueError(
                f"Cannot mark completed/failed run as running: {run_id}"
            )
        
        run.mark_running()
        run = self.repository.update(run)
        
        logger.info(f"Marked run as running: run_id={run_id}")
        
        return run
    
    async def mark_run_completed(
        self,
        run_id: str,
        deliverable_id: str,
        duration_ms: int,
    ) -> GoalRunModel:
        """Mark a run as completed successfully.
        
        Args:
            run_id: ID of the run to update
            deliverable_id: ID of the created deliverable
            duration_ms: Execution duration in milliseconds
            
        Returns:
            Updated GoalRunModel
            
        Raises:
            ValueError: If run not found
        """
        run = self.repository.get_by_run_id(run_id)
        
        if not run:
            raise ValueError(f"Run not found: {run_id}")
        
        run.mark_completed(deliverable_id, duration_ms)
        run = self.repository.update(run)
        
        logger.info(
            f"Marked run as completed: run_id={run_id} "
            f"deliverable_id={deliverable_id} duration_ms={duration_ms}"
        )
        
        return run
    
    async def mark_run_failed(
        self,
        run_id: str,
        error_message: str,
        error_type: str,
        duration_ms: int,
        stack_trace: Optional[str] = None,
    ) -> GoalRunModel:
        """Mark a run as failed.
        
        Args:
            run_id: ID of the run to update
            error_message: Human-readable error message
            error_type: Type of error (TRANSIENT, PERMANENT)
            duration_ms: Execution duration in milliseconds
            stack_trace: Full stack trace (optional)
            
        Returns:
            Updated GoalRunModel
            
        Raises:
            ValueError: If run not found
        """
        run = self.repository.get_by_run_id(run_id)
        
        if not run:
            raise ValueError(f"Run not found: {run_id}")
        
        error_details = {
            "message": error_message,
            "type": error_type,
            "stack_trace": stack_trace,
        }
        
        run.mark_failed(error_details, duration_ms)
        run = self.repository.update(run)
        
        logger.info(
            f"Marked run as failed: run_id={run_id} "
            f"error_type={error_type} duration_ms={duration_ms}"
        )
        
        return run
    
    async def get_run_status(self, idempotency_key: str) -> Optional[dict]:
        """Get the status of a run by its idempotency key.
        
        Args:
            idempotency_key: Idempotency key to search for
            
        Returns:
            Dictionary with run details or None if not found
        """
        run = self.repository.get_by_idempotency_key(idempotency_key)
        
        if not run:
            return None
        
        return run.to_dict()
    
    async def should_execute_run(self, run: GoalRunModel) -> bool:
        """Determine if a run should be executed.
        
        A run should be executed if:
        - It exists and is in pending status (new run)
        - It does not exist yet (shouldn't happen with get_or_create_run)
        
        A run should NOT be executed if:
        - It's already running (concurrent execution)
        - It's completed (idempotent - return cached result)
        - It's failed (handled by retry logic elsewhere)
        
        Args:
            run: GoalRunModel to check
            
        Returns:
            True if run should be executed, False if should skip/return cached
        """
        if run.status == "pending":
            return True
        
        if run.status == "running":
            logger.warning(
                f"Run already running (concurrent execution detected): "
                f"run_id={run.run_id} key={run.idempotency_key}"
            )
            return False
        
        if run.status == "completed":
            logger.info(
                f"Run already completed (returning cached result): "
                f"run_id={run.run_id} deliverable_id={run.deliverable_id}"
            )
            return False
        
        if run.status == "failed":
            logger.info(
                f"Run previously failed: run_id={run.run_id} "
                f"error={run.error_details.get('message') if run.error_details else 'unknown'}"
            )
            return False
        
        return True
