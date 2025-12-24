-- WAOOAW Vision Stack - PostgreSQL Schema
-- Version: 1.0
-- Purpose: Single Source of Truth for 200+ agent coordination
-- 
-- This schema provides:
-- - Zero context loss across all agent interactions
-- - Full audit trail for debugging and compliance
-- - Real-time agent state tracking
-- - Human escalation management via GitHub mobile

-- =====================================================
-- Agent Context Storage
-- =====================================================
-- Stores all agent context with versioning for time-travel queries
CREATE TABLE IF NOT EXISTS agent_context (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    context_type VARCHAR(50) NOT NULL,
    context_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    version INTEGER DEFAULT 1,
    
    CONSTRAINT unique_agent_context UNIQUE (agent_id, context_type, version)
);

CREATE INDEX IF NOT EXISTS idx_agent_context_agent_id ON agent_context(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_context_type ON agent_context(context_type);
CREATE INDEX IF NOT EXISTS idx_agent_context_created ON agent_context(created_at);
CREATE INDEX IF NOT EXISTS idx_agent_context_data ON agent_context USING GIN(context_data);

COMMENT ON TABLE agent_context IS 'Stores agent context with versioning for zero context loss';
COMMENT ON COLUMN agent_context.context_data IS 'JSONB field containing flexible agent state and decision history';

-- =====================================================
-- Agent Decision Log
-- =====================================================
-- Tracks every decision made by agents with approval status
CREATE TABLE IF NOT EXISTS agent_decisions (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    action_type VARCHAR(100) NOT NULL,
    action_data JSONB NOT NULL,
    approved BOOLEAN NOT NULL,
    reasoning TEXT,
    citations TEXT[],
    vision_layer VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT check_vision_layer CHECK (vision_layer IN ('core', 'policies', 'learned'))
);

CREATE INDEX IF NOT EXISTS idx_decisions_agent_id ON agent_decisions(agent_id);
CREATE INDEX IF NOT EXISTS idx_decisions_approved ON agent_decisions(approved);
CREATE INDEX IF NOT EXISTS idx_decisions_created ON agent_decisions(created_at);
CREATE INDEX IF NOT EXISTS idx_decisions_action_type ON agent_decisions(action_type);
CREATE INDEX IF NOT EXISTS idx_decisions_vision_layer ON agent_decisions(vision_layer);

COMMENT ON TABLE agent_decisions IS 'Audit trail of all agent decisions with vision layer attribution';
COMMENT ON COLUMN agent_decisions.vision_layer IS 'Which vision layer informed this decision: core (immutable), policies (dynamic), or learned (patterns)';

-- =====================================================
-- Vision Violations Log
-- =====================================================
-- Tracks when agents attempt actions that violate vision constraints
CREATE TABLE IF NOT EXISTS vision_violations (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    violation_type VARCHAR(100) NOT NULL,
    attempted_action JSONB NOT NULL,
    constraint_violated TEXT NOT NULL,
    citation TEXT NOT NULL,
    escalated BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT check_escalated CHECK (escalated IN (TRUE, FALSE))
);

CREATE INDEX IF NOT EXISTS idx_violations_agent_id ON vision_violations(agent_id);
CREATE INDEX IF NOT EXISTS idx_violations_escalated ON vision_violations(escalated);
CREATE INDEX IF NOT EXISTS idx_violations_type ON vision_violations(violation_type);
CREATE INDEX IF NOT EXISTS idx_violations_created ON vision_violations(created_at);

COMMENT ON TABLE vision_violations IS 'Tracks constraint violations to identify patterns and improve policies';
COMMENT ON COLUMN vision_violations.citation IS 'Reference to specific vision document section that was violated';

-- =====================================================
-- Human Escalations
-- =====================================================
-- Manages escalations to humans via GitHub issues (mobile-friendly)
CREATE TABLE IF NOT EXISTS human_escalations (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    escalation_reason TEXT NOT NULL,
    action_data JSONB NOT NULL,
    github_issue_number INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    human_response TEXT,
    responded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT check_status CHECK (status IN ('pending', 'approved', 'rejected', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_escalations_status ON human_escalations(status);
CREATE INDEX IF NOT EXISTS idx_escalations_created ON human_escalations(created_at);
CREATE INDEX IF NOT EXISTS idx_escalations_agent_id ON human_escalations(agent_id);
CREATE INDEX IF NOT EXISTS idx_escalations_github_issue ON human_escalations(github_issue_number);

COMMENT ON TABLE human_escalations IS 'Tracks human approvals via GitHub mobile for autonomous operation with oversight';
COMMENT ON COLUMN human_escalations.github_issue_number IS 'Links to GitHub issue for mobile-friendly approval workflow';

-- =====================================================
-- Agent Health Metrics
-- =====================================================
-- Monitors agent performance and health in real-time
CREATE TABLE IF NOT EXISTS agent_health (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_health_agent_id ON agent_health(agent_id);
CREATE INDEX IF NOT EXISTS idx_health_metric ON agent_health(metric_name);
CREATE INDEX IF NOT EXISTS idx_health_created ON agent_health(created_at);
CREATE INDEX IF NOT EXISTS idx_health_metric_value ON agent_health(metric_value);

COMMENT ON TABLE agent_health IS 'Real-time agent performance monitoring for proactive issue detection';
COMMENT ON COLUMN agent_health.metadata IS 'Additional context about the metric (e.g., threshold, alert status)';

-- =====================================================
-- Utility Views
-- =====================================================

-- View: Active agent contexts (latest version only)
CREATE OR REPLACE VIEW active_agent_contexts AS
SELECT DISTINCT ON (agent_id, context_type)
    id,
    agent_id,
    context_type,
    context_data,
    created_at,
    updated_at,
    version
FROM agent_context
ORDER BY agent_id, context_type, version DESC;

COMMENT ON VIEW active_agent_contexts IS 'Shows only the latest version of each agent context for quick access';

-- View: Pending escalations requiring human action
CREATE OR REPLACE VIEW pending_escalations AS
SELECT 
    id,
    agent_id,
    escalation_reason,
    action_data,
    github_issue_number,
    created_at,
    EXTRACT(EPOCH FROM (NOW() - created_at))/3600 AS hours_pending
FROM human_escalations
WHERE status = 'pending'
ORDER BY created_at ASC;

COMMENT ON VIEW pending_escalations IS 'Shows all escalations awaiting human approval with time waiting';

-- View: Agent health summary (last 24 hours)
CREATE OR REPLACE VIEW agent_health_summary AS
SELECT 
    agent_id,
    metric_name,
    AVG(metric_value) AS avg_value,
    MIN(metric_value) AS min_value,
    MAX(metric_value) AS max_value,
    COUNT(*) AS sample_count,
    MAX(created_at) AS last_updated
FROM agent_health
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY agent_id, metric_name
ORDER BY agent_id, metric_name;

COMMENT ON VIEW agent_health_summary IS 'Aggregated health metrics per agent for the last 24 hours';

-- =====================================================
-- Functions
-- =====================================================

-- Function: Update context with automatic versioning
CREATE OR REPLACE FUNCTION update_agent_context(
    p_agent_id VARCHAR(100),
    p_context_type VARCHAR(50),
    p_context_data JSONB
)
RETURNS INTEGER AS $$
DECLARE
    v_new_version INTEGER;
BEGIN
    -- Get next version number
    SELECT COALESCE(MAX(version), 0) + 1 
    INTO v_new_version
    FROM agent_context
    WHERE agent_id = p_agent_id AND context_type = p_context_type;
    
    -- Insert new version
    INSERT INTO agent_context (agent_id, context_type, context_data, version)
    VALUES (p_agent_id, p_context_type, p_context_data, v_new_version);
    
    RETURN v_new_version;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_agent_context IS 'Updates agent context with automatic version increment for time-travel queries';

-- Function: Log agent decision
CREATE OR REPLACE FUNCTION log_agent_decision(
    p_agent_id VARCHAR(100),
    p_action_type VARCHAR(100),
    p_action_data JSONB,
    p_approved BOOLEAN,
    p_reasoning TEXT DEFAULT NULL,
    p_citations TEXT[] DEFAULT NULL,
    p_vision_layer VARCHAR(20) DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    v_decision_id INTEGER;
BEGIN
    INSERT INTO agent_decisions (
        agent_id, 
        action_type, 
        action_data, 
        approved, 
        reasoning, 
        citations, 
        vision_layer
    )
    VALUES (
        p_agent_id,
        p_action_type,
        p_action_data,
        p_approved,
        p_reasoning,
        p_citations,
        p_vision_layer
    )
    RETURNING id INTO v_decision_id;
    
    RETURN v_decision_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION log_agent_decision IS 'Logs an agent decision with full context for audit trail';

-- =====================================================
-- Initial Data
-- =====================================================

-- Insert sample health metrics for monitoring setup verification
INSERT INTO agent_health (agent_id, metric_name, metric_value, metadata)
VALUES 
    ('system', 'schema_version', 1.0, '{"deployed_at": "2025-12-24"}'::jsonb),
    ('system', 'tables_created', 5.0, '{"tables": ["agent_context", "agent_decisions", "vision_violations", "human_escalations", "agent_health"]}'::jsonb)
ON CONFLICT DO NOTHING;

-- =====================================================
-- Grants (adjust for your security model)
-- =====================================================

-- Grant permissions to application user (adjust username as needed)
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO waooaw_app;
-- GRANT SELECT ON ALL VIEWS IN SCHEMA public TO waooaw_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO waooaw_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO waooaw_app;
