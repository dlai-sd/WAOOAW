-- Migration 009: Trial Management Tables
-- Epic 1.1: WowTrialManager (Trial Lifecycle Management)
-- Created: December 30, 2025

-- ============================================================================
-- TRIALS TABLE - Core trial lifecycle tracking
-- ============================================================================
CREATE TABLE IF NOT EXISTS trials (
    trial_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id),
    agent_id UUID REFERENCES agents(id),
    agent_type VARCHAR(100) NOT NULL,
    
    -- Trial lifecycle
    status VARCHAR(20) NOT NULL CHECK (status IN (
        'PROVISIONING', 'ACTIVE', 'EXPIRED', 'CONVERTED', 'CANCELLED', 'FAILED'
    )),
    start_date TIMESTAMP NOT NULL DEFAULT NOW(),
    end_date TIMESTAMP NOT NULL,
    days_remaining INT NOT NULL DEFAULT 7,
    
    -- Usage metrics
    deliverables JSONB DEFAULT '[]'::jsonb,
    tasks_completed INT DEFAULT 0,
    customer_interactions INT DEFAULT 0,
    satisfaction_score FLOAT CHECK (satisfaction_score >= 1.0 AND satisfaction_score <= 5.0),
    
    -- Conversion tracking
    conversion_intent VARCHAR(20) CHECK (conversion_intent IN (
        'INTERESTED', 'NOT_INTERESTED', 'UNDECIDED', NULL
    )),
    converted_at TIMESTAMP,
    subscription_id UUID,
    
    -- Metadata
    ip_address INET,
    user_agent TEXT,
    referral_source VARCHAR(255),
    error TEXT,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for fast lookups
CREATE INDEX idx_trials_customer_id ON trials(customer_id);
CREATE INDEX idx_trials_agent_id ON trials(agent_id);
CREATE INDEX idx_trials_status ON trials(status);
CREATE INDEX idx_trials_status_end_date ON trials(status, end_date);
CREATE INDEX idx_trials_customer_status ON trials(customer_id, status);
CREATE INDEX idx_trials_agent_type ON trials(agent_type);
CREATE INDEX idx_trials_created_at ON trials(created_at);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_trial_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trials_updated_at_trigger
    BEFORE UPDATE ON trials
    FOR EACH ROW
    EXECUTE FUNCTION update_trial_updated_at();


-- ============================================================================
-- TRIAL_USAGE_EVENTS TABLE - Detailed usage event tracking
-- ============================================================================
CREATE TABLE IF NOT EXISTS trial_usage_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trial_id UUID NOT NULL REFERENCES trials(trial_id) ON DELETE CASCADE,
    
    -- Event details
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN (
        'task_completed', 'interaction', 'deliverable_created',
        'feedback_submitted', 'agent_accessed', 'error_occurred'
    )),
    event_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Context
    duration_seconds INT,
    outcome VARCHAR(50),
    
    -- Timestamps
    event_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for event queries
CREATE INDEX idx_usage_events_trial_id ON trial_usage_events(trial_id);
CREATE INDEX idx_usage_events_type ON trial_usage_events(event_type);
CREATE INDEX idx_usage_events_timestamp ON trial_usage_events(event_timestamp);
CREATE INDEX idx_usage_events_trial_type ON trial_usage_events(trial_id, event_type);


-- ============================================================================
-- TRIAL_DELIVERABLES TABLE - Permanent deliverable storage
-- ============================================================================
CREATE TABLE IF NOT EXISTS trial_deliverables (
    deliverable_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trial_id UUID NOT NULL REFERENCES trials(trial_id) ON DELETE CASCADE,
    task_id UUID,
    
    -- Deliverable details
    deliverable_type VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    preview TEXT,
    size_bytes INT NOT NULL,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    format VARCHAR(50),
    
    -- Access control
    permanent_url TEXT,
    accessible_until TIMESTAMP,  -- NULL = forever
    download_count INT DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_accessed_at TIMESTAMP
);

-- Indexes for deliverable access
CREATE INDEX idx_deliverables_trial_id ON trial_deliverables(trial_id);
CREATE INDEX idx_deliverables_task_id ON trial_deliverables(task_id);
CREATE INDEX idx_deliverables_type ON trial_deliverables(deliverable_type);
CREATE INDEX idx_deliverables_created_at ON trial_deliverables(created_at);


