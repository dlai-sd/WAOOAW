# WAOOAW Common Components Library Design

**Version**: 1.0  
**Date**: December 28, 2025  
**Status**: Design Complete, Implementation Week 5-10

---

## Executive Summary

This document specifies the **Common Components Library** (waooaw/common/) - a collection of 8 reusable infrastructure components used across all WAOOAW agents and platform services.

**Purpose**: Eliminate 40-60% code duplication, provide consistent behavior, enable single-source-of-truth maintenance.

**Scope**: Caching, Error Handling, Observability, State Management, Security, Resource Management, Validation, Messaging

**Implementation**: Week 5-10 (after 3+ CoEs operational, patterns validated)

---

## 1. Library Structure

```
waooaw/
  common/
    __init__.py
    cache.py              # CacheHierarchy, SimpleCache
    error_handler.py      # ErrorHandler, CircuitBreaker, RetryPolicy, DLQHandler
    observability.py      # ObservabilityStack (logs, metrics, traces)
    state.py              # StateManager, Serializable
    security.py           # SecurityLayer, HMAC, JWT, AuditLogger
    resource_manager.py   # ResourceManager, Budget, RateLimiter
    validator.py          # Validator, SchemaValidator, BusinessRuleValidator
    messaging.py          # MessageBus, MessageHandler, Priority (references MESSAGE_BUS_ARCHITECTURE.md)
```

---

## 2. Component: CacheHierarchy

**Purpose**: 3-level cache (L1 memory, L2 Redis, L3 PostgreSQL) with automatic promotion/demotion

**Usage**: Decision caching, context caching, response caching

**Appears In**: base_agent.py (5 places), message_bus, orchestration, API gateway

### 2.1 API Design

```python
from waooaw.common.cache import CacheHierarchy, SimpleCache

# Simple use case (80%):
cache = SimpleCache(max_size=1000)  # Just LRU dict
value = cache.get("key", default=None)
cache.set("key", value, ttl=3600)

# Advanced use case (20%):
cache = CacheHierarchy(
    l1_max_size=1000,      # In-memory, 1ms
    l2_ttl=300,            # Redis, 10ms, 5 min TTL
    l3_ttl=3600,           # PostgreSQL, 100ms, 1 hour TTL
    eviction_policy="LRU"  # or custom
)

# Get with automatic promotion:
value = cache.get("decision:123")
# L1 hit → return (1ms)
# L1 miss, L2 hit → promote to L1, return (10ms)
# L1/L2 miss, L3 hit → promote to L2+L1, return (100ms)
# All miss → return None

# Set with automatic demotion:
cache.set("decision:123", decision, ttl=3600)
# Writes to L1, async writes to L2+L3

# Get or compute:
value = cache.get_or_compute(
    key="decision:123",
    compute_fn=lambda: expensive_llm_call(),
    ttl=3600
)
```

### 2.2 Vision Compliance

✅ **Cost Optimization**: 90% cache hit = 90% free (no LLM calls)  
✅ **Zero Risk**: Graceful degradation (cache miss → compute)  
✅ **Simplicity**: SimpleCache for basic use, CacheHierarchy optional  
✅ **Marketplace DNA**: Per-agent cache isolation

### 2.3 Integration Points

- **base_agent.py**: Replace `_check_decision_cache()`, `_cache_decision()`
- **message_bus.py**: Agent response caching
- **orchestration.py**: Workflow state caching
- **api_gateway.py**: Response caching at gateway level

---

## 3. Component: ErrorHandler

**Purpose**: Retry with exponential backoff, circuit breaker, DLQ, graceful degradation

**Usage**: LLM API calls, Redis operations, database queries, agent-to-agent calls

**Appears In**: base_agent.py, message_bus (3-tier errors), orchestration (compensation), API gateway

### 3.1 API Design

