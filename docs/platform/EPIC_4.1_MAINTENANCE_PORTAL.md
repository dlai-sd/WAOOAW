# Epic 4.1: Platform Maintenance Portal

**Status:** PLANNED  
**Priority:** HIGH  
**Version:** v1.1.0  
**Estimated Points:** 55 points  
**Target Completion:** 2 weeks  

## Overview

Build a professional web-based maintenance portal for platform operators to monitor, manage, and maintain the WAOOAW platform. Includes real-time dashboards, agent management, diagnostics, and secure OAuth2 authentication with Google accounts. Deploy on Azure infrastructure.

## Business Value

- **Operational Efficiency:** Centralized platform management reduces maintenance time by 70%
- **Visibility:** Real-time insights into platform health and performance
- **Control:** Manage 22 agents from single interface
- **Security:** Enterprise-grade authentication with Google OAuth2
- **Scalability:** Azure deployment with auto-scaling capabilities

## Architecture Components

1. **Frontend:** HTML5, CSS3, JavaScript (dark theme, responsive)
2. **Backend:** FastAPI + Python 3.11
3. **Authentication:** OAuth2 with Google API
4. **Infrastructure:** Azure App Service, Redis, PostgreSQL
5. **Integration:** Existing Event Bus and Agent ecosystem

---

## Story 1: Authentication & Authorization Foundation

**Points:** 8  
**Priority:** CRITICAL  
**Dependencies:** None  

### Description
Implement OAuth2 authentication with Google API and role-based access control (RBAC) for the maintenance portal.

### Acceptance Criteria
- [ ] OAuth2 flow with Google implemented (login, callback, token management)
- [ ] JWT token generation and validation
- [ ] Role-based access control (Admin, Operator, Viewer)
- [ ] Admin email whitelist configuration
- [ ] Session management (login, logout, token refresh)
- [ ] Protected API endpoints with role checking
- [ ] Audit logging for all authentication events

### Technical Tasks
- Create `backend/app/auth/google_oauth.py` module
- Implement `/auth/login` and `/auth/callback` endpoints
- Create `get_current_user()` dependency
- Implement RBAC decorator `require_role()`
- Add JWT token utilities (create, verify, refresh)
- Create audit logging for auth events
- Write tests for auth flows (20+ test cases)

### Testing Checklist
- [ ] Successful Google OAuth2 login flow
- [ ] Token validation and expiration
- [ ] Role-based access enforcement
- [ ] Logout clears session properly
- [ ] Unauthorized access returns 401
- [ ] Insufficient permissions return 403
- [ ] Audit logs capture all auth events

---

## Story 2: Dashboard Overview UI & API

**Points:** 8  
**Priority:** HIGH  
**Dependencies:** Story 1  

### Description
Create main dashboard showing system health, agent status, key metrics, and recent alerts.

### Acceptance Criteria
- [ ] Dashboard page displays system status (Platform, Redis, Event Bus)
- [ ] Real-time key metrics (events/sec, tasks completed, error rate)
- [ ] Agent status summary (online/degraded/offline count)
- [ ] Top 5 agents with status, task count, uptime
- [ ] Recent alerts (last 10) with severity indicators
- [ ] Auto-refresh every 10 seconds
- [ ] Responsive layout (desktop and tablet)

### API Endpoints
- `GET /api/maintenance/dashboard/status` - System status
- `GET /api/maintenance/dashboard/metrics` - Key metrics (last 1 hour)
- `GET /api/maintenance/dashboard/agents-summary` - Agent overview
- `GET /api/maintenance/dashboard/alerts` - Recent alerts

### Technical Tasks
- Create `backend/app/api/maintenance/dashboard.py`
- Implement dashboard HTML page (`frontend/admin/dashboard.html`)
- Create dashboard CSS (`frontend/admin/css/dashboard.css`)
- Implement dashboard JavaScript (`frontend/admin/js/dashboard.js`)
- Connect to Event Bus for live metrics
- Query Redis for agent status
- Write integration tests for dashboard APIs

### Testing Checklist
- [ ] Dashboard loads in < 2 seconds
- [ ] All metrics display correctly
- [ ] Auto-refresh works without page reload
- [ ] Error states handled gracefully
- [ ] Responsive on different screen sizes

---

## Story 3: Agent Management Interface

**Points:** 8  
**Priority:** HIGH  
**Dependencies:** Story 1  

