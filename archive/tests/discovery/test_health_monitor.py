"""
Tests for Health Monitor

Tests health checking, metrics tracking, status updates,
and integration with service registry.
"""

import asyncio

import pytest

from waooaw.discovery.health_monitor import (
    HealthCheckResult,
    HealthMetrics,
    HealthMonitor,
    HealthStatus,
)
from waooaw.discovery.service_registry import (
    AgentCapability,
    AgentStatus,
    ServiceRegistry,
)


@pytest.mark.asyncio
class TestHealthCheckResult:
    """Test HealthCheckResult dataclass"""

    def test_create_result(self):
        """Should create health check result"""
        result = HealthCheckResult(
            agent_id="agent-1",
            status=HealthStatus.HEALTHY,
            response_time_ms=50.0,
        )

        assert result.agent_id == "agent-1"
        assert result.status == HealthStatus.HEALTHY
        assert result.response_time_ms == 50.0
        assert result.error is None
        assert result.is_healthy

    def test_unhealthy_result(self):
        """Should indicate unhealthy status"""
        result = HealthCheckResult(
            agent_id="agent-1",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=100.0,
            error="Connection refused",
        )

        assert not result.is_healthy
        assert result.error == "Connection refused"


@pytest.mark.asyncio
class TestHealthMetrics:
    """Test HealthMetrics dataclass"""

    def test_create_metrics(self):
        """Should create metrics with defaults"""
        metrics = HealthMetrics(agent_id="agent-1")

        assert metrics.agent_id == "agent-1"
        assert metrics.total_checks == 0
        assert metrics.successful_checks == 0
        assert metrics.failed_checks == 0
        assert metrics.consecutive_failures == 0
        assert metrics.success_rate == 0.0
        assert metrics.failure_rate == 1.0

    def test_success_rate(self):
        """Should calculate success rate"""
        metrics = HealthMetrics(agent_id="agent-1")
        metrics.total_checks = 10
        metrics.successful_checks = 7

        assert metrics.success_rate == 0.7
        assert pytest.approx(metrics.failure_rate, rel=1e-9) == 0.3

    def test_update_from_healthy_result(self):
        """Should update metrics from healthy result"""
        metrics = HealthMetrics(agent_id="agent-1")
        result = HealthCheckResult(
            agent_id="agent-1",
            status=HealthStatus.HEALTHY,
            response_time_ms=50.0,
        )

        metrics.update_from_result(result)

        assert metrics.total_checks == 1
        assert metrics.successful_checks == 1
        assert metrics.failed_checks == 0
        assert metrics.consecutive_failures == 0
        assert metrics.average_response_time_ms == 50.0
        assert metrics.last_success is not None

    def test_update_from_unhealthy_result(self):
        """Should update metrics from unhealthy result"""
        metrics = HealthMetrics(agent_id="agent-1")
        result = HealthCheckResult(
            agent_id="agent-1",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=100.0,
        )

        metrics.update_from_result(result)

        assert metrics.total_checks == 1
        assert metrics.successful_checks == 0
        assert metrics.failed_checks == 1
        assert metrics.consecutive_failures == 1
        assert metrics.last_failure is not None

    def test_consecutive_failures(self):
        """Should track consecutive failures"""
        metrics = HealthMetrics(agent_id="agent-1")

        # Add failures
        for _ in range(3):
            result = HealthCheckResult(
                agent_id="agent-1",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=100.0,
            )
            metrics.update_from_result(result)

        assert metrics.consecutive_failures == 3

        # Add success - should reset
        result = HealthCheckResult(
            agent_id="agent-1",
            status=HealthStatus.HEALTHY,
            response_time_ms=50.0,
        )
        metrics.update_from_result(result)

        assert metrics.consecutive_failures == 0

    def test_exponential_moving_average(self):
        """Should calculate EMA for response time"""
        metrics = HealthMetrics(agent_id="agent-1")

        # First result sets initial value
        result1 = HealthCheckResult(
            agent_id="agent-1",
            status=HealthStatus.HEALTHY,
            response_time_ms=100.0,
        )
        metrics.update_from_result(result1)
        assert metrics.average_response_time_ms == 100.0

        # Second result applies EMA
        result2 = HealthCheckResult(
            agent_id="agent-1",
            status=HealthStatus.HEALTHY,
            response_time_ms=200.0,
        )
        metrics.update_from_result(result2)

        # EMA: 0.3 * 200 + 0.7 * 100 = 130
        assert metrics.average_response_time_ms == 130.0


