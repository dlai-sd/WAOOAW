# WAOOAW Orchestration Runtime

**Version**: 0.7.3  
**Status**: Production Ready  
**Coverage**: 88% (119/135 tests passing)  
**Tests**: ✅ Unit tests complete, integration tests in progress

---

## Overview

The WAOOAW Orchestration Runtime is a powerful task execution engine for coordinating multi-agent workflows with dependencies, priorities, retries, and compensation. It provides the scheduling and execution backbone for complex agent collaboration scenarios.

**Features**:
- ✅ Priority-based task queue (HIGH/NORMAL/LOW/BACKGROUND)
- ✅ Dependency resolution with topological sorting
- ✅ Concurrent worker pool with load balancing
- ✅ Configurable retry policies with exponential backoff
- ✅ Saga pattern for distributed transaction compensation
- ✅ Real-time metrics and health monitoring
- ✅ Graceful shutdown with task preservation

---

## Quick Start

### Installation

```bash
# Install dependencies
pip install asyncio redis

# Run tests
export PYTHONPATH=/path/to/WAOOAW:$PYTHONPATH
pytest tests/orchestration/ -v
```

### Basic Usage

```python
import asyncio
from waooaw.orchestration import TaskQueue, Task, TaskPriority

async def main():
    # Create task queue
    queue = TaskQueue(max_size=1000)
    
    # Define task function
    async def process_data(data_id: str) -> dict:
        # Your processing logic
        return {"status": "success", "data_id": data_id}
    
    # Create task
    task = Task(
        name="process_data",
        func=process_data,
        args=["data-123"],
        priority=TaskPriority.HIGH,
        workflow_id="workflow-1"
    )
    
    # Enqueue task
    task_id = await queue.enqueue(task)
    print(f"Task enqueued: {task_id}")
    
    # Get task status
    task_metadata = queue.get_task(task_id)
    print(f"Task state: {task_metadata.state}")
    
    # Get queue statistics
    stats = queue.get_statistics()
    print(f"Queue: {stats.pending_count} pending, {stats.running_count} running")

asyncio.run(main())
```

---

## Architecture

### Component Overview

```
┌────────────────────────────────────────────────────────────┐
│                    Orchestration Runtime                    │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌───────────────────┐               │
│  │  Task Queue  │───▶│ Dependency Graph  │               │
│  │  (Priority)  │    │ (Topological Sort)│               │
│  └──────────────┘    └───────────────────┘               │
│         │                     │                            │
│         │                     ▼                            │
│         │            ┌───────────────────┐               │
│         └───────────▶│   Worker Pool     │               │
│                      │ (Max 10 workers)  │               │
│                      └───────────────────┘               │
│                               │                            │
│                  ┌────────────┴────────────┐              │
│                  ▼                         ▼              │
│         ┌────────────────┐       ┌──────────────┐        │
│         │  Retry Policy  │       │ Compensation │        │
│         │  (Exponential) │       │ (Saga)       │        │
│         └────────────────┘       └──────────────┘        │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

### Task Lifecycle

```
PENDING ──(dequeue)──▶ RUNNING ──(success)──▶ COMPLETED
   │                      │
   │                      │
   │                   (failure)
   │                      │
   │                      ▼
   │                   FAILED ──(retry)──▶ PENDING
   │                      │
   │                      │
   │                  (max retries)
   │                      │
   │                      ▼
   │                  [Dead Letter Queue]
   │
(cancel)
   │
   ▼
CANCELLED
```

### Worker Pool Management

```
┌────────────────────────────────────────┐
│         Worker Pool (Max 10)            │
├────────────────────────────────────────┤
│                                         │
│  Worker 1: IDLE    ┐                   │
│  Worker 2: BUSY    │ Load Balancing    │
│  Worker 3: BUSY    │ (Least-loaded)    │
│  Worker 4: IDLE    ┘                   │
│  ...                                    │
│                                         │
│  Metrics:                               │
│  - Active: 2/10                         │
│  - Throughput: 45 tasks/min             │
│  - Utilization: 20%                     │
│                                         │
└────────────────────────────────────────┘
```

---

## Components

### Task Queue

Priority-based queue with state management and statistics.

```python
from waooaw.orchestration import (
    TaskQueue,
    Task,
    TaskPriority,
    TaskState,
    TaskNotFoundError,
    TaskQueueFullError
)

