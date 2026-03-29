"""Platform credential storage (CP).

CP Phase 2: Customers connect their social platforms in CP.
Secrets are encrypted at rest and CP issues opaque `credential_ref` identifiers.

Plant must never receive raw credentials from browser-originated requests.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import secrets
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet, InvalidToken
from pydantic import BaseModel, Field

from services.secret_manager import get_secret_manager_adapter


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _derive_fernet_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    secret = (
        os.getenv("CP_PLATFORM_CREDENTIALS_SECRET")
        or os.getenv("JWT_SECRET")
        or "dev-secret"
    ).strip()
    return Fernet(_derive_fernet_key(secret))


class PlatformCredentialPublic(BaseModel):
    credential_ref: str = Field(..., min_length=1)
    customer_id: str = Field(..., min_length=1)
    platform: str = Field(..., min_length=1)
    posting_identity: Optional[str] = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class _PlatformCredentialRecord(BaseModel):
    credential_ref: str
    customer_id: str
    platform: str
    posting_identity: Optional[str] = None

    secret_ref: Optional[str] = None
    secrets_enc: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class FilePlatformCredentialStore:
    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

    def mint_credential_ref(self) -> str:
        return f"CRED-{secrets.token_urlsafe(12)}"

    def _secret_id(self, *, customer_id: str, platform: str, credential_ref: str) -> str:
        raw = f"cp-social-{customer_id}-{platform}-{credential_ref}".lower()
        normalized = re.sub(r"[^a-z0-9_-]", "-", raw)
        return normalized[:255]

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

    async def upsert(
        self,
        *,
        customer_id: str,
        platform: str,
        posting_identity: Optional[str],
        secrets_payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        credential_ref: Optional[str] = None,
    ) -> PlatformCredentialPublic:
        rows = self._load_records()
        now = _utcnow()

        if not credential_ref:
            credential_ref = self.mint_credential_ref()

        existing = next((row for row in rows if row.credential_ref == credential_ref), None)
        secret_ref = existing.secret_ref if existing is not None else None

        if secrets_payload:
            adapter = get_secret_manager_adapter()
            if secret_ref:
                secret_ref = await adapter.update_secret(secret_ref, secrets_payload)
            else:
                secret_ref = await adapter.write_secret(
                    self._secret_id(
                        customer_id=customer_id,
                        platform=platform,
                        credential_ref=credential_ref,
                    ),
                    secrets_payload,
                )

        record = _PlatformCredentialRecord(
            credential_ref=credential_ref,
            customer_id=customer_id,
            platform=platform,
            posting_identity=posting_identity,
            secret_ref=secret_ref,
            secrets_enc=self._encrypt(secrets_payload or {}) if not secret_ref else "",
            metadata=dict(metadata or {}),
            created_at=now,
            updated_at=now,
        )

        replaced = False
        for idx, existing in enumerate(rows):
            if existing.credential_ref == record.credential_ref:
                record.created_at = existing.created_at
                if not record.secret_ref:
                    record.secret_ref = existing.secret_ref
                if not record.secrets_enc:
                    record.secrets_enc = existing.secrets_enc
                rows[idx] = record
                replaced = True
                break

        if not replaced:
            rows.append(record)

        self._write_records(rows)
        return self._to_public(record)

    async def list(self, *, customer_id: str, platform: Optional[str] = None, limit: int = 100) -> List[PlatformCredentialPublic]:
        rows = [r for r in self._load_records() if r.customer_id == customer_id]
        if platform:
            rows = [r for r in rows if r.platform == platform]
        rows = rows[-max(1, int(limit)) :]
        return [self._to_public(r) for r in rows]

    async def get(self, *, customer_id: str, credential_ref: str) -> PlatformCredentialPublic | None:
        for rec in self._load_records():
            if rec.customer_id == customer_id and rec.credential_ref == credential_ref:
                return self._to_public(rec)
        return None

    async def get_secrets(self, *, customer_id: str, credential_ref: str) -> Dict[str, Any]:
        for rec in self._load_records():
            if rec.customer_id == customer_id and rec.credential_ref == credential_ref:
                if rec.secret_ref:
                    adapter = get_secret_manager_adapter()
                    return await adapter.read_secret(rec.secret_ref)
                return self._decrypt(rec.secrets_enc)
        return {}

    async def update_access_token(
        self,
        *,
        customer_id: str,
        credential_ref: str,
        new_access_token: str,
    ) -> bool:
        rows = self._load_records()
        for idx, rec in enumerate(rows):
            if rec.customer_id != customer_id or rec.credential_ref != credential_ref:
                continue

            secrets_payload: Dict[str, Any]
            if rec.secret_ref:
                adapter = get_secret_manager_adapter()
                secrets_payload = await adapter.read_secret(rec.secret_ref)
                if not secrets_payload:
                    return False
                secrets_payload["access_token"] = new_access_token
                rec.secret_ref = await adapter.update_secret(rec.secret_ref, secrets_payload)
                rec.secrets_enc = ""
            else:
                secrets_payload = self._decrypt(rec.secrets_enc)
                if not secrets_payload:
                    return False
                secrets_payload["access_token"] = new_access_token
                rec.secrets_enc = self._encrypt(secrets_payload)

            rec.updated_at = _utcnow()
            rows[idx] = rec
            self._write_records(rows)
            return True

        return False

    def _to_public(self, rec: _PlatformCredentialRecord) -> PlatformCredentialPublic:
        return PlatformCredentialPublic(
            credential_ref=rec.credential_ref,
            customer_id=rec.customer_id,
            platform=rec.platform,
            posting_identity=rec.posting_identity,
            created_at=rec.created_at,
            updated_at=rec.updated_at,
            metadata=dict(rec.metadata or {}),
        )

    def _load_records(self) -> List[_PlatformCredentialRecord]:
        if not self._path.exists():
            return []
        rows: List[_PlatformCredentialRecord] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(_PlatformCredentialRecord.model_validate_json(line))
            except Exception:
                continue
        return rows

    def _write_records(self, rows: List[_PlatformCredentialRecord]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(row.model_dump_json())
                f.write("\n")


@lru_cache(maxsize=1)
def default_platform_credential_store() -> FilePlatformCredentialStore:
    path = os.getenv("CP_PLATFORM_CREDENTIALS_STORE_PATH", "/app/data/cp_platform_credentials.jsonl")
    return FilePlatformCredentialStore(path)


def get_platform_credential_store() -> FilePlatformCredentialStore:
    return default_platform_credential_store()
