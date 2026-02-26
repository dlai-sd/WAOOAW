"""Idempotency middleware and helpers for Plant Backend write endpoints.

Iteration 3, E2-S1 + E2-S2.

Design:
- Reads ``Idempotency-Key`` header from any POST request to guarded paths.
- First request: passes through normally, caches response in Redis (24h TTL).
- Repeated request with same key + same body hash: returns cached response.
- Repeated request with same key but DIFFERENT body: returns 422 IDEMPOTENCY_KEY_CONFLICT.
- Redis unavailable: skip idempotency, proceed normally (graceful degradation).
- Atomic write via ``SET NX EX`` to avoid race conditions.

Guarded paths (POST only):
  /api/v1/customers
  /api/v1/audit/events

Usage in main.py:
  from services.idempotency import IdempotencyMiddleware
  app.add_middleware(IdempotencyMiddleware)
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# Import here so tests can patch services.idempotency.get_async_redis
try:
    from core.redis_client import get_async_redis
except ImportError:  # pragma: no cover — only missing in stripped test envs
    get_async_redis = None  # type: ignore[assignment]

# Endpoints where idempotency is enforced (POST only)
_GUARDED_PATHS = frozenset([
    "/api/v1/customers",
    "/api/v1/audit/events",
])

_TTL_SECONDS = 86400  # 24 hours
_REDIS_KEY_PREFIX = "idempotency"


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that adds idempotency semantics to POST endpoints.

    Install once:
        app.add_middleware(IdempotencyMiddleware)
    """

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        # Only POST requests to guarded paths
        if request.method != "POST" or request.url.path not in _GUARDED_PATHS:
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            # No key provided — proceed normally
            return await call_next(request)

        # Read body (needed for body-hash check)
        body_bytes: bytes = await request.body()
        body_hash = hashlib.sha256(body_bytes).hexdigest()

        redis_key = f"{_REDIS_KEY_PREFIX}:{request.url.path}:{idempotency_key}"

        try:
            r = get_async_redis()
            cached_raw = await r.get(redis_key)
        except Exception:
            logger.warning(
                "idempotency: Redis unavailable — skipping idempotency check for key=%s",
                idempotency_key,
            )
            # Rebuild consumable request (body was read) and proceed
            return await call_next(_RequestWithCachedBody(request, body_bytes))

        if cached_raw is not None:
            # Cache hit — check body hash matches
            try:
                cached = json.loads(cached_raw)
            except Exception:
                cached = {}

            if cached.get("body_hash") != body_hash:
                return JSONResponse(
                    status_code=422,
                    content={"detail": "IDEMPOTENCY_KEY_CONFLICT"},
                )

            # Return the original cached response
            return JSONResponse(
                status_code=cached.get("status_code", 200),
                content=cached.get("body", {}),
                headers={"X-Idempotency-Replayed": "true"},
            )

        # Cache miss — call the endpoint, then store response
        response = await call_next(_RequestWithCachedBody(request, body_bytes))

        # Only cache successful writes (2xx)
        if 200 <= response.status_code < 300:
            try:
                resp_body = b""
                async for chunk in response.body_iterator:
                    resp_body += chunk if isinstance(chunk, bytes) else chunk.encode()

                body_obj = json.loads(resp_body) if resp_body else {}
                cache_value = json.dumps({
                    "status_code": response.status_code,
                    "body": body_obj,
                    "body_hash": body_hash,
                })

                # SET NX EX — atomic set-if-not-exists with TTL
                try:
                    await r.set(redis_key, cache_value, ex=_TTL_SECONDS, nx=True)
                except Exception:
                    logger.warning(
                        "idempotency: Redis write failed for key=%s — continuing",
                        idempotency_key,
                    )

                return Response(
                    content=resp_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )
            except Exception:
                logger.warning(
                    "idempotency: failed to cache response for key=%s",
                    idempotency_key,
                    exc_info=True,
                )

        return response


class _RequestWithCachedBody(Request):
    """Starlette Request subclass that replays a pre-read body."""

    def __init__(self, request: Request, body: bytes) -> None:
        super().__init__(request.scope, request.receive)
        self._cached_body = body

    async def body(self) -> bytes:  # type: ignore[override]
        return self._cached_body
