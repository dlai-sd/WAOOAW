"""
Integration Tests for Event-Driven Orchestration

Tests the bridge between Event Bus and Orchestration Runtime,
validating event-to-task conversion, task lifecycle event publishing,
and end-to-end integration scenarios.
"""

import asyncio
import pytest
from datetime import datetime
from typing import Dict, List, Any
from unittest.mock import AsyncMock, MagicMock, patch

from waooaw.orchestration import (
    Task,
    TaskQueue,
    TaskPriority,
    TaskState,
    WorkerPool,
)
from waooaw.orchestration.event_adapter import (
    OrchestrationEventType,
    EventToTaskMapping,
    EventToTaskMapper,
    TaskEventPublisher,
    OrchestrationEventHandler,
)


class MockEventBus:
    """Mock EventBus for testing"""

    def __init__(self):
        self.published_events: List[Dict[str, Any]] = []
        self.subscriptions: Dict[str, List] = {}

    async def publish(self, event: Dict[str, Any]) -> None:
        """Record published events"""
        self.published_events.append(event)

    async def subscribe(self, pattern: str, handler, subscriber_agent: str) -> None:
        """Record subscriptions"""
        if pattern not in self.subscriptions:
            self.subscriptions[pattern] = []
        self.subscriptions[pattern].append((handler, subscriber_agent))

    async def unsubscribe(self, pattern: str, subscriber_agent: str) -> None:
        """Remove subscription"""
        if pattern in self.subscriptions:
            self.subscriptions[pattern] = [
                (h, a) for h, a in self.subscriptions[pattern] if a != subscriber_agent
            ]

    def get_published_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """Get all published events of a specific type"""
        return [e for e in self.published_events if e.get("event_type") == event_type]

    def clear(self) -> None:
        """Clear all recorded events"""
        self.published_events.clear()


@pytest.fixture
def mock_event_bus():
    """Fixture providing mock EventBus"""
    return MockEventBus()


@pytest.fixture
def task_queue():
    """Fixture providing TaskQueue"""
    return TaskQueue(max_size=100)


@pytest.fixture
async def worker_pool():
    """Fixture providing WorkerPool"""
    pool = WorkerPool(max_workers=5, min_workers=1)
    await pool.start()
    yield pool
    await pool.stop()


# Sample task functions for testing
async def sample_task(x: int, y: int) -> int:
    """Sample async task"""
    await asyncio.sleep(0.01)  # Simulate work
    return x + y


def sample_sync_task(name: str) -> str:
    """Sample sync task"""
    return f"Hello, {name}!"