```python
from waooaw.common.error_handler import ErrorHandler, RetryPolicy, CircuitBreaker, DLQHandler

# Basic usage (default: 3 retries, exponential backoff):
handler = ErrorHandler()
result = handler.execute(risky_operation)

# With fallback:
result = handler.execute(
    operation=llm_call,
    fallback=rule_based_decision,
    on_error=log_error
)

# Advanced configuration:
handler = ErrorHandler(
    retry_policy=RetryPolicy(
        max_attempts=3,
        base_delay=1.0,
        max_delay=60.0,
        backoff_multiplier=2.0,
        retryable_exceptions=[RedisError, LLMAPIError]
    ),
    circuit_breaker=CircuitBreaker(
        failure_threshold=5,
        timeout=60,  # seconds
        half_open_requests=3
    ),
    dlq_handler=DLQHandler(
        queue_name="failed_tasks",
        max_retries_before_dlq=3
    )
)

# Execute with all error handling:
result = handler.execute(operation)
```

### 3.2 Vision Compliance

✅ **Zero Risk**: Circuit breaker prevents cascading failures  
⚠️ **Human Escalation**: Max 3 retries, then escalate (not 10 retries)  
✅ **Cost Optimization**: Prevent wasted API calls during outages  
✅ **Simplicity**: Sensible defaults for 80% use cases

### 3.3 Integration Points

- **base_agent.py**: Replace `retry_with_backoff()`, `circuit_breaker()`, `send_to_dlq()` stubs
- **message_bus.py**: 3-tier error handling (immediate fail, retry, DLQ)
- **orchestration.py**: Compensation handlers (undo on failure)
- **api_gateway.py**: Circuit breaker for upstream services

---

## 4. Component: ObservabilityStack

**Purpose**: Structured logging (JSON), Prometheus metrics, OpenTelemetry traces

**Usage**: All agent operations, workflow execution, API requests, message bus operations

**Appears In**: base_agent.py, message_bus, orchestration, API gateway, config management

### 4.1 API Design

```python
from waooaw.common.observability import ObservabilityStack, MetricType

# Initialize once per agent:
obs = ObservabilityStack(
    service_name="wowvision_prime",
    log_level="INFO",
    log_format="json",  # Structured logging
    metrics_enabled=True,
    tracing_enabled=True,
    otel_endpoint="http://localhost:4318"  # Optional
)

# Structured logging:
obs.log_structured("decision_made", {
    "decision_type": "create_file",
    "method": "deterministic",
    "confidence": 0.95,
    "cost": 0.0
})

# Metrics:
obs.record_metric("decisions_total", 1, tags={"method": "deterministic"})
obs.record_metric("decision_cost_usd", 0.0, tags={"agent_id": agent_id})

# Distributed tracing:
with obs.trace_operation("make_decision") as span:
    span.set_attribute("decision_type", request_type)
    decision = make_decision()
    span.set_attribute("method", decision.method)
    span.set_attribute("cost", decision.cost)

# Cost breakdown:
cost_breakdown = obs.get_cost_breakdown()
# {"deterministic": 0.0, "cached": 0.0, "llm": 2.50, "total": 2.50}
```

### 4.2 Vision Compliance

✅ **Cost Tracking**: Find expensive agents, optimize 30-50%  
✅ **Zero Risk**: Monitor error rates, alert on spikes  
✅ **Simplicity**: Auto-configured, minimal setup  
✅ **Cost Optimization**: Identify bottlenecks, 20x faster

### 4.3 Integration Points

- **base_agent.py**: Replace `record_metric()`, `start_span()`, `end_span()`, `get_cost_breakdown()` stubs
- **message_bus.py**: Structured logging, metrics (throughput, DLQ rate, latency)
- **orchestration.py**: Workflow execution metrics
- **api_gateway.py**: Request/response logging, rate limit metrics
- **config_management.py**: Config drift metrics, validation failures

---

## 5. Component: StateManager

**Purpose**: Versioned state persistence with audit trail

**Usage**: Agent context, workflow instance state, message state

**Appears In**: base_agent.py (context management), orchestration (workflow state), message handler (message state)

### 5.1 API Design

```python
from waooaw.common.state import StateManager, Serializable

# Initialize with storage backend:
state_mgr = StateManager(
    storage_backend="postgres",  # or "redis" for ephemeral
    table_name="agent_state",
    versioning=True,
    audit_trail=True
)

# Save state:
state = {"current_step": "approval", "retry_count": 0}
state_mgr.save(
    state_id="workflow_123",
    state_data=state,
    increment_version=True
)

# Load state:
state = state_mgr.load("workflow_123")
# {"current_step": "approval", "retry_count": 0, "version": 2}

# Load specific version:
old_state = state_mgr.load("workflow_123", version=1)

# Atomic update:
state_mgr.atomic_update(
    state_id="workflow_123",
    update_fn=lambda state: {**state, "retry_count": state["retry_count"] + 1}
)
```

