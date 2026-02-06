"""Credential resolver (Plant).

Plant must never accept raw exchange keys from browser-originated requests.
Instead, it resolves an opaque `exchange_account_id` via PP/CP backend at
execution time.

MVP: resolve from PP via HTTP (admin/ops assisted). Later: scoped service token
and short-lived signed bundles.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx


@dataclass(frozen=True)
class ResolvedDeltaCredentials:
    api_key: str
    api_secret: str


@dataclass(frozen=True)
class CredentialResolutionError(Exception):
    message: str


class PPCredentialResolver:
    def __init__(
        self,
        *,
        pp_base_url: str,
        bearer_token: Optional[str] = None,
        timeout_seconds: float = 10.0,
        transport: httpx.BaseTransport | httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._pp_base_url = pp_base_url.rstrip("/")
        self._bearer_token = bearer_token
        self._timeout = timeout_seconds
        self._transport = transport

    async def resolve_delta(self, *, exchange_account_id: str, correlation_id: Optional[str] = None) -> ResolvedDeltaCredentials:
        url = f"{self._pp_base_url}/api/pp/exchange-credentials/{exchange_account_id}"
        headers: Dict[str, str] = {}
        if self._bearer_token:
            headers["Authorization"] = f"Bearer {self._bearer_token}"
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id

        try:
            async with httpx.AsyncClient(timeout=self._timeout, transport=self._transport) as client:
                resp = await client.get(url, headers=headers)
        except Exception as exc:  # noqa: BLE001
            raise CredentialResolutionError(f"Failed to contact PP for credentials: {exc}") from exc

        if resp.status_code != 200:
            raise CredentialResolutionError(f"PP returned status {resp.status_code} for credential resolve")

        try:
            data: Dict[str, Any] = resp.json()
        except Exception as exc:  # noqa: BLE001
            raise CredentialResolutionError("PP credential response was not valid JSON") from exc

        api_key = str(data.get("api_key") or "").strip()
        api_secret = str(data.get("api_secret") or "").strip()
        if not api_key or not api_secret:
            raise CredentialResolutionError("PP returned empty credentials")

        return ResolvedDeltaCredentials(api_key=api_key, api_secret=api_secret)
