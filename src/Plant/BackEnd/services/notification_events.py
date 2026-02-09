"""Notification events (Phase-1).

NOTIF-1.1:
- Define a minimal event schema for transactional notifications.
- Emit events from key lifecycle transitions (payment success, trial activated, cancel scheduled/effective).

Phase-1 constraints:
- Default to an in-memory store (docker-friendly).
- Optional JSONL persistence via env var.

This module only records events; delivery (email/SMS) is out of scope here.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class NotificationEventRecord(BaseModel):
    created_at: datetime = Field(default_factory=_utcnow)
    event_type: str

    # Correlation / scope
    customer_id: Optional[str] = None
    subscription_id: Optional[str] = None
    order_id: Optional[str] = None
    hired_instance_id: Optional[str] = None

    # Event metadata (keep safe; avoid secrets/PII when possible)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NotificationEventStore(Protocol):
    def append(self, record: NotificationEventRecord) -> None: ...

    def list_records(
        self,
        *,
        event_type: Optional[str] = None,
        customer_id: Optional[str] = None,
        subscription_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[NotificationEventRecord]: ...


class InMemoryNotificationEventStore:
    def __init__(self) -> None:
        self._records: List[NotificationEventRecord] = []

    def append(self, record: NotificationEventRecord) -> None:
        self._records.append(record)

    def list_records(
        self,
        *,
        event_type: Optional[str] = None,
        customer_id: Optional[str] = None,
        subscription_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[NotificationEventRecord]:
        rows = list(self._records)
        if event_type:
            rows = [r for r in rows if r.event_type == event_type]
        if customer_id:
            rows = [r for r in rows if (r.customer_id or "") == customer_id]
        if subscription_id:
            rows = [r for r in rows if (r.subscription_id or "") == subscription_id]
        return rows[-max(1, int(limit)) :]


class FileNotificationEventStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

    def append(self, record: NotificationEventRecord) -> None:
        line = json.dumps(record.model_dump(mode="json"), ensure_ascii=False)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def list_records(
        self,
        *,
        event_type: Optional[str] = None,
        customer_id: Optional[str] = None,
        subscription_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[NotificationEventRecord]:
        limit = max(1, int(limit))
        rows: List[NotificationEventRecord] = []

        for raw in self._path.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            try:
                data = json.loads(raw)
                rec = NotificationEventRecord.model_validate(data)
            except Exception:
                continue
            rows.append(rec)

        if event_type:
            rows = [r for r in rows if r.event_type == event_type]
        if customer_id:
            rows = [r for r in rows if (r.customer_id or "") == customer_id]
        if subscription_id:
            rows = [r for r in rows if (r.subscription_id or "") == subscription_id]

        return rows[-limit:]


@lru_cache(maxsize=1)
def default_notification_event_store() -> NotificationEventStore:
    path = os.getenv("NOTIFICATION_EVENT_STORE_PATH")
    if path:
        return FileNotificationEventStore(Path(path))
    return InMemoryNotificationEventStore()


def get_notification_event_store() -> NotificationEventStore:
    return default_notification_event_store()
