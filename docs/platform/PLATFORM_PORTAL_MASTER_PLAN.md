# Platform Portal - Master Implementation Plan

**Project**: Professional Platform Portal (New Build in `PlatformPortal/` folder)  
**Status**: Planning Phase  
**Created**: January 1, 2026  
**Total Scope**: 246 Story Points  
**Duration**: 14 weeks (3.5 months)  
**Team**: 2-3 developers

---

## 🎯 Vision

Build a **production-grade operational control plane** for WAOOAW Platform, replacing the current vanilla JS portal with a framework-based, professional solution that combines:

1. **Current portal's strengths**: OAuth2, branding, theme system
2. **Agent lifecycle management**: Deploy, monitor, control agents
3. **Advanced operations**: Factory, servicing, help desk capabilities
4. **Real-time observability**: WebSocket updates, context filtering, diagnostics

---

## 📋 Theme: PLATFORM OPERATIONS

### Theme Goals
- Enable operators to manage 14+ Platform CoE agents efficiently
- Reduce deployment time from 30 min → 5 min
- Reduce MTTR from 20 min → 2 min
- Enable self-service debugging and troubleshooting
- 99.9% platform uptime
- Professional, maintainable codebase

---

## 🏗️ Architecture Decision

### ✅ **DECISION: Reflex (Pure Python Frontend)**

**Decision Date**: January 1, 2026  
**Decision Maker**: Platform Team  
**Status**: Approved ✅

### New Technology Stack
- **Frontend**: **Reflex (Pure Python!)** - React under the hood
- **Backend**: FastAPI (keep existing, enhance)
- **State**: Reflex State (built-in state management)
- **UI Components**: Reflex Component Library (60+ components) + Custom
- **Real-time**: Reflex WebSocket (built-in, no setup needed)
- **Styling**: Reflex Theme System + Custom CSS (WAOOAW colors)
- **Auth**: OAuth2 with Google (keep existing, integrate with Reflex)
- **Language**: **100% Python** - No JavaScript/TypeScript needed!

### Why Reflex (Pure Python)?

#### ✅ **Primary Benefits**
1. **Unified Language** - 100% Python across frontend + backend
2. **Team Efficiency** - Python developers can handle everything (no JS skills needed)
3. **Type Safety** - Python type hints throughout (no learning TypeScript)
4. **Faster Development** - No context switching between Python ↔ JavaScript
5. **React Performance** - Gets React's speed (compiles to React under the hood)
6. **Built-in Real-time** - WebSocket support out-of-the-box
7. **Component Library** - 60+ pre-built components (cards, badges, buttons, etc.)
8. **Hot Reload** - Fast development feedback loop
9. **Production Ready** - Used by companies in production
10. **Easier Hiring** - Easier to find Python devs than React+Python devs

#### 🔄 **vs React + TypeScript**
| Aspect | Reflex (Python) | React (JS/TS) |
|--------|----------------|---------------|
| Language | 100% Python ✅ | JavaScript/TypeScript |
| Team Fit | Perfect for Python team ✅ | Need JS expertise |
| Learning Curve | Low (Python devs) ✅ | High (new language) |
| Maintenance | Single language ✅ | Two languages |
| Type Safety | Python type hints ✅ | TypeScript types |
| Performance | Very Good (React engine) | Excellent |
| Ecosystem | Growing (60+ components) | Huge (unlimited) |
| Real-time | Built-in WebSocket ✅ | Manual setup |

#### ⚖️ **Trade-offs Accepted**
- ❌ Smaller ecosystem than React (but growing rapidly)
- ❌ Slightly larger initial bundle (includes Python→React compiler)
- ❌ Less third-party components (but 60+ built-in covers our needs)
- ✅ **Worth it for**: Unified codebase, team efficiency, faster development

### Why Framework-Based (vs Vanilla HTML/JS)?
- ✅ Component reusability (no duplication)
- ✅ Type safety with Python type hints
- ✅ Better state management (Reflex State)
- ✅ Easier testing and maintenance
- ✅ Hot reload during development
- ✅ Built-in WebSocket for real-time updates
- ✅ Professional component library
- ✅ Same team can maintain frontend + backend

