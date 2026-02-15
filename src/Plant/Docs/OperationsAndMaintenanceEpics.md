# Operations & Maintenance Epics — Phase 3

**Date**: 2026-02-12  
**Purpose**: Post-launch operational excellence, scalability, and automation  
**Related Document**: [README.md](README.md) - Plant docs index (single source of truth)  

---

## Overview

This document contains Phase 3 epics focused on **operational excellence**, **infrastructure scalability**, and **customer automation** that complement the core launch epics (Deployment, Beta Program, Training).

These epics are categorized as:
- **P0 Launch Enablers**: Critical for production operations (Monitoring)
- **P1 Launch Enablers**: Important for production resilience (DR, Multi-region)
- **P2 Post-Launch**: Optimization and automation (Auto-scaling, Onboarding automation)

---

## Epic Summary

| Epic ID | Epic Name | Story Count | Priority | Estimated Effort | Category |
|---------|-----------|-------------|----------|------------------|----------|
| [AGP3-OBS-1](#epic-agp3-obs-1--monitoring--observability) | Monitoring & Observability | 6 | P0 | 1.5 weeks | Launch Enabler |
| [AGP3-DR-1](#epic-agp3-dr-1--disaster-recovery--backup) | Disaster Recovery & Backup | 5 | P1 | 1 week | Launch Enabler |
| [AGP3-SCALE-1](#epic-agp3-scale-1--auto-scaling--load-balancing) | Auto-Scaling & Load Balancing | 5 | P2 | 1 week | Post-Launch |
| [AGP3-GEO-1](#epic-agp3-geo-1--multi-region--geo-redundancy) | Multi-Region & Geo-Redundancy | 6 | P1 | 2 weeks | Launch Enabler |
| [AGP3-AUTO-1](#epic-agp3-auto-1--customer-onboarding-automation) | Customer Onboarding Automation | 5 | P2 | 1.5 weeks | Post-Launch |
| **TOTAL** | **5 Epics** | **27 Stories** | - | **7-8 weeks** | - |

---

## Epic-wise stories (rollup)

| Epic ID | Epic Name | Stories (ID → status) |
|---|---|---|
| AGP3-OBS-1 | Monitoring & Observability | AGP3-OBS-1.1 ✅, AGP3-OBS-1.2 🔴, AGP3-OBS-1.3 ✅, AGP3-OBS-1.4 🔴, AGP3-OBS-1.5 ✅, AGP3-OBS-1.6 ✅ |
| AGP3-DR-1 | Disaster Recovery & Backup | AGP3-DR-1.1 🔴, AGP3-DR-1.2 🔴, AGP3-DR-1.3 🔴, AGP3-DR-1.4 🔴, AGP3-DR-1.5 🔴 |
| AGP3-SCALE-1 | Auto-Scaling & Load Balancing | AGP3-SCALE-1.1 🔴, AGP3-SCALE-1.2 🔴, AGP3-SCALE-1.3 🔴, AGP3-SCALE-1.4 🔴, AGP3-SCALE-1.5 🔴 |
| AGP3-GEO-1 | Multi-Region & Geo-Redundancy | AGP3-GEO-1.1 🔴, AGP3-GEO-1.2 🔴, AGP3-GEO-1.3 🔴, AGP3-GEO-1.4 🔴, AGP3-GEO-1.5 🔴, AGP3-GEO-1.6 🔴 |
| AGP3-AUTO-1 | Customer Onboarding Automation | AGP3-AUTO-1.1 🔴, AGP3-AUTO-1.2 🔴, AGP3-AUTO-1.3 🔴, AGP3-AUTO-1.4 🔴, AGP3-AUTO-1.5 🔴 |

---

## Epic AGP3-OBS-1 — Monitoring & Observability

**Priority**: P0 (Launch Blocker)  
**Estimated Effort**: 1.5 weeks  
**Owner**: SRE Team  
**Dependencies**: AGP3-DEPLOY-1.1 (production environment)

### Epic Goal
Implement comprehensive monitoring, alerting, and observability stack to ensure platform health visibility and rapid incident response.

### Success Criteria
- [x] **Prometheus metrics exported from all services** *(Implemented 2026-02-13)*
- [ ] Grafana dashboards deployed (4 dashboards: Executive, Operations, SRE, Business)
- [x] **Cloud Monitoring dashboards created and validated** *(Implemented 2026-02-13)*
- [ ] Alert rules configured in AlertManager (P0/P1/P2/P3 severity)
- [ ] PagerDuty integration for critical alerts
- [x] **Distributed tracing enabled (Cloud Trace)** *(Implemented 2026-02-13)*
- [x] **Structured logging implemented (JSON format)** *(Implemented 2026-02-13)*

### Stories

| Story ID | Title | Priority | Effort | Status | Completed Date | Notes |
|----------|-------|----------|--------|--------|---------------|-------|
| AGP3-OBS-1.1 | Prometheus metrics implementation | P0 | 3d | ✅ Complete | 2026-02-13 | /metrics endpoint with prometheus_client |
| AGP3-OBS-1.2 | Grafana dashboard deployment | P0 | 3d | 🔴 Not Started | - | Deploy 4 dashboards |
| AGP3-OBS-1.3 | Cloud Monitoring setup | P0 | 2d | ✅ Complete | 2026-02-13 | GCP dashboards, uptime checks, alerts |
| AGP3-OBS-1.4 | Alerting rules & PagerDuty | P0 | 3d | 🔴 Not Started | - | AlertManager + PagerDuty |
| AGP3-OBS-1.5 | Distributed tracing | P1 | 2d | ✅ Complete | 2026-02-13 | Cloud Trace via OpenTelemetry |
| AGP3-OBS-1.6 | Structured logging | P1 | 2d | ✅ Complete | 2026-02-13 | JSON logs, context tracking, middleware |

#### AGP3-OBS-1.1 Implementation Details (Completed 2026-02-13)
- **Module**: `src/Plant/BackEnd/core/metrics.py` (300+ lines)
- **Features Implemented**:
  - Prometheus metrics with `prometheus_client` library
  - `/metrics` endpoint exposing metrics in Prometheus text format
  - `/health` endpoint for load balancer health checks
  - MetricsMiddleware: Automatic HTTP metrics collection
  - HTTP metrics: `http_requests_total`, `http_request_duration_seconds`, `http_requests_in_progress`
  - Database metrics: `db_connections_total`, `db_query_duration_seconds`
  - Business metrics: `active_trials_total`, `agents_available_total`, `goals_created_total`, `goals_executed_total`, `customer_signups_total`
  - Application metrics: `application_version`, `uptime_seconds`
  - Helper functions: `record_http_request()`, `record_db_query()`, `update_business_metrics()`
- **Integration**: `src/Plant/BackEnd/main.py` with `setup_metrics()` and `MetricsMiddleware`
- **Commit**: `10bb5cd` - feat(observability): complete AGP3-OBS-1 monitoring epic
- **Next Steps**: 
  - Deploy to demo/uat/prod
  - Configure Grafana to scrape /metrics endpoint
  - Create Grafana dashboards using Prometheus queries
  - Set up alerting rules in Prometheus AlertManager

#### AGP3-OBS-1.3 Implementation Details (Completed 2026-02-13)
- **Location**: `cloud/monitoring/` directory
- **Files Created**:
  - `README.md`: Comprehensive monitoring guide (250+ lines)
  - `dashboards/executive.json`: Executive dashboard with 9 widgets
  - `alerts/p0-backend-down.yaml`: Critical alert policy for backend downtime
  - `uptime-checks/backend-health.yaml`: Health check configuration
- **Dashboard Features**:
  - Backend status scorecard (up/down with threshold)
  - Request rate (RPM) with sparkline
  - Error rate (%) with yellow (1%) and red (5%) thresholds
  - P95 latency chart with 200ms warning, 500ms critical
  - Requests per second by status code (stacked area)
  - Business metrics: Active trials, agents available, goals executed (24h)
  - Recent errors log panel (5xx responses)
- **Alert Policy**:
  - **P0 Backend Down**: Uptime check fails 3 consecutive times (3 minutes)
  - Notification channels: PagerDuty (immediate), Slack (#waooaw-alerts)
  - Auto-close after 30 minutes if resolved
  - Includes runbook link and rollback commands
- **Uptime Checks**:
  - /health endpoint monitored from 3 regions (APAC, USA, Europe)
  - 1-minute check interval, 10-second timeout
  - Content matcher: `"status":"healthy"`
- **Documentation**:
  - Alert severity levels (P0/P1/P2/P3)
  - SLO definitions (99.9% availability, P95<200ms latency)
  - Notification channels (PagerDuty, Slack, Email)
  - Deployment scripts and verification commands
  - Testing procedures for alerts
- **Commit**: `10bb5cd` - feat(observability): complete AGP3-OBS-1 monitoring epic
- **Deployment**: Run `cloud/<env>/scripts/deploy-monitoring.sh` for each environment

#### AGP3-OBS-1.5 Implementation Details (Completed 2026-02-13)
- **Integration**: Cloud Trace support added to `core/observability.py`
- **Features Implemented**:
  - OpenTelemetry integration with Cloud Trace exporter
  - Automatic trace context propagation via HTTP headers
  - Trace ID added to all log entries (structured JSON field)
  - Trace ID in GCP Cloud Logging format (`logging.googleapis.com/trace`)
  - Span creation for HTTP requests with attributes (method, URL, host)
  - Context variable `trace_id_var` for cross-async tracking
  - Graceful degradation if OpenTelemetry not installed
- **Configuration**: 
  - `gcp_project_id` setting added to `core/config.py`
  - TracerProvider with BatchSpanProcessor for efficient export
  - Resource metadata: service.name, service.version, deployment.environment
- **RequestLoggingMiddleware Enhancement**:
  - Extract trace context from incoming headers
  - Start span for each request
  - Set trace_id in logging context for correlation
- **Dependencies**: Requires `opentelemetry-exporter-gcp-trace` package
- **Commit**: `10bb5cd` - feat(observability): complete AGP3-OBS-1 monitoring epic
- **Usage**: 
  - Traces automatically created for HTTP requests
  - View in Cloud Trace: https://console.cloud.google.com/traces
  - Logs linked to traces via trace_id field

#### AGP3-OBS-1.6 Implementation Details (Completed 2026-02-13)
- **Module**: `src/Plant/BackEnd/core/observability.py` (450+ lines)
- **Features Implemented**:
  - JSONFormatter: GCP-compatible structured logs with severity, context, exceptions
  - ColoredFormatter: Human-readable development logs with PID and color-coding
  - RequestLoggingMiddleware: Automatic HTTP request/response logging with timing
  - Context tracking: `request_id`, `correlation_id`, `customer_id`, `trace_id` across async boundaries
  - `setup_observability(settings)`: Configure logging based on environment
  - Environment flags: 6 flags for production control (request logging, route registration, SQL, startup diagnostics, JSON format, access logs)
  - `log_route_registration(app)`: Debug route mounting with grouped output
  - `set_request_context()`, `clear_request_context()`: Context management
- **Configuration**: `src/Plant/BackEnd/core/config.py` with environment variable support
  - `ENABLE_REQUEST_LOGGING`: HTTP traffic logging (verbose)
  - `ENABLE_ROUTE_REGISTRATION_LOGGING`: Route mounting debug
  - `ENABLE_SQL_LOGGING`: SQLAlchemy queries
  - `ENABLE_STARTUP_DIAGNOSTICS`: Startup sequence details
  - `ENABLE_JSON_LOGS`: JSON structured format
  - `ENABLE_UVICORN_ACCESS_LOGS`: Access logs
- **Integration**: `src/Plant/BackEnd/main.py` with setup_observability() and middleware
- **Commit**: `43280bb` - feat(observability): production-ready logging with environment flags
- **Commit**: `10bb5cd` - feat(observability): complete AGP3-OBS-1 monitoring epic
- **Deployment**: Pending (flags: ENABLE_ROUTE_REGISTRATION_LOGGING, ENABLE_STARTUP_DIAGNOSTICS, ENABLE_JSON_LOGS)
- **Status**: Ready for production use with configurable verbosity

**DoD for Epic**: Can detect and alert on critical issues within 5 minutes, dashboards show real-time health

---

## Epic AGP3-DR-1 — Disaster Recovery & Backup

**Priority**: P1 (Launch Enabler)  
**Estimated Effort**: 1 week  
**Owner**: SRE Team + Infrastructure  
**Dependencies**: AGP3-DEPLOY-1.1 (production environment)

### Epic Goal
Implement automated backup strategy, disaster recovery procedures, and validate RTO/RPO targets.

### Success Criteria
- [ ] Automated daily database backups (PostgreSQL)
- [ ] Point-in-time recovery tested and validated
- [ ] Disaster recovery runbook created and tested
- [ ] RTO validated: < 4 hours from disaster to recovery
- [ ] RPO validated: < 15 minutes of data loss maximum
- [ ] Backup restoration procedure tested (dry run)
- [ ] Emergency contact list and escalation matrix

### Stories

| Story ID | Title | Priority | Effort | Description |
|----------|-------|----------|--------|-------------|
| AGP3-DR-1.1 | Automated database backups | P1 | 2d | Configure Cloud SQL backups, retention policy (30 days), cross-region |
| AGP3-DR-1.2 | Point-in-time recovery testing | P1 | 2d | Test PITR from backup, validate data integrity |
| AGP3-DR-1.3 | Disaster recovery runbook | P1 | 2d | Document DR procedures, failover steps, recovery checklist |
| AGP3-DR-1.4 | RTO/RPO validation | P1 | 2d | Simulate disaster, measure recovery time, validate targets |
| AGP3-DR-1.5 | DR drill execution | P1 | 2d | Quarterly DR drill, full recovery simulation, lessons learned |

**DoD for Epic**: Can recover from catastrophic failure within 4 hours with <15 min data loss

---

## Epic AGP3-SCALE-1 — Auto-Scaling & Load Balancing

**Priority**: P2 (Post-Launch)  
**Estimated Effort**: 1 week  
**Owner**: SRE Team + Infrastructure  
**Dependencies**: AGP3-DEPLOY-1 (production), AGP3-OBS-1 (monitoring)

### Epic Goal
Validate horizontal auto-scaling under real production load, configure load balancing, ensure system scales to handle growth.

### Success Criteria
- [ ] Auto-scaling triggers configured (CPU, memory, request count)
- [ ] Horizontal scaling tested (1→10 instances under load)
- [ ] Load balancer configuration validated (sticky sessions, health checks)
- [ ] Scaling metrics tracked (scale-up latency, scale-down threshold)
- [ ] Cost optimization analysis (right-sizing, reserved vs on-demand)
- [ ] Capacity planning model created (forecasting)

### Stories

| Story ID | Title | Priority | Effort | Description |
|----------|-------|----------|--------|-------------|
| AGP3-SCALE-1.1 | Auto-scaling configuration | P2 | 2d | Configure Cloud Run auto-scaling, triggers, min/max instances |
| AGP3-SCALE-1.2 | Horizontal scaling validation | P2 | 2d | Load test with 1→10 instances, validate graceful scaling |
| AGP3-SCALE-1.3 | Load balancer tuning | P2 | 2d | Configure sticky sessions, health checks, timeout settings |
| AGP3-SCALE-1.4 | Scaling metrics & monitoring | P2 | 2d | Track scale events, latency, cost per instance |
| AGP3-SCALE-1.5 | Capacity planning model | P2 | 2d | Forecasting tool, growth projections, cost modeling |

**DoD for Epic**: System auto-scales seamlessly, handles 10x traffic without manual intervention

---

## Epic AGP3-GEO-1 — Multi-Region & Geo-Redundancy

**Priority**: P1 (Launch Enabler)  
**Estimated Effort**: 2 weeks  
**Owner**: Infrastructure + SRE  
**Dependencies**: AGP3-DEPLOY-1 (production), AGP3-DR-1 (backup)

### Epic Goal
Deploy platform to multiple GCP regions for geo-redundancy, disaster recovery, and latency optimization.

### Success Criteria
- [ ] Secondary region deployed (us-central1 as DR for asia-south1)
- [ ] Database replication configured (cross-region read replicas)
- [ ] Global load balancer configured (geo-routing)
- [ ] Failover tested (primary region failure → secondary)
- [ ] Data residency compliance validated (India PDPB)
- [ ] Latency optimization (CDN for static assets)

### Stories

| Story ID | Title | Priority | Effort | Description |
|----------|-------|----------|--------|-------------|
| AGP3-GEO-1.1 | Secondary region deployment | P1 | 3d | Deploy to us-central1 (DR region), identical config |
| AGP3-GEO-1.2 | Database cross-region replication | P1 | 3d | Configure read replicas, replication lag monitoring |
| AGP3-GEO-1.3 | Global load balancer setup | P1 | 3d | Configure Cloud Load Balancer, geo-routing, health checks |
| AGP3-GEO-1.4 | Failover testing | P1 | 2d | Simulate primary region failure, validate DR failover |
| AGP3-GEO-1.5 | Data residency compliance | P1 | 2d | Validate India data stays in India, audit trail |
| AGP3-GEO-1.6 | CDN optimization | P2 | 2d | Configure Cloud CDN for static assets, latency reduction |

**DoD for Epic**: Platform survives regional outage, failover <30 min, latency optimized

---

## Epic AGP3-AUTO-1 — Customer Onboarding Automation

**Priority**: P2 (Post-Launch)  
**Estimated Effort**: 1.5 weeks  
**Owner**: Engineering + Product  
**Dependencies**: AGP3-BETA-1 (beta learnings), AGP2-DOC-1.1 (onboarding runbook)

### Epic Goal
Automate customer onboarding process (currently manual per runbook) to enable self-service trial activation and agent configuration.

### Success Criteria
- [ ] Self-service trial signup (email → account created)
- [ ] Automated credential collection (OAuth redirect, API key form)
- [ ] Automated agent provisioning (select agent → configure → activate)
- [ ] First goal wizard (guided flow for first goal creation)
- [ ] Onboarding email sequence (welcome, tips, reminders)
- [ ] Onboarding analytics (drop-off points, time-to-first-goal)

### Stories

| Story ID | Title | Priority | Effort | Description |
|----------|-------|----------|--------|-------------|
| AGP3-AUTO-1.1 | Self-service trial signup | P2 | 3d | Email signup, account creation, trial activation (no human) |
| AGP3-AUTO-1.2 | Automated credential collection | P2 | 3d | OAuth redirect flow, API key form, validation |
| AGP3-AUTO-1.3 | Automated agent provisioning | P2 | 3d | Agent catalog, selection, config wizard, activation |
| AGP3-AUTO-1.4 | First goal wizard | P2 | 2d | Guided flow, templates, validation, first run |
| AGP3-AUTO-1.5 | Onboarding email sequence & analytics | P2 | 2d | Drip campaign, analytics dashboard, optimization |

**DoD for Epic**: Customer can sign up, configure agent, create first goal without human assistance

---

## Implementation Strategy

### Phase 1: Core Operations (Weeks 1-2)
**Focus**: Monitoring & Observability  
**Goal**: Production visibility and alerting  
- AGP3-OBS-1: All 6 stories completed
- Outcome: Real-time dashboards, alerts, on-call rotation

### Phase 2: Resilience (Weeks 3-4)
**Focus**: Disaster Recovery & Multi-Region  
**Goal**: Platform survives failures  
- AGP3-DR-1: Backup automation, PITR testing
- AGP3-GEO-1: Secondary region deployment, failover
- Outcome: <4 hour RTO, regional redundancy

### Phase 3: Optimization (Weeks 5-6)
**Focus**: Scaling & Automation  
**Goal**: Efficient growth without manual intervention  
- AGP3-SCALE-1: Auto-scaling, capacity planning
- AGP3-AUTO-1: Customer self-service onboarding
- Outcome: 10x capacity, reduced ops overhead

---

## Success Metrics

### Operational Excellence
- **Observability**: Mean time to detect (MTTD) < 5 minutes
- **Reliability**: MTTR < 1 hour for P0 incidents
- **Availability**: 99.9% uptime SLA
- **Recovery**: RTO < 4 hours, RPO < 15 minutes

### Scalability
- **Auto-scaling**: Handles 10x traffic without manual intervention
- **Latency**: P95 < 200ms globally with CDN
- **Cost Efficiency**: <30% infrastructure cost per customer

### Automation
- **Onboarding**: 80% trial activation without human touch
- **Time to Value**: First goal executed within 30 minutes of signup
- **Self-Service**: <10% customer support tickets related to onboarding

---

## Dependencies & Sequencing

### Critical Path
```
AGP3-DEPLOY-1 → AGP3-OBS-1 (monitoring) → Production Launch
                ↓
         AGP3-DR-1 (backup) → AGP3-GEO-1 (multi-region)
```

### Parallel Work Streams
- **Stream 1**: Monitoring implementation (AGP3-OBS-1) — Week 1-2
- **Stream 2**: DR setup (AGP3-DR-1) — Week 3
- **Stream 3**: Multi-region (AGP3-GEO-1) — Week 3-4
- **Stream 4**: Auto-scaling (AGP3-SCALE-1) — Week 5
- **Stream 5**: Onboarding automation (AGP3-AUTO-1) — Week 5-6

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Monitoring gaps miss critical issue | Low | Critical | Comprehensive alerting, PagerDuty escalation, on-call rotation |
| Disaster recovery test fails | Low | High | Practice DR drills, document learnings, improve procedures |
| Auto-scaling insufficient | Low | Medium | Load testing before launch, capacity buffer, manual scaling backup |
| Multi-region latency issues | Medium | Medium | CDN optimization, geo-routing validation, perf testing |
| Onboarding automation bugs | Medium | Low | Gradual rollout, fallback to manual process, user testing |

---

## Related Documents

- [README.md](README.md) - Plant docs index (single source of truth)
- [AGP2-PERF-1_Implementation_Plan.md](/workspaces/WAOOAW/docs/AGP2-PERF-1_Implementation_Plan.md) - Performance testing framework
- [Runbooks](/workspaces/WAOOAW/docs/runbooks/) - Operational procedures (health monitoring, incident response)
- [INFRASTRUCTURE_DEPLOYMENT.md](/workspaces/WAOOAW/cloud/INFRASTRUCTURE_DEPLOYMENT.md) - Cloud infrastructure setup

---

## Story Status Legend
- ✅ Complete
- 🟡 In Progress
- 🔴 Not Started
- ⏸️ Blocked
