# Iteration 7 — Scale Preparation

**When:** Before growth / scaling beyond initial launch  
**Branch naming:** `feat/scale-prep-it7`  
**Testing:** `docker compose -f docker-compose.local.yml` — no virtual env, no local Python  
**Status:** 🔴 Not Started

---

## Tracking Table

| # | Epic | Story | Status | PR |
|---|------|-------|--------|----|
| E1-S1 | Read Replica | PostgreSQL read replica configured | 🔴 Not Started | — |
| E1-S2 | Read Replica | Audit log queries routed to replica | 🔴 Not Started | — |
| E2-S1 | Feature Flags | Feature flag table and service | 🔴 Not Started | — |
| E2-S2 | Feature Flags | Feature flag check in CP frontend | 🔴 Not Started | — |
| E3-S1 | PII Encryption | Field-level encryption for PII columns | 🔴 Not Started | — |
| E4-S1 | Data Archival | Audit log archival job | 🔴 Not Started | — |
| E4-S2 | Data Archival | OTP session cleanup job | 🔴 Not Started | — |
| E5-S1 | Dependency Pinning | Audit and pin all dependencies | 🔴 Not Started | — |
| E5-S2 | Runbook | Per-service incident runbooks | 🔴 Not Started | — |

**Story Status Key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done

---

## Epic 1 — Read Replica

**Goal:** All reporting, admin dashboard queries, and audit log reads are routed to a PostgreSQL read replica — never to the primary DB. This ensures customer-facing traffic (registration, login) is never degraded by heavy read queries.

---

### E1-S1 — PostgreSQL read replica configured

**Story:**  
As the platform, there is a PostgreSQL read replica that receives all writes from the primary in real-time, so read-heavy operations can be offloaded without impacting primary DB performance.

**Acceptance Criteria:**
- GCP Cloud SQL read replica created for the primary instance
- Replica lag: < 1 second under normal load
- Replica is read-only — any write attempt returns an error
- `READ_REPLICA_URL` env var configured in all backend services
- Plant backend has two SQLAlchemy sessions: `get_db_session()` (primary — for writes) and `get_read_db_session()` (replica — for reads)
- Replica configuration committed to `cloud/terraform/` as Terraform resource

**Technical Implementation Notes:**
- GCP Cloud SQL: replica created via `gcloud sql instances create ... --master-instance-name=...`
- Or Terraform: `google_sql_database_instance` with `master_instance_name` set
- `src/Plant/BackEnd/core/database.py` — add `read_engine` using `READ_REPLICA_URL` env var
- `get_read_db_session()` dependency — used in query-only endpoints
- SQLAlchemy: `create_async_engine(READ_REPLICA_URL)` — separate pool from primary

**Test Cases:**
```
TC-E1-S1-1: Write a record via primary, read from replica within 1 second
  → Record visible on replica

TC-E1-S1-2: Attempt a write via read replica session
  → Error returned: "cannot execute INSERT in a read-only transaction"

TC-E1-S1-3: READ_REPLICA_URL env var missing — service starts with warning, falls back to primary
  → Service starts (no crash), logs warning about missing replica URL

TC-E1-S1-4: Replica lag test — write 1000 records rapidly, check replica
  → All 1000 visible on replica within 2 seconds
```

**Status:** 🔴 Not Started

---

### E1-S2 — Audit log queries routed to replica

**Story:**  
As the admin using the audit log query API, my queries run against the read replica so they never impact the performance of customer-facing registration and login flows.

**Acceptance Criteria:**
- `GET /api/v1/audit/events` uses `get_read_db_session()` — not the primary
- All other read-only list/get endpoints (`GET /api/v1/customers`, `GET /api/v1/customers/lookup`) use read replica
- Write endpoints (`POST /api/v1/customers`, `POST /api/v1/audit/events`) continue to use primary
- Developer documentation comment on each endpoint specifies which session it uses

**Technical Implementation Notes:**
- In `src/Plant/BackEnd/api/v1/audit.py`: `GET` route uses `Depends(get_read_db_session)`
- In `src/Plant/BackEnd/api/v1/customers.py`: `GET /lookup` uses `Depends(get_read_db_session)`
- Pattern: `POST` = primary, `GET` = replica (with rare exceptions documented)

**Test Cases:**
```
TC-E1-S2-1: GET /api/v1/audit/events — verify DB connection goes to replica
  → Log shows connection to READ_REPLICA_URL host (not primary)

TC-E1-S2-2: POST /api/v1/audit/events — verify DB connection goes to primary
  → Log shows connection to primary host

TC-E1-S2-3: Heavy GET /api/v1/audit/events query (10k results)
  → Does not increase latency on POST /api/v1/customers (primary unaffected)
```