### 5.2 Vision Compliance

✅ **Context Preservation**: Agents wake with correct state  
✅ **Zero Risk**: Versioning prevents race conditions  
✅ **Simplicity**: Simple save/load API  
✅ **Audit Trail**: Track state changes (compliance)

### 5.3 Integration Points

- **base_agent.py**: Replace `_save_context()`, `_restore_context()`
- **orchestration.py**: `ProcessVariable` versioning, `WorkflowInstance` state
- **message_handler.py**: `MessageState` tracking

---

## 6. Component: SecurityLayer

**Purpose**: HMAC signing, JWT validation, audit logging, encryption

**Usage**: Agent-to-agent messages, customer API, config secrets, audit trail

**Appears In**: base_agent.py, message_bus (HMAC), API gateway (JWT), config management (secrets)

### 6.1 API Design

```python
from waooaw.common.security import SecurityLayer, HMAC, JWT, AuditLogger

# Initialize with secrets:
security = SecurityLayer(
    hmac_secret=os.getenv("HMAC_SECRET"),
    jwt_secret=os.getenv("JWT_SECRET"),
    jwt_algorithm="HS256",
    audit_enabled=True
)

# HMAC signing (agent-to-agent):
signature = security.hmac_sign(message)
if security.hmac_verify(message, signature):
    process_message()

# JWT tokens (customer API):
token = security.jwt_create(
    user_id="customer_123",
    role="trial",
    expires_in=3600
)
claims = security.jwt_verify(token)

# Audit logging:
security.audit_log(
    action="decision_made",
    agent_id=agent_id,
    resource="file:README.md",
    decision={"approved": False}
)

# Encryption (config secrets):
encrypted = security.encrypt_data(api_key)
decrypted = security.decrypt_data(encrypted)
```

### 6.2 Vision Compliance

✅ **Safety**: Tamper-proof audit trail (7 years compliance)  
✅ **Zero Risk**: HMAC prevents message tampering  
✅ **GDPR/COPPA**: Required for Education gateway  
⚠️ **Human Escalation**: Audit log shows all decisions (no bypass)

### 6.3 Integration Points

- **base_agent.py**: Replace `authenticate()`, `encrypt_data()`, `decrypt_data()`, `audit_log()` stubs
- **message_bus.py**: HMAC signature generation/verification
- **api_gateway.py**: JWT validation (Central Gateway), HMAC (Agent Management Gateway)
- **config_management.py**: Secrets encryption

---

## 7. Component: ResourceManager

**Purpose**: Token budgets, rate limiting, cost tracking, fair queuing

**Usage**: LLM API calls, agent requests, API gateway rate limits

**Appears In**: base_agent.py, API gateway (rate limiting per gateway)

### 7.1 API Design

```python
from waooaw.common.resource_manager import ResourceManager, Budget, RateLimiter

# Initialize with budgets:
resource_mgr = ResourceManager(
    budgets={
        "wowvision_prime": Budget(
            tokens_per_day=100_000,
            requests_per_minute=50,
            priority="HIGH"
        ),
        "wowcontent": Budget(
            tokens_per_day=50_000,
            requests_per_minute=30,
            priority="MEDIUM"
        )
    }
)

# Check budget before operation:
if resource_mgr.check_budget(agent_id, tokens=5000):
    result = make_llm_call()
    resource_mgr.consume(agent_id, tokens=response.usage.total_tokens)
else:
    raise BudgetExceededError("Daily token limit reached")

# Rate limiting:
if resource_mgr.check_rate_limit(agent_id, window=60):
    process_request()
else:
    raise RateLimitError("50 requests/minute limit reached")

# Get status:
status = resource_mgr.get_status(agent_id)
# {"tokens_used": 45000, "tokens_remaining": 55000, "requests_this_minute": 12}
```

### 7.2 Vision Compliance

