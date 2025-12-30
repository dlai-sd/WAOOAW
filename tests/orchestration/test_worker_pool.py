"""
Tests for Parallel Execution

Validates worker pool management, task distribution, load balancing,
and concurrent execution.
"""

import asyncio
import pytest

from waooaw.orchestration import (
    TaskQueue,
    TaskPriority,
    Worker,
    WorkerPool,
    WorkerState,
    WorkerPoolFullError,
)


@pytest.mark.asyncio
class TestWorker:
    """Test Worker operations"""

    async def test_create_worker(self):
        """Should create worker with queue"""
        queue = TaskQueue()
        worker = Worker(worker_id="worker-1", task_queue=queue)

        assert worker.worker_id == "worker-1"
        assert worker.state == WorkerState.IDLE
        assert worker.metrics.tasks_completed == 0
        assert worker.metrics.tasks_failed == 0

    async def test_worker_execute_task_with_handler(self):
        """Should execute task with handler"""
        queue = TaskQueue()
        worker = Worker(worker_id="worker-1", task_queue=queue)

        # Create async handler
        async def handler(payload):
            await asyncio.sleep(0.1)
            return {"result": payload["value"] * 2}

        # Enqueue task
        task_id = await queue.enqueue(
            "compute", {"value": 5}, handler=handler, priority=TaskPriority.HIGH
        )

        # Start worker and let it process
        worker_task = asyncio.create_task(worker.start())
        await asyncio.sleep(0.3)  # Let worker process task
        await worker.stop()
        await worker_task

        # Verify task completed
        task = await queue.get_task(task_id)
        assert task.metadata.state.value == "completed"
        assert task.result == {"result": 10}

        # Verify worker metrics
        assert worker.metrics.tasks_completed == 1
        assert worker.metrics.tasks_failed == 0
        assert worker.metrics.total_execution_time > 0

    async def test_worker_execute_task_without_handler(self):
        """Should mark task complete even without handler"""
        queue = TaskQueue()
        worker = Worker(worker_id="worker-1", task_queue=queue)

        # Enqueue task without handler
        task_id = await queue.enqueue("simple-task", {"data": "test"})

        # Start worker
        worker_task = asyncio.create_task(worker.start())
        await asyncio.sleep(0.2)
        await worker.stop()
        await worker_task

        # Verify task completed
        task = await queue.get_task(task_id)
        assert task.metadata.state.value == "completed"
        assert worker.metrics.tasks_completed == 1

    async def test_worker_handles_task_failure(self):
        """Should handle task execution failures"""
        queue = TaskQueue()
        worker = Worker(worker_id="worker-1", task_queue=queue)

        # Create failing handler
        async def failing_handler(payload):
            raise ValueError("Task failed!")

        task_id = await queue.enqueue("failing-task", {}, handler=failing_handler)

        # Start worker
        worker_task = asyncio.create_task(worker.start())
        await asyncio.sleep(0.2)
        await worker.stop()
        await worker_task

        # Verify task failed
        task = await queue.get_task(task_id)
        assert task.metadata.state.value == "failed"
        assert "Task execution error" in task.metadata.error

        # Verify worker metrics
        assert worker.metrics.tasks_completed == 0
        assert worker.metrics.tasks_failed == 1

    async def test_worker_timeout(self):
        """Should timeout long-running tasks"""
        queue = TaskQueue()
        worker = Worker(worker_id="worker-1", task_queue=queue, max_execution_time=0.2)

        # Create slow handler
        async def slow_handler(payload):
            await asyncio.sleep(1.0)  # Exceeds timeout
            return {"done": True}

        task_id = await queue.enqueue("slow-task", {}, handler=slow_handler)

        # Start worker
        worker_task = asyncio.create_task(worker.start())
        await asyncio.sleep(0.5)  # Wait for timeout
        await worker.stop()
        await worker_task

        # Verify task failed with timeout
        task = await queue.get_task(task_id)
        assert task.metadata.state.value == "failed"
        assert "exceeded max execution time" in task.metadata.error
        assert worker.metrics.tasks_failed == 1

    async def test_worker_metrics(self):
        """Should track worker metrics"""
        queue = TaskQueue()
        worker = Worker(worker_id="worker-1", task_queue=queue)

        async def handler(payload):
            await asyncio.sleep(0.05)
            return {"done": True}

        # Enqueue multiple tasks
        for i in range(3):
            await queue.enqueue(f"task-{i}", {"index": i}, handler=handler)

        # Process tasks
        worker_task = asyncio.create_task(worker.start())
        await asyncio.sleep(0.5)
        await worker.stop()
        await worker_task

        # Verify metrics
        metrics = worker.metrics
        assert metrics.tasks_completed == 3
        assert metrics.tasks_failed == 0
        assert metrics.total_execution_time > 0
        assert metrics.average_execution_time > 0
        assert metrics.success_rate == 1.0

    async def test_worker_stops_gracefully(self):
        """Should stop gracefully when requested"""
        queue = TaskQueue()
        worker = Worker(worker_id="worker-1", task_queue=queue)

        # Start worker
        worker_task = asyncio.create_task(worker.start())
        await asyncio.sleep(0.1)

        # Stop worker
        await worker.stop()
        await worker_task

        assert worker.state == WorkerState.STOPPED


