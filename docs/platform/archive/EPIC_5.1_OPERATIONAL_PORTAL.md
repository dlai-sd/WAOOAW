# Epic 5.1: Operational Portal for Platform CoE Agents

**Epic ID**: Epic-5.1  
**Theme**: ORCHESTRATE  
**Status**: Ready for Planning  
**Owner**: Platform Team  
**Target**: Q1 2026  
**Created**: 2026-01-01

---

## Vision

Transform the Platform Portal from a static registry viewer into a **production-grade operational control plane** where operators can deploy, manage, monitor, and troubleshoot all 14 Platform CoE agents through an intuitive interface with real-time observability.

## Business Value

- **Reduce deployment time**: 30 minutes → 5 minutes (agent deployment)
- **Improve MTTR**: 20 minutes → 2 minutes (mean time to recovery)
- **Increase operator efficiency**: 1 operator can manage 14 agents vs 3 today
- **Enable self-service**: Developers debug agents without DevOps intervention

## Current State (v0.8.3)

✅ **Completed:**
- Platform Portal with OAuth authentication
- Agent registry with 14 Platform CoE agent definitions
- Logs/Alerts/Events/Metrics UI pages
- Agent cards showing registry status (draft, registered, provisioned)
- APIs returning static registry metadata

❌ **Missing:**
- No actual agent deployment to infrastructure
- No lifecycle management (start, stop, restart)
- No real-time status updates
- No bulk operations
- No context-based filtering
- No error recovery mechanisms

## Target State

Operators can:
1. See 14 real Platform CoE agents with live runtime status
2. Deploy agents to Docker/Kubernetes with one click
3. Start/stop/restart agents via UI
4. Perform bulk operations (deploy all, restart errored)
5. See agent-specific logs/alerts/events when troubleshooting
6. Get actionable error messages with recovery suggestions
7. Monitor in real-time without manual refresh

---

## Stories in this Epic

### Story 5.1.1: Agent State Machine & Lifecycle Transitions ⭐ P0
**Points**: 13  
**Dependencies**: None  
**Risk**: Medium

Foundation for all lifecycle management. Implements state machine with transitions, validation, audit trail, and PostgreSQL persistence.

**States**: DRAFT → PROVISIONED → DEPLOYED → RUNNING ↔ SUSPENDED ↔ STOPPED ↔ ERRORED → REVOKED

---

### Story 5.1.2: Single Agent Lifecycle Actions ⭐ P0
**Points**: 21  
**Dependencies**: Story 5.1.1  
**Risk**: Medium

UI actions (provision, deploy, start, stop, suspend, restart) with confirmation modals, loading states, and error handling.

**Endpoints**: 8 action endpoints for each lifecycle transition.

---

### Story 5.1.3: Bulk Agent Operations ⭐ P1
**Points**: 13  
**Dependencies**: Story 5.1.2  
**Risk**: Low

Multi-select with bulk actions (deploy all, start all, stop all) with progress tracking and summary reports.

---

### Story 5.1.4: Agent Deployment to Infrastructure ⭐ P0
**Points**: 21  
**Dependencies**: Story 5.1.1  
**Risk**: High

Docker/Kubernetes deployment integration with health monitoring, auto-restart, and resource management.

---

### Story 5.1.5: Real-Time Status Updates via WebSocket ⭐ P1
**Points**: 13  
**Dependencies**: Story 5.1.1  
**Risk**: Medium

WebSocket streaming of agent state changes, health updates, and bulk operation progress.

---

### Story 5.1.6: Enhanced Error Handling & Recovery ⭐ P1
**Points**: 13  
**Dependencies**: Story 5.1.2  
**Risk**: Low

Error classification, root cause analysis, actionable suggestions, and one-click recovery actions.

---

### Story 5.1.7: Context-Based Observability ⭐ P1
**Points**: 8  
**Dependencies**: None  
**Risk**: Low

Agent-specific filtering for logs/alerts/events/metrics with context switcher, quick actions, and persistence.

---

## Epic Summary

**Total Stories**: 7  
**Total Story Points**: 102  
**Estimated Duration**: 4-5 weeks (2-person team)

**Priority Breakdown**:
- P0 (Critical): 4 stories (68 points)
- P1 (High): 3 stories (34 points)

**Dependencies Graph**:
```
Story 5.1.1 (State Machine)
    ↓
Story 5.1.2 (Single Actions) → Story 5.1.6 (Error Handling)
    ↓                              ↓
Story 5.1.3 (Bulk Ops)         Story 5.1.7 (Context Views)
    ↓
Story 5.1.4 (Deployment)
    ↓
Story 5.1.5 (Real-Time Updates)
```

---

## Success Metrics

**Operational:**
- Deploy all 14 Platform CoE agents in < 5 minutes
- 99.9% uptime for critical agents (WowVision, WowEvent)
- < 30s recovery time from agent crashes
- < 2 min MTTR (mean time to recovery)

**User Experience:**
- Single-click deploy → running (vs manual kubectl/docker)
- Real-time status updates (no manual refresh)
- 80% self-service recovery from errors
- Zero-downtime bulk operations

**Platform Health:**
- Agent uptime dashboards
- Error rate tracking and trending
- Resource utilization monitoring
- Dependency graph visualization

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Agent crashes cascade to dependencies | High | Health checks before start, circuit breakers |
| Docker socket access security concerns | High | Use K8s API, implement RBAC policies |
| Bulk operations exhaust resources | Medium | Rate limiting, max parallel deploys (3-5) |
| State machine race conditions | Medium | Optimistic locking, event sourcing |
| WebSocket stability across networks | Low | Auto-reconnect with backoff, polling fallback |

---

## Technical Components

### Backend Services
- `AgentStateMachine` - State transition validation and audit
- `AgentOrchestrator` - Deployment and lifecycle management
- `AgentHealthMonitor` - Continuous health checking
- `AgentErrorHandler` - Error enrichment and recovery

### Database Schema
- `agent_state_history` - Audit trail of all transitions
- `agent_current_state` - Current state and health
- `agent_deployments` - Deployment metadata
- `agent_errors` - Error tracking and retry history

### Frontend Components
- Context switcher and persistence
- Action dropdown menus (context-aware)
- Bulk selection toolbar
- Progress modals for bulk ops
- Error panels with recovery actions
- WebSocket connection manager

---

## Definition of Done

An operator can:
1. ✅ Deploy WowMemory via UI → Docker container starts
2. ✅ Click "Stop All Running" → All agents gracefully stop
3. ✅ Select 5 errored agents → Click "Restart" → All 5 restart
4. ✅ Click WowCache card → See only WowCache logs/alerts
5. ✅ When agent crashes → See error with recovery steps
6. ✅ Dashboard updates in real-time without refresh
7. ✅ Bulk deploy 14 agents in under 5 minutes

**This epic delivers production-ready agent orchestration.** 🚀
