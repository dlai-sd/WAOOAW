"""add customer platform credentials and oauth connection sessions

Revision ID: 035_customer_platform_credentials_and_oauth_sessions
Revises: 034_pp_agent_authoring_drafts
Create Date: 2026-03-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "035_customer_platform_credentials_and_oauth_sessions"
down_revision = "034_pp_agent_authoring_drafts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customer_platform_credentials",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("customer_id", sa.String(), nullable=False),
        sa.Column("platform_key", sa.String(length=100), nullable=False),
        sa.Column("provider_account_id", sa.String(length=255), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column(
            "granted_scopes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("verification_status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("connection_status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("secret_ref", sa.Text(), nullable=False),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_customer_platform_credentials"),
        sa.UniqueConstraint(
            "customer_id",
            "platform_key",
            "provider_account_id",
            name="uq_customer_platform_credential_customer_platform_provider",
        ),
    )
    op.create_index(
        "ix_customer_platform_credentials_customer_id",
        "customer_platform_credentials",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        "ix_customer_platform_credentials_platform_key",
        "customer_platform_credentials",
        ["platform_key"],
        unique=False,
    )

    op.create_table(
        "oauth_connection_sessions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("customer_id", sa.String(), nullable=False),
        sa.Column("platform_key", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=255), nullable=False),
        sa.Column("nonce", sa.String(length=255), nullable=False),
        sa.Column("redirect_uri", sa.String(length=1024), nullable=False),
        sa.Column("code_verifier", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_oauth_connection_sessions"),
        sa.UniqueConstraint("state", name="uq_oauth_connection_sessions_state"),
    )
    op.create_index(
        "ix_oauth_connection_sessions_customer_id",
        "oauth_connection_sessions",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        "ix_oauth_connection_sessions_platform_key",
        "oauth_connection_sessions",
        ["platform_key"],
        unique=False,
    )

    op.add_column(
        "platform_connections",
        sa.Column("customer_platform_credential_id", sa.String(), nullable=True),
    )
    op.create_foreign_key(
        "fk_platform_connections_customer_platform_credential_id",
        "platform_connections",
        "customer_platform_credentials",
        ["customer_platform_credential_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_platform_connections_customer_platform_credential_id",
        "platform_connections",
        ["customer_platform_credential_id"],
        unique=False,
    )
    op.alter_column("platform_connections", "secret_ref", existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    op.alter_column("platform_connections", "secret_ref", existing_type=sa.Text(), nullable=False)
    op.drop_index(
        "ix_platform_connections_customer_platform_credential_id",
        table_name="platform_connections",
    )
    op.drop_constraint(
        "fk_platform_connections_customer_platform_credential_id",
        "platform_connections",
        type_="foreignkey",
    )
    op.drop_column("platform_connections", "customer_platform_credential_id")

    op.drop_index("ix_oauth_connection_sessions_platform_key", table_name="oauth_connection_sessions")
    op.drop_index("ix_oauth_connection_sessions_customer_id", table_name="oauth_connection_sessions")
    op.drop_table("oauth_connection_sessions")

    op.drop_index(
        "ix_customer_platform_credentials_platform_key",
        table_name="customer_platform_credentials",
    )
    op.drop_index(
        "ix_customer_platform_credentials_customer_id",
        table_name="customer_platform_credentials",
    )
    op.drop_table("customer_platform_credentials")