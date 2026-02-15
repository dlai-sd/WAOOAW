"""
Production-ready observability system with configurable verbosity.

Features:
- Structured logging (JSON or human-readable)
- Request context tracking (request_id, correlation_id, customer_id, trace_id)
- Distributed tracing with Cloud Trace integration
- SQL query logging
- Route registration diagnostics
- Request/response logging middleware
- Environment-based configuration

Usage:
    from core.observability import setup_observability, get_logger, set_request_context
    
    # At app startup
    setup_observability(settings)
    
    # In request handler
    set_request_context(request_id="abc123", customer_id="user-456")
    
    # Logging
    logger = get_logger(__name__)
    logger.info("Processing request", extra={'extra_fields': {'items': 5}})
"""

import logging
import json
import sys
import os
import time
from typing import Any, Optional, Callable
from datetime import datetime
from contextvars import ContextVar
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Cloud Trace support (optional, enabled when dependencies/credentials available)
# Use runtime imports so local dev/test environments without OpenTelemetry don't
# surface import-resolution errors.
TracerProvider = None
BatchSpanProcessor = None
CloudTraceSpanExporter = None
Resource = None
extract = None

try:
    import importlib

    trace = importlib.import_module("opentelemetry.trace")
    TracerProvider = importlib.import_module("opentelemetry.sdk.trace").TracerProvider
    BatchSpanProcessor = importlib.import_module(
        "opentelemetry.sdk.trace.export"
    ).BatchSpanProcessor
    CloudTraceSpanExporter = importlib.import_module(
        "opentelemetry.exporter.cloud_trace"
    ).CloudTraceSpanExporter
    Resource = importlib.import_module("opentelemetry.sdk.resources").Resource
    extract = importlib.import_module("opentelemetry.propagate").extract

    CLOUD_TRACE_AVAILABLE = True
except Exception:
    CLOUD_TRACE_AVAILABLE = False
    trace = None

# Context variables for request tracking across async boundaries
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
customer_id_var: ContextVar[Optional[str]] = ContextVar('customer_id', default=None)
trace_id_var: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)


