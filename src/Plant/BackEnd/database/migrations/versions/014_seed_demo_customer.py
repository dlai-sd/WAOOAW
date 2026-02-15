"""Seed demo customer for demo/uat environments

Revision ID: 014_seed_demo_customer
Revises: b906e19d2162
Create Date: 2026-02-13

Purpose: Automatically create demo@waooaw.com customer in demo/uat environments
to bootstrap DB Updates authentication flow.

This migration is idempotent and environment-aware:
- Only runs in demo/uat (checks ENVIRONMENT env var)
- Skips if customer already exists
- Required for DB Updates page authentication in demo
"""

import os
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers
revision = "014_seed_demo_customer"
down_revision = "b906e19d2162"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Seed demo customer only in demo/uat environments."""
    
    # Check environment - only run in demo/uat
    environment = os.getenv("ENVIRONMENT", "").lower()
    if environment not in ("demo", "uat"):
        print(f"⏭️  Skipping demo customer seed (environment: {environment or 'not set'})")
        return
    
    print(f"🌱 Seeding demo customer for {environment} environment...")
    
    # Use raw SQL to ensure idempotency
    conn = op.get_bind()
    
    # Check if customer already exists
    result = conn.execute(
        sa.text("SELECT COUNT(*) FROM customer_entity WHERE email = 'demo@waooaw.com'")
    ).scalar()
    
    if result > 0:
        print("✅ Demo customer already exists, skipping seed")
        return
    
    # Create base_entity first
    conn.execute(
        sa.text("""
            INSERT INTO base_entity (
                id, entity_type, version_hash, status, governance_agent_id, tags
            )
            SELECT 
                gen_random_uuid(),
                'customer',
                'seed_v1',
                'active',
                'genesis',
                ARRAY['demo', 'testing']::text[]
            WHERE NOT EXISTS (
                SELECT 1 FROM customer_entity WHERE email = 'demo@waooaw.com'
            )
            RETURNING id
        """)
    )
    
    # Get the base_entity id we just created
    base_id_result = conn.execute(
        sa.text("""
            SELECT be.id 
            FROM base_entity be
            LEFT JOIN customer_entity ce ON be.id = ce.id
            WHERE be.entity_type = 'customer' 
            AND be.tags @> ARRAY['demo']::text[]
            AND ce.id IS NULL
            ORDER BY be.created_at DESC
            LIMIT 1
        """)
    ).fetchone()
    
    if base_id_result is None:
        print("⚠️  Could not find base_entity for demo customer, may already exist")
        return
    
    base_id = base_id_result[0]
    
    # Create customer_entity
    conn.execute(
        sa.text("""
            INSERT INTO customer_entity (
                id, email, phone, full_name, business_name, business_industry,
                business_address, preferred_contact_method, consent
            )
            VALUES (
                :id,
                'demo@waooaw.com',
                '+919999999999',
                'Demo User',
                'WAOOAW Demo Business',
                'Technology',
                'Mumbai, India',
                'email',
                true
            )
            ON CONFLICT (email) DO NOTHING
        """),
        {"id": base_id}
    )
    
    print("✅ Demo customer created successfully: demo@waooaw.com")


def downgrade() -> None:
    """Remove demo customer (optional, for development rollback)."""
    
    environment = os.getenv("ENVIRONMENT", "").lower()
    if environment not in ("demo", "uat"):
        return
    
    conn = op.get_bind()
    
    # Get customer ID
    result = conn.execute(
        sa.text("SELECT id FROM customer_entity WHERE email = 'demo@waooaw.com'")
    ).fetchone()
    
    if result is None:
        return
    
    customer_id = result[0]
    
    # Delete customer_entity (will cascade to base_entity due to FK)
    conn.execute(
        sa.text("DELETE FROM customer_entity WHERE id = :id"),
        {"id": customer_id}
    )
    
    # Delete base_entity
    conn.execute(
        sa.text("DELETE FROM base_entity WHERE id = :id"),
        {"id": customer_id}
    )
    
    print("🗑️  Demo customer removed")