-- ============================================================================
-- TRIAL_REMINDERS TABLE - Scheduled reminder tracking
-- ============================================================================
CREATE TABLE IF NOT EXISTS trial_reminders (
    reminder_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trial_id UUID NOT NULL REFERENCES trials(trial_id) ON DELETE CASCADE,
    
    -- Reminder details
    reminder_type VARCHAR(50) NOT NULL CHECK (reminder_type IN (
        'day_5', 'day_6', '6_hours_left', 'expiration', 'grace_period'
    )),
    scheduled_for TIMESTAMP NOT NULL,
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN (
        'PENDING', 'SENT', 'FAILED', 'CANCELLED'
    )),
    sent_at TIMESTAMP,
    error TEXT,
    
    -- Notification details
    notification_id UUID,
    recipient_email VARCHAR(255) NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for reminder processing
CREATE INDEX idx_reminders_trial_id ON trial_reminders(trial_id);
CREATE INDEX idx_reminders_status ON trial_reminders(status);
CREATE INDEX idx_reminders_scheduled_for ON trial_reminders(scheduled_for);
CREATE INDEX idx_reminders_status_scheduled ON trial_reminders(status, scheduled_for);


-- ============================================================================
-- TRIAL_ANALYTICS TABLE - Aggregated analytics for dashboards
-- ============================================================================
CREATE TABLE IF NOT EXISTS trial_analytics (
    analytics_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    agent_type VARCHAR(100),
    
    -- Funnel metrics
    trials_started INT DEFAULT 0,
    trials_active INT DEFAULT 0,
    trials_completed INT DEFAULT 0,
    trials_converted INT DEFAULT 0,
    trials_cancelled INT DEFAULT 0,
    trials_expired INT DEFAULT 0,
    
    -- Engagement metrics
    avg_tasks_completed FLOAT,
    avg_deliverables_created FLOAT,
    avg_interactions FLOAT,
    avg_satisfaction_score FLOAT,
    
    -- Conversion metrics
    conversion_rate FLOAT,
    avg_time_to_conversion_hours FLOAT,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    UNIQUE(date, agent_type)
);

-- Indexes for analytics queries
CREATE INDEX idx_analytics_date ON trial_analytics(date);
CREATE INDEX idx_analytics_agent_type ON trial_analytics(agent_type);
CREATE INDEX idx_analytics_date_type ON trial_analytics(date, agent_type);


-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Calculate days remaining for a trial
CREATE OR REPLACE FUNCTION calculate_days_remaining(trial_end_date TIMESTAMP)
RETURNS INT AS $$
BEGIN
    RETURN GREATEST(0, EXTRACT(DAY FROM (trial_end_date - NOW())));
END;
$$ LANGUAGE plpgsql IMMUTABLE;


-- Check if trial is expired
CREATE OR REPLACE FUNCTION is_trial_expired(trial_end_date TIMESTAMP)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN trial_end_date < NOW();
END;
$$ LANGUAGE plpgsql IMMUTABLE;


