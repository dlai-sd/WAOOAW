"""Unit tests for RuleBasedRecommendationEngine (TRADER-FULL-1 It2 S2)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_trade_row(signal: str = "BUY", was_signal_correct: bool | None = True):
    rec = MagicMock()
    rec.signal = signal
    rec.was_signal_correct = was_signal_correct
    rec.rsi_value = 28.5
    return rec


def _make_db(rows):
    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    db.execute.return_value = result
    return db


# ── Tests ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rule_based_no_trades_returns_defaults():
    """0 trade history → default thresholds, confidence=0.0."""
    from services.recommendation_engine import RuleBasedRecommendationEngine

    engine = RuleBasedRecommendationEngine()
    rec = await engine.generate(
        hired_instance_id="trader-001",
        db=_make_db([]),
    )
    assert rec.suggested_rsi_buy_threshold == 30.0
    assert rec.suggested_rsi_sell_threshold == 70.0
    assert rec.confidence == 0.0
    assert rec.sample_size == 0
    assert rec.engine == "rule_based"


@pytest.mark.asyncio
async def test_rule_based_poor_buy_accuracy_raises_threshold():
    """10 BUY signals all wrong → buy threshold raises by 5."""
    from services.recommendation_engine import RuleBasedRecommendationEngine

    rows = [_make_trade_row(signal="BUY", was_signal_correct=False) for _ in range(10)]
    engine = RuleBasedRecommendationEngine()
    rec = await engine.generate(
        hired_instance_id="trader-001",
        db=_make_db(rows),
        sample_size=10,
    )
    assert rec.suggested_rsi_buy_threshold == 35.0
    assert rec.suggested_rsi_sell_threshold == 70.0  # unchanged


@pytest.mark.asyncio
async def test_rule_based_poor_sell_accuracy_lowers_threshold():
    """10 SELL signals all wrong → sell threshold lowers by 5."""
    from services.recommendation_engine import RuleBasedRecommendationEngine

    rows = [_make_trade_row(signal="SELL", was_signal_correct=False) for _ in range(10)]
    engine = RuleBasedRecommendationEngine()
    rec = await engine.generate(
        hired_instance_id="trader-001",
        db=_make_db(rows),
        sample_size=10,
    )
    assert rec.suggested_rsi_sell_threshold == 65.0
    assert rec.suggested_rsi_buy_threshold == 30.0  # unchanged


@pytest.mark.asyncio
async def test_rule_based_good_accuracy_no_change():
    """10 correct BUY signals → no threshold change, rationale says 'No change'."""
    from services.recommendation_engine import RuleBasedRecommendationEngine

    rows = [_make_trade_row(signal="BUY", was_signal_correct=True) for _ in range(10)]
    engine = RuleBasedRecommendationEngine()
    rec = await engine.generate(
        hired_instance_id="trader-001",
        db=_make_db(rows),
        sample_size=10,
    )
    assert rec.suggested_rsi_buy_threshold == 30.0
    assert "No change needed" in rec.rationale


@pytest.mark.asyncio
async def test_confidence_zero_when_no_trades():
    """confidence = 0.0 when sample_size=0."""
    from services.recommendation_engine import RuleBasedRecommendationEngine

    engine = RuleBasedRecommendationEngine()
    rec = await engine.generate(
        hired_instance_id="trader-001",
        db=_make_db([]),
    )
    assert rec.confidence == 0.0


@pytest.mark.asyncio
async def test_confidence_one_when_twenty_or_more_trades():
    """confidence = 1.0 when sample_size >= 20."""
    from services.recommendation_engine import RuleBasedRecommendationEngine

    rows = [_make_trade_row(signal="BUY", was_signal_correct=True) for _ in range(20)]
    engine = RuleBasedRecommendationEngine()
    rec = await engine.generate(
        hired_instance_id="trader-001",
        db=_make_db(rows),
        sample_size=20,
    )
    assert rec.confidence == 1.0


def test_engine_registry_selects_rule_based():
    """get_recommendation_engine() returns RuleBasedRecommendationEngine by default."""
    from services.recommendation_engine import (
        RuleBasedRecommendationEngine,
        get_recommendation_engine,
    )

    engine = get_recommendation_engine()
    assert isinstance(engine, RuleBasedRecommendationEngine)


def test_engine_registry_unknown_falls_back_to_rule_based(monkeypatch):
    """Unknown RECOMMENDATION_ENGINE value falls back to RuleBasedRecommendationEngine."""
    monkeypatch.setenv("RECOMMENDATION_ENGINE", "llm_v99")
    import core.config as config_module

    config_module.get_settings.cache_clear()
    config_module.settings = config_module.get_settings()

    from services.recommendation_engine import (
        RuleBasedRecommendationEngine,
        get_recommendation_engine,
    )

    engine = get_recommendation_engine()
    assert isinstance(engine, RuleBasedRecommendationEngine)

    # restore
    monkeypatch.setenv("RECOMMENDATION_ENGINE", "rule_based")
    config_module.get_settings.cache_clear()
    config_module.settings = config_module.get_settings()
