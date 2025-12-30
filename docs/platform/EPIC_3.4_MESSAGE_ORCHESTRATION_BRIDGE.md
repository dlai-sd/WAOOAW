# Epic 3.4: Message Bus & Orchestration Integration Bridge

**Status**: PLANNED  
**Priority**: P0 (Critical)  
**Target Version**: v0.8.0  
**Estimated Duration**: 2 weeks  
**Total Points**: 42  
**Dependencies**: Epic 3.3 (Orchestration Runtime)

---

## Executive Summary

While both the Event Bus (v0.6.5-dev) and Orchestration Runtime (v0.7.3) are individually complete, critical gaps prevent their production deployment and integration. This Epic bridges these gaps by:

1. **Fixing critical syntax errors** blocking all imports and tests
2. **Achieving deployment parity** between Message Bus and Orchestration
3. **Implementing event-driven orchestration** for seamless integration
4. **Establishing monitoring & observability** across both systems

---

## Current State Analysis

### Event Bus (Message Bus) ✅
- **Status**: Production Ready
- **Tests**: 133/133 passing (91% coverage)
- **Documentation**: Comprehensive 405-line README
- **Deployment**: Docker Compose + Kubernetes + Runbooks
- **Version**: 0.6.5-dev

### Orchestration Runtime ⚠️
- **Status**: Code Complete, Validation Blocked
- **Tests**: ❌ Cannot run (import errors due to syntax error in wowtrialmanager.py)
- **Documentation**: ❌ Missing README
- **Deployment**: ❌ No infrastructure
- **Version**: 0.7.3

### Critical Gaps Identified

#### 1. **BLOCKER: Syntax Error** (Lines 1620-1630, wowtrialmanager.py)
```python
# Unterminated string literal at line 1627
trial = await self.db.trials.find_one({"trial_id": trial_id}")
```
**Impact**: All imports fail, 11 test errors, orchestration validation impossible

#### 2. **Documentation Disparity**
- Event Bus: 405-line README with examples, architecture, deployment
- Orchestration: No README, no usage examples

#### 3. **Deployment Disparity**
- Event Bus: Docker Compose, Kubernetes manifests, runbooks
- Orchestration: No deployment artifacts

#### 4. **Integration Gap**
- No event-driven task triggering
- No orchestration result publishing to event bus
- No end-to-end integration tests

#### 5. **Observability Gap**
- Event Bus has metrics (p50/p95/p99, throughput)
- Orchestration has worker metrics
- No unified dashboard or correlated tracing

---

## Epic Goals

### Primary Objectives
1. ✅ Unblock orchestration tests by fixing syntax errors
2. 📚 Achieve documentation parity with Event Bus
3. 🚀 Establish deployment infrastructure for orchestration
4. 🔗 Implement event-driven orchestration integration
5. 📊 Unified monitoring across Message Bus + Orchestration

### Success Criteria
- [ ] All 131+ orchestration tests passing
- [ ] Orchestration README matching Event Bus quality (400+ lines)
- [ ] Docker Compose + Kubernetes manifests for orchestration
- [ ] Tasks triggerable via event bus events
- [ ] Task results published as events
- [ ] End-to-end integration test: Event → Orchestration → Event
- [ ] Unified Grafana dashboard for both systems

---

## Stories

### Story 1: Fix Critical Syntax Errors & Unblock Tests ⚡
**Priority**: P0 (Blocker)  
**Points**: 3  
**Assignee**: TBD  
**Dependencies**: None

#### Description
Fix the syntax error in wowtrialmanager.py line 1627 blocking all imports. Validate that all 131+ orchestration tests can collect and run successfully.

#### Tasks
- [ ] Fix unterminated string literal in wowtrialmanager.py:1627
- [ ] Run `pytest tests/orchestration/ --collect-only` (should collect ~131 tests)
- [ ] Run full orchestration test suite: `pytest tests/orchestration/ -v`
- [ ] Verify 0 import errors, 131+ tests collected
- [ ] Check test coverage remains >85%

#### Acceptance Criteria
- [x] Syntax error fixed in wowtrialmanager.py
- [ ] `pytest tests/orchestration/ --collect-only` returns 0 errors
- [ ] All orchestration tests pass (131+ tests)
- [ ] Coverage ≥85%
- [ ] CI/CD pipeline green for orchestration tests

