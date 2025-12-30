"""
Event-Driven Orchestration Adapter

Story 3: Event-Driven Task Orchestration (Epic 3.4)
Points: 8

Bridges the Event Bus and Orchestration Runtime, enabling:
- Task triggering via events (orchestration.task.trigger)
- Task lifecycle event publishing (task.created, started, completed, failed)
- Automatic event-to-task conversion
- Result publishing to event bus

Architecture:
┌─────────────────────────────────────────────────────────────┐
│                      Event Bus                              │
│  orchestration.task.trigger → orchestration.task.created    │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▲
     ┌─────────────────────┐       ┌─────────────────────┐
     │ EventToTaskMapper   │       │ TaskEventPublisher  │
     │ (Event → Task)      │       │ (Task → Event)      │
     └─────────────────────┘       └─────────────────────┘
               │                              ▲
               ▼                              │
┌─────────────────────────────────────────────────────────────┐
│              OrchestrationEventHandler                      │
│  - Subscribe to trigger events                              │
│  - Create tasks from events                                 │
│  - Publish lifecycle events                                 │
│  - Track event-task correlation                             │
└─────────────────────────────────────────────────────────────┘
               │                              ▲
               ▼                              │
┌─────────────────────────────────────────────────────────────┐
│                  Orchestration Runtime                      │
│  TaskQueue → DependencyGraph → WorkerPool                   │
└─────────────────────────────────────────────────────────────┘
"""

import asyncio
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum

from waooaw.orchestration import (
    Task,
    TaskQueue,
    TaskPriority,
    TaskState,
    TaskMetadata,
    WorkerPool,
)

logger = logging.getLogger(__name__)


class OrchestrationEventType(str, Enum):
    """Event types for orchestration integration"""

    # Trigger events (incoming)
    TASK_TRIGGER = "orchestration.task.trigger"
    WORKFLOW_START = "orchestration.workflow.start"
    WORKFLOW_STOP = "orchestration.workflow.stop"

    # Task lifecycle events (outgoing)
    TASK_CREATED = "orchestration.task.created"
    TASK_STARTED = "orchestration.task.started"
    TASK_COMPLETED = "orchestration.task.completed"
    TASK_FAILED = "orchestration.task.failed"
    TASK_CANCELLED = "orchestration.task.cancelled"
    TASK_TIMEOUT = "orchestration.task.timeout"

    # Metrics events (outgoing)
    METRICS_SNAPSHOT = "orchestration.metrics.snapshot"
    WORKER_POOL_STATUS = "orchestration.worker_pool.status"


@dataclass
class EventToTaskMapping:
    """Configuration for converting events to tasks"""

    event_pattern: str  # Event pattern to match (e.g., "orchestration.task.*")
    task_name_field: str = "task_name"  # Field in event payload with task name
    task_args_field: str = "args"  # Field in event payload with task args
    task_kwargs_field: str = "kwargs"  # Field with task kwargs
    priority_field: str = "priority"  # Field with priority
    workflow_id_field: str = "workflow_id"  # Field with workflow ID
    timeout_field: str = "timeout_seconds"  # Field with timeout
    default_priority: TaskPriority = TaskPriority.NORMAL