-- Get trial usage summary
CREATE OR REPLACE FUNCTION get_trial_usage_summary(input_trial_id UUID)
RETURNS TABLE (
    trial_id UUID,
    status VARCHAR,
    days_remaining INT,
    tasks_completed INT,
    deliverables_count BIGINT,
    interactions INT,
    satisfaction FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.trial_id,
        t.status,
        calculate_days_remaining(t.end_date) AS days_remaining,
        t.tasks_completed,
        COUNT(DISTINCT d.deliverable_id) AS deliverables_count,
        t.customer_interactions AS interactions,
        t.satisfaction_score AS satisfaction
    FROM trials t
    LEFT JOIN trial_deliverables d ON t.trial_id = d.trial_id
    WHERE t.trial_id = input_trial_id
    GROUP BY t.trial_id, t.status, t.end_date, t.tasks_completed, 
             t.customer_interactions, t.satisfaction_score;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- VIEWS
-- ============================================================================

-- Active trials view (for monitoring)
CREATE OR REPLACE VIEW active_trials AS
SELECT 
    t.trial_id,
    t.customer_id,
    t.agent_type,
    t.status,
    calculate_days_remaining(t.end_date) AS days_remaining,
    t.tasks_completed,
    jsonb_array_length(t.deliverables) AS deliverables_count,
    t.customer_interactions,
    t.satisfaction_score,
    t.start_date,
    t.end_date
FROM trials t
WHERE t.status = 'ACTIVE'
ORDER BY t.end_date ASC;


-- Trials needing reminders (for cron job)
CREATE OR REPLACE VIEW trials_needing_reminders AS
SELECT 
    t.trial_id,
    t.customer_id,
    t.agent_type,
    calculate_days_remaining(t.end_date) AS days_remaining,
    EXTRACT(EPOCH FROM (t.end_date - NOW())) / 3600 AS hours_remaining,
    t.end_date
FROM trials t
WHERE t.status = 'ACTIVE'
AND (
    -- Day 5 reminder (2 days left)
    calculate_days_remaining(t.end_date) = 2
    OR
    -- Day 6 reminder (1 day left)
    calculate_days_remaining(t.end_date) = 1
    OR
    -- 6 hours left reminder
    (EXTRACT(EPOCH FROM (t.end_date - NOW())) / 3600) <= 6
    AND (EXTRACT(EPOCH FROM (t.end_date - NOW())) / 3600) > 0
);


-- Trial conversion funnel (for analytics)
CREATE OR REPLACE VIEW trial_conversion_funnel AS
SELECT 
    DATE(created_at) AS date,
    agent_type,
    COUNT(*) FILTER (WHERE status IN ('PROVISIONING', 'ACTIVE', 'EXPIRED', 'CONVERTED', 'CANCELLED')) AS trials_started,
    COUNT(*) FILTER (WHERE status = 'ACTIVE') AS trials_active,
    COUNT(*) FILTER (WHERE status IN ('EXPIRED', 'CONVERTED', 'CANCELLED')) AS trials_completed,
    COUNT(*) FILTER (WHERE status = 'CONVERTED') AS trials_converted,
    COUNT(*) FILTER (WHERE status = 'CANCELLED') AS trials_cancelled,
    COUNT(*) FILTER (WHERE status = 'EXPIRED') AS trials_expired,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'CONVERTED') / 
        NULLIF(COUNT(*) FILTER (WHERE status IN ('EXPIRED', 'CONVERTED', 'CANCELLED')), 0),
        2
    ) AS conversion_rate_pct
FROM trials
GROUP BY DATE(created_at), agent_type
ORDER BY date DESC, agent_type;


-- ============================================================================
-- DATA SEEDING (for testing)
-- ============================================================================

-- Insert test customer if not exists
INSERT INTO customers (id, email, name, created_at)
VALUES (
    '00000000-0000-0000-0000-000000000001'::uuid,
    'test@example.com',
    'Test Customer',
    NOW()
)
ON CONFLICT (id) DO NOTHING;


-- ============================================================================
-- GRANTS (adjust based on your roles)
-- ============================================================================

-- Grant permissions to application role
-- GRANT SELECT, INSERT, UPDATE, DELETE ON trials TO app_role;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON trial_usage_events TO app_role;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON trial_deliverables TO app_role;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON trial_reminders TO app_role;
-- GRANT SELECT ON trial_analytics TO app_role;
-- GRANT SELECT ON active_trials TO app_role;
-- GRANT SELECT ON trials_needing_reminders TO app_role;
-- GRANT SELECT ON trial_conversion_funnel TO app_role;


-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE trials IS 'Core trial lifecycle tracking for Try Before Hire marketplace';
COMMENT ON TABLE trial_usage_events IS 'Detailed usage events during trial period';
COMMENT ON TABLE trial_deliverables IS 'Permanent storage of trial deliverables (keep forever)';
COMMENT ON TABLE trial_reminders IS 'Scheduled reminders for trial expiration';
COMMENT ON TABLE trial_analytics IS 'Aggregated analytics for dashboards and reporting';

COMMENT ON COLUMN trials.days_remaining IS 'Calculated daily by cron job';
COMMENT ON COLUMN trials.deliverables IS 'DEPRECATED: Use trial_deliverables table instead';
COMMENT ON COLUMN trial_deliverables.accessible_until IS 'NULL = accessible forever';

-- End of migration 009
