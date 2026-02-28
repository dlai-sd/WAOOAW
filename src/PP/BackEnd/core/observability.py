"""PP-N2 — OpenTelemetry observability for PP Backend (thin proxy).

Sets up:
- OTel tracer provider (console exporter locally, GCP Cloud Trace in staging/prod)
- FastAPI auto-instrumentation (request spans)
- HTTPX auto-instrumentation (outbound call spans to Plant Gateway)
- W3C TraceContext propagation (traceparent header forwarded to Plant)

All OTel imports are guarded by try/except. If the OTel packages are not
installed (e.g. local dev with requirements_proxy.txt), this module is a no-op.

Environment variables:
  OTEL_EXPORTER        — "console" (default) or "gcp"
  OTEL_SAMPLING_RATE   — float 0.0–1.0 (default 1.0)
  SERVICE_NAME         — OTel service name (default "pp-backend")
  GCP_PROJECT_ID       — required when OTEL_EXPORTER=gcp
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# ── Optional OTel imports ──────────────────────────────────────────────────────

OTEL_AVAILABLE = False
_tracer_provider = None

try:
    import importlib as _il

    _otel_trace = _il.import_module("opentelemetry.trace")
    _sdk = _il.import_module("opentelemetry.sdk.trace")
    _exp = _il.import_module("opentelemetry.sdk.trace.export")
    _smp = _il.import_module("opentelemetry.sdk.trace.sampling")
    _res = _il.import_module("opentelemetry.sdk.resources")

    TracerProvider = _sdk.TracerProvider
    BatchSpanProcessor = _exp.BatchSpanProcessor
    SimpleSpanProcessor = _exp.SimpleSpanProcessor
    ConsoleSpanExporter = _exp.ConsoleSpanExporter
    ParentBasedTraceIdRatio = _smp.ParentBasedTraceIdRatio
    Resource = _res.Resource
    set_tracer_provider = _otel_trace.set_tracer_provider

    OTEL_AVAILABLE = True
except Exception:  # pragma: no cover — OTel optional
    pass

_OTEL_FASTAPI_AVAILABLE = False
try:
    import importlib as _il2

    _fastapi_instr = _il2.import_module(
        "opentelemetry.instrumentation.fastapi"
    )
    FastAPIInstrumentor = _fastapi_instr.FastAPIInstrumentor
    _OTEL_FASTAPI_AVAILABLE = True
except Exception:  # pragma: no cover
    pass

_OTEL_HTTPX_AVAILABLE = False
try:
    import importlib as _il3

    _httpx_instr = _il3.import_module(
        "opentelemetry.instrumentation.httpx"
    )
    HTTPXClientInstrumentor = _httpx_instr.HTTPXClientInstrumentor
    _OTEL_HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    pass


# ── GCP Cloud Trace exporter ───────────────────────────────────────────────────

def _get_exporter():  # pragma: no cover
    exporter_type = os.getenv("OTEL_EXPORTER", "console").lower()
    if exporter_type == "gcp":
        try:
            from opentelemetry.exporter.gcp.trace import CloudTraceSpanExporter  # noqa: PLC0415

            return CloudTraceSpanExporter(
                project_id=os.getenv("GCP_PROJECT_ID", "waooaw-oauth")
            )
        except Exception as exc:
            logger.warning("pp_observability: GCP exporter unavailable — %s", exc)
    # Fall back to console
    if OTEL_AVAILABLE:
        return ConsoleSpanExporter()
    return None


# ── Public API ─────────────────────────────────────────────────────────────────

def setup_pp_observability() -> None:
    """Initialise OTel tracing for the PP service.

    Safe to call even when OTel packages are not installed (no-op).
    Call this once at application startup before creating the FastAPI app
    *or* immediately after — instrumentors work either way.
    """
    if not OTEL_AVAILABLE:
        logger.info("pp_observability: OTel packages not installed — tracing disabled")
        return

    sampling_rate = float(os.getenv("OTEL_SAMPLING_RATE", "1.0"))
    service_name = os.getenv("SERVICE_NAME", "pp-backend")

    resource = Resource.create({"service.name": service_name})
    sampler = ParentBasedTraceIdRatio(sampling_rate)
    provider = TracerProvider(resource=resource, sampler=sampler)

    exporter = _get_exporter()
    if exporter is not None:
        processor_cls = (
            BatchSpanProcessor
            if os.getenv("OTEL_EXPORTER", "console").lower() == "gcp"
            else SimpleSpanProcessor
        )
        provider.add_span_processor(processor_cls(exporter))

    set_tracer_provider(provider)
    global _tracer_provider
    _tracer_provider = provider

    logger.info(
        "pp_observability: OTel tracing enabled — service=%s sampling=%.2f",
        service_name,
        sampling_rate,
    )


def instrument_fastapi_app(app: object) -> None:  # type: ignore[type-arg]
    """Instrument a FastAPI application instance with OTel spans.

    Safe to call when OTel is not available (no-op).
    """
    if not _OTEL_FASTAPI_AVAILABLE:
        return
    try:
        FastAPIInstrumentor().instrument_app(app)  # type: ignore[arg-type]
        logger.debug("pp_observability: FastAPI instrumented")
    except Exception as exc:  # pragma: no cover
        logger.warning("pp_observability: FastAPI instrumentation failed — %s", exc)


def instrument_httpx() -> None:
    """Instrument all httpx clients (sync + async) with OTel spans.

    Safe to call when OTel is not available (no-op).
    """
    if not _OTEL_HTTPX_AVAILABLE:
        return
    try:
        HTTPXClientInstrumentor().instrument()
        logger.debug("pp_observability: httpx instrumented")
    except Exception as exc:  # pragma: no cover
        logger.warning("pp_observability: httpx instrumentation failed — %s", exc)
