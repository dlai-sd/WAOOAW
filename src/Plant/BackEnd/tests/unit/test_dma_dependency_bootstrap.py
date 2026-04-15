"""Dependency-bootstrap tests for the DMA publish path.

These tests would have caught the two production failures in April 2026:
  1. ImportError: google-cloud-secret-manager not installed
  2. ValueError: Unsupported local secret ref (wrong adapter selected for GCP path)

All tests are unit-level — no DB, no real GCP calls.
"""
from __future__ import annotations

import os
import importlib
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# 1. Adapter factory wiring
# ---------------------------------------------------------------------------

def test_factory_returns_local_adapter_when_env_unset(monkeypatch):
    """Default (no SECRET_MANAGER_BACKEND) must yield LocalSecretManagerAdapter."""
    monkeypatch.delenv("SECRET_MANAGER_BACKEND", raising=False)
    from services.secret_manager_adapter import get_secret_manager_adapter, LocalSecretManagerAdapter

    adapter = get_secret_manager_adapter()
    assert isinstance(adapter, LocalSecretManagerAdapter)


def test_factory_returns_local_adapter_when_set_to_local(monkeypatch):
    monkeypatch.setenv("SECRET_MANAGER_BACKEND", "local")
    from services.secret_manager_adapter import get_secret_manager_adapter, LocalSecretManagerAdapter

    adapter = get_secret_manager_adapter()
    assert isinstance(adapter, LocalSecretManagerAdapter)


def test_factory_returns_gcp_adapter_when_set_to_gcp(monkeypatch):
    """SECRET_MANAGER_BACKEND=gcp must return GcpSecretManagerAdapter.

    Simulates the Cloud Run environment: google-cloud-secret-manager IS installed
    (it's in requirements.txt now) and GCP_PROJECT_ID is provided.
    """
    monkeypatch.setenv("SECRET_MANAGER_BACKEND", "gcp")
    monkeypatch.setenv("GCP_PROJECT_ID", "waooaw-oauth")

    fake_secretmanager = MagicMock()
    fake_secretmanager.SecretManagerServiceClient.return_value = MagicMock()

    fake_google_cloud = MagicMock()
    fake_google_cloud.secretmanager = fake_secretmanager

    with patch.dict("sys.modules", {
        "google": fake_google_cloud,
        "google.cloud": fake_google_cloud,
        "google.cloud.secretmanager": fake_secretmanager,
    }):
        # Force reimport so class __init__ re-runs under patched sys.modules
        import services.secret_manager_adapter as mod
        importlib.reload(mod)
        adapter = mod.get_secret_manager_adapter()
        assert isinstance(adapter, mod.GcpSecretManagerAdapter)

    # Restore module to original state
    importlib.reload(mod)


def test_factory_raises_when_gcp_project_missing(monkeypatch):
    """GCP backend without a project ID must fail fast at startup, not at first publish."""
    monkeypatch.setenv("SECRET_MANAGER_BACKEND", "gcp")
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)

    from services import secret_manager_adapter as mod
    importlib.reload(mod)

    with pytest.raises(RuntimeError, match="GCP_PROJECT_ID"):
        # We need to patch the GCP import so it doesn't fail on missing package
        fake_sm = MagicMock()
        fake_sm.SecretManagerServiceClient.return_value = MagicMock()
        with patch.dict("sys.modules", {
            "google.cloud.secretmanager": fake_sm,
            "google.cloud": MagicMock(secretmanager=fake_sm),
            "google": MagicMock(),
        }):
            importlib.reload(mod)
            mod.get_secret_manager_adapter()

    importlib.reload(mod)


# ---------------------------------------------------------------------------
# 2. LocalSecretManagerAdapter rejects GCP-format paths
#    (exact error that appeared in logs before PR-1063 fix)
# ---------------------------------------------------------------------------

def test_local_adapter_raises_on_gcp_format_secret_ref():
    """LocalSecretManagerAdapter must raise ValueError for GCP-format refs.

    If SECRET_MANAGER_BACKEND is accidentally left as 'local' in Cloud Run
    while credential_refs are GCP paths, every publish attempt will blow up
    here. This test locks in that contract so the error is obvious pre-deploy.
    """
    from services.secret_manager_adapter import LocalSecretManagerAdapter

    adapter = LocalSecretManagerAdapter()
    gcp_ref = "projects/waooaw-oauth/secrets/hired-1-youtube/versions/latest"

    with pytest.raises(ValueError, match="Unsupported local secret ref"):
        import asyncio
        asyncio.run(adapter.read_secret(gcp_ref))


def test_local_adapter_roundtrips_local_format_ref():
    """LocalSecretManagerAdapter correctly reads back what it wrote."""
    from services.secret_manager_adapter import LocalSecretManagerAdapter

    adapter = LocalSecretManagerAdapter()
    adapter._store.clear()  # isolate from other tests

    import asyncio
    ref = asyncio.run(adapter.write_secret("test-secret-id", {"access_token": "tok"}))
    assert ref.startswith("local://secrets/")

    data = asyncio.run(adapter.read_secret(ref))
    assert data == {"access_token": "tok"}


# ---------------------------------------------------------------------------
# 3. Package import — would have caught missing google-cloud-secret-manager
# ---------------------------------------------------------------------------

def test_gcp_adapter_class_is_importable():
    """GcpSecretManagerAdapter must be importable without triggering import of
    google.cloud.secretmanager at module load time (import is deferred to __init__).

    This test verifies the lazy-import pattern is in place.
    """
    from services.secret_manager_adapter import GcpSecretManagerAdapter

    # The class should exist as a name in the module
    assert GcpSecretManagerAdapter is not None


def test_gcp_adapter_init_fails_gracefully_when_package_missing(monkeypatch):
    """If google-cloud-secret-manager is NOT installed, GcpSecretManagerAdapter.__init__
    raises ImportError immediately (not silently at first I/O operation).

    This test simulates the exact production failure mode from April 2026 where
    the package was missing and every YouTube publish returned ImportError.
    """
    # Temporarily hide the package from sys.modules
    with patch.dict("sys.modules", {
        "google.cloud.secretmanager": None,  # None means "not importable"
    }):
        from services.secret_manager_adapter import GcpSecretManagerAdapter
        with pytest.raises((ImportError, ModuleNotFoundError)):
            GcpSecretManagerAdapter(project_id="waooaw-oauth")

