"""Unit tests for RSIProcessor component (EXEC-ENGINE-001 E5-S2).

Tests:
  E5-S2-T1: Candles producing RSI < 30 → signal="BUY"
  E5-S2-T2: Candles producing RSI > 70 → signal="SELL"
  E5-S2-T3: Candles producing 30 ≤ RSI ≤ 70 → signal="HOLD"
  E5-S2-T4: Empty candles list → success=False, error_message="Insufficient data"
"""
from __future__ import annotations

import asyncio

import pytest

from components import ComponentInput, get_component


def _make_input(candles: list[dict], rsi_period: int = 14) -> ComponentInput:
    return ComponentInput(
        flow_run_id="fr-rsi-001",
        customer_id="cust-001",
        skill_config={"customer_fields": {"rsi_period": rsi_period}},
        run_context={},
        previous_step_output={"candles": candles},
    )


def _declining_candles(n: int = 20) -> list[dict]:
    """Declining prices → RSI < 30 (oversold / BUY)."""
    return [{"close": 200.0 - i * 3.0} for i in range(n)]


def _rising_candles(n: int = 20) -> list[dict]:
    """Rising prices → RSI > 70 (overbought / SELL)."""
    return [{"close": 100.0 + i * 3.0} for i in range(n)]


def _flat_candles(n: int = 20) -> list[dict]:
    """Alternating +1/-1 prices → RSI ≈ 50 (HOLD)."""
    return [{"close": 100.0 + (1.0 if i % 2 == 0 else -1.0)} for i in range(n)]


@pytest.fixture(autouse=True)
def _ensure_rsi_registered():
    """Import the module and ensure RSIProcessor is registered.

    Explicit re-registration makes tests order-independent.
    """
    from components import register_component
    import rsi_processor as _mod
    register_component(_mod.RSIProcessor())


@pytest.mark.unit
def test_rsi_signal_buy():
    """E5-S2-T1: Declining prices → signal=BUY."""
    from rsi_processor import RSIProcessor
    proc = RSIProcessor()
    result = asyncio.run(proc.execute(_make_input(_declining_candles())))
    assert result.success is True
    assert result.data["signal"] == "BUY"


@pytest.mark.unit
def test_rsi_signal_sell():
    """E5-S2-T2: Rising prices → signal=SELL."""
    from rsi_processor import RSIProcessor
    proc = RSIProcessor()
    result = asyncio.run(proc.execute(_make_input(_rising_candles())))
    assert result.success is True
    assert result.data["signal"] == "SELL"


@pytest.mark.unit
def test_rsi_signal_hold():
    """E5-S2-T3: Alternating prices → signal=HOLD."""
    from rsi_processor import RSIProcessor
    proc = RSIProcessor()
    result = asyncio.run(proc.execute(_make_input(_flat_candles())))
    assert result.success is True
    assert result.data["signal"] == "HOLD"


@pytest.mark.unit
def test_rsi_empty_candles():
    """E5-S2-T4: Empty candles → success=False, error_message='Insufficient data'."""
    from rsi_processor import RSIProcessor
    proc = RSIProcessor()
    inp = ComponentInput(
        flow_run_id="fr-rsi-002",
        customer_id="cust-001",
        skill_config={},
        run_context={},
        previous_step_output={"candles": []},
    )
    result = asyncio.run(proc.execute(inp))
    assert result.success is False
    assert result.error_message == "Insufficient data"


@pytest.mark.unit
def test_rsi_registered_after_import():
    """RSIProcessor is in the registry after module import."""
    comp = get_component("RSIProcessor")
    assert comp.component_type == "RSIProcessor"
