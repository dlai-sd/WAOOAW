# Gateway Final Implementation Plan - Complete Constitutional Layer

**Version:** 1.1  
**Date:** 2026-01-17 (Peer Review Complete)  
**Strategy:** Full gateway layer with 7-layer constitutional middleware  
**Story Size:** Medium-Large (5-10 days per story)  
**Total Stories:** 24 stories across 6 phases (+6 new stories from peer review)  
**Total Timeline:** 20-24 weeks (5-6 months, +4 weeks for robustness)  
**Prerequisites:** Phases 1-3 complete (CP/PP/Plant direct integration working)

**Peer Review Status:** ✅ APPROVED with Critical Gaps Addressed  
**Implementation Ready:** ✅ YES (all P0 gaps resolved)

---

## Executive Summary

This plan implements the **complete constitutional gateway layer** described in GATEWAY_ARCHITECTURE_BLUEPRINT.md. After Phases 1-3 (direct integration), this adds enterprise-grade infrastructure for exponential growth.

### What We're Building

**From (Current - Phases 1-3):**
```
CP Frontend ──> Plant Backend (direct)
PP Frontend ──> PP Backend ──> Plant Backend (basic proxy)
```

**To (Final - Phase 4 Complete):**
```
CP Frontend ──> CP Gateway (7 middleware layers) ──> Plant Backend
                 │
                 ├─> Auth Middleware (JWT + Governor)
                 ├─> RBAC Middleware (OPA decisions)
                 ├─> Policy Middleware (trial mode routing)
                 ├─> Budget Guard (agent $1/day caps)
                 ├─> Audit Middleware (correlation_id + constitutional context)
                 ├─> Error Handler (constitutional exceptions)
                 └─> WebSocket Handler (real-time updates)

PP Frontend ──> PP Gateway (same 7 layers + RBAC) ──> Plant Backend
```

### Value Delivered

| Capability | Before (Direct) | After (Gateway) | Business Impact |
|------------|----------------|-----------------|-----------------|
| **Auth** | JWT basic | JWT + Governor role + trial mode | Governor approval workflows enabled |
| **Authorization** | Route-level | OPA policy-based RBAC | Constitutional compliance automated |
| **Rate Limiting** | None | Per-customer tiered limits | Prevents abuse, supports pricing tiers |
| **Audit Trail** | Basic logs | correlation_id + causation_id + constitutional context | L0 compliance, regulatory ready |
| **Budget Enforcement** | Manual | Automated $1/day per agent caps | Cost controls, prevents runaway spending |
| **Observability** | Blind | Correlation tracing + GCP Cloud Logging | Troubleshooting 10x faster |
| **Security** | Basic | Policy-driven, deny-by-default | Ready for SOC 2, ISO 27001 |
| **Scalability** | 100 users | 10,000 users with circuit breakers | Exponential growth ready |
| **Infrastructure Cost** | $55-85/month | **$55-85/month (no increase)** | Zero infrastructure cost increase |

---

## Phase 0: Foundation & Infrastructure Setup (3 weeks, +1 week from peer review)

### GW-00P: Infrastructure Prerequisites & Contracts

**Priority:** P0 (Blocker for all stories)  
**Effort:** 5 days  
**Owner:** Platform Team + Tech Lead  

**Problem:**
- No formal JWT token contract between CP/PP/Plant
- No Plant API versioning strategy
- No Terraform modules for gateway infrastructure
- Environment variables and secrets not documented
- Critical infrastructure gaps prevent implementation

**User Story:**
```gherkin
As a platform engineer
I want all contracts, infrastructure, and configuration documented upfront
So that implementation teams have zero ambiguity
```

**Acceptance Criteria:**

#### 1. JWT Token Contract (GAP-002 Resolution)

- [ ] JWT schema documented and validated:
  ```json
  {
    "user_id": "USER-abc123",
    "email": "user@example.com",
    "customer_id": "CUST-123",
    "roles": ["customer", "governor"],
    "governor_agent_id": "AGENT-xyz789",
    "trial_mode": true,
    "trial_expires_at": "2026-01-24T00:00:00Z",
    "iat": 1705492800,
    "exp": 1705579200,
    "iss": "waooaw-cp",
    "sub": "USER-abc123"
  }
  ```
- [ ] JWT validation library: `PyJWT==2.8.0`
- [ ] Contract tests added (JSON Schema validation)
- [ ] Documentation: `docs/gateway/JWT_CONTRACT.md`

#### 2. Plant API Contract (GAP-003 Resolution)

- [ ] Plant API contract documented:
  ```yaml
  Base URL: https://plant.waooaw.com/api/v1
  Sandbox URL: https://plant-sandbox.waooaw.com/api/v1
  
  Required Headers:
    - Authorization: Bearer <JWT_TOKEN>
    - X-Correlation-ID: <UUID>
    - X-Causation-ID: <UUID>
    - X-Customer-ID: <CUSTOMER_ID>
    - X-Trial-Mode: "true" | "false"
  
  Versioning Strategy:
    - /api/v1/* (current, stable)
    - /api/v2/* (future, breaking changes require 90-day notice)
  
  Breaking Change Policy:
    - Minimum 90-day deprecation notice
    - Parallel v1/v2 support for 180 days
    - Sunset HTTP header: "Sunset: Sat, 31 Dec 2026 23:59:59 GMT"
  ```
- [ ] Documentation: `docs/gateway/PLANT_API_CONTRACT.md`

#### 3. Environment Variables (GAP-006 Resolution)

- [ ] Complete environment variable list documented:
  ```bash
  # Authentication
  JWT_SECRET=<secret>
  JWT_ALGORITHM=HS256
  JWT_EXPIRATION_HOURS=24
  
  # OPA Integration
  OPA_SERVICE_URL=https://opa-policy-engine-PROJECT_ID.a.run.app
  OPA_TIMEOUT_MS=500
  OPA_CACHE_TTL_SECONDS=300
  
  # PostgreSQL (Audit Logs)
  DATABASE_URL=postgresql://user:pass@/cloudsql/PROJECT_ID:REGION:plant-sql-demo/plant_db
  DATABASE_POOL_SIZE=20
  DATABASE_MAX_OVERFLOW=10
  
  # Redis (Budget + Rate Limiting)
  REDIS_HOST=10.0.0.3
  REDIS_PORT=6379
  REDIS_DB=0
  REDIS_POOL_SIZE=10
  
  # Plant Backend
  PLANT_API_URL=https://plant.demo.waooaw.com/api/v1
  PLANT_SANDBOX_URL=https://plant-sandbox.demo.waooaw.com/api/v1
  PLANT_TIMEOUT_SECONDS=30
  
  # Rate Limiting
  RATE_LIMIT_TRIAL=100
  RATE_LIMIT_PAID=1000
  RATE_LIMIT_ENTERPRISE=10000
  
  # Budget Enforcement
  AGENT_DAILY_CAP_USD=1.00
  PLATFORM_MONTHLY_CAP_USD=100.00
  
  # Observability
  GCP_PROJECT_ID=waooaw-oauth
  OTEL_EXPORTER_OTLP_ENDPOINT=https://cloudtrace.googleapis.com/v1/projects/waooaw-oauth/traces
  
  # Feature Flags
  ENABLE_AUTH_MIDDLEWARE=true
  ENABLE_RBAC_MIDDLEWARE=true
  ENABLE_POLICY_MIDDLEWARE=true
  ENABLE_BUDGET_MIDDLEWARE=true
  ENABLE_AUDIT_MIDDLEWARE=true
  ENABLE_ERROR_MIDDLEWARE=true
  ENABLE_WEBSOCKET_MIDDLEWARE=false
  
  # Cost Guards
  COST_GUARD_80_ENABLED=true
  COST_GUARD_95_ENABLED=true
  COST_GUARD_100_ENABLED=true
  ```

#### 4. Secret Manager Mappings (GAP-007 Resolution)

- [ ] GCP Secret Manager secrets created:
  ```yaml
  Secrets:
    - jwt-secret-cp          # CP JWT signing key (HS256)
    - jwt-secret-pp          # PP JWT signing key (HS256)
    - database-password      # PostgreSQL password
    - redis-password         # Redis AUTH password (optional)
    - opa-bundle-key         # OPA policy bundle encryption key
  
  IAM Permissions:
    - CP Gateway Service Account: roles/secretmanager.secretAccessor
    - PP Gateway Service Account: roles/secretmanager.secretAccessor
  ```

#### 5. Terraform Modules (GAP-010 Resolution)

- [ ] Terraform module structure created:
  ```hcl
  infrastructure/terraform/modules/gateway/
  ├── main.tf
  ├── variables.tf
  ├── outputs.tf
  ├── opa-service.tf       # OPA Cloud Run service
  ├── secrets.tf           # Secret Manager secrets
  ├── iam.tf               # Service account IAM bindings
  └── monitoring.tf        # Cloud Monitoring dashboards
  
  # Required IAM roles for gateway service accounts:
  - roles/cloudsql.client        # Gateway → Cloud SQL
  - roles/redis.editor           # Gateway → Redis
  - roles/secretmanager.secretAccessor  # Gateway → Secrets
  - roles/logging.logWriter      # Gateway → Cloud Logging
  - roles/monitoring.metricWriter # Gateway → Cloud Monitoring
  ```

#### 6. OPA Deployment Model (GAP-004 Resolution)

- [ ] OPA deployment clarified: **Separate Cloud Run Service** (not sidecar)
  ```yaml
  # infrastructure/terraform/modules/gateway/opa-service.tf
  resource "google_cloud_run_service" "opa" {
    name     = "opa-policy-engine"
    location = var.region
    
    template {
      spec {
        containers {
          image = "openpolicyagent/opa:0.59.0"
          args  = ["run", "--server", "--addr=0.0.0.0:8181"]
          
          resources {
            limits = {
              memory = "128Mi"
              cpu    = "100m"
            }
          }
          
          env {
            name  = "OPA_LOG_LEVEL"
            value = "info"
          }
        }
        
        service_account_name = google_service_account.opa.email
      }
    }
    
    traffic {
      percent         = 100
      latest_revision = true
    }
  }
  
  # Internal-only (VPC access)
  resource "google_cloud_run_service_iam_member" "opa_invoker" {
    service  = google_cloud_run_service.opa.name
    location = google_cloud_run_service.opa.location
    role     = "roles/run.invoker"
    member   = "serviceAccount:${google_service_account.cp_gateway.email}"
  }
  ```

**Technical Tasks:**
1. Create `docs/gateway/JWT_CONTRACT.md` with JSON schema
2. Create `docs/gateway/PLANT_API_CONTRACT.md` with OpenAPI spec
3. Create `.env.template` files for CP/PP with all variables
4. Create Terraform `modules/gateway/` with all resources
5. Document Secret Manager setup in README
6. Create OPA Cloud Run service definition
7. Write contract validation tests

**Dependencies:** None (foundational)

**Validation:**
```bash
# Test JWT contract validation
python -m pytest tests/contracts/test_jwt_schema.py

# Test environment variables completeness
./scripts/validate-env.sh

# Test Terraform syntax
cd infrastructure/terraform/modules/gateway && terraform validate

# Test Secret Manager access
gcloud secrets versions access latest --secret="jwt-secret-cp"
```

---

### GW-000: OPA Policy Engine Deployment

**Priority:** P0 (Blocker for all gateway features)  
**Effort:** 5 days  
**Owner:** Platform Team  

**Problem:**
- No centralized policy decision point
- Authorization logic scattered across CP/PP/Plant codebases
- Constitutional rules hardcoded, not data-driven

**User Story:**
```gherkin
As a platform architect
I want OPA deployed as a sidecar container with constitutional policies
So that all authorization decisions flow through a single policy engine
```

**Acceptance Criteria:**
- [ ] OPA deployed as Cloud Run service (**separate service**, ~128MB RAM, 100m CPU)
  - Service URL: `https://opa-policy-engine-PROJECT_ID.a.run.app`
  - Internal-only access (VPC connector, no public ingress)
  - Cost: $5-8/month (always-on for <10ms latency)
- [ ] OPA policies written in Rego (with full code examples):

**Policy 1: `trial_mode.rego`** (Trial user restrictions)
```rego
package trial_mode

import future.keywords.if

default allow := false
default reason := ""

# Allow if under task limit and trial not expired
allow if {
    input.task_count_today < 10
    not trial_expired
}

# Trial has expired
trial_expired if {
    time.now_ns() > time.parse_rfc3339_ns(input.trial_expires_at)
}

# Reason for denial
reason := "Trial limit 10 tasks/day exceeded" if {
    input.task_count_today >= 10
}

reason := "Trial period expired" if {
    trial_expired
}
```

**Policy 2: `governor_role.rego`** (Governor approval workflows)
```rego
package governor_role

import future.keywords.if

default requires_approval := false

# External execution requires Governor approval
requires_approval if {
    input.action == "agent.execute.external"
    input.trial_mode == false
}

# Agent creation requires Governor approval (unless Governor)
requires_approval if {
    input.action == "agent.create"
    not is_governor
}

# Check if user has Governor role
is_governor if {
    "governor" in input.roles
}

# Approval bypass for Governors
allow if {
    is_governor
}
```

