from __future__ import annotations

import asyncio
import logging
import os
from decimal import Decimal
from typing import Optional
from urllib.parse import urlparse

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

_redis_client: Optional[aioredis.Redis] = None
_REDIS_CONNECT_TIMEOUT_SECONDS = 0.25
_REDIS_SOCKET_TIMEOUT_SECONDS = 0.25


def _redis_url() -> str:
    return os.getenv("REDIS_URL", "redis://localhost:6379")


async def get_client() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.Redis.from_url(
            _redis_url(),
            decode_responses=True,
            socket_connect_timeout=_REDIS_CONNECT_TIMEOUT_SECONDS,
            socket_timeout=_REDIS_SOCKET_TIMEOUT_SECONDS,
        )
    return _redis_client


def effective_db_index(redis_url: str | None = None) -> int:
    parsed = urlparse(redis_url or _redis_url())
    path = (parsed.path or "").lstrip("/")
    if not path:
        return 0
    try:
        return int(path.split("/", 1)[0])
    except ValueError:
        return 0


async def is_access_token_revoked(jti: str) -> bool:
    client = await get_client()
    return bool(await client.exists(f"revoked_access:{jti}"))


async def get_token_version(user_id: str) -> str | None:
    client = await get_client()
    return await client.get(f"token_version:{user_id}")


async def mark_token_revoked(jti: str, ttl_seconds: int | None = None) -> None:
    client = await get_client()
    await client.set(f"revoked_access:{jti}", "1", ex=ttl_seconds)


async def _apply_budget_update(
    agent_id: str | None,
    customer_id: str,
    cost: Decimal,
) -> None:
    client = await get_client()
    await client.hincrbyfloat("platform_budget", "spent_usd", float(cost))
    if agent_id:
        await client.hincrbyfloat(f"agent_budgets:{agent_id}", "spent_usd", float(cost))
    await client.hincrbyfloat(f"customer_budgets:{customer_id}", "spent_usd", float(cost))


async def enqueue_budget_update(
    agent_id: str | None,
    customer_id: str,
    cost: Decimal,
) -> None:
    async def _runner() -> None:
        try:
            await _apply_budget_update(agent_id, customer_id, cost)
        except Exception as exc:  # pragma: no cover - logged by callers/tests
            logger.error("Failed to update budget in Redis: %s", exc)

    asyncio.create_task(_runner())
