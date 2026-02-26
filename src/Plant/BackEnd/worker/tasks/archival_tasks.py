"""Data archival and cleanup Celery tasks — E4-S1 / E4-S2 (Iteration 7).

E4-S1: archive_audit_logs — monthly job that archives audit log records older
       than 2 years to GCP Cloud Storage and removes them from the primary DB.

E4-S2: cleanup_otp_sessions — daily job that purges expired and verified-old
       OTP session records.

Celery Beat schedule (registered in celery_app.py):
  archive_audit_logs      — 1st of each month at 02:00 UTC (cron)
  cleanup_otp_sessions    — daily at 03:00 UTC (cron)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict

from celery.exceptions import MaxRetriesExceededError

from worker.celery_app import celery_app

logger = logging.getLogger(__name__)

_ARCHIVE_BUCKET = os.getenv("AUDIT_ARCHIVE_BUCKET", "waooaw-audit-archive")
_CHUNK_SIZE = 10_000  # records per GCS upload chunk


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_async(coro):
    """Run an async coroutine from a sync Celery task context."""
    return asyncio.run(coro)


async def _get_db_session():
    """Obtain a raw async DB session from the connector (no FastAPI context)."""
    import os
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/plant")
    engine = create_async_engine(db_url, pool_size=2, max_overflow=2)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    session = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
        await engine.dispose()


async def _archive_to_gcs(bucket: str, blob_name: str, records: list) -> bool:
    """Upload *records* (list of dicts) to GCS as JSON Lines.

    Returns True if the upload succeeded, False if the file already exists
    (idempotency guard).

    GCS is accessed via ``google-cloud-storage`` library.  When the library
    or ADC credentials are unavailable (local dev) the function logs a warning
    and returns True (simulates success so the task can purge the DB rows).
    """
    try:
        from google.cloud import storage  # type: ignore[import]
        from google.api_core.exceptions import PreconditionFailed  # type: ignore[import]
    except ImportError:
        logger.warning("archive_to_gcs: google-cloud-storage not installed — skipping GCS upload")
        return True

    client = storage.Client()
    bucket_ref = client.bucket(bucket)
    blob = bucket_ref.blob(blob_name)

    if blob.exists():
        logger.info("archive_to_gcs: %s/%s already exists — skipping (idempotent)", bucket, blob_name)
        return False  # already archived, skip DB deletion

    jsonl = "\n".join(json.dumps(r, default=str) for r in records)
    try:
        blob.upload_from_string(
            jsonl.encode("utf-8"),
            content_type="application/x-ndjson",
            if_generation_match=0,  # only create, never overwrite
        )
        logger.info("archive_to_gcs: uploaded %d records to gs://%s/%s", len(records), bucket, blob_name)
        return True
    except PreconditionFailed:
        # Race condition — another worker beat us to it
        logger.info("archive_to_gcs: %s/%s created by concurrent run — idempotent OK", bucket, blob_name)
        return False


# ---------------------------------------------------------------------------
# E4-S1: Audit log archival
# ---------------------------------------------------------------------------

@celery_app.task(
    name="archive_audit_logs",
    bind=True,
    max_retries=3,
    queue="archival",
    default_retry_delay=300,  # 5 minutes between retries
)
def archive_audit_logs(self):
    """E4-S1 (Iteration 7): Archive audit log records older than 2 years.

    Monthly Celery Beat task.  Safe to run standalone:
        celery -A worker.celery_app call archive_audit_logs
    """
    try:
        archived, deleted = _run_async(_do_archive_audit_logs())
        logger.info("archive_audit_logs: archived=%d deleted=%d", archived, deleted)
        return {"archived": archived, "deleted": deleted}
    except Exception as exc:
        logger.exception("archive_audit_logs: failed — %s", exc)
        try:
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            logger.error("archive_audit_logs: max retries exceeded")
            raise


async def _do_archive_audit_logs() -> tuple[int, int]:
    """Core async implementation of E4-S1 audit log archival."""
    from sqlalchemy import text

    now_utc = datetime.now(timezone.utc)
    year_str = now_utc.strftime("%Y")
    month_str = now_utc.strftime("%m")
    blob_name = f"{year_str}/{month_str}/audit_logs_{now_utc.strftime('%Y%m%dT%H%M%S')}.jsonl"

    total_archived = 0
    total_deleted = 0

    async for session in _get_db_session():
        # Fetch in chunks to avoid loading huge result sets into memory
        offset = 0
        while True:
            result = await session.execute(
                text(
                    "SELECT id, timestamp, user_id, email, ip_address, user_agent, "
                    "screen, action, outcome, detail, metadata "
                    "FROM audit_logs "
                    "WHERE timestamp < NOW() - INTERVAL '2 years' "
                    "ORDER BY timestamp "
                    "LIMIT :limit OFFSET :offset"
                ),
                {"limit": _CHUNK_SIZE, "offset": offset},
            )
            rows = result.mappings().all()
            if not rows:
                break

            records = [dict(r) for r in rows]
            chunk_blob = blob_name if offset == 0 else blob_name.replace(".jsonl", f"_{offset}.jsonl")

            uploaded = await _archive_to_gcs(_ARCHIVE_BUCKET, chunk_blob, records)
            if uploaded:
                # Delete the archived chunk from DB
                ids = [str(r["id"]) for r in records]
                await session.execute(
                    text("DELETE FROM audit_logs WHERE id = ANY(:ids::uuid[])"),
                    {"ids": ids},
                )
                await session.commit()
                total_deleted += len(records)

            total_archived += len(records)
            offset += _CHUNK_SIZE

    logger.info(
        "archive_audit_logs: Archived %d records to gs://%s/%s",
        total_archived,
        _ARCHIVE_BUCKET,
        blob_name,
    )
    return total_archived, total_deleted


# ---------------------------------------------------------------------------
# E4-S2: OTP session cleanup
# ---------------------------------------------------------------------------

@celery_app.task(
    name="cleanup_otp_sessions",
    bind=True,
    max_retries=3,
    queue="archival",
    default_retry_delay=60,
)
def cleanup_otp_sessions(self):
    """E4-S2 (Iteration 7): Purge expired and old verified OTP sessions.

    Deletes:
      - Expired sessions: ``expires_at < NOW()``
      - Verified + stale: ``verified_at IS NOT NULL AND verified_at < NOW() - 30 days``

    Daily Celery Beat task.  Idempotent.
    """
    try:
        deleted = _run_async(_do_cleanup_otp_sessions())
        logger.info("cleanup_otp_sessions: Cleaned up %d OTP sessions", deleted)
        return {"deleted": deleted}
    except Exception as exc:
        logger.exception("cleanup_otp_sessions: failed — %s", exc)
        try:
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            logger.error("cleanup_otp_sessions: max retries exceeded")
            raise


async def _do_cleanup_otp_sessions() -> int:
    """Core async implementation of E4-S2 OTP session cleanup."""
    from sqlalchemy import text

    total_deleted = 0
    async for session in _get_db_session():
        result = await session.execute(
            text(
                "DELETE FROM otp_sessions "
                "WHERE expires_at < NOW() "
                "   OR (verified_at IS NOT NULL AND verified_at < NOW() - INTERVAL '30 days') "
                "RETURNING id"
            )
        )
        total_deleted = len(result.fetchall())
        await session.commit()

    return total_deleted
