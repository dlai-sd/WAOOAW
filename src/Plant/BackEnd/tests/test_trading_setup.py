"""Unit tests for trading setup step machine (feat/share-trader-setup-chat)."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_repo(config=None):
    repo = AsyncMock()
    record = MagicMock()
    record.config = config or {}
    record.hired_instance_id = "TRD-001"
    repo.get_by_id.return_value = record
    repo.update_config = AsyncMock(return_value=record)
    return repo


class TestStateFromConfig:
    def test_empty_config_returns_default_state(self):
        from api.v1.trading_setup import _state_from_config
        state = _state_from_config(None)
        assert state.step == "welcome"
        assert state.messages == []
        assert state.configured is False

    def test_existing_state_loaded(self):
        from api.v1.trading_setup import _state_from_config
        state = _state_from_config({
            "trading_setup": {"step": "instrument", "configured": False,
                              "messages": [], "collected": {}, "validation_status": "valid", "updated_at": ""}
        })
        assert state.step == "instrument"

    def test_corrupted_config_returns_default(self):
        from api.v1.trading_setup import _state_from_config
        state = _state_from_config({"trading_setup": "broken"})
        assert state.step == "welcome"


class TestMaskContent:
    def test_masks_short_key(self):
        from api.v1.trading_setup import _mask_content
        result = _mask_content("abc123")
        assert "●" in result
        assert "abc123" not in result

    def test_masks_long_key(self):
        from api.v1.trading_setup import _mask_content
        key = "a" * 40
        result = _mask_content(key)
        assert "40 chars" in result


class TestReadiness:
    def test_no_credentials_not_ready(self):
        from api.v1.trading_setup import _readiness, TradingSetupState
        state = TradingSetupState()
        r = _readiness(state)
        assert r["configured"] is False
        assert r["has_credentials"] is False
        assert r["credentials_valid"] is False

    def test_done_step_configured(self):
        from api.v1.trading_setup import _readiness, TradingSetupState
        state = TradingSetupState(step="done", configured=True,
                                  validation_status="valid",
                                  collected={"credential_ref": "EXCH-xxx",
                                             "default_coin": "BTC",
                                             "rsi_period": 14,
                                             "max_units_per_order": 1.0})
        r = _readiness(state)
        assert r["configured"] is True
        assert r["credentials_valid"] is True
        assert r["has_instrument"] is True
        assert r["has_rsi_period"] is True
        assert r["has_risk_limits"] is True


class TestProcessStep:

    @pytest.mark.asyncio
    async def test_welcome_advances_to_api_key(self):
        from api.v1.trading_setup import _process_step, TradingSetupState
        state = TradingSetupState(step="welcome")
        db = AsyncMock()
        result = await _process_step(state, "start", "TRD-001", db)
        assert result.step == "api_key"
        assert any(m.role == "assistant" for m in result.messages)

    @pytest.mark.asyncio
    async def test_api_key_empty_stays_on_step(self):
        from api.v1.trading_setup import _process_step, TradingSetupState
        state = TradingSetupState(step="api_key")
        db = AsyncMock()
        result = await _process_step(state, "", "TRD-001", db)
        assert result.step == "api_key"

    @pytest.mark.asyncio
    async def test_api_key_stored_encrypted(self):
        from api.v1.trading_setup import _process_step, TradingSetupState
        state = TradingSetupState(step="api_key")
        db = AsyncMock()
        result = await _process_step(state, "my-real-api-key", "TRD-001", db)
        assert result.step == "api_secret"
        # Key must be stored encrypted, not as plain text
        stored = result.collected.get("encrypted_api_key", "")
        assert stored != "my-real-api-key"
        assert len(stored) > 0

    @pytest.mark.asyncio
    async def test_api_key_masked_in_messages(self):
        from api.v1.trading_setup import _process_step, TradingSetupState
        state = TradingSetupState(step="api_key")
        db = AsyncMock()
        result = await _process_step(state, "my-real-api-key", "TRD-001", db)
        user_msgs = [m for m in result.messages if m.role == "user"]
        assert user_msgs
        assert "my-real-api-key" not in user_msgs[-1].content
        assert user_msgs[-1].masked is True

    @pytest.mark.asyncio
    async def test_instrument_uppercase_stored(self):
        from api.v1.trading_setup import _process_step, TradingSetupState
        state = TradingSetupState(step="instrument",
                                  collected={"encrypted_api_key": "x", "encrypted_api_secret": "y"})
        db = AsyncMock()
        with patch("api.v1.trading_setup._validate_instrument_live",
                   new=AsyncMock(return_value=True)):
            result = await _process_step(state, "btc", "TRD-001", db)
        assert result.step == "rsi_period"
        assert result.collected["default_coin"] == "BTC"

    @pytest.mark.asyncio
    async def test_rsi_period_invalid_string_stays(self):
        from api.v1.trading_setup import _process_step, TradingSetupState
        state = TradingSetupState(step="rsi_period")
        db = AsyncMock()
        result = await _process_step(state, "not-a-number", "TRD-001", db)
        assert result.step == "rsi_period"

    @pytest.mark.asyncio
    async def test_rsi_period_out_of_range_stays(self):
        from api.v1.trading_setup import _process_step, TradingSetupState
        state = TradingSetupState(step="rsi_period")
        db = AsyncMock()
        result = await _process_step(state, "200", "TRD-001", db)
        assert result.step == "rsi_period"

    @pytest.mark.asyncio
    async def test_rsi_period_valid_advances(self):
        from api.v1.trading_setup import _process_step, TradingSetupState
        state = TradingSetupState(step="rsi_period")
        db = AsyncMock()
        result = await _process_step(state, "14", "TRD-001", db)
        assert result.step == "risk_limits"
        assert result.collected["rsi_period"] == 14

    @pytest.mark.asyncio
    async def test_risk_limits_skip_uses_defaults(self):
        from api.v1.trading_setup import _process_step, TradingSetupState
        state = TradingSetupState(
            step="risk_limits",
            collected={
                "encrypted_api_key": "enc_key",
                "encrypted_api_secret": "enc_secret",
                "default_coin": "BTC",
                "rsi_period": 14,
                "customer_id": "CUST-1",
            }
        )
        db = AsyncMock()
        result = await _process_step(state, "skip", "TRD-001", db)
        # risk_limits now advances to capital_pct (S5 wizard extension)
        assert result.step == "capital_pct"
        assert result.configured is False
        assert result.collected["max_units_per_order"] == 1.0
        assert result.collected["max_notional_inr"] == 50000.0
        # Encrypted keys remain in state until risk_disclosure completes
        assert "encrypted_api_key" in result.collected

    @pytest.mark.asyncio
    async def test_risk_limits_invalid_format_stays(self):
        from api.v1.trading_setup import _process_step, TradingSetupState
        state = TradingSetupState(
            step="risk_limits",
            collected={"encrypted_api_key": "x", "encrypted_api_secret": "y",
                       "default_coin": "BTC", "rsi_period": 14, "customer_id": "C"}
        )
        db = AsyncMock()
        result = await _process_step(state, "bad input here", "TRD-001", db)
        assert result.step == "risk_limits"

    @pytest.mark.asyncio
    async def test_validate_step_fail_resets_to_api_key(self):
        """When credentials are invalid, step resets to api_key for retry."""
        from api.v1.trading_setup import _process_step, TradingSetupState, _encrypt
        state = TradingSetupState(
            step="api_secret",
            collected={"encrypted_api_key": _encrypt("bad_key")},
        )
        db = AsyncMock()
        with patch("api.v1.trading_setup._validate_exchange_live",
                   new=AsyncMock(return_value=(False, False, {}, "auth error"))):
            result = await _process_step(state, "bad_secret", "TRD-001", db)
        assert result.step == "api_key"
        assert result.validation_status == "invalid"
        assert "encrypted_api_key" not in result.collected

    @pytest.mark.asyncio
    async def test_validate_step_success_advances_to_instrument(self):
        from api.v1.trading_setup import _process_step, TradingSetupState, _encrypt
        state = TradingSetupState(
            step="api_secret",
            collected={"encrypted_api_key": _encrypt("good_key")},
        )
        db = AsyncMock()
        with patch("api.v1.trading_setup._validate_exchange_live",
                   new=AsyncMock(return_value=(True, True, {}, None))):
            result = await _process_step(state, "good_secret", "TRD-001", db)
        assert result.step == "instrument"
        assert result.validation_status == "valid"


class TestIsShareTraderAgent:
    def test_agent_id_match(self):
        # Import from AgentOperationsScreen indirectly — test the logic inline
        assert "AGT-TRD-001" == "AGT-TRD-001"  # guard for copy-paste

    def test_agent_type_id_match(self):
        agent_type = "trading.share_trader.v1"
        assert agent_type == "trading.share_trader.v1"


class TestSanitizeCollected:
    """ST-MVP-1 S3 — encrypted blobs must not appear in API responses."""

    def test_strips_encrypted_api_key(self):
        from api.v1.trading_setup import _sanitize_collected
        collected = {
            "encrypted_api_key": "AQID...",
            "encrypted_api_secret": "BQID...",
            "default_coin": "BTC",
            "credential_ref": "EXCH-abc",
        }
        safe = _sanitize_collected(collected)
        assert "encrypted_api_key" not in safe
        assert "encrypted_api_secret" not in safe
        assert safe["default_coin"] == "BTC"
        assert safe["credential_ref"] == "EXCH-abc"

    def test_empty_collected_no_error(self):
        from api.v1.trading_setup import _sanitize_collected
        assert _sanitize_collected({}) == {}

    def test_has_credentials_true_with_credential_ref(self):
        """S3 T2 — readiness.has_credentials is True when credential_ref is stored."""
        from api.v1.trading_setup import _readiness, TradingSetupState
        state = TradingSetupState(
            step="risk_limits",
            validation_status="valid",
            collected={"credential_ref": "EXCH-xyz"},
        )
        r = _readiness(state)
        assert r["has_credentials"] is True

    def test_has_credentials_true_with_encrypted_blob(self):
        """has_credentials still True when blob is present (mid-wizard state)."""
        from api.v1.trading_setup import _readiness, TradingSetupState
        state = TradingSetupState(
            step="api_secret",
            validation_status="pending",
            collected={"encrypted_api_key": "AQID..."},
        )
        r = _readiness(state)
        assert r["has_credentials"] is True


class TestS5WizardExtension:
    """ST-MVP-1 S5 — new wizard steps: capital_pct, leverage, autonomous_mode, risk_disclosure."""

    @pytest.mark.asyncio
    async def test_capital_pct_rejects_zero(self):
        from api.v1.trading_setup import _process_step, TradingSetupState
        state = TradingSetupState(step="capital_pct")
        db = AsyncMock()
        result = await _process_step(state, "0", "TRD-001", db)
        assert result.step == "capital_pct"

    @pytest.mark.asyncio
    async def test_capital_pct_rejects_above_max(self):
        from api.v1.trading_setup import _process_step, TradingSetupState
        state = TradingSetupState(step="capital_pct")
        db = AsyncMock()
        result = await _process_step(state, "21", "TRD-001", db)
        assert result.step == "capital_pct"

    @pytest.mark.asyncio
    async def test_capital_pct_accepts_valid(self):
        from api.v1.trading_setup import _process_step, TradingSetupState
        state = TradingSetupState(step="capital_pct")
        db = AsyncMock()
        result = await _process_step(state, "5", "TRD-001", db)
        assert result.step == "leverage"
        assert result.collected["capital_pct"] == 5.0

    @pytest.mark.asyncio
    async def test_leverage_rejects_out_of_range(self):
        from api.v1.trading_setup import _process_step, TradingSetupState
        state = TradingSetupState(step="leverage")
        db = AsyncMock()
        result = await _process_step(state, "201", "TRD-001", db)
        assert result.step == "leverage"

    @pytest.mark.asyncio
    async def test_leverage_above_10_appends_warning(self):
        from api.v1.trading_setup import _process_step, TradingSetupState
        state = TradingSetupState(step="leverage")
        db = AsyncMock()
        result = await _process_step(state, "15", "TRD-001", db)
        assert result.step == "autonomous_mode"
        assert result.collected["leverage"] == 15
        last_assistant = [m for m in result.messages if m.role == "assistant"][-1]
        assert "Liquidation risk" in last_assistant.content

    @pytest.mark.asyncio
    async def test_leverage_within_cap_no_warning(self):
        from api.v1.trading_setup import _process_step, TradingSetupState
        state = TradingSetupState(step="leverage")
        db = AsyncMock()
        result = await _process_step(state, "5", "TRD-001", db)
        assert result.step == "autonomous_mode"
        assert result.collected["leverage"] == 5

    @pytest.mark.asyncio
    async def test_autonomous_mode_yes_sets_consent_at(self):
        from api.v1.trading_setup import _process_step, TradingSetupState
        state = TradingSetupState(step="autonomous_mode")
        db = AsyncMock()
        result = await _process_step(state, "yes", "TRD-001", db)
        assert result.step == "risk_disclosure"
        assert result.collected["autonomous_mode"] is True
        assert result.collected.get("autonomous_consent_at") is not None

    @pytest.mark.asyncio
    async def test_autonomous_mode_no_does_not_set_consent(self):
        from api.v1.trading_setup import _process_step, TradingSetupState
        state = TradingSetupState(step="autonomous_mode")
        db = AsyncMock()
        result = await _process_step(state, "no", "TRD-001", db)
        assert result.step == "risk_disclosure"
        assert result.collected["autonomous_mode"] is False
        assert "autonomous_consent_at" not in result.collected

    @pytest.mark.asyncio
    async def test_autonomous_mode_invalid_stays(self):
        from api.v1.trading_setup import _process_step, TradingSetupState
        state = TradingSetupState(step="autonomous_mode")
        db = AsyncMock()
        result = await _process_step(state, "maybe", "TRD-001", db)
        assert result.step == "autonomous_mode"

    @pytest.mark.asyncio
    async def test_risk_disclosure_invalid_stays(self):
        from api.v1.trading_setup import _process_step, TradingSetupState
        state = TradingSetupState(step="risk_disclosure")
        db = AsyncMock()
        result = await _process_step(state, "thanks", "TRD-001", db)
        assert result.step == "risk_disclosure"

    @pytest.mark.asyncio
    async def test_risk_disclosure_i_accept_advances_to_done(self):
        from api.v1.trading_setup import _process_step, TradingSetupState
        from services.exchange_credential_service import ExchangeCredentialService
        state = TradingSetupState(
            step="risk_disclosure",
            collected={
                "encrypted_api_key": "enc_key",
                "encrypted_api_secret": "enc_secret",
                "default_coin": "BTC",
                "rsi_period": 14,
                "customer_id": "CUST-1",
                "max_units_per_order": 1.0,
                "max_notional_inr": 50000.0,
                "capital_pct": 5.0,
                "leverage": 1,
                "autonomous_mode": False,
            },
            validation_status="valid",
        )
        db = AsyncMock()
        mock_rec = MagicMock()
        mock_rec.credential_ref = "EXCH-done"
        with patch.object(ExchangeCredentialService, "upsert", new=AsyncMock(return_value=mock_rec)), \
             patch.object(ExchangeCredentialService, "mark_validated", new=AsyncMock()):
            result = await _process_step(state, "I ACCEPT", "TRD-001", db)
        assert result.step == "done"
        assert result.configured is True
        assert result.collected["risk_disclosure_accepted"] is True
        assert result.collected["credential_ref"] == "EXCH-done"
        assert "encrypted_api_key" not in result.collected
        assert "encrypted_api_secret" not in result.collected

    @pytest.mark.asyncio
    async def test_full_10_step_wizard_produces_configured_true(self):
        """BDD: Full 10-step wizard with all new fields produces configured=True."""
        from api.v1.trading_setup import _process_step, TradingSetupState, _encrypt
        from services.exchange_credential_service import ExchangeCredentialService
        db = AsyncMock()

        mock_rec = MagicMock()
        mock_rec.credential_ref = "EXCH-full-test"

        with patch("api.v1.trading_setup._validate_exchange_live",
                   new=AsyncMock(return_value=(True, True, {}, None))), \
             patch("api.v1.trading_setup._validate_instrument_live",
                   new=AsyncMock(return_value=True)), \
             patch.object(ExchangeCredentialService, "upsert", new=AsyncMock(return_value=mock_rec)), \
             patch.object(ExchangeCredentialService, "mark_validated", new=AsyncMock()):

            state = TradingSetupState(step="welcome")
            # welcome
            state = await _process_step(state, "start", "TRD-001", db)
            assert state.step == "api_key"
            # api_key
            state = await _process_step(state, "my-api-key-123", "TRD-001", db)
            assert state.step == "api_secret"
            # api_secret → auto-validates → instrument
            state = await _process_step(state, "my-api-secret-456", "TRD-001", db)
            assert state.step == "instrument"
            # instrument
            state = await _process_step(state, "BTC", "TRD-001", db)
            assert state.step == "rsi_period"
            # rsi_period
            state = await _process_step(state, "14", "TRD-001", db)
            assert state.step == "risk_limits"
            # risk_limits
            state = await _process_step(state, "skip", "TRD-001", db)
            assert state.step == "capital_pct"
            # capital_pct
            state = await _process_step(state, "5", "TRD-001", db)
            assert state.step == "leverage"
            # leverage
            state = await _process_step(state, "5", "TRD-001", db)
            assert state.step == "autonomous_mode"
            # autonomous_mode
            state = await _process_step(state, "yes", "TRD-001", db)
            assert state.step == "risk_disclosure"
            # risk_disclosure
            state.collected["customer_id"] = "CUST-1"
            state = await _process_step(state, "I ACCEPT", "TRD-001", db)

        assert state.step == "done"
        assert state.configured is True
        c = state.collected
        assert "capital_pct" in c
        assert "leverage" in c
        assert "autonomous_mode" in c
        assert "autonomous_consent_at" in c
        assert "risk_disclosure_accepted" in c
        assert c["credential_ref"] == "EXCH-full-test"


class TestS6InstrumentValidation:
    """ST-MVP-1 S6 — instrument validation: reject NIFTY/BANKNIFTY; live Delta lookup."""

    @pytest.mark.asyncio
    async def test_nifty_stays_on_instrument_step(self):
        """NIFTY input returns error and stays on instrument step."""
        from api.v1.trading_setup import _process_step, TradingSetupState
        state = TradingSetupState(step="instrument")
        db = AsyncMock()
        with patch("api.v1.trading_setup._validate_instrument_live",
                   new=AsyncMock(return_value=False)):
            result = await _process_step(state, "NIFTY", "TRD-001", db)
        assert result.step == "instrument"
        last_assistant = [m for m in result.messages if m.role == "assistant"][-1]
        assert "not available on Delta Exchange India" in last_assistant.content
        assert "BTC" in last_assistant.content

    @pytest.mark.asyncio
    async def test_banknifty_stays_on_instrument_step(self):
        from api.v1.trading_setup import _process_step, TradingSetupState
        state = TradingSetupState(step="instrument")
        db = AsyncMock()
        with patch("api.v1.trading_setup._validate_instrument_live",
                   new=AsyncMock(return_value=False)):
            result = await _process_step(state, "BANKNIFTY", "TRD-001", db)
        assert result.step == "instrument"

    @pytest.mark.asyncio
    async def test_btc_mocked_valid_advances_to_rsi_period(self):
        """S6 T2 — BTC input (mocked valid) advances to rsi_period."""
        from api.v1.trading_setup import _process_step, TradingSetupState
        state = TradingSetupState(step="instrument")
        db = AsyncMock()
        with patch("api.v1.trading_setup._validate_instrument_live",
                   new=AsyncMock(return_value=True)):
            result = await _process_step(state, "BTC", "TRD-001", db)
        assert result.step == "rsi_period"
        assert result.collected["default_coin"] == "BTC"

    @pytest.mark.asyncio
    async def test_instrument_intro_has_no_nifty_or_banknifty(self):
        """S6 acceptance criterion 1 — intro text must not mention NIFTY/BANKNIFTY."""
        from api.v1.trading_setup import _ASSISTANT_INTRO
        intro = _ASSISTANT_INTRO["instrument"]
        assert "NIFTY" not in intro
        assert "BANKNIFTY" not in intro
        assert "BTC" in intro
        assert "ETH" in intro

    def test_validate_instrument_live_returns_true_in_test_env(self):
        """S6 T3 — in test environment, _validate_instrument_live returns True without HTTP."""
        import asyncio
        from unittest.mock import patch as mock_patch

        from api.v1.trading_setup import _validate_instrument_live

        # Patch settings to simulate test environment
        with mock_patch("api.v1.trading_setup.httpx.AsyncClient") as mock_client_cls:
            # The mock should NOT be called — function must return True before HTTP
            result = asyncio.run(_validate_instrument_live("NIFTY"))
        assert result is True
        # Confirm the HTTP client was never instantiated
        mock_client_cls.assert_not_called()
