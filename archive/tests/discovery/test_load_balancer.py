"""
Tests for Load Balancer

Tests load balancing strategies, agent selection, connection tracking,
and integration with health monitoring.
"""

import pytest

from waooaw.discovery.health_monitor import HealthMonitor, HealthStatus
from waooaw.discovery.load_balancer import (
    LoadBalancer,
    LoadBalancerMetrics,
    LoadBalancingStrategy,
    NoAvailableAgentsError,
    SelectionResult,
)
from waooaw.discovery.service_registry import (
    AgentCapability,
    AgentStatus,
    ServiceRegistry,
)


@pytest.mark.asyncio
class TestLoadBalancerMetrics:
    """Test LoadBalancerMetrics dataclass"""

    def test_create_metrics(self):
        """Should create metrics with defaults"""
        metrics = LoadBalancerMetrics(agent_id="agent-1")

        assert metrics.agent_id == "agent-1"
        assert metrics.total_requests == 0
        assert metrics.active_connections == 0
        assert metrics.failed_requests == 0
        assert metrics.success_rate == 1.0

    def test_success_rate(self):
        """Should calculate success rate"""
        metrics = LoadBalancerMetrics(agent_id="agent-1")
        metrics.total_requests = 10
        metrics.failed_requests = 2

        assert metrics.success_rate == 0.8


@pytest.mark.asyncio
class TestSelectionResult:
    """Test SelectionResult dataclass"""

    async def test_create_result(self):
        """Should create selection result"""
        registry = ServiceRegistry()
        await registry.register(
            agent_id="agent-1",
            name="Test",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("test", "1.0")},
        )

        agent = await registry.get("agent-1")
        metrics = LoadBalancerMetrics(agent_id="agent-1")

        result = SelectionResult(
            agent=agent,
            strategy=LoadBalancingStrategy.ROUND_ROBIN,
            metrics=metrics,
            healthy=True,
        )

        assert result.agent.agent_id == "agent-1"
        assert result.strategy == LoadBalancingStrategy.ROUND_ROBIN
        assert result.healthy


