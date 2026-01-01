# Story 5.1.9: Real-Time Orchestration Monitoring

**Story ID**: 5.1.9  
**Epic**: Epic 5.1 - Operational Portal  
**Priority**: P0  
**Points**: 21  
**Status**: Ready for Development  
**Dependencies**: Story 5.1.0 (Common Components - WebSocket Manager, Timeline Viewer, Live Metrics, Status Tracking Schema)  
**Risk**: High

---

## User Story

**As a** platform operator  
**I want** to monitor orchestration workflows in real-time with step-by-step execution tracking  
**So that** I can diagnose workflow failures, identify slow steps, and ensure SLA compliance

---

## Problem Statement

### Current State
- No visibility into running workflows
- Cannot see which step is executing or stuck
- Workflow failures discovered after completion (or timeout)
- No real-time progress indicators
- Cannot identify which agent/step is causing delays
- No way to pause/resume or cancel stuck workflows
- Parallel execution paths are black boxes
- Retry logic and compensation flows invisible

### User Pain Points
1. "Workflow failed at step 7 of 15. What happened in steps 1-6?"
2. "Customer trial workflow stuck for 30 minutes. Which step is blocking?"
3. "SLA breach: Expected 5 minutes, took 45 minutes. Where's the delay?"
4. "Workflow retried 3 times. Why? Which step keeps failing?"
5. "Cannot cancel runaway workflow consuming resources"
6. "Parallel branches: Which finished? Which is still running?"
7. "Compensation rollback triggered. What got rolled back?"

### Impact
- **MTTR**: 30-60 minutes to diagnose workflow issues
- **SLA Breaches**: 15% of workflows exceed target time
- **Resource Waste**: Stuck workflows consume compute for hours
- **Manual Intervention**: 10+ times per week killing workflows
- **Customer Impact**: Trial activation delays hurt conversion

---

## Proposed Solution

### Real-Time Orchestration Dashboard

**Orchestration Page** (`orchestration.html`)

Live visualization with:
1. **Active Workflows View**: Currently running workflows with progress
2. **Workflow Detail View**: Step-by-step execution timeline
3. **Workflow Timeline Gantt**: Visual execution sequence with durations
4. **Parallel Branch View**: Concurrent execution paths
5. **Workflow Actions**: Pause, resume, cancel, retry
6. **Historical Analysis**: Completed workflows with performance metrics

### Key Features

#### 1. Workflow List (Real-Time)
- **Active Workflows**: Currently executing (with progress %)
- **Pending Workflows**: Queued waiting for resources
- **Completed Workflows**: Last 100 finished (success/failed)
- **Failed Workflows**: Recent failures with error details
- **Slow Workflows**: Exceeding SLA threshold (> 90% of target time)

**Workflow Metadata:**
- Workflow ID, Type (trial_activation, agent_deployment, data_sync)
- Status (PENDING, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED)
- Start time, Duration, Progress (step 7/15)
- Triggered by (user, scheduled, event)
- Priority (HIGH, NORMAL, LOW)

#### 2. Workflow Detail View
**Step Execution Timeline:**
- Each step shows: Name, Status, Start/End time, Duration, Output
- Status icons: ⏳ Pending, ⚙️ Running, ✅ Completed, ❌ Failed, ⏸️ Paused
- Expand step → View input/output data, logs, errors
- Parallel branches visualized side-by-side
- Retry attempts tracked with iteration numbers
- Compensation steps highlighted in yellow

**Interactive Timeline:**
- Horizontal timeline with steps as blocks
- Color-coded by status (green=success, red=failed, blue=running)
- Hover for details
- Click step → Open detail panel

#### 3. Gantt Chart View
Visual execution flow:
- X-axis: Time (00:00 → 00:45)
- Y-axis: Steps (Step 1 → Step 15)
- Bars show duration of each step
- Overlapping bars = parallel execution
- Red bars = failed/retried steps
- Annotations: Delays, retries, rollbacks