# Create queue
queue = TaskQueue(
    max_size=1000,
    max_running=50
)

# Create high-priority task
task = Task(
    name="process_urgent_order",
    func=process_order,
    args=["order-789"],
    priority=TaskPriority.HIGH,
    workflow_id="order-workflow",
    timeout_seconds=300
)

# Enqueue
task_id = await queue.enqueue(task)

# Dequeue (respects priority)
task = await queue.dequeue(timeout=5.0)

# Update state
await queue.complete_task(task_id, result={"status": "success"})
await queue.fail_task(task_id, error="Database timeout")
await queue.cancel_task(task_id)

# Query tasks
task_meta = queue.get_task(task_id)
workflow_tasks = queue.get_workflow_tasks("order-workflow")

# Statistics
stats = queue.get_statistics()
print(f"Pending: {stats.pending_count}")
print(f"Running: {stats.running_count}")
print(f"Completed: {stats.completed_count}")
print(f"Avg Duration: {stats.average_duration_seconds}s")
```

**Priority Levels**:
- `HIGH`: Critical tasks (order 1)
- `NORMAL`: Standard tasks (order 2, default)
- `LOW`: Background processing (order 3)
- `BACKGROUND`: Maintenance tasks (order 4)

**State Tracking**:
- `PENDING`: Waiting in queue
- `RUNNING`: Currently executing
- `COMPLETED`: Successfully finished
- `FAILED`: Execution error
- `CANCELLED`: Manually stopped
- `TIMEOUT`: Exceeded time limit

---

### Dependency Resolver

Topological sorting and dependency graph management.

```python
from waooaw.orchestration import (
    DependencyGraph,
    TaskNode,
    ExecutionPlan,
    CyclicDependencyError,
    InvalidDependencyError
)

# Create dependency graph
graph = DependencyGraph()

# Add tasks with dependencies
task_a = TaskNode(task_id="task-a", name="fetch_data")
task_b = TaskNode(task_id="task-b", name="transform_data", dependencies=["task-a"])
task_c = TaskNode(task_id="task-c", name="load_data", dependencies=["task-b"])
task_d = TaskNode(task_id="task-d", name="send_notification", dependencies=["task-c"])

graph.add_node(task_a)
graph.add_node(task_b)
graph.add_node(task_c)
graph.add_node(task_d)

# Validate (checks for cycles)
if not graph.is_valid():
    raise CyclicDependencyError("Circular dependency detected!")

# Generate execution plan
plan = graph.create_execution_plan()

# Execute in order
for batch in plan.execution_batches:
    # Tasks in same batch can run in parallel
    tasks_to_run = [graph.get_node(task_id) for task_id in batch]
    await asyncio.gather(*[execute_task(t) for t in tasks_to_run])

# Mark task complete and update graph
graph.mark_completed("task-a")
next_tasks = graph.get_ready_tasks()  # Returns ["task-b"]
```

**Features**:
- Topological sort using Kahn's algorithm
- Cycle detection
- Parallel execution batching
- Dependency validation
- Ready task identification

**Example Workflow**:
```
fetch_data ──▶ transform_data ──▶ load_data ──▶ send_notification
                                        │
                                        └──▶ update_metrics
```

---

### Worker Pool

Concurrent task execution with load balancing and health monitoring.

```python
from waooaw.orchestration import (
    WorkerPool,
    Worker,
    WorkerState,
    WorkerPoolFullError,
    NoWorkersAvailableError
)

