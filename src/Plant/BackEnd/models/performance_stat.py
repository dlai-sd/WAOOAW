"""PerformanceStat — day-keyed skill performance metrics per hired agent.

PLANT-SKILLS-1 E3-S1

Written by the daily Celery stats-collector job (out of scope for this plan).
Unique per (hired_instance_id, skill_id, platform_key, stat_date) — upsert-safe.

metrics JSONB shape by skill type:
  social-content-publisher:
    { "impressions": int, "clicks": int, "engagement_rate": float, "posts_published": int }
  execute-trade-order:
    { "trades_count": int, "pnl_pct": float, "win_rate": float,
      "stop_loss_count": int, "profit_count": int }
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from core.database import Base


class PerformanceStatModel(Base):
    __tablename__ = "performance_stats"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    hired_instance_id = Column(
        String,
        ForeignKey("hired_agents.hired_instance_id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id = Column(String, nullable=False)
    platform_key = Column(String(100), nullable=False)
    stat_date = Column(Date, nullable=False)
    metrics = Column(JSONB, nullable=False, default=dict)
    collected_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint(
            "hired_instance_id", "skill_id", "platform_key", "stat_date",
            name="uq_perf_stats_hired_skill_platform_date",
        ),
        Index("ix_performance_stats_hired_instance_id", "hired_instance_id"),
        Index("ix_performance_stats_stat_date", "stat_date"),
    )
