"""Unit tests for DeltaPublisher component (EXEC-ENGINE-001 E5-S3).

Tests:
  E5-S3-T1: BUY signal + HTTP 200 → success=True, data["order_id"] set
  E5-S3-T2: HOLD signal → success=True, data["status"]="skipped"
  E5-S3-T3: HTTP 4xx → safe_execute() returns success=False
  E5-S3-T4: API key value does NOT appear in any captured log record
"""
from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from components import ComponentInput, get_component


def _make_input(signal: str = "BUY", api_key: str = "secret-key-xyz") -> ComponentInput:
    return ComponentInput(
        flow_run_id="fr-pub-001",
        customer_id="cust-001",
        skill_config={"customer_fields": {"delta_api_key": api_key, "instrument": "NIFTY"}},
        run_context={},
        previous_step_output={"signal": signal},
    )


@pytest.fixture(autouse=True)
def _ensure_publisher_registered():
    """Import the module and ensure DeltaPublisher is registered.

    Explicit re-registration makes tests order-independent.
    """
    from components import register_component
    import delta_publisher as _mod
    register_component(_mod.DeltaPublisher())


@pytest.mark.unit
def test_publisher_buy_order_placed():
    """E5-S3-T1: BUY signal + HTTP 200 → success=True, order_id set."""
    from delta_publisher import DeltaPublisher

    mock_response = MagicMock()
    mock_response.json.return_value = {"result": {"id": "ord-123", "avg_fill_price": 100.5}}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)

    pub = DeltaPublisher()

    with patch("delta_publisher.httpx.AsyncClient", return_value=mock_client):
        result = asyncio.run(pub.execute(_make_input("BUY")))

    assert result.success is True
    assert result.data["order_id"] == "ord-123"


@pytest.mark.unit
def test_publisher_hold_skips_order():
    """E5-S3-T2: HOLD signal → success=True, status=skipped (no HTTP call)."""
    from delta_publisher import DeltaPublisher

    pub = DeltaPublisher()
    result = asyncio.run(pub.execute(_make_input("HOLD")))

    assert result.success is True
    assert result.data["status"] == "skipped"


@pytest.mark.unit
def test_publisher_http_error_returns_failure():
    """E5-S3-T3: HTTP 4xx → safe_execute() returns success=False."""
    import httpx
    from delta_publisher import DeltaPublisher

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "400 Bad Request",
            request=MagicMock(),
            response=MagicMock(status_code=400),
        )
    )

    pub = DeltaPublisher()

    with patch("delta_publisher.httpx.AsyncClient", return_value=mock_client):
        result = asyncio.run(pub.safe_execute(_make_input("BUY")))

    assert result.success is False


@pytest.mark.unit
def test_publisher_api_key_not_logged(caplog):
    """E5-S3-T4: API key does NOT appear in any log record during execute()."""
    from delta_publisher import DeltaPublisher

    secret_key = "SUPER_SECRET_KEY_MUST_NOT_APPEAR_IN_LOGS"

    mock_response = MagicMock()
    mock_response.json.return_value = {"result": {"id": "ord-456", "avg_fill_price": 99.0}}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)

    pub = DeltaPublisher()

    with caplog.at_level(logging.DEBUG):
        with patch("delta_publisher.httpx.AsyncClient", return_value=mock_client):
            asyncio.run(pub.execute(_make_input("BUY", api_key=secret_key)))

    for record in caplog.records:
        assert secret_key not in record.getMessage(), (
            f"API key leaked in log record: {record.getMessage()}"
        )


@pytest.mark.unit
def test_publisher_registered_after_import():
    """DeltaPublisher is in the registry after module import."""
    comp = get_component("DeltaPublisher")
    assert comp.component_type == "DeltaPublisher"
