"""create_feature_flags_table

Revision ID: 019_feature_flags
Revises: 018_audit_logs
Create Date: 2026-02-26

Iteration 7 — E2-S1 (Scale Prep)
Purpose: Feature flag table enabling dark deployments and percentage-based
         rollouts without redeployment.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY, TEXT


# revision identifiers, used by Alembic.
revision = "019_feature_flags"
down_revision = "018_audit_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create feature_flags table with indexes."""
    op.create_table(
        "feature_flags",
        sa.Column(
            "key",
            sa.Text(),
            primary_key=True,
            nullable=False,
            comment="Unique flag identifier e.g. new_dashboard_v2",
        ),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="Master switch — false means flag is off for everyone",
        ),
        sa.Column(
            "rollout_percentage",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("100"),
            comment="0-100 — 100=everyone, 0=nobody (ignored when enabled=false)",
        ),
        sa.Column(
            "enabled_for_customer_ids",
            ARRAY(PG_UUID(as_uuid=True)),
            nullable=True,
            comment="Optional allowlist — these customers always see the flag enabled",
        ),
        sa.Column(
            "scope",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'all'"),
            comment="Which frontend surfaces see this flag: all | cp | plant | mobile",
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="Human-readable purpose of the flag",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            onupdate=sa.text("NOW()"),
            nullable=False,
        ),
    )
    # Index to quickly fetch flags by scope (CP proxy filters by scope=cp)
    op.create_index("ix_feature_flags_scope", "feature_flags", ["scope"])
    # Rollout constraint: 0 <= rollout_percentage <= 100
    op.create_check_constraint(
        "ck_feature_flags_rollout_pct",
        "feature_flags",
        "rollout_percentage >= 0 AND rollout_percentage <= 100",
    )


def downgrade() -> None:
    op.drop_index("ix_feature_flags_scope", table_name="feature_flags")
    op.drop_constraint("ck_feature_flags_rollout_pct", "feature_flags", type_="check")
    op.drop_table("feature_flags")
