-- Migration: Add agent_entities table for DID-based agent identity
-- Date: 2025-12-29
-- Author: GitHub Copilot + dlai-sd
-- Purpose: Implement Agent Entity Architecture (Layer 0) with DID support

-- ============================================================================
-- 1. Create agent_entities table
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_entities (
    -- Identity
    did TEXT PRIMARY KEY,  -- e.g., "did:waooaw:wowvision-prime"
    display_name TEXT NOT NULL,
    description TEXT,
    avatar_url TEXT,
    
    -- Identity Composition (JSONB for flexibility)
    identity JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Structure: {
    --   "core": {"did": "...", "display_name": "...", "created_at": "..."},
    --   "capabilities": [{"name": "can:...", "scope": [...], "constraints": {...}}],
    --   "credentials": [{"type": "VerifiableCredential", "issuer": "...", ...}],
    --   "runtime": {"type": "kubernetes", "schedule": "...", ...},
    --   "attestation": {"identity": {...}, "capability": {...}, "runtime": {...}},
    --   "observability": {"metrics_endpoint": "...", "logs_retention_days": 90},
    --   "governance": {"owner": "...", "compliance_level": "..."}
    -- }
    
    -- Capabilities (denormalized for query performance)
    capabilities JSONB NOT NULL DEFAULT '[]'::jsonb,
    -- Structure: [
    --   {"name": "can:validate-code", "scope": ["python", "yaml"], "constraints": {...}},
    --   {"name": "can:create-github-issue", "scope": ["dlai-sd/WAOOAW"], ...}
    -- ]
    
    -- Runtime Configuration
    runtimes JSONB NOT NULL DEFAULT '[]'::jsonb,
    -- Structure: [
    --   {"type": "kubernetes", "schedule": "cron", "cron_expression": "0 */6 * * *", 
    --    "resource_limits": {"cpu": "500m", "memory": "512Mi"}, ...}
    -- ]
    
    -- Attestations
    attestations JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Structure: {
    --   "identity": {"issuer": "did:waooaw:platform-admin", "issuance_date": "...", ...},
    --   "capability": {"issuer": "did:waooaw:wowvision-prime", ...},
    --   "runtime": {"issuer": "did:k8s:admission-controller", ...},
    --   "key_rotation": {"last_rotation": "...", "next_rotation": "..."}
    -- }
    
    -- Key Material (encrypted references, NOT actual keys)
    key_material JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Structure: {
    --   "type": "Ed25519",
    --   "rotation_policy": "every-180-days",
    --   "kms_provider": "aws-kms",
    --   "kms_key_id": "arn:aws:kms:us-east-1:xxx:key/...",
    --   "public_key": "...",  -- Safe to store
    --   "fingerprint": "..."
    -- }
    
    -- Lifecycle Management
    lifecycle_state TEXT NOT NULL DEFAULT 'draft',
    -- States: draft, provisioned, active, suspended, revoked
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    -- Flexible metadata storage
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    activated_at TIMESTAMP WITH TIME ZONE,
    suspended_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    last_wake TIMESTAMP WITH TIME ZONE,
    
    -- Activity Tracking
    wake_count INTEGER DEFAULT 0,
    last_error TEXT,
    error_count INTEGER DEFAULT 0,
    
    -- Constraints
    CONSTRAINT valid_lifecycle_state CHECK (
        lifecycle_state IN ('draft', 'provisioned', 'active', 'suspended', 'revoked')
    ),
    CONSTRAINT did_format CHECK (did ~ '^did:waooaw:[a-z0-9-]+$')
);

-- ============================================================================
-- 2. Create indexes for performance
-- ============================================================================

-- Primary query patterns
CREATE INDEX idx_agent_entities_lifecycle ON agent_entities(lifecycle_state);
CREATE INDEX idx_agent_entities_display_name ON agent_entities(display_name);
CREATE INDEX idx_agent_entities_created_at ON agent_entities(created_at DESC);
CREATE INDEX idx_agent_entities_last_wake ON agent_entities(last_wake DESC);

-- JSONB indexes for capabilities queries
CREATE INDEX idx_agent_entities_capabilities ON agent_entities USING GIN (capabilities);
CREATE INDEX idx_agent_entities_identity ON agent_entities USING GIN (identity);

