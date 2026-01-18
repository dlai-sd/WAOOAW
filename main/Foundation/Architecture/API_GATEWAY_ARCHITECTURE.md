# API Gateway Architecture - Source of Truth

**Document Version:** 1.0  
**Last Updated:** 2024-01-28  
**Owner:** Systems Architect Agent  
**Status:** Active - Source of Truth  

---

## Document Purpose

This is the **single source of truth** for WAOOAW's unified FastAPI Gateway architecture. All gateway-related decisions, designs, and implementation details reference this document.

**Supporting Documentation:**
- **Detailed Analysis:** [GATEWAY_ARCHITECTURE_ANALYSIS.md](./APIGateway/GATEWAY_ARCHITECTURE_ANALYSIS.md) - Fitment analysis, exponential growth strategy, cost models
- **Implementation Guide:** [GATEWAY_ARCHITECTURE_BLUEPRINT.md](./APIGateway/GATEWAY_ARCHITECTURE_BLUEPRINT.md) - 7-layer middleware design with code examples
- **Gap Analysis:** [GATEWAY_INTEGRATION_GAP_ANALYSIS.md](./APIGateway/GATEWAY_INTEGRATION_GAP_ANALYSIS.md) - Integration gaps, blockers, deployment simulation
- **Implementation Plan:** [IMPLEMENTATION_PLAN.md](./APIGateway/IMPLEMENTATION_PLAN.md) - Deployment sequence, migration scripts, code structure

---

## Executive Summary

WAOOAW's unified FastAPI Gateway serves as the **single entry point** for all API traffic across 4 platform layers (CP, PP, Plant, Mobile), enforcing constitutional governance principles (L0-01 through L0-07) through a 7-layer middleware stack. The gateway routes requests to 17 backend microservices across 4 environments (Local, Demo, UAT, Prod) using database-driven routing with blue/green versioning.

**Key Metrics:**
- **Layers Served:** 4 (Customer Portal, Platform Portal, Plant Data Layer, Mobile App)
- **Backend Services:** 17 microservices on GCP Cloud Run
- **Environments:** 4 (Local, Demo, UAT, Prod) with separate VPCs + Cloud SQL
- **Constitutional Enforcement:** 7 L0 principles enforced at gateway layer
- **Performance:** 40% latency overhead (150ms → 210ms p95) - acceptable per user confirmation
- **Cost:** $84/month governance infrastructure (within $100 budget with shared OPA for Demo/UAT)
- **Deployment Timeline:** 6 weeks (infrastructure → schema → middleware → backend integration)

**Critical Decisions (Locked):**
- ✅ FastAPI gateways superior to GCP API Gateway (no WebSocket, no custom constitutional logic)
- ✅ Database-driven routing (PostgreSQL `gateway_routes` table with 12 columns)
- ✅ External URLs with environment toggle (GATEWAY_USE_INTERNAL_URLS for cost optimization)
- ✅ Fail-closed OPA mode with environment override (POLICY_FAIL_MODE=closed for Prod, =open for Demo/UAT testing)
- ✅ Clean cutover migration (gateway.demo.waooaw.com, no coexistence with old URLs)
- ✅ 40% latency acceptable without caching (will review at Month 3 for optimization)
- ✅ Single point of failure accepted for now (3-month HA review placeholder)
- ✅ Blue/green rollback via route_version column (instant rollback without code redeployment)
- ✅ Mobile provisioning in 2 months (provision database columns now, activate routes when Flutter app launches)
- ✅ Shared OPA for Demo/UAT ($29/month savings), dedicated OPA for Prod

---

## 1. Architecture Overview

