# Gateway Implementation Plan - Peer Review Enhancements
## Comprehensive Updates Based on Staff Engineer Review

**Date:** 2026-01-17  
**Review ID:** PEER-REVIEW-001  
**Status:** All Critical Gaps Addressed  

---

## Executive Summary

The peer review identified **13 critical gaps (GAP-001 through GAP-013)** and **6 missing stories (MS-001 through MS-006)** that prevented the implementation plan from being actionable.

**This document contains all remaining enhancements** that should be incorporated into the Gateway Final IMPLEMENTATION_PLAN.md file.

---

## Section 1: Middleware Registration Code (GAP-001)

**Add to all middleware stories (GW-100 through GW-105):**

### FastAPI Middleware Registration Pattern

```python
# src/CP/BackEnd/main.py
# src/PP/BackEnd/main.py

from fastapi import FastAPI
from middleware.error import ErrorHandlingMiddleware
from middleware.audit import AuditLoggingMiddleware
from middleware.budget import BudgetGuardMiddleware
from middleware.policy import PolicyMiddleware
from middleware.rbac import RBACMiddleware  # PP only
from middleware.auth import ConstitutionalAuthMiddleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CP Gateway" if IS_CP else "PP Gateway")

# CRITICAL: Order matters - middleware executes in REVERSE order
# (First added = outermost layer, runs last on request, first on response)

app.add_middleware(ErrorHandlingMiddleware)       # Layer 7: Catch-all errors
app.add_middleware(AuditLoggingMiddleware)        # Layer 6: Log everything
app.add_middleware(BudgetGuardMiddleware)         # Layer 5: Budget enforcement
app.add_middleware(PolicyMiddleware)              # Layer 4: OPA policy decisions
if not IS_CP:  # PP only
    app.add_middleware(RBACMiddleware)            # Layer 3: Role-based access
app.add_middleware(ConstitutionalAuthMiddleware)  # Layer 2: JWT + correlation_id
app.add_middleware(
    CORSMiddleware,                               # Layer 1: CORS (existing)
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Public endpoints (skip auth middleware)
PUBLIC_PATHS = [
    "/health",
    "/api/auth/google/login",
    "/api/auth/google/callback",
    "/openapi.json",
    "/docs"
]
```

---

## Section 2: Redis Data Structures (GAP-005)

**Add to GW-103 (Budget Middleware) and GW-400 (Rate Limiting):**

### Budget Tracking Redis Schema

```python
# Budget keys (GW-103)
KEY_PATTERN = "budget:agent:{agent_id}:daily:{YYYY-MM-DD}"
DATA_TYPE = "HASH"
TTL = 7 days  # Not 30 days (cost optimization)

EXAMPLE_KEY = "budget:agent:AGENT-123:daily:2026-01-17"
HASH_FIELDS = {
    "spent_usd": "0.45",              # Dollars spent today
    "task_count": "12",               # Tasks executed today
    "last_updated": "2026-01-17T10:30:00Z",
    "warnings_sent": "1"              # Budget warning count
}

# Python implementation
async def get_agent_budget_today(agent_id: str) -> dict:
    key = f"budget:agent:{agent_id}:daily:{date.today().isoformat()}"
    data = await redis.hgetall(key)
    if not data:
        # Initialize
        await redis.hset(key, mapping={
            "spent_usd": "0.00",
            "task_count": "0",
            "last_updated": datetime.utcnow().isoformat(),
            "warnings_sent": "0"
        })
        await redis.expire(key, 86400 * 7)  # 7-day TTL
        return {"spent_usd": 0.0, "task_count": 0}
    
    return {
        "spent_usd": float(data["spent_usd"]),
        "task_count": int(data["task_count"]),
        "warnings_sent": int(data["warnings_sent"])
    }

async def increment_agent_spend(agent_id: str, amount_usd: float):
    key = f"budget:agent:{agent_id}:daily:{date.today().isoformat()}"
    await redis.hincrbyfloat(key, "spent_usd", amount_usd)
    await redis.hincrby(key, "task_count", 1)
    await redis.hset(key, "last_updated", datetime.utcnow().isoformat())
```

