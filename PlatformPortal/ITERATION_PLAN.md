# PlatformPortal - Fix & Complete Iteration Plan

**Status**: Ready to Execute  
**Created**: January 2, 2026  
**Approach**: Incremental - Fix and test one feature at a time  
**Estimated Duration**: 6-8 days (1-2 days per iteration)

---

## 🎯 Strategy: Progressive Enhancement

**Philosophy**: Fix existing high-quality code rather than rewrite. Enable features incrementally, test thoroughly, then move to next iteration.

**Current State**:
- ✅ Foundation: 43 files, 2,850 LOC, clean architecture
- ✅ 2 pages working: Login, Dashboard
- ❌ 5 pages disabled: Queues, Workflows, Factory, Servicing, Helpdesk
- ⚠️ OAuth needs integration testing
- ⚠️ Backend API integration needs validation

---

## 📋 Iteration Breakdown

### **ITERATION 0: Environment Setup & Validation** (2 hours)

**Goal**: Ensure dev environment is stable and backend APIs are reachable

**Tasks**:
1. Start backend API server (FastAPI on port 8000)
2. Verify critical endpoints:
   - `GET /api/platform/metrics`
   - `GET /api/platform/agents`
   - `GET /auth/google` (OAuth)
3. Check Reflex server starts without errors
4. Document any missing backend endpoints

**Deliverables**:
- [ ] Backend running on `http://localhost:8000`
- [ ] Reflex portal accessible on `http://localhost:3000`
- [ ] API health check passing
- [ ] List of missing/broken API endpoints

**Success Criteria**: Both servers start cleanly, no import errors

---

### **ITERATION 1: OAuth2 Authentication** (Day 1)

**Goal**: Get Google OAuth2 login flow working end-to-end

**Current State**:
- Login page exists: `waooaw_portal/pages/login.py`
- Auth state exists: `waooaw_portal/state/auth_state.py`
- OAuth routes: `/auth/google`, `/auth/callback`

**Tasks**:
1. Review and test `auth_state.py` OAuth flow
2. Configure Google OAuth credentials in environment
3. Test login redirect → Google → callback flow
4. Implement session persistence (JWT storage)
5. Add protected route decorator
6. Test logout flow

**Files to Touch**:
- `waooaw_portal/state/auth_state.py` - OAuth handlers
- `waooaw_portal/pages/login.py` - Login UI
- `backend/app/auth/` - Backend OAuth routes
- `.env` - Google OAuth credentials

**Deliverables**:
- [ ] Login with Google button works
- [ ] User redirected to dashboard after auth
- [ ] JWT token stored in browser
- [ ] Protected routes block unauthenticated users
- [ ] Logout clears session

**Testing Checklist**:
- [ ] Click "Login with Google" → Opens Google consent
- [ ] Accept consent → Redirects to dashboard
- [ ] Refresh page → Still logged in
- [ ] Click logout → Redirects to login
- [ ] Try accessing `/dashboard` without auth → Blocked

**Success Criteria**: Full OAuth flow working, users can login/logout

---

### **ITERATION 2: Dashboard + Agent List** (Day 2)

**Goal**: Dashboard fully functional with real-time metrics and agent list

**Current State**:
- Dashboard page working: Shows 4 metric cards
- Needs: Agent list/grid view
- Backend: `/api/platform/metrics`, `/api/platform/agents`

**Tasks**:
1. Enhance dashboard with agent grid
2. Add agent status indicators (🟢🟡🔴)
3. Implement auto-refresh (30s interval)
4. Add filter/search for agents
5. Click agent → View details modal
6. Wire up WebSocket for real-time updates (optional)

**Files to Touch**:
- `waooaw_portal/pages/dashboard.py` - Add agent grid
- `waooaw_portal/state/dashboard_state.py` - Agent data management
- `waooaw_portal/state/agents_state.py` - Agent-specific state
- `waooaw_portal/components/common/status_badge.py` - Already exists
- Backend: Ensure `/api/platform/agents` returns proper data

**Deliverables**:
- [ ] Dashboard shows 4 metric cards (existing)
- [ ] Agent grid below metrics (new)
- [ ] Each agent shows: name, status, tier, last_active
- [ ] Click agent → Detail modal with actions
- [ ] Auto-refresh every 30 seconds
- [ ] Search/filter agents by name or status