#### Technical Notes
```bash
# Validate fix
python -c "from waooaw.orchestration import TaskQueue, Worker, DependencyGraph"
pytest tests/orchestration/ --collect-only
pytest tests/orchestration/ -v --cov=waooaw.orchestration
```

#### Definition of Done
- Syntax error resolved
- All imports work
- Test suite runs successfully
- Coverage report generated

---

### Story 2: Orchestration Documentation Parity 📚
**Priority**: P1 (High)  
**Points**: 5  
**Assignee**: TBD  
**Dependencies**: Story 1 (tests must pass for examples)

#### Description
Create comprehensive README for waooaw/orchestration matching the quality and structure of waooaw/events/README.md (405 lines). Include architecture, usage examples, API reference, and integration patterns.

#### Tasks
- [ ] Create waooaw/orchestration/README.md (400+ lines)
- [ ] Document architecture (task queue, dependency graph, worker pool, retry/saga)
- [ ] Quick start guide with code examples
- [ ] API reference for all 5 components
- [ ] Integration examples with Event Bus
- [ ] Performance tuning guide
- [ ] Add examples/ directory with sample workflows
- [ ] Update docs/platform/ with orchestration architecture diagram

#### Content Structure
```markdown
# Orchestration Runtime

## Overview
- What it does
- Key features
- When to use

## Architecture
- Component diagram
- Task lifecycle
- Worker pool management
- Dependency resolution flow

## Quick Start
- Installation
- Basic task example
- Dependency example
- Worker pool example

## Components
### Task Queue
- Priority-based queuing
- State management
- Statistics

### Dependency Resolver
- Topological sort
- Cycle detection
- Execution planning

### Worker Pool
- Concurrent execution
- Load balancing
- Health monitoring

### Retry & Compensation
- Retry policies
- Saga pattern
- Rollback strategies

## Integration
- Event-driven orchestration
- Publishing results
- Cross-component patterns

## Deployment
- Local development
- Docker setup
- Kubernetes deployment

## Performance
- Tuning worker count
- Optimizing dependencies
- Monitoring metrics

## API Reference
- Complete API docs
```

#### Acceptance Criteria
- [ ] README.md created with 400+ lines
- [ ] Matches Event Bus README quality
- [ ] Includes 5+ working code examples
- [ ] Architecture diagram included
- [ ] Integration patterns documented
- [ ] Peer review approved

#### Definition of Done
- README committed to main branch
- Examples validated (all run successfully)
- Documentation website updated

---

### Story 3: Event-Driven Task Orchestration 🔗
**Priority**: P1 (High)  
**Points**: 8  
**Assignee**: TBD  
**Dependencies**: Story 1 (tests must pass)

#### Description
Enable task orchestration to be triggered by Event Bus events. Implement event-to-task mapping, automatic task creation from events, and lifecycle event publishing.

#### Tasks
- [ ] Create `waooaw/orchestration/event_adapter.py` (300+ lines)
  - EventToTaskMapper
  - TaskEventPublisher
  - OrchestrationEventHandler
- [ ] Implement event subscription for task triggers
  - Subscribe to `orchestration.*` event patterns
  - Map event payloads to Task objects
  - Handle task creation errors
- [ ] Implement task lifecycle event publishing
  - `task.created`, `task.started`, `task.completed`, `task.failed`
  - Include task metadata, duration, worker info
- [ ] Add integration tests (tests/integration/test_event_orchestration.py)
  - Event → Task creation
  - Task execution → Event publishing
  - Error handling → DLQ

#### Implementation Example
```python
# waooaw/orchestration/event_adapter.py
from waooaw.events import EventBus, Event
from waooaw.orchestration import TaskQueue, Task

class OrchestrationEventHandler:
    """Handle event-driven task orchestration"""
    
    def __init__(self, event_bus: EventBus, task_queue: TaskQueue):
        self.event_bus = event_bus
        self.task_queue = task_queue
    
    async def start(self):
        """Subscribe to orchestration events"""
        await self.event_bus.subscribe(
            "orchestration.task.trigger",
            self._handle_task_trigger
        )
    
    async def _handle_task_trigger(self, event: Event):
        """Create task from event"""
        task = Task(
            name=event.data["task_name"],
            func=event.data["func"],
            args=event.data.get("args", []),
            priority=event.data.get("priority", "NORMAL")
        )
        task_id = await self.task_queue.add_task(task)
        
        # Publish task created event
        await self.event_bus.publish(Event(
            type="orchestration.task.created",
            data={"task_id": task_id, "trigger_event_id": event.id}
        ))
```