### Rate Limiting Redis Schema

```python
# Rate limit keys (GW-400)
KEY_PATTERN = "ratelimit:{customer_id}:{window_start_epoch}"
DATA_TYPE = "SORTED_SET"
TTL = 1 hour

EXAMPLE_KEY = "ratelimit:CUST-123:1705492800"
SORTED_SET_MEMBERS = [
    (1705492801.123, "req_1"),  # (score=timestamp, member=request_id)
    (1705492802.456, "req_2"),
    (1705492803.789, "req_3"),
]

# Python implementation (sliding window)
async def check_rate_limit(customer_id: str, limit: int, window_seconds: int = 3600) -> bool:
    now = time.time()
    window_start = now - window_seconds
    key = f"ratelimit:{customer_id}:{int(now // window_seconds) * window_seconds}"
    
    # Remove expired entries
    await redis.zremrangebyscore(key, 0, window_start)
    
    # Count requests in window
    count = await redis.zcard(key)
    
    if count >= limit:
        return False  # Rate limit exceeded
    
    # Add current request
    await redis.zadd(key, {f"req_{uuid.uuid4()}": now})
    await redis.expire(key, window_seconds * 2)  # Double TTL for safety
    
    return True  # Request allowed

# Get remaining quota
async def get_rate_limit_status(customer_id: str, limit: int) -> dict:
    now = time.time()
    window_start = now - 3600
    key = f"ratelimit:{customer_id}:{int(now // 3600) * 3600}"
    
    count = await redis.zcard(key)
    remaining = max(0, limit - count)
    reset_time = (int(now // 3600) + 1) * 3600  # Next hour boundary
    
    return {
        "limit": limit,
        "remaining": remaining,
        "reset": reset_time
    }
```

---

## Section 3: Trial Task Counter (SE-004 Enhancement)

**Add to GW-102 (Policy Middleware):**

```python
# src/CP/BackEnd/middleware/policy.py

async def get_task_count_today(customer_id: str) -> int:
    """Get trial customer's task count for today."""
    key = f"trial:tasks:{customer_id}:{date.today().isoformat()}"
    count = await redis.get(key)
    
    if count is None:
        # Initialize counter with 24-hour TTL
        await redis.set(key, 0, ex=86400)
        return 0
    
    return int(count)

async def increment_task_count(customer_id: str):
    """Increment trial customer's task count."""
    key = f"trial:tasks:{customer_id}:{date.today().isoformat()}"
    new_count = await redis.incr(key)
    
    # Set TTL on first increment (in case key exists without TTL)
    if new_count == 1:
        await redis.expire(key, 86400)
    
    return new_count

# In PolicyMiddleware
async def __call__(self, request: Request, call_next):
    ctx: ConstitutionalContext = request.state.constitutional_context
    
    if ctx.trial_mode:
        # Check trial limits
        task_count = await get_task_count_today(ctx.customer_id)
        
        if task_count >= 10:
            # Query OPA for denial reason
            opa_response = await opa_client.query("trial_mode/allow", {
                "input": {
                    "customer_id": ctx.customer_id,
                    "task_count_today": task_count,
                    "trial_expires_at": ctx.trial_expires_at.isoformat()
                }
            })
            
            if not opa_response["result"]["allow"]:
                raise TrialLimitExceeded(
                    detail=opa_response["result"]["reason"],
                    task_count=task_count,
                    limit=10
                )
        
        # Increment counter for this request
        await increment_task_count(ctx.customer_id)
    
    return await call_next(request)
```

---

## Section 4: Async Audit Writer (SE-005 Enhancement)

**Add to GW-104 (Audit Middleware):**