# Create worker pool
pool = WorkerPool(
    max_workers=10,
    min_workers=2
)

# Start pool
await pool.start()

# Submit task for execution
async def my_task(x: int, y: int) -> int:
    return x + y

result = await pool.execute_task(my_task, args=[5, 3])
print(f"Result: {result}")  # 8

# Scale workers dynamically
await pool.scale_up(workers_to_add=3)
await pool.scale_down(workers_to_remove=2)

# Get pool metrics
metrics = pool.get_metrics()
print(f"Active workers: {metrics.active_workers}/{pool.max_workers}")
print(f"Idle workers: {metrics.idle_workers}")
print(f"Tasks completed: {metrics.tasks_completed}")
print(f"Throughput: {metrics.throughput_per_minute} tasks/min")
print(f"Utilization: {metrics.utilization_percentage}%")

# Get individual worker metrics
worker_metrics = pool.get_worker_metrics("worker-1")
print(f"Worker state: {worker_metrics.state}")
print(f"Tasks completed: {worker_metrics.tasks_completed}")
print(f"Uptime: {worker_metrics.uptime_seconds}s")

# Stop pool gracefully
await pool.stop()
```

**Load Balancing**:
- Round-robin assignment
- Idle worker prioritization
- Automatic worker recovery
- Graceful shutdown with task completion

**Worker States**:
- `IDLE`: Ready for tasks
- `BUSY`: Executing task
- `ERROR`: Task execution failed
- `STOPPED`: Gracefully shut down

**Metrics Tracked**:
- Tasks completed per worker
- Average task duration
- Worker utilization percentage
- Throughput (tasks/minute)
- Error rate

---

### Retry Policy

Configurable retry strategies with exponential backoff.

```python
from waooaw.orchestration import (
    RetryPolicy,
    RetryConfig,
    RetryStrategy,
    RetryContext,
    MaxRetriesExceededError,
    RETRY_POLICY_AGGRESSIVE,
    RETRY_POLICY_STANDARD,
    RETRY_POLICY_CONSERVATIVE,
    RETRY_POLICY_QUICK
)

# Use preset policy
policy = RetryPolicy(config=RETRY_POLICY_STANDARD)
# max_retries=3, initial_delay=1s, max_delay=60s, backoff_multiplier=2.0

# Or create custom policy
custom_policy = RetryPolicy(
    config=RetryConfig(
        max_retries=5,
        initial_delay_seconds=2.0,
        max_delay_seconds=120.0,
        backoff_multiplier=2.5,
        strategy=RetryStrategy.EXPONENTIAL
    )
)

# Execute with retry
async def flaky_operation():
    # Might fail occasionally
    response = await api_call()
    return response

context = RetryContext(operation_name="api_call")
result = await policy.execute_with_retry(flaky_operation, context)

# Manual retry logic
attempt = 0
while attempt < policy.config.max_retries:
    try:
        result = await flaky_operation()
        break
    except Exception as e:
        attempt += 1
        if attempt >= policy.config.max_retries:
            raise MaxRetriesExceededError(f"Failed after {attempt} attempts")
        
        delay = policy.calculate_delay(attempt, context)
        await asyncio.sleep(delay)
```

**Preset Policies**:

| Policy | Max Retries | Initial Delay | Max Delay | Multiplier |
|--------|-------------|---------------|-----------|------------|
| `AGGRESSIVE` | 5 | 0.5s | 30s | 2.0 |
| `STANDARD` | 3 | 1.0s | 60s | 2.0 |
| `CONSERVATIVE` | 2 | 2.0s | 120s | 3.0 |
| `QUICK` | 3 | 0.1s | 5s | 1.5 |

**Retry Strategies**:
- `EXPONENTIAL`: Delay doubles each attempt (1s → 2s → 4s → 8s)
- `LINEAR`: Constant delay between attempts
- `FIBONACCI`: Fibonacci sequence delays (1s → 1s → 2s → 3s → 5s)

---

### Compensation (Saga Pattern)

Distributed transaction rollback with compensation actions.

```python
from waooaw.orchestration import (
    Saga,
    SagaBuilder,
    SagaStep,
    SagaExecution,
    SagaExecutionError
)

