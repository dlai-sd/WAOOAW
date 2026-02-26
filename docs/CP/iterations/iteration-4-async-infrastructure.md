# Iteration 4 — Async Infrastructure

**When:** Before production  
**Branch naming:** `feat/async-infra-it4`  
**Testing:** `docker compose -f docker-compose.local.yml` — no virtual env, no local Python  
**Status:** 🔴 Not Started

---

## Tracking Table

| # | Epic | Story | Status | PR |
|---|------|-------|--------|----|
| E1-S1 | Celery Setup | Wire Celery with Redis broker | 🔴 Not Started | — |
| E1-S2 | Celery Setup | Celery worker in docker-compose | 🔴 Not Started | — |
| E2-S1 | Async Email | Move OTP email send to Celery task | 🔴 Not Started | — |
| E2-S2 | Async Email | Retry logic for failed sends | 🔴 Not Started | — |
| E3-S1 | Notification Service | Notification service abstraction | 🔴 Not Started | — |
| E3-S2 | Notification Service | Registration complete event fires welcome email | 🔴 Not Started | — |
| E4-S1 | Event Architecture | Registration complete publishes domain event | 🔴 Not Started | — |

**Story Status Key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done

---

## Epic 1 — Celery + Redis Setup

**Goal:** Celery task queue wired with Redis as broker. Tasks can be enqueued from any backend service and processed by dedicated workers. Redis is already in docker-compose — this iteration wires it up for task processing.

---

### E1-S1 — Wire Celery with Redis broker

**Story:**  
As the Plant backend, I can enqueue background tasks using Celery with Redis as the message broker, so long-running work (email sending, notifications) happens outside the HTTP request cycle.

**Acceptance Criteria:**
- Celery app defined in `src/Plant/BackEnd/worker/celery_app.py`
- Broker URL: `redis://redis:6379/1` (database 1 — separate from session/cache data on db 0)
- Result backend: `redis://redis:6379/2` (database 2)
- `celery` added to Plant backend `requirements.txt`
- Celery app importable without errors
- Task discovery: `celery_app.autodiscover_tasks(["worker.tasks"])`

**Technical Implementation Notes:**
- `src/Plant/BackEnd/worker/__init__.py` — empty
- `src/Plant/BackEnd/worker/celery_app.py` — Celery instance
- `src/Plant/BackEnd/worker/tasks/__init__.py` — empty
- Celery config: `task_serializer="json"`, `result_serializer="json"`, `accept_content=["json"]`, `timezone="UTC"`, `enable_utc=True`
- `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` read from env vars

**Test Cases:**
```
TC-E1-S1-1: Import celery_app — no errors
TC-E1-S1-2: celery_app.conf.broker_url reads from CELERY_BROKER_URL env var
TC-E1-S1-3: celery -A worker.celery_app inspect ping (in container) — worker responds
```

**Status:** 🔴 Not Started

---

### E1-S2 — Celery worker in docker-compose

**Story:**  
As the platform, there is a dedicated Celery worker container that processes background tasks, separate from the API server container.

**Acceptance Criteria:**
- New service `plant-worker` in `docker-compose.local.yml`
- Runs: `celery -A worker.celery_app worker --loglevel=info --concurrency=4`
- Uses same Docker image as `plant-backend` (same Dockerfile, different CMD)
- Has access to same env vars as `plant-backend` (DB, Redis, etc.)
- Starts after `redis` and `db` services
- Health: `celery -A worker.celery_app inspect ping` returns response

**Technical Implementation Notes:**
- In `docker-compose.local.yml`: add `plant-worker` service with `command` override
- `depends_on: [redis, db]`
- Same environment variables as `plant-backend`
- Flower (Celery monitoring UI) optional but useful: add `plant-flower` service on port 5555

**Test Cases:**
```
TC-E1-S2-1: docker compose up -d — plant-worker starts without errors
TC-E1-S2-2: docker compose logs plant-worker — shows "ready" / "celery@... ready"
TC-E1-S2-3: Enqueue a test task from plant-backend, verify plant-worker picks it up within 2 seconds
TC-E1-S2-4: plant-worker restarts gracefully without losing in-flight tasks
```

**Status:** 🔴 Not Started

---

## Epic 2 — Async Email / OTP Sending

**Goal:** OTP email is currently sent inline — if the email provider is slow, the user's HTTP request hangs. Move to async: enqueue the send, return HTTP 202 immediately, worker sends.

---

### E2-S1 — Move OTP email send to Celery task

**Story:**  
As a user requesting an OTP, I receive an immediate response confirming the OTP is on its way — I never wait for email delivery to complete before seeing a response.

