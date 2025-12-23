-- PostgreSQL Schema for Context Preservation System
-- Created: 2025-12-23
-- Description: Comprehensive schema for managing domain-specific knowledge,
--              context preservation, and agent collaboration

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================================
-- CONTEXT REGISTRY
-- ============================================================================
-- Central registry for all context entries across the system
CREATE TABLE context_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    context_key VARCHAR(255) NOT NULL UNIQUE,
    context_type VARCHAR(50) NOT NULL,
    domain VARCHAR(100) NOT NULL,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    tags TEXT[],
    priority INTEGER DEFAULT 0,
    expiration_date TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT context_type_check CHECK (context_type IN (
        'knowledge', 'rule', 'constraint', 'pattern', 'template', 
        'workflow', 'decision', 'historical', 'analytical', 'other'
    )),
    CONSTRAINT priority_check CHECK (priority BETWEEN 0 AND 10)
);

-- Indexes for context_registry
CREATE INDEX idx_context_registry_type ON context_registry(context_type);
CREATE INDEX idx_context_registry_domain ON context_registry(domain);
CREATE INDEX idx_context_registry_active ON context_registry(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_context_registry_tags ON context_registry USING GIN(tags);
CREATE INDEX idx_context_registry_metadata ON context_registry USING GIN(metadata);
CREATE INDEX idx_context_registry_created_at ON context_registry(created_at DESC);
CREATE INDEX idx_context_registry_priority ON context_registry(priority DESC);
CREATE INDEX idx_context_registry_key_trgm ON context_registry USING GIN(context_key gin_trgm_ops);

-- ============================================================================
-- CONTEXT ACCESS LOG
-- ============================================================================
-- Tracks all access patterns and usage of context entries
CREATE TABLE context_access_log (
    id BIGSERIAL PRIMARY KEY,
    context_id UUID NOT NULL REFERENCES context_registry(id) ON DELETE CASCADE,
    access_type VARCHAR(50) NOT NULL,
    accessed_by VARCHAR(100) NOT NULL,
    access_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    access_metadata JSONB DEFAULT '{}',
    operation_result VARCHAR(50),
    response_time_ms INTEGER,
    error_message TEXT,
    
    CONSTRAINT access_type_check CHECK (access_type IN (
        'read', 'write', 'update', 'delete', 'query', 'search', 
        'reference', 'copy', 'export', 'import'
    ))
);

-- Indexes for context_access_log
CREATE INDEX idx_access_log_context_id ON context_access_log(context_id);
CREATE INDEX idx_access_log_accessed_by ON context_access_log(accessed_by);
CREATE INDEX idx_access_log_timestamp ON context_access_log(access_timestamp DESC);
CREATE INDEX idx_access_log_session ON context_access_log(session_id);
CREATE INDEX idx_access_log_type ON context_access_log(access_type);
CREATE INDEX idx_access_log_composite ON context_access_log(context_id, access_timestamp DESC);

-- ============================================================================
-- CONTEXT RELATIONSHIPS
-- ============================================================================
-- Manages relationships and dependencies between context entries
CREATE TABLE context_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_context_id UUID NOT NULL REFERENCES context_registry(id) ON DELETE CASCADE,
    target_context_id UUID NOT NULL REFERENCES context_registry(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    relationship_strength DECIMAL(3,2) DEFAULT 1.0,
    bidirectional BOOLEAN DEFAULT FALSE,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    
    CONSTRAINT relationship_type_check CHECK (relationship_type IN (
        'depends_on', 'extends', 'overrides', 'references', 'similar_to',
        'conflicts_with', 'complements', 'derived_from', 'parent_of', 
        'child_of', 'associated_with', 'prerequisite_for'
    )),
    CONSTRAINT strength_check CHECK (relationship_strength BETWEEN 0.0 AND 1.0),
    CONSTRAINT no_self_reference CHECK (source_context_id != target_context_id),
    UNIQUE(source_context_id, target_context_id, relationship_type)
);

-- Indexes for context_relationships
CREATE INDEX idx_relationships_source ON context_relationships(source_context_id);
CREATE INDEX idx_relationships_target ON context_relationships(target_context_id);
CREATE INDEX idx_relationships_type ON context_relationships(relationship_type);
CREATE INDEX idx_relationships_active ON context_relationships(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_relationships_strength ON context_relationships(relationship_strength DESC);
CREATE INDEX idx_relationships_bidirectional ON context_relationships(source_context_id, target_context_id) 
    WHERE bidirectional = TRUE;

-- ============================================================================
-- CONTEXT SNAPSHOTS
-- ============================================================================
-- Version control and historical snapshots of context entries
CREATE TABLE context_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    context_id UUID NOT NULL REFERENCES context_registry(id) ON DELETE CASCADE,
    snapshot_version INTEGER NOT NULL,
    snapshot_data JSONB NOT NULL,
    snapshot_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    change_description TEXT,
    change_type VARCHAR(50),
    delta JSONB,
    tags TEXT[],
    is_checkpoint BOOLEAN DEFAULT FALSE,
    parent_snapshot_id UUID REFERENCES context_snapshots(id),
    
    CONSTRAINT change_type_check CHECK (change_type IN (
        'create', 'update', 'delete', 'restore', 'merge', 'fork', 'rollback'
    )),
    UNIQUE(context_id, snapshot_version)
);

-- Indexes for context_snapshots
CREATE INDEX idx_snapshots_context_id ON context_snapshots(context_id);
CREATE INDEX idx_snapshots_version ON context_snapshots(context_id, snapshot_version DESC);
CREATE INDEX idx_snapshots_timestamp ON context_snapshots(snapshot_timestamp DESC);
CREATE INDEX idx_snapshots_checkpoint ON context_snapshots(is_checkpoint) WHERE is_checkpoint = TRUE;
CREATE INDEX idx_snapshots_data ON context_snapshots USING GIN(snapshot_data);
CREATE INDEX idx_snapshots_parent ON context_snapshots(parent_snapshot_id);

-- ============================================================================
-- COE COLLABORATION LOG
-- ============================================================================
-- Center of Excellence collaboration and decision tracking
CREATE TABLE coe_collaboration_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collaboration_type VARCHAR(50) NOT NULL,
    participants TEXT[] NOT NULL,
    context_ids UUID[],
    session_id VARCHAR(255) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    collaboration_data JSONB DEFAULT '{}',
    decisions_made JSONB DEFAULT '[]',
    outcomes TEXT,
    effectiveness_score DECIMAL(3,2),
    tags TEXT[],
    is_successful BOOLEAN,
    
    CONSTRAINT collaboration_type_check CHECK (collaboration_type IN (
        'review', 'approval', 'brainstorm', 'problem_solving', 
        'knowledge_sharing', 'decision_making', 'conflict_resolution',
        'training', 'audit', 'planning'
    )),
    CONSTRAINT effectiveness_check CHECK (effectiveness_score IS NULL OR 
        (effectiveness_score BETWEEN 0.0 AND 1.0))
);

