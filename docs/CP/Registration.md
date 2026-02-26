# CP Registration — Root Cause Analysis & Proposed Fixes

**Date**: 2026-02-25  
**Status**: PENDING APPROVAL — no code changed yet  
**Investigator**: GitHub Copilot  
**Scope**: Web CP registration screen (12-field form → OTP → JWT)

---

## ⚠️ Required Flow — Agreed Standard (2026-02-25)

The following is the **agreed correct registration flow** for CP. All implementation must conform to this. Any existing code or PR that deviates from this is incorrect and must be reworked.

| Step | What happens | Why |
|------|-------------|-----|
| 1 | User fills in required details (name, email, etc.) | Nothing is saved to DB at this point |
| 2 | CAPTCHA shown and verified | Blocks bots before any OTP is triggered — prevents abuse and cost |
| 3 | OTP sent to user's email | OTP input is **always visible** on screen — user is never confused about what to do next |
| 4 | User enters and verifies OTP | Confirms the user genuinely owns that email address |
| 5 | Duplicate check via Plant | CP asks Plant to check DB for existing record — **no write yet** |
| 5a | **If duplicate found** → show message to user | "This email is already registered. Would you like to log in, or use a different email?" — two options: **Go to Login** (redirects to login screen) or **Use Different Email** (clears form back to step 1) |
| 6 | If not duplicate → save record | Only at this point is a customer record created in the database |

**Key rules:**
- No DB record is created before OTP is verified
- CAPTCHA gates the OTP send (not the DB save)
- OTP gates the DB write
- Duplicate check happens before the final save, not after
- On duplicate: user is informed and given a clear choice — never silently fail or continue

---

## ⚠️ Infrastructure Standards — Must Be Done With Registration (2026-02-25)

Registration is the first complete end-to-end flow. These standards must be established here and applied to every screen going forward.

### Platform Architecture (Confirmed)

WAOOAW is **one platform, one database, four interfaces**:

| Interface | What it is |
|-----------|-----------|
| CP Web | Customer portal frontend (React/Vite) |
| Mobile | React Native app |
| Plant | Core backend + admin |
| APIs | External/partner API access |

There is **one PostgreSQL database**. CP, mobile, and Plant all read/write the same DB — either directly (Plant) or via Plant's APIs (CP, mobile). No separate databases per interface.

---

### 1. OTP Storage — Move from Files to Database

Currently OTP codes are stored in local files on the CP backend. This is not acceptable for production:

| Issue | Impact |
|-------|--------|
| Files are lost on container restart | User's OTP becomes invalid mid-flow |
| No expiry enforcement at storage level | Stale OTPs can linger |
| Cannot scale horizontally | Two CP backend instances won't share OTP state |

**Required:** OTP codes must be stored in the PostgreSQL database with a dedicated table:

| Column | Purpose |
|--------|---------|
| `id` | UUID primary key |
| `email` | Who the OTP belongs to |
| `code` | Hashed OTP code (never plain text) |
| `expires_at` | Timestamp — OTP invalid after this |
| `verified_at` | Set when successfully verified, null until then |
| `created_at` | Audit trail |

### 2. Audit / Trace Table — Single Table, All Screens, Defacto Standard

One central `audit_logs` table. Every service, every screen, every action writes to it. No per-feature tables.

**Table structure:**

| Column | Type | Purpose |
|--------|------|---------|
| `id` | UUID | Primary key |
| `timestamp` | timestamptz | When it happened |
| `user_id` | UUID (nullable) | Customer ID if known at time of event |
| `email` | text (nullable) | Email if known (pre-registration, user_id may not exist yet) |
| `ip_address` | text | Client IP |
| `user_agent` | text | Browser/device |
| `screen` | text | Which screen/flow (e.g. `cp_registration`, `cp_login`) |
| `action` | text | What happened (e.g. `otp_sent`, `captcha_failed`) |
| `outcome` | text | `success` / `failure` |
| `detail` | text (nullable) | Human-readable description |
| `metadata` | jsonb | Anything extra — flexible, queryable |

**This is the standard for every screen going forward. No flow ships without audit coverage.**

For registration specifically, these events must be written:

| `action` | `outcome` | When |
|----------|-----------|------|
| `registration_started` | success | User submits form |
| `captcha_verified` | success/failure | CAPTCHA result |
| `otp_sent` | success/failure | OTP dispatch attempt |
| `otp_verified` | success/failure | User enters OTP |
| `otp_failed` | failure | Wrong code (include attempt count in metadata) |
| `duplicate_detected` | failure | Email already exists in DB |
| `registration_complete` | success | Record saved, customer_id assigned |

### 3. Audit API — Standard Access Pattern

Nobody writes to `audit_logs` directly. All audit writes and reads go through a dedicated Audit API. This ensures consistent format and prevents bypassing.