#### Acceptance Criteria
- [ ] EventToTaskMapper converts events to tasks
- [ ] TaskEventPublisher publishes lifecycle events
- [ ] OrchestrationEventHandler subscribes and processes events
- [ ] Integration tests pass (10+ scenarios)
- [ ] Event replay works for failed tasks
- [ ] Documentation includes event schemas

#### Metrics
- Event-to-task latency <100ms (p95)
- Task lifecycle events published within 50ms
- 100% event delivery (no dropped tasks)

#### Definition of Done
- Code complete with tests
- Integration validated
- Documentation updated
- Metrics tracked

---

### Story 4: Orchestration Result Publishing 📤
**Priority**: P2 (Medium)  
**Points**: 5  
**Assignee**: TBD  
**Dependencies**: Story 3 (event integration)

#### Description
Automatically publish task results, worker metrics, and orchestration status to Event Bus. Enable downstream consumers to react to orchestration outcomes.

#### Tasks
- [ ] Implement result event publishing in worker_pool.py
  - Publish on task completion
  - Include result data, duration, worker info
- [ ] Implement metric event publishing
  - Periodic worker pool metrics
  - Task queue statistics
  - Dependency resolution stats
- [ ] Create result event schemas
  - `orchestration.task.completed`
  - `orchestration.task.failed`
  - `orchestration.metrics.snapshot`
- [ ] Add result consumer examples
- [ ] Integration tests for result flow

#### Event Schemas
```python
# orchestration.task.completed
{
  "task_id": "task-123",
  "name": "process_data",
  "result": {...},
  "duration_ms": 1234,
  "worker_id": "worker-5",
  "completed_at": "2025-12-30T10:00:00Z"
}

# orchestration.metrics.snapshot
{
  "timestamp": "2025-12-30T10:00:00Z",
  "task_queue": {
    "pending": 10,
    "running": 5,
    "completed": 100
  },
  "worker_pool": {
    "active_workers": 8,
    "idle_workers": 2,
    "throughput_per_min": 45
  }
}
```

#### Acceptance Criteria
- [ ] Task results published as events
- [ ] Metrics published every 10 seconds
- [ ] Event schemas validated
- [ ] Consumer examples working
- [ ] Tests cover all result types

#### Definition of Done
- Result publishing implemented
- Tests passing
- Examples documented
- Metrics validated

---

### Story 5: Orchestration Deployment Infrastructure 🚀
**Priority**: P1 (High)  
**Points**: 8  
**Assignee**: TBD  
**Dependencies**: Story 1 (tests must pass)

#### Description
Create deployment parity with Event Bus: Docker Compose, Kubernetes manifests, runbooks, and deployment checklists. Enable production deployment of orchestration runtime.

#### Tasks
- [ ] Create `docker-compose.orchestration.yml`
  - Orchestration service
  - Redis (shared with Event Bus)
  - Worker pool configuration
  - Health checks
- [ ] Create Kubernetes manifests
  - `infrastructure/kubernetes/orchestration-deployment.yaml`
  - `infrastructure/kubernetes/orchestration-service.yaml`
  - ConfigMap for worker configuration
  - HPA (Horizontal Pod Autoscaler) for workers
- [ ] Create Dockerfile
  - `infrastructure/docker/orchestration.Dockerfile`
  - Multi-stage build
  - Non-root user
- [ ] Create deployment runbook
  - `docs/runbooks/orchestration-deployment.md` (400+ lines)
  - Pre-deployment checklist
  - Deployment steps
  - Post-deployment validation
  - Rollback procedures
- [ ] Create monitoring setup
  - Prometheus metrics endpoint
  - Grafana dashboard JSON

