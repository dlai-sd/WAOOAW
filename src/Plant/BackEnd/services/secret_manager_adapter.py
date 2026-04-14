"""Secret Manager adapter for Plant backend.

Mirrors the CP Backend adapter interface. Toggled via SECRET_MANAGER_BACKEND env var:
  "gcp"   → GcpSecretManagerAdapter  (Cloud Run: demo / uat / prod)
  "local" → LocalSecretManagerAdapter (local dev / CI — in-memory, data lost on restart)

Image promotion: SECRET_MANAGER_BACKEND is injected by Terraform per environment.
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SecretManagerAdapter(ABC):
    """Cloud-portable secret storage interface."""

    @abstractmethod
    async def write_secret(self, secret_id: str, payload: dict) -> str:
        """Write payload and return opaque secret_ref."""

    @abstractmethod
    async def read_secret(self, secret_ref: str) -> dict:
        """Read a secret payload by ref."""

    @abstractmethod
    async def update_secret(self, secret_ref: str, payload: dict) -> str:
        """Write new version, return updated ref."""


class GcpSecretManagerAdapter(SecretManagerAdapter):
    """GCP Secret Manager — same implementation as CP adapter."""

    def __init__(self, project_id: str) -> None:
        from google.cloud import secretmanager  # type: ignore[import]

        self._client = secretmanager.SecretManagerServiceClient()
        self._project = project_id

    async def write_secret(self, secret_id: str, payload: dict) -> str:
        import asyncio
        from google.api_core.exceptions import AlreadyExists  # type: ignore[import]

        parent = f"projects/{self._project}"
        secret_resource = f"{parent}/secrets/{secret_id}"
        loop = asyncio.get_event_loop()

        def _ensure_secret() -> None:
            try:
                self._client.create_secret(
                    request={
                        "parent": parent,
                        "secret_id": secret_id,
                        "secret": {"replication": {"automatic": {}}},
                    }
                )
            except AlreadyExists:
                pass

        def _add_version() -> object:
            return self._client.add_secret_version(
                request={
                    "parent": secret_resource,
                    "payload": {"data": json.dumps(payload).encode("utf-8")},
                }
            )

        await loop.run_in_executor(None, _ensure_secret)
        version = await loop.run_in_executor(None, _add_version)
        return str(version.name)  # type: ignore[union-attr]

    async def read_secret(self, secret_ref: str) -> dict:
        import asyncio

        loop = asyncio.get_event_loop()

        def _access() -> object:
            return self._client.access_secret_version(request={"name": secret_ref})

        response = await loop.run_in_executor(None, _access)
        raw = response.payload.data.decode("utf-8")  # type: ignore[union-attr]
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}

    async def update_secret(self, secret_ref: str, payload: dict) -> str:
        import asyncio

        loop = asyncio.get_event_loop()
        parent = _gcp_secret_parent(secret_ref)

        def _add_version() -> object:
            return self._client.add_secret_version(
                request={
                    "parent": parent,
                    "payload": {"data": json.dumps(payload).encode("utf-8")},
                }
            )

        version = await loop.run_in_executor(None, _add_version)
        return str(version.name)  # type: ignore[union-attr]


class LocalSecretManagerAdapter(SecretManagerAdapter):
    """In-memory adapter for local dev and CI. Data lost on restart."""

    _store: dict[str, str] = {}

    async def write_secret(self, secret_id: str, payload: dict) -> str:
        ref = f"local://secrets/{secret_id}/versions/latest"
        self._store[secret_id] = json.dumps(payload)
        logger.debug("LocalSecretManagerAdapter: stored '%s'", secret_id)
        return ref

    async def read_secret(self, secret_ref: str) -> dict:
        secret_id = _local_secret_id(secret_ref)
        raw = self._store.get(secret_id)
        if not raw:
            return {}
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}

    async def update_secret(self, secret_ref: str, payload: dict) -> str:
        secret_id = _local_secret_id(secret_ref)
        self._store[secret_id] = json.dumps(payload)
        return secret_ref


def _local_secret_id(secret_ref: str) -> str:
    marker = "local://secrets/"
    if not secret_ref.startswith(marker):
        raise ValueError(f"Unsupported local secret ref: {secret_ref}")
    tail = secret_ref[len(marker):]
    return tail.split("/versions/", 1)[0]


def _gcp_secret_parent(secret_ref: str) -> str:
    marker = "/versions/"
    if marker not in secret_ref:
        raise ValueError(f"Unsupported GCP secret ref: {secret_ref}")
    return secret_ref.split(marker, 1)[0]


def get_secret_manager_adapter() -> SecretManagerAdapter:
    """Factory — returns correct adapter based on SECRET_MANAGER_BACKEND env var."""
    backend = (os.getenv("SECRET_MANAGER_BACKEND") or "local").strip().lower()
    if backend == "gcp":
        project_id = (
            os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or ""
        )
        if not project_id:
            raise RuntimeError(
                "GCP_PROJECT_ID env var is required when SECRET_MANAGER_BACKEND=gcp"
            )
        return GcpSecretManagerAdapter(project_id=project_id)
    return LocalSecretManagerAdapter()
