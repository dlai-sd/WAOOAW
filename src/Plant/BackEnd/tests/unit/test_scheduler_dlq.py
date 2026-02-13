"""Tests for dead letter queue service and integration.

Tests cover DLQ operations including:
- Moving failed goals to DLQ
- Listing DLQ entries
- Retry tracking
- Entry expiration
- DLQ size alerts
- Integration with GoalSchedulerService
"""

import logging
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from models.scheduler_dlq import SchedulerDLQModel, SchedulerDLQRepository
from services.goal_scheduler_service import (
    ErrorType,
    GoalSchedulerService,
    TransientError,
)
from services.scheduler_dlq_service import DLQService, DLQ_SIZE_ALERT_THRESHOLD


class TestSchedulerDLQModel:
    """Test cases for DLQ model operations."""
    
    def test_create_from_failure(self):
        """Test creating DLQ entry from failed goal."""
        dlq_entry = SchedulerDLQModel.create_from_failure(
            dlq_id="dlq-123",
            goal_instance_id="goal-456",
            hired_instance_id="hired-789",
            error_type="TRANSIENT",
            error_message="Test error",
            stack_trace="Stack trace here",
            failure_count=5,
        )
        
        assert dlq_entry.dlq_id == "dlq-123"
        assert dlq_entry.goal_instance_id == "goal-456"
        assert dlq_entry.hired_instance_id == "hired-789"
        assert dlq_entry.error_type == "TRANSIENT"
        assert dlq_entry.error_message == "Test error"
        assert dlq_entry.stack_trace == "Stack trace here"
        assert dlq_entry.failure_count == 5
        assert dlq_entry.retry_count == 0
        assert dlq_entry.first_failed_at is not None
        assert dlq_entry.last_failed_at is not None
        
        # Check expiration is set to 7 days from now
        now = datetime.now(timezone.utc)
        expected_expiry = now + timedelta(days=7)
        time_diff = abs((dlq_entry.expires_at - expected_expiry).total_seconds())
        assert time_diff < 2  # Within 2 seconds
    
    def test_update_failure(self):
        """Test updating failure details."""
        dlq_entry = SchedulerDLQModel.create_from_failure(
            dlq_id="dlq-123",
            goal_instance_id="goal-456",
            hired_instance_id="hired-789",
            error_type="TRANSIENT",
            error_message="First error",
            stack_trace=None,
            failure_count=1,
        )
        
        original_count = dlq_entry.failure_count
        dlq_entry.update_failure("Second error", "New stack trace")
        
        assert dlq_entry.error_message == "Second error"
        assert dlq_entry.stack_trace == "New stack trace"
        assert dlq_entry.failure_count == original_count + 1
    
    def test_record_retry_attempt(self):
        """Test recording retry attempts."""
        dlq_entry = SchedulerDLQModel.create_from_failure(
            dlq_id="dlq-123",
            goal_instance_id="goal-456",
            hired_instance_id="hired-789",
            error_type="TRANSIENT",
            error_message="Test error",
            stack_trace=None,
            failure_count=5,
        )
        
        assert dlq_entry.retry_count == 0
        dlq_entry.record_retry_attempt()
        assert dlq_entry.retry_count == 1
        dlq_entry.record_retry_attempt()
        assert dlq_entry.retry_count == 2
    
    def test_is_expired(self):
        """Test expiration checking."""
        # Create entry that expires in the past
        dlq_entry = SchedulerDLQModel.create_from_failure(
            dlq_id="dlq-123",
            goal_instance_id="goal-456",
            hired_instance_id="hired-789",
            error_type="TRANSIENT",
            error_message="Test error",
            stack_trace=None,
            failure_count=5,
        )
        
        # Not expired yet (expires in 7 days)
        assert not dlq_entry.is_expired()
        
        # Make it expired
        dlq_entry.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        assert dlq_entry.is_expired()


