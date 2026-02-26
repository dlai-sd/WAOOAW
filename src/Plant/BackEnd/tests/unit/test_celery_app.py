"""Unit tests for worker/celery_app.py (E1-S1)."""

from __future__ import annotations

import os
import importlib


def test_celery_app_importable() -> None:
    """celery_app module must be importable without a running broker."""
    from worker.celery_app import celery_app  # noqa: PLC0415
    assert celery_app is not None


def test_celery_app_name() -> None:
    from worker.celery_app import celery_app
    assert celery_app.main == "waooaw_plant"


def test_celery_app_default_broker() -> None:
    """Default broker must target Redis DB 4 (not DB 0–3 used by app state)."""
    from worker.celery_app import celery_app
    broker = celery_app.conf.broker_url
    assert broker is not None
    assert "redis://" in broker
    # Default must end with /4
    assert broker.endswith("/4"), f"Expected broker on DB 4, got: {broker}"


def test_celery_app_default_result_backend() -> None:
    """Default result backend must target Redis DB 5."""
    from worker.celery_app import celery_app
    backend = celery_app.conf.result_backend
    assert backend is not None
    assert backend.endswith("/5"), f"Expected result backend on DB 5, got: {backend}"


def test_celery_app_env_override(monkeypatch) -> None:
    """CELERY_BROKER_URL env var must override default."""
    import sys
    # Trigger import so the module is in sys.modules, then grab it directly
    # (worker/__init__.py re-exports celery_app so 'import worker.celery_app as x'
    #  resolves to the Celery *instance*, not the submodule — use sys.modules instead)
    import worker.celery_app  # noqa: F401
    ca_module = sys.modules["worker.celery_app"]
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://myhost:6379/9")
    importlib.reload(ca_module)
    assert "myhost" in ca_module.celery_app.conf.broker_url
    # Restore default
    importlib.reload(ca_module)


def test_celery_app_serializer() -> None:
    from worker.celery_app import celery_app
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.result_serializer == "json"
    assert "json" in celery_app.conf.accept_content


def test_celery_app_acks_late() -> None:
    from worker.celery_app import celery_app
    assert celery_app.conf.task_acks_late is True


def test_celery_app_task_routes() -> None:
    from worker.celery_app import celery_app
    routes = celery_app.conf.task_routes
    assert routes["send_otp_email"]["queue"] == "email"
    assert routes["send_welcome_email"]["queue"] == "email"
    assert routes["handle_customer_registered"]["queue"] == "events"
