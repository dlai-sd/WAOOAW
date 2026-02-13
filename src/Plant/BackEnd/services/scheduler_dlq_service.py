"""Service for managing dead letter queue operations.

This service handles failed goals that require manual intervention,
including moving to DLQ, retry operations, and cleanup.
"""

import logging
import traceback
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from models.scheduler_dlq import SchedulerDLQModel, SchedulerDLQRepository
from services.goal_scheduler_service import ErrorType


logger = logging.getLogger(__name__)


# Alert thresholds
DLQ_SIZE_ALERT_THRESHOLD = 10


class DLQService:
    """Service for dead letter queue operations."""
    
    def __init__(self, db: Session):
        """Initialize DLQ service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.repository = SchedulerDLQRepository(db)
    
    async def move_to_dlq(
        self,
        goal_instance_id: str,
        hired_instance_id: str,
        error_type: ErrorType,
        error_message: str,
        failure_count: int,
        stack_trace: Optional[str] = None,
    ) -> SchedulerDLQModel:
        """Move a failed goal to the dead letter queue.
        
        Args:
            goal_instance_id: ID of the failed goal instance
            hired_instance_id: ID of the hired agent instance
            error_type: Type of error (TRANSIENT or PERMANENT)
            error_message: Human-readable error message
            failure_count: Number of times goal execution was attempted
            stack_trace: Full stack trace (optional)
            
        Returns:
            Created DLQ entry
        """
        # Check if goal already exists in DLQ
        existing = self.repository.get_by_goal_instance(goal_instance_id)
        
        if existing:
            # Update existing entry
            existing.update_failure(error_message, stack_trace)
            dlq_entry = self.repository.update(existing)
            logger.info(
                f"Updated existing DLQ entry: dlq_id={existing.dlq_id} "
                f"goal_instance_id={goal_instance_id} failure_count={existing.failure_count}"
            )
        else:
            # Create new entry
            dlq_id = str(uuid.uuid4())
            dlq_entry = SchedulerDLQModel.create_from_failure(
                dlq_id=dlq_id,
                goal_instance_id=goal_instance_id,
                hired_instance_id=hired_instance_id,
                error_type=error_type.value,
                error_message=error_message,
                stack_trace=stack_trace,
                failure_count=failure_count,
            )
            dlq_entry = self.repository.add(dlq_entry)
            logger.info(
                f"Moved goal to DLQ: dlq_id={dlq_id} goal_instance_id={goal_instance_id}"
            )
        
        # Check if should alert on DLQ size
        await self._check_dlq_size_alert()
        
        return dlq_entry
    
    async def list_dlq_entries(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[SchedulerDLQModel], int]:
        """List active DLQ entries.
        
        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            
        Returns:
            Tuple of (DLQ entries, total count)
        """
        entries = self.repository.list_active(limit=limit, offset=offset)
        total_count = self.repository.count_active()
        
        logger.info(f"Listed DLQ entries: count={len(entries)} total={total_count}")
        
        return entries, total_count
    
    async def get_dlq_entry(self, dlq_id: str) -> Optional[SchedulerDLQModel]:
        """Get a single DLQ entry by ID.
        
        Args:
            dlq_id: DLQ entry ID
            
        Returns:
            DLQ entry or None if not found
        """
        entry = self.repository.get_by_id(dlq_id)
        
        if entry and entry.is_expired():
            logger.warning(f"DLQ entry is expired: dlq_id={dlq_id}")
        
        return entry
    
    async def record_retry_attempt(self, dlq_id: str) -> Optional[SchedulerDLQModel]:
        """Record that a manual retry was attempted for a DLQ entry.
        
        Args:
            dlq_id: DLQ entry ID
            
        Returns:
            Updated DLQ entry or None if not found
        """
        entry = self.repository.get_by_id(dlq_id)
        
        if not entry:
            logger.warning(f"DLQ entry not found for retry: dlq_id={dlq_id}")
            return None
        
        if entry.is_expired():
            logger.warning(f"Cannot retry expired DLQ entry: dlq_id={dlq_id}")
            return None
        
        entry.record_retry_attempt()
        entry = self.repository.update(entry)
        
        logger.info(
            f"Recorded retry attempt: dlq_id={dlq_id} "
            f"retry_count={entry.retry_count} goal_instance_id={entry.goal_instance_id}"
        )
        
        return entry
    
    async def remove_from_dlq(self, dlq_id: str) -> bool:
        """Remove a DLQ entry after successful retry.
        
        Args:
            dlq_id: DLQ entry ID
            
        Returns:
            True if removed, False if not found
        """
        deleted = self.repository.delete(dlq_id)
        
        if deleted:
            logger.info(f"Removed DLQ entry: dlq_id={dlq_id}")
        else:
            logger.warning(f"DLQ entry not found for removal: dlq_id={dlq_id}")
        
        return deleted
    
    async def cleanup_expired(self) -> int:
        """Remove expired DLQ entries.
        
        Returns:
            Number of entries removed
        """
        deleted_count = self.repository.delete_expired()
        
        if deleted_count > 0:
            logger.info(f"Cleaned up expired DLQ entries: count={deleted_count}")
        
        return deleted_count
    
    async def _check_dlq_size_alert(self) -> None:
        """Check if DLQ size exceeds alert threshold and log warning.
        
        This should be integrated with a proper alerting system in production.
        """
        dlq_size = self.repository.count_active()
        
        if dlq_size >= DLQ_SIZE_ALERT_THRESHOLD:
            logger.error(
                f"⚠️  DLQ SIZE ALERT: {dlq_size} items in dead letter queue "
                f"(threshold: {DLQ_SIZE_ALERT_THRESHOLD}). Manual intervention required."
            )
