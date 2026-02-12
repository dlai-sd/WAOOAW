"""Scheduler admin service for pause/resume/trigger operations.

Provides administrative control over the goal scheduler with audit logging.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from models.scheduler_state import (
    SchedulerStateModel,
    SchedulerStateRepository,
    SchedulerActionLogModel,
    SchedulerActionLogRepository,
)


logger = logging.getLogger(__name__)


class SchedulerAdminService:
    """Service for scheduler administrative operations."""
    
    def __init__(self, db: Session):
        """Initialize admin service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.state_repository = SchedulerStateRepository(db)
        self.log_repository = SchedulerActionLogRepository(db)
        self._running_goals: set[str] = set()  # Track currently running goals
    
    async def pause_scheduler(
        self,
        operator: str,
        reason: Optional[str] = None,
        wait_for_completion: bool = True,
        timeout_seconds: int = 300,
    ) -> dict:
        """Pause the scheduler.
        
        Optionally waits for running goals to complete (graceful pause).
        
        Args:
            operator: Username/ID of operator pausing scheduler
            reason: Optional reason for pausing
            wait_for_completion: Wait for running goals to complete
            timeout_seconds: Max wait time for running goals
            
        Returns:
            Dictionary with pause result
        """
        # Get current state
        state = self.state_repository.get_or_create_state()
        
        if state.is_paused():
            logger.warning(f"Scheduler already paused by {state.paused_by}")
            return {
                "status": "already_paused",
                "message": f"Scheduler already paused by {state.paused_by}",
                "paused_at": state.paused_at.isoformat() if state.paused_at else None,
            }
        
        # Pause the scheduler
        state.pause(operator, reason)
        self.state_repository.update_state(state)
        
        # Log the action
        log = SchedulerActionLogModel.create_log(
            log_id=str(uuid.uuid4()),
            action="pause",
            operator=operator,
            reason=reason,
            metadata={
                "wait_for_completion": wait_for_completion,
                "timeout_seconds": timeout_seconds,
            },
        )
        self.log_repository.add_log(log)
        
        logger.info(
            f"Scheduler paused by {operator} "
            f"(reason: {reason or 'none'}, wait_for_completion: {wait_for_completion})"
        )
        
        # Wait for running goals if requested
        running_count = len(self._running_goals)
        if wait_for_completion and running_count > 0:
            logger.info(
                f"Waiting for {running_count} running goals to complete "
                f"(timeout: {timeout_seconds}s)"
            )
            
            waited_seconds = 0
            while len(self._running_goals) > 0 and waited_seconds < timeout_seconds:
                await asyncio.sleep(1)
                waited_seconds += 1
            
            if len(self._running_goals) > 0:
                logger.warning(
                    f"Timeout waiting for running goals: {len(self._running_goals)} still running"
                )
        
        return {
            "status": "paused",
            "message": f"Scheduler paused by {operator}",
            "paused_at": state.paused_at.isoformat(),
            "reason": reason,
            "running_goals_at_pause": running_count,
            "running_goals_after_wait": len(self._running_goals),
        }
    
    async def resume_scheduler(self, operator: str) -> dict:
        """Resume the scheduler.
        
        Args:
            operator: Username/ID of operator resuming scheduler
            
        Returns:
            Dictionary with resume result
        """
        # Get current state
        state = self.state_repository.get_or_create_state()
        
        if state.is_running():
            logger.warning("Scheduler already running")
            return {
                "status": "already_running",
                "message": "Scheduler already running",
            }
        
        # Resume the scheduler
        state.resume(operator)
        self.state_repository.update_state(state)
        
        # Log the action
        log = SchedulerActionLogModel.create_log(
            log_id=str(uuid.uuid4()),
            action="resume",
            operator=operator,
            metadata={
                "paused_by": state.paused_by,
                "paused_at": state.paused_at.isoformat() if state.paused_at else None,
            },
        )
        self.log_repository.add_log(log)
        
        logger.info(f"Scheduler resumed by {operator}")
        
        return {
            "status": "running",
            "message": f"Scheduler resumed by {operator}",
            "resumed_at": state.resumed_at.isoformat(),
        }
    
    async def trigger_goal_run(
        self,
        goal_instance_id: str,
        operator: str,
        scheduled_time: Optional[datetime] = None,
    ) -> dict:
        """Manually trigger a goal run.
        
        Args:
            goal_instance_id: Goal instance ID to trigger
            operator: Username/ID of operator triggering run
            scheduled_time: Optional scheduled time (default: now)
            
        Returns:
            Dictionary with trigger result
        """
        if scheduled_time is None:
            scheduled_time = datetime.now(timezone.utc)
        
        # Log the action
        log = SchedulerActionLogModel.create_log(
            log_id=str(uuid.uuid4()),
            action="trigger",
            operator=operator,
            goal_instance_id=goal_instance_id,
            metadata={
                "scheduled_time": scheduled_time.isoformat(),
            },
        )
        self.log_repository.add_log(log)
        
        logger.info(
            f"Manual trigger: goal_instance_id={goal_instance_id} "
            f"operator={operator}"
        )
        
        return {
            "status": "triggered",
            "message": f"Goal run triggered by {operator}",
            "goal_instance_id": goal_instance_id,
            "scheduled_time": scheduled_time.isoformat(),
            "operator": operator,
        }
    
    async def get_scheduler_status(self) -> dict:
        """Get current scheduler status.
        
        Returns:
            Dictionary with scheduler status
        """
        state = self.state_repository.get_or_create_state()
        
        return {
            "status": state.status,
            "is_paused": state.is_paused(),
            "is_running": state.is_running(),
            "paused_at": state.paused_at.isoformat() if state.paused_at else None,
            "paused_by": state.paused_by,
            "paused_reason": state.paused_reason,
            "resumed_at": state.resumed_at.isoformat() if state.resumed_at else None,
            "resumed_by": state.resumed_by,
            "updated_at": state.updated_at.isoformat(),
            "running_goals_count": len(self._running_goals),
        }
    
    async def is_scheduler_paused(self) -> bool:
        """Check if scheduler is paused.
        
        Returns:
            True if paused, False if running
        """
        state = self.state_repository.get_or_create_state()
        return state.is_paused()
    
    def register_running_goal(self, goal_instance_id: str) -> None:
        """Register a goal as currently running.
        
        Args:
            goal_instance_id: Goal instance ID
        """
        self._running_goals.add(goal_instance_id)
        logger.debug(f"Registered running goal: {goal_instance_id}")
    
    def unregister_running_goal(self, goal_instance_id: str) -> None:
        """Unregister a goal that completed/failed.
        
        Args:
            goal_instance_id: Goal instance ID
        """
        self._running_goals.discard(goal_instance_id)
        logger.debug(f"Unregistered running goal: {goal_instance_id}")
    
    async def get_recent_actions(self, limit: int = 100) -> list[dict]:
        """Get recent admin actions.
        
        Args:
            limit: Maximum number of actions to return
            
        Returns:
            List of action dictionaries
        """
        logs = self.log_repository.get_recent_logs(limit)
        return [log.to_dict() for log in logs]
    
    async def get_actions_by_operator(
        self,
        operator: str,
        limit: int = 100,
    ) -> list[dict]:
        """Get actions by specific operator.
        
        Args:
            operator: Operator username/ID
            limit: Maximum number of actions to return
            
        Returns:
            List of action dictionaries
        """
        logs = self.log_repository.get_logs_by_operator(operator, limit)
        return [log.to_dict() for log in logs]
