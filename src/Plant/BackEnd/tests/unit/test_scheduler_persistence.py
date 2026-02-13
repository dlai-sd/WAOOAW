"""Tests for scheduler persistence and recovery."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch

from models.scheduled_goal_run import (
    ScheduledGoalRunModel,
    ScheduledGoalRunRepository,
)
from models.goal_run import GoalRunModel
from services.scheduler_persistence_service import (
    SchedulerPersistenceService,
    RecoveryResult,
)


# ============================================================================
# Test ScheduledGoalRunModel
# ============================================================================


class TestScheduledGoalRunModel:
    """Test ScheduledGoalRunModel."""
    
    def test_create_scheduled_run(self):
        """Test creating a scheduled run."""
        scheduled_time = datetime(2026, 2, 15, 10, 0, 0, tzinfo=timezone.utc)
        
        scheduled_run = ScheduledGoalRunModel.create_scheduled_run(
            scheduled_run_id="sched_goal1_1739606400",
            goal_instance_id="goal1",
            scheduled_time=scheduled_time,
            hired_instance_id="hired1",
            metadata={"source": "scheduler"},
        )
        
        assert scheduled_run.scheduled_run_id == "sched_goal1_1739606400"
        assert scheduled_run.goal_instance_id == "goal1"
        assert scheduled_run.hired_instance_id == "hired1"
        assert scheduled_run.scheduled_time == scheduled_time
        assert scheduled_run.status == "pending"
        assert scheduled_run.run_metadata == {"source": "scheduler"}
        assert scheduled_run.created_at is not None
        assert scheduled_run.completed_at is None
    
    def test_mark_completed(self):
        """Test marking scheduled run as completed."""
        scheduled_run = ScheduledGoalRunModel.create_scheduled_run(
            scheduled_run_id="sched_goal1_1739606400",
            goal_instance_id="goal1",
            scheduled_time=datetime.now(timezone.utc),
        )
        
        scheduled_run.mark_completed()
        
        assert scheduled_run.status == "completed"
        assert scheduled_run.completed_at is not None
    
    def test_mark_cancelled(self):
        """Test marking scheduled run as cancelled."""
        scheduled_run = ScheduledGoalRunModel.create_scheduled_run(
            scheduled_run_id="sched_goal1_1739606400",
            goal_instance_id="goal1",
            scheduled_time=datetime.now(timezone.utc),
        )
        
        scheduled_run.mark_cancelled()
        
        assert scheduled_run.status == "cancelled"
        assert scheduled_run.completed_at is not None
    
    def test_is_pending(self):
        """Test checking if run is pending."""
        scheduled_run = ScheduledGoalRunModel.create_scheduled_run(
            scheduled_run_id="sched_goal1_1739606400",
            goal_instance_id="goal1",
            scheduled_time=datetime.now(timezone.utc),
        )
        
        assert scheduled_run.is_pending() is True
        
        scheduled_run.mark_completed()
        assert scheduled_run.is_pending() is False
    
    def test_is_missed_future_run(self):
        """Test is_missed with future scheduled time."""
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        current_time = datetime.now(timezone.utc)
        
        scheduled_run = ScheduledGoalRunModel.create_scheduled_run(
            scheduled_run_id="sched_goal1_1739606400",
            goal_instance_id="goal1",
            scheduled_time=future_time,
        )
        
        assert scheduled_run.is_missed(current_time) is False
    
    def test_is_missed_past_run(self):
        """Test is_missed with past scheduled time."""
        past_time = datetime.now(timezone.utc) - timedelta(hours=2)
        current_time = datetime.now(timezone.utc)
        
        scheduled_run = ScheduledGoalRunModel.create_scheduled_run(
            scheduled_run_id="sched_goal1_1739606400",
            goal_instance_id="goal1",
            scheduled_time=past_time,
        )
        
        assert scheduled_run.is_missed(current_time) is True
    
    def test_is_missed_completed_run(self):
        """Test is_missed with completed run."""
        past_time = datetime.now(timezone.utc) - timedelta(hours=2)
        current_time = datetime.now(timezone.utc)
        
        scheduled_run = ScheduledGoalRunModel.create_scheduled_run(
            scheduled_run_id="sched_goal1_1739606400",
            goal_instance_id="goal1",
            scheduled_time=past_time,
        )
        scheduled_run.mark_completed()
        
        assert scheduled_run.is_missed(current_time) is False
    
    def test_is_very_old_missed_recent(self):
        """Test is_very_old_missed with recent missed run."""
        past_time = datetime.now(timezone.utc) - timedelta(hours=2)
        current_time = datetime.now(timezone.utc)
        
        scheduled_run = ScheduledGoalRunModel.create_scheduled_run(
            scheduled_run_id="sched_goal1_1739606400",
            goal_instance_id="goal1",
            scheduled_time=past_time,
        )
        
        assert scheduled_run.is_very_old_missed(threshold_hours=24, current_time=current_time) is False
    
    def test_is_very_old_missed_old(self):
        """Test is_very_old_missed with very old missed run."""
        past_time = datetime.now(timezone.utc) - timedelta(hours=48)
        current_time = datetime.now(timezone.utc)
        
        scheduled_run = ScheduledGoalRunModel.create_scheduled_run(
            scheduled_run_id="sched_goal1_1739606400",
            goal_instance_id="goal1",
            scheduled_time=past_time,
        )
        
        assert scheduled_run.is_very_old_missed(threshold_hours=24, current_time=current_time) is True
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        scheduled_time = datetime(2026, 2, 15, 10, 0, 0, tzinfo=timezone.utc)
        
        scheduled_run = ScheduledGoalRunModel.create_scheduled_run(
            scheduled_run_id="sched_goal1_1739606400",
            goal_instance_id="goal1",
            scheduled_time=scheduled_time,
            hired_instance_id="hired1",
            metadata={"source": "scheduler"},
        )
        
        result = scheduled_run.to_dict()
        
        assert result["scheduled_run_id"] == "sched_goal1_1739606400"
        assert result["goal_instance_id"] == "goal1"
        assert result["hired_instance_id"] == "hired1"
        assert result["scheduled_time"] == scheduled_time.isoformat()
        assert result["status"] == "pending"
        assert result["completed_at"] is None
        assert result["run_metadata"] == {"source": "scheduler"}


# ============================================================================
# Test ScheduledGoalRunRepository
# ============================================================================


class TestScheduledGoalRunRepository:
    """Test ScheduledGoalRunRepository."""
    
    def test_add_scheduled_run(self):
        """Test adding scheduled run."""
        db = Mock()
        repo = ScheduledGoalRunRepository(db)
        
        scheduled_run = ScheduledGoalRunModel.create_scheduled_run(
            scheduled_run_id="sched_goal1_1739606400",
            goal_instance_id="goal1",
            scheduled_time=datetime.now(timezone.utc),
        )
        
        result = repo.add(scheduled_run)
        
        db.add.assert_called_once_with(scheduled_run)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(scheduled_run)
        assert result == scheduled_run
    
    def test_get_by_id_found(self):
        """Test getting scheduled run by ID when found."""
        db = Mock()
        repo = ScheduledGoalRunRepository(db)
        
        scheduled_run = ScheduledGoalRunModel.create_scheduled_run(
            scheduled_run_id="sched_goal1_1739606400",
            goal_instance_id="goal1",
            scheduled_time=datetime.now(timezone.utc),
        )
        
        db.query.return_value.filter.return_value.first.return_value = scheduled_run
        
        result = repo.get_by_id("sched_goal1_1739606400")
        
        assert result == scheduled_run
    
    def test_get_by_id_not_found(self):
        """Test getting scheduled run by ID when not found."""
        db = Mock()
        repo = ScheduledGoalRunRepository(db)
        
        db.query.return_value.filter.return_value.first.return_value = None
        
        result = repo.get_by_id("nonexistent")
        
        assert result is None
    
    def test_update_scheduled_run(self):
        """Test updating scheduled run."""
        db = Mock()
        repo = ScheduledGoalRunRepository(db)
        
        scheduled_run = ScheduledGoalRunModel.create_scheduled_run(
            scheduled_run_id="sched_goal1_1739606400",
            goal_instance_id="goal1",
            scheduled_time=datetime.now(timezone.utc),
        )
        
        result = repo.update(scheduled_run)
        
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(scheduled_run)
        assert result == scheduled_run
    
    def test_get_pending_runs(self):
        """Test getting pending scheduled runs."""
        db = Mock()
        repo = ScheduledGoalRunRepository(db)
        
        pending_runs = [
            ScheduledGoalRunModel.create_scheduled_run(
                scheduled_run_id=f"sched_goal{i}_1739606400",
                goal_instance_id=f"goal{i}",
                scheduled_time=datetime.now(timezone.utc),
            )
            for i in range(3)
        ]
        
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = pending_runs
        
        result = repo.get_pending_runs()
        
        assert len(result) == 3
        assert result == pending_runs
    
    def test_get_missed_runs(self):
        """Test getting missed scheduled runs."""
        db = Mock()
        repo = ScheduledGoalRunRepository(db)
        
        current_time = datetime.now(timezone.utc)
        missed_runs = [
            ScheduledGoalRunModel.create_scheduled_run(
                scheduled_run_id=f"sched_goal{i}_1739606400",
                goal_instance_id=f"goal{i}",
                scheduled_time=current_time - timedelta(hours=i+1),
            )
            for i in range(3)
        ]
        
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = missed_runs
        
        result = repo.get_missed_runs(current_time)
        
        assert len(result) == 3
        assert result == missed_runs
    
    def test_get_upcoming_runs(self):
        """Test getting upcoming scheduled runs."""
        db = Mock()
        repo = ScheduledGoalRunRepository(db)
        
        current_time = datetime.now(timezone.utc)
        upcoming_runs = [
            ScheduledGoalRunModel.create_scheduled_run(
                scheduled_run_id=f"sched_goal{i}_1739606400",
                goal_instance_id=f"goal{i}",
                scheduled_time=current_time + timedelta(hours=i+1),
            )
            for i in range(3)
        ]
        
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = upcoming_runs
        
        result = repo.get_upcoming_runs(limit=100, current_time=current_time)
        
        assert len(result) == 3
        assert result == upcoming_runs
    
    def test_delete_old_completed(self):
        """Test deleting old completed runs."""
        db = Mock()
        repo = ScheduledGoalRunRepository(db)
        
        db.query.return_value.filter.return_value.delete.return_value = 5
        
        result = repo.delete_old_completed(days_old=30)
        
        assert result == 5
        db.commit.assert_called_once()


# ============================================================================
# Test RecoveryResult
# ============================================================================


class TestRecoveryResult:
    """Test RecoveryResult."""
    
    def test_recovery_result_initialization(self):
        """Test RecoveryResult initialization."""
        result = RecoveryResult()
        
        assert result.interrupted_runs_count == 0
        assert result.missed_runs_count == 0
        assert result.replayed_runs_count == 0
        assert result.skipped_runs_count == 0
        assert result.recovery_errors == []
    
    def test_recovery_result_to_dict(self):
        """Test RecoveryResult to_dict."""
        result = RecoveryResult()
        result.interrupted_runs_count = 2
        result.missed_runs_count = 5
        result.replayed_runs_count = 3
        result.skipped_runs_count = 2
        result.recovery_errors = [{"error": "test"}]
        
        result_dict = result.to_dict()
        
        assert result_dict["interrupted_runs_count"] == 2
        assert result_dict["missed_runs_count"] == 5
        assert result_dict["replayed_runs_count"] == 3
        assert result_dict["skipped_runs_count"] == 2
        assert len(result_dict["recovery_errors"]) == 1


# ============================================================================
# Test SchedulerPersistenceService
# ============================================================================


class TestSchedulerPersistenceService:
    """Test SchedulerPersistenceService."""
    
    @pytest.mark.asyncio
    async def test_recover_state_no_interrupted_or_missed(self):
        """Test recovery with no interrupted or missed runs."""
        db = Mock()
        scheduler_service = Mock()
        service = SchedulerPersistenceService(db, scheduler_service)
        
        # Mock no interrupted runs
        service.goal_run_repo.get_runs_by_status = Mock(return_value=[])
        
        # Mock no missed runs
        service.scheduled_run_repo.get_missed_runs = Mock(return_value=[])
        
        result = await service.recover_state()
        
        assert result.interrupted_runs_count == 0
        assert result.missed_runs_count == 0
        assert result.replayed_runs_count == 0
        assert result.skipped_runs_count == 0
        assert len(result.recovery_errors) == 0
    
    @pytest.mark.asyncio
    async def test_recover_state_marks_interrupted_as_failed(self):
        """Test recovery marks interrupted runs as failed."""
        db = Mock()
        scheduler_service = Mock()
        service = SchedulerPersistenceService(db, scheduler_service)
        
        # Mock interrupted runs with all required methods
        interrupted_run1 = Mock(spec=GoalRunModel)
        interrupted_run1.run_id = "run1"
        interrupted_run1.goal_instance_id = "goal1"
        interrupted_run1.idempotency_key = "goal1:2026-02-15T10:00:00Z"
        interrupted_run1.mark_as_failed = Mock()
        
        interrupted_run2 = Mock(spec=GoalRunModel)
        interrupted_run2.run_id = "run2"
        interrupted_run2.goal_instance_id = "goal2"
        interrupted_run2.idempotency_key = "goal2:2026-02-15T11:00:00Z"
        interrupted_run2.mark_as_failed = Mock()
        
        service.goal_run_repo.get_runs_by_status = Mock(return_value=[interrupted_run1, interrupted_run2])
        service.goal_run_repo.update = Mock()
        
        # Mock no missed runs
        service.scheduled_run_repo.get_missed_runs = Mock(return_value=[])
        
        result = await service.recover_state()
        
        assert result.interrupted_runs_count == 2
        interrupted_run1.mark_as_failed.assert_called_once()
        interrupted_run2.mark_as_failed.assert_called_once()
        assert service.goal_run_repo.update.call_count == 2
    
    @pytest.mark.asyncio
    async def test_recover_state_replays_recent_missed_runs(self):
        """Test recovery replays recent missed runs."""
        db = Mock()
        scheduler_service = Mock()
        scheduler_service.run_goal_with_retry = AsyncMock()
        service = SchedulerPersistenceService(db, scheduler_service, replay_threshold_hours=24)
        
        # Mock no interrupted runs
        service.goal_run_repo.get_runs_by_status = Mock(return_value=[])
        
        # Mock recent missed runs (2 hours ago)
        current_time = datetime.now(timezone.utc)
        missed_time = current_time - timedelta(hours=2)
        
        missed_run = ScheduledGoalRunModel.create_scheduled_run(
            scheduled_run_id="sched_goal1_1739606400",
            goal_instance_id="goal1",
            scheduled_time=missed_time,
            hired_instance_id="hired1",
        )
        
        service.scheduled_run_repo.get_missed_runs = Mock(return_value=[missed_run])
        service.scheduled_run_repo.update = Mock()
        
        result = await service.recover_state()
        
        assert result.missed_runs_count == 1
        assert result.replayed_runs_count == 1
        assert result.skipped_runs_count == 0
        scheduler_service.run_goal_with_retry.assert_called_once_with(
            goal_instance_id="goal1",
            hired_instance_id="hired1",
            scheduled_time=missed_time,
        )
        assert missed_run.status == "completed"
    
    @pytest.mark.asyncio
    async def test_recover_state_skips_old_missed_runs(self):
        """Test recovery skips very old missed runs."""
        db = Mock()
        scheduler_service = Mock()
        service = SchedulerPersistenceService(db, scheduler_service, replay_threshold_hours=24)
        
        # Mock no interrupted runs
        service.goal_run_repo.get_runs_by_status = Mock(return_value=[])
        
        # Mock old missed runs (48 hours ago)
        current_time = datetime.now(timezone.utc)
        missed_time = current_time - timedelta(hours=48)
        
        missed_run = ScheduledGoalRunModel.create_scheduled_run(
            scheduled_run_id="sched_goal1_1739606400",
            goal_instance_id="goal1",
            scheduled_time=missed_time,
        )
        
        service.scheduled_run_repo.get_missed_runs = Mock(return_value=[missed_run])
        service.scheduled_run_repo.update = Mock()
        
        result = await service.recover_state()
        
        assert result.missed_runs_count == 1
        assert result.replayed_runs_count == 0
        assert result.skipped_runs_count == 1
        assert missed_run.status == "cancelled"
    
    @pytest.mark.asyncio
    async def test_recover_state_mixed_missed_runs(self):
        """Test recovery with mix of recent and old missed runs."""
        db = Mock()
        scheduler_service = Mock()
        scheduler_service.run_goal_with_retry = AsyncMock()
        service = SchedulerPersistenceService(db, scheduler_service, replay_threshold_hours=24)
        
        # Mock no interrupted runs
        service.goal_run_repo.get_runs_by_status = Mock(return_value=[])
        
        # Mock mixed missed runs
        current_time = datetime.now(timezone.utc)
        
        recent_run = ScheduledGoalRunModel.create_scheduled_run(
            scheduled_run_id="sched_goal1_1739606400",
            goal_instance_id="goal1",
            scheduled_time=current_time - timedelta(hours=2),
            hired_instance_id="hired1",
        )
        
        old_run = ScheduledGoalRunModel.create_scheduled_run(
            scheduled_run_id="sched_goal2_1739606400",
            goal_instance_id="goal2",
            scheduled_time=current_time - timedelta(hours=48),
        )
        
        service.scheduled_run_repo.get_missed_runs = Mock(return_value=[recent_run, old_run])
        service.scheduled_run_repo.update = Mock()
        
        result = await service.recover_state()
        
        assert result.missed_runs_count == 2
        assert result.replayed_runs_count == 1
        assert result.skipped_runs_count == 1
        assert recent_run.status == "completed"
        assert old_run.status == "cancelled"
    
    @pytest.mark.asyncio
    async def test_recover_state_handles_replay_error(self):
        """Test recovery handles replay errors."""
        db = Mock()
        scheduler_service = Mock()
        scheduler_service.run_goal_with_retry = AsyncMock(side_effect=Exception("Replay failed"))
        service = SchedulerPersistenceService(db, scheduler_service, replay_threshold_hours=24)
        
        # Mock no interrupted runs
        service.goal_run_repo.get_runs_by_status = Mock(return_value=[])
        
        # Mock recent missed run
        current_time = datetime.now(timezone.utc)
        missed_run = ScheduledGoalRunModel.create_scheduled_run(
            scheduled_run_id="sched_goal1_1739606400",
            goal_instance_id="goal1",
            scheduled_time=current_time - timedelta(hours=2),
        )
        
        service.scheduled_run_repo.get_missed_runs = Mock(return_value=[missed_run])
        service.scheduled_run_repo.update = Mock()
        
        result = await service.recover_state()
        
        assert result.missed_runs_count == 1
        assert result.replayed_runs_count == 0  # Failed to replay
        assert len(result.recovery_errors) == 1
        assert result.recovery_errors[0]["scheduled_run_id"] == "sched_goal1_1739606400"
        assert "Replay failed" in result.recovery_errors[0]["error"]
    
    @pytest.mark.asyncio
    async def test_save_state(self):
        """Test saving scheduled run state."""
        db = Mock()
        service = SchedulerPersistenceService(db)
        
        scheduled_time = datetime(2026, 2, 15, 10, 0, 0, tzinfo=timezone.utc)
        
        service.scheduled_run_repo.add = Mock(return_value=Mock(spec=ScheduledGoalRunModel))
        
        result = await service.save_state(
            goal_instance_id="goal1",
            scheduled_time=scheduled_time,
            hired_instance_id="hired1",
            metadata={"source": "scheduler"},
        )
        
        service.scheduled_run_repo.add.assert_called_once()
        assert result is not None
    
    def test_get_pending_runs(self):
        """Test getting pending runs."""
        db = Mock()
        service = SchedulerPersistenceService(db)
        
        pending_runs = [Mock(spec=ScheduledGoalRunModel) for _ in range(3)]
        service.scheduled_run_repo.get_pending_runs = Mock(return_value=pending_runs)
        
        result = service.get_pending_runs()
        
        assert len(result) == 3
        assert result == pending_runs
    
    def test_get_upcoming_runs(self):
        """Test getting upcoming runs."""
        db = Mock()
        service = SchedulerPersistenceService(db)
        
        upcoming_runs = [Mock(spec=ScheduledGoalRunModel) for _ in range(5)]
        service.scheduled_run_repo.get_upcoming_runs = Mock(return_value=upcoming_runs)
        
        result = service.get_upcoming_runs(limit=100)
        
        assert len(result) == 5
        assert result == upcoming_runs
    
    def test_cleanup_old_completed_runs(self):
        """Test cleanup of old completed runs."""
        db = Mock()
        service = SchedulerPersistenceService(db)
        
        service.scheduled_run_repo.delete_old_completed = Mock(return_value=10)
        
        result = service.cleanup_old_completed_runs(days_old=30)
        
        assert result == 10
        service.scheduled_run_repo.delete_old_completed.assert_called_once_with(
            days_old=30,
            current_time=None,
        )
