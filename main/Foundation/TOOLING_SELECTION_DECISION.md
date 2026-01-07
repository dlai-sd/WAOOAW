# Tooling Selection Decision
## Technology Stack for WaooaW Platform

**Version:** 1.0  
**Date:** 2026-01-06  
**Status:** Approved (Platform Governor)  
**Authority:** Constitutional requirement for explicit tooling decisions  
**Budget Constraint:** $100/month total platform cost  

---

## Selection Policies

1. **Open-source, free, off-the-shelf, secured tools** preferred
2. **Lightweight, low-cost, high availability** for production; simpler for dev/MVP
3. **GCP-native** where possible (cloud provider constraint)
4. **Cloud Run first** for maximum scale flexibility and cost optimization
5. **Budget governance:** $100/month hard cap with cost guards at 80%/95%

---

## Final Tool Selection

### 1. **Database: PostgreSQL Cloud SQL**

**Decision:** Managed PostgreSQL (Cloud SQL)

**Rationale:**
- **Append-only semantics:** Triggers + constraints enforce immutable audit logs
- **High availability:** Automated backups, point-in-time recovery, regional HA
- **GCP-native:** Deep integration with Cloud Run, IAM, Secret Manager
- **Cost-effective:** db-f1-micro instance sufficient for MVP (1 vCPU, 0.6GB RAM)
- **jsonb support:** Flexible schemas for manifests, precedent seeds, contracts

**Configuration:**
- **Instance tier:** db-f1-micro (MVP), db-g1-small (production)
- **Region:** us-central1 (MVP), multi-region for tier 2+ customers
- **Backups:** Automated daily, 7-day retention
- **Connections:** Cloud Run services via Unix domain socket (no public IP)

**Cost:** $15-25/month (managed instance + storage)

**Alternatives Considered:**
- ❌ SQLite: Too simple, no HA, single-node bottleneck
- ❌ DynamoDB: AWS-only, expensive, harder append-only semantics
- ❌ MongoDB: NoSQL unnecessary, more expensive than PostgreSQL

---

### 2. **Message Bus: Google Cloud Pub/Sub**

**Decision:** Cloud Pub/Sub with topics + schemas

**Rationale:**
- **Durability:** At-least-once delivery, message persistence, DLQ support
- **Schema enforcement:** Protobuf/Avro/JSON schema validation built-in
- **GCP-native:** Tight integration with Cloud Run (push subscriptions)
- **Scalability:** Auto-scales to thousands of messages/sec (future-proof)
- **Cost predictability:** Pay-per-message after free tier

**Configuration:**
- **Topics:** approvals, decisions, health_events, policy_attestations, audit_events, slo_breach
- **Schemas:** JSON Schema binding per topic (data_contracts.yml)
- **Subscriptions:** Push to Cloud Run endpoints (PEP enforcement)
- **DLQ:** Dead-letter topic with 30-day retention
- **Ordering:** Ordering key on agent_id for sequencing guarantees

**Cost:** $10-15/month (estimated 100K messages/day after free tier)

**Alternatives Considered:**
- ❌ Redis Pub/Sub: No persistence, lose messages on restart
- ❌ RabbitMQ: Operational overhead, need to manage HA
- ❌ Kafka: Over-engineered for scale, expensive to run

---

### 3. **Secrets Management: Google Secret Manager**

**Decision:** Secret Manager with per-engagement isolation

**Rationale:**
- **GCP-native:** Automatic rotation, audit logging via Cloud Audit Logs
- **Per-secret access control:** IAM bindings per agent/engagement
- **Versioning:** Secret versions enable rotation without downtime
- **Cost-effective:** $0.06/secret/month (first 6 secrets free)
- **Integration:** Native Cloud Run binding via environment variables

**Configuration:**
- **Secret naming:** `{engagement_id}/{agent_id}/{credential_type}`
- **Access control:** Per-agent service account can only read own secrets
- **Rotation policy:** 30-day rotation for API keys, 90-day for certificates
- **Audit:** All secret access logged to audit writer

**Cost:** $2-5/month (30-80 secrets estimated)

**Alternatives Considered:**
- ❌ HashiCorp Vault: Operational overhead, need to manage HA, more expensive
- ❌ File-based: Insecure, no rotation, audit gaps
- ❌ AWS Secrets Manager: Not GCP-native

