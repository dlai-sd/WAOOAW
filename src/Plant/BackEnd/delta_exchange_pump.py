"""DeltaExchangePump — fetches OHLCV candles from Delta Exchange (EXEC-ENGINE-001 E5-S1).

Pulls the last 50 1-minute candles for the customer's configured instrument.
The API key is resolved via ExchangeCredentialService using a credential_ref stored
in skill_config.customer_fields.  The plaintext key MUST NOT appear in any log records.

Import and register:
    import delta_exchange_pump  # noqa: F401  — triggers register_component()
"""
from __future__ import annotations

import httpx

from components import BaseComponent, ComponentInput, ComponentOutput, register_component
from core.logging import PiiMaskingFilter, get_logger
from core.security import circuit_breaker

logger = get_logger(__name__)
logger.addFilter(PiiMaskingFilter())


class DeltaExchangePump(BaseComponent):
    """Fetches OHLCV candle data from the Delta Exchange REST API."""

    @property
    def component_type(self) -> str:
        return "DeltaExchangePump"

    async def execute(self, input: ComponentInput) -> ComponentOutput:
        customer_fields = input.skill_config.get("customer_fields", {})
        instrument = customer_fields.get("instrument", customer_fields.get("default_coin", "BTC"))
        credential_ref = customer_fields.get("credential_ref", "")
        if not credential_ref:
            return ComponentOutput(
                success=False,
                error_message="No credential_ref configured — complete trading setup wizard first",
            )
        # Resolve secrets from DB — never log the returned key/secret values
        from core.database import _connector
        from services.exchange_credential_service import ExchangeCredentialService

        async with _connector.get_session() as session:
            svc = ExchangeCredentialService(session)
            secrets = await svc.get_secrets(credential_ref=credential_ref)
        if not secrets:
            return ComponentOutput(
                success=False,
                error_message="Credentials not found for credential_ref",
            )
        api_key = secrets["api_key"]  # NEVER log this value
        candles = await self._fetch_candles(instrument, api_key)
        return ComponentOutput(
            success=True,
            data={"candles": candles, "instrument": instrument},
        )

    @circuit_breaker(service="delta_exchange_api")
    async def _fetch_candles(self, instrument: str, api_key: str) -> list[dict]:
        """Fetch last 50 1m candles. API key is never logged."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.delta.exchange/v2/history/candles",
                params={"symbol": instrument, "resolution": "1m", "limit": 50},
                headers={"api-key": api_key},
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json().get("result", [])


register_component(DeltaExchangePump())
