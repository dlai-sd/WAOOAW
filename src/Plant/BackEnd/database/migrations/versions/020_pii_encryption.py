"""add_pii_encryption_support

Revision ID: 020_pii_encryption
Revises: 019_feature_flags
Create Date: 2026-02-26

Iteration 7 — E3-S1 (Scale Prep): Field-level PII encryption.

This migration adds infrastructure for transparent field-level encryption:

  1. email_hash — HMAC-SHA256 of normalised email for index-based lookups.
     Allows `WHERE email_hash = ?` queries without storing plaintext email.

  2. Widens email / phone / full_name columns to 1024 chars to accommodate
     AES-256-GCM ciphertext + base64 encoding overhead.

Zero-downtime strategy:
  Phase A (this migration): add email_hash column + widen columns.
  Phase B (application code): EncryptedString TypeDecorator handles
    encrypt-on-write / decrypt-on-read transparently.
  Phase C (future): back-fill email_hash for existing rows via a one-off
    data migration script (scripts/backfill_email_hash.py).
  Phase D (future): drop the plaintext email unique index, add one on
    email_hash.
"""

from alembic import op
import sqlalchemy as sa


revision = "020_pii_encryption"
down_revision = "019_feature_flags"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add deterministic search column for encrypted email lookups.
    #    Nullable at first — existing rows don't have a hash yet (back-fill later).
    op.add_column(
        "customer_entity",
        sa.Column(
            "email_hash",
            sa.String(64),
            nullable=True,
            comment="HMAC-SHA256 of normalised email — used for lookups after encryption",
        ),
    )
    op.create_index("ix_customer_email_hash", "customer_entity", ["email_hash"])

    # 2. Widen PII columns to hold AES-256-GCM ciphertext (base64-encoded).
    #    Plain 255-char email → ~456 characters of base64. 1024 is safe upper bound.
    op.alter_column(
        "customer_entity",
        "email",
        existing_type=sa.String(255),
        type_=sa.String(1024),
        existing_nullable=False,
    )
    op.alter_column(
        "customer_entity",
        "phone",
        existing_type=sa.String(50),
        type_=sa.String(512),
        existing_nullable=False,
    )
    op.alter_column(
        "customer_entity",
        "full_name",
        existing_type=sa.String(255),
        type_=sa.String(1024),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "customer_entity",
        "full_name",
        existing_type=sa.String(1024),
        type_=sa.String(255),
        existing_nullable=False,
    )
    op.alter_column(
        "customer_entity",
        "phone",
        existing_type=sa.String(512),
        type_=sa.String(50),
        existing_nullable=False,
    )
    op.alter_column(
        "customer_entity",
        "email",
        existing_type=sa.String(1024),
        type_=sa.String(255),
        existing_nullable=False,
    )
    op.drop_index("ix_customer_email_hash", table_name="customer_entity")
    op.drop_column("customer_entity", "email_hash")