#### 4. Workflow Actions
- **Pause**: Halt execution after current step completes
- **Resume**: Continue from paused state
- **Cancel**: Terminate workflow + trigger compensation
- **Retry**: Re-run failed workflow from start or failed step
- **Clone**: Duplicate workflow with same inputs
- **Export**: Download execution trace (JSON)

#### 5. Performance Analytics
- **SLA Compliance**: % workflows meeting target time
- **Avg Duration by Type**: trial_activation: 4.2 min, agent_deployment: 8.5 min
- **Failure Rate**: 12% overall (breakdown by workflow type)
- **Slowest Steps**: Top 10 steps by avg duration
- **Retry Rate**: Steps that retry most frequently

---

## User Flows

### Flow 1: Monitor Active Workflows
```
1. User opens orchestration.html
2. Active Workflows section shows:
   - trial-wf-12345 (trial_activation) → Step 7/15 (47%) → ⚙️ RUNNING
   - deploy-wf-67890 (agent_deployment) → Step 3/8 (38%) → ⚙️ RUNNING
   - sync-wf-11111 (data_sync) → Step 1/5 (20%) → ⏳ PENDING
3. Real-time updates: Progress bars increment as steps complete
4. User sees trial-wf-12345 stuck at 47% for 5 minutes
5. User clicks workflow for details
```

### Flow 2: Diagnose Stuck Workflow
```
1. User clicks trial-wf-12345
2. Detail view opens with timeline:
   Step 1: ✅ Validate trial request (2s)
   Step 2: ✅ Check agent availability (1s)
   Step 3: ✅ Provision agent resources (15s)
   Step 4: ✅ Configure agent memory (5s)
   Step 5: ✅ Deploy agent container (25s)
   Step 6: ✅ Wait for health check (10s)
   Step 7: ⚙️ Initialize agent context (RUNNING - 5 min) ← STUCK
   Step 8: ⏳ Send welcome email (PENDING)
   ...
3. User clicks Step 7 → Sees:
   - Input: {"agent_id": "WowMemory", "context_size": "large"}
   - Error: None
   - Logs: "Loading 10GB context file... 45% complete"
4. User realizes: Large context file causing delay (not stuck, just slow)
5. User waits → Step completes after 8 minutes → Workflow succeeds
```

### Flow 3: Cancel Runaway Workflow
```
1. User sees deploy-wf-67890 running for 45 minutes (SLA: 10 min)
2. User clicks workflow → Timeline shows:
   Step 1-5: ✅ Completed (normal)
   Step 6: ⚙️ Waiting for external API (40 minutes) ← TIMEOUT
3. User clicks "Cancel Workflow" button
4. Confirmation modal: "Cancel deploy-wf-67890? This will trigger rollback."
5. User confirms
6. Status changes: RUNNING → CANCELLING → CANCELLED
7. Compensation steps execute:
   - Step C1: ✅ Delete deployed container (2s)
   - Step C2: ✅ Release reserved resources (1s)
   - Step C3: ✅ Notify user of cancellation (1s)
8. Workflow marked CANCELLED with reason: "Manual cancellation"
```

### Flow 4: Analyze Failed Workflow
```
1. User navigates to "Failed Workflows" tab
2. Sees trial-wf-99999 failed 10 minutes ago
3. User clicks workflow → Timeline shows:
   Step 1-3: ✅ Completed
   Step 4: ❌ FAILED (Retry 1/3) (2s)
   Step 4: ❌ FAILED (Retry 2/3) (2s)
   Step 4: ❌ FAILED (Retry 3/3) (2s)
   Step 4: ❌ FAILED (Final) - "Database connection refused"
4. User clicks Step 4 → Sees:
   - Input: {"query": "INSERT INTO trials..."}
   - Error: "psycopg2.OperationalError: Connection refused"
   - Retry policy: Exponential backoff (1s, 2s, 4s)
5. User checks diagnostics page → Database is down
6. User restarts database → Clicks "Retry Workflow"
7. Workflow re-runs from Step 4 → Succeeds
```

