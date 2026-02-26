# Iteration 5 — Observability

**When:** Before production  
**Branch naming:** `feat/observability-it5`  
**Testing:** `docker compose -f docker-compose.local.yml` — no virtual env, no local Python  
**Status:** 🔴 Not Started

---

## Tracking Table

| # | Epic | Story | Status | PR |
|---|------|-------|--------|----|
| E1-S1 | Tracing | OpenTelemetry SDK in Plant and CP backends | 🔴 Not Started | — |
| E1-S2 | Tracing | Trace spans for DB queries and external HTTP calls | 🔴 Not Started | — |
| E1-S3 | Tracing | Trace exporter to GCP Cloud Trace | 🔴 Not Started | — |
| E2-S1 | Uptime | External uptime check on /health endpoints | 🔴 Not Started | — |
| E3-S1 | Alerts | Error rate alert rule | 🔴 Not Started | — |
| E3-S2 | Alerts | Latency alert rule | 🔴 Not Started | — |
| E3-S3 | Alerts | Registration failure rate alert | 🔴 Not Started | — |
| E3-S4 | Alerts | Health check failing alert | 🔴 Not Started | — |

**Story Status Key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done

---

## Epic 1 — Distributed Tracing (OpenTelemetry)

**Goal:** Every request that flows through CP frontend → CP backend → Plant → DB produces a trace with timing at each hop. When a request is slow or fails in production, the trace shows exactly where time was spent.

**Context:**  
Correlation ID already exists (Iteration 3 confirmed). OpenTelemetry (OTel) builds on this — it auto-instruments FastAPI, SQLAlchemy, and httpx. Traces are sent to GCP Cloud Trace (free tier, available in GCP project).

---

### E1-S1 — OpenTelemetry SDK in Plant and CP backends

**Story:**  
As any backend service, I automatically produce trace spans for every HTTP request I receive and every outgoing HTTP call I make, with no manual instrumentation needed.

**Acceptance Criteria:**
- `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi`, `opentelemetry-instrumentation-httpx`, `opentelemetry-instrumentation-sqlalchemy` added to `requirements.txt` for both backends
- OTel SDK initialised at app startup — before any middleware or route is registered
- Every incoming HTTP request produces a trace span with: method, path, status code, duration
- Every outgoing httpx call (CP→Plant, Plant→external APIs) produces a child span
- Every SQLAlchemy query produces a child span with query text (sanitised — no parameter values)
- Trace ID matches the `X-Correlation-ID` header (or propagates it as W3C `traceparent`)

**Technical Implementation Notes:**
- `src/Plant/BackEnd/core/observability.py` — check if this already exists (seen in file list) — extend it
- `src/CP/BackEnd/core/observability.py` — new file or extend
- Initialise: `FastAPIInstrumentor.instrument_app(app)`, `SQLAlchemyInstrumentor().instrument()`, `HTTPXClientInstrumentor().instrument()`
- Propagator: W3C TraceContext (`TraceContextTextMapPropagator`) — reads/writes `traceparent` header
- `SERVICE_NAME` env var used as OTel service name: `plant-backend`, `cp-backend`

**Test Cases:**
```
TC-E1-S1-1: Make any API request — check OTel exporter receives a span
  → Span contains http.method, http.url, http.status_code

TC-E1-S1-2: CP backend call to Plant — check parent/child span relationship
  → CP backend span is parent
  → Plant backend span is child with same trace_id

TC-E1-S1-3: DB query span visible
  → Span with db.system=postgresql and db.statement present

TC-E1-S1-4: traceparent header present in CP→Plant HTTP calls
  → Plant backend span continues the same trace
```

**Status:** 🔴 Not Started

---

### E1-S2 — Trace spans for DB queries and external HTTP calls

**Story:**  
As a developer investigating a slow registration, I can see in the trace exactly how long the DB query took, how long CAPTCHA verification took, and how long the Plant API call took.

**Acceptance Criteria:**
- All DB queries produce spans with duration (auto-instrumented by SQLAlchemy instrumentor)
- All outgoing HTTP calls (Cloudflare CAPTCHA, Plant API, email provider) produce spans with URL and status code
- Span names are meaningful: `POST /api/v1/customers`, `GET customers.get_by_email`, etc.
- Sensitive data never in span attributes: no email addresses, no OTP codes, no tokens

