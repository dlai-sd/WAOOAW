"""Unit tests for _validate_instrument_live (ST-MVP-1 S6)."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


class TestValidateInstrumentLive:
    """ST-MVP-1 S6 T3 — instrument validation in test env returns True without HTTP."""

    def test_returns_true_in_test_environment(self):
        """In test/development env, no HTTP call is made and result is True."""
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

    def test_validate_instrument_live_returns_bool(self):
        """Return type is always bool regardless of env."""
        from api.v1.trading_setup import _validate_instrument_live

        result = asyncio.run(_validate_instrument_live("SOL"))
        assert isinstance(result, bool)