| Method | Endpoint | Who calls it | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/v1/audit/events` | Any backend service (CP backend, Plant backend, Gateway) | Internal service key (`X-CP-Registration-Key` pattern) |
| `GET` | `/api/v1/audit/events` | Admin/compliance only | JWT, admin role required |
| `GET` | `/api/v1/audit/events?user_id=&screen=&action=` | Admin/compliance only | JWT, admin role required |

**Rules:**
- No service writes directly to the `audit_logs` table via SQL — always goes via the API
- Read access is JWT-gated and restricted to admin roles only
- Every backend call to the Audit API is fire-and-forget (async, non-blocking) — audit failure must never break the user flow

---

## ⚠️ Platform NFRs & Industry Standards — Full Reference (2026-02-25)

These apply to the entire platform, not just registration. Registration is the first place to implement them. Every screen and feature built after this must comply.

---

### SECURITY

**Rate Limiting**
- Default: 10 requests per IP per minute per endpoint
- Registration/OTP specifically: 5 attempts per IP per 10 minutes
- Lockout: IP blocked for 15 minutes after limit hit
- Must return `HTTP 429` with `Retry-After` header

**OTP Attempt Lockout**
- Max 3 wrong OTP attempts per OTP session
- On 3rd failure: OTP session invalidated, user must restart from step 1
- Prevents brute-force of 6-digit codes

**JWT Strategy**
- Access token expiry: 15 minutes
- Refresh token expiry: 7 days
- Silent refresh: frontend refreshes access token automatically before expiry — user never sees a logout
- Refresh token stored in `httpOnly` cookie (not localStorage — prevents XSS theft)
- On logout: refresh token invalidated server-side

**HTTPS Only**
- All traffic HTTPS in staging and production, no exceptions
- HTTP requests redirected to HTTPS (301)
- HSTS header: `max-age=31536000; includeSubDomains`

**CORS Policy**
- Allowlist specific origins only — never `*` in production
- CP web, mobile app origins explicitly listed
- Credentials allowed only for those origins

**Input Validation**
- All inputs validated server-side regardless of client-side validation
- Email: normalised to lowercase, trimmed, RFC5322 validated
- Phone: E.164 format enforced
- All text fields: max length enforced, HTML stripped

**Secrets Management**
- No secrets in code or git — ever
- All secrets via environment variables or secrets manager (GCP Secret Manager)
- Rotate secrets without downtime — always via env, never hardcoded

---

### DATA

**Soft Deletes Only**
- Never hard-delete any customer, audit, or transaction record
- All tables with user data must have `deleted_at timestamptz` (null = active)
- Queries always filter `WHERE deleted_at IS NULL`
- Hard delete only allowed for explicit GDPR erasure requests, via a controlled process

**GDPR / Data Privacy**
- PII stored: email, phone, name, GST, IP address, user agent
- Right to erasure: process must exist — anonymise PII in all tables when requested (replace with `[REDACTED]`, keep record structure for audit integrity)
- Data retention: audit logs kept 2 years, OTP records kept 30 days then purged
- No PII in logs (structured logs must mask email/phone)

**DB Indexes — Must Have From Day One**

| Table | Index on |
|-------|---------|
| `customers` | `email`, `phone` |
| `audit_logs` | `email`, `user_id`, `action`, `timestamp`, `screen` |
| `otp_sessions` | `email`, `expires_at` |

**DB Connection Pooling**
- Use PgBouncer or SQLAlchemy pool — never open a new connection per request
- Pool size: min 5, max 20 per service instance

**Data Retention / Cleanup Jobs**
- OTP records: delete expired + verified records after 30 days (scheduled job)
- Audit logs: archive to cold storage after 2 years
- Unverified/abandoned registrations: none — new flow never creates unverified records

---

### API STANDARDS

**Consistent Error Format — Every API, Every Service**

All errors must return this shape, no exceptions:
```json
{
  "error": {
    "code": "OTP_EXPIRED",
    "message": "Your OTP has expired. Please request a new one.",
    "detail": "otp_session_id abc123 expired at 2026-02-25T10:00:00Z",
    "correlation_id": "req_abc123xyz"
  }
}
```
- `code`: machine-readable, uppercase snake case — frontend uses this for logic
- `message`: human-readable, safe to show to user
- `detail`: optional, more info for debugging (never expose stack traces)
- `correlation_id`: ties back to logs

**Correlation ID**
- Every request gets a unique ID at the Gateway (`X-Correlation-ID` header)
- This ID flows through: CP backend → Plant → all internal calls
- Logged at every hop
- Returned in every error response
- Allows end-to-end tracing of any single request across all services

**API Versioning**
- Always `/api/v1/...` — already in place
- Breaking changes go to `/api/v2/...` — never modify existing versioned endpoints in a breaking way

**Pagination — All List Endpoints**
- Default page size: 20
- Max page size: 100
- Response always includes `total`, `page`, `page_size`, `has_more`
- Cursor-based pagination preferred for large tables (audit_logs)

**Request/Response Size Limits**
- Max request body: 1MB
- Max file upload (if any): defined per endpoint explicitly

**Timeout Standards**
- CP backend → Plant: 10 second timeout
- Plant → external APIs (CAPTCHA, email): 5 second timeout
- All external calls: must have explicit timeout — no hanging requests

**Retry Policy for External Calls**
- CAPTCHA verification: no retry (tokens are single-use)
- Email sending (OTP): retry 2 times with 1 second backoff
- Plant API calls from CP: retry 2 times on 5xx only, never on 4xx

---

### OBSERVABILITY

**Structured Logging**
- All logs in JSON format
- Every log line includes: `timestamp`, `level`, `service`, `correlation_id`, `message`
- No PII in logs — mask email as `u***@domain.com`, never log phone or full name
- Log levels: `DEBUG` (dev only), `INFO` (normal flow), `WARNING` (recoverable issues), `ERROR` (failures needing attention)

**Health Check Endpoints**
- Every service must expose `GET /health` — returns `200 OK` with `{ "status": "ok" }`
- Deep health check `GET /health/ready` — checks DB connection, returns service as ready only if DB is reachable

**Metrics (Good to Have, Do Before Production)**
- Track: request count, error rate, latency per endpoint
- Track: OTP send success/failure rate, registration completion rate
- Use for alerting: error rate > 1% triggers alert

---

### FRONTEND STANDARDS

**Loading States**
- Every async action (form submit, OTP send, verify) must show a spinner/disabled state
- User must never be able to double-submit — button disabled until response received

**User-Facing Error Messages**
- Never show raw API error strings to the user (`"IntegrityError: duplicate key"` is not acceptable)
- Use the `code` field from the error response to map to friendly messages on the frontend
- All user-facing messages must be defined in a central constants file — not scattered in component code

**Client-Side Validation**
- Always validate before hitting the API — saves round trips and gives instant feedback
- But never trust client-side validation alone — server always validates too

---

### TESTING STANDARDS

| Type | Minimum coverage | When required |
|------|-----------------|---------------|
| Unit tests | 80% overall, 90% on services/business logic | Every PR |
| Integration tests | All API endpoints covered | Every new endpoint |
| E2E tests | All happy paths + top 3 failure paths per screen | Before any production deploy |

**Test data must never use real customer data.** Fixtures and factories only.

---

### MUST HAVE vs GOOD TO HAVE

| Standard | Priority | When |
|----------|----------|------|
| Consistent error format | **Must have** | Before any screen ships |
| Correlation ID | **Must have** | Before any screen ships |
| Rate limiting | **Must have** | Before any screen ships |
| OTP lockout | **Must have** | Registration |
| Soft deletes | **Must have** | From first migration |
| DB indexes | **Must have** | From first migration |
| JWT refresh / httpOnly cookie | **Must have** | Before login ships |
| HTTPS + HSTS | **Must have** | Before staging |
| Structured logging | **Must have** | Now |
| Health checks | **Must have** | Now |
| GDPR erasure process | **Must have** | Before any real customer data |
| Pagination standard | **Must have** | First list endpoint |
| Audit fire-and-forget | **Must have** | Registration |
| CORS allowlist | **Must have** | Before staging |
| Circuit breaker | **Must have** | Before production |
| Idempotency keys | **Must have** | Before production |
| Token revocation (Redis) | **Must have** | Before login ships |
| CSP / security headers | **Must have** | Before staging |
| Dependency vuln scanning in CI | **Must have** | Now — add to pipeline |
| Async email / notifications | **Must have** | Before production |
| SLA / SLO defined | **Must have** | Before any real customer onboarding |
| GDPR PII data classification | **Must have** | Before any real customer data |
| Reversible DB migrations | **Must have** | From first migration |
| Backup restore tested | **Must have** | Before production |
| Metrics / alerting | **Good to have** | Before production |
| Field-level PII encryption | **Good to have** | Before production |
| Distributed tracing (OpenTelemetry) | **Good to have** | Before production |
| Feature flags | **Good to have** | Before scaling |
| Event-driven / async messaging | **Good to have** | Before scaling |
| Read replica | **Good to have** | Before admin dashboard |
| Cursor-based pagination | **Good to have** | When audit_logs grows large |
| Data archival jobs | **Good to have** | Before production |
| Pen testing | **Good to have** | Before real customer onboarding |
| Uptime monitoring (external) | **Good to have** | Before production |

---

## ⚠️ Enterprise Architecture Gaps — Full Gap Analysis (2026-02-25)

---

### SECURITY GAPS

**Field-level PII Encryption**
- `email`, `phone`, `gst_number` stored in plain text in PostgreSQL
- Disk-level encryption is not enough — if DB is compromised, all PII is readable
- **Required:** encrypt these columns using `pgcrypto` (PostgreSQL built-in), decrypt only on read
- Priority: Good to have now, Must have before real customer data

**Token Revocation**
- Currently no way to invalidate a JWT once issued
- If a user's account is compromised or they reset their password, their old tokens remain valid until expiry
- **Required:** Redis-based revocation list — store invalidated JWT IDs, check on every authenticated request
- Redis is already in docker-compose — just needs to be wired up
- Priority: Must have before login ships

**Content Security Policy (CSP) Headers**
- No CSP headers on CP frontend responses
- Without CSP: injected scripts can run, clickjacking is possible
- **Required:** `Content-Security-Policy: script-src 'self'; frame-ancestors 'none'` and `X-Frame-Options: DENY`
- Priority: Must have before staging

**Dependency Vulnerability Scanning**
- No automated CVE scanning in CI/CD pipeline
- A critical vulnerability in a Python or npm package will not be caught until manually noticed
- **Required:** `pip audit` in backend CI, `npm audit` in frontend CI — fail build on critical severity
- Priority: Must have — add to pipeline now

**OWASP Top 10 Formal Checklist**
- No formal OWASP coverage checklist exists
- SQLAlchemy covers SQL injection, but IDOR, CSRF, XSS, security misconfiguration need formal review
- **Required:** OWASP checklist completed before any screen goes to production
- Priority: Must have before production

**Penetration Testing**
- No pen test planned
- **Required:** At minimum run OWASP ZAP automated scan before real customer onboarding. Annual manual pen test once live.
- Priority: Good to have, must happen before real customers

---

### RELIABILITY GAPS

**Circuit Breaker**
- When Plant backend is slow or down, CP backend hangs for the full timeout (10 seconds)
- Under load, this causes request pile-up and cascading failures
- **Required:** Circuit breaker on all CP→Plant calls — open after 3 failures in 10 seconds, half-open after 30 seconds, return clean error immediately when open
- Library: Tenacity (already used in codebase for retries)
- Priority: Must have before production

**Idempotency Keys**
- `POST /customers` and `POST /audit/events` are not idempotent
- A network timeout causes the client to retry and potentially create duplicate records
- **Required:** `Idempotency-Key: <uuid>` header support on all write endpoints — server deduplicates within 24 hours using Redis
- Priority: Must have before production

**Zero Downtime DB Migrations**
- No formal rule on migration strategy — a bad migration can lock tables and take the service down
- **Required:** All migrations must be additive-first (add column → deploy → remove old code → remove column in next deploy). Never drop a column and remove the code using it in the same deploy.
- Priority: Must have from now

**SLA / SLO Definitions**
- No defined uptime target — no way to know if the platform is "good enough"
- **Suggested defaults:**
  - Uptime: 99.9% (43 minutes downtime/month allowed)
  - p95 API response time: < 500ms
  - Error rate: < 0.1%
  - These gate go-live decisions and alert thresholds
- Priority: Must have before any real customer onboarding

---

### DATA ARCHITECTURE GAPS

**PII Data Classification**
- No formal classification of what is PII vs business data
- Affects logging rules, export, retention, erasure obligations
- **Required classification:**
  - PII: email, phone, full_name, IP address, user agent
  - Business data: business_name, GST number, industry (different retention rules)
  - System data: audit log technical fields (no PII rules apply)
- Priority: Must have before any real customer data

**Reversible Migrations**
- Alembic `downgrade()` functions may not all work — not enforced or tested
- **Required:** Every migration `downgrade()` must be implemented and tested in CI
- Priority: Must have from now

**Read Replica**
- All reads and writes hit the same primary DB
- Admin dashboards and audit log queries will degrade registration/login performance as data grows
- **Required:** Set up a read replica in PostgreSQL before any admin dashboard is built. Reports and audit queries route to replica only.
- Priority: Good to have, required before admin dashboard

**Backup Restore Tested**
- Automated backups exist (GCP) but restore has likely never been tested
- **Required:** Monthly restore drill — restore to a test environment, verify data integrity
- "Untested backups are not backups"
- Priority: Must have before production

---

### ASYNC / EVENT ARCHITECTURE GAPS

**Email Sending is Synchronous**
- OTP email is sent inline during the request — if the email provider is slow, the user waits
- **Required:** Move to async — enqueue the send job, return HTTP 202 immediately, worker sends the email
- Redis + Celery already available in docker-compose — just needs wiring
- Priority: Must have before production

**No Event-Driven Architecture**
- Registration completing should trigger downstream actions: welcome email, onboarding task, admin notification
- Currently these would all be synchronous calls in the same request — tight coupling
- **Required:** Registration success fires an event (Redis pub/sub or Celery task). Subscribers handle their own concerns independently.
- Priority: Good to have, required before scaling

**Notification Service**
- Email logic is baked into registration code
- When WhatsApp/SMS OTP is added, it will be duplicated in every flow
- **Required:** Dedicated notification service — registration fires `send_otp` event with `{ channel, destination, code }`, notification service handles delivery
- Priority: Good to have before adding more channels

---

### OBSERVABILITY GAPS

**Distributed Tracing**
- Correlation ID flows through services but no proper trace spans with timing
- Cannot see exactly where time is spent in a slow request (was it CAPTCHA? DB? Email?)
- **Required:** OpenTelemetry instrumentation — auto-instruments FastAPI, SQLAlchemy, httpx. Traces every hop with timing.
- Priority: Good to have, required before production debugging becomes painful

**External Uptime Monitoring**
- Internal `/health` checks only — if the entire service is unreachable from outside, nobody knows
- **Required:** External uptime check (GCP Uptime Checks or UptimeRobot) hitting `/health` from outside every minute
- Priority: Good to have, required before production

**Alert Rules**
- Metrics exist on paper but no alert thresholds defined or configured
- **Required alert rules (minimum):**
  - Error rate > 1% for 5 minutes → page on-call
  - Registration failure rate > 5% → critical alert
  - p95 latency > 2 seconds → warning alert
  - Service health check failing → immediate alert
- Priority: Good to have, required before production

---

### DEVELOPER EXPERIENCE GAPS

**Feature Flags**
- No ability to turn a feature on/off without a deployment
- **Required:** Simple feature flag system — even a `feature_flags` DB table to start. Lets new features be deployed dark and enabled for a % of users.
- Priority: Good to have before scaling

**Environment Parity**
- Dev, staging, prod may diverge in config structure — causes "works on my machine" bugs
- **Required:** All environments use identical config structure. Only values (URLs, secrets) differ. Enforced by a single `config.py` that reads from env vars everywhere.
- Priority: Must have — enforce now

**Runbook / Incident Playbook**
- When production goes down, no documented process for who does what
- **Required:** 1-page runbook per service: how to check logs, how to restart, how to rollback, escalation path
- Priority: Good to have, required before real customers

**Dependency Pinning**
- If `requirements.txt` uses `>=` versions, a package update can silently break the build overnight
- **Required:** All Python dependencies pinned with `==` exact versions. `package-lock.json` committed for frontend.
- Priority: Must have — audit and fix now

---

### GAP STATUS SUMMARY

| Area | Exists | Missing |
|------|--------|---------|
| Rate limiting | ✅ | — |
| Correlation ID | ✅ | — |
| Structured logging | ✅ | — |
| Health checks | ✅ | — |
| Alembic migrations | ✅ | Reversible rule not enforced |
| Redis in infra | ✅ | Not wired for auth/tokens/jobs |
| Circuit breaker | ❌ | Needs Tenacity wiring on CP→Plant |
| Idempotency keys | ❌ | Not implemented anywhere |
| Token revocation | ❌ | No Redis revocation list |
| Field-level PII encryption | ❌ | Plain text in DB |
| Async email / notifications | ❌ | Synchronous inline send |
| Event-driven architecture | ❌ | No pub/sub or task queue wired |
| Feature flags | ❌ | Not implemented |
| Distributed tracing | ❌ | No OpenTelemetry |
| GDPR erasure process | ❌ | No anonymisation process |
| Dependency vuln scanning | ❌ | Not in CI pipeline |
| CSP / security headers | ❌ | Not set |
| SLA / SLO defined | ❌ | No targets defined |
| Read replica | ❌ | Single primary only |
| Backup restore tested | ❓ | Not confirmed |
| Uptime monitoring (external) | ❌ | Not configured |
| Alert rules | ❌ | Not configured |
| Runbook | ❌ | Not written |
| Dependency pinning | ⚠️ | Needs audit |
| PII data classification | ❌ | Not formally done |
| OWASP checklist | ❌ | Not done |

---

## Table of Contents

1. [Observed Symptoms](#1-observed-symptoms)
2. [The Full Registration Flow (as designed)](#2-the-full-registration-flow-as-designed)
3. [Bug Catalogue — All Root Causes](#3-bug-catalogue--all-root-causes)
4. [Why Testing Has Not Caught These for 10 Days](#4-why-testing-has-not-caught-these-for-10-days)
5. [Proposed Fixes — Summary Table](#5-proposed-fixes--summary-table)
6. [Proposed Fix Detail](#6-proposed-fix-detail)
7. [Proposed Test Strategy](#7-proposed-test-strategy)

---

## 1. Observed Symptoms

| # | Symptom | When it occurs |
|---|---------|---------------|
| S1 | `"email is required for OTP flow"` (HTTP 400) | After filling all 12 fields and submitting — OTP step fails immediately |
| S2 | `"CAPTCHA verification failed"` (HTTP 400) | When re-submitting the form (e.g., after a 409 conflict or after a previous attempt) |
| S3 | `"Customer not found"` (HTTP 404) | If Bug 1 is worked around by patching and OTP start proceeds — lookup fails |

---

## 2. The Full Registration Flow (as designed)

```
[User fills 12-field form]
        │
        ▼
 FE: AuthPanel.handleRegisterSubmit()
        │  POST /api/cp/auth/register  { 12 fields + captchaToken }
        ▼
 CP BE: cp_registration.py  →  POST /api/v1/customers  (Plant Gateway)
        │  returns: { registration_id: <customer_uuid>, email, phone, ... }
        ▼
 FE: calls startOtp(reg.registration_id)
        │  POST /api/cp/auth/otp/start  { registration_id: "<uuid>" }
        ▼
 CP BE: cp_otp.py  →  GET /api/v1/customers/lookup?email=...  (Plant Gateway)
        │  returns: { otp_id, channel, destination_masked, otp_code? }
        ▼
 FE: User enters OTP
        │  POST /api/cp/auth/otp/verify  { otp_id, code }
        ▼
 CP BE: cp_otp.py  →  GET /api/v1/customers/lookup?email=...  (Plant Gateway)
        │  creates CP-local user, issues JWT
        ▼
 FE: navigate to /portal
