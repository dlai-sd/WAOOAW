"""DeltaPublisher — places a market order on Delta Exchange (EXEC-ENGINE-001 E5-S3).

Reads the trade signal from previous_step_output["signal"].
HOLD signal → skips order placement (returns success=True with status="skipped").
BUY/SELL  → decrypts the API key via core.encryption.decrypt_field and places a
             market order on Delta Exchange.

API key MUST NOT appear in any log records.

Import and register:
    import delta_publisher  # noqa: F401  — triggers register_component()
"""
from __future__ import annotations

import httpx

from components import BaseComponent, ComponentInput, ComponentOutput, register_component
from core.encryption import decrypt_field
from core.logging import PiiMaskingFilter, get_logger
from core.security import circuit_breaker

logger = get_logger(__name__)
logger.addFilter(PiiMaskingFilter())


class DeltaPublisher(BaseComponent):
    """Places market orders on Delta Exchange based on RSI signal."""

    @property
    def component_type(self) -> str:
        return "DeltaPublisher"

    async def execute(self, input: ComponentInput) -> ComponentOutput:
        signal = (input.previous_step_output or {}).get("signal", "HOLD")
        if signal == "HOLD":
            return ComponentOutput(
                success=True,
                data={"status": "skipped", "reason": "HOLD signal"},
            )
        customer_fields = input.skill_config.get("customer_fields", {})
        encrypted_key = customer_fields.get("delta_api_key", "")
        api_key = decrypt_field(encrypted_key)
        instrument = customer_fields.get("instrument", "NIFTY")
        result = await self._place_order(instrument, signal, api_key)
        return ComponentOutput(success=True, data=result)

    @circuit_breaker(service="delta_exchange_api")
    async def _place_order(self, instrument: str, side: str, api_key: str) -> dict:
        """Place a market order. API key is never logged."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.delta.exchange/v2/orders",
                json={
                    "product_symbol": instrument,
                    "side": side.lower(),
                    "order_type": "market_order",
                    "size": 1,
                },
                headers={"api-key": api_key},
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json().get("result", {})
            return {
                "order_id": data.get("id", ""),
                "fill_price": data.get("avg_fill_price", 0.0),
                "status": "filled",
            }


register_component(DeltaPublisher())