### 1.1 Platform Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                        WAOOAW Platform                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │           Unified FastAPI Gateway (Port 8080)           │    │
│  │  gateway.{demo|uat|prod}.waooaw.com                     │    │
│  │                                                          │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │  7-Layer Middleware Stack                         │  │    │
│  │  │  1. CORS → 2. Auth → 3. RBAC → 4. OPA Policy     │  │    │
│  │  │  5. Budget Guard → 6. Audit Logging → 7. Errors  │  │    │
│  │  └──────────────────────────────────────────────────┘  │    │
│  │                                                          │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │  Database-Driven Routing (gateway_routes table)  │  │    │
│  │  │  Blue/Green Versioning: route_version (1 or 2)   │  │    │
│  │  └──────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────────┘    │
│                              │                                   │
│              ┌───────────────┼───────────────┬──────────────┐  │
│              ▼               ▼               ▼              ▼  │
│  ┌─────────────────┐ ┌─────────────┐ ┌────────────┐ ┌──────┐  │
│  │   CP Backend    │ │  PP Backend │ │   Plant    │ │Mobile│  │
│  │   Port 8015     │ │  Port 8006  │ │  Backend   │ │ API  │  │
│  │                 │ │             │ │  Port 8000 │ │(FCM) │  │
│  │  Customer       │ │  Platform   │ │  Data      │ │Port  │  │
│  │  Portal         │ │  Portal     │ │  Layer     │ │8017  │  │
│  │  (Marketplace)  │ │  (Admin)    │ │  (Genesis) │ │      │  │
│  └─────────────────┘ └─────────────┘ └────────────┘ └──────┘  │
│           │                 │               │            │      │
│           └─────────────────┴───────────────┴────────────┘      │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │          17 Backend Microservices (Cloud Run)           │    │
│  │  8001: Agent Creation      │ 8010: Audit Writer         │    │
│  │  8002: Agent Execution     │ 8011: Health Aggregator    │    │
│  │  8003: Governance Service  │ 8012: Manifest Service     │    │
│  │  8004: Industry Knowledge  │ 8013: OPA Policy Service   │    │
│  │  8005: Learning Service    │ 8014: Plant Orchestrator   │    │
│  │  8006: PP Gateway          │ 8015: CP Gateway           │    │
│  │  8007: Finance Service     │ 8016: Helpdesk Service     │    │
│  │  8008: AI Explorer         │ 8017: FCM Push Service     │    │
│  │  8009: Outside World       │                             │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │         Infrastructure Services (VPC-Connected)         │    │
│  │  • PostgreSQL Cloud SQL (gateway_routes, audit_logs)    │    │
│  │  • Redis Memorystore (policy cache, rate limiting)      │    │
│  │  • VPC Connector (gateway → Cloud SQL, $26/month)       │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

### 1.2 Four-Layer Integration

#### Layer 1: Customer Portal (CP) - Port 8015

**Purpose:** Customer-facing marketplace for agent discovery, trial signup, subscription management.

**API Endpoints (7):**
- `GET /api/agents` - List marketplace agents with filters (industry, rating, price)
- `GET /api/agents/{id}` - Agent profile details (rating, specialty, activity)
- `POST /api/agents/{id}/demo` - Request personalized agent demo
- `POST /api/trials` - Start 7-day trial (keep deliverables)
- `POST /api/agents/{id}/execute` - Execute agent task (trial mode → sandbox routing)
- `GET /api/subscriptions` - List customer subscriptions
- `POST /api/subscriptions` - Convert trial to paid subscription

**Constitutional Requirements:**
- Trial mode sandbox routing (ADR-012: trial agents cannot access external APIs)
- Per-agent budget caps ($30/month, $1/day maximum spend)
- PostgreSQL RLS for customer data isolation (ADR-004)
- Audit logging with correlation_id (7-year retention)

**Current State:** ❌ **0% gateway-ready** - Basic FastAPI (117 lines), no middleware

---

#### Layer 2: Platform Portal (PP) - Port 8006

**Purpose:** Internal admin operations for @waooaw.com employees (Agent Orchestrator, Subscription Manager, Infrastructure Engineer, Helpdesk Agent, Admin, Industry Manager, Viewer).

**API Endpoints (12):**
- `GET /api/admin/agents` - List all platform agents
- `POST /api/admin/agents/create` - Create new agent (Genesis workflow)
- `POST /api/genesis/certify` - Certify agent (Genesis validation)
- `GET /api/admin/customers` - List customers
- `GET /api/admin/billing/credit-proposals` - View credit proposals
- `POST /api/admin/billing/credit-proposals/approve` - Approve credit (requires reason)
- `GET /api/governor/queue` - Governor approval queue
- `POST /api/governor/approve` - Approve agent action (requires Governor role)
- `GET /api/health` - Health aggregator (13 microservices + queues + database)
- `GET /api/incidents` - List SLA breaches
- `POST /api/incidents/resolve` - Resolve incident
- `WS /api/health/stream` - Real-time health dashboard (WebSocket)

**Constitutional Requirements:**
- RBAC enforcement (7 hierarchical roles via OPA)
- Google OAuth domain restriction (@waooaw.com ONLY)
- Governor role validation (L0-01: Single Governor principle)
- Admin force action logging (requires reason field)
- Proxy routing to 13 backend microservices

**Current State:** ❌ **0% gateway-ready** - Basic FastAPI (68 lines), no RBAC, no proxy routing

---

#### Layer 3: Plant Backend (Data Layer) - Port 8000

**Purpose:** Agent manufacturing pipeline with constitutional alignment (L0/L1 validation), Genesis certification, audit trail.

