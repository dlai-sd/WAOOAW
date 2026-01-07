"""
Tests for Event Replay

Story 4: Event Replay (Epic 3.1)
Coverage: Event storage, replay, catch-up, time travel
"""

import asyncio
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from waooaw.events.event_bus import Event, EventType
from waooaw.events.replay import (
    EventStore,
    EventReplayer,
    ReplayConfig,
)


@pytest.fixture
def event_store():
    """Event store instance"""
    return EventStore(max_size=100)


@pytest.fixture
def sample_events():
    """Sample events for testing"""
    now = datetime.now(timezone.utc)

    events = []
    for i in range(5):
        event_time = now + timedelta(seconds=i)
        event = Event(
            event_type=EventType.TASK_COMPLETED if i % 2 == 0 else EventType.AGENT_STARTED,
            source_agent=f"did:waooaw:agent:agent{i}",
            payload={"index": i},
        )
        event.timestamp = event_time.isoformat()
        events.append(event)

    return events


@pytest.fixture
def replayer(event_store):
    """Event replayer instance"""
    return EventReplayer(event_store)


# Test EventStore
def test_event_store_creation():
    """Test creating an event store"""
    store = EventStore(max_size=50)

    assert store.max_size == 50
    assert len(store.events) == 0
    assert store.total_stored == 0


def test_store_event(event_store, sample_events):
    """Test storing an event"""
    event = sample_events[0]
    event_store.store(event)

    assert len(event_store.events) == 1
    assert event_store.total_stored == 1


def test_store_multiple_events(event_store, sample_events):
    """Test storing multiple events"""
    for event in sample_events:
        event_store.store(event)

    assert len(event_store.events) == 5
    assert event_store.total_stored == 5


def test_store_events_fifo_eviction(sample_events):
    """Test FIFO eviction when max size exceeded"""
    store = EventStore(max_size=3)

    # Store 5 events (should keep only last 3)
    for event in sample_events:
        store.store(event)

    assert len(store.events) == 3
    assert store.total_stored == 5

    # Should have events 2, 3, 4 (0-indexed)
    assert store.events[0].payload["index"] == 2
    assert store.events[1].payload["index"] == 3
    assert store.events[2].payload["index"] == 4


def test_get_events_no_filter(event_store, sample_events):
    """Test getting all events"""
    for event in sample_events:
        event_store.store(event)

    events = event_store.get_events()

    assert len(events) == 5


def test_get_events_by_time_range(event_store, sample_events):
    """Test getting events in time range"""
    for event in sample_events:
        event_store.store(event)

    # Get events from index 1 to 3
    start_time = sample_events[1].timestamp
    end_time = sample_events[3].timestamp

    events = event_store.get_events(start_time=start_time, end_time=end_time)

    # Should get events 1, 2, 3
    assert len(events) == 3


def test_get_events_by_pattern(event_store, sample_events):
    """Test getting events by type pattern"""
    for event in sample_events:
        event_store.store(event)

    # Get only task.completed events (even indices)
    events = event_store.get_events(pattern="task.*")

    assert len(events) == 3  # Events 0, 2, 4


def test_get_events_with_max_limit(event_store, sample_events):
    """Test max events limit"""
    for event in sample_events:
        event_store.store(event)

    events = event_store.get_events(max_events=2)

    assert len(events) == 2


def test_get_events_since(event_store, sample_events):
    """Test getting events since timestamp"""
    for event in sample_events:
        event_store.store(event)

    # Get events since index 2
    since_time = sample_events[2].timestamp

    events = event_store.get_events_since(since_time)

    # Should get events 2, 3, 4
    assert len(events) == 3


def test_get_events_by_type(event_store, sample_events):
    """Test getting events by specific type"""
    for event in sample_events:
        event_store.store(event)

    task_events = event_store.get_events_by_type("task.completed")
    agent_events = event_store.get_events_by_type("agent.started")

    assert len(task_events) == 3  # Events 0, 2, 4
    assert len(agent_events) == 2  # Events 1, 3


def test_get_latest_events(event_store, sample_events):
    """Test getting latest events"""
    for event in sample_events:
        event_store.store(event)

    latest = event_store.get_latest_events(count=2)

    assert len(latest) == 2
    assert latest[0].payload["index"] == 3
    assert latest[1].payload["index"] == 4


def test_clear_event_store(event_store, sample_events):
    """Test clearing event store"""
    for event in sample_events:
        event_store.store(event)

    count = event_store.clear()

    assert count == 5
    assert len(event_store.events) == 0


