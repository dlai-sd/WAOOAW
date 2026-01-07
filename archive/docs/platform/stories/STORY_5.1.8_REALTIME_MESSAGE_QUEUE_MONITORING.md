# Story 5.1.8: Real-Time Message Queue Monitoring

**Story ID**: 5.1.8  
**Epic**: Epic 5.1 - Operational Portal  
**Priority**: P0  
**Points**: 13  
**Status**: Ready for Development  
**Dependencies**: Story 5.1.0 (Common Components - WebSocket Manager, Live Metrics, Status Badge, Health Checker)  
**Risk**: Medium

---

## User Story

**As a** platform operator  
**I want** to monitor message queues in real-time with live metrics and flow visualization  
**So that** I can detect bottlenecks, dead letters, and performance issues before they impact agents

---

## Problem Statement

### Current State
- No visibility into message queue health
- Cannot see pending messages, processing rates, or consumer lag
- Dead letter queues (DLQ) fill up silently
- Message routing errors discovered hours later in logs
- No real-time alerts when queues back up
- Cannot identify which agent is causing bottlenecks

### User Pain Points
1. "Agent stopped processing, but I don't know if it's stuck or starved"
2. "Messages disappeared. Are they in DLQ? How many?"
3. "Queue has 10K messages. Is that normal or a problem?"
4. "Which agent is slow? Can't tell from queue alone"
5. "Need to SSH into Redis to run commands manually"
6. "Alert fires after queue backed up for 30 minutes"

### Impact
- **MTTR**: 20-40 minutes to diagnose queue issues
- **Data Loss**: Messages dropped without notification
- **Cascading Failures**: One slow agent blocks others
- **Manual Intervention**: 5+ times per week checking queues

---

## Proposed Solution

### Real-Time Queue Dashboard

**Queue Monitoring Page** (`queues.html`)

Live visualization with:
1. **Queue List View**: All queues with key metrics
2. **Queue Detail View**: Deep dive into selected queue
3. **Message Flow Diagram**: Visual routing between agents
4. **Dead Letter Queue Panel**: Trapped messages with retry options
5. **Real-Time Alerts**: Threshold breaches and anomalies

### Key Features

#### 1. Queue Metrics (Real-Time)
- **Pending Messages**: Count in queue waiting to be processed
- **Processing Rate**: Messages/second throughput
- **Consumer Count**: Active workers consuming from queue
- **Consumer Lag**: Time between message arrival and processing
- **Error Rate**: Failed messages per minute
- **DLQ Count**: Messages in dead letter queue
- **Avg Processing Time**: Time to handle one message
- **Queue Age**: Oldest message timestamp

#### 2. Queue Health Status
- 🟢 **Healthy**: Lag < 5s, error rate < 1%
- 🟡 **Degraded**: Lag 5-30s or error rate 1-5%
- 🔴 **Critical**: Lag > 30s or error rate > 5%
- ⚫ **Stalled**: No messages processed in 5 minutes

#### 3. Message Inspector
- View message payload (JSON formatted)
- Message metadata (ID, timestamp, retry count)
- Routing headers (source, destination, priority)
- Processing history (attempts, errors)
- Manual actions (retry, move to DLQ, delete)

#### 4. Flow Visualization
- Interactive diagram showing message paths
- Nodes: Agents, queues, routers
- Edges: Message flow with throughput labels
- Animated pulses showing active flows
- Bottleneck highlighting (red nodes/edges)

---

## User Flows

### Flow 1: Dashboard Overview
```
1. User opens queues.html
2. Page shows 8 queues in list view:
   - agent.commands (15 pending, 🟢 Healthy)
   - agent.events (0 pending, 🟢 Healthy)
   - orchestration.tasks (250 pending, 🟡 Degraded)
   - workflow.results (5 pending, 🟢 Healthy)
   - agent.logs (1200 pending, 🔴 Critical)
   - dlq.agent.commands (3 messages)
   - dlq.orchestration.tasks (0 messages)
   - dlq.agent.logs (12 messages)
3. Real-time updates: Numbers change as messages flow
4. User sees red indicator on agent.logs queue
5. User clicks for details
```