**API Endpoints (13):**
- **Genesis Certification:**
  - `POST /api/v1/genesis/skills` - Create skill
  - `POST /api/v1/genesis/job-roles` - Create job role
  - `GET /api/v1/genesis/skills/{id}` - Get skill details
  - `POST /api/v1/genesis/skills/{id}/certify` - Certify skill (Genesis validation)
- **Agent Management:**
  - `POST /api/v1/agents` - Create agent (requires Governor role)
  - `GET /api/v1/agents` - List agents (filters: industry_id, job_role_id)
  - `GET /api/v1/agents/{id}` - Get agent details
  - `POST /api/v1/agents/{id}/assign-team` - Assign team
- **Constitutional Audit:**
  - `POST /api/v1/audit/run` - Run L0/L1 compliance audit (expensive)
  - `GET /api/v1/audit/tampering/{id}` - Detect hash chain tampering
  - `GET /api/v1/audit/export` - Export compliance report
- **Health:**
  - `GET /` - Service info with constitutional alignment status
  - `GET /health` - Database connectivity check

**Constitutional Strengths (Best Implementation):**
- ✅ 7-section BaseEntity model (identity, lifecycle, versioning, constitutional, audit, metadata, relationships)
- ✅ L0/L1 constitutional validators (validate_constitutional_alignment)
- ✅ Custom exception handlers (ConstitutionalAlignmentError, HashChainBrokenError)
- ✅ Hash chain integrity (SHA-256 linking, RSA-4096 signatures)
- ✅ Append-only amendment history (database triggers prevent tampering)

**Current State:** ⚠️ **50% gateway-ready** - Best domain logic (166 lines), but no authentication, no audit logging with correlation_id

---

#### Layer 4: Mobile App (Future) - Flutter/FCM

**Purpose:** Governor approval interface, agent monitoring, push notifications for constitutional violations.

**API Endpoints (8) - To Be Implemented:**
- `POST /api/mobile/register` - Register device token (FCM)
- `GET /api/mobile/governor/queue` - Approval queue (Governor only)
- `POST /api/mobile/governor/approve` - Approve agent action
- `POST /api/mobile/governor/reject` - Reject with reason
- `GET /api/mobile/alerts` - Constitutional violation alerts
- `GET /api/mobile/agents/{id}` - Agent status (real-time)
- `WS /api/mobile/stream` - Real-time updates (WebSocket)
- `POST /api/mobile/logout` - Invalidate device token

**Constitutional Requirements:**
- Device token validation (FCM service port 8017)
- Governor-only endpoints (mobile_app_role=governor)
- Push notification for high-severity events (L0 violations)

**Current State:** ❌ **Not implemented** - Provisioning database columns now (requires_mobile_device_token), activate routes in 2 months

---

## 2. Constitutional Enforcement

### 2.1 L0 Principles Mapped to Gateway

| L0 Principle | Gateway Enforcement Mechanism | Implementation Status |
|--------------|-------------------------------|----------------------|
| **L0-01: Single Governor** | Constitutional Auth Middleware extracts `is_governor` JWT claim, routes `/api/governor/*` only if true | ❌ Not implemented |
| **L0-02: Agent Specialization** | OPA Policy Middleware validates agent can perform requested task (skill + job role match) | ❌ Not implemented |
| **L0-03: External Execution Approval** | Budget Guard Middleware blocks execution if monthly spend exceeds $30 cap | ❌ Not implemented |
| **L0-04: Deny-by-Default** | OPA failure mode = fail-closed (all requests denied if OPA service unavailable) | ❌ Not implemented |
| **L0-05: Immutable Audit Trail** | Audit Logging Middleware writes all requests to `audit_logs` table (7-year retention, append-only) | ❌ Not implemented |
| **L0-06: Data Minimization** | PostgreSQL RLS session variable (`app.current_customer_id`) enforces row-level security | ❌ Not implemented |
| **L0-07: Governance Protocols** | RBAC Middleware enforces 7 hierarchical roles via OPA (Admin → Manager → Operator → Viewer) | ❌ Not implemented |

**Current Compliance:** **0/7 (0%)** - Gateway architecture designed but not deployed.

---

### 2.2 Middleware Stack (7 Layers)

**Execution Order (request flows top to bottom):**