**Mock Data Structure**:
```json
{
  "agents": [
    {
      "agent_id": "wow-memory",
      "name": "WowMemory",
      "tier": "Platform CoE",
      "status": "online",
      "last_active": "2 minutes ago",
      "capabilities": ["memory", "context"],
      "health": "healthy"
    }
  ]
}
```

**Testing Checklist**:
- [ ] Dashboard loads in <2s
- [ ] Metrics show real/mock data
- [ ] Agent cards render correctly
- [ ] Status badges show correct colors
- [ ] Clicking agent opens detail modal
- [ ] Refresh button updates data

**Success Criteria**: Dashboard is fully interactive with agent visibility

---

### **ITERATION 3: Queues Monitoring** (Day 3)

**Goal**: Enable queue monitoring page with DLQ management

**Current State**:
- Page exists: `waooaw_portal/pages/queues.py` (438 lines)
- State exists: `waooaw_portal/state/queue_state.py`
- Commented out in main app

**Tasks**:
1. Uncomment queues page in `waooaw_portal.py`
2. Create backend endpoint: `GET /api/platform/queues`
3. Test queue list rendering
4. Implement DLQ panel
5. Add message retry/delete actions
6. Add real-time updates (WebSocket or polling)

**Files to Touch**:
- `waooaw_portal/waooaw_portal.py` - Uncomment route
- `waooaw_portal/pages/queues.py` - Review and test
- `waooaw_portal/state/queue_state.py` - API integration
- `backend/app/routes/platform.py` - Add `/queues` endpoint
- Navigation: Add "Queues" link to sidebar

**Backend API Spec**:
```python
# GET /api/platform/queues
{
  "queues": [
    {
      "queue_name": "agent-tasks",
      "status": "healthy",  # healthy | degraded | critical
      "messages_pending": 245,
      "throughput_per_sec": 12,
      "consumer_lag": 5,
      "error_rate": 0.2,
      "dlq_messages": 3
    }
  ]
}

# GET /api/platform/queues/{name}/dlq
{
  "messages": [
    {
      "message_id": "msg-123",
      "payload": {...},
      "error": "Connection timeout",
      "retry_count": 3,
      "timestamp": "2026-01-02T10:30:00Z"
    }
  ]
}
```

**Deliverables**:
- [ ] Queues page accessible at `/queues`
- [ ] Queue list with health status
- [ ] DLQ panel showing failed messages
- [ ] Retry button works
- [ ] Delete button works
- [ ] Real-time status updates

**Testing Checklist**:
- [ ] Navigate to Queues page
- [ ] See list of 4+ queues
- [ ] Click queue → DLQ panel opens
- [ ] Click retry → Message reprocessed
- [ ] Status updates every 5 seconds

**Success Criteria**: Queue monitoring fully operational

---

### **ITERATION 4: Workflows Orchestration** (Day 4)

**Goal**: Enable workflow monitoring with Gantt chart visualization

**Current State**:
- Page exists: `waooaw_portal/pages/workflows.py` (602 lines)
- State exists: `waooaw_portal/state/workflow_state.py`
- Commented out in main app

**Tasks**:
1. Uncomment workflows page in `waooaw_portal.py`
2. Create backend endpoint: `GET /api/platform/orchestration/workflows`
3. Test workflow list rendering
4. Implement Gantt chart (timeline visualization)
5. Add workflow controls: pause, resume, cancel
6. Add step detail inspector

**Files to Touch**:
- `waooaw_portal/waooaw_portal.py` - Uncomment route
- `waooaw_portal/pages/workflows.py` - Review and test
- `waooaw_portal/state/workflow_state.py` - API integration
- `backend/app/routes/orchestration.py` - Add workflow endpoints
- Navigation: Add "Workflows" link

