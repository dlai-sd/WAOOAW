# Architecture Decision Records (ADRs)
# WAOOAW Platform
# Version: 1.0
# Owner: Systems Architect Agent

---

## Table of Contents

1. [ADR-001: FastAPI Gateway vs GCP API Gateway](#adr-001-fastapi-gateway-vs-gcp-api-gateway)
2. [ADR-002: Kubernetes-Style Reconciliation for Grooming](#adr-002-kubernetes-style-reconciliation-for-grooming)
3. [ADR-003: Hash-Chained Audit Logs](#adr-003-hash-chained-audit-logs)
4. [ADR-004: PostgreSQL Row-Level Security](#adr-004-postgresql-row-level-security)
5. [ADR-005: Blue-Green Deployment Strategy](#adr-005-blue-green-deployment-strategy)
6. [ADR-006: Constitutional Framework Enforcement](#adr-006-constitutional-framework-enforcement)
7. [ADR-007: Temporal Workflow Engine for Orchestration](#adr-007-temporal-workflow-engine-for-orchestration)
8. [ADR-008: CPU-Only ML Models](#adr-008-cpu-only-ml-models)
9. [ADR-009: Pub/Sub for Event-Driven Architecture](#adr-009-pubsub-for-event-driven-architecture)
10. [ADR-010: Firebase Cloud Messaging for Mobile Notifications](#adr-010-firebase-cloud-messaging-for-mobile-notifications)
11. [ADR-011: GitHub Issues for Helpdesk](#adr-011-github-issues-for-helpdesk)
12. [ADR-012: Trial Mode Sandbox Routing](#adr-012-trial-mode-sandbox-routing)
13. [ADR-013: Open Policy Agent (OPA) for Policy Enforcement](#adr-013-open-policy-agent-opa-for-policy-enforcement)
14. [ADR-014: Redis for Distributed Caching](#adr-014-redis-for-distributed-caching)
15. [ADR-015: GCP Cloud Run for Microservices](#adr-015-gcp-cloud-run-for-microservices)

---

## ADR-001: FastAPI Gateway vs GCP API Gateway

**Status:** Accepted  
**Date:** 2026-01-09  
**Decision Makers:** Systems Architect Agent, Platform Engineering Team  
**Context:** Need API gateway for Customer Portal (CP) and Platform Portal (PP)

### Context

The platform requires API gateways for:
1. **Customer Portal (CP)**: Customer-facing APIs (agent execution, approvals, setup wizard)
2. **Platform Portal (PP)**: Internal admin APIs (health monitoring, audit queries, deployment)

Two options considered:
- **Option A**: FastAPI gateways (custom code)
- **Option B**: GCP API Gateway (managed service)

### Decision

**We will use FastAPI gateways (PP Gateway on port 8015, Admin Gateway on port 8006) with a migration path to GCP API Gateway in the future.**

### Rationale

**Pros of FastAPI:**
- ✅ **Full Control**: Custom authentication (JWT), RBAC, rate limiting, WebSocket support
- ✅ **Constitutional Enforcement**: Can validate Governor role, trial mode restrictions, approval workflows
- ✅ **Rapid Prototyping**: No vendor lock-in, easy to iterate during MVP phase
- ✅ **Cost**: $0 additional cost (runs on Cloud Run)
- ✅ **Debugging**: Direct access to logs, errors, metrics

**Cons of FastAPI:**
- ❌ **Maintenance**: Need to implement rate limiting, auth, routing ourselves
- ❌ **Scalability**: Must manage scaling logic (auto-scaling Cloud Run handles this)

**Pros of GCP API Gateway:**
- ✅ **Managed Service**: Google handles scaling, rate limiting, OpenAPI spec support
- ✅ **Enterprise Features**: Built-in security, monitoring, quotas

**Cons of GCP API Gateway:**
- ❌ **Cost**: $3/million requests + $0.20/GB egress
- ❌ **Limited Constitutional Enforcement**: Cannot enforce custom L0 principles
- ❌ **WebSocket Limitations**: No native WebSocket support (required for real-time updates)

### Consequences

**Positive:**
- Rapid development with full control over gateway logic
- Constitutional principles (Governor role, trial mode) enforced at gateway layer
- Zero additional cost during MVP phase
- WebSocket support for real-time agent updates

**Negative:**
- Need to maintain custom gateway code (authentication, rate limiting, routing)
- Potential refactor cost if migrating to GCP API Gateway later

**Mitigation:**
- Design gateways with clean separation of concerns (auth module, rate limiter module)
- Use OpenAPI spec to document APIs (future migration to GCP API Gateway easier)
- Monitor gateway performance and cost; trigger migration if traffic exceeds 10M requests/month

**Migration Path:**
- Phase 1: FastAPI gateways (current, MVP)
- Phase 2: Evaluate traffic patterns after 6 months
- Phase 3: Migrate to GCP API Gateway if cost-effective (expected at 10M+ requests/month)

---

## ADR-002: Kubernetes-Style Reconciliation for Grooming

**Status:** Accepted  
**Date:** 2026-01-09  
**Decision Makers:** Systems Architect Agent  
**Context:** Need lifecycle management for agent grooming (Conceive → Birth → Assembly → Certification → Activation)

### Context

The **grooming lifecycle** requires orchestration across 5 stages:
1. **Conceive**: Customer initiates trial, define agent goals
2. **Birth**: Create agent record, allocate resources
3. **Assembly**: Configure agent (OAuth, goals, skills)
4. **Certification**: Genesis 42-check validation
5. **Activation**: Deploy agent to production

Traditional workflow engines (Step Functions, Airflow) are linear and don't handle retries, state drift, or reconciliation well.

### Decision

**We will use Kubernetes-style reconciliation loops with Temporal Workflow Engine for saga patterns.**

### Rationale

**Kubernetes Reconciliation Pattern:**
- **Desired State**: Customer defines agent configuration (OAuth, goals, industry)
- **Current State**: Agent's actual state (trial_active, production_active, etc.)
- **Reconciliation Loop**: Plant Orchestrator continuously checks if current state matches desired state
  - If mismatch → trigger corrective actions (re-run certification, retry OAuth, etc.)
  - If match → no-op

**Temporal Saga Pattern:**
- Long-running workflows with compensation logic
- Automatic retries, timeout handling
- Durable execution (survives service restarts)

**Example Reconciliation:**
```python
# Desired State (from customer)
desired_state = {
  "agent_id": "agent_123",
  "status": "production_active",
  "oauth_credentials": ["wordpress", "mailchimp"],
  "goals": ["Publish 5 blog posts per week"],
}

# Current State (from database)
current_state = {
  "agent_id": "agent_123",
  "status": "trial_active",
  "oauth_credentials": ["wordpress"],  # Missing mailchimp
  "goals": ["Publish 5 blog posts per week"],
}

# Reconciliation Actions
actions = [
  "Request OAuth for Mailchimp",
  "Re-run Genesis certification",
  "Transition to production_active",
]
```

**Pros:**
- ✅ **Self-Healing**: Automatically detects and fixes state drift
- ✅ **Idempotent**: Safe to re-run reconciliation loops
- ✅ **Observable**: Clear desired vs current state comparison
- ✅ **Resilient**: Handles partial failures gracefully

**Cons:**
- ❌ **Complexity**: Requires understanding of reconciliation pattern
- ❌ **Debugging**: State transitions harder to trace than linear workflows

### Consequences

**Positive:**
- Agent grooming is resilient to failures (OAuth timeout, service downtime)
- Customers can modify agent configuration mid-trial; system auto-adjusts
- Genesis certification can be re-run if constitutional checks fail

**Negative:**
- Developers must understand reconciliation loops (training needed)
- Debugging requires tracing state transitions across multiple reconciliation cycles

**Mitigation:**
- Document reconciliation loops in grooming_lifecycle_blueprint.md
- Use Temporal UI for debugging workflow history
- Emit Pub/Sub events for every state transition (audit trail)

**Implementation:**
- Plant Orchestrator (port 8014) runs reconciliation every 30 seconds
- Temporal workflows for long-running sagas (grooming, trial expiration)
- PostgreSQL stores desired vs current state (agents table)

---

## ADR-003: Hash-Chained Audit Logs

**Status:** Accepted  
**Date:** 2026-01-09  
**Decision Makers:** Systems Architect Agent, Compliance Team  
**Context:** Need immutable audit trail for constitutional compliance (L0-05)

### Context

L0-05 principle: **Immutable Audit Trail**
- All agent actions, approvals, policy evaluations must be logged
- Logs must be tamper-proof (detect unauthorized modifications)
- Logs must support compliance queries (e.g., "Show all external actions by Agent X in trial mode")

### Decision

**We will implement SHA256 hash-chained audit logs stored in Google Cloud Storage (GCS) with PostgreSQL indexing.**

### Rationale

**Hash Chain Structure:**
```json
{
  "timestamp": "2026-01-09T10:30:00Z",
  "event_type": "agent_action_approved",
  "agent_id": "agent_123",
  "action": "POST /api/wordpress/publish",
  "approved_by": "governor_user_456",
  "previous_hash": "abc123...def",
  "current_hash": "SHA256(previous_hash + event_data)"
}
```

**Tamper Detection:**
- If **current_hash ≠ SHA256(previous_hash + event_data)** → Log tampered!
- Logs are append-only (no updates/deletes)
- Stored in GCS (immutable, versioned)

**Alternatives Considered:**
- **Blockchain (rejected)**: Overkill for centralized platform, high cost
- **AWS CloudTrail (rejected)**: Vendor lock-in, no custom event schemas
- **Plaintext logs (rejected)**: Not tamper-proof

**Pros:**
- ✅ **Tamper-Proof**: Hash chain detects unauthorized modifications
- ✅ **Cost-Effective**: GCS storage ($0.026/GB/month)
- ✅ **Query Performance**: PostgreSQL index for fast lookups (<1 second)
- ✅ **Compliance Ready**: Supports GDPR, SOC 2 audit requirements

**Cons:**
- ❌ **Complexity**: Need to maintain hash chain integrity
- ❌ **Storage Growth**: Audit logs grow indefinitely (mitigated by 90-day retention)

### Consequences

**Positive:**
- Constitutional compliance (L0-05) enforced at technical layer
- Audit queries execute in <1 second (PostgreSQL index)
- Supports forensic analysis ("Who approved Agent X's action at 10:30 AM?")

**Negative:**
- Hash chain breaks if logs corrupted → need periodic integrity checks
- 90-day retention means historical data lost (acceptable for MVP)

**Mitigation:**
- Run daily hash chain validation script (detect tampering within 24 hours)
- Backup audit logs to separate GCS bucket (disaster recovery)
- Implement retention policies (archive logs older than 90 days to cold storage)

**Implementation:**
- Audit Service (port 8010) appends logs to GCS (JSONL format)
- PostgreSQL audit_log_index table for fast queries
- 10 query patterns (see component_audit_log_query_patterns.yml)

---

## ADR-004: PostgreSQL Row-Level Security

**Status:** Accepted  
**Date:** 2026-01-09  
**Decision Makers:** Systems Architect Agent, Security Team  
**Context:** Need database-level access control to enforce data isolation

### Context

**Requirement**: Customers must only access their own agents, subscriptions, audit logs.

**Options:**
- **Option A**: Application-layer filtering (`WHERE customer_id = ?`)
- **Option B**: Database-layer filtering (PostgreSQL RLS)

### Decision

**We will use PostgreSQL Row-Level Security (RLS) for defense-in-depth.**

### Rationale

**Row-Level Security Example:**
```sql
-- Enable RLS on agents table
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;

-- Policy: Customers see only their agents
CREATE POLICY agent_access_policy ON agents
FOR SELECT
USING (customer_id = current_setting('app.current_customer_id')::uuid);

-- Application sets session variable
SET app.current_customer_id = 'customer_123';

-- This query automatically filtered by RLS
SELECT * FROM agents;  -- Only returns agents WHERE customer_id = 'customer_123'
```

**Pros:**
- ✅ **Defense-in-Depth**: Protects against SQL injection, application bugs
- ✅ **Zero Trust**: Database enforces isolation, even if application bypassed
- ✅ **Audit Trail**: PostgreSQL logs policy violations
- ✅ **Performance**: RLS uses indexes, no performance penalty

**Cons:**
- ❌ **Complexity**: Need to set session variables in every request
- ❌ **Debugging**: RLS errors can be cryptic

**Alternatives:**
- **Application-layer filtering**: Easy to implement but risky (bugs expose data)
- **Separate databases per customer**: Expensive, complex migrations

### Consequences

**Positive:**
- Prevents cross-customer data leaks (e.g., Agent A accessing Agent B's logs)
- Simplifies application code (no need for `WHERE customer_id = ?` everywhere)
- Supports constitutional principle (Governor data ownership)

**Negative:**
- Developers must remember to set `app.current_customer_id` in every request
- RLS policies must be tested for edge cases (admin users, support tickets)

**Mitigation:**
- Create FastAPI middleware to automatically set session variable from JWT token
- Unit tests for RLS policies (verify isolation)
- Document RLS setup in component_rbac_hierarchy.yml

**Implementation:**
- RLS policies on: agents, subscriptions, audit_log_index, customer_profiles
- Session variable set by PP Gateway / Admin Gateway
- PostgreSQL roles: customer_role, admin_role, systems_architect_role

---

## ADR-005: Blue-Green Deployment Strategy

**Status:** Accepted  
**Date:** 2026-01-09  
**Decision Makers:** Systems Architect Agent, DevOps Team  
**Context:** Need zero-downtime deployments for production

### Context

**Requirements:**
- Deploy 17 microservices without downtime
- Rollback instantly if deployment fails
- Test new version in production-like environment before cutover

**Options:**
- **Rolling Deployment**: Update instances one-by-one (slow, risky)
- **Canary Deployment**: Route 5% traffic to new version (complex routing)
- **Blue-Green Deployment**: Deploy full new environment, instant cutover

### Decision

**We will use Blue-Green Deployment with Cloud Run and Cloud Load Balancer.**

### Rationale

**Blue-Green Strategy:**
1. **Blue** = Current production (e.g., v1.2.3)
2. **Green** = New version (e.g., v1.2.4)
3. Deploy Green alongside Blue (no traffic yet)
4. Run smoke tests on Green
5. Cutover: Update load balancer to route traffic from Blue → Green
6. Monitor Green for 30 minutes
7. If issues → Instant rollback (route traffic back to Blue)
8. If stable → Decommission Blue

**Pros:**
- ✅ **Zero Downtime**: Cutover takes <5 seconds (load balancer update)
- ✅ **Instant Rollback**: Route traffic back to Blue if Green fails
- ✅ **Safe Testing**: Smoke tests on Green before production traffic
- ✅ **Cost-Effective**: Blue + Green run for ~30 minutes only

**Cons:**
- ❌ **Double Resources**: Need 2x Cloud Run instances during deployment
- ❌ **Database Migrations**: Must be backward-compatible (Blue + Green both connect to same DB)

**Alternatives:**
- **Rolling**: Slow (30+ minutes for 17 services), risky (partial failures)
- **Canary**: Complex (need traffic splitting logic), overkill for MVP

### Consequences

**Positive:**
- Customers experience zero downtime during deployments
- Failed deployments rollback instantly (no customer impact)
- Confidence in production releases (smoke tests validate Green)

**Negative:**
- Database migrations must be backward-compatible (Blue + Green coexist)
- Cloud Run costs double during deployment (~30 minutes, ~$5/deployment)

**Mitigation:**
- Write database migrations as 2-phase:
  - Phase 1: Additive changes (new columns, tables) → Deploy Green
  - Phase 2: Removal changes (drop old columns) → After Blue decommissioned
- Monitor Green for 30 minutes before decommissioning Blue
- Automate smoke tests (see FLOW-PP-DEPLOY-001)

**Implementation:**
- GitHub Actions workflow (see component_github_cicd_integration.yml)
- Cloud Load Balancer for traffic routing
- Smoke tests: Health checks + critical API calls (trial start, agent execution)

---

## ADR-006: Constitutional Framework Enforcement

**Status:** Accepted  
**Date:** 2026-01-09  
**Decision Makers:** Systems Architect Agent, Governance Team  
**Context:** Need to enforce L0 principles and Amendment-001 at runtime

### Context

**Constitutional Principles (L0):**
1. **Single Governor**: Customer is the Platform Governor
2. **Agent Specialization**: Agents don't cross domains (marketing vs sales)
3. **External Execution Approval**: Governor approves all external actions
4. **Deny-by-Default**: Permissions explicitly granted
5. **Immutable Audit Trail**: Hash-chained logs
6. **Data Minimization**: Agents access only necessary data
7. **Governance Protocols**: Manager → Governor escalation

**Challenge**: How to enforce these principles in code?

### Decision

**We will implement a 3-layer enforcement stack:**
1. **Policy Service (OPA)**: Evaluate policies at runtime
2. **Governance Service**: Orchestrate approval workflows
3. **Audit Service**: Validate compliance post-execution

### Rationale

**Layer 1: Policy Service (OPA)**
- Open Policy Agent evaluates Rego policies
- Example policy: `trial_mode_sandbox_routing.rego`
  ```rego
  allow {
    input.agent.status == "trial_active"
    input.action.target == "sandbox"  # Trial agents must use sandbox APIs
  }
  ```
- Policies loaded from PostgreSQL (dynamic updates)

**Layer 2: Governance Service**
- Orchestrates approval workflows (L0-03)
- Mobile push → Governor review → Approve/Reject → Resume agent
- Maintains approval history (audit trail)

**Layer 3: Audit Service**
- Post-execution validation: "Did agent comply with approved action?"
- Detects drift: "Agent executed X but was approved for Y"
- Triggers alerts for constitutional violations

**Pros:**
- ✅ **Decoupled**: Policy logic separate from business logic
- ✅ **Auditable**: Every policy evaluation logged
- ✅ **Flexible**: Add new principles without code changes (update Rego policies)

**Cons:**
- ❌ **Complexity**: Developers must understand OPA + Rego
- ❌ **Performance**: Policy evaluation adds latency (~10ms)

**Alternatives:**
- **Hardcode policies**: Fast but inflexible (code changes for new rules)
- **Database-driven rules**: Slow, no version control

### Consequences

**Positive:**
- Constitutional principles enforced at runtime (not just documentation)
- Genesis 42-check certification validates compliance
- Customers trust platform (transparent governance)

**Negative:**
- Learning curve for OPA + Rego (team training needed)
- Policy debugging harder than imperative code

**Mitigation:**
- Document all Rego policies in component_rbac_hierarchy.yml
- Unit tests for policies (verify L0 principles)
- Policy versioning (track changes via Git)

**Implementation:**
- Policy Service (port 8013) runs OPA server
- Policies stored in PostgreSQL (cached in Redis)
- Genesis (port 8021) runs 42 checks (9 constitutional compliance checks)

---

## ADR-007: Temporal Workflow Engine for Orchestration

**Status:** Accepted  
**Date:** 2026-01-09  
**Decision Makers:** Systems Architect Agent  
**Context:** Need orchestration for long-running workflows (grooming, trials)

### Context

**Requirements:**
- Grooming lifecycle: 5 stages, 30+ minutes duration
- Trial expiration: Check every 24 hours, send reminders
- Saga patterns: Compensate on failure (e.g., rollback OAuth if certification fails)
- Durable execution: Survive service restarts

**Options:**
- **Celery + Redis**: Task queue (no workflow semantics)
- **AWS Step Functions**: Vendor lock-in
- **Temporal**: Open-source, durable workflows

### Decision

**We will use Temporal Workflow Engine for orchestration.**

### Rationale

**Temporal Workflows:**
- **Durable Execution**: Workflow state persisted in PostgreSQL
- **Automatic Retries**: Activities retried on failure (exponential backoff)
- **Versioning**: Deploy new workflow code without breaking running workflows
- **Saga Pattern**: Compensation logic for rollbacks

**Example Workflow:**
```python
@workflow.defn
class GroomingWorkflow:
    @workflow.run
    async def run(self, agent_id: str):
        # Stage 1: Birth
        await workflow.execute_activity(create_agent, agent_id)
        
        # Stage 2: Assembly (can take hours, durable across restarts)
        await workflow.execute_activity(configure_oauth, agent_id)
        
        # Stage 3: Certification (Genesis 42 checks)
        try:
            await workflow.execute_activity(run_genesis_certification, agent_id)
        except CertificationFailure:
            # Compensate: Delete agent, notify customer
            await workflow.execute_activity(compensate_grooming, agent_id)
            raise
        
        # Stage 4: Activation
        await workflow.execute_activity(activate_agent, agent_id)
```

**Pros:**
- ✅ **Durable**: Workflows survive service restarts, crashes
- ✅ **Saga Patterns**: Built-in compensation logic
- ✅ **Versioning**: Safe upgrades (old workflows continue, new start on new version)
- ✅ **Visibility**: Temporal UI shows workflow history

**Cons:**
- ❌ **Learning Curve**: Developers must learn Temporal SDK
- ❌ **Infrastructure**: Need Temporal server + PostgreSQL

**Alternatives:**
- **Celery**: No workflow semantics, manual retry logic
- **Step Functions**: Vendor lock-in, expensive

### Consequences

**Positive:**
- Grooming lifecycle resilient to failures (service restarts, timeouts)
- Trial expiration workflows run reliably (even if service down for 24 hours)
- Saga patterns simplify error handling (compensate instead of manual rollback)

**Negative:**
- Team must learn Temporal SDK (Python async/await semantics)
- Temporal server adds infrastructure complexity (PostgreSQL for state)

**Mitigation:**
- Document Temporal patterns in grooming_lifecycle_blueprint.md
- Use Temporal UI for debugging workflow history
- Start with simple workflows (trial expiration), progressively add complexity

**Implementation:**
- Orchestration Service (port 8001) runs Temporal worker
- PostgreSQL stores workflow state (temporal_workflows table)
- Activities call backend services (Agent Execution, Governance, Genesis)

---

## ADR-008: CPU-Only ML Models

**Status:** Accepted  
**Date:** 2026-01-09  
**Decision Makers:** Systems Architect Agent, ML Team  
**Context:** Need to keep ML inference costs low (<$10/month)

### Context

**ML Use Cases:**
- Skills extraction (DistilBERT)
- Summarization (BART)
- Embeddings (MiniLM)
- LLM reasoning (Phi-3-mini)
- Forecasting (Prophet)
- Classification (Logistic Regression)
- Time series (LSTM)
- Semantic search (Weaviate)

**Options:**
- **GPU Instances**: Fast inference (10-50ms) but expensive ($300+/month)
- **CPU Instances**: Slower inference (50-200ms) but cheap ($10/month)

### Decision

**We will use CPU-only ML models with quantization and model optimization.**

### Rationale

**CPU Optimization Techniques:**
1. **Quantization**: INT8 models (4x smaller, 2x faster)
2. **Model Distillation**: Use smaller models (DistilBERT vs BERT)
3. **Batch Inference**: Process multiple requests together
4. **Caching**: Cache embeddings in Redis

**Performance:**
- DistilBERT: <100ms (skills extraction)
- BART: <200ms (summarization)
- MiniLM: <50ms (embeddings)
- Phi-3-mini: <200ms (LLM reasoning, quantized)

**Cost:**
- ML Inference Service: 4 vCPU, 2 GB RAM = $15/month
- Total ML cost: <$10/month (included in Cloud Run)

**Pros:**
- ✅ **Cost-Effective**: $10/month vs $300+/month for GPU
- ✅ **Latency**: <200ms acceptable for agent tasks (not real-time chat)
- ✅ **Scalability**: Cloud Run auto-scales CPU instances

**Cons:**
- ❌ **Slower**: 2-5x slower than GPU
- ❌ **Model Limitations**: Cannot run large models (GPT-4, Llama 70B)

**Alternatives:**
- **GPU Instances**: Too expensive for MVP ($300+/month)
- **External APIs (OpenAI)**: Pay-per-token, unpredictable costs

### Consequences

**Positive:**
- ML inference costs <$10/month (within $100/month total budget)
- Agents respond within 2-10 minutes (acceptable for trial mode)
- No vendor lock-in (self-hosted models)

**Negative:**
- Cannot run large LLMs (GPT-4, Llama 70B) → Use OpenAI API for rare cases
- Slower inference may frustrate customers for real-time use cases

**Mitigation:**
- Cache embeddings in Redis (90% cache hit rate expected)
- Batch inference: Process 10 requests together (10x throughput)
- Monitor latency: If >500ms, consider GPU upgrade

**Implementation:**
- ML Inference Service (port 8005): 4 vCPU, 2 GB RAM
- Models stored in GCS (waooaw-ml-models bucket)
- Redis cache for embeddings (1 GB memory)

---

## ADR-009: Pub/Sub for Event-Driven Architecture

**Status:** Accepted  
**Date:** 2026-01-09  
**Decision Makers:** Systems Architect Agent  
**Context:** Need decoupled communication between 17 microservices

### Context

**Requirements:**
- Services must communicate without tight coupling
- Audit logs must capture all events
- Eventual consistency acceptable (not ACID transactions)

**Options:**
- **Synchronous HTTP**: Direct service-to-service calls (tight coupling)
- **Message Queue (RabbitMQ)**: Self-hosted, complex operations
- **GCP Pub/Sub**: Managed, scalable, $4/month

### Decision

**We will use GCP Pub/Sub for event-driven architecture.**

### Rationale

**Pub/Sub Pattern:**
- **Publisher**: Service emits event (e.g., "agent_action_completed")
- **Topic**: Event channel (e.g., "agent-execution-events")
- **Subscriber**: Service listens for events (e.g., Audit Service)

**Example:**
```
Agent Execution (8002) → Pub/Sub (agent-execution-events) → Audit Service (8010)
                                                           → Customer Service (8004)
                                                           → Mobile Push (8017)
```

**16 Topics:**
- agent-execution-events
- config-update-events
- approval-workflow-events
- trial-lifecycle-events
- health-metrics
- incident-alerts
- deployment-events
- audit-log-events
- oauth-refresh-events
- subscription-events
- governance-events
- finance-events
- grooming-lifecycle-events
- ml-inference-events
- policy-evaluation-events
- helpdesk-events

**Pros:**
- ✅ **Decoupled**: Services don't know about each other (pub/sub)
- ✅ **Scalable**: Pub/Sub handles 10M+ messages/month
- ✅ **Reliable**: At-least-once delivery guarantee
- ✅ **Cost-Effective**: $4/month for 10M messages

**Cons:**
- ❌ **Eventual Consistency**: Events not processed instantly (~100ms delay)
- ❌ **Debugging**: Harder to trace event flow across services

**Alternatives:**
- **Synchronous HTTP**: Tight coupling, cascading failures
- **RabbitMQ**: Self-hosted, complex operations

### Consequences

**Positive:**
- Services loosely coupled (easy to add/remove services)
- Audit Service captures all events (100% audit coverage)
- Health Aggregator monitors events for incident detection

**Negative:**
- Eventual consistency: Agent action completed but audit log written 100ms later
- Event ordering not guaranteed (must handle out-of-order events)

**Mitigation:**
- Use idempotent event handlers (safe to process duplicate events)
- Add event_id + timestamp for ordering
- Implement retry logic for failed event processing

**Implementation:**
- 16 Pub/Sub topics (see pubsub_event_schema_registry.yml)
- All services subscribe to relevant topics
- Events include: event_id, timestamp, event_type, payload, previous_hash (for audit)

---

## ADR-010: Firebase Cloud Messaging for Mobile Notifications

**Status:** Accepted  
**Date:** 2026-01-09  
**Decision Makers:** Systems Architect Agent, Mobile Team  
**Context:** Need mobile push notifications for Governor approvals

### Context

**Requirements:**
- Push notifications for approval requests (L0-03: External Execution Approval)
- Support iOS + Android
- Offline queue (deliver when device online)
- Low cost (<$5/month)

**Options:**
- **Firebase Cloud Messaging (FCM)**: Free, unlimited notifications
- **AWS SNS**: $0.50/million notifications
- **Custom WebSocket**: Self-hosted, complex

### Decision

**We will use Firebase Cloud Messaging (FCM) for mobile push notifications.**

### Rationale

**FCM Features:**
- **Free**: Unlimited notifications
- **Cross-Platform**: iOS + Android
- **Offline Queue**: FCM stores notifications for up to 4 weeks
- **High Delivery Rate**: 95%+ delivery within 5 minutes

**Example Notification:**
```json
{
  "to": "device_token_abc123",
  "notification": {
    "title": "Agent Approval Required",
    "body": "Agent needs approval to publish blog post to WordPress",
    "click_action": "APPROVE_ACTION",
  },
  "data": {
    "agent_id": "agent_123",
    "action_id": "action_456",
    "action_type": "wordpress_publish",
  }
}
```

**Pros:**
- ✅ **Free**: $0/month (no usage limits)
- ✅ **Reliable**: 95%+ delivery rate
- ✅ **Offline Queue**: Notifications delivered when device online
- ✅ **Simple Integration**: FCM SDK for iOS/Android

**Cons:**
- ❌ **Google Dependency**: Vendor lock-in (but FCM free forever)
- ❌ **iOS Limitations**: Must use APNs (Apple Push Notification Service) for iOS

**Alternatives:**
- **AWS SNS**: Paid ($0.50/million), no offline queue
- **Custom WebSocket**: Self-hosted, complex, requires always-on connection

### Consequences

**Positive:**
- Governor approvals work even when mobile app closed (offline queue)
- Zero cost for mobile notifications
- High delivery rate (95%+ within 5 minutes)

**Negative:**
- Vendor lock-in to Google Firebase
- iOS requires APNs integration (FCM uses APNs under the hood)

**Mitigation:**
- Abstract FCM behind Mobile Push Service (port 8017)
- Store device tokens in PostgreSQL (easy to migrate to SNS if needed)
- Monitor delivery rates (alert if <90%)

**Implementation:**
- Mobile Push Service (port 8017) calls FCM API
- Device tokens stored in PostgreSQL (device_tokens table)
- Notification types: approval_request, task_completed, trial_ending_soon, ticket_updated

---

## ADR-011: GitHub Issues for Helpdesk

**Status:** Accepted  
**Date:** 2026-01-09  
**Decision Makers:** Systems Architect Agent, Support Team  
**Context:** Need support ticketing system for Platform Portal (PP)

### Context

**Requirements:**
- Support tickets for customers (bug reports, feature requests)
- Ticket assignment, status tracking, SLA monitoring
- Low cost (<$5/month)

**Options:**
- **Zendesk**: $19/agent/month (expensive for MVP)
- **Jira Service Desk**: $20/agent/month
- **GitHub Issues**: Free (already using GitHub)
- **Custom Solution**: Build from scratch (high effort)

### Decision

**We will use GitHub Issues as the helpdesk ticketing system.**

### Rationale

**GitHub Issues Features:**
- **Labels**: Bug, Feature Request, Support (categorize tickets)
- **Assignees**: Assign tickets to Systems Architect Agent, support team
- **Milestones**: Track tickets by sprint
- **Projects**: Kanban board for ticket status (To Do, In Progress, Done)
- **API**: GitHub REST API v3 (automate ticket creation)

**Example Ticket:**
```markdown
Title: Agent X failed to publish blog post
Labels: bug, high-priority
Assignee: @systems-architect-agent
Body:
Customer: customer_123
Agent: agent_456
Error: "WordPress OAuth token expired"
Steps to Reproduce: ...
```

**Pros:**
- ✅ **Free**: GitHub Issues included with repository
- ✅ **Familiar**: Team already uses GitHub
- ✅ **API**: Automate ticket creation, status updates
- ✅ **Notifications**: Email, Slack integration

**Cons:**
- ❌ **Limited SLA Tracking**: No built-in SLA dashboards (must build custom)
- ❌ **No Customer Portal**: Customers cannot access GitHub Issues (internal only)

**Alternatives:**
- **Zendesk**: Too expensive ($19/agent/month)
- **Custom Solution**: High effort, maintenance cost

### Consequences

**Positive:**
- Zero cost for helpdesk ticketing
- Platform Portal (PP) can list, create, update tickets via GitHub API
- Support team uses familiar GitHub interface

**Negative:**
- Customers cannot access tickets directly (must contact support)
- SLA tracking requires custom dashboard (query GitHub API)

**Mitigation:**
- Build PP Dashboard showing ticket metrics (average resolution time, SLA breaches)
- Email notifications to customers when tickets updated
- Consider migrating to Zendesk if ticket volume exceeds 100/month

**Implementation:**
- Helpdesk Service (port 8016) calls GitHub REST API v3
- Ticket cache in PostgreSQL (reduce API calls)
- SLA monitoring: 24-hour response time, 72-hour resolution time

---

## ADR-012: Trial Mode Sandbox Routing

**Status:** Accepted  
**Date:** 2026-01-09  
**Decision Makers:** Systems Architect Agent, Governance Team  
**Context:** Need to sandbox trial agents (prevent real external actions)

### Context

**Constitutional Requirement:**
- Trial agents must not perform real external actions (e.g., publish to live WordPress)
- Trial agents use sandbox APIs (e.g., WordPress staging site)
- Production agents use real APIs after payment

**Options:**
- **Hardcode routing**: `if trial: use_sandbox()`
- **Policy-based routing**: OPA evaluates policies at runtime

### Decision

**We will use Open Policy Agent (OPA) for policy-based sandbox routing.**

### Rationale

**OPA Policy Example:**
```rego
# trial_mode_sandbox_routing.rego
package trial_mode

default allow = false

# Trial agents must use sandbox
allow {
  input.agent.status == "trial_active"
  input.action.target == "sandbox"
}

# Production agents use real APIs
allow {
  input.agent.status == "production_active"
  input.action.target == "production"
}

# Deny trial agents from production APIs
deny {
  input.agent.status == "trial_active"
  input.action.target == "production"
}
```

**Routing Logic:**
```python
# Outside World Connector (port 8009)
def route_action(agent_id: str, action: dict):
    # Query Policy Service (OPA)
    policy_result = policy_service.evaluate({
        "agent": {"id": agent_id, "status": agent.status},
        "action": {"target": action.target, "type": action.type},
    })
    
    if policy_result.allow:
        # Route to sandbox or production
        target_url = get_target_url(action, agent.status)
        return execute_action(target_url, action)
    else:
        raise UnauthorizedError("Policy denied action")
```

**Pros:**
- ✅ **Flexible**: Add new routing rules without code changes
- ✅ **Auditable**: Every policy evaluation logged
- ✅ **Constitutional**: Enforces trial mode restrictions (L0 principles)

**Cons:**
- ❌ **Complexity**: Developers must understand OPA + Rego
- ❌ **Performance**: Policy evaluation adds latency (~10ms)

**Alternatives:**
- **Hardcode routing**: Fast but inflexible (code changes for new rules)

### Consequences

**Positive:**
- Trial agents cannot accidentally perform real external actions
- Production agents seamlessly transition from sandbox → real APIs
- Policy changes require no code deployment (update Rego policies)

**Negative:**
- OPA adds latency (~10ms per action)
- Developers must learn Rego (policy language)

**Mitigation:**
- Cache policy results in Redis (reduce OPA calls by 90%)
- Document sandbox routing in component_trial_mode_state_machine.yml
- Unit tests for policies (verify trial vs production routing)

**Implementation:**
- Policy Service (port 8013) runs OPA server
- Outside World Connector (port 8009) calls Policy Service for routing decisions
- Policies stored in PostgreSQL (cached in Redis)

---

## ADR-013: Open Policy Agent (OPA) for Policy Enforcement

**Status:** Accepted  
**Date:** 2026-01-09  
**Decision Makers:** Systems Architect Agent  
**Context:** Need centralized policy evaluation (RBAC, trial mode, constitutional compliance)

### Context

**Policy Use Cases:**
- RBAC: "Can user X access resource Y?"
- Trial Mode: "Can agent perform action Z?"
- Constitutional: "Does action comply with L0 principles?"
- Rate Limiting: "Has customer exceeded API quota?"

**Options:**
- **Hardcoded logic**: `if trial: sandbox()` (inflexible)
- **Database rules**: `SELECT * FROM policies WHERE ...` (slow)
- **Open Policy Agent (OPA)**: Declarative policy language (Rego)

### Decision

**We will use Open Policy Agent (OPA) for policy evaluation.**

### Rationale

**OPA Architecture:**
- **Policies**: Written in Rego (declarative language)
- **Evaluation**: Fast (<10ms), in-memory
- **Storage**: Policies in PostgreSQL, cached in Redis
- **Versioning**: Git tracks policy changes

**Example Policy:**
```rego
# rbac_policy.rego
package rbac

# Systems Architect can access all resources
allow {
  input.user.role == "systems_architect"
}

# Customers can access their own agents only
allow {
  input.user.role == "customer"
  input.user.id == input.resource.customer_id
}
```

**Pros:**
- ✅ **Declarative**: Policies are data, not code
- ✅ **Fast**: <10ms evaluation
- ✅ **Versioned**: Git tracks policy changes
- ✅ **Testable**: Unit tests for policies

**Cons:**
- ❌ **Learning Curve**: Rego syntax different from Python/JS
- ❌ **Debugging**: Policy errors harder to trace than imperative code

**Alternatives:**
- **Hardcoded logic**: Fast but inflexible
- **Database rules**: Slow, no version control

### Consequences

**Positive:**
- Policy changes require no code deployment (update Rego policies)
- Constitutional compliance enforced via policies
- Easy to add new policy rules (RBAC, rate limiting, etc.)

**Negative:**
- Developers must learn Rego (policy language)
- Policy debugging harder than imperative code

**Mitigation:**
- Document all policies in component_rbac_hierarchy.yml
- Unit tests for policies (verify RBAC, trial mode logic)
- Policy versioning via Git (track changes)

**Implementation:**
- Policy Service (port 8013) runs OPA server
- Policies: trial_mode_sandbox_routing.rego, rbac_policy.rego, constitutional_compliance.rego, trial_mode_api_rate_limits.rego, approval_mode_enforcement.rego
- Policies stored in PostgreSQL (cached in Redis)

---

## ADR-014: Redis for Distributed Caching

**Status:** Accepted  
**Date:** 2026-01-09  
**Decision Makers:** Systems Architect Agent  
**Context:** Need caching to reduce database load and improve latency

### Context

**Cache Use Cases:**
- OAuth tokens (avoid Secret Manager calls)
- ML embeddings (90% cache hit rate)
- Policy evaluations (OPA results)
- Config values (reduce database queries)

**Options:**
- **In-Memory (Python dict)**: Fast but not shared across services
- **Redis**: Distributed, persistent, $10/month
- **Memcached**: Distributed but no persistence

### Decision

**We will use Redis (Memorystore) for distributed caching.**

### Rationale

**Redis Features:**
- **Distributed**: All services share same cache
- **Persistent**: Cache survives service restarts (optional)
- **Data Structures**: Strings, hashes, lists, sets (flexible)
- **TTL**: Automatic expiration (e.g., OAuth tokens expire in 1 hour)

**Example:**
```python
# Cache OAuth token
redis_client.setex(
    key=f"oauth_token:{customer_id}:wordpress",
    value=oauth_token,
    time=3600,  # Expire in 1 hour
)

# Retrieve OAuth token
oauth_token = redis_client.get(f"oauth_token:{customer_id}:wordpress")
if oauth_token:
    return oauth_token
else:
    # Cache miss: Fetch from Secret Manager
    oauth_token = secret_manager.get_secret(...)
    redis_client.setex(...)
    return oauth_token
```

**Pros:**
- ✅ **Distributed**: All services share same cache
- ✅ **Fast**: <1ms latency (in-memory)
- ✅ **Persistent**: Cache survives service restarts
- ✅ **Cost-Effective**: $10/month for 1 GB

**Cons:**
- ❌ **Single Point of Failure**: If Redis down, cache misses increase (not critical)
- ❌ **Memory Limits**: 1 GB cache (must evict old data)

**Alternatives:**
- **In-Memory**: Not shared across services
- **Memcached**: No persistence (cache lost on restart)

### Consequences

**Positive:**
- OAuth token cache reduces Secret Manager calls by 90%
- ML embedding cache reduces ML Inference calls by 90%
- Policy cache reduces OPA calls by 90%

**Negative:**
- Redis downtime causes cache misses (services still work, just slower)
- Memory limits require eviction policy (LRU: Least Recently Used)

**Mitigation:**
- Monitor Redis memory usage (alert if >80%)
- Implement fallback: If Redis down, fetch from source (Secret Manager, OPA)
- Use Redis persistence (AOF: Append-Only File) for crash recovery

**Implementation:**
- Redis (Memorystore Basic): 1 GB memory, $10/month
- Cache keys: oauth_token:{customer_id}:{platform}, ml_embedding:{text_hash}, policy_result:{policy_name}:{input_hash}, config:{key}
- TTL: OAuth tokens (1 hour), embeddings (7 days), policies (5 minutes), config (1 minute)

---

## ADR-015: GCP Cloud Run for Microservices

**Status:** Accepted  
**Date:** 2026-01-09  
**Decision Makers:** Systems Architect Agent, Infrastructure Team  
**Context:** Need serverless compute for 17 backend services

### Context

**Requirements:**
- Deploy 17 microservices
- Auto-scaling (0 → 10 instances based on traffic)
- Low cost (<$100/month)
- Zero downtime deployments

**Options:**
- **GCP Cloud Run**: Serverless containers, pay-per-request
- **GCP Kubernetes Engine (GKE)**: Full control, $75/month minimum (3 nodes)
- **AWS Lambda**: Vendor lock-in, 15-minute timeout limit
- **AWS ECS Fargate**: Similar to Cloud Run, AWS lock-in

### Decision

**We will use GCP Cloud Run for all 17 backend services.**

### Rationale

**Cloud Run Features:**
- **Serverless**: Scale to zero (no cost when idle)
- **Containers**: Deploy any Docker image
- **Auto-Scaling**: 0 → 10 instances automatically
- **Pay-per-Request**: $0.00002400 per request + $0.00000900 per second
- **Blue-Green Deployments**: Traffic splitting built-in

**Cost Example:**
- 17 services * 100,000 requests/month = 1.7M requests
- 1.7M * $0.000024 = $40.80/month (requests)
- 17 services * 1 instance * 30 days * 86,400 seconds * $0.000009 = $37.80/month (compute)
- **Total**: ~$80/month

**Pros:**
- ✅ **Cost-Effective**: Scale to zero (no idle cost)
- ✅ **Auto-Scaling**: Handle traffic spikes (10x) automatically
- ✅ **Zero Ops**: No server management, patching, scaling
- ✅ **Fast Deployments**: <2 minutes to deploy new version

**Cons:**
- ❌ **Cold Starts**: ~500ms latency for first request (mitigated by min instances)
- ❌ **Vendor Lock-In**: Google-specific (mitigated by Docker containers)

**Alternatives:**
- **GKE**: More control but $75/month minimum (expensive for MVP)
- **Lambda**: 15-minute timeout limit (blocks Temporal workflows)
- **ECS Fargate**: AWS lock-in

### Consequences

**Positive:**
- Total cloud cost <$100/month (within budget)
- Auto-scaling handles traffic spikes (10x) without manual intervention
- Zero ops burden (no server patching, scaling, monitoring infrastructure)

**Negative:**
- Cold starts add latency (~500ms) for idle services
- Vendor lock-in to Google Cloud (mitigated by Docker portability)

**Mitigation:**
- Set min_instances=1 for critical services (Health Aggregator, Orchestration)
- Monitor cold start latency (alert if >1 second)
- Use Docker containers (portable to ECS, Kubernetes if migrating)

**Implementation:**
- 17 Cloud Run services (ports 8001-8021)
- Auto-scaling: 1-10 instances per service
- Min instances: 1 for critical services (Health Aggregator, Orchestration), 0 for others
- Deployment: GitHub Actions → Artifact Registry → Cloud Run

---

## Summary

### Key Decisions

| ADR | Decision | Rationale |
|-----|----------|-----------|
| **001** | FastAPI Gateway | Full control, constitutional enforcement, zero cost |
| **002** | Kubernetes-style Reconciliation | Self-healing grooming lifecycle |
| **003** | Hash-Chained Audit Logs | Tamper-proof, constitutional compliance |
| **004** | PostgreSQL RLS | Defense-in-depth, database-level isolation |
| **005** | Blue-Green Deployment | Zero downtime, instant rollback |
| **006** | Constitutional Framework Enforcement | L0 principles enforced via OPA + Governance + Audit |
| **007** | Temporal Workflow Engine | Durable workflows, saga patterns |
| **008** | CPU-Only ML Models | Cost-effective (<$10/month), acceptable latency |
| **009** | Pub/Sub Event-Driven Architecture | Decoupled services, audit coverage |
| **010** | Firebase Cloud Messaging | Free mobile push, offline queue |
| **011** | GitHub Issues for Helpdesk | Zero cost, familiar interface |
| **012** | Trial Mode Sandbox Routing | OPA policy-based routing |
| **013** | Open Policy Agent (OPA) | Declarative policies, versioned, testable |
| **014** | Redis Distributed Caching | 90% cache hit rate, <1ms latency |
| **015** | GCP Cloud Run | Serverless, auto-scaling, <$100/month |

### Trade-offs

**Cost vs Flexibility:**
- Chose FastAPI Gateway over GCP API Gateway (save $3/million requests, keep control)
- Chose CPU ML over GPU ($10/month vs $300/month, accept 200ms latency)
- Chose GitHub Issues over Zendesk ($0 vs $19/agent/month, limited SLA tracking)

**Complexity vs Control:**
- Chose OPA over hardcoded policies (higher learning curve, but flexible)
- Chose Temporal over Celery (steeper learning curve, but durable workflows)
- Chose Kubernetes-style reconciliation (harder to debug, but self-healing)

**Performance vs Safety:**
- Chose hash-chained audit logs (10ms overhead, but tamper-proof)
- Chose PostgreSQL RLS (zero overhead, defense-in-depth)
- Chose Blue-Green deployment (2x resources for 30 min, zero downtime)

### Future Considerations

**Phase 2 Decisions (6-12 months):**
- Migrate FastAPI Gateway → GCP API Gateway (if traffic >10M requests/month)
- Upgrade ML models to GPU (if latency >500ms impacts customers)
- Migrate GitHub Issues → Zendesk (if ticket volume >100/month)
- Implement multi-region deployment (if latency >500ms for customers outside US)

**Phase 3 Decisions (12-24 months):**
- Implement Amendment-001 (Manager + Worker agent teams)
- Add SOC 2 Type II compliance
- Migrate to Kubernetes (GKE) if Cloud Run auto-scaling insufficient
- Add real-time chat (WebSocket) for agent-governor communication

---

**Metadata:**
- **Total ADRs**: 15
- **Last Updated**: 2026-01-09
- **Owned By**: Systems Architect Agent
- **Next Review**: 2026-02-09 (monthly)
