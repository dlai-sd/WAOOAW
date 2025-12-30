-- Migration 007: Add Identity System Tables
-- Epic 2.3 Story 5: Persistent Storage
-- Date: December 29, 2025
-- Purpose: Migrate credentials, attestations, and key rotation history from in-memory to PostgreSQL

-- =============================================================================
-- CREDENTIALS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS credentials (
    -- Primary identification
    id TEXT PRIMARY KEY,  -- urn:uuid:...
    
    -- Issuer and subject
    issuer_did TEXT NOT NULL,  -- did:waooaw:wowvision-prime
    subject_did TEXT NOT NULL,  -- did:waooaw:wowdomain
    
    -- Credential type and context
    credential_type JSONB NOT NULL DEFAULT '["VerifiableCredential", "AgentCapabilityCredential"]'::jsonb,
    context JSONB NOT NULL DEFAULT '["https://www.w3.org/2018/credentials/v1", "https://waooaw.com/credentials/v1"]'::jsonb,
    
    -- Subject data
    credential_subject JSONB NOT NULL,
    -- Structure: {
    --   "id": "did:waooaw:wowdomain",
    --   "capabilities": ["can:model-domain", "can:validate-ddd"],
    --   "constraints": [{"type": "time", "value": "business-hours"}]
    -- }
    
    -- Temporal validity
    issuance_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expiration_date TIMESTAMPTZ NOT NULL,
    
    -- Revocation
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    revoked_at TIMESTAMPTZ,
    revoked_reason TEXT,
    
    -- Digital signature
    proof JSONB,
    -- Structure: {
    --   "type": "Ed25519Signature2020",
    --   "created": "2025-12-29T10:00:00Z",
    --   "verificationMethod": "did:waooaw:wowvision-prime#key-1",
    --   "proofPurpose": "assertionMethod",
    --   "proofValue": "z58DAdFfa9..."
    -- }
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT credentials_valid_dates CHECK (expiration_date > issuance_date),
    CONSTRAINT credentials_revoked_reason_required CHECK (
        (revoked = FALSE AND revoked_at IS NULL AND revoked_reason IS NULL) OR
        (revoked = TRUE AND revoked_at IS NOT NULL AND revoked_reason IS NOT NULL)
    )
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_credentials_issuer_did ON credentials(issuer_did);
CREATE INDEX IF NOT EXISTS idx_credentials_subject_did ON credentials(subject_did);
CREATE INDEX IF NOT EXISTS idx_credentials_issuance_date ON credentials(issuance_date);
CREATE INDEX IF NOT EXISTS idx_credentials_expiration_date ON credentials(expiration_date);
CREATE INDEX IF NOT EXISTS idx_credentials_revoked ON credentials(revoked) WHERE revoked = TRUE;
CREATE INDEX IF NOT EXISTS idx_credentials_active ON credentials(expiration_date, revoked) 
    WHERE expiration_date > NOW() AND revoked = FALSE;

-- GIN index for capability searches
CREATE INDEX IF NOT EXISTS idx_credentials_capabilities ON credentials 
    USING GIN ((credential_subject->'capabilities'));

-- Comments
COMMENT ON TABLE credentials IS 'W3C Verifiable Credentials for agent capabilities';
COMMENT ON COLUMN credentials.id IS 'Unique credential identifier (urn:uuid:...)';
COMMENT ON COLUMN credentials.issuer_did IS 'DID of credential issuer (typically did:waooaw:wowvision-prime)';
COMMENT ON COLUMN credentials.subject_did IS 'DID of agent receiving credential';
COMMENT ON COLUMN credentials.credential_subject IS 'Subject data including capabilities and constraints';
COMMENT ON COLUMN credentials.revoked IS 'Whether credential has been revoked';
COMMENT ON COLUMN credentials.proof IS 'Ed25519 digital signature proving authenticity';

-- =============================================================================
-- ATTESTATIONS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS attestations (
    -- Primary identification
    id SERIAL PRIMARY KEY,
    
    -- Agent and issuer
    agent_did TEXT NOT NULL,  -- did:waooaw:wowdomain
    issuer_did TEXT NOT NULL,  -- did:waooaw:wowvision-prime (attester)
    
    -- Runtime information
    runtime_type TEXT NOT NULL,  -- kubernetes, serverless, edge
    runtime_manifest JSONB NOT NULL,
    -- Structure (kubernetes): {
    --   "image_digest": "sha256:abc123...",
    --   "pod_id": "wowdomain-12345",
    --   "namespace": "waooaw-agents",
    --   "resources": {"cpu": "500m", "memory": "512Mi"}
    -- }
    
    -- Agent state
    state JSONB NOT NULL,
    -- Structure: {
    --   "lifecycle": "active",
    --   "health": "healthy",
    --   "uptime_seconds": 3600,
    --   "metrics": {...}
    -- }
    
    -- Capabilities at attestation time
    capabilities JSONB NOT NULL,  -- ["can:model-domain", "can:validate-ddd"]
    
    -- Temporal validity
    timestamp TIMESTAMPTZ NOT NULL,  -- When attestation was issued
    max_age_seconds INTEGER NOT NULL DEFAULT 300,  -- 5 minutes default
    
    -- Digital signature
    signature TEXT NOT NULL,  -- Ed25519 signature (hex encoded)
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT attestations_valid_runtime_type CHECK (
        runtime_type IN ('kubernetes', 'serverless', 'edge')
    ),
    CONSTRAINT attestations_positive_max_age CHECK (max_age_seconds > 0)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_attestations_agent_did ON attestations(agent_did);
CREATE INDEX IF NOT EXISTS idx_attestations_issuer_did ON attestations(issuer_did);
CREATE INDEX IF NOT EXISTS idx_attestations_timestamp ON attestations(timestamp);
CREATE INDEX IF NOT EXISTS idx_attestations_runtime_type ON attestations(runtime_type);

-- Index for finding recent attestations (within max_age)
CREATE INDEX IF NOT EXISTS idx_attestations_valid ON attestations(agent_did, timestamp)
    WHERE timestamp > NOW() - INTERVAL '5 minutes';

-- Comments
COMMENT ON TABLE attestations IS 'Runtime attestations proving agent state at specific moments';
COMMENT ON COLUMN attestations.agent_did IS 'DID of agent being attested';
COMMENT ON COLUMN attestations.issuer_did IS 'DID of attester (guardian/platform)';
COMMENT ON COLUMN attestations.runtime_type IS 'Type of runtime environment (kubernetes, serverless, edge)';
COMMENT ON COLUMN attestations.runtime_manifest IS 'Runtime-specific metadata (pod ID, image digest, etc.)';
COMMENT ON COLUMN attestations.state IS 'Agent state snapshot (lifecycle, health, metrics)';
COMMENT ON COLUMN attestations.max_age_seconds IS 'Maximum age before attestation expires (default 5 minutes)';
COMMENT ON COLUMN attestations.signature IS 'Ed25519 signature over canonical attestation form';

-- =============================================================================
-- KEY ROTATION HISTORY TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS key_rotation_history (
    -- Primary identification
    id SERIAL PRIMARY KEY,
    
    -- Agent
    agent_did TEXT NOT NULL,
    
    -- Key rotation details
    old_key_id TEXT NOT NULL,  -- did:waooaw:agent#key-1
    new_key_id TEXT NOT NULL,  -- did:waooaw:agent#key-2
    
    -- Temporal information
    rotation_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    grace_period_end TIMESTAMPTZ NOT NULL,
    
    -- Rotation reason
    reason TEXT NOT NULL,  -- scheduled, compromised, manual
    
    -- Credential re-issuance
    credentials_reissued INTEGER NOT NULL DEFAULT 0,
    
    -- Metadata
    metadata JSONB,
    -- Structure: {
    --   "key_type": "Ed25519",
    --   "rotation_interval_days": 90,
    --   "triggered_by": "automated_schedule",
    --   "rotation_duration_ms": 1234
    -- }
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT key_rotation_valid_reason CHECK (
        reason IN ('scheduled', 'compromised', 'manual')
    ),
    CONSTRAINT key_rotation_grace_period_after_rotation CHECK (
        grace_period_end > rotation_date
    )
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_key_rotation_agent_did ON key_rotation_history(agent_did);
CREATE INDEX IF NOT EXISTS idx_key_rotation_date ON key_rotation_history(rotation_date);
CREATE INDEX IF NOT EXISTS idx_key_rotation_reason ON key_rotation_history(reason);

-- Index for finding most recent rotation per agent
CREATE INDEX IF NOT EXISTS idx_key_rotation_latest ON key_rotation_history(agent_did, rotation_date DESC);

-- Comments
COMMENT ON TABLE key_rotation_history IS 'History of cryptographic key rotations for agents';
COMMENT ON COLUMN key_rotation_history.agent_did IS 'DID of agent whose key was rotated';
COMMENT ON COLUMN key_rotation_history.old_key_id IS 'Verification method ID of previous key';
COMMENT ON COLUMN key_rotation_history.new_key_id IS 'Verification method ID of new key';
COMMENT ON COLUMN key_rotation_history.rotation_date IS 'When key rotation occurred';
COMMENT ON COLUMN key_rotation_history.grace_period_end IS 'Date when old key becomes invalid';
COMMENT ON COLUMN key_rotation_history.reason IS 'Reason for rotation (scheduled/compromised/manual)';
COMMENT ON COLUMN key_rotation_history.credentials_reissued IS 'Number of credentials re-issued with new key';

-- =============================================================================
-- ROTATION POLICIES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS rotation_policies (
    -- Primary key
    agent_did TEXT PRIMARY KEY,
    
    -- Rotation schedule
    rotation_interval_days INTEGER NOT NULL,  -- 90 or 180
    last_rotation TIMESTAMPTZ NOT NULL,
    next_rotation TIMESTAMPTZ NOT NULL,
    
    -- Grace period
    grace_period_days INTEGER NOT NULL DEFAULT 7,
    
    -- Automation
    auto_rotate BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Key type
    key_type TEXT NOT NULL DEFAULT 'Ed25519',
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT rotation_policies_valid_interval CHECK (
        rotation_interval_days IN (90, 180)
    ),
    CONSTRAINT rotation_policies_positive_grace_period CHECK (
        grace_period_days > 0
    ),
    CONSTRAINT rotation_policies_next_after_last CHECK (
        next_rotation > last_rotation
    )
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_rotation_policies_next_rotation ON rotation_policies(next_rotation)
    WHERE auto_rotate = TRUE;

-- Index for finding agents due for rotation
CREATE INDEX IF NOT EXISTS idx_rotation_policies_due ON rotation_policies(next_rotation, auto_rotate)
    WHERE next_rotation <= NOW() AND auto_rotate = TRUE;

-- Comments
COMMENT ON TABLE rotation_policies IS 'Key rotation policies for agents';
COMMENT ON COLUMN rotation_policies.agent_did IS 'DID of agent (primary key)';
COMMENT ON COLUMN rotation_policies.rotation_interval_days IS 'Days between rotations (90 for security-critical, 180 for standard)';
COMMENT ON COLUMN rotation_policies.next_rotation IS 'Next scheduled rotation date';
COMMENT ON COLUMN rotation_policies.grace_period_days IS 'Days old key remains valid after rotation';
COMMENT ON COLUMN rotation_policies.auto_rotate IS 'Whether to automatically rotate on schedule';

-- =============================================================================
-- UTILITY FUNCTIONS
-- =============================================================================

-- Function to check if credential is valid (not expired, not revoked)
CREATE OR REPLACE FUNCTION is_credential_valid(cred_id TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM credentials
        WHERE id = cred_id
        AND expiration_date > NOW()
        AND revoked = FALSE
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION is_credential_valid IS 'Check if credential is valid (not expired, not revoked)';

-- Function to get active credentials for an agent
CREATE OR REPLACE FUNCTION get_active_credentials(agent TEXT)
RETURNS SETOF credentials AS $$
BEGIN
    RETURN QUERY
    SELECT * FROM credentials
    WHERE subject_did = agent
    AND expiration_date > NOW()
    AND revoked = FALSE
    ORDER BY issuance_date DESC;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_active_credentials IS 'Get all active (non-expired, non-revoked) credentials for an agent';

-- Function to revoke a credential
CREATE OR REPLACE FUNCTION revoke_credential(
    cred_id TEXT,
    reason_text TEXT
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE credentials
    SET revoked = TRUE,
        revoked_at = NOW(),
        revoked_reason = reason_text,
        updated_at = NOW()
    WHERE id = cred_id
    AND revoked = FALSE;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION revoke_credential IS 'Revoke a credential with reason';

-- Function to get agents due for key rotation
CREATE OR REPLACE FUNCTION get_agents_due_for_rotation()
RETURNS TABLE (
    agent_did TEXT,
    rotation_interval_days INTEGER,
    last_rotation TIMESTAMPTZ,
    next_rotation TIMESTAMPTZ,
    days_overdue INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        rp.agent_did,
        rp.rotation_interval_days,
        rp.last_rotation,
        rp.next_rotation,
        EXTRACT(DAY FROM (NOW() - rp.next_rotation))::INTEGER AS days_overdue
    FROM rotation_policies rp
    WHERE rp.next_rotation <= NOW()
    AND rp.auto_rotate = TRUE
    ORDER BY days_overdue DESC;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_agents_due_for_rotation IS 'Get all agents due for key rotation';

-- Function to clean up old attestations (older than 24 hours)
CREATE OR REPLACE FUNCTION cleanup_old_attestations(
    retention_hours INTEGER DEFAULT 24
)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM attestations
    WHERE timestamp < NOW() - (retention_hours || ' hours')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_attestations IS 'Delete attestations older than specified hours (default 24)';

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Trigger to update updated_at on credentials
CREATE OR REPLACE FUNCTION update_credentials_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER credentials_updated_at_trigger
    BEFORE UPDATE ON credentials
    FOR EACH ROW
    EXECUTE FUNCTION update_credentials_updated_at();

-- Trigger to update updated_at on rotation_policies
CREATE OR REPLACE FUNCTION update_rotation_policies_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER rotation_policies_updated_at_trigger
    BEFORE UPDATE ON rotation_policies
    FOR EACH ROW
    EXECUTE FUNCTION update_rotation_policies_updated_at();

-- =============================================================================
-- SAMPLE DATA (for testing)
-- =============================================================================

-- Sample credential (commented out for production)
/*
INSERT INTO credentials (
    id,
    issuer_did,
    subject_did,
    credential_subject,
    issuance_date,
    expiration_date,
    proof
) VALUES (
    'urn:uuid:sample-credential-123',
    'did:waooaw:wowvision-prime',
    'did:waooaw:wowdomain',
    '{"id": "did:waooaw:wowdomain", "capabilities": ["can:model-domain", "can:validate-ddd"]}'::jsonb,
    NOW(),
    NOW() + INTERVAL '365 days',
    '{"type": "Ed25519Signature2020", "proofValue": "z..."}'::jsonb
);
*/

-- Sample rotation policy
/*
INSERT INTO rotation_policies (
    agent_did,
    rotation_interval_days,
    last_rotation,
    next_rotation,
    grace_period_days,
    auto_rotate,
    key_type
) VALUES (
    'did:waooaw:wowsecurity',
    90,
    NOW(),
    NOW() + INTERVAL '90 days',
    7,
    TRUE,
    'Ed25519'
);
*/

-- =============================================================================
-- ROLLBACK SCRIPT (run separately if needed)
-- =============================================================================

/*
-- To rollback this migration, run:

DROP TRIGGER IF EXISTS credentials_updated_at_trigger ON credentials;
DROP TRIGGER IF EXISTS rotation_policies_updated_at_trigger ON rotation_policies;

DROP FUNCTION IF EXISTS update_credentials_updated_at();
DROP FUNCTION IF EXISTS update_rotation_policies_updated_at();
DROP FUNCTION IF EXISTS is_credential_valid(TEXT);
DROP FUNCTION IF EXISTS get_active_credentials(TEXT);
DROP FUNCTION IF EXISTS revoke_credential(TEXT, TEXT);
DROP FUNCTION IF EXISTS get_agents_due_for_rotation();
DROP FUNCTION IF EXISTS cleanup_old_attestations(INTEGER);

DROP TABLE IF EXISTS rotation_policies;
DROP TABLE IF EXISTS key_rotation_history;
DROP TABLE IF EXISTS attestations;
DROP TABLE IF EXISTS credentials;
*/

-- =============================================================================
-- END MIGRATION 007
-- =============================================================================

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON credentials TO waooaw_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON attestations TO waooaw_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON key_rotation_history TO waooaw_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON rotation_policies TO waooaw_app;
-- GRANT USAGE, SELECT ON SEQUENCE attestations_id_seq TO waooaw_app;
-- GRANT USAGE, SELECT ON SEQUENCE key_rotation_history_id_seq TO waooaw_app;
