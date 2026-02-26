"""Feature flag service — E2-S1 (Iteration 7: Scale Prep).

Provides feature flag evaluation with Redis caching (60-second TTL).
Flags can be enabled globally, by percentage-based rollout, or for specific
customer IDs.

Rollout algorithm (when enabled=true):
  1. customer_id in enabled_for_customer_ids → True
  2. rollout_percentage == 100 → True
  3. hash(customer_id) % 100 < rollout_percentage → True
  4. Otherwise → False
  5. When customer_id is None → evaluate as percentage == 100

Redis cache key: feature_flag:{key} — TTL 60 seconds.
Falls back to DB query when Redis is unavailable.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_REDIS_TTL = 60  # seconds


def _flag_cache_key(key: str) -> str:
    return f"feature_flag:{key}"


def _hash_rollout(customer_id: UUID) -> int:
    """Deterministic 0-99 bucket for a customer UUID."""
    digest = hashlib.md5(str(customer_id).encode(), usedforsecurity=False).hexdigest()
    return int(digest, 16) % 100


class FeatureFlagService:
    """
    Query and evaluate feature flags.

    Args:
        db: SQLAlchemy async session (can be read replica session).
        redis: Optional aioredis / redis-py async client. Falls back to DB if None.
    """

    def __init__(self, db: AsyncSession, redis=None):
        self._db = db
        self._redis = redis

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def is_enabled(
        self,
        key: str,
        customer_id: Optional[UUID] = None,
    ) -> bool:
        """Return True if the feature flag `key` is active for the given customer.

        Args:
            key: Flag identifier string (e.g. ``"new_dashboard_v2"``).
            customer_id: Optional customer UUID for per-customer / rollout checks.

        Returns:
            bool: True if the flag is active, False otherwise (including when
            the flag does not exist — safe default).
        """
        flag = await self._get_flag(key)
        if flag is None:
            return False
        return self._evaluate(flag, customer_id)

    async def list_flags(self, scope: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return all feature flags, optionally filtered by scope.

        Args:
            scope: If given, only flags matching this scope (or scope='all') are returned.

        Returns:
            List of dicts with flag data.
        """
        sql = "SELECT key, enabled, rollout_percentage, enabled_for_customer_ids, scope, description, updated_at FROM feature_flags"
        params: Dict[str, Any] = {}
        if scope and scope != "all":
            sql += " WHERE scope = :scope OR scope = 'all'"
            params["scope"] = scope
        sql += " ORDER BY key"
        result = await self._db.execute(text(sql), params)
        rows = result.mappings().all()
        return [dict(r) for r in rows]

    async def upsert_flag(self, data: Dict[str, Any]) -> None:
        """Create or update a feature flag (admin use).

        Args:
            data: Dict with keys matching feature_flags columns.
        """
        await self._db.execute(
            text(
                """
                INSERT INTO feature_flags
                    (key, enabled, rollout_percentage, enabled_for_customer_ids,
                     scope, description, updated_at)
                VALUES
                    (:key, :enabled, :rollout_percentage, :customer_ids,
                     :scope, :description, NOW())
                ON CONFLICT (key) DO UPDATE SET
                    enabled = EXCLUDED.enabled,
                    rollout_percentage = EXCLUDED.rollout_percentage,
                    enabled_for_customer_ids = EXCLUDED.enabled_for_customer_ids,
                    scope = EXCLUDED.scope,
                    description = EXCLUDED.description,
                    updated_at = NOW()
                """
            ),
            {
                "key": data["key"],
                "enabled": data.get("enabled", False),
                "rollout_percentage": data.get("rollout_percentage", 100),
                "customer_ids": data.get("enabled_for_customer_ids"),
                "scope": data.get("scope", "all"),
                "description": data.get("description"),
            },
        )
        await self._db.commit()
        # Bust cache
        await self._invalidate_cache(data["key"])

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _evaluate(self, flag: Dict[str, Any], customer_id: Optional[UUID]) -> bool:
        if not flag.get("enabled", False):
            return False

        rollout_pct: int = flag.get("rollout_percentage", 100)
        allowlist: List[UUID] = flag.get("enabled_for_customer_ids") or []

        if customer_id is not None:
            # Explicit allowlist takes precedence
            if customer_id in allowlist:
                return True
            if rollout_pct >= 100:
                return True
            if rollout_pct <= 0:
                return False
            return _hash_rollout(customer_id) < rollout_pct

        # No customer context — treat as global: requires 100% rollout
        return rollout_pct >= 100

    async def _get_flag(self, key: str) -> Optional[Dict[str, Any]]:
        """Fetch flag from Redis cache or DB."""
        cache_key = _flag_cache_key(key)

        # 1. Try Redis cache
        if self._redis is not None:
            try:
                raw = await self._redis.get(cache_key)
                if raw:
                    return json.loads(raw)
            except Exception as exc:  # noqa: BLE001
                logger.warning("feature_flag: Redis get failed (falling back to DB): %s", exc)

        # 2. Fall back to DB
        flag = await self._fetch_from_db(key)
        if flag is None:
            return None

        # 3. Populate cache
        if self._redis is not None:
            try:
                await self._redis.set(cache_key, json.dumps(flag, default=str), ex=_REDIS_TTL)
            except Exception as exc:  # noqa: BLE001
                logger.warning("feature_flag: Redis set failed: %s", exc)

        return flag

    async def _fetch_from_db(self, key: str) -> Optional[Dict[str, Any]]:
        result = await self._db.execute(
            text(
                "SELECT key, enabled, rollout_percentage, enabled_for_customer_ids, "
                "scope, description, updated_at FROM feature_flags WHERE key = :key"
            ),
            {"key": key},
        )
        row = result.mappings().first()
        if row is None:
            return None
        return dict(row)

    async def _invalidate_cache(self, key: str) -> None:
        if self._redis is not None:
            try:
                await self._redis.delete(_flag_cache_key(key))
            except Exception as exc:  # noqa: BLE001
                logger.warning("feature_flag: Redis delete failed: %s", exc)
