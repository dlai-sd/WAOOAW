"""
Tests for WowEvent Core - Event Bus

Story 1: WowEvent Core (Epic 3.1)
Coverage: Event lifecycle, pub/sub, pattern matching, routing
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from waooaw.events.event_bus import (
    Event,
    EventBus,
    EventType,
    EventPriority,
    Subscription,
)


@pytest.fixture
def redis_url():
    """Redis URL for tests"""
    return "redis://localhost:6379"


@pytest.fixture
def event_bus(redis_url):
    """Event bus instance"""
    return EventBus(redis_url=redis_url, channel_prefix="test:events:")


@pytest.fixture
def sample_event():
    """Sample event for testing"""
    return Event(
        event_type=EventType.TASK_COMPLETED,
        source_agent="did:waooaw:agent:marketing",
        payload={"task_id": "task-123", "result": "success"},
    )


# Test Event data structure
def test_event_creation():
    """Test creating an event"""
    event = Event(
        event_type=EventType.AGENT_STARTED,
        source_agent="did:waooaw:agent:test",
        payload={"status": "ready"},
    )

    assert event.event_type == EventType.AGENT_STARTED
    assert event.source_agent == "did:waooaw:agent:test"
    assert event.payload == {"status": "ready"}
    assert event.event_id is not None
    assert event.timestamp is not None
    assert event.priority == EventPriority.NORMAL


def test_event_with_priority():
    """Test event with custom priority"""
    event = Event(
        event_type=EventType.SYSTEM_ALERT,
        source_agent="did:waooaw:system",
        payload={"alert": "high_cpu"},
        priority=EventPriority.CRITICAL,
    )

    assert event.priority == EventPriority.CRITICAL


def test_event_to_dict():
    """Test converting event to dictionary"""
    event = Event(
        event_type=EventType.TASK_COMPLETED,
        source_agent="did:waooaw:agent:test",
        payload={"result": "success"},
    )

    event_dict = event.to_dict()

    assert event_dict["event_type"] == "task.completed"
    assert event_dict["source_agent"] == "did:waooaw:agent:test"
    assert event_dict["payload"] == {"result": "success"}
    assert event_dict["priority"] == 1  # NORMAL


def test_event_from_dict():
    """Test creating event from dictionary"""
    event_dict = {
        "event_id": "evt-123",
        "event_type": "task.completed",
        "source_agent": "did:waooaw:agent:test",
        "payload": {"result": "success"},
        "timestamp": "2025-01-01T00:00:00Z",
        "priority": 1,
    }

    event = Event.from_dict(event_dict)

    assert event.event_id == "evt-123"
    assert event.event_type == EventType.TASK_COMPLETED
    assert event.source_agent == "did:waooaw:agent:test"
    assert event.priority == EventPriority.NORMAL


# Test EventBus initialization
def test_event_bus_creation(event_bus):
    """Test creating event bus"""
    assert event_bus.redis_url == "redis://localhost:6379"
    assert event_bus.channel_prefix == "test:events:"
    assert event_bus.running is False
    assert event_bus.events_published == 0
    assert event_bus.events_delivered == 0


@pytest.mark.asyncio
@patch("redis.asyncio.from_url")
async def test_start_event_bus(mock_redis, event_bus):
    """Test starting the event bus"""
    # Mock Redis client
    mock_client = AsyncMock()
    mock_pubsub = AsyncMock()
    mock_pubsub.close = AsyncMock()
    mock_pubsub.listen = AsyncMock(return_value=iter([]))
    mock_client.pubsub = MagicMock(return_value=mock_pubsub)
    mock_redis.return_value = mock_client

    await event_bus.start()

    assert event_bus.running is True
    assert event_bus.redis_client is not None
    assert event_bus.redis_pubsub is not None
    assert event_bus.listener_task is not None

    # Cleanup
    await event_bus.stop()


@pytest.mark.asyncio
@patch("redis.asyncio.from_url")
async def test_publish_event(mock_redis, event_bus, sample_event):
    """Test publishing an event"""
    # Mock Redis client
    mock_client = AsyncMock()
    mock_pubsub = AsyncMock()
    mock_pubsub.close = AsyncMock()
    mock_pubsub.listen = AsyncMock(return_value=iter([]))
    mock_client.pubsub = MagicMock(return_value=mock_pubsub)
    mock_client.publish = AsyncMock(return_value=1)
    mock_redis.return_value = mock_client

    await event_bus.start()

    # Publish event
    result = await event_bus.publish(sample_event)

    assert result is True
    assert event_bus.events_published == 1

    # Verify Redis publish was called
    mock_client.publish.assert_called_once()

    # Cleanup
    await event_bus.stop()


@pytest.mark.asyncio
async def test_publish_without_start(event_bus, sample_event):
    """Test publishing without starting event bus raises error"""
    with pytest.raises(RuntimeError, match="Event bus is not running"):
        await event_bus.publish(sample_event)


@pytest.mark.asyncio
@patch("redis.asyncio.from_url")
async def test_subscribe_to_pattern(mock_redis, event_bus):
    """Test subscribing to event pattern"""
    # Mock Redis client
    mock_client = AsyncMock()
    mock_pubsub = AsyncMock()
    mock_pubsub.close = AsyncMock()
    mock_pubsub.listen = AsyncMock(return_value=iter([]))
    mock_pubsub.psubscribe = AsyncMock()
    mock_client.pubsub = MagicMock(return_value=mock_pubsub)
    mock_redis.return_value = mock_client

    await event_bus.start()

    # Create handler
    handler = AsyncMock()

    # Subscribe
    subscription = await event_bus.subscribe(
        pattern="task.*",
        handler=handler,
        subscriber_agent="did:waooaw:agent:test",
    )

    assert subscription.pattern == "task.*"
    assert subscription.subscriber_agent == "did:waooaw:agent:test"
    assert event_bus.subscription_count == 1

    # Verify Redis psubscribe was called
    mock_pubsub.psubscribe.assert_called_once_with("test:events:task.*")

    # Cleanup
    await event_bus.stop()


@pytest.mark.asyncio
@patch("redis.asyncio.from_url")
async def test_unsubscribe(mock_redis, event_bus):
    """Test unsubscribing from events"""
    # Mock Redis client
    mock_client = AsyncMock()
    mock_pubsub = AsyncMock()
    mock_pubsub.close = AsyncMock()
    mock_pubsub.listen = AsyncMock(return_value=iter([]))
    mock_pubsub.psubscribe = AsyncMock()
    mock_pubsub.punsubscribe = AsyncMock()
    mock_client.pubsub = MagicMock(return_value=mock_pubsub)
    mock_redis.return_value = mock_client

    await event_bus.start()

    # Subscribe
    handler = AsyncMock()
    subscription = await event_bus.subscribe(
        pattern="task.*",
        handler=handler,
        subscriber_agent="did:waooaw:agent:test",
    )

    # Unsubscribe
    result = await event_bus.unsubscribe(subscription.subscription_id)

    assert result is True
    assert event_bus.subscription_count == 0

    # Verify Redis punsubscribe was called
    mock_pubsub.punsubscribe.assert_called_once_with("test:events:task.*")

    # Cleanup
    await event_bus.stop()


@pytest.mark.asyncio
@patch("redis.asyncio.from_url")
async def test_route_event_to_handler(mock_redis, event_bus, sample_event):
    """Test routing event to matching handler"""
    # Create handler that records calls
    received_events = []

    async def handler(event: Event):
        received_events.append(event)

    # Setup subscription
    subscription = Subscription(
        subscription_id="sub-123",
        subscriber_agent="did:waooaw:agent:test",
        pattern="task.*",
        handler=handler,
        active=True,
    )

    event_bus.subscriptions["sub-123"] = subscription
    event_bus.pattern_to_subscriptions["task.*"].add("sub-123")

    # Route event
    await event_bus._route_event("task.*", sample_event)

    # Verify handler was called
    assert len(received_events) == 1
    assert received_events[0].event_id == sample_event.event_id
    assert event_bus.events_delivered == 1


@pytest.mark.asyncio
@patch("redis.asyncio.from_url")
async def test_get_stats(mock_redis, event_bus):
    """Test getting event bus statistics"""
    # Mock Redis client
    mock_client = AsyncMock()
    mock_pubsub = AsyncMock()
    mock_pubsub.close = AsyncMock()
    mock_pubsub.listen = AsyncMock(return_value=iter([]))
    mock_pubsub.psubscribe = AsyncMock()
    mock_client.pubsub = MagicMock(return_value=mock_pubsub)
    mock_redis.return_value = mock_client

    await event_bus.start()

    # Subscribe to some patterns
    handler1 = AsyncMock()
    handler2 = AsyncMock()

    await event_bus.subscribe(
        pattern="task.*",
        handler=handler1,
        subscriber_agent="did:waooaw:agent:agent1",
    )

    await event_bus.subscribe(
        pattern="agent.*",
        handler=handler2,
        subscriber_agent="did:waooaw:agent:agent2",
    )

    # Get stats
    stats = event_bus.get_stats()

    assert stats["running"] is True
    assert stats["active_subscriptions"] == 2
    assert "task.*" in stats["patterns"]
    assert "agent.*" in stats["patterns"]

    # Cleanup
    await event_bus.stop()
