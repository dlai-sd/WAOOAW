# NFR Reusable Interfaces — Gap Analysis & Action Plan

**Date:** 2026-02-27  
**Purpose:** Ensure NFRs from Iterations 1–7 are part of platform DNA — not just implemented once but used consistently by every existing and new flow.

---

## 1. Gap Analysis

The table below shows the current state of each NFR: whether the interface exists, whether it is universally applied, and the precise gap.

| # | NFR | Iteration | Interface Exists? | Universally Used? | Gap |
|---|-----|-----------|:-----------------:|:-----------------:|-----|
| 1 | JWT Refresh + Silent Refresh | It-1 | ✅ | ✅ | None — auth endpoints, cookie, revocation all wired correctly |
| 2 | Token Revocation on Logout | It-1 | ✅ | ✅ | None — Redis revocation checked on every authenticated request |
| 3 | Audit Logging | It-2 | ✅ exists in `services/audit_client.py` | ❌ | `fire_and_forget_audit()` is never called from any API route — registration, login, OTP, hire, payment flows emit zero audit events |
| 4 | Circuit Breaker (CP→Plant) | It-3 | ✅ exists in `services/plant_client.py` | ❌ partial | Only `cp_registration.py` uses `PlantClient`. `PlantGatewayClient` (used by trading, marketing review, hired agents, subscriptions) has no circuit breaker at all |
| 5 | Idempotency on Writes | It-3 | ✅ `IdempotencyMiddleware` in `main.py` | ✅ | Middleware wired at app level; `IdempotencyService` used in scheduler and payments |
| 6 | CORS Strict Allowlist | It-3 | ✅ | ✅ | None — env-driven allowlist in both backends |
| 7 | Distributed Tracing (OTel) | It-5 | ✅ `core/observability.py` in CP + Plant | ✅ | FastAPI, httpx, SQLAlchemy auto-instrumented |
| 8 | Correlation ID Propagation | It-5 | ✅ | ✅ | Set by middleware, propagated in httpx headers |
| 9 | PII Masking in Logs | It-6 | ❌ | ❌ | No `PIIMaskingFilter` or equivalent applied to either `core/logging.py` formatter — raw emails, phone numbers, and names CAN appear in structured logs |
| 10 | GDPR Erasure API | It-6 | ✅ | ✅ | Erasure endpoint exists, anonymises PII across tables |
| 11 | Read Replica for Reads | It-7 | ✅ `get_read_db_session()` in `core/database.py` | ❌ partial | Correctly used in `audit.py`, `feature_flags.py`, `customers.py` (lookup). NOT used in `agents.py`, `agent_types_db.py`, `agent_types_simple.py`, `hired_agents_simple.py` — all catalog reads hit primary DB |
| 12 | Feature Flags | It-7 | ✅ `FeatureFlagService` + admin API | ❌ | Flags can be managed via API but no CP route actually checks a flag to gate or change behaviour — flags exist but are never read at runtime |
| 13 | PII Field-Level Encryption | It-7 | ✅ partial — `core/encryption.py`, `email_search_hash` used in customer lookup | ❌ | `email`, `phone`, `full_name` columns have migration `020_pii_encryption.py` but customer service writes raw plaintext — encrypt-on-write / decrypt-on-read not implemented |

---

## 2. Required Changes

The table below is the actionable backlog — one row per gap, in plain English.

