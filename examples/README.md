# WAOOAW Examples

Real-world examples demonstrating the WAOOAW multi-agent orchestration and discovery platform.

## Overview

These examples showcase how to build production-ready distributed systems using WAOOAW's orchestration and discovery components:

- **Service Registry** - Agent registration with capabilities and tags
- **Health Monitoring** - Continuous health checks with configurable thresholds
- **Load Balancing** - Intelligent agent selection (round-robin, least-connections, weighted, random)
- **Circuit Breakers** - Fault isolation and automatic recovery
- **Retry Logic** - Exponential backoff with jitter
- **Task Orchestration** - Priority queuing and worker pool management

## Examples

### 1. Data Processing Pipeline

**File:** [`data_processing_pipeline.py`](data_processing_pipeline.py)

**Use Case:** Multi-stage ETL pipeline with specialized agents for each stage

**Demonstrates:**
- 5-stage pipeline: Ingestion → Validation → Transformation → Aggregation → Export
- Specialized agents with capability-based routing
- Health monitoring with automatic failover
- Load-balanced task distribution
- Fault tolerance with circuit breakers

**Run:**
```bash
cd examples
PYTHONPATH=/workspaces/WAOOAW python data_processing_pipeline.py
```

**Architecture:**
```
┌─────────────┐
│  Ingestion  │ (3 agents) - Load data
└──────┬──────┘
       ↓
┌─────────────┐
│ Validation  │ (2 agents) - Check quality
└──────┬──────┘
       ↓
┌─────────────┐
│Transform    │ (4 agents) - Apply transformations
└──────┬──────┘
       ↓
┌─────────────┐
│ Aggregation │ (2 agents) - Compute aggregates
└──────┬──────┘
       ↓
┌─────────────┐
│   Export    │ (1 agent) - Save results
└─────────────┘
```

**Output:**
```
🚀 Starting Data Processing Pipeline (10 batches)
================================================

📥 Stage 1-3: Ingestion → Validation → Transformation

  📥 Ingested 3247 records (batch batch-001) via ingestion-0
  🔍 Validated batch batch-001: ✅ valid via validation-1
  ⚙️  Transformed batch batch-001 via transform-2
  ...

📊 Stage 4: Aggregation

  📊 Aggregated 9/10 batches (28,423 records) via aggregate-0

💾 Stage 5: Export

  💾 Exported results via export-0

✅ Pipeline Complete!
Duration: 12.45s
Total batches: 10
Valid batches: 9
Total records: 28,423
```

---

### 2. Distributed Computation

**File:** [`distributed_computation.py`](distributed_computation.py)

**Use Case:** Parallel computation with tiered worker pools

**Demonstrates:**
- 3-tier compute cluster: Premium (fast) / Standard (normal) / Budget (slow)
- Weighted load balancing (premium agents get 10x more tasks)
- GPU capability routing
- Dynamic scaling based on workload
- Performance-aware task distribution

**Run:**
```bash
cd examples
PYTHONPATH=/workspaces/WAOOAW python distributed_computation.py
```

**Architecture:**
```
┌──────────────────────────────────┐
│     Compute Cluster              │
│                                  │
│  ⚡ Premium (3 agents, 10x)     │
│     - 8 cores, high memory       │
│     - GPU support                │
│     - 98% uptime                 │
│                                  │
│  ⚙️  Standard (5 agents, 1x)    │
│     - 4 cores, standard memory   │
│     - 92% uptime                 │
│                                  │
│  🐢 Budget (4 agents, 0.5x)     │
│     - 2 cores, low memory        │
│     - 85% uptime                 │
└──────────────────────────────────┘
```

**Output:**
```
🚀 Starting Distributed Computation
Tasks: 100
Complexity: 1.0x - 2.5x
Parallel workers: 15

  ⚡ Task 001 completed via premium-0 (0.087s, π≈3.1423)
  ⚙️  Task 002 completed via standard-2 (0.154s, π≈3.1409)
  ...

✅ Batch Complete!
Duration: 8.32s
Successful tasks: 98/100 (98.0%)
Average π estimate: 3.141598 (error: 0.000%)
Throughput: 11.8 tasks/sec

📊 Agent Utilization:
  ⚡ Premium    premium-0        42 tasks (42.9%)
  ⚡ Premium    premium-1        38 tasks (38.8%)
  ⚙️  Standard  standard-1       8 tasks ( 8.2%)
  ...
```

