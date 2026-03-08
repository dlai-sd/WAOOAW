"""RSIProcessor — computes RSI and produces BUY/SELL/HOLD signal (EXEC-ENGINE-001 E5-S2).

Reads previous_step_output["candles"] from DeltaExchangePump.
RSI period is customer-configurable via skill_config.customer_fields.rsi_period (default 14).
Empty candles list → ComponentOutput(success=False, error_message="Insufficient data").

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
    """Pure-calculation component: RSI signal classification."""

    @property
    def component_type(self) -> str:
        return "RSIProcessor"

    async def execute(self, input: ComponentInput) -> ComponentOutput:
        candles = (input.previous_step_output or {}).get("candles", [])
        if not candles:
            return ComponentOutput(success=False, error_message="Insufficient data")
        period = int(
            input.skill_config.get("customer_fields", {}).get("rsi_period", 14)
        )
        rsi_value = self._calculate_rsi(candles, period)
        if rsi_value < 30:
            signal = "BUY"
        elif rsi_value > 70:
            signal = "SELL"
        else:
            signal = "HOLD"
        return ComponentOutput(
            success=True,
            data={"rsi_value": rsi_value, "signal": signal, "confidence": 0.9},
        )

    def _calculate_rsi(self, candles: list[dict], period: int) -> float:
        closes = [float(c.get("close", 0)) for c in candles]
        if len(closes) < period + 1:
            return 50.0
        deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        gains = [d for d in deltas[-period:] if d > 0]
        losses = [-d for d in deltas[-period:] if d < 0]
        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0
        if avg_loss == 0:
            return 100.0
        return 100 - (100 / (1 + avg_gain / avg_loss))


register_component(RSIProcessor())
