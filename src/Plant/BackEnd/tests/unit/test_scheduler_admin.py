"""Unit tests for scheduler admin controls.

Tests:
- SchedulerStateModel pause/resume operations
- SchedulerAdminService pause/resume/trigger
- Graceful pause waiting for running goals
- Action audit logging
- API endpoints for admin operations
"""

import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

from sqlalchemy.orm import Session

from models.scheduler_state import (
    SchedulerStateModel,
    SchedulerStateRepository,
    SchedulerActionLogModel,
    SchedulerActionLogRepository,
)
from services.scheduler_admin_service import SchedulerAdminService
from api.v1.scheduler_admin import (
    PauseSchedulerRequest,
    ResumeSchedulerRequest,
    TriggerGoalRequest,
)


# ----- Test SchedulerStateModel -----


class TestSchedulerStateModel:
    """Test SchedulerStateModel operations."""
    
    def test_create_global_state(self):
        """Test creating global scheduler state."""
        state = SchedulerStateModel.get_global_state()
        
        assert state.state_id == "global"
        assert state.status == "running"
        assert state.paused_at is None
        assert state.paused_by is None
        assert state.is_running() is True
        assert state.is_paused() is False
    
    def test_pause_scheduler(self):
        """Test pausing scheduler."""
        state = SchedulerStateModel.get_global_state()
        
        state.pause(operator="admin@example.com", reason="Maintenance")
        
        assert state.status == "paused"
        assert state.paused_by == "admin@example.com"
        assert state.paused_reason == "Maintenance"
        assert state.paused_at is not None
        assert state.is_paused() is True
        assert state.is_running() is False
    
    def test_resume_scheduler(self):
        """Test resuming scheduler."""
        state = SchedulerStateModel.get_global_state()
        state.pause("admin1", "Test")
        
        state.resume(operator="admin2")
        
        assert state.status == "running"
        assert state.resumed_by == "admin2"
        assert state.resumed_at is not None
        assert state.is_running() is True
        assert state.is_paused() is False
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        state = SchedulerStateModel.get_global_state()
        state.pause("admin", "Test")
        
        data = state.to_dict()
        
        assert data["state_id"] == "global"
        assert data["status"] == "paused"
        assert data["paused_by"] == "admin"
        assert data["paused_reason"] == "Test"
        assert "updated_at" in data


class TestSchedulerActionLogModel:
    """Test SchedulerActionLogModel operations."""
    
    def test_create_pause_log(self):
        """Test creating pause action log."""
        log = SchedulerActionLogModel.create_log(
            log_id="log-123",
            action="pause",
            operator="admin@example.com",
            reason="Emergency maintenance",
        )
        
        assert log.log_id == "log-123"
        assert log.action == "pause"
        assert log.operator == "admin@example.com"
        assert log.reason == "Emergency maintenance"
        assert log.timestamp is not None
        assert log.goal_instance_id is None
    
    def test_create_trigger_log(self):
        """Test creating trigger action log."""
        log = SchedulerActionLogModel.create_log(
            log_id="log-456",
            action="trigger",
            operator="ops@example.com",
            goal_instance_id="goal-789",
        )
        
        assert log.action == "trigger"
        assert log.goal_instance_id == "goal-789"
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        log = SchedulerActionLogModel.create_log(
            log_id="log-123",
            action="resume",
            operator="admin",
        )
        
        data = log.to_dict()
        
        assert data["log_id"] == "log-123"
        assert data["action"] == "resume"
        assert data["operator"] == "admin"
        assert "timestamp" in data


# ----- Test SchedulerStateRepository -----


