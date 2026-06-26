"""Add trade_results table.

Revision ID: 042_trade_results
Revises: 041_exchange_credentials
Create Date: 2026-06-26

Individual trade outcome records — signal, fill_price, pnl_pct, was_signal_correct.
These feed the Iteration 2 recommendation engine.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "042_trade_results"
down_revision = "041_exchange_credentials"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    existing_tables = inspector.get_table_names()
    if "trade_results" in existing_tables:
        return

    op.create_table(
        "trade_results",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("hired_instance_id", sa.String(), nullable=False),
        sa.Column("signal", sa.String(10), nullable=False),
        sa.Column("instrument", sa.String(50), nullable=False),
        sa.Column("fill_price", sa.Float(), nullable=True),
        sa.Column("exit_price", sa.Float(), nullable=True),
        sa.Column("pnl_pct", sa.Float(), nullable=True),
        sa.Column("was_signal_correct", sa.Boolean(), nullable=True),
        sa.Column("rsi_value", sa.Float(), nullable=True),
        sa.Column(
            "trade_date",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["hired_instance_id"],
            ["hired_agents.hired_instance_id"],
            name="fk_trade_results_hired_instance_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_trade_results_hired_instance_id",
        "trade_results",
        ["hired_instance_id"],
    )
    op.create_index(
        "ix_trade_results_trade_date",
        "trade_results",
        ["trade_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_trade_results_trade_date", table_name="trade_results")
    op.drop_index("ix_trade_results_hired_instance_id", table_name="trade_results")
    op.drop_table("trade_results")
