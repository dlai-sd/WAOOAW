"""Security throttling utilities.

REG-1.9: Plant throttles for registration-sensitive endpoints.

Design goals:
- Prefer Redis counters with TTL (shared across replicas).
- Safe fallback to in-memory counters if Redis is unavailable.
- Keep surface minimal and dependency-injectable.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Optional, Protocol, Tuple

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class ThrottleDecision:
    allowed: bool
    retry_after_seconds: Optional[int] = None
    reason: Optional[str] = None


class ThrottleStore(Protocol):
    def get_int(self, key: str) -> Optional[int]: ...

    def set_int_with_ttl(self, key: str, value: int, ttl_seconds: int) -> None: ...

    def incr_with_ttl(self, key: str, ttl_seconds: int) -> int: ...

    def ttl_seconds(self, key: str) -> Optional[int]: ...


class InMemoryThrottleStore:
    def __init__(self) -> None:
        self._data: Dict[str, Tuple[int, float]] = {}

    def _cleanup(self) -> None:
        now = time.time()
        expired = [k for k, (_, exp) in self._data.items() if exp <= now]
        for k in expired:
            self._data.pop(k, None)

    def get_int(self, key: str) -> Optional[int]:
        self._cleanup()
        entry = self._data.get(key)
        if entry is None:
            return None
        return int(entry[0])

    def set_int_with_ttl(self, key: str, value: int, ttl_seconds: int) -> None:
        self._cleanup()
        exp = time.time() + max(1, int(ttl_seconds))
        self._data[key] = (int(value), exp)

    def incr_with_ttl(self, key: str, ttl_seconds: int) -> int:
        self._cleanup()
        now = time.time()
        ttl_seconds = max(1, int(ttl_seconds))

        if key not in self._data:
            self._data[key] = (1, now + ttl_seconds)
            return 1

        value, exp = self._data[key]
        if exp <= now:
            self._data[key] = (1, now + ttl_seconds)
            return 1

        new_value = int(value) + 1
        self._data[key] = (new_value, exp)
        return new_value

    def ttl_seconds(self, key: str) -> Optional[int]:
        self._cleanup()
        entry = self._data.get(key)
        if entry is None:
            return None
        _, exp = entry
        remaining = int(exp - time.time())
        return max(0, remaining)


class RedisThrottleStore:
    def __init__(self, redis_url: str):
        import redis  # local import: keep module importable without redis in some contexts

        self._client = redis.from_url(redis_url, decode_responses=True)

    def get_int(self, key: str) -> Optional[int]:
        raw = self._client.get(key)
        if raw is None:
            return None
        try:
            return int(raw)
        except Exception:
            return None

    def set_int_with_ttl(self, key: str, value: int, ttl_seconds: int) -> None:
        self._client.setex(key, max(1, int(ttl_seconds)), int(value))

    def incr_with_ttl(self, key: str, ttl_seconds: int) -> int:
        # Ensure key exists with TTL. Use pipeline to minimize race windows.
        ttl_seconds = max(1, int(ttl_seconds))
        pipe = self._client.pipeline()
        pipe.incr(key)
        pipe.ttl(key)
        value, ttl = pipe.execute()

        # If no TTL, set it.
        if ttl in (-1, -2):
            try:
                self._client.expire(key, ttl_seconds)
            except Exception:
                pass

        return int(value)

    def ttl_seconds(self, key: str) -> Optional[int]:
        ttl = self._client.ttl(key)
        if ttl is None:
            return None
        if ttl < 0:
            return None
        return int(ttl)


_in_memory_fallback_store = InMemoryThrottleStore()


def default_throttle_store() -> ThrottleStore:
    """Return a best-effort store.

    If Redis is down/unreachable, fall back to in-memory counters.
    """

    url = getattr(settings, "redis_url", None)
    if not url:
        return _in_memory_fallback_store

    try:
        store = RedisThrottleStore(url)
        # Ping to validate connectivity.
        store._client.ping()  # type: ignore[attr-defined]
        return store
    except Exception:
        logger.warning("Redis unavailable for throttling; falling back to in-memory store")
        return _in_memory_fallback_store


class SecurityThrottle:
    def __init__(
        self,
        store: ThrottleStore,
        *,
        max_attempts: int,
        window_seconds: int,
        lockout_seconds: int,
    ) -> None:
        self._store = store
        self._max_attempts = max(1, int(max_attempts))
        self._window_seconds = max(1, int(window_seconds))
        self._lockout_seconds = max(1, int(lockout_seconds))

    def check(self, *, scope: str, subject: str) -> ThrottleDecision:
        """Check and increment attempt counters for a (scope, subject) pair."""

        scope = (scope or "").strip() or "default"
        subject = (subject or "").strip() or "unknown"

        lockout_key = f"throttle:{scope}:{subject}:lockout"
        attempts_key = f"throttle:{scope}:{subject}:attempts"

        lockout_remaining = self._store.ttl_seconds(lockout_key)
        if lockout_remaining is not None and lockout_remaining > 0:
            return ThrottleDecision(
                allowed=False,
                retry_after_seconds=lockout_remaining,
                reason="locked_out",
            )

        attempts = self._store.incr_with_ttl(attempts_key, self._window_seconds)

        if attempts > self._max_attempts:
            self._store.set_int_with_ttl(lockout_key, 1, self._lockout_seconds)
            return ThrottleDecision(
                allowed=False,
                retry_after_seconds=self._lockout_seconds,
                reason="too_many_attempts",
            )

        return ThrottleDecision(allowed=True)


def get_security_throttle() -> SecurityThrottle:
    return SecurityThrottle(
        default_throttle_store(),
        max_attempts=getattr(settings, "security_customer_upsert_max_attempts", 10),
        window_seconds=getattr(settings, "security_customer_upsert_window_seconds", 60),
        lockout_seconds=getattr(settings, "security_customer_upsert_lockout_seconds", 300),
    )