**Status:** 🔴 Not Started

---

## Epic 2 — Feature Flags

**Goal:** New features can be deployed to production in a "dark" state and enabled for a percentage of customers without a new deployment. This enables safe gradual rollouts and instant killswitches.

---

### E2-S1 — Feature flag table and service

**Story:**  
As any backend service, I can check whether a feature is enabled for a given customer or globally, so features can be toggled without deployment.

**Acceptance Criteria:**
- `feature_flags` table in PostgreSQL:
  - `key` text PRIMARY KEY (e.g. `new_dashboard_v2`, `otp_via_whatsapp`)
  - `enabled` boolean default false
  - `rollout_percentage` integer 0-100 (100 = everyone, 0 = nobody)
  - `enabled_for_customer_ids` UUID[] nullable (specific customers only)
  - `description` text
  - `updated_at` timestamptz
- `FeatureFlagService.is_enabled(key: str, customer_id: UUID = None) -> bool`
  - Returns true if `enabled=true` AND (`rollout_percentage=100` OR customer in `enabled_for_customer_ids` OR hash(customer_id) % 100 < rollout_percentage)
- Flags cached in Redis for 60 seconds — not fetched from DB on every request
- `GET /api/v1/feature-flags` — admin JWT required — returns all flags and their states

**Technical Implementation Notes:**
- Migration: `src/Plant/BackEnd/database/migrations/versions/017_feature_flags.py`
- Service: `src/Plant/BackEnd/services/feature_flag_service.py`
- Redis cache key: `feature_flag:{key}` TTL=60
- Hash-based rollout: `int(hashlib.md5(str(customer_id).encode()).hexdigest(), 16) % 100 < rollout_percentage`

**Test Cases:**
```
TC-E2-S1-1: Flag enabled=true, rollout_percentage=100
  → is_enabled returns true for all customers

TC-E2-S1-2: Flag enabled=true, rollout_percentage=0
  → is_enabled returns false for all customers

TC-E2-S1-3: Flag enabled=true, enabled_for_customer_ids=[specific_id]
  → is_enabled(specific_id) returns true
  → is_enabled(other_id) returns false

TC-E2-S1-4: Flag checked 100 times — DB queried only once (Redis cache hit)
  → DB query count = 1
  → Redis cache hit count = 99

TC-E2-S1-5: Redis unavailable — is_enabled falls back to DB query
  → Still works, warning logged
```

**Status:** 🔴 Not Started

---

### E2-S2 — Feature flag check in CP frontend

**Story:**  
As the CP frontend, I can check feature flags returned from the backend to conditionally show or hide UI features, enabling dark deployments of new screens.

**Acceptance Criteria:**
- `GET /api/cp/feature-flags` endpoint on CP backend — proxies to Plant's feature flags endpoint
- Returns flags relevant to CP (not all flags — filtered by `scope: "cp"`)
- CP frontend fetches flags on app load and stores in React context
- Components use `useFeatureFlag("flag_key")` hook to conditionally render
- Flag changes take effect within 60 seconds (cache TTL) without page reload

**Technical Implementation Notes:**
- File: `src/CP/FrontEnd/src/contexts/FeatureFlagContext.tsx` — new file
- File: `src/CP/FrontEnd/src/hooks/useFeatureFlag.ts` — new file
- Fetch flags once on app startup, store in context
- Re-fetch every 60 seconds (polling — acceptable until WebSocket push is built)

**Test Cases:**
```
TC-E2-S2-1: Flag enabled=false — useFeatureFlag("flag_key") returns false
  → Component not rendered

TC-E2-S2-2: Flag enabled=true — useFeatureFlag("flag_key") returns true
  → Component rendered

TC-E2-S2-3: Change flag in DB — within 60 seconds frontend reflects the change
  → Component appears/disappears without deployment

TC-E2-S2-4: Feature flags endpoint unavailable — app loads normally
  → All flags default to false (safe default — nothing unexpected shown)
```

**Status:** 🔴 Not Started

---

## Epic 3 — Field-Level PII Encryption

**Goal:** PII columns in PostgreSQL are encrypted at the field level. Raw database access (e.g., a compromised DBA account or DB backup theft) cannot read customer email, phone, or name in plain text.

---

### E3-S1 — Field-level encryption for PII columns

**Story:**  
As the platform, even if the PostgreSQL database files are directly accessed, PII fields are not readable without the application encryption key.

