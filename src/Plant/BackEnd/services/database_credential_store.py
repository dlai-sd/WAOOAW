"""Database-backed platform credential store (Plant).

Replaces CP's FilePlatformCredentialStore for the credential record index.
Actual secrets live in GCP Secret Manager (prod) or in-memory (dev/CI).
The credential_ref → secret_manager_ref mapping is now in the Plant DB,
so it survives Cloud Run container restarts.

Credential flow:
  1. OAuth callback stores tokens → Secret Manager → gets secret_manager_ref
  2. secret_manager_ref + credential_ref stored in CustomerPlatformCredentialModel
  3. At publish time: look up credential_ref → secret_manager_ref → read Secret Manager
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.customer_platform_credential import CustomerPlatformCredentialModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def mint_credential_ref() -> str:
    """Generate an opaque credential reference identifier."""
    return f"CRED-{secrets.token_urlsafe(12)}"


class CredentialRecord:
    """Resolved credential record with secret references."""

    __slots__ = (
        "credential_ref",
        "customer_id",
        "platform",
        "posting_identity",
        "secret_manager_ref",
        "metadata",
        "created_at",
        "updated_at",
    )

    def __init__(
        self,
        *,
        credential_ref: str,
        customer_id: str,
        platform: str,
        posting_identity: Optional[str] = None,
        secret_manager_ref: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        self.credential_ref = credential_ref
        self.customer_id = customer_id
        self.platform = platform
        self.posting_identity = posting_identity
        self.secret_manager_ref = secret_manager_ref
        self.metadata = metadata or {}
        self.created_at = created_at or _utcnow()
        self.updated_at = updated_at or _utcnow()


class DatabaseCredentialStore:
    """Persistent credential store backed by Plant database.

    Replaces CP's FilePlatformCredentialStore to fix Cloud Run ephemeral-FS bug.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def upsert(
        self,
        *,
        customer_id: str,
        platform: str,
        posting_identity: Optional[str] = None,
        secret_manager_ref: Optional[str] = None,
        credential_ref: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        provider_account_id: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> CredentialRecord:
        """Create or update a credential record in the Plant database."""
        now = _utcnow()

        existing: Optional[CustomerPlatformCredentialModel] = None
        if credential_ref:
            result = await self._db.execute(
                select(CustomerPlatformCredentialModel).where(
                    CustomerPlatformCredentialModel.credential_ref == credential_ref
                )
            )
            existing = result.scalar_one_or_none()

        if existing is None and provider_account_id:
            result = await self._db.execute(
                select(CustomerPlatformCredentialModel)
                .where(CustomerPlatformCredentialModel.customer_id == customer_id)
                .where(CustomerPlatformCredentialModel.platform_key == platform)
                .where(
                    CustomerPlatformCredentialModel.provider_account_id
                    == provider_account_id
                )
            )
            existing = result.scalar_one_or_none()

        if not credential_ref:
            credential_ref = existing.credential_ref if existing and existing.credential_ref else mint_credential_ref()

        if existing is not None:
            existing.credential_ref = credential_ref
            if secret_manager_ref:
                existing.secret_manager_ref = secret_manager_ref
            if posting_identity is not None:
                existing.posting_identity = posting_identity
            if metadata is not None:
                existing.metadata_ = metadata
            if display_name is not None:
                existing.display_name = display_name
            existing.updated_at = now
            await self._db.flush()
            return self._to_record(existing)

        model = CustomerPlatformCredentialModel(
            customer_id=customer_id,
            platform_key=platform,
            provider_account_id=provider_account_id,
            display_name=display_name or posting_identity,
            credential_ref=credential_ref,
            secret_ref=credential_ref,
            secret_manager_ref=secret_manager_ref,
            posting_identity=posting_identity,
            metadata_=metadata or {},
            verification_status="verified",
            connection_status="connected",
            created_at=now,
            updated_at=now,
        )
        self._db.add(model)
        await self._db.flush()
        return self._to_record(model)

    async def get_by_credential_ref(
        self, *, customer_id: str, credential_ref: str
    ) -> Optional[CredentialRecord]:
        """Look up a credential record by its opaque credential_ref."""
        result = await self._db.execute(
            select(CustomerPlatformCredentialModel)
            .where(CustomerPlatformCredentialModel.customer_id == customer_id)
            .where(CustomerPlatformCredentialModel.credential_ref == credential_ref)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_record(model)

    async def get_by_customer_platform(
        self, *, customer_id: str, platform: str
    ) -> Optional[CredentialRecord]:
        """Get the most recent credential for a customer + platform."""
        result = await self._db.execute(
            select(CustomerPlatformCredentialModel)
            .where(CustomerPlatformCredentialModel.customer_id == customer_id)
            .where(CustomerPlatformCredentialModel.platform_key == platform)
            .order_by(CustomerPlatformCredentialModel.updated_at.desc())
        )
        model = result.scalars().first()
        if model is None:
            return None
        return self._to_record(model)

    async def update_secret_manager_ref(
        self, *, credential_ref: str, secret_manager_ref: str
    ) -> bool:
        """Update the Secret Manager reference for a credential."""
        result = await self._db.execute(
            select(CustomerPlatformCredentialModel).where(
                CustomerPlatformCredentialModel.credential_ref == credential_ref
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False
        model.secret_manager_ref = secret_manager_ref
        model.updated_at = _utcnow()
        await self._db.flush()
        return True

    async def list_for_customer(
        self, *, customer_id: str, platform: Optional[str] = None
    ) -> list[CredentialRecord]:
        """List all credentials for a customer, optionally filtered by platform."""
        stmt = select(CustomerPlatformCredentialModel).where(
            CustomerPlatformCredentialModel.customer_id == customer_id
        )
        if platform:
            stmt = stmt.where(
                CustomerPlatformCredentialModel.platform_key == platform
            )
        stmt = stmt.order_by(CustomerPlatformCredentialModel.updated_at.desc())
        result = await self._db.execute(stmt)
        return [self._to_record(m) for m in result.scalars().all()]

    @staticmethod
    def _to_record(model: CustomerPlatformCredentialModel) -> CredentialRecord:
        return CredentialRecord(
            credential_ref=model.credential_ref or model.secret_ref,
            customer_id=model.customer_id,
            platform=model.platform_key,
            posting_identity=model.posting_identity,
            secret_manager_ref=model.secret_manager_ref,
            metadata=dict(model.metadata_ or {}),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
