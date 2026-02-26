"""
Redis client utilities for Plant Backend.

Provides both synchronous and async Redis client access, 
lazily initialised from ``settings.redis_url``.
"""

from __future__ import annotations

import logging
from typing import Optional

import redis
import redis.asyncio as aioredis

from core.config import settings

logger = logging.getLogger(__name__)

_sync_client: Optional[redis.Redis] = None
_async_client: Optional[aioredis.Redis] = None


def get_redis() -> redis.Redis:
    """Return a lazily-initialised synchronous Redis client.

    The connection pool is reused across calls within the same process.
    """
    global _sync_client
    if _sync_client is None:
        _sync_client = redis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
    return _sync_client


def get_async_redis() -> aioredis.Redis:
    """Return a lazily-initialised async Redis client.

    Thread-local pools are not required here because this is only called
    from within the asyncio event loop.
    """
    global _async_client
    if _async_client is None:
        _async_client = aioredis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
    return _async_client
