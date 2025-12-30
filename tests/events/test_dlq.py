"""
Tests for Dead Letter Queue

Story 3: Dead Letter Queue (Epic 3.1)
Coverage: Failed event handling, retry logic, exponential backoff
"""

import asyncio
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from waooaw.events.event_bus import Event, EventType
from waooaw.events.dlq import (
    DeadLetterQueue,
    FailedEvent,
    FailureReason,
)


@pytest.fixture
def dlq():
    """Dead letter queue instance"""
    return DeadLetterQueue(
        max_retries=3,
        initial_backoff_seconds=1.0,
        max_backoff_seconds=60.0,
        backoff_multiplier=2.0,
    )


@pytest.fixture
def sample_event():
    """Sample event for testing"""
    return Event(
        event_type=EventType.TASK_COMPLETED,
        source_agent="did:waooaw:agent:source",
        payload={"task_id": "task-123", "result": "success"},
    )


@pytest.fixture
def failed_event(sample_event):
    """Sample failed event"""
    return FailedEvent(
        event=sample_event,
        subscription_id="sub-123",
        subscriber_agent="did:waooaw:agent:subscriber",
        failure_reason=FailureReason.HANDLER_ERROR,
        error_message="Handler threw exception",
    )


# Test FailedEvent
def test_failed_event_creation(sample_event):
    """Test creating a failed event"""
    failed = FailedEvent(
        event=sample_event,
        subscription_id="sub-123",
        subscriber_agent="did:waooaw:agent:subscriber",
        failure_reason=FailureReason.HANDLER_ERROR,
        error_message="Test error",
    )

    assert failed.event == sample_event
    assert failed.subscription_id == "sub-123"
    assert failed.subscriber_agent == "did:waooaw:agent:subscriber"
    assert failed.failure_reason == FailureReason.HANDLER_ERROR
    assert failed.error_message == "Test error"
    assert failed.retry_count == 0
    assert failed.max_retries == 3


def test_failed_event_to_dict(failed_event):
    """Test converting failed event to dictionary"""
    data = failed_event.to_dict()

    assert "event" in data
    assert data["subscription_id"] == "sub-123"
    assert data["subscriber_agent"] == "did:waooaw:agent:subscriber"
    assert data["failure_reason"] == "handler_error"
    assert data["retry_count"] == 0


def test_failed_event_from_dict(sample_event):
    """Test creating failed event from dictionary"""
    data = {
        "event": sample_event.to_dict(),
        "subscription_id": "sub-456",
        "subscriber_agent": "did:waooaw:agent:test",
        "failure_reason": "timeout",
        "error_message": "Handler timeout",
        "retry_count": 2,
        "max_retries": 5,
    }

    failed = FailedEvent.from_dict(data)

    assert failed.subscription_id == "sub-456"
    assert failed.failure_reason == FailureReason.TIMEOUT
    assert failed.retry_count == 2
    assert failed.max_retries == 5


# Test DeadLetterQueue initialization
def test_dlq_creation():
    """Test creating a DLQ"""
    dlq = DeadLetterQueue(
        max_retries=5,
        initial_backoff_seconds=2.0,
        max_backoff_seconds=120.0,
        backoff_multiplier=3.0,
    )

    assert dlq.max_retries == 5
    assert dlq.initial_backoff_seconds == 2.0
    assert dlq.max_backoff_seconds == 120.0
    assert dlq.backoff_multiplier == 3.0
    assert len(dlq.retry_queue) == 0
    assert len(dlq.dead_letters) == 0


def test_dlq_default_values():
    """Test DLQ with default values"""
    dlq = DeadLetterQueue()

    assert dlq.max_retries == 3
    assert dlq.initial_backoff_seconds == 1.0
    assert dlq.max_backoff_seconds == 300.0
    assert dlq.backoff_multiplier == 2.0


# Test adding failed events
@pytest.mark.asyncio
async def test_add_failed_event(dlq, sample_event):
    """Test adding a failed event to DLQ"""
    await dlq.add_failed_event(
        event=sample_event,
        subscription_id="sub-123",
        subscriber_agent="did:waooaw:agent:subscriber",
        failure_reason=FailureReason.HANDLER_ERROR,
        error_message="Test error",
    )

    assert len(dlq.retry_queue) == 1
    assert dlq.total_failures == 1

    failed = dlq.retry_queue[0]
    assert failed.event == sample_event
    assert failed.retry_count == 0
    assert failed.next_retry_at is not None


@pytest.mark.asyncio
async def test_add_multiple_failed_events(dlq, sample_event):
    """Test adding multiple failed events"""
    for i in range(3):
        await dlq.add_failed_event(
            event=sample_event,
            subscription_id=f"sub-{i}",
            subscriber_agent=f"did:waooaw:agent:agent{i}",
            failure_reason=FailureReason.HANDLER_ERROR,
            error_message=f"Error {i}",
        )

    assert len(dlq.retry_queue) == 3
    assert dlq.total_failures == 3


