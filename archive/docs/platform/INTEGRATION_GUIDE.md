# WAOOAW Integration Guide

**Version:** 1.0  
**Last Updated:** December 29, 2025  
**Audience:** Platform developers, integration engineers, DevOps teams

> **Quick Links:** [Architecture](#architecture) | [API Reference](#api-reference) | [Deployment](#deployment) | [Troubleshooting](#troubleshooting) | [Examples](../../examples/)

---

## Overview

This guide covers the integration of WAOOAW's orchestration and discovery layers to build distributed multi-agent systems. The platform provides composable APIs for task management, agent coordination, health monitoring, and fault tolerance.

**Key Capabilities:**
- **Orchestration Runtime**: Task queuing, worker pools, dependency management, retry logic, saga patterns
- **Agent Discovery**: Service registry, health monitoring, load balancing, circuit breakers
- **Integration**: Seamless coordination between orchestration and discovery layers
- **Fault Tolerance**: Circuit breakers, retry policies, health-based routing, degraded state handling

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Application Layer                         │
│  (Data Pipelines, Distributed Compute, HA Services, etc.)       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
┌───────▼────────┐                  ┌─────────▼──────────┐
│  Orchestration │                  │     Discovery      │
│     Layer      │                  │      Layer         │
├────────────────┤                  ├────────────────────┤
│ • TaskQueue    │◄────────────────►│ • ServiceRegistry │
│ • WorkerPool   │  Agent Selection │ • HealthMonitor   │
│ • DepGraph     │                  │ • LoadBalancer    │
│ • RetryPolicy  │                  │ • CircuitBreaker  │
│ • Saga         │                  │                   │
└────────────────┘                  └───────────────────┘
        │                                     │
        └──────────────────┬──────────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │          Common Services            │
        ├─────────────────────────────────────┤
        │ • Logging Framework                 │
        │ • Metrics & Observability           │
        │ • Configuration Management          │
        │ • Error Handling                    │
        │ • State Management                  │
        └─────────────────────────────────────┘
```

### Component Interaction Flow

```
1. Application registers agents
   └─► ServiceRegistry.register(agent_id, capabilities, tags, metadata)

2. Health monitoring starts
   └─► HealthMonitor.start() → Background health checks every N seconds
       └─► Custom health_checker() returns True/False
           └─► Update HealthStatus: HEALTHY/DEGRADED/UNHEALTHY/UNKNOWN

3. Load balancer selects agents
   └─► LoadBalancer.select_agent(capability, require_healthy)
       └─► Get healthy agents from ServiceRegistry
       └─► Apply strategy: ROUND_ROBIN/LEAST_CONNECTIONS/WEIGHTED/RANDOM
       └─► Return selected agent

4. Circuit breaker protects calls
   └─► CircuitBreaker.check_state(agent_id)
       └─► State: CLOSED (allow), OPEN (reject), HALF_OPEN (test)
       └─► Record success/failure
       └─► Trip on failure threshold

5. Task execution with retry
   └─► TaskQueue.submit(task, priority)
       └─► WorkerPool processes task
           └─► LoadBalancer selects agent
           └─► CircuitBreaker checks state
           └─► Execute with retry on failure
           └─► RetryPolicy calculates backoff
```

### Data Flow

```
Task Submission → Task Queue → Worker Pool → Agent Selection → Execution
                     │             │              │                │
                     │             │              ▼                │
                     │             │      Load Balancer            │
                     │             │              │                │
                     │             │              ▼                │
                     │             │      Health Monitor           │
                     │             │              │                │
                     │             │              ▼                │
                     │             │      Service Registry         │
                     │             │                               │
                     │             ▼                               ▼
                     │      Circuit Breaker ─────────► Success/Failure
                     │                                       │
                     └───────────────────────────────────────┘
                                  Retry Loop
```

---

## API Reference

### Core Components

#### ServiceRegistry

**Purpose:** Central registry for agent registration, discovery, and lifecycle management.

```python
from waooaw.discovery.service_registry import (
    ServiceRegistry, 
    AgentCapability,
    AgentStatus
)

# Initialize
registry = ServiceRegistry()

# Register agent
await registry.register(
    agent_id="worker-1",
    name="Worker Agent 1",
    host="localhost",
    port=9000,
    capabilities={
        AgentCapability("compute", "1.0"),
        AgentCapability("process", "1.0")
    },
    status=AgentStatus.ONLINE,
    tags={"production", "gpu"},
    metadata={"tier": "premium", "cores": 16},
    ttl_seconds=60
)

# Discover agents
agents = await registry.discover(
    capability=AgentCapability("compute", "1.0"),
    tags={"production"}
)

# Deregister
await registry.deregister(agent_id="worker-1")
```

**Key Methods:**
- `register()`: Register agent with capabilities, tags, metadata
- `deregister()`: Remove agent from registry
- `discover()`: Find agents by capability and tags
- `get_registration()`: Get specific agent registration
- `list_all()`: List all registered agents
- `update_status()`: Update agent status
- `refresh_ttl()`: Extend agent TTL

---

#### HealthMonitor

**Purpose:** Monitor agent health status with periodic checks and custom health checkers.

```python
from waooaw.discovery.health_monitor import (
    HealthMonitor,
    HealthStatus
)

# Initialize
monitor = HealthMonitor(
    registry,
    check_interval=5.0,  # Check every 5 seconds
    degraded_threshold_ms=500.0,  # >500ms = DEGRADED
    unhealthy_threshold_failures=3  # 3 failures = UNHEALTHY
)

# Register custom health checker
async def my_health_checker():
    try:
        # Check agent connectivity, resources, etc.
        return True  # healthy
    except Exception:
        return False  # unhealthy

monitor.register_health_checker("worker-1", my_health_checker)

# Start monitoring
await monitor.start()

# Check health
health_status = await monitor.get_health_status("worker-1")
print(f"Status: {health_status.status}")
print(f"Response time: {health_status.response_time_ms}ms")

# Get metrics
metrics = await monitor.get_metrics("worker-1")
print(f"Success rate: {metrics.success_rate:.1%}")
print(f"Avg response: {metrics.average_response_time_ms:.1f}ms")

# Stop monitoring
await monitor.stop()
```

**Health States:**
- `HEALTHY`: Agent responding normally
- `DEGRADED`: Agent slow (>threshold response time)
- `UNHEALTHY`: Agent failing health checks
- `UNKNOWN`: No health data available

---

#### LoadBalancer

**Purpose:** Select agents for task execution using configurable strategies.

```python
from waooaw.discovery.load_balancer import (
    LoadBalancer,
    LoadBalancingStrategy
)

# Initialize
load_balancer = LoadBalancer(
    registry,
    monitor,
    strategy=LoadBalancingStrategy.LEAST_CONNECTIONS,
    default_weight=1
)

# Set agent weights (for WEIGHTED strategy)
load_balancer.set_weight("premium-agent", 10)  # 10x priority
load_balancer.set_weight("standard-agent", 1)   # 1x priority

# Select agent
selected = await load_balancer.select_agent(
    capability="compute",
    tags={"production"},
    require_healthy=True
)

if selected:
    agent_id = selected.agent.agent_id
    
    # Acquire connection (tracks active connections)
    await load_balancer.acquire_connection(agent_id)
    
    try:
        # Execute task on agent
        result = await execute_task(agent_id)
    finally:
        # Release connection
        await load_balancer.release_connection(agent_id)
```

**Strategies:**
- `ROUND_ROBIN`: Rotate through agents sequentially
- `LEAST_CONNECTIONS`: Select agent with fewest active connections
- `WEIGHTED`: Priority-based selection (use with `set_weight()`)
- `RANDOM`: Random agent selection

---

#### CircuitBreaker

**Purpose:** Protect system from cascading failures by isolating failing agents.

```python
from waooaw.discovery.circuit_breaker import CircuitBreaker

# Initialize
circuit_breaker = CircuitBreaker(
    failure_threshold=0.5,  # 50% failure rate
    success_threshold=0.7,   # 70% success to close
    timeout_seconds=30.0,    # 30s before retry
    min_requests=5           # Min requests before trip
)

# Check circuit state
state = await circuit_breaker.get_state("worker-1")
# Returns: CircuitState.CLOSED, OPEN, or HALF_OPEN

# Execute with circuit breaker
agent_id = "worker-1"

if await circuit_breaker.check_state(agent_id):
    try:
        result = await execute_task(agent_id)
        await circuit_breaker.record_success(agent_id)
    except Exception as e:
        await circuit_breaker.record_failure(agent_id)
        raise
else:
    # Circuit is OPEN, use fallback
    raise CircuitOpenError(f"Circuit open for {agent_id}")

# Get metrics
metrics = await circuit_breaker.get_metrics(agent_id)
print(f"Failure rate: {metrics.failure_rate:.1%}")
print(f"State: {metrics.state}")
```

**States:**
- `CLOSED`: Normal operation, requests allowed
- `OPEN`: Too many failures, requests blocked
- `HALF_OPEN`: Testing if agent recovered

---

#### TaskQueue

**Purpose:** Priority-based task queuing with state tracking.

```python
from waooaw.orchestration.task_queue import (
    TaskQueue,
    Task,
    TaskPriority,
    TaskState
)

# Initialize
queue = TaskQueue(max_size=1000)

# Submit task
task = Task(
    task_id="task-001",
    name="Process Data",
    priority=TaskPriority.HIGH,
    metadata={"batch_id": "batch-001"}
)

await queue.submit(task)

# Get next task
next_task = await queue.get_next()

# Update task state
await queue.update_state(
    task_id="task-001",
    state=TaskState.RUNNING
)

# Complete task
await queue.complete_task(
    task_id="task-001",
    result={"processed": 1000}
)

# Fail task
await queue.fail_task(
    task_id="task-002",
    error="Processing failed"
)

# Get queue stats
stats = await queue.get_stats()
print(f"Pending: {stats['pending']}")
print(f"Running: {stats['running']}")
print(f"Completed: {stats['completed']}")
```

**Task States:**
- `PENDING`: Queued, waiting for worker
- `RUNNING`: Being processed
- `COMPLETED`: Successfully finished
- `FAILED`: Execution failed
- `CANCELLED`: Task cancelled

---

#### WorkerPool

**Purpose:** Concurrent task execution with configurable worker limits.

```python
from waooaw.orchestration.worker_pool import WorkerPool

# Initialize
worker_pool = WorkerPool(
    task_queue,
    max_workers=10
)

# Start workers
await worker_pool.start()

# Workers automatically process tasks from queue
# Each worker:
# 1. Gets task from queue
# 2. Executes task
# 3. Updates task state
# 4. Repeats

# Get pool stats
stats = await worker_pool.get_stats()
print(f"Active workers: {stats['active_workers']}")
print(f"Total processed: {stats['total_processed']}")

# Stop workers (graceful shutdown)
await worker_pool.stop()
```

---

#### RetryPolicy

**Purpose:** Configurable retry logic with exponential backoff and jitter.

```python
from waooaw.orchestration.retry_policy import (
    RetryPolicy,
    RetryStrategy
)

# Initialize
retry_policy = RetryPolicy(
    max_attempts=3,
    strategy=RetryStrategy.EXPONENTIAL,
    base_delay=0.1,        # 100ms
    max_delay=2.0,         # 2 seconds
    jitter_factor=0.2      # 20% jitter
)

# Execute with retry
for attempt in range(retry_policy.max_attempts):
    try:
        result = await execute_task()
        break  # Success
    except Exception as e:
        if attempt < retry_policy.max_attempts - 1:
            delay = retry_policy.calculate_delay(attempt)
            await asyncio.sleep(delay)
        else:
            raise  # Max attempts reached
```

**Strategies:**
- `EXPONENTIAL`: Delay = base_delay * (2 ^ attempt)
- `LINEAR`: Delay = base_delay * (attempt + 1)
- `CONSTANT`: Delay = base_delay

---

### Integration Patterns

#### Pattern 1: Basic Agent Registration & Discovery

```python
import asyncio
from waooaw.discovery.service_registry import ServiceRegistry, AgentCapability
from waooaw.discovery.health_monitor import HealthMonitor

async def basic_setup():
    # Initialize components
    registry = ServiceRegistry()
    monitor = HealthMonitor(registry)
    
    # Register agents
    await registry.register(
        agent_id="worker-1",
        name="Worker 1",
        host="localhost",
        port=9000,
        capabilities={AgentCapability("compute", "1.0")}
    )
    
    # Start health monitoring
    await monitor.start()
    
    # Discover agents
    agents = await registry.discover(
        capability=AgentCapability("compute", "1.0")
    )
    
    print(f"Found {len(agents)} compute agents")
    
    # Cleanup
    await monitor.stop()

asyncio.run(basic_setup())
```

---

#### Pattern 2: Load-Balanced Task Execution

```python
async def load_balanced_execution():
    registry = ServiceRegistry()
    monitor = HealthMonitor(registry)
    load_balancer = LoadBalancer(
        registry, 
        monitor,
        strategy=LoadBalancingStrategy.LEAST_CONNECTIONS
    )
    
    # Register multiple agents
    for i in range(5):
        await registry.register(
            agent_id=f"worker-{i}",
            name=f"Worker {i}",
            host="localhost",
            port=9000 + i,
            capabilities={AgentCapability("process", "1.0")}
        )
    
    await monitor.start()
    await asyncio.sleep(0.5)  # Wait for health checks
    
    # Execute tasks with load balancing
    for task_num in range(20):
        selected = await load_balancer.select_agent(
            capability="process",
            require_healthy=True
        )
        
        if selected:
            agent_id = selected.agent.agent_id
            await load_balancer.acquire_connection(agent_id)
            
            try:
                await process_task(task_num, agent_id)
            finally:
                await load_balancer.release_connection(agent_id)
    
    await monitor.stop()
```

---

#### Pattern 3: Fault-Tolerant Execution

```python
async def fault_tolerant_execution():
    registry = ServiceRegistry()
    monitor = HealthMonitor(registry)
    load_balancer = LoadBalancer(registry, monitor)
    circuit_breaker = CircuitBreaker()
    retry_policy = RetryPolicy(max_attempts=3)
    
    # Setup agents
    await setup_agents(registry)
    await monitor.start()
    await asyncio.sleep(0.5)
    
    # Execute with fault tolerance
    async def execute_with_protection(task_id):
        for attempt in range(retry_policy.max_attempts):
            # Select agent
            selected = await load_balancer.select_agent(
                capability="compute",
                require_healthy=True
            )
            
            if not selected:
                raise NoAvailableAgentsError()
            
            agent_id = selected.agent.agent_id
            
            # Check circuit breaker
            if not await circuit_breaker.check_state(agent_id):
                continue  # Circuit open, try another agent
            
            # Execute
            await load_balancer.acquire_connection(agent_id)
            try:
                result = await execute_task(task_id, agent_id)
                await circuit_breaker.record_success(agent_id)
                return result
            except Exception as e:
                await circuit_breaker.record_failure(agent_id)
                
                if attempt < retry_policy.max_attempts - 1:
                    delay = retry_policy.calculate_delay(attempt)
                    await asyncio.sleep(delay)
                else:
                    raise
            finally:
                await load_balancer.release_connection(agent_id)
    
    # Execute tasks
    results = []
    for i in range(100):
        result = await execute_with_protection(f"task-{i}")
        results.append(result)
    
    await monitor.stop()
    return results
```

---

#### Pattern 4: Priority Task Processing

```python
async def priority_task_processing():
    # Setup
    task_queue = TaskQueue()
    worker_pool = WorkerPool(task_queue, max_workers=5)
    
    await worker_pool.start()
    
    # Submit tasks with priorities
    await task_queue.submit(Task(
        task_id="critical-001",
        name="Critical Task",
        priority=TaskPriority.CRITICAL
    ))
    
    await task_queue.submit(Task(
        task_id="high-001",
        name="High Priority",
        priority=TaskPriority.HIGH
    ))
    
    await task_queue.submit(Task(
        task_id="normal-001",
        name="Normal Priority",
        priority=TaskPriority.NORMAL
    ))
    
    # Workers process in priority order: CRITICAL → HIGH → NORMAL → LOW
    
    # Wait for completion
    await asyncio.sleep(5)
    
    stats = await task_queue.get_stats()
    print(f"Completed: {stats['completed']}")
    
    await worker_pool.stop()
```

---

## Deployment

### Prerequisites

**System Requirements:**
- Python 3.11+
- Docker 20.10+ (for containerized deployment)
- Redis 6+ (for distributed state, optional)
- PostgreSQL 14+ (for persistence, optional)

**Python Dependencies:**
```bash
pip install -r requirements.txt
```

**Core dependencies:**
- `asyncio`: Async/await support
- `dataclasses`: Data structures
- `typing`: Type annotations
- `psutil`: Resource monitoring (for performance benchmarks)

---

### Local Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/WAOOAW.git
cd WAOOAW

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Run examples
python examples/data_processing_pipeline.py
python examples/distributed_computation.py
python examples/fault_tolerant_service.py
```

---

### Docker Deployment

**Build images:**
```bash
docker build -t waooaw-platform:latest .
```

**Run with Docker Compose:**
```yaml
# docker-compose.yml
version: '3.8'

services:
  waooaw-app:
    build: .
    environment:
      - WAOOAW_LOG_LEVEL=INFO
      - WAOOAW_CHECK_INTERVAL=5.0
      - WAOOAW_MAX_WORKERS=10
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config
    depends_on:
      - redis
      - postgres

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=waooaw
      - POSTGRES_USER=waooaw
      - POSTGRES_PASSWORD=secure_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

**Start services:**
```bash
docker-compose up -d
```

---

### Configuration

**Environment Variables:**
```bash
# Logging
WAOOAW_LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# Health Monitoring
WAOOAW_CHECK_INTERVAL=5.0  # Seconds between health checks
WAOOAW_DEGRADED_THRESHOLD_MS=500.0  # Response time threshold
WAOOAW_UNHEALTHY_THRESHOLD=3  # Consecutive failures

# Circuit Breaker
WAOOAW_CIRCUIT_FAILURE_THRESHOLD=0.5  # 50% failure rate
WAOOAW_CIRCUIT_TIMEOUT_SECONDS=30.0  # Time before retry

# Worker Pool
WAOOAW_MAX_WORKERS=10  # Maximum concurrent workers

# Task Queue
WAOOAW_QUEUE_MAX_SIZE=1000  # Maximum queue size
```

**Configuration File (`config/production.yaml`):**
```yaml
orchestration:
  max_workers: 20
  queue_max_size: 5000
  retry_max_attempts: 3
  retry_base_delay: 0.1
  retry_max_delay: 5.0

discovery:
  check_interval: 5.0
  degraded_threshold_ms: 500.0
  unhealthy_threshold: 3
  load_balancing_strategy: "least_connections"
  circuit_failure_threshold: 0.5
  circuit_timeout_seconds: 30.0

logging:
  level: "INFO"
  format: "json"
  output: "stdout"
```

---

### Monitoring

**Health Checks:**
```python
# Application health endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "components": {
            "registry": await registry.health_check(),
            "monitor": await monitor.health_check(),
            "worker_pool": await worker_pool.health_check()
        }
    }