### Flow 5: Gantt Chart Analysis
```
1. User switches to "Gantt View" tab
2. Chart shows parallel execution:
   00:00 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 00:45
   Step 1  ■■ (2s)
   Step 2     ■ (1s)
   Step 3       ■■■■■■■■ (15s)
   Step 4                ■■ (5s) ← Branch A starts
   Step 5                  ■■■■■■■■■■■ (25s)
   Step 6                              ■■■■ (10s)
   Step 7                ■■ (5s) ← Branch B starts (parallel)
   Step 8                  ■■■■■ (12s)
   Step 9                              ■■■■■■■■■■■■■■■■ (40s) ← BOTTLENECK
3. User sees Step 9 took 40s (expected: 5s)
4. User clicks Step 9 bar → "External API timeout"
5. User notes for future: Increase timeout or make async
```

---

## Technical Implementation

### Backend APIs

**1. Workflow List API**
```
GET /api/platform/orchestration/workflows?status=RUNNING&limit=50

Response:
{
  "workflows": [
    {
      "id": "trial-wf-12345",
      "type": "trial_activation",
      "status": "RUNNING",
      "progress": {
        "current_step": 7,
        "total_steps": 15,
        "percent": 47
      },
      "started_at": "2026-01-01T12:00:00Z",
      "duration_seconds": 120,
      "sla_target_seconds": 300,
      "sla_status": "on_track",
      "triggered_by": "user@example.com",
      "priority": "HIGH",
      "can_pause": true,
      "can_cancel": true
    },
    ...
  ],
  "total": 3,
  "stats": {
    "active": 3,
    "pending": 1,
    "completed_today": 45,
    "failed_today": 7
  }
}
```

**2. Workflow Detail API**
```
GET /api/platform/orchestration/workflows/{workflow_id}

Response:
{
  "id": "trial-wf-12345",
  "type": "trial_activation",
  "status": "RUNNING",
  "definition": {
    "name": "Trial Activation Workflow",
    "version": "1.2.0",
    "steps": 15,
    "sla_target_seconds": 300
  },
  "execution": {
    "started_at": "2026-01-01T12:00:00Z",
    "updated_at": "2026-01-01T12:05:30Z",
    "duration_seconds": 330,
    "current_step": 7,
    "steps": [
      {
        "step_number": 1,
        "name": "validate_trial_request",
        "status": "COMPLETED",
        "started_at": "2026-01-01T12:00:00Z",
        "completed_at": "2026-01-01T12:00:02Z",
        "duration_seconds": 2,
        "input": {"customer_id": "cust-123", "plan": "pro"},
        "output": {"valid": true},
        "logs": ["Validating customer...", "Customer verified"],
        "error": null,
        "retry_count": 0
      },
      {
        "step_number": 7,
        "name": "initialize_agent_context",
        "status": "RUNNING",
        "started_at": "2026-01-01T12:05:00Z",
        "completed_at": null,
        "duration_seconds": 300,
        "input": {"agent_id": "WowMemory", "context_size": "large"},
        "output": null,
        "logs": ["Loading context file...", "Progress: 45%"],
        "error": null,
        "retry_count": 0
      },
      ...
    ],
    "parallel_branches": [
      {
        "branch_id": "branch-a",
        "steps": [4, 5, 6],
        "status": "COMPLETED"
      },
      {
        "branch_id": "branch-b",
        "steps": [7, 8],
        "status": "RUNNING"
      }
    ]
  },
  "metadata": {
    "triggered_by": "user@example.com",
    "trigger_type": "manual",
    "priority": "HIGH",
    "tags": ["trial", "customer-123"]
  }
}
```

