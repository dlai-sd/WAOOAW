"""add_publish_receipts

Revision ID: 036_add_publish_receipts
Revises: 035_customer_platform_credentials_and_oauth_sessions
Create Date: 2026-04-01
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "036_add_publish_receipts"
down_revision = "035_customer_platform_credentials_and_oauth_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "publish_receipts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("post_id", sa.String(), nullable=False),
        sa.Column("destination_type", sa.String(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("platform_post_id", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("raw_response", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_publish_receipts"),
    )
    op.create_index("ix_publish_receipts_post_id", "publish_receipts", ["post_id"])
    op.create_index(
        "ix_publish_receipts_post_dest",
        "publish_receipts",
        ["post_id", "destination_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_publish_receipts_post_dest", table_name="publish_receipts")
    op.drop_index("ix_publish_receipts_post_id", table_name="publish_receipts")
    op.drop_table("publish_receipts")
