from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

import redis.asyncio as aioredis

from core.config import settings
from core.logging import PiiMaskingFilter

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())

_redis_client: aioredis.Redis | None = None
_REDIS_CONNECT_TIMEOUT_SECONDS = 2
_REDIS_SOCKET_TIMEOUT_SECONDS = 2
_NAMESPACES = ("cache", "sessions")


async def get_client() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=_REDIS_CONNECT_TIMEOUT_SECONDS,
            socket_timeout=_REDIS_SOCKET_TIMEOUT_SECONDS,
        )
    return _redis_client


def effective_db_index(redis_url: str | None = None) -> int:
    parsed = urlparse(redis_url or settings.redis_url)
    path = (parsed.path or "").lstrip("/")
    if not path:
        return 0
    try:
        return int(path.split("/", 1)[0])
    except ValueError:
        return 0


def namespace_catalog() -> list[str]:
    return list(_NAMESPACES)


def runtime_config() -> dict[str, Any]:
    return {
        "service": "plant-backend",
        "db_index": effective_db_index(),
        "namespaces": namespace_catalog(),
    }


async def health_check() -> dict[str, Any]:
    client = await get_client()
    await client.ping()
    return {
        "status": "ok",
        "redis": "ok",
        "service": "plant-backend",
        "db_index": effective_db_index(),
        "namespaces": namespace_catalog(),
    }


async def invalidate(namespace: str, key: str) -> dict[str, Any]:
    client = await get_client()
    if key == "*":
        pattern = f"plant:{namespace}:*"
        keys = [redis_key async for redis_key in client.scan_iter(match=pattern)]
        deleted = await client.delete(*keys) if keys else 0
        return {"namespace": namespace, "deleted": int(deleted)}

    deleted = await client.delete(f"plant:{namespace}:{key}")
    return {"namespace": namespace, "key": key, "deleted": int(deleted)}