**3. Workflow Actions API**
```
POST /api/platform/orchestration/workflows/{workflow_id}/pause
POST /api/platform/orchestration/workflows/{workflow_id}/resume
POST /api/platform/orchestration/workflows/{workflow_id}/cancel
Body: { "reason": "Manual cancellation by operator" }

POST /api/platform/orchestration/workflows/{workflow_id}/retry
Body: { "from_step": 4 }  // Optional: retry from failed step

Response:
{
  "status": "success",
  "workflow_id": "trial-wf-12345",
  "new_status": "PAUSED",
  "message": "Workflow paused after step 7 completes"
}
```

**4. Workflow Analytics API**
```
GET /api/platform/orchestration/analytics?period=24h

Response:
{
  "sla_compliance": {
    "percent": 85,
    "on_track": 38,
    "breached": 7
  },
  "avg_duration_by_type": {
    "trial_activation": 252,
    "agent_deployment": 510,
    "data_sync": 180
  },
  "failure_rate": {
    "overall": 12,
    "by_type": {
      "trial_activation": 8,
      "agent_deployment": 15,
      "data_sync": 5
    }
  },
  "slowest_steps": [
    {
      "step_name": "initialize_agent_context",
      "avg_duration_seconds": 180,
      "occurrences": 45
    },
    ...
  ],
  "retry_rate": {
    "overall": 18,
    "top_steps": [
      {"step_name": "database_insert", "retry_rate": 35},
      {"step_name": "external_api_call", "retry_rate": 28}
    ]
  }
}
```

**5. WebSocket for Real-Time Updates**
```
WS /ws/orchestration

Client subscribes:
{ "action": "subscribe", "workflow_ids": ["trial-wf-12345"] }

Server pushes:
{
  "event": "step_completed",
  "workflow_id": "trial-wf-12345",
  "step_number": 7,
  "step_name": "initialize_agent_context",
  "duration_seconds": 480,
  "status": "COMPLETED"
}

{
  "event": "workflow_status_changed",
  "workflow_id": "trial-wf-12345",
  "old_status": "RUNNING",
  "new_status": "COMPLETED",
  "duration_seconds": 540
}

{
  "event": "sla_warning",
  "workflow_id": "trial-wf-12345",
  "message": "Workflow at 90% of SLA target",
  "current_duration": 270,
  "sla_target": 300
}
```

### Backend Implementation

**Orchestration Service** (`app/services/orchestration_service.py`)
- Query workflow engine (Temporal/Airflow/custom) for active workflows
- Fetch workflow definitions and execution state
- Calculate progress percentage and SLA status
- Support pause/resume/cancel operations
- Track compensation/rollback steps

**Workflow Analytics** (`app/services/workflow_analytics.py`)
- Aggregate workflow metrics from event logs
- Calculate SLA compliance, failure rates, avg durations
- Identify slowest steps and retry patterns
- Generate Gantt chart data structure

**Real-Time Updates** (`app/websocket/orchestration.py`)
- Subscribe to workflow engine events
- Broadcast step completion, status changes to connected clients
- Send SLA warnings when approaching threshold

### Frontend Components

**1. Workflow List View** (`orchestration.html`)
- Tabs: Active, Pending, Completed, Failed
- Table with workflow ID, type, progress, duration, status
- Real-time updates via WebSocket
- Quick actions: View, Pause, Cancel

**2. Workflow Detail Panel**
- Step-by-step timeline with status icons
- Expandable steps showing input/output/logs/errors
- Progress bar at top (7/15 steps, 47%)
- Parallel branch visualization (side-by-side)
- Action buttons: Pause, Resume, Cancel, Retry, Export

**3. Gantt Chart View** (Chart.js or D3.js)
- Horizontal timeline with step bars
- Color-coded by status
- Hover tooltips with step details
- Annotations for retries, delays, rollbacks