**Acceptance Criteria:**
- Columns encrypted: `customers.email`, `customers.phone`, `customers.full_name`
- Encryption algorithm: AES-256-GCM
- Encryption key stored in GCP Secret Manager — not in env file
- Encryption/decryption transparent to application code — handled in model layer
- Existing data migrated (re-encrypted) in a single migration with no downtime
- `email` index maintained — use deterministic encryption (HMAC of email) as the index value, not the ciphertext
- Performance impact < 5ms per record read

**Technical Implementation Notes:**
- Library: `cryptography` (already in Python ecosystem)
- `src/Plant/BackEnd/core/encryption.py` — `encrypt(plaintext, key)` and `decrypt(ciphertext, key)` functions
- SQLAlchemy TypeDecorator: `EncryptedString` — auto-encrypts on `process_bind_param`, decrypts on `process_result_value`
- Index: `customers.email_hash` column — `HMAC-SHA256(email, index_key)` — used for lookup queries (constant-time compare)
- Migration: `018_encrypt_pii_columns.py` — add ciphertext columns, populate, drop plaintext columns
- Zero-downtime migration: deploy code that writes both columns → populate ciphertext → deploy code that reads only ciphertext → drop plaintext

**Test Cases:**
```
TC-E3-S1-1: Save a customer — inspect raw DB value for email column
  → Not a readable email address (ciphertext)

TC-E3-S1-2: Read customer via API
  → Email returned correctly decrypted

TC-E3-S1-3: Lookup customer by email
  → email_hash index used for lookup, correct customer returned

TC-E3-S1-4: Change encryption key (key rotation)
  → Re-encrypt migration runs
  → Old ciphertext unreadable with new key (key rotation works)

TC-E3-S1-5: Performance test — read 1000 customers
  → p95 read time increase < 5ms vs unencrypted
```

**Status:** 🔴 Not Started

---

## Epic 4 — Data Archival & Cleanup Jobs

**Goal:** Audit logs and OTP records don't grow forever. Scheduled jobs purge or archive data according to the retention policy defined in Iteration 6.

---

### E4-S1 — Audit log archival job

**Story:**  
As the platform, audit log records older than 2 years are automatically archived to cold storage (GCP Cloud Storage) and removed from the primary DB, so the table doesn't grow unboundedly.