**Policy 3: `agent_budget.rego`** (Agent spending caps)
```rego
package agent_budget

import future.keywords.if

default allow := false
default reason := ""

# Agent daily cap: $1.00
allow if {
    input.agent_spend_today < 1.00
    input.platform_spend_month < 100.00
}

reason := sprintf("Agent budget $%.2f/day exceeded (spent: $%.2f)", 
    [1.00, input.agent_spend_today]) if {
    input.agent_spend_today >= 1.00
}

reason := sprintf("Platform budget $%.2f/month exceeded (spent: $%.2f)", 
    [100.00, input.platform_spend_month]) if {
    input.platform_spend_month >= 100.00
}
```

**Policy 4: `rbac_pp.rego`** (PP 7-role hierarchy)
```rego
package rbac_pp

import future.keywords.if

default allow := false

# Role hierarchy (higher roles inherit lower permissions)
role_hierarchy := {
    "admin": 7,
    "subscription_manager": 6,
    "agent_orchestrator": 5,
    "infrastructure_engineer": 4,
    "helpdesk_agent": 3,
    "industry_manager": 2,
    "viewer": 1
}

# Permission mappings
permissions := {
    "agent:create": ["admin", "agent_orchestrator"],
    "agent:approve": ["admin", "agent_orchestrator"],
    "subscription:force_cancel": ["admin", "subscription_manager"],
    "billing:approve_credit": ["admin", "subscription_manager"],
    "user:assign_role": ["admin"],
    "sla:view_breaches": ["admin", "subscription_manager", "helpdesk_agent"],
    "incident:create": ["admin", "infrastructure_engineer"]
}

# Check if user has required permission
allow if {
    required_roles := permissions[input.action]
    some role in required_roles
    role in input.roles
}

# Get user's highest role level
user_max_role_level := max([role_hierarchy[role] | role := input.roles[_]])
```

**Policy 5: `sandbox_routing.rego`** (Trial mode sandbox vs production routing)
```rego
package sandbox_routing

import future.keywords.if

default route_to := "production"

# Route trial users to sandbox
route_to := "sandbox" if {
    input.trial_mode == true
}

# Route paid users to production
route_to := "production" if {
    input.trial_mode == false
}

# Get target Plant URL
plant_url := url if {
    route_to == "sandbox"
    url := "https://plant-sandbox.demo.waooaw.com/api/v1"
}

plant_url := url if {
    route_to == "production"
    url := "https://plant.demo.waooaw.com/api/v1"
}
```

- [ ] OPA data bundle loaded (customer metadata):
  ```json
  {
    "customers": {
      "CUST-123": {
        "trial_mode": true,
        "trial_expires_at": "2026-01-24T00:00:00Z",
        "budget_agent_daily": 1.00,
        "budget_platform_monthly": 100.00
      }
    },
    "pp_users": {
      "USER-456": {
        "roles": ["subscription_manager"],
        "customer_id": "WAOOAW-INTERNAL"
      }
    }
  }
  ```
- [ ] Health check endpoint: `GET http://opa:8181/health`
- [ ] Policy validation tests (100% coverage for 5 policies)

**Technical Tasks:**
1. Deploy OPA as Cloud Run service (shares existing infrastructure)
2. Create `infrastructure/opa/policies/` directory
3. Write 5 Rego policy files (200 lines each)
4. Create policy test suite (`conftest` for Rego testing)
5. Add OPA bundle build to CI/CD (policy validation on PR)
6. Document policy API endpoints for gateway middleware
7. Configure OPA service URL in existing Cloud Run env vars

**Dependencies:** None (foundational)

**Validation:**
```bash
# Test OPA policy
curl -X POST http://opa:8181/v1/data/trial_mode/allow \
  -d '{"input": {"customer_id": "CUST-123", "task_count_today": 5}}'
# Expected: {"result": true}

# Test with exceeded limit
curl -X POST http://opa:8181/v1/data/trial_mode/allow \
  -d '{"input": {"customer_id": "CUST-123", "task_count_today": 11}}'
# Expected: {"result": false, "reason": "Trial limit 10 tasks/day exceeded"}
```

**Risks:**
- Rego syntax learning curve (2 days for team)
- OPA performance overhead (~5ms per policy decision)
- Policy conflicts if not carefully designed

---

### GW-001: PostgreSQL Audit Schema & RLS Setup

**Priority:** P0 (Required for audit middleware)  
**Effort:** 4 days  
**Owner:** Database Team  

**Problem:**
- No centralized audit table for gateway requests
- No RLS session variables for customer data isolation
- Audit logs not queryable for constitutional compliance

**User Story:**
```gherkin
As a compliance officer
I want all gateway requests logged with constitutional context
So that I can audit L0/L1 principle enforcement
```

**Acceptance Criteria:**
- [ ] `gateway_audit_logs` table created in **existing** Plant PostgreSQL Cloud SQL instance (no new database)
  - Cost: $0 (uses existing db-f1-micro $15-25/month instance)
  - Schema:
  ```sql
  CREATE TABLE gateway_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    correlation_id UUID NOT NULL,
    causation_id UUID,  -- Links constitutional decisions
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    customer_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    agent_id TEXT,  -- Which agent was accessed
    method TEXT NOT NULL,  -- GET, POST, PUT, DELETE
    path TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    duration_ms INTEGER NOT NULL,
    constitutional_context JSONB NOT NULL,  -- Governor role, trial mode, etc.
    opa_decision JSONB,  -- OPA policy result
    error_message TEXT,
    CONSTRAINT audit_customer_fkey FOREIGN KEY (customer_id) REFERENCES customers(id)
  );
  
  CREATE INDEX idx_audit_correlation ON gateway_audit_logs(correlation_id);
  CREATE INDEX idx_audit_customer_time ON gateway_audit_logs(customer_id, timestamp DESC);
  CREATE INDEX idx_audit_agent ON gateway_audit_logs(agent_id) WHERE agent_id IS NOT NULL;
  ```
- [ ] Row-Level Security (RLS) enabled:
  ```sql
  ALTER TABLE gateway_audit_logs ENABLE ROW LEVEL SECURITY;
  
  CREATE POLICY audit_customer_isolation ON gateway_audit_logs
    USING (customer_id = current_setting('app.current_customer_id')::TEXT);
  ```
- [ ] Session variable setter function:
  ```sql
  CREATE OR REPLACE FUNCTION set_customer_context(p_customer_id TEXT)
  RETURNS VOID AS $$
  BEGIN
    PERFORM set_config('app.current_customer_id', p_customer_id, false);
  END;
  $$ LANGUAGE plpgsql;
  ```
- [ ] 7-year retention policy (constitutional compliance):
  ```sql
  CREATE TABLE gateway_audit_logs_archive (LIKE gateway_audit_logs);
  -- Archive records older than 7 years
  ```
- [ ] Query performance validated (<100ms for customer audit queries)

**Technical Tasks:**
1. Create Alembic migration: `007_gateway_audit_schema.py`
2. Add RLS policies + session variable function
3. Test RLS enforcement (customer can only see own logs)
4. Create audit query views for common patterns
5. Add PostgreSQL partitioning (monthly partitions for scale)
6. Document audit log schema in API docs

**Dependencies:** None (database-only)

**Validation:**
```python
# Test RLS enforcement
async with db_session() as session:
    # Set customer context
    await session.execute("SELECT set_customer_context('CUST-123')")
    
    # Query audit logs (should only see CUST-123)
    result = await session.execute("SELECT customer_id FROM gateway_audit_logs")
    assert all(r.customer_id == 'CUST-123' for r in result)
```

---

## Phase 1: Core Middleware Layer (4 weeks)

### GW-100: Constitutional Auth Middleware

**Priority:** P0 (Foundation for all other middleware)  
**Effort:** 5 days  
**Owner:** Backend Team  

**Problem:**
- No JWT validation at gateway entry
- No Governor role extraction
- No trial mode detection from JWT claims
- No correlation_id injection for request tracing

**User Story:**
```gherkin
As a backend developer
I want every request to have validated JWT + constitutional context
So that downstream handlers can trust user identity and permissions
```

**Acceptance Criteria:**
- [ ] Auth middleware created: `src/CP/BackEnd/middleware/auth.py`
- [ ] JWT validation:
  - Verify signature with `JWT_SECRET`
  - Check expiration (`exp` claim)
  - Extract user_id, email, customer_id, roles
- [ ] Governor role detection:
  ```python
  is_governor = "governor" in jwt_payload.get("roles", [])
  # Or check: jwt_payload.get("governor_agent_id") is not None
  ```
- [ ] Trial mode detection:
  ```python
  trial_mode = jwt_payload.get("trial_mode", True)
  trial_expires_at = jwt_payload.get("trial_expires_at")
  ```
- [ ] Correlation ID injection:
  ```python
  correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
  request.state.correlation_id = correlation_id
  ```
- [ ] ConstitutionalContext model:
  ```python
  @dataclass
  class ConstitutionalContext:
      user_id: str
      email: str
      customer_id: str
      roles: List[str]
      is_governor: bool
      trial_mode: bool
      trial_expires_at: Optional[datetime]
      correlation_id: str
      issued_at: datetime
  ```
- [ ] Request state injection: `request.state.constitutional_context`
- [ ] Public endpoints excluded: `/health`, `/api/auth/google/*`
- [ ] Error responses (RFC 7807):
  - 401 Unauthorized: Missing/invalid token
  - 401 Unauthorized: Expired token (include `refresh_token` action)

**Technical Tasks:**
1. Create `ConstitutionalContext` model
2. Implement `ConstitutionalAuthMiddleware` class
3. Add JWT validation logic (using `PyJWT` library)
4. Add correlation_id generation/propagation
5. Write unit tests (15 test cases)
6. Register middleware in `main.py`

**Dependencies:** GW-000 (OPA) not required yet

**Validation:**
```python
# Test JWT validation
response = client.get(
    "/api/agents",
    headers={"Authorization": f"Bearer {valid_token}"}
)
assert response.status_code == 200
assert hasattr(request.state, "constitutional_context")

# Test expired token
response = client.get(
    "/api/agents",
    headers={"Authorization": f"Bearer {expired_token}"}
)
assert response.status_code == 401
assert response.json()["action"] == "refresh_token"
```

---

### GW-101: RBAC Enforcement Middleware (PP Only)

**Priority:** P1 (Blocking PP admin features)  
**Effort:** 7 days  
**Owner:** Backend Team  

**Problem:**
- PP has 7 hierarchical roles but no enforcement
- Admin actions not validated against role permissions
- No audit trail for denied permission attempts

**User Story:**
```gherkin
As a PP admin with "Subscription Manager" role
I want to be prevented from creating agents (requires "Agent Orchestrator" role)
So that role boundaries are enforced constitutionally
```

**Acceptance Criteria:**
- [ ] RBAC middleware: `src/PP/BackEnd/middleware/rbac.py`
- [ ] Route → Permission mapping:
  ```python
  ROUTE_PERMISSIONS = {
      "POST /api/agents": "agent:create",
      "POST /api/agents/{id}/approve": "agent:approve",
      "POST /api/customers/{id}/force-cancel": "subscription:force_cancel",
      "POST /api/billing/credit-proposals/approve": "billing:approve_credit",
      "POST /api/users/assign-role": "user:assign_role",
      "GET /api/sla/breaches": "sla:view_breaches",
      "POST /api/incidents": "incident:create",
  }
  ```
- [ ] OPA RBAC query:
  ```python
  opa_request = {
      "input": {
          "user_id": ctx.user_id,
          "roles": ctx.roles,
          "action": required_permission,
          "resource": {"agent_id": path_params.get("agent_id")}
      }
  }
  result = await opa_client.query("rbac_pp/allow", opa_request)
  ```
- [ ] 7-role hierarchy enforcement:
  1. Admin (all permissions)
  2. Subscription Manager (customer + billing)
  3. Agent Orchestrator (agent creation + approval)
  4. Infrastructure Engineer (infrastructure only)
  5. Helpdesk Agent (customer support)
  6. Industry Manager (Genesis certification)
  7. Viewer (read-only)
- [ ] Permission denied response:
  ```json
  {
    "status": 403,
    "title": "Forbidden",
    "detail": "Role 'Subscription Manager' lacks permission 'agent:create'",
    "required_roles": ["Agent Orchestrator", "Admin"],
    "audit_logged": true
  }
  ```
- [ ] Audit denied attempts (security events)

**Technical Tasks:**
1. Create `RBACMiddleware` class
2. Implement route → permission mapper
3. Create OPA client wrapper
4. Write `rbac_pp.rego` policy (100 lines)
5. Add permission tests (25 test cases covering all 7 roles)
6. Document RBAC architecture in PP docs

**Dependencies:** GW-000 (OPA), GW-100 (Auth)