**Backend API Spec**:
```python
# GET /api/platform/orchestration/workflows
{
  "workflows": [
    {
      "workflow_id": "wf-123",
      "workflow_name": "Customer Onboarding",
      "customer_name": "Acme Corp",
      "status": "running",  # pending | running | completed | failed | paused
      "progress": 60,
      "total_tasks": 5,
      "completed_tasks": 3,
      "failed_tasks": 0,
      "started_at": "2026-01-02T10:00:00Z",
      "tasks": [
        {
          "task_id": "task-1",
          "task_name": "Provision Agent",
          "status": "completed",
          "duration_ms": 2000,
          "started_at": "2026-01-02T10:00:00Z",
          "completed_at": "2026-01-02T10:00:02Z"
        }
      ]
    }
  ]
}
```

**Deliverables**:
- [ ] Workflows page accessible at `/workflows`
- [ ] Workflow list with status
- [ ] Gantt chart timeline (simplified)
- [ ] Click workflow → Detail view with tasks
- [ ] Pause/resume/cancel buttons work
- [ ] Progress bar shows completion

**Testing Checklist**:
- [ ] Navigate to Workflows page
- [ ] See list of workflows
- [ ] Click workflow → Task details shown
- [ ] Progress bar animates correctly
- [ ] Pause button → Workflow pauses
- [ ] Resume button → Workflow continues

**Success Criteria**: Workflow orchestration monitoring working

---

### **ITERATION 5: Agent Factory** (Day 5-6)

**Goal**: Enable agent creation wizard with 6 templates

**Current State**:
- Page exists: `waooaw_portal/pages/factory.py` (647 lines)
- State exists: `waooaw_portal/state/factory_state.py` (465 lines)
- Templates defined: Memory, Orchestration, API, Data, Monitoring, Blank
- Commented out in main app

**Tasks**:
1. Uncomment factory page in `waooaw_portal.py`
2. Test 6-step wizard flow
3. Create backend endpoints for template/validation/deployment
4. Wire up form validation
5. Implement sandbox testing (mock for now)
6. Test full agent creation flow

**Files to Touch**:
- `waooaw_portal/waooaw_portal.py` - Uncomment route
- `waooaw_portal/pages/factory.py` - Review and test
- `waooaw_portal/state/factory_state.py` - API integration
- `waooaw_portal/components/factory/` - Wizard components
- `backend/app/routes/factory.py` - Create factory endpoints
- Navigation: Add "Factory" link

**Backend API Spec**:
```python
# GET /api/platform/factory/templates
{
  "templates": [
    {
      "template_id": "tmpl-memory",
      "name": "Memory Agent",
      "description": "...",
      "category": "memory",
      "complexity": "medium"
    }
  ]
}

# POST /api/platform/factory/validate
{
  "agent_name": "my-memory-agent",
  "template_id": "tmpl-memory",
  "config": {...}
}
# Response: {"valid": true, "errors": []}

# POST /api/platform/factory/agents
{
  "agent_name": "my-memory-agent",
  "template_id": "tmpl-memory",
  "config": {...}
}
# Response: {"agent_id": "agent-456", "status": "provisioning"}
```

**Wizard Steps**:
1. Choose Template (6 cards)
2. Configure Agent (form with validation)
3. Set Resources (CPU, memory, storage sliders)
4. Review Configuration (summary)
5. Deploy (progress tracking)
6. Complete (success message + agent details)

**Deliverables**:
- [ ] Factory page accessible at `/factory`
- [ ] 6 template cards render
- [ ] Click template → Wizard advances
- [ ] Form validation works (name required, etc.)
- [ ] Resource sliders functional
- [ ] Review shows all config
- [ ] Deploy button → Agent created
- [ ] Success page shows agent ID

**Testing Checklist**:
- [ ] Navigate to Factory page
- [ ] Click "Memory Agent" template
- [ ] Fill in agent name: "test-agent"
- [ ] Configure resources
- [ ] Review configuration
- [ ] Click Deploy
- [ ] See deployment progress
- [ ] Success message shows

**Success Criteria**: Full agent creation wizard working end-to-end

---

### **ITERATION 6: Agent Servicing** (Day 7)

**Goal**: Enable agent upgrade/configuration management

**Current State**:
- Page exists: `waooaw_portal/pages/servicing.py`
- State exists: `waooaw_portal/state/servicing_state.py`
- Commented out in main app

**Tasks**:
1. Uncomment servicing page in `waooaw_portal.py`
2. Create agent version management UI
3. Implement upgrade wizard
4. Add rollback functionality
5. Add hot configuration patching