### Flow 2: Investigate Bottleneck
```
1. User clicks "orchestration.tasks (250 pending, 🟡 Degraded)"
2. Detail view opens:
   - Graph: Pending messages spiking from 10 → 250 in 5 min
   - Consumers: 2 active (WowOrchestrator, WowWorkflow)
   - Processing rate: 0.5 msg/s (expected: 5 msg/s)
   - Consumer lag: 15 seconds
   - Error rate: 2%
3. User sees "WowOrchestrator: Last processed 3 min ago"
4. User clicks "View Consumer Health" → Navigates to agent context
5. Agent shows: RUNNING but CPU throttled
6. User restarts agent → Queue drains in 2 minutes
```

### Flow 3: Handle Dead Letter Messages
```
1. User sees "dlq.agent.logs (12 messages)" in red
2. User clicks DLQ panel
3. Panel shows 12 messages with errors:
   - "Invalid JSON schema" × 8
   - "Missing agent_id field" × 3
   - "Timeout after 30s" × 1
4. User selects first message → Inspector shows payload
5. User sees malformed JSON from WowMemory
6. User clicks "Retry with Fix" → Edits JSON → Resubmits
7. Message moves from DLQ to agent.logs queue
8. Success! DLQ count: 11
```

### Flow 4: Real-Time Alert
```
1. User on agents.html page
2. Toast notification: "🔴 Queue Critical: agent.logs has 1200 pending"
3. User clicks notification
4. Page navigates to queues.html with agent.logs selected
5. Detail view shows:
   - Consumer: WowLogger (STOPPED)
   - Messages piling up at 10/second
6. User clicks "Quick Action: Restart Consumer"
7. WowLogger restarts → Queue drains → Status: 🟢 Healthy
```

### Flow 5: Flow Visualization
```
1. User clicks "Flow Diagram" tab
2. Interactive graph appears:
   [WowMemory] --5 msg/s--> [agent.logs] --5 msg/s--> [WowLogger]
   [WowOrchestrator] --0.5 msg/s--> [orchestration.tasks] --0.5 msg/s--> [WowWorkflow]
                                                                           ↓ 2 msg/s
                                                                      [workflow.results]
3. Red edge highlights slow flow: orchestration.tasks → WowWorkflow
4. User clicks red edge → Shows bottleneck details
5. User clicks WowWorkflow node → Context switches to agent
```

---

## Technical Implementation

### Backend APIs

**1. Queue List API**
```
GET /api/platform/queues

Response:
{
  "queues": [
    {
      "name": "agent.commands",
      "type": "direct",
      "pending_messages": 15,
      "processing_rate": 12.5,
      "consumer_count": 3,
      "consumer_lag_seconds": 2.1,
      "error_rate_percent": 0.5,
      "dlq_count": 0,
      "avg_processing_time_ms": 85,
      "oldest_message_age_seconds": 5,
      "status": "healthy",
      "consumers": ["WowMemory", "WowOrchestrator", "WowCache"]
    },
    ...
  ],
  "total_pending": 1485,
  "total_dlq": 15,
  "overall_status": "degraded"
}
```

**2. Queue Detail API**
```
GET /api/platform/queues/{queue_name}

Response:
{
  "name": "orchestration.tasks",
  "type": "topic",
  "pending_messages": 250,
  "processing_rate": 0.5,
  "consumers": [
    {
      "agent_id": "WowOrchestrator",
      "status": "running",
      "last_processed_at": "2026-01-01T12:00:00Z",
      "processing_rate": 0.3,
      "error_count": 5
    },
    {
      "agent_id": "WowWorkflow",
      "status": "running",
      "last_processed_at": "2026-01-01T12:04:30Z",
      "processing_rate": 0.2,
      "error_count": 0
    }
  ],
  "metrics_history": {
    "timestamps": ["12:00:00", "12:01:00", ...],
    "pending": [10, 25, 50, 100, 150, 250],
    "processing_rate": [5, 4.5, 3, 1.5, 0.8, 0.5]
  },
  "recent_errors": [
    {
      "timestamp": "2026-01-01T12:03:15Z",
      "consumer": "WowOrchestrator",
      "error": "Timeout processing message",
      "message_id": "msg-12345"
    }
  ]
}
```

**3. DLQ Messages API**
```
GET /api/platform/queues/{queue_name}/dlq

Response:
{
  "queue": "dlq.agent.logs",
  "count": 12,
  "messages": [
    {
      "id": "msg-67890",
      "original_queue": "agent.logs",
      "payload": {"level": "error", "message": "Invalid data"},
      "error": "JSON schema validation failed",
      "retry_count": 3,
      "timestamp": "2026-01-01T11:45:00Z",
      "source_agent": "WowMemory",
      "can_retry": true
    },
    ...
  ]
}

POST /api/platform/queues/{queue_name}/dlq/{message_id}/retry
Body: { "payload": {...}, "target_queue": "agent.logs" }

DELETE /api/platform/queues/{queue_name}/dlq/{message_id}
```