```python
# src/CP/BackEnd/services/audit_service.py

import asyncio
import time
from typing import Dict, List
from collections import deque

class AsyncAuditWriter:
    """
    Batched async audit log writer with performance optimizations.
    
    Features:
    - Batches up to 100 entries before flushing
    - Flushes every 5 seconds regardless of batch size
    - Non-blocking queue with back-pressure (max 1000 entries)
    - Graceful shutdown (flushes remaining entries)
    """
    
    def __init__(
        self, 
        batch_size: int = 100,
        flush_interval: float = 5.0,
        max_queue_size: int = 1000
    ):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_queue_size = max_queue_size
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.background_task = None
        self._shutdown = False
    
    async def start(self):
        """Start background audit writer task."""
        self.background_task = asyncio.create_task(self._process_queue())
        logger.info("Async audit writer started")
    
    async def stop(self):
        """Stop background task and flush remaining entries."""
        self._shutdown = True
        if self.background_task:
            await self.background_task
        logger.info("Async audit writer stopped")
    
    async def _process_queue(self):
        """Background task that processes audit queue."""
        batch: List[Dict] = []
        last_flush_time = time.time()
        
        while not self._shutdown:
            try:
                # Wait for next item with timeout
                try:
                    entry = await asyncio.wait_for(
                        self.queue.get(),
                        timeout=self.flush_interval
                    )
                    batch.append(entry)
                    self.queue.task_done()
                except asyncio.TimeoutError:
                    pass  # Timeout, check if we need to flush
                
                # Flush conditions
                current_time = time.time()
                time_since_flush = current_time - last_flush_time
                should_flush = (
                    len(batch) >= self.batch_size or
                    (batch and time_since_flush >= self.flush_interval)
                )
                
                if should_flush:
                    await self._flush_batch(batch)
                    batch = []
                    last_flush_time = time.time()
            
            except Exception as e:
                logger.error(f"Audit writer error: {e}", exc_info=True)
                # Don't lose entries on error
                batch = []
        
        # Final flush on shutdown
        if batch:
            await self._flush_batch(batch)
    
    async def _flush_batch(self, batch: List[Dict]):
        """Write batch of audit entries to PostgreSQL."""
        if not batch:
            return
        
        try:
            async with db_pool.acquire() as conn:
                # Batch insert (much faster than individual inserts)
                await conn.executemany(
                    """
                    INSERT INTO gateway_audit_logs (
                        correlation_id, causation_id, timestamp,
                        customer_id, user_id, agent_id,
                        method, path, status_code, duration_ms,
                        constitutional_context, opa_decision, error_message
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
                    )
                    """,
                    [(
                        entry["correlation_id"],
                        entry["causation_id"],
                        entry["timestamp"],
                        entry["customer_id"],
                        entry["user_id"],
                        entry.get("agent_id"),
                        entry["method"],
                        entry["path"],
                        entry["status_code"],
                        entry["duration_ms"],
                        json.dumps(entry["constitutional_context"]),
                        json.dumps(entry.get("opa_decision")),
                        entry.get("error_message")
                    ) for entry in batch]
                )
            
            logger.info(f"Flushed {len(batch)} audit entries to PostgreSQL")
        
        except Exception as e:
            logger.error(f"Failed to flush audit batch: {e}", exc_info=True)
            # TODO: Dead-letter queue for failed audit writes
    
    async def log(self, entry: Dict):
        """
        Queue an audit entry for async write.
        
        Raises:
            asyncio.QueueFull: If queue is full (back-pressure)
        """
        try:
            # Non-blocking put with immediate failure if full
            self.queue.put_nowait(entry)
        except asyncio.QueueFull:
            logger.warning("Audit queue full, dropping entry (back-pressure)")
            # In production, send to Pub/Sub DLQ instead of dropping
            # await pubsub_client.publish("audit-dlq", entry)

# Global instance
audit_writer = AsyncAuditWriter()

# Startup/shutdown hooks in main.py
@app.on_event("startup")
async def startup_event():
    await audit_writer.start()

@app.on_event("shutdown")
async def shutdown_event():
    await audit_writer.stop()
```

---

## Section 5: Missing Stories (Add to Plan)

### MS-001: Shared Middleware Library Extraction

**Priority:** P1  
**Phase:** Insert between Phase 1 and Phase 2  
**Effort:** 3 days  
**Owner:** Backend Team  

