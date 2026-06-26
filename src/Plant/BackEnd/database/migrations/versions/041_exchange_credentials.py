"""Add exchange_credentials table.

Revision ID: 041_exchange_credentials
Revises: 040_dma_batch_type_workflow
Create Date: 2026-06-26

DB-backed exchange credential store that replaces CP's FileExchangeSetupStore.
Secrets are stored Fernet-encrypted; credential_ref is an opaque external key.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import JSONB


revision = "041_exchange_credentials"
down_revision = "040_dma_batch_type_workflow"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    existing_tables = inspector.get_table_names()
    if "exchange_credentials" in existing_tables:
        return

    op.create_table(
        "exchange_credentials",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("customer_id", sa.String(), nullable=False),
        sa.Column("credential_ref", sa.String(255), nullable=False),
        sa.Column(
            "exchange_provider",
            sa.String(100),
            nullable=False,
            server_default="delta_exchange_india",
        ),
        sa.Column("encrypted_api_key", sa.Text(), nullable=False),
        sa.Column("encrypted_api_secret", sa.Text(), nullable=False),
        sa.Column("default_coin", sa.String(50), nullable=False),
        sa.Column("allowed_coins", JSONB(), nullable=False, server_default="[]"),
        sa.Column("risk_limits", JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "validation_status",
            sa.String(50),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "credential_ref",
            name="uq_exchange_credentials_credential_ref",
        ),
        sa.UniqueConstraint(
            "customer_id",
            "exchange_provider",
            name="uq_exchange_credentials_customer_provider",
        ),
    )
    op.create_index(
        "ix_exchange_credentials_credential_ref",
        "exchange_credentials",
        ["credential_ref"],
        unique=True,
    )
    op.create_index(
        "ix_exchange_credentials_customer_id",
        "exchange_credentials",
        ["customer_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_exchange_credentials_customer_id",
        table_name="exchange_credentials",
    )
    op.drop_index(
        "ix_exchange_credentials_credential_ref",
        table_name="exchange_credentials",
    )
    op.drop_table("exchange_credentials")