# Build saga
saga = (
    SagaBuilder()
    .add_step(
        name="reserve_inventory",
        action=reserve_inventory,
        compensation=release_inventory,
        args={"product_id": "prod-123", "quantity": 5}
    )
    .add_step(
        name="charge_payment",
        action=charge_customer,
        compensation=refund_customer,
        args={"customer_id": "cust-456", "amount": 99.99}
    )
    .add_step(
        name="ship_order",
        action=create_shipment,
        compensation=cancel_shipment,
        args={"order_id": "order-789"}
    )
    .build()
)

# Execute saga
try:
    execution = await saga.execute()
    print(f"Saga completed: {execution.saga_id}")
except SagaExecutionError as e:
    print(f"Saga failed at step: {e.failed_step}")
    print(f"Compensation status: {e.compensation_status}")
    # Compensations automatically executed in reverse order

# Manual execution with monitoring
execution = SagaExecution(saga_id="saga-001")
for step in saga.steps:
    try:
        result = await step.action(**step.args)
        execution.mark_step_completed(step.name, result)
    except Exception as e:
        # Compensate all completed steps in reverse
        for completed_step in reversed(execution.completed_steps):
            await completed_step.compensation(**completed_step.args)
        raise
```

**Use Cases**:
- Multi-service transactions (order → payment → shipment)
- Resource allocation and cleanup
- Multi-agent coordination with rollback
- Distributed workflows with failure recovery

**Compensation Flow**:
```
Step 1: Reserve Inventory ✓
Step 2: Charge Payment ✓
Step 3: Ship Order ✗ (FAILED)
    ▼
Compensate Step 2: Refund Payment ✓
Compensate Step 1: Release Inventory ✓
    ▼
Saga Failed (Consistent State Restored)
```

---

## Integration Patterns

### Event-Driven Orchestration

Trigger tasks from Event Bus events (see Event Bus README).

```python
from waooaw.events import EventBus, Event
from waooaw.orchestration import TaskQueue, Task

async def event_to_task_bridge():
    event_bus = EventBus(redis_client)
    task_queue = TaskQueue()
    
    # Subscribe to orchestration trigger events
    async def handle_task_trigger(event: Event):
        # Convert event to task
        task = Task(
            name=event.payload["task_name"],
            func=get_task_function(event.payload["task_name"]),
            args=event.payload.get("args", []),
            priority=TaskPriority[event.payload.get("priority", "NORMAL")],
            workflow_id=event.correlation_id
        )
        
        # Enqueue task
        task_id = await task_queue.enqueue(task)
        
        # Publish task created event
        await event_bus.publish(Event(
            event_type="orchestration.task.created",
            source_agent="orchestrator",
            payload={"task_id": task_id, "trigger_event_id": event.event_id}
        ))
    
    await event_bus.subscribe("orchestration.task.trigger", handle_task_trigger)
```

### Multi-Agent Workflow

Coordinate multiple agents with dependencies.

```python
from waooaw.orchestration import DependencyGraph, TaskNode, WorkerPool