**4. Analytics Dashboard**
- SLA compliance gauge (85%)
- Avg duration by type (bar chart)
- Failure rate pie chart
- Slowest steps table
- Retry rate chart

**5. WebSocket Manager** (`js/orchestration-ws.js`)
- Connect to WebSocket endpoint
- Subscribe to active workflows
- Update UI on step completion, status change
- Handle reconnection with backoff

---

## Acceptance Criteria

### Functional Requirements
- [ ] Workflow list shows active, pending, completed, failed workflows
- [ ] Each workflow displays ID, type, status, progress %, duration, SLA status
- [ ] Click workflow → Detail view with step-by-step timeline
- [ ] Each step shows status, start/end time, duration, input/output
- [ ] Real-time updates via WebSocket (step completion, status change)
- [ ] Progress bar updates as steps complete
- [ ] Pause workflow button (when running)
- [ ] Resume workflow button (when paused)
- [ ] Cancel workflow button (trigger compensation)
- [ ] Retry workflow button (from start or failed step)
- [ ] Export workflow trace as JSON
- [ ] Gantt chart visualizes execution timeline
- [ ] Parallel branches shown side-by-side or overlapping
- [ ] SLA warning when workflow exceeds 90% of target time
- [ ] Analytics dashboard with compliance, failure rate, slowest steps
- [ ] Filter workflows by type, status, date range

### Backend Requirements
- [ ] Workflow list API returns paginated results
- [ ] Workflow detail API includes all steps with full metadata
- [ ] Pause API halts execution after current step
- [ ] Resume API continues from paused state
- [ ] Cancel API triggers compensation workflow
- [ ] Retry API re-runs from specified step
- [ ] Analytics API aggregates metrics from last 24h
- [ ] WebSocket broadcasts workflow events in real-time
- [ ] Support multiple workflow engines (Temporal, Airflow, custom)

### Edge Cases
- [ ] Workflow doesn't exist → 404 error
- [ ] Workflow already completed → Cannot pause/resume
- [ ] Workflow compensation fails → Show error + allow manual intervention
- [ ] WebSocket disconnect → Auto-reconnect + sync state
- [ ] Step takes > 1 hour → Show duration in hours
- [ ] Workflow with 100+ steps → Paginate step list
- [ ] Parallel branches > 5 → Collapse/expand branches

### Performance
- [ ] Page load < 2 seconds for 50 active workflows
- [ ] Workflow detail loads < 500ms
- [ ] Gantt chart renders < 1 second for 50 steps
- [ ] WebSocket latency < 100ms per event
- [ ] Support 500+ concurrent workflows without lag

---

## UI/UX Design

### Workflow List View
```
┌─────────────────────────────────────────────────────────────────────┐
│ ⚙️ Orchestration Workflows                                          │
│ [Active (3)] [Pending (1)] [Completed (45)] [Failed (7)]           │
├─────────────────────────────────────────────────────────────────────┤
│ Workflow ID         Type              Progress  Duration  Status    │
├─────────────────────────────────────────────────────────────────────┤
│ trial-wf-12345   trial_activation    ▰▰▰▰▰▱▱▱▱▱  2:00   ⚙️ RUNNING│
│                                       7/15 (47%)                     │
│ deploy-wf-67890  agent_deployment    ▰▰▰▱▱▱▱▱▱▱  8:30   ⚙️ RUNNING│
│                                       3/8 (38%)                      │
│ sync-wf-11111    data_sync           ▰▱▱▱▱▱▱▱▱▱  0:05   ⏳ PENDING│
│                                       1/5 (20%)                      │
├─────────────────────────────────────────────────────────────────────┤
│ Stats: 3 active • 1 pending • 85% SLA compliance today             │
└─────────────────────────────────────────────────────────────────────┘
```