**Validation:**
```python
# Test Admin role (should allow all)
response = client.post(
    "/api/agents",
    headers={"Authorization": f"Bearer {admin_token}"},
    json={"name": "Test Agent"}
)
assert response.status_code == 201

# Test Subscription Manager role (should deny agent creation)
response = client.post(
    "/api/agents",
    headers={"Authorization": f"Bearer {subscription_manager_token}"},
    json={"name": "Test Agent"}
)
assert response.status_code == 403
assert "lacks permission 'agent:create'" in response.json()["detail"]
```

---

### GW-102: Policy Decision Point (PDP) Middleware

**Priority:** P1 (Blocking trial mode enforcement)  
**Effort:** 6 days  
**Owner:** Backend Team  

**Problem:**
- No trial mode restrictions enforced
- Trial users can execute unlimited agents
- No sandbox routing for trial customers
- No constitutional validation before external actions

**User Story:**
```gherkin
As a trial customer
I want to be limited to 10 agent tasks per day
So that I understand the platform limits before upgrading
```

**Acceptance Criteria:**
- [ ] PDP middleware: `src/CP/BackEnd/middleware/policy.py`, `src/PP/BackEnd/middleware/policy.py`
- [ ] Trial mode checks:
  ```python
  if ctx.trial_mode:
      # Query OPA for trial restrictions
      opa_request = {
          "input": {
              "customer_id": ctx.customer_id,
              "task_count_today": await get_task_count_today(ctx.customer_id),
              "trial_expires_at": ctx.trial_expires_at.isoformat()
          }
      }
      result = await opa_client.query("trial_mode/allow", opa_request)
      if not result["allow"]:
          raise TrialLimitExceeded(result["reason"])
  ```
- [ ] Trial limits enforced:
  - 10 agent tasks per day
  - 7-day trial period
  - Sandbox environment only (no production agent execution)
- [ ] Sandbox routing:
  ```python
  if ctx.trial_mode:
      # Route to sandbox Plant instance
      plant_url = settings.PLANT_SANDBOX_URL
  else:
      # Route to production Plant instance
      plant_url = settings.PLANT_API_URL
  ```
- [ ] Governor approval gates:
  ```python
  if requires_governor_approval(action):
      if not ctx.is_governor:
          raise GovernorApprovalRequired(
              action=action,
              approval_link="/api/approvals/request"
          )
  ```
- [ ] Constitutional validation:
  - L0-03: External execution requires approval
  - L0-02: Agent specialization enforced (job role + skills certified)
- [ ] Policy decision logged to audit table

**Technical Tasks:**
1. Create `PolicyMiddleware` class
2. Write `trial_mode.rego` policy (150 lines)
3. Write `governor_approval.rego` policy (100 lines)
4. Implement trial task counter (Redis cache)
5. Add sandbox routing logic
6. Write policy tests (20 test cases)

**Dependencies:** GW-000 (OPA), GW-100 (Auth), GW-001 (Audit)

**Validation:**
```python
# Test trial limit enforcement
# Day 1: 10 tasks succeed
for i in range(10):
    response = client.post(
        "/api/agents/execute",
        headers={"Authorization": trial_token},
        json={"task": f"Task {i}"}
    )
    assert response.status_code == 200

# 11th task fails
response = client.post(
    "/api/agents/execute",
    headers={"Authorization": trial_token},
    json={"task": "Task 11"}
)
assert response.status_code == 403
assert "Trial limit 10 tasks/day exceeded" in response.json()["detail"]
```

---

### GW-103: Budget Guard Middleware

**Priority:** P2 (Cost control, not MVP-blocking)  
**Effort:** 5 days  
**Owner:** Backend Team  

**Problem:**
- No agent spending caps enforced
- Customers can accidentally run up large bills
- No platform-level budget controls
- No real-time budget alerts

**User Story:**
```gherkin
As a customer
I want agents to stop executing when they hit $1/day budget
So that I don't get unexpected bills
```

**Acceptance Criteria:**
- [ ] Budget middleware: `src/CP/BackEnd/middleware/budget.py`
- [ ] Budget tracking:
  ```python
  # Check agent daily budget
  agent_spend_today = await get_agent_spend_today(agent_id)
  if agent_spend_today >= 1.00:  # $1/day cap
      raise AgentBudgetExceeded(
          agent_id=agent_id,
          daily_cap=1.00,
          spent_today=agent_spend_today
      )
  
  # Check platform monthly budget
  platform_spend_month = await get_platform_spend_month(customer_id)
  if platform_spend_month >= 100.00:  # $100/month cap
      raise PlatformBudgetExceeded(
          customer_id=customer_id,
          monthly_cap=100.00,
          spent_month=platform_spend_month
      )
  ```
- [ ] Budget limits (configurable):
  - Agent: $1/day default, $10/day max
  - Platform: $100/month trial, $1000/month paid
- [ ] Budget tracking storage (**existing Redis Memorystore**, no new instance):
  - Cost: $0 (uses existing $10-15/month Redis)
  - Key: `budget:agent:{agent_id}:daily:{YYYY-MM-DD}`
  - Key: `budget:platform:{customer_id}:monthly:{YYYY-MM}`
  - TTL: 30 days for auto-cleanup
- [ ] Budget alert webhooks:
  - 80% budget reached: Warning email
  - 90% budget reached: Critical email
  - 100% budget reached: Execution stopped + email
- [ ] Budget reset:
  - Agent daily: Resets at midnight UTC
  - Platform monthly: Resets on subscription renewal date

**Technical Tasks:**
1. Create `BudgetGuardMiddleware` class
2. Implement Redis budget tracker
3. Add OPA budget policy: `agent_budget.rego`
4. Create budget alerting service
5. Add budget dashboard endpoints (GET /api/budget/status)
6. Write budget tests (15 test cases)

**Dependencies:** GW-100 (Auth), existing Redis Memorystore

**Validation:**
```python
# Test agent budget cap
# Execute tasks until $1 spent
for i in range(100):  # Each task costs ~$0.01
    response = client.post(
        "/api/agents/execute",
        headers={"Authorization": customer_token},
        json={"agent_id": "AGENT-123", "task": f"Task {i}"}
    )
    if response.status_code == 403:
        assert "Agent budget $1.00/day exceeded" in response.json()["detail"]
        break
    assert response.status_code == 200

# Verify budget status endpoint
response = client.get(
    "/api/budget/status/AGENT-123",
    headers={"Authorization": customer_token}
)
assert response.json()["spent_today"] >= 1.00
assert response.json()["daily_cap"] == 1.00
```

---

### GW-104: Audit Logging Middleware

**Priority:** P0 (Constitutional compliance requirement)  
**Effort:** 5 days  
**Owner:** Backend Team  

**Problem:**
- No centralized audit trail for gateway requests
- No correlation_id propagation to Plant backend
- No constitutional context logged (Governor actions, trial mode, OPA decisions)
- Can't answer "Who did what, when, and why?" for compliance

**User Story:**
```gherkin
As a compliance auditor
I want every gateway request logged with constitutional context
So that I can trace Governor approvals and constitutional decisions
```

**Acceptance Criteria:**
- [ ] Audit middleware: `src/CP/BackEnd/middleware/audit.py`, `src/PP/BackEnd/middleware/audit.py`
- [ ] Audit log entry created for every request:
  ```python
  audit_entry = {
      "correlation_id": request.state.correlation_id,
      "causation_id": request.state.causation_id,  # Links related requests
      "timestamp": datetime.utcnow(),
      "customer_id": ctx.customer_id,
      "user_id": ctx.user_id,
      "agent_id": request.state.get("agent_id"),
      "method": request.method,
      "path": request.url.path,
      "status_code": response.status_code,
      "duration_ms": int((end_time - start_time) * 1000),
      "constitutional_context": {
          "is_governor": ctx.is_governor,
          "trial_mode": ctx.trial_mode,
          "roles": ctx.roles,
      },
      "opa_decision": request.state.get("opa_decision"),
      "error_message": response.get("detail") if response.status_code >= 400 else None
  }
  await audit_service.log(audit_entry)
  ```
- [ ] Correlation ID propagation:
  ```python
  # Add to outbound Plant API requests
  headers = {
      "X-Correlation-ID": request.state.correlation_id,
      "X-Causation-ID": str(uuid.uuid4())  # New causation ID
  }
  ```
- [ ] Causation chain tracking:
  - Request 1 (CP Gateway): correlation_id=A, causation_id=A1
  - Request 2 (Plant Backend from CP): correlation_id=A, causation_id=A2
  - Request 3 (OPA decision from CP): correlation_id=A, causation_id=A3
- [ ] Performance impact < 5ms per request
- [ ] Async audit writes (non-blocking)
- [ ] Audit query API:
  - `GET /api/audit?correlation_id={id}` - Trace request chain
  - `GET /api/audit?customer_id={id}&start={date}&end={date}` - Customer audit
  - `GET /api/audit?agent_id={id}` - Agent activity history

**Technical Tasks:**
1. Create `AuditLoggingMiddleware` class
2. Implement async audit writer (PostgreSQL + batch inserts)
3. Add causation_id chain tracking
4. Create audit query endpoints
5. Add audit log retention policy (7 years)
6. Write audit tests (20 test cases)

**Dependencies:** GW-001 (Audit schema), GW-100 (Auth)

**Validation:**
```python
# Test audit log creation
response = client.post(
    "/api/agents",
    headers={"Authorization": customer_token,
             "X-Correlation-ID": "test-correlation-123"},
    json={"name": "Test Agent"}
)
assert response.status_code == 201

# Query audit log
audit_log = await db.execute(
    "SELECT * FROM gateway_audit_logs WHERE correlation_id = $1",
    "test-correlation-123"
)
assert audit_log["method"] == "POST"
assert audit_log["path"] == "/api/agents"
assert audit_log["constitutional_context"]["trial_mode"] is True
assert audit_log["status_code"] == 201
```

---

### GW-105: Error Handling Middleware

**Priority:** P1 (Developer experience)  
**Effort:** 4 days  
**Owner:** Backend Team  

**Problem:**
- Inconsistent error responses across CP/PP/Plant
- No RFC 7807 (Problem Details) standard
- Stack traces leak to customers
- No constitutional error categorization

**User Story:**
```gherkin
As a frontend developer
I want consistent, structured error responses
So that I can display meaningful messages to users
```

**Acceptance Criteria:**
- [ ] Error middleware: `src/CP/BackEnd/middleware/error.py`, `src/PP/BackEnd/middleware/error.py`
- [ ] RFC 7807 Problem Details format:
  ```python
  {
      "type": "https://waooaw.com/errors/trial-limit-exceeded",
      "title": "Trial Limit Exceeded",
      "status": 403,
      "detail": "You have exceeded the trial limit of 10 tasks per day. Upgrade to continue.",
      "instance": "/api/agents/execute/TASK-123",
      "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
      "constitutional_context": {
          "principle_violated": "L0-03: Trial mode restrictions",
          "trial_mode": true,
          "tasks_today": 11,
          "limit": 10
      }
  }
  ```
- [ ] Constitutional error types:
  - `TrialLimitExceeded` (403) - L0-03 violation
  - `GovernorApprovalRequired` (403) - L0-01 violation
  - `AgentBudgetExceeded` (403) - Cost control
  - `AgentNotCertified` (422) - L0-02 violation
  - `ConstitutionalViolation` (422) - Generic L0/L1 violation
- [ ] Stack trace sanitization (production):
  - Dev: Full stack traces
  - Production: Sanitized, logged server-side only
- [ ] Error categorization:
  - Client errors (4xx): User actionable
  - Server errors (5xx): Engineering alerts
  - Constitutional errors: Audit logged + OPA query
- [ ] Error response headers:
  ```python
  headers = {
      "X-Correlation-ID": correlation_id,
      "X-Error-Code": "TRIAL_LIMIT_EXCEEDED",
      "X-Retry-After": "86400"  # 24 hours for trial limit reset
  }
  ```

**Technical Tasks:**
1. Create `ErrorHandlingMiddleware` class
2. Define constitutional exception classes
3. Implement RFC 7807 response builder
4. Add stack trace sanitization
5. Create error documentation page
6. Write error handling tests (25 test cases)

**Dependencies:** GW-100 (Auth for correlation_id)

**Validation:**
```python
# Test RFC 7807 error response
response = client.post(
    "/api/agents/execute",
    headers={"Authorization": trial_token},
    json={"task": "Task 11"}  # Exceeds trial limit
)
assert response.status_code == 403
assert response.json()["type"] == "https://waooaw.com/errors/trial-limit-exceeded"
assert response.json()["correlation_id"] is not None
assert "L0-03" in response.json()["constitutional_context"]["principle_violated"]
```

---

## Phase 2: Real-Time & WebSocket Support (2 weeks)

### GW-200: WebSocket Middleware (CP Only)

**Priority:** P2 (Real-time trial progress)  
**Effort:** 6 days  
**Owner:** Backend Team  

