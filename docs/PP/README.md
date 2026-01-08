# Platform Portal (PP) Documentation

**Version:** 1.0  
**Status:** Specification Complete  
**Last Updated:** January 8, 2026

---

## Overview

The **Platform Portal (PP)** is WAOOAW's internal operations hub for monitoring, managing, and maintaining the AI agent marketplace. Exclusively for WAOOAW employees with @waooaw.com email addresses.

### Quick Facts

- **Purpose**: Internal operations and agent lifecycle management
- **Users**: WAOOAW employees only (@waooaw.com domain)
- **Authentication**: Google OAuth 2.0 (Workspace)
- **Roles**: 7 hierarchical roles (Admin → Manager → Operator → Viewer)
- **Architecture**: Separate backend service (PP Gateway on port 8015)
- **Constitutional**: All operations aligned with WAOOAW Constitution

---

## Documentation Structure

```
docs/PP/
├── README.md (this file)
└── user_journey/
    ├── PP_USER_JOURNEY.yaml     # Machine-readable specification
    └── PP_USER_JOURNEY.md       # Human-readable guide (42,000 words)
```

### Component Specifications

Located in `main/Foundation/template/`:

**Phase 1: Foundation (5 components)**
1. `component_pp_authentication_oauth.yml` - Google OAuth authentication
2. `component_pp_rbac_system.yml` - Role-based access control
3. `component_pp_health_dashboard.yml` - Platform health monitoring
4. `component_pp_helpdesk_ticketing.yml` - Internal ticketing system
5. `component_pp_user_management.yml` - User CRUD and role assignment

**Phase 2: Operations (2 components)**
6. `component_pp_subscription_management.yml` - Subscription monitoring
7. `component_pp_agent_orchestration.yml` - Agent creation and CI/CD

**Phase 3: Advanced (2 components)**
8. `component_pp_sla_ola_management.yml` - SLA/OLA tracking
9. `component_pp_industry_knowledge.yml` - Knowledge bases and retuning

---

## Quick Start

### For Admins

1. **Access**: Navigate to `https://portal.waooaw.com`
2. **Login**: Click "Sign in with Google" (requires @waooaw.com email)
3. **First Steps**:
   - Review Health Dashboard (13 microservices status)
   - Add new users (User Management)
   - Assign roles (Admin, Subscription Manager, etc.)
   - Configure alert thresholds

### For Subscription Managers

1. **Monitor Subscriptions**: Check subscriptions with health score < 60
2. **Audit Agent Runs**: View agent run logs (forensic access)
3. **Create Incidents**: For failing agents or customer complaints
4. **Export Reports**: CSV/PDF of agent performance metrics

### For Agent Orchestrators

1. **Create Agents**: 5-step workflow (Genesis validation → CI/CD → handoff)
2. **Monitor CI/CD**: Track GitHub Actions pipeline (25-35 min)
3. **Complete Handoff**: Checklist (Docker image, runbook, monitoring)
4. **Retune Agents**: Update with new industry knowledge (quarterly)

### For Infrastructure Engineers

1. **Health Monitoring**: Poll dashboard every 5 minutes (agent-triggered)
2. **Alert Response**: Slack/email for critical issues
3. **Log Analysis**: Query ELK Stack (6-month retention)
4. **On-Call**: Respond to PagerDuty pages (15-min SLA)

---

## User Roles

### Hierarchy

```
Admin (Level 1)
  ├── Subscription Manager (Level 2)
  ├── Agent Orchestrator (Level 2)
  ├── Infrastructure Engineer (Level 2)
  │     ├── Helpdesk Agent (Level 3)
  │     └── Industry Manager (Level 3)
  └── Viewer (Level 4)
```

### Permissions

| Role | Access Level | Key Permissions |
|------|--------------|----------------|
| **Admin** | Full control | `*:*`, force cancel subscriptions, add/remove users |
| **Subscription Manager** | Subscription lifecycle | `subscription_management:*`, `agent_runs:forensics` |
| **Agent Orchestrator** | Agent creation | `agent_orchestration:*`, `agent_retuning:initiate` |
| **Infrastructure Engineer** | Platform health | `health_monitoring:*`, `infrastructure:*` |
| **Helpdesk Agent** | Ticket management | `helpdesk:*`, `tickets:*` |
| **Industry Manager** | Knowledge bases | `industry_knowledge:*`, `knowledge_sources:*` |
| **Viewer** | Read-only | `*:read` |

---

## Architecture

### Tech Stack

- **Backend**: Python 3.11+, FastAPI, PostgreSQL, Redis
- **Frontend**: React 18, TypeScript, CSS3 (3 themes)
- **Authentication**: Google OAuth 2.0 (Workspace)
- **Monitoring**: Prometheus, Grafana, ELK Stack
- **Task Queue**: Celery, RabbitMQ
- **Vector DB**: Pinecone/Weaviate

### API Summary

**Total**: 46 API endpoints across 9 components

For detailed API documentation, see [PP_USER_JOURNEY.md](user_journey/PP_USER_JOURNEY.md#api-catalog)

---

## Database Schema

**20+ PP-specific tables:**
- Authentication & Users (pp_users, pp_sessions, pp_audit_logs)
- Roles & Permissions (pp_roles, pp_user_roles, pp_permission_checks)
- Health Monitoring (pp_health_checks, pp_queue_metrics, pp_server_metrics)
- Ticketing (pp_tickets, pp_ticket_comments, pp_ticket_history)
- Agent Orchestration (pp_agent_creations, pp_agent_service_status)
- SLA/OLA (pp_sla_definitions, pp_sla_breaches, pp_agent_handoffs)
- Industry Knowledge (pp_industry_knowledge, pp_embeddings, pp_knowledge_sources)

---

## Constitutional Compliance

### Key Principles

**1. Customer Sovereignty**
- ❌ PP users **cannot** access customer core data
- ✅ PP users **can** view agent run logs (forensics)

**2. Genesis Validation**
- ✅ All agent creations/retuning require Genesis approval
- ❌ Admin **cannot** override Genesis rejection

**3. Transparency**
- ✅ All agent actions auditable
- ✅ All PP user actions logged

**4. Operational Readiness**
- ✅ Handoff checklist 100% complete before production
- ✅ Blue-green deployment with rollback safety

---

## Roadmap

### Phase 1: Foundation (Weeks 1-4) ✅
- [x] Authentication (Google OAuth)
- [x] RBAC (7 roles)
- [x] Health Dashboard
- [x] Ticketing System
- [x] User Management

### Phase 2: Operations (Weeks 5-8) ✅
- [x] Subscription Management
- [x] Agent Orchestration

### Phase 3: Advanced (Weeks 9-13) ✅
- [x] SLA/OLA Management
- [x] Industry Knowledge Management

### Phase 4: Polish & Launch (Weeks 14-15) ⏳
- [ ] End-to-end testing
- [ ] Security audit
- [ ] Production deployment

**Current Status**: Specification Complete (v1.0) | Implementation: TBD

---

## Support

- **Slack**: #platform-portal
- **Email**: ops@waooaw.com
- **Documentation**: [PP_USER_JOURNEY.md](user_journey/PP_USER_JOURNEY.md)

---

**Document Version**: 1.0  
**Last Updated**: January 8, 2026  
**Maintained By**: WAOOAW Operations Team
