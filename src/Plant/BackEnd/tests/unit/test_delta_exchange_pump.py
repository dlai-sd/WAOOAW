"""Unit tests for DeltaExchangePump component (EXEC-ENGINE-001 E5-S1 + ST-MVP-1 S1).

Tests:
  E5-S1-T1: Mock HTTP 200 → execute() returns success=True, data["candles"] populated
  E5-S1-T2: Mock HTTP 500 → safe_execute() returns success=False, error_message non-empty
  E5-S1-T3: After module import, get_component("DeltaExchangePump") returns an instance
  ST-S1-T2: valid credential_ref → success=True
  ST-S1-T3: missing credential_ref → success=False with descriptive message
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from components import ComponentInput, _REGISTRY, get_component


def _make_input(credential_ref: str = "EXCH-test123") -> ComponentInput:
    return ComponentInput(
        flow_run_id="fr-pump-001",
        customer_id="cust-001",
        skill_config={"customer_fields": {"instrument": "BTC", "credential_ref": credential_ref}},
        run_context={},
    )


def _make_input_legacy() -> ComponentInput:
    """Legacy input with delta_api_key (no credential_ref) — used for E5-S1 backward-compat tests."""
    return ComponentInput(
        flow_run_id="fr-pump-legacy",
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
    """ST-S1-T2: valid credential_ref → success=True, candles populated."""
    from delta_exchange_pump import DeltaExchangePump

    mock_response = MagicMock()
    mock_response.json.return_value = {"result": [{"close": 100.0}]}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)

    mock_secrets = {"api_key": "test-key", "api_secret": "test-secret"}
    mock_svc = AsyncMock()
    mock_svc.get_secrets = AsyncMock(return_value=mock_secrets)

    mock_session_cm = AsyncMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=MagicMock())
    mock_session_cm.__aexit__ = AsyncMock(return_value=False)

    pump = DeltaExchangePump()

    with patch("delta_exchange_pump.httpx.AsyncClient", return_value=mock_client), \
         patch("delta_exchange_pump._connector") as mock_connector, \
         patch("delta_exchange_pump.ExchangeCredentialService", return_value=mock_svc):
        mock_connector.get_session.return_value = mock_session_cm
        result = asyncio.run(pump.execute(_make_input()))

    assert result.success is True
    assert result.data["candles"] == [{"close": 100.0}]
    assert result.data["instrument"] == "BTC"


@pytest.mark.unit
def test_pump_execute_missing_credential_ref():
    """ST-S1-T3: missing credential_ref → success=False with descriptive message."""
    from delta_exchange_pump import DeltaExchangePump

    pump = DeltaExchangePump()
    empty_input = ComponentInput(
        flow_run_id="fr-pump-002",
        customer_id="cust-002",
        skill_config={"customer_fields": {"instrument": "BTC"}},
        run_context={},
    )

    result = asyncio.run(pump.execute(empty_input))

    assert result.success is False
    assert "credential_ref" in result.error_message.lower()


@pytest.mark.unit
def test_pump_execute_empty_credential_ref():
    """ST-S1-T3 variant: empty string credential_ref → success=False."""
    from delta_exchange_pump import DeltaExchangePump

    pump = DeltaExchangePump()
    empty_ref_input = ComponentInput(
        flow_run_id="fr-pump-003",
        customer_id="cust-003",
        skill_config={"customer_fields": {"instrument": "BTC", "credential_ref": ""}},
        run_context={},
    )

    result = asyncio.run(pump.execute(empty_ref_input))

    assert result.success is False
    assert "credential_ref" in result.error_message.lower()


@pytest.mark.unit
def test_pump_execute_credential_not_found():
    """execute() with valid ref but missing DB record → success=False."""
    from delta_exchange_pump import DeltaExchangePump

    mock_svc = AsyncMock()
    mock_svc.get_secrets = AsyncMock(return_value=None)

    mock_session_cm = AsyncMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=MagicMock())
    mock_session_cm.__aexit__ = AsyncMock(return_value=False)

    pump = DeltaExchangePump()

    with patch("delta_exchange_pump._connector") as mock_connector, \
         patch("delta_exchange_pump.ExchangeCredentialService", return_value=mock_svc):
        mock_connector.get_session.return_value = mock_session_cm
        result = asyncio.run(pump.execute(_make_input("EXCH-missing")))

    assert result.success is False
    assert result.error_message


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

    mock_secrets = {"api_key": "test-key", "api_secret": "test-secret"}
    mock_svc = AsyncMock()
    mock_svc.get_secrets = AsyncMock(return_value=mock_secrets)

    mock_session_cm = AsyncMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=MagicMock())
    mock_session_cm.__aexit__ = AsyncMock(return_value=False)

    pump = DeltaExchangePump()

    with patch("delta_exchange_pump.httpx.AsyncClient", return_value=mock_client), \
         patch("delta_exchange_pump._connector") as mock_connector, \
         patch("delta_exchange_pump.ExchangeCredentialService", return_value=mock_svc):
        mock_connector.get_session.return_value = mock_session_cm
        result = asyncio.run(pump.safe_execute(_make_input()))

    assert result.success is False
    assert result.error_message


@pytest.mark.unit
def test_pump_registered_after_import():
    """E5-S1-T3: get_component("DeltaExchangePump") succeeds after module import."""
    comp = get_component("DeltaExchangePump")
    assert comp.component_type == "DeltaExchangePump"
