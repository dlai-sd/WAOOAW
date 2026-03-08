"""Unit tests for DeltaExchangePump component (EXEC-ENGINE-001 E5-S1).

Tests:
  E5-S1-T1: Mock HTTP 200 → execute() returns success=True, data["candles"] populated
  E5-S1-T2: Mock HTTP 500 → safe_execute() returns success=False, error_message non-empty
  E5-S1-T3: After module import, get_component("DeltaExchangePump") returns an instance
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from components import ComponentInput, _REGISTRY, get_component


def _make_input() -> ComponentInput:
    return ComponentInput(
        flow_run_id="fr-pump-001",
        customer_id="cust-001",
        skill_config={"customer_fields": {"instrument": "NIFTY", "delta_api_key": "test-key"}},
        run_context={},
    )


@pytest.fixture(autouse=True)
def _ensure_pump_registered():
    """Import the module and ensure DeltaExchangePump is registered.

    The global _REGISTRY may have been cleared by other tests
    (test_component_registry uses an autouse fixture that clears it).
    Re-registering explicitly makes each test isolated and order-independent.
    """
    from components import register_component
    import delta_exchange_pump as _mod
    register_component(_mod.DeltaExchangePump())


@pytest.mark.unit
def test_pump_execute_success():
    """E5-S1-T1: HTTP 200 → success=True, candles populated."""
    from delta_exchange_pump import DeltaExchangePump

    mock_response = MagicMock()
    mock_response.json.return_value = {"result": [{"close": 100.0}]}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)

    pump = DeltaExchangePump()

    with patch("delta_exchange_pump.httpx.AsyncClient", return_value=mock_client):
        result = asyncio.run(pump.execute(_make_input()))

    assert result.success is True
    assert result.data["candles"] == [{"close": 100.0}]
    assert result.data["instrument"] == "NIFTY"


@pytest.mark.unit
def test_pump_execute_http_error():
    """E5-S1-T2: HTTP 500 → safe_execute() returns success=False."""
    import httpx
    from delta_exchange_pump import DeltaExchangePump

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "500 Server Error",
            request=MagicMock(),
            response=MagicMock(status_code=500),
        )
    )

    pump = DeltaExchangePump()

    with patch("delta_exchange_pump.httpx.AsyncClient", return_value=mock_client):
        result = asyncio.run(pump.safe_execute(_make_input()))

    assert result.success is False
    assert result.error_message


@pytest.mark.unit
def test_pump_registered_after_import():
    """E5-S1-T3: get_component("DeltaExchangePump") succeeds after module import."""
    comp = get_component("DeltaExchangePump")
    assert comp.component_type == "DeltaExchangePump"
