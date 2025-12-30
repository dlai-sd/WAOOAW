"""
Task Queue Core

Priority-based task queue with lifecycle management for orchestrating
multi-agent workflows.
"""

import asyncio
import heapq
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from waooaw.common.logging_framework import StructuredLogger


class TaskState(Enum):
    """Task lifecycle states"""

    PENDING = "pending"  # Queued, waiting to run
    RUNNING = "running"  # Currently executing
    COMPLETED = "completed"  # Successfully finished
    FAILED = "failed"  # Execution failed
    CANCELLED = "cancelled"  # Manually cancelled
    TIMEOUT = "timeout"  # Exceeded execution time limit


class TaskPriority(Enum):
    """Task priority levels"""

    CRITICAL = 0  # Highest priority
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4  # Lowest priority


class TaskNotFoundError(Exception):
    """Raised when task not found in queue"""

    pass


class TaskQueueFullError(Exception):
    """Raised when queue capacity exceeded"""

    pass


@dataclass
class TaskMetadata:
    """Task metadata for tracking and observability"""

    task_id: str
    name: str
    priority: TaskPriority
    state: TaskState
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    dependencies: Set[str] = field(default_factory=set)
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_seconds: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    error: Optional[str] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate task duration if completed"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_terminal(self) -> bool:
        """Check if task is in terminal state"""
        return self.state in {
            TaskState.COMPLETED,
            TaskState.FAILED,
            TaskState.CANCELLED,
            TaskState.TIMEOUT,
        }


@dataclass
class Task:
    """
    Task for execution in orchestration workflow
    
    Tasks are ordered by priority, then by creation time (FIFO within priority).
    """

    metadata: TaskMetadata
    payload: Dict[str, Any]
    handler: Optional[Callable] = None
    result: Optional[Any] = None

    def __lt__(self, other: "Task") -> bool:
        """Compare tasks for priority queue ordering"""
        # Lower priority value = higher priority
        if self.metadata.priority.value != other.metadata.priority.value:
            return self.metadata.priority.value < other.metadata.priority.value
        # Within same priority, FIFO by creation time
        return self.metadata.created_at < other.metadata.created_at

    def __hash__(self) -> int:
        """Hash by task_id for set operations"""
        return hash(self.metadata.task_id)

    def __eq__(self, other: object) -> bool:
        """Equality by task_id"""
        if not isinstance(other, Task):
            return False
        return self.metadata.task_id == other.metadata.task_id


@dataclass
class TaskStatistics:
    """Queue statistics for monitoring"""

    total_tasks: int = 0
    pending_tasks: int = 0
    running_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    cancelled_tasks: int = 0
    timeout_tasks: int = 0
    tasks_by_priority: Dict[TaskPriority, int] = field(default_factory=dict)
    average_duration_seconds: Optional[float] = None
    oldest_pending_task: Optional[datetime] = None


