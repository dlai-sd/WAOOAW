"""
Integration Tests for Event Bus System

End-to-end tests validating component integration:
- Schema Validation + DLQ + Metrics
- Event Store + Replay + Metrics
- Multi-component workflows

Note: These tests focus on component integration patterns without requiring actual Redis.
Unit tests for EventBus pub/sub exist in test_event_bus.py.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from waooaw.events import (
    Event,
    EventType,
    EventSchema,
    EventValidator,
    SchemaRegistry,
    DeadLetterQueue,
    FailureReason,
    EventStore,
    EventReplayer,
    ReplayConfig,
    EventMetrics,
    SubscriberHealth,
)


@pytest.fixture
def schema_registry():
    """Create SchemaRegistry with custom schemas."""
    registry = SchemaRegistry()
    
    # Add custom task schema
    task_schema = EventSchema(
        event_type="task.created",
        version="1.0.0",
        description="Task created schema",
        json_schema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "title": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high"]}
            },
            "required": ["task_id", "title"]
        }
    )
    registry.register_schema(task_schema)
    
    return registry


@pytest.fixture
def event_validator(schema_registry):
    """Create EventValidator."""
    return EventValidator(registry=schema_registry)


@pytest.fixture
def dlq():
    """Create DeadLetterQueue."""
    return DeadLetterQueue()


@pytest.fixture
def event_store():
    """Create EventStore."""
    return EventStore(max_size=1000)


@pytest.fixture
def event_metrics():
    """Create EventMetrics."""
    return EventMetrics(window_seconds=60)


# ===== Validation + DLQ + Metrics Integration =====

@pytest.mark.asyncio
async def test_validation_dlq_metrics_pipeline(
    event_validator,
    dlq,
    event_metrics
):
    """Test validation → DLQ → metrics integration."""
    # Valid event
    valid_event = Event(
        event_type="task.created",
        source_agent="agent-1",
        payload={"task_id": "task-123", "title": "Valid Task", "priority": "high"}
    )
    
    # Invalid event (missing required field)
    invalid_event = Event(
        event_type="task.created",
        source_agent="agent-1",
        payload={"task_id": "task-456"}  # Missing "title"
    )
    
    # Process both events
    for event in [valid_event, invalid_event]:
        await event_metrics.record_publish(event.event_type)
        
        # Validate
        try:
            is_valid = event_validator.validate_event(event)
            # Success path
            await event_metrics.record_delivery(event.event_type, "processor", 0.05, True)
        except Exception as error:
            # Failure path → DLQ
            await dlq.add_failed_event(
                event,
                "sub-123",
                "processor-agent",
                FailureReason.VALIDATION_ERROR,
                str(error)
            )
            await event_metrics.record_error(event.event_type)
            # Note: Failed delivery recorded as unsuccessful, not as separate delivery
            # await event_metrics.record_delivery(event.event_type, "processor", 0.05, False)
    
    # Verify DLQ has failed event (in retry queue or dead letters)
    retry_queue = dlq.get_retry_queue()
    dead_letters = dlq.get_dead_letters()
    assert len(retry_queue) + len(dead_letters) == 1
    
    # Verify metrics
    metrics = await event_metrics.get_metrics()
    assert metrics["totals"]["publishes"] == 2
    assert metrics["totals"]["deliveries"] == 1  # Only valid one succeeded
    assert metrics["totals"]["errors"] == 1


@pytest.mark.asyncio
async def test_dlq_retry_metrics_integration(dlq, event_metrics):
    """Test DLQ retry tracking with metrics."""
    event = Event(
        event_type="task.updated",
        source_agent="agent-1",
        payload={"task_id": "task-789"}
    )
    
    # Add to DLQ
    await dlq.add_failed_event(
        event,
        "sub-456",
        "worker-agent",
        FailureReason.HANDLER_ERROR,
        "Temporary failure"
    )
    await event_metrics.record_error(event.event_type)
    
    # Get from retry queue
    retry_queue = dlq.get_retry_queue()
    assert len(retry_queue) == 1
    
    # Simulate 3 retry attempts
    for i in range(3):
        await event_metrics.record_retry(event.event_type)
    
    # Verify metrics
    metrics = await event_metrics.get_metrics()
    assert metrics["totals"]["retries"] == 3
    assert metrics["totals"]["errors"] >= 1


# ===== Event Store + Replay + Metrics Integration =====

@pytest.mark.asyncio
async def test_store_replay_metrics_integration(event_store, event_metrics):
    """Test event storage, replay, and metrics tracking."""
    # Store events
    for i in range(5):
        event = Event(
            event_type="task.created",
            source_agent=f"agent-{i}",
            payload={"task_id": f"task-{i}"}
        )
        event_store.store(event)
        await event_metrics.record_publish(event.event_type)
    
    # Replay events with metrics
    replayed_count = 0
    
    async def replay_handler(event: Event):
        nonlocal replayed_count
        replayed_count += 1
        await event_metrics.record_delivery(event.event_type, "replay-handler", 0.01, True)
    
    replayer = EventReplayer(event_store)
    config = ReplayConfig(speed_multiplier=0)  # Instant replay
    
    await replayer.replay(replay_handler, config)
    
    # Verify replay
    assert replayed_count == 5
    
    # Verify metrics
    metrics = await event_metrics.get_metrics()
    assert metrics["totals"]["publishes"] == 5
    assert metrics["totals"]["deliveries"] == 5


@pytest.mark.asyncio
async def test_catch_up_metrics_integration(event_store, event_metrics):
    """Test agent catch-up with metrics."""
    downtime_start = datetime.now() - timedelta(minutes=10)
    
    # Store events during downtime
    for i in range(3):
        event = Event(
            event_type="task.updated",
            source_agent="other-agent",
            payload={"task_id": f"task-{i}"},
            timestamp=(downtime_start + timedelta(minutes=i)).isoformat()
        )
        event_store.store(event)
    
    # Agent catches up
    caught_up = []
    
    async def catch_up_handler(event: Event):
        caught_up.append(event)
        await event_metrics.record_delivery(event.event_type, "recovering-agent", 0.02, True)
    
    replayer = EventReplayer(event_store)
    await replayer.catch_up(catch_up_handler, downtime_start.isoformat(), pattern="task.*")
    
    # Verify catch-up
    assert len(caught_up) == 3
    
    # Verify metrics
    metrics = await event_metrics.get_metrics()
    assert metrics["totals"]["deliveries"] == 3


# ===== Multi-Component Workflow Tests =====

@pytest.mark.asyncio
async def test_complete_event_lifecycle(
    event_validator,
    dlq,
    event_store,
    event_metrics
):
    """Test complete event lifecycle: validate → store → metrics → DLQ if failed."""
    events = [
        Event(event_type="task.created", source_agent="api", payload={"task_id": "1", "title": "Valid"}),
        Event(event_type="task.created", source_agent="api", payload={"task_id": "2"}),  # Invalid
        Event(event_type="task.updated", source_agent="api", payload={"task_id": "3", "status": "done"}),
    ]
    
    processed_count = 0
    stored_count = 0
    dlq_count = 0
    
    for event in events:
        await event_metrics.record_publish(event.event_type)
        
        # Validate
        try:
            event_validator.validate_event(event)
            # Store valid events
            event_store.store(event)
            stored_count += 1
            await event_metrics.record_delivery(event.event_type, "processor", 0.05, True)
            processed_count += 1
        except Exception as error:
            # Invalid → DLQ
            await dlq.add_failed_event(
                event,
                "sub-789",
                "processor",
                FailureReason.VALIDATION_ERROR,
                str(error)
            )
            dlq_count += 1
            await event_metrics.record_error(event.event_type)
            await event_metrics.record_dlq(event.event_type)
    
    # Verify end-to-end
    assert processed_count >= 1  # At least one valid event
    assert stored_count >= 1
    assert dlq_count >= 1
    
    # Verify storage
    stored_events = event_store.get_events()
    assert len(stored_events) == stored_count
    
    # Verify DLQ
    retry_queue = dlq.get_retry_queue()
    dead_letters = dlq.get_dead_letters()
    assert len(retry_queue) + len(dead_letters) == dlq_count
    
    # Verify metrics
    metrics = await event_metrics.get_metrics()
    assert metrics["totals"]["publishes"] == len(events)
    assert metrics["totals"]["deliveries"] >= 1
    assert metrics["totals"]["errors"] >= 1
    assert metrics["totals"]["dlq"] >= 1


@pytest.mark.asyncio
async def test_subscriber_health_with_errors(event_metrics, dlq):
    """Test subscriber health tracking with mixed success/failure."""
    # Healthy subscriber
    for i in range(100):
        await event_metrics.record_delivery("task.created", "healthy-agent", 0.01, True)
    
    # Unhealthy subscriber (high error rate)
    for i in range(50):
        success = i % 3 != 0  # 33% error rate
        await event_metrics.record_delivery("task.created", "unhealthy-agent", 0.05, success)
        if not success:
            event = Event(event_type="task.created", source_agent="test", payload={"task_id": str(i)})
            await dlq.add_failed_event(event, "sub-unhealthy", "unhealthy-agent", FailureReason.HANDLER_ERROR, "Failed")
    
    # Check health
    healthy_metrics = await event_metrics.get_subscriber_metrics("healthy-agent")
    unhealthy_metrics = await event_metrics.get_subscriber_metrics("unhealthy-agent")
    
    assert healthy_metrics["health"] == "healthy"
    assert unhealthy_metrics["health"] in ["degraded", "unhealthy"]
    
    # Get unhealthy list
    unhealthy_list = await event_metrics.get_unhealthy_subscribers()
    assert "unhealthy-agent" in unhealthy_list


@pytest.mark.asyncio
async def test_metrics_aggregation_across_components(
    event_validator,
    dlq,
    event_store,
    event_metrics
):
    """Test metrics aggregation from multiple components."""
    # Simulate activity across all components
    
    # Publications
    for i in range(10):
        await event_metrics.record_publish("test.event")
    
    # Validations (some fail)
    valid_event = Event(event_type="task.created", source_agent="api", payload={"task_id": "1", "title": "Test"})
