"""Social platform credential resolver (Plant).

Plant resolves opaque credential_ref values via CP Backend at execution time.
CP Backend holds the encrypted secrets (access_token, refresh_token).

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


def get_default_resolver() -> CPSocialCredentialResolver:
    """Get default social credential resolver.
    
    Reads configuration from environment:
    - CP_BACKEND_URL: CP Backend base URL (default: http://localhost:8001)
    - PLANT_INTERNAL_API_KEY: Internal API key for Plant→CP communication
    """
    cp_base_url = os.getenv("CP_BACKEND_URL", "http://localhost:8001")
    return CPSocialCredentialResolver(cp_base_url=cp_base_url)
