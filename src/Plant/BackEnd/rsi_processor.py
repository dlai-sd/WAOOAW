"""RSIProcessor — computes RSI and produces BUY/SELL/HOLD signal (EXEC-ENGINE-001 E5-S2).

Reads previous_step_output["candles"] from DeltaExchangePump.
RSI period is customer-configurable via skill_config.customer_fields.rsi_period (default 14).
Empty candles list → ComponentOutput(success=False, error_message="Insufficient data").

Uses Wilder's smoothed EMA (matches TradingView output for the same period + candles).

Position guard: if previous_step_output["open_positions"] contains a matching direction,
the signal is suppressed to HOLD to prevent stacking duplicate entries.

Pure calculation — no external HTTP calls.

Import and register:
    import rsi_processor  # noqa: F401  — triggers register_component()
"""
from __future__ import annotations

from components import BaseComponent, ComponentInput, ComponentOutput, register_component
from core.logging import PiiMaskingFilter, get_logger

logger = get_logger(__name__)
logger.addFilter(PiiMaskingFilter())


class RSIProcessor(BaseComponent):
    """Pure-calculation component: RSI signal classification using Wilder's EMA."""

    @property
    def component_type(self) -> str:
        return "RSIProcessor"

    async def execute(self, input: ComponentInput) -> ComponentOutput:
        candles = (input.previous_step_output or {}).get("candles", [])
        open_positions = (input.previous_step_output or {}).get("open_positions", [])
        if not candles:
            return ComponentOutput(success=False, error_message="Insufficient data")
        period = int(
            input.skill_config.get("customer_fields", {}).get("rsi_period", 14)
        )
        rsi_value = self._calculate_rsi_wilder(candles, period)
        # Classify raw signal
        if rsi_value < 30:
            raw_signal = "BUY"
        elif rsi_value > 70:
            raw_signal = "SELL"
        else:
            raw_signal = "HOLD"
        # Position guard: suppress signal if matching direction already open
        position_sides = [p.get("side", "").lower() for p in open_positions]
        if raw_signal == "BUY" and "long" in position_sides:
            raw_signal = "HOLD"  # already long, do not stack
        if raw_signal == "SELL" and "short" in position_sides:
            raw_signal = "HOLD"  # already short, do not stack
        return ComponentOutput(
            success=True,
            data={"rsi_value": rsi_value, "signal": raw_signal, "confidence": 0.9},
        )

    def _calculate_rsi_wilder(self, candles: list[dict], period: int) -> float:
        """Wilder's smoothed RSI — matches TradingView output."""
        closes = [float(c.get("close", 0)) for c in candles]
        if len(closes) < period + 1:
            return 50.0
        deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        gains = [max(d, 0.0) for d in deltas]
        losses = [max(-d, 0.0) for d in deltas]
        # Seed with simple average over first period
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        # Wilder's smoothing: alpha = 1/period
        for g, l in zip(gains[period:], losses[period:]):
            avg_gain = (avg_gain * (period - 1) + g) / period
            avg_loss = (avg_loss * (period - 1) + l) / period
        if avg_loss == 0:
            return 100.0
        return round(100 - (100 / (1 + avg_gain / avg_loss)), 4)

    # Keep legacy alias so any callers that reference the old name still work
    def _calculate_rsi(self, candles: list[dict], period: int) -> float:
        return self._calculate_rsi_wilder(candles, period)


register_component(RSIProcessor())
