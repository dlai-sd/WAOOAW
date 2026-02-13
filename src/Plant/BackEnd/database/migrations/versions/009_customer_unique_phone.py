"""Add unique constraint for customer phone

Revision ID: 009_customer_unique_phone
Revises: 008_customer_entity
Create Date: 2026-02-08

AUTH-1.3: Plant is the auth source-of-truth for customer identity.
Enforce uniqueness for customer phone numbers.
"""

from alembic import op


# revision identifiers
revision = "009_customer_unique_phone"
down_revision = "008_customer_entity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_customer_phone",
        "customer_entity",
        ["phone"],
    )
    op.create_index("ix_customer_phone", "customer_entity", ["phone"])


def downgrade() -> None:
    # Use batch operations with if_exists for idempotency
    op.drop_index("ix_customer_phone", table_name="customer_entity", if_exists=True)
    op.drop_constraint("uq_customer_phone", "customer_entity", type_="unique")
