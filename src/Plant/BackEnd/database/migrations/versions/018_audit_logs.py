"""create_audit_logs_table

Revision ID: 018_audit_logs
Revises: 017_token_version
Create Date: 2026-02-26

Iteration 2 — Audit API (E1-S1)
Purpose: Single audit_logs table for all significant business events across
         all interfaces (CP web, mobile, Plant admin, APIs). Event records
         are append-only and soft-deleted only.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB


# revision identifiers, used by Alembic.
revision = "018_audit_logs"
down_revision = "017_token_version"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create audit_logs table with indexes."""
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            PG_UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        # User identity (nullable — pre-registration events may have no user_id)
        sa.Column("user_id", PG_UUID(as_uuid=True), nullable=True),
        sa.Column("email", sa.Text(), nullable=True),
        # Request context
        sa.Column("ip_address", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        # Event classification
        sa.Column("screen", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column(
            "outcome",
            sa.Text(),
            nullable=False,
            # Must be 'success' or 'failure'
        ),
        # Detail + metadata
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("metadata", JSONB(), nullable=True, server_default="{}"),
        # Tracing
        sa.Column("correlation_id", sa.Text(), nullable=True),
        # Soft delete
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Outcome constraint
        sa.CheckConstraint(
            "outcome IN ('success', 'failure')",
            name="ck_audit_logs_outcome",
        ),
    )

    # Indexes for common filter/query patterns
    op.create_index("idx_audit_logs_email", "audit_logs", ["email"])
    op.create_index("idx_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("idx_audit_logs_action", "audit_logs", ["action"])
    op.create_index("idx_audit_logs_screen", "audit_logs", ["screen"])
    op.create_index(
        "idx_audit_logs_timestamp",
        "audit_logs",
        [sa.text("timestamp DESC")],
    )
    op.create_index(
        "idx_audit_logs_correlation_id",
        "audit_logs",
        ["correlation_id"],
    )


def downgrade() -> None:
    """Drop audit_logs table and all indexes."""
    op.drop_index("idx_audit_logs_correlation_id", table_name="audit_logs")
    op.drop_index("idx_audit_logs_timestamp", table_name="audit_logs")
    op.drop_index("idx_audit_logs_screen", table_name="audit_logs")
    op.drop_index("idx_audit_logs_action", table_name="audit_logs")
    op.drop_index("idx_audit_logs_user_id", table_name="audit_logs")
    op.drop_index("idx_audit_logs_email", table_name="audit_logs")
    op.drop_table("audit_logs")
