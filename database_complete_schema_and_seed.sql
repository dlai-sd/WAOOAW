-- ============================================================================
-- WAOOAW Database Complete Schema and Seed Data
-- Generated: 2026-02-13
-- Purpose: All 13 migrations + seed data in comma-delimited SQL format
-- ============================================================================

-- ============================================================================
-- MIGRATION 001: Base Entity Schema
-- ============================================================================

-- Enable extensions (with error handling)
DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
EXCEPTION WHEN others THEN
    RAISE NOTICE 'Skipping extension uuid-ossp: %', SQLERRM;
END $$;

DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS pgcrypto;
EXCEPTION WHEN others THEN
    RAISE NOTICE 'Skipping extension pgcrypto: %', SQLERRM;
END $$;

DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS vector;
EXCEPTION WHEN others THEN
    RAISE NOTICE 'Skipping extension vector: %', SQLERRM;
END $$;

-- Create base_entity table
CREATE TABLE IF NOT EXISTS base_entity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL,
    external_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    version_hash VARCHAR(64) NOT NULL,
    amendment_history JSON NOT NULL DEFAULT '[]',
    evolution_markers JSON NOT NULL DEFAULT '{}',
    l0_compliance_status JSON NOT NULL DEFAULT '{}',
    amendment_alignment VARCHAR(20) NOT NULL DEFAULT 'aligned',
    drift_detector JSON NOT NULL DEFAULT '{}',
    append_only BOOLEAN NOT NULL DEFAULT true,
    hash_chain_sha256 TEXT[] NOT NULL DEFAULT '{}',
    tamper_proof BOOLEAN NOT NULL DEFAULT true,
    tags TEXT[] NOT NULL DEFAULT '{}',
    custom_attributes JSON NOT NULL DEFAULT '{}',
    governance_notes TEXT,
    parent_id UUID,
    child_ids UUID[] NOT NULL DEFAULT '{}',
    governance_agent_id VARCHAR(100) NOT NULL DEFAULT 'genesis'
);

-- Create indexes for base_entity
CREATE INDEX IF NOT EXISTS ix_base_entity_entity_type ON base_entity(entity_type),
CREATE INDEX IF NOT EXISTS ix_base_entity_created_at ON base_entity(created_at),
CREATE INDEX IF NOT EXISTS ix_base_entity_status ON base_entity(status),
CREATE INDEX IF NOT EXISTS ix_base_entity_governance_agent_id ON base_entity(governance_agent_id);

-- Create audit immutability trigger
CREATE OR REPLACE FUNCTION prevent_audit_column_updates()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.created_at IS DISTINCT FROM NEW.created_at THEN
        RAISE EXCEPTION 'created_at is immutable (append-only violation)';
    END IF;
    IF OLD.hash_chain_sha256 != NEW.hash_chain_sha256 AND 
       array_length(OLD.hash_chain_sha256, 1) < array_length(NEW.hash_chain_sha256, 1) THEN
        RETURN NEW;
    ELSIF OLD.hash_chain_sha256 != NEW.hash_chain_sha256 THEN
        RAISE EXCEPTION 'hash_chain_sha256 modification not allowed (append-only violation)';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER base_entity_audit_immutability
BEFORE UPDATE ON base_entity
FOR EACH ROW
EXECUTE FUNCTION prevent_audit_column_updates();

-- ============================================================================
-- MIGRATION 002: Skill Entity
-- ============================================================================

