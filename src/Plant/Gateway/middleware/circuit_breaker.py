"""
Standalone circuit breaker for gateway middleware — P-1 preventive gate.

Copied from src/CP/BackEnd/services/plant_client.py to avoid a cross-service
import. Logic is identical; only the PlantClient wrapper is omitted.

Architecture:
- One module-level CircuitBreaker instance per middleware that makes upstream calls.
- Circuit opens after 3 failures in 10 s; recovers after 30 s.
- When open: GatewayCircuitOpenError is raised immediately (no HTTP call made).
"""

from __future__ import annotations

import logging
import time
from enum import Enum

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Thresholds (kept in sync with plant_client.py defaults)
# ---------------------------------------------------------------------------
_FAILURE_THRESHOLD = 3
_FAILURE_WINDOW_SECS = 10.0
_COOLDOWN_SECS = 30.0


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class GatewayCircuitOpenError(Exception):
    """Raised when the circuit is open — upstream call is blocked."""

    def __init__(self, service: str = "upstream") -> None:
        super().__init__(f"Circuit open — {service} is temporarily unavailable")
        self.retry_after: int = int(_COOLDOWN_SECS)


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

class _State(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    """Lightweight in-memory circuit breaker.

    Not thread-safe across asyncio tasks at the counter-increment level but
    safe enough for a single-instance gateway service.
    """

    def __init__(
        self,
        *,
        failure_threshold: int = _FAILURE_THRESHOLD,
        failure_window_secs: float = _FAILURE_WINDOW_SECS,
        cooldown_secs: float = _COOLDOWN_SECS,
        service_name: str = "upstream",
    ) -> None:
        self._threshold = failure_threshold
        self._window = failure_window_secs
        self._cooldown = cooldown_secs
        self._service_name = service_name

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
            logger.info(
                "circuit_breaker[%s]: probe succeeded — circuit CLOSED",
                self._service_name,
            )
        self._state = _State.CLOSED

    def record_failure(self) -> None:
        """Call after a 5xx, connection error, or timeout."""
        now = time.monotonic()
        self._failure_timestamps.append(now)
        cutoff = now - self._window
        self._failure_timestamps = [t for t in self._failure_timestamps if t >= cutoff]

        if self._state == _State.HALF_OPEN:
            logger.warning(
                "circuit_breaker[%s]: probe failed — circuit re-OPENED for %ds",
                self._service_name,
                self._cooldown,
            )
            self._state = _State.OPEN
            self._opened_at = now
        elif len(self._failure_timestamps) >= self._threshold:
            if self._state == _State.CLOSED:
                logger.warning(
                    "circuit_breaker[%s]: %d failures in %.0fs — circuit OPENED",
                    self._service_name,
                    len(self._failure_timestamps),
                    self._window,
                )
                self._state = _State.OPEN
                self._opened_at = now

    def is_call_permitted(self) -> bool:
        """Return True if the call should proceed; False if it should be blocked."""
        self._maybe_transition()
        return self._state in (_State.CLOSED, _State.HALF_OPEN)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _maybe_transition(self) -> None:
        """Transition OPEN → HALF_OPEN when cooldown expires."""
        if self._state == _State.OPEN:
            elapsed = time.monotonic() - self._opened_at
            if elapsed >= self._cooldown:
                logger.info(
                    "circuit_breaker[%s]: cooldown expired (%.1fs) — entering HALF_OPEN",
                    self._service_name,
                    elapsed,
                )
                self._state = _State.HALF_OPEN
