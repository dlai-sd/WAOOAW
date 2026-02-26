"""Unit tests for PlantClient circuit breaker — Iteration 3 E1-S1 + E1-S2.

Covers:
  TC-E1-S1-1  Plant returns 200 → circuit stays CLOSED
  TC-E1-S1-2  Three consecutive 500s → circuit opens, subsequent call raises ServiceUnavailableError
  TC-E1-S1-3  After cooldown, circuit moves to HALF_OPEN (one probe allowed)
  TC-E1-S1-4  Probe succeeds → circuit closes, normal requests resume
  TC-E1-S1-5  Probe fails → circuit re-opens
  TC-E1-S1-6  Plant returns 404 → circuit stays CLOSED (4xx is not a fault)
  TC-E1-S2-1  Circuit open → PlantClient raises ServiceUnavailableError
  TC-E1-S2-2  ServiceUnavailableError has retry_after=30
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from services.plant_client import CircuitBreaker, PlantClient, ServiceUnavailableError, _State


# ---------------------------------------------------------------------------
# TC-E1-S1: CircuitBreaker state machine
# ---------------------------------------------------------------------------

def test_circuit_starts_closed():
    cb = CircuitBreaker()
    assert cb.state == _State.CLOSED


def test_circuit_stays_closed_on_success():
    """TC-E1-S1-1: Success does not trip circuit."""
    cb = CircuitBreaker(failure_threshold=3)
    cb.record_success()
    assert cb.state == _State.CLOSED


def test_circuit_stays_closed_below_threshold():
    cb = CircuitBreaker(failure_threshold=3)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == _State.CLOSED


def test_circuit_opens_after_threshold_failures():
    """TC-E1-S1-2 (partial): Three failures trip the circuit."""
    cb = CircuitBreaker(failure_threshold=3, failure_window_secs=60)
    cb.record_failure()
    cb.record_failure()
    cb.record_failure()
    assert cb.state == _State.OPEN


def test_circuit_open_blocks_calls():
    """TC-E1-S1-2 (partial): Circuit open → is_call_permitted returns False."""
    cb = CircuitBreaker(failure_threshold=3, failure_window_secs=60)
    for _ in range(3):
        cb.record_failure()
    assert not cb.is_call_permitted()


def test_circuit_transitions_to_half_open_after_cooldown():
    """TC-E1-S1-3: After cooldown, circuit moves to HALF_OPEN."""
    cb = CircuitBreaker(failure_threshold=3, cooldown_secs=0.01)
    for _ in range(3):
        cb.record_failure()
    assert cb.state == _State.OPEN
    time.sleep(0.02)
    assert cb.state == _State.HALF_OPEN
    assert cb.is_call_permitted()


def test_probe_success_closes_circuit():
    """TC-E1-S1-4: Probe succeeds → circuit CLOSED."""
    cb = CircuitBreaker(failure_threshold=3, cooldown_secs=0.01)
    for _ in range(3):
        cb.record_failure()
    time.sleep(0.02)
    assert cb.state == _State.HALF_OPEN
    cb.record_success()
    assert cb.state == _State.CLOSED


def test_probe_failure_reopens_circuit():
    """TC-E1-S1-5: Probe fails → circuit re-opens for another cooldown."""
    cb = CircuitBreaker(failure_threshold=3, cooldown_secs=0.01)
    for _ in range(3):
        cb.record_failure()
    time.sleep(0.02)
    assert cb.state == _State.HALF_OPEN
    cb.record_failure()
    assert cb.state == _State.OPEN


def test_4xx_does_not_trip_circuit():
    """TC-E1-S1-6: 4xx responses do not count as failures."""
    cb = CircuitBreaker(failure_threshold=3)
    # 4xx handling is done in PlantClient._request — CircuitBreaker.record_failure
    # is only called for 5xx, timeouts, connection errors.
    # Here we test that 3 successes (even after 4xx-like scenario) keep it closed.
    cb.record_success()
    cb.record_success()
    cb.record_success()
    assert cb.state == _State.CLOSED


def test_failures_outside_window_do_not_count():
    """Failures outside the rolling window are ignored."""
    cb = CircuitBreaker(failure_threshold=2, failure_window_secs=0.01)
    cb.record_failure()
    time.sleep(0.02)
    # First failure is now outside window; this second one should NOT trip circuit
    cb.record_failure()
    assert cb.state == _State.CLOSED


# ---------------------------------------------------------------------------
# TC-E1-S1 + TC-E1-S2: PlantClient integration with circuit breaker
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_plant_client_success_keeps_circuit_closed():
    """TC-E1-S1-1: Successful response keeps circuit CLOSED."""
    cb = CircuitBreaker()
    with patch("httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        instance.request = AsyncMock(return_value=httpx.Response(200, json={"ok": True}))
        MockClient.return_value = instance

        client = PlantClient(base_url="http://plant:8000", circuit_breaker=cb)
        resp = await client.post("/api/v1/customers", json={"a": 1})

    assert resp.status_code == 200
    assert cb.state == _State.CLOSED


@pytest.mark.asyncio
async def test_plant_client_three_5xx_opens_circuit():
    """TC-E1-S1-2: Three 5xx responses open the circuit."""
    cb = CircuitBreaker(failure_threshold=3, failure_window_secs=60)
    with patch("httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        instance.request = AsyncMock(return_value=httpx.Response(500))
        MockClient.return_value = instance

        client = PlantClient(base_url="http://plant:8000", circuit_breaker=cb)
        for _ in range(3):
            await client.post("/api/v1/customers", json={})

    assert cb.state == _State.OPEN

    # Next call must raise ServiceUnavailableError without making HTTP call
    with pytest.raises(ServiceUnavailableError):
        await client.post("/api/v1/customers", json={})


@pytest.mark.asyncio
async def test_plant_client_4xx_does_not_open_circuit():
    """TC-E1-S1-6: 4xx response does not count as circuit fault."""
    cb = CircuitBreaker(failure_threshold=3, failure_window_secs=60)
    with patch("httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        instance.request = AsyncMock(return_value=httpx.Response(409))
        MockClient.return_value = instance

        client = PlantClient(base_url="http://plant:8000", circuit_breaker=cb)
        for _ in range(5):
            resp = await client.post("/api/v1/customers", json={})
            assert resp.status_code == 409

    assert cb.state == _State.CLOSED


@pytest.mark.asyncio
async def test_plant_client_timeout_opens_circuit():
    """Timeout counts as a circuit failure."""
    cb = CircuitBreaker(failure_threshold=3)
    with patch("httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        instance.request = AsyncMock(
            side_effect=httpx.TimeoutException("timeout", request=MagicMock())
        )
        MockClient.return_value = instance

        client = PlantClient(base_url="http://plant:8000", circuit_breaker=cb)
        for _ in range(3):
            with pytest.raises(ServiceUnavailableError):
                await client.post("/api/v1/customers", json={})

    assert cb.state == _State.OPEN


# ---------------------------------------------------------------------------
# TC-E1-S2: ServiceUnavailableError properties
# ---------------------------------------------------------------------------

def test_service_unavailable_error_has_retry_after():
    """TC-E1-S2-2: ServiceUnavailableError.retry_after == 30."""
    err = ServiceUnavailableError()
    assert err.retry_after == 30


def test_service_unavailable_error_message():
    err = ServiceUnavailableError("custom message")
    assert "custom message" in str(err)