**Acceptance Criteria:**
- Celery Beat scheduled task runs monthly: `archive_old_audit_logs`
- Selects all `audit_logs` records where `timestamp < NOW() - INTERVAL '2 years'`
- Exports selected records to GCP Cloud Storage as JSON Lines file: `gs://waooaw-audit-archive/YYYY-MM/audit_logs.jsonl`
- Deletes exported records from DB (hard delete acceptable here — they're archived)
- Job is idempotent — running twice doesn't create duplicate archive files or double-delete
- Job logs how many records were archived

**Technical Implementation Notes:**
- Celery Beat schedule: `celery_app.conf.beat_schedule = { "archive-audit-logs": { "task": "archive_audit_logs", "schedule": crontab(day_of_month=1, hour=2) } }`
- GCS upload: `google-cloud-storage` library, batch export in chunks of 10000 rows
- File naming: `gs://waooaw-audit-archive/{YYYY}/{MM}/audit_logs_{timestamp}.jsonl`
- Idempotency: check if archive file already exists before exporting

**Test Cases:**
```
TC-E4-S1-1: Insert 100 audit records with timestamp 3 years ago — run job
  → 100 records exported to GCS
  → 100 records deleted from audit_logs table
  → Records from last 2 years untouched

TC-E4-S1-2: Run job twice for same month
  → Second run skips (file already exists)
  → No duplicate archive file
  → No double deletion

TC-E4-S1-3: Job log shows: "Archived 100 records to gs://..."
```

**Status:** 🔴 Not Started

---

### E4-S2 — OTP session cleanup job

**Story:**  
As the platform, expired and verified OTP sessions are automatically purged from the database so the `otp_sessions` table stays lean even at scale.

**Acceptance Criteria:**
- Celery Beat scheduled task runs daily: `cleanup_otp_sessions`
- Deletes records where `expires_at < NOW()` (expired, never used)
- Deletes records where `verified_at IS NOT NULL AND verified_at < NOW() - INTERVAL '30 days'` (verified, old)
- Hard delete acceptable — OTP records have no long-term audit value
- Job is idempotent
- Job logs count of deleted records

**Technical Implementation Notes:**
- Schedule: daily at 3am UTC: `crontab(hour=3, minute=0)`
- Single SQL: `DELETE FROM otp_sessions WHERE expires_at < NOW() OR (verified_at IS NOT NULL AND verified_at < NOW() - INTERVAL '30 days')`

**Test Cases:**
```
TC-E4-S2-1: Insert 50 expired OTP records — run job
  → All 50 deleted
  → Active/unexpired records untouched

TC-E4-S2-2: Insert 20 verified records older than 30 days — run job
  → All 20 deleted

TC-E4-S2-3: Job log shows: "Cleaned up 70 OTP sessions"
```

**Status:** 🔴 Not Started

---

## Epic 5 — Dependency Pinning & Runbooks

---

### E5-S1 — Audit and pin all dependencies

**Story:**  
As the platform, every Python and npm dependency is pinned to an exact version so builds are reproducible and a package author's surprise update cannot break production overnight.

**Acceptance Criteria:**
- All `requirements.txt` files use `==` exact versions (not `>=` or `~=`)
- `package-lock.json` committed and up to date (not in `.gitignore`)
- CI fails if `requirements.txt` contains any non-pinned version specifier
- Dependabot or Renovate configured to create PRs for dependency updates (not auto-merge)
- Audit existing files — replace all `>=` with current installed version

**Technical Implementation Notes:**
- Run: `pip freeze > requirements.txt` in each backend container to capture exact versions
- Check: `grep -E "[>~^<]=" requirements.txt` — must return nothing
- Dependabot config: `.github/dependabot.yml` — `package-ecosystem: pip` and `npm`

**Test Cases:**
```
TC-E5-S1-1: grep ">=\|~=\|^=" requirements.txt → empty (no unpinned versions)
TC-E5-S1-2: PR with a >= version specifier → CI fails with "unpinned dependency" error
TC-E5-S1-3: package-lock.json exists and is not in .gitignore
TC-E5-S1-4: .github/dependabot.yml exists with pip and npm configured
```

**Status:** 🔴 Not Started

---

### E5-S2 — Per-service incident runbooks

**Story:**  
As any team member responding to a production incident, I can follow a runbook for the affected service to diagnose and resolve it without needing to call the original developer.

**Acceptance Criteria:**
- Runbook created for each service: `docs/runbooks/plant-backend.md`, `docs/runbooks/cp-backend.md`, `docs/runbooks/plant-worker.md`
- Each runbook covers:
  - How to check service health and logs
  - Common failure modes and their fixes
  - How to restart the service safely
  - How to roll back a bad deployment
  - Escalation contacts
- Runbooks reviewed and approved by someone who did not write them

**Runbook template for each service:**
```markdown
## Service: {service-name}
## On-call contact: {name/email}

### Check Health
docker exec {container} curl localhost:{port}/health

### View Logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name={service}"

### Common Failures
| Symptom | Cause | Fix |
|---------|-------|-----|
| 500 errors on all requests | DB connection exhausted | Restart service, check pool config |
| Slow responses | Redis unavailable | Check Redis health, restart if needed |

### Restart Service
gcloud run services update {service} --region={region}

### Rollback
gcloud run services update-traffic {service} --to-revisions={prev-revision}=100

### Escalation
If not resolved in 30 minutes: contact {escalation-contact}
```

**Test Cases:**
```
TC-E5-S2-1: 3 runbook files exist in docs/runbooks/
TC-E5-S2-2: New team member uses runbook to diagnose a simulated incident
  → Resolves within 30 minutes without outside help
TC-E5-S2-3: Each runbook has health check, log view, restart, rollback, and escalation sections
```

**Status:** 🔴 Not Started

---

## Epic Completion — Docker Integration Test

```bash
# Start all services
docker compose -f docker-compose.local.yml up -d

# Full test suite
docker compose -f docker-compose.local.yml run --rm --no-deps plant-backend pytest tests/ -x -q
docker compose -f docker-compose.local.yml run --rm --no-deps cp-backend pytest tests/ -x -q

# TypeScript check
docker compose -f docker-compose.local.yml run --rm --no-deps cp-frontend npx tsc --noEmit

# Test feature flags
docker compose -f docker-compose.local.yml exec db psql -U waooaw -c \
  "INSERT INTO feature_flags (key, enabled, rollout_percentage, description) VALUES ('test_flag', true, 100, 'test');"
curl http://localhost:8020/api/cp/feature-flags
# → Should include test_flag: true

# Test dependency pinning
docker compose -f docker-compose.local.yml run --rm plant-backend grep -E ">=|~=" requirements.txt
# → Should return nothing (no unpinned deps)

# Test OTP cleanup job (manual trigger)
docker compose -f docker-compose.local.yml run --rm plant-worker \
  celery -A worker.celery_app call worker.tasks.cleanup_otp_sessions

# Verify migration
docker compose -f docker-compose.local.yml run --rm plant-backend alembic current
# → Should show 017_feature_flags + 018_encrypt_pii (head)
```

All tests pass. Feature flags work end-to-end. PII encrypted at rest. Dependency pinning verified. Runbooks present.