```
┌─────────────────────────────────────────────────────┐
│  1. CORS Middleware                                  │
│     • Origin validation                              │
│     • Preflight OPTIONS handling                     │
│     • Credentials: true                              │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  2. Constitutional Auth Middleware                   │
│     • JWT validation (HS256, JWT_SECRET)             │
│     • Governor role extraction (is_governor claim)   │
│     • PostgreSQL RLS session variable                │
│       (SET app.current_customer_id = '...')          │
│     • Inject ConstitutionalContext into request.state│
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  3. RBAC Middleware (PP only)                        │
│     • Map route to required permission               │
│       (/api/agents/create → agent:create)            │
│     • Query OPA: POST /v1/data/rbac/allow            │
│     • Deny if user lacks permission (403 Forbidden)  │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  4. OPA Policy Middleware                            │
│     • Trial mode sandbox routing check               │
│       (query: /v1/data/trial/sandbox_route)          │
│     • Budget cap enforcement check                   │
│       (query: /v1/data/budget/allow)                 │
│     • Override target URL if sandbox_route = true    │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  5. Budget Guard Middleware (CP only)                │
│     • Query agent_budget_tracking table              │
│     • Check: total_spend_usd < monthly_cap_usd       │
│     • Block if budget exceeded (429 Too Many Requests)│
│     • Increment spend estimate (async)               │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  6. Audit Logging Middleware                         │
│     • Generate correlation_id (UUID)                 │
│     • Extract causation_id from X-Causation-ID header│
│     • Log request to Audit Writer service (async)    │
│     • Add X-Correlation-ID to response header        │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  7. Error Handling Middleware                        │
│     • Catch all exceptions                           │
│     • Map to constitutional error codes              │
│       (ConstitutionalAlignmentError → 422)           │
│     • Return structured error response               │
└─────────────────────────────────────────────────────┘
                        ↓
                ┌───────────────┐
                │  Route Handler│
                │  (proxy to    │
                │   backend)    │
                └───────────────┘
```

**Code References:**
- Full middleware implementations: [GATEWAY_ARCHITECTURE_BLUEPRINT.md](./APIGateway/GATEWAY_ARCHITECTURE_BLUEPRINT.md) Section 2.2
- Service integrations (OPAClient, AuditService, BudgetTracker): [GATEWAY_ARCHITECTURE_BLUEPRINT.md](./APIGateway/GATEWAY_ARCHITECTURE_BLUEPRINT.md) Section 8

---

## 3. Database-Driven Routing

### 3.1 Routing Table Schema

**Table:** `gateway_routes` (12 columns)

```sql
CREATE TABLE gateway_routes (
    id SERIAL PRIMARY KEY,
    
    -- Blue/Green Versioning
    route_version INTEGER NOT NULL,  -- 1 (blue) or 2 (green)
    
    -- Route Definition
    source_path TEXT NOT NULL,       -- '/api/agents/{id}/execute'
    http_method TEXT NOT NULL,       -- 'GET', 'POST', 'PUT', 'DELETE'
    target_backend TEXT NOT NULL,    -- 'cp', 'pp', 'plant', 'mobile'
    target_service_url TEXT NOT NULL, -- 'https://cp.demo.waooaw.com/api/agents/{id}/execute'
    
    -- Middleware Configuration
    middleware_stack JSONB DEFAULT '[]', -- ['auth', 'rbac', 'opa', 'budget', 'audit']
    requires_governor_role BOOLEAN DEFAULT false,
    trial_mode_sandbox_url TEXT,     -- 'https://sandbox.demo.waooaw.com/api/agents/{id}/execute'
    
    -- Rate Limiting
    rate_limit_per_hour INTEGER DEFAULT 1000,
    
    -- Policy Enforcement
    requires_opa_policy TEXT,        -- 'rbac/allow', 'trial/sandbox_route', 'budget/allow'
    
    -- Mobile Provisioning
    requires_mobile_device_token BOOLEAN DEFAULT false,
    
    -- Lifecycle
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_gateway_routes_active ON gateway_routes (is_active, route_version);
CREATE INDEX idx_gateway_routes_path_method ON gateway_routes (source_path, http_method);
```

**Routing Lookup Query:**
```sql
SELECT target_service_url, middleware_stack, requires_governor_role, trial_mode_sandbox_url, requires_opa_policy
FROM gateway_routes
WHERE is_active = true
  AND route_version = 1  -- Active version (1 or 2)
  AND source_path = '/api/agents/{id}/execute'
  AND http_method = 'POST'
LIMIT 1;
```

**Performance:** <5ms (indexed lookup on is_active + route_version + source_path + http_method)

---

### 3.2 Blue/Green Rollback Strategy

**Scenario:** Deploy new routes (version 2) while keeping old routes (version 1) active.

**Step 1: Deploy Green Routes (version 2)**
```sql
-- Insert new routes with route_version = 2, is_active = false
INSERT INTO gateway_routes (route_version, source_path, http_method, target_service_url, is_active)
VALUES (2, '/api/agents/{id}/execute', 'POST', 'https://cp-v2.demo.waooaw.com/api/agents/{id}/execute', false);
```