| # | What to change | Where to change it | Why (which NFR) | Effort |
|---|---------------|--------------------|-----------------|--------|
| C1 | Add a reusable `audit_event(screen, action, outcome)` FastAPI dependency that any route can include in one line, calling `fire_and_forget_audit()` in background | New file: `src/CP/BackEnd/services/audit_dependency.py` | Audit (It-2) — routes can't easily call the existing client today | Small |
| C2 | Wire audit events into the 5 key CP flows: registration success/failure, OTP sent/verified, Google login, hire wizard started/completed, payment initiated | `cp_registration.py`, `cp_otp.py`, `auth/routes.py`, `hire_wizard.py`, `payments_razorpay.py` | Audit (It-2) — these are the flows that matter most for compliance | Medium |
| C3 | Add circuit breaker wrapping to `PlantGatewayClient` — same open/half-open/closed pattern already in `PlantClient` | `src/CP/BackEnd/services/plant_gateway_client.py` | Circuit Breaker (It-3) — trading, marketing review, hired agents have no protection today |  Small |
| C4 | Add a `PIIMaskingFilter` log filter to the structured log setup in CP Backend `core/logging.py` — masks email, phone, full_name, IP in any log record before it is emitted | `src/CP/BackEnd/core/logging.py` | PII Masking (It-6) — raw PII reaching Cloud Logging violates the compliance design | Small |
| C5 | Add the same `PIIMaskingFilter` to Plant Backend `core/logging.py` | `src/Plant/BackEnd/core/logging.py` | PII Masking (It-6) — same risk in Plant Backend where most PII originates | Small |
| C6 | Switch all catalog read endpoints in Plant Backend to use `get_read_db_session()` instead of `get_db_session()` | `src/Plant/BackEnd/api/v1/agents.py` (all GET routes), `agent_types_db.py`, `agent_types_simple.py`, `hired_agents_simple.py` (all GET routes) | Read Replica (It-7) — catalog is THE most read-heavy path; should never touch primary | Small |
| C7 | Create a `get_feature_flag(flag_name)` FastAPI dependency factory so any route can check a flag with `Depends(get_feature_flag("new_hire_wizard"))` and return a 404 or fallback if flag is off | New file: `src/Plant/BackEnd/api/v1/feature_flag_dependency.py`, mirrored in `src/CP/BackEnd/api/feature_flag_dependency.py` | Feature Flags (It-7) — flags are managed but never evaluated | Small |
| ~~C8~~ | ~~Implement encrypt-on-write / decrypt-on-read for `email`, `phone`, `full_name`~~ **PERMANENTLY PARKED** — CMEK at-rest encryption + `PIIMaskingFilter` in logs + `email_search_hash` for lookups + GDPR erasure tooling together cover ≥95 % of the compliance benefit. Application-layer field encryption breaks all DB queries, admin tooling, log correlation, and key rotation with no marginal security gain over the existing controls. Revisit only if a specific regulatory audit explicitly requires it. | — | — | — |

---

## 3. Reusable Interface Definitions

The sections below define the exact interfaces that should be built so every existing and new flow can adopt them in one line.

---

### I-1: Audit Dependency (`audit_dependency.py`)

**Problem:** Today, to fire an audit event a route must import `AuditClient`, build the client, call `.log()`, and wrap in `fire_and_forget_audit()`. Four steps. Nobody does it.

**Solution:** A FastAPI dependency that a route adds to its signature and then calls in one line.

```python
# src/CP/BackEnd/services/audit_dependency.py

def get_audit_logger(request: Request) -> AuditLogger:
    """FastAPI dependency — inject into any route that needs to emit audit events."""
    ...

class AuditLogger:
    async def log(
        self,
        screen: str,          # e.g. "cp_registration", "cp_login"
        action: str,          # e.g. "otp_sent", "registration_complete"
        outcome: Literal["success", "failure"],
        user_id: str | None = None,
        email: str | None = None,
        detail: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Fire-and-forget — never blocks the response."""
        ...
```

**Usage in a route (one extra line):**
```python
@router.post("/register")
async def register(
    body: RegistrationRequest,
    audit: AuditLogger = Depends(get_audit_logger),  # ← add this
):
    result = await do_registration(body)
    await audit.log("cp_registration", "registration_complete", "success", email=body.email)
    return result
```

---

### I-2: Circuit Breaker on PlantGatewayClient

**Problem:** `PlantGatewayClient` makes raw `httpx` calls — no circuit breaker, no fast-fail.

**Solution:** Wrap `PlantGatewayClient._request()` with the same circuit breaker already in `PlantClient`. Centralise the state so all routes share one breaker instance.

```python
# src/CP/BackEnd/services/plant_gateway_client.py

class PlantGatewayClient:
    _circuit_breaker: CircuitBreaker = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=30,
    )

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        if self._circuit_breaker.is_open():
            raise ServiceUnavailableError("Plant Gateway circuit open")
        try:
            response = await self._client.request(method, path, **kwargs)
            self._circuit_breaker.record_success()
            return response
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            self._circuit_breaker.record_failure()
            raise ServiceUnavailableError(str(exc)) from exc
```

---

### I-3: PII Masking Log Filter

**Problem:** `core/logging.py` in both backends formats structured JSON logs but never masks PII fields.

**Solution:** A single `PIIMaskingFilter` class added to the root logger once at startup.

