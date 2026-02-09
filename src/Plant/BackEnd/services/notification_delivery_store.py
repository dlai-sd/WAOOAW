"""Notification delivery store (Phase-1).

NOTIF-1.2:
- Track which notification events have already been delivered (best-effort).

Phase-1 constraints:
- Default to in-memory.
- Optional JSONL persistence via env var.
"""

from __future__ import annotations

import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import List, Protocol, Set

from services.notification_events import NotificationEventRecord


def event_key(event: NotificationEventRecord) -> str:
    # Deterministic key (safe, no secrets): stable fields only.
    raw = "|".join(
        [
            str(event.event_type or ""),
            str(event.created_at.isoformat() if event.created_at else ""),
            str(event.customer_id or ""),
            str(event.subscription_id or ""),
            str(event.order_id or ""),
            str(event.hired_instance_id or ""),
        ]
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def delivery_key(channel: str, event: NotificationEventRecord) -> str:
    """Channel-specific key to avoid cross-channel dedupe collisions."""
    ch = (channel or "").strip().lower() or "unknown"
    raw = f"{ch}|{event_key(event)}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class NotificationDeliveryStore(Protocol):
    def has(self, key: str) -> bool: ...

    def mark(self, key: str) -> None: ...

    def list_keys(self, *, limit: int = 1000) -> List[str]: ...


class InMemoryNotificationDeliveryStore:
    def __init__(self) -> None:
        self._keys: Set[str] = set()

    def has(self, key: str) -> bool:
        return key in self._keys

    def mark(self, key: str) -> None:
        self._keys.add(key)

    def list_keys(self, *, limit: int = 1000) -> List[str]:
        # No strong ordering guaranteed; good enough for Phase-1.
        limit = max(1, int(limit))
        return list(self._keys)[:limit]


class FileNotificationDeliveryStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)
        self._cache: Set[str] = set()
        self._load()

    def _load(self) -> None:
        try:
            for raw in self._path.read_text(encoding="utf-8").splitlines():
                if not raw.strip():
                    continue
                try:
                    obj = json.loads(raw)
                    key = str(obj.get("key") or "").strip()
                except Exception:
                    continue
                if key:
                    self._cache.add(key)
        except Exception:
            return

    def has(self, key: str) -> bool:
        return key in self._cache

    def mark(self, key: str) -> None:
        if key in self._cache:
            return
        self._cache.add(key)
        try:
            with self._path.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"key": key}) + "\n")
        except Exception:
            return

    def list_keys(self, *, limit: int = 1000) -> List[str]:
        limit = max(1, int(limit))
        return list(self._cache)[:limit]


@lru_cache(maxsize=1)
def default_notification_delivery_store() -> NotificationDeliveryStore:
    path = (os.getenv("NOTIFICATION_DELIVERY_STORE_PATH") or "").strip()
    if path:
        return FileNotificationDeliveryStore(Path(path))
    return InMemoryNotificationDeliveryStore()


def get_notification_delivery_store() -> NotificationDeliveryStore:
    return default_notification_delivery_store()
