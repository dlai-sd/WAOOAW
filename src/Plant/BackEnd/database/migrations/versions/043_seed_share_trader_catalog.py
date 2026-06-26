"""Seed Share Trader catalog release so it appears in the CP hiring marketplace.

Revision ID: 043_seed_share_trader_catalog
Revises: 042_trade_results
Create Date: 2026-06-26

Root cause: agent_catalog_releases had no row for AGT-TRD-001 (Share Trader).
The list_live_releases() query filters approved_for_new_hire=True AND
retired_from_catalog_at IS NULL, so the agent was invisible to the CP portal.
AGT-MKT-DMA-001 had a row (lifecycle_state='live_on_cp', approved_for_new_hire=t)
but AGT-TRD-001 did not.
"""
from __future__ import annotations

from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

revision = "043_seed_share_trader_catalog"
down_revision = "042_trade_results"
branch_labels = None
depends_on = None

_NOW = datetime.now(timezone.utc)

_RELEASE_ID = "car-trd-v1-live"
_AGENT_ID = "AGT-TRD-001"
_AGENT_TYPE_ID = "trading.share_trader.v1"


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO agent_catalog_releases (
                release_id,
                agent_id,
                agent_type_id,
                internal_definition_version_id,
                external_catalog_version,
                public_name,
                short_description,
                industry_name,
                job_role_label,
                monthly_price_inr,
                trial_days,
                allowed_durations,
                supported_channels,
                approval_mode,
                lifecycle_state,
                approved_for_new_hire,
                retired_from_catalog_at,
                created_at,
                updated_at
            ) VALUES (
                :release_id,
                :agent_id,
                :agent_type_id,
                NULL,
                :external_catalog_version,
                :public_name,
                :short_description,
                :industry_name,
                :job_role_label,
                :monthly_price_inr,
                :trial_days,
                :allowed_durations,
                :supported_channels,
                :approval_mode,
                :lifecycle_state,
                :approved_for_new_hire,
                NULL,
                :created_at,
                :updated_at
            )
            ON CONFLICT (agent_id, external_catalog_version) DO UPDATE SET
                lifecycle_state          = EXCLUDED.lifecycle_state,
                approved_for_new_hire    = EXCLUDED.approved_for_new_hire,
                public_name              = EXCLUDED.public_name,
                short_description        = EXCLUDED.short_description,
                updated_at               = EXCLUDED.updated_at
            """
        ).bindparams(
            release_id=_RELEASE_ID,
            agent_id=_AGENT_ID,
            agent_type_id=_AGENT_TYPE_ID,
            external_catalog_version="v1",
            public_name="Share Trader",
            short_description=(
                "Autonomous RSI-driven trading agent for Delta Exchange. "
                "Analyses market candles, generates BUY/SELL signals, and "
                "executes approved orders within your configured risk limits. "
                "7-day free trial — keep all trade history."
            ),
            industry_name="Finance",
            job_role_label="Algo Trader",
            monthly_price_inr=15000,
            trial_days=7,
            allowed_durations='["monthly", "quarterly"]',
            supported_channels='["delta_exchange"]',
            approval_mode="manual_review",
            lifecycle_state="live_on_cp",
            approved_for_new_hire=True,
            created_at=_NOW,
            updated_at=_NOW,
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM agent_catalog_releases WHERE agent_id = :agent_id"
        ).bindparams(agent_id=_AGENT_ID)
    )