#### Docker Compose Structure
```yaml
# docker-compose.orchestration.yml
version: '3.8'

services:
  orchestration:
    build:
      context: .
      dockerfile: infrastructure/docker/orchestration.Dockerfile
    environment:
      - REDIS_URL=redis://redis:6379
      - WORKER_POOL_SIZE=10
      - TASK_QUEUE_MAX_SIZE=1000
    depends_on:
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  redis:
    image: redis:7-alpine
    volumes:
      - orchestration_redis:/data
```

#### Acceptance Criteria
- [ ] Docker Compose deploys orchestration locally
- [ ] Kubernetes manifests deploy to test cluster
- [ ] Health checks passing
- [ ] Runbook complete (400+ lines)
- [ ] Deployment tested end-to-end
- [ ] Rollback procedure validated

#### Definition of Done
- All deployment artifacts created
- Successfully deployed to staging
- Runbook peer-reviewed
- Metrics exposed

---

### Story 6: End-to-End Integration Testing 🧪
**Priority**: P1 (High)  
**Points**: 8  
**Assignee**: TBD  
**Dependencies**: Story 3, Story 4 (event integration)

#### Description
Comprehensive integration tests validating Event Bus → Orchestration → Event Bus flow. Test complex scenarios including failures, retries, compensation, and event replay.

#### Tasks
- [ ] Create `tests/integration/test_message_orchestration_bridge.py`
  - Event-triggered task creation
  - Task execution and result publishing
  - Multi-step workflow via events
  - Failure handling and DLQ
  - Compensation saga triggered by events
- [ ] Performance integration tests
  - Load test: 1000 events/sec → tasks
  - Latency: Event → Task → Result Event
  - Throughput with worker pool scaling
- [ ] Chaos engineering tests
  - Worker failure during task execution
  - Redis connection loss
  - Event bus downtime
  - Retry exhaustion scenarios
- [ ] End-to-end workflow examples
  - Multi-agent collaboration workflow
  - Data pipeline orchestration
  - Trial provisioning workflow (using WowTrialManager)

#### Test Scenarios
1. **Happy Path**: Event → Task → Completion Event
2. **Retry Path**: Task fails → Retry → Success → Event
3. **Compensation Path**: Task fails → Saga rollback → Event
4. **DLQ Path**: Max retries exceeded → DLQ → Alert event
5. **Dependency Chain**: Event triggers Task A → Task B → Task C
6. **Worker Scaling**: Auto-scale workers based on queue depth
7. **Event Replay**: Replay events to reprocess failed workflows

#### Performance Targets
- Event-to-result latency: <500ms (p95)
- Throughput: 100 tasks/sec with 10 workers
- Event ordering preserved in task execution
- Zero event loss (with DLQ)

#### Acceptance Criteria
- [ ] 20+ integration test scenarios
- [ ] All tests passing
- [ ] Performance targets met
- [ ] Chaos tests validate resilience
- [ ] Coverage ≥80% for integration paths

#### Definition of Done
- Integration test suite complete
- Performance validated
- Documentation includes test results
- CI/CD runs integration tests

---

### Story 7: Unified Monitoring & Observability 📊
**Priority**: P2 (Medium)  
**Points**: 5  
**Assignee**: TBD  
**Dependencies**: Story 5 (deployment), Story 6 (integration)

#### Description
Create unified monitoring dashboard combining Event Bus and Orchestration metrics. Enable correlated tracing across both systems and implement alerting for critical conditions.

#### Tasks
- [ ] Create Grafana dashboard JSON
  - Event Bus section (throughput, latency, DLQ)
  - Orchestration section (queue depth, workers, task duration)
  - Integration section (event-to-task flow, end-to-end latency)
- [ ] Implement distributed tracing
  - Add trace IDs to events and tasks
  - Correlate event → task → result
  - Integrate with Jaeger/Tempo
- [ ] Create alerting rules
  - Task queue depth >80% capacity
  - Worker utilization >90%
  - Event-to-task latency >1s
  - Task failure rate >5%
  - DLQ growth rate anomaly
- [ ] Create runbook for common issues
  - `docs/runbooks/message-orchestration-troubleshooting.md`
  - Worker pool exhaustion
  - Event bus backpressure
  - Task dependency deadlock