**Technical Implementation Notes:**
- Auto-instrumentation handles most of this — manual spans only needed for business logic boundaries
- Add manual span for CAPTCHA verification: `with tracer.start_as_current_span("captcha.verify") as span: ...`
- Sanitise: review auto-instrumented span attributes, add `SpanProcessor` to strip PII if auto-captured

**Test Cases:**
```
TC-E1-S2-1: Trigger a registration — inspect trace
  → Spans present for: captcha verify, Plant API call, DB insert
  → Each span has start time and duration

TC-E1-S2-2: Slow DB query (artificially introduce delay)
  → Trace shows DB span with high duration
  → HTTP span duration reflects the DB slowness

TC-E1-S2-3: grep span attributes for email/otp/token values
  → Not found in any span attributes
```

**Status:** 🔴 Not Started

---

### E1-S3 — Trace exporter to GCP Cloud Trace

**Story:**  
As a developer, I can view traces in GCP Cloud Trace console — searchable by trace ID, time range, service, and latency — so production issues can be investigated without log diving.

**Acceptance Criteria:**
- `opentelemetry-exporter-gcp-trace` added to requirements
- Traces exported to GCP Cloud Trace in staging and production
- In local dev: traces exported to console (`ConsoleSpanExporter`) — no GCP needed
- `OTEL_EXPORTER` env var: `gcp` (staging/prod), `console` (local)
- Trace sampling: 100% in staging, 10% in production (configurable via `OTEL_SAMPLING_RATE`)
- Traces visible in GCP Cloud Trace for registration flow within 30 seconds of request

**Technical Implementation Notes:**
- `GCloudSpanExporter` from `opentelemetry-exporter-gcp-trace`
- Switch based on `OTEL_EXPORTER` env var in `observability.py`
- GCP auth: uses Application Default Credentials — already in GCP-deployed containers
- Sampling: `ParentBasedTraceIdRatio(sample_rate)` sampler

**Test Cases:**
```
TC-E1-S3-1: Local dev — complete registration
  → Console logs show span data for the request

TC-E1-S3-2: Staging — complete registration, wait 30 seconds
  → GCP Cloud Trace shows trace with all spans

TC-E1-S3-3: OTEL_EXPORTER=console in docker-compose.local.yml
  → No GCP calls made locally (no auth required)
```

**Status:** 🔴 Not Started

---

## Epic 2 — External Uptime Monitoring

**Goal:** An external service checks the platform health from outside every minute. If the platform is unreachable from the internet, the team is alerted within 1 minute — not when a customer reports it.

---

### E2-S1 — External uptime check on /health endpoints

**Story:**  
As the platform team, we know within 1 minute if any service is unreachable from the internet, not when a customer tells us.

**Acceptance Criteria:**
- GCP Uptime Check configured for: `plant-backend /health`, `cp-backend /health`
- Check frequency: every 1 minute
- Check from multiple regions: at least 2 GCP regions
- Alert fires if 2 consecutive checks fail (2 minutes downtime)
- Alert notification: email + (optionally) PagerDuty/Slack webhook
- Uptime check configuration committed to `cloud/monitoring/uptime-checks/`

**Technical Implementation Notes:**
- GCP Console: Monitoring → Uptime Checks → Create
- Or Terraform: `google_monitoring_uptime_check_config` resource in `cloud/terraform/`
- `GET /health` must return `200 OK` with `{"status": "ok"}` — no auth required
- Alert policy: `google_monitoring_alert_policy` — condition: uptime check failed for > 2 minutes

**Test Cases:**
```
TC-E2-S1-1: Manually stop plant-backend container
  → Alert email received within 2 minutes

TC-E2-S1-2: Restart plant-backend
  → Alert resolves/clears

TC-E2-S1-3: Uptime check config exists in cloud/monitoring/
TC-E2-S1-4: Health check returns 200 with {"status": "ok"} without any auth
```

**Status:** 🔴 Not Started

---

## Epic 3 — Alert Rules

**Goal:** Automated alerts for the 4 most critical conditions: high error rate, high latency, registration failures, and health check down. The team is notified before customers start complaining.

---

### E3-S1 — Error rate alert rule

**Story:**  
As the on-call team, I am paged within 5 minutes if our API error rate exceeds 1%, so I can investigate before it affects all customers.