class TaskQueue:
    """
    Priority-based task queue with lifecycle management
    
    Features:
    - Priority-based ordering (CRITICAL to BACKGROUND)
    - Task state tracking (pending, running, completed, failed, etc.)
    - Timeout enforcement
    - Capacity limits
    - Queue statistics
    - Task retrieval and cancellation
    """

    def __init__(
        self,
        name: str = "default",
        max_capacity: Optional[int] = None,
        max_running: int = 10,
    ):
        """
        Initialize task queue
        
        Args:
            name: Queue identifier
            max_capacity: Maximum total tasks (None = unlimited)
            max_running: Maximum concurrent running tasks
        """
        self.name = name
        self.max_capacity = max_capacity
        self.max_running = max_running

        # Priority queue (min-heap)
        self._pending_queue: List[Task] = []
        
        # Task storage by ID
        self._tasks: Dict[str, Task] = {}
        
        # Tasks by state
        self._running: Set[str] = set()
        self._completed: Set[str] = set()
        self._failed: Set[str] = set()
        self._cancelled: Set[str] = set()
        self._timeout: Set[str] = set()

        # Workflow tracking
        self._workflows: Dict[str, Set[str]] = {}  # workflow_id -> task_ids

        # Statistics
        self._total_enqueued = 0
        self._total_completed = 0
        self._total_failed = 0
        
        # Lock for thread-safety
        self._lock = asyncio.Lock()
        
        # Logger
        self._logger = StructuredLogger(name=f"task-queue-{name}", level="INFO")

    async def enqueue(
        self,
        name: str,
        payload: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        agent_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        dependencies: Optional[Set[str]] = None,
        tags: Optional[Dict[str, str]] = None,
        timeout_seconds: Optional[float] = None,
        max_retries: int = 3,
        handler: Optional[Callable] = None,
    ) -> str:
        """
        Enqueue a new task
        
        Args:
            name: Task name/type
            payload: Task data
            priority: TaskPriority level
            agent_id: Agent responsible for task
            workflow_id: Workflow this task belongs to
            parent_task_id: Parent task ID (for subtasks)
            dependencies: Set of task IDs this depends on
            tags: Metadata tags
            timeout_seconds: Execution timeout
            max_retries: Maximum retry attempts
            handler: Optional async callable to execute task
            
        Returns:
            task_id: Unique task identifier
            
        Raises:
            TaskQueueFullError: If queue at capacity
        """
        async with self._lock:
            # Check capacity
            if self.max_capacity and len(self._tasks) >= self.max_capacity:
                raise TaskQueueFullError(
                    f"Queue '{self.name}' at capacity ({self.max_capacity})"
                )

            # Create task
            task_id = str(uuid.uuid4())
            metadata = TaskMetadata(
                task_id=task_id,
                name=name,
                priority=priority,
                state=TaskState.PENDING,
                agent_id=agent_id,
                workflow_id=workflow_id,
                parent_task_id=parent_task_id,
                dependencies=dependencies or set(),
                tags=tags or {},
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
            )

            task = Task(metadata=metadata, payload=payload, handler=handler)

            # Store task
            self._tasks[task_id] = task
            heapq.heappush(self._pending_queue, task)

            # Track workflow
            if workflow_id:
                if workflow_id not in self._workflows:
                    self._workflows[workflow_id] = set()
                self._workflows[workflow_id].add(task_id)

            self._total_enqueued += 1

            self._logger.info(
                "task_enqueued",
                extra={
                    "task_id": task_id,
                    "name": name,
                    "priority": priority.name,
                    "workflow_id": workflow_id,
                    "queue_size": len(self._pending_queue),
                },
            )

            return task_id

    async def dequeue(self, timeout: Optional[float] = None) -> Optional[Task]:
        """
        Dequeue next task by priority
        
        Args:
            timeout: Maximum wait time for task availability
            
        Returns:
            Task if available, None if timeout or empty
            
        Raises:
            None (returns None instead of blocking forever)
        """
        start_time = datetime.utcnow()

        while True:
            async with self._lock:
                # Check running capacity
                if len(self._running) >= self.max_running:
                    # Wait before retry
                    pass
                elif self._pending_queue:
                    # Get highest priority task
                    task = heapq.heappop(self._pending_queue)

                    # Update state
                    task.metadata.state = TaskState.RUNNING
                    task.metadata.started_at = datetime.utcnow()
                    self._running.add(task.metadata.task_id)

                    self._logger.info(
                        "task_dequeued",
                        extra={
                            "task_id": task.metadata.task_id,
                            "name": task.metadata.name,
                            "priority": task.metadata.priority.name,
                            "pending_count": len(self._pending_queue),
                            "running_count": len(self._running),
                        },
                    )

                    return task

            # Check timeout
            if timeout is not None:
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                if elapsed >= timeout:
                    return None

            # Wait before retry
            await asyncio.sleep(0.1)

    async def complete_task(
        self, task_id: str, result: Optional[Any] = None
    ) -> None:
        """
        Mark task as completed
        
        Args:
            task_id: Task identifier
            result: Task execution result
            
        Raises:
            TaskNotFoundError: If task doesn't exist
        """
        async with self._lock:
            if task_id not in self._tasks:
                raise TaskNotFoundError(f"Task {task_id} not found")

            task = self._tasks[task_id]
            task.metadata.state = TaskState.COMPLETED
            task.metadata.completed_at = datetime.utcnow()
            task.result = result

            # Update tracking
            self._running.discard(task_id)
            self._completed.add(task_id)
            self._total_completed += 1

            self._logger.info(
                "task_completed",
                extra={
                    "task_id": task_id,
                    "name": task.metadata.name,
                    "duration_seconds": task.metadata.duration_seconds,
                    "running_count": len(self._running),
                },
            )

    async def fail_task(self, task_id: str, error: str) -> None:
        """
        Mark task as failed
        
        Args:
            task_id: Task identifier
            error: Error message
            
        Raises:
            TaskNotFoundError: If task doesn't exist
        """
        async with self._lock:
            if task_id not in self._tasks:
                raise TaskNotFoundError(f"Task {task_id} not found")

            task = self._tasks[task_id]
            task.metadata.state = TaskState.FAILED
            task.metadata.completed_at = datetime.utcnow()
            task.metadata.error = error

            # Update tracking
            self._running.discard(task_id)
            self._failed.add(task_id)
            self._total_failed += 1

            self._logger.error(
                "task_failed",
                extra={
                    "task_id": task_id,
                    "name": task.metadata.name,
                    "error": error,
                    "retry_count": task.metadata.retry_count,
                    "running_count": len(self._running),
                },
            )

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending or running task
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if cancelled, False if already terminal
            
        Raises:
            TaskNotFoundError: If task doesn't exist
        """
        async with self._lock:
            if task_id not in self._tasks:
                raise TaskNotFoundError(f"Task {task_id} not found")

            task = self._tasks[task_id]

            # Can't cancel terminal tasks
            if task.metadata.is_terminal:
                return False

            # Update state
            task.metadata.state = TaskState.CANCELLED
            task.metadata.completed_at = datetime.utcnow()

            # Update tracking
            self._running.discard(task_id)
            self._cancelled.add(task_id)

            # Remove from pending queue if present
            try:
                self._pending_queue.remove(task)
                heapq.heapify(self._pending_queue)
            except ValueError:
                pass  # Not in pending queue

            self._logger.info(
                "task_cancelled",
                extra={
                    "task_id": task_id,
                    "name": task.metadata.name,
                    "running_count": len(self._running),
                },
            )

            return True

    async def get_task(self, task_id: str) -> Task:
        """
        Retrieve task by ID
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task object
            
        Raises:
            TaskNotFoundError: If task doesn't exist
        """
        async with self._lock:
            if task_id not in self._tasks:
                raise TaskNotFoundError(f"Task {task_id} not found")
            return self._tasks[task_id]

    async def get_workflow_tasks(self, workflow_id: str) -> List[Task]:
        """
        Get all tasks for a workflow
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            List of tasks in workflow
        """
        async with self._lock:
            task_ids = self._workflows.get(workflow_id, set())
            return [self._tasks[tid] for tid in task_ids if tid in self._tasks]

    async def get_statistics(self) -> TaskStatistics:
        """
        Get queue statistics
        
        Returns:
            TaskStatistics with current queue state
        """
        async with self._lock:
            # Count by priority
            by_priority: Dict[TaskPriority, int] = {}
            for task in self._pending_queue:
                priority = task.metadata.priority
                by_priority[priority] = by_priority.get(priority, 0) + 1

            # Calculate average duration
            durations = [
                task.metadata.duration_seconds
                for task in self._tasks.values()
                if task.metadata.duration_seconds is not None
            ]
            avg_duration = sum(durations) / len(durations) if durations else None

            # Find oldest pending
            oldest_pending = None
            if self._pending_queue:
                oldest_pending = min(
                    task.metadata.created_at for task in self._pending_queue
                )

            return TaskStatistics(
                total_tasks=len(self._tasks),
                pending_tasks=len(self._pending_queue),
                running_tasks=len(self._running),
                completed_tasks=len(self._completed),
                failed_tasks=len(self._failed),
                cancelled_tasks=len(self._cancelled),
                timeout_tasks=len(self._timeout),
                tasks_by_priority=by_priority,
                average_duration_seconds=avg_duration,
                oldest_pending_task=oldest_pending,
            )

    async def clear(self) -> None:
        """Clear all tasks from queue"""
        async with self._lock:
            self._pending_queue.clear()
            self._tasks.clear()
            self._running.clear()
            self._completed.clear()
            self._failed.clear()
            self._cancelled.clear()
            self._timeout.clear()
            self._workflows.clear()
            self._total_enqueued = 0
            self._total_completed = 0
            self._total_failed = 0

            self._logger.info("queue_cleared", extra={"queue_name": self.name})
