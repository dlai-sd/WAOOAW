# Phase 3: Observability (Context, Queue, Orchestration Monitoring)

**Stories**: 5.1.7 + 5.1.8 + 5.1.9  
**Total Points**: 42 (8 + 13 + 21)  
**Duration**: Weeks 5-6 (January 29 - February 11, 2026)  
**Status**: 🚧 READY TO START

---

## Summary Table

| Phase | Story | Description | Points | Status |
|-------|-------|-------------|--------|--------|
| Phase 3 | 5.1.7 | Context-Based Observability | 8 | ⏳ Not Started |
| Phase 3 | 5.1.8 | Real-Time Queue Monitoring | 13 | ⏳ Not Started |
| Phase 3 | 5.1.9 | Orchestration Monitoring | 21 | ⏳ Not Started |

---

## Story 5.1.7: Context-Based Observability (8 Points)

**Goal**: Enable agent-specific filtering across all portal pages

**Duration**: 1 week  
**Team**: 1 developer  
**Dependencies**: Phase 1 (context_selector), Phase 2 (agents_state)

### Features

#### 1. Enhanced Context Selector Integration
- **Global Filter**: Use existing `context_selector_enhanced.py`
- **Persistence**: Store selection in localStorage
- **Multi-Select**: Allow filtering by multiple agents
- **Sync Across Pages**: Context persists across navigation

#### 2. Filtered Views
Apply context filter to existing pages:
- **Dashboard** (`pages/dashboard.py`):
  - Metrics filtered by selected agents
  - Activity feed shows only selected agents
  - Agent status for selected agents only
- **Logs** (new page):
  - Log entries filtered by agent_id
  - Color-coded by agent
  - Real-time streaming via WebSocket
- **Alerts** (new page):
  - Alerts filtered by agent_id
  - Severity-based grouping
  - Acknowledge/resolve actions
- **Metrics** (enhance dashboard):
  - Time-series charts for selected agents
  - Comparative view (agent A vs agent B)
  - Export to CSV

#### 3. Context State Management
```python
# Extend agents_state.py
class ContextState(rx.State):
    selected_agent_ids: List[str] = []
    filter_active: bool = False
    
    def apply_filter(self, data: List[Any]) -> List[Any]:
        """Filter data by selected agents"""
        if not self.filter_active or not self.selected_agent_ids:
            return data
        return [d for d in data if d.agent_id in self.selected_agent_ids]
```

### APIs Required

```python
# Enhance existing APIs
GET /api/platform/metrics?agent_ids=agent-1,agent-2
GET /api/platform/logs?agent_ids=agent-1,agent-2&limit=100
GET /api/platform/alerts?agent_ids=agent-1,agent-2&status=active
GET /api/platform/events?agent_ids=agent-1,agent-2&since=<timestamp>
```

### Database Schema

```sql
-- Add agent_id to existing tables
ALTER TABLE platform_logs ADD COLUMN agent_id VARCHAR(255);
ALTER TABLE platform_alerts ADD COLUMN agent_id VARCHAR(255);
ALTER TABLE platform_metrics ADD COLUMN agent_id VARCHAR(255);

-- Add indexes for filtering
CREATE INDEX idx_logs_agent_id ON platform_logs(agent_id, timestamp DESC);
CREATE INDEX idx_alerts_agent_id ON platform_alerts(agent_id, created_at DESC);
CREATE INDEX idx_metrics_agent_id ON platform_metrics(agent_id, timestamp DESC);
```

### Components to Create

| Component | Description | LOC | Dependencies |
|-----------|-------------|-----|--------------|
| `pages/logs.py` | Log viewer with filtering | 200 | context_selector, websocket |
| `pages/alerts.py` | Alert management | 180 | context_selector, status_badge |
| `components/logs/log_viewer.py` | Log entry component | 120 | timeline_component |
| `components/alerts/alert_card.py` | Alert card with actions | 100 | status_badge |
| `state/context_state.py` | Global context state | 80 | agents_state |

### Success Criteria
- [ ] Context selector persists across pages
- [ ] Dashboard metrics filter by selected agents
- [ ] Logs page shows filtered log entries
- [ ] Alerts page shows filtered alerts
- [ ] Real-time updates respect filter
- [ ] Performance: Filter 1000+ items in <100ms

---

## Story 5.1.8: Real-Time Message Queue Monitoring (13 Points)

**Goal**: Monitor message queues, DLQs, and message flow in real-time

**Duration**: 1-2 weeks  
**Team**: 1 developer  
**Dependencies**: Story 5.1.0 (websocket_manager, metrics_widget), Story 5.1.7 (context filter)

### Features

