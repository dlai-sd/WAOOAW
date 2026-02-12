"""Tests for scheduler health monitoring service and API.

Tests cover:
- Health metrics tracking and calculation
- Success/failure rate calculation
- Alert triggering for degraded health
- Prometheus metrics export
- Health status determination
- API endpoint responses
"""

import logging
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.v1.scheduler_health import router, get_health_service
from models.scheduler_dlq import SchedulerDLQRepository
from services.scheduler_dlq_service import DLQService
from services.scheduler_health_service import (
    SchedulerHealthService,
    SchedulerStatus,
    PENDING_GOALS_ALERT_THRESHOLD,
    SUCCESS_RATE_ALERT_THRESHOLD,
)


class TestSchedulerHealthService:
    """Test cases for scheduler health service."""
    
    def test_health_service_initialization(self):
        """Test health service initializes correctly."""
        service = SchedulerHealthService()
        
        assert service._pending_goals == 0
        assert service._running_goals == 0
        assert service._last_run is None
        assert len(service._metrics) == 0
    
    def test_record_successful_execution(self):
        """Test recording a successful goal execution."""
        service = SchedulerHealthService()
        
        service.record_goal_execution(
            goal_instance_id="goal-123",
            success=True,
            duration_ms=1500,
        )
        
        assert len(service._metrics) == 1
        assert service._last_run is not None
        assert service._last_success is not None
        assert service._last_failure is None
    
    def test_record_failed_execution(self):
        """Test recording a failed goal execution."""
        service = SchedulerHealthService()
        
        service.record_goal_execution(
            goal_instance_id="goal-123",
            success=False,
            duration_ms=500,
            error_type="TRANSIENT",
        )
        
        assert len(service._metrics) == 1
        assert service._last_run is not None
        assert service._last_failure is not None
        assert service._last_success is None
    
    def test_metrics_cleanup(self):
        """Test old metrics are cleaned up."""
        service = SchedulerHealthService()
        
        # Add old metric
        old_time = datetime.now(timezone.utc) - timedelta(hours=2)
        service._metrics.append(
            GoalExecutionMetric(
                goal_instance_id="old-goal",
                timestamp=old_time,
                success=True,
                duration_ms=1000,
            )
        )
        
        # Add recent metric
        service.record_goal_execution("new-goal", True, 1000)
        
        # Trigger cleanup
        service._cleanup_old_metrics()
        
        # Old metric should be removed
        assert len(service._metrics) == 1
        assert service._metrics[0].goal_instance_id == "new-goal"
    
    @pytest.mark.asyncio
    async def test_health_metrics_all_successful(self):
        """Test health metrics with 100% success rate."""
        service = SchedulerHealthService()
        
        # Record 10 successful executions
        for i in range(10):
            service.record_goal_execution(f"goal-{i}", True, 1000 + i * 100)
        
        metrics = await service.get_health_metrics()
        
        assert metrics.status == SchedulerStatus.HEALTHY
        assert metrics.success_rate_1h == 1.0
        assert metrics.failure_rate_1h == 0.0
        assert metrics.total_executions_1h == 10
        assert metrics.avg_duration_ms == 1450.0  # Average of 1000-1900
    
    @pytest.mark.asyncio
    async def test_health_metrics_with_failures(self):
        """Test health metrics with some failures."""
        service = SchedulerHealthService()
        
        # Record 7 successful, 3 failed
        for i in range(7):
            service.record_goal_execution(f"goal-success-{i}", True, 1000)
        for i in range(3):
            service.record_goal_execution(f"goal-fail-{i}", False, 500)
        
        metrics = await service.get_health_metrics()
        
        assert metrics.success_rate_1h == pytest.approx(0.7)
        assert metrics.failure_rate_1h == pytest.approx(0.3)
        assert metrics.total_executions_1h == 10
    
    @pytest.mark.asyncio
    async def test_health_status_healthy(self):
        """Test healthy status determination."""
        service = SchedulerHealthService()
        
        # 96% success rate, DLQ size 2
        for i in range(96):
            service.record_goal_execution(f"goal-success-{i}", True, 1000)
        for i in range(4):
            service.record_goal_execution(f"goal-fail-{i}", False, 500)
        
        metrics = await service.get_health_metrics()
        
        assert metrics.status == SchedulerStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_health_status_degraded(self):
        """Test degraded status determination."""
        service = SchedulerHealthService()
        
        # 85% success rate
        for i in range(85):
            service.record_goal_execution(f"goal-success-{i}", True, 1000)
        for i in range(15):
            service.record_goal_execution(f"goal-fail-{i}", False, 500)
        
        metrics = await service.get_health_metrics()
        
        assert metrics.status == SchedulerStatus.DEGRADED
    
    @pytest.mark.asyncio
    async def test_health_status_down_low_success_rate(self):
        """Test down status with low success rate."""
        service = SchedulerHealthService()
        
        # 70% success rate
        for i in range(70):
            service.record_goal_execution(f"goal-success-{i}", True, 1000)
        for i in range(30):
            service.record_goal_execution(f"goal-fail-{i}", False, 500)
        
        metrics = await service.get_health_metrics()
        
        assert metrics.status == SchedulerStatus.DOWN
    
    @pytest.mark.asyncio
    async def test_health_status_down_no_recent_runs(self):
        """Test down status when scheduler hasn't run recently."""
        service = SchedulerHealthService()
        
        # Set last run to 15 minutes ago
        service._last_run = datetime.now(timezone.utc) - timedelta(minutes=15)
        
        # Record successful executions (but old)
        for i in range(10):
            service.record_goal_execution(f"goal-{i}", True, 1000)
        
        # Manually set last_run back to old time
        service._last_run = datetime.now(timezone.utc) - timedelta(minutes=15)
        
        metrics = await service.get_health_metrics()
        
        assert metrics.status == SchedulerStatus.DOWN
    
    def test_set_pending_goals(self):
        """Test setting pending goals count."""
        service = SchedulerHealthService()
        
        service.set_pending_goals(50)
        
        assert service._pending_goals == 50
    
    def test_pending_goals_alert_triggered(self, caplog):
        """Test alert triggered when pending goals exceed threshold."""
        service = SchedulerHealthService()
        
        with caplog.at_level(logging.ERROR):
            service.set_pending_goals(PENDING_GOALS_ALERT_THRESHOLD + 10)
            
            assert "PENDING GOALS ALERT" in caplog.text
            assert str(PENDING_GOALS_ALERT_THRESHOLD) in caplog.text
    
    @pytest.mark.asyncio
    async def test_success_rate_alert_triggered(self, caplog):
        """Test alert triggered when success rate is low."""
        service = SchedulerHealthService()
        
        # 85% success rate (below 90% threshold)
        for i in range(85):
            service.record_goal_execution(f"goal-success-{i}", True, 1000)
        for i in range(15):
            service.record_goal_execution(f"goal-fail-{i}", False, 500)
        
        with caplog.at_level(logging.ERROR):
            await service.get_health_metrics()
            
            assert "SCHEDULER HEALTH ALERT" in caplog.text
            assert "Low success rate" in caplog.text
    
    def test_prometheus_metrics_export(self):
        """Test Prometheus metrics export format."""
        service = SchedulerHealthService()
        
        # Record some executions
        for i in range(8):
            service.record_goal_execution(f"goal-success-{i}", True, 1000)
        for i in range(2):
            service.record_goal_execution(f"goal-fail-{i}", False, 500)
        
        service.set_pending_goals(25)
        service.set_running_goals(3)
        
        metrics_text = service.get_prometheus_metrics()
        
        assert "scheduler_goals_total 10" in metrics_text
        assert "scheduler_goals_success_total 8" in metrics_text
        assert "scheduler_goals_failure_total 2" in metrics_text
        assert "scheduler_success_rate 0.8" in metrics_text
        assert "scheduler_pending_goals 25" in metrics_text
        assert "scheduler_running_goals 3" in metrics_text
        assert "scheduler_avg_duration_ms" in metrics_text
    
    @pytest.mark.asyncio
    async def test_health_metrics_with_dlq_service(self):
        """Test health metrics includes DLQ size."""
        mock_db = MagicMock(spec=Session)
        dlq_service = DLQService(mock_db)
        dlq_service.repository.count_active = MagicMock(return_value=7)
        
        service = SchedulerHealthService(dlq_service=dlq_service)
        
        # Record some executions
        for i in range(10):
            service.record_goal_execution(f"goal-{i}", True, 1000)
        
        metrics = await service.get_health_metrics()
        
        assert metrics.dlq_size == 7