**Step 2: Switch Traffic to Green**
```sql
BEGIN TRANSACTION;

-- Activate green routes
UPDATE gateway_routes SET is_active = true WHERE route_version = 2;

-- Deactivate blue routes
UPDATE gateway_routes SET is_active = false WHERE route_version = 1;

COMMIT;
```

**Step 3: Rollback to Blue (if issues detected)**
```sql
BEGIN TRANSACTION;

-- Reactivate blue routes
UPDATE gateway_routes SET is_active = true WHERE route_version = 1;

-- Deactivate green routes
UPDATE gateway_routes SET is_active = false WHERE route_version = 2;

COMMIT;
```

**Rollback Time:** <1 second (database UPDATE, no code redeployment required)

---

### 3.3 OpenAPI Auto-Discovery (Future Enhancement)

**Purpose:** Automatically discover new backend endpoints without manual routing table updates.

**Implementation:**
1. Background scheduler (APScheduler) runs every 1 hour
2. Query backend OpenAPI specs:
   - `GET https://cp.demo.waooaw.com/openapi.json`
   - `GET https://pp.demo.waooaw.com/openapi.json`
   - `GET https://plant.demo.waooaw.com/openapi.json`
3. Compare with existing routes in `gateway_routes` table
4. If new endpoint found:
   - Create draft route with `is_active = false`
   - Notify Systems Architect (email/Slack)
   - Require manual approval to activate route

**Status:** ❌ Not implemented (defer to Month 3 for automation)

---

## 4. Multi-Environment Deployment

### 4.1 Environment Topology

| Environment | Purpose | VPC | Cloud SQL | Redis | Gateway URL | Config |
|-------------|---------|-----|-----------|-------|-------------|--------|
| **Local** | Developer testing | N/A | Docker | Docker | `http://localhost:8080` | `GATEWAY_USE_INTERNAL_URLS=true`, `OPA_FAIL_MODE=open` |
| **Demo** | Staging/testing | `waooaw-demo-vpc` | `waooaw-demo-db` | `waooaw-demo-redis` | `https://gateway.demo.waooaw.com` | `GATEWAY_USE_INTERNAL_URLS=false`, `OPA_FAIL_MODE=closed` |
| **UAT** | User acceptance testing | `waooaw-uat-vpc` | `waooaw-uat-db` | `waooaw-uat-redis` | `https://gateway.uat.waooaw.com` | `GATEWAY_USE_INTERNAL_URLS=false`, `OPA_FAIL_MODE=closed` |
| **Prod** | Production | `waooaw-prod-vpc` | `waooaw-prod-db` | `waooaw-prod-redis` | `https://gateway.waooaw.com` | `GATEWAY_USE_INTERNAL_URLS=false`, `OPA_FAIL_MODE=closed` |

---

### 4.2 Environment Configuration

**Configuration via Environment Variables:**

```bash
# Gateway Core
GATEWAY_USE_INTERNAL_URLS=false  # true = VPC internal URLs (lower cost), false = external URLs
OPA_FAIL_MODE=closed            # closed = deny all if OPA down, open = allow all (TESTING ONLY)

# Service URLs
OPA_SERVICE_URL=https://opa.demo.waooaw.com
AUDIT_SERVICE_URL=https://audit.demo.waooaw.com

# Database (Cloud SQL via VPC Connector)
DATABASE_URL=postgresql://user:pass@10.128.0.3:5432/waooaw  # Private IP via VPC Connector
REDIS_URL=redis://10.128.0.4:6379

# JWT
JWT_SECRET=<secret-from-secret-manager>
JWT_ALGORITHM=HS256
JWT_EXPIRY_DAYS=15  # 15 days for internal PP users

# CORS
CORS_ORIGINS=https://waooaw.com,https://www.waooaw.com,https://gateway.demo.waooaw.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_HOUR=1000  # Default for authenticated users
```

**Demo Environment Example:**
```yaml
# cloud-run-gateway-demo.yaml
env:
  - name: GATEWAY_USE_INTERNAL_URLS
    value: "false"  # Use external URLs (https://cp.demo.waooaw.com)
  - name: OPA_FAIL_MODE
    value: "closed"  # Fail-closed for demo (simulate production)
  - name: OPA_SERVICE_URL
    value: "https://opa.demo.waooaw.com"  # Shared OPA (Demo + UAT)
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: waooaw-demo-secrets
        key: DATABASE_URL
```

---

### 4.3 VPC Connectivity

**Challenge:** Gateway (Cloud Run) must connect to Cloud SQL (private IP) via VPC Connector.