### What to Keep from Current Portal
- ✅ Google OAuth2 authentication flow
- ✅ WAOOAW logo and branding (Waooaw-Logo.png)
- ✅ Dark/light theme colors (#0a0a0a, #00f2fe, #667eea)
- ✅ User role system (Admin/Operator/Viewer)
- ✅ Page navigation structure (7 core pages)
- ✅ Backend API patterns

### What to Rebuild
- ❌ All frontend code (vanilla JS → Reflex Python)
- ❌ Component patterns (HTML → Reflex components)
- ❌ State management (localStorage → Reflex State)
- ❌ Real-time updates (setTimeout → Reflex WebSocket)
- ❌ API integration (fetch → proper Reflex service layer)

---

## 📋 Framework Decision Documentation

### Alternatives Considered

**Option A: Reflex (Pure Python)** ✅ **CHOSEN**
- **Pros**: 100% Python, team efficiency, type-safe, built-in real-time
- **Cons**: Smaller ecosystem, newer framework
- **Decision**: Best fit for Python-heavy team

**Option B: React + TypeScript** ❌ Rejected
- **Pros**: Huge ecosystem, mature, excellent performance
- **Cons**: Requires JS/TS skills, team split, two languages
- **Decision**: Too much overhead for Python team

**Option C: NiceGUI (Python)** ❌ Rejected
- **Pros**: Simple, pure Python, FastAPI native
- **Cons**: Less flexible for complex UIs, smaller component library
- **Decision**: Not powerful enough for 246-point epic

**Option D: HTMX + FastAPI** ❌ Rejected
- **Pros**: Minimal JS, server-side rendering, simple
- **Cons**: Less interactive, more server requests, limited state
- **Decision**: Too simplistic for real-time operational portal

### Why Reflex Won

1. **Team Alignment** - Python developers, Python stack
2. **Unified Codebase** - No context switching between languages
3. **Production Ready** - Proven in enterprise environments
4. **Built-in Features** - WebSocket, state management, hot reload
5. **Performance** - React engine under the hood
6. **Type Safety** - Python type hints throughout
7. **Maintenance** - Single language = easier long-term
8. **Hiring** - Easier to find Python devs

### Success Criteria for Reflex

- [ ] All 14 stories implementable in Reflex
- [ ] Performance meets targets (<2s load, <100ms updates)
- [ ] Team productivity increases (no JS context switching)
- [ ] WebSocket real-time updates working smoothly
- [ ] 85%+ test coverage maintained
- [ ] WAOOAW theme perfectly replicated
- [ ] Production deployment successful

### Reflex Resources

- **Documentation**: https://reflex.dev/docs
- **Component Gallery**: https://reflex.dev/docs/library
- **Examples**: https://github.com/reflex-dev/reflex-examples
- **Discord Community**: https://discord.gg/T5WSbC2YtQ
- **GitHub**: https://github.com/reflex-dev/reflex

### Quick Start Example

Here's what a Reflex component looks like (100% Python):

```python
import reflex as rx

class DashboardState(rx.State):
    """State management for dashboard."""
    agent_count: int = 0
    active_tasks: int = 0
    
    async def load_metrics(self):
        """Load metrics from backend API."""
        response = await self.get_state().api_client.get("/api/agents/metrics")
        self.agent_count = response["agent_count"]
        self.active_tasks = response["active_tasks"]

def metrics_card(title: str, value: str, icon: str, trend: str) -> rx.Component:
    """Reusable metrics card component."""
    return rx.card(
        rx.hstack(
            rx.icon(icon, size=32, color="cyan"),
            rx.vstack(
                rx.text(title, size="2", color="gray"),
                rx.heading(value, size="6"),
                rx.text(trend, size="1", color="green"),
                align="start",
                spacing="1",
            ),
            justify="between",
            width="100%",
        ),
        padding="1.5rem",
        background="var(--gray-2)",
        border="1px solid var(--gray-6)",
        _hover={"transform": "translateY(-4px)", "box_shadow": "0 0 20px rgba(0, 242, 254, 0.2)"},
    )

def dashboard() -> rx.Component:
    """Main dashboard page."""
    return rx.box(
        rx.heading("Platform Dashboard", size="8", margin_bottom="2rem"),
        rx.grid(
            metrics_card("Total Agents", DashboardState.agent_count, "users", "↑ 12% this week"),
            metrics_card("Active Tasks", DashboardState.active_tasks, "activity", "→ Stable"),
            columns="2",
            spacing="4",
        ),
        on_mount=DashboardState.load_metrics,
        padding="2rem",
    )
```

**Key Benefits Shown**:
- 🐍 Pure Python (no JSX, no TypeScript)
- 🎨 Component-based (like React)
- 🔄 Reactive state updates (automatic UI refresh)
- 🎯 Type-safe (Python type hints)
- 🚀 Fast (compiles to optimized React)

---

## 📊 Implementation Phases

### **PHASE 1: FOUNDATION (Weeks 1-2) - 13 Points**

#### Epic 1: Common Platform Components (Story 5.1.0)
**Status**: Critical Path - Build First  
**Points**: 13  
**Duration**: 2 weeks  
**Team**: 2 developers (paired)

**Goal**: Build reusable infrastructure that all other stories will use

#### Frontend Components (6 components)
- **WebSocket Manager** (`services/websocket.py`)
  - Connection lifecycle with auto-reconnect
  - Subscription management
  - Heartbeat/keepalive
  - Error handling with exponential backoff
  - Used in: Queue monitoring, orchestration, agent servicing

- **Metrics Widget** (`components/common/metrics_widget.py`)
  - Real-time number display with formatting
  - Trend indicators (↑↓→)
  - Mini sparkline charts
  - Configurable refresh intervals
  - Status color coding
  - Used in: Dashboard, queue monitoring, help desk

- **Status Badge** (`components/common/status_badge.py`)
  - Color-coded status indicators
  - Consistent styling across portal
  - Tooltip with details
  - Animation on status changes
  - Used in: Agent cards, queue health, workflow steps

- **Timeline Viewer** (`components/common/timeline.py`)
  - Vertical timeline with steps
  - Status icons per step
  - Duration display
  - Collapsible details
  - Used in: Orchestration monitoring, help desk

- **Progress Tracker** (`components/common/progress_tracker.py`)
  - Step-by-step progress visualization
  - Percentage complete
  - Estimated time remaining
  - Cancel/pause actions
  - Used in: Agent factory, agent servicing, bulk operations

- **Context Selector** (`components/common/context_selector.py`)
  - Global agent/customer selector dropdown
  - Search/filter capabilities
  - Persistent selection (browser storage)
  - Quick actions menu
  - Used in: All observability pages

#### Backend Services (5 services)
- **WebSocket Broadcaster** (`backend/app/services/websocket.py`)
  - Room-based message broadcasting
  - Client connection management
  - Authentication integration
  - Rate limiting
  - Used in: All real-time features

- **Metrics Aggregator** (`backend/app/services/metrics.py`)
  - Time-series data collection
  - Caching layer (Redis)
  - Threshold monitoring
  - Alert generation
  - Used in: Dashboard, queue monitoring, orchestration

- **Health Checker** (`backend/app/services/health.py`)
  - Agent health probes (HTTP/TCP/exec)
  - Dependency health checks
  - Health history tracking
  - Auto-remediation triggers
  - Used in: Agent management, deployment, servicing

- **Audit Logger** (`backend/app/services/audit.py`)
  - User action logging
  - State change tracking
  - Compliance reports
  - Searchable audit trail
  - Used in: All mutation operations

- **Provisioning Engine** (`backend/app/services/provisioning.py`)
  - Infrastructure resource allocation
  - Docker/K8s deployment
  - Configuration management
  - Cleanup on failure
  - Used in: Agent factory, agent deployment, servicing

#### Success Criteria
- [ ] All 12 components working with 85%+ test coverage
- [ ] Documentation complete with usage examples
- [ ] Performance: <50ms component response, 99.9% WebSocket uptime
- [ ] Published to internal component registry

---

### **PHASE 2: CORE PORTAL (Weeks 3-4) - 29 Points**

#### Epic 2.1: Authentication & Dashboard (New)
**Points**: 8  
**Duration**: 1 week  
**Team**: 1 developer

**Stories**:
- Port OAuth2 system to React
- Implement JWT token management
- Build dashboard with real-time stats
- User profile and logout

**Pages**:
- `pages/Login.tsx` - OAuth flow
- `pages/Dashboard.tsx` - Main portal home

**APIs**:
- Keep existing: `/auth/login`, `/auth/callback`
- Enhance: `/api/platform/metrics` with real data

#### Epic 2.2: Agent Management Foundation (Stories 5.1.1 + 5.1.7 combined)
**Points**: 21 (13 + 8)  
**Duration**: 1.5 weeks  
**Team**: 2 developers

**Story 2.2.1: Agent State Machine (13 pts)**
- Implement state machine: DRAFT → PROVISIONED → DEPLOYED → RUNNING → STOPPED → ERRORED
- State transition validation
- Audit trail in PostgreSQL
- State history visualization

**Example Reflex Code**:
```python
# components/agents/agent_card.py
import reflex as rx
from typing import Optional

class AgentCard(rx.Component):
    """Reusable agent card component with state machine"""
    
    agent_id: str
    agent_name: str
    status: str  # DRAFT, PROVISIONED, DEPLOYED, RUNNING, etc.
    last_active: str
    tier: str
    
    def render(self):
        return rx.card(
            rx.hstack(
                # Agent avatar with gradient
                rx.avatar(
                    name=self.agent_name[:2],
                    bg=self._get_gradient_color(),
                    size="lg"
                ),
                rx.vstack(
                    rx.heading(self.agent_name, size="md"),
                    rx.text(f"Tier: {self.tier}", color="gray"),
                    rx.text(f"Last active: {self.last_active}", size="sm"),
                    align_items="start",
                    spacing="1",
                ),
                spacing="4",
            ),
            # Status badge (from common components)
            rx.badge(
                self.status,
                color_scheme=self._get_status_color(),
                variant="solid"
            ),
            # Action buttons
            rx.menu(
                rx.menu_button("Actions", size="sm"),
                rx.menu_list(
                    rx.menu_item("Start", on_click=lambda: AgentState.start_agent(self.agent_id)),
                    rx.menu_item("Stop", on_click=lambda: AgentState.stop_agent(self.agent_id)),
                    rx.menu_item("Restart", on_click=lambda: AgentState.restart_agent(self.agent_id)),
                    rx.menu_divider(),
                    rx.menu_item("View Logs", on_click=lambda: rx.redirect(f"/logs?agent={self.agent_id}")),
                ),
            ),
            width="100%",
            padding="4",
            border_radius="lg",
            _hover={"transform": "translateY(-4px)", "box_shadow": "0 0 20px rgba(0, 242, 254, 0.3)"},
        )
    
    def _get_status_color(self) -> str:
        """Map agent status to badge color"""
        status_colors = {
            "RUNNING": "green",
            "DEPLOYED": "blue",
            "STOPPED": "gray",
            "ERRORED": "red",
            "PROVISIONED": "yellow",
            "DRAFT": "gray",
        }
        return status_colors.get(self.status, "gray")
    
    def _get_gradient_color(self) -> str:
        """Get gradient color based on agent name"""
        gradients = ["blue.500", "purple.500", "cyan.500", "pink.500"]
        return gradients[hash(self.agent_name) % len(gradients)]
```

**Story 2.2.2: Context-Based Observability (8 pts)**
- Global context selector component
- Filter all pages by selected agent
- Persistent context (localStorage)
- Quick actions menu (view logs, restart, configure)

**Pages**:
- `pages/Agents.tsx` - Agent list with state machine
- Enhanced: All observability pages with context selector

**Database Schema**:
```sql
CREATE TABLE agent_states (
  id UUID PRIMARY KEY,
  agent_id VARCHAR(100) NOT NULL,
  state VARCHAR(50) NOT NULL,
  previous_state VARCHAR(50),
  metadata JSONB,
  triggered_by VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Success Criteria**:
- [ ] Agent state transitions working with validation
- [ ] Context selector on all 6 pages (logs, alerts, events, metrics, diagnostics, agents)
- [ ] 80%+ operators use context selector daily

---

### **PHASE 3: AGENT LIFECYCLE (Weeks 5-7) - 47 Points**

#### Epic 3.1: Single Agent Operations (Story 5.1.2)
**Points**: 21  
**Duration**: 2 weeks  
**Team**: 2 developers

**Features**:
- **8 Lifecycle Actions**:
  - Provision (DRAFT → PROVISIONED)
  - Deploy (PROVISIONED → DEPLOYED)
  - Start (DEPLOYED → RUNNING)
  - Stop (RUNNING → STOPPED)
  - Suspend (RUNNING → SUSPENDED)
  - Resume (SUSPENDED → RUNNING)
  - Restart (RUNNING → RUNNING)
  - Revoke (ANY → REVOKED)

- **UI Components**:
  - Action dropdown menu per agent card
  - Confirmation modals with impact preview
  - Loading states during transitions
  - Success/error notifications
  - Undo capability (where applicable)

**APIs**:
```
POST /api/platform/agents/{agent_id}/provision
POST /api/platform/agents/{agent_id}/deploy
POST /api/platform/agents/{agent_id}/start
POST /api/platform/agents/{agent_id}/stop
POST /api/platform/agents/{agent_id}/suspend
POST /api/platform/agents/{agent_id}/resume
POST /api/platform/agents/{agent_id}/restart
POST /api/platform/agents/{agent_id}/revoke
```

#### Epic 3.2: Bulk Operations (Story 5.1.3)
**Points**: 13  
**Duration**: 1 week  
**Team**: 1 developer

**Features**:
- Multi-select checkbox on agent cards
- Bulk action toolbar (deploy all, start all, stop all, restart errored)
- Progress tracking modal with live updates
- Summary report (success/failed counts)
- Rollback on partial failure option

**UI Flow**:
1. Select multiple agents (checkboxes)
2. Choose bulk action from toolbar
3. Confirm with impact preview
4. Watch progress in modal (WebSocket updates)
5. Review summary report

#### Epic 3.3: Infrastructure Deployment (Story 5.1.4)
**Points**: 13  
**Duration**: 1 week  
**Team**: 1 developer

**Features**:
- Docker container deployment
- Kubernetes pod management
- Health check integration
- Auto-restart on failure
- Resource management (CPU, memory limits)
- Volume mounting for persistence

**Integration**:
- Docker API for local development
- Kubernetes API for production
- Health probes (liveness, readiness)
- Log aggregation setup

**Success Criteria**:
- [ ] Deploy 14 agents in <5 minutes
- [ ] 99.9% deployment success rate
- [ ] Auto-restart on crash within 30s
- [ ] Resource limits enforced

---

### **PHASE 4: REAL-TIME & MONITORING (Weeks 8-10) - 68 Points**

#### Epic 4.1: Real-Time Status Updates (Story 5.1.5)
**Points**: 13  
**Duration**: 1 week  
**Team**: 1 developer

**Features**:
- WebSocket streaming of agent state changes
- Real-time health status updates
- Bulk operation progress streaming
- Auto-refresh disabled (replaced by WebSocket)
- Connection status indicator

**Events**:
```typescript
// Agent state changed
ws.on('agent:state_changed', {agent_id, old_state, new_state, timestamp})

// Health update
ws.on('agent:health_update', {agent_id, health, metrics, timestamp})

// Bulk operation progress
ws.on('bulk_op:progress', {operation_id, completed, total, failed, status})
```

#### Epic 4.2: Error Handling & Recovery (Story 5.1.6)
**Points**: 13  
**Duration**: 1 week  
**Team**: 1 developer

**Features**:
- Error classification (transient, permanent, configuration, dependency)
- Root cause analysis with suggested actions
- One-click recovery actions
- Error history and patterns
- Automated recovery workflows

**Error Panel UI**:
```
❌ Agent Failed to Start
├─ Root Cause: Port 8080 already in use
├─ Suggested Actions:
│  • Change port to 8081 (recommended)
│  • Stop conflicting service
│  • Contact DevOps if persistent
└─ [Fix Automatically] [Change Port] [View Logs]
```

#### Epic 4.3: Queue Monitoring (Story 5.1.8)
**Points**: 13  
**Duration**: 1 week  
**Team**: 1 developer

**Features**:
- Queue list view with health status
- Dead Letter Queue (DLQ) panel
- Message inspector with JSON viewer
- Retry failed messages
- Flow diagram (producer → consumer)
- Real-time throughput metrics

**Pages**:
- `pages/Queues.tsx` - New page for queue monitoring

**Metrics**:
- Messages pending
- Throughput (msg/sec)
- Consumer lag
- Error rate
- DLQ message count

#### Epic 4.4: Orchestration Monitoring (Story 5.1.9)
**Points**: 21  
**Duration**: 2 weeks  
**Team**: 2 developers

**Features**:
- Workflow timeline visualization
- Gantt chart for parallel steps
- Step details (status, duration, dependencies, logs)
- Action controls (pause, resume, cancel, retry, rollback)
- SLA monitoring with auto-rollback
- Dependency graph visualization

**Pages**:
- `pages/Orchestration.tsx` - New page for workflow tracking

**UI Layout**:
```
┌─────────────────────────────────────────────┐
│ Workflow: Customer Onboarding              │
│ Status: Running (Step 3 of 5)              │
├─────────────────────────────────────────────┤
│ Timeline                    Gantt Chart     │
│ ✓ Step 1: Provision [2s]   ████░░░░░░      │
│ ✓ Step 2: Configure [5s]   ░░░░████░░      │
│ ⏳ Step 3: Deploy [running] ░░░░░░░░██      │
│ ⏸ Step 4: Test [pending]    ░░░░░░░░░░      │
│ ⏸ Step 5: Activate [pending]░░░░░░░░░░      │
└─────────────────────────────────────────────┘
```

**Success Criteria**:
- [ ] 100% workflow visibility
- [ ] <5s workflow list load time
- [ ] 95%+ SLA compliance
- [ ] <2s from issue to alert

---

### **PHASE 5: ADVANCED OPERATIONS (Weeks 11-14) - 89 Points**

#### Epic 5.1: Agent Factory (Story 5.1.10)
**Points**: 34  
**Duration**: 3 weeks  
**Team**: 2 developers

**Goal**: Wizard to create new agents from templates with sandbox testing

**6 Agent Templates**:
1. **Memory Agent** - Short-term + long-term memory
2. **Orchestration Agent** - Multi-step workflows
3. **API Agent** - External API integration
4. **Data Agent** - Data processing pipelines
5. **Monitoring Agent** - Health checks + alerting
6. **Blank Agent** - Start from scratch

**Wizard Steps**:
1. **Choose Template** - Card selection with descriptions
2. **Configure Agent** - Form with validation
   - Name, description, tier
   - Capabilities, specializations
   - Resource limits (CPU, memory)
   - Environment variables
   - Dependencies
3. **Test in Sandbox** - Preview agent in isolated environment
   - Run test tasks
   - View logs
   - Check performance
4. **Provision Infrastructure** - Automated setup
   - Docker container creation
   - Message queue setup
   - Storage allocation
   - Monitoring configuration
5. **Review & Deploy** - Final confirmation
   - Cost estimate
   - Resource summary
   - Deployment timeline
6. **Monitor Deployment** - Real-time progress
   - Provisioning status
   - Health checks
   - First successful task

**Pages**:
- `pages/Factory.tsx` - Agent creation wizard

**APIs**:
```
GET  /api/platform/factory/templates
POST /api/platform/factory/validate
POST /api/platform/factory/test-sandbox
POST /api/platform/factory/agents
GET  /api/platform/factory/cost-estimate
```

**Success Criteria**:
- [ ] <5 minutes from start to production agent
- [ ] 100% config validation (no runtime errors)
- [ ] 90% agents use templates (not blank)
- [ ] <$2/month per agent operational cost

#### Epic 5.2: Agent Servicing (Story 5.1.11)
**Points**: 34  
**Duration**: 3 weeks  
**Team**: 2 developers

**Goal**: Zero-downtime agent upgrades with rollback capability

**Deployment Strategies**:
1. **Blue-Green** - Deploy new version, switch traffic
2. **Canary** - Gradual rollout (10% → 50% → 100%)
3. **Rolling** - Update instances one-by-one

**Upgrade Wizard (6 Steps)**:
1. **Plan** - Select agents and target version
2. **Backup** - Snapshot current state
3. **Deploy** - New version deployment
4. **Test** - Health checks and smoke tests
5. **Cutover** - Traffic switch to new version
6. **Verify** - Monitor for issues

**Features**:
- Version management dashboard
- Upgrade scheduling (maintenance windows)
- Automatic rollback on failure
- Hot configuration patching (no restart)
- A/B testing during canary rollout
- Resource scaling during upgrade

**Pages**:
- `pages/Servicing.tsx` - Agent upgrade management

**Rollback System**:
- Automatic rollback triggers:
  - Health check failure
  - Error rate > 5%
  - Latency increase > 50%
  - Manual trigger
- Rollback time: <30 seconds
- State restoration from backup

**Success Criteria**:
- [ ] 0 downtime during upgrades
- [ ] <10 minutes upgrade duration
- [ ] <30 seconds rollback time
- [ ] 100% health checks pass post-upgrade

#### Epic 5.3: Technical Help Desk (Story 5.1.12)
**Points**: 21  
**Duration**: 2 weeks  
**Team**: 2 developers

**Goal**: Customer-centric diagnostics with AI-powered root cause analysis

**Features**:
- **Customer Search** - Find customers by email, company, or agent usage
- **Customer Overview** - Profile, agents, subscription, activity
- **Issue Detective** (AI-powered):
  - Analyze symptoms
  - Root cause analysis (90% confidence)
  - Suggested fixes with priority
  - Past similar issues
- **Agent Interaction Timeline** - Last 50 interactions chronologically
- **Quick Actions Panel**:
  - Restart agent
  - Clear cache
  - Reset trial
  - Resend notification email
  - Grant temporary access
- **Playbook Library** - Common issues with resolution steps
  - Agent not responding
  - Slow performance
  - Authentication errors
  - Trial not activating
  - Payment failures
- **Ticket Integration** - Zendesk/Jira sync

**Pages**:
- `pages/HelpDesk.tsx` - Customer support interface

**Issue Detective Flow**:
```
1. Operator enters: "Customer reports agent not responding"
2. AI analyzes:
   - Agent health logs
   - Recent errors
   - Queue backlogs
   - Resource usage
3. Returns diagnosis:
   ⚠️ Root Cause: Queue backlog (1200 messages)
   🎯 Confidence: 92%
   ✅ Recommended Fix: Scale up workers (2 → 5)
   📝 Similar Issues: 3 in past week (all resolved by scaling)
4. One-click apply fix
```

**Success Criteria**:
- [ ] 90% issues diagnosed automatically
- [ ] <2 minutes from search to diagnosis
- [ ] 80% issues resolved via playbooks
- [ ] 95%+ customer satisfaction with support

---

## 📊 Complete Story Breakdown

### All Stories by Phase

| Phase | Story | Points | Duration | Priority |
|-------|-------|--------|----------|----------|
| **1** | 5.1.0 Common Components | 13 | 2 weeks | P0 |
| **2** | 2.1 Auth & Dashboard | 8 | 1 week | P0 |
| **2** | 5.1.1 State Machine | 13 | 1 week | P0 |
| **2** | 5.1.7 Context Observability | 8 | 1 week | P1 |
| **3** | 5.1.2 Single Agent Actions | 21 | 2 weeks | P0 |
| **3** | 5.1.3 Bulk Operations | 13 | 1 week | P1 |
| **3** | 5.1.4 Infrastructure Deploy | 13 | 1 week | P0 |
| **4** | 5.1.5 Real-Time WebSocket | 13 | 1 week | P1 |
| **4** | 5.1.6 Error Handling | 13 | 1 week | P1 |
| **4** | 5.1.8 Queue Monitoring | 13 | 1 week | P0 |
| **4** | 5.1.9 Orchestration Monitoring | 21 | 2 weeks | P0 |
| **5** | 5.1.10 Agent Factory | 34 | 3 weeks | P0 |
| **5** | 5.1.11 Agent Servicing | 34 | 3 weeks | P0 |
| **5** | 5.1.12 Technical Help Desk | 21 | 2 weeks | P1 |

**Total**: 14 stories, 246 points, 14 weeks

### Priority Distribution
- **P0 (Critical)**: 10 stories, 195 points (79%)
- **P1 (High)**: 4 stories, 51 points (21%)

---

## 🎯 Success Metrics

### Operational KPIs
- **Deployment Time**: 30 min → 5 min (83% reduction)
- **MTTR**: 20 min → 2 min (90% reduction)
- **Agent Uptime**: 99.9% target
- **Recovery Success Rate**: 80% self-service
- **Operator Efficiency**: 1 operator manages 14+ agents

### User Experience KPIs
- **Portal Load Time**: <2 seconds
- **WebSocket Uptime**: 99.9%
- **Real-time Update Latency**: <100ms
- **Component Response Time**: <50ms
- **Error Recovery Time**: <30 seconds

### Development KPIs
- **Test Coverage**: >85% on all components
- **Type Safety**: 100% Python type hint coverage
- **Component Reuse**: 100% (no duplication)
- **Reflex Build Time**: <10 seconds (auto-compile)
- **Hot Reload**: <500ms

---

## 📁 File Structure Overview

```
PlatformPortal/
├── frontend/                    # Reflex application (Pure Python!)
│   ├── app.py                   # Main Reflex app entry point
│   ├── rxconfig.py              # Reflex configuration
│   ├── components/              # 15+ reusable components (Python)
│   │   ├── common/
│   │   │   ├── status_badge.py
│   │   │   ├── metrics_widget.py
│   │   │   ├── timeline.py
│   │   │   ├── progress_tracker.py
│   │   │   └── context_selector.py
│   │   ├── agents/
│   │   │   ├── agent_card.py
│   │   │   ├── agent_actions.py
│   │   │   └── agent_state_machine.py
│   │   └── layout/
│   │       ├── header.py
│   │       ├── sidebar.py
│   │       └── theme_toggle.py
│   ├── pages/                   # 10 page components (Python)
│   │   ├── dashboard.py
│   │   ├── agents.py
│   │   ├── events.py
│   │   ├── metrics.py
│   │   ├── logs.py
│   │   ├── diagnostics.py
│   │   ├── alerts.py
│   │   ├── factory.py
│   │   ├── servicing.py
│   │   └── helpdesk.py
│   ├── state/                   # Reflex state management (Python)
│   │   ├── auth_state.py
│   │   ├── agent_state.py
│   │   ├── metrics_state.py
│   │   └── theme_state.py
│   ├── services/                # Backend API integration (Python)
│   │   ├── api.py
│   │   ├── websocket.py
│   │   └── auth.py
│   ├── theme/                   # WAOOAW theme (Python)
│   │   ├── colors.py
│   │   ├── dark.py
│   │   └── light.py
│   ├── models/                  # Data models (Python dataclasses)
│   │   ├── agent.py
│   │   ├── user.py
│   │   └── metrics.py
│   └── assets/                  # Static files
│       ├── Waooaw-Logo.png      # Existing logo
│       └── favicon.ico
│
├── backend/                     # FastAPI (enhanced)
│   └── app/
│       ├── main.py              # Enhanced with new endpoints
│       ├── auth/                # OAuth2 (keep existing)
│       └── services/            # 10+ new services
│
├── docs/
│   └── stories/                 # Implementation guides per phase
│
├── requirements.txt             # All Python dependencies
└── README.md
```

**Key Differences from React**:
- ✅ All `.py` files instead of `.tsx`/`.ts`
- ✅ No `package.json`, `tsconfig.json`, `vite.config.ts`
- ✅ Reflex handles bundling and compilation automatically
- ✅ Single `requirements.txt` for all dependencies
- ✅ No separate build step - Reflex compiles on the fly

---

## 🔄 Migration Strategy

### Current Portal → New Portal

**Week 1-2: Parallel Development**
- Keep current portal running
- Build new portal in PlatformPortal/ folder
- Share backend APIs

**Week 3-4: Gradual Migration**
- Internal team uses new portal
- Gather feedback
- Fix critical issues

**Week 5+: Full Cutover**
- All operators switch to new portal
- Archive old portal code
- Update documentation

**Rollback Plan**:
- Current portal remains accessible for 4 weeks
- Can revert if critical issues found
- Zero impact on backend services

---

## 🚧 Risk Management

### High Risks
1. **WebSocket Stability** - Mitigate with auto-reconnect + polling fallback
2. **Docker Security** - Use K8s API with RBAC instead of Docker socket
3. **State Machine Races** - Implement optimistic locking

### Medium Risks
1. **Bulk Operations Resource Exhaustion** - Rate limiting, max parallel = 5
2. **Complex UI State** - Use Zustand with proper patterns
3. **Integration Issues** - E2E tests after each phase

### Low Risks
1. **Theme System** - Port existing CSS variables
2. **OAuth Migration** - Working pattern exists
3. **Component Library** - Clear specifications available

---

## 📋 Next Steps

### Pre-Development (Week 0)
- [x] Review and approve this plan
- [x] Choose final framework (**Reflex - Pure Python**)
- [ ] Setup GitHub project board
- [ ] Create PlatformPortal/ folder structure
- [ ] Archive old portal code (frontend-old/)

### Week 1 Kickoff
- [ ] Install Reflex (`pip install reflex`)
- [ ] Initialize Reflex project (`reflex init`)
- [ ] Configure Reflex theme with WAOOAW colors (dark/light)
- [ ] Setup OAuth2 integration with Reflex
- [ ] Configure hot reload and development server
- [ ] Begin Story 5.1.0 (Common Components in Python)
- [ ] Setup Python linting (Black, Ruff, mypy)

### Weekly Cadence
- Daily standup (15 min)
- Mid-week check-in (30 min)
- Friday demo to stakeholders (1 hour)
- Sprint planning every 2 weeks

---

## 📊 Resource Requirements

### Team
- **Frontend Developer** (Python + Reflex expert)
- **Backend Developer** (FastAPI/Python expert)
- **Full-stack Developer** (overlap, testing, integration)

**Note**: All roles require Python expertise only - no JavaScript/TypeScript skills needed!

### Infrastructure
- **Development**: GitHub Codespaces (existing)
- **CI/CD**: GitHub Actions
- **Deployment**: Azure App Service (existing)
- **Database**: PostgreSQL (Supabase, existing)
- **Cache**: Redis (existing)
- **Monitoring**: Application Insights (Azure)

### Budget
- **Infrastructure**: $160/month (no change)
- **Development Tools**: $0 (using GitHub free tier)
- **Total**: Within existing $200/month budget ✅

---

## ✅ Definition of Done

### Per Story
- [ ] All acceptance criteria met
- [ ] Unit tests written (>85% coverage)
- [ ] Integration tests passing
- [ ] Python type hints complete
- [ ] Documentation updated
- [ ] Code review approved
- [ ] Deployed to staging
- [ ] Demo to stakeholders

### Per Phase
- [ ] All stories in phase complete
- [ ] E2E tests passing
- [ ] Performance benchmarks met
- [ ] Security review passed
- [ ] Accessibility audit complete
- [ ] Stakeholder approval

### Epic Complete (Week 14)
- [ ] All 14 stories delivered
- [ ] Production deployment successful
- [ ] 3+ operators trained
- [ ] All metrics within targets
- [ ] Handover documentation complete
- [ ] Old portal archived

---

## 📞 Stakeholder Communication

### Weekly Updates
- Progress report (stories completed)
- Blockers and risks
- Upcoming milestones
- Demo links

### Monthly Reviews
- ROI analysis (time savings)
- User feedback summary
- Roadmap adjustments
- Success metrics review

---

**Document Status**: ✅ Ready for Review  
**Next Action**: Stakeholder review and approval  
**Timeline Start**: January 6, 2026 (pending approval)  
**Estimated Completion**: April 4, 2026 (14 weeks)

---

*This plan consolidates Epic 4.1 (Maintenance Portal) and Epic 5.1 (Operational Portal) into a comprehensive implementation roadmap for the new Platform Portal.*
