# Iteration 6 — Compliance

**When:** Before real customer data enters the system  
**Branch naming:** `feat/compliance-it6`  
**Testing:** `docker compose -f docker-compose.local.yml` — no virtual env, no local Python  
**Status:** 🟢 Done

---

## Tracking Table

| # | Epic | Story | Status | PR |
|---|------|-------|--------|----|
| E1-S1 | PII Classification | Formal PII data classification register | 🟢 Done | — |
| E1-S2 | PII Classification | No PII in logs — masking enforced | 🟢 Done | — |
| E2-S1 | GDPR Erasure | Customer erasure API endpoint | 🟢 Done | — |
| E2-S2 | GDPR Erasure | Anonymise PII across all tables | 🟢 Done | — |
| E2-S3 | GDPR Erasure | Audit log of erasure requests | 🟢 Done | — |
| E3-S1 | Backup | Backup restore drill procedure documented | 🟢 Done | — |
| E3-S2 | Backup | Monthly restore test automated | 🟢 Done | — |
| E4-S1 | OWASP | OWASP Top 10 checklist completed | 🟢 Done | — |
| E4-S2 | Security Scan | Dependency vulnerability scanning in CI | 🟢 Done | — |
| E5-S1 | Pen Test | OWASP ZAP automated scan executed | 🟢 Done | — |

**Story Status Key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done

---

## Epic 1 — PII Data Classification

**Goal:** Every field in the database is formally classified. This drives logging rules, retention periods, erasure obligations, and encryption prioritisation.

---

### E1-S1 — Formal PII data classification register

**Story:**  
As the platform, every data field we store is classified so we know our obligations for each piece of data — what we can log, how long we keep it, and what we must erase on request.

**Acceptance Criteria:**
- Data classification register created in `docs/CP/data-classification.md`
- Every column in `customers`, `audit_logs`, `otp_sessions` classified as one of:
  - **PII** — directly identifies a person (email, phone, full_name, ip_address, user_agent)
  - **Business data** — company info, not personal (business_name, gst_number, industry, website)
  - **System data** — technical metadata (id, created_at, timestamps, status codes)
- Retention periods defined per class:
  - PII: retained while account active + 1 year after deletion
  - Business data: retained while account active + 3 years (legal/audit requirements)
  - System data: 2 years
- Classification register reviewed and agreed before storing real customer data

**Technical Implementation Notes:**
- Document only — no code change
- File: `docs/CP/data-classification.md`
- Must list every table and every column

**Test Cases:**
```
TC-E1-S1-1: data-classification.md exists with all tables and columns classified
TC-E1-S1-2: No column is unclassified (no blanks in the register)
TC-E1-S1-3: Retention periods defined for each class
```

**Status:** 🟢 Done

---

### E1-S2 — No PII in logs — masking enforced

**Story:**  
As the platform, when structured logs are written, PII fields are automatically masked so a developer reading logs or a log aggregation tool never sees real email addresses or phone numbers.

**Acceptance Criteria:**
- Email in logs: masked to `u***@domain.com` format (preserve domain for debugging)
- Phone in logs: masked to `+91******7890` (first 3 + last 4 digits visible)
- Full name in logs: masked to initials only `J.D.`
- IP address in logs: last octet masked `192.168.1.XXX`
- OTP codes: NEVER logged under any circumstances — any log containing a raw OTP is a bug
- Masking applied at the log formatter level — not ad-hoc per log line
- Unit tests verify masking functions produce correct output

**Technical Implementation Notes:**
- File: `src/Plant/BackEnd/core/logging.py` — add `mask_pii(value, field_type)` functions
- Custom log formatter: override `format()` to scan log record for known PII keys and mask
- Known PII keys to scan: `email`, `phone`, `full_name`, `ip_address`, `ip`, `user_agent`
- Also apply to `src/CP/BackEnd/core/logging.py`
- Test: ensure existing log statements that include `email` now output masked value

**Test Cases:**
```
TC-E1-S2-1: mask_email("user@example.com") → "u***@example.com"
TC-E1-S2-2: mask_phone("+919876543210") → "+91*****3210"
TC-E1-S2-3: Log a registration event with email field
  → docker compose logs plant-backend | grep "@" → masked value only
TC-E1-S2-4: grep codebase for raw OTP logging
  → No log statement logs the otp_code value
```

