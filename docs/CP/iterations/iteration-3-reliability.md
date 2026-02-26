# Iteration 3 — Reliability

**When:** Before staging goes live  
**Branch naming:** `feat/reliability-it3`  
**Testing:** `docker compose -f docker-compose.local.yml` — no virtual env, no local Python  
**Status:** 🟢 Done — PR #770

---

## Tracking Table

| # | Epic | Story | Status | PR |
|---|------|-------|--------|----|
| E1-S1 | Circuit Breaker | Circuit breaker on CP→Plant HTTP calls | 🟢 Done | #770 |
| E1-S2 | Circuit Breaker | Clean user-facing error when circuit is open | 🟢 Done | #770 |
| E2-S1 | Idempotency | Idempotency key support on write endpoints | 🟢 Done | #770 |
| E2-S2 | Idempotency | Deduplication via Redis | 🟢 Done | #770 |
| E3-S1 | CORS | Strict CORS allowlist — no wildcard in staging/prod | 🟢 Done | #770 |
| E4-S1 | Env Parity | Config audit — all envs use identical structure | 🟢 Done | #770 |
| E4-S2 | Migrations | Enforce reversible migration rule + CI check | 🟢 Done | #770 |
| E5-S1 | SLA/SLO | Define and document SLA targets + alert thresholds | 🟢 Done | #770 |

**Story Status Key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done

---

## Epic 1 — Circuit Breaker on CP→Plant Calls

**Goal:** When Plant backend is slow or down, CP backend fails fast with a clean error instead of holding connections open and cascading failures across the platform.

**Context:**  
Currently CP backend calls Plant via `httpx`. If Plant is down, every CP request hangs for the full timeout (10 seconds). Under load this fills all worker threads and CP becomes unresponsive too. A circuit breaker detects repeated failures and short-circuits immediately for a cooldown period.

---

### E1-S1 — Circuit breaker on CP→Plant HTTP calls

**Story:**  
As the CP backend, when Plant is failing or slow, I stop sending it requests immediately and return a clean error, so CP stays responsive and Plant gets time to recover.

**Acceptance Criteria:**
- Circuit breaker wraps all `httpx` calls from CP backend to Plant
- Opens (stops calling Plant) after 3 consecutive failures within 10 seconds
- Stays open for 30 seconds (cooldown period)
- Moves to half-open after 30 seconds — allows 1 probe request through
- If probe succeeds: circuit closes, normal operation resumes
- If probe fails: circuit re-opens for another 30 seconds
- When circuit is open: calls return immediately with `ServiceUnavailableError` (no HTTP call made)
- Library: `tenacity` (available in Python) or implement lightweight state machine

**Technical Implementation Notes:**
- File: `src/CP/BackEnd/services/plant_client.py` — create this as the single place for all Plant HTTP calls
- All CP backend code that currently calls Plant directly must be refactored to use `PlantClient`
- Circuit breaker state stored in memory (per-process) — acceptable for single-instance; use Redis for multi-instance
- Use `tenacity` with `stop_after_attempt(1)` and a custom `CircuitBreaker` wrapper, OR implement a simple `CircuitBreakerState` class with `CLOSED`, `OPEN`, `HALF_OPEN` states
- Failure conditions: HTTP 5xx responses, connection errors, timeouts — NOT 4xx (those are valid responses)

**Test Cases:**
```
TC-E1-S1-1: Plant returns 200 — circuit stays closed
  → Request succeeds, circuit state = CLOSED

TC-E1-S1-2: Plant returns 500 three times consecutively
  → 3rd failure → circuit opens
  → Subsequent call → immediate ServiceUnavailableError (no HTTP call made)

TC-E1-S1-3: After 30 seconds with circuit open
  → Circuit moves to HALF_OPEN
  → One probe request sent to Plant

TC-E1-S1-4: Probe succeeds
  → Circuit closes
  → Normal requests resume

TC-E1-S1-5: Probe fails
  → Circuit re-opens for another 30 seconds

TC-E1-S1-6: Plant returns 404
  → Circuit stays closed (4xx is not a circuit failure)
```

