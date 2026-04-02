"""add customer platform credentials and oauth connection sessions

Revision ID: 035_customer_platform_credentials_and_oauth_sessions
Revises: 034_pp_agent_authoring_drafts
Create Date: 2026-03-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision = "035_customer_platform_credentials_and_oauth_sessions"
down_revision = "034_pp_agent_authoring_drafts"
branch_labels = None
depends_on = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _has_foreign_key(inspector: sa.Inspector, table_name: str, constraint_name: str) -> bool:
    return any(fk["name"] == constraint_name for fk in inspector.get_foreign_keys(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _has_table(inspector, "customer_platform_credentials"):
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
        inspector = inspect(bind)

    if not _has_index(inspector, "customer_platform_credentials", "ix_customer_platform_credentials_customer_id"):
        op.create_index(
            "ix_customer_platform_credentials_customer_id",
            "customer_platform_credentials",
            ["customer_id"],
            unique=False,
        )

    if not _has_index(inspector, "customer_platform_credentials", "ix_customer_platform_credentials_platform_key"):
        op.create_index(
            "ix_customer_platform_credentials_platform_key",
            "customer_platform_credentials",
            ["platform_key"],
            unique=False,
        )

    if not _has_table(inspector, "oauth_connection_sessions"):
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
        inspector = inspect(bind)

    if not _has_index(inspector, "oauth_connection_sessions", "ix_oauth_connection_sessions_customer_id"):
        op.create_index(
            "ix_oauth_connection_sessions_customer_id",
            "oauth_connection_sessions",
            ["customer_id"],
            unique=False,
        )

    if not _has_index(inspector, "oauth_connection_sessions", "ix_oauth_connection_sessions_platform_key"):
        op.create_index(
            "ix_oauth_connection_sessions_platform_key",
            "oauth_connection_sessions",
            ["platform_key"],
            unique=False,
        )

    if not _has_column(inspector, "platform_connections", "customer_platform_credential_id"):
        op.add_column(
            "platform_connections",
            sa.Column("customer_platform_credential_id", sa.String(), nullable=True),
        )
        inspector = inspect(bind)

    if not _has_foreign_key(
        inspector,
        "platform_connections",
        "fk_platform_connections_customer_platform_credential_id",
    ):
        op.create_foreign_key(
            "fk_platform_connections_customer_platform_credential_id",
            "platform_connections",
            "customer_platform_credentials",
            ["customer_platform_credential_id"],
            ["id"],
            ondelete="SET NULL",
        )

    if not _has_index(
        inspector,
        "platform_connections",
        "ix_platform_connections_customer_platform_credential_id",
    ):
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