def test_event_store_stats(event_store, sample_events):
    """Test getting event store statistics"""
    for event in sample_events:
        event_store.store(event)

    stats = event_store.get_stats()

    assert stats["current_size"] == 5
    assert stats["max_size"] == 100
    assert stats["total_stored"] == 5
    assert stats["oldest_event"] is not None
    assert stats["newest_event"] is not None


def test_pattern_matching_exact():
    """Test exact pattern matching"""
    store = EventStore()

    assert store._matches_pattern("task.completed", "task.completed") is True
    assert store._matches_pattern("task.started", "task.completed") is False


def test_pattern_matching_wildcard():
    """Test wildcard pattern matching"""
    store = EventStore()

    assert store._matches_pattern("task.completed", "task.*") is True
    assert store._matches_pattern("task.started", "task.*") is True
    assert store._matches_pattern("agent.started", "task.*") is False


def test_pattern_matching_all():
    """Test match-all pattern"""
    store = EventStore()

    assert store._matches_pattern("task.completed", "*") is True
    assert store._matches_pattern("agent.started", "*") is True
    assert store._matches_pattern("anything", "*") is True


# Test EventReplayer
def test_replayer_creation(event_store):
    """Test creating an event replayer"""
    replayer = EventReplayer(event_store)

    assert replayer.event_store == event_store
    assert len(replayer.active_replays) == 0


@pytest.mark.asyncio
async def test_replay_events(event_store, sample_events, replayer):
    """Test replaying events"""
    # Store events
    for event in sample_events:
        event_store.store(event)

    # Create handler that records calls
    received_events = []

    async def handler(event: Event):
        received_events.append(event)

    # Replay all events (instant)
    config = ReplayConfig(speed_multiplier=0)
    count = await replayer.replay(handler, config)

    assert count == 5
    assert len(received_events) == 5


@pytest.mark.asyncio
async def test_replay_with_time_filter(event_store, sample_events, replayer):
    """Test replaying events with time filter"""
    for event in sample_events:
        event_store.store(event)

    received_events = []

    async def handler(event: Event):
        received_events.append(event)

    # Replay only events 2-4
    config = ReplayConfig(
        start_time=sample_events[2].timestamp,
        end_time=sample_events[4].timestamp,
        speed_multiplier=0,
    )

    count = await replayer.replay(handler, config)

    assert count == 3
    assert len(received_events) == 3


@pytest.mark.asyncio
async def test_replay_with_pattern_filter(event_store, sample_events, replayer):
    """Test replaying events with pattern filter"""
    for event in sample_events:
        event_store.store(event)

    received_events = []

    async def handler(event: Event):
        received_events.append(event)

    # Replay only task.* events
    config = ReplayConfig(pattern="task.*", speed_multiplier=0)

    count = await replayer.replay(handler, config)

    assert count == 3  # Events 0, 2, 4


@pytest.mark.asyncio
async def test_replay_with_max_events(event_store, sample_events, replayer):
    """Test replaying with max events limit"""
    for event in sample_events:
        event_store.store(event)

    received_events = []

    async def handler(event: Event):
        received_events.append(event)

    config = ReplayConfig(max_events=2, speed_multiplier=0)

    count = await replayer.replay(handler, config)

    assert count == 2


@pytest.mark.asyncio
async def test_replay_no_events(event_store, replayer):
    """Test replaying when no events match"""
    received_events = []

    async def handler(event: Event):
        received_events.append(event)

    config = ReplayConfig(speed_multiplier=0)

    count = await replayer.replay(handler, config)

    assert count == 0


@pytest.mark.asyncio
async def test_replay_with_sync_handler(event_store, sample_events, replayer):
    """Test replaying with synchronous handler"""
    for event in sample_events:
        event_store.store(event)

    received_events = []

    def sync_handler(event: Event):
        received_events.append(event)

    config = ReplayConfig(speed_multiplier=0)

    count = await replayer.replay(sync_handler, config)

    assert count == 5


@pytest.mark.asyncio
async def test_replay_with_handler_error(event_store, sample_events, replayer):
    """Test replaying continues despite handler errors"""
    for event in sample_events:
        event_store.store(event)

    call_count = 0

    async def failing_handler(event: Event):
        nonlocal call_count
        call_count += 1
        raise Exception("Handler error")

    config = ReplayConfig(speed_multiplier=0)

    count = await replayer.replay(failing_handler, config)

    # Should attempt all events despite errors
    assert call_count == 5
    assert count == 0  # But none succeed