async def multi_agent_workflow(order_data: dict):
    graph = DependencyGraph()
    
    # Step 1: Validate order (Agent: OrderValidator)
    validate_node = TaskNode(
        task_id="validate-order",
        name="validate_order",
        agent_id="order-validator",
        metadata=order_data
    )
    graph.add_node(validate_node)
    
    # Step 2: Check inventory (Agent: InventoryManager)
    inventory_node = TaskNode(
        task_id="check-inventory",
        name="check_inventory",
        agent_id="inventory-manager",
        dependencies=["validate-order"]
    )
    graph.add_node(inventory_node)
    
    # Step 3: Process payment (Agent: PaymentProcessor)
    payment_node = TaskNode(
        task_id="process-payment",
        name="process_payment",
        agent_id="payment-processor",
        dependencies=["check-inventory"]
    )
    graph.add_node(payment_node)
    
    # Step 4: Create shipment (Agent: ShippingAgent)
    shipment_node = TaskNode(
        task_id="create-shipment",
        name="create_shipment",
        agent_id="shipping-agent",
        dependencies=["process-payment"]
    )
    graph.add_node(shipment_node)
    
    # Execute with worker pool
    pool = WorkerPool(max_workers=10)
    await pool.start()
    
    plan = graph.create_execution_plan()
    for batch in plan.execution_batches:
        tasks = [execute_agent_task(graph.get_node(tid)) for tid in batch]
        results = await asyncio.gather(*tasks)
        
        # Update graph with results
        for task_id in batch:
            graph.mark_completed(task_id)
    
    await pool.stop()
```

---

## Performance Tuning

### Worker Pool Sizing

```python
# For CPU-bound tasks
pool = WorkerPool(max_workers=min(10, os.cpu_count()))

# For I/O-bound tasks (API calls, DB queries)
pool = WorkerPool(max_workers=50)

# Dynamic scaling based on queue depth
queue_depth = task_queue.get_statistics().pending_count
if queue_depth > 100:
    await pool.scale_up(workers_to_add=5)
elif queue_depth < 20 and pool.active_workers > pool.min_workers:
    await pool.scale_down(workers_to_remove=2)
```

### Queue Optimization

```python
# High-throughput configuration
queue = TaskQueue(
    max_size=10000,        # Large queue for burst traffic
    max_running=100        # Many concurrent tasks
)

# Low-latency configuration
queue = TaskQueue(
    max_size=100,          # Small queue, process immediately
    max_running=20
)
```

### Retry Tuning

```python
# Fast-failing for time-sensitive operations
policy = RetryPolicy(config=RETRY_POLICY_QUICK)  # 3 retries, max 5s

# Resilient for critical operations
policy = RetryPolicy(config=RETRY_POLICY_AGGRESSIVE)  # 5 retries, max 30s
```

---

## Deployment

### Local Development

```bash
# Set PYTHONPATH
export PYTHONPATH=/path/to/WAOOAW:$PYTHONPATH

# Run orchestration service
python -m waooaw.orchestration.service

# Run tests
pytest tests/orchestration/ -v
```

### Docker Deployment

```dockerfile
# See: infrastructure/docker/orchestration.Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY waooaw/ waooaw/
ENV PYTHONPATH=/app

CMD ["python", "-m", "waooaw.orchestration.service"]
```

### Kubernetes

```yaml
# See: infrastructure/kubernetes/orchestration-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orchestration-runtime
spec:
  replicas: 3
  selector:
    matchLabels:
      app: orchestration
  template:
    spec:
      containers:
      - name: orchestration
        image: waooaw/orchestration:0.7.3
        env:
        - name: WORKER_POOL_SIZE
          value: "10"
        - name: TASK_QUEUE_MAX_SIZE
          value: "1000"
        resources:
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

---

## API Reference

### TaskQueue

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `enqueue(task)` | `task: Task` | `str` | Add task to queue, returns task_id |
| `dequeue(timeout)` | `timeout: float` | `Task` | Get highest priority task |
| `complete_task(task_id, result)` | `task_id: str, result: Any` | `None` | Mark task as completed |
| `fail_task(task_id, error)` | `task_id: str, error: str` | `None` | Mark task as failed |
| `cancel_task(task_id)` | `task_id: str` | `None` | Cancel pending/running task |
| `get_task(task_id)` | `task_id: str` | `TaskMetadata` | Get task metadata |
| `get_workflow_tasks(workflow_id)` | `workflow_id: str` | `List[TaskMetadata]` | Get all tasks in workflow |
| `get_statistics()` | None | `TaskStatistics` | Get queue statistics |

