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
| C8 | Implement encrypt-on-write / decrypt-on-read for `email`, `phone`, `full_name` in `CustomerService.create()` and `CustomerService.get()` using the existing `core/encryption.py` primitives | `src/Plant/BackEnd/services/customer_service.py` | PII Field Encryption (It-7) — migration ran but customer data is still stored in plaintext | Medium |

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
| P2 | C8 — PII encrypt-on-write | Compliance — migration ran but data still plaintext |
| P3 | C7 — Feature flag dependency | Operational — enables safe rollouts; no live risk today |