#### 1. Queue List View
Display all queues with health status:
- **Queue Name**: `agent-tasks`, `event-bus`, `notifications`
- **Status**: 🟢 Healthy | 🟡 Degraded | 🔴 Critical
- **Metrics**:
  - Messages Pending
  - Throughput (msg/sec)
  - Consumer Lag
  - Error Rate
  - Oldest Message Age

#### 2. Dead Letter Queue (DLQ) Panel
Dedicated panel for failed messages:
- **DLQ List**: All failed messages with reason
- **Message Inspector**: View message payload (JSON)
- **Retry Actions**:
  - Retry Single Message
  - Retry All (with confirmation)
  - Delete Message (with audit log)
- **Filters**: By error type, age, queue name

#### 3. Message Flow Visualization
Flow diagram showing message path:
```
Producer → Queue → Consumer
  ↓         ↓         ↓
Metrics   Health   Success/Failure
```
- **Animated Flow**: Messages move through pipeline
- **Bottleneck Detection**: Highlight slow stages
- **Color Coding**: Green (healthy), Yellow (warning), Red (error)

#### 4. Real-Time Metrics Dashboard
WebSocket-powered live metrics:
- **Charts**:
  - Throughput (line chart, last 1 hour)
  - Queue depth (area chart)
  - Error rate (bar chart)
  - Consumer lag (gauge)
- **Auto-Refresh**: 5-second intervals
- **Historical View**: 1h, 6h, 24h, 7d

### APIs Required

```python
# Queue monitoring endpoints
GET  /api/queues                          # List all queues
GET  /api/queues/{queue_id}/metrics       # Queue metrics
GET  /api/queues/{queue_id}/messages      # Recent messages
GET  /api/queues/dlq                      # Dead letter queue
POST /api/queues/dlq/{message_id}/retry   # Retry failed message
DELETE /api/queues/dlq/{message_id}       # Delete message

# WebSocket for real-time updates
WS /ws/queue-metrics                      # Stream metrics
```

### Database Schema

```sql
-- Queue metrics history
CREATE TABLE queue_metrics (
  id UUID PRIMARY KEY,
  queue_name VARCHAR(255) NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  messages_pending INT NOT NULL,
  throughput_per_sec FLOAT,
  consumer_lag INT,
  error_rate FLOAT,
  oldest_message_age_sec INT
);

-- Dead letter queue
CREATE TABLE dead_letter_queue (
  id UUID PRIMARY KEY,
  queue_name VARCHAR(255) NOT NULL,
  message_id VARCHAR(255) NOT NULL,
  payload JSONB NOT NULL,
  error_message TEXT,
  retry_count INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  last_retry_at TIMESTAMP
);

CREATE INDEX idx_queue_metrics_time ON queue_metrics(queue_name, timestamp DESC);
CREATE INDEX idx_dlq_queue ON dead_letter_queue(queue_name, created_at DESC);
```

### Components to Create

| Component | Description | LOC | Dependencies |
|-----------|-------------|-----|--------------|
| `pages/queues.py` | Queue monitoring page | 350 | metrics_widget, websocket |
| `components/queues/queue_card.py` | Queue status card | 150 | status_badge, metrics |
| `components/queues/dlq_panel.py` | DLQ management panel | 200 | timeline_component |
| `components/queues/flow_diagram.py` | Message flow visualization | 180 | SVG animation |
| `state/queue_state.py` | Queue monitoring state | 120 | websocket_manager |
| `services/queue_monitor.py` | Queue metrics service | 200 | Redis, metrics_aggregator |

### Success Criteria
- [ ] Display all queues with real-time metrics
- [ ] DLQ panel shows failed messages
- [ ] Retry failed messages successfully
- [ ] Flow diagram animates message path
- [ ] WebSocket updates every 5 seconds
- [ ] Performance: Handle 100+ queues without lag

---

## Story 5.1.9: Orchestration Workflow Monitoring (21 Points)

**Goal**: Track multi-agent workflows with dependencies, Gantt chart, and actions

**Duration**: 2-3 weeks  
**Team**: 1-2 developers (complex)  
**Dependencies**: Story 5.1.0 (timeline, progress_tracker, websocket), Story 5.1.8 (queue monitoring)

### Features

#### 1. Workflow Timeline View
Chronological list of all workflows:
- **Workflow Card**:
  - Workflow Name
  - Current Status (Running, Completed, Failed, Paused)
  - Progress: 3/5 tasks complete
  - Duration: 2m 34s elapsed
  - Owner: Agent or Operator
- **Filtering**:
  - By status (running, completed, failed)
  - By date range
  - By agent (context filter)
- **Search**: By workflow name or ID

#### 2. Workflow Detail View
Detailed task-level view:
- **Task List** (left panel):
  - Task name, status, duration
  - Dependencies (visual arrows)
  - Retry count (if failed)
