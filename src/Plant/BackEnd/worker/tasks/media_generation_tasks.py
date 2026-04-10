from __future__ import annotations

import os
from typing import Any, Dict, Tuple
from uuid import uuid4

from core.logging import get_logger
from worker.celery_app import celery_app


logger = get_logger(__name__)


@celery_app.task(
    name="generate_media_artifact",
    bind=True,
    max_retries=3,
    default_retry_delay=15,
    acks_late=True,
)
def generate_media_artifact(self, payload: Dict[str, Any]) -> Dict[str, Any]:  # noqa: ARG001
    return payload


def enqueue_media_generation_job(*, payload: Dict[str, Any]) -> Tuple[str, str]:
    job_id = str(payload.get("job_id") or uuid4())
    queue_enabled = os.getenv("MEDIA_ARTIFACT_QUEUE_ENABLED", "false").strip().lower() == "true"
    if not queue_enabled:
        return job_id, "deferred"

    try:
        generate_media_artifact.apply_async(kwargs={"payload": {**payload, "job_id": job_id}}, task_id=job_id)
        return job_id, "celery"
    except Exception as exc:
        logger.warning(
            "Failed to enqueue media artifact job; leaving draft in deferred queued state",
            extra={"artifact_job_id": job_id, "error": str(exc)},
        )
        return job_id, "deferred"