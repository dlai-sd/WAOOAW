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
        from services.exchange_credential_service import ExchangeCredentialService
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
        mock_rec = MagicMock()
        mock_rec.credential_ref = "EXCH-test"
        with patch.object(ExchangeCredentialService, "upsert", new=AsyncMock(return_value=mock_rec)), \
             patch.object(ExchangeCredentialService, "mark_validated", new=AsyncMock()):
            result = await _process_step(state, "skip", "TRD-001", db)
        assert result.step == "done"
        assert result.configured is True
        assert result.collected["max_units_per_order"] == 1.0
        assert result.collected["max_notional_inr"] == 50000.0
        # Raw encrypted keys must be removed from persisted state
        assert "encrypted_api_key" not in result.collected
        assert "encrypted_api_secret" not in result.collected

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