class TestSchedulerHealthAPI:
    """Test cases for scheduler health API endpoints."""
    
    def setup_method(self):
        """Set up test client and app."""
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)
    
    def test_health_endpoint_returns_metrics(self):
        """Test health endpoint returns comprehensive metrics."""
        # Mock the health service
        mock_service = MagicMock(spec=SchedulerHealthService)
        mock_service.get_health_metrics = AsyncMock(
            return_value=SchedulerHealthMetrics(
                status=SchedulerStatus.HEALTHY,
                pending_goals=45,
                running_goals=3,
                success_rate_1h=0.95,
                failure_rate_1h=0.05,
                total_executions_1h=120,
                last_run=datetime(2026, 2, 12, 10, 30, 0, tzinfo=timezone.utc),
                last_success=datetime(2026, 2, 12, 10, 30, 0, tzinfo=timezone.utc),
                last_failure=datetime(2026, 2, 12, 9, 15, 0, tzinfo=timezone.utc),
                dlq_size=2,
                avg_duration_ms=1250.5,
            )
        )
        
        # Override the dependency
        self.app.dependency_overrides[get_health_service] = lambda: mock_service
        
        response = self.client.get("/api/v1/scheduler/health")
        
        # Clear override after test
        self.app.dependency_overrides = {}
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["pending_goals"] == 45
        assert data["running_goals"] == 3
        assert data["success_rate_1h"] == 0.95
        assert data["failure_rate_1h"] == 0.05
        assert data["total_executions_1h"] == 120
        assert data["dlq_size"] == 2
        assert data["avg_duration_ms"] == 1250.5
    
    def test_metrics_endpoint_returns_prometheus_format(self):
        """Test metrics endpoint returns Prometheus format."""
        mock_service = MagicMock(spec=SchedulerHealthService)
        mock_service.get_prometheus_metrics = MagicMock(
            return_value="scheduler_goals_total 100\nscheduler_success_rate 0.95\n"
        )
        
        with patch("api.v1.scheduler_health.get_health_service", return_value=mock_service):
            response = self.client.get("/api/v1/scheduler/metrics")
        
        assert response.status_code == 200
        assert "scheduler_goals_total" in response.text
        assert "scheduler_success_rate" in response.text


# Import required for test
from services.scheduler_health_service import (
    GoalExecutionMetric,
    SchedulerHealthMetrics,
)
