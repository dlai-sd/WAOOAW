"""performance_stats table

Revision ID: 023_performance_stats
Revises: 022_platform_connections
Create Date: 2026-03-01

PLANT-SKILLS-1 E3-S1

Day-keyed skill performance metrics written by the daily Celery stats-collector job.
One row per (hired_instance_id, skill_id, platform_key, stat_date).

metrics JSONB shape by skill type:
  social-content-publisher:
    { "impressions": int, "clicks": int, "engagement_rate": float, "posts_published": int }
  execute-trade-order:
    { "trades_count": int, "pnl_pct": float, "win_rate": float,
      "stop_loss_count": int, "profit_count": int }
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "023_performance_stats"
down_revision = "022_platform_connections"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "performance_stats",
        sa.Column("id", sa.String, primary_key=True, nullable=False),
        sa.Column(
            "hired_instance_id",
            sa.String,
            sa.ForeignKey("hired_agents.hired_instance_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("skill_id", sa.String, nullable=False),
        sa.Column("platform_key", sa.String(100), nullable=False),
        sa.Column("stat_date", sa.Date, nullable=False),
        sa.Column(
            "metrics",
            postgresql.JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "collected_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_unique_constraint(
        "uq_perf_stats_hired_skill_platform_date",
        "performance_stats",
        ["hired_instance_id", "skill_id", "platform_key", "stat_date"],
    )
    op.create_index(
        "ix_performance_stats_hired_instance_id",
        "performance_stats",
        ["hired_instance_id"],
    )
    op.create_index(
        "ix_performance_stats_stat_date",
        "performance_stats",
        ["stat_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_performance_stats_stat_date", table_name="performance_stats")
    op.drop_index(
        "ix_performance_stats_hired_instance_id", table_name="performance_stats"
    )
    op.drop_constraint(
        "uq_perf_stats_hired_skill_platform_date",
        "performance_stats",
        type_="unique",
    )
    op.drop_table("performance_stats")