-- Composite index for active agents with recent activity
CREATE INDEX idx_agent_entities_active_wake ON agent_entities(lifecycle_state, last_wake DESC) 
    WHERE lifecycle_state = 'active';

-- ============================================================================
-- 3. Create updated_at trigger
-- ============================================================================

CREATE OR REPLACE FUNCTION update_agent_entities_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_agent_entities_updated_at
    BEFORE UPDATE ON agent_entities
    FOR EACH ROW
    EXECUTE FUNCTION update_agent_entities_updated_at();

-- ============================================================================
-- 4. Migrate existing agent_context references (if needed)
-- ============================================================================

-- Add agent_entity_did column to agent_context (optional, for future migration)
ALTER TABLE agent_context 
    ADD COLUMN IF NOT EXISTS agent_entity_did TEXT REFERENCES agent_entities(did);

-- Create index for the foreign key
CREATE INDEX IF NOT EXISTS idx_agent_context_agent_entity_did 
    ON agent_context(agent_entity_did);

-- ============================================================================
-- 5. Seed initial data (WowVision Prime)
-- ============================================================================

INSERT INTO agent_entities (
    did,
    display_name,
    description,
    avatar_url,
    identity,
    capabilities,
    runtimes,
    attestations,
    key_material,
    lifecycle_state,
    activated_at,
    last_wake,
    wake_count
) VALUES (
    'did:waooaw:wowvision-prime',
    'WowVision Prime',
    'Architecture Guardian & Quality Gatekeeper',
    'https://waooaw.com/agents/wowvision-prime.png',
    '{
        "core": {
            "did": "did:waooaw:wowvision-prime",
            "display_name": "WowVision Prime",
            "version": "v0.3.6",
            "created_at": "2024-12-27T00:00:00Z"
        },
        "observability": {
            "metrics_endpoint": "/metrics",
            "logs_retention_days": 90,
            "tracing_enabled": true
        },
        "governance": {
            "owner": "dlai-sd",
            "compliance_level": "production",
            "approval_required": false
        }
    }'::jsonb,
    '[
        {
            "name": "can:validate-code",
            "scope": ["python", "yaml", "dockerfile", "json", "markdown"],
            "constraints": {
                "file_size_max_mb": 10,
                "validation_timeout_sec": 300
            }
        },
        {
            "name": "can:create-github-issue",
            "scope": ["dlai-sd/WAOOAW"],
            "constraints": {
                "labels": ["architecture-violation", "quality-gate"],
                "auto_assign": ["dlai-sd"]
            }
        },
        {
            "name": "can:block-deployment",
            "scope": ["all-agents", "infrastructure", "customer-agents"],
            "constraints": {
                "severity_threshold": "high",
                "require_human_override": true
            }
        },
        {
            "name": "can:approve-deployment",
            "scope": ["all-agents"],
            "constraints": {
                "validation_passed": true,
                "test_coverage_min": 80
            }
        },
        {
            "name": "can:read-context",
            "scope": ["agent_context", "knowledge_base", "decision_cache"]
        },
        {
            "name": "can:write-context",
            "scope": ["agent_context", "knowledge_base", "decision_cache"]
        }
    ]'::jsonb,
    '[
        {
            "type": "kubernetes",
            "schedule": "cron",
            "cron_expression": "0 */6 * * *",
            "resource_limits": {
                "cpu": "500m",
                "memory": "512Mi"
            },
            "environment": {
                "VALIDATION_MODE": "strict",
                "CACHE_HIT_TARGET": "95",
                "LLM_PROVIDER": "anthropic",
                "MODEL": "claude-sonnet-4.5"
            }
        }
    ]'::jsonb,
    '{
        "identity": {
            "issuer": "did:waooaw:platform-admin",
            "issuance_date": "2024-12-27T00:00:00Z",
            "expiry": "2025-12-27T00:00:00Z"
        },
        "capability": {
            "issuer": "did:waooaw:platform-admin",
            "issuance_date": "2024-12-27T00:00:00Z",
            "renewal_policy": "annual"
        },
        "runtime": {
            "issuer": "did:k8s:admission-controller",
            "verification": "signed-container-digest",
            "image_digest": "sha256:wowvision-prime-v0.3.6"
        }
    }'::jsonb,
    '{
        "type": "RSA-4096",
        "rotation_policy": "every-90-days",
        "kms_provider": "aws-kms",
        "kms_key_id": "arn:aws:kms:us-east-1:xxx:key/wowvision-prime",
        "fingerprint": "sha256:abc123...",
        "last_rotation": "2024-12-27T00:00:00Z",
        "next_rotation": "2025-03-27T00:00:00Z"
    }'::jsonb,
    'active',
    '2024-12-27T00:00:00Z',
    '2025-12-29T12:00:00Z',
    15
)
ON CONFLICT (did) DO NOTHING;