---

### 4. **Container Orchestration: Google Cloud Run**

**Decision:** Cloud Run (serverless containers)

**Rationale:**
- **Cost optimization:** Pay-per-request, scale-to-zero when idle
- **Separation of Duties:** Each governance agent runs isolated service
- **Blue/green deployments:** Traffic splitting, gradual rollouts built-in
- **Regional HA:** Multi-region deployment for tier 2+ customers
- **Auto-scaling:** 0 to N instances based on load

**Configuration:**
- **Services:** genesis-agent, architect-agent, vision-guardian, pdp-service, manifest-service, ai-explorer, connector, audit-writer, orchestrator, api-gateway
- **CPU allocation:** 1 vCPU per governance agent, 0.5 vCPU for utilities
- **Memory:** 512MB-1GB per service
- **Concurrency:** 80 requests/instance (default)
- **Min instances:** 0 (scale-to-zero), 1 for critical services (audit-writer, pdp-service)

**Cost:** $30-50/month (estimated request volume + always-on services)

**Alternatives Considered:**
- ❌ GKE (Kubernetes): Over-engineered for scale, $70+/month minimum cluster cost
- ❌ Docker Compose: Local dev only, not production-ready
- ❌ VMs (Compute Engine): Always-on cost, no auto-scale

---

### 5. **Observability: Google Cloud Monitoring + Logging**

**Decision:** Cloud Monitoring (formerly Stackdriver)

**Rationale:**
- **GCP-native:** Automatic integration with Cloud Run, Cloud SQL, Pub/Sub
- **Free tier:** 5GB logs/month, 150MB metrics/month included
- **Alerting:** Built-in alert policies, notification channels (email, Slack)
- **Unified:** Metrics, traces, logs in single pane
- **Cost predictability:** Pay only above free tier

**Configuration:**
- **Metrics:** Custom metrics from governance namespace (data_contracts.yml)
- **Traces:** Cloud Trace for request correlation
- **Logs:** Structured JSON logs with redaction filters
- **Dashboards:** Pre-built + custom (approval funnel, token usage, SLO)
- **Alerts:** 4-tier severity (critical/high/medium/low) per playbook

**Cost:** $5-10/month (above free tier for custom metrics + log retention)

**Alternatives Considered:**
- ❌ Prometheus + Grafana: Operational overhead, need to host
- ❌ Datadog: Expensive ($15-50/host/month)
- ❌ Splunk: Enterprise pricing, overkill

---

### 6. **Frontend: React + FastAPI + Tortoise ORM**

**Decision:** React (web) + Flutter (mobile) + FastAPI backend + Tortoise ORM

**Rationale:**
- **React:** Most popular, component ecosystem, fast development
- **Flutter:** Single codebase for iOS/Android, native performance
- **FastAPI:** Async-native, automatic OpenAPI docs, Pydantic validation
- **Tortoise ORM:** Async-compatible, SQLAlchemy-like syntax, FastAPI optimized
- **Unified backend:** Same FastAPI endpoints serve web + mobile

**Configuration:**
- **Web:** React 18 + Vite (fast dev builds)
- **Mobile:** Flutter 3.x + Dart
- **Backend:** FastAPI 0.128+ + Tortoise ORM 0.20+
- **API:** RESTful + WebSocket for real-time updates (trial status, approvals)
- **Auth:** OAuth2 + JWT tokens (shared across web/mobile)

**Cost:** $0 (hosting on Cloud Run already counted)

**Alternatives Considered:**
- ❌ Next.js: Server-side rendering unnecessary for MVP
- ❌ Vue.js: Smaller ecosystem than React
- ❌ Native iOS/Android: Duplicate effort vs Flutter

---

### 7. **AI API: Groq (primary) + OpenAI (fallback)**

**Decision:** Groq for speed/cost, ChatGPT-4 for complex reasoning

**Rationale:**
- **Groq:** Ultra-fast inference (~500 tok/sec), cheap ($0.10-0.30/M tokens), Llama models
- **OpenAI:** Better reasoning (GPT-4o), more expensive ($1-5/M tokens)
- **Cost optimization:** 80% requests to Groq, 20% high-stakes to OpenAI
- **Fallback:** If Groq unavailable, route to OpenAI automatically

