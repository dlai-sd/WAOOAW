# Platform Portal (PP) User Journey v1.0

**Version:** 1.0  
**Status:** Complete Specification  
**Created:** January 8, 2026  
**Owner:** WAOOAW Operations Team

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Platform Portal Overview](#platform-portal-overview)
3. [User Roles & Responsibilities](#user-roles--responsibilities)
4. [Lifecycle Stages](#lifecycle-stages)
5. [Component Architecture](#component-architecture)
6. [API Catalog](#api-catalog)
7. [Database Architecture](#database-architecture)
8. [Constitutional Alignment](#constitutional-alignment)
9. [Implementation Roadmap](#implementation-roadmap)

---

## Executive Summary

The **Platform Portal (PP)** is WAOOAW's internal operations hub, designed for the team to monitor, manage, and maintain the AI agent marketplace. Unlike the Customer Portal (CP) which serves external customers, PP is exclusively for WAOOAW employees with @waooaw.com email addresses.

### Key Characteristics

- **Agent-First Design**: UI aids AI agents, not replaces human dashboards
- **Polling-Based**: No real-time streaming; agents trigger data refreshes
- **Constitutional Mandate**: All operations must align with WAOOAW Constitution
- **Separate Architecture**: Independent backend service (PP Gateway on port 8015)
- **7 User Roles**: Hierarchical access (Admin → Manager → Operator → Viewer)
- **Google OAuth**: Restricted to @waooaw.com domain

### By the Numbers

- **9 Core Components** across 4 phases
- **39+ API Endpoints** for operations
- **20+ Database Tables** for PP functionality
- **3 UI Themes**: Dark (#0a0a0a), White, Vibrant Colorful
- **13 Microservices Monitored**: From authentication to payment
- **6-Month Log Retention**: Centralized in ELK Stack

---

## Platform Portal Overview

### Vision

> "A single human enterprise designed, created, maintained and operated by AI Agents"

PP enables one person (the founder) + AI agents to operate WAOOAW at scale. Internal team members are force multipliers, not mandatory dependencies.

### Design Philosophy

**1. Agent-First, Not Human-First**
- Traditional dashboards show data; PP surfaces **actionable intelligence**
- Agents query PP APIs, not humans staring at graphs
- Human operators review agent decisions, don't micromanage

**2. Polling Over Real-Time**
- No WebSockets, Server-Sent Events, or live dashboards
- Agents poll endpoints (every 30s-5min based on SLA)
- Reduces infrastructure complexity, aligns with agent workflows

**3. Constitutional Guardrails**
- PP users have **zero access** to customer core data
- Forensics allowed (read-only agent run logs)
- Force actions (cancel subscription, pause agent) require Admin approval + reason

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Platform Portal (PP)                   │
│                  React SPA + PP Gateway (8015)              │
└─────────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ Google   │   │ Genesis  │   │ Customer │
    │ OAuth    │   │ Agent    │   │ Portal   │
    │ API      │   │ Validator│   │ Backend  │
    └──────────┘   └──────────┘   └──────────┘
          │               │               │
          └───────────────┴───────────────┘
                          ▼
                ┌─────────────────────┐
                │ PostgreSQL + Redis  │
                │ ELK Stack + Grafana │
                └─────────────────────┘
```

**Key Components:**
- **PP Gateway**: FastAPI backend (port 8015), separate from CP backend
- **React SPA**: Frontend with 3 selectable themes
- **Google OAuth**: @waooaw.com domain restriction
- **Genesis Agent**: Constitutional validator (approves agent creation/retuning)
- **PostgreSQL**: 20+ new PP tables (pp_users, pp_tickets, pp_health_checks, etc.)
- **Redis**: Session store (15-day JWT expiry) + caching
- **ELK Stack**: Centralized logging (6-month retention)
- **Prometheus + Grafana**: Metrics and monitoring

---

## User Roles & Responsibilities

### Role Hierarchy

```
Admin (Level 1)
  ├── Subscription Manager (Level 2)
  ├── Agent Orchestrator (Level 2)
  ├── Infrastructure Engineer (Level 2)
  │     ├── Helpdesk Agent (Level 3)
  │     └── Industry Manager (Level 3)
  └── Viewer (Level 4)
```

### 1. Admin

**Access Level:** Full platform control  
**Count:** 1-2 (founder + backup)

**Responsibilities:**
- User management (add/remove users, assign roles)
- Force actions (cancel subscriptions, pause agents)
- Genesis validation overrides (rare emergency cases)
- Constitutional policy updates

**Permissions:**
- `*:*` (all actions)
- Bypass RBAC checks

**Typical Workflows:**
- Review daily platform health report
- Approve agent creation (post-Genesis validation)
- Handle escalated customer issues
- Manage PP user accounts

---

### 2. Subscription Manager

**Access Level:** Subscription and customer lifecycle  
**Count:** 2-3

**Responsibilities:**
- Monitor subscription health (trial conversions, churn)
- Audit agent run forensics (read-only)
- Manage incidents (not tickets, focus on subscription-level issues)
- Proactive outreach (customers with failing agents)

**Permissions:**
- `subscription_management:read`
- `subscription_management:write` (limited: incidents, notes)
- `agent_runs:forensics` (read-only agent logs)
- `incidents:create`, `incidents:manage`

**Typical Workflows:**
- Daily: Check subscriptions with health score < 60
- Weekly: Export agent run metrics for analysis
- Ad-hoc: Investigate customer complaints, create incidents

**Constitutional Constraints:**
- ❌ Cannot access customer core data (industry_data, strategic_plans)
- ❌ Cannot force cancel subscriptions (Admin only)
- ✅ Can view agent run logs (forensics)

---

### 3. Agent Orchestrator

**Access Level:** Agent lifecycle management  
**Count:** 2-3

**Responsibilities:**
- Agent creation workflow (Genesis validation)
- CI/CD pipeline monitoring (GitHub Actions)
- Agent retuning (industry knowledge updates)
- Handoff to service team (operational readiness checklist)

**Permissions:**
- `agent_orchestration:create`, `agent_orchestration:read`
- `agent_retuning:initiate`
- `cicd:read`

**Typical Workflows:**
- Initiate agent creation (5-step workflow)
- Monitor Genesis validation (< 5 min)
- Track CI/CD pipeline (25-35 min)
- Complete handoff checklist (Docker image, runbook, monitoring)
- Retune agents quarterly with new industry knowledge

**Constitutional Gates:**
- Genesis validation required before code generation
- Admin approval required after Genesis for retuning
- Operational readiness checklist 100% complete before production

---

### 4. Infrastructure Engineer

**Access Level:** Platform health and infrastructure  
**Count:** 2-4

**Responsibilities:**
- Monitor microservice health (13 services)
- Manage queues (Temporal, Celery, RabbitMQ)
- Server metrics (CPU, memory, disk)
- Log analysis (ELK Stack, 6-month retention)
- Set alert thresholds

**Permissions:**
- `health_monitoring:read`, `health_monitoring:write`
- `infrastructure:read`, `infrastructure:write`
- `logs:query`

**Typical Workflows:**
- Polling: Check health dashboard every 5 minutes (agent-triggered)
- Alerts: Respond to Slack/email (service down, high error rate)
- On-call: Investigate and resolve incidents
- Weekly: Review server metrics, plan scaling

---

### 5. Helpdesk Agent

**Access Level:** Ticket management  
**Count:** 3-5

**Responsibilities:**
- Handle internal tickets (support, incident, feature_request)
- SLA tracking (critical: 15min response, 4hr resolution)
- Escalate to Infrastructure Engineer or Admin
- Customer-facing support (indirect via Customer Portal)

**Permissions:**
- `helpdesk:read`, `helpdesk:write`
- `tickets:create`, `tickets:assign`, `tickets:update`, `tickets:close`

**Typical Workflows:**
- Monitor ticket queue (filter by priority)
- Respond to tickets within SLA (critical: 15min)
- Escalate if unresolved within SLA window
- Close tickets with resolution notes

**SLA Definitions:**
- **Critical**: 15min response, 4hr resolution
- **High**: 2hr response, 24hr resolution
- **Medium**: 8hr response, 72hr resolution
- **Low**: 24hr response, 1 week resolution

---

### 6. Industry Manager

**Access Level:** Industry knowledge management  
**Count:** 1-2 per industry (3-6 total)

**Responsibilities:**
- Add knowledge sources (API endpoints, RSS feeds)
- Monitor scraping jobs (daily ingestion)
- Review knowledge diffs (version changes)
- Initiate agent retuning (quarterly)

**Permissions:**
- `industry_knowledge:read`, `industry_knowledge:write`
- `knowledge_sources:create`, `knowledge_sources:manage`
- `agent_retuning:initiate` (constitutional approval required)

**Typical Workflows:**
- Add new knowledge source (Google Ads API, HubSpot)
- Schedule daily scraping (2 AM IST)
- Review monthly knowledge diff (embeddings added/modified)
- Initiate retuning proposal (Genesis validates)

**Industries:**
- Marketing (Google Ads, Meta Ads, HubSpot)
- Education (NCERT, JEE/NEET, Khan Academy)
- Sales (Salesforce, LinkedIn Sales Navigator)

---

### 7. Viewer

**Access Level:** Read-only  
**Count:** Unlimited (future hires, stakeholders)

**Responsibilities:**
- View dashboards (health, subscriptions)
- Read tickets (cannot create/update)
- Observe agent creation workflows

**Permissions:**
- `*:read` (all read permissions)
- No write/delete permissions

**Typical Workflows:**
- Review platform health for reporting
- Monitor subscription metrics
- Observe team workflows

---

## Lifecycle Stages

### Stage 1: Authentication & Authorization (Phase 1)

**User Goal:** Securely access Platform Portal

**Workflow:**
1. User navigates to `https://portal.waooaw.com`
2. Click "Sign in with Google" button
3. Redirect to Google OAuth (Workspace account required)
4. Google callback returns authorization code
5. PP Gateway exchanges code for Google tokens
6. Validate email domain (@waooaw.com)
7. Check `pp_users` table (exists? proceed : reject)
8. Generate JWT (HS256, 15-day expiry) with user roles
9. Store session in Redis (multi-device support, max 5 sessions)
10. Redirect to dashboard (role-based rendering)

**Components:**
- `component_pp_authentication_oauth.yml`
- `component_pp_rbac_system.yml`

**APIs:**
- `POST /pp/v1/auth/login`
- `POST /pp/v1/auth/callback`
- `POST /pp/v1/auth/refresh`
- `POST /pp/v1/auth/logout`

**Constitutional Compliance:**
- ✅ Domain restriction enforces employee-only access
- ✅ JWT includes roles for RBAC enforcement
- ✅ Session expiry prevents stale access

---

### Stage 2: Health Monitoring (Phase 1)

**User Goal:** Monitor platform health and troubleshoot issues

**Roles:** Infrastructure Engineer (primary), Admin, Viewer

**Workflow:**
1. Navigate to Health Dashboard
2. View overview (13 microservices status)
3. Drill into microservice details (authentication, payment, agent-execution, etc.)
4. Check queue metrics (Temporal workflows, Celery tasks, RabbitMQ messages)
5. Query logs (ELK Stack, 6-month retention, filters: service, level, time range)
6. Set alert thresholds (service down, high error rate, queue backlog, CPU/memory)
7. Receive alerts (Slack #platform-health, email)

**Dashboard Sections:**
- **Overview**: Service count, uptime %, recent alerts
- **Microservices**: 13 services with status (🟢 up, 🔴 down), response time, error rate
- **Queues**: Temporal (pending/running workflows), Celery (task queue depth), RabbitMQ (message count)
- **Logs**: Elasticsearch query interface (filters, date range, log level)

**Monitored Microservices:**
1. authentication-service
2. customer-portal-backend
3. agent-execution-engine
4. orchestration-service
5. payment-service
6. notification-service
7. analytics-service
8. helpdesk-service
9. subscription-service
10. marketplace-service
11. trial-management-service
12. webhook-service
13. genesis-validator-service

**Alert Types:**
- **Service Down**: No heartbeat for 2 minutes → Critical alert
- **High Error Rate**: >5% errors for 5 minutes → Warning
- **Queue Backlog**: Temporal workflows pending >100 → Warning
- **High CPU/Memory**: >80% for 10 minutes → Warning

**Components:**
- `component_pp_health_dashboard.yml`

**APIs:**
- `GET /pp/v1/health/overview`
- `GET /pp/v1/health/microservices`
- `GET /pp/v1/health/microservices/{service_id}`
- `GET /pp/v1/health/queues`
- `POST /pp/v1/health/logs/query`
- `GET /pp/v1/health/alerts`

---

### Stage 3: Ticket Management (Phase 1)

**User Goal:** Handle internal support requests and incidents

**Roles:** Helpdesk Agent (primary), Infrastructure Engineer, Admin

**Workflow:**
1. Navigate to Tickets Dashboard
2. View ticket queue (filter by type, priority, status, assignee)
3. Create new ticket (type: support/incident/feature_request, priority, description)
4. Assign ticket (to self or team member)
5. Update ticket (status, comments, attachments)
6. Track SLA (response time, resolution time, countdown timer)
7. Escalate if SLA breach imminent
8. Close ticket with resolution notes

**Ticket Lifecycle:**
```
open → in_progress → [on_hold | escalated] → resolved → closed
```

**Ticket Types:**
- **Support**: General questions, configuration help
- **Incident**: Platform issues, bugs, outages
- **Feature Request**: Internal tooling improvements

**Priority Levels & SLAs:**
| Priority | Response Time | Resolution Time | Escalation Path |
|----------|---------------|-----------------|-----------------|
| Critical | 15 minutes    | 4 hours         | Infra Engineer  |
| High     | 2 hours       | 24 hours        | Infra Engineer  |
| Medium   | 8 hours       | 72 hours        | Team Lead       |
| Low      | 24 hours      | 1 week          | Team Lead       |

**Components:**
- `component_pp_helpdesk_ticketing.yml`

**APIs:**
- `GET /pp/v1/tickets`
- `POST /pp/v1/tickets`
- `GET /pp/v1/tickets/{ticket_id}`
- `PUT /pp/v1/tickets/{ticket_id}`
- `POST /pp/v1/tickets/{ticket_id}/assign`
- `POST /pp/v1/tickets/{ticket_id}/escalate`
- `POST /pp/v1/tickets/{ticket_id}/close`

**Integrations:**
- **Slack API**: Ticket created/escalated notifications (#helpdesk channel)
- **SendGrid**: Email notifications for SLA breaches

---

### Stage 4: User & Role Management (Phase 1)

**User Goal:** Manage PP user accounts and permissions

**Roles:** Admin (only)

**Workflow:**
1. Navigate to User Management
2. View all users (table: name, email, roles, status, last active)
3. Add new user (email @waooaw.com, validate via Google Directory API)
4. Assign role(s) (multiple roles allowed, e.g., Agent Orchestrator + Viewer)
5. Update user (change roles, activate/deactivate)
6. Revoke role (removes permission immediately)
7. Invalidate JWT (force re-login on role change)
8. Bulk operations (assign role to multiple users, max 50)

**User States:**
- **Active**: Can access PP
- **Inactive**: Cannot login (soft delete)
- **Pending**: Invited but not logged in yet

**Role Assignment Rules:**
- Admin role is exclusive (cannot combine with other roles)
- Manager roles can combine (e.g., Subscription Manager + Industry Manager)
- Operator roles can combine (e.g., Helpdesk + Viewer)

**Components:**
- `component_pp_user_management.yml`

**APIs:**
- `GET /pp/v1/users`
- `GET /pp/v1/users/{user_id}`
- `POST /pp/v1/users`
- `PUT /pp/v1/users/{user_id}`
- `POST /pp/v1/users/{user_id}/assign-role`
- `POST /pp/v1/users/{user_id}/revoke-role`
- `POST /pp/v1/users/bulk-assign-role`
- `POST /pp/v1/users/role-request` (future: self-service)

**Security:**
- Google Directory API validates @waooaw.com accounts
- JWT invalidation on role change (delete Redis session)
- Audit log tracks all role changes (`pp_role_change_log`)

---

### Stage 5: Subscription Management (Phase 2)

**User Goal:** Monitor subscriptions and audit agent runs

**Roles:** Subscription Manager (primary), Admin

**Workflow:**
1. Navigate to Subscriptions Dashboard
2. View all active subscriptions (table: customer, agent, health score, status)
3. Filter subscriptions (health score < 60, errors > 5, churned)
4. Drill into subscription details (agent runs, error logs, customer actions)
5. Audit agent runs (forensic access: inputs, outputs, timestamps, errors)
6. Export agent runs (CSV/PDF for analysis)
7. Create incident (if health score < 60 or >5 consecutive failures)
8. Force cancel subscription (Admin only, with reason + refund option)

**Health Score Calculation:**
```
health_score = (0.5 * success_rate + 0.3 * (1 - error_rate) + 0.2 * activity_score) * 100
```

**Dashboard Metrics:**
- **Subscription Status**: Active, Churned, Paused, Canceled
- **Health Score**: 0-100 (🟢 80+, 🟡 60-79, 🔴 <60)
- **Agent Run Success Rate**: % successful runs (last 30 days)
- **Error Rate**: % failed runs
- **Activity Score**: Frequency of agent executions

**Forensic Access (Constitutional Compliant):**
- ✅ Can view agent run logs (inputs, outputs, timestamps, errors)
- ✅ Can see which actions agent performed
- ❌ Cannot access customer core data (industry_data, strategic_plans)
- ❌ Cannot modify agent configurations

**Incident Auto-Creation Triggers:**
- Health score < 60 for 3 consecutive days
- More than 5 consecutive agent run failures
- Customer complaint (flagged by CP support ticket)

**Components:**
- `component_pp_subscription_management.yml`

**APIs:**
- `GET /pp/v1/subscriptions`
- `GET /pp/v1/subscriptions/{subscription_id}`
- `GET /pp/v1/subscriptions/{subscription_id}/agent-runs`
- `POST /pp/v1/subscriptions/{subscription_id}/export-runs`
- `POST /pp/v1/subscriptions/{subscription_id}/force-cancel` (Admin only)

---

### Stage 6: Agent Orchestration (Phase 2)

**User Goal:** Create new agents and monitor CI/CD pipelines

**Roles:** Agent Orchestrator (primary), Admin

**Workflow:**

**Agent Creation (5-Step Process):**

1. **Initiate Creation**
   - Navigate to Agent Orchestration
   - Click "Create New Agent"
   - Fill form (agent name, industry, specialty, SLA targets)
   - Submit creation request

2. **Genesis Validation (< 5 minutes, automated)**
   - Genesis Agent receives webhook
   - Validates constitutional compliance:
     - Customer sovereignty (agent serves customer, not WAOOAW)
     - Data privacy (no unauthorized data access)
     - Transparency (agent actions auditable)
     - Least privilege (minimal permissions)
   - Returns: Approved | Rejected (with reason)
   - If rejected: Stop process, notify Agent Orchestrator

3. **Code Generation (< 15 minutes, LLM-assisted)**
   - LLM generates agent code (FastAPI endpoints, business logic)
   - Generate Docker image
   - Create tests (unit + integration)
   - Commit to GitHub repository

4. **CI/CD Pipeline (25-35 minutes, 5 stages)**
   - **Stage 1**: Linting (Flake8, Black) - 2 min
   - **Stage 2**: Unit Tests (Pytest) - 8 min
   - **Stage 3**: Build Docker Image - 10 min
   - **Stage 4**: Integration Tests - 12 min
   - **Stage 5**: Push to Registry - 3 min
   - GitHub Actions webhook updates PP on each stage
   - If failure: Notify Agent Orchestrator, halt pipeline

5. **Handoff to Service Team (< 2 days)**
   - Creation team completes checklist:
     - [x] Docker image built and pushed
     - [x] Runbook documented
     - [x] Health check endpoint working
     - [x] Monitoring dashboard created
     - [x] Alert thresholds configured
     - [x] On-call engineer assigned
     - [x] SLA defined and agreed
     - [x] Load testing completed
   - Submit handoff request
   - Service team reviews (< 24 hours OLA)
   - Accept or Reject handoff
   - If accepted: Agent status → "production_ready"

**Agent Lifecycle:**
```
creation_phase (step 1-5) → service_phase (operational)
```

**Operational Readiness Parameters:**
- **Customer-Configurable** (in CP setup wizard):
  - Working hours (e.g., 09:00-18:00 IST)
  - Approval threshold (0.8 = 80% confidence)
  - Data freshness (e.g., 24 hours)
  - Error tolerance (e.g., 3 consecutive errors before pause)
  - Budget limit (e.g., ₹5,000/month)
  
- **Platform-Managed**:
  - Rate limits (100 API calls/min, 50K LLM tokens/hour)
  - Resource quotas (5 concurrent executions, 2GB RAM, 2 CPU cores)
  - Monitoring (30s health checks, 6-month logs, 7-day metrics)

**Agent Upgrades (Blue-Green Deployment):**
- Create new version with updates
- Deploy to green environment
- Run smoke tests
- Route 10% traffic to green
- Monitor for 1 hour
- If acceptable: Route 100% to green
- Keep blue as standby (rollback ready)

**Components:**
- `component_pp_agent_orchestration.yml`

**APIs:**
- `POST /pp/v1/agents/create`
- `GET /pp/v1/agents/{agent_id}/creation-status`
- `GET /pp/v1/agents/{agent_id}/cicd-pipeline`
- `POST /pp/v1/agent-handoff`
- `POST /pp/v1/agent-handoff/{handoff_id}/accept`

**Integrations:**
- Genesis Agent (validation webhook)
- GitHub Actions (CI/CD webhook)
- Docker Registry (image storage)

---

### Stage 7: SLA/OLA Management (Phase 3)

**User Goal:** Define and track Service Level Agreements and Operational Level Agreements

**Roles:** Agent Orchestrator (SLA config), Infrastructure Engineer (OLA config), Service Team Lead (compliance monitoring)

**Workflow:**

**SLA Configuration:**
1. During agent creation, configure SLA targets:
   - Response time (p95): < 2000ms
   - Uptime: >= 99.9%
   - Error rate: < 1%
   - Support response: < 4 hours
   - Critical incident resolution: < 4 hours
2. Choose SLA type (standard, premium, custom)
3. Set effective date
4. System tracks compliance automatically

**OLA Definition:**
1. Define internal team commitments:
   - Agent creation team → Service team (delivery within 2 weeks)
   - Service team acknowledgment (within 24 hours)
   - Infrastructure provisioning (within 4 hours)
   - On-call response (within 15 minutes)
2. Set escalation path
3. Track OLA breaches

**SLA Compliance Monitoring:**
1. Navigate to SLA Compliance Dashboard
2. View all agents with compliance % (last 30 days)
3. Color-coded status:
   - 🟢 Compliant (meeting all SLA targets)
   - 🟡 Warning (1-2 metrics close to breach)
   - 🔴 Breach (1+ metrics exceeded)
4. Drill into agent SLA details
5. View breach history (timestamp, metric, duration, root cause)

**Breach Handling:**
- **Immediate**: Alert on-call engineer (PagerDuty)
- **Customer Notification**: Email if breach affects them
- **SLA Credit**: Automatic if uptime < 99.9% for month

**Components:**
- `component_pp_sla_ola_management.yml`

**APIs:**
- `POST /pp/v1/sla-definitions`
- `GET /pp/v1/agents/{agent_id}/sla-compliance`
- `POST /pp/v1/ola-definitions`
- `POST /pp/v1/agent-handoff` (includes OLA deadline)
- `POST /pp/v1/agent-handoff/{handoff_id}/accept`

---

### Stage 8: Industry Knowledge Management (Phase 3)

**User Goal:** Manage industry-specific knowledge bases and retune agents

**Roles:** Industry Manager (primary), Agent Orchestrator (retuning), Admin (approval)

**Workflow:**

**Add Knowledge Source:**
1. Navigate to Industry Knowledge
2. Select industry (marketing, education, sales)
3. Click "Add Knowledge Source"
4. Fill form:
   - Source name (e.g., "Google Ads API")
   - Source type (API, RSS, webhook, manual upload)
   - Connection details (URL, auth type, credentials)
   - Scraping frequency (hourly, daily, weekly)
   - Scraping time (default: 2 AM IST)
5. Test connection
6. Submit
7. System schedules scraping job (Celery)

**Monitor Scraping Jobs:**
1. View knowledge sources table (status, last scraped, next scrape, records count)
2. Check scraping logs (success/failure, records ingested)
3. Receive alerts if scraping fails 3 consecutive times

**Review Knowledge Diff:**
1. Select industry
2. Choose version range (e.g., v2024-12-01 to v2025-01-01)
3. View change summary:
   - Embeddings added (1200)
   - Embeddings modified (450)
   - Embeddings removed (80)
   - % change (3.7%)
   - New topics (AI-powered targeting, Privacy-first analytics)
   - Removed topics (Third-party cookies)
4. Drill into top sources (which sources contributed most changes)

**Initiate Agent Retuning (Constitutional Approval Required):**
1. Select agent to retune
2. Choose knowledge version (e.g., v2025-01-01)
3. Provide reason ("Improve accuracy on Q4 2024 ad formats")
4. Select deployment strategy (blue-green or canary)
5. Submit retuning proposal
6. **Genesis Validation (< 10 minutes, automated)**:
   - Check for biases (demographic, gender, racial)
   - Check for harmful content (misinformation, illegal)
   - Validate constitutional alignment
   - Validate data quality (no duplicates, similarity scores)
   - Return: Approved | Rejected (with detailed reason)
7. **Admin Approval (manual)**:
   - If Genesis rejected: Cannot proceed (constitutional mandate)
   - If Genesis approved: Admin reviews and approves/rejects
8. **Deployment**:
   - Create new agent version with new knowledge
   - Deploy to staging (green environment)
   - Run smoke tests (10 test requests)
   - Route 10% traffic to green
   - Monitor for 1 hour (accuracy, response time, error rate)
   - If acceptable: Route 100% to green
   - Mark blue as standby (rollback ready for 7 days)
9. **Post-Deployment Monitoring**:
   - Check metrics at 1 hour, 24 hours, 7 days
   - Compare accuracy vs old version (A/B test)
   - If accuracy drops >5% or error rate increases >2x: Auto-rollback

**Rollback Conditions:**
- Error rate > 5%
- Response time > 2x baseline
- Customer complaints > 3
- Accuracy drops > 5%

**Components:**
- `component_pp_industry_knowledge.yml`

**APIs:**
- `POST /pp/v1/industry-knowledge/sources`
- `GET /pp/v1/industry-knowledge/sources`
- `GET /pp/v1/industry-knowledge/{industry}/diff`
- `POST /pp/v1/agents/{agent_id}/retune`
- `POST /pp/v1/agent-retuning/{retuning_id}/approve`
- `POST /pp/v1/industry-knowledge/{industry}/search`

**Integrations:**
- Google Ads API, Meta Ads API, HubSpot (marketing)
- NCERT, JEE/NEET APIs, Khan Academy (education)
- Salesforce, LinkedIn Sales Navigator (sales)
- OpenAI (embeddings generation)
- Pinecone/Weaviate (vector database)
- Genesis Agent (constitutional validation)

---

## Component Architecture

### Phase 1: Foundation (MVP)

**1. component_pp_authentication_oauth.yml**
- **Purpose**: Google OAuth 2.0 authentication for @waooaw.com
- **APIs**: 4 endpoints (login, callback, refresh, logout)
- **Database**: pp_users, pp_sessions (Redis), pp_audit_logs
- **Security**: Domain restriction, CSRF protection, JWT (HS256)

**2. component_pp_rbac_system.yml**
- **Purpose**: Role-based access control with 7 hierarchical roles
- **APIs**: 4 endpoints (roles, user roles, check permission, assign role)
- **Database**: pp_roles, pp_user_roles, pp_permission_checks
- **Hierarchy**: Admin > Manager > Operator > Viewer

**3. component_pp_health_dashboard.yml**
- **Purpose**: Platform health monitoring (13 microservices, queues, logs)
- **APIs**: 6 endpoints (overview, microservices, queues, logs, alerts)
- **Database**: pp_health_checks, pp_queue_metrics, pp_server_metrics, pp_alert_thresholds
- **Integrations**: ELK Stack, Prometheus, Grafana

**4. component_pp_helpdesk_ticketing.yml**
- **Purpose**: Internal ticketing system (support, incident, feature_request)
- **APIs**: 7 endpoints (list, create, get, update, assign, escalate, close)
- **Database**: pp_tickets, pp_ticket_comments, pp_ticket_history
- **SLA Tracking**: 4 priority levels with response/resolution times

**5. component_pp_user_management.yml**
- **Purpose**: User CRUD and role assignment (Admin-only)
- **APIs**: 8 endpoints (list, details, add, update, assign/revoke role, bulk assign)
- **Database**: pp_users, pp_user_roles, pp_role_change_log
- **Security**: Google Directory API validation, JWT invalidation

---

### Phase 2: Operations

**6. component_pp_subscription_management.yml**
- **Purpose**: Subscription monitoring and agent run forensics
- **APIs**: 5 endpoints (list, details, agent runs, export, force cancel)
- **Database**: subscriptions (existing), agent_runs (existing), pp_subscription_actions
- **Health Score**: 0-100 calculation (success rate, error rate, activity)
- **Constitutional**: No customer core data access

**7. component_pp_agent_orchestration.yml**
- **Purpose**: Agent creation workflow (Genesis validation, CI/CD, handoff)
- **APIs**: 5 endpoints (create, creation status, CI/CD pipeline, handoff, accept handoff)
- **Database**: pp_agent_creations, pp_agent_service_status, pp_agent_upgrades
- **Integrations**: Genesis Agent, GitHub Actions, Docker Registry

---

### Phase 3: Advanced

**8. component_pp_sla_ola_management.yml**
- **Purpose**: SLA/OLA configuration and compliance tracking
- **APIs**: 5 endpoints (create SLA, SLA compliance, create OLA, track handoff, accept handoff)
- **Database**: pp_sla_definitions, pp_sla_breaches, pp_ola_definitions, pp_agent_handoffs
- **SLA Types**: Standard, Premium, Custom

**9. component_pp_industry_knowledge.yml**
- **Purpose**: Industry knowledge scraping, embeddings, agent retuning
- **APIs**: 6 endpoints (create source, list sources, diff, retune, approve, search)
- **Database**: pp_industry_knowledge, pp_embeddings, pp_knowledge_sources, pp_retuning_history
- **Integrations**: OpenAI (embeddings), Pinecone (vector DB), Genesis Agent

---

## API Catalog

### Authentication & Authorization (5 endpoints)

| Endpoint | Method | Description | Roles |
|----------|--------|-------------|-------|
| `/pp/v1/auth/login` | POST | Initiate Google OAuth | Public |
| `/pp/v1/auth/callback` | POST | Google OAuth callback | Public |
| `/pp/v1/auth/refresh` | POST | Refresh JWT token | Authenticated |
| `/pp/v1/auth/logout` | POST | Logout (invalidate session) | Authenticated |
| `/pp/v1/roles/{role_id}/check-permission` | POST | Check user permission | Authenticated |

---

### User Management (8 endpoints)

| Endpoint | Method | Description | Roles |
|----------|--------|-------------|-------|
| `/pp/v1/users` | GET | List all users | Admin |
| `/pp/v1/users/{user_id}` | GET | Get user details | Admin |
| `/pp/v1/users` | POST | Add new user | Admin |
| `/pp/v1/users/{user_id}` | PUT | Update user | Admin |
| `/pp/v1/users/{user_id}/assign-role` | POST | Assign role | Admin |
| `/pp/v1/users/{user_id}/revoke-role` | POST | Revoke role | Admin |
| `/pp/v1/users/bulk-assign-role` | POST | Bulk assign role (max 50) | Admin |
| `/pp/v1/users/role-request` | POST | Request role (future) | Any |

---

### Health Monitoring (6 endpoints)

| Endpoint | Method | Description | Roles |
|----------|--------|-------------|-------|
| `/pp/v1/health/overview` | GET | Platform health overview | Infrastructure Engineer, Admin, Viewer |
| `/pp/v1/health/microservices` | GET | List all microservices | Infrastructure Engineer, Admin, Viewer |
| `/pp/v1/health/microservices/{service_id}` | GET | Microservice details | Infrastructure Engineer, Admin, Viewer |
| `/pp/v1/health/queues` | GET | Queue metrics (Temporal, Celery, RabbitMQ) | Infrastructure Engineer, Admin |
| `/pp/v1/health/logs/query` | POST | Query ELK Stack logs | Infrastructure Engineer, Admin |
| `/pp/v1/health/alerts` | GET | List alerts | Infrastructure Engineer, Admin |

---

### Ticketing (7 endpoints)

| Endpoint | Method | Description | Roles |
|----------|--------|-------------|-------|
| `/pp/v1/tickets` | GET | List tickets | Helpdesk Agent, Infrastructure Engineer, Admin |
| `/pp/v1/tickets` | POST | Create ticket | Helpdesk Agent, Infrastructure Engineer, Admin |
| `/pp/v1/tickets/{ticket_id}` | GET | Get ticket details | Helpdesk Agent, Infrastructure Engineer, Admin |
| `/pp/v1/tickets/{ticket_id}` | PUT | Update ticket | Helpdesk Agent, Infrastructure Engineer, Admin |
| `/pp/v1/tickets/{ticket_id}/assign` | POST | Assign ticket | Helpdesk Agent, Infrastructure Engineer, Admin |
| `/pp/v1/tickets/{ticket_id}/escalate` | POST | Escalate ticket | Helpdesk Agent, Infrastructure Engineer, Admin |
| `/pp/v1/tickets/{ticket_id}/close` | POST | Close ticket | Helpdesk Agent, Infrastructure Engineer, Admin |

---

### Subscription Management (5 endpoints)

| Endpoint | Method | Description | Roles |
|----------|--------|-------------|-------|
| `/pp/v1/subscriptions` | GET | List subscriptions | Subscription Manager, Admin |
| `/pp/v1/subscriptions/{subscription_id}` | GET | Subscription details | Subscription Manager, Admin |
| `/pp/v1/subscriptions/{subscription_id}/agent-runs` | GET | Agent run forensics | Subscription Manager, Admin |
| `/pp/v1/subscriptions/{subscription_id}/export-runs` | POST | Export agent runs (CSV/PDF) | Subscription Manager, Admin |
| `/pp/v1/subscriptions/{subscription_id}/force-cancel` | POST | Force cancel (Admin only) | Admin |

---

### Agent Orchestration (5 endpoints)

| Endpoint | Method | Description | Roles |
|----------|--------|-------------|-------|
| `/pp/v1/agents/create` | POST | Initiate agent creation | Agent Orchestrator, Admin |
| `/pp/v1/agents/{agent_id}/creation-status` | GET | Creation progress (5 steps) | Agent Orchestrator, Admin |
| `/pp/v1/agents/{agent_id}/cicd-pipeline` | GET | CI/CD pipeline status | Agent Orchestrator, Admin |
| `/pp/v1/agent-handoff` | POST | Handoff to service team | Agent Orchestrator, Admin |
| `/pp/v1/agent-handoff/{handoff_id}/accept` | POST | Accept handoff | Infrastructure Engineer, Admin |

---

### SLA/OLA Management (5 endpoints)

| Endpoint | Method | Description | Roles |
|----------|--------|-------------|-------|
| `/pp/v1/sla-definitions` | POST | Define SLA for agent | Agent Orchestrator, Admin |
| `/pp/v1/agents/{agent_id}/sla-compliance` | GET | SLA compliance report | Agent Orchestrator, Infrastructure Engineer, Admin |
| `/pp/v1/ola-definitions` | POST | Define internal OLA | Infrastructure Engineer, Admin |
| `/pp/v1/agent-handoff` | POST | Track handoff (OLA deadline) | Agent Orchestrator |
| `/pp/v1/agent-handoff/{handoff_id}/accept` | POST | Accept handoff (within 24h OLA) | Infrastructure Engineer, Admin |

---

### Industry Knowledge (6 endpoints)

| Endpoint | Method | Description | Roles |
|----------|--------|-------------|-------|
| `/pp/v1/industry-knowledge/sources` | POST | Add knowledge source | Industry Manager, Admin |
| `/pp/v1/industry-knowledge/sources` | GET | List knowledge sources | Industry Manager, Admin |
| `/pp/v1/industry-knowledge/{industry}/diff` | GET | Compare knowledge versions | Industry Manager, Admin |
| `/pp/v1/agents/{agent_id}/retune` | POST | Initiate retuning (Genesis gate) | Industry Manager, Agent Orchestrator, Admin |
| `/pp/v1/agent-retuning/{retuning_id}/approve` | POST | Admin approves retuning | Admin |
| `/pp/v1/industry-knowledge/{industry}/search` | POST | Search embeddings | Industry Manager, Admin |

---

**Total API Endpoints: 46**

---

## Database Architecture

### PP-Specific Tables (20+)

**Authentication & Users:**
- `pp_users` (id, email, name, status, created_at)
- `pp_sessions` (Redis: session_id, user_id, jwt, expires_at)
- `pp_audit_logs` (id, user_id, action, resource, timestamp)

**Roles & Permissions:**
- `pp_roles` (id, role_name, level, permissions JSONB)
- `pp_user_roles` (user_id, role_id, assigned_by, assigned_at)
- `pp_permission_checks` (id, user_id, permission, allowed, timestamp)
- `pp_role_change_log` (id, user_id, old_role, new_role, changed_by, timestamp)
- `pp_role_requests` (id, user_id, requested_role, reason, status) [future]

**Health Monitoring:**
- `pp_health_checks` (id, service_id, status, response_time_ms, error_rate, checked_at)
- `pp_queue_metrics` (id, queue_name, pending_count, running_count, checked_at)
- `pp_server_metrics` (id, server_name, cpu_percent, memory_percent, disk_percent, checked_at)
- `pp_alert_thresholds` (id, alert_type, threshold_value, severity, created_by)

**Ticketing:**
- `pp_tickets` (id, type, priority, status, title, description, assignee_id, created_by, created_at, resolved_at)
- `pp_ticket_comments` (id, ticket_id, user_id, comment, created_at)
- `pp_ticket_history` (id, ticket_id, field_changed, old_value, new_value, changed_by, changed_at)

**Subscriptions:**
- `pp_subscription_actions` (id, subscription_id, action_type, reason, performed_by, timestamp)

**Agent Orchestration:**
- `pp_agent_creations` (id, agent_id, status, genesis_status, cicd_status, created_by, created_at, completed_at)
- `pp_agent_service_status` (id, agent_id, status, on_call_engineer, health_check_url, dashboard_url)
- `pp_agent_upgrades` (id, agent_id, from_version, to_version, deployment_strategy, status, deployed_at)

**SLA/OLA:**
- `pp_sla_definitions` (id, agent_id, sla_type, response_time_p95_ms, uptime_percent, error_rate_percent, effective_date)
- `pp_sla_breaches` (id, sla_id, agent_id, metric_name, target_value, actual_value, severity, breach_start, breach_end, resolved)
- `pp_ola_definitions` (id, ola_name, provider_team, consumer_team, commitment, target_duration_value, target_duration_unit, escalation_path)
- `pp_agent_handoffs` (id, agent_id, status, handoff_checklist JSONB, initiated_by, accepted_by, initiated_at, accepted_at, ola_deadline)

**Industry Knowledge:**
- `pp_industry_knowledge` (id, industry, source_id, document_id, content, metadata JSONB, published_at, ingested_at, version)
- `pp_embeddings` (id, knowledge_id, embedding_vector VECTOR(1536), version, created_at)
- `pp_knowledge_sources` (id, industry, source_name, source_type, connection_details JSONB, scraping_frequency, status, last_scraped_at, next_scrape_at)
- `pp_retuning_history` (id, agent_id, knowledge_version_from, knowledge_version_to, reason, status, genesis_validation_result JSONB, deployed_at)

---

### Shared Tables (Existing from CP)

- `agents` (used for agent_id foreign keys)
- `subscriptions` (used for subscription management)
- `agent_runs` (used for forensic access)

---

## Constitutional Alignment

### WAOOAW Constitution Principles

**1. Customer Sovereignty**
- ✅ PP users cannot access customer core data (industry_data, strategic_plans)
- ✅ Agent run forensics are read-only (inputs, outputs, timestamps, errors)
- ✅ Force actions (cancel subscription) require Admin approval + reason
- ✅ Agents serve customers, not WAOOAW (Genesis validates this)

**2. Genesis Validation**
- ✅ All agent creations require Genesis approval
- ✅ All agent retuning requires Genesis approval
- ✅ Genesis checks: customer sovereignty, data privacy, transparency, least privilege
- ✅ Admin cannot override Genesis rejection (constitutional mandate)

**3. Transparency**
- ✅ All agent actions auditable (agent_runs table)
- ✅ All PP user actions logged (pp_audit_logs)
- ✅ SLA compliance visible to customers (CP displays SLA)
- ✅ Knowledge sources visible to admins (pp_knowledge_sources)

**4. Operational Readiness**
- ✅ Handoff checklist 100% complete before production
- ✅ Customer configures operational parameters (working hours, approval thresholds)
- ✅ Blue-green deployment with rollback safety
- ✅ SLA tracking with breach alerts

**5. Least Privilege**
- ✅ 7 hierarchical roles with granular permissions
- ✅ Admin-only force actions (cancel subscription, override)
- ✅ Role change invalidates JWT (immediate effect)
- ✅ Audit log tracks all permission checks

---

### Constitutional Gates (Enforced in Code)

**Genesis Validation Gate:**
```python
# pp_agent_creations table
if genesis_status != 'approved':
    raise ConstitutionalViolation("Cannot proceed without Genesis approval")
```

**Admin Approval Gate (Post-Genesis):**
```python
# pp_retuning_history table
if status == 'genesis_approved' and admin_approval is None:
    raise ConstitutionalViolation("Admin must approve retuning")
```

**Forensic Access Limit:**
```python
# Subscription Manager accessing agent_runs
allowed_fields = ['id', 'agent_id', 'inputs', 'outputs', 'created_at', 'status', 'error_message']
forbidden_fields = ['customer_industry_data', 'customer_strategic_plan']
```

**Force Action Audit:**
```python
# Admin cancels subscription
pp_subscription_actions.insert({
    'subscription_id': sub_id,
    'action_type': 'force_cancel',
    'reason': admin_reason,  # REQUIRED
    'performed_by': admin_user_id,
    'timestamp': now()
})
```

---

## Implementation Roadmap

### Phase 1: Foundation (4 weeks)

**Sprint 1 (Week 1-2): Authentication & RBAC**
- [ ] Set up PP Gateway (FastAPI, port 8015)
- [ ] Google OAuth integration (@waooaw.com domain restriction)
- [ ] JWT generation (HS256, 15-day expiry)
- [ ] Redis session store
- [ ] PostgreSQL setup (pp_users, pp_roles, pp_user_roles)
- [ ] RBAC middleware (permission enforcement)
- [ ] 7 roles seeded (Admin, Subscription Manager, Agent Orchestrator, Infrastructure Engineer, Helpdesk Agent, Industry Manager, Viewer)

**Sprint 2 (Week 2-3): Health Dashboard & Ticketing**
- [ ] Health monitoring (13 microservices heartbeats)
- [ ] ELK Stack integration (log query API)
- [ ] Queue metrics (Temporal, Celery, RabbitMQ)
- [ ] Alert system (Slack + email)
- [ ] Ticketing system (CRUD, SLA tracking)
- [ ] Frontend: Health Dashboard + Tickets Dashboard

**Sprint 3 (Week 3-4): User Management**
- [ ] User CRUD APIs (Admin-only)
- [ ] Google Directory API integration (email validation)
- [ ] Role assignment/revocation
- [ ] JWT invalidation on role change
- [ ] Bulk operations (max 50 users)
- [ ] Frontend: User Management page

---

### Phase 2: Operations (4 weeks)

**Sprint 4 (Week 5-6): Subscription Management**
- [ ] Subscription list API (filter by health score)
- [ ] Health score calculation (success rate, error rate, activity)
- [ ] Agent run forensics (read-only, constitutional compliant)
- [ ] Export agent runs (CSV/PDF)
- [ ] Incident auto-creation triggers
- [ ] Force cancel subscription (Admin-only)
- [ ] Frontend: Subscriptions Dashboard

**Sprint 5 (Week 6-8): Agent Orchestration**
- [ ] Agent creation workflow (5-step process)
- [ ] Genesis Agent validation webhook
- [ ] CI/CD pipeline tracking (GitHub Actions webhook)
- [ ] Handoff checklist (7 required items)
- [ ] Operational readiness parameters (customer + platform)
- [ ] Blue-green deployment for upgrades
- [ ] Frontend: Agent Orchestration Dashboard

---

### Phase 3: Advanced (5 weeks)

**Sprint 6 (Week 9-10): SLA/OLA Management**
- [ ] SLA definition (standard, premium, custom)
- [ ] SLA compliance tracking (5-min polling)
- [ ] SLA breach detection + alerts
- [ ] OLA definition (internal team commitments)
- [ ] Handoff OLA tracking (24-hour deadline)
- [ ] Frontend: SLA/OLA Dashboard

**Sprint 7 (Week 11-13): Industry Knowledge**
- [ ] Knowledge source management (API, RSS, webhook)
- [ ] Scraping jobs (Celery, daily at 2 AM IST)
- [ ] Embeddings generation (OpenAI ada-002)
- [ ] Vector database integration (Pinecone/Weaviate)
- [ ] Knowledge diff (version comparison)
- [ ] Agent retuning workflow (Genesis gate + Admin approval)
- [ ] Blue-green deployment + rollback
- [ ] Frontend: Industry Knowledge Dashboard

---

### Phase 4: Polish & Launch (2 weeks)

**Sprint 8 (Week 14-15): Testing & Documentation**
- [ ] End-to-end testing (all workflows)
- [ ] Load testing (Locust)
- [ ] Security audit (OWASP Top 10)
- [ ] User documentation (role-specific guides)
- [ ] Admin training session
- [ ] Runbook creation
- [ ] Production deployment

---

**Total Estimated Timeline: 15 weeks (3.5 months)**

---

## Conclusion

The **Platform Portal (PP)** is the operational backbone of WAOOAW, designed to enable a single-person + AI agents enterprise model. By enforcing constitutional guardrails, implementing role-based access, and providing comprehensive monitoring, PP ensures that WAOOAW operates reliably, transparently, and at scale.

### Key Success Metrics

- **Agent Creation Time**: < 2 weeks from initiation to production
- **SLA Compliance**: >= 99.9% uptime for all production agents
- **Platform Health**: 0 critical alerts in 30 days
- **Constitutional Compliance**: 100% Genesis approval rate (rejections handled)
- **Team Efficiency**: 1 founder + 10-15 internal agents + AI agents operating $1M+ ARR

---

### Next Steps

1. **Approve Specification**: Review this document with leadership
2. **Allocate Resources**: Assign backend/frontend/PM teams
3. **Set Up Infrastructure**: Provision PP Gateway, PostgreSQL, Redis, ELK
4. **Begin Sprint 1**: Authentication & RBAC (Week 1-2)

---

**Document Version:** 1.0  
**Last Updated:** January 8, 2026  
**Maintained By:** WAOOAW Operations Team  
**Contact:** ops@waooaw.com