**Acceptance Criteria:**
- Alert fires when error rate (5xx responses / total responses) > 1% for 5 consecutive minutes
- Alert severity: CRITICAL
- Notification: email to on-call
- Alert policy committed to `cloud/monitoring/alert-policies/error-rate.yaml`

**Technical Implementation Notes:**
- GCP Monitoring alerting policy on `logging/user/request_count` metric filtered to `status >= 500`
- Condition: ratio metric, threshold 0.01, duration 5 minutes

**Test Cases:**
```
TC-E3-S1-1: Trigger 20+ 500 errors in 1 minute
  → Alert fires within 6 minutes
TC-E3-S1-2: Error rate drops below 1%
  → Alert resolves
```

**Status:** 🔴 Not Started

---

### E3-S2 — Latency alert rule

**Story:**  
As the on-call team, I am notified if p95 API latency exceeds 2 seconds, indicating DB slowness, memory pressure, or a service degradation.

**Acceptance Criteria:**
- Alert fires when p95 latency > 2000ms sustained for 5 minutes
- Alert severity: WARNING
- Notification: email (not page — latency warnings are not wake-you-up events)

**Technical Implementation Notes:**
- GCP Monitoring alerting policy on request latency distribution metric
- p95 condition: 95th percentile > 2000ms for 5 minutes

**Test Cases:**
```
TC-E3-S2-1: Introduce artificial delay (sleep 3s in a route)
  → Alert fires within 6 minutes
TC-E3-S2-2: Remove delay
  → Alert resolves
```

**Status:** 🔴 Not Started

---

### E3-S3 — Registration failure rate alert

**Story:**  
As the platform team, I am alerted if more than 5% of registration attempts fail, so registration bugs in production are caught immediately.

**Acceptance Criteria:**
- Alert fires when `registration_complete` audit events < 95% of `registration_started` audit events over a 10-minute window
- Alert severity: CRITICAL
- Notification: email to on-call
- Requires audit log metrics — query `audit_logs` on action/outcome

**Technical Implementation Notes:**
- Custom metric: publish `registration_success_count` and `registration_attempt_count` as GCP custom metrics from the Audit API
- Or: GCP Log-based metric on audit log entries
- Alert condition: ratio < 0.95 for 10 minutes

**Test Cases:**
```
TC-E3-S3-1: Simulate 20 registration_started events and only 5 registration_complete events
  → Alert fires within 11 minutes
```

**Status:** 🔴 Not Started

---

### E3-S4 — Health check failing alert

**Story:**  
As the on-call team, I know within 1 minute if an internal health check fails (DB unreachable, service crashed), before the external uptime check picks it up.

**Acceptance Criteria:**
- Alert fires when `GET /health/ready` returns non-200, OR when the service process stops responding
- Alert fires within 1 minute of health check failure
- Alert severity: CRITICAL — this is a page-worthy event

**Technical Implementation Notes:**
- GCP Uptime Check on `/health/ready` endpoint (internal, deep health check)
- `/health/ready` checks: DB connection, Redis connection — returns 503 if either fails
- Check interval: 1 minute
- Alert: fires on first failure (not 2 consecutive like external uptime)

**Test Cases:**
```
TC-E3-S4-1: Stop the database container
  → /health/ready returns 503
  → Alert fires within 1 minute

TC-E3-S4-2: Restore database
  → /health/ready returns 200
  → Alert resolves
```

**Status:** 🔴 Not Started

---

## Epic Completion — Docker Integration Test

```bash
# Start all services
docker compose -f docker-compose.local.yml up -d

# Run all tests
docker compose -f docker-compose.local.yml run --rm --no-deps plant-backend pytest tests/ -x -q
docker compose -f docker-compose.local.yml run --rm --no-deps cp-backend pytest tests/ -x -q

# Verify OTel traces appear in console (local mode)
docker compose -f docker-compose.local.yml logs plant-backend | grep "SpanExporter"

# Verify health endpoints
curl http://localhost:8000/health       # → {"status": "ok"}
curl http://localhost:8000/health/ready # → {"status": "ok", "db": "ok", "redis": "ok"}
curl http://localhost:8020/health       # → {"status": "ok"}

# Stop DB and verify /health/ready returns 503
docker compose -f docker-compose.local.yml stop db
curl http://localhost:8000/health/ready  # → 503
docker compose -f docker-compose.local.yml start db
```

All tests pass. Health endpoints correct. OTel traces visible in logs. Alert configs committed to `cloud/monitoring/`.
