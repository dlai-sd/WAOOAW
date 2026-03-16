from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import os
import threading
import uuid


@dataclass(frozen=True)
class StoredSecret:
    secret_ref: str
    created_at: datetime


class SecretManagerService:
    _memory_store: dict[str, dict[str, Any]] = {}
    _lock = threading.Lock()

    def __init__(self, *, project_id: str | None = None, prefix: str | None = None) -> None:
        self._project_id = (project_id or os.getenv("GCP_PROJECT_ID") or "waooaw-oauth").strip()
        self._prefix = (prefix or os.getenv("YOUTUBE_TOKEN_SECRET_PREFIX") or "customer-platform").strip()

    def _build_secret_ref(self, *, customer_id: str, platform_key: str, provider_account_id: str | None) -> str:
        account_fragment = (provider_account_id or "pending").replace("/", "-").replace(" ", "-")
        secret_name = f"{self._prefix}-{platform_key}-{customer_id}-{account_fragment}-{uuid.uuid4().hex[:8]}"
        return f"projects/{self._project_id}/secrets/{secret_name}/versions/latest"

    def store_oauth_tokens(
        self,
        *,
        customer_id: str,
        platform_key: str,
        provider_account_id: str | None,
        payload: dict[str, Any],
    ) -> StoredSecret:
        secret_ref = self._build_secret_ref(
            customer_id=customer_id,
            platform_key=platform_key,
            provider_account_id=provider_account_id,
        )
        created_at = datetime.now(timezone.utc)
        with self._lock:
            self._memory_store[secret_ref] = dict(payload)
        return StoredSecret(secret_ref=secret_ref, created_at=created_at)

    def update_access_token(self, *, secret_ref: str, access_token: str, token_expires_at: datetime | None) -> None:
        with self._lock:
            if secret_ref not in self._memory_store:
                self._memory_store[secret_ref] = {}
            self._memory_store[secret_ref]["access_token"] = access_token
            self._memory_store[secret_ref]["token_expires_at"] = token_expires_at.isoformat() if token_expires_at else None

    def get_payload(self, *, secret_ref: str) -> dict[str, Any] | None:
        with self._lock:
            payload = self._memory_store.get(secret_ref)
            return dict(payload) if payload is not None else None


def get_secret_manager_service() -> SecretManagerService:
    return SecretManagerService()