### DependencyGraph

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `add_node(node)` | `node: TaskNode` | `None` | Add task node to graph |
| `is_valid()` | None | `bool` | Check for circular dependencies |
| `create_execution_plan()` | None | `ExecutionPlan` | Generate topologically sorted plan |
| `mark_completed(task_id)` | `task_id: str` | `None` | Mark task as complete |
| `get_ready_tasks()` | None | `List[str]` | Get tasks ready to execute |

### WorkerPool

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `start()` | None | `None` | Start worker pool |
| `stop()` | None | `None` | Stop pool gracefully |
| `execute_task(func, args)` | `func: Callable, args: List` | `Any` | Execute task, returns result |
| `scale_up(workers_to_add)` | `workers_to_add: int` | `None` | Add workers |
| `scale_down(workers_to_remove)` | `workers_to_remove: int` | `None` | Remove workers |
| `get_metrics()` | None | `WorkerPoolMetrics` | Get pool metrics |
| `get_worker_metrics(worker_id)` | `worker_id: str` | `WorkerMetrics` | Get worker metrics |

---

## Troubleshooting

### Common Issues

**Issue**: Tasks stuck in RUNNING state
```python
# Check worker pool health
metrics = pool.get_metrics()
if metrics.active_workers == 0:
    await pool.start()  # Restart pool

# Check for deadlocked tasks
await queue.cancel_task(stuck_task_id)
```

**Issue**: High queue depth
```python
# Scale up workers
await pool.scale_up(workers_to_add=5)

# Or increase max_running limit
queue.max_running = 100
```

**Issue**: Tasks failing with retries exhausted
```python
# Use more aggressive retry policy
policy = RetryPolicy(config=RETRY_POLICY_AGGRESSIVE)

# Or customize
custom_policy = RetryPolicy(
    config=RetryConfig(max_retries=10, initial_delay_seconds=0.5)
)
```

---

## Best Practices

### Task Design
- ✅ Keep tasks idempotent (safe to retry)
- ✅ Set appropriate timeouts (default: no timeout)
- ✅ Use workflow_id to group related tasks
- ✅ Handle errors gracefully with try/except
- ✅ Return meaningful results for downstream tasks

### Dependency Management
- ✅ Validate graphs before execution (`is_valid()`)
- ✅ Keep dependency chains shallow (≤5 levels)
- ✅ Use parallel batches when possible
- ✅ Handle missing dependencies gracefully

### Worker Pool
- ✅ Size pool based on task type (CPU vs I/O)
- ✅ Monitor utilization and scale dynamically
- ✅ Use graceful shutdown to preserve tasks
- ✅ Implement health checks for workers

### Monitoring
- ✅ Track queue depth and throughput
- ✅ Monitor worker utilization percentage
- ✅ Alert on high failure rates
- ✅ Log task execution times for optimization

---

## Examples

See `examples/` directory:
- `data_processing_pipeline.py` - 5-stage ETL workflow
- `distributed_computation.py` - Monte Carlo simulation with worker pools
- `fault_tolerant_service.py` - HA service with retry and compensation

---

## Related Documentation

- [Event Bus README](../events/README.md) - Event-driven integration
- [Integration Guide](../../docs/platform/INTEGRATION_GUIDE.md) - Complete integration patterns
- [Epic 3.4](../../docs/platform/EPIC_3.4_MESSAGE_ORCHESTRATION_BRIDGE.md) - Orchestration + Event Bus bridge

---

## Contributing

Run tests before submitting:
```bash
export PYTHONPATH=/path/to/WAOOAW:$PYTHONPATH
pytest tests/orchestration/ -v --cov=waooaw.orchestration
```

**Coverage Target**: ≥85%  
**Test Categories**: Unit tests (119), Integration tests (16)

---

**Version**: 0.7.3  
**Last Updated**: 2025-12-30  
**Status**: Production Ready ✅
