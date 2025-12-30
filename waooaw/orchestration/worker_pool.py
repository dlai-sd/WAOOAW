"""
Parallel Execution

Worker pool management for concurrent task execution with load balancing
and task distribution across multiple workers.
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

from waooaw.common.logging_framework import StructuredLogger
from waooaw.orchestration.task_queue import Task, TaskQueue, TaskState


class WorkerState(Enum):
    """Worker lifecycle states"""

    IDLE = "idle"  # Ready to accept work
    BUSY = "busy"  # Currently executing task
    STOPPED = "stopped"  # Shut down
    ERROR = "error"  # Error state, needs recovery


class WorkerPoolFullError(Exception):
    """Raised when worker pool at capacity"""

    pass


class NoWorkersAvailableError(Exception):
    """Raised when no workers available to handle task"""

    pass


@dataclass
class WorkerMetrics:
    """Performance metrics for a worker"""

    worker_id: str
    state: WorkerState
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time: float = 0.0
    current_task_id: Optional[str] = None
    current_task_start: Optional[datetime] = None
    last_active: datetime = field(default_factory=datetime.utcnow)
    error: Optional[str] = None

    @property
    def average_execution_time(self) -> float:
        """Calculate average task execution time"""
        if self.tasks_completed == 0:
            return 0.0
        return self.total_execution_time / self.tasks_completed

    @property
    def success_rate(self) -> float:
        """Calculate task success rate"""
        total = self.tasks_completed + self.tasks_failed
        if total == 0:
            return 1.0
        return self.tasks_completed / total


@dataclass
class WorkerPoolMetrics:
    """Metrics for entire worker pool"""

    total_workers: int
    idle_workers: int
    busy_workers: int
    stopped_workers: int
    total_tasks_completed: int
    total_tasks_failed: int
    average_execution_time: float
    pool_utilization: float  # Percentage of workers busy


class Worker:
    """
    Async worker for executing tasks from queue
    
    Workers pull tasks from a queue, execute them, and update
    task status on completion or failure.
    """

    def __init__(
        self,
        worker_id: str,
        task_queue: TaskQueue,
        max_execution_time: Optional[float] = None,
    ):
        """
        Initialize worker
        
        Args:
            worker_id: Unique worker identifier
            task_queue: Queue to pull tasks from
            max_execution_time: Maximum time for task execution (timeout)
        """
        self.worker_id = worker_id
        self.task_queue = task_queue
        self.max_execution_time = max_execution_time

        self._state = WorkerState.IDLE
        self._metrics = WorkerMetrics(worker_id=worker_id, state=WorkerState.IDLE)
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._logger = StructuredLogger(name=f"worker-{worker_id}", level="INFO")

    @property
    def state(self) -> WorkerState:
        """Get current worker state"""
        return self._state

    @property
    def metrics(self) -> WorkerMetrics:
        """Get worker metrics"""
        return self._metrics

    async def start(self) -> None:
        """Start worker task processing loop"""
        self._logger.info(
            "worker_started", extra={"worker_id": self.worker_id}
        )

        while not self._stop_event.is_set():
            try:
                # Wait for task from queue
                task = await self.task_queue.dequeue(timeout=1.0)

                if task is None:
                    # No task available, continue waiting
                    continue

                # Execute task
                await self._execute_task(task)

            except Exception as e:
                self._state = WorkerState.ERROR
                self._metrics.state = WorkerState.ERROR
                self._metrics.error = str(e)
                self._logger.error(
                    "worker_error",
                    extra={"worker_id": self.worker_id, "error": str(e)},
                )
                # Continue processing after error
                await asyncio.sleep(1.0)
                self._state = WorkerState.IDLE
                self._metrics.state = WorkerState.IDLE

        self._state = WorkerState.STOPPED
        self._metrics.state = WorkerState.STOPPED
        self._logger.info(
            "worker_stopped", extra={"worker_id": self.worker_id}
        )

    async def stop(self) -> None:
        """Stop worker gracefully"""
        self._stop_event.set()

        # Wait for current task to complete
        if self._task and not self._task.done():
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except asyncio.TimeoutError:
                self._task.cancel()

    async def _execute_task(self, task: Task) -> None:
        """
        Execute a single task
        
        Args:
            task: Task to execute
        """
        self._state = WorkerState.BUSY
        self._metrics.state = WorkerState.BUSY
        self._metrics.current_task_id = task.metadata.task_id
        self._metrics.current_task_start = datetime.utcnow()
        self._metrics.last_active = datetime.utcnow()

        start_time = time.time()

        self._logger.info(
            "task_execution_started",
            extra={
                "worker_id": self.worker_id,
                "task_id": task.metadata.task_id,
                "task_name": task.metadata.name,
            },
        )

        try:
            # Execute task handler if provided
            if task.handler:
                if self.max_execution_time:
                    result = await asyncio.wait_for(
                        task.handler(task.payload),
                        timeout=self.max_execution_time,
                    )
                else:
                    result = await task.handler(task.payload)

                # Mark task as completed
                await self.task_queue.complete_task(task.metadata.task_id, result)

            else:
                # No handler - just mark complete
                await self.task_queue.complete_task(task.metadata.task_id)

            # Update metrics
            execution_time = time.time() - start_time
            self._metrics.tasks_completed += 1
            self._metrics.total_execution_time += execution_time

            self._logger.info(
                "task_execution_completed",
                extra={
                    "worker_id": self.worker_id,
                    "task_id": task.metadata.task_id,
                    "execution_time": execution_time,
                },
            )

        except asyncio.TimeoutError:
            # Task exceeded max execution time
            error = f"Task exceeded max execution time ({self.max_execution_time}s)"
            await self.task_queue.fail_task(task.metadata.task_id, error)
            self._metrics.tasks_failed += 1

            self._logger.warning(
                "task_execution_timeout",
                extra={
                    "worker_id": self.worker_id,
                    "task_id": task.metadata.task_id,
                    "max_execution_time": self.max_execution_time,
                },
            )

        except Exception as e:
            # Task execution failed
            error = f"Task execution error: {str(e)}"
            await self.task_queue.fail_task(task.metadata.task_id, error)
            self._metrics.tasks_failed += 1

            self._logger.error(
                "task_execution_failed",
                extra={
                    "worker_id": self.worker_id,
                    "task_id": task.metadata.task_id,
                    "error": str(e),
                },
            )

        finally:
            # Reset worker state
            self._state = WorkerState.IDLE
            self._metrics.state = WorkerState.IDLE
            self._metrics.current_task_id = None
            self._metrics.current_task_start = None
            self._metrics.last_active = datetime.utcnow()


class WorkerPool:
    """
    Pool of workers for parallel task execution
    
    Features:
    - Dynamic worker pool sizing
    - Load balancing across workers
    - Worker health monitoring
    - Pool-level metrics and statistics
    """

    def __init__(
        self,
        task_queue: TaskQueue,
        min_workers: int = 1,
        max_workers: int = 10,
        max_execution_time: Optional[float] = None,
    ):
        """
        Initialize worker pool
        
        Args:
            task_queue: Queue for tasks
            min_workers: Minimum number of workers
            max_workers: Maximum number of workers
            max_execution_time: Maximum task execution time
        """
        if min_workers < 1:
            raise ValueError("min_workers must be at least 1")
        if max_workers < min_workers:
            raise ValueError("max_workers must be >= min_workers")

        self.task_queue = task_queue
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.max_execution_time = max_execution_time

        self._workers: Dict[str, Worker] = {}
        self._worker_tasks: Dict[str, asyncio.Task] = {}
        self._started = False
        self._logger = StructuredLogger(name="worker-pool", level="INFO")

    async def start(self) -> None:
        """Start worker pool with minimum workers"""
        if self._started:
            return

        self._logger.info(
            "worker_pool_starting",
            extra={
                "min_workers": self.min_workers,
                "max_workers": self.max_workers,
            },
        )

        # Start minimum workers
        for i in range(self.min_workers):
            await self._start_worker()

        self._started = True
        self._logger.info(
            "worker_pool_started",
            extra={"active_workers": len(self._workers)},
        )

    async def stop(self) -> None:
        """Stop all workers gracefully"""
        if not self._started:
            return

        self._logger.info(
            "worker_pool_stopping",
            extra={"active_workers": len(self._workers)},
        )

        # Stop all workers
        stop_tasks = [worker.stop() for worker in self._workers.values()]
        await asyncio.gather(*stop_tasks, return_exceptions=True)

        # Cancel all worker tasks
        for task in self._worker_tasks.values():
            if not task.done():
                task.cancel()

        # Wait for all tasks to finish
        await asyncio.gather(*self._worker_tasks.values(), return_exceptions=True)

        self._workers.clear()
        self._worker_tasks.clear()
        self._started = False

        self._logger.info("worker_pool_stopped")

    async def scale_up(self, count: int = 1) -> int:
        """
        Add workers to pool
        
        Args:
            count: Number of workers to add
            
        Returns:
            Number of workers actually added
            
        Raises:
            WorkerPoolFullError: If pool at max capacity
        """
        if not self._started:
            raise RuntimeError("Worker pool not started")

        added = 0
        for _ in range(count):
            if len(self._workers) >= self.max_workers:
                raise WorkerPoolFullError(
                    f"Worker pool at max capacity ({self.max_workers})"
                )

            await self._start_worker()
            added += 1

        self._logger.info(
            "worker_pool_scaled_up",
            extra={"added": added, "total_workers": len(self._workers)},
        )

        return added

    async def scale_down(self, count: int = 1) -> int:
        """
        Remove workers from pool
        
        Args:
            count: Number of workers to remove
            
        Returns:
            Number of workers actually removed
        """
        if not self._started:
            raise RuntimeError("Worker pool not started")

        # Find idle workers to stop
        idle_workers = [
            worker
            for worker in self._workers.values()
            if worker.state == WorkerState.IDLE
        ]

        # Don't go below minimum
        can_remove = min(
            count, len(idle_workers), len(self._workers) - self.min_workers
        )

        if can_remove <= 0:
            return 0

        # Stop workers
        for worker in idle_workers[:can_remove]:
            await self._stop_worker(worker.worker_id)

        self._logger.info(
            "worker_pool_scaled_down",
            extra={"removed": can_remove, "total_workers": len(self._workers)},
        )

        return can_remove

    async def get_metrics(self) -> WorkerPoolMetrics:
        """
        Get pool-level metrics
        
        Returns:
            WorkerPoolMetrics with aggregate statistics
        """
        idle_count = 0
        busy_count = 0
        stopped_count = 0
        total_completed = 0
        total_failed = 0
        total_execution_time = 0.0

        for worker in self._workers.values():
            metrics = worker.metrics

            if metrics.state == WorkerState.IDLE:
                idle_count += 1
            elif metrics.state == WorkerState.BUSY:
                busy_count += 1
            elif metrics.state == WorkerState.STOPPED:
                stopped_count += 1

            total_completed += metrics.tasks_completed
            total_failed += metrics.tasks_failed
            total_execution_time += metrics.total_execution_time

        avg_execution_time = (
            total_execution_time / total_completed if total_completed > 0 else 0.0
        )
        utilization = (
            busy_count / len(self._workers) if len(self._workers) > 0 else 0.0
        )

        return WorkerPoolMetrics(
            total_workers=len(self._workers),
            idle_workers=idle_count,
            busy_workers=busy_count,
            stopped_workers=stopped_count,
            total_tasks_completed=total_completed,
            total_tasks_failed=total_failed,
            average_execution_time=avg_execution_time,
            pool_utilization=utilization,
        )

    async def get_worker_metrics(self, worker_id: str) -> WorkerMetrics:
        """
        Get metrics for specific worker
        
        Args:
            worker_id: Worker identifier
            
        Returns:
            WorkerMetrics for the worker
            
        Raises:
            KeyError: If worker doesn't exist
        """
        if worker_id not in self._workers:
            raise KeyError(f"Worker {worker_id} not found")

        return self._workers[worker_id].metrics

    def get_worker_ids(self) -> List[str]:
        """Get list of all worker IDs"""
        return list(self._workers.keys())

    async def _start_worker(self) -> str:
        """Start a new worker"""
        worker_id = f"worker-{str(uuid4())[:8]}"
        worker = Worker(
            worker_id=worker_id,
            task_queue=self.task_queue,
            max_execution_time=self.max_execution_time,
        )

        self._workers[worker_id] = worker
        self._worker_tasks[worker_id] = asyncio.create_task(worker.start())

        self._logger.info(
            "worker_started", extra={"worker_id": worker_id}
        )

        return worker_id

    async def _stop_worker(self, worker_id: str) -> None:
        """Stop a specific worker"""
        if worker_id not in self._workers:
            return

        worker = self._workers[worker_id]
        await worker.stop()

        # Cancel task
        task = self._worker_tasks[worker_id]
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        del self._workers[worker_id]
        del self._worker_tasks[worker_id]

        self._logger.info(
            "worker_stopped", extra={"worker_id": worker_id}
        )
