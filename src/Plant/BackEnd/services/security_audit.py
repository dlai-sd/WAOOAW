"""Security audit logging.

REG-1.9: Plant security logging.

Keep this lightweight and docker-friendly:
- In-memory store by default.
- Optional JSONL persistence via env var.

This is intentionally separate from Gateway DB-backed audit logs.
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


class SecurityAuditRecord(BaseModel):
    created_at: datetime = Field(default_factory=_utcnow)
    event_type: str

    # Actor / context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    email: Optional[str] = None

    # Request context
    http_method: Optional[str] = None
    path: Optional[str] = None

    # Outcome
    success: bool = True
    detail: Optional[str] = None

    # Extra metadata (safe, non-PII as much as possible)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SecurityAuditStore(Protocol):
    def append(self, record: SecurityAuditRecord) -> None: ...

    def list_records(
        self,
        *,
        event_type: Optional[str] = None,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        limit: int = 100,
    ) -> List[SecurityAuditRecord]: ...


class InMemorySecurityAuditStore:
    def __init__(self) -> None:
        self._records: List[SecurityAuditRecord] = []

    def append(self, record: SecurityAuditRecord) -> None:
        self._records.append(record)

    def list_records(
        self,
        *,
        event_type: Optional[str] = None,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        limit: int = 100,
    ) -> List[SecurityAuditRecord]:
        rows = list(self._records)
        if event_type:
            rows = [r for r in rows if r.event_type == event_type]
        if email:
            rows = [r for r in rows if (r.email or "").lower() == email.lower()]
        if ip_address:
            rows = [r for r in rows if r.ip_address == ip_address]
        return rows[-max(1, int(limit)) :]


class FileSecurityAuditStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

    def append(self, record: SecurityAuditRecord) -> None:
        line = json.dumps(record.model_dump(mode="json"), ensure_ascii=False)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def list_records(
        self,
        *,
        event_type: Optional[str] = None,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        limit: int = 100,
    ) -> List[SecurityAuditRecord]:
        limit = max(1, int(limit))
        rows: List[SecurityAuditRecord] = []

        for raw in self._path.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            try:
                data = json.loads(raw)
                rec = SecurityAuditRecord.model_validate(data)
            except Exception:
                continue
            rows.append(rec)

        if event_type:
            rows = [r for r in rows if r.event_type == event_type]
        if email:
            rows = [r for r in rows if (r.email or "").lower() == email.lower()]
        if ip_address:
            rows = [r for r in rows if r.ip_address == ip_address]

        return rows[-limit:]


@lru_cache(maxsize=1)
def default_security_audit_store() -> SecurityAuditStore:
    path = os.getenv("SECURITY_AUDIT_STORE_PATH")
    if path:
        return FileSecurityAuditStore(Path(path))
    return InMemorySecurityAuditStore()


def get_security_audit_store() -> SecurityAuditStore:
    return default_security_audit_store()