```

---

## 3. Bug Catalogue — All Root Causes

### BUG-1 (CRITICAL): Frontend sends `registration_id` (UUID); backend rejects it — requires `email`

| Attribute | Detail |
|-----------|--------|
| **Severity** | CRITICAL — blocks 100% of registrations at OTP step |
| **File (FE)** | `src/CP/FrontEnd/src/services/otp.service.ts` line 21 |
| **File (BE)** | `src/CP/BackEnd/api/cp_otp.py` lines 185–191 |

**What the frontend sends:**
```typescript
// otp.service.ts — startOtp()
body: JSON.stringify({ registration_id: registrationId })
//  registrationId = reg.registration_id = Plant customer UUID e.g. "cust-abc-123"
```

**What the backend expects:**
```python
# cp_otp.py — start_otp()
if payload.email:
    email = payload.email.strip().lower()
else:
    raise HTTPException(400, "email is required for OTP flow")   # ← always triggered
```

The `registration_id` field is present on the Pydantic model (`OtpStartRequest`) and is read — but only to be stored as a placeholder. If `payload.email` is absent (which it always is from the frontend), the function immediately raises 400 before using `registration_id` at all.

The registration response DOES return `email` (`reg.email`), but `AuthPanel.tsx` line 414 passes `reg.registration_id` (the UUID) to `startOtp()` — not the email.

Same bug affects the **Resend OTP** path: `handleResendRegisterOtp()` line 455 calls `startOtp(registrationId)` where `registrationId` state holds the UUID.

---

### BUG-2 (CRITICAL): CAPTCHA token is not reset after a failed submission

| Attribute | Detail |
|-----------|--------|
| **Severity** | CRITICAL — prevents retry after any error (409 conflict, 4xx, network) |
| **File** | `src/CP/FrontEnd/src/components/auth/AuthPanel.tsx` — `handleRegisterSubmit()` |

Cloudflare Turnstile tokens are **single-use**. After the first call to `/cp/auth/register` — whether it succeeds or fails — the token is consumed by Cloudflare's server when `_verify_turnstile_token()` is called.

**What happens in the catch block:**
```typescript
} catch (e) {
    setRegisterError(e instanceof Error ? e.message : 'Registration failed')
    // ← captchaToken is NOT cleared here
}
```

On re-submit, the widget has not been re-solved, so `captchaToken` still holds the expired/consumed value. The backend receives this stale token, Cloudflare rejects it, and the user sees "CAPTCHA verification failed" — even though the form looks correct.

This also means: a user who gets a 409 (email already registered), corrects their email, and re-submits will always fail on the second attempt.

---

### BUG-3 (HIGH): `_get_customer_from_plant` lookup does not send `X-CP-Registration-Key`

| Attribute | Detail |
|-----------|--------|
| **Severity** | HIGH — causes 404 "Customer not found" even if BUG-1 is fixed |
| **File** | `src/CP/BackEnd/api/cp_otp.py` — `_get_customer_from_plant()` lines 34–59 |

The Plant Gateway's `AuthMiddleware` guards the entire `/api/v1/customers` prefix (including `/api/v1/customers/lookup`) with `X-CP-Registration-Key`. This is the same key requirement that caused the original "Registration validation failed" bug in `cp_registration.py` (fixed in PR #763).

The `_get_customer_from_plant()` function in `cp_otp.py` makes a bare GET request with **no authentication header**:

```python
resp = await client.get(
    f"{base_url}/api/v1/customers/lookup",
    params={"email": email},
)
# ← No X-CP-Registration-Key header
```

Plant Gateway returns 401 → `_get_customer_from_plant` treats `>= 400` as a failure and returns `None` → OTP start returns 404 "Customer not found".

This is the **same class of bug** as the one fixed in PR #763 for `cp_registration.py`. BUG-3 was simply hidden because BUG-1 raises 400 first.

---

### BUG-4 (MEDIUM): `PolicyMiddleware` also guards the lookup endpoint — fixed in PR #763 but deserves note

After PR #763, `PolicyMiddleware` now uses `_is_public_path()` correctly. However, `/api/v1/customers/lookup` is NOT in `PUBLIC_ENDPOINTS` — it is instead guarded by the CP registration key path in `AuthMiddleware`. This is by design and correct, but it means any call to the lookup endpoint without the key will get a 401 — reinforcing the fix needed for BUG-3.

---

### BUG-5 (LOW): `OtpStartRequest` model accepts `registration_id` but the lookup logic silently cannot use it

| Attribute | Detail |
|-----------|--------|
| **Severity** | LOW — misleading API contract; causes confusion in code review |
| **File** | `src/CP/BackEnd/api/cp_otp.py` lines 152–154, 176–179 |

The `OtpStartRequest` model has a `registration_id: str | None` field. The code logic reads it but the comment says:
```python
# Direct lookup by customer_id not available in Plant API,
# so we can't support fetching by ID.
```

There is no `GET /api/v1/customers/{id}` endpoint in Plant Backend — only `GET /api/v1/customers/lookup?email=...`. So even if the frontend sent a valid UUID as `registration_id`, the backend has no way to resolve it to a customer without an email. The field is effectively a dead parameter that invites confusion.

---

## 4. Why Testing Has Not Caught These for 10 Days

This is the structural problem. There are three test layers (FE unit, BE unit, E2E) but they are **decoupled** in a way that lets incompatibilities fall through the cracks.

| Layer | What it tests | What it misses |
|-------|--------------|---------------|
| **FE unit tests** (`AuthModalRegistration.test.tsx`) | Mock the backend API; verify the UI state machine | Never sees a real HTTP 400/401/404 from the backend |
| **BE unit tests** (`test_cp_otp_routes.py`) | Call OTP start **with `email`** directly — the correct path | Never test the path the frontend actually takes: `registration_id`-only |
| **BE registration tests** | Mock `httpx.AsyncClient`; verify Pydantic validation | Never test the actual Plant Gateway call with a real key |
| **E2E tests** | None exist for this flow | The full chain register → OTP start → OTP verify → JWT has never been run end-to-end |

**The critical disconnect:**

`test_cp_otp_routes.py::test_otp_start_requires_email` asserts:
```python
payload = {"channel": "email"}   # ← no email, no registration_id
resp = client.post("/api/cp/auth/otp/start", json=payload)
assert resp.status_code == 400   # ← test passes and is considered "correct"
```

This test documents the backend behaviour correctly. But **no test ever checks what the frontend actually sends** — `{ registration_id: "uuid" }` — which also hits the same 400. The test verifying "no email = 400" accidentally covers up the fact that the frontend never sends an email.

Similarly, `test_otp_verify_creates_user_and_returns_tokens` passes because it patches `_get_customer_from_plant` — so the missing auth header in the real HTTP call is never exercised.

**In summary: every layer is green individually, but the contract between layers is broken.**

---

## 5. Proposed Fixes — Summary Table

| Bug | Root Cause | Fix location | Lines to change |
|-----|-----------|-------------|-----------------|
| BUG-1 | Frontend sends UUID, backend needs email | `otp.service.ts` + `AuthPanel.tsx` | `startOtp()` must accept/send email; `AuthPanel` must pass `reg.email` |
| BUG-2 | CAPTCHA token not cleared after failed submit | `AuthPanel.tsx` — catch block in `handleRegisterSubmit()` | Add `setCaptchaToken(null)` + trigger widget reset in catch |
| BUG-3 | Lookup call missing `X-CP-Registration-Key` header | `cp_otp.py` — `_get_customer_from_plant()` | Pass header just like `_emit_notification_event_best_effort` does |
| BUG-5 | Dead `registration_id` field on `OtpStartRequest` | `cp_otp.py` — `OtpStartRequest` model + `start_otp()` | Remove the field (or deprecate with comment); simplify the code |

---

## 6. Proposed Fix Detail

### Fix for BUG-1

**A. `src/CP/FrontEnd/src/services/otp.service.ts`**

Change `startOtp` signature to accept email instead of (or in addition to) `registrationId`:

```typescript
// BEFORE
export async function startOtp(registrationId: string): Promise<OtpStartResponse> {
  body: JSON.stringify({ registration_id: registrationId })
}

