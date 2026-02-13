"""Unit tests for goal run idempotency functionality.

Tests:
- GoalRunModel status transitions and state machine
- GoalRunRepository database operations and locking
- IdempotencyService key generation and duplicate detection
- Integration with GoalSchedulerService for idempotent execution
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.orm import Session

from models.goal_run import GoalRunModel, GoalRunRepository
from services.idempotency_service import IdempotencyService
from services.goal_scheduler_service import (
    GoalSchedulerService,
    GoalRunStatus,
    TransientError,
    PermanentError,
)


# ----- Test GoalRunModel -----


class TestGoalRunModel:
    """Test GoalRunModel status transitions."""
    
    def test_create_pending_run(self):
        """Test creating a pending run."""
        run = GoalRunModel.create_pending(
            run_id="run-123",
            goal_instance_id="goal-456",
            idempotency_key="goal-456:2026-02-12T10:30:00+00:00",
        )
        
        assert run.run_id == "run-123"
        assert run.goal_instance_id == "goal-456"
        assert run.idempotency_key == "goal-456:2026-02-12T10:30:00+00:00"
        assert run.status == "pending"
        assert run.started_at is not None
        assert run.completed_at is None
        assert run.deliverable_id is None
        assert run.error_details is None
        assert run.duration_ms is None
    
    def test_mark_running(self):
        """Test marking run as running."""
        run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        
        run.mark_running()
        
        assert run.status == "running"
        assert run.started_at is not None
    
    def test_mark_completed(self):
        """Test marking run as completed."""
        run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        run.mark_running()
        
        run.mark_completed(deliverable_id="deliv-789", duration_ms=5000)
        
        assert run.status == "completed"
        assert run.deliverable_id == "deliv-789"
        assert run.duration_ms == 5000
        assert run.completed_at is not None
    
    def test_mark_failed(self):
        """Test marking run as failed."""
        run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        run.mark_running()
        
        error_details = {
            "message": "Network timeout",
            "type": "TRANSIENT",
            "stack_trace": "Traceback...",
        }
        run.mark_failed(error_details, duration_ms=3000)
        
        assert run.status == "failed"
        assert run.error_details == error_details
        assert run.duration_ms == 3000
        assert run.completed_at is not None
    
    def test_is_terminal_state_completed(self):
        """Test terminal state detection for completed run."""
        run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        run.mark_running()
        run.mark_completed("deliv-789", 5000)
        
        assert run.is_terminal_state() is True
    
    def test_is_terminal_state_failed(self):
        """Test terminal state detection for failed run."""
        run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        run.mark_running()
        run.mark_failed({"message": "Error"}, 3000)
        
        assert run.is_terminal_state() is True
    
    def test_is_not_terminal_state_pending(self):
        """Test non-terminal state detection for pending run."""
        run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        
        assert run.is_terminal_state() is False
    
    def test_is_not_terminal_state_running(self):
        """Test non-terminal state detection for running run."""
        run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        run.mark_running()
        
        assert run.is_terminal_state() is False
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        run.mark_running()
        run.mark_completed("deliv-789", 5000)
        
        data = run.to_dict()
        
        assert data["run_id"] == "run-123"
        assert data["goal_instance_id"] == "goal-456"
        assert data["idempotency_key"] == "key-123"
        assert data["status"] == "completed"
        assert data["deliverable_id"] == "deliv-789"
        assert data["duration_ms"] == 5000
        assert "started_at" in data
        assert "completed_at" in data


# ----- Test GoalRunRepository -----


class TestGoalRunRepository:
    """Test GoalRunRepository database operations."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def repository(self, mock_db):
        """Create repository with mock database."""
        return GoalRunRepository(mock_db)
    
    def test_get_by_idempotency_key_found(self, repository, mock_db):
        """Test getting run by idempotency key when it exists."""
        mock_run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_run
        
        result = repository.get_by_idempotency_key("key-123")
        
        assert result == mock_run
        mock_db.query.assert_called_once_with(GoalRunModel)
    
    def test_get_by_idempotency_key_not_found(self, repository, mock_db):
        """Test getting run by idempotency key when it doesn't exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = repository.get_by_idempotency_key("key-nonexistent")
        
        assert result is None
    
    def test_get_by_run_id_found(self, repository, mock_db):
        """Test getting run by run ID when it exists."""
        mock_run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_run
        
        result = repository.get_by_run_id("run-123")
        
        assert result == mock_run
    
    def test_create_with_lock_new_run(self, repository, mock_db):
        """Test creating new run with lock when no existing run."""
        new_run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        
        # Mock SELECT FOR UPDATE returning no existing run
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None
        
        result = repository.create_with_lock(new_run)
        
        assert result == new_run
        mock_db.add.assert_called_once_with(new_run)
        mock_db.commit.assert_called_once()
    
    def test_create_with_lock_existing_run(self, repository, mock_db):
        """Test creating run with lock when run already exists (race condition)."""
        new_run = GoalRunModel.create_pending("run-new", "goal-456", "key-123")
        existing_run = GoalRunModel.create_pending("run-existing", "goal-456", "key-123")
        
        # Mock SELECT FOR UPDATE returning existing run
        mock_db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = existing_run
        
        result = repository.create_with_lock(new_run)
        
        assert result == existing_run
        assert result.run_id == "run-existing"
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
    
    def test_update_run(self, repository, mock_db):
        """Test updating run status."""
        run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        run.mark_running()
        run.mark_completed("deliv-789", 5000)
        
        result = repository.update(run)
        
        assert result == run
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(run)
    
    def test_list_by_goal_instance(self, repository, mock_db):
        """Test listing runs for a goal instance."""
        mock_runs = [
            GoalRunModel.create_pending("run-1", "goal-456", "key-1"),
            GoalRunModel.create_pending("run-2", "goal-456", "key-2"),
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_runs
        
        result = repository.list_by_goal_instance("goal-456", limit=10)
        
        assert result == mock_runs
    
    def test_list_by_status(self, repository, mock_db):
        """Test listing runs by status."""
        mock_runs = [
            GoalRunModel.create_pending("run-1", "goal-1", "key-1"),
            GoalRunModel.create_pending("run-2", "goal-2", "key-2"),
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_runs
        
        result = repository.list_by_status("pending", limit=10)
        
        assert result == mock_runs


# ----- Test IdempotencyService -----


class TestIdempotencyService:
    """Test IdempotencyService key generation and duplicate detection."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def service(self, mock_db):
        """Create idempotency service with mock database."""
        return IdempotencyService(mock_db)
    
    def test_generate_idempotency_key(self, service):
        """Test idempotency key generation."""
        scheduled_time = datetime(2026, 2, 12, 10, 30, 0, tzinfo=timezone.utc)
        
        key = service.generate_idempotency_key("goal-456", scheduled_time)
        
        assert key == "goal-456:2026-02-12T10:30:00+00:00"
    
    def test_generate_idempotency_key_naive_datetime(self, service):
        """Test idempotency key generation with naive datetime."""
        scheduled_time = datetime(2026, 2, 12, 10, 30, 0)  # No timezone
        
        key = service.generate_idempotency_key("goal-456", scheduled_time)
        
        assert key == "goal-456:2026-02-12T10:30:00+00:00"
    
    @pytest.mark.asyncio
    async def test_get_or_create_run_new_run(self, service):
        """Test getting or creating run when no existing run."""
        service.repository = Mock()
        service.repository.get_by_idempotency_key.return_value = None
        
        # Create callable that returns a new run
        def create_run_side_effect(run):
            # Return the run passed in (simulating successful creation)
            return run
        
        service.repository.create_with_lock.side_effect = create_run_side_effect
        
        run, is_new = await service.get_or_create_run("goal-456", "key-123")
        
        # Verify a new run was created
        assert run.goal_instance_id == "goal-456"
        assert run.idempotency_key == "key-123"
        assert run.status == "pending"
        assert is_new is True
        service.repository.create_with_lock.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_or_create_run_existing_run(self, service):
        """Test getting or creating run when run already exists."""
        service.repository = Mock()
        existing_run = GoalRunModel.create_pending("run-existing", "goal-456", "key-123")
        service.repository.get_by_idempotency_key.return_value = existing_run
        
        run, is_new = await service.get_or_create_run("goal-456", "key-123")
        
        assert run == existing_run
        assert is_new is False
        service.repository.create_with_lock.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_mark_run_running(self, service):
        """Test marking run as running."""
        service.repository = Mock()
        run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        service.repository.get_by_run_id.return_value = run
        service.repository.update.return_value = run
        
        result = await service.mark_run_running("run-123")
        
        assert result.status == "running"
        service.repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mark_run_running_not_found(self, service):
        """Test marking non-existent run as running raises error."""
        service.repository = Mock()
        service.repository.get_by_run_id.return_value = None
        
        with pytest.raises(ValueError, match="Run not found"):
            await service.mark_run_running("run-nonexistent")
    
    @pytest.mark.asyncio
    async def test_mark_run_running_already_completed(self, service):
        """Test marking completed run as running raises error."""
        service.repository = Mock()
        run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        run.mark_running()
        run.mark_completed("deliv-789", 5000)
        service.repository.get_by_run_id.return_value = run
        
        with pytest.raises(ValueError, match="Cannot mark completed/failed run as running"):
            await service.mark_run_running("run-123")
    
    @pytest.mark.asyncio
    async def test_mark_run_completed(self, service):
        """Test marking run as completed."""
        service.repository = Mock()
        run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        run.mark_running()
        service.repository.get_by_run_id.return_value = run
        service.repository.update.return_value = run
        
        result = await service.mark_run_completed("run-123", "deliv-789", 5000)
        
        assert result.status == "completed"
        assert result.deliverable_id == "deliv-789"
        assert result.duration_ms == 5000
        service.repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mark_run_failed(self, service):
        """Test marking run as failed."""
        service.repository = Mock()
        run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        run.mark_running()
        service.repository.get_by_run_id.return_value = run
        service.repository.update.return_value = run
        
        result = await service.mark_run_failed(
            "run-123",
            "Network timeout",
            "TRANSIENT",
            3000,
            "Traceback...",
        )
        
        assert result.status == "failed"
        assert result.error_details["message"] == "Network timeout"
        assert result.error_details["type"] == "TRANSIENT"
        assert result.duration_ms == 3000
        service.repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_run_status_found(self, service):
        """Test getting run status when run exists."""
        service.repository = Mock()
        run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        run.mark_running()
        run.mark_completed("deliv-789", 5000)
        service.repository.get_by_idempotency_key.return_value = run
        
        status = await service.get_run_status("key-123")
        
        assert status is not None
        assert status["run_id"] == "run-123"
        assert status["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_get_run_status_not_found(self, service):
        """Test getting run status when run doesn't exist."""
        service.repository = Mock()
        service.repository.get_by_idempotency_key.return_value = None
        
        status = await service.get_run_status("key-nonexistent")
        
        assert status is None
    
    @pytest.mark.asyncio
    async def test_should_execute_run_pending(self, service):
        """Test should execute pending run."""
        run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        
        result = await service.should_execute_run(run)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_should_not_execute_run_running(self, service):
        """Test should not execute already running run."""
        run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        run.mark_running()
        
        result = await service.should_execute_run(run)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_should_not_execute_run_completed(self, service):
        """Test should not execute already completed run."""
        run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        run.mark_running()
        run.mark_completed("deliv-789", 5000)
        
        result = await service.should_execute_run(run)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_should_not_execute_run_failed(self, service):
        """Test should not execute already failed run."""
        run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        run.mark_running()
        run.mark_failed({"message": "Error"}, 3000)
        
        result = await service.should_execute_run(run)
        
        assert result is False


# ----- Test Idempotency Integration -----


class TestIdempotencyIntegration:
    """Test idempotency integration with GoalSchedulerService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def idempotency_service(self, mock_db):
        """Create idempotency service with mock database."""
        return IdempotencyService(mock_db)
    
    @pytest.fixture
    def scheduler_service(self, idempotency_service):
        """Create scheduler service with idempotency."""
        return GoalSchedulerService(
            max_retries=3,
            initial_backoff_seconds=1,
            backoff_multiplier=2.0,
            idempotency_service=idempotency_service,
        )
    
    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_first_execution_creates_run(
        self,
        mock_sleep,
        scheduler_service,
        idempotency_service,
    ):
        """Test first execution creates new run."""
        scheduled_time = datetime(2026, 2, 12, 10, 30, 0, tzinfo=timezone.utc)
        
        # Mock repository to return None (no existing run)
        idempotency_service.repository = Mock()
        idempotency_service.repository.get_by_idempotency_key.return_value = None
        
        new_run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        idempotency_service.repository.create_with_lock.return_value = new_run
        idempotency_service.repository.get_by_run_id.return_value = new_run
        idempotency_service.repository.update.return_value = new_run
        
        # Mock successful execution
        scheduler_service._execute_goal = AsyncMock(return_value="deliv-789")
        
        result = await scheduler_service.run_goal_with_retry(
            goal_instance_id="goal-456",
            scheduled_time=scheduled_time,
        )
        
        assert result.status == GoalRunStatus.COMPLETED
        assert result.deliverable_id == "deliv-789"
        
        # Verify run was created and marked running then completed
        idempotency_service.repository.create_with_lock.assert_called_once()
        assert idempotency_service.repository.update.call_count == 2  # running, completed
    
    @pytest.mark.asyncio
    async def test_duplicate_execution_returns_cached_result(
        self,
        scheduler_service,
        idempotency_service,
    ):
        """Test duplicate execution returns cached completed result."""
        scheduled_time = datetime(2026, 2, 12, 10, 30, 0, tzinfo=timezone.utc)
        
        # Mock repository to return existing completed run
        completed_run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        completed_run.mark_running()
        completed_run.mark_completed("deliv-789", 5000)
        
        idempotency_service.repository = Mock()
        idempotency_service.repository.get_by_idempotency_key.return_value = completed_run
        
        # Mock execution should NOT be called
        scheduler_service._execute_goal = AsyncMock()
        
        result = await scheduler_service.run_goal_with_retry(
            goal_instance_id="goal-456",
            scheduled_time=scheduled_time,
        )
        
        assert result.status == GoalRunStatus.COMPLETED
        assert result.deliverable_id == "deliv-789"
        assert result.total_duration_ms == 5000
        
        # Verify execution was NOT called (idempotent)
        scheduler_service._execute_goal.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_concurrent_execution_detected(
        self,
        scheduler_service,
        idempotency_service,
    ):
        """Test concurrent execution returns RUNNING status."""
        scheduled_time = datetime(2026, 2, 12, 10, 30, 0, tzinfo=timezone.utc)
        
        # Mock repository to return existing running run
        running_run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        running_run.mark_running()
        
        idempotency_service.repository = Mock()
        idempotency_service.repository.get_by_idempotency_key.return_value = running_run
        
        # Mock execution should NOT be called
        scheduler_service._execute_goal = AsyncMock()
        
        result = await scheduler_service.run_goal_with_retry(
            goal_instance_id="goal-456",
            scheduled_time=scheduled_time,
        )
        
        assert result.status == GoalRunStatus.RUNNING
        
        # Verify execution was NOT called (concurrent run detected)
        scheduler_service._execute_goal.assert_not_called()
    
    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_failed_execution_marks_run_failed(
        self,
        mock_sleep,
        scheduler_service,
        idempotency_service,
    ):
        """Test failed execution marks run as failed."""
        scheduled_time = datetime(2026, 2, 12, 10, 30, 0, tzinfo=timezone.utc)
        
        # Mock repository to return new run
        idempotency_service.repository = Mock()
        idempotency_service.repository.get_by_idempotency_key.return_value = None
        
        new_run = GoalRunModel.create_pending("run-123", "goal-456", "key-123")
        idempotency_service.repository.create_with_lock.return_value = new_run
        idempotency_service.repository.get_by_run_id.return_value = new_run
        idempotency_service.repository.update.return_value = new_run
        
        # Mock permanent failure
        scheduler_service._execute_goal = AsyncMock(
            side_effect=PermanentError("Invalid configuration")
        )
        
        result = await scheduler_service.run_goal_with_retry(
            goal_instance_id="goal-456",
            scheduled_time=scheduled_time,
        )
        
        assert result.status == GoalRunStatus.FAILED
        assert result.error_message == "Invalid configuration"
        
        # Verify run was marked as failed
        idempotency_service.repository.update.assert_called()