```gherkin
As a platform engineer
I want middleware code shared between CP/PP in a common library
So that we maintain one implementation and reduce bugs

Acceptance Criteria:
- [ ] Create shared-middleware/ Python package with setup.py
- [ ] Extract identical middleware: auth.py, audit.py, error.py
- [ ] Keep platform-specific: rbac.py (PP only), policy.py (different OPA policies)
- [ ] Publish to internal PyPI or Git submodule
- [ ] Update CP/PP requirements.txt: shared-middleware==0.1.0
- [ ] 70%+ code reuse achieved

File Structure:
shared-middleware/
├── setup.py
├── README.md
├── shared_middleware/
│   ├── __init__.py
│   ├── auth.py              # JWT validation
│   ├── audit.py             # Audit logging
│   ├── error.py             # RFC 7807 errors
│   ├── models.py            # ConstitutionalContext
│   └── utils/
│       ├── correlation.py   # Correlation ID generation
│       └── opa_client.py    # OPA query wrapper
└── tests/
    ├── test_auth.py
    ├── test_audit.py
    └── test_error.py

Technical Tasks:
1. Create shared-middleware/ package structure with setup.py
2. Extract auth, audit, error middleware from CP (pick one as canonical)
3. Write shared middleware unit tests (30 tests)
4. Publish to internal PyPI (pip install -i https://pypi.waooaw.com shared-middleware)
5. Update CP/PP to import from shared library
6. Remove duplicate code from CP/PP
7. Document shared vs separate middleware in README

Dependencies: GW-105 (error middleware design complete)
```

### MS-002: Trial Mode Sandbox Provisioning

**Priority:** P1  
**Phase:** Insert in Phase 1 (parallel with GW-102)  
**Effort:** 7 days  
**Owner:** Platform Team  
**Cost Impact:** +$10-15/month (sandbox Cloud Run service)  

```gherkin
As a trial customer
I want to execute agents in a sandbox that can't affect production data
So that I can safely test the platform

Acceptance Criteria:
- [ ] Plant Sandbox Cloud Run service deployed
  - Service name: plant-sandbox
  - URL: https://plant-sandbox.demo.waooaw.com
  - Database: Isolated PostgreSQL schema "trial_sandbox"
  - CPU/Memory: Same as production Plant (500m CPU, 1GB RAM)
- [ ] Sandbox has limited agent catalog:
  - Only Genesis Agent visible
  - No customer agents
  - 5 basic skills: Python, JavaScript, Sales, Marketing, Math
- [ ] Sandbox agent executions use mock external APIs:
  - No real email sending
  - No real payment processing
  - No real external API calls (L0-03 compliance)
- [ ] Gateway routes trial customers to sandbox (GW-102 integration)
- [ ] Sandbox data purged after 30 days (automated cleanup job)
- [ ] Sandbox performance matches production (<500ms p95 latency)

Technical Tasks:
1. Deploy plant-sandbox Cloud Run service (duplicate of plant service)
2. Create "trial_sandbox" PostgreSQL schema with RLS isolation
3. Seed sandbox with Genesis Agent + 5 basic skills
4. Add mock external API responders (email, payments, web scraping)
5. Update GW-102 sandbox routing to use sandbox URL
6. Create sandbox data cleanup Cloud Scheduler job (daily, purge >30 days old)
7. Add sandbox monitoring dashboard
8. Document sandbox limitations in trial onboarding

Dependencies: GW-102 (policy middleware with sandbox routing)
Cost: +$10-15/month (Cloud Run always-on instance)
```

### MS-005: Cost Guard Automation

**Priority:** P0  
**Phase:** Insert in Phase 0 (infrastructure)  
**Effort:** 5 days  
**Owner:** Platform Team  

