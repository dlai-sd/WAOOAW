"""create_otp_sessions_table

Revision ID: 016_otp_sessions
Revises: 015_add_agent_type_id_to_hired_agents
Create Date: 2026-02-25

Story: REG-OTP-1 - Move OTP storage from local files to PostgreSQL
Purpose: Replace FileCPOtpStore (local file-based) with a DB-backed otp_sessions
         table. Enables: attempt lockout (3 strikes), audit trail, soft deletes,
         proper TTL-based expiry, and multi-instance deployments.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "016_otp_sessions"
down_revision = "015_add_agent_type_id_to_hired_agents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create otp_sessions table."""
    op.create_table(
        "otp_sessions",
        sa.Column("otp_id", sa.String(), nullable=False),
        sa.Column("registration_id", sa.String(), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),       # 'email' | 'phone'
        sa.Column("destination", sa.String(), nullable=False),   # email or E.164 phone
        sa.Column("code_hash", sa.String(), nullable=False),     # bcrypt hash of OTP code
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        # Soft delete
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("otp_id", name="pk_otp_sessions"),
    )

    # Indexes for common query patterns
    op.create_index("ix_otp_sessions_destination", "otp_sessions", ["destination"], unique=False)
    op.create_index("ix_otp_sessions_registration_id", "otp_sessions", ["registration_id"], unique=False)
    op.create_index("ix_otp_sessions_expires_at", "otp_sessions", ["expires_at"], unique=False)
    op.create_index("ix_otp_sessions_verified_at", "otp_sessions", ["verified_at"], unique=False)


def downgrade() -> None:
    """Drop otp_sessions table."""
    op.drop_index("ix_otp_sessions_verified_at", table_name="otp_sessions")
    op.drop_index("ix_otp_sessions_expires_at", table_name="otp_sessions")
    op.drop_index("ix_otp_sessions_registration_id", table_name="otp_sessions")
    op.drop_index("ix_otp_sessions_destination", table_name="otp_sessions")
    op.drop_table("otp_sessions")
