# Runbook: Plant Worker (Celery)

## Service: plant-worker (Cloud Run Jobs: `waooaw-plant-worker`)
## On-call contact: platform-team@waooaw.io | #incidents Slack channel
## Iteration added: 7 (E5-S2 Scale Prep)

---

## Ownership

| Role | Contact |
|------|---------|
| Primary on-call | Rotate (PagerDuty: `waooaw-platform`) |
| Escalation | Engineering Lead — `#escalations` Slack |

---

## Service Overview

Plant Worker runs all async background tasks via **Celery + Redis broker**.

**Queues**:
- `email` — OTP + welcome email sending
- `events` — Customer registration domain events
- `archival` — Monthly audit log archival + daily OTP cleanup (E4-S1/E4-S2 Iteration 7)

**Beat Scheduler** (single instance — `waooaw-plant-worker-beat`):
- Monthly: `archive_audit_logs` (1st of month 02:00 UTC)
- Daily: `cleanup_otp_sessions` (03:00 UTC)

---

## Check Health

```bash
# Check worker is running and responding to ping
celery -A worker.celery_app inspect ping

# Check queue depths (requires Redis CLI access)
redis-cli -h <MEMORYSTORE_IP> llen celery:email
redis-cli -h <MEMORYSTORE_IP> llen celery:events
redis-cli -h <MEMORYSTORE_IP> llen celery:archival

# Check active tasks
celery -A worker.celery_app inspect active

# Check reserved tasks (queued but not started)
celery -A worker.celery_app inspect reserved
```

---

## View Logs

```bash
# All worker logs
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="waooaw-plant-worker" AND severity>=WARNING' \
  --limit=100

# Failed tasks
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="waooaw-plant-worker" AND jsonPayload.message:"MaxRetriesExceededError"' \
  --limit=50

# Archival job results
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="waooaw-plant-worker" AND jsonPayload.message:"archive_audit_logs"' \
  --limit=20
```

---

## Common Failures

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Emails not sending | SMTP credentials wrong / email provider down | Check `SENDGRID_API_KEY` / `SES_SMTP_*` env vars |
| OTP emails delayed > 5 min | Email queue backlog | Check queue depth; scale up worker instances |
| `archive_audit_logs` not running | Celery Beat not deployed or crashed | Check beat scheduler logs; restart beat service |
| Archive job failing with GCS error | `AUDIT_ARCHIVE_BUCKET` wrong / ADC missing | Verify bucket exists; check worker service account permissions |
| `cleanup_otp_sessions` stuck | Long-running transaction / DB lock | Check `pg_stat_activity` on DB for blocking queries |
| `CELERY_BROKER_URL` connection refused | Redis down or wrong URL | Check Memorystore health; verify env var |
| Tasks retrying forever | Max retries = 3 so they stop after 3 attempts | Check DLQ; root cause in logs |

---

## Manually Trigger a Task (Emergency)

```bash
# Run OTP cleanup right now (skip waiting for scheduled cron)
celery -A worker.celery_app call cleanup_otp_sessions

# Run audit log archival right now
celery -A worker.celery_app call archive_audit_logs

# Purge a specific queue (destructive — tasks are lost)
celery -A worker.celery_app purge -Q archival
```

---

## Restart Worker

```bash
# Graceful restart (deploy new revision)
gcloud run services update waooaw-plant-worker --region=asia-south1

# Beat scheduler restart
gcloud run services update waooaw-plant-worker-beat --region=asia-south1
```

---

## Rollback

```bash
# List revisions for worker
gcloud run revisions list --service=waooaw-plant-worker --region=asia-south1

# Roll back worker
gcloud run services update-traffic waooaw-plant-worker \
  --to-revisions=waooaw-plant-worker-XXXXXXXX-xxx=100 \
  --region=asia-south1
```

---

## Escalation Path

1. **0–15 min**: On-call engineer checks queue depth and error logs.
2. **15 min**: If email queue is backed up, verify SMTP provider status page.
3. **15 min**: If archival failing, check GCS bucket + IAM permissions.
4. **30 min**: Restart worker service; escalate to Engineering Lead if not resolved.
