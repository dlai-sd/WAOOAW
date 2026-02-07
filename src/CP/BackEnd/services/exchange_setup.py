"""Exchange setup storage (CP).

Phase 2: Customer self-serve trading setup for Delta Exchange India.
Customers submit API keys to CP backend which stores secrets encrypted at rest
and returns an opaque `credential_ref`.

Plant must never receive raw exchange credentials from browser-originated
requests. CP returns only `credential_ref` + non-secret configuration.
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
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet, InvalidToken
from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _derive_fernet_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    secret = (os.getenv("CP_EXCHANGE_SETUP_SECRET") or os.getenv("JWT_SECRET") or "dev-secret").strip()
    return Fernet(_derive_fernet_key(secret))


class RiskLimits(BaseModel):
    max_units_per_order: float = Field(..., gt=0)
    max_notional_inr: Optional[float] = Field(default=None, gt=0)


class ExchangeSetupPublic(BaseModel):
    credential_ref: str = Field(..., min_length=1)
    customer_id: str = Field(..., min_length=1)
    exchange_provider: str = Field(..., min_length=1)

    default_coin: str = Field(..., min_length=1)
    allowed_coins: List[str] = Field(default_factory=list)
    risk_limits: RiskLimits

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class _ExchangeSetupRecord(BaseModel):
    credential_ref: str
    customer_id: str
    exchange_provider: str

    default_coin: str
    allowed_coins: List[str] = Field(default_factory=list)
    risk_limits: RiskLimits

    secrets_enc: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class FileExchangeSetupStore:
    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

    def mint_credential_ref(self) -> str:
        return f"EXCH-{secrets.token_urlsafe(12)}"

    def _encrypt(self, payload: Dict[str, Any]) -> str:
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return _fernet().encrypt(raw.encode("utf-8")).decode("utf-8")

    def _decrypt(self, token: str) -> Dict[str, Any]:
        try:
            raw = _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
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
        default_coin: str,
        allowed_coins: List[str],
        risk_limits: RiskLimits,
        metadata: Optional[Dict[str, Any]] = None,
        credential_ref: Optional[str] = None,
    ) -> ExchangeSetupPublic:
        rows = self._load_records()
        now = _utcnow()

        if not credential_ref:
            credential_ref = self.mint_credential_ref()

        record = _ExchangeSetupRecord(
            credential_ref=credential_ref,
            customer_id=customer_id,
            exchange_provider=exchange_provider,
            default_coin=default_coin,
            allowed_coins=list(allowed_coins or []),
            risk_limits=risk_limits,
            secrets_enc=self._encrypt({"api_key": api_key, "api_secret": api_secret}),
            metadata=dict(metadata or {}),
            created_at=now,
            updated_at=now,
        )

        replaced = False
        for idx, existing in enumerate(rows):
            if existing.credential_ref == record.credential_ref:
                record.created_at = existing.created_at
                rows[idx] = record
                replaced = True
                break

        if not replaced:
            rows.append(record)

        self._write_records(rows)
        return self._to_public(record)

    def list(self, *, customer_id: str, limit: int = 100) -> List[ExchangeSetupPublic]:
        rows = [r for r in self._load_records() if r.customer_id == customer_id]
        rows = rows[-max(1, int(limit)) :]
        return [self._to_public(r) for r in rows]

    def get_secrets(self, *, customer_id: str, credential_ref: str) -> Dict[str, Any]:
        for rec in self._load_records():
            if rec.customer_id == customer_id and rec.credential_ref == credential_ref:
                return self._decrypt(rec.secrets_enc)
        return {}

    def _to_public(self, rec: _ExchangeSetupRecord) -> ExchangeSetupPublic:
        return ExchangeSetupPublic(
            credential_ref=rec.credential_ref,
            customer_id=rec.customer_id,
            exchange_provider=rec.exchange_provider,
            default_coin=rec.default_coin,
            allowed_coins=list(rec.allowed_coins or []),
            risk_limits=rec.risk_limits,
            created_at=rec.created_at,
            updated_at=rec.updated_at,
            metadata=dict(rec.metadata or {}),
        )

    def _load_records(self) -> List[_ExchangeSetupRecord]:
        if not self._path.exists():
            return []
        rows: List[_ExchangeSetupRecord] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(_ExchangeSetupRecord.model_validate_json(line))
            except Exception:
                continue
        return rows

    def _write_records(self, rows: List[_ExchangeSetupRecord]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(row.model_dump_json())
                f.write("\n")


@lru_cache(maxsize=1)
def default_exchange_setup_store() -> FileExchangeSetupStore:
    path = os.getenv("CP_EXCHANGE_SETUP_STORE_PATH", "/app/data/cp_exchange_setups.jsonl")
    return FileExchangeSetupStore(path)


def get_exchange_setup_store() -> FileExchangeSetupStore:
    return default_exchange_setup_store()