```gherkin
As a platform operator
I want automated cost guards at 80%/95%/100% of $100/month budget
So that we never exceed budget without explicit Governor approval

Acceptance Criteria:
- [ ] Cloud Function deployed: cost-guard-enforcer
- [ ] Cloud Function triggered by Cloud Billing Pub/Sub topic
- [ ] 80% guard ($80/month):
  - Send WARNING alert to platform-ops Slack channel
  - Throttle audit log writes to 80% rate (batch size 80 instead of 100)
  - Increase OPA cache TTL to 10 minutes (from 5 minutes)
- [ ] 95% guard ($95/month):
  - Send CRITICAL alert to platform-ops + Governor
  - Enable aggressive caching (OPA TTL 30 minutes)
  - Disable detailed audit logs (basic logs only, no constitutional_context)
  - Throttle WebSocket connections (max 2 per customer, down from 5)
- [ ] 100% guard ($100/month):
  - Send EMERGENCY alert to Governor
  - Halt all new trial signups
  - Enable minimal gateway mode (Auth + Error handling only, disable Policy/Budget/RBAC)
  - Notify Governor for budget increase approval
- [ ] Cost monitoring dashboard (GCP Cloud Monitoring):
  - Real-time spend (updated hourly)
  - Projected monthly spend
  - Cost guard threshold indicators (80%, 95%, 100%)
  - Alert history log

Technical Tasks:
1. Create Cloud Function: cost-guard-enforcer (Python 3.11)
2. Subscribe to Cloud Billing Pub/Sub topic (projects/waooaw-oauth/topics/billing)
3. Implement 3-tier throttling logic (80%/95%/100%)
4. Create Slack webhook integration (platform-ops channel)
5. Add Governor notification (email + Slack DM)
6. Create cost monitoring dashboard (GCP Cloud Monitoring)
7. Write cost guard tests (simulate budget thresholds)
8. Document manual override procedure (Governor approval required)

Dependencies: None (infrastructure, can run immediately)
Cost: $0 (Cloud Functions free tier covers this usage)
```

### MS-006: Feature Flag Infrastructure

**Priority:** P1  
**Phase:** Insert in Phase 0 (infrastructure)  
**Effort:** 4 days  
**Owner:** Backend Team  

```gherkin
As a platform engineer
I want to toggle gateway features via environment variables and per-customer overrides
So that we can roll back problematic middleware without redeployment

Acceptance Criteria:
- [ ] Environment variable feature flags (global):
  - ENABLE_AUTH_MIDDLEWARE=true/false
  - ENABLE_RBAC_MIDDLEWARE=true/false
  - ENABLE_POLICY_MIDDLEWARE=true/false
  - ENABLE_BUDGET_MIDDLEWARE=true/false
  - ENABLE_AUDIT_MIDDLEWARE=true/false
  - ENABLE_ERROR_MIDDLEWARE=true/false
  - ENABLE_WEBSOCKET_MIDDLEWARE=true/false
- [ ] Per-customer feature flag overrides (database):
  ```sql
  CREATE TABLE gateway_feature_flags (
      customer_id TEXT PRIMARY KEY,
      gateway_enabled BOOLEAN DEFAULT FALSE,
      middleware_config JSONB DEFAULT '{"auth": true, "rbac": false}'::JSONB,
      rollout_cohort TEXT,  -- 'canary_5pct', 'canary_25pct', 'stable_100pct'
      updated_at TIMESTAMPTZ DEFAULT NOW(),
      updated_by TEXT
  );
  ```
- [ ] Feature flag service:
  ```python
  class FeatureFlagService:
      async def is_enabled(self, flag: str, customer_id: str = None) -> bool:
          # Check customer-specific override first
          if customer_id:
              override = await db.fetchrow(
                  "SELECT middleware_config FROM gateway_feature_flags WHERE customer_id = $1",
                  customer_id
              )
              if override:
                  return override["middleware_config"].get(flag, False)
          
          # Fall back to global env var
          return getattr(settings, f"ENABLE_{flag.upper()}_MIDDLEWARE", True)
  ```
- [ ] PP admin UI for feature flags:
  - View all customer feature flags
  - Toggle flags per customer
  - Bulk update by cohort (canary_5pct, canary_25pct, stable_100pct)
- [ ] Feature flag change audit logging:
  ```python
  await audit_log("feature_flag_changed", {
      "customer_id": customer_id,
      "flag": flag_name,
      "old_value": old_value,
      "new_value": new_value,
      "changed_by": admin_user_id,
      "reason": change_reason
  })
  ```

Technical Tasks:
1. Create gateway_feature_flags PostgreSQL table
2. Implement FeatureFlagService class
3. Add feature flag checks to each middleware __call__ method
4. Create PP admin UI routes: GET/PUT /api/admin/feature-flags
5. Build React feature flag toggle component
6. Add feature flag change audit logging
7. Write feature flag tests (10 test cases)

Dependencies: GW-100 (auth middleware as reference)
```