**4. Message Flow API**
```
GET /api/platform/queues/flow

Response:
{
  "nodes": [
    {"id": "WowMemory", "type": "agent", "status": "running"},
    {"id": "agent.logs", "type": "queue", "pending": 5},
    {"id": "WowLogger", "type": "agent", "status": "running"}
  ],
  "edges": [
    {
      "source": "WowMemory",
      "target": "agent.logs",
      "throughput": 5.2,
      "latency_ms": 12
    },
    {
      "source": "agent.logs",
      "target": "WowLogger",
      "throughput": 5.1,
      "latency_ms": 85
    }
  ],
  "bottlenecks": [
    {
      "queue": "orchestration.tasks",
      "reason": "consumer_slow",
      "impact": "250 messages pending"
    }
  ]
}
```

**5. WebSocket for Real-Time Updates**
```
WS /ws/queues

Client subscribes:
{ "action": "subscribe", "queues": ["agent.logs", "orchestration.tasks"] }

Server pushes:
{
  "event": "queue_update",
  "queue": "agent.logs",
  "data": {
    "pending_messages": 1205,
    "processing_rate": 0.1,
    "status": "critical"
  }
}

{
  "event": "dlq_message",
  "queue": "dlq.agent.logs",
  "message_id": "msg-99999",
  "error": "Timeout"
}
```

### Backend Implementation

**Queue Metrics Service** (`app/services/queue_metrics.py`)
- Connects to Redis/RabbitMQ to fetch queue stats
- Calculates derived metrics (lag, error rate, health status)
- Caches metrics for 2 seconds to reduce load
- Exposes WebSocket broadcast for real-time updates

**Message Inspector** (`app/services/message_inspector.py`)
- Fetch message by ID from queue or DLQ
- Parse payload and metadata
- Validate schema and routing headers
- Support manual retry/delete operations

**Flow Analyzer** (`app/services/flow_analyzer.py`)
- Build graph from queue topology
- Calculate throughput between nodes
- Detect bottlenecks (threshold-based)
- Return graph structure for D3.js visualization

### Frontend Components

**1. Queue List View** (`queues.html`)
- Table with queue name, pending, consumers, status
- Real-time updates via WebSocket
- Click row to expand detail view
- DLQ indicator (red badge)
- Overall health summary at top

**2. Queue Detail Panel**
- Metrics chart (pending messages over time)
- Consumer list with individual stats
- Recent errors table
- Quick actions (restart consumers, clear queue)

**3. Message Inspector Modal**
- JSON payload viewer with syntax highlighting
- Metadata panel (ID, timestamp, retry count)
- Routing info (source, destination)
- Actions: Retry, Edit & Retry, Move to DLQ, Delete

**4. Flow Visualization** (D3.js force-directed graph)
- Nodes: Agents (circles), Queues (rectangles)
- Edges: Arrows with throughput labels
- Colors: Green (healthy), Yellow (degraded), Red (critical)
- Animated pulses showing active message flow
- Click nodes/edges for details

**5. DLQ Panel**
- List of trapped messages
- Grouped by error type
- Bulk actions (retry all, delete all)
- Individual message actions

---

## Acceptance Criteria

### Functional Requirements
- [ ] Queue list page shows all 8+ queues with real-time metrics
- [ ] Pending messages, processing rate, consumer count displayed
- [ ] Queue health status (🟢🟡🔴⚫) calculated and shown
- [ ] Click queue → Detail view with metrics history chart
- [ ] Detail view shows consumer list with individual stats
- [ ] DLQ panel shows trapped messages with error details
- [ ] Message inspector displays payload and metadata
- [ ] Manual retry of DLQ messages (edit optional)
- [ ] Manual delete of DLQ messages
- [ ] Flow diagram visualizes message routing
- [ ] Bottleneck detection highlights slow paths
- [ ] Real-time WebSocket updates every 2 seconds
- [ ] Alert thresholds configurable per queue
- [ ] Toast notifications for critical queue events