---

### 3. Fault-Tolerant Service

**File:** [`fault_tolerant_service.py`](fault_tolerant_service.py)

**Use Case:** Highly available API service with comprehensive fault tolerance

**Demonstrates:**
- Multi-tier service replicas (primary/secondary/backup)
- Health monitoring with degraded state detection
- Circuit breakers for cascading failure prevention
- Automatic retry with exponential backoff
- Graceful degradation under high load
- Load balancing with least-connections strategy

**Run:**
```bash
cd examples
PYTHONPATH=/workspaces/WAOOAW python fault_tolerant_service.py
```

**Architecture:**
```
┌────────────────────────────────────┐
│   Service Fleet (9 replicas)      │
│                                    │
│  🟢 Primary (3) - 90% healthy      │
│     - Database + API               │
│     - High reliability             │
│                                    │
│  🟡 Secondary (4) - 80% healthy    │
│     - Cache + API                  │
│     - Good reliability             │
│                                    │
│  🔴 Backup (2) - 70% healthy       │
│     - API only                     │
│     - Fallback tier                │
└────────────────────────────────────┘

Load Balancer (Least Connections)
          ↓
Health Monitor (5s interval)
          ↓
Circuit Breakers (50% threshold)
          ↓
Retry Logic (3 attempts, exp backoff)
```

**Output:**
```
🚀 Load Test Starting
Total requests: 200
Concurrency: 20

✅ Load Test Complete!
Duration: 15.23s
Throughput: 13.1 req/sec

📊 Request Statistics:
  Total: 200
  Successful: 194 (97.0%)
  Failed: 6 (3.0%)
  Retried: 23

⏱️  Latency:
  Average: 145.3ms
  P95: 287.1ms

🔄 Request Distribution:
  🟢 Primary     primary-0        64 requests (33.0%)
  🟢 Primary     primary-1        58 requests (29.9%)
  🟡 Secondary   secondary-2      31 requests (16.0%)
  ...

🏥 Health Summary:
  Healthy: 7/9
  ⚠️  Unhealthy: 2 agents

🔌 Circuit Breaker Summary:
  ⚠️  Open: 1 circuits
  ✅ Majority healthy
```

---

## Common Patterns

### 1. Agent Registration

```python
from waooaw.discovery import ServiceRegistry, AgentCapability

registry = ServiceRegistry()

await registry.register(
    agent_id="worker-1",
    name="Worker 1",
    host="localhost",
    port=8001,
    capabilities={
        AgentCapability("compute", "1.0"),
        AgentCapability("storage", "2.0"),
    },
    tags=["production", "high-performance"],
)
```

### 2. Health Monitoring

```python
from waooaw.discovery import HealthMonitor

monitor = HealthMonitor(registry, failure_threshold=3)

# Custom health checker
async def check_health():
    # Your health check logic
    return True  # healthy

monitor.register_health_checker("worker-1", check_health)
await monitor.start()
```

### 3. Load Balancing

```python
from waooaw.discovery import LoadBalancer, LoadBalancingStrategy

lb = LoadBalancer(
    registry,
    health_monitor=monitor,
    strategy=LoadBalancingStrategy.LEAST_CONNECTIONS,
)

# Select agent
agent = await lb.select_agent(
    capability="compute",
    require_healthy=True,
)

# Use agent
await lb.acquire_connection(agent.agent.agent_id)
# ... do work ...
await lb.release_connection(agent.agent.agent_id)
```

### 4. Circuit Breakers