@pytest.mark.asyncio
class TestHealthMonitor:
    """Test HealthMonitor functionality"""

    async def test_create_monitor(self):
        """Should create health monitor"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(
            registry,
            check_interval=30,
            failure_threshold=3,
            response_timeout=5.0,
        )

        assert monitor._check_interval == 30
        assert monitor._failure_threshold == 3
        assert monitor._response_timeout == 5.0

    async def test_start_stop(self):
        """Should start and stop monitoring"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry, check_interval=10)

        await monitor.start()
        assert monitor._monitor_task is not None

        await monitor.stop()
        assert monitor._monitor_task is None

    async def test_register_health_checker(self):
        """Should register custom health checker"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry)

        async def custom_checker():
            return True

        monitor.register_health_checker("agent-1", custom_checker)
        assert "agent-1" in monitor._health_checkers

        assert monitor.unregister_health_checker("agent-1")
        assert "agent-1" not in monitor._health_checkers

    async def test_check_health_with_custom_checker(self):
        """Should use custom health checker"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry)

        async def healthy_checker():
            await asyncio.sleep(0.01)
            return True

        monitor.register_health_checker("agent-1", healthy_checker)
        result = await monitor.check_health("agent-1")

        assert result.agent_id == "agent-1"
        assert result.status == HealthStatus.HEALTHY
        assert result.response_time_ms > 0

    async def test_check_health_with_unhealthy_checker(self):
        """Should detect unhealthy agent"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry)

        async def unhealthy_checker():
            return False

        monitor.register_health_checker("agent-1", unhealthy_checker)
        result = await monitor.check_health("agent-1")

        assert result.status == HealthStatus.UNHEALTHY

    async def test_check_health_timeout(self):
        """Should timeout on slow health check"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry, response_timeout=0.1)

        async def slow_checker():
            await asyncio.sleep(1.0)
            return True

        monitor.register_health_checker("agent-1", slow_checker)
        result = await monitor.check_health("agent-1")

        assert result.status == HealthStatus.UNHEALTHY
        assert "timeout" in result.error.lower()

    async def test_check_health_degraded(self):
        """Should detect degraded performance"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry, degraded_threshold_ms=50.0)

        async def slow_but_healthy():
            await asyncio.sleep(0.1)  # 100ms
            return True

        monitor.register_health_checker("agent-1", slow_but_healthy)
        result = await monitor.check_health("agent-1")

        assert result.status == HealthStatus.DEGRADED
        assert result.response_time_ms > 50.0

    async def test_check_health_with_error(self):
        """Should handle checker errors"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry)

        async def failing_checker():
            raise ValueError("Check failed")

        monitor.register_health_checker("agent-1", failing_checker)
        result = await monitor.check_health("agent-1")

        assert result.status == HealthStatus.UNHEALTHY
        assert "Check failed" in result.error

    async def test_check_health_default_checker(self):
        """Should use default checker if no custom checker"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry)

        # Register agent
        await registry.register(
            agent_id="agent-1",
            name="Test",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("test", "1.0")},
        )

        # Check health (default: verify registration)
        result = await monitor.check_health("agent-1")

        assert result.status == HealthStatus.HEALTHY

    async def test_metrics_tracking(self):
        """Should track metrics across checks"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry)

        async def checker():
            return True

        monitor.register_health_checker("agent-1", checker)

        # Perform multiple checks
        for _ in range(5):
            await monitor.check_health("agent-1")

        metrics = await monitor.get_metrics("agent-1")
        assert metrics is not None
        assert metrics.total_checks == 5
        assert metrics.successful_checks == 5
        assert metrics.success_rate == 1.0

    async def test_get_health_status(self):
        """Should get current health status"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry)

        async def checker():
            return True

        monitor.register_health_checker("agent-1", checker)

        # Unknown before first check
        status = await monitor.get_health_status("agent-1")
        assert status == HealthStatus.UNKNOWN

        # Healthy after successful check
        await monitor.check_health("agent-1")
        status = await monitor.get_health_status("agent-1")
        assert status == HealthStatus.HEALTHY

    async def test_consecutive_failures_threshold(self):
        """Should mark unhealthy after failure threshold"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry, failure_threshold=3)

        async def failing_checker():
            return False

        monitor.register_health_checker("agent-1", failing_checker)

        # Perform checks up to threshold
        for _ in range(3):
            await monitor.check_health("agent-1")

        status = await monitor.get_health_status("agent-1")
        assert status == HealthStatus.UNHEALTHY

        metrics = await monitor.get_metrics("agent-1")
        assert metrics.consecutive_failures == 3

    async def test_get_all_metrics(self):
        """Should get metrics for all agents"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry)

        async def checker():
            return True

        monitor.register_health_checker("agent-1", checker)
        monitor.register_health_checker("agent-2", checker)

        await monitor.check_health("agent-1")
        await monitor.check_health("agent-2")

        all_metrics = await monitor.get_all_metrics()
        assert len(all_metrics) == 2
        assert "agent-1" in all_metrics
        assert "agent-2" in all_metrics

    async def test_get_healthy_agents(self):
        """Should list healthy agents"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry)

        async def healthy():
            return True

        async def unhealthy():
            return False

        monitor.register_health_checker("agent-1", healthy)
        monitor.register_health_checker("agent-2", unhealthy)

        await monitor.check_health("agent-1")
        await monitor.check_health("agent-2")

        healthy_agents = await monitor.get_healthy_agents()
        assert len(healthy_agents) == 1
        assert "agent-1" in healthy_agents

    async def test_get_unhealthy_agents(self):
        """Should list unhealthy agents"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry)

        async def healthy():
            return True

        async def unhealthy():
            return False

        monitor.register_health_checker("agent-1", healthy)
        monitor.register_health_checker("agent-2", unhealthy)

        await monitor.check_health("agent-1")
        await monitor.check_health("agent-2")

        unhealthy_agents = await monitor.get_unhealthy_agents()
        assert len(unhealthy_agents) == 1
        assert "agent-2" in unhealthy_agents

    async def test_update_registry_status(self):
        """Should update registry based on health"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry, failure_threshold=2)

        # Register agent
        await registry.register(
            agent_id="agent-1",
            name="Test",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("test", "1.0")},
            status=AgentStatus.ONLINE,
        )

        # Unhealthy checker
        async def unhealthy():
            return False

        monitor.register_health_checker("agent-1", unhealthy)

        # Check multiple times to exceed threshold
        for _ in range(2):
            await monitor.check_health("agent-1")

        # Registry status should be updated to OFFLINE
        agent = await registry.get("agent-1")
        assert agent.status == AgentStatus.OFFLINE

    async def test_check_all_agents(self):
        """Should check all registered agents"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry, check_interval=10)

        # Register agents
        await registry.register(
            agent_id="agent-1",
            name="A",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("test", "1.0")},
        )
        await registry.register(
            agent_id="agent-2",
            name="B",
            host="localhost",
            port=8002,
            capabilities={AgentCapability("test", "1.0")},
        )

        # Check all
        await monitor._check_all_agents()

        # Both should have metrics
        metrics1 = await monitor.get_metrics("agent-1")
        metrics2 = await monitor.get_metrics("agent-2")

        assert metrics1 is not None
        assert metrics2 is not None
        assert metrics1.total_checks == 1
        assert metrics2.total_checks == 1

    async def test_monitor_loop(self):
        """Should automatically check agents periodically"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry, check_interval=1)

        # Register agent
        await registry.register(
            agent_id="agent-1",
            name="Test",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("test", "1.0")},
        )

        await monitor.start()

        # Wait for multiple check cycles
        await asyncio.sleep(2.5)

        # Should have performed multiple checks
        metrics = await monitor.get_metrics("agent-1")
        assert metrics is not None
        assert metrics.total_checks >= 2

        await monitor.stop()
