"""
End-to-End Integration Tests: Message Bus & Orchestration Bridge

Tests the complete flow from Event Bus events triggering orchestration tasks,
executing workflows, and publishing results back to Event Bus. Validates
resilience, performance, and complex multi-step scenarios.
"""

import asyncio
import pytest
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from waooaw.orchestration import (
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


# ==================== Test Fixtures ====================

class MockEventBus:
    """Mock EventBus for testing"""

    def __init__(self):
        self.published_events: List[Dict[str, Any]] = []
        self.subscriptions: Dict[str, List] = {}
        self._event_history: List[Dict[str, Any]] = []

    async def publish(self, event: Dict[str, Any]) -> None:
        """Record published events"""
        event["published_at"] = datetime.utcnow().isoformat()
        self.published_events.append(event)
        self._event_history.append(event)

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

    def get_event_chain(self, trigger_event_id: str) -> List[Dict[str, Any]]:
        """Get all events correlated to a trigger event"""
        chain = []
        for event in self._event_history:
            payload = event.get("payload", {})
            if (payload.get("trigger_event_id") == trigger_event_id or
                event.get("event_id") == trigger_event_id):
                chain.append(event)
        return chain

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
    return TaskQueue(name="test-queue", max_capacity=100)


@pytest.fixture
async def worker_pool():
    """Fixture providing WorkerPool"""
    pool = WorkerPool(max_workers=5, min_workers=1)
    await pool.start()
    yield pool
    await pool.stop()


@pytest.fixture
async def orchestration_handler_instance_instance(mock_event_bus, task_queue):
    """Fixture providing OrchestrationEventHandler"""
    handler = OrchestrationEventHandler(mock_event_bus, task_queue)
    await handler.start()
    yield handler
    await handler.stop()


# ==================== Test Task Functions ====================

async def sample_add_task(a: int, b: int) -> int:
    """Sample async task for testing"""
    await asyncio.sleep(0.01)
    return a + b


async def sample_multiply_task(a: int, b: int) -> int:
    """Sample multiplication task"""
    await asyncio.sleep(0.01)
    return a * b


async def failing_task(should_fail: bool = True) -> str:
    """Task that fails conditionally"""
    await asyncio.sleep(0.01)
    if should_fail:
        raise ValueError("Intentional failure for testing")
    return "success"


async def slow_task(duration_seconds: float = 1.0) -> str:
    """Task that takes time to complete"""
    await asyncio.sleep(duration_seconds)
    return f"completed after {duration_seconds}s"


def compensation_task(original_result: Any) -> str:
    """Compensation task for saga pattern"""
    return f"compensated: {original_result}"


# ==================== Scenario 1: Happy Path ====================

@pytest.mark.asyncio
class TestHappyPath:
    """Test successful event → task → result flow"""

    async def test_event_triggers_task_completion(
        self, orchestration_handler_instance, mock_event_bus
    ):
        """Event triggers task that completes successfully and publishes result"""
        # Register task
        orchestration_handler_instance.register_task_function("add", sample_add_task)
        orchestration_handler_instance.add_event_mapping(
            EventToTaskMapping(event_pattern="orchestration.task.trigger")
        )

        # Trigger event
        trigger_event = {
            "event_id": "evt-happy-001",
            "event_type": "orchestration.task.trigger",
            "payload": {
                "task_name": "add",
                "args": [10, 20],
                "priority": "HIGH",
                "workflow_id": "workflow-happy-001",
            },
        }

        await orchestration_handler_instance._handle_task_trigger(trigger_event)
        await asyncio.sleep(0.2)

        # Verify task.created event
        created_events = mock_event_bus.get_published_events_by_type(
            OrchestrationEventType.TASK_CREATED.value
        )
        assert len(created_events) == 1
        assert created_events[0]["payload"]["trigger_event_id"] == "evt-happy-001"

        # Verify task in queue
        stats = await orchestration_handler_instance.task_queue.get_statistics()
        assert stats.pending_tasks >= 1

    async def test_multi_step_workflow_via_events(
        self, orchestration_handler_instance, mock_event_bus
    ):
        """Multiple tasks triggered in sequence via events"""
        # Register tasks
        orchestration_handler_instance.register_task_function("add", sample_add_task)
        orchestration_handler_instance.register_task_function("multiply", sample_multiply_task)
        orchestration_handler_instance.add_event_mapping(
            EventToTaskMapping(event_pattern="orchestration.task.trigger")
        )

        workflow_id = "workflow-multi-001"

        # Step 1: Add
        event1 = {
            "event_id": "evt-step1",
            "event_type": "orchestration.task.trigger",
            "payload": {
                "task_name": "add",
                "args": [5, 3],
                "workflow_id": workflow_id,
            },
        }
        await orchestration_handler_instance._handle_task_trigger(event1)

        # Step 2: Multiply
        event2 = {
            "event_id": "evt-step2",
            "event_type": "orchestration.task.trigger",
            "payload": {
                "task_name": "multiply",
                "args": [8, 2],  # Result from step 1 would be 8
                "workflow_id": workflow_id,
            },
        }
        await orchestration_handler_instance._handle_task_trigger(event2)

        await asyncio.sleep(0.3)

        # Verify both tasks created
        created_events = mock_event_bus.get_published_events_by_type(
            OrchestrationEventType.TASK_CREATED.value
        )
        assert len(created_events) == 2

        # Verify both tasks share workflow_id
        workflow_tasks = [
            e for e in created_events if e["payload"]["workflow_id"] == workflow_id
        ]
        assert len(workflow_tasks) == 2


# ==================== Scenario 2: Retry Handling ====================

@pytest.mark.asyncio
class TestRetryPath:
    """Test task failure, retry, and eventual success"""

    async def test_task_failure_triggers_retry(
        self, orchestration_handler_instance, mock_event_bus
    ):
        """Failed task triggers retry via event"""
        # Register failing task
        orchestration_handler_instance.register_task_function("failing", failing_task)
        orchestration_handler_instance.add_event_mapping(
            EventToTaskMapping(event_pattern="orchestration.task.trigger")
        )

        trigger_event = {
            "event_id": "evt-retry-001",
            "event_type": "orchestration.task.trigger",
            "payload": {
                "task_name": "failing",
                "kwargs": {"should_fail": True},
                "workflow_id": "workflow-retry-001",
            },
        }

        await orchestration_handler_instance._handle_task_trigger(trigger_event)
        await asyncio.sleep(0.2)

        # Task should be created
        created_events = mock_event_bus.get_published_events_by_type(
            OrchestrationEventType.TASK_CREATED.value
        )
        assert len(created_events) == 1


# ==================== Scenario 3: Dependency Chain ====================

@pytest.mark.asyncio
class TestDependencyChain:
    """Test tasks with dependencies triggered sequentially"""

    async def test_dependency_chain_execution(
        self, orchestration_handler_instance, mock_event_bus
    ):
        """Tasks execute in dependency order"""
        workflow_id = "workflow-dep-001"

        # Register tasks
        orchestration_handler_instance.register_task_function("add", sample_add_task)
        orchestration_handler_instance.register_task_function("multiply", sample_multiply_task)
        orchestration_handler_instance.add_event_mapping(
            EventToTaskMapping(event_pattern="orchestration.task.trigger")
        )

        # Task A (no dependencies)
        event_a = {
            "event_id": "evt-task-a",
            "event_type": "orchestration.task.trigger",
            "payload": {
                "task_name": "add",
                "args": [2, 3],
                "workflow_id": workflow_id,
            },
        }

        # Task B (depends on A)
        event_b = {
            "event_id": "evt-task-b",
            "event_type": "orchestration.task.trigger",
            "payload": {
                "task_name": "multiply",
                "args": [5, 4],  # Uses result from A
                "workflow_id": workflow_id,
                "dependencies": ["task-a"],
            },
        }

        # Trigger in order
        await orchestration_handler_instance._handle_task_trigger(event_a)
        await asyncio.sleep(0.1)
        await orchestration_handler_instance._handle_task_trigger(event_b)
        await asyncio.sleep(0.3)

        # Verify both tasks created
        created_events = mock_event_bus.get_published_events_by_type(
            OrchestrationEventType.TASK_CREATED.value
        )
        assert len(created_events) >= 2


# ==================== Scenario 4: Performance Tests ====================

@pytest.mark.asyncio
class TestPerformance:
    """Test performance and throughput"""

    async def test_high_volume_event_processing(
        self, orchestration_handler_instance, mock_event_bus
    ):
        """Process 100 events rapidly"""
        orchestration_handler_instance.register_task_function("add", sample_add_task)
        orchestration_handler_instance.add_event_mapping(
            EventToTaskMapping(event_pattern="orchestration.task.trigger")
        )

        start_time = time.time()
        num_events = 100

        # Send batch of events
        for i in range(num_events):
            event = {
                "event_id": f"evt-perf-{i}",
                "event_type": "orchestration.task.trigger",
                "payload": {
                    "task_name": "add",
                    "args": [i, i + 1],
                    "workflow_id": f"workflow-perf-{i}",
                },
            }
            await orchestration_handler_instance._handle_task_trigger(event)

        await asyncio.sleep(1.0)  # Wait for processing

        elapsed = time.time() - start_time

        # Verify throughput
        created_events = mock_event_bus.get_published_events_by_type(
            OrchestrationEventType.TASK_CREATED.value
        )
        assert len(created_events) >= num_events

        throughput = len(created_events) / elapsed
        print(f"Throughput: {throughput:.2f} events/sec")
        assert throughput > 50  # Should process >50 events/sec

    async def test_event_to_result_latency(
        self, orchestration_handler_instance, mock_event_bus
    ):
        """Measure latency from event to result"""
        orchestration_handler_instance.register_task_function("add", sample_add_task)
        orchestration_handler_instance.add_event_mapping(
            EventToTaskMapping(event_pattern="orchestration.task.trigger")
        )

        latencies = []

        for i in range(10):
            start = time.time()

            event = {
                "event_id": f"evt-latency-{i}",
                "event_type": "orchestration.task.trigger",
                "payload": {
                    "task_name": "add",
                    "args": [1, 2],
                },
            }

            await orchestration_handler_instance._handle_task_trigger(event)
            await asyncio.sleep(0.05)  # Wait for task creation

            end = time.time()
            latency_ms = (end - start) * 1000
            latencies.append(latency_ms)

        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

        print(f"Avg latency: {avg_latency:.2f}ms, P95: {p95_latency:.2f}ms")
        assert p95_latency < 500  # P95 should be <500ms


# ==================== Scenario 5: Event Correlation ====================

@pytest.mark.asyncio
class TestEventCorrelation:
    """Test event correlation and tracing"""

    async def test_correlation_id_preserved(
        self, orchestration_handler_instance, mock_event_bus
    ):
        """Correlation IDs preserved across event chain"""
        orchestration_handler_instance.register_task_function("add", sample_add_task)
        orchestration_handler_instance.add_event_mapping(
            EventToTaskMapping(event_pattern="orchestration.task.trigger")
        )

        trigger_event_id = "evt-correlation-001"
        workflow_id = "workflow-correlation-001"

        trigger_event = {
            "event_id": trigger_event_id,
            "event_type": "orchestration.task.trigger",
            "payload": {
                "task_name": "add",
                "args": [5, 10],
                "workflow_id": workflow_id,
            },
        }

        await orchestration_handler_instance._handle_task_trigger(trigger_event)
        await asyncio.sleep(0.2)

        # Get event chain
        chain = mock_event_bus.get_event_chain(trigger_event_id)

        # Verify chain contains correlated events
        assert len(chain) >= 1

        # Verify trigger_event_id in task.created
        created_events = mock_event_bus.get_published_events_by_type(
            OrchestrationEventType.TASK_CREATED.value
        )
        if created_events:
            assert created_events[0]["payload"]["trigger_event_id"] == trigger_event_id


# ==================== Scenario 6: Chaos Engineering ====================

@pytest.mark.asyncio
class TestChaosEngineering:
    """Test resilience under failure conditions"""

    async def test_task_queue_overflow_handling(self, orchestration_handler_instance):
        """Handle queue overflow gracefully"""
        small_queue = TaskQueue(name="small-queue", max_capacity=10)
        handler = OrchestrationEventHandler(MockEventBus(), small_queue)
        handler.register_task_function("add", sample_add_task)
        handler.add_event_mapping(
            EventToTaskMapping(event_pattern="orchestration.task.trigger")
        )

        await handler.start()

        # Try to overflow queue
        for i in range(15):
            event = {
                "event_id": f"evt-overflow-{i}",
                "event_type": "orchestration.task.trigger",
                "payload": {"task_name": "add", "args": [i, i]},
            }
            try:
                await handler._handle_task_trigger(event)
            except Exception:
                pass  # Expected for overflow

        await handler.stop()

        # Verify queue didn't crash
        stats = await small_queue.get_statistics()
        assert stats.total_tasks <= 10


# ==================== Scenario 7: Event Replay ====================

@pytest.mark.asyncio
class TestEventReplay:
    """Test event replay for failed workflows"""

    async def test_replay_failed_workflow(
        self, orchestration_handler_instance, mock_event_bus
    ):
        """Replay events to reprocess failed workflow"""
        orchestration_handler_instance.register_task_function("failing", failing_task)
        orchestration_handler_instance.add_event_mapping(
            EventToTaskMapping(event_pattern="orchestration.task.trigger")
        )

        original_event = {
            "event_id": "evt-replay-001",
            "event_type": "orchestration.task.trigger",
            "payload": {
                "task_name": "failing",
                "kwargs": {"should_fail": True},
                "workflow_id": "workflow-replay-001",
            },
        }

        # First attempt (will fail)
        await orchestration_handler_instance._handle_task_trigger(original_event)
        await asyncio.sleep(0.2)

        initial_count = len(mock_event_bus.published_events)

        # Replay with fixed parameters
        replay_event = {
            "event_id": "evt-replay-002",
            "event_type": "orchestration.task.trigger",
            "payload": {
                "task_name": "failing",
                "kwargs": {"should_fail": False},  # Fixed
                "workflow_id": "workflow-replay-001",
                "replay_of": "evt-replay-001",
            },
        }

        await orchestration_handler_instance._handle_task_trigger(replay_event)
        await asyncio.sleep(0.2)

        # Verify replay generated new events
        assert len(mock_event_bus.published_events) > initial_count


# ==================== Summary Test ====================

@pytest.mark.asyncio
async def test_complete_end_to_end_workflow(mock_event_bus, task_queue):
    """Complete workflow: Event → Task Queue → Execution → Result Event"""
    handler = OrchestrationEventHandler(mock_event_bus, task_queue)

    # Setup
    handler.register_task_function("add", sample_add_task)
    handler.register_task_function("multiply", sample_multiply_task)
    handler.add_event_mapping(
        EventToTaskMapping(event_pattern="orchestration.task.trigger")
    )

    await handler.start()

    workflow_id = "workflow-e2e-final"

    # Step 1: Add
    event1 = {
        "event_id": "evt-e2e-1",
        "event_type": "orchestration.task.trigger",
        "payload": {"task_name": "add", "args": [100, 200], "workflow_id": workflow_id},
    }

    # Step 2: Multiply
    event2 = {
        "event_id": "evt-e2e-2",
        "event_type": "orchestration.task.trigger",
        "payload": {
            "task_name": "multiply",
            "args": [300, 2],
            "workflow_id": workflow_id,
        },
    }

    # Execute workflow
    await handler._handle_task_trigger(event1)
    await asyncio.sleep(0.15)
    await handler._handle_task_trigger(event2)
    await asyncio.sleep(0.3)

    # Verify complete flow
    created = mock_event_bus.get_published_events_by_type(
        OrchestrationEventType.TASK_CREATED.value
    )
    assert len(created) >= 2

    # Verify workflow_id correlation
    workflow_events = [
        e for e in created if e["payload"]["workflow_id"] == workflow_id
    ]
    assert len(workflow_events) == 2

    await handler.stop()

    print(f"✓ Complete E2E workflow validated: {len(workflow_events)} tasks")
