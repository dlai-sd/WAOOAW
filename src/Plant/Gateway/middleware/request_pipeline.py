"""US-492-2: API Request Pipeline middleware.

Centralizes cross-cutting gateway concerns:
- Correlation ID minting and propagation via request.state
- Tenant isolation injection via request.state.tenant_id (derived from auth context)
- Request validation against upstream Plant Backend OpenAPI schema
- Circuit breaker for upstream errors (3 errors in 10 seconds)

This middleware is designed to be used in the Plant Gateway only.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from threading import Lock
from typing import Any, Callable, Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from openapi_core import OpenAPI
from openapi_core.contrib.starlette.requests import StarletteOpenAPIRequest
from openapi_core.validation.request.exceptions import OpenAPIError
from openapi_core.validation.schemas.exceptions import InvalidSchemaValue
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


def _now() -> float:
    return time.time()


def _get_header(request: Request, name: str) -> str | None:
    return request.headers.get(name) or request.headers.get(name.lower())


def _mint_correlation_id() -> str:
    return str(uuid.uuid4())


@dataclass(frozen=True)
class CircuitBreakerConfig:
    failure_threshold: int = 3
    window_seconds: int = 10


class CircuitBreaker:
    def __init__(self, config: CircuitBreakerConfig) -> None:
        self._config = config
        self._lock = Lock()
        self._failures: list[float] = []

    def _prune_locked(self, now: float) -> None:
        cutoff = now - float(self._config.window_seconds)
        self._failures = [t for t in self._failures if t >= cutoff]

    def is_open(self) -> bool:
        now = _now()
        with self._lock:
            self._prune_locked(now)
            return len(self._failures) >= self._config.failure_threshold

    def record_failure(self) -> None:
        now = _now()
        with self._lock:
            self._prune_locked(now)
            self._failures.append(now)

    def record_success(self) -> None:
        # Keep it simple: a success clears failure history.
        with self._lock:
            self._failures = []


class OpenApiSpecCache:
    def __init__(self, *, ttl_seconds: int = 60) -> None:
        self._ttl_seconds = max(1, int(ttl_seconds))
        self._lock = Lock()
        self._loaded_at: float | None = None
        self._openapi: OpenAPI | None = None

    def is_fresh(self) -> bool:
        if self._loaded_at is None:
            return False
        return (_now() - self._loaded_at) < float(self._ttl_seconds)

    def get_openapi(self) -> OpenAPI | None:
        with self._lock:
            return self._openapi

    def set_spec(self, spec: dict[str, Any]) -> None:
        with self._lock:
            self._openapi = OpenAPI.from_dict(spec)
            self._loaded_at = _now()


class RequestPipelineMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        http_client_getter: Callable[[], Any],
        backend_url_getter: Callable[[], str],
        spec_cache_ttl_seconds: int = 60,
        validate_openapi: bool = True,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ) -> None:
        super().__init__(app)
        self._http_client_getter = http_client_getter
        self._backend_url_getter = backend_url_getter
        self._validate_openapi = bool(validate_openapi)
        self._spec_cache = OpenApiSpecCache(ttl_seconds=spec_cache_ttl_seconds)
        self._breaker = circuit_breaker or CircuitBreaker(CircuitBreakerConfig())

    def _exempt_from_validation(self, request: Request) -> bool:
        path = (request.url.path or "/").rstrip("/") or "/"
        if request.method.upper() == "OPTIONS":
            return True
        return path in {"/health", "/docs", "/redoc", "/openapi.json"} or path.startswith("/docs/")

    async def _fetch_openapi_spec(self, request: Request) -> dict[str, Any] | None:
        backend_url = (self._backend_url_getter() or "").rstrip("/")
        if not backend_url:
            return None

        url = f"{backend_url}/openapi.json"
        headers: dict[str, str] = {}

        correlation_id = getattr(request.state, "correlation_id", None)
        if correlation_id:
            headers["X-Correlation-ID"] = str(correlation_id)

        client = self._http_client_getter()
        try:
            res = await client.get(url, headers=headers)
        except Exception:
            return None

        if res.status_code != 200:
            return None
        try:
            return res.json()
        except Exception:
            return None

    async def _ensure_openapi(self, request: Request) -> OpenAPI | None:
        openapi = self._spec_cache.get_openapi()
        if openapi is not None and self._spec_cache.is_fresh():
            return openapi

        spec = await self._fetch_openapi_spec(request)
        if not isinstance(spec, dict):
            return None

        try:
            self._spec_cache.set_spec(spec)
        except Exception:
            return None

        return self._spec_cache.get_openapi()

    @staticmethod
    def _openapi_error_strings(exc: Exception) -> list[str]:
        schema_exc = exc.__cause__ if exc.__cause__ is not None else exc.__context__
        if isinstance(schema_exc, InvalidSchemaValue):
            return [str(e) for e in (schema_exc.schema_errors or [])] or [str(exc)]
        return [str(exc)]

    def _set_correlation_id(self, request: Request) -> str:
        corr = (
            _get_header(request, "X-Correlation-ID")
            or _get_header(request, "X-Request-ID")
            or getattr(request.state, "correlation_id", None)
        )
        corr = (str(corr).strip() if corr else "")
        if not corr:
            corr = _mint_correlation_id()
        request.state.correlation_id = corr
        return corr

    def _set_tenant_context(self, request: Request) -> None:
        # Use customer_id as the tenant identifier (fits existing gateway semantics).
        tenant_id = getattr(request.state, "customer_id", None)
        if not (tenant_id or "").strip():
            jwt_claims = getattr(request.state, "jwt", None)
            if isinstance(jwt_claims, dict):
                tenant_id = jwt_claims.get("customer_id") or jwt_claims.get("tenant_id")
        tenant_id = (str(tenant_id).strip() if tenant_id else "")
        if tenant_id:
            request.state.tenant_id = tenant_id

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id = self._set_correlation_id(request)
        self._set_tenant_context(request)

        if self._breaker.is_open():
            return JSONResponse(
                status_code=503,
                content={
                    "type": "https://waooaw.com/errors/service-unavailable",
                    "title": "Service Unavailable",
                    "status": 503,
                    "detail": "Upstream Plant Backend circuit breaker is open",
                    "instance": request.url.path,
                    "correlation_id": correlation_id,
                },
                headers={"X-Correlation-ID": correlation_id},
            )

        if self._validate_openapi and not self._exempt_from_validation(request):
            openapi = await self._ensure_openapi(request)
            if openapi is None:
                return JSONResponse(
                    status_code=503,
                    content={
                        "type": "https://waooaw.com/errors/service-unavailable",
                        "title": "Service Unavailable",
                        "status": 503,
                        "detail": "OpenAPI schema validation is unavailable",
                        "instance": request.url.path,
                        "correlation_id": correlation_id,
                    },
                    headers={"X-Correlation-ID": correlation_id},
                )

            try:
                body_bytes = await request.body()
                openapi_request = StarletteOpenAPIRequest(request, body=body_bytes)
                openapi.validate_request(openapi_request)
            except OpenAPIError as exc:
                return JSONResponse(
                    status_code=422,
                    content={
                        "type": "https://waooaw.com/errors/validation-error",
                        "title": "Validation Error",
                        "status": 422,
                        "detail": "Request does not conform to OpenAPI schema",
                        "errors": self._openapi_error_strings(exc),
                        "instance": request.url.path,
                        "correlation_id": correlation_id,
                    },
                    headers={"X-Correlation-ID": correlation_id},
                )

        response = await call_next(request)

        # Always surface correlation_id on the way out.
        response.headers.setdefault("X-Correlation-ID", correlation_id)

        # Circuit breaker: count upstream failures.
        if response.status_code >= 500:
            self._breaker.record_failure()
        else:
            self._breaker.record_success()

        return response