```python
# src/CP/BackEnd/core/logging.py  (and mirrored in Plant BackEnd)

import re, logging

class PIIMaskingFilter(logging.Filter):
    """Masks PII in any log record before emission. Zero-overhead when no PII present."""

    _EMAIL_RE  = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
    _PHONE_RE  = re.compile(r'(\+?\d{1,3})[\s\-]?\d{3,5}[\s\-]?\d{4,6}')
    _IP_LAST   = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3})\.\d{1,3}')

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._mask(str(record.msg))
        record.args = tuple(self._mask(str(a)) for a in (record.args or ()))
        return True

    def _mask(self, text: str) -> str:
        text = self._EMAIL_RE.sub(lambda m: self._mask_email(m.group()), text)
        text = self._PHONE_RE.sub(lambda m: m.group(1) + '******' + m.group()[-4:], text)
        text = self._IP_LAST.sub(r'\1.XXX', text)
        return text

    @staticmethod
    def _mask_email(email: str) -> str:
        user, domain = email.split('@', 1)
        return f"{user[0]}***@{domain}"

# Wire up at app init (one line):
logging.getLogger().addFilter(PIIMaskingFilter())
```

---

### I-4: Feature Flag FastAPI Dependency

**Problem:** `FeatureFlagService` exists and the admin API manages flags, but no business route reads flags to gate behaviour.

**Solution:** A dependency factory that any route can use to check a flag. Returns `True/False`; routes decide what to do (404, fallback, etc.).

```python
# src/Plant/BackEnd/api/v1/feature_flag_dependency.py

def require_flag(flag_name: str, *, default: bool = False):
    """
    FastAPI dependency factory. Returns a dependency that resolves to bool.

    Usage:
        @router.post("/new-hire-wizard")
        async def hire(
            _: bool = Depends(require_flag("new_hire_wizard")),
        ):
            ...  # only reached if flag is on

    If flag is off, raises HTTP 404 automatically.
    """
    async def _check(
        db: AsyncSession = Depends(get_read_db_session),
    ) -> bool:
        svc = FeatureFlagService(db)
        enabled = await svc.is_enabled(flag_name, default=default)
        if not enabled:
            raise HTTPException(status_code=404, detail=f"Feature '{flag_name}' not available")
        return True
    return _check
```

---

### I-5: Catalog Endpoints → Read Replica (Convention)

**Problem:** `agents.py`, `agent_types_db.py`, `hired_agents_simple.py` GET endpoints use `get_db_session()`.

**Solution:** Convention + one-line change per endpoint. No new interface needed — `get_read_db_session()` already exists.

**Rule (add to coding standards):**
> Any endpoint that only reads data (GET, or POST that is search/query) MUST use `get_read_db_session()`.  
> Only endpoints that write (INSERT / UPDATE / DELETE) use `get_db_session()`.

```python
# Before (wrong — hits primary for a read-only catalog list):
@router.get("/agents")
async def list_agents(db: AsyncSession = Depends(get_db_session)):
    ...

# After (correct — routes to replica):
@router.get("/agents")
async def list_agents(db: AsyncSession = Depends(get_read_db_session)):
    ...
```

---

## 4. Priority Order

| Priority | Change | Reason |
|----------|--------|--------|
| P0 | C4 + C5 — PII masking in logs | Compliance violation — raw PII in Cloud Logging today |
| P1 | C3 — Circuit breaker on PlantGatewayClient | Production stability — trading/marketing/hire flows have no protection |
| P1 | C6 — Catalog reads to read replica | Performance — catalog is the hottest read path |
| P2 | C1 + C2 — Audit dependency + wire into 5 flows | Compliance — audit trail required before real customer data |
| ~~P2~~ | ~~C8 — PII encrypt-on-write~~ **PARKED** | CMEK + PII masking + email_hash + GDPR erasure cover the requirement; app-layer encryption breaks queries/tooling |
| P3 | C7 — Feature flag dependency | Operational — enables safe rollouts; no live risk today |

---

## 6. Image Promotion & Configuration — Mandatory Rules

> **These rules apply to every story, every PR, every service (CP, Plant, PP, Gateway).  
> Violating any of these is a production incident waiting to happen.**

### 6.1 — The Image Promotion Model

WAAOOW follows a **build-once, promote-through-environments** deployment model:

```
One Docker image built in CI
       ↓
   demo env  ← runtime env vars injected by Cloud Run revision
       ↓ (same image, different vars)
   uat env
       ↓ (same image, different vars)
   prod env
```