// AFTER
export async function startOtp(email: string): Promise<OtpStartResponse> {
  body: JSON.stringify({ email })
}
```

**B. `src/CP/FrontEnd/src/components/auth/AuthPanel.tsx`**

Line 412–414 — store email from registration response and pass it to `startOtp`:

```typescript
// BEFORE
setRegistrationId(reg.registration_id)
const otpStart = await startOtp(reg.registration_id)

// AFTER
setRegistrationId(reg.registration_id)
setRegistrationEmail(reg.email)          // store email in new state
const otpStart = await startOtp(reg.email)
```

Line 455 — resend OTP also needs email (state variable, not UUID):
```typescript
// BEFORE
const otpStart = await startOtp(registrationId)

// AFTER
const otpStart = await startOtp(registrationEmail)   // use email state
```

A new state variable `registrationEmail: string` needs to be added alongside the existing `registrationId` state.

**C. `src/CP/BackEnd/api/cp_otp.py`** (optional cleanup — BUG-5)

Simplify `OtpStartRequest` and `start_otp()` to remove the dead `registration_id` path:
```python
class OtpStartRequest(BaseModel):
    email: str   # required; previously optional
    channel: Literal["email", "phone"] | None = None
```

---

### Fix for BUG-2

**`src/CP/FrontEnd/src/components/auth/AuthPanel.tsx`** — `handleRegisterSubmit()` catch block:

```typescript
// BEFORE
} catch (e) {
    setRegisterError(e instanceof Error ? e.message : 'Registration failed')
}