class JSONFormatter(logging.Formatter):
    """
    JSON formatter with request context for log aggregation systems.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with full context."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "severity": record.levelname,  # GCP uses 'severity'
            "logger": record.name,
            "message": record.getMessage(),
            "source": {
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "file": record.pathname,
            },
            "process": {
                "pid": os.getpid(),
                "thread": record.thread,
            }
        }
        
        # Add request context if available
        request_id = request_id_var.get()
        correlation_id = correlation_id_var.get()
        customer_id = customer_id_var.get()
        trace_id = trace_id_var.get()
        
        if request_id or correlation_id or customer_id or trace_id:
            log_data["context"] = {}
            if request_id:
                log_data["context"]["request_id"] = request_id
            if correlation_id:
                log_data["context"]["correlation_id"] = correlation_id
            if customer_id:
                log_data["context"]["customer_id"] = customer_id
            if trace_id:
                log_data["context"]["trace_id"] = trace_id
                # GCP Cloud Logging trace format
                log_data["logging.googleapis.com/trace"] = trace_id
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "stacktrace": self.formatException(record.exc_info),
            }
        
        # Add extra fields from record
        if hasattr(record, 'extra_fields') and isinstance(record.extra_fields, dict):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Human-readable formatter with colors and context for development.
    """
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format with colors and request context."""
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # Build context string
        context_parts = []
        request_id = request_id_var.get()
        correlation_id = correlation_id_var.get()
        customer_id = customer_id_var.get()
        trace_id = trace_id_var.get()
        
        if request_id:
            context_parts.append(f"req={request_id[:8]}")
        if correlation_id:
            context_parts.append(f"cor={correlation_id[:8]}")
        if customer_id:
            context_parts.append(f"cust={customer_id[:8]}")
        if trace_id:
            context_parts.append(f"trace={trace_id[:16]}")
        
        context_str = f" [{', '.join(context_parts)}]" if context_parts else ""
        
        # Format message
        timestamp = datetime.utcnow().strftime('%H:%M:%S.%f')[:-3]
        log_line = (
            f"{color}{self.BOLD}{record.levelname:8}{self.RESET} "
            f"{timestamp} "
            f"{record.name:30.30} "
            f"{record.funcName:20.20} "
            f"PID:{os.getpid()}{context_str} -"
            f"\n    {record.getMessage()}"
        )
        
        if record.exc_info:
            log_line += "\n" + self.formatException(record.exc_info)
        
        return log_line


def setup_observability(settings: Any) -> None:
    """
    Configure application-wide observability based on settings.
    
    Args:
        settings: Application settings with observability flags
    """
    # Determine log level
    log_level = settings.log_level.upper()
    
    # Choose formatter based on settings
    use_json = settings.enable_json_logs or settings.environment in ["production", "prod", "uat"]
    formatter = JSONFormatter() if use_json else ColoredFormatter()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove only handlers previously installed by this function.
    #
    # Important for tests: pytest's caplog installs its own handler on the root
    # logger; removing it results in empty caplog output across the test suite.
    for handler in root_logger.handlers[:]:
        if getattr(handler, "_waooaw_observability", False):
            root_logger.removeHandler(handler)
    
    # Add console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    setattr(handler, "_waooaw_observability", True)
    root_logger.addHandler(handler)
    
    # Log configuration
    logger = logging.getLogger("core.observability")
    logger.info("=" * 80)
    logger.info("🔍 OBSERVABILITY CONFIGURED")
    logger.info(f"   Environment: {settings.environment}")
    logger.info(f"   Log Level: {log_level}")
    logger.info(f"   JSON Logs: {use_json}")
    logger.info(f"   Request Logging: {settings.enable_request_logging}")
    logger.info(f"   SQL Logging: {settings.enable_sql_logging}")
    logger.info(f"   Route Registration Logging: {settings.enable_route_registration_logging}")
    logger.info(f"   Startup Diagnostics: {settings.enable_startup_diagnostics}")
    logger.info("=" * 80)
    
    # Configure SQLAlchemy logging
    if settings.enable_sql_logging:
        sql_logger = logging.getLogger('sqlalchemy.engine')
        sql_logger.setLevel(logging.INFO)
        logger.info("   ✅ SQL query logging ENABLED")
    else:
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    # Initialize Cloud Trace if available
    if CLOUD_TRACE_AVAILABLE:
        try:
            # Get GCP project ID from settings
            project_id = getattr(settings, 'gcp_project_id', os.getenv('GCP_PROJECT_ID', 'waooaw-demo'))
            
            # Create resource
            resource = Resource.create(attributes={
                "service.name": "waooaw-plant-backend",
                "service.version": getattr(settings, 'version', '1.0.0'),
                "deployment.environment": settings.environment,
            })
            
            # Create tracer provider
            tracer_provider = TracerProvider(resource=resource)
            
            # Add Cloud Trace exporter
            cloud_trace_exporter = CloudTraceSpanExporter(project_id=project_id)
            tracer_provider.add_span_processor(BatchSpanProcessor(cloud_trace_exporter))
            
            # Set global tracer provider
            trace.set_tracer_provider(tracer_provider)
            
            logger.info(f"   ✅ Cloud Trace ENABLED (project: {project_id})")
        except Exception as e:
            logger.warning(f"   ⚠️  Cloud Trace initialization failed: {e}")
            logger.info("   → Continuing without distributed tracing")
    else:
        logger.info("   ℹ️  Cloud Trace SDK not available (install opentelemetry-exporter-gcp-trace)")
    
    # Quiet down noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING if not settings.enable_request_logging else logging.INFO)
    logging.getLogger('httpcore').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance (observability must be configured first).
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        logging.Logger: Logger instance
        
    Example:
        logger = get_logger(__name__)
        logger.info("Processing", extra={'extra_fields': {'user_id': 123}})
    """
    return logging.getLogger(name)


