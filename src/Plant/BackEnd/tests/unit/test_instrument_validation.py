"""Unit tests for _validate_instrument_live (feat/delta-exchange-real-credentials)."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


class TestValidateInstrumentLive:
    """Mock is now active ONLY in the 'test' environment (pytest sets this automatically)."""

    def test_returns_true_in_test_environment(self):
        """In the 'test' pytest environment no HTTP call is made and result is True."""
        from api.v1.trading_setup import _validate_instrument_live

        with patch("api.v1.trading_setup.httpx.AsyncClient") as mock_cls:
            result = asyncio.run(_validate_instrument_live("NIFTY"))

        assert result is True
        mock_cls.assert_not_called()

    def test_btc_returns_true_in_test_environment(self):
        from api.v1.trading_setup import _validate_instrument_live

        with patch("api.v1.trading_setup.httpx.AsyncClient") as mock_cls:
            result = asyncio.run(_validate_instrument_live("BTC"))

        assert result is True
        mock_cls.assert_not_called()

    def test_non_test_env_calls_delta_exchange_api(self):
        """When DELTA_EXCHANGE_REAL_API=true, the function calls the real products endpoint."""
        from api.v1.trading_setup import _validate_instrument_live

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "result": [
                {"symbol": "BTCUSD", "underlying_asset": {"symbol": "BTC"}},
            ]
        }
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)

        with patch("api.v1.trading_setup.httpx.AsyncClient", return_value=mock_client), \
             patch.dict("os.environ", {"DELTA_EXCHANGE_REAL_API": "true"}):
            result = asyncio.run(_validate_instrument_live("BTC"))

        assert result is True
        mock_client.get.assert_called_once()
        called_url = mock_client.get.call_args[0][0]
        assert "/v2/products" in called_url

    def test_instrument_intro_no_nifty_banknifty(self):
        """_ASSISTANT_INTRO['instrument'] must not list NIFTY or BANKNIFTY (crypto-only)."""
        from api.v1.trading_setup import _ASSISTANT_INTRO

        intro = _ASSISTANT_INTRO["instrument"]
        assert "NIFTY" not in intro
        assert "BANKNIFTY" not in intro

    def test_instrument_intro_lists_crypto_examples(self):
        from api.v1.trading_setup import _ASSISTANT_INTRO

        intro = _ASSISTANT_INTRO["instrument"]
        assert "BTC" in intro
        assert "ETH" in intro
