"""Approval records (PP).

Phase 1: ops-assisted approvals. PP can mint an `approval_id` for a specific
customer + agent + action (e.g. trading `place_order` / `close_position`).

Plant execution currently accepts `approval_id` as a string token; PP keeps the
approval record for operational auditability.

Storage is JSONL to keep this lightweight and Docker-friendly.
"""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ApprovalRecord(BaseModel):
    approval_id: str = Field(..., min_length=1)
    customer_id: str = Field(..., min_length=1)
    agent_id: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)

    requested_by: str = Field(..., min_length=1)
    correlation_id: Optional[str] = None
    purpose: Optional[str] = None
    notes: Optional[str] = None

    created_at: datetime = Field(default_factory=_utcnow)
    expires_at: Optional[datetime] = None


class FileApprovalStore:
    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

    def mint_approval_id(self) -> str:
        return f"APR-{secrets.token_urlsafe(12)}"

    def create(
        self,
        *,
        customer_id: str,
        agent_id: str,
        action: str,
        requested_by: str,
        correlation_id: Optional[str] = None,
        purpose: Optional[str] = None,
        notes: Optional[str] = None,
        expires_in_seconds: Optional[int] = None,
        approval_id: Optional[str] = None,
    ) -> ApprovalRecord:
        now = _utcnow()
        if not approval_id:
            approval_id = self.mint_approval_id()

        expires_at: Optional[datetime] = None
        if expires_in_seconds is not None:
            try:
                seconds = int(expires_in_seconds)
            except Exception:
                seconds = 0
            if seconds > 0:
                expires_at = now + timedelta(seconds=seconds)

        record = ApprovalRecord(
            approval_id=approval_id,
            customer_id=customer_id,
            agent_id=agent_id,
            action=action,
            requested_by=requested_by,
            correlation_id=correlation_id,
            purpose=purpose,
            notes=notes,
            created_at=now,
            expires_at=expires_at,
        )

        rows = self._load_records()
        rows.append(record)
        self._write_records(rows)
        return record

    def get(self, *, approval_id: str) -> Optional[ApprovalRecord]:
        for rec in self._load_records():
            if rec.approval_id == approval_id:
                return rec
        return None

    def list(
        self,
        *,
        customer_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        action: Optional[str] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[ApprovalRecord]:
        rows = self._load_records()
        if customer_id:
            rows = [r for r in rows if r.customer_id == customer_id]
        if agent_id:
            rows = [r for r in rows if r.agent_id == agent_id]
        if action:
            rows = [r for r in rows if r.action == action]
        if correlation_id:
            rows = [r for r in rows if (r.correlation_id or '') == correlation_id]
        rows = rows[-max(1, int(limit)) :]
        return rows

    def _load_records(self) -> List[ApprovalRecord]:
        if not self._path.exists():
            return []
        rows: List[ApprovalRecord] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(ApprovalRecord.model_validate_json(line))
            except Exception:
                continue
        return rows

    def _write_records(self, rows: List[ApprovalRecord]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(row.model_dump_json())
                f.write("\n")


@lru_cache(maxsize=1)
def default_approval_store() -> FileApprovalStore:
    path = os.getenv("PP_APPROVALS_STORE_PATH", "/app/data/approvals.jsonl")
    return FileApprovalStore(path)


def get_approval_store() -> FileApprovalStore:
    return default_approval_store()