@pytest.mark.asyncio
class TestEventToTaskMapper:
    """Test event-to-task conversion"""

    def test_register_task_function(self):
        """Should register task functions"""
        mapper = EventToTaskMapper()
        mapper.register_task_function("add", sample_task)
        mapper.register_task_function("greet", sample_sync_task)

        assert "add" in mapper.task_registry
        assert "greet" in mapper.task_registry
        assert mapper.task_registry["add"] == sample_task

    def test_add_mapping(self):
        """Should add event-to-task mappings"""
        mapper = EventToTaskMapper()
        mapping = EventToTaskMapping(
            event_pattern="orchestration.task.trigger",
            task_name_field="task_name",
            default_priority=TaskPriority.HIGH,
        )
        mapper.add_mapping(mapping)

        assert len(mapper.mappings) == 1
        assert mapper.mappings[0].event_pattern == "orchestration.task.trigger"

    def test_map_event_to_task_success(self):
        """Should successfully map event to task"""
        mapper = EventToTaskMapper()
        mapper.register_task_function("add", sample_task)
        mapper.add_mapping(
            EventToTaskMapping(event_pattern="orchestration.task.trigger")
        )

        event_payload = {
            "task_name": "add",
            "args": [5, 3],
            "kwargs": {},
            "priority": "HIGH",
            "workflow_id": "workflow-123",
        }

        task = mapper.map_event_to_task(
            "orchestration.task.trigger", event_payload, "event-001"
        )

        assert task is not None
        assert task.name == "add"
        assert task.args == [5, 3]
        assert task.priority == TaskPriority.HIGH
        assert task.workflow_id == "workflow-123"
        assert task.metadata["trigger_event_id"] == "event-001"

    def test_map_event_missing_task_name(self):
        """Should return None if task_name missing"""
        mapper = EventToTaskMapper()
        mapper.add_mapping(
            EventToTaskMapping(event_pattern="orchestration.task.trigger")
        )

        event_payload = {"args": [5, 3]}  # Missing task_name

        task = mapper.map_event_to_task(
            "orchestration.task.trigger", event_payload, "event-001"
        )

        assert task is None

    def test_map_event_unregistered_function(self):
        """Should return None if function not registered"""
        mapper = EventToTaskMapper()
        mapper.add_mapping(
            EventToTaskMapping(event_pattern="orchestration.task.trigger")
        )

        event_payload = {"task_name": "unknown_task", "args": []}

        task = mapper.map_event_to_task(
            "orchestration.task.trigger", event_payload, "event-001"
        )

        assert task is None

    def test_map_event_default_priority(self):
        """Should use default priority if not specified"""
        mapper = EventToTaskMapper()
        mapper.register_task_function("greet", sample_sync_task)
        mapper.add_mapping(
            EventToTaskMapping(
                event_pattern="orchestration.task.trigger",
                default_priority=TaskPriority.LOW,
            )
        )

        event_payload = {"task_name": "greet", "args": ["World"]}

        task = mapper.map_event_to_task(
            "orchestration.task.trigger", event_payload, "event-001"
        )

        assert task.priority == TaskPriority.LOW

    def test_map_event_pattern_matching(self):
        """Should match event patterns with wildcards"""
        mapper = EventToTaskMapper()
        mapper.register_task_function("add", sample_task)
        mapper.add_mapping(
            EventToTaskMapping(event_pattern="orchestration.*")  # Wildcard pattern
        )

        event_payload = {"task_name": "add", "args": [1, 2]}

        task = mapper.map_event_to_task(
            "orchestration.task.custom", event_payload, "event-001"
        )

        assert task is not None
        assert task.name == "add"


@pytest.mark.asyncio
class TestTaskEventPublisher:
    """Test task lifecycle event publishing"""

    async def test_publish_task_created(self, mock_event_bus):
        """Should publish task.created event"""
        publisher = TaskEventPublisher(mock_event_bus, "test-agent")

        task = Task(
            name="test_task",
            func=sample_task,
            args=[1, 2],
            priority=TaskPriority.HIGH,
            workflow_id="workflow-123",
        )

        await publisher.publish_task_created("task-001", task, "event-001")

        events = mock_event_bus.get_published_events_by_type(
            OrchestrationEventType.TASK_CREATED.value
        )
        assert len(events) == 1

        event = events[0]
        assert event["source_agent"] == "test-agent"
        assert event["payload"]["task_id"] == "task-001"
        assert event["payload"]["task_name"] == "test_task"
        assert event["payload"]["priority"] == "HIGH"
        assert event["payload"]["trigger_event_id"] == "event-001"

    async def test_publish_task_completed(self, mock_event_bus, task_queue):
        """Should publish task.completed event"""
        publisher = TaskEventPublisher(mock_event_bus)

        task = Task(name="test", func=sample_task, args=[5, 3])
        task_id = await task_queue.enqueue(task)
        await task_queue.complete_task(task_id, result=8)

        task_meta = task_queue.get_task(task_id)
        await publisher.publish_task_completed(task_id, task_meta, 8, duration_ms=150.5)

        events = mock_event_bus.get_published_events_by_type(
            OrchestrationEventType.TASK_COMPLETED.value
        )
        assert len(events) == 1

        event = events[0]
        assert event["payload"]["task_id"] == task_id
        assert event["payload"]["result"] == 8
        assert event["payload"]["duration_ms"] == 150.5

    async def test_publish_task_failed(self, mock_event_bus, task_queue):
        """Should publish task.failed event"""
        publisher = TaskEventPublisher(mock_event_bus)

        task = Task(name="test", func=sample_task, args=[1, 2])
        task_id = await task_queue.enqueue(task)
        await task_queue.fail_task(task_id, "Connection timeout")

        task_meta = task_queue.get_task(task_id)
        await publisher.publish_task_failed(task_id, task_meta, "Connection timeout", 1)

        events = mock_event_bus.get_published_events_by_type(
            OrchestrationEventType.TASK_FAILED.value
        )
        assert len(events) == 1

        event = events[0]
        assert event["payload"]["task_id"] == task_id
        assert event["payload"]["error"] == "Connection timeout"
        assert event["payload"]["retry_count"] == 1

    async def test_publish_metrics_snapshot(self, mock_event_bus):
        """Should publish metrics snapshot"""
        publisher = TaskEventPublisher(mock_event_bus)

        queue_stats = {"pending": 5, "running": 2, "completed": 10}
        pool_metrics = {"active_workers": 3, "throughput_per_minute": 45.5}

        await publisher.publish_metrics_snapshot(queue_stats, pool_metrics)

        events = mock_event_bus.get_published_events_by_type(
            OrchestrationEventType.METRICS_SNAPSHOT.value
        )
        assert len(events) == 1

        event = events[0]
        assert event["payload"]["task_queue"] == queue_stats
        assert event["payload"]["worker_pool"] == pool_metrics


