"""add credential_ref, secret_manager_ref, posting_identity, metadata to customer_platform_credentials

Revision ID: 039_credential_ref_and_secret_manager_ref
Revises: 038_add_brand_voices
Create Date: 2026-04-14

Moves the credential record index from CP's ephemeral JSONL file
into the persistent Plant DB so credentials survive container restarts.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision = "039_credential_ref_and_secret_manager_ref"
down_revision = "038_add_brand_voices"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    def column_exists(table_name: str, column_name: str) -> bool:
        return any(c["name"] == column_name for c in inspector.get_columns(table_name))

    def index_exists(table_name: str, index_name: str) -> bool:
        return any(i["name"] == index_name for i in inspector.get_indexes(table_name))

    if not column_exists("customer_platform_credentials", "credential_ref"):
        op.add_column(
            "customer_platform_credentials",
            sa.Column("credential_ref", sa.String(length=255), nullable=True),
        )

    if not column_exists("customer_platform_credentials", "secret_manager_ref"):
        op.add_column(
            "customer_platform_credentials",
            sa.Column("secret_manager_ref", sa.Text(), nullable=True),
        )

    if not column_exists("customer_platform_credentials", "posting_identity"):
        op.add_column(
            "customer_platform_credentials",
            sa.Column("posting_identity", sa.String(length=255), nullable=True),
        )

    if not column_exists("customer_platform_credentials", "metadata"):
        op.add_column(
            "customer_platform_credentials",
            sa.Column(
                "metadata",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
        )

    if not index_exists("customer_platform_credentials", "ix_customer_platform_credentials_credential_ref"):
        op.create_index(
            "ix_customer_platform_credentials_credential_ref",
            "customer_platform_credentials",
            ["credential_ref"],
            unique=True,
        )


def downgrade() -> None:
    op.drop_index(
        "ix_customer_platform_credentials_credential_ref",
        table_name="customer_platform_credentials",
    )
    op.drop_column("customer_platform_credentials", "metadata")
    op.drop_column("customer_platform_credentials", "posting_identity")
    op.drop_column("customer_platform_credentials", "secret_manager_ref")
    op.drop_column("customer_platform_credentials", "credential_ref")