**Problem:**
- No real-time updates for agent execution status
- Trial customers can't see progress without polling
- No WebSocket authentication at gateway layer

**User Story:**
```gherkin
As a CP customer watching my trial agent execute
I want to see real-time progress updates
So that I know the agent is working and not frozen
```

**Acceptance Criteria:**
- [ ] WebSocket middleware: `src/CP/BackEnd/middleware/websocket.py`
- [ ] WebSocket authentication:
  ```python
  @app.websocket("/ws/agent/{agent_id}")
  async def agent_status_ws(websocket: WebSocket, agent_id: str):
      # Authenticate via query param token
      token = websocket.query_params.get("token")
      ctx = await validate_jwt(token)
      
      # Verify customer owns agent
      agent = await get_agent(agent_id)
      if agent.customer_id != ctx.customer_id:
          await websocket.close(code=1008, reason="Forbidden")
          return
      
      await websocket.accept()
  ```
- [ ] WebSocket channels:
  - `/ws/agent/{agent_id}` - Agent execution updates
  - `/ws/approvals` - Governor approval requests (PP only)
  - `/ws/trial-progress` - Trial task count updates
- [ ] Message format:
  ```json
  {
    "type": "agent.status",
    "agent_id": "AGENT-123",
    "status": "executing",
    "task_progress": {
      "current_step": 3,
      "total_steps": 10,
      "step_description": "Analyzing customer data"
    },
    "timestamp": "2026-01-17T10:30:00Z"
  }
  ```
- [ ] Heartbeat/keepalive (30 sec)
- [ ] Connection limit: 5 concurrent per customer (prevent abuse)
- [ ] Auto-reconnect on disconnect

**Technical Tasks:**
1. Create `WebSocketMiddleware` class
2. Implement WebSocket authentication
3. Add WebSocket channel routing
4. Implement heartbeat mechanism
5. Add connection pooling
6. Write WebSocket tests (integration tests)

**Dependencies:** GW-100 (Auth)

**Validation:**
```python
# Test WebSocket connection
async with websockets.connect(
    f"ws://localhost:8015/ws/agent/AGENT-123?token={customer_token}"
) as websocket:
    # Receive status update
    message = await websocket.recv()
    data = json.loads(message)
    assert data["type"] == "agent.status"
    assert data["agent_id"] == "AGENT-123"
```

---

## Phase 3: Observability & Monitoring (2 weeks)

### GW-300: OpenTelemetry Integration

**Priority:** P2 (Observability)  
**Effort:** 5 days  
**Owner:** Platform Team  

**Problem:**
- No distributed tracing across CP/PP/Plant
- Can't debug slow requests or failures
- No service mesh visibility

**User Story:**
```gherkin
As an SRE
I want to trace requests across CP → Plant → OPA
So that I can debug performance bottlenecks
```

**Acceptance Criteria:**
- [ ] OpenTelemetry SDK installed in CP/PP gateways
- [ ] Traces exported to **GCP Cloud Logging** (existing $5-10/month, no Jaeger/Zipkin cost)
- [ ] Span creation for middleware layers:
  - Auth middleware span
  - RBAC middleware span
  - Policy middleware span
  - Audit middleware span
- [ ] Trace propagation to Plant backend:
  ```python
  headers = {
      "traceparent": f"00-{trace_id}-{span_id}-01"
  }
  ```
- [ ] Metrics collection:
  - Request rate (requests/sec)
  - Error rate (4xx/5xx %)
  - Latency (p50, p95, p99)
  - OPA policy decision time
- [ ] Dashboard in **GCP Cloud Monitoring** (free tier, no Grafana cost)

**Technical Tasks:**
1. Install OpenTelemetry SDK
2. Configure GCP Cloud Logging exporter (free tier)
3. Add middleware instrumentation
4. Create GCP Cloud Monitoring dashboard
5. Add trace tests

**Dependencies:** GCP Cloud Logging enabled (already active)

---

## Phase 4: Performance & Scale (2 weeks)

### GW-400: Rate Limiting Infrastructure

**Priority:** P1 (Prevent abuse)  
**Effort:** 5 days  
**Owner:** Platform Team  

**Problem:**
- No rate limiting
- Trial customers can spam APIs
- No DDoS protection

**User Story:**
```gherkin
As a platform operator
I want to rate limit customers by tier
So that free trial users don't overwhelm the system
```

**Acceptance Criteria:**
- [ ] Rate limiter: **Existing Redis** Memorystore (no new infrastructure)
- [ ] Tiers:
  - Trial: 100 requests/hour
  - Paid: 1000 requests/hour
  - Enterprise: 10000 requests/hour
- [ ] Rate limit headers:
  ```
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 45
  X-RateLimit-Reset: 1705492800
  ```
- [ ] 429 Too Many Requests response

**Technical Tasks:**
1. Implement Redis sliding window rate limiter
2. Add rate limit middleware
3. Configure per-tier limits
4. Add Retry-After headers
5. Write rate limit tests

**Dependencies:** Existing Redis Memorystore (already deployed)

---

### GW-401: Circuit Breaker Pattern

**Priority:** P2 (Resilience)  
**Effort:** 4 days  
**Owner:** Backend Team  

**Problem:**
- Plant backend failures cascade to CP/PP
- No automatic failover
- No graceful degradation

**User Story:**
```gherkin
As a customer
I want the CP to stay responsive even when Plant is down
So that I can still browse the marketplace
```

**Acceptance Criteria:**
- [ ] Circuit breaker for Plant API calls
- [ ] States: CLOSED → OPEN → HALF_OPEN
- [ ] Failure threshold: 5 consecutive errors
- [ ] Timeout: 30 seconds
- [ ] Graceful degradation (cached data)

**Technical Tasks:**
1. Implement circuit breaker (using `pybreaker`)
2. Add Plant API wrapper with circuit breaker
3. Add fallback responses (cached data)
4. Write circuit breaker tests

**Dependencies:** None

---

## Phase 5: Production Hardening (3 weeks)

### GW-500: Security Audit & Penetration Testing

**Priority:** P0 (Production readiness)  
**Effort:** 10 days  
**Owner:** Security Team  

**Problem:**
- Gateway not security-tested
- Unknown vulnerabilities
- No SOC 2 compliance validation

**Acceptance Criteria:**
- [ ] OWASP Top 10 testing completed
- [ ] JWT token security validated
- [ ] OPA policy bypass attempts tested
- [ ] Rate limit bypass attempts tested
- [ ] SQL injection testing (RLS bypass attempts)
- [ ] Penetration test report (no critical findings)

**Technical Tasks:**
1. Run OWASP ZAP automated scan
2. Manual penetration testing
3. Security code review
4. Fix identified vulnerabilities
5. Document security architecture

**Dependencies:** All middleware complete

---

### GW-501: Load Testing & Capacity Planning

**Priority:** P1 (Scale validation)  
**Effort:** 5 days  
**Owner:** Platform Team  

**Problem:**
- Don't know gateway capacity limits
- No baseline performance metrics
- Can't predict scale requirements

**Acceptance Criteria:**
- [ ] Load test scenarios:
  - 100 concurrent users
  - 1000 concurrent users
  - 10000 concurrent users
- [ ] Performance benchmarks:
  - Auth middleware: < 5ms
  - RBAC middleware: < 10ms (OPA call)
  - Audit middleware: < 5ms (async write)
  - Total gateway latency: < 50ms (p95)
- [ ] Capacity plan document

**Technical Tasks:**
1. Create load test scripts (Locust)
2. Run load tests in staging
3. Analyze bottlenecks
4. Optimize hot paths
5. Document capacity limits

**Dependencies:** All middleware complete

---

### GW-502: Disaster Recovery & Backup

**Priority:** P0 (Business continuity)  
**Effort:** 5 days  
**Owner:** Platform Team  

**Problem:**
- No audit log backup strategy
- No OPA policy version control
- No rollback plan for bad gateway releases

**Acceptance Criteria:**
- [ ] Audit log backup (S3/GCS daily)
- [ ] OPA policy version control (Git)
- [ ] Gateway rollback procedure (blue-green deployment)
- [ ] Disaster recovery runbook

**Technical Tasks:**
1. Implement audit log backup to S3
2. Add OPA policy CI/CD
3. Create blue-green deployment for gateway
4. Write DR runbook
5. Test rollback procedure

**Dependencies:** None

---

## Phase 6: Documentation & Handoff (1 week)

### GW-600: Gateway Operations Runbook

**Priority:** P0 (Production support)  
**Effort:** 3 days  
**Owner:** Tech Writer + Platform Team  

**Acceptance Criteria:**
- [ ] Runbook sections:
  - Gateway architecture diagram
  - Middleware layer explanations
  - OPA policy management
  - Rate limit adjustment procedures
  - Circuit breaker manual override
  - Audit log queries (common scenarios)
  - Troubleshooting guide (10 common issues)
- [ ] On-call playbook

**Technical Tasks:**
1. Write comprehensive runbook
2. Create architecture diagrams
3. Document OPA policy syntax
4. Add troubleshooting flowcharts
5. Record video walkthroughs

**Dependencies:** All phases complete

---

### GW-601: Developer Documentation

**Priority:** P1 (Developer experience)  
**Effort:** 3 days  
**Owner:** Tech Writer + Backend Team  

**Acceptance Criteria:**
- [ ] Gateway middleware API docs
- [ ] OPA policy development guide
- [ ] Error handling guide (RFC 7807)
- [ ] WebSocket API docs
- [ ] Testing guide (unit + integration)
- [ ] Migration guide (from direct integration)

**Technical Tasks:**
1. Write developer documentation
2. Add code examples
3. Create migration guide
4. Record tutorial videos
5. Update API documentation

**Dependencies:** GW-600

---

## Testing Strategy

### Unit Tests (Per Story)
- Middleware classes: 10-15 tests each
- OPA policies: 100% coverage with `conftest`
- Error handling: 25+ test cases
- **Target:** 90% code coverage

### Integration Tests
- End-to-end gateway flows (20 scenarios)
- WebSocket connection tests
- Circuit breaker behavior
- Rate limit enforcement

### Performance Tests
- Load tests: 100/1000/10000 concurrent users
- Latency benchmarks: < 50ms p95
- OPA policy decision time: < 10ms
- Audit write throughput: 10k writes/sec

### Security Tests
- OWASP Top 10 automated scan
- JWT token validation bypasses
- OPA policy bypasses
- SQL injection attempts (RLS bypass)
- Rate limit bypasses

---

## Deployment Strategy

### Phase Rollout
1. **Staging:** Deploy all 6 phases to staging
2. **Canary:** 5% of production traffic
3. **Blue-Green:** Full production cutover
4. **Rollback Plan:** Keep old direct integration for 2 weeks

### Feature Flags
- `ENABLE_GATEWAY_MIDDLEWARE=true/false`
- `ENABLE_OPA_ENFORCEMENT=true/false`
- `ENABLE_RATE_LIMITING=true/false`
- Per-customer feature flags for gradual rollout

### Monitoring
- Grafana dashboard: Gateway metrics
- PagerDuty alerts: Circuit breaker open, rate limit exceeded
- Slack notifications: Audit anomalies

---

## Success Metrics

| Metric | Baseline (Direct) | Target (Gateway) | Measurement |
|--------|-------------------|------------------|-------------|
| **Latency (p95)** | 100ms | < 150ms (+50ms for middleware) | OpenTelemetry traces |
| **Error Rate** | 2% | < 1% (better error handling) | Prometheus metrics |
| **Security Incidents** | 3/month | 0/month (policy-driven) | Audit log analysis |
| **Trial Conversion** | 10% | 15% (better trial experience) | Business analytics |
| **Governor Approval Time** | 24 hours | < 1 hour (real-time alerts) | Audit log timestamps |
| **Cost per Request** | $0.001 | $0.0015 (+50% for OPA/audit) | Cloud billing |
| **Audit Compliance** | 60% | 100% (complete trail) | Compliance review |

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **OPA Performance** | Medium | High | Cache policy decisions (5 min TTL), load test early |
| **Audit Log Storage** | Low | Medium | S3 tiered storage, 7-year retention with compression |
| **WebSocket Scale** | Medium | Medium | Connection limit (5/customer), load balancer with sticky sessions |
| **Circuit Breaker False Positives** | High | Low | Configurable thresholds, manual override |
| **Rate Limit Gaming** | Medium | Medium | IP-based + token-based limits, anomaly detection |

---

## Budget

| Phase | Effort (Days) | Eng Cost ($150/hr) | Infra Cost/Month | Total |
|-------|---------------|-------------------|------------------|-------|
| Phase 0 | 9 | $10,800 | **$0** (OPA in existing Cloud Run) | $10,800 |
| Phase 1 | 32 | $38,400 | **$0** (existing PostgreSQL + Redis) | $38,400 |
| Phase 2 | 6 | $7,200 | **$0** (Cloud Run WebSockets) | $7,200 |
| Phase 3 | 5 | $6,000 | **$0** (GCP Cloud Logging/Monitoring) | $6,000 |
| Phase 4 | 9 | $10,800 | **$0** (existing Redis) | $10,800 |
| Phase 5 | 20 | $24,000 | $0 | $24,000 |
| Phase 6 | 6 | $7,200 | $0 | $7,200 |
| **Total** | **87 days** | **$104,400** | **$0 (no new infra)** | **$104,400** |