class TestSchedulerStateRepository:
    """Test SchedulerStateRepository database operations."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def repository(self, mock_db):
        """Create repository with mock database."""
        return SchedulerStateRepository(mock_db)
    
    def test_get_state_found(self, repository, mock_db):
        """Test getting state when it exists."""
        mock_state = SchedulerStateModel.get_global_state()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_state
        
        result = repository.get_state("global")
        
        assert result == mock_state
    
    def test_get_state_not_found(self, repository, mock_db):
        """Test getting state when it doesn't exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = repository.get_state("global")
        
        assert result is None
    
    def test_get_or_create_state_existing(self, repository, mock_db):
        """Test get or create when state exists."""
        mock_state = SchedulerStateModel.get_global_state()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_state
        
        result = repository.get_or_create_state()
        
        assert result == mock_state
        mock_db.add.assert_not_called()
    
    def test_get_or_create_state_new(self, repository, mock_db):
        """Test get or create when state doesn't exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = repository.get_or_create_state()
        
        assert result.state_id == "global"
        assert result.status == "running"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_update_state(self, repository, mock_db):
        """Test updating state."""
        state = SchedulerStateModel.get_global_state()
        state.pause("admin", "Test")
        
        result = repository.update_state(state)
        
        assert result == state
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(state)


# ----- Test SchedulerAdminService -----


class TestSchedulerAdminService:
    """Test SchedulerAdminService operations."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def service(self, mock_db):
        """Create admin service with mock database."""
        service = SchedulerAdminService(mock_db)
        # Mock repositories
        service.state_repository = Mock(spec=SchedulerStateRepository)
        service.log_repository = Mock(spec=SchedulerActionLogRepository)
        return service
    
    @pytest.mark.asyncio
    async def test_pause_scheduler(self, service):
        """Test pausing scheduler."""
        # Mock state
        state = SchedulerStateModel.get_global_state()
        service.state_repository.get_or_create_state.return_value = state
        service.state_repository.update_state.return_value = state
        service.log_repository.add_log.return_value = Mock()
        
        result = await service.pause_scheduler(
            operator="admin@example.com",
            reason="Planned maintenance",
            wait_for_completion=False,
        )
        
        assert result["status"] == "paused"
        assert result["message"] == "Scheduler paused by admin@example.com"
        assert result["reason"] == "Planned maintenance"
        assert state.is_paused() is True
        service.state_repository.update_state.assert_called_once()
        service.log_repository.add_log.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_pause_already_paused(self, service):
        """Test pausing already paused scheduler."""
        state = SchedulerStateModel.get_global_state()
        state.pause("admin1", "Previous pause")
        service.state_repository.get_or_create_state.return_value = state
        
        result = await service.pause_scheduler(
            operator="admin2",
            wait_for_completion=False,
        )
        
        assert result["status"] == "already_paused"
        assert "already paused by admin1" in result["message"]
    
    @pytest.mark.asyncio
    async def test_pause_with_wait_for_completion(self, service):
        """Test graceful pause waiting for running goals."""
        state = SchedulerStateModel.get_global_state()
        service.state_repository.get_or_create_state.return_value = state
        service.state_repository.update_state.return_value = state
        service.log_repository.add_log.return_value = Mock()
        
        # Add some running goals
        service.register_running_goal("goal-1")
        service.register_running_goal("goal-2")
        
        # Simulate goals completing after 2 seconds
        async def complete_goals():
            await asyncio.sleep(2)
            service.unregister_running_goal("goal-1")
            service.unregister_running_goal("goal-2")
        
        task = asyncio.create_task(complete_goals())
        
        result = await service.pause_scheduler(
            operator="admin",
            wait_for_completion=True,
            timeout_seconds=10,
        )
        
        await task
        
        assert result["status"] == "paused"
        assert result["running_goals_at_pause"] == 2
        assert result["running_goals_after_wait"] == 0
    
    @pytest.mark.asyncio
    async def test_pause_with_timeout(self, service):
        """Test pause timeout when goals don't complete."""
        state = SchedulerStateModel.get_global_state()
        service.state_repository.get_or_create_state.return_value = state
        service.state_repository.update_state.return_value = state
        service.log_repository.add_log.return_value = Mock()
        
        # Add running goals that won't complete
        service.register_running_goal("goal-slow")
        
        result = await service.pause_scheduler(
            operator="admin",
            wait_for_completion=True,
            timeout_seconds=2,  # Short timeout
        )
        
        assert result["status"] == "paused"
        assert result["running_goals_after_wait"] == 1  # Still running
    
    @pytest.mark.asyncio
    async def test_resume_scheduler(self, service):
        """Test resuming scheduler."""
        state = SchedulerStateModel.get_global_state()
        state.pause("admin1", "Test")
        service.state_repository.get_or_create_state.return_value = state
        service.state_repository.update_state.return_value = state
        service.log_repository.add_log.return_value = Mock()
        
        result = await service.resume_scheduler(operator="admin2")
        
        assert result["status"] == "running"
        assert result["message"] == "Scheduler resumed by admin2"
        assert state.is_running() is True
        service.state_repository.update_state.assert_called_once()
        service.log_repository.add_log.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_resume_already_running(self, service):
        """Test resuming already running scheduler."""
        state = SchedulerStateModel.get_global_state()
        service.state_repository.get_or_create_state.return_value = state
        
        result = await service.resume_scheduler(operator="admin")
        
        assert result["status"] == "already_running"
    
    @pytest.mark.asyncio
    async def test_trigger_goal_run(self, service):
        """Test manually triggering goal run."""
        service.log_repository.add_log.return_value = Mock()
        
        scheduled_time = datetime(2026, 2, 12, 10, 30, 0, tzinfo=timezone.utc)
        result = await service.trigger_goal_run(
            goal_instance_id="goal-123",
            operator="ops@example.com",
            scheduled_time=scheduled_time,
        )
        
        assert result["status"] == "triggered"
        assert result["goal_instance_id"] == "goal-123"
        assert result["operator"] == "ops@example.com"
        service.log_repository.add_log.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_scheduler_status(self, service):
        """Test getting scheduler status."""
        state = SchedulerStateModel.get_global_state()
        state.pause("admin", "Test")
        service.state_repository.get_or_create_state.return_value = state
        
        service.register_running_goal("goal-1")
        service.register_running_goal("goal-2")
        
        status = await service.get_scheduler_status()
        
        assert status["status"] == "paused"
        assert status["is_paused"] is True
        assert status["paused_by"] == "admin"
        assert status["running_goals_count"] == 2
    
    @pytest.mark.asyncio
    async def test_is_scheduler_paused(self, service):
        """Test checking if scheduler is paused."""
        state = SchedulerStateModel.get_global_state()
        service.state_repository.get_or_create_state.return_value = state
        
        # Initially running
        is_paused = await service.is_scheduler_paused()
        assert is_paused is False
        
        # After pause
        state.pause("admin", "Test")
        is_paused = await service.is_scheduler_paused()
        assert is_paused is True
    
    def test_register_unregister_running_goal(self, service):
        """Test tracking running goals."""
        assert len(service._running_goals) == 0
        
        service.register_running_goal("goal-1")
        assert len(service._running_goals) == 1
        assert "goal-1" in service._running_goals
        
        service.register_running_goal("goal-2")
        assert len(service._running_goals) == 2
        
        service.unregister_running_goal("goal-1")
        assert len(service._running_goals) == 1
        assert "goal-1" not in service._running_goals
        
        service.unregister_running_goal("goal-2")
        assert len(service._running_goals) == 0
    
    @pytest.mark.asyncio
    async def test_get_recent_actions(self, service):
        """Test getting recent admin actions."""
        mock_logs = [
            SchedulerActionLogModel.create_log("log-1", "pause", "admin1"),
            SchedulerActionLogModel.create_log("log-2", "resume", "admin2"),
        ]
        service.log_repository.get_recent_logs.return_value = mock_logs
        
        actions = await service.get_recent_actions(limit=10)
        
        assert len(actions) == 2
        assert actions[0]["action"] == "pause"
        assert actions[1]["action"] == "resume"
        service.log_repository.get_recent_logs.assert_called_once_with(10)
    
    @pytest.mark.asyncio
    async def test_get_actions_by_operator(self, service):
        """Test getting actions by specific operator."""
        mock_logs = [
            SchedulerActionLogModel.create_log("log-1", "pause", "admin1"),
            SchedulerActionLogModel.create_log("log-2", "resume", "admin1"),
        ]
        service.log_repository.get_logs_by_operator.return_value = mock_logs
        
        actions = await service.get_actions_by_operator(operator="admin1", limit=10)
        
        assert len(actions) == 2
        assert all(action["operator"] == "admin1" for action in actions)
        service.log_repository.get_logs_by_operator.assert_called_once_with("admin1", 10)


