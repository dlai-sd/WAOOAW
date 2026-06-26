"""ExchangeCredentialService — DB-backed exchange credential store.

TRADER-FULL-1 S1.
Replaces CP's FileExchangeSetupStore. Plant is the authoritative credential store.
EXCHANGE_SECRET_BACKEND=fernet (default) uses Fernet symmetric encryption.
EXCHANGE_SECRET_BACKEND=secret_manager stores a GCP Secret Manager resource name prefix.
"""
from __future__ import annotations

import secrets
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


def mint_credential_ref() -> str:
    return f"EXCH-{secrets.token_urlsafe(12)}"


def _fernet():
    import base64
    import hashlib

    from cryptography.fernet import Fernet

    secret = (
        getattr(settings, "cp_exchange_setup_secret", None)
        or getattr(settings, "secret_key", "dev-secret")
    ).strip()
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
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