**Status:** 🟢 Done

---

### E1-S2 — Clean user-facing error when circuit is open

**Story:**  
As a user trying to register while Plant is down, I see a clear, friendly message instead of a timeout or cryptic error, so I know to try again in a moment.

**Acceptance Criteria:**
- When circuit is open and CP backend cannot reach Plant: HTTP 503 returned to frontend
- Error body follows platform error format: `{ "error": { "code": "SERVICE_TEMPORARILY_UNAVAILABLE", "message": "Our service is temporarily unavailable. Please try again in a moment.", "correlation_id": "..." } }`
- Frontend displays this message on registration form without crashing
- `Retry-After: 30` header included so frontend can show a countdown if desired

**Technical Implementation Notes:**
- Catch `ServiceUnavailableError` in CP backend API route handlers
- Return `JSONResponse(status_code=503, content=..., headers={"Retry-After": "30"})`
- Frontend: handle HTTP 503 explicitly — show message, re-enable form after 30 seconds

**Test Cases:**
```
TC-E1-S2-1: Circuit open — attempt registration
  → HTTP 503
  → Body: { "error": { "code": "SERVICE_TEMPORARILY_UNAVAILABLE", ... } }
  → Header: Retry-After: 30

TC-E1-S2-2: Frontend handles 503 gracefully
  → Error message shown
  → Form not in broken state
  → User can retry
```

**Status:** 🟢 Done

---

## Epic 2 — Idempotency Keys

**Goal:** Write endpoints are safe to retry without creating duplicate records. A network timeout causing a retry must not register a customer twice.

---

### E2-S1 — Idempotency key support on write endpoints

**Story:**  
As a client calling a write endpoint, I can include an `Idempotency-Key` header with a UUID, and if I call the same endpoint again with the same key, I get the same response without a second record being created.

**Acceptance Criteria:**
- `Idempotency-Key` header supported on: `POST /api/v1/customers`, `POST /api/v1/audit/events`, `POST /api/cp/auth/register`
- If `Idempotency-Key` is provided and a previous response exists for it: return cached response immediately (no DB write)
- If `Idempotency-Key` not provided: endpoint works normally (backwards compatible)
- Idempotency window: 24 hours (Redis TTL)
- If same key used with different request body: return HTTP 422 with code `IDEMPOTENCY_KEY_CONFLICT`

**Technical Implementation Notes:**
- FastAPI dependency: `idempotency_check(request: Request, idempotency_key: str = Header(None))`
- Redis key pattern: `idempotency:{endpoint_path}:{idempotency_key}`
- Stored value: serialised response body + status code
- TTL: 86400 seconds (24 hours)
- Check request body hash too — if key matches but body differs, return 422
- Implement as a reusable FastAPI middleware or dependency — not duplicated per endpoint

**Test Cases:**
```
TC-E2-S1-1: POST /api/v1/customers with Idempotency-Key: abc123
  → HTTP 201, customer created

TC-E2-S1-2: POST /api/v1/customers again with same Idempotency-Key: abc123 and same body
  → HTTP 201 (same status code)
  → Same response body as first call
  → No second DB record created (customer count unchanged)

TC-E2-S1-3: POST /api/v1/customers with Idempotency-Key: abc123 but different body
  → HTTP 422
  → Error code: IDEMPOTENCY_KEY_CONFLICT

TC-E2-S1-4: POST with no Idempotency-Key header
  → Works normally (no idempotency cache checked)

TC-E2-S1-5: After 24 hours (expire Redis key), same Idempotency-Key
  → Request processed normally (new record potentially created)
```

**Status:** 🟢 Done

---

### E2-S2 — Deduplication via Redis

**Story:**  
As the platform, idempotency state is stored in Redis so it works correctly even if requests hit different backend instances.

**Acceptance Criteria:**
- Redis key `idempotency:{path}:{key}` holds serialised response (JSON status + body)
- TTL set to 86400 on first write
- `GET` check is atomic with the write — use Redis `SET NX` (set if not exists) to avoid race conditions
- If Redis is unavailable: skip idempotency check and proceed normally (degrade gracefully)