```

**Metrics Endpoint:**
```python
@app.get("/metrics")
async def metrics():
    return {
        "agents": {
            "total": len(await registry.list_all()),
            "healthy": await monitor.get_healthy_count(),
            "unhealthy": await monitor.get_unhealthy_count()
        },
        "tasks": await task_queue.get_stats(),
        "workers": await worker_pool.get_stats(),
        "circuit_breakers": await circuit_breaker.get_all_metrics()
    }
```

**Prometheus Integration:**
```python
from prometheus_client import Counter, Histogram, Gauge

task_counter = Counter('waooaw_tasks_total', 'Total tasks processed')
task_duration = Histogram('waooaw_task_duration_seconds', 'Task duration')
active_agents = Gauge('waooaw_agents_active', 'Active agents')
```

---

## Troubleshooting

### Common Issues

#### Issue 1: NoAvailableAgentsError

**Symptom:**
```
NoAvailableAgentsError: No available agents for capability=compute
```

**Causes:**
1. No agents registered with required capability
2. All agents marked unhealthy
3. All circuits open for available agents

**Solutions:**
```python
# Check registered agents
agents = await registry.list_all()
print(f"Total agents: {len(agents)}")

# Check health status
for agent in agents:
    health = await monitor.get_health_status(agent.agent_id)
    print(f"{agent.agent_id}: {health.status}")