### Workflow Detail View
```
┌─────────────────────────────────────────────────────────────────────┐
│ ⚙️ trial-wf-12345 (trial_activation)            [Pause] [Cancel]   │
│ Progress: ▰▰▰▰▰▱▱▱▱▱ 7/15 (47%) • Duration: 5:30 • SLA: 5:00      │
├─────────────────────────────────────────────────────────────────────┤
│ Step Timeline                                                       │
│ ✅ 1. Validate trial request                            (2s)       │
│ ✅ 2. Check agent availability                          (1s)       │
│ ✅ 3. Provision agent resources                         (15s)      │
│ ✅ 4. Configure agent memory                            (5s)       │
│ ✅ 5. Deploy agent container                            (25s)      │
│ ✅ 6. Wait for health check                             (10s)      │
│ ⚙️ 7. Initialize agent context                 (RUNNING - 5:00)    │
│    └─ Loading 10GB context file... 45% complete                   │
│ ⏳ 8. Send welcome email                                (PENDING)  │
│ ⏳ 9. Configure trial limits                            (PENDING)  │
│ ⏳ 10. Enable agent features                            (PENDING)  │
│ ... (5 more steps)                                                  │
├─────────────────────────────────────────────────────────────────────┤
│ Actions: [🔄 Retry] [📥 Export JSON] [📊 View Gantt]               │
└─────────────────────────────────────────────────────────────────────┘
```

### Gantt Chart View
```
┌─────────────────────────────────────────────────────────────────────┐
│ 📊 Workflow Timeline: trial-wf-12345                               │
├─────────────────────────────────────────────────────────────────────┤
│        00:00    01:00    02:00    03:00    04:00    05:00          │
│ Step 1  ▓▓                                                          │
│ Step 2    ▓                                                         │
│ Step 3      ▓▓▓▓▓▓▓▓                                                │
│ Step 4              ▓▓▓                                             │
│ Step 5                 ▓▓▓▓▓▓▓▓▓▓▓▓▓▓                               │
│ Step 6                                ▓▓▓▓▓                         │
│ Step 7              ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ (still running) │
│ Step 8  (pending)                                                   │
│                                                                     │
│ 🔴 SLA Target: 5:00 • Current: 5:30 • Breach: +30s                │
└─────────────────────────────────────────────────────────────────────┘
```

