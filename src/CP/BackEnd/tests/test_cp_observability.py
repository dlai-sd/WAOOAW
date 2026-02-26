"""Unit tests for CP backend E1-S2 PiiSanitiserSpanProcessor and E1-S1/S3 setup.

Mirrors the Plant backend tests but imports from cp's core.observability module.

Covers:
  - PiiSanitiserSpanProcessor strips PII span attributes
  - setup_observability runs without error
  - instrument_fastapi_app is safe to call
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


def _fake_settings(**kw):
    defaults = dict(
        environment="development",
        log_level="WARNING",
        app_version="1.0.0",
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


def _make_fake_span(attrs: dict):
    span = MagicMock()
    span.attributes = dict(attrs)
    span._attributes = dict(attrs)
    return span


# ── PiiSanitiserSpanProcessor ─────────────────────────────────────────────────

class TestCPPiiSanitiserSpanProcessor:
    """E1-S2: CP backend PII sanitiser must strip sensitive attributes."""

    @pytest.fixture
    def processor(self):
        from core.observability import PiiSanitiserSpanProcessor
        return PiiSanitiserSpanProcessor()

    def test_strips_email(self, processor) -> None:
        span = _make_fake_span({"email": "user@cp.com"})
        processor.on_end(span)
        assert span._attributes["email"] == "[REDACTED]"

    def test_strips_authorization(self, processor) -> None:
        span = _make_fake_span({"authorization": "Bearer abc.def.ghi"})
        processor.on_end(span)
        assert span._attributes["authorization"] == "[REDACTED]"

    def test_leaves_http_method_intact(self, processor) -> None:
        span = _make_fake_span({"http.method": "POST"})
        processor.on_end(span)
        assert span._attributes["http.method"] == "POST"

    def test_empty_attrs_safe(self, processor) -> None:
        span = MagicMock()
        span.attributes = {}
        processor.on_end(span)

    def test_none_attrs_safe(self, processor) -> None:
        span = MagicMock()
        span.attributes = None
        processor.on_end(span)

    def test_force_flush_true(self, processor) -> None:
        assert processor.force_flush() is True


# ── setup_observability ───────────────────────────────────────────────────────

class TestCPSetupObservability:
    """E1-S1/S3: setup_observability wires logging and OTel for CP backend."""

    def test_does_not_raise_console(self, monkeypatch) -> None:
        monkeypatch.setenv("OTEL_EXPORTER", "console")
        monkeypatch.setenv("OTEL_SAMPLING_RATE", "1.0")
        from core.observability import setup_observability
        setup_observability(_fake_settings())

    def test_does_not_raise_production_console_override(self, monkeypatch) -> None:
        """OTEL_EXPORTER=console must work even with environment=production."""
        monkeypatch.setenv("OTEL_EXPORTER", "console")
        from core.observability import setup_observability
        setup_observability(_fake_settings(environment="production"))

    def test_instrument_fastapi_app_safe(self, monkeypatch) -> None:
        monkeypatch.setenv("OTEL_EXPORTER", "console")
        from fastapi import FastAPI
        from core.observability import instrument_fastapi_app
        mini = FastAPI()
        instrument_fastapi_app(mini)  # must not raise

    def test_instrument_fastapi_app_safe_when_no_instrumentor(self, monkeypatch) -> None:
        import core.observability as obs_mod
        monkeypatch.setattr(obs_mod, "_FASTAPI_INSTRUMENTOR", None)
        from fastapi import FastAPI
        obs_mod.instrument_fastapi_app(FastAPI())  # must not raise