```python
from waooaw.discovery import CircuitBreaker

cb = CircuitBreaker(
    failure_threshold=0.5,  # Open at 50% failure rate
    minimum_requests=5,      # Need 5 requests before opening
    timeout=60.0,           # Try half-open after 60s
)

try:
    # Your operation
    result = await do_something()
    await cb.record_success("agent-1")
except Exception:
    await cb.record_failure("agent-1")
    raise
```

### 5. Retry Logic

```python
from waooaw.orchestration import RetryPolicy, RetryConfig, RetryStrategy

retry_policy = RetryPolicy(
    config=RetryConfig(
        max_retries=3,
        strategy=RetryStrategy.EXPONENTIAL,
        base_delay=0.1,
        max_delay=2.0,
        jitter=0.2,
    )
)

for attempt in range(retry_policy.config.max_retries):
    try:
        return await operation()
    except Exception:
        if attempt < retry_policy.config.max_retries - 1:
            delay = retry_policy.calculate_delay(attempt)
            await asyncio.sleep(delay)
        else:
            raise
```

---

## Key Concepts

### Service Registry
- **Purpose:** Central registry for agent discovery
- **Features:** TTL-based expiration, heartbeat mechanism, capability/tag filtering
- **Use When:** Need to discover agents dynamically

### Health Monitoring
- **Purpose:** Continuous health assessment of agents
- **Features:** 4-state health (HEALTHY/DEGRADED/UNHEALTHY/UNKNOWN), EMA metrics, custom checkers
- **Use When:** Need to detect and route around unhealthy agents

### Load Balancer
- **Purpose:** Intelligent agent selection for optimal distribution
- **Strategies:**
  - **Round-robin:** Fair distribution
  - **Least-connections:** Route to least busy
  - **Weighted:** Prioritize premium agents
  - **Random:** Simple random selection
- **Use When:** Multiple agents can handle a task

### Circuit Breaker
- **Purpose:** Prevent cascading failures
- **States:** CLOSED (normal) → OPEN (failing) → HALF_OPEN (recovering)
- **Use When:** Need to isolate failing components

### Retry Policy
- **Purpose:** Automatic retry with backoff
- **Strategies:** Fixed, Exponential, Linear, Random
- **Use When:** Transient failures are expected

---

## Performance Tips

1. **Right-size worker pools:** Match `max_workers` to CPU cores
2. **Tune health check intervals:** Balance responsiveness vs overhead
3. **Configure circuit breaker thresholds:** Adjust based on error rates
4. **Use weighted load balancing:** Route more to premium agents
5. **Enable connection pooling:** Reuse connections where possible
6. **Monitor metrics:** Track latency, throughput, error rates

---

## Best Practices

### 1. Graceful Shutdown
```python
try:
    await worker_pool.start()
    await monitor.start()
    # Do work
finally:
    await worker_pool.stop()
    await monitor.stop()
```

### 2. Error Handling
```python
try:
    await operation()
    await circuit_breaker.record_success(agent_id)
except Exception as e:
    await circuit_breaker.record_failure(agent_id)
    # Handle or retry
```

### 3. Resource Cleanup
```python
await load_balancer.acquire_connection(agent_id)
try:
    # Use agent
    pass
finally:
    await load_balancer.release_connection(agent_id)
```

### 4. Health Check Design
- Keep checks lightweight (<100ms)
- Check actual dependencies (DB, APIs)
- Return degraded state when slow
- Avoid false positives

---

## Troubleshooting

### All agents unhealthy
- Check health checker implementation
- Verify failure threshold settings
- Check network connectivity

### Circuit breakers stuck open
- Increase timeout value
- Lower failure threshold
- Verify agents are actually healthy

### Poor load distribution
- Check agent weights
- Verify health status
- Try different load balancing strategy

### High retry rates
- Increase retry delay
- Lower max retries
- Fix underlying agent issues

---

## Next Steps

- Explore integration tests in [`tests/integration/`](../tests/integration/)
- Review architecture docs in [`docs/platform/`](../docs/platform/)
- See production deployment guide in [`docs/runbooks/`](../docs/runbooks/)

---

**Questions?** Check the [WAOOAW documentation](../README.md) or open an issue.
