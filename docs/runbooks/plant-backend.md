# Runbook: Plant Backend

## Service: plant-backend (Cloud Run: `waooaw-plant`)
## On-call contact: platform-team@waooaw.io | #incidents Slack channel
## Iteration added: 7 (E5-S2 Scale Prep)

---

## Ownership

| Role | Contact |
|------|---------|
| Primary on-call | Rotate (PagerDuty schedule: `waooaw-platform`) |
| Escalation | Engineering Lead — `#escalations` Slack |
| DBA contact | `#database` Slack channel |

---

## Service Overview

Plant Backend is the **authoritative data service** for WAOOAW. All customer PII, agent data, billing records, and audit logs live here. CP and PP are thin proxies that call Plant via the gateway.

- **Port**: 8000
- **Health endpoint**: `GET /health`
- **Metrics**: Cloud Monitoring (GCP) — namespace `waooaw/plant`
- **Logs**: Cloud Logging — `resource.labels.service_name="waooaw-plant"`
- **Database**: Cloud SQL PostgreSQL — instance `waooaw-plant-db`
- **Redis**: Memorystore — `waooaw-redis`

---

## Check Health

```bash
# Cloud Run health
gcloud run services describe waooaw-plant --region=asia-south1 --format="value(status.conditions)"

# HTTP health check
curl -sf https://plant.waooaw.io/health | jq .

# Database connectivity
gcloud sql connect waooaw-plant-db --user=plant
# Then: SELECT count(*) FROM customer_entity;

# Redis connectivity
redis-cli -h <MEMORYSTORE_IP> ping
```

---

## View Logs

```bash
# Last 100 error log lines
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="waooaw-plant" AND severity>=ERROR' \
  --limit=100 --format="table(timestamp, jsonPayload.message)"

# Specific request by correlation ID
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="waooaw-plant" AND jsonPayload.correlation_id="<ID>"' \
  --limit=50

# Slow queries (> 5 seconds)
gcloud logging read \
  'resource.type="cloud_sql_database" AND jsonPayload.duration>5000' \
  --limit=50
```

---

## Common Failures

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| 500 on all endpoints | DB connection pool exhausted | Restart service; check `database_pool_size` config |
| 500 on `/api/v1/customers` | PostgreSQL down or unreachable | Check Cloud SQL health; verify network routes |
| Slow GET endpoints | Read replica lagging or down | Check `READ_REPLICA_URL` env var; failover to primary |
| 401 on all JWT-protected endpoints | `JWT_SECRET` rotation mid-flight | Verify `JWT_SECRET` in Secret Manager matches deployed version |
| Redis errors in logs | Memorystore unreachable | Verify VPC peering; restart Plant service to reset pool |
| OOM kill (exit 137) | Memory leak under load | Scale up Cloud Run memory; check open DB connections |
| Feature flags always returning false | `feature_flags` table empty | Run seed script or insert flags via `/api/v1/feature-flags` |
| `cryptography` errors in logs | `ENCRYPTION_KEY` wrong length | Regenerate with `python -c "import secrets; print(secrets.token_hex(32))"` |

---

## Restart Service

```bash
# Graceful restart (deploy latest revision)
gcloud run services update waooaw-plant --region=asia-south1

# Force new revision (triggers cold start on all instances)
gcloud run deploy waooaw-plant \
  --image gcr.io/waooaw-prod/plant-backend:latest \
  --region=asia-south1
```

---

## Rollback a Bad Deployment

```bash
# List recent revisions
gcloud run revisions list --service=waooaw-plant --region=asia-south1

# Route 100% traffic to previous revision
gcloud run services update-traffic waooaw-plant \
  --to-revisions=waooaw-plant-XXXXXXXX-xxx=100 \
  --region=asia-south1
```

---

## Database — Emergency Queries

```bash
# Count pending un-archived audit logs
SELECT count(*) FROM audit_logs WHERE timestamp < NOW() - INTERVAL '2 years';

# Check for locked queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query, state
FROM pg_stat_activity
WHERE state = 'active' AND now() - pg_stat_activity.query_start > INTERVAL '30 seconds';

# Kill a stuck query (get pid from above)
SELECT pg_terminate_backend(<pid>);

# Check replication lag on read replica
SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()))::int AS lag_seconds;
```

---

## Escalation Path

1. **0–15 min**: On-call engineer works the runbook above.
2. **15–30 min**: If unresolved, post in `#incidents` Slack. Tag Engineering Lead.
3. **30+ min**: Rollback to last known good revision. Page DBA if DB is involved.
4. **60+ min**: Declare incident in status page. Consider failover region.
