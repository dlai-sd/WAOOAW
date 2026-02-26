"""Celery application — E1-S1 Iteration 4.

Broker: Redis DB 4  (separate from session/cache on DB 0)
Result backend: Redis DB 5

Environment variables:
  CELERY_BROKER_URL   — defaults to redis://redis:6379/4
  CELERY_RESULT_BACKEND — defaults to redis://redis:6379/5

Usage:
  # Start worker inside container:
  celery -A worker.celery_app worker --loglevel=info --concurrency=4

  # Inspect in CI:
  celery -A worker.celery_app inspect ping
"""

from __future__ import annotations

import os

from celery import Celery

# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------

celery_app = Celery("waooaw_plant")

celery_app.conf.broker_url = os.getenv(
    "CELERY_BROKER_URL", "redis://redis:6379/4"
)
celery_app.conf.result_backend = os.getenv(
    "CELERY_RESULT_BACKEND", "redis://redis:6379/5"
)

# Serialization
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]

# Timezone
celery_app.conf.timezone = "UTC"
celery_app.conf.enable_utc = True

# Task routing
celery_app.conf.task_routes = {
    "send_otp_email": {"queue": "email"},
    "send_welcome_email": {"queue": "email"},
    "handle_customer_registered": {"queue": "events"},
    # E4-S1 / E4-S2 (Iteration 7): archival + cleanup
    "archive_audit_logs": {"queue": "archival"},
    "cleanup_otp_sessions": {"queue": "archival"},
}

# E4-S1 / E4-S2 (Iteration 7): Celery Beat scheduled tasks
from celery.schedules import crontab  # noqa: E402

celery_app.conf.beat_schedule = {
    # E4-S1: Archive audit logs older than 2 years — 1st of each month at 02:00 UTC
    "archive-audit-logs": {
        "task": "archive_audit_logs",
        "schedule": crontab(day_of_month=1, hour=2, minute=0),
    },
    # E4-S2: Purge expired / old verified OTP sessions — daily at 03:00 UTC
    "cleanup-otp-sessions": {
        "task": "cleanup_otp_sessions",
        "schedule": crontab(hour=3, minute=0),
    },
}

# Retry / reliability
celery_app.conf.task_acks_late = True           # Ack only after task completes
celery_app.conf.worker_prefetch_multiplier = 1  # One task at a time per worker process

# Task discovery
celery_app.autodiscover_tasks(["worker.tasks"])
