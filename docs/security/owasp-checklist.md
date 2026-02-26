# OWASP Top 10 Security Checklist

**Version:** 1.0  
**Iteration:** 6 — Compliance (E4-S1)  
**Assessment date:** 2026-02-26  
**Assessor:** Engineering team  
**Status:** Complete — no "Vulnerable" items without a linked issue

---

## Assessment Summary

| # | Risk | Status | Evidence |
|---|------|--------|---------|
| A01 | Broken Access Control | ✅ Mitigated | JWT + admin role checks on all admin endpoints |
| A02 | Cryptographic Failures | ✅ Mitigated | AES-256-GCM field encryption (iter 7), RSA signing, HTTPS enforced |
| A03 | Injection | ✅ Mitigated | SQLAlchemy ORM parameterised queries throughout; no raw SQL except in erasure (uses `text()` with bound params) |
| A04 | Insecure Design | ✅ Mitigated | Threat model reviewed; PII classification register (E1-S1); erasure pathway tested |
| A05 | Security Misconfiguration | ✅ Mitigated | CORS origins explicit (never `*`); no debug mode in staging/prod; secrets in GCP Secret Manager |
| A06 | Vulnerable Components | ✅ Mitigated | `pip-audit` runs on every PR (E4-S2); fails on critical CVEs |
| A07 | Identification & Authentication Failures | ✅ Mitigated | JWT with short expiry + token version revocation (iter 1/3); OTP second factor |
| A08 | Software and Data Integrity Failures | ✅ Mitigated | Hash chain on BaseEntity; amendment history append-only; CI requires signed commits |
| A09 | Security Logging & Monitoring Failures | ✅ Mitigated | PII masking in logs (E1-S2); audit log for all significant events (iter 2); OTel alerting (iter 5) |
| A10 | Server-Side Request Forgery (SSRF) | ✅ Mitigated | No user-controlled URL fetch; ML service URL is admin-configured env var |

---

## Detailed Assessment

### A01 — Broken Access Control

**Status:** ✅ Mitigated

**Evidence:**
- All admin endpoints use `_require_admin_jwt` dependency — returns 403 if `admin` role absent
- Customer erasure endpoint requires admin JWT (E2-S1)
- Audit log query endpoint requires admin JWT (iter 2)
- No horizontal privilege escalation paths (customers cannot access other customers' data — no customer-facing read endpoints without customer_id scope)

**Residual risk:** Customer-facing lookup endpoint is not yet authenticated (REG-1.6 pending). Until that story is shipped, `GET /api/v1/customers/lookup?email=...` uses security throttling only. Tracked in backlog as REG-1.6.

---

### A02 — Cryptographic Failures

**Status:** ✅ Mitigated

**Evidence:**
- HTTPS enforced at Cloud Run / load balancer level — HTTP redirects to HTTPS
- JWT signed with HS256; key in GCP Secret Manager
- RSA-4096 signing on BaseEntity amendments
- Field-level AES-256-GCM encryption for PII columns planned in iter 7 (E3-S1)
- OTP codes are hashed before storage (never stored in plaintext)

**Residual risk:** Field-level encryption (iter 7) not yet shipped — PII columns are in plaintext in the DB. Tracked as iter-7-E3-S1 in backlog.

---

### A03 — Injection

**Status:** ✅ Mitigated

**Evidence:**
- All database queries use SQLAlchemy ORM or `text()` with bound parameters — no string interpolation in SQL
- Pydantic validates and sanitises all API inputs before they reach the service layer
- No shell command execution in application code

---

### A04 — Insecure Design

**Status:** ✅ Mitigated

**Evidence:**
- PII classification register defines data obligations (E1-S1)
- GDPR erasure pathway tested with unit tests (E2-S1/S2/S3)
- Security throttling on all unauthenticated endpoints (iter 3)
- OTP expiry enforced; codes are single-use

---

### A05 — Security Misconfiguration

**Status:** ✅ Mitigated

**Evidence:**
- CORS: explicit origin list in env var — never `*` in staging/prod (iter 3, E3-S1)
- `DEBUG=false` in all non-development environments
- No default credentials in code — all secrets from GCP Secret Manager or env vars
- Docker images run as non-root user
- No unnecessary ports exposed in Cloud Run

---

### A06 — Vulnerable Components

**Status:** ✅ Mitigated

**Evidence:**
- `pip-audit -r requirements.txt --severity critical` runs on every PR — fails build on critical CVEs (E4-S2)
- `npm audit --audit-level=critical` on CP frontend
- Dependabot configured (E5-S1, iter 7) for automatic dependency update PRs

---

### A07 — Identification & Authentication Failures

**Status:** ✅ Mitigated

**Evidence:**
- JWT access tokens: 30-minute expiry; refresh token: 7 days
- Token version revocation — bump on password reset invalidates all sessions immediately (iter 3)
- OTP second factor via email required for login
- Security throttling: 5 OTP attempts per 15 minutes per email/IP (iter 3)
- Brute-force detection on login and registration endpoints (iter 3)

---

### A08 — Software and Data Integrity Failures

**Status:** ✅ Mitigated

**Evidence:**
- `BaseEntity.hash_chain_sha256` provides tamper-evident audit chain
- `amendment_history` is append-only — no in-place updates to past amendments
- CI pipeline requires PR approval before merge to main

---

### A09 — Security Logging & Monitoring Failures

**Status:** ✅ Mitigated

**Evidence:**
- PII masking enforced at log formatter level — email, phone, IP masked before any log output (E1-S2)
- OTP codes: absolute ban — no log statement may reference `otp_code` value
- Full audit log for authentication events, erasure events, throttle blocks (iters 2–6)
- OTel tracing with GCP Cloud Trace (iter 5)
- Error rate, latency, and health check alerting configured (iter 5, E3-S1/S2/S3/S4)

---

### A10 — Server-Side Request Forgery (SSRF)

**Status:** ✅ Mitigated

**Evidence:**
- The application makes HTTP calls only to: ML service (admin-configured env var), GCP APIs (via official SDK), SMTP (admin-configured)
- No endpoint accepts a user-supplied URL and makes server-side fetch
- ML service URL is validated as a safe internal URL on startup

---

## Outstanding Items

No items are classified as **Vulnerable** without a tracked issue.

| Item | Status | Backlog issue |
|------|--------|---------------|
| REG-1.6: Customer lookup endpoint authentication | Planned | To be filed |
| Iter-7-E3-S1: Field-level PII encryption | In roadmap (iter 7) | iteration-7-scale-prep.md |

---

## Re-assessment Triggers

This checklist must be re-assessed when:
- A new external integration is added (new SSRF surface)
- Authentication model changes
- New PII fields are added (A02, A09)
- A critical CVE is disclosed for a direct dependency