- **Gantt Chart** (right panel):
  - Horizontal bars for task execution
  - Dependencies shown as arrows
  - Current time indicator
  - Parallel tasks shown side-by-side
- **Task Inspector** (bottom panel):
  - Task input/output
  - Logs for this task
  - Retry history
  - Error details (if failed)

#### 3. Workflow Actions
Actions on running workflows:
- **Pause**: Pause execution (current task completes)
- **Resume**: Resume paused workflow
- **Cancel**: Stop and cleanup
- **Retry Failed Tasks**: Re-run failed tasks
- **Skip Task**: Skip failed task, continue with next
- **Force Complete**: Mark task as complete (dangerous)

#### 4. Real-Time Updates
WebSocket-powered live tracking:
- **Task Status**: Updates as tasks complete
- **Progress Bar**: Shows overall completion
- **Notifications**: Toast for important events (failure, completion)
- **Auto-Scroll**: Follow active task

#### 5. Workflow History
Historical view of completed workflows:
- **Success Rate**: % of workflows completed successfully
- **Average Duration**: Mean execution time
- **Common Failures**: Top 5 failure reasons
- **Slowest Tasks**: Tasks taking longest

### APIs Required

```python
# Workflow monitoring endpoints
GET  /api/workflows                       # List workflows
GET  /api/workflows/{workflow_id}         # Workflow details
GET  /api/workflows/{workflow_id}/tasks   # Task list with status
POST /api/workflows/{workflow_id}/pause   # Pause workflow
POST /api/workflows/{workflow_id}/resume  # Resume workflow
POST /api/workflows/{workflow_id}/cancel  # Cancel workflow
POST /api/workflows/{workflow_id}/retry   # Retry failed tasks
GET  /api/workflows/metrics/summary       # Historical metrics

# WebSocket for real-time updates
WS /ws/workflow/{workflow_id}             # Stream workflow updates
```

### Database Schema

```sql
-- Workflows table
CREATE TABLE workflows (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  status VARCHAR(50) NOT NULL,  -- running, completed, failed, paused, cancelled
  owner_id VARCHAR(255),
  agent_id VARCHAR(255),
  started_at TIMESTAMP NOT NULL,
  completed_at TIMESTAMP,
  total_tasks INT NOT NULL,
  completed_tasks INT DEFAULT 0,
  failed_tasks INT DEFAULT 0,
  metadata JSONB
);

-- Workflow tasks
CREATE TABLE workflow_tasks (
  id UUID PRIMARY KEY,
  workflow_id UUID REFERENCES workflows(id),
  name VARCHAR(255) NOT NULL,
  status VARCHAR(50) NOT NULL,  -- pending, running, completed, failed, skipped
  depends_on JSONB,  -- Array of task IDs
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  duration_sec INT,
  retry_count INT DEFAULT 0,
  input_data JSONB,
  output_data JSONB,
  error_message TEXT
);

-- Indexes
CREATE INDEX idx_workflows_status ON workflows(status, started_at DESC);
CREATE INDEX idx_workflow_tasks_workflow ON workflow_tasks(workflow_id);
CREATE INDEX idx_workflows_agent ON workflows(agent_id, started_at DESC);
```

### Components to Create

| Component | Description | LOC | Dependencies |
|-----------|-------------|-----|--------------|
| `pages/workflows.py` | Workflow monitoring page | 400 | timeline, progress_tracker |
| `components/workflows/workflow_card.py` | Workflow summary card | 150 | status_badge, progress |
| `components/workflows/gantt_chart.py` | Gantt chart visualization | 300 | D3.js or Recharts |
| `components/workflows/task_inspector.py` | Task detail view | 200 | timeline, logs |
| `components/workflows/workflow_actions.py` | Action toolbar | 100 | buttons, modals |
| `state/workflow_state.py` | Workflow monitoring state | 180 | websocket_manager |
| `services/workflow_monitor.py` | Workflow tracking service | 250 | orchestration system |

### Success Criteria
- [ ] Display all workflows with status
- [ ] Gantt chart shows task timeline
- [ ] Pause/resume/cancel actions work
- [ ] Task inspector shows task details
- [ ] Real-time updates via WebSocket
- [ ] Historical metrics dashboard
- [ ] Performance: Render 100+ task workflow in <2s

---

## Phase 3 Milestones

### Milestone 3.1: Context Observability (End of Week 5)
- ✅ Context filter integrated across all pages
- ✅ Logs page operational
- ✅ Alerts page operational
- ✅ Performance validated (1000+ items filtered)
- **Demo**: Filter dashboard/logs/alerts by agent

### Milestone 3.2: Queue Monitoring (Mid Week 6)
- ✅ Queue list view with real-time metrics
- ✅ DLQ panel with retry functionality
- ✅ Flow diagram visualization
- ✅ WebSocket updates working
- **Demo**: Monitor queue, retry DLQ message

