"""Redis response cache for PP ops proxy routes.

Provides a thin async Redis cache that wraps JSON-serializable responses
from the Plant API. Gracefully degrades: if Redis is unavailable or
REDIS_URL is not configured, every cache_get returns None (miss) and
cache_set is a no-op — routes fall back to direct Plant API calls.

Cache keys are scoped to the ops namespace to avoid collisions with other
Redis consumers. TTL defaults to OPS_CACHE_TTL_SECONDS (60 s).
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Optional
from urllib.parse import urlparse

from core.config import settings
from core.logging import PIIMaskingFilter

logger = logging.getLogger(__name__)
logger.addFilter(PIIMaskingFilter())

# Module-level singleton — created lazily on first use.
_redis_client: Any = None


def _effective_db_index(redis_url: str) -> int:
    parsed = urlparse(redis_url)
    path = (parsed.path or "").lstrip("/")
    if not path:
        return 0
    try:
        return int(path.split("/", 1)[0])
    except ValueError:
        return 0


async def _get_redis() -> Optional[Any]:
    """Return the async Redis client, or None if Redis is unavailable."""
    global _redis_client  # noqa: PLW0603

    # Already initialised (may be None if permanently disabled).
    if _redis_client is not None:
        return _redis_client

    redis_url = settings.REDIS_URL
    if not redis_url:
        return None

    try:
        import redis.asyncio as aioredis  # type: ignore[import]

        client = aioredis.from_url(redis_url, decode_responses=True)
        await client.ping()
        _redis_client = client
        logger.info("ops_cache: Redis connected (db_index=%s)", _effective_db_index(redis_url))
        return _redis_client
    except Exception as exc:  # pragma: no cover — only hit when Redis is down
        logger.warning("ops_cache: Redis unavailable — cache disabled: %s", exc)
        return None


def _build_key(namespace: str, path: str, params: Optional[dict] = None) -> str:
    """Build a deterministic, fixed-length cache key.

    Format: ``pp:ops:{namespace}:{sha256_hex[:16]}``
    The hash covers path + sorted JSON params to avoid key collisions.
    """
    params_str = json.dumps(params or {}, sort_keys=True)
    hash_input = f"{path}:{params_str}"
    digest = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    return f"pp:ops:{namespace}:{digest}"


async def cache_get(
    namespace: str,
    path: str,
    params: Optional[dict] = None,
) -> Optional[Any]:
    """Return the cached value for the given key, or None on miss/error.

    Args:
        namespace: Short string scoping the key (e.g. ``"subs"``).
        path: The Plant API path that produced the value.
        params: Query-param dict used in the original request.

    Returns:
        Deserialized cached value, or ``None`` if not found.
    """
    try:
        client = await _get_redis()
        if client is None:
            return None
        key = _build_key(namespace, path, params)
        raw = await client.get(key)
        if raw is not None:
            return json.loads(raw)
    except Exception as exc:
        logger.warning("ops_cache: get error (key=%s) — bypassing cache: %s", path, exc)
    return None


async def cache_set(
    namespace: str,
    path: str,
    value: Any,
    params: Optional[dict] = None,
    ttl_seconds: Optional[int] = None,
) -> None:
    """Store *value* in the cache with a TTL.

    Silently swallows all Redis errors so callers never fail due to caching.

    Args:
        namespace: Short string scoping the key.
        path: The Plant API path that produced the value.
        value: JSON-serializable response body.
        params: Query-param dict used in the original request.
        ttl_seconds: Override the default TTL (``OPS_CACHE_TTL_SECONDS``).
    """
    try:
        client = await _get_redis()
        if client is None:
            return
        key = _build_key(namespace, path, params)
        ttl = ttl_seconds if ttl_seconds is not None else settings.OPS_CACHE_TTL_SECONDS
        await client.set(key, json.dumps(value), ex=ttl)
    except Exception as exc:
        logger.warning("ops_cache: set error (key=%s) — continuing without cache: %s", path, exc)