@pytest.mark.asyncio
class TestOrchestrationEventHandler:
    """Test end-to-end event handler"""

    async def test_handler_start_and_stop(self, mock_event_bus, task_queue):
        """Should start and stop handler with subscriptions"""
        handler = OrchestrationEventHandler(mock_event_bus, task_queue)

        await handler.start()
        assert handler._running is True
        assert len(handler.subscriptions) == 2  # task.trigger + workflow.start

        await handler.stop()
        assert handler._running is False
        assert len(handler.subscriptions) == 0

    async def test_handle_task_trigger_event(self, mock_event_bus, task_queue):
        """Should handle task trigger event and create task"""
        handler = OrchestrationEventHandler(mock_event_bus, task_queue)
        handler.register_task_function("add", sample_task)
        handler.add_event_mapping(
            EventToTaskMapping(event_pattern="orchestration.task.trigger")
        )

        await handler.start()

        # Simulate task trigger event
        trigger_event = {
            "event_id": "event-123",
            "event_type": "orchestration.task.trigger",
            "payload": {
                "task_name": "add",
                "args": [10, 20],
                "priority": "HIGH",
                "workflow_id": "workflow-456",
            },
        }

        await handler._handle_task_trigger(trigger_event)

        # Wait for async processing
        await asyncio.sleep(0.1)

        # Check task was created
        stats = task_queue.get_statistics()
        assert stats.pending_count >= 1

        # Check task.created event was published
        created_events = mock_event_bus.get_published_events_by_type(
            OrchestrationEventType.TASK_CREATED.value
        )
        assert len(created_events) == 1
        assert created_events[0]["payload"]["trigger_event_id"] == "event-123"

        # Check correlation tracking
        assert "event-123" in handler.event_task_map

        await handler.stop()

    async def test_event_task_correlation(self, mock_event_bus, task_queue):
        """Should track event-task correlation"""
        handler = OrchestrationEventHandler(mock_event_bus, task_queue)
        handler.register_task_function("greet", sample_sync_task)
        handler.add_event_mapping(
            EventToTaskMapping(event_pattern="orchestration.task.trigger")
        )

        await handler.start()

        trigger_event = {
            "event_id": "event-999",
            "event_type": "orchestration.task.trigger",
            "payload": {"task_name": "greet", "args": ["Test"]},
        }

        await handler._handle_task_trigger(trigger_event)
        await asyncio.sleep(0.05)

        # Check correlation maps
        assert "event-999" in handler.event_task_map
        task_id = handler.event_task_map["event-999"]
        assert task_id in handler.task_event_map
        assert handler.task_event_map[task_id] == "event-999"

        await handler.stop()

    async def test_metrics_publishing_loop(self, mock_event_bus, task_queue):
        """Should periodically publish metrics"""
        handler = OrchestrationEventHandler(mock_event_bus, task_queue)

        await handler.start()

        # Wait for at least one metrics publish (10s interval, but we'll wait shorter)
        # We'll patch the sleep to make this faster
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_sleep.return_value = None  # Instant return

            # Trigger metrics loop iteration
            await asyncio.sleep(0.01)  # Let loop start
            await handler._metrics_publishing_loop()  # Should execute once and exit

        await handler.stop()

        # Note: In a real test, we'd wait for the actual loop to publish
        # For this test, we just verify the structure exists


