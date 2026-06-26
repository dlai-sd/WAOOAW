"""TradeResultModel — individual trade outcome record (TRADER-FULL-1 S5)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, String

from core.database import Base


class TradeResultModel(Base):
    __tablename__ = "trade_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    hired_instance_id = Column(
        String,
        ForeignKey("hired_agents.hired_instance_id", ondelete="CASCADE"),
        nullable=False,
    )
    signal = Column(String(10), nullable=False)       # "BUY" | "SELL" | "HOLD"
    instrument = Column(String(50), nullable=False)
    fill_price = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)
    pnl_pct = Column(Float, nullable=True)            # (exit-fill)/fill * 100
    was_signal_correct = Column(Boolean, nullable=True)
    rsi_value = Column(Float, nullable=True)          # RSI at time of signal
    trade_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_trade_results_hired_instance_id", "hired_instance_id"),
        Index("ix_trade_results_trade_date", "trade_date"),
    )