# Test retry logic
@pytest.mark.asyncio
async def test_retry_event_success(dlq, failed_event):
    """Test successful retry"""
    # Mock handler that succeeds
    handler = AsyncMock()

    result = await dlq.retry_event(failed_event, handler)

    assert result is True
    assert failed_event.retry_count == 1
    assert dlq.successful_retries == 1
    handler.assert_called_once_with(failed_event.event)


@pytest.mark.asyncio
async def test_retry_event_failure(dlq, failed_event):
    """Test failed retry"""
    # Mock handler that fails
    handler = AsyncMock(side_effect=Exception("Retry failed"))

    result = await dlq.retry_event(failed_event, handler)

    assert result is False
    assert failed_event.retry_count == 1
    assert failed_event.last_error == "Retry failed"
    assert failed_event.next_retry_at is not None


@pytest.mark.asyncio
async def test_retry_until_max_retries(dlq, failed_event):
    """Test retrying until max retries exceeded"""
    # Mock handler that always fails
    handler = AsyncMock(side_effect=Exception("Always fails"))

    # Retry 3 times (max_retries = 3)
    for i in range(3):
        result = await dlq.retry_event(failed_event, handler)
        assert result is False
        assert failed_event.retry_count == i + 1

    # After 3 retries, should be in dead letters
    assert len(dlq.dead_letters) == 1
    assert dlq.permanent_failures == 1
    assert dlq.dead_letters[0] == failed_event


@pytest.mark.asyncio
async def test_retry_with_sync_handler(dlq, failed_event):
    """Test retry with synchronous handler"""
    # Mock sync handler
    handler = MagicMock()

    result = await dlq.retry_event(failed_event, handler)

    assert result is True
    handler.assert_called_once_with(failed_event.event)


# Test exponential backoff
def test_calculate_next_retry_first_attempt(dlq, failed_event):
    """Test backoff calculation for first retry"""
    failed_event.retry_count = 0

    next_retry_str = dlq._calculate_next_retry(failed_event)
    next_retry = datetime.fromisoformat(next_retry_str)
    now = datetime.now(timezone.utc)

    # Should be approximately 1 second (initial_backoff * 2^0)
    delta = (next_retry - now).total_seconds()
    assert 0.9 <= delta <= 1.5  # Allow some tolerance


def test_calculate_next_retry_exponential(dlq, failed_event):
    """Test exponential backoff"""
    # First retry: 1 * 2^0 = 1 second
    failed_event.retry_count = 0
    next_retry_1 = dlq._calculate_next_retry(failed_event)

    # Second retry: 1 * 2^1 = 2 seconds
    failed_event.retry_count = 1
    next_retry_2 = dlq._calculate_next_retry(failed_event)

    # Third retry: 1 * 2^2 = 4 seconds
    failed_event.retry_count = 2
    next_retry_3 = dlq._calculate_next_retry(failed_event)

    # Verify exponential growth
    t1 = datetime.fromisoformat(next_retry_1)
    t2 = datetime.fromisoformat(next_retry_2)
    t3 = datetime.fromisoformat(next_retry_3)
    now = datetime.now(timezone.utc)

    delta1 = (t1 - now).total_seconds()
    delta2 = (t2 - now).total_seconds()
    delta3 = (t3 - now).total_seconds()

    # Should grow exponentially
    assert delta1 < delta2 < delta3


def test_calculate_next_retry_max_backoff(dlq, failed_event):
    """Test backoff caps at max_backoff_seconds"""
    # Set high retry count to exceed max backoff
    failed_event.retry_count = 10  # Would be 1 * 2^10 = 1024 seconds

    next_retry_str = dlq._calculate_next_retry(failed_event)
    next_retry = datetime.fromisoformat(next_retry_str)
    now = datetime.now(timezone.utc)

    delta = (next_retry - now).total_seconds()

    # Should be capped at max_backoff_seconds (60.0)
    assert delta <= dlq.max_backoff_seconds + 1  # Allow 1 second tolerance


# Test DLQ lifecycle
@pytest.mark.asyncio
async def test_dlq_start_stop(dlq):
    """Test starting and stopping DLQ"""
    assert dlq.running is False

    await dlq.start()
    assert dlq.running is True
    assert dlq.retry_task is not None

    await dlq.stop()
    assert dlq.running is False


@pytest.mark.asyncio
async def test_dlq_start_already_running(dlq):
    """Test starting DLQ when already running"""
    await dlq.start()
    await dlq.start()  # Second start should be no-op

    assert dlq.running is True

    await dlq.stop()


# Test dead letter operations
def test_get_retry_queue(dlq, failed_event):
    """Test getting retry queue"""
    dlq.retry_queue.append(failed_event)

    queue = dlq.get_retry_queue()

    assert len(queue) == 1
    assert queue[0] == failed_event


def test_get_dead_letters(dlq, failed_event):
    """Test getting dead letters"""
    dlq.dead_letters.append(failed_event)

    dead_letters = dlq.get_dead_letters()

    assert len(dead_letters) == 1
    assert dead_letters[0] == failed_event