class TestDLQService:
    """Test cases for DLQ service operations."""
    
    @pytest.mark.asyncio
    async def test_move_to_dlq_new_entry(self):
        """Test moving a new goal to DLQ."""
        mock_db = MagicMock(spec=Session)
        dlq_service = DLQService(mock_db)
        
        # Mock repository methods
        dlq_service.repository.get_by_goal_instance = MagicMock(return_value=None)
        dlq_service.repository.add = MagicMock(side_effect=lambda x: x)
        dlq_service.repository.count_active = MagicMock(return_value=5)
        
        dlq_entry = await dlq_service.move_to_dlq(
            goal_instance_id="goal-456",
            hired_instance_id="hired-789",
            error_type=ErrorType.TRANSIENT,
            error_message="Test error",
            failure_count=5,
            stack_trace="Stack trace",
        )
        
        assert dlq_entry.goal_instance_id == "goal-456"
        assert dlq_entry.hired_instance_id == "hired-789"
        assert dlq_entry.error_type == "transient"
        assert dlq_entry.error_message == "Test error"
        assert dlq_entry.failure_count == 5
        dlq_service.repository.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_move_to_dlq_existing_entry(self):
        """Test updating an existing DLQ entry."""
        mock_db = MagicMock(spec=Session)
        dlq_service = DLQService(mock_db)
        
        # Mock existing entry
        existing_entry = SchedulerDLQModel.create_from_failure(
            dlq_id="dlq-123",
            goal_instance_id="goal-456",
            hired_instance_id="hired-789",
            error_type="TRANSIENT",
            error_message="First error",
            stack_trace=None,
            failure_count=3,
        )
        
        dlq_service.repository.get_by_goal_instance = MagicMock(return_value=existing_entry)
        dlq_service.repository.update = MagicMock(side_effect=lambda x: x)
        dlq_service.repository.count_active = MagicMock(return_value=5)
        
        dlq_entry = await dlq_service.move_to_dlq(
            goal_instance_id="goal-456",
            hired_instance_id="hired-789",
            error_type=ErrorType.TRANSIENT,
            error_message="Second error",
            failure_count=5,
            stack_trace="New stack trace",
        )
        
        assert dlq_entry.error_message == "Second error"
        assert dlq_entry.stack_trace == "New stack trace"
        assert dlq_entry.failure_count == 4  # Original 3 + 1 from update
        dlq_service.repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_dlq_size_alert(self, caplog):
        """Test alert triggered when DLQ size exceeds threshold."""
        mock_db = MagicMock(spec=Session)
        dlq_service = DLQService(mock_db)
        
        dlq_service.repository.get_by_goal_instance = MagicMock(return_value=None)
        dlq_service.repository.add = MagicMock(side_effect=lambda x: x)
        dlq_service.repository.count_active = MagicMock(
            return_value=DLQ_SIZE_ALERT_THRESHOLD + 5
        )
        
        with caplog.at_level(logging.ERROR):
            await dlq_service.move_to_dlq(
                goal_instance_id="goal-456",
                hired_instance_id="hired-789",
                error_type=ErrorType.TRANSIENT,
                error_message="Test error",
                failure_count=5,
            )
            
            assert "DLQ SIZE ALERT" in caplog.text
            assert str(DLQ_SIZE_ALERT_THRESHOLD) in caplog.text
    
    @pytest.mark.asyncio
    async def test_list_dlq_entries(self):
        """Test listing DLQ entries."""
        mock_db = MagicMock(spec=Session)
        dlq_service = DLQService(mock_db)
        
        mock_entries = [
            SchedulerDLQModel.create_from_failure(
                dlq_id=f"dlq-{i}",
                goal_instance_id=f"goal-{i}",
                hired_instance_id="hired-789",
                error_type="TRANSIENT",
                error_message="Test error",
                stack_trace=None,
                failure_count=5,
            )
            for i in range(3)
        ]
        
        dlq_service.repository.list_active = MagicMock(return_value=mock_entries)
        dlq_service.repository.count_active = MagicMock(return_value=3)
        
        entries, total = await dlq_service.list_dlq_entries(limit=10, offset=0)
        
        assert len(entries) == 3
        assert total == 3
        dlq_service.repository.list_active.assert_called_once_with(limit=10, offset=0)
    
    @pytest.mark.asyncio
    async def test_record_retry_attempt(self):
        """Test recording a retry attempt."""
        mock_db = MagicMock(spec=Session)
        dlq_service = DLQService(mock_db)
        
        dlq_entry = SchedulerDLQModel.create_from_failure(
            dlq_id="dlq-123",
            goal_instance_id="goal-456",
            hired_instance_id="hired-789",
            error_type="TRANSIENT",
            error_message="Test error",
            stack_trace=None,
            failure_count=5,
        )
        
        dlq_service.repository.get_by_id = MagicMock(return_value=dlq_entry)
        dlq_service.repository.update = MagicMock(side_effect=lambda x: x)
        
        updated_entry = await dlq_service.record_retry_attempt("dlq-123")
        
        assert updated_entry.retry_count == 1
        dlq_service.repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_record_retry_attempt_expired_entry(self):
        """Test retry attempt on expired entry returns None."""
        mock_db = MagicMock(spec=Session)
        dlq_service = DLQService(mock_db)
        
        dlq_entry = SchedulerDLQModel.create_from_failure(
            dlq_id="dlq-123",
            goal_instance_id="goal-456",
            hired_instance_id="hired-789",
            error_type="TRANSIENT",
            error_message="Test error",
            stack_trace=None,
            failure_count=5,
        )
        dlq_entry.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        
        dlq_service.repository.get_by_id = MagicMock(return_value=dlq_entry)
        
        result = await dlq_service.record_retry_attempt("dlq-123")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        """Test cleaning up expired DLQ entries."""
        mock_db = MagicMock(spec=Session)
        dlq_service = DLQService(mock_db)
        
        dlq_service.repository.delete_expired = MagicMock(return_value=5)
        
        deleted_count = await dlq_service.cleanup_expired()
        
        assert deleted_count == 5
        dlq_service.repository.delete_expired.assert_called_once()


