"""Approval records (CP).

Phase 2: customer self-serve approvals. CP mints an `approval_id` for a
specific customer-scoped action (e.g., approve a draft post) and persists it
for auditability.

Plant enforcement treats `approval_id` as an opaque token.
"""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CPApprovalRecord(BaseModel):
    approval_id: str = Field(..., min_length=1)
    customer_id: str = Field(..., min_length=1)

    subject_type: str = Field(..., min_length=1)
    subject_id: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)

    decision: str = Field(..., min_length=1)  # approved | rejected
    reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=_utcnow)


class FileCPApprovalStore:
    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

    def mint_approval_id(self) -> str:
        # Keep the same prefix as PP/Plant docs for consistency.
        return f"APR-{secrets.token_urlsafe(12)}"

    def append(
        self,
        *,
        customer_id: str,
        subject_type: str,
        subject_id: str,
        action: str,
        decision: str,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        approval_id: Optional[str] = None,
    ) -> CPApprovalRecord:
        if not approval_id:
            approval_id = self.mint_approval_id()
        record = CPApprovalRecord(
            approval_id=approval_id,
            customer_id=customer_id,
            subject_type=subject_type,
            subject_id=subject_id,
            action=action,
            decision=decision,
            reason=reason,
            metadata=dict(metadata or {}),
        )

        with self._path.open("a", encoding="utf-8") as f:
            f.write(record.model_dump_json())
            f.write("\n")
        return record

    def list(self, *, customer_id: str, limit: int = 100) -> List[CPApprovalRecord]:
        rows = [r for r in self._load_records() if r.customer_id == customer_id]
        rows = rows[-max(1, int(limit)) :]
        return rows

    def _load_records(self) -> List[CPApprovalRecord]:
        if not self._path.exists():
            return []
        rows: List[CPApprovalRecord] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(CPApprovalRecord.model_validate_json(line))
            except Exception:
                continue
        return rows


@lru_cache(maxsize=1)
def default_cp_approval_store() -> FileCPApprovalStore:
    path = os.getenv("CP_APPROVALS_STORE_PATH", "/app/data/cp_approvals.jsonl")
    return FileCPApprovalStore(path)


def get_cp_approval_store() -> FileCPApprovalStore:
    return default_cp_approval_store()
