"""
Tests for Task Queue Core

Validates priority-based queuing, lifecycle management, and statistics.
"""

import asyncio
import pytest
from datetime import datetime, timedelta

from waooaw.orchestration import (
    Task,
    TaskQueue,
    TaskState,
    TaskPriority,
    TaskMetadata,
    TaskStatistics,
    TaskNotFoundError,
    TaskQueueFullError,
)


@pytest.mark.asyncio
class TestTaskMetadata:
    """Test TaskMetadata dataclass"""

    def test_create_metadata(self):
        """Should create metadata with defaults"""
        metadata = TaskMetadata(
            task_id="task-1",
            name="test-task",
            priority=TaskPriority.NORMAL,
            state=TaskState.PENDING,
        )

        assert metadata.task_id == "task-1"
        assert metadata.name == "test-task"
        assert metadata.priority == TaskPriority.NORMAL
        assert metadata.state == TaskState.PENDING
        assert metadata.agent_id is None
        assert metadata.workflow_id is None
        assert metadata.retry_count == 0
        assert metadata.max_retries == 3
        assert isinstance(metadata.created_at, datetime)

    def test_duration_calculation(self):
        """Should calculate task duration"""
        metadata = TaskMetadata(
            task_id="task-1",
            name="test-task",
            priority=TaskPriority.NORMAL,
            state=TaskState.RUNNING,
        )
        metadata.started_at = datetime.utcnow()
        metadata.completed_at = metadata.started_at + timedelta(seconds=5)

        assert metadata.duration_seconds == pytest.approx(5.0, abs=0.1)

    def test_duration_none_when_not_completed(self):
        """Should return None for duration if not completed"""
        metadata = TaskMetadata(
            task_id="task-1",
            name="test-task",
            priority=TaskPriority.NORMAL,
            state=TaskState.RUNNING,
        )
        metadata.started_at = datetime.utcnow()

        assert metadata.duration_seconds is None

    def test_is_terminal(self):
        """Should identify terminal states"""
        terminal_states = [
            TaskState.COMPLETED,
            TaskState.FAILED,
            TaskState.CANCELLED,
            TaskState.TIMEOUT,
        ]

        for state in terminal_states:
            metadata = TaskMetadata(
                task_id="task-1",
                name="test-task",
                priority=TaskPriority.NORMAL,
                state=state,
            )
            assert metadata.is_terminal is True

        # Non-terminal states
        for state in [TaskState.PENDING, TaskState.RUNNING]:
            metadata = TaskMetadata(
                task_id="task-1",
                name="test-task",
                priority=TaskPriority.NORMAL,
                state=state,
            )
            assert metadata.is_terminal is False


@pytest.mark.asyncio
class TestTask:
    """Test Task dataclass"""

    def test_create_task(self):
        """Should create task with metadata"""
        metadata = TaskMetadata(
            task_id="task-1",
            name="test-task",
            priority=TaskPriority.HIGH,
            state=TaskState.PENDING,
        )
        task = Task(metadata=metadata, payload={"key": "value"})

        assert task.metadata == metadata
        assert task.payload == {"key": "value"}
        assert task.handler is None
        assert task.result is None

    def test_task_comparison_by_priority(self):
        """Should compare tasks by priority"""
        task_high = Task(
            metadata=TaskMetadata(
                task_id="task-1",
                name="high",
                priority=TaskPriority.HIGH,
                state=TaskState.PENDING,
            ),
            payload={},
        )
        task_low = Task(
            metadata=TaskMetadata(
                task_id="task-2",
                name="low",
                priority=TaskPriority.LOW,
                state=TaskState.PENDING,
            ),
            payload={},
        )

        # High priority < Low priority (for min-heap)
        assert task_high < task_low

    def test_task_comparison_fifo_within_priority(self):
        """Should use FIFO within same priority"""
        now = datetime.utcnow()
        task1 = Task(
            metadata=TaskMetadata(
                task_id="task-1",
                name="first",
                priority=TaskPriority.NORMAL,
                state=TaskState.PENDING,
                created_at=now,
            ),
            payload={},
        )
        task2 = Task(
            metadata=TaskMetadata(
                task_id="task-2",
                name="second",
                priority=TaskPriority.NORMAL,
                state=TaskState.PENDING,
                created_at=now + timedelta(seconds=1),
            ),
            payload={},
        )

        # Earlier created task < later created task
        assert task1 < task2

    def test_task_equality(self):
        """Should check equality by task_id"""
        metadata1 = TaskMetadata(
            task_id="task-1",
            name="test",
            priority=TaskPriority.NORMAL,
            state=TaskState.PENDING,
        )
        metadata2 = TaskMetadata(
            task_id="task-1",  # Same ID
            name="different",
            priority=TaskPriority.HIGH,
            state=TaskState.RUNNING,
        )
        task1 = Task(metadata=metadata1, payload={})
        task2 = Task(metadata=metadata2, payload={})

        assert task1 == task2

    def test_task_hash(self):
        """Should hash by task_id"""
        task = Task(
            metadata=TaskMetadata(
                task_id="task-1",
                name="test",
                priority=TaskPriority.NORMAL,
                state=TaskState.PENDING,
            ),
            payload={},
        )

        assert hash(task) == hash("task-1")