**Status:** 🟢 Done

---

## Epic 2 — GDPR Right to Erasure

**Goal:** When a customer requests deletion of their data (GDPR "right to be forgotten"), we can fulfill it — anonymising PII across all tables while preserving record structure for audit integrity.

**Context:**  
Hard deletion is not acceptable — it orphans audit logs and breaks referential integrity. Instead, PII is replaced with `[REDACTED]` markers. The customer record still exists as a structure, but nothing in it can identify the person.

---

### E2-S1 — Customer erasure API endpoint

**Story:**  
As an admin, I can submit a data erasure request for a customer by customer_id, and the system anonymises all PII associated with that customer across all tables.

**Acceptance Criteria:**
- `DELETE /api/v1/customers/{customer_id}/erase` — admin JWT required
- Accepts optional `reason` in request body (for audit purposes)
- Triggers erasure process (E2-S2) synchronously — returns 200 when complete
- Returns 404 if customer not found
- Returns 409 if customer already erased
- The endpoint itself is audited (creates an audit log entry — using a system account)

**Technical Implementation Notes:**
- File: `src/Plant/BackEnd/api/v1/customers.py` — add new route
- Require admin role: `Depends(require_admin_role)`
- Call `CustomerService.erase(customer_id, reason, erased_by)` — new service method (E2-S2)
- `erased_by`: admin user ID from JWT claims

**Test Cases:**
```
TC-E2-S1-1: DELETE /api/v1/customers/{id}/erase with admin JWT
  → HTTP 200
  → Customer PII anonymised

TC-E2-S1-2: DELETE with non-admin JWT → HTTP 403
TC-E2-S1-3: DELETE with unknown customer_id → HTTP 404
TC-E2-S1-4: DELETE same customer twice → HTTP 409 with code: CUSTOMER_ALREADY_ERASED
```

**Status:** 🟢 Done

---

### E2-S2 — Anonymise PII across all tables

**Story:**  
As the erasure process, when triggered for a customer, I replace all PII in all tables with `[REDACTED]` values so the customer is no longer identifiable while record structure is preserved.

**Acceptance Criteria:**
- `customers` table: `email` → `redacted_{id}@erased.invalid`, `phone` → `REDACTED`, `full_name` → `REDACTED`, `business_address` → `REDACTED`
- `audit_logs` table: `email` → `REDACTED` for all rows matching the customer's email
- `otp_sessions` table: delete any unexpired OTP records for this email (OTPs are temporary — safe to delete)
- `customers.deleted_at` set to `NOW()`
- All changes in a single DB transaction — atomically all succeed or all roll back
- After erasure: `GET /api/v1/customers/{id}` returns 404

**Technical Implementation Notes:**
- `CustomerService.erase(customer_id, reason, erased_by)` — new method
- Use `UPDATE customers SET email='redacted_X@erased.invalid', phone='REDACTED', full_name='REDACTED', deleted_at=NOW() WHERE id = ?`
- Use `UPDATE audit_logs SET email='REDACTED' WHERE email = ?`
- All in one `async with db.begin():` transaction block
- `email = f"redacted_{customer_id}@erased.invalid"` — unique, queryable, clearly marked

**Test Cases:**
```
TC-E2-S2-1: Trigger erasure for a customer with audit log history
  → customers.email = "redacted_{id}@erased.invalid"
  → customers.full_name = "REDACTED"
  → audit_logs rows for that email: email = "REDACTED"
  → customers.deleted_at is set

TC-E2-S2-2: Erasure process fails mid-way (mock DB error on audit_logs update)
  → Transaction rolls back
  → customers table unchanged
  → No partial erasure

TC-E2-S2-3: GET /api/v1/customers/{id} after erasure
  → HTTP 404

TC-E2-S2-4: OTP records for erased email
  → Deleted
```

**Status:** 🟢 Done

---

### E2-S3 — Audit log of erasure requests

**Story:**  
As a compliance officer, every erasure request is itself recorded so we can demonstrate GDPR compliance — when it was requested, by whom, and that it was completed.

**Acceptance Criteria:**
- Before erasure executes: audit event written — `{ screen: "admin", action: "erasure_requested", outcome: "success", metadata: { customer_id, reason, requested_by } }`
- After erasure completes: audit event — `{ screen: "admin", action: "erasure_complete", outcome: "success", metadata: { customer_id } }`
- These audit events use `[SYSTEM]` as email (no PII now) and the admin's user_id as `user_id`
- Erasure audit events are in a separate protected table or flagged — they must NEVER be themselves erasable