# Check circuit breaker states
for agent in agents:
    state = await circuit_breaker.get_state(agent.agent_id)
    print(f"{agent.agent_id}: {state}")

# Force health check
for agent in agents:
    await monitor.check_health(agent.agent_id)
```

---

#### Issue 2: Circuit Breaker Stuck Open

**Symptom:**
Circuit breaker remains in OPEN state, blocking all requests to agent.

**Causes:**
1. Agent genuinely failing
2. Timeout too long
3. Success threshold too high

**Solutions:**
```python
# Check circuit breaker metrics
metrics = await circuit_breaker.get_metrics(agent_id)
print(f"Failure rate: {metrics.failure_rate:.1%}")
print(f"State: {metrics.state}")
print(f"Last failure: {metrics.last_failure_time}")

# Manually reset circuit (use with caution)
await circuit_breaker.reset(agent_id)

# Adjust thresholds
circuit_breaker = CircuitBreaker(
    failure_threshold=0.7,  # More lenient
    timeout_seconds=15.0    # Shorter timeout
)
```

---

#### Issue 3: Poor Load Distribution

**Symptom:**
One agent receives all tasks while others idle.

**Causes:**
1. Wrong load balancing strategy
2. Incorrect weights
3. Connection not released

**Solutions:**
```python
# Check load distribution
stats = await load_balancer.get_stats()
for agent_id, connections in stats.items():
    print(f"{agent_id}: {connections} active connections")

