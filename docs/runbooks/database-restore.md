# Runbook: Database Restore (GCP Cloud SQL)

**Iteration:** 6 — Compliance (E3-S1)  
**Last tested:** See monthly backup test results (`.github/workflows/monthly-backup-test.yml`)  
**Estimated restore time:** ~15–30 minutes to a test instance; ~45–60 minutes to production

---

## Overview

WAOOAW's primary database is a GCP Cloud SQL PostgreSQL instance.
Cloud SQL takes automated backups daily (retained for 7 days) plus on-demand backups.
This runbook covers restoring from backup to a test environment and, if necessary, promoting to production.

---

## Prerequisites

- GCP CLI (`gcloud`) authenticated with a service account that has `roles/cloudsql.admin`
- Target project set: `gcloud config set project waooaw-demo` (or `waooaw-prod`)
- Know the primary instance name (from GCP console or Terraform output):
  - Staging: `waooaw-plant-db-staging`
  - Production: `waooaw-plant-db-prod`

---

## Step 1 — Find the Latest Backup

```bash
# List available automated backups for the instance
gcloud sql backups list \
  --instance=waooaw-plant-db-prod \
  --project=waooaw-prod \
  --filter="status=SUCCESSFUL" \
  --sort-by="~windowStartTime" \
  --limit=10
```

Note the `id` field (e.g. `1704067200000`) of the backup you want to restore.

---

## Step 2 — Restore to a Test Instance

**Never restore directly to production.** Always restore to a test instance first
to verify data integrity.

```bash
# 1. Create a temporary test instance
gcloud sql instances create test-restore-$(date +%Y%m) \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=asia-south1 \
  --project=waooaw-prod

# 2. Restore the backup to the test instance
gcloud sql backups restore BACKUP_ID \
  --restore-instance=test-restore-$(date +%Y%m) \
  --backup-instance=waooaw-plant-db-prod \
  --project=waooaw-prod

# Wait for the operation to complete (~10–15 min)
# Monitor: gcloud sql operations list --instance=test-restore-$(date +%Y%m)
```

---

## Step 3 — Verify Data Integrity

Connect to the test instance and run verification queries:

```bash
# Get connection name
gcloud sql instances describe test-restore-$(date +%Y%m) \
  --format="value(connectionName)"

# Connect via Cloud SQL Auth Proxy (recommended)
cloud_sql_proxy -instances=CONNECTION_NAME=tcp:5433 &
psql "host=127.0.0.1 port=5433 dbname=waooaw user=plant_app sslmode=require" \
  -f - <<'SQL'
-- Row count verification
SELECT 'customers' AS tbl, COUNT(*) AS rows FROM customer_entity
UNION ALL
SELECT 'audit_logs', COUNT(*) FROM audit_logs
UNION ALL
SELECT 'otp_sessions', COUNT(*) FROM otp_sessions;

-- Check most recent customer registration
SELECT MAX(created_at) AS latest_registration FROM customer_entity;

-- Check most recent audit event
SELECT MAX(timestamp) AS latest_audit_event FROM audit_logs;
SQL
```

Expected minimums (update these as the platform grows):

| Table | Minimum row count |
|-------|------------------|
| `customer_entity` | > 0 |
| `audit_logs` | > 0 |

If row counts are zero or timestamps are unexpectedly old, the backup may be corrupted or from the wrong window — choose an earlier backup and repeat.

---

## Step 4 — Verify Application Starts Against Test Instance

```bash
# Temporarily point the Plant backend at the test instance
# (do this in staging only — never in production config files)
export DATABASE_URL="postgresql://plant_app:PASSWORD@127.0.0.1:5433/waooaw"

cd src/Plant/BackEnd
python -c "
import asyncio
from core.database import _connector
from sqlalchemy import text

async def check():
    async with _connector.get_session() as s:
        result = await s.execute(text('SELECT COUNT(*) FROM customer_entity'))
        print('Customers:', result.scalar())

asyncio.run(check())
"
```

---

## Step 5 — Promote to Production (emergency only)

Only proceed if you have confirmed:
- ✅ Test restore verified (Step 3 passed)
- ✅ Data loss window is acceptable (backup timestamp vs current time)
- ✅ Engineering lead approval obtained

```bash
# Stop all write traffic first (scale down Cloud Run services)
gcloud run services update waooaw-plant-backend \
  --min-instances=0 --max-instances=0 \
  --region=asia-south1 --project=waooaw-prod

# Restore backup directly to production instance
gcloud sql backups restore BACKUP_ID \
  --restore-instance=waooaw-plant-db-prod \
  --backup-instance=waooaw-plant-db-prod \
  --project=waooaw-prod

# Wait for operation completion
gcloud sql operations list --instance=waooaw-plant-db-prod --project=waooaw-prod

# Restore traffic
gcloud run services update waooaw-plant-backend \
  --min-instances=1 --max-instances=10 \
  --region=asia-south1 --project=waooaw-prod
```

---

## Step 6 — Clean Up Test Instance

```bash
gcloud sql instances delete test-restore-$(date +%Y%m) \
  --project=waooaw-prod \
  --quiet
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Restore operation fails immediately | Backup instance and restore instance must both exist | Ensure test instance created before restoring |
| Row counts are unexpectedly low | Wrong backup selected | Choose an earlier backup from Step 1 |
| Application can't connect after restore | Database user password not preserved | Reset password: `gcloud sql users set-password plant_app ...` |
| Restore takes > 30 min | Large database size | Normal — monitor with `gcloud sql operations list` |

---

## Escalation

If this runbook fails at any step and production is down:

1. Immediately page the on-call engineer (see `docs/runbooks/plant-backend.md` escalation section)
2. Do not attempt further restore steps without a second engineer present
3. Document every command run and its output for the post-incident review
