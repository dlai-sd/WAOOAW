"""
Integration Tests: Orchestration + Discovery

Tests the complete multi-agent system combining task orchestration
with agent discovery, health monitoring, load balancing, and fault tolerance.

These tests demonstrate how the orchestration and discovery layers work together
to create a fault-tolerant, scalable multi-agent system.
"""

import asyncio
import pytest

from waooaw.discovery import (
    CircuitBreaker,
    HealthMonitor,
    LoadBalancer,
    LoadBalancingStrategy,
    ServiceRegistry,
    AgentCapability,
)
from waooaw.orchestration import (
    RetryPolicy,
    RetryConfig,
    RetryStrategy,
)


@pytest.mark.asyncio
class TestOrchestrationDiscoveryIntegration:
    """Integration tests for orchestration + discovery"""

    async def test_service_registry_with_health_monitoring(self):
        """Should register agents and monitor their health"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry, failure_threshold=2)

        # Register agents
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
            capabilities={AgentCapability("process", "1.0")},
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
        await monitor.check_health("agent-2")  # Trip threshold

        # Verify healthy agents
        healthy_agents = await monitor.get_healthy_agents()
        assert "agent-1" in healthy_agents
        assert "agent-2" not in healthy_agents

        # Verify registry updated
        agent1 = await registry.get("agent-1")
        assert agent1 is not None

        await monitor.stop()

    async def test_load_balancer_with_circuit_breaker(self):
        """Should load balance agents and track failures with circuit breaker"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry, strategy=LoadBalancingStrategy.ROUND_ROBIN)
        cb = CircuitBreaker(failure_threshold=0.5, minimum_requests=2)

        # Register agents
        for i in range(3):
            await registry.register(
                agent_id=f"worker-{i}",
                name=f"Worker {i}",
                host="localhost",
                port=8001 + i,
                capabilities={AgentCapability("compute", "1.0")},
            )

        # Select agents and track with circuit breaker
        selections = []
        for _ in range(6):
            agent = await lb.select_agent(capability="compute")
            selections.append(agent.agent.agent_id)
            await lb.acquire_connection(agent.agent.agent_id)
            
            # Simulate some failures on worker-1
            if agent.agent.agent_id == "worker-1":
                await cb.record_failure(agent.agent.agent_id)
            else:
                await cb.record_success(agent.agent.agent_id)
            
            await lb.release_connection(agent.agent.agent_id)

        # Verify round-robin distribution
        assert all(f"worker-{i}" in selections for i in range(3))

        # Verify circuit breaker tracked failures
        metrics_1 = await cb.get_metrics("worker-1")
        assert metrics_1.failed_requests > 0

        # Verify successful workers
        metrics_0 = await cb.get_metrics("worker-0")
        assert metrics_0.successful_requests > 0

    async def test_health_based_load_balancing(self):
        """Should route only to healthy agents"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry, failure_threshold=2)
        lb = LoadBalancer(registry, health_monitor=monitor)

        # Register agents
        await registry.register(
            agent_id="healthy",
            name="Healthy",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("work", "1.0")},
        )
        await registry.register(
            agent_id="unhealthy",
            name="Unhealthy",
            host="localhost",
            port=8002,
            capabilities={AgentCapability("work", "1.0")},
        )

        # Set health checkers
        async def healthy():
            return True

        async def unhealthy():
            return False

        monitor.register_health_checker("healthy", healthy)
        monitor.register_health_checker("unhealthy", unhealthy)

        # Check health
        await monitor.check_health("healthy")
        await monitor.check_health("unhealthy")
        await monitor.check_health("unhealthy")  # Trip threshold

        # Select agents - should only get healthy
        selections = []
        for _ in range(5):
            agent = await lb.select_agent(capability="work", require_healthy=True)
            selections.append(agent.agent.agent_id)

        # All should be healthy agent
        assert all(agent_id == "healthy" for agent_id in selections)

        await monitor.stop()

    async def test_circuit_breaker_with_retry_logic(self):
        """Should combine circuit breaker with retry policy"""
        cb = CircuitBreaker(failure_threshold=0.5, minimum_requests=2)
        retry_config = RetryConfig(
            max_retries=3,
            strategy=RetryStrategy.EXPONENTIAL,
            base_delay=0.1,
        )
        retry_policy = RetryPolicy(config=retry_config)

        attempt = 0

        async def failing_then_succeeding():
            nonlocal attempt
            attempt += 1
            if attempt <= 2:
                await cb.record_failure("agent-1")
                raise ValueError(f"Attempt {attempt} failed")
            await cb.record_success("agent-1")
            return "success"

        # Execute with retries
        result = None
        for i in range(retry_config.max_retries):
            try:
                result = await failing_then_succeeding()
                break
            except ValueError:
                if i < retry_config.max_retries - 1:
                    delay = retry_policy.calculate_delay(i)
                    await asyncio.sleep(delay)
                    continue
                raise

        # Verify success
        assert result == "success"
        assert attempt == 3

        # Verify circuit breaker metrics
        metrics = await cb.get_metrics("agent-1")
        assert metrics.failed_requests == 2
        assert metrics.successful_requests == 1

    async def test_multi_agent_fault_tolerance(self):
        """Should handle multi-agent workflow with failures"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry, failure_threshold=2)
        lb = LoadBalancer(registry, health_monitor=monitor)
        cb = CircuitBreaker(failure_threshold=0.6, minimum_requests=3)

        # Register agents (some unhealthy)
        for i in range(4):
            await registry.register(
                agent_id=f"agent-{i}",
                name=f"Agent {i}",
                host="localhost",
                port=8001 + i,
                capabilities={AgentCapability("process", "1.0")},
            )

        # Set health checkers (agent-2 is unhealthy)
        async def healthy():
            return True

        async def unhealthy():
            return False

        monitor.register_health_checker("agent-0", healthy)
        monitor.register_health_checker("agent-1", healthy)
        monitor.register_health_checker("agent-2", unhealthy)
        monitor.register_health_checker("agent-3", healthy)

        # Check health
        for i in range(4):
            await monitor.check_health(f"agent-{i}")
            await monitor.check_health(f"agent-{i}")  # Second check

        # Process tasks through healthy agents
        successful = 0
        for _ in range(10):
            try:
                agent = await lb.select_agent(capability="process", require_healthy=True)
                await lb.acquire_connection(agent.agent.agent_id)
                
                # Simulate processing
                await asyncio.sleep(0.01)
                
                await cb.record_success(agent.agent.agent_id)
                await lb.release_connection(agent.agent.agent_id)
                successful += 1
            except Exception:
                pass

        # All tasks should succeed (routed to healthy agents)
        assert successful == 10

        # Verify healthy agents
        healthy_agents = await monitor.get_healthy_agents()
        assert len(healthy_agents) == 3
        assert "agent-2" not in healthy_agents

        # Verify load distribution
        metrics = await lb.get_all_metrics()
        assert len(metrics) >= 3

        await monitor.stop()

    async def test_weighted_load_balancing_integration(self):
        """Should distribute load based on agent weights"""
        registry = ServiceRegistry()
        lb = LoadBalancer(registry, strategy=LoadBalancingStrategy.WEIGHTED)

        # Register agents
        await registry.register(
            agent_id="premium",
            name="Premium Agent",
            host="localhost",
            port=8001,
            capabilities={AgentCapability("compute", "1.0")},
        )
        await registry.register(
            agent_id="standard",
            name="Standard Agent",
            host="localhost",
            port=8002,
            capabilities={AgentCapability("compute", "1.0")},
        )

        # Set weights (premium 10x more likely)
        lb.set_weight("premium", 10)
        lb.set_weight("standard", 1)

        # Select agents
        selections = []
        for _ in range(20):
            agent = await lb.select_agent(capability="compute")
            selections.append(agent.agent.agent_id)

        # Premium should be selected more often (roughly 10:1 ratio)
        premium_count = selections.count("premium")
        standard_count = selections.count("standard")
        
        assert premium_count > standard_count
        assert premium_count >= 15  # Should be most selections