# Verify connection release
async def execute_safely(agent_id):
    await load_balancer.acquire_connection(agent_id)
    try:
        result = await execute_task(agent_id)
    finally:
        # CRITICAL: Always release
        await load_balancer.release_connection(agent_id)

# Try different strategy
load_balancer.set_strategy(LoadBalancingStrategy.WEIGHTED)

# Adjust weights
for agent_id in ["premium-1", "premium-2"]:
    load_balancer.set_weight(agent_id, 10)
```

---

#### Issue 4: High Retry Rate

**Symptom:**
Many tasks retrying, increasing latency and resource usage.

**Causes:**
1. Agents genuinely unstable
2. Retry policy too aggressive
3. Health checks not detecting failures

**Solutions:**
```python
# Analyze retry metrics
retry_stats = await get_retry_stats()
print(f"Tasks retried: {retry_stats['retried']}")
print(f"Retry rate: {retry_stats['retry_rate']:.1%}")

# Adjust retry policy
retry_policy = RetryPolicy(
    max_attempts=2,  # Fewer retries
    base_delay=0.5,  # Longer initial delay
    strategy=RetryStrategy.EXPONENTIAL
)

# Improve health checking
monitor = HealthMonitor(
    registry,
    check_interval=2.0,  # More frequent checks
    unhealthy_threshold=2  # Faster detection
)
```

---

#### Issue 5: Memory Leak

**Symptom:**
Memory usage grows over time, not released.

**Causes:**
1. Task results not cleared
2. Metrics accumulating
3. Connections not closed

**Solutions:**
```python
# Clear completed tasks periodically
async def cleanup_tasks():
    while True:
        await task_queue.clear_completed(older_than_seconds=3600)
        await asyncio.sleep(600)  # Every 10 minutes

