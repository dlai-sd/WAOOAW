"""add Plant-owned PP agent authoring drafts table

Revision ID: 034_pp_agent_authoring_drafts
Revises: 033_agent_catalog_lifecycle
Create Date: 2026-03-14

Story: PP-AGENT-LIFECYCLE-1 E1-S1
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "034_pp_agent_authoring_drafts"
down_revision = "033_agent_catalog_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_authoring_drafts",
        sa.Column("draft_id", sa.String(), nullable=False),
        sa.Column("candidate_agent_type_id", sa.String(), nullable=False),
        sa.Column("candidate_agent_label", sa.String(), nullable=False),
        sa.Column(
            "contract_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "section_states",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "constraint_policy",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "reviewer_comments",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("reviewer_id", sa.String(), nullable=True),
        sa.Column("reviewer_name", sa.String(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("draft_id", name="pk_agent_authoring_drafts"),
    )

    op.create_index(
        "ix_agent_authoring_drafts_candidate_agent_type_id",
        "agent_authoring_drafts",
        ["candidate_agent_type_id"],
        unique=False,
    )
    op.create_index(
        "ix_agent_authoring_drafts_status",
        "agent_authoring_drafts",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_agent_authoring_drafts_status",
        table_name="agent_authoring_drafts",
    )
    op.drop_index(
        "ix_agent_authoring_drafts_candidate_agent_type_id",
        table_name="agent_authoring_drafts",
    )
    op.drop_table("agent_authoring_drafts")