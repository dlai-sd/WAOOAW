"""Initial Plant schema

Revision ID: 0001_initial_plant_schema
Revises: 
Create Date: 2026-01-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = "0001_initial_plant_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")

    op.create_table(
        "base_entity",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'active'")),
        sa.Column("version_hash", sa.String(length=64), nullable=False, server_default=sa.text("'initial'")),
        sa.Column("amendment_history", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("evolution_markers", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("l0_compliance_status", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("amendment_alignment", sa.String(length=20), nullable=False, server_default=sa.text("'aligned'")),
        sa.Column("drift_detector", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("append_only", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("hash_chain_sha256", postgresql.ARRAY(sa.String()), nullable=False, server_default=sa.text("'{}'::text[]")),
        sa.Column("tamper_proof", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=False, server_default=sa.text("'{}'::text[]")),
        sa.Column("custom_attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("governance_notes", sa.Text(), nullable=True),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("child_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False, server_default=sa.text("'{}'::uuid[]")),
        sa.Column("governance_agent_id", sa.String(length=100), nullable=False, server_default=sa.text("'genesis'")),
    )
    op.create_index("ix_base_entity_entity_type", "base_entity", ["entity_type"], unique=False)
    op.create_index("ix_base_entity_created_at", "base_entity", ["created_at"], unique=False)
    op.create_index("ix_base_entity_status", "base_entity", ["status"], unique=False)
    op.create_index("ix_base_entity_governance_agent_id", "base_entity", ["governance_agent_id"], unique=False)

    op.create_table(
        "industry_entity",
        sa.Column("id", postgresql.UUID(as_uuid=True), sa.ForeignKey("base_entity.id"), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("agents", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False, server_default=sa.text("'{}'::uuid[]")),
        sa.Column("embedding_384", Vector(384), nullable=True),
    )
    op.create_index("ix_industry_name", "industry_entity", ["name"], unique=True)
    op.create_index("ix_industry_embedding", "industry_entity", ["embedding_384"], unique=False, postgresql_using="ivfflat", postgresql_ops={"embedding_384": "vector_cosine_ops"})

    op.create_table(
        "job_role_entity",
        sa.Column("id", postgresql.UUID(as_uuid=True), sa.ForeignKey("base_entity.id"), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("required_skills", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False, server_default=sa.text("'{}'::uuid[]")),
        sa.Column("seniority_level", sa.String(length=20), nullable=False, server_default=sa.text("'mid'")),
        sa.Column("industry_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("industry_entity.id"), nullable=True),
    )
    op.create_index("ix_job_role_name", "job_role_entity", ["name"], unique=True)
    op.create_index("ix_job_role_seniority_level", "job_role_entity", ["seniority_level"], unique=False)
    op.create_index("ix_job_role_industry_id", "job_role_entity", ["industry_id"], unique=False)

    op.create_table(
        "skill_entity",
        sa.Column("id", postgresql.UUID(as_uuid=True), sa.ForeignKey("base_entity.id"), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("embedding_384", Vector(384), nullable=True),
        sa.Column("genesis_certification", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("ix_skill_name", "skill_entity", ["name"], unique=True)
    op.create_index("ix_skill_category", "skill_entity", ["category"], unique=False)
    op.create_index("ix_skill_embedding", "skill_entity", ["embedding_384"], unique=False, postgresql_using="ivfflat", postgresql_ops={"embedding_384": "vector_cosine_ops"})

    op.create_table(
        "team_entity",
        sa.Column("id", postgresql.UUID(as_uuid=True), sa.ForeignKey("base_entity.id"), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("agents", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False, server_default=sa.text("'{}'::uuid[]")),
        sa.Column("job_role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_role_entity.id"), nullable=False),
        sa.Column("industry_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("industry_entity.id"), nullable=True),
    )
    op.create_index("ix_team_name", "team_entity", ["name"], unique=True)
    op.create_index("ix_team_job_role_id", "team_entity", ["job_role_id"], unique=False)

    op.create_table(
        "agent_entity",
        sa.Column("id", postgresql.UUID(as_uuid=True), sa.ForeignKey("base_entity.id"), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skill_entity.id"), nullable=False),
        sa.Column("job_role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_role_entity.id"), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("team_entity.id"), nullable=True),
        sa.Column("industry_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("industry_entity.id"), nullable=False),
    )
    op.create_index("ix_agent_name", "agent_entity", ["name"], unique=True)
    op.create_index("ix_agent_industry_id", "agent_entity", ["industry_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_agent_industry_id", table_name="agent_entity")
    op.drop_index("ix_agent_name", table_name="agent_entity")
    op.drop_table("agent_entity")

    op.drop_index("ix_team_job_role_id", table_name="team_entity")
    op.drop_index("ix_team_name", table_name="team_entity")
    op.drop_table("team_entity")

    op.drop_index("ix_skill_embedding", table_name="skill_entity")
    op.drop_index("ix_skill_category", table_name="skill_entity")
    op.drop_index("ix_skill_name", table_name="skill_entity")
    op.drop_table("skill_entity")

    op.drop_index("ix_job_role_industry_id", table_name="job_role_entity")
    op.drop_index("ix_job_role_seniority_level", table_name="job_role_entity")
    op.drop_index("ix_job_role_name", table_name="job_role_entity")
    op.drop_table("job_role_entity")

    op.drop_index("ix_industry_embedding", table_name="industry_entity")
    op.drop_index("ix_industry_name", table_name="industry_entity")
    op.drop_table("industry_entity")

    op.drop_index("ix_base_entity_governance_agent_id", table_name="base_entity")
    op.drop_index("ix_base_entity_status", table_name="base_entity")
    op.drop_index("ix_base_entity_created_at", table_name="base_entity")
    op.drop_index("ix_base_entity_entity_type", table_name="base_entity")
    op.drop_table("base_entity")