# Limit metrics retention
circuit_breaker = CircuitBreaker(
    max_history_size=100  # Keep only recent metrics
)

# Monitor memory
import psutil
process = psutil.Process()
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
```

---

### Debug Mode

**Enable verbose logging:**
```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Component-specific loggers
logging.getLogger('waooaw.discovery.load_balancer').setLevel(logging.DEBUG)
logging.getLogger('waooaw.discovery.circuit_breaker').setLevel(logging.DEBUG)
```

**Trace execution:**
```python
from waooaw.common.observability import trace_async

@trace_async
async def my_function():
    # Function execution traced
    pass
```

---

### Performance Tuning

**Optimize worker pool size:**
```python
# CPU-bound tasks: workers = CPU cores
import os
max_workers = os.cpu_count()

# I/O-bound tasks: workers = 2-4x CPU cores
max_workers = os.cpu_count() * 3

worker_pool = WorkerPool(task_queue, max_workers=max_workers)
```

**Tune health check interval:**
```python
# High-frequency (responsive, higher overhead)
monitor = HealthMonitor(registry, check_interval=2.0)

# Low-frequency (efficient, slower detection)
monitor = HealthMonitor(registry, check_interval=10.0)

# Adaptive (best of both)
monitor = HealthMonitor(
    registry,
    check_interval=5.0,
    adaptive=True  # Increase frequency on failures
)
```

**Circuit breaker tuning:**
```python
# Aggressive (fast failure detection)
circuit_breaker = CircuitBreaker(
    failure_threshold=0.3,  # 30%
    min_requests=3,
    timeout_seconds=10.0
)