**Acceptance Criteria:**
- OTP email send moved to a Celery task: `send_otp_email.delay(email, otp_code, expires_in_minutes)`
- Plant backend OTP endpoint returns HTTP 202 after enqueuing the task — does not wait for email delivery
- Task executes in `plant-worker` container
- If email delivery fails in the task: task retries (E2-S2)
- OTP record is saved to DB (otp_sessions table) synchronously before 202 is returned — only the email send is async
- User experience: response is immediate, email arrives within seconds

**Technical Implementation Notes:**
- File: `src/Plant/BackEnd/worker/tasks/email_tasks.py`
- Task: `@celery_app.task(name="send_otp_email", bind=True, max_retries=3)`
- Email provider: use existing email configuration from Plant backend settings
- OTP record must be committed to DB BEFORE the 202 is returned — so the code is valid even if email is delayed
- Remove the `await send_email(...)` call from the OTP endpoint, replace with `send_otp_email.delay(...)`

**Test Cases:**
```
TC-E2-S1-1: POST /auth/otp/start
  → HTTP 202 returned immediately (< 200ms)
  → OTP record exists in otp_sessions table
  → Celery task enqueued (visible in Redis broker queue)
  → Email delivered within 5 seconds

TC-E2-S1-2: Email provider down — POST /auth/otp/start
  → HTTP 202 returned (OTP saved to DB)
  → Task retries in background (E2-S2)
  → User can verify OTP once task eventually succeeds

TC-E2-S1-3: docker compose logs plant-worker
  → Shows task execution log for each OTP email sent
```

**Status:** 🔴 Not Started

---

### E2-S2 — Retry logic for failed email sends

**Story:**  
As the platform, if an OTP email fails to send (SMTP timeout, provider error), it is automatically retried so transient failures don't permanently block registration.

**Acceptance Criteria:**
- `send_otp_email` task retries up to 3 times
- Retry delay: exponential backoff — 1s, 2s, 4s
- After 3 failures: task moves to dead letter queue (Redis key `celery.dead_letter`)
- Dead letter queue contents are logged as `ERROR` for manual investigation
- OTP expiry is checked before retry — if OTP already expired, skip retry (pointless send)

**Technical Implementation Notes:**
- Celery retry: `self.retry(exc=exc, countdown=2**self.request.retries)` inside the task
- `max_retries=3` on the task decorator
- Dead letter handling: on `MaxRetriesExceededError`, log the failure with email and task ID
- Check OTP expiry: query DB for OTP record before sending — if `expires_at < now()`, log and skip

**Test Cases:**
```
TC-E2-S2-1: Mock email provider to fail once — OTP email task
  → Task retries after 1 second
  → Second attempt succeeds
  → Email delivered

TC-E2-S2-2: Mock email provider to fail 4 times
  → Task retries 3 times (4 total attempts)
  → After 3rd retry: MaxRetriesExceeded
  → Error logged with email address and task ID

TC-E2-S2-3: OTP expired before retry executes
  → Task checks expiry, skips send
  → Logs: "OTP expired, skipping email send"
```

**Status:** 🔴 Not Started

---

## Epic 3 — Notification Service

**Goal:** A dedicated notification service that handles all customer-facing messages (email, WhatsApp, SMS). Business logic never calls email libraries directly — it fires notification events. When new channels are added, only the notification service changes.

---

### E3-S1 — Notification service abstraction

**Story:**  
As any backend service needing to contact a customer, I call `NotificationService.send(channel, destination, template, context)` and the notification service handles delivery — I don't care how.

**Acceptance Criteria:**
- `NotificationService` class in `src/Plant/BackEnd/services/notification_service.py`
- Method: `async send(channel: str, destination: str, template: str, context: dict) -> None`
- Supported channels initially: `email`
- `template` is a key (e.g. `otp_verification`, `welcome`, `password_reset`) — not a HTML string
- Templates stored in `src/Plant/BackEnd/templates/` as Jinja2 `.html` files
- Service enqueues a Celery task — does not send synchronously
- Unknown channel raises `ValueError` immediately (not silently ignored)

**Technical Implementation Notes:**
- `NotificationService.send()` maps template key to Jinja2 template, renders it, enqueues `send_email_task.delay(destination, subject, html_body)`
- Templates directory: `src/Plant/BackEnd/templates/email/otp_verification.html`, `welcome.html`, etc.
- Jinja2 already available in Python stdlib-adjacent packages — add to requirements if not present
- Each template has a matching subject line in a `templates/subjects.py` dict