✅ **Cost Control**: Prevent runaway costs ($100/day → $10/day)  
✅ **Zero Risk**: Budget limits prevent surprises  
✅ **Marketplace DNA**: Per-agent budgets (isolation)  
✅ **Cost Optimization**: Fair resource allocation

### 7.3 Integration Points

- **base_agent.py**: Replace `check_budget()`, `consume_resource()`, `get_rate_limit_status()` stubs
- **api_gateway.py**: Rate limiting (1000/500/200 req/min per gateway)

---

## 8. Component: Validator

**Purpose**: Schema validation, business rules, connectivity checks

**Usage**: Config validation, message validation, decision validation

**Appears In**: config_management (5-layer validation), message_bus (schema validation), base_agent (LLM decision validation)

### 8.1 API Design

```python
from waooaw.common.validator import Validator, SchemaValidator, BusinessRuleValidator, ConnectivityValidator

# Compose validators:
validator = Validator([
    SchemaValidator(schema=config_schema),
    BusinessRuleValidator(rules=[
        lambda cfg: cfg["port"] > 1024,  # No privileged ports
        lambda cfg: cfg["db_host"] != "localhost" or cfg["env"] == "dev"  # Localhost only in dev
    ]),
    ConnectivityValidator(checks=[
        lambda cfg: check_redis_connection(cfg["redis_url"]),
        lambda cfg: check_postgres_connection(cfg["db_url"])
    ])
])

# Validate:
errors = validator.validate(config)
if errors:
    raise ValidationError(f"Validation failed: {errors}")

# Schema validation only:
schema_validator = SchemaValidator({
    "type": "object",
    "required": ["port", "db_host"],
    "properties": {
        "port": {"type": "integer", "minimum": 1024},
        "db_host": {"type": "string"}
    }
})
errors = schema_validator.validate(config)
```

### 8.2 Vision Compliance

✅ **Safety**: Catch errors before production (10,000x ROI)  
✅ **Zero Risk**: Validation prevents AWS S3-style outages  
✅ **Simplicity**: Compose validators, add rules incrementally  
✅ **Cost Optimization**: Prevent outages (1 prevented = all validation justified)

### 8.3 Integration Points

- **config_management.py**: 5-layer validation (syntax, schema, business rules, connectivity, runtime)
- **message_bus.py**: Schema validation (InvalidMessageError)
- **base_agent.py**: `_validate_llm_decision()` (confidence check, reason length)

---

## 9. Vision Compliance Summary

| Component | Cost Optimization | Zero Risk | Human Escalation | Simplicity | Marketplace DNA |
|-----------|-------------------|-----------|------------------|------------|-----------------|
| **CacheHierarchy** | ✅ 90% cache hit | ✅ Graceful degradation | ✅ N/A | ✅ SimpleCache option | ✅ Per-agent isolation |
| **ErrorHandler** | ✅ Prevent wasted API calls | ✅ Circuit breaker | ⚠️ Max 3 retries, then escalate | ✅ Sensible defaults | ✅ Per-agent config |
| **ObservabilityStack** | ✅ Find expensive agents | ✅ Monitor error rates | ✅ Audit trail | ✅ Auto-configured | ✅ Per-agent metrics |
| **StateManager** | ✅ Efficient state storage | ✅ Versioning, no races | ✅ Audit trail | ✅ Simple save/load | ✅ Per-agent state |
| **SecurityLayer** | ✅ N/A | ✅ Tamper-proof audit | ✅ Audit log | ✅ Simple API | ✅ Multi-tenant isolation |
| **ResourceManager** | ✅ Budget limits | ✅ Prevent overruns | ✅ Escalate on limit | ✅ Simple check/consume | ✅ Per-agent budgets |
| **Validator** | ✅ Prevent outages | ✅ 10,000x ROI | ✅ Safety first | ✅ Compose validators | ✅ Per-agent rules |
| **Messaging** | ✅ Efficient communication | ✅ Reliable delivery | ✅ Human visibility | ✅ Simple pub/sub | ✅ Per-agent topics |

**Overall Compliance**: ✅ **APPROVED** - All components align with WAOOAW vision

---

## 10. Implementation Timeline

**Week 5-6: Foundation**
- Implement CacheHierarchy, SimpleCache
- Implement ErrorHandler, RetryPolicy, CircuitBreaker, DLQHandler
- 95% test coverage, chaos testing