# Conservative (tolerate transient failures)
circuit_breaker = CircuitBreaker(
    failure_threshold=0.7,  # 70%
    min_requests=10,
    timeout_seconds=60.0
)
```

---

## Best Practices

### 1. Agent Registration

✅ **DO:**
- Register agents with specific capabilities
- Use descriptive agent IDs and names
- Include metadata for filtering and debugging
- Set appropriate TTL values
- Refresh TTL periodically

❌ **DON'T:**
- Register agents without capabilities
- Use generic IDs like "agent-1"
- Skip metadata
- Set TTL too short (causes frequent re-registration)

```python
# GOOD
await registry.register(
    agent_id="data-processor-001",
    name="Data Processor (Batch ETL)",
    host="10.0.1.5",
    port=9000,
    capabilities={
        AgentCapability("etl", "2.0"),
        AgentCapability("batch", "1.0")
    },
    tags={"production", "batch", "etl"},
    metadata={
        "tier": "premium",
        "region": "us-east-1",
        "max_batch_size": 10000
    },
    ttl_seconds=300  # 5 minutes
)

# BAD
await registry.register(
    agent_id="agent1",
    name="Agent",
    host="localhost",
    port=9000,
    capabilities={AgentCapability("compute", "1.0")}
)
```

---

### 2. Health Checking

✅ **DO:**
- Implement custom health checkers
- Check actual agent capabilities
- Return quickly (<100ms)
- Handle exceptions gracefully
- Monitor health check performance

❌ **DON'T:**
- Return always True/False
- Perform expensive operations
- Block indefinitely
- Ignore exceptions

```python
# GOOD
async def comprehensive_health_check():
    try:
        # Quick connectivity check
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://{agent_host}:{agent_port}/health",
                timeout=aiohttp.ClientTimeout(total=1.0)
            ) as response:
                if response.status != 200:
                    return False
                
                # Check resource availability
                data = await response.json()
                return data.get('cpu_percent', 100) < 90
    except Exception:
        return False

