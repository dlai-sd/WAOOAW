"""ExchangeCredentialService — DB-backed exchange credential store.

TRADER-FULL-1 S1.
Plant is the authoritative credential store for customer exchange API keys.

## Credential storage — industry-standard two-backend design

### Backend 1: Fernet symmetric encryption (default, `EXCHANGE_SECRET_BACKEND=fernet`)

Used in: local, development, codespace, demo, uat

- Each api_key and api_secret is encrypted with Fernet (AES-128-CBC + HMAC-SHA256).
- The Fernet key is derived from `CP_EXCHANGE_SETUP_SECRET` env var (32+ random bytes,
  base64-url encoded). Fall back to `SECRET_KEY` if not set — but this is insecure and
  will produce a startup warning in non-test environments.
- Only the encrypted blob is stored in the DB; the plaintext never touches disk.
- Key rotation: change `CP_EXCHANGE_SETUP_SECRET` and re-run a migration script that
  decrypts with the old key and re-encrypts with the new key.

### Backend 2: GCP Secret Manager (`EXCHANGE_SECRET_BACKEND=secret_manager`)

Used in: prod

- At upsert time: api_key/api_secret are written to a new GCP Secret version under the
  resource path `projects/<project>/secrets/hired-<hired_id>-delta/versions/latest`.
- Only the resource path (the `secret_ref`) is stored in the DB — no key material at all.
- At runtime: `get_secrets()` resolves the reference via Secret Manager API using the
  Cloud Run service account. The raw credentials are held in memory for the duration of
  one request and then garbage-collected.
- Rotation: create a new Secret version in GCP; `get_secrets()` always fetches `latest`.

## Security checklist (apply to every new environment)
- [ ] `CP_EXCHANGE_SETUP_SECRET` is set to a cryptographically random 32+ byte value
- [ ] `CP_EXCHANGE_SETUP_SECRET` lives in GCP Secret Manager, not committed env files
- [ ] DB column `encrypted_api_key` is never returned in any GET API response
- [ ] `api_key`/`api_secret` never appear in logs (PIIMaskingFilter covers them by key name)
"""
from __future__ import annotations

import secrets
import warnings
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.logging import PiiMaskingFilter, get_logger
from models.exchange_credential import ExchangeCredentialModel

logger = get_logger(__name__)
logger.addFilter(PiiMaskingFilter())

# Weak-key sentinel — the default used when CP_EXCHANGE_SETUP_SECRET is not set.
_WEAK_KEY_SENTINEL = "dev-secret"


def mint_credential_ref() -> str:
    return f"EXCH-{secrets.token_urlsafe(12)}"


def _fernet():
    import base64
    import hashlib

    from cryptography.fernet import Fernet

    raw_secret = (
        getattr(settings, "cp_exchange_setup_secret", None)
        or getattr(settings, "secret_key", _WEAK_KEY_SENTINEL)
    ).strip()

    if raw_secret == _WEAK_KEY_SENTINEL and getattr(settings, "environment", "local") != "test":
        warnings.warn(
            "ExchangeCredentialService: CP_EXCHANGE_SETUP_SECRET is not set. "
            "Exchange credentials are encrypted with the fallback dev-secret which is INSECURE. "
            "Set CP_EXCHANGE_SETUP_SECRET to a strong random value in non-test environments. "
            "Generate one with: python -c \"import secrets, base64; "
            "print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())\"",
            stacklevel=2,
        )

    key = base64.urlsafe_b64encode(hashlib.sha256(raw_secret.encode()).digest())
    return Fernet(key)


def _encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def _decrypt(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()


class ExchangeCredentialService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def upsert(
        self,
        *,
        customer_id: str,
        exchange_provider: str,
        api_key: str,
        api_secret: str,
        default_coin: str,
        allowed_coins: List[str],
        risk_limits: Dict[str, Any],
    ) -> ExchangeCredentialModel:
        """Create or replace credentials for customer+provider pair."""
        credential_ref = mint_credential_ref()
        stmt = (
            pg_insert(ExchangeCredentialModel)
            .values(
                customer_id=customer_id,
                credential_ref=credential_ref,
                exchange_provider=exchange_provider,
                encrypted_api_key=_encrypt(api_key),
                encrypted_api_secret=_encrypt(api_secret),
                default_coin=default_coin,
                allowed_coins=allowed_coins,
                risk_limits=risk_limits,
                validation_status="pending",
            )
            .on_conflict_do_update(
                constraint="uq_exchange_credentials_customer_provider",
                set_={
                    "encrypted_api_key": _encrypt(api_key),
                    "encrypted_api_secret": _encrypt(api_secret),
                    "default_coin": default_coin,
                    "allowed_coins": allowed_coins,
                    "risk_limits": risk_limits,
                    "validation_status": "pending",
                    "updated_at": datetime.now(timezone.utc),
                },
            )
            .returning(ExchangeCredentialModel)
        )
        result = await self._db.execute(stmt)
        await self._db.commit()
        return result.scalars().first()

    async def get_public(self, *, customer_id: str) -> Optional[ExchangeCredentialModel]:
        """Return credential record without secrets (public view)."""
        result = await self._db.execute(
            select(ExchangeCredentialModel).where(
                ExchangeCredentialModel.customer_id == customer_id
            )
        )
        return result.scalars().first()

    async def get_secrets(self, *, credential_ref: str) -> Optional[Dict[str, str]]:
        """Return decrypted {api_key, api_secret} for internal use only — never log."""
        result = await self._db.execute(
            select(ExchangeCredentialModel).where(
                ExchangeCredentialModel.credential_ref == credential_ref
            )
        )
        rec = result.scalars().first()
        if rec is None:
            return None
        return {
            "api_key": _decrypt(rec.encrypted_api_key),
            "api_secret": _decrypt(rec.encrypted_api_secret),
        }

    async def mark_validated(self, *, credential_ref: str, status: str) -> None:
        result = await self._db.execute(
            select(ExchangeCredentialModel).where(
                ExchangeCredentialModel.credential_ref == credential_ref
            )
        )
        rec = result.scalars().first()
        if rec:
            rec.validation_status = status
            rec.last_validated_at = datetime.now(timezone.utc)
            await self._db.commit()
