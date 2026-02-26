# Worker package — Celery task definitions for Plant backend.
# Import celery_app to ensure tasks are registered on worker startup.
from worker.celery_app import celery_app  # noqa: F401
