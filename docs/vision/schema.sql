-- Vision Stack Schema - WowVision Prime Governance Tables
-- PostgreSQL 14+
--
-- This schema supports the 3-layer vision stack for platform governance:
-- Layer 1: Core Vision (immutable constraints)
-- Layer 2: Policies (agent-managed rules)
-- Layer 3: Context (runtime state)

-- =====================================
-- VISION CONTEXT & DECISIONS
-- =====================================

-- Agent context snapshots (versioned for each wake cycle)
-- Tracks context across wake cycles for all agents
CREATE TABLE IF NOT EXISTS agent_context (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    context_type VARCHAR(50) NOT NULL,  -- 'wake_cycle', 'initialization', etc.
    context_data JSONB NOT NULL,
    version INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_context_agent_id ON agent_context(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_context_version ON agent_context(agent_id, version DESC);

-- Agent decision log with vision validation
-- Tracks all decisions made by agents with vision stack validation results
CREATE TABLE IF NOT EXISTS agent_decisions (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    decision_type VARCHAR(50) NOT NULL,  -- 'file_create', 'file_edit', 'policy_change', etc.
    decision_data JSONB NOT NULL,
    vision_layer INTEGER NOT NULL,  -- 1=core, 2=policies, 3=context
    approved BOOLEAN NOT NULL,
    approval_reason TEXT,
    executed BOOLEAN DEFAULT FALSE,
    execution_result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    executed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_decision_agent ON agent_decisions(agent_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_decision_type ON agent_decisions(decision_type);
CREATE INDEX IF NOT EXISTS idx_decision_approved ON agent_decisions(approved);

-- =====================================
-- VISION VIOLATIONS & GOVERNANCE
-- =====================================

-- Vision stack violations
-- Tracks attempted actions that violated vision constraints
CREATE TABLE IF NOT EXISTS vision_violations (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    violation_type VARCHAR(50) NOT NULL,  -- 'core_constraint', 'policy_rule', 'context_invalid'
    violation_layer INTEGER NOT NULL,  -- 1=core, 2=policies, 3=context
    action_attempted JSONB NOT NULL,
    constraint_violated TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',  -- 'low', 'medium', 'high', 'critical'
    resolution_status VARCHAR(20) DEFAULT 'unresolved',  -- 'unresolved', 'acknowledged', 'fixed', 'waived'
    resolution_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_violation_agent ON vision_violations(agent_id);
CREATE INDEX IF NOT EXISTS idx_violation_severity ON vision_violations(severity);
CREATE INDEX IF NOT EXISTS idx_violation_status ON vision_violations(resolution_status);

-- =====================================
-- HUMAN ESCALATION & OVERSIGHT
-- =====================================

-- Human escalations for ambiguous/risky decisions
-- Tracks escalations requiring human review and approval
CREATE TABLE IF NOT EXISTS human_escalations (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    escalation_reason TEXT NOT NULL,
    action_data JSONB NOT NULL,
    vision_context JSONB,  -- Related vision stack context
    github_issue_number INTEGER,
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'approved', 'rejected', 'resolved'
    urgency VARCHAR(20) DEFAULT 'medium',  -- 'low', 'medium', 'high', 'critical'
    resolution_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_escalation_status ON human_escalations(status);
CREATE INDEX IF NOT EXISTS idx_escalation_agent ON human_escalations(agent_id);
CREATE INDEX IF NOT EXISTS idx_escalation_issue ON human_escalations(github_issue_number);

-- =====================================
-- AGENT HEALTH & MONITORING
-- =====================================

-- Agent health metrics and status
-- Tracks operational health and performance of agents
CREATE TABLE IF NOT EXISTS agent_health (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    health_status VARCHAR(20) NOT NULL,  -- 'healthy', 'degraded', 'unhealthy', 'offline'
    uptime_hours NUMERIC(10,2) DEFAULT 0,
    wake_cycles_completed INTEGER DEFAULT 0,
    decisions_made INTEGER DEFAULT 0,
    escalations_pending INTEGER DEFAULT 0,
    last_wake_up TIMESTAMPTZ,
    last_error TEXT,
    last_error_at TIMESTAMPTZ,
    metrics JSONB,  -- Additional health metrics
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_health_agent ON agent_health(agent_id);
CREATE INDEX IF NOT EXISTS idx_health_status ON agent_health(health_status);
CREATE INDEX IF NOT EXISTS idx_health_updated ON agent_health(updated_at DESC);

-- =====================================
-- INITIAL DATA
-- =====================================

-- Insert default health record for WowVision Prime
INSERT INTO agent_health (
    agent_id,
    health_status,
    uptime_hours,
    wake_cycles_completed,
    decisions_made,
    escalations_pending,
    metrics
)
VALUES (
    'WowVision-Prime',
    'healthy',
    0,
    0,
    0,
    0,
    '{"initialized_at": "2025-12-24T00:00:00Z", "version": "1.0.0"}'
)
ON CONFLICT DO NOTHING;

-- =====================================
-- INDEXES FOR PERFORMANCE
-- =====================================

-- Additional indexes for common queries
CREATE INDEX IF NOT EXISTS idx_context_recent ON agent_context(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_decision_recent ON agent_decisions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_violation_recent ON vision_violations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_escalation_pending ON human_escalations(status, created_at) WHERE status = 'pending';

-- =====================================
-- CLEANUP & MAINTENANCE
-- =====================================

-- Function to archive old context snapshots (keep only last 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_vision_context() RETURNS void AS $$
BEGIN
    DELETE FROM agent_context 
    WHERE created_at < NOW() - INTERVAL '30 days'
    AND context_type = 'wake_cycle';
END;
$$ LANGUAGE plpgsql;

-- Function to clean resolved violations (older than 90 days)
CREATE OR REPLACE FUNCTION cleanup_old_violations() RETURNS void AS $$
BEGIN
    DELETE FROM vision_violations
    WHERE created_at < NOW() - INTERVAL '90 days'
    AND resolution_status IN ('fixed', 'waived');
END;
$$ LANGUAGE plpgsql;

-- =====================================
-- COMMENTS
-- =====================================

COMMENT ON TABLE agent_context IS 'Versioned context snapshots for each agent wake cycle';
COMMENT ON TABLE agent_decisions IS 'Agent decision log with vision stack validation results';
COMMENT ON TABLE vision_violations IS 'Vision stack violations and constraint breaches';
COMMENT ON TABLE human_escalations IS 'Escalations requiring human review and approval';
COMMENT ON TABLE agent_health IS 'Agent health metrics and operational status';

-- =====================================
-- VERIFICATION
-- =====================================

-- Verify vision tables
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
AND table_name IN (
    'agent_context',
    'agent_decisions',
    'vision_violations',
    'human_escalations',
    'agent_health'
)
ORDER BY table_name;
