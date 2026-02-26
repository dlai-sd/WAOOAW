# Iteration 2 — Audit API

**When:** Before the second screen ships (immediately after registration)  
**Branch naming:** `feat/audit-api-it2`  
**Testing:** `docker compose -f docker-compose.local.yml` — no virtual env, no local Python  
**Status:** 🟢 Complete — merged PR #769

---

## Tracking Table

| # | Epic | Story | Status | PR |
|---|------|-------|--------|----|
| E1-S1 | Audit Table | Create audit_logs migration in Plant DB | 🟢 Done | [#769](https://github.com/dlai-sd/WAOOAW/pull/769) |
| E1-S2 | Audit Table | Create AuditLog model and schema | 🟢 Done | [#769](https://github.com/dlai-sd/WAOOAW/pull/769) |
| E1-S3 | Audit Table | Create AuditService | 🟢 Done | [#769](https://github.com/dlai-sd/WAOOAW/pull/769) |
| E2-S1 | Audit API | POST /api/v1/audit/events endpoint | 🟢 Done | [#769](https://github.com/dlai-sd/WAOOAW/pull/769) |
| E2-S2 | Audit API | GET /api/v1/audit/events endpoint (admin only) | 🟢 Done | [#769](https://github.com/dlai-sd/WAOOAW/pull/769) |
| E2-S3 | Audit API | Service key auth for write endpoint | 🟢 Done | [#769](https://github.com/dlai-sd/WAOOAW/pull/769) |
| E3-S1 | Integration | CP backend writes registration events via Audit API | 🟢 Done | [#769](https://github.com/dlai-sd/WAOOAW/pull/769) |
| E3-S2 | Integration | Fire-and-forget wrapper — audit never blocks user flow | 🟢 Done | [#769](https://github.com/dlai-sd/WAOOAW/pull/769) |

**Story Status Key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done

---

## Epic 1 — Audit Table in Plant DB

**Goal:** A single `audit_logs` table in Plant's PostgreSQL — one record per significant business event across all interfaces (CP web, mobile, Plant admin, APIs).

---

### E1-S1 — Create audit_logs migration in Plant DB

**Story:**  
As the platform database, I have an `audit_logs` table with correct schema, indexes, and soft delete capability from day one.

**Acceptance Criteria:**
- New Alembic migration file created: `016_audit_logs.py`
- Table `audit_logs` created with these columns:
  - `id` — UUID, primary key, default `gen_random_uuid()`
  - `timestamp` — `timestamptz`, default `NOW()`, NOT NULL
  - `user_id` — UUID, nullable (FK to `customers.id` ON DELETE SET NULL)
  - `email` — text, nullable (for pre-registration events where user_id doesn't exist yet)
  - `ip_address` — text, nullable
  - `user_agent` — text, nullable
  - `screen` — text, NOT NULL (e.g. `cp_registration`, `cp_login`, `mobile_registration`)
  - `action` — text, NOT NULL (e.g. `otp_sent`, `captcha_failed`, `registration_complete`)
  - `outcome` — text, NOT NULL — constraint: must be `success` or `failure`
  - `detail` — text, nullable (human-readable description)
  - `metadata` — jsonb, nullable, default `{}`
  - `correlation_id` — text, nullable (links to Gateway correlation ID)
  - `deleted_at` — `timestamptz`, nullable (soft delete)
- Indexes created:
  - `idx_audit_logs_email` on `email`
  - `idx_audit_logs_user_id` on `user_id`
  - `idx_audit_logs_action` on `action`
  - `idx_audit_logs_screen` on `screen`
  - `idx_audit_logs_timestamp` on `timestamp DESC`
  - `idx_audit_logs_correlation_id` on `correlation_id`
- Migration has working `downgrade()` that drops the table

**Technical Implementation Notes:**
- File location: `src/Plant/BackEnd/database/migrations/versions/016_audit_logs.py`
- Use `op.create_table()` and `op.create_index()` — see existing migrations for pattern
- `outcome` check constraint: `CHECK (outcome IN ('success', 'failure'))`
- Run migration: `docker compose -f docker-compose.local.yml run --rm plant-backend alembic upgrade head`

**Test Cases:**
```
TC-E1-S1-1: Run migration upgrade
  → No errors
  → audit_logs table exists in DB

TC-E1-S1-2: Inspect audit_logs columns
  → All 13 columns present with correct types and constraints

TC-E1-S1-3: Test outcome constraint
  → INSERT with outcome='invalid' → constraint violation error

TC-E1-S1-4: Run migration downgrade
  → No errors
  → audit_logs table removed

TC-E1-S1-5: All 6 indexes exist
  → \d audit_logs in psql shows all indexes
```

**Status:** 🟢 Done — PR #769

---

### E1-S2 — Create AuditLog model and schema

**Story:**  
As the Plant backend, I have a SQLAlchemy model and Pydantic schemas for audit logs so I can read and write them type-safely.

**Acceptance Criteria:**
- SQLAlchemy model `AuditLog` in `src/Plant/BackEnd/models/audit_log.py`
- Pydantic schemas: `AuditEventCreate` (write), `AuditEventResponse` (read) in `src/Plant/BackEnd/schemas/audit_log.py`
- `AuditEventCreate` fields: `screen`, `action`, `outcome`, plus all optional fields
- `AuditEventResponse` includes all fields including `id` and `timestamp`
- Model has `__tablename__ = "audit_logs"`
- `deleted_at` is always excluded from public responses

**Technical Implementation Notes:**
- Follow exact pattern of existing models — see `src/Plant/BackEnd/models/customer.py`
- `AuditLog` inherits from `BaseEntity` if that provides `id`/`created_at`, otherwise define manually
- `metadata` field: use `JSON` SQLAlchemy type, default `{}`
- Pydantic `outcome` field: use `Literal["success", "failure"]` for type safety

**Test Cases:**
```
TC-E1-S2-1: Import AuditLog model — no errors
TC-E1-S2-2: Create AuditEventCreate with valid data — no validation errors
TC-E1-S2-3: Create AuditEventCreate with invalid outcome ('invalid') — ValidationError raised
TC-E1-S2-4: AuditEventResponse does not include deleted_at field
```

**Status:** 🟢 Done — PR #769

---

### E1-S3 — Create AuditService

**Story:**  
As the Plant backend, I have an `AuditService` that provides `log_event()` for writing and `query_events()` for reading, so no caller ever writes SQL directly.

**Acceptance Criteria:**
- `AuditService` class in `src/Plant/BackEnd/services/audit_service.py`
- `async log_event(payload: AuditEventCreate) -> AuditLog` — inserts record, returns created row
- `async query_events(user_id=None, email=None, screen=None, action=None, outcome=None, from_ts=None, to_ts=None, page=1, page_size=20) -> tuple[list[AuditLog], int]` — returns paginated results + total count
- `query_events` always filters `WHERE deleted_at IS NULL`
- `log_event` never raises — on DB error, logs the error and returns None (audit must not break caller)

**Technical Implementation Notes:**
- File: `src/Plant/BackEnd/services/audit_service.py`
- Follow pattern of `src/Plant/BackEnd/services/customer_service.py`
- `log_event` wraps DB write in try/except — catches all exceptions, logs with Python `logging.error()`, returns None on failure
- `query_events` uses SQLAlchemy `select` with dynamic `where` clauses based on provided filters
- Pagination: `offset = (page - 1) * page_size`, `limit = page_size`

**Test Cases:**
```
TC-E1-S3-1: log_event with valid AuditEventCreate
  → Returns AuditLog object with populated id and timestamp

TC-E1-S3-2: query_events with no filters
  → Returns list of all non-deleted records + total count

TC-E1-S3-3: query_events with screen='cp_registration'
  → Returns only records matching that screen

TC-E1-S3-4: query_events pagination — 25 records, page_size=10, page=2
  → Returns 10 records, total=25

TC-E1-S3-5: log_event when DB is unavailable (mock DB error)
  → Does not raise
  → Returns None
  → Error logged
```

**Status:** 🟢 Done — PR #769

---

## Epic 2 — Audit API Endpoints

**Goal:** All audit writes and reads go through a secured API — no direct DB access from callers. Write is protected by service key, read is protected by admin JWT.

---

### E2-S1 — POST /api/v1/audit/events endpoint

**Story:**  
As any backend service (CP backend, Plant backend, Gateway), I can write an audit event by calling `POST /api/v1/audit/events` with a service key, so audit format is always consistent.

**Acceptance Criteria:**
- `POST /api/v1/audit/events` accepts `AuditEventCreate` JSON body
- Protected by `X-Audit-Service-Key` header — value must match `AUDIT_SERVICE_KEY` env var
- Returns HTTP 201 with `AuditEventResponse` on success
- Returns HTTP 403 if service key is missing or wrong
- Returns HTTP 422 if request body is invalid
- Endpoint is in the public path list (no JWT required — uses service key instead)
- Response time < 100ms for a single write

**Technical Implementation Notes:**
- File: `src/Plant/BackEnd/api/v1/audit.py` — new file
- Register router in `src/Plant/BackEnd/api/v1/router.py`
- Service key check: FastAPI dependency `verify_audit_service_key(request: Request)` — reads `X-Audit-Service-Key`, compares to `settings.AUDIT_SERVICE_KEY`
- Add `AUDIT_SERVICE_KEY` to `src/Plant/BackEnd/core/config.py` and `.env.example`
- Add to `_is_public_path()` in `src/Plant/Gateway/middleware/auth.py`: `/api/v1/audit/events` (POST only)

**Test Cases:**
```
TC-E2-S1-1: POST /api/v1/audit/events with valid body + correct service key
  → HTTP 201
  → Body contains AuditEventResponse with id and timestamp
  → Record exists in DB

TC-E2-S1-2: POST /api/v1/audit/events with missing X-Audit-Service-Key header
  → HTTP 403
  → Error code: AUDIT_KEY_MISSING

TC-E2-S1-3: POST /api/v1/audit/events with wrong service key
  → HTTP 403
  → Error code: AUDIT_KEY_INVALID

TC-E2-S1-4: POST /api/v1/audit/events with invalid body (missing required field)
  → HTTP 422

TC-E2-S1-5: POST /api/v1/audit/events without JWT (verify public path)
  → Does not return 401 — service key is the auth mechanism
```

**Status:** 🟢 Done — PR #769

---

### E2-S2 — GET /api/v1/audit/events endpoint (admin only)

**Story:**  
As an admin user, I can query audit logs by user, screen, action, and time range so I can investigate customer issues and compliance queries.

**Acceptance Criteria:**
- `GET /api/v1/audit/events` — JWT required, admin role required
- Query params: `user_id`, `email`, `screen`, `action`, `outcome`, `from_ts`, `to_ts`, `page` (default 1), `page_size` (default 20, max 100)
- Response: `{ items: [...], total, page, page_size, has_more }`
- Returns HTTP 403 if JWT is valid but user is not admin role
- Returns HTTP 401 if no JWT
- Soft-deleted records never returned

**Technical Implementation Notes:**
- File: `src/Plant/BackEnd/api/v1/audit.py`
- Role check: FastAPI dependency `require_admin_role(claims: dict = Depends(get_jwt_claims))` — checks `claims["role"] == "admin"`
- Pagination response shape must match platform standard (defined in NFR doc)
- `from_ts` / `to_ts` are ISO 8601 strings, parsed to `datetime` in query param handler

**Test Cases:**
```
TC-E2-S2-1: GET /api/v1/audit/events with admin JWT
  → HTTP 200
  → Response contains items, total, page, page_size, has_more

TC-E2-S2-2: GET /api/v1/audit/events with non-admin JWT
  → HTTP 403

TC-E2-S2-3: GET /api/v1/audit/events with no JWT
  → HTTP 401

TC-E2-S2-4: GET /api/v1/audit/events?screen=cp_registration
  → Returns only cp_registration events

TC-E2-S2-5: GET /api/v1/audit/events?page=1&page_size=5 with 12 records
  → Returns 5 records, total=12, has_more=true

TC-E2-S2-6: GET /api/v1/audit/events?page_size=200
  → Returns 422 or clamps to max 100
```

**Status:** 🟢 Done — PR #769

---

### E2-S3 — Service key auth for write endpoint

**Story:**  
As the platform, only authorised backend services can write audit events — random callers with no service key are rejected, so the audit log is trustworthy.

**Acceptance Criteria:**
- `AUDIT_SERVICE_KEY` is a 32+ character random string, stored in env var / GCP Secret Manager
- Key is never logged, never returned in any API response
- Key rotation: changing `AUDIT_SERVICE_KEY` env var and redeploying immediately revokes old key
- All backend services that write audit events have `AUDIT_SERVICE_KEY` in their env config

**Technical Implementation Notes:**
- Add `AUDIT_SERVICE_KEY` to:
  - `src/Plant/BackEnd/core/config.py` (Settings class)
  - `src/CP/BackEnd/core/config.py` (Settings class — CP reads it to send in header)
  - `docker-compose.local.yml` — both plant-backend and cp-backend services
  - `.env.example` — with placeholder value
- Generate a secure key: `python -c "import secrets; print(secrets.token_hex(32))"`

**Test Cases:**
```
TC-E2-S3-1: AUDIT_SERVICE_KEY env var present in both plant-backend and cp-backend containers
  → docker compose exec plant-backend env | grep AUDIT_SERVICE_KEY → shows value
  → docker compose exec cp-backend env | grep AUDIT_SERVICE_KEY → shows value

TC-E2-S3-2: AUDIT_SERVICE_KEY does not appear in any log output
  → grep AUDIT_SERVICE_KEY in docker compose logs → not found

TC-E2-S3-3: Change AUDIT_SERVICE_KEY, restart services, old key rejected
  → POST with old key → HTTP 403
```

**Status:** 🟢 Done — PR #769

---

## Epic 3 — Integration: CP Backend Uses Audit API

**Goal:** CP backend writes all registration audit events through the Audit API, not directly to any file or DB, and audit failures never break the user flow.

---

### E3-S1 — CP backend writes registration events via Audit API

**Story:**  
As the CP backend, after each significant step in the registration flow, I fire an audit event to Plant's Audit API so every registration is fully traceable.

**Acceptance Criteria:**
- CP backend has an `AuditClient` helper that wraps `POST /api/v1/audit/events` calls
- `AuditClient` is configured with Plant's base URL and `AUDIT_SERVICE_KEY`
- Registration flow writes these events (screen = `cp_registration`):
  - `captcha_verified` — success/failure
  - `otp_sent` — success/failure
  - `otp_verified` — success/failure
  - `otp_failed` — failure (with attempt count in metadata)
  - `duplicate_detected` — failure
  - `registration_complete` — success (with customer_id in metadata)
- Each call includes `correlation_id` from the incoming request header if present

**Technical Implementation Notes:**
- File: `src/CP/BackEnd/services/audit_client.py` — new file
- Uses `httpx.AsyncClient` with `base_url = settings.PLANT_API_URL`, header `X-Audit-Service-Key`
- Timeout: 2 seconds — must not stall the registration request
- Each audit call is `await`ed but wrapped in try/except (E3-S2 covers fire-and-forget)
- Correlation ID: read from incoming request headers `X-Correlation-ID`, pass to audit event

**Test Cases:**
```
TC-E3-S1-1: Complete registration flow end to end
  → audit_logs table contains all 4+ events for that email in order

TC-E3-S1-2: Registration with wrong OTP
  → audit_logs contains otp_failed event with attempt_count in metadata

TC-E3-S1-3: Registration with duplicate email
  → audit_logs contains duplicate_detected event

TC-E3-S1-4: Each audit event has matching correlation_id
  → All events from one registration share the same correlation_id
```

**Status:** 🟢 Done — PR #769

---

### E3-S2 — Fire-and-forget wrapper — audit never blocks user flow

**Story:**  
As a registering user, if the audit service is slow or down, my registration completes normally — I never wait for audit and never see an audit error.

**Acceptance Criteria:**
- All `AuditClient` calls are wrapped so exceptions are caught and swallowed
- Audit call failures are logged (Python `logging.warning`) but not re-raised
- If Audit API returns non-2xx: log the error, continue
- If Audit API times out (> 2 seconds): log, continue
- User-facing registration response is never delayed by audit

**Technical Implementation Notes:**
- Implement `fire_and_forget_audit(coro)` helper in `src/CP/BackEnd/services/audit_client.py`
- Use `asyncio.create_task()` — fires the audit call as a background task without awaiting
- Alternatively: wrap each call in `try/except Exception` with `logging.warning` — simpler, acceptable
- Recommended: `asyncio.create_task()` for truly non-blocking behaviour

**Test Cases:**
```
TC-E3-S2-1: Mock Audit API to return 500 — attempt registration
  → Registration completes successfully
  → HTTP 201 returned to user
  → Warning logged in CP backend logs

TC-E3-S2-2: Mock Audit API to time out (delay > 2s) — attempt registration
  → Registration completes without waiting for audit
  → User gets response in < 3 seconds total

TC-E3-S2-3: Audit API completely unreachable — attempt registration
  → Registration completes
  → Connection error logged as warning, not error
```

**Status:** 🟢 Done — PR #769

---

## Epic Completion — Docker Integration Test

Run after all stories in this iteration are complete.

```bash
# Start all services
docker compose -f docker-compose.local.yml up -d

# Run Plant backend tests
docker compose -f docker-compose.local.yml run --rm --no-deps plant-backend pytest tests/ -x -q

# Run CP backend tests
docker compose -f docker-compose.local.yml run --rm --no-deps cp-backend pytest tests/ -x -q

# Verify migration ran
docker compose -f docker-compose.local.yml exec plant-backend alembic current
# Should show: 016_audit_logs (head)

# Verify audit table exists
docker compose -f docker-compose.local.yml exec db psql -U waooaw -c "\d audit_logs"

# Verify indexes
docker compose -f docker-compose.local.yml exec db psql -U waooaw -c "\d+ audit_logs"

# Do a test registration and verify audit events written
# Then query:
docker compose -f docker-compose.local.yml exec db psql -U waooaw -c "SELECT screen, action, outcome, timestamp FROM audit_logs ORDER BY timestamp;"
```

All tests must pass. Audit table must exist with all indexes. At least 4 audit events visible after a test registration.