#### Dashboard Sections
```
┌────────────────────────────────────────┐
│     Event Bus + Orchestration          │
├────────────────────────────────────────┤
│ Event Bus Metrics                      │
│ - Events/sec: [GRAPH]                  │
│ - Latency (p95): [GAUGE]               │
│ - DLQ Size: [GRAPH]                    │
├────────────────────────────────────────┤
│ Orchestration Metrics                  │
│ - Task Queue Depth: [GAUGE]            │
│ - Active Workers: [GAUGE]              │
│ - Tasks/min: [GRAPH]                   │
├────────────────────────────────────────┤
│ Integration Metrics                    │
│ - Event→Task Latency: [GRAPH]          │
│ - Task→Event Latency: [GRAPH]          │
│ - End-to-End Latency: [HISTOGRAM]      │
└────────────────────────────────────────┘
```

#### Acceptance Criteria
- [ ] Grafana dashboard deployed
- [ ] All metrics visible in dashboard
- [ ] Tracing correlates events and tasks
- [ ] Alerts configured in Prometheus
- [ ] Runbook complete
- [ ] Alert tested (trigger and resolve)

#### Definition of Done
- Dashboard deployed to staging
- Metrics validated
- Alerts triggered in test
- Documentation complete

---

## Technical Architecture

### Component Integration Diagram
```
┌──────────────────────────────────────────────────────────────┐
│                      Event Bus                               │
│  ┌────────────┐  ┌─────────┐  ┌──────┐  ┌─────────┐        │
│  │ Publishers ├─→│ Schemas ├─→│ DLQ  ├─→│ Metrics │        │
│  └────────────┘  └─────────┘  └──────┘  └─────────┘        │
└────────────┬────────────────────────────────────┬────────────┘
             │                                    │
             │ orchestration.task.trigger         │ task.completed
             │ orchestration.workflow.start       │ task.failed
             ↓                                    ↑
┌────────────────────────────────────────────────────────────────┐
│              Orchestration Event Adapter                       │
│  ┌──────────────────┐         ┌───────────────────┐          │
│  │ Event→Task       │         │ Task→Event        │          │
│  │ Mapper           │         │ Publisher         │          │
│  └────────┬─────────┘         └─────────┬─────────┘          │
└───────────┼───────────────────────────────┼────────────────────┘
            │                               │
            ↓                               ↑
┌────────────────────────────────────────────────────────────────┐
│                  Orchestration Runtime                         │
│  ┌────────────┐  ┌──────────────┐  ┌───────────────┐         │
│  │ Task Queue ├─→│ Dependency   ├─→│ Worker Pool   │         │
│  │            │  │ Resolver     │  │               │         │
│  └────────────┘  └──────────────┘  └───────┬───────┘         │
│                                             │                  │
│  ┌────────────┐  ┌──────────────┐          │                 │
│  │ Retry      │  │ Compensation │          │                 │
│  │ Policy     │  │ (Saga)       │          │                 │
│  └────────────┘  └──────────────┘          │                 │
└─────────────────────────────────────────────┼──────────────────┘
                                              │
                                              ↓
                                    ┌──────────────────┐
                                    │ Metrics &        │
                                    │ Observability    │
                                    └──────────────────┘
```

### Data Flow
1. **Event Triggered Orchestration**
   - Event published to `orchestration.task.trigger`
   - EventAdapter converts event → Task
   - Task added to TaskQueue with priority
   - DependencyResolver builds execution plan
   - WorkerPool executes tasks
   - Results published as events

2. **Task Lifecycle Events**
   - `task.created`: Task added to queue
   - `task.started`: Worker begins execution
   - `task.completed`: Success with result
   - `task.failed`: Error with retry info

3. **Metrics Flow**
   - Both systems expose Prometheus metrics
   - Grafana unified dashboard
   - Distributed tracing correlates events and tasks

---

## Risk Management

### Critical Risks
1. **Syntax Error Impact** (P0)
   - Risk: Blocks all development and testing
   - Mitigation: Story 1 with immediate fix
   - Status: IDENTIFIED

2. **Integration Complexity** (P1)
   - Risk: Event↔Task mapping edge cases
   - Mitigation: Comprehensive test scenarios in Story 6
   - Status: PLANNED