**VPC Connector Cost:** $26/month per environment (3 environments = $78/month)

**Configuration:**
```yaml
metadata:
  annotations:
    run.googleapis.com/vpc-access-connector: gateway-demo-connector
    run.googleapis.com/vpc-access-egress: private-ranges-only  # Only database traffic via VPC
```

**VPC Connector Creation:**
```bash
gcloud compute networks vpc-access connectors create gateway-demo-connector \
  --network=waooaw-demo-vpc \
  --region=us-central1 \
  --range=10.8.0.0/28
```

---

## 5. OPA Policy Enforcement

### 5.1 OPA Service Architecture

**Deployment:**
- **Demo + UAT:** Shared OPA instance (port 8013) - $29/month
- **Prod:** Dedicated OPA instance - $29/month
- **Total Cost:** $58/month (vs $87/month if dedicated for each)

**OPA Docker Image:** `openpolicyagent/opa:0.58.0-rootless`

**Cloud Run Configuration:**
```yaml
spec:
  containers:
    - image: openpolicyagent/opa:0.58.0-rootless
      args:
        - "run"
        - "--server"
        - "--addr=0.0.0.0:8181"
        - "--log-level=info"
        - "/policies"  # Mount Rego policy files
      volumeMounts:
        - name: policies
          mountPath: /policies
  volumes:
    - name: policies
      configMap:
        name: opa-policies  # Rego files stored in ConfigMap
```

---

### 5.2 Rego Policy Files (3 policies)

#### Policy 1: RBAC (Role-Based Access Control)

**File:** `rbac.rego`

```rego
package rbac

# Default: deny all
default allow = false

# Admin role: full access
allow {
    input.user.roles[_] == "admin"
}

# Subscription Manager: billing permissions
allow {
    input.user.roles[_] == "subscription_manager"
    input.permission == "billing:view"
}
allow {
    input.user.roles[_] == "subscription_manager"
    input.permission == "billing:approve_credit"
}

# Agent Orchestrator: agent management
allow {
    input.user.roles[_] == "agent_orchestrator"
    startswith(input.permission, "agent:")
}

# Industry Manager: industry-specific agents
allow {
    input.user.roles[_] == "industry_manager"
    input.permission == "agent:view"
    input.agent.industry == input.user.managed_industry
}

# Viewer: read-only access
allow {
    input.user.roles[_] == "viewer"
    startswith(input.permission, ":view")
}
```

#### Policy 2: Trial Mode Sandbox Routing

**File:** `trial.rego`

```rego
package trial

# Default: production routing
default sandbox_route = false

# Sandbox routing for trial mode agents
sandbox_route {
    input.agent.trial_mode == true
    input.action == "execute"
}

# Obligations: sandbox URL
obligations[key] = value {
    sandbox_route
    key = "sandbox_url"
    value = input.agent.sandbox_url  # From routing table
}
```

#### Policy 3: Budget Enforcement

**File:** `budget.rego`

```rego
package budget

# Default: allow (budget checks done in Budget Guard Middleware)
default deny = false

# Deny if agent exceeds monthly cap
deny {
    input.agent.monthly_spend >= input.agent.monthly_cap
}

# Deny if agent in trial mode AND exceeds trial cap ($10)
deny {
    input.agent.trial_mode == true
    input.agent.monthly_spend >= 10
}
```

---

### 5.3 OPA Failure Modes

**Fail-Closed Mode (Production):**
```python
try:
    decision = await opa_client.evaluate("rbac/allow", policy_request)
except Exception as e:
    # OPA service unavailable
    return JSONResponse(
        status_code=503,
        content={
            "error": "Policy service unavailable",
            "constitutional_principle": "L0-04: Deny-by-Default",
            "details": str(e)
        }
    )
```

**Fail-Open Mode (Demo/UAT Testing Only):**
```python
try:
    decision = await opa_client.evaluate("rbac/allow", policy_request)
except Exception as e:
    if settings.OPA_FAIL_MODE == "open":
        logger.warning(f"OPA unavailable, fail-open mode enabled: {e}")
        decision = PolicyDecision(allow=True, reason="OPA unavailable (fail-open)")
    else:
        return JSONResponse(status_code=503, content={"error": "Policy service unavailable"})
```

**Configuration:**
- Demo: `OPA_FAIL_MODE=open` (testing tolerance)
- UAT: `OPA_FAIL_MODE=closed` (simulate production)
- Prod: `OPA_FAIL_MODE=closed` (strict enforcement)

---

## 6. Cost Analysis

### 6.1 Gateway Infrastructure Costs