**Technical Implementation Notes:**
- Use `aioredis` async client
- Atomic pattern: `SET idempotency:{path}:{key} {value} EX 86400 NX` — returns OK if set, None if key already existed
- If None returned: key existed — fetch cached response with `GET` and return it
- On Redis connection error: log warning, skip idempotency, proceed with normal write

**Test Cases:**
```
TC-E2-S2-1: Two concurrent requests with same Idempotency-Key
  → Exactly one DB write occurs
  → Both callers receive identical response

TC-E2-S2-2: Redis unavailable — write endpoint called
  → Proceeds without idempotency (no error to caller)
  → Warning logged

TC-E2-S2-3: Verify Redis key exists after first call
  → redis-cli GET idempotency:{path}:{key} → non-empty value
  → TTL approximately 86400
```

**Status:** 🟢 Done

---

## Epic 3 — CORS Strict Allowlist

**Goal:** In staging and production, only known origins (CP frontend, mobile app) can make credentialed cross-origin requests. Wildcard `*` is forbidden.

---

### E3-S1 — Strict CORS allowlist — no wildcard in staging/prod

**Story:**  
As the platform security posture, cross-origin requests are only accepted from explicitly approved origins, preventing malicious sites from making authenticated requests on behalf of users.

**Acceptance Criteria:**
- `CORS_ALLOWED_ORIGINS` env var — comma-separated list of allowed origins
- Dev: `http://localhost:3000,http://localhost:8080` (broad for convenience)
- Staging: `https://cp.demo.waooaw.com` (explicit)
- Production: `https://cp.waooaw.com` (explicit)
- Credentials allowed (`allow_credentials=True`) only for explicitly listed origins
- `*` wildcard never used in staging or production
- Preflight (`OPTIONS`) requests return correct CORS headers

**Technical Implementation Notes:**
- Files: `src/Plant/BackEnd/main.py` and `src/CP/BackEnd/main.py` — CORSMiddleware configuration
- Read `CORS_ALLOWED_ORIGINS` from env, split by comma, pass as `allow_origins` list
- `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]` — origins are the restriction
- Add `CORS_ALLOWED_ORIGINS` to all `docker-compose.*.yml` env sections and `.env.example`

**Test Cases:**
```
TC-E3-S1-1: Request from allowed origin with credentials
  → HTTP 200
  → Access-Control-Allow-Origin: {origin} (not *)

TC-E3-S1-2: Request from disallowed origin
  → No Access-Control-Allow-Origin header
  → Browser blocks the request

TC-E3-S1-3: OPTIONS preflight from allowed origin
  → HTTP 200 with correct CORS headers

TC-E3-S1-4: CORS_ALLOWED_ORIGINS not set (or empty)
  → Server refuses to start OR defaults to localhost-only (never wildcard)
```

**Status:** 🟢 Done

---

## Epic 4 — Environment Parity & Migration Standards

---

### E4-S1 — Config audit — all envs use identical structure

**Story:**  
As any developer or deployment, the config structure is identical across dev, staging, and prod — only values differ — so "works on my machine" config bugs are impossible.

**Acceptance Criteria:**
- `.env.example` files exist for each service with ALL required env vars listed (no values, just keys)
- CI checks that all required env vars are present in the running container — startup fails with clear error if any missing
- No hardcoded URLs, ports, or credentials anywhere in code — always read from env
- `docker-compose.local.yml` uses all vars from `.env.example` (with dev values)

**Technical Implementation Notes:**
- Audit `src/Plant/BackEnd/core/config.py` and `src/CP/BackEnd/core/config.py` — all settings must have no default values for required settings (use `...` as default to force explicit configuration)
- Run: `grep -r "localhost\|127.0.0.1\|hardcoded_secret" src/` — must return nothing
- `src/Plant/BackEnd/.env.example` and `src/CP/BackEnd/.env.example` must list all vars

