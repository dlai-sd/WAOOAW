"""E1-S1/S2/S3 — OpenTelemetry observability for CP backend.

Sets up:
- Structured JSON/coloured logging
- OTel tracer provider (console exporter locally, GCP Cloud Trace in staging/prod)
- ParentBasedTraceIdRatio sampling (OTEL_SAMPLING_RATE env var)
- PII sanitiser SpanProcessor
- FastAPI, HTTPX, SQLAlchemy auto-instrumentation
- W3C TraceContext propagation (traceparent header)

Environment variables:
  OTEL_EXPORTER        — "console" (default) or "gcp"
  OTEL_SAMPLING_RATE   — float 0.0–1.0 (default 1.0 dev, 0.1 prod)
  SERVICE_NAME         — OTel service name (default "cp-backend")
  GCP_PROJECT_ID       — required when OTEL_EXPORTER=gcp
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from contextvars import ContextVar
from typing import Any, Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# ── Optional OTel imports ─────────────────────────────────────────────────────

TracerProvider = None
BatchSpanProcessor = None
SimpleSpanProcessor = None
ConsoleSpanExporter = None
CloudTraceSpanExporter = None
ParentBasedTraceIdRatio = None
Resource = None
extract = None
set_tracer_provider_fn = None
_otel_trace = None

OTEL_AVAILABLE = False
try:
    import importlib as _il

    _otel_trace = _il.import_module("opentelemetry.trace")
    _sdk = _il.import_module("opentelemetry.sdk.trace")
    _exp = _il.import_module("opentelemetry.sdk.trace.export")
    _smp = _il.import_module("opentelemetry.sdk.trace.sampling")

    TracerProvider = _sdk.TracerProvider
    BatchSpanProcessor = _exp.BatchSpanProcessor
    SimpleSpanProcessor = _exp.SimpleSpanProcessor
    ConsoleSpanExporter = _exp.ConsoleSpanExporter
    ParentBasedTraceIdRatio = _smp.ParentBasedTraceIdRatio
    Resource = _il.import_module("opentelemetry.sdk.resources").Resource
    extract = _il.import_module("opentelemetry.propagate").extract
    set_tracer_provider_fn = _otel_trace.set_tracer_provider

    try:
        CloudTraceSpanExporter = _il.import_module(
            "opentelemetry.exporter.cloud_trace"
        ).CloudTraceSpanExporter
    except Exception:
        CloudTraceSpanExporter = None

    OTEL_AVAILABLE = True
except Exception:
    pass

# Auto-instrumentation
_FASTAPI_INSTRUMENTOR = None
_SQLALCHEMY_INSTRUMENTOR = None
_HTTPX_INSTRUMENTOR = None
try:
    import importlib as _il2

    _FASTAPI_INSTRUMENTOR = _il2.import_module(
        "opentelemetry.instrumentation.fastapi"
    ).FastAPIInstrumentor
    _SQLALCHEMY_INSTRUMENTOR = _il2.import_module(
        "opentelemetry.instrumentation.sqlalchemy"
    ).SQLAlchemyInstrumentor
    _HTTPX_INSTRUMENTOR = _il2.import_module(
        "opentelemetry.instrumentation.httpx"
    ).HTTPXClientInstrumentor
except Exception:
    pass

# ── Context variables ─────────────────────────────────────────────────────────

request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)

# ── E1-S2: PII Sanitiser SpanProcessor ───────────────────────────────────────

_PII_KEYS = frozenset({
    "email", "otp", "otp_code", "password", "token", "secret",
    "api_key", "authorization", "phone", "mobile", "credit_card",
    "card_number", "cvv", "pan",
})
_PII_REDACT = "[REDACTED]"


class PiiSanitiserSpanProcessor:
    """Strips PII values from span attributes before export."""

    def on_start(self, span, parent_context=None):  # noqa: ANN001
        pass

    def on_end(self, span) -> None:  # noqa: ANN001
        try:
            attrs = dict(span.attributes or {})
            changed = False
            for key in list(attrs):
                if any(pii in key.lower() for pii in _PII_KEYS):
                    attrs[key] = _PII_REDACT
                    changed = True
            if changed:
                object.__setattr__(span, "_attributes", attrs)
        except Exception:  # pragma: no cover
            pass

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30_000) -> bool:  # noqa: ARG002
        return True


# ── Formatters ────────────────────────────────────────────────────────────────

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
            "correlation_id": correlation_id_var.get(),
            "trace_id": trace_id_var.get(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


class ColoredFormatter(logging.Formatter):
    _COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    _RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self._COLORS.get(record.levelname, "")
        ts = self.formatTime(record, "%H:%M:%S")
        line = f"{color}[{ts}] {record.levelname:8}{self._RESET} {record.name}: {record.getMessage()}"
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


# ── Middleware ────────────────────────────────────────────────────────────────

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, enable_logging: bool = True):
        super().__init__(app)
        self.enable_logging = enable_logging
        self.logger = logging.getLogger(__name__)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.enable_logging:
            return await call_next(request)

        request_id = request.headers.get("X-Request-ID") or f"{time.time():.6f}"
        correlation_id = request.headers.get("X-Correlation-ID")
        request_id_var.set(request_id)
        correlation_id_var.set(correlation_id)

        start = time.time()
        self.logger.info("→ %s %s", request.method, request.url.path)
        try:
            response = await call_next(request)
            ms = (time.time() - start) * 1000
            self.logger.info("← %d %s %s (%.2fms)", response.status_code, request.method, request.url.path, ms)
            return response
        except Exception as exc:
            ms = (time.time() - start) * 1000
            self.logger.error("✗ %s %s FAILED (%.2fms)", request.method, request.url.path, ms, exc_info=exc)
            raise
        finally:
            request_id_var.set(None)
            correlation_id_var.set(None)


# ── Setup ─────────────────────────────────────────────────────────────────────

def setup_observability(settings: Any) -> None:
    """Configure logging and OTel for CP backend.

    Must be called before app = FastAPI(). Follow up with instrument_fastapi_app(app).
    """
    log_level = getattr(settings, "log_level", "INFO").upper()
    use_json = getattr(settings, "environment", "development") in ("production", "prod", "staging", "uat")
    formatter: logging.Formatter = JSONFormatter() if use_json else ColoredFormatter()

    root = logging.getLogger()
    root.setLevel(log_level)
    for h in root.handlers[:]:
        if getattr(h, "_waooaw_cp_obs", False):
            root.removeHandler(h)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    setattr(handler, "_waooaw_cp_obs", True)
    root.addHandler(handler)

    logger = logging.getLogger("core.observability")
    logger.info("🔍 CP observability configured — env=%s level=%s json=%s",
                getattr(settings, "environment", "?"), log_level, use_json)

    if not OTEL_AVAILABLE:
        logger.info("   ℹ️  OTel SDK not available — tracing disabled")
        return

    try:
        environment = getattr(settings, "environment", "development")
        default_exporter = (
            "gcp" if environment in ("production", "prod", "staging", "uat")
            else "console"
        )
        otel_exporter = os.getenv("OTEL_EXPORTER", default_exporter).lower()

        default_rate = 0.1 if environment in ("production", "prod") else 1.0
        try:
            sample_rate = float(os.getenv("OTEL_SAMPLING_RATE", str(default_rate)))
        except ValueError:
            sample_rate = default_rate

        service_name = os.getenv("SERVICE_NAME", "cp-backend")
        resource = Resource.create({
            "service.name": service_name,
            "service.version": getattr(settings, "app_version", "1.0.0"),
            "deployment.environment": environment,
        })

        tracer_provider = TracerProvider(
            resource=resource,
            sampler=ParentBasedTraceIdRatio(sample_rate),
        )
        tracer_provider.add_span_processor(PiiSanitiserSpanProcessor())

        if otel_exporter == "gcp" and CloudTraceSpanExporter is not None:
            project_id = os.getenv("GCP_PROJECT_ID", "waooaw-demo")
            tracer_provider.add_span_processor(
                BatchSpanProcessor(CloudTraceSpanExporter(project_id=project_id))
            )
            logger.info("   ✅ OTel GCP Cloud Trace exporter (project: %s)", project_id)
        else:
            tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
            logger.info("   ✅ OTel console exporter (local dev)")

        logger.info("   ✅ OTel sampling rate: %.0f%%", sample_rate * 100)

        if set_tracer_provider_fn:
            set_tracer_provider_fn(tracer_provider)

        # Auto-instrument SQLAlchemy and HTTPX now; FastAPI after app creation
        if _SQLALCHEMY_INSTRUMENTOR:
            _SQLALCHEMY_INSTRUMENTOR().instrument()
            logger.info("   ✅ SQLAlchemy auto-instrumentation ENABLED")
        if _HTTPX_INSTRUMENTOR:
            _HTTPX_INSTRUMENTOR().instrument()
            logger.info("   ✅ HTTPX auto-instrumentation ENABLED")

    except Exception as exc:
        logger.warning("   ⚠️  OTel setup failed: %s — continuing without tracing", exc)


def instrument_fastapi_app(app: Any) -> None:
    """E1-S1: Wire FastAPIInstrumentor after app = FastAPI(...)."""
    if _FASTAPI_INSTRUMENTOR is None:
        return
    try:
        _FASTAPI_INSTRUMENTOR().instrument_app(app)
        logging.getLogger("core.observability").info(
            "   ✅ FastAPI auto-instrumentation ENABLED"
        )
    except Exception as exc:  # pragma: no cover
        logging.getLogger("core.observability").warning(
            "   ⚠️  FastAPI instrumentation failed: %s", exc
        )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