3. **Performance Degradation** (P2)
   - Risk: Event overhead slows orchestration
   - Mitigation: Performance tests with targets
   - Status: MONITORED

### Dependencies
- Redis: Shared by both Event Bus and Orchestration
- Python 3.11+: Required runtime
- Kubernetes: For production deployment

---

## Success Metrics

### Functional Metrics
- ✅ All 131+ orchestration tests passing
- ✅ 20+ integration tests passing
- ✅ 0 import errors
- ✅ Documentation parity achieved (400+ lines)

### Performance Metrics
- 📈 Event→Task latency: <100ms (p95)
- 📈 Task→Event latency: <50ms (p95)
- 📈 End-to-end latency: <500ms (p95)
- 📈 Throughput: 100 tasks/sec (10 workers)

### Operational Metrics
- 🚀 Successful staging deployment
- 🚀 Successful production deployment (dry run)
- 🚀 Runbooks validated
- 🚀 Alerts tested and tuned

---

## Timeline

### Week 1: Foundation (Stories 1-2)
- **Day 1-2**: Fix syntax errors, validate tests (Story 1)
- **Day 3-5**: Write orchestration README and docs (Story 2)

### Week 2: Integration & Deployment (Stories 3-7)
- **Day 1-2**: Event-driven orchestration (Story 3)
- **Day 3**: Result publishing (Story 4)
- **Day 4-5**: Deployment infrastructure (Story 5)
- **Day 6-8**: Integration testing (Story 6)
- **Day 9-10**: Monitoring & observability (Story 7)

---

## Deliverables

### Code
- ✅ Syntax error fix in wowtrialmanager.py
- ✅ waooaw/orchestration/event_adapter.py (300+ lines)
- ✅ waooaw/orchestration/README.md (400+ lines)
- ✅ tests/integration/test_message_orchestration_bridge.py (500+ lines)

### Infrastructure
- ✅ docker-compose.orchestration.yml
- ✅ infrastructure/kubernetes/orchestration-*.yaml
- ✅ infrastructure/docker/orchestration.Dockerfile

### Documentation
- ✅ docs/runbooks/orchestration-deployment.md (400+ lines)
- ✅ docs/runbooks/message-orchestration-troubleshooting.md (300+ lines)
- ✅ docs/platform/orchestration-architecture.md
- ✅ Grafana dashboard JSON

### Validation
- ✅ 131+ orchestration tests passing
- ✅ 20+ integration tests passing
- ✅ Performance benchmarks documented
- ✅ Deployment validated in staging

---

## Definition of Done (Epic)

### Code Quality
- [ ] All 7 stories completed
- [ ] All tests passing (150+ total)
- [ ] Code coverage ≥85%
- [ ] No syntax errors or import failures
- [ ] Peer review approved

### Documentation
- [ ] Orchestration README complete (400+ lines)
- [ ] Deployment runbook complete (400+ lines)
- [ ] Troubleshooting runbook complete (300+ lines)
- [ ] Architecture diagrams updated
- [ ] API reference complete

### Deployment
- [ ] Docker Compose working locally
- [ ] Kubernetes manifests validated
- [ ] Successfully deployed to staging
- [ ] Health checks passing
- [ ] Metrics exposed and working

### Integration
- [ ] Event→Task flow working
- [ ] Task→Event publishing working
- [ ] End-to-end tests passing
- [ ] Performance targets met
- [ ] Distributed tracing operational

### Operational Readiness
- [ ] Monitoring dashboard deployed
- [ ] Alerts configured and tested
- [ ] Runbooks validated
- [ ] Team trained on new components
- [ ] Production deployment plan approved

---

## Next Steps After Epic

1. **v1.0.0 Release Preparation**
   - Tag v1.0.0 with all epics complete
   - Release notes
   - Production deployment

2. **Advanced Orchestration Features** (Epic 3.5)
   - Dynamic workflow generation
   - AI-driven task optimization
   - Predictive scaling

3. **Multi-Tenant Orchestration** (Epic 4.1)
   - Tenant isolation
   - Resource quotas
   - Usage tracking

---

**Epic Owner**: Platform Team  
**Created**: 2025-12-30  
**Last Updated**: 2025-12-30  
**Status**: PLANNING → READY FOR DEVELOPMENT
