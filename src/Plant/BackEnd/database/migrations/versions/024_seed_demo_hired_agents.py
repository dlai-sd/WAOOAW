"""seed demo hired agents for yogesh and rupali

Revision ID: 024_seed_demo_hired_agents
Revises: 023_performance_stats
Create Date: 2026-03-01

Purpose:
    Seed two demo hired agents for each test user so My Agents page shows
    cards during development/demo.  Idempotent — uses ON CONFLICT DO NOTHING.

customer_ids (from demo DB customer_entity table — confirmed 2026-03-01):
    yogeshkhandge@gmail.com  → 1a9c1294-073e-4565-a359-27eae94a05b4
    rupalikhandge@gmail.com  → 8a8e1d58-949f-41f3-81ff-7abf5d4a172e

    These are hardcoded below — no env vars required.
    Run: alembic upgrade head
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from alembic import op
import sqlalchemy as sa


# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------
revision = "024_seed_demo_hired_agents"
down_revision = "023_performance_stats"
branch_labels = None
depends_on = None

# ---------------------------------------------------------------------------
# Constants — agent catalogue
# ---------------------------------------------------------------------------
_NOW = datetime.now(timezone.utc)
_TRIAL_START = _NOW - timedelta(days=30)
_TRIAL_END   = _NOW + timedelta(days=30)

_AGENTS = [
    {
        "agent_id":      "AGT-MKT-001",
        "agent_type_id": "marketing.digital_marketing.v1",
        "nickname":      "Content Creator & Publisher",
        "theme":         "purple",
    },
    {
        "agent_id":      "AGT-TRD-001",
        "agent_type_id": "trading.share_trader.v1",
        "nickname":      "Share Trader",
        "theme":         "cyan",
    },
]

_USERS = [
    {
        "label":       "yogesh",
        "customer_id": "1a9c1294-073e-4565-a359-27eae94a05b4",  # yogeshkhandge@gmail.com
        "sub_prefix":  "SUB-YOGESH",
        "inst_prefix": "INST-YOGESH",
    },
    {
        "label":       "rupali",
        "customer_id": "8a8e1d58-949f-41f3-81ff-7abf5d4a172e",  # rupalikhandge@gmail.com
        "sub_prefix":  "SUB-RUPALI",
        "inst_prefix": "INST-RUPALI",
    },
]


def _rows() -> list[dict]:
    """Build the hired_agent rows to insert."""
    rows = []
    for user in _USERS:
        customer_id = user["customer_id"]
        for i, agent in enumerate(_AGENTS, start=1):
            rows.append(
                {
                    "hired_instance_id": f"{user['inst_prefix']}-{i:02d}",
                    "subscription_id":   f"{user['sub_prefix']}-{i:02d}",
                    "agent_id":          agent["agent_id"],
                    "agent_type_id":     agent["agent_type_id"],
                    "customer_id":       customer_id,
                    "nickname":          agent["nickname"],
                    "theme":             agent["theme"],
                    "config":            "{}",
                    "configured":        False,
                    "goals_completed":   False,
                    "active":            True,
                    "trial_status":      "active",
                    "trial_start_at":    _TRIAL_START,
                    "trial_end_at":      _TRIAL_END,
                    "created_at":        _NOW,
                    "updated_at":        _NOW,
                }
            )
    return rows


def upgrade() -> None:
    connection = op.get_bind()
    for row in _rows():
        # agent_type_id was added in migration 015 which is not yet applied to
        # all environments — omit it so this seed runs on demo DB too.
        row_without_type = {k: v for k, v in row.items() if k != "agent_type_id"}
        connection.execute(
            sa.text(
                """
                INSERT INTO hired_agents (
                    hired_instance_id, subscription_id, agent_id,
                    customer_id, nickname, theme, config,
                    configured, goals_completed, active,
                    trial_status, trial_start_at, trial_end_at,
                    created_at, updated_at
                )
                VALUES (
                    :hired_instance_id, :subscription_id, :agent_id,
                    :customer_id, :nickname, :theme, :config::jsonb,
                    :configured, :goals_completed, :active,
                    :trial_status, :trial_start_at, :trial_end_at,
                    :created_at, :updated_at
                )
                ON CONFLICT (subscription_id) DO NOTHING
                """
            ),
            row_without_type,
        )


def downgrade() -> None:
    connection = op.get_bind()
    sub_ids = [
        f"{u['sub_prefix']}-{i:02d}"
        for u in _USERS
        for i in range(1, len(_AGENTS) + 1)
    ]
    connection.execute(
        sa.text("DELETE FROM hired_agents WHERE subscription_id = ANY(:ids)"),
        {"ids": sub_ids},
    )