@pytest.mark.asyncio
async def test_replay_async(event_store, sample_events, replayer):
    """Test asynchronous replay (non-blocking)"""
    for event in sample_events:
        event_store.store(event)

    received_events = []

    async def handler(event: Event):
        received_events.append(event)
        await asyncio.sleep(0.01)  # Simulate processing

    config = ReplayConfig(speed_multiplier=0)

    replay_id = await replayer.replay_async(handler, config)

    assert replay_id is not None
    assert replay_id in replayer.active_replays

    # Wait for replay to complete
    await asyncio.sleep(0.2)


@pytest.mark.asyncio
async def test_cancel_replay(event_store, sample_events, replayer):
    """Test cancelling an active replay"""
    for event in sample_events:
        event_store.store(event)

    async def slow_handler(event: Event):
        await asyncio.sleep(1)  # Slow processing

    config = ReplayConfig(speed_multiplier=0)

    replay_id = await replayer.replay_async(slow_handler, config)

    # Cancel immediately
    result = await replayer.cancel_replay(replay_id)

    assert result is True
    assert replay_id not in replayer.active_replays


@pytest.mark.asyncio
async def test_cancel_nonexistent_replay(replayer):
    """Test cancelling a replay that doesn't exist"""
    result = await replayer.cancel_replay("nonexistent-replay")

    assert result is False


def test_get_active_replays(event_store, replayer):
    """Test getting active replay IDs"""
    # Create mock tasks
    replayer.active_replays["replay-1"] = MagicMock()
    replayer.active_replays["replay-2"] = MagicMock()

    active = replayer.get_active_replays()

    assert len(active) == 2
    assert "replay-1" in active
    assert "replay-2" in active


@pytest.mark.asyncio
async def test_catch_up(event_store, sample_events, replayer):
    """Test agent catch-up from timestamp"""
    for event in sample_events:
        event_store.store(event)

    received_events = []

    async def handler(event: Event):
        received_events.append(event)

    # Catch up from event 2
    last_seen = sample_events[2].timestamp

    count = await replayer.catch_up(handler, last_seen)

    # Should get events 2, 3, 4
    assert count == 3


@pytest.mark.asyncio
async def test_catch_up_with_pattern(event_store, sample_events, replayer):
    """Test catch-up with pattern filter"""
    for event in sample_events:
        event_store.store(event)

    received_events = []

    async def handler(event: Event):
        received_events.append(event)

    # Catch up on only task.* events from event 1
    last_seen = sample_events[1].timestamp

    count = await replayer.catch_up(handler, last_seen, pattern="task.*")

    # Should get task events 2, 4
    assert count == 2


@pytest.mark.asyncio
async def test_replay_event_stream(event_store, sample_events, replayer):
    """Test replaying specific events by ID"""
    for event in sample_events:
        event_store.store(event)

    received_events = []

    async def handler(event: Event):
        received_events.append(event)

    # Replay events 1 and 3
    event_ids = [sample_events[1].event_id, sample_events[3].event_id]

    count = await replayer.replay_event_stream(handler, event_ids)

    assert count == 2
    assert received_events[0].event_id == sample_events[1].event_id
    assert received_events[1].event_id == sample_events[3].event_id


def test_get_replay_stats(replayer):
    """Test getting replay statistics"""
    replayer.active_replays["replay-1"] = MagicMock()
    replayer.active_replays["replay-2"] = MagicMock()

    stats = replayer.get_replay_stats()

    assert stats["active_replays"] == 2
    assert len(stats["replay_ids"]) == 2


# Test ReplayConfig
def test_replay_config_defaults():
    """Test default replay configuration"""
    config = ReplayConfig()

    assert config.start_time is None
    assert config.end_time is None
    assert config.pattern is None
    assert config.max_events is None
    assert config.speed_multiplier == 1.0
    assert config.include_failures is False


def test_replay_config_custom():
    """Test custom replay configuration"""
    config = ReplayConfig(
        start_time="2025-01-01T00:00:00Z",
        end_time="2025-01-02T00:00:00Z",
        pattern="task.*",
        max_events=100,
        speed_multiplier=2.0,
        include_failures=True,
    )

    assert config.start_time == "2025-01-01T00:00:00Z"
    assert config.end_time == "2025-01-02T00:00:00Z"
    assert config.pattern == "task.*"
    assert config.max_events == 100
    assert config.speed_multiplier == 2.0
    assert config.include_failures is True
