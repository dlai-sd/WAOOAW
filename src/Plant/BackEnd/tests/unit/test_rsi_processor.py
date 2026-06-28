"""Unit tests for RSIProcessor component (EXEC-ENGINE-001 E5-S2 + ST-MVP-1 S7).

Tests:
  E5-S2-T1: Candles producing RSI < 30 → signal="BUY"
  E5-S2-T2: Candles producing RSI > 70 → signal="SELL"
  E5-S2-T3: Candles producing 30 ≤ RSI ≤ 70 → signal="HOLD"
  E5-S2-T4: Empty candles list → success=False, error_message="Insufficient data"
  ST-S7-T1: Wilder's RSI with 20 known closes matches expected value ± 0.1
  ST-S7-T2: BUY signal suppressed to HOLD when open_positions has a long
  ST-S7-T3: SELL signal suppressed to HOLD when open_positions has a short
"""
from __future__ import annotations

import asyncio

import pytest

from components import ComponentInput, get_component


def _make_input(
    candles: list[dict],
    rsi_period: int = 14,
    open_positions: list[dict] | None = None,
) -> ComponentInput:
    return ComponentInput(
        flow_run_id="fr-rsi-001",
        customer_id="cust-001",
        skill_config={"customer_fields": {"rsi_period": rsi_period}},
        run_context={},
        previous_step_output={"candles": candles, "open_positions": open_positions or []},
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


@pytest.mark.unit
def test_wilder_rsi_known_value():
    """ST-S7-T1: Wilder's RSI with 20 known closes matches expected output ± 0.1.

    Using a simple all-rising sequence of 20 candles with period=14:
    All gains, no losses → RSI should be 100.0.
    """
    from rsi_processor import RSIProcessor
    proc = RSIProcessor()
    # 20 strictly rising candles: all gains, 0 losses → RSI = 100
    candles = [{"close": 100.0 + i} for i in range(20)]
    rsi = proc._calculate_rsi_wilder(candles, period=14)
    assert abs(rsi - 100.0) < 0.1, f"Expected RSI≈100 for all-rising, got {rsi}"


@pytest.mark.unit
def test_wilder_rsi_all_declining():
    """Wilder's RSI with all-declining candles → RSI close to 0."""
    from rsi_processor import RSIProcessor
    proc = RSIProcessor()
    candles = [{"close": 200.0 - i} for i in range(20)]
    rsi = proc._calculate_rsi_wilder(candles, period=14)
    assert rsi < 10.0, f"Expected RSI close to 0 for all-declining, got {rsi}"


@pytest.mark.unit
def test_wilder_rsi_insufficient_data():
    """Wilder's RSI returns 50.0 when candles < period+1."""
    from rsi_processor import RSIProcessor
    proc = RSIProcessor()
    candles = [{"close": 100.0 + i} for i in range(5)]
    rsi = proc._calculate_rsi_wilder(candles, period=14)
    assert rsi == 50.0


@pytest.mark.unit
def test_position_guard_buy_suppressed():
    """ST-S7-T2: BUY signal suppressed to HOLD when open_positions has a long."""
    from rsi_processor import RSIProcessor
    proc = RSIProcessor()
    # Declining candles → BUY signal without guard
    candles = _declining_candles(20)
    open_positions = [{"side": "long", "product_symbol": "BTC"}]
    inp = _make_input(candles, rsi_period=14, open_positions=open_positions)
    result = asyncio.run(proc.execute(inp))
    assert result.success is True
    assert result.data["signal"] == "HOLD", (
        f"Expected HOLD (long already open), got {result.data['signal']}"
    )


@pytest.mark.unit
def test_position_guard_sell_suppressed():
    """ST-S7-T3: SELL signal suppressed to HOLD when open_positions has a short."""
    from rsi_processor import RSIProcessor
    proc = RSIProcessor()
    # Rising candles → SELL signal without guard
    candles = _rising_candles(20)
    open_positions = [{"side": "short", "product_symbol": "BTC"}]
    inp = _make_input(candles, rsi_period=14, open_positions=open_positions)
    result = asyncio.run(proc.execute(inp))
    assert result.success is True
    assert result.data["signal"] == "HOLD", (
        f"Expected HOLD (short already open), got {result.data['signal']}"
    )


@pytest.mark.unit
def test_position_guard_no_suppression_when_empty():
    """No position guard when open_positions is empty — signal fires normally."""
    from rsi_processor import RSIProcessor
    proc = RSIProcessor()
    candles = _declining_candles(20)
    inp = _make_input(candles, rsi_period=14, open_positions=[])
    result = asyncio.run(proc.execute(inp))
    assert result.success is True
    assert result.data["signal"] == "BUY"

