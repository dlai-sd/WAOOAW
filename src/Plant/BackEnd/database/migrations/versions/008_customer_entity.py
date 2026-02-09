"""Create customer entity table

Revision ID: 008_customer_entity
Revises: 007_gateway_audit_logs
Create Date: 2026-02-08

REG-1.5: Plant stores customer identity + business profile.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers
revision = "008_customer_entity"
down_revision = "007_gateway_audit_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customer_entity",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            sa.ForeignKey("base_entity.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("phone", sa.String(50), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("business_name", sa.String(255), nullable=False),
        sa.Column("business_industry", sa.String(100), nullable=False),
        sa.Column("business_address", sa.Text, nullable=False),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("gst_number", sa.String(20), nullable=True),
        sa.Column("preferred_contact_method", sa.String(20), nullable=False),
        sa.Column("consent", sa.Boolean, nullable=False, server_default=sa.text("false")),
    )

    op.create_index("ix_customer_email", "customer_entity", ["email"])


def downgrade() -> None:
    op.drop_index("ix_customer_email", table_name="customer_entity")
    op.drop_table("customer_entity")