# ----- Test API Endpoints -----


class TestSchedulerAdminAPI:
    """Test scheduler admin API endpoints."""
    
    @pytest.fixture
    def mock_admin_service(self):
        """Create mock admin service."""
        service = Mock(spec=SchedulerAdminService)
        # Make async methods return coroutines
        service.pause_scheduler = AsyncMock()
        service.resume_scheduler = AsyncMock()
        service.trigger_goal_run = AsyncMock()
        service.get_scheduler_status = AsyncMock()
        service.get_recent_actions = AsyncMock()
        service.get_actions_by_operator = AsyncMock()
        service.register_running_goal = Mock()
        service.unregister_running_goal = Mock()
        return service
    
    @pytest.mark.asyncio
    async def test_pause_endpoint(self, mock_admin_service):
        """Test pause scheduler endpoint."""
        from api.v1.scheduler_admin import pause_scheduler
        
        mock_admin_service.pause_scheduler.return_value = {
            "status": "paused",
            "message": "Scheduler paused by admin",
            "paused_at": "2026-02-12T10:30:00+00:00",
            "reason": "Maintenance",
            "running_goals_at_pause": 0,
            "running_goals_after_wait": 0,
        }
        
        request = PauseSchedulerRequest(
            operator="admin",
            reason="Maintenance",
            wait_for_completion=True,
            timeout_seconds=300,
        )
        
        response = await pause_scheduler(request, mock_admin_service)
        
        assert response.status == "paused"
        assert response.reason == "Maintenance"
        mock_admin_service.pause_scheduler.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_resume_endpoint(self, mock_admin_service):
        """Test resume scheduler endpoint."""
        from api.v1.scheduler_admin import resume_scheduler
        
        mock_admin_service.resume_scheduler.return_value = {
            "status": "running",
            "message": "Scheduler resumed by admin",
            "resumed_at": "2026-02-12T11:00:00+00:00",
        }
        
        request = ResumeSchedulerRequest(operator="admin")
        
        response = await resume_scheduler(request, mock_admin_service)
        
        assert response.status == "running"
        mock_admin_service.resume_scheduler.assert_called_once_with(operator="admin")
    
    @pytest.mark.asyncio
    async def test_get_status_endpoint(self, mock_admin_service):
        """Test get scheduler status endpoint."""
        from api.v1.scheduler_admin import get_scheduler_status
        
        mock_admin_service.get_scheduler_status.return_value = {
            "status": "running",
            "is_paused": False,
            "is_running": True,
            "paused_at": None,
            "paused_by": None,
            "paused_reason": None,
            "resumed_at": None,
            "resumed_by": None,
            "updated_at": "2026-02-12T10:00:00+00:00",
            "running_goals_count": 3,
        }
        
        response = await get_scheduler_status(mock_admin_service)
        
        assert response.status == "running"
        assert response.is_running is True
        assert response.running_goals_count == 3
        mock_admin_service.get_scheduler_status.assert_called_once()