# BAD
async def simple_health_check():
    return True  # Always healthy (useless)
```

---

### 3. Error Handling

✅ **DO:**
- Use try/except/finally blocks
- Release resources in finally
- Log errors with context
- Propagate critical errors
- Provide fallback behavior

❌ **DON'T:**
- Swallow exceptions silently
- Forget to release connections
- Log without context
- Retry indefinitely

```python
# GOOD
async def execute_with_error_handling(task_id):
    agent_id = None
    try:
        selected = await load_balancer.select_agent("compute")
        if not selected:
            raise NoAvailableAgentsError("No compute agents available")
        
        agent_id = selected.agent.agent_id
        await load_balancer.acquire_connection(agent_id)
        
        result = await execute_task(task_id, agent_id)
        await circuit_breaker.record_success(agent_id)
        
        logger.info(
            "Task executed successfully",
            extra={"task_id": task_id, "agent_id": agent_id}
        )
        
        return result
        
    except Exception as e:
        if agent_id:
            await circuit_breaker.record_failure(agent_id)
        
        logger.error(
            "Task execution failed",
            extra={
                "task_id": task_id,
                "agent_id": agent_id,
                "error": str(e)
            },
            exc_info=True
        )
        raise
        
    finally:
        if agent_id:
            await load_balancer.release_connection(agent_id)