**Platform stays at $55-85/month** (existing Cloud SQL $15-25 + Redis $10-15 + Cloud Run $20-30 + other $10-20)

**Timeline:** 16-20 weeks (4-5 months) with 2-3 engineers

---

## Conclusion

This plan transforms the WAOOAW platform from a basic MVP with direct API integration into an **enterprise-grade constitutional platform** ready for exponential growth.

### Key Achievements
1. ✅ **Security:** OPA-driven policy enforcement, deny-by-default
2. ✅ **Compliance:** Complete audit trail with correlation_id + causation_id
3. ✅ **Scale:** Rate limiting, circuit breakers, 10000 concurrent users
4. ✅ **Constitutional:** L0/L1 principles enforced in middleware
5. ✅ **Observability:** OpenTelemetry traces, GCP Cloud Monitoring dashboards
6. ✅ **Cost Governance:** **Zero infrastructure cost increase** - stays within $100/month budget

### Next Steps After Completion
1. **Extend to Plant Gateway:** Apply same middleware to Plant backend
2. **Multi-Region:** Deploy gateway in 3 regions (US/EU/India)
3. **API Versioning:** Add v2 API with breaking changes
4. **GraphQL Gateway:** Add GraphQL layer on top of REST
5. **Service Mesh:** Migrate to Istio for advanced routing

**This gateway is the foundation for serving 100,000 customers and 1,000,000 agents.** 🚀

---

## Test Plan

### Test Strategy Overview

**Testing Philosophy**: Shift-left testing with CI/CD integration. Every middleware component, policy, and service must pass automated tests before deployment.

### 1. Unit Testing

**Scope**: Individual middleware components, utility functions, OPA policies

**Coverage Target**: ≥90% code coverage

**Status**: ✅ **99% COMPLETE** - 75/76 tests passing (1 skipped)

**Test Results** (Updated: 2026-01-17):
- ✅ Error Handler: 14/14 passing (100%) - Exception handler architecture fixed
- ✅ Auth Middleware: 27/28 passing (96%) - 1 skipped async test (cosmetic)
- ✅ Budget Middleware: 9/9 passing (100%) - Redis mocks working
- ✅ RBAC Middleware: 15/15 passing (100%) - OPA mocks working
- ✅ Policy Middleware: 10/10 passing (100%) - Feature flag mocks added

**Commits**:
- `fc6cbc7`: Error handler refactor (middleware → exception handlers)
- `a6704ed`: Auth JWT key sync initial attempt
- `20d4f31`: JWT env vars + policy/budget mocks (87%)
- `a9d0af8`: Final fixes - **75/76 passing (99%)** ✅

**Test Categories**:

| Component | Test Count | Status | Coverage |
|-----------|------------|--------|----------|
| Auth Middleware | 28 tests | ✅ 27/28 (96%) | 95%+ |
| RBAC Middleware | 15 tests | ✅ 15/15 (100%) | 95%+ |
| Policy Middleware | 10 tests | ✅ 10/10 (100%) | 90%+ |
| Budget Middleware | 9 tests | ✅ 9/9 (100%) | 90%+ |
| Error Handler | 14 tests | ✅ 14/14 (100%) | 95%+ |
| **TOTAL** | **76 tests** | **✅ 75/76 (99%)** | **93%+** |

**Test Execution**:
- Run on every commit via GitHub Actions
- Parallel execution across components
- All P0 blocking issues resolved

**Key Fixes Applied**:
1. Error Handler: Refactored from middleware to exception handlers (FastAPI processes exception handlers before middleware)
2. JWT Keys: Environment variable sharing for cross-module access
3. Policy Mocks: FeatureFlagService mocks enable OPA policy checks
4. Request Types: FastAPI Request type annotations for endpoints
5. Action Extraction: delete_agent detection in policy middleware
6. Timeout Handling: Re-raise TimeoutException (fail closed vs fail open)

**Sample Test Scenarios**:
- Auth: JWT validation, expired tokens, missing claims, RS256 signature verification ✅
- RBAC: Role hierarchy (admin→viewer), permission checks, OPA query timeout ✅
- Policy: Trial limit exceeded, Governor approval required, sandbox routing ✅
- Budget: Alert thresholds (80%/95%/100%), 402 blocking, Redis failure fallback ✅
- Audit: Correlation ID propagation, causation_id tracking (pending integration tests)
- Error Handler: RFC 7807 format, status code mapping, environment-based trace inclusion ✅

### 2. Integration Testing

**Scope**: End-to-end request flows through complete middleware chain

**Coverage Target**: 100% critical paths

**Status**: ⏳ **IN PROGRESS** - Docker Compose environment setup

**Test Scenarios** (30+ scenarios):

| Scenario | Gateway | Expected Outcome |
|----------|---------|------------------|
| Valid JWT → Plant | CP | 200 OK, correlation ID propagated |
| Expired JWT | CP | 401 Unauthorized |
| Trial limit exceeded | CP | 429 Too Many Requests, Retry-After header |
| Trial expired | CP | 403 Forbidden, trial-expired error type |
| Budget exceeded | CP | 402 Payment Required |
| Governor approval required | CP | 307 Redirect to approval UI |
| Admin full access | PP | Create/Delete allowed, RBAC headers set |
| Developer limited access | PP | Create allowed, Delete denied (403) |
| Viewer read-only | PP | GET allowed, POST/DELETE denied |
| OPA timeout | Both | 503 Service Unavailable |
| Plant unreachable | Both | 502 Bad Gateway |
| Concurrent requests | Both | 50 parallel requests, all succeed |
| Correlation ID missing | Both | Auto-generated UUID propagated |
| Audit log write failure | Both | Request succeeds (fail-open) |

**Test Execution**:
- Run via `pytest src/gateway/tests/test_integration.py`
- Uses MockServer for Plant service
- Requires Docker Compose (postgres, redis, opa, plant-mock)
- Run in CI after unit tests pass

### 3. Regression Testing

**Scope**: Ensure new changes don't break existing functionality

**Strategy**:
- Maintain test suite of 125+ tests (95 unit + 30 integration)
- Run full test suite on every PR
- Compare test results against baseline (main branch)
- Block merge if any test fails or coverage drops