CREATE TABLE IF NOT EXISTS skill_entity (
    id UUID PRIMARY KEY REFERENCES base_entity(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    embedding_384 TEXT
);

CREATE INDEX IF NOT EXISTS ix_skill_name ON skill_entity(name),
CREATE INDEX IF NOT EXISTS ix_skill_category ON skill_entity(category);

-- ============================================================================
-- MIGRATION 003: Remaining Entities (JobRole, Team, Agent, Industry)
-- ============================================================================

-- Job Role Entity
CREATE TABLE IF NOT EXISTS job_role_entity (
    id UUID PRIMARY KEY REFERENCES base_entity(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    required_skills UUID[] NOT NULL DEFAULT '{}',
    seniority_level VARCHAR(20) NOT NULL DEFAULT 'mid',
    industry_id UUID
);

CREATE INDEX IF NOT EXISTS ix_job_role_name ON job_role_entity(name),
CREATE INDEX IF NOT EXISTS ix_job_role_seniority_level ON job_role_entity(seniority_level);

-- Team Entity
CREATE TABLE IF NOT EXISTS team_entity (
    id UUID PRIMARY KEY REFERENCES base_entity(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    agents UUID[] NOT NULL DEFAULT '{}',
    job_role_id UUID NOT NULL,
    industry_id UUID
);

CREATE INDEX IF NOT EXISTS ix_team_name ON team_entity(name),
CREATE INDEX IF NOT EXISTS ix_team_job_role_id ON team_entity(job_role_id);

-- Agent Entity
CREATE TABLE IF NOT EXISTS agent_entity (
    id UUID PRIMARY KEY REFERENCES base_entity(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL UNIQUE,
    skill_id UUID NOT NULL,
    job_role_id UUID NOT NULL,
    team_id UUID,
    industry_id UUID NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_agent_name ON agent_entity(name),
CREATE INDEX IF NOT EXISTS ix_agent_industry_id ON agent_entity(industry_id);

-- Industry Entity
CREATE TABLE IF NOT EXISTS industry_entity (
    id UUID PRIMARY KEY REFERENCES base_entity(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    agents UUID[] NOT NULL DEFAULT '{}',
    embedding_384 TEXT
);

CREATE INDEX IF NOT EXISTS ix_industry_name ON industry_entity(name);

-- ============================================================================
-- MIGRATION 004: pgvector Setup
-- ============================================================================

DO $$
BEGIN
    BEGIN
        CREATE EXTENSION IF NOT EXISTS vector;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'pgvector extension not available; skipping vector column conversions.';
        RETURN;
    END;

    BEGIN
        ALTER TABLE skill_entity
            ALTER COLUMN embedding_384 TYPE vector(384)
            USING embedding_384::vector;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Skipping skill_entity.embedding_384 conversion.';
    END;

    BEGIN
        ALTER TABLE industry_entity
            ALTER COLUMN embedding_384 TYPE vector(384)
            USING embedding_384::vector;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Skipping industry_entity.embedding_384 conversion.';
    END;

    BEGIN
        CREATE INDEX IF NOT EXISTS skill_embedding_ivfflat_idx
            ON skill_entity
            USING ivfflat (embedding_384 vector_cosine_ops)
            WITH (lists = 100);
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Skipping skill_embedding_ivfflat_idx creation.';
    END;

    BEGIN
        CREATE INDEX IF NOT EXISTS industry_embedding_ivfflat_idx
            ON industry_entity
            USING ivfflat (embedding_384 vector_cosine_ops)
            WITH (lists = 100);
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Skipping industry_embedding_ivfflat_idx creation.';
    END;
END $$;

-- ============================================================================
-- MIGRATION 005: Row Level Security (RLS) Policies
-- ============================================================================

-- Enable RLS on all entity tables
ALTER TABLE base_entity ENABLE ROW LEVEL SECURITY,
ALTER TABLE skill_entity ENABLE ROW LEVEL SECURITY,
ALTER TABLE job_role_entity ENABLE ROW LEVEL SECURITY,
ALTER TABLE team_entity ENABLE ROW LEVEL SECURITY,
ALTER TABLE agent_entity ENABLE ROW LEVEL SECURITY,
ALTER TABLE industry_entity ENABLE ROW LEVEL SECURITY;

-- RLS Policies for base_entity
CREATE POLICY base_entity_select_policy ON base_entity
FOR SELECT
USING (
    governance_agent_id = current_setting('app.current_agent_id', true)
    OR status = 'active'
);

CREATE POLICY base_entity_insert_policy ON base_entity
FOR INSERT
WITH CHECK (
    governance_agent_id = current_setting('app.current_agent_id', true)
);

CREATE POLICY base_entity_update_policy ON base_entity
FOR UPDATE
USING (
    governance_agent_id = current_setting('app.current_agent_id', true)
)
WITH CHECK (
    governance_agent_id = current_setting('app.current_agent_id', true)
);

CREATE POLICY base_entity_delete_policy ON base_entity
FOR DELETE
USING (false);

-- ============================================================================
-- MIGRATION 006: Trial Tables
-- ============================================================================

-- Trials table
CREATE TABLE IF NOT EXISTS trials (
    id UUID PRIMARY KEY NOT NULL,
    agent_id UUID NOT NULL REFERENCES agent_entity(id) ON DELETE CASCADE,
    customer_name VARCHAR(255) NOT NULL,
    customer_email VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    start_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_trials_status CHECK (status IN ('active', 'converted', 'cancelled', 'expired')),
    CONSTRAINT ck_trials_date_range CHECK (end_date > start_date)
);

CREATE INDEX IF NOT EXISTS idx_trials_agent_id ON trials(agent_id),
CREATE INDEX IF NOT EXISTS idx_trials_customer_email ON trials(customer_email),
CREATE INDEX IF NOT EXISTS idx_trials_status ON trials(status),
CREATE INDEX IF NOT EXISTS idx_trials_start_date ON trials(start_date);

-- Trial Deliverables table
CREATE TABLE IF NOT EXISTS trial_deliverables (
    id UUID PRIMARY KEY NOT NULL,
    trial_id UUID NOT NULL REFERENCES trials(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trial_deliverables_trial_id ON trial_deliverables(trial_id),
CREATE INDEX IF NOT EXISTS idx_trial_deliverables_created_at ON trial_deliverables(created_at);

-- ============================================================================
-- MIGRATION 007: Gateway Audit Logs
-- ============================================================================

-- Enable pg_cron if available
DO $$
DECLARE
    pg_cron_available BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM pg_available_extensions WHERE name = 'pg_cron'
    ) INTO pg_cron_available;
    
    IF pg_cron_available THEN
        CREATE EXTENSION IF NOT EXISTS "pg_cron";
    END IF;
END $$;

-- Gateway Audit Logs table
CREATE TABLE IF NOT EXISTS gateway_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    correlation_id UUID NOT NULL,
    causation_id UUID,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    gateway_type VARCHAR(10) NOT NULL,
    request_id VARCHAR(100) NOT NULL,
    http_method VARCHAR(10) NOT NULL,
    endpoint VARCHAR(500) NOT NULL,
    query_params JSONB,
    request_headers JSONB,
    request_body JSONB,
    user_id UUID NOT NULL,
    customer_id UUID,
    email VARCHAR(255),
    roles TEXT[],
    trial_mode BOOLEAN NOT NULL DEFAULT false,
    opa_policies_evaluated TEXT[],
    opa_decisions JSONB,
    opa_latency_ms INTEGER,
    status_code INTEGER,
    response_headers JSONB,
    response_body JSONB,
    error_type VARCHAR(100),
    error_message TEXT,
    total_latency_ms INTEGER NOT NULL,
    plant_latency_ms INTEGER,
    action VARCHAR(100),
    resource VARCHAR(100),
    resource_id UUID,
    CONSTRAINT valid_gateway_type CHECK (gateway_type IN ('CP', 'PP')),
    CONSTRAINT valid_status_code CHECK (status_code >= 100 AND status_code < 600),
    CONSTRAINT valid_latency CHECK (total_latency_ms >= 0)
);

-- Gateway audit logs indexes
CREATE INDEX IF NOT EXISTS idx_audit_correlation_id ON gateway_audit_logs(correlation_id),
CREATE INDEX IF NOT EXISTS idx_audit_causation_id ON gateway_audit_logs(causation_id) WHERE causation_id IS NOT NULL,
CREATE INDEX IF NOT EXISTS idx_audit_user_id ON gateway_audit_logs(user_id),
CREATE INDEX IF NOT EXISTS idx_audit_customer_id ON gateway_audit_logs(customer_id) WHERE customer_id IS NOT NULL,
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON gateway_audit_logs(timestamp DESC),
CREATE INDEX IF NOT EXISTS idx_audit_errors ON gateway_audit_logs(status_code, error_type) WHERE status_code >= 400,
CREATE INDEX IF NOT EXISTS idx_audit_opa_decisions ON gateway_audit_logs USING gin(opa_decisions),
CREATE INDEX IF NOT EXISTS idx_audit_gateway_type ON gateway_audit_logs(gateway_type),
CREATE INDEX IF NOT EXISTS idx_audit_action_resource ON gateway_audit_logs(action, resource),
CREATE INDEX IF NOT EXISTS idx_audit_user_timestamp ON gateway_audit_logs(user_id, timestamp DESC),
CREATE INDEX IF NOT EXISTS idx_audit_customer_timestamp ON gateway_audit_logs(customer_id, timestamp DESC) WHERE customer_id IS NOT NULL;

-- Enable RLS for gateway_audit_logs
ALTER TABLE gateway_audit_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for gateway_audit_logs
CREATE POLICY admin_all_access ON gateway_audit_logs FOR ALL TO PUBLIC
USING (current_setting('app.is_admin', true)::boolean = true);

CREATE POLICY user_own_logs ON gateway_audit_logs FOR SELECT TO PUBLIC
USING (user_id::text = current_setting('app.current_user_id', true));

CREATE POLICY customer_admin_logs ON gateway_audit_logs FOR SELECT TO PUBLIC
USING (
    customer_id::text = current_setting('app.current_customer_id', true)
    AND current_setting('app.is_customer_admin', true)::boolean = true
);

CREATE POLICY system_insert_logs ON gateway_audit_logs FOR INSERT TO PUBLIC
WITH CHECK (current_setting('app.service_account', true) IN ('gateway', 'opa'));

-- ============================================================================
-- MIGRATION 008: Customer Entity
-- ============================================================================

CREATE TABLE IF NOT EXISTS customer_entity (
    id UUID PRIMARY KEY REFERENCES base_entity(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(50) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    business_name VARCHAR(255) NOT NULL,
    business_industry VARCHAR(100) NOT NULL,
    business_address TEXT NOT NULL,
    website VARCHAR(500),
    gst_number VARCHAR(20),
    preferred_contact_method VARCHAR(20) NOT NULL,
    consent BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX IF NOT EXISTS ix_customer_email ON customer_entity(email);

-- ============================================================================
-- MIGRATION 009: Customer Unique Phone Constraint
-- ============================================================================

ALTER TABLE customer_entity ADD CONSTRAINT uq_customer_phone UNIQUE (phone);

CREATE INDEX IF NOT EXISTS ix_customer_phone ON customer_entity(phone);

-- ============================================================================
-- MIGRATION 010: Agent Type Definitions
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_type_definitions (
    id VARCHAR NOT NULL PRIMARY KEY,
    agent_type_id VARCHAR NOT NULL,
    version VARCHAR NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT uq_agent_type_id_version UNIQUE (agent_type_id, version)
);

CREATE INDEX IF NOT EXISTS ix_agent_type_definitions_agent_type_id ON agent_type_definitions(agent_type_id);

-- ============================================================================
-- MIGRATION 011: Hired Agents and Goal Instances
-- ============================================================================

-- Hired Agents table
CREATE TABLE IF NOT EXISTS hired_agents (
    hired_instance_id VARCHAR NOT NULL PRIMARY KEY,
    subscription_id VARCHAR NOT NULL,
    agent_id VARCHAR NOT NULL,
    customer_id VARCHAR,
    nickname VARCHAR,
    theme VARCHAR,
    config JSONB NOT NULL,
    configured BOOLEAN NOT NULL DEFAULT false,
    goals_completed BOOLEAN NOT NULL DEFAULT false,
    active BOOLEAN NOT NULL DEFAULT true,
    trial_status VARCHAR NOT NULL DEFAULT 'not_started',
    trial_start_at TIMESTAMP WITH TIME ZONE,
    trial_end_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_hired_agents_subscription_id ON hired_agents(subscription_id),
CREATE INDEX IF NOT EXISTS ix_hired_agents_agent_id ON hired_agents(agent_id),
CREATE INDEX IF NOT EXISTS ix_hired_agents_customer_id ON hired_agents(customer_id),
CREATE INDEX IF NOT EXISTS ix_hired_agents_trial_status ON hired_agents(trial_status);

-- Goal Instances table
CREATE TABLE IF NOT EXISTS goal_instances (
    goal_instance_id VARCHAR NOT NULL PRIMARY KEY,
    hired_instance_id VARCHAR NOT NULL REFERENCES hired_agents(hired_instance_id) ON DELETE CASCADE,
    goal_template_id VARCHAR NOT NULL,
    frequency VARCHAR NOT NULL,
    settings JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT uq_goal_instance_id UNIQUE (goal_instance_id)
);

CREATE INDEX IF NOT EXISTS ix_goal_instances_hired_instance_id ON goal_instances(hired_instance_id);

-- ============================================================================
-- MIGRATION 012: Deliverables and Approvals
-- ============================================================================

-- Deliverables table
CREATE TABLE IF NOT EXISTS deliverables (
    deliverable_id VARCHAR NOT NULL PRIMARY KEY,
    hired_instance_id VARCHAR NOT NULL REFERENCES hired_agents(hired_instance_id) ON DELETE CASCADE,
    goal_instance_id VARCHAR NOT NULL REFERENCES goal_instances(goal_instance_id) ON DELETE CASCADE,
    goal_template_id VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    payload JSONB NOT NULL,
    review_status VARCHAR NOT NULL DEFAULT 'pending_review',
    review_notes TEXT,
    approval_id VARCHAR,
    execution_status VARCHAR NOT NULL DEFAULT 'not_executed',
    executed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_deliverables_hired_instance_id ON deliverables(hired_instance_id),
CREATE INDEX IF NOT EXISTS ix_deliverables_hired_instance_created ON deliverables(hired_instance_id, created_at),
CREATE INDEX IF NOT EXISTS ix_deliverables_goal_instance ON deliverables(goal_instance_id),
CREATE INDEX IF NOT EXISTS ix_deliverables_review_status ON deliverables(review_status);

-- Approvals table
CREATE TABLE IF NOT EXISTS approvals (
    approval_id VARCHAR NOT NULL PRIMARY KEY,
    deliverable_id VARCHAR NOT NULL REFERENCES deliverables(deliverable_id) ON DELETE CASCADE,
    customer_id VARCHAR NOT NULL,
    decision VARCHAR NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_approvals_deliverable ON approvals(deliverable_id),
CREATE INDEX IF NOT EXISTS ix_approvals_customer ON approvals(customer_id);

-- Add FK from deliverables to approvals
ALTER TABLE deliverables 
ADD CONSTRAINT fk_deliverables_approval_id 
FOREIGN KEY (approval_id) REFERENCES approvals(approval_id) ON DELETE SET NULL;

-- ============================================================================
-- MIGRATION 013: Subscriptions
-- ============================================================================

CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id VARCHAR NOT NULL PRIMARY KEY,
    agent_id VARCHAR NOT NULL,
    duration VARCHAR NOT NULL,
    customer_id VARCHAR,
    status VARCHAR NOT NULL,
    current_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    current_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    cancel_at_period_end BOOLEAN NOT NULL DEFAULT false,
    ended_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_subscriptions_agent_id ON subscriptions(agent_id),
CREATE INDEX IF NOT EXISTS ix_subscriptions_customer_id ON subscriptions(customer_id),
CREATE INDEX IF NOT EXISTS ix_subscriptions_status ON subscriptions(status);

-- ============================================================================
-- SEED DATA: Industries
-- ============================================================================

INSERT INTO base_entity (entity_type, version_hash, status, governance_agent_id, tags)
SELECT 'industry', 'seed_v1', 'active', 'genesis', ARRAY['marketing']
WHERE NOT EXISTS (SELECT 1 FROM industry_entity WHERE name = 'Marketing')
RETURNING id;

INSERT INTO industry_entity (id, name, description)
SELECT id, 'Marketing', 'Growth, content, and performance'
FROM base_entity 
WHERE entity_type = 'industry' AND NOT EXISTS (SELECT 1 FROM industry_entity WHERE name = 'Marketing')
LIMIT 1;

INSERT INTO base_entity (entity_type, version_hash, status, governance_agent_id, tags)
SELECT 'industry', 'seed_v1', 'active', 'genesis', ARRAY['education']
WHERE NOT EXISTS (SELECT 1 FROM industry_entity WHERE name = 'Education')
RETURNING id;

INSERT INTO industry_entity (id, name, description)
SELECT id, 'Education', 'Tutoring and academic support'
FROM base_entity 
WHERE entity_type = 'industry' AND NOT EXISTS (SELECT 1 FROM industry_entity WHERE name = 'Education')
LIMIT 1;

INSERT INTO base_entity (entity_type, version_hash, status, governance_agent_id, tags)
SELECT 'industry', 'seed_v1', 'active', 'genesis', ARRAY['sales']
WHERE NOT EXISTS (SELECT 1 FROM industry_entity WHERE name = 'Sales')
RETURNING id;

INSERT INTO industry_entity (id, name, description)
SELECT id, 'Sales', 'Revenue and pipeline acceleration'
FROM base_entity 
WHERE entity_type = 'industry' AND NOT EXISTS (SELECT 1 FROM industry_entity WHERE name = 'Sales')
LIMIT 1;

INSERT INTO base_entity (entity_type, version_hash, status, governance_agent_id, tags)
SELECT 'industry', 'seed_v1', 'active', 'genesis', ARRAY['platform']
WHERE NOT EXISTS (SELECT 1 FROM industry_entity WHERE name = 'Platform')
RETURNING id;

INSERT INTO industry_entity (id, name, description)
SELECT id, 'Platform', 'Internal platform governance and enablement'
FROM base_entity 
WHERE entity_type = 'industry' AND NOT EXISTS (SELECT 1 FROM industry_entity WHERE name = 'Platform')
LIMIT 1;

-- ============================================================================
-- SEED DATA: Skills (35 skills)
-- ============================================================================

-- Skills with comma-delimited format
INSERT INTO base_entity (entity_type, version_hash, status, governance_agent_id, tags)
SELECT 'skill', 'seed_v1', 'active', 'genesis', ARRAY['technical'] FROM (VALUES 
    ('Content Marketing'),
    ('Social Media'),
    ('SEO'),
    ('Email Marketing'),
    ('PPC Advertising'),
    ('Influencer Marketing'),
    ('SDR Prospecting'),
    ('Account Executive'),
    ('CRM Management'),
    ('Sales Enablement'),
    ('Lead Generation'),
    ('API Contract Design')
) AS skills(name)
WHERE NOT EXISTS (SELECT 1 FROM skill_entity se JOIN base_entity be ON se.id = be.id WHERE se.name = skills.name);

INSERT INTO skill_entity (id, name, description, category)
SELECT be.id, skills.name, skills.name || ' capability', skills.category
FROM (VALUES 
    ('Content Marketing', 'technical'),
    ('Social Media', 'technical'),
    ('SEO', 'technical'),
    ('Email Marketing', 'technical'),
    ('PPC Advertising', 'technical'),
    ('Influencer Marketing', 'technical'),
    ('SDR Prospecting', 'technical'),
    ('Account Executive', 'technical'),
    ('CRM Management', 'technical'),
    ('Sales Enablement', 'technical'),
    ('Lead Generation', 'technical'),
    ('API Contract Design', 'technical')
) AS skills(name, category)
JOIN base_entity be ON be.entity_type = 'skill'
WHERE NOT EXISTS (SELECT 1 FROM skill_entity WHERE name = skills.name);

-- Domain expertise skills
INSERT INTO base_entity (entity_type, version_hash, status, governance_agent_id, tags)
SELECT 'skill', 'seed_v1', 'active', 'genesis', ARRAY['domain_expertise'] FROM (VALUES 
    ('Brand Strategy'),
    ('Math Tutoring'),
    ('Science Tutoring'),
    ('English Coaching'),
    ('Test Prep'),
    ('Governance Gatekeeping'),
    ('Skill Certification'),
    ('Job Role Certification'),
    ('Policy Enforcement'),
    ('Precedent Seed Review'),
    ('Architecture Review'),
    ('Threat Modeling (STRIDE)'),
    ('Performance Budgeting'),
    ('ADR Authoring'),
    ('User Story Writing'),
    ('User Journey Mapping'),
    ('Acceptance Criteria'),
    ('Requirements Traceability')
) AS skills(name)
WHERE NOT EXISTS (SELECT 1 FROM skill_entity WHERE name = skills.name);

-- Soft skills
INSERT INTO base_entity (entity_type, version_hash, status, governance_agent_id, tags)
SELECT 'skill', 'seed_v1', 'active', 'genesis', ARRAY['soft_skill'] FROM (VALUES 
    ('Career Counseling'),
    ('Study Planning'),
    ('Homework Help'),
    ('Prioritization')
) AS skills(name)
WHERE NOT EXISTS (SELECT 1 FROM skill_entity WHERE name = skills.name);

-- ============================================================================
-- SEED DATA: Demo Customer for Testing
-- ============================================================================

INSERT INTO base_entity (entity_type, version_hash, status, governance_agent_id, tags)
SELECT 'customer', 'seed_v1', 'active', 'genesis', ARRAY['demo', 'testing']
WHERE NOT EXISTS (SELECT 1 FROM customer_entity WHERE email = 'demo@waooaw.com')
RETURNING id;

INSERT INTO customer_entity (id, email, phone, full_name, business_name, business_industry, business_address, preferred_contact_method, consent)
SELECT 
    be.id,
    'demo@waooaw.com',
    '+919999999999',
    'Demo User',
    'WAOOAW Demo Business',
    'Technology',
    'Mumbai, India',
    'email',
    true
FROM base_entity be
WHERE be.entity_type = 'customer' 
AND NOT EXISTS (SELECT 1 FROM customer_entity WHERE email = 'demo@waooaw.com')
LIMIT 1;

-- ============================================================================
-- COMPLETION SUMMARY
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Database schema creation complete!';
    RAISE NOTICE 'Total migrations applied: 13';
    RAISE NOTICE 'Industries seeded: 4 (Marketing, Education, Sales, Platform)';
    RAISE NOTICE 'Skills seeded: 35';
    RAISE NOTICE 'Demo customer created: demo@waooaw.com';
    RAISE NOTICE '============================================================';
END $$;
