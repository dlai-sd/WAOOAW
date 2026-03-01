#!/usr/bin/env python3
"""
get_customer_ids.py — look up customer UUIDs from Plant's customer_entity table.

Customer records are stored in the Plant DB `customer_entity` table (UUID pk).
Email is encrypted (AES-256-GCM); lookups use email_hash (HMAC-SHA256 or plain
SHA-256 in dev when INDEX_KEY is not set).

Usage:
    # Must be run from src/Plant/BackEnd with Plant env vars loaded:
    python scripts/get_customer_ids.py yogeshkhandge@gmail.com rupalikhandge@gmail.com

    # Or via docker-compose:
    docker-compose exec plant-backend python scripts/get_customer_ids.py <email1> <email2>

Output (copy these to run the migration):
    export SEED_CUSTOMER_YOGESH=<uuid>
    export SEED_CUSTOMER_RUPALI=<uuid>
    alembic upgrade head
"""

from __future__ import annotations

import hashlib
import hmac
import os
import sys

# ---------------------------------------------------------------------------
# DB connection — reads PLANT_DB_URL or falls back to local default
# ---------------------------------------------------------------------------
DATABASE_URL = (
    os.getenv("PLANT_DB_URL")
    or os.getenv("DATABASE_URL")
    or "postgresql://postgres:waooaw_dev_password@localhost:5432/waooaw_plant_dev"
)
SYNC_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

try:
    import sqlalchemy as sa
except ImportError:
    print("ERROR: sqlalchemy not installed.  Run: pip install sqlalchemy psycopg2-binary")
    sys.exit(1)


def _email_hash(email: str) -> str:
    """Mirror of Plant's email_search_hash() in core/encryption.py.

    Uses HMAC-SHA256 keyed on INDEX_KEY env var if set (production/demo).
    Falls back to plain SHA-256 of lowercased email (dev, no secret key).
    """
    normalised = email.strip().lower()
    index_key_b64 = os.getenv("INDEX_KEY", "").strip()
    if index_key_b64:
        import base64
        try:
            key = base64.b64decode(index_key_b64)
        except Exception:
            key = index_key_b64.encode()
        return hmac.new(key, normalised.encode("utf-8"), hashlib.sha256).hexdigest()
    # Dev fallback — no key
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def main(emails: list[str]) -> None:
    engine = sa.create_engine(SYNC_URL)
    print(f"\nConnecting to: {SYNC_URL.split('@')[-1]}\n")

    with engine.connect() as conn:
        for email in emails:
            eh = _email_hash(email)
            result = conn.execute(
                sa.text(
                    """
                    SELECT id::text
                    FROM customer_entity
                    WHERE email_hash = :email_hash
                    LIMIT 1
                    """
                ),
                {"email_hash": eh},
            )
            row = result.fetchone()
            label = email.split("@")[0].replace(".", "").upper()
            if row:
                print(f"  export SEED_CUSTOMER_{label}={row[0]}  # {email}")
            else:
                print(f"  # NOT FOUND: {email} (email_hash={eh[:12]}...)")
                print(f"  # User may not have registered yet, or INDEX_KEY mismatch.")

    print()
    print("Once you have both IDs, run:")
    print("  alembic upgrade head")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/get_customer_ids.py email1@x.com email2@x.com")
        sys.exit(1)
    main(sys.argv[1:])
