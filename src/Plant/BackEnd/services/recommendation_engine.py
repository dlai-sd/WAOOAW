"""Pluggable recommendation engine (TRADER-FULL-1 It2 S2).

RECOMMENDATION_ENGINE env var selects the engine:
  "rule_based"  — default: RSI threshold tuning from signal accuracy stats
  "llm"         — future: LLM-generated recommendations (next iteration)

To add a new engine: subclass RecommendationEngine, register in ENGINE_REGISTRY.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.logging import PiiMaskingFilter
from models.trade_result import TradeResultModel

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())


@dataclass
class TradeRecommendation:
    current_rsi_buy_threshold: float
    current_rsi_sell_threshold: float
    suggested_rsi_buy_threshold: float
    suggested_rsi_sell_threshold: float
    confidence: float       # 0.0–1.0
    rationale: str
    sample_size: int
    engine: str             # "rule_based" | "llm" | ...


class RecommendationEngine(ABC):
    """Abstract base — implement generate() to plug in any strategy."""

    @abstractmethod
    async def generate(
        self,
        *,
        hired_instance_id: str,
        db: AsyncSession,
        sample_size: int = 20,
    ) -> TradeRecommendation: ...


class RuleBasedRecommendationEngine(RecommendationEngine):
    """RSI threshold tuning from signal accuracy stats.

    Logic:
    - If BUY signal accuracy < 50%: raise buy threshold by 5 (more conservative)
    - If SELL signal accuracy < 50%: lower sell threshold by 5 (more conservative)
    - Confidence = min(sample_size / 20, 1.0)
    """

    async def generate(
        self,
        *,
        hired_instance_id: str,
        db: AsyncSession,
        sample_size: int = 20,
    ) -> TradeRecommendation:
        result = await db.execute(
            select(TradeResultModel)
            .where(TradeResultModel.hired_instance_id == hired_instance_id)
            .order_by(TradeResultModel.trade_date.desc())
            .limit(sample_size)
        )
        rows: List[TradeResultModel] = result.scalars().all()

        buy_threshold, sell_threshold = 30.0, 70.0  # platform defaults

        if not rows:
            return TradeRecommendation(
                current_rsi_buy_threshold=buy_threshold,
                current_rsi_sell_threshold=sell_threshold,
                suggested_rsi_buy_threshold=buy_threshold,
                suggested_rsi_sell_threshold=sell_threshold,
                confidence=0.0,
                rationale="Insufficient trade history (0 trades).",
                sample_size=0,
                engine="rule_based",
            )

        buys = [r for r in rows if r.signal == "BUY" and r.was_signal_correct is not None]
        sells = [r for r in rows if r.signal == "SELL" and r.was_signal_correct is not None]

        buy_accuracy = sum(1 for r in buys if r.was_signal_correct) / max(len(buys), 1)
        sell_accuracy = sum(1 for r in sells if r.was_signal_correct) / max(len(sells), 1)

        new_buy = buy_threshold + 5 if buy_accuracy < 0.5 else buy_threshold
        new_sell = sell_threshold - 5 if sell_accuracy < 0.5 else sell_threshold

        confidence = min(len(rows) / 20.0, 1.0)

        parts = []
        parts.append(
            f"BUY accuracy {buy_accuracy:.0%} over {len(buys)} signals; "
            f"SELL accuracy {sell_accuracy:.0%} over {len(sells)} signals."
        )
        if new_buy > buy_threshold:
            parts.append("Raising BUY threshold.")
        if new_sell < sell_threshold:
            parts.append("Lowering SELL threshold.")
        if new_buy == buy_threshold and new_sell == sell_threshold:
            parts.append("No change needed.")
        rationale = " ".join(parts).strip()

        return TradeRecommendation(
            current_rsi_buy_threshold=buy_threshold,
            current_rsi_sell_threshold=sell_threshold,
            suggested_rsi_buy_threshold=new_buy,
            suggested_rsi_sell_threshold=new_sell,
            confidence=confidence,
            rationale=rationale,
            sample_size=len(rows),
            engine="rule_based",
        )


ENGINE_REGISTRY = {"rule_based": RuleBasedRecommendationEngine}


def get_recommendation_engine() -> RecommendationEngine:
    engine_name = getattr(settings, "recommendation_engine", "rule_based")
    cls = ENGINE_REGISTRY.get(engine_name, RuleBasedRecommendationEngine)
    return cls()
