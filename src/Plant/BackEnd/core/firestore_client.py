"""
FirestoreClient — INFRA-ROUTING-1 Firestore access layer.

Single entry point for all Firestore reads/writes in Plant BackEnd.
Service files MUST NOT import google.cloud.firestore directly.

Circuit breaker: every network call is wrapped so a Firestore outage
cannot propagate into a Plant BackEnd 500.  On open circuit the caller
receives None (reads) or False (writes) and falls back to SQL.

PII rule: document field names and log messages must never contain
email, phone, or full_name values. Use entity IDs only.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from core.config import settings
from core.logging import PiiMaskingFilter

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())

_CIRCUIT_OPEN_THRESHOLD = 5    # consecutive failures before opening
_CIRCUIT_RESET_SECONDS  = 30   # seconds before half-open retry


class _SimpleCircuitBreaker:
    """Lightweight circuit breaker — no external dependency required."""

    def __init__(self, threshold: int = _CIRCUIT_OPEN_THRESHOLD, reset_seconds: int = _CIRCUIT_RESET_SECONDS) -> None:
        import time
        self._failures = 0
        self._threshold = threshold
        self._reset_seconds = reset_seconds
        self._opened_at: Optional[float] = None
        self._time = time

    def is_open(self) -> bool:
        if self._opened_at is None:
            return False
        if self._time.time() - self._opened_at > self._reset_seconds:
            self._opened_at = None
            self._failures = 0
            return False
        return True

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self._threshold:
            self._opened_at = self._time.time()
            logger.warning("firestore_client: circuit opened after %d consecutive failures", self._failures)


_breaker = _SimpleCircuitBreaker()
_fs_client: Any = None  # google.cloud.firestore.AsyncClient or None


def _get_client() -> Any:
    """Lazily initialise the Firestore async client."""
    global _fs_client
    if _fs_client is not None:
        return _fs_client
    if settings.environment in {"development", "test", "local"}:
        # Return a mock so unit tests never hit the network.
        from unittest.mock import MagicMock  # stdlib — only imported in non-prod paths
        _fs_client = MagicMock()
        return _fs_client
    try:
        from google.cloud import firestore as _fs  # type: ignore[import]
        _fs_client = _fs.AsyncClient(project=settings.gcp_project_id)
        logger.info("firestore_client: async client initialised for project=%s", settings.gcp_project_id)
    except Exception as exc:
        logger.error("firestore_client: failed to initialise — %s", exc)
        _fs_client = None
    return _fs_client


async def get_document(collection: str, doc_id: str) -> Optional[dict]:
    """Read a single Firestore document. Returns None on circuit open or error."""
    if _breaker.is_open():
        logger.warning("firestore_client: circuit open, skipping read %s/%s", collection, doc_id)
        return None
    client = _get_client()
    if client is None:
        return None
    try:
        doc_ref = client.collection(collection).document(doc_id)
        snapshot = await doc_ref.get()
        _breaker.record_success()
        return snapshot.to_dict() if snapshot.exists else None
    except Exception as exc:
        _breaker.record_failure()
        logger.error("firestore_client: read error %s/%s — %s", collection, doc_id, exc)
        return None


async def set_document(collection: str, doc_id: str, data: dict, merge: bool = True) -> bool:
    """Write a Firestore document. Returns False on circuit open or error."""
    if _breaker.is_open():
        logger.warning("firestore_client: circuit open, skipping write %s/%s", collection, doc_id)
        return False
    client = _get_client()
    if client is None:
        return False
    try:
        doc_ref = client.collection(collection).document(doc_id)
        await doc_ref.set(data, merge=merge)
        _breaker.record_success()
        return True
    except Exception as exc:
        _breaker.record_failure()
        logger.error("firestore_client: write error %s/%s — %s", collection, doc_id, exc)
        return False


def reset_client_for_testing() -> None:
    """Reset the module-level client singleton — for use in tests only."""
    global _fs_client
    _fs_client = None