**Test Cases:**
```
TC-E4-S1-1: Start plant-backend with a required env var missing
  → Service fails to start with clear error naming the missing var

TC-E4-S1-2: grep codebase for hardcoded localhost/IPs
  → Only found in .env.example files and config comments, not in application code

TC-E4-S1-3: All keys in .env.example have matching entries in config.py
```

**Status:** 🟢 Done

---

### E4-S2 — Enforce reversible migration rule + CI check

**Story:**  
As the platform, every Alembic migration has a working `downgrade()` function so we can roll back a bad deploy without data loss.

**Acceptance Criteria:**
- Every migration file has a `downgrade()` that reverses its `upgrade()` completely
- CI pipeline runs `alembic downgrade -1` after `alembic upgrade head` — must succeed without errors
- New migrations are rejected in PR review if `downgrade()` is not implemented (code review checklist item)
- Add this to `.github/PULL_REQUEST_TEMPLATE.md`: `[ ] Migration downgrade() tested`

**Technical Implementation Notes:**
- Add to CI workflow: after running upgrade, run `alembic downgrade -1`, then `alembic upgrade head` again (round-trip test)
- File: `.github/workflows/` — add step to existing backend CI job

**Test Cases:**
```
TC-E4-S2-1: Run alembic upgrade head → alembic downgrade -1 → alembic upgrade head
  → No errors at any step
  → Database schema identical after round-trip

TC-E4-S2-2: CI pipeline fails if downgrade raises NotImplementedError
```

**Status:** 🟢 Done

---

## Epic 5 — SLA / SLO Definitions

---

### E5-S1 — Define and document SLA targets + alert thresholds

**Story:**  
As the platform team, we have documented service targets that define what "good" looks like, so we know when to act and have thresholds for automated alerts.

**Acceptance Criteria:**
- SLA/SLO targets documented and agreed:
  - Uptime: 99.9% (max 43 minutes downtime/month)
  - p95 API response time: < 500ms
  - Error rate: < 0.1%
  - Registration success rate: > 95%
- Alert thresholds defined:
  - Error rate > 1% for 5 minutes → page on-call
  - p95 latency > 2 seconds → warning alert
  - Registration failure rate > 5% → critical alert
  - Health check failing → immediate alert
- Document updated in `docs/CP/Registration.md` infrastructure standards section
- Alert rules configured in GCP Monitoring (or equivalent) — screenshot/config committed to `cloud/monitoring/`

**Technical Implementation Notes:**
- No code change — configuration and documentation task
- GCP Cloud Monitoring: create Alerting Policies for each threshold
- Commit alert policy YAML to `cloud/monitoring/alert-policies/`

**Test Cases:**
```
TC-E5-S1-1: Manually trigger error rate spike (send 20 bad requests)
  → Alert fires within 5 minutes

TC-E5-S1-2: Health check endpoint returns 503
  → Alert fires within 1 minute

TC-E5-S1-3: All alert policies visible in GCP Monitoring console
```

**Status:** 🟢 Done

---

## Epic Completion — Docker Integration Test

```bash
# Start all services
docker compose -f docker-compose.local.yml up -d

# Full test suite
docker compose -f docker-compose.local.yml run --rm --no-deps plant-backend pytest tests/ -x -q
docker compose -f docker-compose.local.yml run --rm --no-deps cp-backend pytest tests/ -x -q

# Test migration round-trip
docker compose -f docker-compose.local.yml run --rm plant-backend alembic upgrade head
docker compose -f docker-compose.local.yml run --rm plant-backend alembic downgrade -1
docker compose -f docker-compose.local.yml run --rm plant-backend alembic upgrade head

# Verify Redis idempotency keys work
docker compose -f docker-compose.local.yml exec redis redis-cli KEYS "idempotency:*"

# Verify CORS headers
curl -H "Origin: http://localhost:3000" -I http://localhost:8000/health
# → Should show Access-Control-Allow-Origin: http://localhost:3000
```

All tests pass. Migration round-trip succeeds. CORS headers correct.