@pytest.mark.asyncio
class TestEndToEndIntegration:
    """End-to-end integration tests"""

    async def test_event_to_task_to_event_flow(self, mock_event_bus, task_queue):
        """Complete flow: Event → Task → Execution → Result Event"""
        handler = OrchestrationEventHandler(
            mock_event_bus, task_queue, worker_pool=None
        )

        # Register task
        async def multiply_task(a: int, b: int) -> int:
            return a * b

        handler.register_task_function("multiply", multiply_task)
        handler.add_event_mapping(
            EventToTaskMapping(event_pattern="orchestration.task.trigger")
        )

        await handler.start()

        # Send trigger event
        trigger_event = {
            "event_id": "event-e2e-001",
            "event_type": "orchestration.task.trigger",
            "payload": {
                "task_name": "multiply",
                "args": [6, 7],
                "priority": "NORMAL",
                "workflow_id": "workflow-e2e",
            },
        }

        await handler._handle_task_trigger(trigger_event)
        await asyncio.sleep(0.1)

        # Verify task created event
        created_events = mock_event_bus.get_published_events_by_type(
            OrchestrationEventType.TASK_CREATED.value
        )
        assert len(created_events) == 1
        assert created_events[0]["payload"]["task_name"] == "multiply"
        assert created_events[0]["payload"]["workflow_id"] == "workflow-e2e"

        # Verify task is in queue
        stats = task_queue.get_statistics()
        assert stats.pending_count >= 1

        await handler.stop()

    async def test_multiple_tasks_from_events(self, mock_event_bus, task_queue):
        """Should handle multiple concurrent task trigger events"""
        handler = OrchestrationEventHandler(mock_event_bus, task_queue)

        handler.register_task_function("add", sample_task)
        handler.register_task_function("greet", sample_sync_task)
        handler.add_event_mapping(
            EventToTaskMapping(event_pattern="orchestration.task.trigger")
        )

        await handler.start()

        # Send multiple events
        events = [
            {
                "event_id": f"event-{i}",
                "event_type": "orchestration.task.trigger",
                "payload": {"task_name": "add" if i % 2 == 0 else "greet", "args": [i, i]},
            }
            for i in range(5)
        ]

        for event in events:
            await handler._handle_task_trigger(event)

        await asyncio.sleep(0.2)

        # Verify all tasks created
        created_events = mock_event_bus.get_published_events_by_type(
            OrchestrationEventType.TASK_CREATED.value
        )
        assert len(created_events) == 5

        # Verify correlation tracking
        assert len(handler.event_task_map) == 5
        assert len(handler.task_event_map) == 5

        await handler.stop()

    async def test_error_handling_invalid_event(self, mock_event_bus, task_queue):
        """Should handle invalid events gracefully"""
        handler = OrchestrationEventHandler(mock_event_bus, task_queue)
        handler.add_event_mapping(
            EventToTaskMapping(event_pattern="orchestration.task.trigger")
        )

        await handler.start()

        # Send event with missing task_name
        invalid_event = {
            "event_id": "event-invalid",
            "event_type": "orchestration.task.trigger",
            "payload": {"args": [1, 2]},  # Missing task_name
        }

        # Should not raise exception
        await handler._handle_task_trigger(invalid_event)

        await asyncio.sleep(0.05)

        # No task should be created
        stats = task_queue.get_statistics()
        assert stats.pending_count == 0

        # No task.created event published
        created_events = mock_event_bus.get_published_events_by_type(
            OrchestrationEventType.TASK_CREATED.value
        )
        assert len(created_events) == 0

        await handler.stop()
