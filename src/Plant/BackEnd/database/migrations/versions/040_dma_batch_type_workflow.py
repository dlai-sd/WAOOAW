"""Add batch_type and parent_batch_id to marketing_draft_batches

Revision ID: 040_dma_batch_type_workflow
Revises: 039_credential_ref_and_secret_manager_ref
Create Date: 2026-04-15

Enables the two-stage DMA workflow:
  - batch_type = 'theme'   → content plan/table draft for customer to approve
  - batch_type = 'content' → actual posts created after theme is approved
  - batch_type = 'direct'  → legacy single-step batch (default, backward-compatible)

parent_batch_id links a content batch back to the theme batch it was derived from.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "040_dma_batch_type_workflow"
down_revision = "039_credential_ref_and_secret_manager_ref"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    def column_exists(table_name: str, column_name: str) -> bool:
        return any(c["name"] == column_name for c in inspector.get_columns(table_name))

    def index_exists(table_name: str, index_name: str) -> bool:
        return any(i["name"] == index_name for i in inspector.get_indexes(table_name))

    if not column_exists("marketing_draft_batches", "batch_type"):
        op.add_column(
            "marketing_draft_batches",
            sa.Column(
                "batch_type",
                sa.String(length=32),
                nullable=False,
                server_default="direct",
            ),
        )

    if not column_exists("marketing_draft_batches", "parent_batch_id"):
        op.add_column(
            "marketing_draft_batches",
            sa.Column("parent_batch_id", sa.String(), nullable=True),
        )
        op.create_foreign_key(
            "fk_marketing_draft_batches_parent_batch_id",
            "marketing_draft_batches",
            "marketing_draft_batches",
            ["parent_batch_id"],
            ["batch_id"],
            ondelete="SET NULL",
        )

    if not index_exists("marketing_draft_batches", "ix_marketing_draft_batches_batch_type"):
        op.create_index(
            "ix_marketing_draft_batches_batch_type",
            "marketing_draft_batches",
            ["batch_type"],
        )

    if not index_exists("marketing_draft_batches", "ix_marketing_draft_batches_parent_batch_id"):
        op.create_index(
            "ix_marketing_draft_batches_parent_batch_id",
            "marketing_draft_batches",
            ["parent_batch_id"],
        )


def downgrade() -> None:
    op.drop_index(
        "ix_marketing_draft_batches_parent_batch_id",
        table_name="marketing_draft_batches",
    )
    op.drop_index(
        "ix_marketing_draft_batches_batch_type",
        table_name="marketing_draft_batches",
    )
    op.drop_constraint(
        "fk_marketing_draft_batches_parent_batch_id",
        "marketing_draft_batches",
        type_="foreignkey",
    )
    op.drop_column("marketing_draft_batches", "parent_batch_id")
    op.drop_column("marketing_draft_batches", "batch_type")