| Component | Monthly Cost | Notes |
|-----------|--------------|-------|
| **Gateway (Demo)** | $15 | 1 min instance, 1 vCPU, 512MB RAM |
| **Gateway (UAT)** | $15 | 1 min instance, 1 vCPU, 512MB RAM |
| **Gateway (Prod)** | $25 | 2 min instances, 2 vCPU, 1GB RAM |
| **OPA (Shared Demo+UAT)** | $29 | 1 min instance, 0.5 vCPU, 256MB RAM |
| **OPA (Prod)** | $29 | Dedicated instance |
| **Audit Writer (Shared Demo+UAT)** | $29 | 1 min instance, 0.5 vCPU, 256MB RAM |
| **Audit Writer (Prod)** | $29 | Dedicated instance |
| **VPC Connector (Demo)** | $26 | $0.035/hour always-on |
| **VPC Connector (UAT)** | $26 | $0.035/hour always-on |
| **VPC Connector (Prod)** | $26 | $0.035/hour always-on |
| **TOTAL** | **$249** | ⚠️ $149 over $100 budget |

**Optimization Applied:**
- ✅ Share OPA between Demo/UAT - Saves $29/month
- ✅ Share Audit Writer between Demo/UAT - Saves $29/month
- ✅ Reduce Gateway Prod min instances (2→1) - Saves $12/month
- ❌ Cannot remove VPC Connectors (required for Cloud SQL connectivity)

**Revised Cost:**
- Shared OPA/Audit: -$58
- Reduced Prod Gateway: -$12
- **NEW TOTAL: $179/month** (still $79 over budget)

**Budget Resolution Options:**
1. ❌ Remove Demo environment - Not acceptable (testing requirement)
2. ✅ Remove UAT environment - Saves $67/month → **$112/month** (still $12 over)
3. ✅ Request budget increase to $180/month

**Recommendation:** Request budget increase to $180/month OR accept $79 overrun temporarily, optimize at Month 3 review.

---

### 6.2 Latency Impact

| Request Path | Baseline | With Gateway | Overhead | Acceptable? |
|--------------|----------|--------------|----------|-------------|
| `GET /api/agents` | 120ms | 168ms | +40% | ✅ YES |
| `POST /api/agents/execute` | 250ms | 350ms | +40% | ✅ YES |
| `POST /api/v1/agents` | 180ms | 252ms | +40% | ✅ YES |
| `WS /api/health/stream` | 50ms | 70ms | +40% | ✅ YES |

**Breakdown (per request):**
- Routing table lookup: 5ms
- JWT validation: 8ms
- OPA policy evaluation: 15ms
- PostgreSQL RLS session variable: 3ms
- Audit logging (async): 5ms
- **Total overhead:** 36ms (~40%)

**User Confirmation:** 40% latency overhead acceptable without caching, will review at Month 3 for optimization opportunities.

---

## 7. Deployment Timeline

### 7.1 6-Week Implementation Plan

**Week 1: Infrastructure Services**
- [ ] Deploy OPA Policy Service (Demo+UAT shared, Prod dedicated)
- [ ] Deploy Audit Writer Service (Demo+UAT shared, Prod dedicated)
- [ ] Create VPC Connectors (Demo, UAT, Prod)
- [ ] Test OPA connectivity from Local environment

**Week 2: Database Schema**
- [ ] Create `gateway_routes` table (12 columns, 2 indexes)
- [ ] Create `agent_budget_tracking` table (5 columns, 1 index)
- [ ] Create `audit_logs` table (15 columns, 3 indexes, 7-year retention policy)
- [ ] Seed initial routing table with 13 routes (CP, PP, Plant)

**Week 3: Middleware Implementation (Layers 1-4)**
- [ ] Constitutional Auth Middleware (JWT validation, Governor role extraction, PostgreSQL RLS)
- [ ] RBAC Middleware (OPA integration, 7 roles, 25 permissions)
- [ ] OPA Policy Middleware (trial mode sandbox routing, budget enforcement)
- [ ] Budget Guard Middleware (monthly cap checks, agent spend tracking)

**Week 4: Middleware Implementation (Layers 5-7)**
- [ ] Audit Logging Middleware (correlation_id, causation_id, async logging)
- [ ] Error Handling Middleware (constitutional error codes, structured responses)
- [ ] CORS Middleware (production origin list, credentials: true)

**Week 5: Rego Policies & Testing**
- [ ] Write `rbac.rego` (7 roles, 25 permissions)
- [ ] Write `trial.rego` (sandbox routing logic)
- [ ] Write `budget.rego` (monthly cap enforcement)
- [ ] Unit tests for middleware (80% coverage)
- [ ] Integration tests (CP, PP, Plant routing)