### Analytics Dashboard
```
┌─────────────────────────────────────────────────────────────────────┐
│ 📈 Workflow Analytics (Last 24h)                                   │
├─────────────────────────────────────────────────────────────────────┤
│ SLA Compliance           Failure Rate           Avg Duration        │
│   ┌────────┐               ┌────────┐          trial_activation    │
│   │   85%  │               │   12%  │            4.2 min            │
│   │ ▓▓▓▓▓▓ │               │ ▓▓     │          agent_deployment    │
│   └────────┘               └────────┘            8.5 min            │
│                                                 data_sync            │
│                                                   3.0 min            │
├─────────────────────────────────────────────────────────────────────┤
│ Slowest Steps (Avg Duration)                                       │
│ 1. initialize_agent_context         3:00                           │
│ 2. deploy_agent_container           1:45                           │
│ 3. external_api_call                1:20                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Technical Tasks

### Phase 1: Backend Core (4 days)
1. Integrate with workflow engine (Temporal/Airflow/custom)
2. Implement workflow list API (`GET /workflows`)
3. Implement workflow detail API (`GET /workflows/{id}`)
4. Implement pause API (`POST /workflows/{id}/pause`)
5. Implement resume API (`POST /workflows/{id}/resume`)
6. Implement cancel API (`POST /workflows/{id}/cancel`)
7. Implement retry API (`POST /workflows/{id}/retry`)
8. Build workflow analytics service
9. Implement analytics API (`GET /analytics`)
10. Write unit tests for all endpoints

### Phase 2: Real-Time Updates (2 days)
11. Implement WebSocket endpoint for orchestration
12. Subscribe to workflow engine events
13. Broadcast step completion events
14. Broadcast status change events
15. Send SLA warning events
16. Handle client subscriptions and unsubscriptions

### Phase 3: Frontend Core (3 days)
17. Create orchestration.html page
18. Implement workflow list view (tabs, table)
19. Implement workflow detail panel
20. Build step timeline component
21. Add expandable step details (input/output/logs)
22. Implement action buttons (pause, resume, cancel, retry)
23. Add real-time WebSocket connection

### Phase 4: Advanced Visualizations (3 days)
24. Build Gantt chart component (Chart.js or D3.js)
25. Implement parallel branch visualization
26. Add step duration bars and annotations
27. Build analytics dashboard
28. Add SLA compliance gauge
29. Add failure rate and duration charts
30. Implement export workflow trace feature (JSON download)

### Phase 5: Testing & Polish (2 days)
31. E2E tests for workflow monitoring flows
32. Test pause/resume/cancel actions
33. Test WebSocket reconnection and sync
34. Load testing with 500 concurrent workflows
35. Performance optimization (caching, pagination)
36. Error handling and edge cases
37. Documentation and API specs

**Total Estimate**: 14 days (1 developer)

---

## Testing Strategy

### Unit Tests
- Workflow status calculations
- SLA breach detection
- Progress percentage calculations
- Parallel branch tracking

### Integration Tests
- Workflow engine integration (Temporal/Airflow)
- WebSocket event broadcasting
- Pause/resume/cancel operations
- Retry logic with step selection

### E2E Tests
- User views active workflows → Sees real-time progress
- User clicks workflow → Detail view with timeline
- User pauses workflow → Execution halts after current step
- User cancels workflow → Compensation runs
- User retries failed workflow → Succeeds

### Performance Tests
- API response time with 500 workflows
- WebSocket scalability (200 concurrent users)
- Gantt chart rendering (100 steps)
- Analytics aggregation speed

---

## Success Metrics

### User Experience
- MTTR for workflow issues: 30min → 5min (83% reduction)
- SLA breach detection: Real-time (vs hours later)
- Manual workflow cancellations: 90% success rate

### Technical
- Workflow list API < 500ms
- Workflow detail API < 300ms
- WebSocket latency < 100ms per event
- Gantt render time < 1 second

### Business
- SLA compliance: 85% → 95% (better visibility = faster fixes)
- Workflow failure recovery: 60% → 90% (retry feature)
- Customer trial activation time: -20% (faster diagnosis)

---

## Dependencies

### Prerequisites
- Workflow engine deployed (Temporal/Airflow) ✅
- WebSocket infrastructure (Story 5.1.5) ✅
- Event bus for workflow events ✅

### Integrations
- Agent status API (Story 5.1.1)
- Queue monitoring (Story 5.1.8)
- Alert system (Story 5.1.6)

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Workflow engine integration complexity | High | Medium | Use adapter pattern, support multiple engines |
| Real-time event lag | Medium | Medium | Cache workflow state, sync on reconnect |
| Large workflow definitions (1000+ steps) | Medium | Low | Paginate steps, lazy load details |
| Compensation failure leaves partial state | High | Low | Manual intervention UI, detailed rollback logs |
| WebSocket scalability | Medium | Medium | Use gateway, rate limiting, subscription limits |

---

## Out of Scope

- ❌ Workflow definition editor (create new workflows)
- ❌ Custom step logic (code editor for steps)
- ❌ Workflow versioning and migration
- ❌ Advanced compensation strategies (custom rollback logic)
- ❌ Workflow scheduling (cron-based triggers)
- ❌ Historical workflow replay (time-travel debugging)

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Code reviewed and merged
- [ ] Unit tests passing (>85% coverage)
- [ ] Integration tests passing
- [ ] E2E tests passing
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] Deployed to staging and tested
- [ ] Product owner approval
- [ ] Deployed to production

---

**This story enables proactive orchestration monitoring, fast failure diagnosis, and SLA compliance tracking.** ⚙️