// AFTER
} catch (e) {
    setRegisterError(e instanceof Error ? e.message : 'Registration failed')
    setCaptchaToken(null)   // force CAPTCHA widget to reset so user can re-solve
}
```

The Turnstile widget renders with a `onExpire` / `onError` callback already wired to `handleCaptchaError` (which calls `setCaptchaToken(null)`). Setting the token to null in the catch block will cause the widget to show the unsolved state, prompting the user to re-complete it before re-submitting.

---

### Fix for BUG-3

**`src/CP/BackEnd/api/cp_otp.py`** — `_get_customer_from_plant()` function:

```python
# BEFORE
async with httpx.AsyncClient(timeout=10.0) as client:
    resp = await client.get(
        f"{base_url}/api/v1/customers/lookup",
        params={"email": email},
    )

# AFTER
registration_key = (os.getenv("CP_REGISTRATION_KEY") or "").strip()
async with httpx.AsyncClient(timeout=10.0) as client:
    resp = await client.get(
        f"{base_url}/api/v1/customers/lookup",
        params={"email": email},
        headers={"X-CP-Registration-Key": registration_key},
    )
```

This is identical to the pattern already established in `_emit_notification_event_best_effort()` in the same file (line 83) and in `cp_registration.py` (fixed in PR #763).

---

## 7. Proposed Test Strategy

To prevent recurrence, the following tests should be added alongside the code fixes:

### New BE tests (pytest, Docker)

| Test | File | What it covers |
|------|------|---------------|
| `test_otp_start_with_registration_id_fails` | `test_cp_otp_routes.py` | Asserts 400 when `registration_id` UUID sent without email — makes the contract explicit |
| `test_otp_start_with_email_succeeds` | `test_cp_otp_routes.py` | Happy path: send `{ email }` → 200. Already passes but naming makes contract explicit |
| `test_get_customer_from_plant_sends_registration_key` | `test_cp_otp_routes.py` | Assert `X-CP-Registration-Key` header is present in the GET lookup call |

### New FE tests (Vitest)

| Test | File | What it covers |
|------|------|---------------|
| `startOtp sends email not registration_id` | `otp.service.test.ts` | Assert `body` contains `{ email }` not `{ registration_id }` |
| `captcha token is cleared after failed registration` | `AuthModalRegistration.test.tsx` | After a mocked 409 response, assert CAPTCHA widget is in unsolved state |
| `resend OTP uses email not UUID` | `AuthModalRegistration.test.tsx` | Assert resend call also passes email |

### E2E contract test (new file)

An integration test that runs against the live-but-mocked stack to verify the full chain:
```
POST /api/cp/auth/register → 201
  → POST /api/cp/auth/otp/start { email: reg.email } → 200
    → POST /api/cp/auth/otp/verify { otp_id, code } → 200 + { access_token }
