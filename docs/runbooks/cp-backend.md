# Runbook: CP Backend

## Service: cp-backend (Cloud Run: `waooaw-cp`)
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

CP Backend is the **Customer Portal thin proxy**. It authenticates customers (Google OAuth / OTP), forwards most requests to Plant Gateway, and owns CP-specific features (feature flags, registration flow).

- **Port**: 8080
- **Health endpoint**: `GET /health`
- **Logs**: Cloud Logging — `resource.labels.service_name="waooaw-cp"`
- **Upstream**: Plant Gateway at `PLANT_GATEWAY_URL`
- **No direct DB access** (except auth sessions via Plant)

---

## Check Health

```bash
# Cloud Run health
gcloud run services describe waooaw-cp --region=asia-south1 \
  --format="value(status.conditions)"

# HTTP health check
curl -sf https://cp.waooaw.io/health | jq .

# Verify Plant Gateway reachability from CP
gcloud run services logs read waooaw-cp --limit=20 | grep PLANT_GATEWAY
```

---

## View Logs

```bash
# Recent errors
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="waooaw-cp" AND severity>=ERROR' \
  --limit=100

# Auth failures (sign-in issues)
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="waooaw-cp" AND jsonPayload.path="/api/auth/google"' \
  --limit=50
```

---

## Common Failures

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| All proxy requests returning 502 | `PLANT_GATEWAY_URL` wrong / Plant down | Verify env var; check Plant backend runbook |
| Google OAuth sign-in failing | `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` wrong | Re-verify in GCP Console; check Secret Manager |
| Feature flags always empty | Plant Feature Flags API unreachable | Check Plant health; `GET /api/v1/feature-flags` on Plant |
| 401 on all authenticated endpoints | `JWT_SECRET` mismatch between CP and Plant | Verify both services use the same `JWT_SECRET` from Secret Manager |
| OTP emails not arriving | Celery email task queue backed up | Check Plant worker runbook |
| CORS errors in browser | `CORS_ORIGINS` missing the frontend domain | Add domain to `CORS_ORIGINS` env var and redeploy |
| High latency (> 3s) on all requests | Plant backend slow | Check Plant backend runbook |

---

## Restart Service

```bash
gcloud run services update waooaw-cp --region=asia-south1
```

---

## Rollback

```bash
# List revisions
gcloud run revisions list --service=waooaw-cp --region=asia-south1

# Roll back
gcloud run services update-traffic waooaw-cp \
  --to-revisions=waooaw-cp-XXXXXXXX-xxx=100 \
  --region=asia-south1
```

---

## Escalation Path

1. **0–15 min**: On-call engineer works the runbook above.
2. **15 min**: Check Plant backend first — CP failures are often upstream Plant issues.
3. **30 min**: If CP-specific, rollback to last known good revision.
4. **30+ min**: Page Engineering Lead via `#incidents` Slack.
