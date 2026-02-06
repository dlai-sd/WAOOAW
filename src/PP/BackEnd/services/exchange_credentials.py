"""Exchange credential storage (PP).

Phase 1: PP stores raw exchange API keys encrypted at rest and issues opaque
`exchange_account_id` identifiers. Plant receives only the ID and resolves
credentials server-side at execution time.

Storage is JSONL to keep this lightweight and Docker-friendly.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
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
    secret = (os.getenv("PP_EXCHANGE_CREDENTIALS_SECRET") or os.getenv("JWT_SECRET") or "dev-secret").strip()
    return Fernet(_derive_fernet_key(secret))


class ExchangeCredential(BaseModel):
    exchange_account_id: str = Field(..., min_length=1)
    customer_id: str = Field(..., min_length=1)
    exchange_provider: str = Field(..., min_length=1)

    api_key: str = Field(..., min_length=1)
    api_secret: str = Field(..., min_length=1)

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class _ExchangeCredentialRecord(BaseModel):
    exchange_account_id: str
    customer_id: str
    exchange_provider: str

    secrets_enc: str

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class FileExchangeCredentialStore:
    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

    def mint_exchange_account_id(self) -> str:
        return f"EXCH-{secrets.token_urlsafe(12)}"

    def _encrypt_secrets(self, *, api_key: str, api_secret: str) -> str:
        raw = json.dumps({"api_key": api_key, "api_secret": api_secret}, ensure_ascii=False, sort_keys=True)
        return _fernet().encrypt(raw.encode("utf-8")).decode("utf-8")

    def _decrypt_secrets(self, token: str) -> Dict[str, str]:
        try:
            raw = _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
            data = json.loads(raw)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
        except (InvalidToken, ValueError, TypeError):
            return {}
        return {}

    def upsert(
        self,
        *,
        customer_id: str,
        exchange_provider: str,
        api_key: str,
        api_secret: str,
        exchange_account_id: Optional[str] = None,
    ) -> ExchangeCredential:
        rows = self._load_records()
        now = _utcnow()

        if not exchange_account_id:
            exchange_account_id = self.mint_exchange_account_id()

        record = _ExchangeCredentialRecord(
            exchange_account_id=exchange_account_id,
            customer_id=customer_id,
            exchange_provider=exchange_provider,
            secrets_enc=self._encrypt_secrets(api_key=api_key, api_secret=api_secret),
            created_at=now,
            updated_at=now,
        )

        replaced = False
        for idx, existing in enumerate(rows):
            if existing.exchange_account_id == record.exchange_account_id:
                record.created_at = existing.created_at
                rows[idx] = record
                replaced = True
                break

        if not replaced:
            rows.append(record)

        self._write_records(rows)
        return self._to_model(record)

    def get(self, *, exchange_account_id: str) -> Optional[ExchangeCredential]:
        for rec in self._load_records():
            if rec.exchange_account_id == exchange_account_id:
                return self._to_model(rec)
        return None

    def list(self, *, customer_id: Optional[str] = None, limit: int = 100) -> List[ExchangeCredential]:
        rows = self._load_records()
        if customer_id:
            rows = [r for r in rows if r.customer_id == customer_id]
        rows = rows[-max(1, int(limit)) :]
        return [self._to_model(r) for r in rows]

    def _to_model(self, rec: _ExchangeCredentialRecord) -> ExchangeCredential:
        secrets_map = self._decrypt_secrets(rec.secrets_enc)
        return ExchangeCredential(
            exchange_account_id=rec.exchange_account_id,
            customer_id=rec.customer_id,
            exchange_provider=rec.exchange_provider,
            api_key=secrets_map.get("api_key") or "",
            api_secret=secrets_map.get("api_secret") or "",
            created_at=rec.created_at,
            updated_at=rec.updated_at,
        )

    def _load_records(self) -> List[_ExchangeCredentialRecord]:
        if not self._path.exists():
            return []
        rows: List[_ExchangeCredentialRecord] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(_ExchangeCredentialRecord.model_validate_json(line))
            except Exception:
                continue
        return rows

    def _write_records(self, rows: List[_ExchangeCredentialRecord]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(row.model_dump_json())
                f.write("\n")


@lru_cache(maxsize=1)
def default_exchange_credential_store() -> FileExchangeCredentialStore:
    path = os.getenv("PP_EXCHANGE_CREDENTIALS_STORE_PATH", "/app/data/exchange_credentials.jsonl")
    return FileExchangeCredentialStore(path)


def get_exchange_credential_store() -> FileExchangeCredentialStore:
    return default_exchange_credential_store()