**Files to Touch**:
- `waooaw_portal/waooaw_portal.py` - Uncomment route
- `waooaw_portal/pages/servicing.py` - Review and test
- `waooaw_portal/state/servicing_state.py` - API integration
- `backend/app/routes/servicing.py` - Servicing endpoints
- Navigation: Add "Servicing" link

**Backend API Spec**:
```python
# GET /api/platform/agents/{agent_id}/versions
{
  "current_version": "v1.2.0",
  "available_versions": ["v1.2.1", "v1.3.0"],
  "changelog": "..."
}

# POST /api/platform/agents/{agent_id}/upgrade
{
  "target_version": "v1.2.1",
  "strategy": "blue-green"  # blue-green | canary | rolling
}

# POST /api/platform/agents/{agent_id}/rollback
# Rolls back to previous version

# PATCH /api/platform/agents/{agent_id}/config
{
  "config": {"rate_limit": 200}
}
```

**Deliverables**:
- [ ] Servicing page accessible at `/servicing`
- [ ] Agent list with current versions
- [ ] Click agent → Version manager
- [ ] Upgrade button starts wizard
- [ ] Rollback button works
- [ ] Hot config patch applies instantly

**Testing Checklist**:
- [ ] Navigate to Servicing page
- [ ] Select agent
- [ ] See current version
- [ ] Click upgrade → Wizard starts
- [ ] Complete upgrade flow
- [ ] Agent version updated

**Success Criteria**: Agent servicing operational

---

### **ITERATION 7: Help Desk** (Day 8)

**Goal**: Enable customer support tools with diagnostics

**Current State**:
- Page exists: `waooaw_portal/pages/helpdesk.py`
- State exists: `waooaw_portal/state/helpdesk_state.py`
- Commented out in main app

**Tasks**:
1. Uncomment helpdesk page in `waooaw_portal.py`
2. Create customer search
3. Implement issue diagnostics panel
4. Add quick actions (restart, clear cache, etc.)
5. Create playbook library

**Files to Touch**:
- `waooaw_portal/waooaw_portal.py` - Uncomment route
- `waooaw_portal/pages/helpdesk.py` - Review and test
- `waooaw_portal/state/helpdesk_state.py` - API integration
- `backend/app/routes/helpdesk.py` - Helpdesk endpoints
- Navigation: Add "Help Desk" link

**Backend API Spec**:
```python
# GET /api/platform/helpdesk/customers/search?q=acme
{
  "customers": [
    {
      "customer_id": "cust-123",
      "company_name": "Acme Corp",
      "email": "admin@acme.com",
      "agents_count": 3,
      "status": "active"
    }
  ]
}

# GET /api/platform/helpdesk/customers/{id}/overview
{
  "customer": {...},
  "agents": [...],
  "recent_issues": [...]
}

# POST /api/platform/helpdesk/actions/restart-agent
{
  "agent_id": "agent-123"
}
```

**Deliverables**:
- [ ] Help Desk page accessible at `/helpdesk`
- [ ] Customer search works
- [ ] Click customer → Overview panel
- [ ] Quick actions functional
- [ ] Issue diagnostics show root cause
- [ ] Playbooks accessible

**Testing Checklist**:
- [ ] Navigate to Help Desk
- [ ] Search "acme"
- [ ] Click customer
- [ ] See agent list
- [ ] Click "Restart Agent"
- [ ] Agent restarts

**Success Criteria**: Help desk fully operational

---

### **ITERATION 8: Logs & Alerts** (Optional - if time permits)

**Goal**: Add observability pages for logs and alerts

**Tasks**:
1. Create logs page with filtering
2. Create alerts page with acknowledgment
3. Integrate with context selector
4. Add real-time updates

**Files to Create/Touch**:
- `waooaw_portal/pages/logs.py` - New page
- `waooaw_portal/pages/alerts.py` - New page
- Backend endpoints for logs/alerts
- Navigation links

**Deliverables**:
- [ ] Logs page with filters (level, agent, time)
- [ ] Alerts page with severity badges
- [ ] Acknowledge/resolve actions
- [ ] Real-time log streaming

**Success Criteria**: Full observability stack complete

---

## 🔧 Technical Approach Per Iteration