**Test Cases:**
```
TC-E3-S1-1: NotificationService.send(channel="email", destination="test@example.com", template="otp_verification", context={"otp_code": "123456"})
  → Celery task enqueued
  → No error raised

TC-E3-S1-2: NotificationService.send(channel="unknown_channel", ...)
  → ValueError raised immediately

TC-E3-S1-3: NotificationService.send with template="otp_verification" and context with otp_code
  → Rendered email contains the otp_code value

TC-E3-S1-4: Template file missing for given template key
  → TemplateNotFound raised with clear message
```

**Status:** 🔴 Not Started

---

### E3-S2 — Registration complete event fires welcome email

**Story:**  
As a newly registered customer, I receive a welcome email automatically after my registration is complete — without any explicit "send welcome email" call in the registration code.

**Acceptance Criteria:**
- Registration complete triggers a `customer_registered` event
- A Celery task listens for this event and calls `NotificationService.send(channel="email", template="welcome", ...)`
- Welcome email template exists: `templates/email/welcome.html` — includes customer's first name and login link
- Registration endpoint does NOT contain any welcome email code — it only fires the event
- Welcome email is sent within 30 seconds of registration completing

**Technical Implementation Notes:**
- Event firing: after customer record saved, call `customer_registered_event.delay(customer_id, email, full_name)`
- Task in `src/Plant/BackEnd/worker/tasks/registration_tasks.py`
- Task calls `NotificationService.send(...)` internally
- Template: `src/Plant/BackEnd/templates/email/welcome.html` — simple, brand-consistent

**Test Cases:**
```
TC-E3-S2-1: Complete registration
  → Welcome email received within 30 seconds
  → Email contains customer's first name

TC-E3-S2-2: Registration code has no direct email import or send call
  → grep "send_email\|smtplib\|sendgrid" in registration endpoint files → not found

TC-E3-S2-3: Welcome email task fails (email provider down)
  → Registration still completes (event is fire-and-forget)
  → Task retried per retry policy
```

**Status:** 🔴 Not Started

---

## Epic 4 — Event-Driven Registration

**Goal:** Registration completion is a domain event, not just an HTTP response. Other parts of the system subscribe to it independently. Decouples registration from downstream actions.

---

### E4-S1 — Registration complete publishes domain event

**Story:**  
As the platform, when a customer completes registration, a `customer.registered` event is published so any number of independent subscribers can react without the registration code knowing about them.

**Acceptance Criteria:**
- After `POST /customers` returns `created=True`, registration handler publish `customer.registered` event
- Event payload: `{ customer_id, email, full_name, business_name, registered_at }`
- Published to Redis pub/sub channel `events.customer.registered`
- Current subscribers: welcome email task, onboarding task (create initial trial record)
- Adding new subscribers requires zero changes to registration code
- Event is fire-and-forget — publication failure does not fail registration

**Technical Implementation Notes:**
- Publisher: `src/Plant/BackEnd/services/event_publisher.py` — `publish(channel, payload)` using `aioredis`
- Subscriber: Celery tasks that subscribe via `CELERY_QUEUES` or Redis pub/sub listener
- Simpler alternative (acceptable for now): directly enqueue multiple Celery tasks instead of pure pub/sub — functionally equivalent, easier to reason about
- Recommended approach: `registration_complete_handler.delay(customer_id, email, ...)` which internally fans out to welcome email + onboarding

**Test Cases:**
```
TC-E4-S1-1: Complete registration
  → Welcome email task enqueued
  → Onboarding task enqueued (creates initial record)
  → Both fire within 5 seconds

TC-E4-S1-2: Redis unavailable at event publish time
  → Registration returns HTTP 201 (success)
  → Event publish failure logged as warning
  → Welcome email not sent (acceptable — manual retry possible)

TC-E4-S1-3: Registration code contains no reference to welcome email or onboarding
  → grep "welcome\|onboarding" in customers.py → not found
```

**Status:** 🔴 Not Started

---

## Epic Completion — Docker Integration Test

```bash
# Start all services including worker
docker compose -f docker-compose.local.yml up -d

# Verify worker is running
docker compose -f docker-compose.local.yml logs plant-worker | grep "ready"

# Run all tests
docker compose -f docker-compose.local.yml run --rm --no-deps plant-backend pytest tests/ -x -q
docker compose -f docker-compose.local.yml run --rm --no-deps cp-backend pytest tests/ -x -q

# Test async email — trigger an OTP and watch worker logs
docker compose -f docker-compose.local.yml logs -f plant-worker &
# (trigger OTP via API)
# → Should see task execution in worker logs within 2 seconds

# Verify Celery task queue in Redis
docker compose -f docker-compose.local.yml exec redis redis-cli LLEN celery

# Flower UI (if configured)
# Open http://localhost:5555 — should show worker and task history
```

All tests pass. Worker starts and processes tasks. OTP email confirmed sent via worker logs.
