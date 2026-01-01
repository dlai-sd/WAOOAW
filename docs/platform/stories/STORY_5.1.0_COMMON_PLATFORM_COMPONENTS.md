# Story 5.1.0: Common Platform Components (Shared Infrastructure)

**Story ID**: 5.1.0  
**Epic**: Epic 5.1 - Operational Portal  
**Priority**: P0 (Foundation)  
**Points**: 21  
**Status**: Ready for Development  
**Dependencies**: None (foundation story)  
**Risk**: Low

---

## User Story

**As a** platform developer  
**I want** reusable frontend and backend components for common operational patterns  
**So that** I can build consistent, maintainable features faster across all portal pages

---

## Problem Statement

### Current State
- Each story implements similar patterns from scratch
- Real-time monitoring duplicated across pages
- Status indicators inconsistent across UI
- WebSocket connection logic repeated
- No shared component library

### Identified Patterns (from Stories 5.1.7-5.1.12)
**Frontend:** 6 components used 2-4 times each
**Backend:** 5 services used 2-4 times each
**Schemas:** 1 status tracking pattern used 3 times

---

## Proposed Solution

### Shared Component Library

Build foundation components used across all operational stories (5.1.7-5.1.12).

---

## Components to Build

### **Frontend Components**

#### 1. WebSocket Connection Manager (`js/websocket-manager.js`)
**Purpose:** Centralized WebSocket lifecycle management

**Features:**
- Connection establishment with auth
- Auto-reconnection with exponential backoff
- Subscription management (subscribe/unsubscribe to topics)
- Heartbeat/keepalive
- Error handling and retry logic
- Event listener registration

**API:**
```javascript
const ws = new WebSocketManager('/ws/platform');
await ws.connect();
ws.subscribe('queues', (data) => console.log(data));
ws.unsubscribe('queues');
await ws.disconnect();
```

**Used in:**
- Story 5.1.8 (Queue Monitoring)
- Story 5.1.9 (Orchestration Monitoring)
- Story 5.1.11 (Agent Servicing)

---

#### 2. Live Metrics Widget (`components/live-metrics-widget.js`)
**Purpose:** Auto-refreshing metric cards with sparklines

**Features:**
- Real-time number display with formatting
- Trend indicators (↑↓→)
- Mini sparkline charts
- Configurable refresh interval
- Status color coding

**Usage:**
```html
<live-metrics-widget 
  metric-name="Queue Pending"
  value="250"
  trend="up"
  status="warning"
  refresh-interval="2000">
</live-metrics-widget>
```

**Used in:**
- Story 5.1.8 (Queue metrics)
- Story 5.1.9 (Workflow metrics)
- Story 5.1.12 (Customer health score)

---

#### 3. Status Badge Component (`components/status-badge.js`)
**Purpose:** Consistent status indicators across all pages

**Variants:**
- 🟢 Healthy / Success / Online / Active
- 🟡 Degraded / Warning / Working / Pending
- 🔴 Critical / Failed / Offline / Error
- ⚫ Unknown / Stopped / Cancelled

**Usage:**
```html
<status-badge status="healthy" label="Online"></status-badge>
<status-badge status="degraded" label="Slow"></status-badge>
```

**Used in:** All stories (5.1.7-5.1.12)

---

#### 4. Event Timeline Viewer (`components/timeline-viewer.js`)
**Purpose:** Chronological event display with filtering

**Features:**
- Expandable timeline entries
- Time-based grouping (today, yesterday, last week)
- Status icon per entry
- Filter by type, status, date range
- Infinite scroll / pagination
- Export timeline (JSON, CSV)

**Usage:**
```html
<timeline-viewer 
  data-source="/api/platform/timeline"
  filters='["type", "status", "date"]'
  expandable="true">
</timeline-viewer>
```

**Used in:**
- Story 5.1.9 (Orchestration step timeline)
- Story 5.1.12 (Help Desk interaction timeline)

---

#### 5. Progress Tracker Component (`components/progress-tracker.js`)
**Purpose:** Multi-stage progress visualization

**Features:**
- Stage list with status (pending, in-progress, completed, failed)
- Progress bar (percentage)
- Estimated time remaining
- Stage duration tracking
- Expandable stage details

**Usage:**
```html
<progress-tracker 
  stages='[{"name": "Deploy", "status": "completed"}, ...]'
  current-stage="3"
  progress-percent="60">
</progress-tracker>
```

**Used in:**
- Story 5.1.10 (Agent Factory deployment)
- Story 5.1.11 (Agent Servicing upgrade)

---

#### 6. Context Selector (`components/context-selector.js`)
**Purpose:** Global filtering context with persistence

**Features:**
- Dropdown with search
- LocalStorage persistence
- Cross-page context sync (storage events)
- Context change notifications (pub/sub)
- "Clear filter" button