### Backend Requirements
- [ ] Queue list API returns all queues with metrics
- [ ] Queue detail API includes metrics history (5-minute window)
- [ ] DLQ API lists messages with pagination (50/page)
- [ ] Retry API moves message back to original queue
- [ ] Delete API removes message from DLQ
- [ ] Flow API returns graph structure (nodes + edges)
- [ ] WebSocket endpoint broadcasts queue updates
- [ ] Metrics cached for 2 seconds (reduce Redis load)

### Edge Cases
- [ ] Queue doesn't exist → 404 error
- [ ] No consumers for queue → Show "No active consumers"
- [ ] DLQ empty → "No dead letters"
- [ ] Message retry fails → Show error + keep in DLQ
- [ ] WebSocket disconnect → Auto-reconnect + backoff
- [ ] Queue metrics unavailable → Show stale data + warning
- [ ] Message payload > 10KB → Truncate in list, full in inspector

### Performance
- [ ] Page load < 1 second for 20 queues
- [ ] WebSocket latency < 100ms per update
- [ ] Flow diagram renders < 500ms for 50 nodes
- [ ] API response time < 200ms for queue list
- [ ] Support 100+ queues without UI lag

---

## UI/UX Design

### Queue List View
```
┌─────────────────────────────────────────────────────────────────┐
│ 🔄 Message Queues                     Overall: 🟡 1 Degraded   │
├─────────────────────────────────────────────────────────────────┤
│ Queue Name            Pending  Rate    Consumers  Status  DLQ   │
├─────────────────────────────────────────────────────────────────┤
│ agent.commands          15     12.5/s      3      🟢       0    │
│ agent.events             0      0/s        2      🟢       0    │
│ orchestration.tasks    250      0.5/s      2      🟡       0    │
│ workflow.results         5      3.2/s      1      🟢       0    │
│ agent.logs            1200      0.1/s      1      🔴      12    │
│ agent.metrics           50      8.0/s      1      🟢       0    │
│ dlq.agent.commands       3       -         -      -        -    │
│ dlq.agent.logs          12       -         -      -        -    │
└─────────────────────────────────────────────────────────────────┘
```

### Queue Detail View (Expanded)
```
┌─────────────────────────────────────────────────────────────────┐
│ 🔴 orchestration.tasks               [Close ✕]                  │
├─────────────────────────────────────────────────────────────────┤
│ Pending Messages                                                │
│   ▲                                                              │
│ 250│        ╱───────────                                        │
│ 200│      ╱                                                     │
│ 150│    ╱                                                       │
│ 100│  ╱                                                         │
│  50│╱                                                           │
│   0└────────────────────────────────────────────────────────   │
│     12:00  12:01  12:02  12:03  12:04  12:05                   │
├─────────────────────────────────────────────────────────────────┤
│ Consumers (2)                                                   │
│ • WowOrchestrator   Last: 3 min ago   Rate: 0.3/s   Errors: 5 │
│ • WowWorkflow       Last: 30s ago     Rate: 0.2/s   Errors: 0 │
├─────────────────────────────────────────────────────────────────┤
│ Recent Errors (5 in last 5 min)                                │
│ 12:03:15  WowOrchestrator  Timeout processing message          │
│ 12:02:40  WowOrchestrator  Connection refused                  │
└─────────────────────────────────────────────────────────────────┘
```

### Message Inspector Modal
```
┌─────────────────────────────────────────────────────────────────┐
│ 📧 Message: msg-67890                         [Close ✕]        │
├─────────────────────────────────────────────────────────────────┤
│ Payload (JSON)                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ {                                                           │ │
│ │   "level": "error",                                         │ │
│ │   "message": "Invalid data",                                │ │
│ │   "agent_id": "WowMemory"                                   │ │
│ │ }                                                           │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ Metadata                                                        │
│ • ID: msg-67890                                                │
│ • Timestamp: 2026-01-01 11:45:00                               │
│ • Retry Count: 3                                               │
│ • Original Queue: agent.logs                                   │
│ • Source Agent: WowMemory                                      │
│                                                                 │
│ Error                                                           │
│ ❌ JSON schema validation failed: Missing 'timestamp' field    │
│                                                                 │
│ Actions                                                         │
│ [🔄 Retry]  [✏️ Edit & Retry]  [🗑️ Delete]                   │
└─────────────────────────────────────────────────────────────────┘
```

