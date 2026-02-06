"""AgentSetup storage (PP).

Phase 1: PP stores per-customer, per-agent post-hire configuration.
We persist credential *references* (not raw platform secrets), but still encrypt
at rest to reduce accidental leakage in dev/demo environments.

Storage is JSONL to keep this lightweight and Docker-friendly.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from cryptography.fernet import Fernet, InvalidToken
from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _derive_fernet_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    secret = (os.getenv("PP_AGENT_SETUP_SECRET") or os.getenv("JWT_SECRET") or "dev-secret").strip()
    return Fernet(_derive_fernet_key(secret))


class AgentSetup(BaseModel):
    customer_id: str = Field(..., min_length=1)
    agent_id: str = Field(..., min_length=1)

    channels: List[str] = Field(default_factory=list)
    posting_identity: Optional[str] = None

    credential_refs: Dict[str, str] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class _AgentSetupRecord(BaseModel):
    customer_id: str
    agent_id: str

    channels: List[str] = Field(default_factory=list)
    posting_identity: Optional[str] = None

    credential_refs_enc: str

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class FileAgentSetupStore:
    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

    def _encrypt_refs(self, refs: Dict[str, str]) -> str:
        raw = json.dumps(refs, ensure_ascii=False, sort_keys=True)
        return _fernet().encrypt(raw.encode("utf-8")).decode("utf-8")

    def _decrypt_refs(self, token: str) -> Dict[str, str]:
        try:
            raw = _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
            data = json.loads(raw)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
        except (InvalidToken, ValueError, TypeError):
            return {}
        return {}

    def upsert(self, setup: AgentSetup) -> AgentSetup:
        setups = self._load_records()

        now = _utcnow()
        record = _AgentSetupRecord(
            customer_id=setup.customer_id,
            agent_id=setup.agent_id,
            channels=list(setup.channels or []),
            posting_identity=setup.posting_identity,
            credential_refs_enc=self._encrypt_refs(setup.credential_refs or {}),
            created_at=setup.created_at,
            updated_at=now,
        )

        replaced = False
        for idx, existing in enumerate(setups):
            if existing.customer_id == record.customer_id and existing.agent_id == record.agent_id:
                record.created_at = existing.created_at
                setups[idx] = record
                replaced = True
                break

        if not replaced:
            record.created_at = now
            setups.append(record)

        self._write_records(setups)
        return self._to_model(record)

    def get(self, *, customer_id: str, agent_id: str) -> Optional[AgentSetup]:
        for rec in self._load_records():
            if rec.customer_id == customer_id and rec.agent_id == agent_id:
                return self._to_model(rec)
        return None

    def list(self, *, customer_id: Optional[str] = None, agent_id: Optional[str] = None, limit: int = 100) -> List[AgentSetup]:
        rows = self._load_records()
        if customer_id:
            rows = [r for r in rows if r.customer_id == customer_id]
        if agent_id:
            rows = [r for r in rows if r.agent_id == agent_id]
        rows = rows[-max(1, int(limit)) :]
        return [self._to_model(r) for r in rows]

    def _to_model(self, rec: _AgentSetupRecord) -> AgentSetup:
        return AgentSetup(
            customer_id=rec.customer_id,
            agent_id=rec.agent_id,
            channels=list(rec.channels or []),
            posting_identity=rec.posting_identity,
            credential_refs=self._decrypt_refs(rec.credential_refs_enc),
            created_at=rec.created_at,
            updated_at=rec.updated_at,
        )

    def _load_records(self) -> List[_AgentSetupRecord]:
        if not self._path.exists():
            return []
        rows: List[_AgentSetupRecord] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(_AgentSetupRecord.model_validate_json(line))
            except Exception:
                continue
        return rows

    def _write_records(self, rows: List[_AgentSetupRecord]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(row.model_dump_json())
                f.write("\n")


@lru_cache(maxsize=1)
def default_agent_setup_store() -> FileAgentSetupStore:
    path = os.getenv("PP_AGENT_SETUP_STORE_PATH", "/app/data/agent_setups.jsonl")
    return FileAgentSetupStore(path)


def get_agent_setup_store() -> FileAgentSetupStore:
    return default_agent_setup_store()
