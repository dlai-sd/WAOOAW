"""add_token_version_to_customer_entity

Revision ID: 017_token_version
Revises: 016_otp_sessions
Create Date: 2026-03-03

Story: E2-S3 — Revoke all tokens on password reset.
Purpose: Add ``token_version`` column to ``customer_entity``.  When a customer
         resets their password, this counter is incremented so all outstanding
         JWTs (which carry the old version) are immediately rejected by the
         Gateway middleware.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "017_token_version"
down_revision = "016_otp_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add token_version column to customer_entity."""
    op.add_column(
        "customer_entity",
        sa.Column(
            "token_version",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )


def downgrade() -> None:
    """Remove token_version column from customer_entity."""
    op.drop_column("customer_entity", "token_version")