**Regression Categories**:
- Middleware behavior changes (e.g., auth logic update shouldn't break RBAC)
- OPA policy changes (e.g., trial_mode update shouldn't break budget)
- Dependency upgrades (FastAPI, PyJWT, redis, asyncpg version bumps)
- Environment variable changes (ensure backward compatibility)

**Execution**: Automated via GitHub Actions on PR creation/update

### 4. UI/API Testing

**Scope**: Frontend integration with gateway APIs

**Coverage Target**: 100% user-facing flows

**Test Scenarios**:
- CP Frontend: Trial request flow (form submission → gateway → 201 Created)
- CP Frontend: Real-time trial progress (WebSocket connection, status updates)
- PP Frontend: Agent creation with RBAC (admin creates, viewer blocked)
- PP Frontend: Governor approval UI (307 redirect handling)
- Error handling: Display RFC 7807 error messages to users

**Tools**:
- Playwright for browser automation
- API contract testing (Pact)
- Screenshot comparison (visual regression)

**Execution**: Manual smoke tests + automated E2E tests in staging

### 5. Load Testing

**Scope**: Validate gateway performance under realistic traffic

**Coverage Target**: 1,000 RPS per gateway with <100ms p95 latency

**Load Test Scenarios**:

| Scenario | Tool | Target Load | Duration | Success Criteria |
|----------|------|-------------|----------|------------------|
| Baseline load | k6 | 100 RPS | 5 min | p95 <50ms, 0% errors |
| Normal load | k6 | 500 RPS | 10 min | p95 <75ms, <1% errors |
| Peak load | k6 | 1000 RPS | 5 min | p95 <100ms, <2% errors |
| Spike test | k6 | 0→2000 RPS | 2 min | Autoscale in 30s |
| Endurance test | k6 | 500 RPS | 60 min | No memory leaks, stable latency |
| OPA stress | k6 | 5000 policy queries/sec | 5 min | OPA p95 <10ms |
| Budget check stress | k6 | 10000 Redis ops/sec | 5 min | Redis p95 <5ms |

**k6 Script Example Location**: `load-tests/k6-cp-gateway.js`, `load-tests/k6-pp-gateway.js`

**Metrics Collected**:
- Request duration (p50, p95, p99)
- Error rate (4xx, 5xx)
- Throughput (RPS)
- OPA query time
- Redis operation time
- Plant proxy latency

**Execution**: Run in staging before production release

### 6. Security Testing

**Scope**: Validate security controls and identify vulnerabilities

**Coverage Target**: Zero critical/high vulnerabilities

**Test Categories**:

| Test Type | Tool | Frequency | Scope |
|-----------|------|-----------|-------|
| OWASP Top 10 | OWASP ZAP | Every release | Automated scan |
| JWT bypass | Custom scripts | Every release | Auth middleware |
| OPA policy bypass | Custom scripts | Every release | RBAC/Policy middleware |
| SQL injection | sqlmap | Every release | Audit log queries |
| Rate limit bypass | Custom scripts | Every release | Rate limiter |
| CORS misconfiguration | Burp Suite | Manual | CORS middleware |
| Secret leakage | truffleHog | Every commit | Git commits, logs |
| Dependency vulnerabilities | Snyk | Daily | requirements.txt |

**Security Test Scenarios**:
- JWT: Missing signature, tampered payload, expired tokens, wrong issuer
- RBAC: Role escalation attempts, permission bypass via direct OPA calls
- Policy: Trial limit bypass via parallel requests, Governor approval skip
- Budget: Redis manipulation to bypass limits
- Audit: Log injection attacks, PII leakage in logs
- Rate Limiting: IP spoofing, distributed attack simulation

**Penetration Testing**: Conduct manual pentest by security team before production

**Compliance Validation**:
- SOC 2 Type II readiness (audit trail completeness)
- GDPR compliance (PII handling, right to erasure)
- ISO 27001 alignment (access controls, encryption)

**Execution**: Automated scans in CI/CD + manual pentest pre-production

### 7. Performance Benchmarking

**Scope**: Measure and optimize middleware overhead

**Benchmarks**:

| Component | Target Latency | Measurement Method |
|-----------|----------------|-------------------|
| Auth middleware | <5ms | OpenTelemetry span |
| RBAC middleware | <10ms (OPA call) | OpenTelemetry span |
| Policy middleware | <10ms (OPA call) | OpenTelemetry span |
| Budget middleware | <5ms (Redis op) | OpenTelemetry span |
| Audit middleware | <5ms (async write) | OpenTelemetry span |
| Total gateway overhead | <50ms (p95) | End-to-end trace |

**Optimization Targets**:
- OPA caching: 90% cache hit rate (5 min TTL)
- Redis connection pooling: Reuse connections
- PostgreSQL async writes: Non-blocking audit logs
- HTTP connection pooling: Reuse Plant connections

**Execution**: Continuous monitoring in production via OpenTelemetry

### 8. Test Automation & CI/CD Integration

**GitHub Actions Workflows**:

| Workflow | Trigger | Tests Run | Duration |
|----------|---------|-----------|----------|
| `gateway-test.yml` | Every commit | Unit + integration | 5-8 min |
| `gateway-security.yml` | Every PR | OWASP ZAP + Snyk | 10 min |
| `gateway-load-test.yml` | Pre-release | k6 load tests | 20 min |
| `gateway-e2e.yml` | Staging deploy | UI/API E2E tests | 15 min |

**Test Coverage Reporting**:
- Generate coverage report: `pytest --cov=src/gateway --cov-report=html`
- Publish to Codecov/Coveralls
- Block PR if coverage drops below 85%

**Test Data Management**:
- Use fixtures for deterministic tests
- Mock external dependencies (OPA, Plant, Redis, PostgreSQL)
- Seed test database with known data
- Clean up after tests (docker-compose down -v)

### 9. Acceptance Criteria

**Gateway is production-ready when**:
- ✅ All 125+ tests passing (95 unit + 30 integration)
- ✅ Code coverage ≥85% overall, ≥90% for critical middleware
- ✅ Load test: 1000 RPS with p95 <100ms
- ✅ Security scan: Zero critical/high vulnerabilities
- ✅ Penetration test: No critical findings
- ✅ Integration test: All 30 scenarios pass
- ✅ E2E test: All user flows complete successfully
- ✅ Performance: Total gateway overhead <50ms p95

---

## Deployment Plan

### Deployment Strategy Overview

**Philosophy**: Zero-downtime, workflow-driven deployments with automated rollback and comprehensive validation.

**Deployment Method**: GitHub Actions workflows only (no manual CLI commands)

### 1. Pre-Deployment Checklist

**Prerequisites Validation**:
- ✅ Branch: `feature/phase-4-api-gateway` merged to `main`
- ✅ Tests: All 125+ tests passing in CI
- ✅ Security: OWASP scan passed, no critical vulnerabilities
- ✅ Secrets: JWT keys, database URL, LaunchDarkly SDK key in Secret Manager
- ✅ Dependencies: PostgreSQL (plant-sql-demo), Redis (Memorystore), OPA service deployed
- ✅ DNS: `cp.demo.waooaw.com`, `pp.demo.waooaw.com`, `plant.demo.waooaw.com` → 35.190.6.91

**Secret Manager Validation**:
```bash
# Verify secrets exist (run in GitHub Actions)
gcloud secrets describe demo-plant-database-url --project=waooaw-oauth
gcloud secrets describe demo-jwt-public-key --project=waooaw-oauth
gcloud secrets describe demo-launchdarkly-sdk-key --project=waooaw-oauth
```

**Infrastructure State Check**:
- Verify Plant database is RUNNABLE
- Verify existing services (CP, PP, Plant) are healthy
- Confirm Terraform state bucket accessible (waooaw-terraform-state)

### 2. Deployment Sequence (Automated)

**Batch 0: OPA Policy Service** (5-10 min)

**Workflow**: Manual deployment script (future: integrate into workflows)

**Steps**:
1. Build OPA Docker image with 5 policies
2. Deploy to Cloud Run: `opa-service-demo`
3. Validate health: `curl $OPA_URL/health`
4. Test policy query: `curl $OPA_URL/v1/data/trial_mode`

**Validation**:
- OPA service returns 200 on /health
- All 5 policies loaded (trial_mode, rbac_pp, agent_budget, governor_role, sandbox_routing)
- Policy query returns valid decision

---

**Batch 1: Gateway App Stack Deployment** (6-10 min)

**Workflow**: `waooaw-deploy.yml`

**Trigger**:
```bash
gh workflow run waooaw-deploy.yml \
  -f environment=demo \
  -f terraform_action=plan  # Review plan first

# After plan review, apply
gh workflow run waooaw-deploy.yml \
  -f environment=demo \
  -f terraform_action=apply
```

**What Happens**:
1. Workflow detects Dockerfiles in `src/gateway/cp_gateway/Dockerfile`, `src/gateway/pp_gateway/Dockerfile`
2. Builds Docker images: `waooaw/gateway-cp:demo`, `waooaw/gateway-pp:demo`
3. Pushes to Artifact Registry: `asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/`
4. Terraform applies `cloud/terraform/stacks/gateway/`
5. Deploys Cloud Run services:
   - `waooaw-gateway-cp-demo` (port 8000)
   - `waooaw-gateway-pp-demo` (port 8001)
6. Registers NEGs (Network Endpoint Groups) for load balancer
7. Writes outputs to Terraform state

**Validation**:
- GitHub Actions workflow succeeds (green checkmark)
- Cloud Run services status: READY
- Health check: `curl $CP_GATEWAY_URL/health` → 200 OK
- Health check: `curl $PP_GATEWAY_URL/health` → 200 OK
- NEG IDs available in Terraform state

---

**Batch 2: Foundation Update (Load Balancer Routing)** (5-10 min)

**Workflow**: `waooaw-foundation-deploy.yml`

**Prerequisite**: Update `cloud/terraform/stacks/foundation/environments/default.tfvars`
```hcl
enable_cp    = true
enable_pp    = true
enable_plant = true
enable_gateway = true  # NEW: Route through gateways
```

**Trigger**:
```bash
gh workflow run waooaw-foundation-deploy.yml \
  -f terraform_action=plan  # Review plan

# After plan review, apply
gh workflow run waooaw-foundation-deploy.yml \
  -f terraform_action=apply
```

**What Happens**:
1. Terraform reads gateway NEGs from remote state
2. Updates load balancer routing:
   - `cp.demo.waooaw.com` → CP Gateway → Plant
   - `pp.demo.waooaw.com` → PP Gateway → Plant
3. Regenerates SSL certificate (hash-based name for create_before_destroy)
4. SSL enters PROVISIONING state

**Validation**:
- Foundation workflow succeeds
- SSL certificate status: PROVISIONING → ACTIVE (wait 15-60 min)
- Load balancer routing updated

---

**Batch 3: SSL Certificate Provisioning Wait** (15-60 min)

**Manual Monitoring**:
```bash
# Check SSL status (run in GitHub Actions or manually)
gcloud compute ssl-certificates list --global \
  --format="table(name,managed.status,managed.domainStatus)"
```

**Expected Progression**:
- PROVISIONING → ACTIVE (15-60 min typical)
- Domain status: cp.demo.waooaw.com → ACTIVE, pp.demo.waooaw.com → ACTIVE

**Do NOT proceed to validation until**: All domains show ACTIVE

---

**Batch 4: Post-Deployment Validation** (5 min)

**Health Checks**:
```bash
# Run via GitHub Actions or automated script
curl -f https://cp.demo.waooaw.com/health
curl -f https://pp.demo.waooaw.com/health
curl -f https://plant.demo.waooaw.com/health
```

**Integration Tests**:
```bash
# Run integration test suite against demo
pytest src/gateway/tests/test_integration.py \
  --gateway-url=https://cp.demo.waooaw.com \
  --verbose
```

**Smoke Tests**:
- CP: Submit trial request → 201 Created
- PP: Create agent with admin JWT → 201 Created
- PP: Delete agent with viewer JWT → 403 Forbidden
- OPA: Trial limit exceeded → 429 Too Many Requests
- Budget: Budget exceeded → 402 Payment Required

**Monitoring Validation**:
- Check Cloud Logging for gateway logs
- Verify audit logs writing to PostgreSQL
- Confirm OPA policy queries logged
- Check Redis budget tracking updates

### 3. Rollback Procedure

**Automated Rollback** (if validation fails):

**Step 1: Revert Foundation** (5 min)
```bash
# Disable gateway routing
# Update default.tfvars: enable_gateway=false
gh workflow run waooaw-foundation-deploy.yml \
  -f terraform_action=apply
```

**Step 2: Stop Gateway Services** (2 min)
```bash
# Scale down to zero instances
gcloud run services update waooaw-gateway-cp-demo \
  --min-instances=0 --max-instances=0 \
  --region=asia-south1 --project=waooaw-oauth

gcloud run services update waooaw-gateway-pp-demo \
  --min-instances=0 --max-instances=0 \
  --region=asia-south1 --project=waooaw-oauth
```

**Step 3: Verify Direct Routing** (2 min)
```bash
# Confirm CP/PP/Plant still accessible via direct URLs
curl -f https://cp.demo.waooaw.com/health
curl -f https://pp.demo.waooaw.com/health
```

**Rollback Decision Tree**:
- Gateway health check fails → Rollback foundation, keep gateway deployed (debugging)
- SSL provisioning timeout (>2 hours) → Rollback foundation, investigate DNS
- Integration tests fail → Rollback foundation, fix tests, redeploy
- Critical production incident → Immediate rollback via workflow

### 4. Environment Progression

**Deployment Order**: Demo → UAT → Prod

**Demo Deployment**: Full validation environment
- Purpose: Testing, integration validation, load testing
- Deployment frequency: Daily (on main branch updates)
- Monitoring: Basic Cloud Logging
- Rollback: Automated on failure

**UAT Deployment**: Pre-production staging
- Purpose: User acceptance testing, final validation
- Deployment frequency: Weekly (on stable demo)
- Monitoring: Full observability (OpenTelemetry)
- Rollback: Manual approval required

**Prod Deployment**: Live customer traffic
- Purpose: Serve production workloads
- Deployment frequency: Bi-weekly (on stable UAT)
- Monitoring: Full observability + alerting
- Rollback: Immediate on critical errors

**Promotion Workflow**:
```bash
# Demo → UAT
gh workflow run waooaw-deploy.yml -f environment=uat -f terraform_action=apply
gh workflow run waooaw-foundation-deploy.yml -f terraform_action=apply

# UAT → Prod (after manual approval)
gh workflow run waooaw-deploy.yml -f environment=prod -f terraform_action=apply
gh workflow run waooaw-foundation-deploy.yml -f terraform_action=apply
```

### 5. Post-Deployment Monitoring

**Immediate Monitoring** (First 24 hours):
- Watch Cloud Run logs for errors
- Monitor OPA query latency (<10ms)
- Check Redis connection pool utilization
- Verify audit log writes (PostgreSQL)
- Track gateway latency (p95 <100ms)
- Monitor error rate (<1%)

**Ongoing Monitoring**:
- Daily: Review error logs, security incidents
- Weekly: Load test regression, performance benchmarks
- Monthly: Security scan, dependency updates

**Alerting Thresholds**:
- Error rate >5% → PagerDuty alert
- Gateway latency p95 >200ms → Slack notification
- OPA query latency >50ms → Investigate caching
- Budget critical threshold hit → Email to finance team
- SSL certificate expires in <30 days → Rotate certificate

### 6. Deployment Checklist

**Before Deployment**:
- [ ] All tests passing (125+ tests)
- [ ] Security scan passed
- [ ] Secrets verified in Secret Manager
- [ ] DNS verified (nslookup)
- [ ] Infrastructure dependencies healthy (Plant DB, Redis, OPA)
- [ ] Rollback plan reviewed
- [ ] Stakeholders notified (deployment window)

**During Deployment**:
- [ ] OPA service deployed and healthy
- [ ] Gateway app stack workflow succeeded
- [ ] Foundation workflow succeeded
- [ ] SSL certificate ACTIVE (all domains)
- [ ] Health checks passed

**After Deployment**:
- [ ] Integration tests passed
- [ ] Smoke tests completed
- [ ] Monitoring dashboards updated
- [ ] Team notified (deployment complete)
- [ ] Deployment documented (runbook updated)
- [ ] Post-mortem scheduled (if issues)

### 7. Deployment Timeline

**Full Demo Deployment**: 40-75 minutes

| Phase | Duration | Automated? | Blocking? |
|-------|----------|------------|-----------|
| Pre-deployment checks | 5 min | Partial | Yes |
| OPA service deploy | 5-10 min | Manual script | Yes |
| Gateway app stack | 6-10 min | GitHub Actions | Yes |
| Foundation update | 5-10 min | GitHub Actions | Yes |
| SSL provisioning | 15-60 min | Automated wait | Yes |
| Post-deployment validation | 5 min | Automated tests | No |

**Total**: 40-75 minutes (including SSL wait)

**Optimization**: SSL wait can be parallelized with other environment deployments

### 8. Success Criteria

**Deployment is successful when**:
- ✅ All workflows completed successfully (green checkmarks)
- ✅ SSL certificate ACTIVE for all domains
- ✅ Health checks return 200 OK
- ✅ Integration tests pass (30/30 scenarios)
- ✅ Smoke tests completed successfully
- ✅ No error spikes in Cloud Logging (first hour)
- ✅ Gateway latency p95 <100ms (first hour)
- ✅ Audit logs writing to PostgreSQL
- ✅ Team notified and deployment documented

---

## Phase 5: Architecture Restructuring - Plant-Centric Design (2 weeks)

**Date Added:** 2026-01-17  
**Context:** After completing Phases 0-4, we discovered the gateway middleware was incorrectly placed as a standalone service (`src/gateway/`). This phase restructures the architecture to follow the correct design: CP/PP as thin clients, all business logic in Plant.

**Status:** 🔴 CRITICAL - Must complete before production deployment

### Phase 5 Overview

**Problem:**
- `src/gateway/` created as standalone 4th service (WRONG)
- Gateway middleware should be part of Plant ecosystem (RIGHT)
- CP/PP backends have unused code that should be minimal proxies
- Docker images don't match actual architecture (3 services, not 4)

**Correct Architecture:**
```
src/
├── CP/BackEnd/           → Thin proxy (OAuth + forward to Plant)
├── PP/BackEnd/           → Thin proxy (OAuth + forward to Plant)
└── Plant/
    ├── Gateway/          → All middleware (port 8000)
    └── BackEnd/          → All APIs (port 8001)
```

**Docker Images:**
- `waooaw-cp:latest` (Frontend + Thin Backend)
- `waooaw-pp:latest` (Frontend + Thin Backend)
- `waooaw-plant-gateway:latest` (Middleware only)
- `waooaw-plant-backend:latest` (APIs only)

**Benefits:**
- ✅ CP/PP can be replaced with Angular/mobile apps (no business logic)
- ✅ All business logic in Plant (single source of truth)
- ✅ Gateway and Backend can scale independently
- ✅ Standard microservices pattern (one process per container)
- ✅ Zero refactoring needed when scaling later

---

### GW-5.1: Move Gateway to Plant Ecosystem (3 days)

**Priority:** P0 (Blocks production deployment)  
**Effort:** 3 days  
**Owner:** Backend Team  
**Dependencies:** Phase 4 complete (middleware tested at 99%)

**User Story:**
```gherkin
As a platform architect
I want gateway middleware to live in Plant/Gateway/
So that CP/PP can remain thin clients with no business logic
```

**Changes:**

#### Step 1.1: Create Plant/Gateway Structure (Day 1 - Morning)
```bash
# Create new directory
mkdir -p src/Plant/Gateway
mkdir -p src/Plant/Gateway/middleware

# Move middleware code
mv src/gateway/middleware/*.py src/Plant/Gateway/middleware/
mv src/gateway/middleware/tests/ src/Plant/Gateway/middleware/

# Move infrastructure (for testing)
mv src/gateway/infrastructure/ src/Plant/Gateway/

# Keep test utilities in place for now
# (mock_plant_service.py, test_integration_docker.py, locustfile.py)
```

**Files to Move:**
```
src/gateway/middleware/
├── auth.py              → src/Plant/Gateway/middleware/auth.py
├── rbac.py              → src/Plant/Gateway/middleware/rbac.py
├── policy.py            → src/Plant/Gateway/middleware/policy.py
├── budget.py            → src/Plant/Gateway/middleware/budget.py
├── error_handler.py     → src/Plant/Gateway/middleware/error_handler.py
├── audit.py             → src/Plant/Gateway/middleware/audit.py
├── __init__.py          → src/Plant/Gateway/middleware/__init__.py
└── tests/               → src/Plant/Gateway/middleware/tests/
    ├── test_auth.py
    ├── test_rbac.py
    ├── test_policy.py
    ├── test_budget.py
    └── test_error_handler.py
```

**Validation:**
```bash
# Verify structure
tree -L 3 src/Plant/Gateway/

# Expected output:
# src/Plant/Gateway/
# ├── middleware/
# │   ├── auth.py
# │   ├── rbac.py
# │   ├── policy.py
# │   ├── budget.py
# │   ├── error_handler.py
# │   ├── audit.py
# │   ├── __init__.py
# │   └── tests/
# └── infrastructure/
#     └── feature_flags/
```

**Test After Move:**
```bash
cd src/Plant/Gateway/middleware
pytest tests/ -v

# Expected: 75/76 tests passing (99%)
```

---

#### Step 1.2: Create Plant Gateway Main Application (Day 1 - Afternoon)

**Create:** `src/Plant/Gateway/main.py`

```python
"""
WAOOAW Plant Gateway - Middleware Layer
Port: 8000

All incoming requests flow through this gateway:
CP Frontend → CP Backend (thin) → Plant Gateway → Plant Backend
PP Frontend → PP Backend (thin) → Plant Gateway → Plant Backend

Middleware Stack:
1. ErrorHandlingMiddleware
2. BudgetGuardMiddleware  
3. PolicyMiddleware
4. RBACMiddleware
5. AuthMiddleware
"""

import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx

# Import middleware
from middleware.auth import AuthMiddleware
from middleware.rbac import RBACMiddleware
from middleware.policy import PolicyMiddleware
from middleware.budget import BudgetGuardMiddleware
from middleware.error_handler import ErrorHandlingMiddleware

# Configuration
PLANT_BACKEND_URL = os.getenv("PLANT_BACKEND_URL", "http://plant-backend:8001")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
OPA_URL = os.getenv("OPA_URL", "http://opa:8181")
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY", "")
APPROVAL_UI_URL = os.getenv("APPROVAL_UI_URL", "http://localhost:3000/approval")

# Create FastAPI app
app = FastAPI(
    title="WAOOAW Plant Gateway",
    description="Constitutional middleware layer for all API requests",
    version="1.0.0"
)

# Health check (no auth)
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "plant-gateway",
        "backend_url": PLANT_BACKEND_URL
    }

# Add middleware (reverse order - last added runs first)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(
    BudgetGuardMiddleware, 
    opa_service_url=OPA_URL, 
    redis_url=REDIS_URL
)
app.add_middleware(
    PolicyMiddleware,
    opa_service_url=OPA_URL,
    redis_url=REDIS_URL,
    approval_ui_url=APPROVAL_UI_URL
)
app.add_middleware(RBACMiddleware)
app.add_middleware(AuthMiddleware, jwt_public_key=JWT_PUBLIC_KEY)

# Proxy all API requests to Plant Backend
@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_backend(request: Request, full_path: str):
    """
    Proxy requests to Plant Backend after middleware processing
    """
    target_url = f"{PLANT_BACKEND_URL}/{full_path}"
    query_params = dict(request.query_params)
    
    # Forward headers (add user context from middleware)
    headers = {}
    if hasattr(request.state, "user_id"):
        headers["X-User-Id"] = request.state.user_id
    if hasattr(request.state, "role"):
        headers["X-User-Role"] = request.state.role
    if hasattr(request.state, "correlation_id"):
        headers["X-Correlation-Id"] = request.state.correlation_id
    
    async with httpx.AsyncClient() as client:
        try:
            body = None
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
            
            response = await client.request(
                method=request.method,
                url=target_url,
                params=query_params,
                headers=headers,
                content=body,
                timeout=30.0
            )
            
            return JSONResponse(
                status_code=response.status_code,
                content=response.json() if response.content else {},
                headers=dict(response.headers)
            )
        
        except httpx.TimeoutException:
            return JSONResponse(
                status_code=504,
                content={"error": "Backend service timeout"}
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": f"Gateway error: {str(e)}"}
            )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Validation:**
```bash
cd src/Plant/Gateway
python main.py &

# Wait for startup
sleep 3

# Test health
curl http://localhost:8000/health

# Expected: {"status": "healthy", "service": "plant-gateway"}
```

---

#### Step 1.3: Update Import Paths in Tests (Day 2 - Morning)

**Update:** `src/Plant/Gateway/middleware/tests/*.py`

All test files need updated imports:
```python
# OLD (in src/gateway/middleware/tests/)
from middleware.auth import AuthMiddleware

# NEW (in src/Plant/Gateway/middleware/tests/)
from middleware.auth import AuthMiddleware  # Same, no change needed!
```

**Why no change?** Tests run from `src/Plant/Gateway/` directory, so relative imports work.

**Validation:**
```bash
cd src/Plant/Gateway
pytest middleware/tests/ -v --tb=short

# Expected: 75/76 tests passing (99%)
```

---

#### Step 1.4: Delete Old Gateway Files (Day 2 - Afternoon)

```bash
# Delete standalone gateway files (no longer needed)
rm src/gateway/main.py
rm -rf src/gateway/cp_gateway/
rm -rf src/gateway/pp_gateway/

# Keep test utilities (will move later)
# Keep: src/gateway/tests/mock_plant_service.py
# Keep: src/gateway/tests/test_integration_docker.py
# Keep: src/gateway/tests/locustfile.py
```

**Files Deleted:**
- `src/gateway/main.py` (standalone gateway - wrong concept)
- `src/gateway/cp_gateway/` (unclear purpose)
- `src/gateway/pp_gateway/` (unclear purpose)

**Files Kept:**
- `src/gateway/tests/mock_plant_service.py` (useful for testing)
- `src/gateway/tests/test_integration_docker.py` (integration tests)
- `src/gateway/tests/locustfile.py` (load testing)

**Validation:**
```bash
# Verify deletions
ls src/gateway/

# Expected output:
# tests/
# requirements.txt
# (no main.py, no cp_gateway/, no pp_gateway/)
```

**Acceptance Criteria:**
- [ ] Plant/Gateway/middleware/ contains all 6 middleware files
- [ ] Plant/Gateway/main.py created and starts successfully
- [ ] All 75 unit tests pass from new location
- [ ] Old gateway files deleted
- [ ] No broken imports in any file

---

### GW-5.2: Simplify CP/PP to Thin Proxies (2 days)

**Priority:** P0  
**Effort:** 2 days  
**Owner:** Frontend Team + Backend Team

**User Story:**
```gherkin
As a frontend developer
I want CP/PP backends to be minimal proxies
So that I can replace them with Angular/mobile apps without losing functionality
```

**Changes:**

#### Step 2.1: Simplify CP Backend (Day 3 - Morning)

**Update:** `src/CP/BackEnd/main.py`

```python
"""
WAOOAW Customer Portal - Thin Backend
Port: 8015

Responsibilities:
1. Serve React SPA (static files)
2. Handle OAuth callback (Google login)
3. Proxy all API requests to Plant Gateway

NO business logic here - everything in Plant!
"""

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
import httpx

from core.config import settings
from api import auth_router  # OAuth only

app = FastAPI(
    title=settings.APP_NAME,
    description="Customer Portal - Thin Client",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth routes only
app.include_router(auth_router, prefix="/api")

# Frontend static files
FRONTEND_DIST = Path("/app/frontend/dist")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cp-thin-backend"}

# Serve React SPA
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")
    
    @app.get("/")
    async def serve_spa():
        return FileResponse(FRONTEND_DIST / "index.html")
    
    @app.get("/{full_path:path}")
    async def serve_spa_catchall(full_path: str):
        # SPA routing - always serve index.html
        if full_path.startswith("api/"):
            # API routes - proxy to Plant Gateway
            return await proxy_to_plant(full_path)
        return FileResponse(FRONTEND_DIST / "index.html")

# Proxy all API requests to Plant Gateway
@app.api_route("/api/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_plant(full_path: str, request: Request = None):
    """Forward all API requests to Plant Gateway"""
    plant_gateway_url = settings.PLANT_GATEWAY_URL  # http://plant-gateway:8000
    target_url = f"{plant_gateway_url}/api/{full_path}"
    
    # Forward request
    async with httpx.AsyncClient() as client:
        try:
            if request:
                headers = dict(request.headers)
                body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
                params = dict(request.query_params)
            else:
                headers, body, params = {}, None, {}
            
            response = await client.request(
                method=request.method if request else "GET",
                url=target_url,
                headers=headers,
                content=body,
                params=params,
                timeout=30.0
            )
            
            return response.json()
        except Exception as e:
            return {"error": f"Gateway unavailable: {str(e)}"}, 503
```

**Add to:** `src/CP/BackEnd/core/config.py`

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Plant Gateway URL (NEW)
    PLANT_GATEWAY_URL: str = Field(
        default="http://plant-gateway:8000",
        description="Plant Gateway service URL"
    )
```

**Validation:**
```bash
cd src/CP/BackEnd
python main.py &

curl http://localhost:8015/health
# Expected: {"status": "healthy", "service": "cp-thin-backend"}

# Test proxy (assuming Plant Gateway running)
curl http://localhost:8015/api/v1/agents
# Should forward to Plant Gateway
```

---

#### Step 2.2: Simplify PP Backend (Day 3 - Afternoon)

**Update:** `src/PP/BackEnd/main.py` (same pattern as CP)

```python
"""
WAOOAW Platform Portal - Thin Backend
Port: 8006

Responsibilities:
1. Serve React Admin SPA (static files)
2. Handle OAuth callback (Google login)
3. Proxy all API requests to Plant Gateway

NO business logic here - everything in Plant!
"""

# Same structure as CP, just different port and app name
# (Copy from Step 2.1, adjust app name and port)
```

**Validation:**
```bash
cd src/PP/BackEnd
python main.py &

curl http://localhost:8006/health
# Expected: {"status": "healthy", "service": "pp-thin-backend"}
```

**Acceptance Criteria:**
- [ ] CP main.py simplified to <150 lines
- [ ] PP main.py simplified to <150 lines
- [ ] Both backends proxy to Plant Gateway
- [ ] OAuth still works (callback routes preserved)
- [ ] Static file serving works (React SPA loads)
- [ ] No middleware imports in CP/PP (all in Plant)

---

### GW-5.3: Create Docker Images (2 days)

**Priority:** P0  
**Effort:** 2 days  
**Owner:** DevOps Team

**User Story:**
```gherkin
As a DevOps engineer
I want 4 separate Docker images (CP, PP, Plant-Gateway, Plant-Backend)
So that each service can scale independently
```

**Changes:**

#### Step 3.1: Plant Gateway Dockerfile (Day 4 - Morning)

**Create:** `src/Plant/Gateway/Dockerfile`

```dockerfile
# Multi-stage build for Plant Gateway
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy gateway code
COPY middleware/ /app/middleware/
COPY infrastructure/ /app/infrastructure/
COPY main.py /app/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run gateway
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Create:** `src/Plant/Gateway/requirements.txt`

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
httpx==0.26.0
redis==5.0.1
PyJWT==2.8.0
cryptography==41.0.7
python-multipart==0.0.6
```

**Build and Test:**
```bash
cd src/Plant/Gateway
docker build -t waooaw-plant-gateway:latest .

# Test
docker run -d -p 8000:8000 \
  -e PLANT_BACKEND_URL=http://host.docker.internal:8001 \
  -e JWT_PUBLIC_KEY="$JWT_PUBLIC_KEY" \
  waooaw-plant-gateway:latest

# Wait and test
sleep 5
curl http://localhost:8000/health
```

---

#### Step 3.2: Plant Backend Dockerfile (Day 4 - Afternoon)

**Update:** `src/Plant/BackEnd/Dockerfile` (if not exists, create)

```dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy backend code
COPY api/ /app/api/
COPY core/ /app/core/
COPY models/ /app/models/
COPY services/ /app/services/
COPY middleware/ /app/middleware/
COPY main.py /app/

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8001/health')"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

---

#### Step 3.3: CP Combined Dockerfile (Day 5 - Morning)

**Create:** `src/CP/Dockerfile`

```dockerfile
# Multi-stage: Frontend build + Backend
FROM node:18-alpine as frontend-builder

WORKDIR /app/frontend
COPY FrontEnd/package*.json ./
RUN npm ci
COPY FrontEnd/ ./
RUN npm run build

# Backend stage
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY BackEnd/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY BackEnd/ /app/

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

EXPOSE 8015

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8015"]
```

---

#### Step 3.4: PP Combined Dockerfile (Day 5 - Afternoon)

**Create:** `src/PP/Dockerfile` (same pattern as CP, port 8006)

---

#### Step 3.5: Docker Compose for Local Development (Day 5 - Evening)

**Create:** `docker-compose.local.yml`

```yaml
version: '3.8'

services:
  # Infrastructure
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: waooaw
      POSTGRES_USER: waooaw
      POSTGRES_PASSWORD: waooaw_password
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U waooaw"]
      interval: 5s
      timeout: 5s
      retries: 5
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
  
  opa:
    image: openpolicyagent/opa:latest
    command: ["run", "--server", "--addr=0.0.0.0:8181"]
    ports:
      - "8181:8181"
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8181/health"]
      interval: 5s
      timeout: 3s
      retries: 5
  
  # Plant Services
  plant-backend:
    build:
      context: ./src/Plant/BackEnd
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://waooaw:waooaw_password@postgres:5432/waooaw
      REDIS_URL: redis://redis:6379/0
    ports:
      - "8001:8001"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8001/health"]
      interval: 10s
      timeout: 5s
      retries: 3
  
  plant-gateway:
    build:
      context: ./src/Plant/Gateway
      dockerfile: Dockerfile
    environment:
      PLANT_BACKEND_URL: http://plant-backend:8001
      REDIS_URL: redis://redis:6379/0
      OPA_URL: http://opa:8181
      JWT_PUBLIC_KEY: ${JWT_PUBLIC_KEY}
    ports:
      - "8000:8000"
    depends_on:
      plant-backend:
        condition: service_healthy
      redis:
        condition: service_healthy
      opa:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
  
  # Thin Clients
  cp-app:
    build:
      context: ./src/CP
      dockerfile: Dockerfile
    environment:
      PLANT_GATEWAY_URL: http://plant-gateway:8000
      GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID}
      GOOGLE_CLIENT_SECRET: ${GOOGLE_CLIENT_SECRET}
    ports:
      - "8015:8015"
    depends_on:
      plant-gateway:
        condition: service_healthy
  
  pp-app:
    build:
      context: ./src/PP
      dockerfile: Dockerfile
    environment:
      PLANT_GATEWAY_URL: http://plant-gateway:8000
      GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID_PP}
      GOOGLE_CLIENT_SECRET: ${GOOGLE_CLIENT_SECRET_PP}
    ports:
      - "8006:8006"
    depends_on:
      plant-gateway:
        condition: service_healthy

networks:
  default:
    name: waooaw-network
```

**Test Full Stack:**
```bash
# Start all services
docker-compose -f docker-compose.local.yml up -d

# Wait for health checks
sleep 30

# Test each service
curl http://localhost:8001/health  # Plant Backend
curl http://localhost:8000/health  # Plant Gateway
curl http://localhost:8015/health  # CP
curl http://localhost:8006/health  # PP

# Test flow: CP → Gateway → Backend
curl -H "Authorization: Bearer $TEST_JWT" \
  http://localhost:8015/api/v1/agents

# Should proxy through CP → Gateway → Backend
```

**Acceptance Criteria:**
- [ ] Plant Gateway image builds successfully
- [ ] Plant Backend image builds successfully
- [ ] CP combined image builds successfully
- [ ] PP combined image builds successfully
- [ ] All 4 services start via docker-compose
- [ ] Health checks pass for all services
- [ ] Request flow works: CP → Gateway → Backend

---

### GW-5.4: Update Tests for New Structure (1 day)

**Priority:** P1  
**Effort:** 1 day  
**Owner:** QA Team

**User Story:**
```gherkin
As a QA engineer
I want all tests updated to use the new Plant/Gateway structure
So that CI/CD continues to pass
```

**Changes:**

#### Step 4.1: Update Integration Tests (Day 6 - Morning)

**Update:** `src/gateway/tests/test_integration_docker.py`

```python
# Update paths
# OLD: from middleware.auth import AuthMiddleware
# NEW: sys.path.append to Plant/Gateway, then import

import sys
sys.path.insert(0, '/workspaces/WAOOAW/src/Plant/Gateway')

from middleware.auth import AuthMiddleware
# ... rest of tests unchanged
```

**Or move file:**
```bash
mv src/gateway/tests/test_integration_docker.py \
   src/Plant/Gateway/tests/test_integration.py
```

---

#### Step 4.2: Update E2E Tests (Day 6 - Afternoon)

**Update:** `src/gateway/tests/test_e2e_gateway.py`

```python
# Update URLs
GATEWAY_URL = "http://localhost:8000"  # Plant Gateway
CP_URL = "http://localhost:8015"        # CP thin client
PP_URL = "http://localhost:8006"        # PP thin client

# Test through CP proxy
async def test_cp_proxies_to_gateway():
    """CP should proxy to Plant Gateway"""
    response = await client.get(
        f"{CP_URL}/api/v1/agents",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

# Test direct to Gateway
async def test_gateway_direct():
    """Gateway should work directly"""
    response = await client.get(
        f"{GATEWAY_URL}/api/v1/agents",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

---

#### Step 4.3: Update Load Tests (Day 6 - Evening)

**Update:** `src/gateway/tests/locustfile.py`

```python
# Update host
class GatewayUser(HttpUser):
    host = "http://localhost:8000"  # Plant Gateway directly
    
# Or test through CP
class CPUser(HttpUser):
    host = "http://localhost:8015"  # CP thin client
```

**Run All Tests:**
```bash
# Unit tests (from new location)
cd src/Plant/Gateway
pytest middleware/tests/ -v
# Expected: 75/76 passing

# Integration tests
pytest tests/test_integration.py -v
# Expected: 10/10 passing

# E2E tests (with docker-compose running)
cd /workspaces/WAOOAW
docker-compose -f docker-compose.local.yml up -d
sleep 30
pytest src/gateway/tests/test_e2e_gateway.py -v
# Expected: 18/18 passing

# Load tests
locust -f src/gateway/tests/locustfile.py --headless \
  --users 100 --spawn-rate 10 --run-time 60s \
  --host http://localhost:8000
# Expected: RPS ~1000, p95 <100ms
```

**Acceptance Criteria:**
- [ ] All unit tests pass (75/76, 99%)
- [ ] All integration tests pass (10/10, 100%)
- [ ] All E2E tests pass (18/18, 100%)
- [ ] Load tests meet targets (1000 RPS, p95 <100ms)
- [ ] CI/CD pipeline updated with new paths
- [ ] All test documentation updated

---

### GW-5.5: Update Documentation & Cleanup (1 day)

**Priority:** P2  
**Effort:** 1 day  
**Owner:** Tech Lead

**User Story:**
```gherkin
As a developer
I want updated documentation reflecting the new architecture
So that onboarding and maintenance are easy
```

**Changes:**

#### Step 5.1: Update Architecture Docs (Day 7 - Morning)

**Update:** `main/Foundation/Architecture/APIGateway/GATEWAY_ARCHITECTURE_BLUEPRINT.md`

Add section:
```markdown
## Architecture Update (January 2026)

**Previous (Incorrect):**
- Standalone gateway service at `src/gateway/`
- CP/PP with business logic

**Current (Correct):**
- Plant/Gateway/ contains all middleware
- Plant/BackEnd/ contains all APIs
- CP/PP are thin proxies only

**Rationale:**
- CP/PP can be replaced with any frontend framework
- All business logic in Plant (single source of truth)
- Gateway and Backend scale independently
```

---

#### Step 5.2: Update README Files (Day 7 - Afternoon)

**Update:** `src/Plant/Gateway/README.md` (create)

```markdown
# Plant Gateway

Constitutional middleware layer for all API requests.

## Architecture

All requests flow through this gateway:
- CP Frontend → CP Backend (thin) → **Plant Gateway** → Plant Backend
- PP Frontend → PP Backend (thin) → **Plant Gateway** → Plant Backend

## Middleware Stack

1. AuthMiddleware - JWT validation
2. RBACMiddleware - Role-based access
3. PolicyMiddleware - OPA constitutional policies
4. BudgetGuardMiddleware - Spend tracking
5. ErrorHandlingMiddleware - Problem Details RFC 7807

## Running Locally

```bash
cd src/Plant/Gateway
python main.py
# Starts on port 8000
```

## Running Tests

```bash
pytest middleware/tests/ -v
# Expected: 75/76 tests passing (99%)
```

## Docker

```bash
docker build -t waooaw-plant-gateway:latest .
docker run -p 8000:8000 waooaw-plant-gateway:latest
```
```

**Update:** `README.md` (root)

```markdown
## Architecture

WAOOAW follows a **Plant-centric microservices architecture**:

### Services

1. **CP (Customer Portal)** - Port 8015
   - Thin client: React SPA + OAuth proxy
   - Proxies all API requests to Plant Gateway
   
2. **PP (Platform Portal)** - Port 8006
   - Thin client: React Admin + OAuth proxy
   - Proxies all API requests to Plant Gateway
   
3. **Plant Gateway** - Port 8000
   - Constitutional middleware (Auth, RBAC, Policy, Budget)
   - Routes to Plant Backend
   
4. **Plant Backend** - Port 8001
   - All business logic and APIs
   - Agents, Genesis, Audit, Trials

### Request Flow

```
Browser → CP (8015) → Plant Gateway (8000) → Plant Backend (8001) → Database
```

### Docker Images

- `waooaw-cp:latest` - CP frontend + backend (thin)
- `waooaw-pp:latest` - PP frontend + backend (thin)
- `waooaw-plant-gateway:latest` - Middleware only
- `waooaw-plant-backend:latest` - APIs only
```

---

#### Step 5.3: Final Cleanup (Day 7 - Evening)

```bash
# Delete empty directories
rmdir src/gateway/cp_gateway 2>/dev/null
rmdir src/gateway/pp_gateway 2>/dev/null

# Move remaining test files to Plant
mv src/gateway/tests/mock_plant_service.py \
   src/Plant/Gateway/tests/
mv src/gateway/tests/test_e2e_gateway.py \
   src/Plant/Gateway/tests/
mv src/gateway/tests/locustfile.py \
   src/Plant/Gateway/tests/

# Delete src/gateway/ if empty except requirements.txt
ls src/gateway/
# If only requirements.txt remains, can delete entire folder
```

**Acceptance Criteria:**
- [ ] GATEWAY_ARCHITECTURE_BLUEPRINT.md updated
- [ ] Plant/Gateway/README.md created
- [ ] Root README.md updated with architecture
- [ ] All test files in correct locations
- [ ] No broken links in documentation
- [ ] Architecture diagrams updated

---

### Phase 5 Summary

**Timeline:** 7 days (1.4 weeks)

| Step | Duration | Owner | Status |
|------|----------|-------|--------|
| 5.1: Move to Plant/Gateway | 3 days | Backend | ⏳ Pending |
| 5.2: Simplify CP/PP | 2 days | Frontend/Backend | ⏳ Pending |
| 5.3: Create Docker Images | 2 days | DevOps | ⏳ Pending |
| 5.4: Update Tests | 1 day | QA | ⏳ Pending |
| 5.5: Update Docs | 1 day | Tech Lead | ⏳ Pending |

**Risk Assessment:**
- 🟢 **LOW RISK**: Middleware code already tested (99%)
- 🟢 **LOW RISK**: CP/PP simplification (removes code)
- 🟡 **MEDIUM RISK**: Docker orchestration complexity
- 🟢 **LOW RISK**: Tests already passing, just moving files

**Success Criteria:**
- ✅ All middleware in Plant/Gateway/
- ✅ CP/PP < 150 lines each (thin proxies)
- ✅ 4 Docker images build successfully
- ✅ All tests pass (99% unit, 100% integration)
- ✅ docker-compose.local.yml works end-to-end
- ✅ Documentation updated and accurate

**Next Steps After Phase 5:**
- Deploy to Demo environment (use updated docker-compose)
- Run E2E tests against Demo
- Monitor performance (Gateway → Backend latency)
- Prepare for UAT deployment

---

**End of Implementation Plan** 🚀