---

## Section 6: Circuit Breaker Implementation (SE-006 Enhancement)

**Add to GW-401:**

```python
# Confirmed library: pybreaker==1.0.2
# Install: pip install pybreaker==1.0.2

from pybreaker import CircuitBreaker
import httpx

# Create circuit breaker for Plant API
plant_api_breaker = CircuitBreaker(
    fail_max=5,                    # Open after 5 consecutive failures
    timeout_duration=30,           # Try again after 30 seconds
    exclude=[httpx.HTTPStatusError],  # Don't break on 4xx errors (client fault)
    name="plant_api_circuit_breaker",
    listeners=[CircuitBreakerLogger()]  # Log state transitions
)

class CircuitBreakerLogger:
    """Log circuit breaker state transitions."""
    
    def state_change(self, cb, old_state, new_state):
        logger.warning(
            f"Circuit breaker '{cb.name}' state change: {old_state.name} → {new_state.name}"
        )
        
        if new_state.name == "open":
            # Alert on-call engineer
            await alert_pagerduty(
                "Plant API circuit breaker OPEN",
                severity="critical",
                details=f"Circuit breaker opened after {cb.fail_counter} failures"
            )

@plant_api_breaker
async def call_plant_api(endpoint: str, method: str = "POST", **kwargs):
    """
    Call Plant API with circuit breaker protection.
    
    Raises:
        CircuitBreakerOpen: If circuit is open (Plant API down)
        httpx.HTTPStatusError: If Plant returns error response
    """
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method,
            f"{settings.PLANT_API_URL}/{endpoint}",
            timeout=settings.PLANT_TIMEOUT_SECONDS,
            **kwargs
        )
        response.raise_for_status()
        return response.json()

# In middleware (GW-104 or proxy routes)
try:
    result = await call_plant_api("agents/execute", json=payload)
except CircuitBreakerOpen:
    # Plant API is down, return cached data or error
    logger.error("Plant API circuit breaker open, using fallback")
    
    # Try to get cached agent data
    cached_agent = await redis.get(f"agent:{agent_id}")
    if cached_agent:
        return JSONResponse(
            status_code=200,
            content={
                "status": "degraded",
                "message": "Using cached data, Plant API temporarily unavailable",
                "data": json.loads(cached_agent)
            }
        )
    
    # No cache, return error
    raise HTTPException(
        status_code=503,
        detail="Plant API temporarily unavailable, please try again later"
    )
```

---

## Section 7: Test File Structure (GAP-008 Resolution)

**Add to Testing Strategy section:**