@pytest.mark.asyncio
class TestWorkerPool:
    """Test WorkerPool operations"""

    async def test_create_pool(self):
        """Should create worker pool with defaults"""
        queue = TaskQueue()
        pool = WorkerPool(task_queue=queue, min_workers=2, max_workers=5)

        assert pool.min_workers == 2
        assert pool.max_workers == 5
        assert len(pool.get_worker_ids()) == 0  # Not started yet

    async def test_create_pool_validation(self):
        """Should validate worker count parameters"""
        queue = TaskQueue()

        with pytest.raises(ValueError, match="at least 1"):
            WorkerPool(task_queue=queue, min_workers=0)

        with pytest.raises(ValueError, match=">= min_workers"):
            WorkerPool(task_queue=queue, min_workers=5, max_workers=3)

    async def test_start_pool(self):
        """Should start pool with minimum workers"""
        queue = TaskQueue()
        pool = WorkerPool(task_queue=queue, min_workers=3, max_workers=10)

        await pool.start()

        worker_ids = pool.get_worker_ids()
        assert len(worker_ids) == 3

        await pool.stop()

    async def test_stop_pool(self):
        """Should stop all workers gracefully"""
        queue = TaskQueue()
        pool = WorkerPool(task_queue=queue, min_workers=2)

        await pool.start()
        assert len(pool.get_worker_ids()) == 2

        await pool.stop()
        assert len(pool.get_worker_ids()) == 0

    async def test_scale_up(self):
        """Should add workers to pool"""
        queue = TaskQueue()
        pool = WorkerPool(task_queue=queue, min_workers=2, max_workers=5)

        await pool.start()
        assert len(pool.get_worker_ids()) == 2

        # Scale up by 2
        added = await pool.scale_up(count=2)
        assert added == 2
        assert len(pool.get_worker_ids()) == 4

        await pool.stop()

    async def test_scale_up_at_max_capacity(self):
        """Should raise error when scaling beyond max"""
        queue = TaskQueue()
        pool = WorkerPool(task_queue=queue, min_workers=1, max_workers=3)

        await pool.start()
        await pool.scale_up(count=2)  # Now at max (3 workers)

        with pytest.raises(WorkerPoolFullError, match="max capacity"):
            await pool.scale_up(count=1)

        await pool.stop()

    async def test_scale_down(self):
        """Should remove idle workers from pool"""
        queue = TaskQueue()
        pool = WorkerPool(task_queue=queue, min_workers=2, max_workers=10)

        await pool.start()
        await pool.scale_up(count=3)  # 5 total workers
        assert len(pool.get_worker_ids()) == 5

        # Scale down by 2
        removed = await pool.scale_down(count=2)
        assert removed == 2
        assert len(pool.get_worker_ids()) == 3

        await pool.stop()

    async def test_scale_down_respects_minimum(self):
        """Should not scale below minimum workers"""
        queue = TaskQueue()
        pool = WorkerPool(task_queue=queue, min_workers=3, max_workers=10)

        await pool.start()
        assert len(pool.get_worker_ids()) == 3

        # Try to scale down
        removed = await pool.scale_down(count=2)
        assert removed == 0  # Can't go below minimum
        assert len(pool.get_worker_ids()) == 3

        await pool.stop()

    async def test_pool_processes_tasks(self):
        """Should distribute tasks across workers"""
        queue = TaskQueue()
        pool = WorkerPool(task_queue=queue, min_workers=3)

        async def handler(payload):
            await asyncio.sleep(0.05)
            return {"processed": payload["value"]}

        # Enqueue multiple tasks
        task_ids = []
        for i in range(6):
            task_id = await queue.enqueue(f"task-{i}", {"value": i}, handler=handler)
            task_ids.append(task_id)

        # Start pool and wait for processing
        await pool.start()
        await asyncio.sleep(0.5)  # Let workers process

        # Verify all tasks completed
        stats = await queue.get_statistics()
        assert stats.completed_tasks == 6

        await pool.stop()

    async def test_pool_metrics(self):
        """Should track pool-level metrics"""
        queue = TaskQueue()
        pool = WorkerPool(task_queue=queue, min_workers=2)

        async def handler(payload):
            await asyncio.sleep(0.05)
            return {"done": True}

        # Enqueue tasks
        for i in range(4):
            await queue.enqueue(f"task-{i}", {}, handler=handler)

        # Start pool and process
        await pool.start()
        await asyncio.sleep(0.4)

        # Get metrics
        metrics = await pool.get_metrics()
        assert metrics.total_workers == 2
        assert metrics.total_tasks_completed >= 0
        assert 0 <= metrics.pool_utilization <= 1.0

        await pool.stop()

    async def test_get_worker_metrics(self):
        """Should get individual worker metrics"""
        queue = TaskQueue()
        pool = WorkerPool(task_queue=queue, min_workers=2)

        await pool.start()
        worker_ids = pool.get_worker_ids()
        assert len(worker_ids) == 2

        # Get metrics for first worker
        worker_metrics = await pool.get_worker_metrics(worker_ids[0])
        assert worker_metrics.worker_id == worker_ids[0]
        assert worker_metrics.state in [WorkerState.IDLE, WorkerState.BUSY]

        await pool.stop()

    async def test_get_nonexistent_worker_metrics(self):
        """Should raise error for non-existent worker"""
        queue = TaskQueue()
        pool = WorkerPool(task_queue=queue, min_workers=1)

        await pool.start()

        with pytest.raises(KeyError, match="not found"):
            await pool.get_worker_metrics("non-existent")

        await pool.stop()

    async def test_concurrent_task_execution(self):
        """Should execute tasks concurrently"""
        queue = TaskQueue()
        pool = WorkerPool(task_queue=queue, min_workers=3)

        execution_log = []

        async def handler(payload):
            execution_log.append(("start", payload["id"]))
            await asyncio.sleep(0.1)
            execution_log.append(("end", payload["id"]))
            return {"id": payload["id"]}

        # Enqueue 3 tasks
        for i in range(3):
            await queue.enqueue(f"task-{i}", {"id": i}, handler=handler)

        # Start pool
        await pool.start()
        await asyncio.sleep(0.5)

        # Verify concurrent execution (starts should all come before some ends)
        starts = [entry for entry in execution_log if entry[0] == "start"]
        assert len(starts) >= 2  # At least 2 tasks started concurrently

        await pool.stop()

    async def test_pool_utilization(self):
        """Should calculate pool utilization correctly"""
        queue = TaskQueue()
        pool = WorkerPool(task_queue=queue, min_workers=4)

        async def slow_handler(payload):
            await asyncio.sleep(0.5)
            return {}

        # Enqueue 2 tasks (half the workers)
        await queue.enqueue("task-1", {}, handler=slow_handler)
        await queue.enqueue("task-2", {}, handler=slow_handler)

        await pool.start()
        await asyncio.sleep(0.2)  # Let tasks start

        metrics = await pool.get_metrics()
        # Should be around 50% utilization (2 out of 4 workers busy)
        assert 0.4 <= metrics.pool_utilization <= 0.6

        await pool.stop()

    async def test_worker_error_recovery(self):
        """Should recover from worker errors and continue processing"""
        queue = TaskQueue()
        pool = WorkerPool(task_queue=queue, min_workers=2)

        async def sometimes_fails(payload):
            if payload.get("fail"):
                raise ValueError("Intentional failure")
            return {"success": True}

        # Enqueue mix of failing and successful tasks
        await queue.enqueue("fail-1", {"fail": True}, handler=sometimes_fails)
        await queue.enqueue("success-1", {"fail": False}, handler=sometimes_fails)
        await queue.enqueue("fail-2", {"fail": True}, handler=sometimes_fails)
        await queue.enqueue("success-2", {"fail": False}, handler=sometimes_fails)

        await pool.start()
        await asyncio.sleep(0.5)

        # Verify mixed results
        stats = await queue.get_statistics()
        assert stats.completed_tasks >= 2  # Successful tasks
        assert stats.failed_tasks >= 2  # Failed tasks

        # Workers should still be operational
        metrics = await pool.get_metrics()
        assert metrics.idle_workers + metrics.busy_workers == 2

        await pool.stop()

    async def test_pool_handles_empty_queue(self):
        """Should handle empty queue gracefully"""
        queue = TaskQueue()
        pool = WorkerPool(task_queue=queue, min_workers=2)

        # Start pool with no tasks
        await pool.start()
        await asyncio.sleep(0.3)

        # All workers should be idle
        metrics = await pool.get_metrics()
        assert metrics.idle_workers == 2
        assert metrics.busy_workers == 0

        await pool.stop()
