-- Base Agent Core Architecture - Database Schema
-- PostgreSQL 14+
--
-- This schema supports all WAOOAW agents with:
-- - Context preservation across wake cycles
-- - Decision caching for cost optimization
-- - Memory storage for learning
-- - Escalation tracking
-- - Cross-agent collaboration

-- =====================================
-- AGENT CONTEXT & STATE
-- =====================================

-- Agent context snapshots (versioned for each wake cycle)
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

-- Agent operational state (key-value pairs)
CREATE TABLE IF NOT EXISTS wowvision_state (
    state_key VARCHAR(100) PRIMARY KEY,
    state_value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);


-- =====================================
-- MEMORY SYSTEM
-- =====================================

-- Long-term memory storage
CREATE TABLE IF NOT EXISTS wowvision_memory (
    id SERIAL PRIMARY KEY,
    memory_type VARCHAR(50) NOT NULL,  -- 'decision', 'learning', 'context'
    memory_key VARCHAR(200) NOT NULL,
    memory_data JSONB NOT NULL,
    importance_score NUMERIC(3,2) DEFAULT 0.5,  -- 0.0 to 1.0
    created_at TIMESTAMPTZ DEFAULT NOW()
    
);

CREATE INDEX IF NOT EXISTS idx_memory_type ON wowvision_memory(memory_type);
CREATE INDEX IF NOT EXISTS idx_memory_key ON wowvision_memory(memory_key);
CREATE INDEX IF NOT EXISTS idx_memory_importance ON wowvision_memory(importance_score DESC);

-- Conversation sessions for agent interactions
CREATE TABLE IF NOT EXISTS conversation_sessions (
    session_id VARCHAR(100) PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(100),
    session_type VARCHAR(50),  -- 'escalation', 'collaboration', 'user_chat'
    session_data JSONB,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ
    
);

CREATE INDEX IF NOT EXISTS idx_session_agent ON conversation_sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_session_user ON conversation_sessions(user_id);

-- Individual messages in conversations
CREATE TABLE IF NOT EXISTS conversation_messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL REFERENCES conversation_sessions(session_id),
    role VARCHAR(20) NOT NULL,  -- 'agent', 'user', 'system'
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
    
);

CREATE INDEX IF NOT EXISTS idx_message_session ON conversation_messages(session_id, created_at);

-- =====================================
-- LEARNING & KNOWLEDGE
-- =====================================

-- Knowledge base for learned patterns
CREATE TABLE IF NOT EXISTS knowledge_base (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,  -- '{agent_id}-learnings', 'platform-patterns', etc.
    title VARCHAR(200) NOT NULL,
    content JSONB NOT NULL,
    confidence NUMERIC(3,2) DEFAULT 0.8,  -- 0.0 to 1.0
    source VARCHAR(100),  -- 'outcome-feedback', 'human-input', etc.
    learned_at TIMESTAMPTZ DEFAULT NOW()
    
);

CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_base(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_confidence ON knowledge_base(confidence DESC);

-- =====================================
-- DECISION FRAMEWORK
-- =====================================

-- Decision cache for cost optimization
CREATE TABLE IF NOT EXISTS decision_cache (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    cache_key VARCHAR(200) NOT NULL,
    request_data JSONB NOT NULL,
    decision_data JSONB NOT NULL,
    method VARCHAR(50),  -- 'deterministic', 'vector_memory', 'llm'
    created_at TIMESTAMPTZ DEFAULT NOW()
    
);

CREATE INDEX IF NOT EXISTS idx_cache_key ON decision_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_cache_agent ON decision_cache(agent_id);
CREATE INDEX IF NOT EXISTS idx_cache_created ON decision_cache(created_at DESC);

-- =====================================
-- HUMAN ESCALATION
-- =====================================

-- Human escalations for ambiguous/risky decisions
CREATE TABLE IF NOT EXISTS human_escalations (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    escalation_reason TEXT NOT NULL,
    action_data JSONB NOT NULL,
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
-- AGENT COLLABORATION
-- =====================================

-- Handoff packages for cross-agent coordination
CREATE TABLE IF NOT EXISTS agent_handoffs (
    id SERIAL PRIMARY KEY,
    source_agent_id VARCHAR(100) NOT NULL,
    target_agent_id VARCHAR(100) NOT NULL,
    handoff_type VARCHAR(50) NOT NULL,  -- 'task', 'context', 'escalation'
    handoff_data JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'accepted', 'completed'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
    
);

CREATE INDEX IF NOT EXISTS idx_handoff_target ON agent_handoffs(target_agent_id, status);
CREATE INDEX IF NOT EXISTS idx_handoff_source ON agent_handoffs(source_agent_id);

-- =====================================
-- METRICS & MONITORING
-- =====================================

-- Agent activity metrics
CREATE TABLE IF NOT EXISTS agent_metrics (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC NOT NULL,
    metric_unit VARCHAR(50),
    timestamp TIMESTAMPTZ DEFAULT NOW()
    
);

CREATE INDEX IF NOT EXISTS idx_metrics_agent ON agent_metrics(agent_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_name ON agent_metrics(metric_name);

-- =====================================
-- INITIAL DATA
-- =====================================

-- Insert default state
INSERT INTO wowvision_state (state_key, state_value)
VALUES 
    ('current_phase', '{"phase": "phase1_foundation", "started_at": "2024-12-24T00:00:00Z"}'),
    ('platform_version', '{"version": "1.0.0", "updated_at": "2024-12-24T00:00:00Z"}')
ON CONFLICT (state_key) DO NOTHING;

-- Insert default knowledge base entries
INSERT INTO knowledge_base (category, title, content, confidence, source)
VALUES
    (
        'WowVision-Prime-core-constraints',
        'Phase 1: No Python Code Generation',
        '{"rule": "NEVER generate Python code in Phase 1 (except waooaw/ agent system)", "reason": "Foundation phase focuses on architecture", "exception": "waooaw/ directory is the agent system itself"}',
        1.0,
        'waooaw-core.yaml'
    ),
    (
        'WowVision-Prime-policies',
        'Markdown files always allowed',
        '{"rule": "Markdown files (.md, .markdown) are always allowed", "file_types": [".md", ".markdown"], "reason": "Documentation is always encouraged"}',
        1.0,
        'waooaw-policies.yaml'
    ),
    (
        'WowVision-Prime-policies',
        'Configuration files always allowed',
        '{"rule": "Configuration files are always allowed", "file_types": [".yaml", ".yml", ".json", ".toml", ".ini", ".env.example"], "exception": ".env files should never be committed"}',
        1.0,
        'waooaw-policies.yaml'
    )
ON CONFLICT DO NOTHING;

-- =====================================
-- INDEXES FOR PERFORMANCE
-- =====================================

-- Additional indexes for common queries
CREATE INDEX IF NOT EXISTS idx_context_recent ON agent_context(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_recent ON wowvision_memory(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_recent ON knowledge_base(learned_at DESC);
CREATE INDEX IF NOT EXISTS idx_escalation_pending ON human_escalations(status, created_at) WHERE status = 'pending';

-- =====================================
-- CLEANUP & MAINTENANCE
-- =====================================

-- Function to clean old decision cache entries (older than 7 days)
CREATE OR REPLACE FUNCTION cleanup_decision_cache() RETURNS void AS $$
BEGIN
    DELETE FROM decision_cache WHERE created_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- Function to archive old context snapshots (keep only last 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_context() RETURNS void AS $$
BEGIN
    DELETE FROM agent_context 
    WHERE created_at < NOW() - INTERVAL '30 days'
    AND context_type = 'wake_cycle';
END;
$$ LANGUAGE plpgsql;

-- =====================================
-- COMMENTS
-- =====================================

COMMENT ON TABLE agent_context IS 'Versioned context snapshots for each agent wake cycle';
COMMENT ON TABLE wowvision_state IS 'Platform operational state (key-value store)';
COMMENT ON TABLE wowvision_memory IS 'Long-term memory storage for agents';
COMMENT ON TABLE knowledge_base IS 'Learned patterns and rules for continuous improvement';
COMMENT ON TABLE decision_cache IS 'Cached decisions for cost optimization';
COMMENT ON TABLE human_escalations IS 'Escalations requiring human review';
COMMENT ON TABLE agent_handoffs IS 'Cross-agent collaboration packages';

-- =====================================
-- GRANTS (Adjust as needed)
-- =====================================

-- Grant permissions to agent user
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO waooaw_agent;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO waooaw_agent;

-- =====================================
-- DONE
-- =====================================

-- Verify tables
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
AND table_name IN (
    'agent_context',
    'wowvision_state',
    'wowvision_memory',
    'conversation_sessions',
    'conversation_messages',
    'knowledge_base',
    'decision_cache',
    'human_escalations',
    'agent_handoffs',
    'agent_metrics'
)
ORDER BY table_name;
