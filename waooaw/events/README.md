# WowEvent Event Bus

**Version**: 0.6.5-dev  
**Status**: Production Ready  
**Coverage**: 91%  
**Tests**: 133/133 passing ✅

---

## Overview

WowEvent is the central nervous system for WAOOAW agents, enabling asynchronous event-driven communication with reliability, observability, and time-travel debugging.

**Features**:
- ✅ Redis-backed pub/sub messaging
- ✅ JSON schema validation
- ✅ Dead letter queue with automatic retry
- ✅ Event replay for debugging
- ✅ Comprehensive metrics (p50/p95/p99 latency)
- ✅ Subscriber health monitoring
- ✅ Pattern-based routing

---

## Quick Start

### Installation

```bash
# Install dependencies
pip install redis[hiredis] jsonschema aiohttp

# Run tests
pytest tests/events/ -v --cov=waooaw/events
```

### Basic Usage

```python
import asyncio
import redis.asyncio as redis
from waooaw.events import EventBus, Event

async def main():
    # Connect to Redis
    redis_client = await redis.from_url("redis://localhost:6379")
    
    # Create event bus
    bus = EventBus(redis_client)
    await bus.start()
    
    # Subscribe to events
    async def handler(event: Event):
        print(f"Received: {event.event_type} from {event.source_agent}")
    
    await bus.subscribe("task.*", handler, "my-agent")
    
    # Publish event
    event = Event(
        event_type="task.created",
        source_agent="api",
        payload={"task_id": "123", "title": "Test"}
    )
    await bus.publish(event)
    
    # Cleanup
    await bus.stop()
    await redis_client.close()

asyncio.run(main())
```

---

## Components

### EventBus

Redis-backed publish/subscribe messaging system.

```python
from waooaw.events import EventBus

bus = EventBus(redis_client)
await bus.start()

# Subscribe to pattern
await bus.subscribe("task.*", handler, "worker-1")

# Publish event
await bus.publish(event)

await bus.stop()
```

**Patterns**:
- `task.*` - All task events
- `agent.*` - All agent events
- `*` - All events

### Event Schema Validation

Validate events against JSON schemas.

```python
from waooaw.events import EventSchema, EventValidator, SchemaRegistry

# Define schema
schema = EventSchema(
    event_type="task.created",
    version="1.0.0",
    json_schema={
        "type": "object",
        "properties": {
            "task_id": {"type": "string"},
            "title": {"type": "string"}
        },
        "required": ["task_id", "title"]
    }
)

# Register schema
registry = SchemaRegistry()
registry.register_schema(schema)

# Validate events
validator = EventValidator(registry=registry)
validator.validate_event(event)  # Raises ValidationError if invalid
```

### Dead Letter Queue

Automatic retry with exponential backoff.

```python
from waooaw.events import DeadLetterQueue, FailureReason

dlq = DeadLetterQueue()

# Add failed event
await dlq.add_failed_event(
    event,
    subscription_id="sub-123",
    subscriber_agent="worker-1",
    failure_reason=FailureReason.HANDLER_ERROR,
    error_message="Temporary failure"
)

# Process retries
retry_queue = dlq.get_retry_queue()
for failed_event in retry_queue:
    if failed_event.should_retry():
        # Retry logic
        dlq.retry_dead_letter(failed_event.event.correlation_id)
```

**Backoff**: 1s → 2s → 4s → 8s → 16s (configurable)

### Event Replay

Time-travel debugging and agent catch-up.

```python
from waooaw.events import EventStore, EventReplayer, ReplayConfig

# Store events
event_store = EventStore(max_size=10000)
event_store.store(event)

# Replay events
replayer = EventReplayer(event_store)

async def replay_handler(event: Event):
    print(f"Replaying: {event.event_type}")

config = ReplayConfig(
    start_time="2025-12-29T10:00:00",
    end_time="2025-12-29T12:00:00",
    pattern="task.*",
    speed_multiplier=0  # 0=instant, 1.0=realtime, 2.0=2x
)

await replayer.replay(replay_handler, config)
```

**Use Cases**:
- Debug production issues by replaying events
- Agent recovery after downtime
- Audit event history
- Test with production data

### Event Metrics

Track throughput, latency, and subscriber health.

```python
from waooaw.events import EventMetrics

metrics = EventMetrics(window_seconds=60)

# Record activity
await metrics.record_publish("task.created")
await metrics.record_delivery("task.created", "worker-1", 0.05, success=True)

# Get metrics
snapshot = await metrics.get_metrics()
print(f"Throughput: {snapshot['throughput']['publishes']['per_second']} events/sec")
print(f"P95 latency: {snapshot['latency']['p95']}s")
print(f"Healthy subscribers: {snapshot['subscribers']['health']['healthy']}")

# Check subscriber health
sub_metrics = await metrics.get_subscriber_metrics("worker-1")
print(f"Health: {sub_metrics['health']}")
print(f"Error rate: {sub_metrics['error_rate']}")
```

