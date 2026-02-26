"""PlantClient — single point for all CP→Plant HTTP calls with circuit breaker.

Iteration 3, E1-S1 + E1-S2.

Architecture:
- All CP backend code that calls Plant must go through PlantClient.
- A lightweight in-memory CircuitBreaker wraps every call.
- Circuit opens after 3 failures within 10 seconds, recovers after 30 seconds.
- When open: raises ServiceUnavailableError immediately (no HTTP call made).
- Failure conditions: HTTP 5xx, connection error, timeout.
- Success conditions: HTTP 1xx-4xx (4xx = valid response, not a circuit fault).

Usage:
    from services.plant_client import PlantClient, ServiceUnavailableError

    client = PlantClient(base_url=settings.PLANT_GATEWAY_URL)
    try:
        resp = await client.post("/api/v1/customers", json=payload, headers=hdrs)
    except ServiceUnavailableError:
        raise HTTPException(503, ...)
"""

from __future__ import annotations

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Circuit-breaker constants (matches spec in iteration-3-reliability.md)
# ---------------------------------------------------------------------------
_FAILURE_THRESHOLD = 3       # failures before opening
_FAILURE_WINDOW_SECS = 10    # rolling window for counting failures
_COOLDOWN_SECS = 30          # time to stay open before moving to half-open
_DEFAULT_TIMEOUT = 10.0      # httpx timeout in seconds


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ServiceUnavailableError(Exception):
    """Raised when the circuit is open and Plant is not reachable."""

    def __init__(self, message: str = "Plant backend is temporarily unavailable") -> None:
        super().__init__(message)
        self.retry_after: int = _COOLDOWN_SECS


# ---------------------------------------------------------------------------
# Circuit breaker state machine
# ---------------------------------------------------------------------------

class _State(str, Enum):
    CLOSED = "CLOSED"      # Normal — all requests pass through
    OPEN = "OPEN"          # Failing — requests blocked immediately
    HALF_OPEN = "HALF_OPEN"  # Probing — one request allowed through


class CircuitBreaker:
    """Lightweight in-memory circuit breaker.

    Not thread-safe across asyncio tasks at the counter-increment level but
    safe enough for a single-instance service. For multi-instance, swap
    counters for Redis atomics.
    """

    def __init__(
        self,
        *,
        failure_threshold: int = _FAILURE_THRESHOLD,
        failure_window_secs: float = _FAILURE_WINDOW_SECS,
        cooldown_secs: float = _COOLDOWN_SECS,
    ) -> None:
        self._threshold = failure_threshold
        self._window = failure_window_secs
        self._cooldown = cooldown_secs

        self._state = _State.CLOSED
        self._failure_timestamps: list[float] = []
        self._opened_at: float = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def state(self) -> _State:
        self._maybe_transition()
        return self._state

    def record_success(self) -> None:
        """Call after a successful upstream response."""
        self._failure_timestamps.clear()
        if self._state in (_State.OPEN, _State.HALF_OPEN):
            logger.info("circuit_breaker: probe succeeded — circuit CLOSED")
        self._state = _State.CLOSED

    def record_failure(self) -> None:
        """Call after a 5xx response, connection error, or timeout."""
        now = time.monotonic()
        self._failure_timestamps.append(now)
        # Trim timestamps outside the rolling window
        cutoff = now - self._window
        self._failure_timestamps = [t for t in self._failure_timestamps if t >= cutoff]

        if self._state == _State.HALF_OPEN:
            # Probe failed — re-open
            logger.warning("circuit_breaker: probe failed — circuit re-OPENED for %ds", self._cooldown)
            self._state = _State.OPEN
            self._opened_at = now
        elif len(self._failure_timestamps) >= self._threshold:
            if self._state == _State.CLOSED:
                logger.warning(
                    "circuit_breaker: %d failures in %.0fs — circuit OPENED",
                    len(self._failure_timestamps),
                    self._window,
                )
                self._state = _State.OPEN
                self._opened_at = now

    def is_call_permitted(self) -> bool:
        """Return True if the call should proceed; False if it should be blocked."""
        self._maybe_transition()
        if self._state == _State.CLOSED:
            return True
        if self._state == _State.HALF_OPEN:
            # Allow one probe through (caller must ensure single-flight but
            # for a simple service this is fine)
            return True
        # OPEN
        return False

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _maybe_transition(self) -> None:
        """Transition OPEN → HALF_OPEN when cooldown expires."""
        if self._state == _State.OPEN:
            elapsed = time.monotonic() - self._opened_at
            if elapsed >= self._cooldown:
                logger.info(
                    "circuit_breaker: cooldown expired (%.1fs) — entering HALF_OPEN",
                    elapsed,
                )
                self._state = _State.HALF_OPEN


# ---------------------------------------------------------------------------
# Plant HTTP client
# ---------------------------------------------------------------------------

# Module-level circuit breaker instance (shared across all PlantClient instances)
_circuit_breaker = CircuitBreaker()


class PlantClient:
    """Async HTTP client for CP→Plant calls, protected by a circuit breaker.

    Instantiate once per application (or per request via FastAPI dependency).
    """

    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float = _DEFAULT_TIMEOUT,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._cb = circuit_breaker or _circuit_breaker

    async def post(
        self,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make a POST request to Plant. Raises ServiceUnavailableError if circuit is open."""
        return await self._request("POST", path, json=json, headers=headers)

    async def get(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Make a GET request to Plant. Raises ServiceUnavailableError if circuit is open."""
        return await self._request("GET", path, params=params, headers=headers)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        if not self._cb.is_call_permitted():
            raise ServiceUnavailableError()

        url = f"{self._base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.request(
                    method,
                    url,
                    json=json,
                    params=params,
                    headers=headers or {},
                )
        except httpx.TimeoutException as exc:
            logger.warning("plant_client: timeout %s %s", method, path)
            self._cb.record_failure()
            raise ServiceUnavailableError("Request to Plant timed out") from exc
        except httpx.ConnectError as exc:
            logger.warning("plant_client: connect error %s %s: %s", method, path, exc)
            self._cb.record_failure()
            raise ServiceUnavailableError("Cannot connect to Plant backend") from exc
        except Exception as exc:
            logger.warning("plant_client: unexpected error %s %s: %s", method, path, exc)
            self._cb.record_failure()
            raise ServiceUnavailableError(str(exc)) from exc

        # 5xx = circuit fault; 1xx-4xx = valid Plant response (not a circuit fault)
        if resp.status_code >= 500:
            logger.warning("plant_client: Plant returned %d for %s %s", resp.status_code, method, path)
            self._cb.record_failure()
        else:
            self._cb.record_success()

        return resp


# ---------------------------------------------------------------------------
# FastAPI dependency helper
# ---------------------------------------------------------------------------

def get_plant_client() -> PlantClient:
    """FastAPI dependency — returns a PlantClient using PLANT_GATEWAY_URL env."""
    import os
    base_url = os.getenv("PLANT_GATEWAY_URL", "http://localhost:8000")
    return PlantClient(base_url=base_url)