-- Indexes for coe_collaboration_log
CREATE INDEX idx_coe_collab_type ON coe_collaboration_log(collaboration_type);
CREATE INDEX idx_coe_collab_session ON coe_collaboration_log(session_id);
CREATE INDEX idx_coe_collab_start_time ON coe_collaboration_log(start_time DESC);
CREATE INDEX idx_coe_collab_participants ON coe_collaboration_log USING GIN(participants);
CREATE INDEX idx_coe_collab_context_ids ON coe_collaboration_log USING GIN(context_ids);
CREATE INDEX idx_coe_collab_effectiveness ON coe_collaboration_log(effectiveness_score DESC);
CREATE INDEX idx_coe_collab_tags ON coe_collaboration_log USING GIN(tags);

-- ============================================================================
-- AGENT LEARNING
-- ============================================================================
-- Tracks agent learning patterns, improvements, and knowledge acquisition
CREATE TABLE agent_learning (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(100) NOT NULL,
    learning_type VARCHAR(50) NOT NULL,
    context_id UUID REFERENCES context_registry(id) ON DELETE SET NULL,
    learning_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(100),
    learning_data JSONB NOT NULL,
    confidence_score DECIMAL(3,2),
    validation_status VARCHAR(50),
    validated_by VARCHAR(100),
    validation_timestamp TIMESTAMP WITH TIME ZONE,
    feedback_score DECIMAL(3,2),
    feedback_comments TEXT,
    applied BOOLEAN DEFAULT FALSE,
    applied_timestamp TIMESTAMP WITH TIME ZONE,
    impact_metrics JSONB DEFAULT '{}',
    tags TEXT[],
    
    CONSTRAINT learning_type_check CHECK (learning_type IN (
        'pattern_recognition', 'behavior_adaptation', 'knowledge_acquisition',
        'skill_improvement', 'error_correction', 'optimization', 
        'preference_learning', 'reinforcement', 'transfer_learning'
    )),
    CONSTRAINT validation_status_check CHECK (validation_status IN (
        'pending', 'approved', 'rejected', 'needs_review', 'expired'
    )),
    CONSTRAINT confidence_check CHECK (confidence_score IS NULL OR 
        (confidence_score BETWEEN 0.0 AND 1.0)),
    CONSTRAINT feedback_check CHECK (feedback_score IS NULL OR 
        (feedback_score BETWEEN 0.0 AND 1.0))
);

