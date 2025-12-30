"""
Tests for Event Bus Metrics System

Tests comprehensive observability features:
- Event publication tracking
- Delivery latency measurements (p50/p95/p99)
- Subscriber health monitoring
- Throughput calculations
- Error rate tracking
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta

from waooaw.events.metrics import (
    EventMetrics,
    LatencyStats,
    MetricType,
    SubscriberHealth,
    SubscriberMetrics,
    EventTypeMetrics,
)


@pytest.fixture
def metrics():
    """Create EventMetrics instance."""
    return EventMetrics(window_seconds=60)


@pytest.fixture
def sample_latencies():
    """Sample latency values for testing."""
    return [0.01, 0.02, 0.03, 0.05, 0.10, 0.15, 0.20, 0.25, 0.50, 1.0]


# ===== LatencyStats Tests =====

def test_latency_stats_creation():
    """Test LatencyStats creation."""
    stats = LatencyStats(
        count=100,
        min=0.001,
        max=0.5,
        mean=0.05,
        p50=0.04,
        p95=0.2,
        p99=0.4
    )
    
    assert stats.count == 100
    assert stats.min == 0.001
    assert stats.max == 0.5
    assert stats.mean == 0.05
    assert stats.p50 == 0.04
    assert stats.p95 == 0.2
    assert stats.p99 == 0.4


def test_latency_stats_from_samples(sample_latencies):
    """Test calculating stats from samples."""
    stats = LatencyStats.from_samples(sample_latencies)
    
    assert stats.count == 10
    assert stats.min == 0.01
    assert stats.max == 1.0
    assert stats.mean == pytest.approx(0.231, rel=0.01)
    assert stats.p50 == 0.15  # 50th percentile (index 5)
    assert stats.p95 == 1.0   # 95th percentile
    assert stats.p99 == 1.0   # 99th percentile


def test_latency_stats_empty_samples():
    """Test stats with no samples."""
    stats = LatencyStats.from_samples([])
    
    assert stats.count == 0
    assert stats.min == 0.0
    assert stats.max == 0.0
    assert stats.mean == 0.0
    assert stats.p50 == 0.0
    assert stats.p95 == 0.0
    assert stats.p99 == 0.0


def test_latency_stats_single_sample():
    """Test stats with single sample."""
    stats = LatencyStats.from_samples([0.05])
    
    assert stats.count == 1
    assert stats.min == 0.05
    assert stats.max == 0.05
    assert stats.mean == 0.05
    assert stats.p50 == 0.05
    assert stats.p95 == 0.05
    assert stats.p99 == 0.05


# ===== SubscriberMetrics Tests =====

def test_subscriber_metrics_creation():
    """Test SubscriberMetrics creation."""
    metrics = SubscriberMetrics(
        subscriber_id="agent-1",
        patterns={"task.*", "agent.*"}
    )
    
    assert metrics.subscriber_id == "agent-1"
    assert metrics.patterns == {"task.*", "agent.*"}
    assert metrics.total_deliveries == 0
    assert metrics.health == SubscriberHealth.UNKNOWN


def test_subscriber_error_rate():
    """Test error rate calculation."""
    metrics = SubscriberMetrics(subscriber_id="agent-1")
    metrics.total_deliveries = 100
    metrics.successful_deliveries = 90
    metrics.failed_deliveries = 10
    
    assert metrics.error_rate == 0.10


def test_subscriber_avg_latency():
    """Test average latency calculation."""
    metrics = SubscriberMetrics(subscriber_id="agent-1")
    metrics.successful_deliveries = 5
    metrics.total_latency = 0.5
    
    assert metrics.avg_latency == 0.1


def test_subscriber_health_healthy():
    """Test health calculation for healthy subscriber."""
    metrics = SubscriberMetrics(subscriber_id="agent-1")
    metrics.total_deliveries = 100
    metrics.successful_deliveries = 98
    metrics.failed_deliveries = 2
    metrics.total_latency = 5.0  # 0.05s avg
    
    metrics.update_health()
    assert metrics.health == SubscriberHealth.HEALTHY


def test_subscriber_health_degraded():
    """Test health calculation for degraded subscriber."""
    metrics = SubscriberMetrics(subscriber_id="agent-1")
    metrics.total_deliveries = 100
    metrics.successful_deliveries = 92
    metrics.failed_deliveries = 8  # 8% error rate
    metrics.total_latency = 92.0   # 1.0s avg
    
    metrics.update_health()
    assert metrics.health == SubscriberHealth.DEGRADED


def test_subscriber_health_unhealthy():
    """Test health calculation for unhealthy subscriber."""
    metrics = SubscriberMetrics(subscriber_id="agent-1")
    metrics.total_deliveries = 100
    metrics.successful_deliveries = 75
    metrics.failed_deliveries = 25  # 25% error rate
    metrics.total_latency = 450.0   # 6.0s avg
    
    metrics.update_health()
    assert metrics.health == SubscriberHealth.UNHEALTHY


def test_subscriber_health_unknown():
    """Test health for subscriber with no activity."""
    metrics = SubscriberMetrics(subscriber_id="agent-1")
    metrics.update_health()
    assert metrics.health == SubscriberHealth.UNKNOWN


# ===== EventTypeMetrics Tests =====

def test_event_type_metrics_creation():
    """Test EventTypeMetrics creation."""
    metrics = EventTypeMetrics(event_type="task.created")
    
    assert metrics.event_type == "task.created"
    assert metrics.publish_count == 0
    assert metrics.delivery_count == 0


def test_event_type_add_latency():
    """Test adding latency samples."""
    metrics = EventTypeMetrics(event_type="task.created")
    
    metrics.add_latency(0.01)
    metrics.add_latency(0.02)
    metrics.add_latency(0.03)
    
    assert len(metrics.latency_samples) == 3
    assert list(metrics.latency_samples) == [0.01, 0.02, 0.03]


def test_event_type_get_latency_stats():
    """Test getting latency statistics."""
    metrics = EventTypeMetrics(event_type="task.created")
    
    for latency in [0.01, 0.02, 0.05, 0.10, 0.20]:
        metrics.add_latency(latency)
    
    stats = metrics.get_latency_stats()
    assert stats.count == 5
    assert stats.min == 0.01
    assert stats.max == 0.20


# ===== EventMetrics Tests =====

def test_event_metrics_creation():
    """Test EventMetrics creation."""
    metrics = EventMetrics(window_seconds=60)
    
    assert metrics.window_seconds == 60
    assert metrics.total_publishes == 0
    assert metrics.total_deliveries == 0
    assert len(metrics.subscribers) == 0


@pytest.mark.asyncio
async def test_record_publish(metrics):
    """Test recording event publications."""
    await metrics.record_publish("task.created")
    await metrics.record_publish("task.created")
    await metrics.record_publish("agent.started")
    
    assert metrics.total_publishes == 3
    assert metrics.event_types["task.created"].publish_count == 2
    assert metrics.event_types["agent.started"].publish_count == 1


@pytest.mark.asyncio
async def test_record_delivery_success(metrics):
    """Test recording successful deliveries."""
    await metrics.record_delivery("task.created", "agent-1", 0.05, success=True)
    await metrics.record_delivery("task.created", "agent-1", 0.03, success=True)
    
    assert metrics.total_deliveries == 2
    assert metrics.event_types["task.created"].delivery_count == 2
    assert len(metrics.event_types["task.created"].latency_samples) == 2


@pytest.mark.asyncio
async def test_record_delivery_failure(metrics):
    """Test recording failed deliveries."""
    await metrics.record_delivery("task.created", "agent-1", 0.05, success=False)
    
    assert metrics.total_deliveries == 0
    assert metrics.total_errors == 1
    assert metrics.event_types["task.created"].error_count == 1


@pytest.mark.asyncio
async def test_subscriber_registration(metrics):
    """Test subscriber registration."""
    await metrics.register_subscriber("agent-1", {"task.*", "agent.*"})
    
    assert "agent-1" in metrics.subscribers
    assert metrics.subscribers["agent-1"].patterns == {"task.*", "agent.*"}


@pytest.mark.asyncio
async def test_subscriber_unregistration(metrics):
    """Test subscriber unregistration."""
    await metrics.register_subscriber("agent-1", {"task.*"})
    assert "agent-1" in metrics.subscribers
    
    await metrics.unregister_subscriber("agent-1")
    assert "agent-1" not in metrics.subscribers


@pytest.mark.asyncio
async def test_record_error(metrics):
    """Test recording errors."""
    await metrics.record_error("task.created")
    await metrics.record_error("task.created")
    
    assert metrics.total_errors == 2
    assert metrics.event_types["task.created"].error_count == 2


@pytest.mark.asyncio
async def test_record_retry(metrics):
    """Test recording retries."""
    await metrics.record_retry("task.created")
    
    assert metrics.total_retries == 1
    assert metrics.event_types["task.created"].retry_count == 1


@pytest.mark.asyncio
async def test_record_dlq(metrics):
    """Test recording DLQ events."""
    await metrics.record_dlq("task.created")
    
    assert metrics.total_dlq == 1
    assert metrics.event_types["task.created"].dlq_count == 1


@pytest.mark.asyncio
async def test_get_metrics_comprehensive(metrics):
    """Test getting comprehensive metrics."""
    # Record some activity
    await metrics.record_publish("task.created")
    await metrics.record_publish("agent.started")
    await metrics.record_delivery("task.created", "agent-1", 0.05, success=True)
    await metrics.record_delivery("agent.started", "agent-2", 0.03, success=True)
    await metrics.register_subscriber("agent-1", {"task.*"})
    await metrics.register_subscriber("agent-2", {"agent.*"})
    
    snapshot = await metrics.get_metrics()
    
    assert "timestamp" in snapshot
    assert "uptime_seconds" in snapshot
    assert snapshot["totals"]["publishes"] == 2
    assert snapshot["totals"]["deliveries"] == 2
    assert snapshot["subscribers"]["total"] == 2
    assert "task.created" in snapshot["event_types"]
    assert "agent.started" in snapshot["event_types"]


@pytest.mark.asyncio
async def test_get_subscriber_metrics(metrics):
    """Test getting subscriber-specific metrics."""
    await metrics.register_subscriber("agent-1", {"task.*"})
    await metrics.record_delivery("task.created", "agent-1", 0.05, success=True)
    await metrics.record_delivery("task.updated", "agent-1", 0.03, success=True)
    
    sub_metrics = await metrics.get_subscriber_metrics("agent-1")
    
    assert sub_metrics is not None
    assert sub_metrics["subscriber_id"] == "agent-1"
    assert sub_metrics["total_deliveries"] == 2
    assert sub_metrics["successful_deliveries"] == 2
    assert sub_metrics["health"] == "healthy"


@pytest.mark.asyncio
async def test_get_subscriber_metrics_nonexistent(metrics):
    """Test getting metrics for nonexistent subscriber."""
    sub_metrics = await metrics.get_subscriber_metrics("nonexistent")
    assert sub_metrics is None


@pytest.mark.asyncio
async def test_get_unhealthy_subscribers(metrics):
    """Test getting list of unhealthy subscribers."""
    await metrics.register_subscriber("agent-1", {"task.*"})
    await metrics.register_subscriber("agent-2", {"agent.*"})
    
    # Make agent-1 unhealthy (25% error rate)
    for _ in range(75):
        await metrics.record_delivery("task.created", "agent-1", 0.05, success=True)
    for _ in range(25):
        await metrics.record_delivery("task.created", "agent-1", 0.05, success=False)
    
    # Keep agent-2 healthy
    await metrics.record_delivery("agent.started", "agent-2", 0.05, success=True)
    
    unhealthy = await metrics.get_unhealthy_subscribers()
    assert "agent-1" in unhealthy
    assert "agent-2" not in unhealthy


@pytest.mark.asyncio
async def test_throughput_calculation(metrics):
    """Test throughput calculations."""
    # Record events
    for _ in range(10):
        await metrics.record_publish("task.created")
        await asyncio.sleep(0.01)  # Small delay
    
    snapshot = await metrics.get_metrics()
    
    # Check throughput structure
    assert "throughput" in snapshot
    assert "publishes" in snapshot["throughput"]
    assert "count" in snapshot["throughput"]["publishes"]
    assert "per_second" in snapshot["throughput"]["publishes"]
    assert "per_minute" in snapshot["throughput"]["publishes"]


@pytest.mark.asyncio
async def test_latency_percentiles(metrics):
    """Test latency percentile calculations."""
    latencies = [0.01, 0.02, 0.03, 0.05, 0.10, 0.15, 0.20, 0.25, 0.50, 1.0]
    
    for latency in latencies:
        await metrics.record_delivery("task.created", "agent-1", latency, success=True)
    
    snapshot = await metrics.get_metrics()
    
    assert "latency" in snapshot
    assert snapshot["latency"]["count"] == 10
    assert snapshot["latency"]["p50"] > 0
    assert snapshot["latency"]["p95"] > 0
    assert snapshot["latency"]["p99"] > 0
    assert snapshot["latency"]["p95"] >= snapshot["latency"]["p50"]


@pytest.mark.asyncio
async def test_reset_metrics(metrics):
    """Test resetting all metrics."""
    # Record some activity
    await metrics.record_publish("task.created")
    await metrics.record_delivery("task.created", "agent-1", 0.05, success=True)
    await metrics.register_subscriber("agent-1", {"task.*"})
    
    assert metrics.total_publishes > 0
    assert len(metrics.subscribers) > 0
    
    # Reset
    await metrics.reset()
    
    assert metrics.total_publishes == 0
    assert metrics.total_deliveries == 0
    assert len(metrics.subscribers) == 0
    assert len(metrics.event_types) == 0


@pytest.mark.asyncio
async def test_concurrent_metric_recording(metrics):
    """Test thread-safety with concurrent recordings."""
    async def record_activity():
        for _ in range(10):
            await metrics.record_publish("task.created")
            await metrics.record_delivery("task.created", "agent-1", 0.05, success=True)
    
    # Run multiple concurrent tasks
    await asyncio.gather(*[record_activity() for _ in range(5)])
    
    assert metrics.total_publishes == 50
    assert metrics.total_deliveries == 50


@pytest.mark.asyncio
async def test_event_type_metrics_aggregation(metrics):
    """Test metrics aggregation by event type."""
    # Record different event types
    await metrics.record_publish("task.created")
    await metrics.record_publish("task.updated")
    await metrics.record_publish("agent.started")
    
    await metrics.record_delivery("task.created", "agent-1", 0.05, success=True)
    await metrics.record_delivery("task.updated", "agent-1", 0.03, success=True)
    
    snapshot = await metrics.get_metrics()
    
    assert "task.created" in snapshot["event_types"]
    assert "task.updated" in snapshot["event_types"]
    assert "agent.started" in snapshot["event_types"]
    
    assert snapshot["event_types"]["task.created"]["publishes"] == 1
    assert snapshot["event_types"]["task.created"]["deliveries"] == 1
    assert snapshot["event_types"]["agent.started"]["deliveries"] == 0


@pytest.mark.asyncio
async def test_subscriber_health_tracking_over_time(metrics):
    """Test subscriber health changes over time."""
    await metrics.register_subscriber("agent-1", {"task.*"})
    
    # Start healthy
    for _ in range(100):
        await metrics.record_delivery("task.created", "agent-1", 0.05, success=True)
    
    sub_metrics = await metrics.get_subscriber_metrics("agent-1")
    assert sub_metrics["health"] == "healthy"
    
    # Degrade
    for _ in range(10):
        await metrics.record_delivery("task.created", "agent-1", 0.05, success=False)
    
    sub_metrics = await metrics.get_subscriber_metrics("agent-1")
    assert sub_metrics["health"] == "degraded"