The **image never changes** between environments. Only the runtime configuration (env vars and secrets) changes. This means:

| ✅ DO | ❌ NEVER DO |
|------|------------|
| Read config from `os.environ` / Pydantic `BaseSettings` at startup | Hardcode `if env == "prod":` branches in code |
| Store secrets in GCP Secret Manager — read at container start | Write secret values into `Dockerfile`, `docker-compose`, or any file committed to git |
| Read `DATABASE_URL`, `REDIS_URL`, `SMTP_HOST` from env vars | Set `DATABASE_URL = "postgresql://...demo-host..."` in source code |
| Use env-specific tfvars files (`demo.tfvars`, `uat.tfvars`, `prod.tfvars`) | Add environment-specific logic to Terraform modules themselves |
| Pass new secrets via Cloud Run `--set-secrets` in Terraform `cloud_run_service` resource | Embed secrets in container image layers |

### 6.2 — Where Configuration Lives

| Config type | Where it lives | How the app reads it |
|---|---|---|
| Non-secret env var (e.g. `LOG_LEVEL`, `CORS_ORIGIN`, `SMTP_PORT`) | Cloud Run env var → Terraform `env_vars` block | `os.environ` / Pydantic `BaseSettings` |
| Secret (e.g. `DATABASE_URL`, `JWT_SECRET`, `SMTP_PASSWORD`) | GCP Secret Manager → Cloud Run secret mount | `os.environ` (Cloud Run injects secret as env var at start) |
| Feature flags | Database table `feature_flags` — managed via PP admin API | `FeatureFlagService.is_enabled()` |
| Local dev only | `.env` file (gitignored) | `python-dotenv` / `BaseSettings` with `env_file` |

### 6.3 — Terraform Alignment Rule (Critical)

Every time a story introduces a new environment variable or GCP secret, the agent **must** update Terraform in the same PR. Failing to do so leaves the platform in a broken state after the next `terraform apply`.

**Files to check and update:**

```
cloud/terraform/stacks/plant/
├── variables.tf            ← declare the new variable here
├── main.tf                 ← wire it into the cloud_run_service resource
└── environments/
    ├── demo.tfvars         ← set the value for demo
    ├── uat.tfvars          ← set the value for uat
    └── prod.tfvars         ← set the value for prod

cloud/terraform/stacks/cp/   ← same structure for CP-side vars
```

**Pattern for a new non-secret env var:**
```hcl
# variables.tf — declare
variable "smtp_host" {
  type        = string
  description = "SMTP relay hostname for outbound email"
}

# main.tf — wire into Cloud Run service
resource "google_cloud_run_v2_service" "plant" {
  ...
  template {
    containers {
      env {
        name  = "SMTP_HOST"
        value = var.smtp_host
      }
    }
  }
}

# demo.tfvars
smtp_host = "smtp.gmail.com"
```

**Pattern for a new secret:**
```hcl
# main.tf — mount from Secret Manager (never inline the value)
env {
  name = "NEW_API_KEY"
  value_source {
    secret_key_ref {
      secret  = "new-api-key"          # Secret Manager secret name
      version = "latest"
    }
  }
}
```
Then create the secret in GCP Secret Manager manually (or via `gcloud`) — never commit the value.

### 6.4 — Checklist: When Your Story Adds Any Config

```
[ ] New env var declared in cloud/terraform/stacks/<service>/variables.tf
[ ] New env var wired in main.tf cloud_run_service env block
[ ] Value set in demo.tfvars, uat.tfvars, prod.tfvars
[ ] Secret values stored in GCP Secret Manager — NOT in tfvars
[ ] .env.example updated with the new var (blank value, documented)
[ ] Pydantic BaseSettings field added in src/<service>/core/config.py
[ ] No hardcoded env-specific values anywhere in Python or TypeScript
```

---

## 5. Preventive Gate Stories

> **What this section is:** The changes above (C1–C8) were *corrective* — they fixed gaps in existing routes.
> This section is *preventive* — changes that make every **future** route automatically compliant
> without the developer needing to remember anything.

### Summary Tracking Table