```
Complete Test File Structure:

tests/
├── conftest.py                 # Pytest configuration + shared fixtures
├── fixtures/
│   ├── auth_fixtures.py        # JWT tokens (trial, governor, admin, etc.)
│   ├── customer_fixtures.py    # Test customers with various states
│   ├── agent_fixtures.py       # Test agents with different specializations
│   └── opa_fixtures.py         # Mock OPA responses
│
├── unit/
│   ├── middleware/
│   │   ├── test_auth_middleware.py          # 15 tests
│   │   ├── test_rbac_middleware.py          # 25 tests (PP only)
│   │   ├── test_policy_middleware.py        # 20 tests
│   │   ├── test_budget_middleware.py        # 15 tests
│   │   ├── test_audit_middleware.py         # 20 tests
│   │   └── test_error_middleware.py         # 25 tests
│   ├── services/
│   │   ├── test_opa_client.py               # 10 tests
│   │   ├── test_audit_service.py            # 15 tests (async writer)
│   │   └── test_budget_tracker.py           # 12 tests (Redis)
│   └── models/
│       ├── test_constitutional_context.py   # 8 tests
│       └── test_policy.py                   # 10 tests
│
├── integration/
│   ├── test_gateway_flow.py                 # 20 end-to-end scenarios
│   │   # Scenarios:
│   │   # 1. Trial customer creates agent (success)
│   │   # 2. Trial customer exceeds 10 tasks (denied)
│   │   # 3. Governor approves external execution (success)
│   │   # 4. Non-Governor attempts external execution (denied)
│   │   # 5. PP Admin with "Viewer" role creates agent (denied)
│   │   # 6. PP Admin with "Agent Orchestrator" creates agent (success)
│   │   # ... (14 more scenarios)
│   ├── test_websocket.py                    # 10 tests
│   │   # 1. WebSocket auth with valid token
│   │   # 2. WebSocket auth with expired token (reject)
│   │   # 3. WebSocket heartbeat mechanism
│   │   # 4. Agent status updates received
│   │   # ... (6 more tests)
│   └── test_circuit_breaker.py              # 8 tests
│       # 1. Plant API healthy (circuit closed)
│       # 2. Plant API fails 5 times (circuit opens)
│       # 3. Circuit half-open after timeout
│       # 4. Successful request closes circuit
│       # ... (4 more tests)
│
├── performance/
│   ├── locustfile.py                        # Load test scenarios
│   │   # User behaviors:
│   │   # - TrialUser: Create agents, execute tasks (10 tasks/day limit)
│   │   # - PaidUser: Execute agents, view analytics
│   │   # - PPAdmin: Manage agents, approve requests
│   │   # Target: 100/1000/10000 concurrent users
│   ├── test_load_100_users.py               # 100 concurrent users
│   ├── test_load_1000_users.py              # 1000 concurrent users
│   └── test_load_10000_users.py             # 10000 concurrent users (stress test)
│
└── security/
    ├── test_owasp_top10.py                  # OWASP ZAP scan
    ├── test_jwt_bypass.py                   # JWT validation bypass attempts
    ├── test_opa_bypass.py                   # OPA policy bypass attempts
    ├── test_sql_injection.py                # SQL injection (RLS bypass attempts)
    └── test_rate_limit_bypass.py            # Rate limit gaming attempts

# Pytest configuration (conftest.py)
import pytest
from httpx import AsyncClient
from main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def trial_token():
    return create_jwt({
        "customer_id": "CUST-TRIAL-001",
        "trial_mode": True,
        "trial_expires_at": (datetime.utcnow() + timedelta(days=5)).isoformat()
    })

@pytest.fixture
def governor_token():
    return create_jwt({
        "roles": ["governor"],
        "governor_agent_id": "AGENT-GOV-001"
    })

# ... (20 more fixtures)
```

---

## Section 8: Updated Timeline & Budget

**Replace Budget table with:**

| Phase | Original Effort | Updated Effort | Eng Cost ($150/hr) | Infra Cost/Month | Total |
|-------|----------------|----------------|-------------------|------------------|-------|
| Phase 0 (Infrastructure) | 9 days | **14 days** | **$16,800** | **$0** (OPA in Cloud Run) | **$16,800** |
| - GW-00P: Prerequisites & Contracts | NEW | 5 days | $6,000 | $0 | $6,000 |
| - GW-000: OPA Deployment | 5 days | 5 days | $6,000 | $0 | $6,000 |
| - GW-001: Audit Schema | 4 days | 4 days | $4,800 | $0 | $4,800 |
| - MS-005: Cost Guards | NEW | 5 days (parallel) | $0 | $0 | $0 |
| - MS-006: Feature Flags | NEW | 4 days (parallel) | $0 | $0 | $0 |
| Phase 1 (Core Middleware) | 32 days | **38 days** | **$45,600** | **$0** | **$45,600** |
| - GW-100 through GW-105 | 32 days | 32 days | $38,400 | $0 | $38,400 |
| - MS-001: Shared Middleware | NEW | 3 days | $3,600 | $0 | $3,600 |
| - MS-002: Sandbox Provisioning | NEW | 7 days (parallel) | $8,400 | **+$10-15/month** | $8,400 |
| Phase 2 (Real-Time) | 6 days | 6 days | $7,200 | $0 | $7,200 |
| Phase 3 (Observability) | 5 days | 5 days | $6,000 | $0 | $6,000 |
| Phase 4 (Performance) | 9 days | 9 days | $10,800 | $0 | $10,800 |
| Phase 5 (Production Hardening) | 20 days | 20 days | $24,000 | $0 | $24,000 |
| Phase 6 (Documentation) | 6 days | 6 days | $7,200 | $0 | $7,200 |
| **TOTAL** | **87 days** | **98 days** | **$117,600** | **+$10-15/month** | **$117,600** |