**Usage:**
```javascript
const selector = new ContextSelector('agent_context');
selector.on('change', (context) => {
  // Reload page data with context filter
});
selector.set('WowMemory');
const current = selector.get(); // "WowMemory"
selector.clear();
```

**Used in:**
- Story 5.1.7 (Context Observability)
- Story 5.1.12 (Help Desk customer context)

---

### **Backend Services**

#### 7. WebSocket Event Broadcaster (`app/websocket/broadcaster.py`)
**Purpose:** Centralized real-time event distribution

**Features:**
- Client subscription management
- Topic-based routing
- Rate limiting per client
- Event buffering during disconnect
- Broadcast to all or specific clients

**API:**
```python
from app.websocket.broadcaster import Broadcaster

broadcaster = Broadcaster()
await broadcaster.connect(websocket, client_id)
await broadcaster.subscribe(client_id, "queues")
await broadcaster.broadcast("queues", {"queue": "agent.commands", "pending": 15})
await broadcaster.disconnect(client_id)
```

**Used in:**
- Story 5.1.8 (Queue updates)
- Story 5.1.9 (Orchestration updates)
- Story 5.1.11 (Agent upgrade progress)

---

#### 8. Metrics Aggregation Service (`app/services/metrics_aggregator.py`)
**Purpose:** Time-series data aggregation with caching

**Features:**
- Aggregate metrics over time windows (1m, 5m, 1h, 1d)
- Caching with TTL
- Threshold-based alerting
- Rate calculation (per second, per minute)
- Percentile calculations (p50, p95, p99)

**API:**
```python
from app.services.metrics_aggregator import MetricsAggregator

agg = MetricsAggregator()
metrics = await agg.get_metrics(
    metric_name="queue_pending",
    time_window="5m",
    aggregation="avg"
)
```

**Used in:**
- Story 5.1.8 (Queue metrics)
- Story 5.1.9 (Workflow metrics)
- Story 5.1.12 (Customer health score)

---

#### 9. Health Check Service (`app/services/health_checker.py`)
**Purpose:** Component health monitoring

**Features:**
- Pluggable health check providers
- Component status aggregation
- Degradation detection (threshold-based)
- Health history tracking
- Alerting integration

**API:**
```python
from app.services.health_checker import HealthChecker

checker = HealthChecker()
checker.register("database", check_database_health)
health = await checker.check_all()
# Returns: {component: status, overall_status: "healthy"}
```

**Used in:**
- Story 5.1.8 (Queue health)
- Story 5.1.9 (Workflow engine health)
- Story 5.1.10 (Agent Factory sandbox)
- Story 5.1.11 (Agent Servicing post-deploy)

---

#### 10. Audit Logger Service (`app/services/audit_logger.py`)
**Purpose:** Structured audit trail logging

**Features:**
- Before/after snapshots
- Operator tracking (who)
- Timestamp tracking (when)
- Reason/justification field
- Query interface (filter, search)
- Export to CSV/JSON

**API:**
```python
from app.services.audit_logger import AuditLogger

logger = AuditLogger()
await logger.log_event(
    event_type="agent_upgrade",
    resource_id="WowMemory",
    operator="admin@waooaw.com",
    before_state={"version": "0.4.2"},
    after_state={"version": "0.4.3"},
    reason="Bug fix for memory leak"
)
```

**Used in:**
- Story 5.1.10 (Agent creation logs)
- Story 5.1.11 (Agent upgrade/rollback logs)
- Story 5.1.12 (Help Desk ticket actions)

---

#### 11. Provisioning Engine (`app/services/provisioning_engine.py`)
**Purpose:** Infrastructure provisioning orchestration

**Features:**
- Docker container lifecycle management
- Message queue creation
- Storage allocation
- Health check execution
- Idempotent operations (safe retries)
- Rollback on failure

**API:**
```python
from app.services.provisioning_engine import ProvisioningEngine

engine = ProvisioningEngine()
result = await engine.provision_agent(
    agent_id="WowCustomerContext",
    config={...}
)
# Returns: {status, container_id, queues, storage}
```

**Used in:**
- Story 5.1.10 (Agent Factory - create new agents)
- Story 5.1.11 (Agent Servicing - deploy new versions)

---

### **Shared Data Models**

#### 12. Status Tracking Schema (`app/schemas/status_tracking.py`)
**Purpose:** Consistent multi-stage operation tracking

**Schema:**
```python
class StageStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class Stage(BaseModel):
    stage: str
    status: StageStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    error: Optional[str]

class StatusTracking(BaseModel):
    status: StageStatus
    stages: List[Stage]
    current_stage: Optional[str]
    progress_percent: int
    estimated_duration_seconds: Optional[int]
```