-- Indexes for agent_learning
CREATE INDEX idx_agent_learning_agent_id ON agent_learning(agent_id);
CREATE INDEX idx_agent_learning_type ON agent_learning(learning_type);
CREATE INDEX idx_agent_learning_context ON agent_learning(context_id);
CREATE INDEX idx_agent_learning_timestamp ON agent_learning(learning_timestamp DESC);
CREATE INDEX idx_agent_learning_validation ON agent_learning(validation_status);
CREATE INDEX idx_agent_learning_confidence ON agent_learning(confidence_score DESC);
CREATE INDEX idx_agent_learning_applied ON agent_learning(applied) WHERE applied = TRUE;
CREATE INDEX idx_agent_learning_data ON agent_learning USING GIN(learning_data);
CREATE INDEX idx_agent_learning_tags ON agent_learning USING GIN(tags);

-- ============================================================================
-- CONTEXT HEALTH METRICS
-- ============================================================================
-- Monitors health, quality, and performance metrics of context entries
CREATE TABLE context_health_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    context_id UUID NOT NULL REFERENCES context_registry(id) ON DELETE CASCADE,
    metric_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    health_score DECIMAL(5,2) NOT NULL,
    quality_score DECIMAL(5,2),
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2),
    error_rate DECIMAL(5,2),
    average_response_time_ms INTEGER,
    last_accessed TIMESTAMP WITH TIME ZONE,
    access_frequency_24h INTEGER DEFAULT 0,
    access_frequency_7d INTEGER DEFAULT 0,
    access_frequency_30d INTEGER DEFAULT 0,
    staleness_days INTEGER,
    completeness_score DECIMAL(3,2),
    accuracy_score DECIMAL(3,2),
    relevance_score DECIMAL(3,2),
    performance_metrics JSONB DEFAULT '{}',
    issues_detected TEXT[],
    recommendations TEXT[],
    alert_level VARCHAR(20),
    
    CONSTRAINT health_score_check CHECK (health_score BETWEEN 0.0 AND 100.0),
    CONSTRAINT quality_score_check CHECK (quality_score IS NULL OR 
        (quality_score BETWEEN 0.0 AND 100.0)),
    CONSTRAINT success_rate_check CHECK (success_rate IS NULL OR 
        (success_rate BETWEEN 0.0 AND 100.0)),
    CONSTRAINT error_rate_check CHECK (error_rate IS NULL OR 
        (error_rate BETWEEN 0.0 AND 100.0)),
    CONSTRAINT score_checks CHECK (
        (completeness_score IS NULL OR completeness_score BETWEEN 0.0 AND 1.0) AND
        (accuracy_score IS NULL OR accuracy_score BETWEEN 0.0 AND 1.0) AND
        (relevance_score IS NULL OR relevance_score BETWEEN 0.0 AND 1.0)
    ),
    CONSTRAINT alert_level_check CHECK (alert_level IN (
        'normal', 'warning', 'critical', 'degraded', 'unknown'
    ))
);

-- Indexes for context_health_metrics
CREATE INDEX idx_health_metrics_context ON context_health_metrics(context_id);
CREATE INDEX idx_health_metrics_timestamp ON context_health_metrics(metric_timestamp DESC);
CREATE INDEX idx_health_metrics_health_score ON context_health_metrics(health_score DESC);
CREATE INDEX idx_health_metrics_quality ON context_health_metrics(quality_score DESC);
CREATE INDEX idx_health_metrics_alert ON context_health_metrics(alert_level) 
    WHERE alert_level IN ('warning', 'critical');