# BAD
async def execute_poorly(task_id):
    try:
        result = await execute_task(task_id)
    except:
        pass  # Silently ignored
    # Connection never released
```

---

### 4. Graceful Shutdown

✅ **DO:**
- Stop accepting new tasks
- Wait for active tasks to complete
- Release all resources
- Close connections
- Log shutdown progress

```python
# GOOD
async def graceful_shutdown():
    logger.info("Initiating graceful shutdown...")
    
    # 1. Stop accepting new tasks
    await task_queue.stop_accepting()
    logger.info("Stopped accepting new tasks")
    
    # 2. Wait for active tasks (with timeout)
    try:
        await asyncio.wait_for(
            worker_pool.wait_for_completion(),
            timeout=30.0
        )
        logger.info("All tasks completed")
    except asyncio.TimeoutError:
        logger.warning("Shutdown timeout, forcing stop")
    
    # 3. Stop workers
    await worker_pool.stop()
    logger.info("Workers stopped")
    
    # 4. Stop health monitoring
    await monitor.stop()
    logger.info("Health monitoring stopped")
    
    # 5. Deregister agents
    for agent in await registry.list_all():
        await registry.deregister(agent.agent_id)
    logger.info("All agents deregistered")
    
    logger.info("Shutdown complete")
```

---

## Next Steps

### 1. Run Examples

Start with the provided examples to understand integration patterns:

```bash
# Data processing pipeline
python examples/data_processing_pipeline.py

# Distributed computation
python examples/distributed_computation.py

# Fault-tolerant service
python examples/fault_tolerant_service.py

# Performance benchmark
python examples/performance_benchmark.py
```

### 2. Review Integration Tests

Study the integration tests to see components working together:

```bash
# Run integration tests
pytest tests/integration/test_orchestration_discovery.py -v
```

### 3. Build Your Application

Use the patterns and APIs to build your own distributed system:

1. Design agent capabilities and roles
2. Implement health checkers
3. Configure load balancing strategy
4. Set up circuit breakers
5. Define retry policies
6. Deploy and monitor

### 4. Performance Testing

Benchmark your system under load:

```bash
# Run performance tests
python examples/performance_benchmark.py
```

### 5. Production Deployment

Follow the deployment guide:
1. Configure environment variables
2. Set up monitoring
3. Deploy with Docker Compose
4. Configure health checks
5. Set up alerting

---

## Additional Resources

- **Examples:** [examples/](../../examples/) - Production-ready code samples
- **Tests:** [tests/integration/](../../tests/integration/) - Integration test suite
- **Architecture:** [PLATFORM_ARCHITECTURE.md](PLATFORM_ARCHITECTURE.md) - System design
- **API Documentation:** Auto-generated from code docstrings
- **Roadmap:** [docs/projects/THEME_EXECUTION_ROADMAP.md](../projects/THEME_EXECUTION_ROADMAP.md)

---

## Support

**Issues:** Report bugs and request features on GitHub Issues  
**Discussions:** Join community discussions on GitHub Discussions  
**Documentation:** Full documentation at [docs/](../../docs/)

---

**Last Updated:** December 29, 2025  
**Version:** 1.0  
**Platform Version:** v0.7.7