**Used in:**
- Story 5.1.9 (Orchestration workflow stages)
- Story 5.1.10 (Agent Factory deployment stages)
- Story 5.1.11 (Agent Servicing upgrade stages)

---

## Technical Implementation

### Phase 1: Frontend Foundation (5 days)
1. Setup shared component directory structure
2. Build WebSocket Manager with reconnection logic
3. Build Status Badge component (Web Component)
4. Build Context Selector with localStorage
5. Add component documentation and examples
6. Write unit tests for each component

### Phase 2: Frontend Advanced (4 days)
7. Build Live Metrics Widget with sparklines
8. Build Event Timeline Viewer with filtering
9. Build Progress Tracker with stages
10. Integrate Chart.js or lightweight charting library
11. Add component integration tests

### Phase 3: Backend Services (6 days)
12. Build WebSocket Broadcaster service
13. Build Metrics Aggregation service with caching
14. Build Health Check service with providers
15. Build Audit Logger service
16. Build Provisioning Engine (Docker integration)
17. Write unit tests for all services

### Phase 4: Data Models & Integration (3 days)
18. Define Status Tracking schema
19. Create shared API response models
20. Build component registry/catalog
21. Integration tests for cross-component usage
22. Performance testing and optimization

### Phase 5: Documentation & Examples (3 days)
23. Component usage documentation
24. API documentation (OpenAPI)
25. Example implementations for each component
26. Migration guide for existing code
27. Developer onboarding guide

**Total Estimate:** 21 days (1 developer)

---

## Acceptance Criteria

### Functional Requirements
- [ ] 6 frontend components built and tested
- [ ] 5 backend services implemented
- [ ] 1 shared schema defined
- [ ] All components have unit tests (>85% coverage)
- [ ] All components have usage documentation
- [ ] Example implementations provided
- [ ] Integration tests passing

### Code Quality
- [ ] Components follow design system
- [ ] Services follow FastAPI best practices
- [ ] TypeScript types for frontend (if applicable)
- [ ] Pydantic models for backend
- [ ] Error handling in all components
- [ ] Logging for debugging

### Documentation
- [ ] Component catalog with screenshots
- [ ] API documentation (JSDoc, Pydantic)
- [ ] Usage examples for each component
- [ ] Migration guide for refactoring existing code

---

## Success Metrics

### Developer Experience
- Component reuse: Used in 3+ stories each
- Development speed: 30% faster feature implementation
- Code consistency: Same patterns across all pages
- Maintainability: Single source of truth for common logic

### Technical
- Code duplication: Reduced by 60%
- Bundle size: < 50KB for shared JS components
- Performance: No measurable overhead from abstraction
- Test coverage: 85%+ for all shared code

---

## Dependencies

### Prerequisites
- FastAPI backend ✅
- Docker environment ✅
- Redis/RabbitMQ for queues ✅
- PostgreSQL for data ✅

### Integrations
- None (foundation layer)

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Over-abstraction slows development | Medium | Low | Keep components simple, allow overrides |
| Breaking changes impact all stories | High | Medium | Semantic versioning, deprecation warnings |
| Performance overhead from layers | Low | Low | Benchmark, optimize hot paths |
| Learning curve for team | Medium | Medium | Good docs, examples, pair programming |

---

## Out of Scope

- ❌ UI framework migration (React, Vue, etc.) - staying with vanilla JS/Web Components
- ❌ Component visual design system (colors, fonts) - use existing CSS
- ❌ Automated component testing (e2e) - manual for now
- ❌ Component versioning system - simple semver

---

## Usage in Other Stories

**This story is a dependency for:**
- Story 5.1.7 (Context Observability) - Uses: Context Selector, Status Badge
- Story 5.1.8 (Queue Monitoring) - Uses: WebSocket Manager, Live Metrics, Status Badge, Health Checker
- Story 5.1.9 (Orchestration) - Uses: WebSocket Manager, Timeline Viewer, Live Metrics, Status Tracking Schema
- Story 5.1.10 (Agent Factory) - Uses: Progress Tracker, Status Badge, Provisioning Engine, Audit Logger, Health Checker
- Story 5.1.11 (Agent Servicing) - Uses: WebSocket Manager, Progress Tracker, Status Tracking Schema, Provisioning Engine, Audit Logger
- Story 5.1.12 (Help Desk) - Uses: Context Selector, Timeline Viewer, Live Metrics, Metrics Aggregator

---

## Definition of Done

- [ ] All 12 components/services implemented
- [ ] Code reviewed and merged
- [ ] Unit tests passing (>85% coverage)
- [ ] Integration tests passing
- [ ] Documentation complete
- [ ] Examples provided
- [ ] Component catalog published
- [ ] Deployed to staging
- [ ] Other stories can import and use components
- [ ] Product owner approval

---

**This story provides the foundation for consistent, maintainable operational portal features.** 🧩
