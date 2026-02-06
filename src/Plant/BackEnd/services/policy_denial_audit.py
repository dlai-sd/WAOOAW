"""Policy denial audit store.

Goal 2 / Epic 2.2 / Story 2.2.2:
- Persist policy denials as append-only audit records.
- Provide a small read surface for debugging/compliance.

This is intentionally lightweight and docker-friendly:
- In-memory store by default.
- Optional JSONL persistence via env var.
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


class PolicyDenialAuditRecord(BaseModel):
    created_at: datetime = Field(default_factory=_utcnow)
    correlation_id: str
    decision_id: Optional[str] = None

    agent_id: Optional[str] = None
    customer_id: Optional[str] = None
    stage: Optional[str] = None
    action: Optional[str] = None
    reason: Optional[str] = None
    path: Optional[str] = None

    details: Dict[str, Any] = Field(default_factory=dict)


class PolicyDenialAuditStore(Protocol):
    def append(self, record: PolicyDenialAuditRecord) -> None: ...

    def list_records(
        self,
        *,
        correlation_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[PolicyDenialAuditRecord]: ...


class InMemoryPolicyDenialAuditStore:
    def __init__(self) -> None:
        self._records: List[PolicyDenialAuditRecord] = []

    def append(self, record: PolicyDenialAuditRecord) -> None:
        self._records.append(record)

    def list_records(
        self,
        *,
        correlation_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[PolicyDenialAuditRecord]:
        rows = list(self._records)
        if correlation_id:
            rows = [r for r in rows if r.correlation_id == correlation_id]
        if customer_id:
            rows = [r for r in rows if r.customer_id == customer_id]
        if agent_id:
            rows = [r for r in rows if r.agent_id == agent_id]
        return rows[-max(1, int(limit)) :]


class FilePolicyDenialAuditStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

    def append(self, record: PolicyDenialAuditRecord) -> None:
        line = json.dumps(record.model_dump(mode="json"), ensure_ascii=False)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def list_records(
        self,
        *,
        correlation_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[PolicyDenialAuditRecord]:
        limit = max(1, int(limit))
        rows: List[PolicyDenialAuditRecord] = []

        # Keep it simple: read all lines; this is dev-scale.
        for raw in self._path.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            try:
                data = json.loads(raw)
                rec = PolicyDenialAuditRecord.model_validate(data)
            except Exception:
                continue
            rows.append(rec)

        if correlation_id:
            rows = [r for r in rows if r.correlation_id == correlation_id]
        if customer_id:
            rows = [r for r in rows if r.customer_id == customer_id]
        if agent_id:
            rows = [r for r in rows if r.agent_id == agent_id]

        return rows[-limit:]


@lru_cache(maxsize=1)
def default_policy_denial_audit_store() -> PolicyDenialAuditStore:
    path = os.getenv("POLICY_DENIAL_AUDIT_STORE_PATH")
    if path:
        return FilePolicyDenialAuditStore(Path(path))
    return InMemoryPolicyDenialAuditStore()


def get_policy_denial_audit_store() -> PolicyDenialAuditStore:
    return default_policy_denial_audit_store()
