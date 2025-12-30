"""
Tests for Circuit Breaker

Tests circuit breaker pattern, state transitions, failure tracking,
and integration with health monitoring.
"""

import asyncio
import time

import pytest

from waooaw.discovery.circuit_breaker import (
    CircuitBreaker,
    CircuitMetrics,
    CircuitOpenError,
    CircuitState,
)
from waooaw.discovery.health_monitor import HealthMonitor
from waooaw.discovery.service_registry import ServiceRegistry


@pytest.mark.asyncio
class TestCircuitMetrics:
    """Test CircuitMetrics dataclass"""

    def test_create_metrics(self):
        """Should create metrics with defaults"""
        metrics = CircuitMetrics(agent_id="agent-1")

        assert metrics.agent_id == "agent-1"
        assert metrics.state == CircuitState.CLOSED
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.failure_rate == 0.0
        assert metrics.success_rate == 1.0

    def test_failure_rate(self):
        """Should calculate failure rate"""
        metrics = CircuitMetrics(agent_id="agent-1")
        metrics.total_requests = 10
        metrics.successful_requests = 7
        metrics.failed_requests = 3

        assert metrics.failure_rate == 0.3
        assert metrics.success_rate == 0.7


@pytest.mark.asyncio
class TestCircuitBreaker:
    """Test CircuitBreaker functionality"""

    async def test_create_circuit_breaker(self):
        """Should create circuit breaker"""
        cb = CircuitBreaker(
            failure_threshold=0.5,
            success_threshold=2,
            timeout=60.0,
        )

        assert cb._failure_threshold == 0.5
        assert cb._success_threshold == 2
        assert cb._timeout == 60.0

    async def test_validation(self):
        """Should validate parameters"""
        with pytest.raises(ValueError, match="failure_threshold"):
            CircuitBreaker(failure_threshold=1.5)

        with pytest.raises(ValueError, match="success_threshold"):
            CircuitBreaker(success_threshold=0)

        with pytest.raises(ValueError, match="timeout"):
            CircuitBreaker(timeout=-1)

        with pytest.raises(ValueError, match="minimum_requests"):
            CircuitBreaker(minimum_requests=0)

    async def test_initial_state(self):
        """Should start in closed state"""
        cb = CircuitBreaker()
        state = cb.get_state("agent-1")

        assert state == CircuitState.CLOSED

    async def test_record_success(self):
        """Should record successful requests"""
        cb = CircuitBreaker()

        await cb.record_success("agent-1")
        await cb.record_success("agent-1")

        metrics = await cb.get_metrics("agent-1")
        assert metrics.total_requests == 2
        assert metrics.successful_requests == 2
        assert metrics.consecutive_successes == 2
        assert metrics.state == CircuitState.CLOSED

    async def test_record_failure(self):
        """Should record failed requests"""
        cb = CircuitBreaker()

        await cb.record_failure("agent-1")
        await cb.record_failure("agent-1")

        metrics = await cb.get_metrics("agent-1")
        assert metrics.total_requests == 2
        assert metrics.failed_requests == 2
        assert metrics.consecutive_failures == 2

    async def test_open_circuit_on_threshold(self):
        """Should open circuit when failure threshold exceeded"""
        cb = CircuitBreaker(
            failure_threshold=0.5,
            minimum_requests=5,
        )

        # Record requests: 3 failures out of 5 = 60% failure rate
        await cb.record_success("agent-1")
        await cb.record_success("agent-1")
        await cb.record_failure("agent-1")
        await cb.record_failure("agent-1")
        await cb.record_failure("agent-1")

        state = cb.get_state("agent-1")
        assert state == CircuitState.OPEN

        metrics = await cb.get_metrics("agent-1")
        assert metrics.trip_count == 1

    async def test_minimum_requests_requirement(self):
        """Should require minimum requests before opening"""
        cb = CircuitBreaker(
            failure_threshold=0.5,
            minimum_requests=10,
        )

        # Only 3 failures, below minimum
        await cb.record_failure("agent-1")
        await cb.record_failure("agent-1")
        await cb.record_failure("agent-1")

        state = cb.get_state("agent-1")
        assert state == CircuitState.CLOSED

    async def test_call_with_closed_circuit(self):
        """Should allow calls when circuit closed"""
        cb = CircuitBreaker()

        async def successful_call():
            return "success"

        result = await cb.call("agent-1", successful_call)
        assert result == "success"

        metrics = await cb.get_metrics("agent-1")
        assert metrics.successful_requests == 1

    async def test_call_with_open_circuit(self):
        """Should block calls when circuit open"""
        cb = CircuitBreaker(
            failure_threshold=0.5,
            minimum_requests=2,
        )

        # Trip circuit
        await cb.record_failure("agent-1")
        await cb.record_failure("agent-1")

        async def any_call():
            return "result"

        # Should raise CircuitOpenError
        with pytest.raises(CircuitOpenError):
            await cb.call("agent-1", any_call)

    async def test_call_records_failure(self):
        """Should record failure when call raises exception"""
        cb = CircuitBreaker()

        async def failing_call():
            raise ValueError("Call failed")

        with pytest.raises(ValueError):
            await cb.call("agent-1", failing_call)

        metrics = await cb.get_metrics("agent-1")
        assert metrics.failed_requests == 1

    async def test_transition_to_half_open(self):
        """Should transition to half-open after timeout"""
        cb = CircuitBreaker(
            failure_threshold=0.5,
            minimum_requests=2,
            timeout=0.1,  # Short timeout for testing
        )

        # Trip circuit
        await cb.record_failure("agent-1")
        await cb.record_failure("agent-1")

        assert cb.get_state("agent-1") == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(0.15)

        state = cb.get_state("agent-1")
        assert state == CircuitState.HALF_OPEN

    async def test_half_open_success_closes_circuit(self):
        """Should close circuit after successful half-open requests"""
        cb = CircuitBreaker(
            failure_threshold=0.5,
            minimum_requests=2,
            success_threshold=2,
            timeout=0.1,
        )

        # Trip circuit
        await cb.record_failure("agent-1")
        await cb.record_failure("agent-1")

        # Wait for half-open
        await asyncio.sleep(0.15)
        assert cb.get_state("agent-1") == CircuitState.HALF_OPEN

        # Record successes
        await cb.record_success("agent-1")
        await cb.record_success("agent-1")

        state = cb.get_state("agent-1")
        assert state == CircuitState.CLOSED

    async def test_half_open_failure_reopens_circuit(self):
        """Should reopen circuit on half-open failure"""
        cb = CircuitBreaker(
            failure_threshold=0.5,
            minimum_requests=2,
            timeout=0.1,
        )

        # Trip circuit
        await cb.record_failure("agent-1")
        await cb.record_failure("agent-1")

        # Wait for half-open
        await asyncio.sleep(0.15)
        assert cb.get_state("agent-1") == CircuitState.HALF_OPEN

        # Record failure
        await cb.record_failure("agent-1")

        state = cb.get_state("agent-1")
        assert state == CircuitState.OPEN

        metrics = await cb.get_metrics("agent-1")
        assert metrics.trip_count == 2

    async def test_reset_circuit(self):
        """Should reset circuit to closed state"""
        cb = CircuitBreaker(
            failure_threshold=0.5,
            minimum_requests=2,
        )

        # Trip circuit
        await cb.record_failure("agent-1")
        await cb.record_failure("agent-1")

        assert cb.get_state("agent-1") == CircuitState.OPEN

        # Reset
        await cb.reset("agent-1")

        state = cb.get_state("agent-1")
        assert state == CircuitState.CLOSED

        metrics = await cb.get_metrics("agent-1")
        assert metrics.consecutive_successes == 0
        assert metrics.consecutive_failures == 0

    async def test_get_metrics(self):
        """Should retrieve circuit metrics"""
        cb = CircuitBreaker()

        await cb.record_success("agent-1")

        metrics = await cb.get_metrics("agent-1")
        assert metrics is not None
        assert metrics.agent_id == "agent-1"

        # Unknown agent returns None
        metrics = await cb.get_metrics("unknown")
        assert metrics is None

    async def test_get_all_metrics(self):
        """Should retrieve all circuit metrics"""
        cb = CircuitBreaker()

        await cb.record_success("agent-1")
        await cb.record_success("agent-2")

        all_metrics = await cb.get_all_metrics()
        assert len(all_metrics) == 2
        assert "agent-1" in all_metrics
        assert "agent-2" in all_metrics

    async def test_get_open_circuits(self):
        """Should list open circuits"""
        cb = CircuitBreaker(
            failure_threshold=0.5,
            minimum_requests=2,
        )

        # Trip one circuit
        await cb.record_failure("agent-1")
        await cb.record_failure("agent-1")

        # Keep another closed
        await cb.record_success("agent-2")

        open_circuits = await cb.get_open_circuits()
        assert len(open_circuits) == 1
        assert "agent-1" in open_circuits

    async def test_get_half_open_circuits(self):
        """Should list half-open circuits"""
        cb = CircuitBreaker(
            failure_threshold=0.5,
            minimum_requests=2,
            timeout=0.1,
        )

        # Trip circuit
        await cb.record_failure("agent-1")
        await cb.record_failure("agent-1")

        # Wait for half-open
        await asyncio.sleep(0.15)

        half_open = await cb.get_half_open_circuits()
        assert len(half_open) == 1
        assert "agent-1" in half_open

    async def test_multiple_agents(self):
        """Should manage circuits for multiple agents independently"""
        cb = CircuitBreaker(
            failure_threshold=0.5,
            minimum_requests=2,
        )

        # Trip agent-1
        await cb.record_failure("agent-1")
        await cb.record_failure("agent-1")

        # Keep agent-2 closed
        await cb.record_success("agent-2")
        await cb.record_success("agent-2")

        assert cb.get_state("agent-1") == CircuitState.OPEN
        assert cb.get_state("agent-2") == CircuitState.CLOSED

    async def test_consecutive_counters(self):
        """Should track consecutive successes and failures"""
        cb = CircuitBreaker()

        # Consecutive successes
        await cb.record_success("agent-1")
        await cb.record_success("agent-1")
        await cb.record_success("agent-1")

        metrics = await cb.get_metrics("agent-1")
        assert metrics.consecutive_successes == 3
        assert metrics.consecutive_failures == 0

        # Failure resets success counter
        await cb.record_failure("agent-1")

        metrics = await cb.get_metrics("agent-1")
        assert metrics.consecutive_successes == 0
        assert metrics.consecutive_failures == 1

    async def test_last_failure_time(self):
        """Should track last failure time"""
        cb = CircuitBreaker()

        before = time.time()
        await cb.record_failure("agent-1")
        after = time.time()

        metrics = await cb.get_metrics("agent-1")
        assert metrics.last_failure_time is not None
        assert before <= metrics.last_failure_time <= after

    async def test_last_success_time(self):
        """Should track last success time"""
        cb = CircuitBreaker()

        before = time.time()
        await cb.record_success("agent-1")
        after = time.time()

        metrics = await cb.get_metrics("agent-1")
        assert metrics.last_success_time is not None
        assert before <= metrics.last_success_time <= after

    async def test_trip_count(self):
        """Should count circuit trips"""
        cb = CircuitBreaker(
            failure_threshold=0.5,
            minimum_requests=2,
            timeout=0.1,
        )

        # First trip
        await cb.record_failure("agent-1")
        await cb.record_failure("agent-1")

        metrics = await cb.get_metrics("agent-1")
        assert metrics.trip_count == 1

        # Wait for half-open and trip again
        await asyncio.sleep(0.15)
        
        # Should be in half-open state now
        assert cb.get_state("agent-1") == CircuitState.HALF_OPEN
        
        # Record another failure - this should reopen the circuit
        await cb.record_failure("agent-1")
        
        # Verify circuit reopened
        state = cb.get_state("agent-1")
        assert state == CircuitState.OPEN

        metrics = await cb.get_metrics("agent-1")
        assert metrics.trip_count == 2

    async def test_integration_with_health_monitor(self):
        """Should integrate with health monitor"""
        registry = ServiceRegistry()
        monitor = HealthMonitor(registry)
        cb = CircuitBreaker(health_monitor=monitor)

        # Circuit breaker can be created with health monitor
        assert cb._health_monitor is monitor

    async def test_full_lifecycle(self):
        """Should handle full circuit breaker lifecycle"""
        cb = CircuitBreaker(
            failure_threshold=0.6,
            success_threshold=2,
            minimum_requests=5,
            timeout=0.1,
        )

        # Phase 1: Closed - normal operation
        assert cb.get_state("agent-1") == CircuitState.CLOSED

        # Phase 2: Accumulate failures
        await cb.record_success("agent-1")
        await cb.record_failure("agent-1")
        await cb.record_failure("agent-1")
        await cb.record_failure("agent-1")
        await cb.record_failure("agent-1")  # 4/5 = 80% failure rate

        # Phase 3: Circuit opens
        assert cb.get_state("agent-1") == CircuitState.OPEN
        open_circuits = await cb.get_open_circuits()
        assert "agent-1" in open_circuits

        # Phase 4: Calls blocked
        async def test_call():
            return "result"

        with pytest.raises(CircuitOpenError):
            await cb.call("agent-1", test_call)

        # Phase 5: Wait for half-open
        await asyncio.sleep(0.15)
        assert cb.get_state("agent-1") == CircuitState.HALF_OPEN

        # Phase 6: Recovery - successful requests
        await cb.record_success("agent-1")
        await cb.record_success("agent-1")

        # Phase 7: Circuit closes
        assert cb.get_state("agent-1") == CircuitState.CLOSED

        # Phase 8: Verify metrics
        metrics = await cb.get_metrics("agent-1")
        assert metrics.trip_count == 1
        assert metrics.total_requests == 7  # 5 during closed, 2 during half-open

    async def test_different_thresholds(self):
        """Should respect different threshold configurations"""
        # Strict threshold
        strict_cb = CircuitBreaker(
            failure_threshold=0.2,
            minimum_requests=5,
        )

        # 1 failure out of 5 = 20% (meets threshold)
        await strict_cb.record_success("agent-1")
        await strict_cb.record_success("agent-1")
        await strict_cb.record_success("agent-1")
        await strict_cb.record_success("agent-1")
        await strict_cb.record_failure("agent-1")

        assert strict_cb.get_state("agent-1") == CircuitState.OPEN

        # Lenient threshold
        lenient_cb = CircuitBreaker(
            failure_threshold=0.8,
            minimum_requests=5,
        )

        # 1 failure out of 5 = 20% (below threshold)
        await lenient_cb.record_success("agent-2")
        await lenient_cb.record_success("agent-2")
        await lenient_cb.record_success("agent-2")
        await lenient_cb.record_success("agent-2")
        await lenient_cb.record_failure("agent-2")

        assert lenient_cb.get_state("agent-2") == CircuitState.CLOSED
