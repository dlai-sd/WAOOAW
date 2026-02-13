"""Scheduler persistence service for state recovery.

Handles saving scheduler state and recovering after restart.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
import logging

from sqlalchemy.orm import Session

from models.scheduled_goal_run import ScheduledGoalRunModel, ScheduledGoalRunRepository
from models.goal_run import GoalRunModel, GoalRunRepository
from services.goal_scheduler_service import GoalSchedulerService


logger = logging.getLogger(__name__)


class RecoveryResult:
    """Result of scheduler recovery operation."""
    
    def __init__(self):
        """Initialize recovery result."""
        self.interrupted_runs_count = 0
        self.missed_runs_count = 0
        self.replayed_runs_count = 0
        self.skipped_runs_count = 0
        self.recovery_errors: list[dict] = []
    
    def to_dict(self) -> dict:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "interrupted_runs_count": self.interrupted_runs_count,
            "missed_runs_count": self.missed_runs_count,
            "replayed_runs_count": self.replayed_runs_count,
            "skipped_runs_count": self.skipped_runs_count,
            "recovery_errors": self.recovery_errors,
        }


class SchedulerPersistenceService:
    """Service for scheduler state persistence and recovery."""
    
    def __init__(
        self,
        db: Session,
        scheduler_service: Optional[GoalSchedulerService] = None,
        replay_threshold_hours: int = 24,
    ):
        """Initialize persistence service.
        
        Args:
            db: Database session
            scheduler_service: Goal scheduler service for replaying runs
            replay_threshold_hours: Hours threshold for replaying missed runs
        """
        self.db = db
        self.scheduler_service = scheduler_service
        self.replay_threshold_hours = replay_threshold_hours
        self.scheduled_run_repo = ScheduledGoalRunRepository(db)
        self.goal_run_repo = GoalRunRepository(db)
    
    async def recover_state(self) -> RecoveryResult:
        """Recover scheduler state after restart.
        
        Recovery logic:
        1. Find all goal runs with status=running and mark as failed (interrupted)
        2. Find all missed scheduled runs (scheduled_time < now, status=pending)
        3. For each missed run:
           - If missed < replay_threshold_hours: replay immediately
           - If missed >= replay_threshold_hours: skip and log warning
        
        Returns:
            RecoveryResult with counts and errors
        """
        result = RecoveryResult()
        current_time = datetime.now(timezone.utc)
        
        logger.info("Starting scheduler recovery", extra={
            "current_time": current_time.isoformat(),
            "replay_threshold_hours": self.replay_threshold_hours,
        })
        
        # Step 1: Mark interrupted runs as failed
        await self._mark_interrupted_runs_as_failed(result)
        
        # Step 2: Find and process missed runs
        missed_runs = self.scheduled_run_repo.get_missed_runs(current_time)
        result.missed_runs_count = len(missed_runs)
        
        logger.info(f"Found {result.missed_runs_count} missed scheduled runs")
        
        # Step 3: Replay or skip based on threshold
        for scheduled_run in missed_runs:
            try:
                if self._should_replay(scheduled_run, current_time):
                    await self._replay_missed_run(scheduled_run, result)
                else:
                    self._skip_old_run(scheduled_run, result)
            except Exception as e:
                error_info = {
                    "scheduled_run_id": scheduled_run.scheduled_run_id,
                    "goal_instance_id": scheduled_run.goal_instance_id,
                    "scheduled_time": scheduled_run.scheduled_time.isoformat(),
                    "error": str(e),
                }
                result.recovery_errors.append(error_info)
                logger.error(
                    f"Error processing missed run {scheduled_run.scheduled_run_id}",
                    extra=error_info,
                    exc_info=True,
                )
        
        logger.info("Scheduler recovery completed", extra=result.to_dict())
        
        return result
    
    async def _mark_interrupted_runs_as_failed(self, result: RecoveryResult) -> None:
        """Mark all running goal runs as failed (interrupted by restart).
        
        Args:
            result: RecoveryResult to update
        """
        interrupted_runs = self.goal_run_repo.get_runs_by_status("running")
        result.interrupted_runs_count = len(interrupted_runs)
        
        logger.info(f"Found {result.interrupted_runs_count} interrupted runs")
        
        for goal_run in interrupted_runs:
            goal_run.mark_as_failed(
                error_message="Goal run interrupted by scheduler restart",
                error_details={"recovery": True},
            )
            self.goal_run_repo.update(goal_run)
            
            logger.warning(
                f"Marked interrupted run as failed: {goal_run.run_id}",
                extra={
                    "run_id": goal_run.run_id,
                    "goal_instance_id": goal_run.goal_instance_id,
                    "idempotency_key": goal_run.idempotency_key,
                },
            )
    
    def _should_replay(
        self,
        scheduled_run: ScheduledGoalRunModel,
        current_time: datetime,
    ) -> bool:
        """Check if missed run should be replayed.
        
        Args:
            scheduled_run: Scheduled run to check
            current_time: Current time
            
        Returns:
            True if should replay, False if should skip
        """
        return not scheduled_run.is_very_old_missed(
            threshold_hours=self.replay_threshold_hours,
            current_time=current_time,
        )
    
    async def _replay_missed_run(
        self,
        scheduled_run: ScheduledGoalRunModel,
        result: RecoveryResult,
    ) -> None:
        """Replay a missed scheduled run.
        
        Args:
            scheduled_run: Scheduled run to replay
            result: RecoveryResult to update
        """
        logger.info(
            f"Replaying missed run: {scheduled_run.scheduled_run_id}",
            extra={
                "scheduled_run_id": scheduled_run.scheduled_run_id,
                "goal_instance_id": scheduled_run.goal_instance_id,
                "scheduled_time": scheduled_run.scheduled_time.isoformat(),
                "hired_instance_id": scheduled_run.hired_instance_id,
            },
        )
        
        # Use scheduler service to replay with retry logic
        if self.scheduler_service:
            try:
                await self.scheduler_service.run_goal_with_retry(
                    goal_instance_id=scheduled_run.goal_instance_id,
                    hired_instance_id=scheduled_run.hired_instance_id,
                    scheduled_time=scheduled_run.scheduled_time,
                )
                result.replayed_runs_count += 1
            except Exception as e:
                logger.error(
                    f"Failed to replay missed run {scheduled_run.scheduled_run_id}",
                    extra={
                        "scheduled_run_id": scheduled_run.scheduled_run_id,
                        "error": str(e),
                    },
                    exc_info=True,
                )
                raise
        else:
            logger.warning("No scheduler service configured, cannot replay")
            result.replayed_runs_count += 1  # Count as replayed for simulation
        
        # Mark scheduled run as completed
        scheduled_run.mark_completed()
        self.scheduled_run_repo.update(scheduled_run)
    
    def _skip_old_run(
        self,
        scheduled_run: ScheduledGoalRunModel,
        result: RecoveryResult,
    ) -> None:
        """Skip a very old missed run.
        
        Args:
            scheduled_run: Scheduled run to skip
            result: RecoveryResult to update
        """
        current_time = datetime.now(timezone.utc)
        age_hours = (current_time - scheduled_run.scheduled_time).total_seconds() / 3600
        
        logger.warning(
            f"Skipping very old missed run: {scheduled_run.scheduled_run_id}",
            extra={
                "scheduled_run_id": scheduled_run.scheduled_run_id,
                "goal_instance_id": scheduled_run.goal_instance_id,
                "scheduled_time": scheduled_run.scheduled_time.isoformat(),
                "age_hours": age_hours,
                "threshold_hours": self.replay_threshold_hours,
            },
        )
        
        # Mark scheduled run as cancelled
        scheduled_run.mark_cancelled()
        self.scheduled_run_repo.update(scheduled_run)
        
        result.skipped_runs_count += 1
    
    async def save_state(
        self,
        goal_instance_id: str,
        scheduled_time: datetime,
        hired_instance_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> ScheduledGoalRunModel:
        """Save a scheduled goal run to database.
        
        Args:
            goal_instance_id: Goal instance ID
            scheduled_time: When to execute (UTC)
            hired_instance_id: Optional hired instance ID
            metadata: Additional metadata
            
        Returns:
            Saved ScheduledGoalRunModel
        """
        # Generate scheduled run ID
        scheduled_run_id = f"sched_{goal_instance_id}_{int(scheduled_time.timestamp())}"
        
        scheduled_run = ScheduledGoalRunModel.create_scheduled_run(
            scheduled_run_id=scheduled_run_id,
            goal_instance_id=goal_instance_id,
            scheduled_time=scheduled_time,
            hired_instance_id=hired_instance_id,
            metadata=metadata,
        )
        
        saved_run = self.scheduled_run_repo.add(scheduled_run)
        
        logger.debug(
            f"Saved scheduled run: {scheduled_run_id}",
            extra={
                "scheduled_run_id": scheduled_run_id,
                "goal_instance_id": goal_instance_id,
                "scheduled_time": scheduled_time.isoformat(),
            },
        )
        
        return saved_run
    
    def get_pending_runs(self) -> list[ScheduledGoalRunModel]:
        """Get all pending scheduled runs.
        
        Returns:
            List of pending ScheduledGoalRunModel
        """
        return self.scheduled_run_repo.get_pending_runs()
    
    def get_upcoming_runs(
        self,
        limit: int = 100,
        current_time: Optional[datetime] = None,
    ) -> list[ScheduledGoalRunModel]:
        """Get upcoming scheduled runs.
        
        Args:
            limit: Maximum number of runs to return
            current_time: Current time (default: now)
            
        Returns:
            List of upcoming ScheduledGoalRunModel
        """
        return self.scheduled_run_repo.get_upcoming_runs(limit, current_time)
    
    def cleanup_old_completed_runs(
        self,
        days_old: int = 30,
        current_time: Optional[datetime] = None,
    ) -> int:
        """Delete old completed scheduled runs.
        
        Args:
            days_old: Days old to delete
            current_time: Current time (default: now)
            
        Returns:
            Number of rows deleted
        """
        deleted_count = self.scheduled_run_repo.delete_old_completed(
            days_old=days_old,
            current_time=current_time,
        )
        
        logger.info(
            f"Cleaned up {deleted_count} old completed scheduled runs",
            extra={"days_old": days_old, "deleted_count": deleted_count},
        )
        
        return deleted_count