```

This should be the **mandatory smoke test** that CI runs on every PR touching `cp_registration.py`, `cp_otp.py`, or `otp.service.ts`.

---

## Log Evidence

### GCP Cloud Logging
`gcloud` CLI is not installed in the devcontainer and no service-account credentials are present in the environment (verified: `which gcloud` → not found; `cat .env | grep gcp` → empty). Direct log queries against project `waooaw-oauth` / region `asia-south1` are not possible without credentials.

### Firebase Test Lab (Feb 20 2026 — `tmp/ftl/results/`)

The FTL run (APK built 02-20 00:51) predates the registration flow reaching the API. The app crashed inside the React renderer before any screen rendered:

```
# tmp/ftl/results/logcat (verbatim)
02-20 00:51:19.755  ReactNativeJS: [API Config] Using EXPO_PUBLIC_API_URL for demo: https://cp.demo.waooaw.com
02-20 00:51:19.772  ReactNativeJS: [Sentry] Initialized successfully (production)
02-20 00:51:19.991  E ReactNativeJS: [Error: Incompatible React versions: react: 19.2.4 vs react-native-renderer: 19.1.0]
```

Zero HTTP calls to `https://cp.demo.waooaw.com` appear in the 3.1 MB logcat for this run. The CP registration API was never reached so the FTL run cannot confirm or refute BUG-1/2/3 — those bugs sit behind the React crash.