### Standard Fix Process:

1. **Uncomment Route**:
   ```python
   # waooaw_portal/waooaw_portal.py
   from waooaw_portal.pages.queues import queues_page
   app.add_page(queues_page, route="/queues", title="Queues - WAOOAW")
   ```

2. **Test Page Rendering**:
   ```bash
   reflex run
   # Open http://localhost:3000/queues
   ```

3. **Fix Import Errors**:
   - Check for missing dependencies
   - Verify state class imports
   - Fix component references

4. **Create/Verify Backend API**:
   ```python
   # backend/app/routes/platform.py
   @router.get("/queues")
   async def get_queues():
       return {"queues": [...]}
   ```

5. **Test State Integration**:
   - Check `on_mount` triggers
   - Verify API calls succeed
   - Check state updates UI

6. **Add Navigation Link**:
   ```python
   # In navigation component
   rx.link("Queues", href="/queues")
   ```

7. **Test End-to-End**:
   - Click through UI
   - Verify all actions work
   - Check error handling

---

## 📊 Progress Tracking

### Daily Standup Template:
```
**Yesterday**: Completed Iteration X - [Feature]
**Today**: Working on Iteration Y - [Feature]
**Blockers**: [None | API endpoint missing | ...]
**Demo**: [Link to working feature]
```

### Completion Checklist:

- [ ] **Iteration 0**: Environment validated
- [ ] **Iteration 1**: OAuth working
- [ ] **Iteration 2**: Dashboard + Agents
- [ ] **Iteration 3**: Queues monitoring
- [ ] **Iteration 4**: Workflows
- [ ] **Iteration 5**: Agent Factory
- [ ] **Iteration 6**: Agent Servicing
- [ ] **Iteration 7**: Help Desk
- [ ] **Iteration 8**: Logs & Alerts (optional)

---

## 🎯 Success Metrics

### Per Iteration:
- [ ] Page loads without errors
- [ ] All UI components render
- [ ] Backend API integration works
- [ ] User actions have visible effects
- [ ] No console errors

### Overall Portal:
- [ ] All 8+ pages accessible
- [ ] Navigation works between pages
- [ ] OAuth protects routes
- [ ] Real-time updates working
- [ ] Professional UI/UX
- [ ] <2s page load time
- [ ] Mobile responsive

---

## 🚨 Known Issues to Address

### High Priority:
1. **OAuth Credentials**: Need Google OAuth client ID/secret configured
2. **Backend API Endpoints**: Most platform routes need implementation
3. **WebSocket Setup**: Real-time updates need WebSocket server

### Medium Priority:
1. **Error Handling**: Add user-friendly error messages
2. **Loading States**: Add skeletons for data fetching
3. **Mobile Responsiveness**: Test on smaller screens

### Low Priority:
1. **Theme Persistence**: Save dark/light preference
2. **Keyboard Navigation**: Add keyboard shortcuts
3. **Accessibility**: ARIA labels for screen readers

---

## 📁 Supporting Files to Create

### Backend Routes (if missing):
- `backend/app/routes/platform.py` - Dashboard metrics, agents
- `backend/app/routes/queues.py` - Queue monitoring
- `backend/app/routes/orchestration.py` - Workflows
- `backend/app/routes/factory.py` - Agent creation
- `backend/app/routes/servicing.py` - Agent upgrades
- `backend/app/routes/helpdesk.py` - Customer support

### Configuration:
- `.env.local` - Development environment variables
- `backend/.env` - Backend configuration
- OAuth credentials setup guide

---

## 🎉 Definition of Done (Final)

### Portal Complete When:
- [x] All 8 pages working
- [x] OAuth authentication flow complete
- [x] All CRUD operations functional
- [x] Real-time updates operational
- [x] Navigation intuitive
- [x] No console errors
- [x] Mobile responsive
- [x] Documentation updated
- [x] Deployed to staging
- [x] Stakeholder demo successful

---

**Estimated Timeline**: 6-8 days (assuming 1 developer, 6-8 hours/day)  
**Risk Level**: Low (code already written, just needs integration)  
**Next Action**: Start Iteration 0 - Environment Setup

---

*This plan leverages the existing high-quality codebase. Focus on integration, not rewriting.*