class TestSchedulerDLQIntegration:
    """Test cases for DLQ integration with goal scheduler."""
    
    @pytest.mark.asyncio
    async def test_goal_moved_to_dlq_after_max_retries(self):
        """Test goal is moved to DLQ after max retries exhausted."""
        mock_db = MagicMock(spec=Session)
        dlq_service = DLQService(mock_db)
        dlq_service.move_to_dlq = AsyncMock(
            return_value=SchedulerDLQModel.create_from_failure(
                dlq_id="dlq-123",
                goal_instance_id="goal-456",
                hired_instance_id="hired-789",
                error_type="TRANSIENT",
                error_message="Test error",
                stack_trace="",
                failure_count=2,
            )
        )
        
        scheduler = GoalSchedulerService(
            max_retries=2,
            dlq_service=dlq_service,
        )
        
        with patch.object(
            scheduler, "_execute_goal", new_callable=AsyncMock
        ) as mock_execute, patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_execute.side_effect = TransientError("Always fails")
            
            result = await scheduler.run_goal_with_retry(
                goal_instance_id="goal-456",
                hired_instance_id="hired-789",
                scheduled_time=datetime(2026, 2, 15, 10, 0, 0, tzinfo=timezone.utc),
            )
            
            # Should have attempted twice
            assert mock_execute.call_count == 2
            
            # Should have moved to DLQ
            dlq_service.move_to_dlq.assert_called_once()
            call_args = dlq_service.move_to_dlq.call_args[1]
            assert call_args["goal_instance_id"] == "goal-456"
            assert call_args["hired_instance_id"] == "hired-789"
            assert call_args["error_type"] == ErrorType.TRANSIENT
            assert "Always fails" in call_args["error_message"]
            assert call_args["failure_count"] == 2
    
    @pytest.mark.asyncio
    async def test_dlq_not_called_without_hired_instance_id(self):
        """Test DLQ not called if hired_instance_id not provided."""
        mock_db = MagicMock(spec=Session)
        dlq_service = DLQService(mock_db)
        dlq_service.move_to_dlq = AsyncMock()
        
        scheduler = GoalSchedulerService(
            max_retries=2,
            dlq_service=dlq_service,
        )
        
        with patch.object(
            scheduler, "_execute_goal", new_callable=AsyncMock
        ) as mock_execute, patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_execute.side_effect = TransientError("Always fails")
            
            # No hired_instance_id provided
            await scheduler.run_goal_with_retry(
                goal_instance_id="goal-456",
                scheduled_time=datetime(2026, 2, 15, 10, 0, 0, tzinfo=timezone.utc),
            )
            
            # DLQ should not be called
            dlq_service.move_to_dlq.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_scheduler_continues_if_dlq_fails(self):
        """Test scheduler continues even if moving to DLQ fails."""
        mock_db = MagicMock(spec=Session)
        dlq_service = DLQService(mock_db)
        dlq_service.move_to_dlq = AsyncMock(side_effect=Exception("DLQ error"))
        
        scheduler = GoalSchedulerService(
            max_retries=2,
            dlq_service=dlq_service,
        )
        
        with patch.object(
            scheduler, "_execute_goal", new_callable=AsyncMock
        ) as mock_execute, patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_execute.side_effect = TransientError("Always fails")
            
            # Should not raise exception even if DLQ fails
            result = await scheduler.run_goal_with_retry(
                goal_instance_id="goal-456",
                hired_instance_id="hired-789",
                scheduled_time=datetime(2026, 2, 15, 10, 0, 0, tzinfo=timezone.utc),
            )
            
            assert result.status.value == "failed"
            assert "Max retries exhausted" in result.error_message
