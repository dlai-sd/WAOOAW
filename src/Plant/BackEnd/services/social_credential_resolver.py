"""Social platform credential resolver (Plant).

Phase 1 (legacy): Plant resolves opaque credential_ref via CP Backend HTTP API.
Phase 2 (current): Plant resolves directly from its own DB + Secret Manager,
    eliminating the dependency on CP's ephemeral JSONL file store.

SECURITY: Plant never receives raw credentials from browser traffic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import os

import httpx


@dataclass(frozen=True)
class ResolvedSocialCredentials:
    """Resolved social platform credentials."""
    credential_ref: str
    customer_id: str
    platform: str
    posting_identity: Optional[str]
    access_token: str
    refresh_token: Optional[str]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class StoredSocialCredentials:
    credential_ref: str
    customer_id: str
    platform: str
    posting_identity: Optional[str]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class CredentialResolutionError(Exception):
    """Error resolving credentials from CP Backend."""
    message: str


class CPSocialCredentialResolver:
    """Resolves social platform credentials via CP Backend internal API."""
    
    def __init__(
        self,
        *,
        cp_base_url: str,
        internal_api_key: Optional[str] = None,
        timeout_seconds: float = 10.0,
        transport: httpx.BaseTransport | httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._cp_base_url = cp_base_url.rstrip("/")
        self._internal_api_key = internal_api_key or os.getenv("PLANT_INTERNAL_API_KEY", "dev-plant-internal-key")
        self._timeout = timeout_seconds
        self._transport = transport

    async def resolve(
        self, 
        *, 
        customer_id: str, 
        credential_ref: str, 
        correlation_id: Optional[str] = None
    ) -> ResolvedSocialCredentials:
        """Resolve credential_ref to actual secrets for social platform posting.
        
        Args:
            customer_id: Customer ID (e.g., "CUST-123")
            credential_ref: Opaque credential reference (e.g., "CRED-xyz")
            correlation_id: Optional correlation ID for tracing
            
        Returns:
            ResolvedSocialCredentials with access_token, refresh_token
            
        Raises:
            CredentialResolutionError: If resolution fails
        """
        url = f"{self._cp_base_url}/api/internal/plant/credentials/resolve"
        headers: Dict[str, str] = {
            "X-Plant-Internal-Key": self._internal_api_key,
            "Content-Type": "application/json",
        }
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id

        try:
            async with httpx.AsyncClient(timeout=self._timeout, transport=self._transport) as client:
                resp = await client.post(
                    url,
                    headers=headers,
                    json={
                        "customer_id": customer_id,
                        "credential_ref": credential_ref,
                    },
                )
        except Exception as exc:  # noqa: BLE001
            raise CredentialResolutionError(f"Failed to contact CP for credentials: {exc}") from exc

        if resp.status_code == 404:
            raise CredentialResolutionError(
                f"Credential not found: {credential_ref} for customer {customer_id}"
            )
        
        if resp.status_code != 200:
            raise CredentialResolutionError(
                f"CP returned status {resp.status_code} for credential resolve"
            )

        try:
            data: Dict[str, Any] = resp.json()
        except Exception as exc:  # noqa: BLE001
            raise CredentialResolutionError("CP credential response was not valid JSON") from exc

        access_token = str(data.get("access_token") or "").strip()
        if not access_token:
            raise CredentialResolutionError("CP returned empty access_token")

        return ResolvedSocialCredentials(
            credential_ref=data["credential_ref"],
            customer_id=data["customer_id"],
            platform=data["platform"],
            posting_identity=data.get("posting_identity"),
            access_token=access_token,
            refresh_token=data.get("refresh_token"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    async def update_access_token(
        self, 
        *, 
        customer_id: str, 
        credential_ref: str, 
        new_access_token: str,
        correlation_id: Optional[str] = None
    ) -> None:
        """Update access_token in CP Backend after OAuth2 refresh.
        
        Args:
            customer_id: Customer ID
            credential_ref: Credential reference
            new_access_token: New access token from OAuth2 refresh
            correlation_id: Optional correlation ID for tracing
            
        Raises:
            CredentialResolutionError: If update fails
        """
        url = f"{self._cp_base_url}/api/internal/plant/credentials/update-token"
        headers: Dict[str, str] = {
            "X-Plant-Internal-Key": self._internal_api_key,
            "Content-Type": "application/json",
        }
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id

        try:
            async with httpx.AsyncClient(timeout=self._timeout, transport=self._transport) as client:
                resp = await client.post(
                    url,
                    headers=headers,
                    json={
                        "customer_id": customer_id,
                        "credential_ref": credential_ref,
                        "new_access_token": new_access_token,
                    },
                )
        except Exception as exc:  # noqa: BLE001
            raise CredentialResolutionError(f"Failed to contact CP for token update: {exc}") from exc

        if resp.status_code != 200:
            raise CredentialResolutionError(
                f"CP returned status {resp.status_code} for token update"
            )

    async def upsert(
        self,
        *,
        customer_id: str,
        platform: str,
        posting_identity: Optional[str],
        access_token: str,
        refresh_token: Optional[str],
        credential_ref: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
    ) -> StoredSocialCredentials:
        url = f"{self._cp_base_url}/api/internal/plant/credentials/upsert"
        headers: Dict[str, str] = {
            "X-Plant-Internal-Key": self._internal_api_key,
            "Content-Type": "application/json",
        }
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id

        try:
            async with httpx.AsyncClient(timeout=self._timeout, transport=self._transport) as client:
                resp = await client.post(
                    url,
                    headers=headers,
                    json={
                        "customer_id": customer_id,
                        "platform": platform,
                        "posting_identity": posting_identity,
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "credential_ref": credential_ref,
                        "metadata": metadata or {},
                    },
                )
        except Exception as exc:  # noqa: BLE001
            raise CredentialResolutionError(f"Failed to contact CP for credential upsert: {exc}") from exc

        if resp.status_code != 200:
            raise CredentialResolutionError(
                f"CP returned status {resp.status_code} for credential upsert"
            )

        try:
            data: Dict[str, Any] = resp.json()
        except Exception as exc:  # noqa: BLE001
            raise CredentialResolutionError("CP credential upsert response was not valid JSON") from exc

        stored_ref = str(data.get("credential_ref") or "").strip()
        if not stored_ref:
            raise CredentialResolutionError("CP credential upsert returned empty credential_ref")

        return StoredSocialCredentials(
            credential_ref=stored_ref,
            customer_id=str(data.get("customer_id") or customer_id),
            platform=str(data.get("platform") or platform),
            posting_identity=data.get("posting_identity"),
            created_at=str(data.get("created_at") or ""),
            updated_at=str(data.get("updated_at") or ""),
        )


def get_default_resolver() -> CPSocialCredentialResolver:
    """Get default social credential resolver.
    
    Reads configuration from environment:
    - CP_BACKEND_URL: CP Backend base URL (default: http://localhost:8001)
    - PLANT_INTERNAL_API_KEY: Internal API key for Plant→CP communication
    """
    cp_base_url = os.getenv("CP_BACKEND_URL", "http://localhost:8001")
    return CPSocialCredentialResolver(cp_base_url=cp_base_url)


class DatabaseCredentialResolver:
    """Resolve credentials directly from Plant DB + Secret Manager.

    Replaces the CP HTTP round-trip with a direct DB lookup + Secret Manager read.
    This eliminates the dependency on CP's ephemeral JSONL file store.
    """

    def __init__(self, db: "AsyncSession") -> None:  # noqa: F821
        self._db = db

    async def resolve(
        self,
        *,
        customer_id: str,
        credential_ref: str,
        correlation_id: Optional[str] = None,
    ) -> ResolvedSocialCredentials:
        from services.database_credential_store import DatabaseCredentialStore

        store = DatabaseCredentialStore(self._db)
        record = await store.get_by_credential_ref(
            customer_id=customer_id, credential_ref=credential_ref
        )
        if record is None:
            raise CredentialResolutionError(
                f"Credential not found in Plant DB: {credential_ref} for customer {customer_id}"
            )

        if not record.secret_manager_ref:
            raise CredentialResolutionError(
                f"No secret_manager_ref for credential {credential_ref}"
            )

        from services.secret_manager_adapter import get_secret_manager_adapter

        adapter = get_secret_manager_adapter()
        secrets = await adapter.read_secret(record.secret_manager_ref)
        if not secrets:
            raise CredentialResolutionError(
                f"Secret Manager returned empty payload for {credential_ref}"
            )

        access_token = str(secrets.get("access_token") or "").strip()
        if not access_token:
            raise CredentialResolutionError(
                f"No access_token in Secret Manager for {credential_ref}"
            )

        return ResolvedSocialCredentials(
            credential_ref=record.credential_ref,
            customer_id=record.customer_id,
            platform=record.platform,
            posting_identity=record.posting_identity,
            access_token=access_token,
            refresh_token=secrets.get("refresh_token"),
            created_at=record.created_at.isoformat() if record.created_at else "",
            updated_at=record.updated_at.isoformat() if record.updated_at else "",
        )

    async def update_access_token(
        self,
        *,
        customer_id: str,
        credential_ref: str,
        new_access_token: str,
        correlation_id: Optional[str] = None,
    ) -> None:
        from services.database_credential_store import DatabaseCredentialStore
        from services.secret_manager_adapter import get_secret_manager_adapter

        store = DatabaseCredentialStore(self._db)
        record = await store.get_by_credential_ref(
            customer_id=customer_id, credential_ref=credential_ref
        )
        if record is None or not record.secret_manager_ref:
            raise CredentialResolutionError(
                f"Credential not found for token update: {credential_ref}"
            )

        adapter = get_secret_manager_adapter()
        secrets = await adapter.read_secret(record.secret_manager_ref)
        secrets["access_token"] = new_access_token
        new_ref = await adapter.update_secret(record.secret_manager_ref, secrets)
        await store.update_secret_manager_ref(
            credential_ref=credential_ref, secret_manager_ref=new_ref
        )

    async def upsert(
        self,
        *,
        customer_id: str,
        platform: str,
        posting_identity: Optional[str],
        access_token: str,
        refresh_token: Optional[str],
        credential_ref: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        provider_account_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> StoredSocialCredentials:
        from services.database_credential_store import DatabaseCredentialStore
        from services.secret_manager_adapter import get_secret_manager_adapter

        store = DatabaseCredentialStore(self._db)
        adapter = get_secret_manager_adapter()

        cred_ref = credential_ref or ""
        secret_id = _build_secret_id(customer_id, platform, cred_ref)

        secrets_payload = {"access_token": access_token}
        if refresh_token:
            secrets_payload["refresh_token"] = refresh_token

        secret_manager_ref = await adapter.write_secret(secret_id, secrets_payload)

        record = await store.upsert(
            customer_id=customer_id,
            platform=platform,
            posting_identity=posting_identity,
            secret_manager_ref=secret_manager_ref,
            credential_ref=credential_ref,
            metadata=metadata,
            provider_account_id=provider_account_id,
        )

        return StoredSocialCredentials(
            credential_ref=record.credential_ref,
            customer_id=record.customer_id,
            platform=record.platform,
            posting_identity=record.posting_identity,
            created_at=record.created_at.isoformat() if record.created_at else "",
            updated_at=record.updated_at.isoformat() if record.updated_at else "",
        )


def _build_secret_id(customer_id: str, platform: str, credential_ref: str) -> str:
    import re

    raw = f"cp-social-{customer_id}-{platform}-{credential_ref}".lower()
    normalised = re.sub(r"[^a-z0-9_-]", "-", raw)
    return normalised[:255]