def test_get_stats(dlq):
    """Test getting DLQ statistics"""
    dlq.total_failures = 10
    dlq.total_retries = 15
    dlq.successful_retries = 12
    dlq.permanent_failures = 3

    stats = dlq.get_stats()

    assert stats["total_failures"] == 10
    assert stats["total_retries"] == 15
    assert stats["successful_retries"] == 12
    assert stats["permanent_failures"] == 3
    assert stats["retry_success_rate"] == 12 / 15


def test_get_stats_zero_retries(dlq):
    """Test stats with zero retries"""
    stats = dlq.get_stats()

    assert stats["retry_success_rate"] == 0.0


# Test reprocessing dead letters
@pytest.mark.asyncio
async def test_reprocess_dead_letter_success(dlq, failed_event):
    """Test successfully reprocessing a dead letter"""
    # Add to dead letters
    dlq.dead_letters.append(failed_event)

    # Mock handler that succeeds
    handler = AsyncMock()

    result = await dlq.reprocess_dead_letter(failed_event.event.event_id, handler)

    assert result is True
    assert len(dlq.dead_letters) == 0
    handler.assert_called_once_with(failed_event.event)


@pytest.mark.asyncio
async def test_reprocess_dead_letter_failure(dlq, failed_event):
    """Test reprocessing a dead letter that fails again"""
    dlq.dead_letters.append(failed_event)

    # Mock handler that fails
    handler = AsyncMock(side_effect=Exception("Still failing"))

    result = await dlq.reprocess_dead_letter(failed_event.event.event_id, handler)

    assert result is False
    assert len(dlq.dead_letters) == 1  # Still in dead letters


@pytest.mark.asyncio
async def test_reprocess_nonexistent_dead_letter(dlq):
    """Test reprocessing a dead letter that doesn't exist"""
    handler = AsyncMock()

    result = await dlq.reprocess_dead_letter("nonexistent-id", handler)

    assert result is False


def test_clear_dead_letters(dlq, failed_event):
    """Test clearing all dead letters"""
    # Add multiple dead letters
    for i in range(5):
        dlq.dead_letters.append(failed_event)

    count = dlq.clear_dead_letters()

    assert count == 5
    assert len(dlq.dead_letters) == 0


# Test filtering operations
def test_get_failed_events_by_reason(dlq, sample_event):
    """Test filtering failed events by reason"""
    # Add events with different reasons
    dlq.retry_queue.append(
        FailedEvent(
            event=sample_event,
            subscription_id="sub-1",
            subscriber_agent="agent-1",
            failure_reason=FailureReason.HANDLER_ERROR,
            error_message="Error 1",
        )
    )
    dlq.retry_queue.append(
        FailedEvent(
            event=sample_event,
            subscription_id="sub-2",
            subscriber_agent="agent-2",
            failure_reason=FailureReason.TIMEOUT,
            error_message="Error 2",
        )
    )
    dlq.retry_queue.append(
        FailedEvent(
            event=sample_event,
            subscription_id="sub-3",
            subscriber_agent="agent-3",
            failure_reason=FailureReason.HANDLER_ERROR,
            error_message="Error 3",
        )
    )

    handler_errors = dlq.get_failed_events_by_reason(FailureReason.HANDLER_ERROR)
    timeouts = dlq.get_failed_events_by_reason(FailureReason.TIMEOUT)

    assert len(handler_errors) == 2
    assert len(timeouts) == 1


def test_get_failed_events_by_subscriber(dlq, sample_event):
    """Test filtering failed events by subscriber"""
    # Add events for different subscribers
    dlq.retry_queue.append(
        FailedEvent(
            event=sample_event,
            subscription_id="sub-1",
            subscriber_agent="did:waooaw:agent:agent1",
            failure_reason=FailureReason.HANDLER_ERROR,
            error_message="Error 1",
        )
    )
    dlq.retry_queue.append(
        FailedEvent(
            event=sample_event,
            subscription_id="sub-2",
            subscriber_agent="did:waooaw:agent:agent2",
            failure_reason=FailureReason.TIMEOUT,
            error_message="Error 2",
        )
    )
    dlq.retry_queue.append(
        FailedEvent(
            event=sample_event,
            subscription_id="sub-3",
            subscriber_agent="did:waooaw:agent:agent1",
            failure_reason=FailureReason.HANDLER_ERROR,
            error_message="Error 3",
        )
    )

    agent1_failures = dlq.get_failed_events_by_subscriber("did:waooaw:agent:agent1")
    agent2_failures = dlq.get_failed_events_by_subscriber("did:waooaw:agent:agent2")

    assert len(agent1_failures) == 2
    assert len(agent2_failures) == 1


def test_failure_reason_enum():
    """Test FailureReason enum values"""
    assert FailureReason.HANDLER_ERROR.value == "handler_error"
    assert FailureReason.TIMEOUT.value == "timeout"
    assert FailureReason.VALIDATION_ERROR.value == "validation_error"
    assert FailureReason.SUBSCRIBER_UNAVAILABLE.value == "subscriber_unavailable"
    assert FailureReason.DESERIALIZATION_ERROR.value == "deserialization_error"
    assert FailureReason.UNKNOWN.value == "unknown"
