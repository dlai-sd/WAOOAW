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
}

# Retry / reliability
celery_app.conf.task_acks_late = True           # Ack only after task completes
celery_app.conf.worker_prefetch_multiplier = 1  # One task at a time per worker process

# Task discovery
celery_app.autodiscover_tasks(["worker.tasks"])