-- ============================================================================
-- 6. Create view for active agents
-- ============================================================================

CREATE OR REPLACE VIEW active_agents AS
SELECT 
    did,
    display_name,
    description,
    lifecycle_state,
    jsonb_array_length(capabilities) as capability_count,
    last_wake,
    wake_count,
    created_at
FROM agent_entities
WHERE lifecycle_state = 'active'
ORDER BY last_wake DESC;

-- ============================================================================
-- 7. Create helper functions
-- ============================================================================

-- Function to get agent capabilities
CREATE OR REPLACE FUNCTION get_agent_capabilities(p_did TEXT)
RETURNS JSONB AS $$
BEGIN
    RETURN (
        SELECT capabilities 
        FROM agent_entities 
        WHERE did = p_did
    );
END;
$$ LANGUAGE plpgsql;

-- Function to verify agent capability
CREATE OR REPLACE FUNCTION has_capability(p_did TEXT, p_capability_name TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 
        FROM agent_entities,
        jsonb_array_elements(capabilities) as cap
        WHERE did = p_did
        AND cap->>'name' = p_capability_name
    );
END;
$$ LANGUAGE plpgsql;

-- Function to update agent wake
CREATE OR REPLACE FUNCTION record_agent_wake(p_did TEXT)
RETURNS VOID AS $$
BEGIN
    UPDATE agent_entities
    SET last_wake = NOW(),
        wake_count = wake_count + 1
    WHERE did = p_did;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 8. Grant permissions
-- ============================================================================

-- Grant to application role (adjust role name as needed)
-- GRANT SELECT, INSERT, UPDATE ON agent_entities TO waooaw_app;
-- GRANT USAGE ON SEQUENCE agent_entities_id_seq TO waooaw_app;

-- ============================================================================
-- Comments for documentation
-- ============================================================================

COMMENT ON TABLE agent_entities IS 'Agent Entity Architecture (Layer 0) - DID-based identity for all WAOOAW agents';
COMMENT ON COLUMN agent_entities.did IS 'Decentralized Identifier (DID) in format did:waooaw:{agent-name}';
COMMENT ON COLUMN agent_entities.capabilities IS 'Denormalized array of capabilities for query performance';
COMMENT ON COLUMN agent_entities.attestations IS 'Identity, capability, runtime, and key rotation attestations';
COMMENT ON COLUMN agent_entities.key_material IS 'Encrypted references to KMS keys (NOT raw keys)';
COMMENT ON COLUMN agent_entities.lifecycle_state IS 'Agent lifecycle: draft → provisioned → active → suspended → revoked';

-- ============================================================================
-- Rollback instructions (commented out)
-- ============================================================================

/*
-- To rollback this migration:

DROP VIEW IF EXISTS active_agents;
DROP FUNCTION IF EXISTS record_agent_wake(TEXT);
DROP FUNCTION IF EXISTS has_capability(TEXT, TEXT);
DROP FUNCTION IF EXISTS get_agent_capabilities(TEXT);
DROP TRIGGER IF EXISTS trigger_update_agent_entities_updated_at ON agent_entities;
DROP FUNCTION IF EXISTS update_agent_entities_updated_at();

ALTER TABLE agent_context DROP COLUMN IF EXISTS agent_entity_did;

DROP INDEX IF EXISTS idx_agent_context_agent_entity_did;
DROP INDEX IF EXISTS idx_agent_entities_active_wake;
DROP INDEX IF EXISTS idx_agent_entities_identity;
DROP INDEX IF EXISTS idx_agent_entities_capabilities;
DROP INDEX IF EXISTS idx_agent_entities_last_wake;
DROP INDEX IF EXISTS idx_agent_entities_created_at;
DROP INDEX IF EXISTS idx_agent_entities_display_name;
DROP INDEX IF EXISTS idx_agent_entities_lifecycle;

DROP TABLE IF EXISTS agent_entities;
*/

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