**Technical Implementation Notes:**
- Write audit events via `AuditClient` (Iteration 2) before and after erasure
- Erasure audit events: `outcome="success"` both times (if the process fails, exception propagates — no "failure" audit written, the transaction rollback is the record)

**Test Cases:**
```
TC-E2-S3-1: Trigger erasure — inspect audit_logs
  → Two records: erasure_requested + erasure_complete
  → Both have admin user_id and no PII email

TC-E2-S3-2: Attempt to erase the erasure audit records
  → Not possible via any API endpoint (no general-purpose delete on audit_logs)
```

**Status:** 🟢 Done

---

## Epic 3 — Backup & Restore

---

### E3-S1 — Backup restore drill procedure documented

**Story:**  
As any team member facing a production incident, I can follow a documented procedure to restore the database from backup without needing tribal knowledge.

**Acceptance Criteria:**
- `docs/runbooks/database-restore.md` created with step-by-step restore procedure
- Covers: how to find the latest backup, how to restore to a test environment, how to verify data integrity, how to promote to production if needed
- Estimated time to restore documented
- Tested by someone who did not write it (follows the doc blindly and it works)

**Technical Implementation Notes:**
- GCP Cloud SQL automated backups — document how to find them in console
- Restore command: `gcloud sql backups restore ...`
- Verification: row count checks on key tables after restore

**Test Cases:**
```
TC-E3-S1-1: New team member follows the runbook
  → Successfully restores to test environment in < 30 minutes with no outside help
TC-E3-S1-2: runbook exists at docs/runbooks/database-restore.md
```

**Status:** 🟢 Done

---

### E3-S2 — Monthly restore test automated

**Story:**  
As the platform, database backups are verified monthly by actually restoring them, so we know they work before we need them in an emergency.

**Acceptance Criteria:**
- GitHub Actions scheduled workflow runs on the 1st of every month
- Workflow: restore latest backup to a temporary test Cloud SQL instance → run row count verification queries → report result → delete test instance
- Result posted to team Slack channel or email
- Workflow config committed to `.github/workflows/monthly-backup-test.yml`

**Technical Implementation Notes:**
- GCP service account with `cloudsql.admin` role for the workflow
- Test instance: `test-restore-YYYYMM` — created, tested, deleted in one workflow run
- Verification queries: `SELECT COUNT(*) FROM customers`, `SELECT COUNT(*) FROM audit_logs` — compare to expected minimums

**Test Cases:**
```
TC-E3-S2-1: Trigger workflow manually → completes without error → test instance deleted
TC-E3-S2-2: Workflow fails (backup corrupt) → notification sent, test instance cleaned up
TC-E3-S2-3: monthly-backup-test.yml exists in .github/workflows/
```

**Status:** 🟢 Done

---

## Epic 4 — OWASP & Dependency Scanning

---

### E4-S1 — OWASP Top 10 checklist completed

**Story:**  
As the platform, we have formally assessed and addressed each of the OWASP Top 10 vulnerabilities before real customers use the system.

**Acceptance Criteria:**
- `docs/security/owasp-checklist.md` created
- Each OWASP Top 10 item assessed: vulnerable / mitigated / not applicable
- Every "vulnerable" item has a linked issue in the backlog
- All critical items (Injection, Broken Auth, Sensitive Data Exposure) marked mitigated with evidence

**OWASP Top 10 Assessment (2021):**

| # | Risk | Status | Evidence |
|---|------|--------|---------|
| A01 | Broken Access Control | To assess | — |
| A02 | Cryptographic Failures | To assess | — |
| A03 | Injection | To assess | SQLAlchemy ORM (likely mitigated) |
| A04 | Insecure Design | To assess | — |
| A05 | Security Misconfiguration | To assess | — |
| A06 | Vulnerable Components | To assess | Dependency scanning (E4-S2) |
| A07 | Auth Failures | To assess | JWT + revocation (Iteration 1) |
| A08 | Data Integrity Failures | To assess | — |
| A09 | Logging Failures | To assess | PII masking (E1-S2) |
| A10 | SSRF | To assess | — |