@pytest.mark.asyncio
class TestTaskQueue:
    """Test TaskQueue operations"""

    async def test_create_queue(self):
        """Should create queue with defaults"""
        queue = TaskQueue(name="test-queue")

        assert queue.name == "test-queue"
        assert queue.max_capacity is None
        assert queue.max_running == 10

    async def test_enqueue_task(self):
        """Should enqueue task successfully"""
        queue = TaskQueue()

        task_id = await queue.enqueue(
            name="test-task", payload={"key": "value"}, priority=TaskPriority.HIGH
        )

        assert task_id is not None
        assert len(task_id) == 36  # UUID format

        # Verify task stored
        task = await queue.get_task(task_id)
        assert task.metadata.task_id == task_id
        assert task.metadata.name == "test-task"
        assert task.metadata.priority == TaskPriority.HIGH
        assert task.metadata.state == TaskState.PENDING
        assert task.payload == {"key": "value"}

    async def test_enqueue_with_metadata(self):
        """Should enqueue task with full metadata"""
        queue = TaskQueue()

        task_id = await queue.enqueue(
            name="complex-task",
            payload={"data": "value"},
            priority=TaskPriority.CRITICAL,
            agent_id="agent-1",
            workflow_id="workflow-1",
            parent_task_id="parent-1",
            dependencies={"dep-1", "dep-2"},
            tags={"env": "prod", "team": "backend"},
            timeout_seconds=30.0,
            max_retries=5,
        )

        task = await queue.get_task(task_id)
        assert task.metadata.agent_id == "agent-1"
        assert task.metadata.workflow_id == "workflow-1"
        assert task.metadata.parent_task_id == "parent-1"
        assert task.metadata.dependencies == {"dep-1", "dep-2"}
        assert task.metadata.tags == {"env": "prod", "team": "backend"}
        assert task.metadata.timeout_seconds == 30.0
        assert task.metadata.max_retries == 5

    async def test_enqueue_capacity_limit(self):
        """Should raise error when queue full"""
        queue = TaskQueue(max_capacity=2)

        await queue.enqueue("task-1", {})
        await queue.enqueue("task-2", {})

        with pytest.raises(TaskQueueFullError, match="at capacity"):
            await queue.enqueue("task-3", {})

    async def test_dequeue_by_priority(self):
        """Should dequeue highest priority task first"""
        queue = TaskQueue()

        # Enqueue tasks in random priority order
        task_low = await queue.enqueue("low", {}, priority=TaskPriority.LOW)
        task_high = await queue.enqueue("high", {}, priority=TaskPriority.HIGH)
        task_critical = await queue.enqueue(
            "critical", {}, priority=TaskPriority.CRITICAL
        )
        task_normal = await queue.enqueue("normal", {}, priority=TaskPriority.NORMAL)

        # Dequeue should get CRITICAL first
        task = await queue.dequeue()
        assert task.metadata.task_id == task_critical

        # Then HIGH
        task = await queue.dequeue()
        assert task.metadata.task_id == task_high

        # Then NORMAL
        task = await queue.dequeue()
        assert task.metadata.task_id == task_normal

        # Then LOW
        task = await queue.dequeue()
        assert task.metadata.task_id == task_low

    async def test_dequeue_fifo_within_priority(self):
        """Should dequeue FIFO within same priority"""
        queue = TaskQueue()

        task1 = await queue.enqueue("first", {}, priority=TaskPriority.NORMAL)
        await asyncio.sleep(0.01)  # Ensure different timestamps
        task2 = await queue.enqueue("second", {}, priority=TaskPriority.NORMAL)
        await asyncio.sleep(0.01)
        task3 = await queue.enqueue("third", {}, priority=TaskPriority.NORMAL)

        # Should dequeue in FIFO order
        task = await queue.dequeue()
        assert task.metadata.task_id == task1

        task = await queue.dequeue()
        assert task.metadata.task_id == task2

        task = await queue.dequeue()
        assert task.metadata.task_id == task3

    async def test_dequeue_updates_state(self):
        """Should update task state to RUNNING on dequeue"""
        queue = TaskQueue()

        task_id = await queue.enqueue("test", {})
        task = await queue.dequeue()

        assert task.metadata.state == TaskState.RUNNING
        assert task.metadata.started_at is not None
        assert isinstance(task.metadata.started_at, datetime)

    async def test_dequeue_empty_queue_timeout(self):
        """Should return None when queue empty and timeout"""
        queue = TaskQueue()

        task = await queue.dequeue(timeout=0.1)
        assert task is None

    async def test_dequeue_respects_max_running(self):
        """Should not exceed max_running limit"""
        queue = TaskQueue(max_running=2)

        # Enqueue 3 tasks
        await queue.enqueue("task-1", {})
        await queue.enqueue("task-2", {})
        await queue.enqueue("task-3", {})

        # Dequeue 2 tasks
        task1 = await queue.dequeue()
        task2 = await queue.dequeue()
        assert task1 is not None
        assert task2 is not None

        # Third dequeue should timeout (max_running reached)
        task3 = await queue.dequeue(timeout=0.2)
        assert task3 is None

    async def test_complete_task(self):
        """Should mark task as completed"""
        queue = TaskQueue()

        task_id = await queue.enqueue("test", {})
        task = await queue.dequeue()

        await queue.complete_task(task_id, result={"status": "success"})

        task = await queue.get_task(task_id)
        assert task.metadata.state == TaskState.COMPLETED
        assert task.metadata.completed_at is not None
        assert task.result == {"status": "success"}
        assert task.metadata.duration_seconds is not None

    async def test_fail_task(self):
        """Should mark task as failed"""
        queue = TaskQueue()

        task_id = await queue.enqueue("test", {})
        task = await queue.dequeue()

        await queue.fail_task(task_id, error="Something went wrong")

        task = await queue.get_task(task_id)
        assert task.metadata.state == TaskState.FAILED
        assert task.metadata.completed_at is not None
        assert task.metadata.error == "Something went wrong"

    async def test_cancel_pending_task(self):
        """Should cancel pending task"""
        queue = TaskQueue()

        task_id = await queue.enqueue("test", {})
        cancelled = await queue.cancel_task(task_id)

        assert cancelled is True

        task = await queue.get_task(task_id)
        assert task.metadata.state == TaskState.CANCELLED
        assert task.metadata.completed_at is not None

        # Should not be dequeueable
        dequeued = await queue.dequeue(timeout=0.1)
        assert dequeued is None

    async def test_cancel_running_task(self):
        """Should cancel running task"""
        queue = TaskQueue()

        task_id = await queue.enqueue("test", {})
        await queue.dequeue()  # Start task

        cancelled = await queue.cancel_task(task_id)
        assert cancelled is True

        task = await queue.get_task(task_id)
        assert task.metadata.state == TaskState.CANCELLED

    async def test_cancel_terminal_task(self):
        """Should not cancel already completed task"""
        queue = TaskQueue()

        task_id = await queue.enqueue("test", {})
        await queue.dequeue()
        await queue.complete_task(task_id)

        cancelled = await queue.cancel_task(task_id)
        assert cancelled is False

        task = await queue.get_task(task_id)
        assert task.metadata.state == TaskState.COMPLETED  # Still completed

    async def test_get_task_not_found(self):
        """Should raise error for non-existent task"""
        queue = TaskQueue()

        with pytest.raises(TaskNotFoundError, match="not found"):
            await queue.get_task("non-existent")

    async def test_get_workflow_tasks(self):
        """Should retrieve all tasks for workflow"""
        queue = TaskQueue()

        # Enqueue tasks for workflow
        task1 = await queue.enqueue("task-1", {}, workflow_id="workflow-1")
        task2 = await queue.enqueue("task-2", {}, workflow_id="workflow-1")
        task3 = await queue.enqueue("task-3", {}, workflow_id="workflow-2")

        # Get workflow tasks
        workflow_tasks = await queue.get_workflow_tasks("workflow-1")
        assert len(workflow_tasks) == 2
        task_ids = {t.metadata.task_id for t in workflow_tasks}
        assert task_ids == {task1, task2}

    async def test_get_statistics(self):
        """Should return queue statistics"""
        queue = TaskQueue()

        # Enqueue various tasks
        task1 = await queue.enqueue("task-1", {}, priority=TaskPriority.HIGH)
        task2 = await queue.enqueue("task-2", {}, priority=TaskPriority.NORMAL)
        task3 = await queue.enqueue("task-3", {}, priority=TaskPriority.NORMAL)

        # Complete one task
        await queue.dequeue()
        await queue.complete_task(task1)

        # Fail one task
        await queue.dequeue()
        await queue.fail_task(task2, "error")

        # Get statistics
        stats = await queue.get_statistics()
        assert stats.total_tasks == 3
        assert stats.pending_tasks == 1  # task3
        assert stats.running_tasks == 0
        assert stats.completed_tasks == 1
        assert stats.failed_tasks == 1
        assert stats.cancelled_tasks == 0
        assert stats.tasks_by_priority[TaskPriority.NORMAL] == 1  # task3 pending

    async def test_statistics_average_duration(self):
        """Should calculate average task duration"""
        queue = TaskQueue()

        # Enqueue and complete tasks
        task1 = await queue.enqueue("task-1", {})
        task = await queue.dequeue()
        await asyncio.sleep(0.1)
        await queue.complete_task(task1)

        task2 = await queue.enqueue("task-2", {})
        task = await queue.dequeue()
        await asyncio.sleep(0.2)
        await queue.complete_task(task2)

        # Get statistics
        stats = await queue.get_statistics()
        assert stats.average_duration_seconds is not None
        assert 0.1 < stats.average_duration_seconds < 0.3

    async def test_clear_queue(self):
        """Should clear all tasks"""
        queue = TaskQueue()

        # Enqueue tasks
        await queue.enqueue("task-1", {})
        await queue.enqueue("task-2", {})

        await queue.clear()

        # Verify empty
        stats = await queue.get_statistics()
        assert stats.total_tasks == 0
        assert stats.pending_tasks == 0

    async def test_concurrent_enqueue(self):
        """Should handle concurrent enqueues"""
        queue = TaskQueue()

        async def enqueue_task(i: int):
            await queue.enqueue(f"task-{i}", {"index": i})

        # Enqueue 10 tasks concurrently
        await asyncio.gather(*[enqueue_task(i) for i in range(10)])

        stats = await queue.get_statistics()
        assert stats.total_tasks == 10
        assert stats.pending_tasks == 10

    async def test_concurrent_dequeue(self):
        """Should handle concurrent dequeues"""
        queue = TaskQueue(max_running=5)

        # Enqueue 5 tasks
        for i in range(5):
            await queue.enqueue(f"task-{i}", {})

        async def dequeue_and_complete():
            task = await queue.dequeue()
            if task:
                await asyncio.sleep(0.05)
                await queue.complete_task(task.metadata.task_id)

        # Dequeue 5 tasks concurrently
        await asyncio.gather(*[dequeue_and_complete() for _ in range(5)])

        stats = await queue.get_statistics()
        assert stats.completed_tasks == 5
        assert stats.pending_tasks == 0