class EventToTaskMapper:
    """
    Converts Event Bus events to Orchestration tasks.

    Handles the mapping logic between event payloads and task parameters,
    including priority mapping, argument extraction, and validation.
    """

    def __init__(self, task_registry: Optional[Dict[str, Callable]] = None):
        """
        Initialize mapper.

        Args:
            task_registry: Map of task_name → function to execute
        """
        self.task_registry = task_registry or {}
        self.mappings: List[EventToTaskMapping] = []

    def register_task_function(self, name: str, func: Callable) -> None:
        """Register a task function that can be invoked from events"""
        self.task_registry[name] = func
        logger.info(f"Registered task function: {name}")

    def add_mapping(self, mapping: EventToTaskMapping) -> None:
        """Add an event-to-task mapping configuration"""
        self.mappings.append(mapping)
        logger.info(f"Added event mapping for pattern: {mapping.event_pattern}")

    def map_event_to_task(
        self, event_type: str, payload: Dict[str, Any], event_id: str
    ) -> Optional[Task]:
        """
        Convert an event to a task.

        Args:
            event_type: Type of event received
            payload: Event payload with task parameters
            event_id: Event correlation ID

        Returns:
            Task object if mapping succeeds, None otherwise

        Example payload:
            {
                "task_name": "process_data",
                "args": ["data-123"],
                "kwargs": {"mode": "fast"},
                "priority": "HIGH",
                "workflow_id": "workflow-456",
                "timeout_seconds": 300
            }
        """
        # Find matching mapping
        mapping = self._find_mapping(event_type)
        if not mapping:
            logger.warning(f"No mapping found for event type: {event_type}")
            return None

        try:
            # Extract task parameters from payload
            task_name = payload.get(mapping.task_name_field)
            if not task_name:
                logger.error(f"Missing {mapping.task_name_field} in event payload")
                return None

            # Get task function
            func = self.task_registry.get(task_name)
            if not func:
                logger.error(f"Task function not registered: {task_name}")
                return None

            # Extract arguments
            args = payload.get(mapping.task_args_field, [])
            kwargs = payload.get(mapping.task_kwargs_field, {})

            # Extract priority
            priority_str = payload.get(mapping.priority_field, mapping.default_priority.name)
            try:
                priority = TaskPriority[priority_str.upper()]
            except (KeyError, AttributeError):
                priority = mapping.default_priority
                logger.warning(f"Invalid priority '{priority_str}', using {priority.name}")

            # Extract optional fields
            workflow_id = payload.get(mapping.workflow_id_field)
            timeout_seconds = payload.get(mapping.timeout_field)

            # Create task
            task = Task(
                name=task_name,
                func=func,
                args=args,
                kwargs=kwargs,
                priority=priority,
                workflow_id=workflow_id,
                timeout_seconds=timeout_seconds,
                metadata={"trigger_event_id": event_id, "event_type": event_type},
            )

            logger.info(
                f"Mapped event {event_type} → task {task_name} "
                f"(priority={priority.name}, workflow={workflow_id})"
            )
            return task

        except Exception as e:
            logger.error(f"Failed to map event to task: {e}", exc_info=True)
            return None

    def _find_mapping(self, event_type: str) -> Optional[EventToTaskMapping]:
        """Find mapping for event type (supports glob patterns)"""
        for mapping in self.mappings:
            # Simple pattern matching (can be enhanced with fnmatch)
            if mapping.event_pattern == "*" or mapping.event_pattern == event_type:
                return mapping
            # Check prefix matching (e.g., "orchestration.*" matches "orchestration.task.trigger")
            if mapping.event_pattern.endswith("*"):
                prefix = mapping.event_pattern[:-1]
                if event_type.startswith(prefix):
                    return mapping
        return None