**Configuration:**
- **Primary:** Groq Llama 3.1 70B for drafting, classification, routine decisions
- **Fallback:** OpenAI GPT-4o mini for ethics review, complex classification
- **Premium:** OpenAI GPT-4o for Governor-escalated decisions (optional)
- **Cost guards:** Per-execution cap $0.50, per-agent daily cap $5

**Cost:** $10-20/month (trials + MVP workload)

**Alternatives Considered:**
- ❌ Anthropic Claude: More expensive than Groq, similar to OpenAI pricing
- ❌ Google Gemini: Still maturing, pricing unclear
- ❌ OpenAI only: Would exceed budget at scale

---

### 8. **Infrastructure as Code: Terraform + YAML Driver**

**Decision:** Terraform with single `infrastructure.yaml` driver

**Rationale:**
- **Declarative:** YAML defines desired state, Terraform applies
- **GCP modules:** Pre-built modules for Cloud Run, Cloud SQL, Pub/Sub
- **Version control:** Infrastructure changes tracked in Git
- **Preview:** `terraform plan` shows changes before apply

**Configuration:**
- **Driver file:** `cloud/infrastructure.yaml` (single source of truth)
- **Terraform modules:** `cloud/terraform/modules/` (Cloud Run, DB, Pub/Sub)
- **State:** GCS bucket `waooaw-terraform-state` (locked, versioned)
- **CI/CD:** GitHub Actions applies Terraform on push to main

**Cost:** $0 (GCS state bucket <1GB)

**Alternatives Considered:**
- ❌ Cloud Deployment Manager: GCP-only, less portable than Terraform
- ❌ Pulumi: Python/TypeScript IaC, steeper learning curve
- ❌ Manual UI: Not reproducible, no version control

---

### 9. **Workflow Orchestration: Temporal (Self-Hosted)**

**Decision:** Temporal for durable workflow execution (agent creation, servicing, skill orchestration)

**Rationale:**
- **Python-native:** Temporal Python SDK integrates with FastAPI, waooaw/ runtime
- **Durable execution:** Long-running workflows (24-hour Governor veto window, multi-day agent creation)
- **Constitutional fit:** Agent Creation (7 stages), Agent Servicing (proposal/evolution tracks), Manager Skill Orchestration (6-step workflow)
- **Audit trail:** Built-in workflow history, event logs (Think→Act→Observe visibility for Governor)
- **Cost-effective:** Self-hosted on Cloud Run $15/month vs Camunda $50-80/month

**Configuration:**
- **Deployment:** Temporal server on Cloud Run (1 container + PostgreSQL persistence)
- **Workers:** Foundational agents (Genesis, Systems Architect, Vision Guardian) as Temporal activities
- **Workflows:** Agent creation, agent servicing, skill orchestration as Python Temporal workflows
- **UI:** Temporal Web UI (included) for workflow monitoring, Governor oversight

**Cost:** $15/month (Cloud Run container + PostgreSQL storage)

**Alternatives Considered:**
- ❌ Camunda: BPMN visual designer but 3-5x cost ($50-80/month), Java-based, heavier infrastructure
- ❌ Prefect: Data-focused, not business rules, lacks decision tables
- ❌ Airflow: Batch scheduling, not real-time orchestration
- ❌ Manual Python: No durable execution, can't handle 24-hour waits, no audit trail

---

### 10. **Business Rules Engine: Python business-rules Library**

**Decision:** Python business-rules for externalized decision logic (query routing, budget thresholds, Precedent Seed matching)

**Rationale:**
- **Lightweight:** Library not server, zero infrastructure cost
- **Python-native:** Integrates with agent runtime, FastAPI endpoints
- **Externalized rules:** Decision tables in JSON/YAML (not hardcoded in Python)
- **Versioned:** Rules in Git, constitutional changes tracked
- **Audit trail:** Log rule evaluations (which rule fired, why, result)

**Configuration:**
- **Rules location:** `waooaw/rules/` directory (query_routing.yml, budget_thresholds.yml, precedent_seeds.yml)
- **Integration:** FastAPI endpoints load rules, agents query rules engine during execution
- **Format:** YAML decision tables (IF conditions THEN actions)
- **Examples:**
  - Query Routing: `IF query contains "HIPAA" THEN route_to="industry_db"`
  - Budget Threshold: `IF spend >= 0.80 THEN action="warn_governor"`
  - Precedent Seed: `IF request matches GEN-004 conditions THEN auto_approve=true, veto_window=24h`