**Test Cases:**
```
TC-E4-S1-1: owasp-checklist.md exists with all 10 items assessed
TC-E4-S1-2: No item left as "To assess" — every item has a status
TC-E4-S1-3: All "vulnerable" items have a linked backlog issue
```

**Status:** 🟢 Done

---

### E4-S2 — Dependency vulnerability scanning in CI

**Story:**  
As the CI pipeline, every PR automatically scans Python and npm dependencies for known CVEs and fails the build if any critical vulnerability is found.

**Acceptance Criteria:**
- `pip-audit` added to Plant and CP backend CI jobs — runs on every PR
- `npm audit` added to CP frontend CI job — runs on every PR
- Build fails if critical (`--severity critical`) vulnerabilities found
- Warnings for high severity — does not fail build but is reported
- Results visible in GitHub PR checks

**Technical Implementation Notes:**
- File: `.github/workflows/backend-ci.yml` — add step: `pip-audit -r requirements.txt --severity critical`
- File: `.github/workflows/frontend-ci.yml` — add step: `npm audit --audit-level=critical`
- `pip-audit` installed via: `pip install pip-audit`
- Ignore known false positives with `pip-audit --ignore-vuln GHSA-...` (only after review)

**Test Cases:**
```
TC-E4-S2-1: PR with a known vulnerable package
  → CI fails with vulnerability report

TC-E4-S2-2: PR with no vulnerabilities
  → CI passes

TC-E4-S2-3: pip-audit step visible in GitHub Actions workflow output
```

**Status:** 🟢 Done

---

## Epic 5 — Penetration Testing

---

### E5-S1 — OWASP ZAP automated scan executed

**Story:**  
As the platform, before real customers onboard, an automated security scan has been run against the staging environment and all findings addressed or acknowledged.

**Acceptance Criteria:**
- OWASP ZAP baseline scan run against `https://cp.demo.waooaw.com` (staging CP frontend) and `https://plant.demo.waooaw.com/api` (Plant API)
- Scan report saved to `docs/security/zap-scan-YYYY-MM.html`
- All HIGH and CRITICAL findings either fixed or have documented risk acceptance
- Medium findings triaged — at least acknowledged in a backlog issue
- ZAP scan added as optional CI step (manual trigger, not on every PR)

**Technical Implementation Notes:**
- OWASP ZAP Docker image: `ghcr.io/zaproxy/zaproxy:stable`
- Run: `docker run -t ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t https://cp.demo.waooaw.com -r /zap/wrk/report.html`
- Mount volume to capture report
- GitHub Actions workflow: `.github/workflows/security-scan.yml` — manual trigger only (`workflow_dispatch`)

**Test Cases:**
```
TC-E5-S1-1: ZAP scan completes without crashing
TC-E5-S1-2: Report generated and saved to docs/security/
TC-E5-S1-3: All HIGH findings have either a fix PR or a documented risk acceptance
```

**Status:** 🟢 Done

---

## Epic Completion — Docker Integration Test

```bash
# Start all services
docker compose -f docker-compose.local.yml up -d

# Run all tests
docker compose -f docker-compose.local.yml run --rm --no-deps plant-backend pytest tests/ -x -q
docker compose -f docker-compose.local.yml run --rm --no-deps cp-backend pytest tests/ -x -q

# Test PII masking in logs
docker compose -f docker-compose.local.yml run --rm plant-backend python -c "
from core.logging import mask_email, mask_phone
assert mask_email('user@example.com') == 'u***@example.com'
assert mask_phone('+919876543210') == '+91*****3210'
print('PII masking: PASS')
"

# Test erasure endpoint (requires admin token)
# 1. Create a test customer
# 2. Call DELETE /api/v1/customers/{id}/erase with admin token
# 3. Verify PII replaced in DB
docker compose -f docker-compose.local.yml exec db psql -U waooaw -c "SELECT email, full_name FROM customers WHERE email LIKE 'redacted_%';"

# Dependency scan
docker compose -f docker-compose.local.yml run --rm --no-deps plant-backend pip-audit -r requirements.txt
docker compose -f docker-compose.local.yml run --rm --no-deps cp-frontend npm audit

# Verify health/ready checks DB and Redis connections
curl http://localhost:8000/health/ready
```

All tests pass. PII masking verified. Erasure creates REDACTED records. Dependency scan clean.