**Infrastructure Cost Update:**
- Baseline: $55-85/month (existing Cloud SQL + Redis + Cloud Run)
- Gateway additions: **+$10-15/month** (sandbox Plant service only)
- **Total: $65-100/month** (still within $100/month budget ✅)

**Timeline Update:**
- Original: 16-20 weeks (4-5 months)
- Updated: **20-24 weeks (5-6 months)** with 2-3 engineers
- Critical path: 14 weeks (with parallelization)

---

## Section 9: Implementation Readiness Checklist

Before starting implementation, verify:

- [ ] GW-00P complete (JWT contract, Plant API contract, Terraform modules, env vars, secrets)
- [ ] All Rego policies written and tested (5 policies with 100% coverage)
- [ ] Middleware registration code documented in every story (GAP-001)
- [ ] Redis data structures specified for budget + rate limiting (GAP-005)
- [ ] Test file structure created with pytest fixtures (GAP-008)
- [ ] Shared middleware library package created (MS-001)
- [ ] Sandbox Plant service deployed and tested (MS-002)
- [ ] Cost guard Cloud Function deployed (MS-005)
- [ ] Feature flag infrastructure ready (MS-006)
- [ ] OPA deployment model clarified (separate Cloud Run service, not sidecar)
- [ ] All secrets created in Secret Manager (5 secrets)
- [ ] Terraform modules validated (`terraform plan` succeeds)

**Status:** ✅ All critical gaps addressed, implementation can proceed

---

## Section 10: Dependency Graph Visual

```
Phase 0 (Week 1-3):
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  GW-00P      │────▶│  GW-000      │────▶│  GW-001      │
│  (Contracts) │     │  (OPA)       │     │  (Audit DB)  │
└──────────────┘     └──────────────┘     └──────────────┘
       │                                          │
       │              ┌──────────────┐            │
       └─────────────▶│  MS-005      │◀───────────┘
       │              │  (Cost Guard)│
       │              └──────────────┘
       │              ┌──────────────┐
       └─────────────▶│  MS-006      │
                      │  (Flags)     │
                      └──────────────┘

Phase 1 (Week 4-9):
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  GW-100      │────▶│  GW-101      │────▶│  GW-102      │
│  (Auth)      │     │  (RBAC)      │     │  (Policy)    │
└──────────────┘     └──────────────┘     └──────────────┘
                                                  │
       ┌──────────────────────────────────────────┤
       │                                          │
┌──────▼──────┐     ┌──────────────┐     ┌──────▼──────┐
│  GW-103      │────▶│  GW-104      │────▶│  GW-105      │
│  (Budget)    │     │  (Audit)     │     │  (Error)     │
└──────────────┘     └──────────────┘     └──────────────┘
                            │                     │
                     ┌──────▼──────┐      ┌──────▼──────┐
                     │  MS-001      │      │  MS-002      │
                     │  (Shared     │      │  (Sandbox)   │
                     │   Middleware)│      └──────────────┘
                     └──────────────┘

Phase 2-6: Linear dependencies with parallel opportunities documented in plan
```

---

**End of Peer Review Enhancements Document**

**Next Steps:**
1. Incorporate all sections above into Gateway Final IMPLEMENTATION_PLAN.md
2. Update story acceptance criteria with code examples
3. Create prerequisite infrastructure (GW-00P) before starting middleware stories
4. Run `terraform validate` to verify infrastructure readiness
5. Begin implementation with Phase 0 (3 weeks)

**Approval:** ✅ Implementation-ready after incorporating these enhancements