| ID | Story | Priority | Files | New LOC | Changed LOC | Est. Time | Status |
|----|-------|:--------:|:-----:|:-------:|:-----------:|:---------:|:------:|
| P-1 | Gateway circuit breaker on all middleware | P0 | 8 | ~60 | ~20 | 3–4 hrs | ✅ Done |
| P-2 | Global `dependencies=[]` on all 4 FastAPI apps | P1 | 4 | ~20 | ~8 | 30 mins | ✅ Done |
| P-3 | `WAOOAWRouter` factory + ruff ban on bare `APIRouter` | P1 | 59 | ~45 | ~58 | 4–5 hrs | ✅ Done |
| P-4 | Genesis + audit GET routes → read replica | P1 | 2 | 0 | ~8 | 20 mins | ✅ Done |
| P-5 | PP Backend NFR baseline *(separate iteration)* | P2 | 13 | ~200 | ~30 | 3 days | ✅ Done (PR #813) |

---

### P-1 — Gateway Circuit Breaker on All Middleware

**Problem:**
`Plant/Gateway` and `gateway` middleware (`auth.py`, `rbac.py`, `policy.py`, `budget.py`) make raw
`httpx` calls with no circuit breaker. If any upstream service hangs, every single request
platform-wide hangs with it until the 30-second timeout fires. This is the highest production risk
in the entire codebase.

**Scope:**
- `src/Plant/Gateway/middleware/auth.py` — 3 httpx call sites
- `src/Plant/Gateway/middleware/rbac.py` — 2 httpx call sites
- `src/Plant/Gateway/middleware/policy.py` — 3 httpx call sites
- `src/Plant/Gateway/middleware/budget.py` — 2 httpx call sites
- Mirror the same change in `src/gateway/middleware/` (4 identical files)

**What to build:**
A shared `CircuitBreaker` instance scoped per-middleware module (not per-request), wrapping every
`httpx` call with: open check → call → record success/failure → raise `ServiceUnavailableError`
on open or connect error. Reuse the `CircuitBreaker` class already in `services/plant_client.py`.

```python
# Pattern to apply at each httpx call site in all 8 middleware files
_cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30)

async def _call_upstream(url: str, headers: dict) -> httpx.Response:
    if not _cb.is_call_permitted():
        raise ServiceUnavailableError("circuit open")
    try:
        resp = await _client.get(url, headers=headers, timeout=10)
        _cb.record_success()
        return resp
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        _cb.record_failure()
        raise ServiceUnavailableError(str(exc)) from exc
```

**Acceptance criteria:**
- [ ] All 8 middleware files (4 × 2 gateways) wrap httpx calls with circuit breaker
- [ ] `ServiceUnavailableError` returns HTTP 503 to the caller — no hanging requests
- [ ] Existing middleware tests still pass
- [ ] New tests: circuit open returns 503; successful call resets failure counter

---

### P-2 — Global `dependencies=[]` on All 4 FastAPI Apps

**Problem:**
All four `FastAPI(...)` app instantiations have no `dependencies=[]`. There is no
"runs on every request, always" hook. Correlation ID, request logging, and every future
cross-cutting concern depends entirely on per-route developer discipline — which fails silently
when forgotten.

**Scope:**
- `src/CP/BackEnd/main.py`
- `src/Plant/BackEnd/main.py`
- `src/Plant/Gateway/main.py`
- `src/PP/BackEnd/main_proxy.py`

**What to build:**
A `require_correlation_id` dependency that reads `X-Correlation-ID` from the incoming request
header (or generates one if absent) and stores it in a `contextvars.ContextVar` so all downstream
log records and outbound calls carry the same ID automatically.

```python
# src/<service>/core/dependencies.py  (one file per service)
import uuid
from contextvars import ContextVar
from fastapi import Request

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")

def require_correlation_id(request: Request) -> str:
    cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    _correlation_id.set(cid)
    return cid

# main.py — one-line change per app
app = FastAPI(
    ...
    dependencies=[Depends(require_correlation_id)],  # <- add this line
)
```

**Acceptance criteria:**
- [ ] All 4 apps have `dependencies=[Depends(require_correlation_id)]`
- [ ] Correlation ID available in `contextvars` for log formatters and outbound headers
- [ ] Requests without `X-Correlation-ID` header get one auto-generated (UUID4)
- [ ] Existing tests unaffected — dependency is transparent to route logic

---

### P-3 — `WAOOAWRouter` Factory + Ban on Bare `APIRouter`

**Problem:**
58 bare `APIRouter()` instances exist across CP, Plant, and PP. Any new route added to any of
them gets zero NFR gates automatically. There is nothing to stop a developer adding a route that
bypasses audit, correlation ID, or read replica rules — and no CI check catches it today.

**Scope:**
- New file: `src/CP/BackEnd/core/routing.py`
- New file: `src/Plant/BackEnd/core/routing.py`
- 58 router files updated to use the factory instead of bare `APIRouter`
- `pyproject.toml` — add `ruff` noqa-ban on `from fastapi import APIRouter` in `api/` directories

**What to build:**

```python
# src/CP/BackEnd/core/routing.py
from fastapi import APIRouter, Depends
from core.dependencies import require_correlation_id

def waooaw_router(prefix: str, tags: list[str], **kwargs) -> APIRouter:
    """
    Standard WAOOAW router. Every route registered here automatically gets:
    correlation ID propagation. Future platform-wide gates added here apply
    to every route in every service with no per-file changes needed.

    DO NOT use bare APIRouter() in api/ directories.
    Enforced by ruff lint rule in pyproject.toml.
    """
    return APIRouter(
        prefix=prefix,
        tags=tags,
        dependencies=[Depends(require_correlation_id)],
        **kwargs,
    )
```

**Per-file migration (mechanical, no logic change):**
```python
# Before
from fastapi import APIRouter
router = APIRouter(prefix="/payments", tags=["payments"])

# After
from core.routing import waooaw_router
router = waooaw_router(prefix="/payments", tags=["payments"])
```

**Ruff ban rule — prevents regression on every future PR:**
```toml
# pyproject.toml  (per-service)
[tool.ruff.lint]
# Bare APIRouter() forbidden in business API directories; use waooaw_router()
banned-module-level-imports = ["fastapi.APIRouter"]
```

**Acceptance criteria:**
- [ ] `core/routing.py` exists in CP Backend and Plant Backend
- [ ] All 58 router files use `waooaw_router()` instead of bare `APIRouter()`
- [ ] Bare `from fastapi import APIRouter` in `api/` dirs fails CI ruff check
- [ ] All existing route behaviours unchanged; existing tests pass

---

### P-4 — Genesis + Audit GET Routes → Read Replica

**Problem:**
4 routes in `genesis.py` (`list_skills`, `get_skill`, `list_job_roles`, `get_job_role`) and
2 routes in `audit.py` (`detect_tampering`, `export_compliance_report`) use `get_db_session()`
(primary write database) despite being read-only. The genesis catalog is the highest-read path
in Plant — every hire wizard page load fetches skills and job roles from it.

**Scope:**
- `src/Plant/BackEnd/api/v1/genesis.py` — 4 GET functions (lines 130, 149, 282, 300)
- `src/Plant/BackEnd/api/v1/audit.py` — 2 GET functions (lines 231, 252)

**What to change (6 one-line replacements, nothing else):**
```python
# Before (in all 6 function signatures)
db: AsyncSession = Depends(get_db_session)

# After
db: AsyncSession = Depends(get_read_db_session)
```

**Acceptance criteria:**
- [ ] All 6 GET functions use `get_read_db_session`
- [ ] POST/PUT/DELETE routes in same files unchanged — still use write session
- [ ] Existing tests pass without modification

---

### P-5 — PP Backend NFR Baseline *(Separate Iteration)*

**Problem:**
The PP (Partner Portal) backend pre-dates the NFR work and has none of the standards:
no circuit breaker, no OTel tracing, no read replica convention, no audit wiring.
12 API files, 1 main entry point.

**Why separate:**
PP's internal call patterns and upstream dependencies have not been audited. This is a
standalone 3-day effort to be scheduled after P-1 through P-4 are merged and stable.

**Sub-stories (detail in `docs/PP/iterations/NFRBaseline.md` when iteration starts):**

| # | Story | What |
|---|-------|------|
| PP-N1 | Circuit breaker | Add `CircuitBreaker` to `PP/BackEnd/clients/plant_client.py` |
| PP-N2 | OTel tracing | Wire `FastAPIInstrumentor` in `main_proxy.py` |
| PP-N3 | Read replica | Establish read vs. write DB session across 12 API files |
| PP-N4 | Audit wiring | Wire `get_audit_logger` into approval, agent, and genesis flows |
| PP-N5 | Global dep | Add `dependencies=[Depends(require_correlation_id)]` to PP `FastAPI()` |

**Acceptance criteria:** Defined in the PP-NFR iteration doc — not written yet, requires PP
codebase read-through first.