### Description
Build comprehensive agent management interface to view, start, stop, restart, and monitor all 22 platform agents.

### Acceptance Criteria
- [ ] List all agents with status, task count, uptime
- [ ] Filter agents by status (online/degraded/offline)
- [ ] Search agents by name
- [ ] Start/Stop/Restart individual agents
- [ ] View detailed agent info (capabilities, config, health)
- [ ] Bulk operations (restart all, health check all)
- [ ] Run agent roll call to verify responses
- [ ] View agent logs (last 100 lines)

### API Endpoints
- `GET /api/maintenance/agents` - List all agents
- `GET /api/maintenance/agents/{id}` - Agent details
- `POST /api/maintenance/agents/{id}/restart` - Restart agent
- `POST /api/maintenance/agents/{id}/start` - Start agent
- `POST /api/maintenance/agents/{id}/stop` - Stop agent
- `POST /api/maintenance/agents/roll-call` - Run roll call
- `GET /api/maintenance/agents/{id}/logs` - Agent logs

### Technical Tasks
- Create `backend/app/api/maintenance/agents.py`
- Implement agent control via Event Bus
- Create agent management HTML/CSS/JS
- Add agent status monitoring service
- Integrate with existing roll call script
- Write tests for agent operations

### Testing Checklist
- [ ] All 22 agents listed correctly
- [ ] Agent operations execute successfully
- [ ] Roll call returns all agent responses
- [ ] Error handling for failed operations
- [ ] Audit logs capture agent operations

---

## Story 4: Event Bus Monitor & Diagnostics

**Points:** 5  
**Priority:** MEDIUM  
**Dependencies:** Story 1  

### Description
Real-time monitoring of Event Bus activity including throughput, subscriptions, and message flow.

### Acceptance Criteria
- [ ] Display real-time Event Bus metrics
- [ ] Show throughput graph (last 5 minutes)
- [ ] List active subscriptions by pattern
- [ ] Show subscription health (message delivery rates)
- [ ] Publish test messages for diagnostics
- [ ] View message routing paths
- [ ] Detect and alert on dead subscriptions

### API Endpoints
- `GET /api/maintenance/event-bus/metrics` - Current metrics
- `GET /api/maintenance/event-bus/subscriptions` - Active subscriptions
- `POST /api/maintenance/event-bus/test-message` - Send test event
- `WebSocket /api/maintenance/event-bus/stream` - Live metrics stream

### Technical Tasks
- Create `backend/app/api/maintenance/event_bus.py`
- Integrate with existing Event Bus
- Create real-time chart visualization
- Implement WebSocket for live updates
- Add subscription health monitoring
- Write diagnostic test tools

### Testing Checklist
- [ ] Metrics update in real-time
- [ ] Test messages flow correctly
- [ ] Subscription list is accurate
- [ ] WebSocket handles disconnections

---

## Story 5: System Diagnostics & Testing Suite

**Points:** 5  
**Priority:** MEDIUM  
**Dependencies:** Story 1  

### Description
Interface to run existing test suites (smoke test, full platform test, roll call) from the portal with live progress and results.

### Acceptance Criteria
- [ ] List all available diagnostic tests
- [ ] Run tests from UI (one-click execution)
- [ ] Display test progress in real-time
- [ ] Show test results (passed/failed/skipped)
- [ ] View test history (last 20 runs)
- [ ] Schedule automated test runs
- [ ] Export test reports

### API Endpoints
- `GET /api/maintenance/diagnostics/tests` - List available tests
- `POST /api/maintenance/diagnostics/tests/{id}/run` - Execute test
- `GET /api/maintenance/diagnostics/runs/{run_id}` - Test run status
- `GET /api/maintenance/diagnostics/history` - Test history

### Technical Tasks
- Create `backend/app/api/maintenance/diagnostics.py`
- Integrate existing test scripts (smoke, full, roll call)
- Create test execution service
- Implement test result storage
- Build test UI with progress indicators
- Write scheduler for automated tests

### Testing Checklist
- [ ] All test scripts execute correctly
- [ ] Test progress updates in real-time
- [ ] Results display accurately
- [ ] Test history persists correctly

---

## Story 6: Performance Metrics & Monitoring

**Points:** 5  
**Priority:** MEDIUM  
**Dependencies:** Story 2  

### Description
Advanced performance monitoring showing throughput, latency, resource usage, and identifying bottlenecks.