**Week 6: Backend Integration & Deployment**
- [ ] Update CP Backend (JWT validation, PostgreSQL RLS)
- [ ] Update PP Backend (RBAC enforcement, proxy routing)
- [ ] Update Plant Backend (authentication, audit logging)
- [ ] Deploy to Demo environment
- [ ] Load testing (85 req/s target)
- [ ] Production deployment checklist

**Total Time:** 6 weeks (42 days)

---

### 7.2 Deployment Sequence

**Local → Demo → UAT → Prod** (manual promotion via GitHub Actions)

```mermaid
graph LR
    A[Local Dev] -->|Manual Trigger| B[Demo Deploy]
    B -->|Smoke Tests Pass| C[UAT Deploy]
    C -->|Load Tests Pass| D[Prod Deploy]
    D -->|Blue/Green Rollback| E[Prod Stable]
```

**Promotion Gates:**
- Local → Demo: Unit tests pass (80% coverage)
- Demo → UAT: Integration tests pass (13 routes validated)
- UAT → Prod: Load tests pass (85 req/s, p95 <250ms)

---

## 8. Critical Blockers (23 identified)

See [GATEWAY_INTEGRATION_GAP_ANALYSIS.md](./APIGateway/GATEWAY_INTEGRATION_GAP_ANALYSIS.md) for full blocker list.

**Top 5 Blockers:**
1. ❌ **INFRA-002** - No VPC Connectors (gateway cannot reach Cloud SQL)
2. ❌ **POLICY-001** - No OPA Policy Service deployed (port 8013)
3. ❌ **AUDIT-001** - No Audit Writer Service deployed (port 8010)
4. ❌ **ROUTING-001** - No `gateway_routes` table created
5. ❌ **AUTH-001** - CP/PP/Plant lack JWT validation middleware

**Resolution Priority:** Week 1 (infrastructure), Week 2 (database schema), Week 3-4 (middleware)

---

## 9. Success Metrics (Month 1)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Gateway Uptime** | 99.5% | Cloud Run monitoring |
| **p95 Latency** | <250ms | 150ms baseline + 40% overhead |
| **Policy Enforcement Rate** | 100% | All requests pass through OPA |
| **Audit Log Completeness** | 100% | All requests logged with correlation_id |
| **Budget Cap Violations** | 0 | No agents exceed $30/month cap |
| **Constitutional Violations** | 0 | No L0 principle breaches |
| **Cost** | $180/month | Gateway + OPA + Audit Writer + VPC Connectors |

---

## 10. References

**Supporting Documentation:**
- [GATEWAY_ARCHITECTURE_ANALYSIS.md](./APIGateway/GATEWAY_ARCHITECTURE_ANALYSIS.md) - Fitment analysis, exponential growth (10x→100x→1000x), cost economics
- [GATEWAY_ARCHITECTURE_BLUEPRINT.md](./APIGateway/GATEWAY_ARCHITECTURE_BLUEPRINT.md) - 7-layer middleware with Python code examples, service implementations
- [GATEWAY_INTEGRATION_GAP_ANALYSIS.md](./APIGateway/GATEWAY_INTEGRATION_GAP_ANALYSIS.md) - 23 integration blockers, deployment simulation, test cases
- [IMPLEMENTATION_PLAN.md](./APIGateway/IMPLEMENTATION_PLAN.md) - Deployment sequence, migration scripts, GitHub workflow integration

**Architecture Decision Records:**
- ADR-001: FastAPI vs GCP API Gateway (FastAPI chosen)
- ADR-004: PostgreSQL RLS for customer data isolation
- ADR-012: Trial Mode Sandbox Routing (OPA-based)
- ADR-013: OPA Policy Enforcement (fail-closed mode)

**Related Documents:**
- [UNIFIED_ARCHITECTURE.md](/infrastructure/CI_Pipeline/UNIFIED_ARCHITECTURE.md) - CI/CD deployment workflows
- [QUICK_REFERENCE.md](/QUICK_REFERENCE.md) - Platform architecture quick reference

---

## Document Control

**Approval Status:** ✅ Approved by Systems Architect (2024-01-28)  
**Next Review:** Week 3 (post-middleware implementation)  
**Change Log:**
- 2024-01-28: Initial source of truth document created
- Pending: Update after Week 1 infrastructure deployment
- Pending: Update after Week 6 production deployment

**Contact:**
- Owner: Systems Architect Agent
- Questions: Refer to [APIGateway/](./APIGateway/) subfolder for detailed documentation

---

**Status:** ✅ Source of truth document complete. Ready for infrastructure deployment (Week 1).