@pytest.mark.asyncio
class TestLoadBalancer:
    """Test LoadBalancer functionality"""

    async def test_create_load_balancer(self):
        """Should create load balancer"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry)

        assert lb._strategy == LoadBalancingStrategy.ROUND_ROBIN
        assert lb._default_weight == 1

    async def test_create_with_custom_strategy(self):
        """Should create with custom strategy"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry, strategy=LoadBalancingStrategy.RANDOM)

        assert lb._strategy == LoadBalancingStrategy.RANDOM

    async def test_set_strategy(self):
        """Should change strategy"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry)

        lb.set_strategy(LoadBalancingStrategy.LEAST_CONNECTIONS)
        assert lb._strategy == LoadBalancingStrategy.LEAST_CONNECTIONS

    async def test_set_weight(self):
        """Should set agent weight"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry)

        lb.set_weight("agent-1", 5)
        assert lb.get_weight("agent-1") == 5

    async def test_set_weight_validation(self):
        """Should validate weight"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry)

        with pytest.raises(ValueError, match="non-negative"):
            lb.set_weight("agent-1", -1)

    async def test_get_default_weight(self):
        """Should return default weight"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry, default_weight=2)

        assert lb.get_weight("unknown-agent") == 2

    async def test_select_no_agents(self):
        """Should raise error when no agents available"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry)

        with pytest.raises(NoAvailableAgentsError):
            await lb.select_agent()

    async def test_select_agent_round_robin(self):
        """Should select agents using round-robin"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry, strategy=LoadBalancingStrategy.ROUND_ROBIN)

        # Register 3 agents
        for i in range(3):
            await registry.register(
                agent_id=f"agent-{i}",
                name=f"Agent {i}",
                host="localhost",
                port=8001 + i,
                capabilities={AgentCapability("test", "1.0")},
            )

        # Select multiple times - should rotate
        selections = []
        for _ in range(6):
            result = await lb.select_agent()
            selections.append(result.agent.agent_id)

        # Should cycle through all agents
        assert selections == [
            "agent-0",
            "agent-1",
            "agent-2",
            "agent-0",
            "agent-1",
            "agent-2",
        ]

    async def test_select_agent_least_connections(self):
        """Should select agent with fewest connections"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry, strategy=LoadBalancingStrategy.LEAST_CONNECTIONS)

        # Register 3 agents
        for i in range(3):
            await registry.register(
                agent_id=f"agent-{i}",
                name=f"Agent {i}",
                host="localhost",
                port=8001 + i,
                capabilities={AgentCapability("test", "1.0")},
            )

        # Acquire connections on agent-0
        await lb.acquire_connection("agent-0")
        await lb.acquire_connection("agent-0")

        # Next selection should be agent-1 or agent-2 (both have 0 connections)
        result = await lb.select_agent()
        assert result.agent.agent_id in ["agent-1", "agent-2"]

        # Acquire on selected agent
        await lb.acquire_connection(result.agent.agent_id)

        # Next should be the other agent with 0 connections
        result2 = await lb.select_agent()
        assert result2.agent.agent_id != result.agent.agent_id
        assert result2.agent.agent_id != "agent-0"

    async def test_select_agent_weighted(self):
        """Should respect agent weights"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry, strategy=LoadBalancingStrategy.WEIGHTED)

        # Register agents with different weights
        for i in range(2):
            await registry.register(
                agent_id=f"agent-{i}",
                name=f"Agent {i}",
                host="localhost",
                port=8001 + i,
                capabilities={AgentCapability("test", "1.0")},
            )

        # Set weights: agent-0 = 10, agent-1 = 1
        lb.set_weight("agent-0", 10)
        lb.set_weight("agent-1", 1)

        # Select many times - agent-0 should be selected more often
        selections = {"agent-0": 0, "agent-1": 0}
        for _ in range(100):
            result = await lb.select_agent()
            selections[result.agent.agent_id] += 1

        # agent-0 should be selected ~90% of the time
        assert selections["agent-0"] > selections["agent-1"] * 5

    async def test_select_agent_weighted_zero_weights(self):
        """Should handle all zero weights"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry, strategy=LoadBalancingStrategy.WEIGHTED, default_weight=0)

        await registry.register(
            agent_id="agent-1",
            name="Agent",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("test", "1.0")},
        )

        # Should fall back to random selection
        result = await lb.select_agent()
        assert result.agent.agent_id == "agent-1"

    async def test_select_agent_random(self):
        """Should select agents randomly"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry, strategy=LoadBalancingStrategy.RANDOM)

        # Register 3 agents
        for i in range(3):
            await registry.register(
                agent_id=f"agent-{i}",
                name=f"Agent {i}",
                host="localhost",
                port=8001 + i,
                capabilities={AgentCapability("test", "1.0")},
            )

        # Select multiple times - should see all agents
        selections = set()
        for _ in range(20):
            result = await lb.select_agent()
            selections.add(result.agent.agent_id)

        # Should have selected all 3 agents at some point
        assert len(selections) == 3

    async def test_select_by_capability(self):
        """Should filter by capability"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry)

        # Register agents with different capabilities
        await registry.register(
            agent_id="agent-1",
            name="Agent 1",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("process", "1.0")},
        )
        await registry.register(
            agent_id="agent-2",
            name="Agent 2",
            host="localhost",
            port=8002,
            capabilities={AgentCapability("analyze", "1.0")},
        )

        # Select by capability
        result = await lb.select_agent(capability="process")
        assert result.agent.agent_id == "agent-1"

        result = await lb.select_agent(capability="analyze")
        assert result.agent.agent_id == "agent-2"

    async def test_select_by_tags(self):
        """Should filter by tags"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry)

        # Register agents with different tags
        await registry.register(
            agent_id="agent-1",
            name="Agent 1",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("test", "1.0")},
            tags={"production", "us-west"},
        )
        await registry.register(
            agent_id="agent-2",
            name="Agent 2",
            host="localhost",
            port=8002,
            capabilities={AgentCapability("test", "1.0")},
            tags={"staging", "us-east"},
        )

        # Select by tags
        result = await lb.select_agent(tags={"production"})
        assert result.agent.agent_id == "agent-1"

    async def test_select_healthy_only(self):
        """Should only select healthy agents"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry)
        lb = LoadBalancer(registry, health_monitor=monitor)

        # Register agents
        await registry.register(
            agent_id="agent-1",
            name="Agent 1",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("test", "1.0")},
        )
        await registry.register(
            agent_id="agent-2",
            name="Agent 2",
            host="localhost",
            port=8002,
            capabilities={AgentCapability("test", "1.0")},
        )

        # Set up health checkers
        async def healthy():
            return True

        async def unhealthy():
            return False

        monitor.register_health_checker("agent-1", healthy)
        monitor.register_health_checker("agent-2", unhealthy)

        # Check health
        await monitor.check_health("agent-1")
        await monitor.check_health("agent-2")

        # Should only select agent-1
        result = await lb.select_agent(require_healthy=True)
        assert result.agent.agent_id == "agent-1"

    async def test_select_without_health_requirement(self):
        """Should select any agent if health not required"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry)
        lb = LoadBalancer(registry, health_monitor=monitor)

        # Register agents
        await registry.register(
            agent_id="agent-1",
            name="Agent 1",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("test", "1.0")},
        )

        async def unhealthy():
            return False

        monitor.register_health_checker("agent-1", unhealthy)
        await monitor.check_health("agent-1")

        # Should select even though unhealthy
        result = await lb.select_agent(require_healthy=False)
        assert result.agent.agent_id == "agent-1"

    async def test_acquire_connection(self):
        """Should track active connections"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry)

        await lb.acquire_connection("agent-1")
        await lb.acquire_connection("agent-1")

        metrics = await lb.get_metrics("agent-1")
        assert metrics.active_connections == 2
        assert metrics.total_connections == 2
        assert metrics.total_requests == 2

    async def test_release_connection(self):
        """Should decrease active connections"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry)

        await lb.acquire_connection("agent-1")
        await lb.acquire_connection("agent-1")
        await lb.release_connection("agent-1")

        metrics = await lb.get_metrics("agent-1")
        assert metrics.active_connections == 1

    async def test_release_connection_failed(self):
        """Should track failed requests"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry)

        await lb.acquire_connection("agent-1")
        await lb.release_connection("agent-1", failed=True)

        metrics = await lb.get_metrics("agent-1")
        assert metrics.failed_requests == 1
        assert metrics.success_rate == 0.0

    async def test_release_nonexistent_connection(self):
        """Should handle releasing nonexistent connection"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry)

        # Should not raise error
        await lb.release_connection("unknown-agent")

    async def test_get_metrics(self):
        """Should retrieve agent metrics"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry)

        await lb.acquire_connection("agent-1")

        metrics = await lb.get_metrics("agent-1")
        assert metrics is not None
        assert metrics.agent_id == "agent-1"

        # Unknown agent returns None
        metrics = await lb.get_metrics("unknown")
        assert metrics is None

    async def test_get_all_metrics(self):
        """Should retrieve all metrics"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry)

        await lb.acquire_connection("agent-1")
        await lb.acquire_connection("agent-2")

        all_metrics = await lb.get_all_metrics()
        assert len(all_metrics) == 2
        assert "agent-1" in all_metrics
        assert "agent-2" in all_metrics

    async def test_reset_metrics_single(self):
        """Should reset metrics for single agent"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry)

        await lb.acquire_connection("agent-1")
        await lb.reset_metrics("agent-1")

        metrics = await lb.get_metrics("agent-1")
        assert metrics.total_requests == 0
        assert metrics.active_connections == 0

    async def test_reset_metrics_all(self):
        """Should reset all metrics"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry)

        await lb.acquire_connection("agent-1")
        await lb.acquire_connection("agent-2")
        await lb.reset_metrics()

        metrics1 = await lb.get_metrics("agent-1")
        metrics2 = await lb.get_metrics("agent-2")

        assert metrics1.total_requests == 0
        assert metrics2.total_requests == 0

    async def test_selection_result_includes_health(self):
        """Should include health status in result"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry)
        lb = LoadBalancer(registry, health_monitor=monitor)

        await registry.register(
            agent_id="agent-1",
            name="Agent 1",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("test", "1.0")},
        )

        async def healthy():
            return True

        monitor.register_health_checker("agent-1", healthy)
        await monitor.check_health("agent-1")

        result = await lb.select_agent()
        assert result.healthy

    async def test_integration_with_registry_and_monitor(self):
        """Should integrate with registry and health monitor"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry, failure_threshold=2)
        lb = LoadBalancer(
            registry, health_monitor=monitor, strategy=LoadBalancingStrategy.LEAST_CONNECTIONS
        )

        # Register agents
        await registry.register(
            agent_id="agent-1",
            name="Agent 1",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("process", "1.0")},
            tags={"production"},
        )
        await registry.register(
            agent_id="agent-2",
            name="Agent 2",
            host="localhost",
            port=8002,
            capabilities={AgentCapability("process", "1.0")},
            tags={"production"},
        )

        # Set health checkers
        async def healthy():
            return True

        async def unhealthy():
            return False

        monitor.register_health_checker("agent-1", healthy)
        monitor.register_health_checker("agent-2", unhealthy)

        # Check health
        await monitor.check_health("agent-1")
        await monitor.check_health("agent-2")
        await monitor.check_health("agent-2")

        # Load balancer should only select agent-1
        for _ in range(5):
            result = await lb.select_agent(capability="process", require_healthy=True)
            assert result.agent.agent_id == "agent-1"
            assert result.healthy

            # Track connection
            await lb.acquire_connection(result.agent.agent_id)
            await lb.release_connection(result.agent.agent_id)

        # Check metrics
        metrics = await lb.get_metrics("agent-1")
        assert metrics.total_requests == 5
        assert metrics.active_connections == 0
