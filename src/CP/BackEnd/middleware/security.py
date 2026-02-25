"""CP Security middleware.

Adds to every response:
- Correlation-ID  (X-Request-ID in, X-Correlation-ID out + propagated to Plant)
- Security headers (CSP, HSTS, X-Frame-Options, etc.)
- Consistent error wrapper for unhandled exceptions

Item 5: Consistent error format  { "error": { "code", "message", "detail", "correlation_id" } }
Item 7: CSP + security headers as a single middleware
Item 8: Correlation ID flowing CP → Plant (stored in request.state for httpx calls)
"""

from __future__ import annotations

import logging
import uuid

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

_CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://challenges.cloudflare.com; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "connect-src 'self' https://challenges.cloudflare.com; "
    "frame-src https://challenges.cloudflare.com; "
    "font-src 'self' data:; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self';"
)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Add security headers and correlation IDs to every request/response."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        # Generate or propagate correlation ID
        correlation_id = (
            request.headers.get("X-Request-ID")
            or request.headers.get("X-Correlation-ID")
            or str(uuid.uuid4())
        )
        # Make available to route handlers and httpx calls via request.state
        request.state.correlation_id = correlation_id

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            logger.exception("Unhandled exception correlation_id=%s", correlation_id)
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred",
                        "detail": str(exc),
                        "correlation_id": correlation_id,
                    }
                },
                headers={"X-Correlation-ID": correlation_id},
            )

        # Add security headers
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = _CSP_POLICY
        # HSTS (only meaningful over HTTPS, harmless over HTTP)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


def get_correlation_id(request: Request) -> str:
    """Dependency: return correlation ID from request state (set by SecurityMiddleware)."""
    return getattr(request.state, "correlation_id", str(uuid.uuid4()))