def set_request_context(
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    trace_id: Optional[str] = None
) -> None:
    """
    Set request context for logging across async boundaries.
    
    Args:
        request_id: Unique request ID
        correlation_id: Correlation ID for tracing across services
        customer_id: Customer ID if authenticated
        trace_id: Cloud Trace trace ID
    """
    if request_id:
        request_id_var.set(request_id)
    if correlation_id:
        correlation_id_var.set(correlation_id)
    if customer_id:
        customer_id_var.set(customer_id)
    if trace_id:
        trace_id_var.set(trace_id)


def clear_request_context() -> None:
    """Clear request context after request completion."""
    request_id_var.set(None)
    correlation_id_var.set(None)
    customer_id_var.set(None)
    trace_id_var.set(None)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses.
    Can be enabled in production via ENABLE_REQUEST_LOGGING=true
    """
    
    def __init__(self, app: ASGIApp, enable_logging: bool = True):
        super().__init__(app)
        self.enable_logging = enable_logging
        self.logger = get_logger(__name__)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details with trace context."""
        if not self.enable_logging:
            return await call_next(request)
        
        # Generate request ID if not present
        request_id = request.headers.get("X-Request-ID") or f"{time.time():.6f}"
        correlation_id = request.headers.get("X-Correlation-ID")
        
        # Extract trace context if Cloud Trace is available
        trace_id = None
        tracer = None
        if CLOUD_TRACE_AVAILABLE and trace:
            try:
                tracer = trace.get_tracer(__name__)
                # Extract trace context from headers
                context = extract(request.headers)
                
                # Start a span for this request
                with tracer.start_as_current_span(
                    f"{request.method} {request.url.path}",
                    context=context,
                    attributes={
                        "http.method": request.method,
                        "http.url": str(request.url),
                        "http.target": request.url.path,
                        "http.host": request.url.hostname or "unknown",
                    }
                ) as span:
                    # Get trace ID for logging
                    span_context = span.get_span_context()
                    if span_context and span_context.is_valid:
                        trace_id = f"projects/{os.getenv('GCP_PROJECT_ID', 'waooaw-demo')}/traces/{format(span_context.trace_id, '032x')}"
            except Exception as e:
                self.logger.debug(f"Failed to extract trace context: {e}")
        
        # Set context for all logs during this request
        set_request_context(
            request_id=request_id,
            correlation_id=correlation_id,
            trace_id=trace_id
        )
        
        # Log request
        start_time = time.time()
        self.logger.info(
            f"→ {request.method} {request.url.path}",
            extra={'extra_fields': {
                'http': {
                    'method': request.method,
                    'path': request.url.path,
                    'query': str(request.url.query),
                    'headers': dict(request.headers),
                }
            }}
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            self.logger.info(
                f"← {response.status_code} {request.method} {request.url.path} ({duration_ms:.2f}ms)",
                extra={'extra_fields': {
                    'http': {
                        'status_code': response.status_code,
                        'duration_ms': duration_ms,
                    }
                }}
            )
            
            return response
            
        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(
                f"✗ {request.method} {request.url.path} FAILED ({duration_ms:.2f}ms)",
                exc_info=exc,
                extra={'extra_fields': {
                    'http': {
                        'error': str(exc),
                        'duration_ms': duration_ms,
                    }
                }}
            )
            raise
        finally:
            clear_request_context()


def log_route_registration(app: Any) -> None:
    """
    Log all registered routes for debugging.
    
    Args:
        app: FastAPI application instance
    """
    logger = get_logger("core.observability")
    logger.info("=" * 80)
    logger.info("📍 ROUTE REGISTRATION")
    logger.info("=" * 80)
    
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = ', '.join(sorted(route.methods)) if route.methods else 'N/A'
            routes.append((route.path, methods, type(route).__name__))
    
    # Sort by path
    routes.sort(key=lambda x: x[0])
    
    # Group by prefix
    current_prefix = ""
    for path, methods, route_type in routes:
        # Detect prefix change
        prefix = path.split('/')[1] if '/' in path and len(path.split('/')) > 1 else ""
        if prefix != current_prefix:
            current_prefix = prefix
            logger.info(f"\n  /{prefix}/*")
        
        logger.info(f"    {methods:20} {path:50} ({route_type})")
    
    logger.info(f"\n  Total routes: {len(routes)}")
    logger.info("=" * 80)