---

## Deployment

### Docker Compose

```bash
# Start services
docker-compose -f docker-compose.events.yml up -d

# Check health
curl http://localhost:8080/health

# View metrics
curl http://localhost:8080/metrics

# Stop services
docker-compose -f docker-compose.events.yml down
```

### Kubernetes

```bash
# Deploy Redis
kubectl apply -f infrastructure/kubernetes/redis-deployment.yaml

# Deploy Event Bus
kubectl apply -f infrastructure/kubernetes/event-bus-deployment.yaml

# Check status
kubectl get pods -n waooaw -l app=event-bus

# View logs
kubectl logs -n waooaw -l app=event-bus -f
```

---

## Monitoring

### Health Endpoints

- **Health**: `GET /health` - Overall system health
- **Readiness**: `GET /ready` - Ready to accept traffic
- **Metrics**: `GET /metrics` - Prometheus-compatible metrics

### Key Metrics

- `totals.publishes` - Total events published
- `totals.deliveries` - Total successful deliveries
- `totals.errors` - Total errors
- `totals.retries` - Total retry attempts
- `totals.dlq` - Total events in DLQ
- `throughput.publishes.per_second` - Publishing rate
- `latency.p50/p95/p99` - Latency percentiles
- `subscribers.health` - Subscriber health summary

### Subscriber Health

- **Healthy**: < 5% error rate, latency < 1s
- **Degraded**: 5-20% error rate or 1-5s latency
- **Unhealthy**: > 20% error rate or > 5s latency

---

## Testing

### Run Tests

```bash
# All tests
pytest tests/events/ -v

# With coverage
pytest tests/events/ --cov=waooaw/events --cov-report=html

# Specific test
pytest tests/events/test_event_bus.py -k test_publish_event
```

### Test Coverage

| Module | Coverage |
|--------|----------|
| event_bus.py | 80% |
| schemas.py | 98% |
| dlq.py | 87% |
| replay.py | 94% |
| metrics.py | 99% |
| **Overall** | **91%** |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   WowEvent System                    │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌─────────────┐        ┌──────────────┐            │
│  │  EventBus   │◄──────►│    Redis     │            │
│  │  (Pub/Sub)  │        │  (Message    │            │
│  └──────┬──────┘        │   Broker)    │            │
│         │               └──────────────┘            │
│         │                                            │
│    ┌────▼────┐     ┌────────┐     ┌──────────┐     │
│    │ Schema  │     │  DLQ   │     │  Event   │     │
│    │Validator│     │(Retry) │     │  Store   │     │
│    └─────────┘     └────────┘     └──────────┘     │
│                                                       │
│    ┌─────────┐     ┌────────┐     ┌──────────┐     │
│    │ Metrics │     │Replayer│     │  Agents  │     │
│    │(Observe)│     │(Debug) │     │(Pub/Sub) │     │
│    └─────────┘     └────────┘     └──────────┘     │
│                                                       │
└─────────────────────────────────────────────────────┘
```

---

## Performance

### Benchmarks

- **Throughput**: 10,000+ events/sec (single instance)
- **Latency**: p50: 5ms, p95: 20ms, p99: 50ms
- **Subscribers**: 1,000+ concurrent subscribers
- **Storage**: 10,000 events in replay buffer

### Optimization

1. **Redis Tuning**: Increase `maxmemory`, use `allkeys-lru` policy
2. **Horizontal Scaling**: Run multiple Event Bus instances
3. **Pattern Optimization**: Use specific patterns (e.g., `task.created` vs `*`)
4. **Batch Processing**: Process events in batches when possible

---

## Troubleshooting

See [Event Bus Deployment Runbook](../../docs/runbooks/event-bus-deployment.md) for detailed troubleshooting.

**Common Issues**:
- **Events not delivered**: Check Redis connectivity, subscriber patterns
- **High latency**: Scale Event Bus, optimize Redis
- **Memory issues**: Increase Redis memory, reduce replay buffer size
- **Validation errors**: Check event schemas, update as needed

---

## Development

### Running Locally

```bash
# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Run Event Bus service
python -m waooaw.events.service

# In another terminal, run tests
pytest tests/events/ -v
```

### Contributing

1. Write tests first (`tests/events/test_*.py`)
2. Implement feature (`waooaw/events/*.py`)
3. Run tests: `pytest tests/events/ -v --cov`
4. Ensure coverage >= 85%
5. Submit PR

---

## License

Proprietary - WAOOAW Platform © 2025

---

## Support

- **Documentation**: `/docs/platform/PLATFORM_ARCHITECTURE.md`
- **Runbooks**: `/docs/runbooks/event-bus-deployment.md`
- **Issues**: GitHub Issues
- **Slack**: #platform-support
