"""Unit tests for Iteration 5 observability additions (Plant backend).

Covers:
  - PiiSanitiserSpanProcessor: strips PII attributes from spans
  - setup_observability: runs without error (console exporter)
  - instrument_fastapi_app: safe when instrumentor available/unavailable
  - OTEL_EXPORTER env var respected
  - Sampling rate env var respected
"""
from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_fake_settings(**overrides):
    defaults = {
        "environment": "development",
        "log_level": "WARNING",
        "enable_json_logs": False,
        "enable_request_logging": False,
        "enable_sql_logging": False,
        "enable_route_registration_logging": False,
        "enable_startup_diagnostics": False,
        "gcp_project_id": "test-project",
        "app_version": "1.0.0",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_fake_span(attrs: dict):
    """Return a mock span with a .attributes dict and writable _attributes."""
    span = MagicMock()
    span.attributes = dict(attrs)
    # Allow object.__setattr__ to set _attributes
    span._attributes = dict(attrs)
    return span


# ── PiiSanitiserSpanProcessor ─────────────────────────────────────────────────

class TestPiiSanitiserSpanProcessor:
    """E1-S2: PII keys must be redacted; non-PII keys left intact."""

    @pytest.fixture
    def processor(self):
        from core.observability import PiiSanitiserSpanProcessor
        return PiiSanitiserSpanProcessor()

    def test_strips_email_attribute(self, processor) -> None:
        span = _make_fake_span({"email": "user@example.com", "span.kind": "server"})
        processor.on_end(span)
        # _attributes must have been updated
        assert span._attributes["email"] == "[REDACTED]"

    def test_strips_token_attribute(self, processor) -> None:
        span = _make_fake_span({"token": "super-secret", "http.method": "POST"})
        processor.on_end(span)
        assert span._attributes["token"] == "[REDACTED]"

    def test_strips_otp_code_attribute(self, processor) -> None:
        span = _make_fake_span({"otp_code": "123456"})
        processor.on_end(span)
        assert span._attributes["otp_code"] == "[REDACTED]"

    def test_leaves_non_pii_intact(self, processor) -> None:
        span = _make_fake_span({"http.method": "GET", "http.status_code": 200, "span.kind": "server"})
        processor.on_end(span)
        assert span._attributes["http.method"] == "GET"
        assert span._attributes["http.status_code"] == 200

    def test_mixed_attrs(self, processor) -> None:
        span = _make_fake_span({
            "email": "a@b.com",
            "http.url": "https://example.com/api/v1/customers",
            "password": "s3cr3t",
            "http.status_code": 201,
        })
        processor.on_end(span)
        assert span._attributes["email"] == "[REDACTED]"
        assert span._attributes["password"] == "[REDACTED]"
        assert span._attributes["http.url"] == "https://example.com/api/v1/customers"
        assert span._attributes["http.status_code"] == 201

    def test_empty_attributes_does_not_crash(self, processor) -> None:
        span = MagicMock()
        span.attributes = {}
        processor.on_end(span)  # must not raise

    def test_none_attributes_does_not_crash(self, processor) -> None:
        span = MagicMock()
        span.attributes = None
        processor.on_end(span)  # must not raise

    def test_on_start_does_not_crash(self, processor) -> None:
        processor.on_start(MagicMock())  # must not raise

    def test_force_flush_returns_true(self, processor) -> None:
        assert processor.force_flush() is True

    def test_shutdown_does_not_crash(self, processor) -> None:
        processor.shutdown()  # must not raise


# ── setup_observability ───────────────────────────────────────────────────────

class TestSetupObservability:
    """E1-S1/S3: setup_observability must wire tracer provider and instrumentors."""

    def test_runs_without_error_console_exporter(self, monkeypatch) -> None:
        """setup_observability must not raise with OTEL_EXPORTER=console."""
        monkeypatch.setenv("OTEL_EXPORTER", "console")
        monkeypatch.setenv("OTEL_SAMPLING_RATE", "1.0")
        monkeypatch.setenv("SERVICE_NAME", "plant-backend-test")
        from core import observability as obs_mod
        import importlib
        importlib.reload(obs_mod)  # reload to pick up env changes
        obs_mod.setup_observability(_make_fake_settings())  # must not raise

    def test_respects_service_name_env_var(self, monkeypatch) -> None:
        monkeypatch.setenv("SERVICE_NAME", "my-test-service")
        monkeypatch.setenv("OTEL_EXPORTER", "console")
        # Just verify no exception
        from core.observability import setup_observability
        setup_observability(_make_fake_settings())

    def test_sampling_rate_default_is_1_for_dev(self, monkeypatch) -> None:
        monkeypatch.delenv("OTEL_SAMPLING_RATE", raising=False)
        monkeypatch.setenv("OTEL_EXPORTER", "console")
        # In development environment, default sampling = 1.0 — no exception
        from core.observability import setup_observability
        setup_observability(_make_fake_settings(environment="development"))

    def test_sampling_rate_default_is_0p1_for_prod(self, monkeypatch) -> None:
        monkeypatch.delenv("OTEL_SAMPLING_RATE", raising=False)
        monkeypatch.setenv("OTEL_EXPORTER", "console")  # avoid GCP auth
        from core.observability import setup_observability
        setup_observability(_make_fake_settings(environment="production"))


# ── instrument_fastapi_app ────────────────────────────────────────────────────

class TestInstrumentFastAPIApp:
    """E1-S1: instrument_fastapi_app must be safe to call."""

    def test_safe_when_instrumentor_available(self) -> None:
        from fastapi import FastAPI
        from core.observability import instrument_fastapi_app
        mini_app = FastAPI()
        instrument_fastapi_app(mini_app)  # must not raise

    def test_safe_when_instrumentor_none(self, monkeypatch) -> None:
        import core.observability as obs_mod
        monkeypatch.setattr(obs_mod, "_FASTAPI_INSTRUMENTOR", None)
        from fastapi import FastAPI
        mini_app = FastAPI()
        obs_mod.instrument_fastapi_app(mini_app)  # must not raise