**Cost:** $0 (open source library)

**Alternatives Considered:**
- ❌ Drools: Java-based, heavyweight, separate server required
- ❌ Camunda DMN: Requires Camunda engine, $50-80/month
- ❌ Hardcoded Python: Not externalized, constitutional changes require code deployment
- ❌ Database-driven: Adds query latency, requires migration scripts for rule changes

---

### 11. **Policy Decision Point: Open Policy Agent (OPA)**

**Decision:** OPA as PDP service on Cloud Run

**Rationale:**
- **Open-source:** Free, battle-tested, widely adopted
- **Rego language:** Declarative policy language, testable
- **Bundle loading:** Policies as code, version-controlled
- **Performance:** In-memory evaluation, <10ms decisions
- **Standardized:** CNCF project, integrations available

**Configuration:**
- **Deployment:** Cloud Run service `pdp-service`
- **Policies:** `main/Foundation/*.rego` files (converted from YAML policies)
- **Cache:** Redis for PDP decision caching (TTL per policy bundle)
- **API:** RESTful endpoint `/v1/data/waooaw/{policy_bundle}/allow`

**Cost:** $5/month (Cloud Run + minimal Redis cache)

**Alternatives Considered:**
- ❌ Custom Python: Reinventing wheel, harder to test/audit
- ❌ Cloud IAM only: Not expressive enough for constitutional policies
- ❌ Casbin: Less mature than OPA

---

### 10. **Development Platform: GitHub Codespaces**

**Decision:** GitHub Codespaces for cloud-based development

**Rationale:**
- **Consistent environment:** Dev container config ensures identical setup
- **Free tier:** 60 hours/month for personal accounts
- **GCP access:** Pre-configured gcloud CLI, Terraform, kubectl
- **Collaboration:** Multiple developers can use same environment definition

**Configuration:**
- **Instance:** 4-core, 8GB RAM (default)
- **Dev container:** `.devcontainer/devcontainer.json`
- **Pre-installed:** Python 3.11, Node 20, Terraform, gcloud, docker
- **Lifecycle:** Auto-suspend after 30min inactivity

**Cost:** $0 (within free tier for solo developer)

---

## Budget Allocation ($100/month)

| Category | Service | Cost | Notes |
|----------|---------|------|-------|
| **Database** | PostgreSQL Cloud SQL (db-f1-micro) | $15-20 | Managed, HA, backups |
| **Message Bus** | Cloud Pub/Sub | $10-15 | After 10GB free tier |
| **Secrets** | Secret Manager | $2-5 | 30-80 secrets |
| **Compute** | Cloud Run (10 services) | $30-40 | Pay-per-request + always-on |
| **Observability** | Cloud Monitoring + Logging | $5-10 | Above 5GB free tier |
| **AI APIs** | Groq + OpenAI | $10-20 | Trial workload |
| **Storage** | Cloud Storage (backups, state) | $2-3 | <50GB |
| **Networking** | Egress + Load Balancing | $5-10 | Minimal for single region |
| **IaC State** | GCS Terraform state | <$1 | <1GB |
| **CI/CD** | GitHub Actions | $0 | Free for public repos |
| **Development** | GitHub Codespaces | $0 | Free tier (60hrs/month) |
| **Total Estimated** | | **$79-123** | **Avg $101/month** |

**Budget Compliance:**
- Base case: $79/month (below cap, 21% buffer)
- Average case: $101/month (1% over, acceptable variance)
- High case: $123/month (23% over, requires optimization)

**Cost Optimization Triggers:**
- 80% utilization ($80): Emit alert, agents propose optimizations
- 95% utilization ($95): Suspend non-critical agents
- 100% utilization ($100): Halt all except governance agents + Governor escalations

**First Customer Revenue:** ₹8,000/month (~$95 USD) covers platform cost immediately

---

## Migration Strategy

### Phase 1: MVP (Months 1-3)
- PostgreSQL Cloud SQL (db-f1-micro, single region)
- Cloud Pub/Sub (us-central1)
- Cloud Run (us-central1, min instances = 0)
- Groq primary (90%), OpenAI fallback (10%)
- Single region, no multi-region HA