### Acceptance Criteria
- [ ] Display throughput metrics (events/sec, tasks/sec, requests/sec)
- [ ] Show latency percentiles (P50, P95, P99)
- [ ] Monitor resource usage (CPU, memory, disk, network)
- [ ] Identify hotspots (agents consuming most resources)
- [ ] Historical trend charts (last 24 hours)
- [ ] Customizable time ranges
- [ ] Export metrics data

### API Endpoints
- `GET /api/maintenance/metrics/throughput` - Throughput data
- `GET /api/maintenance/metrics/latency` - Latency statistics
- `GET /api/maintenance/metrics/resources` - Resource usage
- `GET /api/maintenance/metrics/hotspots` - Resource hotspots

### Technical Tasks
- Create `backend/app/api/maintenance/metrics.py`
- Integrate with existing metrics collection
- Create chart visualizations (Chart.js)
- Implement metrics aggregation
- Add time range filtering
- Write metrics export functionality

### Testing Checklist
- [ ] Metrics accurately reflect platform state
- [ ] Charts render correctly
- [ ] Time range filtering works
- [ ] Export produces valid data

---

## Story 7: Logs & Debugging Interface

**Points:** 5  
**Priority:** MEDIUM  
**Dependencies:** Story 1  

### Description
Centralized log viewing with filtering, search, and real-time streaming capabilities.

### Acceptance Criteria
- [ ] Display recent errors and warnings
- [ ] Filter logs by agent, severity, time range
- [ ] Search logs by keyword
- [ ] Stream live logs (tail -f style)
- [ ] Export log archives
- [ ] Highlight critical issues
- [ ] Link logs to related incidents

### API Endpoints
- `GET /api/maintenance/logs` - Fetch logs with filters
- `GET /api/maintenance/logs/search` - Search logs
- `SSE /api/maintenance/logs/stream` - Live log stream
- `POST /api/maintenance/logs/export` - Export logs

### Technical Tasks
- Create `backend/app/api/maintenance/logs.py`
- Implement log aggregation from multiple sources
- Create log viewer UI with filtering
- Implement Server-Sent Events for live logs
- Add log export functionality
- Write log parsing and highlighting

### Testing Checklist
- [ ] Logs display correctly
- [ ] Filtering works accurately
- [ ] Search returns relevant results
- [ ] Live streaming works without lag
- [ ] Export produces complete archives

---

## Story 8: Alerts & Incident Management

**Points:** 3  
**Priority:** LOW  
**Dependencies:** Story 2, Story 6  

### Description
Alert management system showing active issues, incident history, and resolution tracking.

### Acceptance Criteria
- [ ] Display active alerts by severity (critical/warning/info)
- [ ] Show alert details (timestamp, agent, description)
- [ ] Acknowledge alerts
- [ ] View incident history (last 30 days)
- [ ] Track resolution status
- [ ] Link alerts to documentation/runbooks

### API Endpoints
- `GET /api/maintenance/alerts` - Active alerts
- `POST /api/maintenance/alerts/{id}/acknowledge` - Acknowledge alert
- `GET /api/maintenance/incidents` - Incident history
- `GET /api/maintenance/incidents/{id}` - Incident details

### Technical Tasks
- Create `backend/app/api/maintenance/alerts.py`
- Implement alert detection logic
- Create alert notification system
- Build incident tracking database
- Design alerts UI
- Write alert tests

### Testing Checklist
- [ ] Alerts trigger correctly
- [ ] Acknowledgement persists
- [ ] Incident history is accurate

---

## Story 9: Azure Deployment Infrastructure

**Points:** 8  
**Priority:** CRITICAL  
**Dependencies:** Stories 1-8  

### Description
Deploy complete platform maintenance portal to Azure with proper configuration, security, and CI/CD pipeline.

### Acceptance Criteria
- [ ] Azure App Service configured (Linux, Python 3.11)
- [ ] Azure Redis Cache provisioned and connected
- [ ] Azure Database for PostgreSQL set up
- [ ] Azure Key Vault for secrets management
- [ ] Environment variables configured
- [ ] SSL/TLS enabled with custom domain
- [ ] CI/CD pipeline automated (Azure DevOps or GitHub Actions)
- [ ] Health checks and monitoring enabled
- [ ] Auto-scaling configured
- [ ] Backup policies implemented