CREATE INDEX idx_health_metrics_latest ON context_health_metrics(context_id, metric_timestamp DESC);
CREATE INDEX idx_health_metrics_performance ON context_health_metrics USING GIN(performance_metrics);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_context_registry_updated_at
    BEFORE UPDATE ON context_registry
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to auto-increment version on context updates
CREATE OR REPLACE FUNCTION increment_context_version()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.* IS DISTINCT FROM NEW.* THEN
        NEW.version = OLD.version + 1;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER increment_version_on_update
    BEFORE UPDATE ON context_registry
    FOR EACH ROW
    EXECUTE FUNCTION increment_context_version();

-- Trigger to calculate collaboration duration
CREATE OR REPLACE FUNCTION calculate_collaboration_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.end_time IS NOT NULL AND NEW.start_time IS NOT NULL THEN
        NEW.duration_seconds = EXTRACT(EPOCH FROM (NEW.end_time - NEW.start_time))::INTEGER;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_duration_on_update
    BEFORE UPDATE ON coe_collaboration_log
    FOR EACH ROW
    WHEN (NEW.end_time IS NOT NULL)
    EXECUTE FUNCTION calculate_collaboration_duration();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View for active context summary
CREATE OR REPLACE VIEW active_context_summary AS
SELECT 
    cr.id,
    cr.context_key,
    cr.context_type,
    cr.domain,
    cr.version,
    cr.priority,
    cr.created_at,
    cr.updated_at,
    COUNT(DISTINCT cal.id) as access_count,
    MAX(cal.access_timestamp) as last_accessed,
    AVG(chm.health_score) as avg_health_score,
    COUNT(DISTINCT crel.id) as relationship_count
FROM context_registry cr
LEFT JOIN context_access_log cal ON cr.id = cal.context_id
LEFT JOIN context_health_metrics chm ON cr.id = chm.context_id
LEFT JOIN context_relationships crel ON cr.id = crel.source_context_id
WHERE cr.is_active = TRUE
GROUP BY cr.id, cr.context_key, cr.context_type, cr.domain, 
         cr.version, cr.priority, cr.created_at, cr.updated_at;

-- View for agent learning summary
CREATE OR REPLACE VIEW agent_learning_summary AS
SELECT 
    agent_id,
    learning_type,
    COUNT(*) as total_learnings,
    AVG(confidence_score) as avg_confidence,
    AVG(feedback_score) as avg_feedback,
    COUNT(*) FILTER (WHERE applied = TRUE) as applied_count,
    COUNT(*) FILTER (WHERE validation_status = 'approved') as approved_count
FROM agent_learning
GROUP BY agent_id, learning_type;

-- View for context health overview
CREATE OR REPLACE VIEW context_health_overview AS
SELECT DISTINCT ON (chm.context_id)
    cr.context_key,
    cr.context_type,
    cr.domain,
    chm.health_score,
    chm.quality_score,
    chm.success_rate,
    chm.alert_level,
    chm.metric_timestamp,
    chm.issues_detected
FROM context_health_metrics chm
JOIN context_registry cr ON chm.context_id = cr.id
WHERE cr.is_active = TRUE
ORDER BY chm.context_id, chm.metric_timestamp DESC;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE context_registry IS 'Central registry for all context entries with versioning and metadata';
COMMENT ON TABLE context_access_log IS 'Audit log tracking all context access patterns and usage';
COMMENT ON TABLE context_relationships IS 'Graph structure defining relationships between context entries';
COMMENT ON TABLE context_snapshots IS 'Version control system for context changes and historical states';
COMMENT ON TABLE coe_collaboration_log IS 'Collaboration tracking for Center of Excellence activities';
COMMENT ON TABLE agent_learning IS 'Agent learning patterns, improvements, and knowledge acquisition tracking';
COMMENT ON TABLE context_health_metrics IS 'Health monitoring and quality metrics for context entries';

-- ============================================================================
-- GRANTS (Customize based on your security requirements)
-- ============================================================================

-- Example grants for application role
-- CREATE ROLE waooaw_app;
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO waooaw_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO waooaw_app;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