class TaskEventPublisher:
    """
    Publishes task lifecycle events to the Event Bus.

    Converts orchestration task state changes into events that other
    agents can subscribe to.
    """

    def __init__(self, event_bus, source_agent: str = "orchestration-runtime"):
        """
        Initialize publisher.

        Args:
            event_bus: EventBus instance
            source_agent: Agent ID for published events
        """
        self.event_bus = event_bus
        self.source_agent = source_agent

    async def publish_task_created(
        self, task_id: str, task: Task, trigger_event_id: Optional[str] = None
    ) -> None:
        """Publish task.created event"""
        await self._publish_event(
            OrchestrationEventType.TASK_CREATED,
            {
                "task_id": task_id,
                "task_name": task.name,
                "priority": task.priority.name,
                "workflow_id": task.workflow_id,
                "trigger_event_id": trigger_event_id,
                "created_at": datetime.utcnow().isoformat(),
            },
        )

    async def publish_task_started(
        self, task_id: str, task_meta: TaskMetadata, worker_id: str
    ) -> None:
        """Publish task.started event"""
        await self._publish_event(
            OrchestrationEventType.TASK_STARTED,
            {
                "task_id": task_id,
                "task_name": task_meta.task.name,
                "worker_id": worker_id,
                "workflow_id": task_meta.task.workflow_id,
                "started_at": task_meta.started_at.isoformat() if task_meta.started_at else None,
            },
        )

    async def publish_task_completed(
        self, task_id: str, task_meta: TaskMetadata, result: Any, duration_ms: float
    ) -> None:
        """Publish task.completed event"""
        await self._publish_event(
            OrchestrationEventType.TASK_COMPLETED,
            {
                "task_id": task_id,
                "task_name": task_meta.task.name,
                "workflow_id": task_meta.task.workflow_id,
                "result": self._serialize_result(result),
                "duration_ms": duration_ms,
                "completed_at": task_meta.completed_at.isoformat()
                if task_meta.completed_at
                else None,
            },
        )

    async def publish_task_failed(
        self, task_id: str, task_meta: TaskMetadata, error: str, retry_count: int
    ) -> None:
        """Publish task.failed event"""
        await self._publish_event(
            OrchestrationEventType.TASK_FAILED,
            {
                "task_id": task_id,
                "task_name": task_meta.task.name,
                "workflow_id": task_meta.task.workflow_id,
                "error": error,
                "retry_count": retry_count,
                "failed_at": task_meta.failed_at.isoformat() if task_meta.failed_at else None,
            },
        )

    async def publish_metrics_snapshot(
        self, queue_stats: Dict[str, Any], pool_metrics: Dict[str, Any]
    ) -> None:
        """Publish periodic metrics snapshot"""
        await self._publish_event(
            OrchestrationEventType.METRICS_SNAPSHOT,
            {
                "timestamp": datetime.utcnow().isoformat(),
                "task_queue": queue_stats,
                "worker_pool": pool_metrics,
            },
        )

    async def _publish_event(self, event_type: OrchestrationEventType, payload: Dict[str, Any]) -> None:
        """Internal helper to publish events"""
        try:
            # EventBus expects Event objects with specific structure
            # We'll create a simple dict that mimics the Event structure
            event = {
                "event_type": event_type.value,
                "source_agent": self.source_agent,
                "payload": payload,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # If event_bus has a publish method that accepts dict or Event object
            await self.event_bus.publish(event)
            logger.debug(f"Published event: {event_type.value}")

        except Exception as e:
            logger.error(f"Failed to publish event {event_type.value}: {e}", exc_info=True)

    def _serialize_result(self, result: Any) -> Any:
        """Serialize task result for event payload"""
        if result is None:
            return None
        if isinstance(result, (str, int, float, bool)):
            return result
        if isinstance(result, dict):
            return result
        if isinstance(result, list):
            return result
        # For complex objects, convert to string
        return str(result)


class OrchestrationEventHandler:
    """
    Main handler that connects Event Bus and Orchestration Runtime.

    Responsibilities:
    - Subscribe to orchestration trigger events
    - Convert events to tasks via EventToTaskMapper
    - Enqueue tasks to TaskQueue
    - Publish task lifecycle events via TaskEventPublisher
    - Track event-task correlation
    """

    def __init__(
        self,
        event_bus,
        task_queue: TaskQueue,
        worker_pool: Optional[WorkerPool] = None,
        source_agent: str = "orchestration-runtime",
    ):
        """
        Initialize handler.

        Args:
            event_bus: EventBus instance
            task_queue: TaskQueue for enqueueing tasks
            worker_pool: Optional WorkerPool for execution
            source_agent: Agent ID for published events
        """
        self.event_bus = event_bus
        self.task_queue = task_queue
        self.worker_pool = worker_pool
        self.source_agent = source_agent

        self.mapper = EventToTaskMapper()
        self.publisher = TaskEventPublisher(event_bus, source_agent)

        # Track event → task correlation
        self.event_task_map: Dict[str, str] = {}  # event_id → task_id
        self.task_event_map: Dict[str, str] = {}  # task_id → event_id

        # Subscription tracking
        self.subscriptions: Set[str] = set()
        self._running = False

    def register_task_function(self, name: str, func: Callable) -> None:
        """Register a task function that can be triggered by events"""
        self.mapper.register_task_function(name, func)

    def add_event_mapping(self, mapping: EventToTaskMapping) -> None:
        """Add event-to-task mapping configuration"""
        self.mapper.add_mapping(mapping)

    async def start(self) -> None:
        """Start the handler and subscribe to trigger events"""
        if self._running:
            logger.warning("OrchestrationEventHandler already running")
            return

        self._running = True

        # Subscribe to trigger events
        await self.event_bus.subscribe(
            OrchestrationEventType.TASK_TRIGGER.value,
            self._handle_task_trigger,
            subscriber_agent=self.source_agent,
        )
        self.subscriptions.add(OrchestrationEventType.TASK_TRIGGER.value)

        # Subscribe to workflow start events
        await self.event_bus.subscribe(
            OrchestrationEventType.WORKFLOW_START.value,
            self._handle_workflow_start,
            subscriber_agent=self.source_agent,
        )
        self.subscriptions.add(OrchestrationEventType.WORKFLOW_START.value)

        logger.info(f"OrchestrationEventHandler started (agent={self.source_agent})")

        # Start metrics publishing loop
        asyncio.create_task(self._metrics_publishing_loop())

    async def stop(self) -> None:
        """Stop the handler and unsubscribe"""
        if not self._running:
            return

        self._running = False

        # Unsubscribe from all patterns
        for pattern in self.subscriptions:
            try:
                await self.event_bus.unsubscribe(pattern, self.source_agent)
            except Exception as e:
                logger.error(f"Error unsubscribing from {pattern}: {e}")

        self.subscriptions.clear()
        logger.info("OrchestrationEventHandler stopped")

    async def _handle_task_trigger(self, event: Dict[str, Any]) -> None:
        """
        Handle orchestration.task.trigger events.

        Event payload example:
        {
            "task_name": "process_data",
            "args": ["data-123"],
            "kwargs": {"mode": "fast"},
            "priority": "HIGH",
            "workflow_id": "workflow-456"
        }
        """
        try:
            event_id = event.get("event_id", "unknown")
            event_type = event.get("event_type", OrchestrationEventType.TASK_TRIGGER.value)
            payload = event.get("payload", {})

            logger.info(f"Received task trigger event: {event_id}")

            # Map event to task
            task = self.mapper.map_event_to_task(event_type, payload, event_id)
            if not task:
                logger.error(f"Failed to map event {event_id} to task")
                return

            # Enqueue task
            task_id = await self.task_queue.enqueue(task)

            # Track correlation
            self.event_task_map[event_id] = task_id
            self.task_event_map[task_id] = event_id

            # Publish task created event
            await self.publisher.publish_task_created(
                task_id, task, trigger_event_id=event_id
            )

            logger.info(
                f"Task created from event: {event_id} → {task_id} "
                f"(name={task.name}, priority={task.priority.name})"
            )

            # If worker pool available, execute immediately
            if self.worker_pool:
                asyncio.create_task(self._execute_task(task_id))

        except Exception as e:
            logger.error(f"Error handling task trigger event: {e}", exc_info=True)

    async def _handle_workflow_start(self, event: Dict[str, Any]) -> None:
        """Handle orchestration.workflow.start events"""
        # Placeholder for workflow orchestration
        workflow_id = event.get("payload", {}).get("workflow_id")
        logger.info(f"Workflow start event received: {workflow_id}")

    async def _execute_task(self, task_id: str) -> None:
        """Execute a task and publish lifecycle events"""
        try:
            # Get task metadata
            task_meta = self.task_queue.get_task(task_id)
            if not task_meta:
                logger.error(f"Task not found: {task_id}")
                return

            # Dequeue task
            task = await self.task_queue.dequeue()
            if not task or task_meta.task_id != task_id:
                logger.warning(f"Task {task_id} not dequeued as expected")
                return

            # Publish started event
            await self.publisher.publish_task_started(task_id, task_meta, worker_id="worker-auto")

            # Execute task
            start_time = datetime.utcnow()
            try:
                result = await task.func(*task.args, **task.kwargs)
                duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

                # Mark complete
                await self.task_queue.complete_task(task_id, result)

                # Publish completed event
                task_meta = self.task_queue.get_task(task_id)
                await self.publisher.publish_task_completed(
                    task_id, task_meta, result, duration_ms
                )

                logger.info(f"Task completed: {task_id} ({duration_ms:.2f}ms)")

            except Exception as e:
                # Mark failed
                await self.task_queue.fail_task(task_id, str(e))

                # Publish failed event
                task_meta = self.task_queue.get_task(task_id)
                await self.publisher.publish_task_failed(
                    task_id, task_meta, str(e), retry_count=0
                )

                logger.error(f"Task failed: {task_id} - {e}")

        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}", exc_info=True)

    async def _metrics_publishing_loop(self) -> None:
        """Periodically publish metrics snapshots"""
        while self._running:
            try:
                await asyncio.sleep(10)  # Publish every 10 seconds

                if not self._running:
                    break

                # Get queue statistics
                stats = self.task_queue.get_statistics()
                queue_stats = {
                    "pending": stats.pending_count,
                    "running": stats.running_count,
                    "completed": stats.completed_count,
                    "failed": stats.failed_count,
                    "cancelled": stats.cancelled_count,
                    "avg_duration_seconds": stats.average_duration_seconds,
                }

                # Get worker pool metrics (if available)
                pool_metrics = {}
                if self.worker_pool:
                    metrics = self.worker_pool.get_metrics()
                    pool_metrics = {
                        "active_workers": metrics.active_workers,
                        "idle_workers": metrics.idle_workers,
                        "tasks_completed": metrics.tasks_completed,
                        "tasks_failed": metrics.tasks_failed,
                        "throughput_per_minute": metrics.throughput_per_minute,
                        "utilization_percentage": metrics.utilization_percentage,
                    }

                # Publish metrics
                await self.publisher.publish_metrics_snapshot(queue_stats, pool_metrics)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics publishing loop: {e}", exc_info=True)