### Milestone 3.3: Phase 3 Complete (End of Week 6)
- ✅ Workflow timeline operational
- ✅ Gantt chart rendering correctly
- ✅ Workflow actions (pause/resume/cancel) working
- ✅ Real-time workflow tracking via WebSocket
- ✅ Historical metrics dashboard
- **Demo**: Full observability stack walkthrough

---

## Technical Implementation Plan

### Week 5: Story 5.1.7 (Context Observability)
**Days 1-2**: Context state management
- Extend `context_selector_enhanced.py`
- Create `state/context_state.py`
- Implement localStorage persistence

**Days 3-4**: Logs page
- Create `pages/logs.py`
- Implement log viewer component
- Add real-time streaming

**Day 5**: Alerts page
- Create `pages/alerts.py`
- Implement alert cards
- Add acknowledge/resolve actions

**Testing**: Filter 1000+ items, verify persistence

---

### Week 6 Part 1: Story 5.1.8 (Queue Monitoring)
**Days 1-2**: Queue list view
- Create `pages/queues.py`
- Implement queue cards
- Add real-time metrics

**Days 3-4**: DLQ panel
- Create DLQ management component
- Implement retry functionality
- Add message inspector

**Day 5**: Flow diagram
- Create flow visualization
- Add animations
- Integrate with WebSocket

**Testing**: Monitor 100+ queues, retry DLQ messages

---

### Week 6 Part 2: Story 5.1.9 (Orchestration Monitoring)
**Days 1-3**: Workflow timeline
- Create `pages/workflows.py`
- Implement workflow cards
- Add filtering and search

**Days 4-6**: Gantt chart & detail view
- Implement Gantt chart component
- Create task inspector
- Add dependency visualization

**Days 7-8**: Workflow actions
- Implement pause/resume/cancel
- Add retry failed tasks
- Create action confirmation modals

**Days 9-10**: Testing & Polish
- Integration testing
- Performance optimization
- Documentation

---

## Testing Strategy

### Unit Tests
- Context filter logic
- Queue metrics calculations
- Workflow status transitions
- Action handlers

### Integration Tests
- Context filter across pages
- Queue DLQ retry flow
- Workflow pause/resume/cancel
- WebSocket real-time updates

### E2E Tests
- Filter dashboard by agent
- Monitor queue, retry DLQ message
- Track workflow from start to completion
- Pause workflow, resume, verify state

### Performance Tests
- Filter 1000+ log entries (<100ms)
- Render 100+ queues (<1s)
- Render 100+ task Gantt chart (<2s)
- WebSocket updates for 50+ workflows

---

## Dependencies

**From Phase 1 (Story 5.1.0):**
- ✅ context_selector.py
- ✅ websocket_manager.py
- ✅ metrics_widget.py
- ✅ timeline_component.py
- ✅ progress_tracker.py

**From Phase 2 (Epic 2.1 & 2.2):**
- ✅ agents_state.py (agent list for context filter)
- ✅ agent_state_machine.py (state logic)
- ✅ Navigation header (for context selector placement)

**External Systems:**
- Backend APIs (FastAPI)
- PostgreSQL (metrics, logs, workflows)
- Redis (queue monitoring, WebSocket)
- Orchestration system (workflow tracking)

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gantt chart complexity | High | Use proven library (D3.js/Recharts), start simple |
| Real-time performance | Medium | Throttle WebSocket updates, use virtual scrolling |
| Context filter bugs | Medium | Comprehensive unit tests, E2E validation |
| DLQ retry failures | Low | Transaction logging, rollback on error |

---

## Success Metrics

- **Context Filter**: 100% of pages support filtering
- **Queue Monitoring**: DLQ retry success rate >95%
- **Workflow Tracking**: Real-time updates <5s latency
- **Performance**: All pages load <2s, filter <100ms
- **Test Coverage**: >85% for all new code
- **Zero Critical Bugs**: In production for 1 week

---

## Related Documents
- [Platform Portal Master Plan](../docs/platform/PLATFORM_PORTAL_MASTER_PLAN.md)
- [Story 5.1.7](../docs/platform/stories/STORY_5.1.7_CONTEXT_BASED_OBSERVABILITY.md)
- [Story 5.1.8](../docs/platform/stories/STORY_5.1.8_REALTIME_MESSAGE_QUEUE_MONITORING.md)
- [Story 5.1.9](../docs/platform/stories/STORY_5.1.9_ORCHESTRATION_MONITORING.md)
- [Phase 2 Issue](.github/ISSUE_PHASE_2_CORE_PORTAL.md)

---

**Last Updated:** January 1, 2026  
**Status:** Ready to start  
**Next Sprint:** Week 5 (January 29, 2026)