**Implication**: A new FTL run is needed after Bug 1 (React version) and Bug 2 (PolicyMiddleware PR #763) are both deployed to produce log evidence for the OTP layer.

### CI Log (Feb 15 2026 — `tmp/ci-22035889335-failed.log`)

The CI log is a **Plant backend** test run dated Feb 15. Relevant extract:

```
tests/unit/test_security.py::TestJWTTokens::test_create_access_token_returns_string  PASSED [86%]
tests/unit/test_security.py::TestJWTTokens::test_verify_token_succeeds_for_valid_token  PASSED [87%]
tests/unit/test_security.py::TestJWTTokens::test_verify_token_fails_for_invalid_token  PASSED [87%]
tests/unit/test_auth_validate.py::test_auth_validate_missing_token_audits_failure  PASSED [27%]
tests/unit/test_auth_validate.py::test_auth_validate_invalid_token_audits_failure  PASSED [28%]
```

JWT token generation and verification are fully working — the "Policy middleware requires JWT claims" error is not a JWT library problem. Confirmed by code: the bug was in `policy.py` skip-list omitting mobile/CP public paths (fixed in PR #763).

CI failures in the log are in `test_agent_mold_enforcement_api.py`, `test_deliverables_simple_api.py`, `test_goal_scheduler_simple_api.py` — unrelated to registration.

### Summary

| Claim | Evidence type | Confirmed? |
|-------|--------------|------------|
| App crashed before any registration API call | FTL logcat timestamp `00:51:19.991` | ✅ Yes |
| API URL is `https://cp.demo.waooaw.com` | FTL logcat `[API Config]` line | ✅ Yes |
| JWT library code is not the bug | CI log — all JWT unit tests PASSED | ✅ Yes |
| BUG-1: FE sends UUID not email | Code trace `otp.service.ts:startOtp` + `AuthPanel.tsx:412` | ✅ Code-confirmed |
| BUG-2: CAPTCHA not cleared on error | Code trace `AuthPanel.tsx` catch block | ✅ Code-confirmed |
| BUG-3: Missing auth header in OTP lookup | Code trace `cp_otp.py:_get_customer_from_plant()` | ✅ Code-confirmed |
| BUG-1/2/3 visible in logs | Requires new FTL run post-React-fix | ❌ Not yet — crash precedes them |

---

*Awaiting approval before any code changes are made.*