### Azure Resources Required
- App Service Plan (P1V2 or higher)
- Azure Redis Cache (Standard C1)
- Azure Database for PostgreSQL (General Purpose)
- Azure Key Vault
- Azure Storage (logs, backups)
- Azure Monitor + Application Insights
- Azure Front Door (optional, for CDN/WAF)

### Technical Tasks
- Create Azure resource group
- Provision all Azure services
- Configure App Service deployment
- Set up Key Vault with secrets
- Create CI/CD pipeline YAML
- Configure environment variables
- Set up Application Insights
- Configure auto-scaling rules
- Implement backup automation
- Write deployment documentation

### Deployment Checklist
- [ ] All Azure resources provisioned
- [ ] Application deploys successfully
- [ ] Database migrations run correctly
- [ ] Redis connection works
- [ ] OAuth2 callback URL configured
- [ ] Environment variables set correctly
- [ ] SSL certificate valid
- [ ] Health endpoint returns 200
- [ ] CI/CD pipeline executes successfully
- [ ] Monitoring shows metrics

---

## Epic Summary

| Story | Description | Points | Priority | Dependencies |
|-------|-------------|--------|----------|--------------|
| 1 | Authentication & Authorization | 8 | CRITICAL | None |
| 2 | Dashboard Overview | 8 | HIGH | Story 1 |
| 3 | Agent Management | 8 | HIGH | Story 1 |
| 4 | Event Bus Monitor | 5 | MEDIUM | Story 1 |
| 5 | System Diagnostics | 5 | MEDIUM | Story 1 |
| 6 | Performance Metrics | 5 | MEDIUM | Story 2 |
| 7 | Logs & Debugging | 5 | MEDIUM | Story 1 |
| 8 | Alerts & Incidents | 3 | LOW | Stories 2, 6 |
| 9 | Azure Deployment | 8 | CRITICAL | Stories 1-8 |
| **TOTAL** | | **55** | | |

---

## Prerequisites

### Before Starting:
- [ ] Azure subscription active and accessible
- [ ] Google OAuth2 credentials obtained (Client ID + Secret)
- [ ] Domain name ready for production (e.g., admin.waooaw.com)
- [ ] Azure DevOps or GitHub repository set up
- [ ] Development environment configured
- [ ] Existing Event Bus and agents tested

### Required Credentials:
- **Google Cloud Console:** OAuth 2.0 Client ID and Secret
- **Azure Portal:** Subscription ID and Service Principal
- **Azure Key Vault:** Access policies configured
- **Database:** PostgreSQL admin credentials

---

## Success Metrics

### Technical Metrics:
- Portal loads in < 2 seconds
- 99.9% uptime after deployment
- Real-time updates with < 1 second latency
- All 22 agents manageable from portal
- 100% test coverage for critical paths

### Operational Metrics:
- 70% reduction in manual maintenance time
- 100% visibility into platform health
- < 5 minutes to identify and diagnose issues
- Zero unauthorized access attempts
- Complete audit trail of all operations

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| OAuth2 integration issues | Medium | High | Use Google's official Python library |
| Azure deployment complexity | Medium | High | Follow Azure best practices, use templates |
| Performance at scale | Low | Medium | Implement caching, load testing |
| Security vulnerabilities | Low | Critical | Security audit, penetration testing |
| Cost overruns on Azure | Medium | Medium | Set budget alerts, use auto-scaling |

---

## Next Steps

### Phase 1 (Week 1): Foundation
- Story 1: Authentication ✓
- Story 2: Dashboard ✓
- Story 3: Agent Management ✓
- Story 9: Azure Setup (basic)

### Phase 2 (Week 2): Advanced Features
- Story 4: Event Bus Monitor ✓
- Story 5: Diagnostics ✓
- Story 6: Performance Metrics ✓
- Story 7: Logs & Debugging ✓
- Story 8: Alerts ✓
- Story 9: Production Deployment ✓

### Post-Launch:
- User training and documentation
- Performance optimization
- Feature requests from operators
- Integration with additional Azure services

---

## Notes

This epic builds on existing platform infrastructure (Event Bus, 22 agents, test suites) and provides the missing piece: a professional operator interface. The architecture is designed for extensibility, allowing future features like agent training, visual designer, and advanced analytics to be added as separate modules without disrupting existing functionality.

**Estimated Timeline:** 2 weeks with 2 developers  
**Technology Stack:** FastAPI, Python 3.11, HTML/CSS/JS, Azure  
**Integration Points:** Event Bus, Redis, PostgreSQL, existing agent ecosystem