**Cost:** $79-90/month

### Phase 2: First Customer (Month 4+)
- Upgrade PostgreSQL to db-g1-small (production workload)
- Add multi-region failover (tier 2 customers)
- Increase Cloud Run min instances (governance agents = 1)
- Observability dashboards + alerting

**Cost:** $95-110/month (offset by customer revenue)

### Phase 3: Scale (10+ customers)
- Multi-region deployment (us, eu, asia)
- Increase AI API budget ($50/month)
- Consider reserved instances for cost savings
- Separate customer tiers (tier 1/2/3 per residency policy)

**Cost:** $200-500/month (10+ customers @ $95 each = $950/month revenue)

---

## Constitutional Compliance

**Tool Selection Policy (Foundation.md):**
- All tools documented with rationale, cost, alternatives considered
- Tooling decisions versioned (this document v1.0)
- Changes require Evolution proposal (Genesis classification)
- Cost guards enforced via platform_budget_policy.yml

**Precedent Seed:**
```yaml
seed_id: "INFRA-001"
version: 1
type: "tooling_selection"
decision: "PostgreSQL Cloud SQL + Cloud Pub/Sub + OPA + Cloud Run + Groq/OpenAI stack approved"
rationale: "Open-source, GCP-native, $100/month budget compliant, HA-ready"
approved_by: "Platform Governor"
date: "2026-01-06"
supersedes: null
status: "active"
```

---

## 11. Microservices Architecture Blueprint

**Decision Date**: 2026-01-07  
**Context**: Clean slate architecture redesign after constitutional design validation. Need industry-standard patterns for velocity.

### 11.1 Service Boundaries

**Decision**: 6 microservices aligned with bounded contexts (not per-agent granularity)

**Rationale**:
- **5 Core Services** (Agent Creation, Agent Execution, Governance, Industry Knowledge, Learning) map to constitutional layers
- **1 Admin Service** (Backend-For-Frontend pattern) aggregates cross-service operations
- Agent-per-service rejected: 7+ services too fragmented, orchestration complexity exceeds benefit
- Single monolith rejected: Cannot scale services independently (Agent Execution high load vs Governance low load)

**Alternatives Considered**:
1. ❌ **Service per agent** (Genesis Service, Manager Service, Governor Service, etc.) - 7+ services, orchestration nightmare, over-fragmentation
2. ❌ **Modular monolith** - Cannot scale independently, Agent Execution would force entire system to scale
3. ✅ **Bounded context services** - Right balance, constitutional alignment, independent scaling

**Cost Impact**: $66-125/month (5 Cloud Run services $16-75 variable + fixed infrastructure $50)

### 11.2 Gap Solutions (Simulation Results)

**Simulated 5 Scenarios**: Healthcare Marketing Campaign, Governor Veto Rollback, 50 Concurrent Jobs, New Industry Addition, Precedent Seed Propagation

**15 Gaps Found, Solutions Documented**:

| Gap | Solution | Pattern | ML Model | Cost |
|-----|----------|---------|----------|------|
| GAP-1: Agent Registry Ownership | Event-sourced registry (Agent Creation writes, all services cache with Redis 5-min TTL) | Event sourcing + caching | DistilBERT agent prediction | $0 |
| GAP-2: Cache Warming SLA | Predictive pre-warming (Prophet forecasts queries 5-min ahead, pre-fetch embeddings) | Predictive infra | Prophet time-series | $0 |
| GAP-3: Seed Extraction Logic | ML-first extraction (BART summarizes in Agent Execution, Genesis reviews in Learning) | AI-in-the-loop | BART-base 140MB | $0 |
| GAP-4: Rollback Coordination | Temporal saga with compensation workflows (Governor veto → reverse Genesis/Architect/Guardian) | Saga pattern | None | $0 |
| GAP-5: Event Ordering | Vector clocks for causal consistency (services buffer out-of-order events) | Vector clocks | None | $0 |
| GAP-6: Mobile Notification Fallback | Multi-channel cascade (Push → SMS 5-min → Email 15-min, ML predicts best channel) | Cascade + ML routing | Logistic Regression | +$5/mo SMS |
| GAP-7: Multi-Level Cache | 3-tier (L1 local 1-min, L2 Redis 5-min, L3 Vector DB) + semantic cache (MiniLM) | Semantic caching | MiniLM 22MB | $0 |
| GAP-8: DB Connection Pooling | PgBouncer (100 real, 1000 virtual) + per-service limits + circuit breaker | Connection multiplexing | LSTM load prediction | +$5/mo PgBouncer |
| GAP-9: Cascading Autoscale | Predictive scaling (Prophet 5-min ahead) + backpressure (exponential backoff on 429) | Predictive + backpressure | Prophet reused | $0 |
| GAP-10: Service Discovery | Event-driven (Pub/Sub IndustryAdded) + polling fallback (5-min /health reconciliation) | Hybrid discovery | None | $0 |
| GAP-11: Industry Exists But No Agents | Industry lifecycle state machine (draft → agents_pending → active) + feature flags | State machine + flags | None | $0 |
| GAP-12: Admin Operations Span Services | Admin Gateway BFF (aggregates calls) + conversational interface (Phi-3-mini NLU) | BFF + conversational | Phi-3-mini 1GB | +$10/mo service |
| GAP-13: Event Fan-Out Consistency | Optimistic UI + reconciliation (show "processing 2/3 services") + WebSocket updates | Optimistic UI | DistilBERT ETA | $0 |
| GAP-14: Circular Event Loop | Event causation tracking (causation_id, correlation_id) + idempotency (Redis 24-hour) | Causation lineage | None | $0 |
| GAP-15: Seed Lifecycle | Temporal workflow state machine (draft → pending_review → approved → active) | Workflow state machine | None | $0 |

**Total Cost Impact**: +$20/month (Admin $10, SMS $5, PgBouncer $5)

### 11.3 ML Models Approved

**8 Small/Medium Models, All CPU-Based**:

1. **DistilBERT** (66MB): Agent prediction, ETA estimation - 50-100ms inference
2. **BART-base** (140MB): Seed summarization - 100-200ms inference
3. **all-MiniLM-L6-v2** (22MB): Semantic cache embeddings - 30-50ms inference
4. **Phi-3-mini** (1GB 4-bit): Conversational admin - 150-300ms inference
5. **Prophet** (10MB): Load forecasting, cache warming - 50ms inference
6. **Logistic Regression** (<1MB): Notification routing - 5ms inference
7. **LSTM Tiny** (5MB): DB connection prediction - 10ms inference

**All models**:
- Run in-service (no separate ML infrastructure)
- CPU-only (no GPU $100+/month cost)
- Open source (no licensing)
- Have non-ML fallbacks (system functions if model fails)

### 11.4 Architectural Patterns Enforced

**Saga Pattern**: Temporal workflows with compensating activities (Agent Creation rollback)  
**Event Sourcing**: Append-only audit_log + causation/correlation tracking  
**Multi-Level Caching**: L1 local (1-min) → L2 Redis (5-min) → L3 source, semantic cache with MiniLM  
**Predictive Infrastructure**: Prophet forecasts load/queries 5-min ahead, LSTM predicts DB connections  
**Circuit Breaker**: Connection wait >2s → 503, downstream 429 → exponential backoff  
**Feature Flags**: Industry lifecycle state machine (agents_pending → active)  
**BFF Pattern**: Admin Gateway aggregates cross-service operations  
**Optimistic UI**: Show progress ("2/3 services processed"), reconcile async via WebSocket

### 11.5 Deviation Detection

**CI/CD Enforcement**:
- Pre-commit hook: Check new service against 6 approved boundaries
- PR checks: Verify OpenAPI schema compliance, event schema validation
- Architecture tests: Ensure no direct service-to-service calls (must use Temporal or Pub/Sub)
- Dependency scanner: Flag gRPC, 2PC libraries, distributed transaction packages
- Cost estimator: Calculate Cloud Run instance count, flag if exceeds $150/month

**Runtime Monitoring**:
- Service mesh observability: Detect synchronous chains >3 hops
- Event lineage tracking: Alert on events missing causation_id or correlation_id
- Cache hit rate: Alert if L1/L2 <80% (indicates warming failure)
- Circuit breaker metrics: Track open circuits, 503 rates per service

---

**Document Version**: 2.0  
**Last Updated**: 2026-01-07 (Session 3 - Microservices Architecture & Gap Resolution)

---

**End of Tooling Selection Decision Document**