### Flow Visualization
```
┌─────────────────────────────────────────────────────────────────┐
│ 🔀 Message Flow Diagram                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   (WowMemory) ──5 msg/s──> [agent.logs] ──5 msg/s──> (WowLogger)│
│                                                                 │
│                                                                 │
│   (WowOrchestrator) ──0.5 msg/s──> [orchestration.tasks]      │
│                                          │                      │
│                                          │ 0.5 msg/s (🔴 SLOW) │
│                                          ↓                      │
│                                    (WowWorkflow)                │
│                                          │                      │
│                                          │ 2 msg/s             │
│                                          ↓                      │
│                                   [workflow.results]            │
│                                                                 │
│ 🔴 Bottleneck: orchestration.tasks → WowWorkflow (250 pending) │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technical Tasks

### Phase 1: Backend APIs (3 days)
1. Implement queue metrics service (Redis/RabbitMQ integration)
2. Create queue list API (`GET /api/platform/queues`)
3. Create queue detail API (`GET /api/platform/queues/{name}`)
4. Create DLQ list API (`GET /api/platform/queues/{name}/dlq`)
5. Create message retry API (`POST .../dlq/{id}/retry`)
6. Create message delete API (`DELETE .../dlq/{id}`)
7. Create flow API (`GET /api/platform/queues/flow`)
8. Add WebSocket endpoint for real-time updates
9. Implement bottleneck detection algorithm
10. Write unit tests for all endpoints

### Phase 2: Frontend Core (2 days)
11. Create queues.html page
12. Implement queue list view component
13. Add real-time WebSocket connection
14. Implement queue detail panel (expandable)
15. Add metrics history chart (Chart.js or similar)
16. Implement DLQ panel with message list

### Phase 3: Advanced Features (2 days)
17. Build message inspector modal
18. Add JSON syntax highlighting
19. Implement retry/delete actions
20. Build flow visualization (D3.js)
21. Add animated message flow pulses
22. Implement bottleneck highlighting

### Phase 4: Testing & Polish (2 days)
23. E2E tests for queue monitoring flows
24. Load testing with 100+ queues
25. WebSocket reconnection testing
26. Performance optimization (caching, pagination)
27. Error handling and edge cases
28. Documentation and API specs

**Total Estimate**: 9 days (1 developer)

---

## Testing Strategy

### Unit Tests
- Queue metrics calculations
- Health status determination
- Bottleneck detection algorithm
- Message retry/delete logic

### Integration Tests
- Redis/RabbitMQ connection and queries
- WebSocket message broadcasting
- API endpoints with mock queue data
- DLQ operations (retry, delete)

### E2E Tests
- User monitors queue list → Sees real-time updates
- User clicks queue → Detail view opens
- User inspects DLQ message → Retries successfully
- User views flow diagram → Identifies bottleneck

### Performance Tests
- API response time with 100 queues
- WebSocket scalability (100 concurrent users)
- Flow diagram rendering (100 nodes)

---

## Success Metrics

### User Experience
- MTTR for queue issues: 20min → 3min (85% reduction)
- Queue bottlenecks detected: Within 30 seconds (vs 30 minutes)
- DLQ message recovery rate: 80%+ within 1 hour

### Technical
- API response time < 200ms (queue list)
- WebSocket latency < 100ms per update
- Page load time < 1 second
- Zero missed queue alerts

### Business
- Reduced message loss incidents: 90% reduction
- Operator manual queue checks: 5/week → 0/week
- Platform uptime improvement: +0.5%

---

## Dependencies

### Prerequisites
- Redis/RabbitMQ deployed and accessible ✅
- WebSocket infrastructure (Story 5.1.5)
- Agent status API (Story 5.1.1)

### Integrations
- Event bus for queue events
- Alert system for threshold breaches (Story 5.1.6)

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Redis performance impact | High | Medium | Cache metrics (2s TTL), batch queries |
| WebSocket scalability | Medium | Low | Use WebSocket gateway, rate limiting |
| Large message payloads | Low | Medium | Truncate in list, paginate DLQ |
| Flow diagram complexity | Medium | Low | Limit to 50 nodes, add filtering |

---

## Out of Scope

- ❌ Queue creation/deletion from UI
- ❌ Message replay from arbitrary timestamp
- ❌ Custom routing rule editor
- ❌ Queue performance tuning recommendations
- ❌ Historical queue metrics (> 24 hours)

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

**This story enables proactive queue monitoring and fast resolution of messaging bottlenecks.** 📬