**Week 7: Pilot (WowVision Prime)**
- Deploy components to 1 agent (low risk)
- Monitor for issues (error rate, latency, cost)
- Collect feedback

**Week 8: Canary (3 agents)**
- Deploy to WowVision Prime, WowDomain, WowBrand
- Monitor closely, iterate based on feedback

**Week 9: Expansion (10 agents)**
- Deploy to 10 agents across 3 CoEs
- Confident after 3 weeks of production use

**Week 10: Full Rollout**
- Deploy to all agents (14 CoEs × 14 instances = 196 agents)
- ObservabilityStack, StateManager, SecurityLayer, ResourceManager, Validator

---

## 11. Testing Requirements

**95% Test Coverage** (vs 80% for agents):
- **Unit Tests (80%)**: Each component method, edge cases
- **Integration Tests (15%)**: Real Redis/PostgreSQL, component interactions
- **Chaos Tests (5%)**: Redis down, DB slow, network partition

**Example Tests**:
```python
# tests/common/test_cache.py
def test_cache_concurrent_writes():
    """100 threads writing simultaneously"""
    
def test_cache_redis_down():
    """Graceful degradation when Redis unavailable"""
    
def test_cache_memory_leak():
    """LRU eviction prevents unbounded growth"""
    
def test_cache_serialization_edge_cases():
    """None, empty dict, circular references"""
```

---

## 12. Monitoring & Alerts

**Component Metrics**:
- `component.error_rate` - Alert if >1%
- `component.latency_p95` - Alert if >5ms
- `component.cache_hit_rate` - Alert if <50%
- `component.budget_utilization` - Alert if >90%

**Kill Switch**:
```bash
# Disable component globally:
export DISABLE_CACHE_COMPONENT=true
export DISABLE_ERROR_HANDLER_COMPONENT=true
```

---

## 13. Migration Strategy

**Phase 1: Add Components (No Breaking Changes)**
- Agents continue using existing code
- Components available but optional
- New agents can use components

**Phase 2: Gradual Migration (Week 7-10)**
- Migrate 1 agent per week
- Monitor for regressions
- Rollback if issues

**Phase 3: Deprecate Old Code (Week 11-24)**
- Mark old patterns as deprecated
- Provide migration guide
- Remove after all agents migrated

**No Big Bang**: Components are additive, not replacement

---

## 14. Documentation Requirements

**Per Component**:
1. **5-Minute Quickstart** - Get started fast
2. **API Reference** - All methods, parameters, return values
3. **Usage Examples** - Common patterns, anti-patterns
4. **Vision Compliance** - How it aligns with WAOOAW philosophy
5. **Integration Guide** - How to integrate with base_agent.py
6. **Testing Guide** - How to test agents using component
7. **Troubleshooting** - Common issues, debugging

**Component Documentation Template**:
```markdown
# Component: CacheHierarchy

## Quickstart (5 minutes)
[Simple example]

## When to Use
[Use cases]

## When NOT to Use
[Anti-patterns, escape hatches]

## API Reference
[All methods]

## Vision Compliance
[Cost optimization, zero-risk, etc.]

## Integration
[How to add to agent]

## Testing
[How to test]

## Troubleshooting
[Common issues]
```

---

## 15. Success Metrics

**Code Reduction**: 40-60% (1,200-1,700 lines saved)  
**Maintenance**: Fix once vs 4-6 times  
**Testing**: Test once vs 4-6 times  
**Consistency**: All agents behave identically  
**Performance**: <5% overhead on hot paths  
**Reliability**: 99.9% uptime (component availability)  
**Adoption**: 100% of agents using components by Week 24

---

## Conclusion

Common components library provides **single source of truth** for infrastructure patterns, reducing duplication by 40-60% while maintaining vision alignment. Implementation in Week 5-10 follows gradual rollout strategy (1 agent → 3 agents → 10 agents → all agents) with 95% test coverage, kill switches, and comprehensive monitoring.

**Next Steps**:
1. Implement components (Week 5-6)
2. Deploy to WowVision Prime (Week 7)
3. Expand to 3 agents (Week 8)
4. Expand to 10 agents (Week 9)
5. Full rollout (Week 10)
