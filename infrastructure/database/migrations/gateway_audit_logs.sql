-- Gateway Audit Logs Schema
-- Version: 1.0
-- Purpose: Track all gateway requests, OPA decisions, and user actions
-- Retention: 90 days (automated cleanup via pg_cron)
-- Created: 2026-01-17

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_cron";

-- Create audit logs table
CREATE TABLE IF NOT EXISTS gateway_audit_logs (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Tracing IDs (for distributed tracing)
    correlation_id UUID NOT NULL,  -- Trace ID (spans multiple requests)
    causation_id UUID,              -- Parent request ID (null for root requests)
    
    -- Timestamp
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Request metadata
    gateway_type VARCHAR(10) NOT NULL CHECK (gateway_type IN ('CP', 'PP')),
    request_id VARCHAR(100) NOT NULL,
    http_method VARCHAR(10) NOT NULL,
    endpoint VARCHAR(500) NOT NULL,
    query_params JSONB,
    request_headers JSONB,
    request_body JSONB,
    
    -- User context
    user_id UUID NOT NULL,
    customer_id UUID,
    email VARCHAR(255),
    roles TEXT[],
    trial_mode BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- OPA policy decisions
    opa_policies_evaluated TEXT[],  -- List of policy names evaluated
    opa_decisions JSONB,             -- {policy_name: {allow: true/false, deny_reason: "..."}}
    opa_latency_ms INTEGER,
    
    -- Response metadata
    status_code INTEGER,
    response_headers JSONB,
    response_body JSONB,
    error_type VARCHAR(100),
    error_message TEXT,
    
    -- Performance metrics
    total_latency_ms INTEGER NOT NULL,
    plant_latency_ms INTEGER,
    
    -- Resource tracking
    action VARCHAR(100),
    resource VARCHAR(100),
    resource_id UUID,
    
    -- Indexes for common queries
    CONSTRAINT valid_status_code CHECK (status_code >= 100 AND status_code < 600),
    CONSTRAINT valid_latency CHECK (total_latency_ms >= 0)
);

-- Create indexes for fast queries

-- Tracing queries (find all requests in a trace)
CREATE INDEX idx_audit_correlation_id ON gateway_audit_logs(correlation_id);
CREATE INDEX idx_audit_causation_id ON gateway_audit_logs(causation_id) WHERE causation_id IS NOT NULL;

-- User queries (find all actions by a user)
CREATE INDEX idx_audit_user_id ON gateway_audit_logs(user_id);
CREATE INDEX idx_audit_customer_id ON gateway_audit_logs(customer_id) WHERE customer_id IS NOT NULL;

-- Time-based queries (recent logs, time-range analytics)
CREATE INDEX idx_audit_timestamp ON gateway_audit_logs(timestamp DESC);

-- Error queries (find failed requests)
CREATE INDEX idx_audit_errors ON gateway_audit_logs(status_code, error_type) WHERE status_code >= 400;

-- Policy decision queries (find OPA denies)
CREATE INDEX idx_audit_opa_decisions ON gateway_audit_logs USING GIN (opa_decisions);

-- Gateway type queries (CP vs PP)
CREATE INDEX idx_audit_gateway_type ON gateway_audit_logs(gateway_type);

-- Action/Resource queries (audit specific actions)
CREATE INDEX idx_audit_action_resource ON gateway_audit_logs(action, resource);

-- Composite index for user activity over time
CREATE INDEX idx_audit_user_timestamp ON gateway_audit_logs(user_id, timestamp DESC);

-- Composite index for customer activity
CREATE INDEX idx_audit_customer_timestamp ON gateway_audit_logs(customer_id, timestamp DESC) WHERE customer_id IS NOT NULL;

-- Row-Level Security (RLS) Policies
ALTER TABLE gateway_audit_logs ENABLE ROW LEVEL SECURITY;

-- Policy 1: Admins can see all logs
CREATE POLICY admin_all_access ON gateway_audit_logs
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.id = current_setting('app.current_user_id')::UUID
            AND 'admin' = ANY(users.roles)
        )
    );

-- Policy 2: Users can only see their own logs
CREATE POLICY user_own_logs ON gateway_audit_logs
    FOR SELECT
    TO authenticated
    USING (
        user_id = current_setting('app.current_user_id')::UUID
    );

-- Policy 3: Customer admins can see logs for their customer
CREATE POLICY customer_admin_logs ON gateway_audit_logs
    FOR SELECT
    TO authenticated
    USING (
        customer_id = current_setting('app.current_customer_id')::UUID
        AND EXISTS (
            SELECT 1 FROM users
            WHERE users.id = current_setting('app.current_user_id')::UUID
            AND 'customer_admin' = ANY(users.roles)
        )
    );

-- Policy 4: System service accounts (gateway, OPA) can insert logs
CREATE POLICY system_insert_logs ON gateway_audit_logs
    FOR INSERT
    TO authenticated
    WITH CHECK (
        current_setting('app.service_account', true) = 'gateway'
        OR current_setting('app.service_account', true) = 'opa'
    );

-- Automated cleanup: Delete logs older than 90 days
-- Runs daily at 2 AM UTC
SELECT cron.schedule(
    'gateway_audit_logs_cleanup',
    '0 2 * * *',  -- 2 AM daily
    $$
    DELETE FROM gateway_audit_logs
    WHERE timestamp < NOW() - INTERVAL '90 days'
    $$
);

-- Partitioning for performance (monthly partitions)
-- Improves query performance and makes cleanup faster

-- Convert to partitioned table (if not already)
-- Note: This requires recreating the table with partitioning
-- For production, use logical replication or pg_partman

-- Create partitioned table
CREATE TABLE IF NOT EXISTS gateway_audit_logs_partitioned (
    LIKE gateway_audit_logs INCLUDING ALL
) PARTITION BY RANGE (timestamp);

-- Create partitions for current and next 3 months
-- This should be automated in production via pg_partman or cron job

-- Example partition for January 2026
CREATE TABLE IF NOT EXISTS gateway_audit_logs_2026_01 PARTITION OF gateway_audit_logs_partitioned
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- Example partition for February 2026
CREATE TABLE IF NOT EXISTS gateway_audit_logs_2026_02 PARTITION OF gateway_audit_logs_partitioned
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- Example partition for March 2026
CREATE TABLE IF NOT EXISTS gateway_audit_logs_2026_03 PARTITION OF gateway_audit_logs_partitioned
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');

-- Example partition for April 2026
CREATE TABLE IF NOT EXISTS gateway_audit_logs_2026_04 PARTITION OF gateway_audit_logs_partitioned
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');

-- Create function to automatically create next month's partition
CREATE OR REPLACE FUNCTION create_next_month_partition()
RETURNS void AS $$
DECLARE
    start_date DATE;
    end_date DATE;
    partition_name TEXT;
BEGIN
    -- Calculate next month's dates
    start_date := DATE_TRUNC('month', NOW() + INTERVAL '1 month');
    end_date := DATE_TRUNC('month', NOW() + INTERVAL '2 months');
    partition_name := 'gateway_audit_logs_' || TO_CHAR(start_date, 'YYYY_MM');
    
    -- Create partition if it doesn't exist
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF gateway_audit_logs_partitioned
         FOR VALUES FROM (%L) TO (%L)',
        partition_name,
        start_date,
        end_date
    );
    
    RAISE NOTICE 'Created partition: %', partition_name;
END;
$$ LANGUAGE plpgsql;

-- Schedule monthly partition creation (1st of each month at 1 AM)
SELECT cron.schedule(
    'create_audit_log_partition',
    '0 1 1 * *',  -- 1 AM on 1st of each month
    $$SELECT create_next_month_partition()$$
);

-- Grant permissions to gateway service account
GRANT SELECT, INSERT ON gateway_audit_logs TO gateway_service_account;
GRANT SELECT, INSERT ON gateway_audit_logs_partitioned TO gateway_service_account;

-- Grant read-only access to analytics users
GRANT SELECT ON gateway_audit_logs TO analytics_read_only;
GRANT SELECT ON gateway_audit_logs_partitioned TO analytics_read_only;

-- Create materialized view for common analytics queries
CREATE MATERIALIZED VIEW IF NOT EXISTS gateway_audit_logs_daily_summary AS
SELECT
    DATE_TRUNC('day', timestamp) AS date,
    gateway_type,
    user_id,
    customer_id,
    trial_mode,
    COUNT(*) AS total_requests,
    COUNT(*) FILTER (WHERE status_code >= 200 AND status_code < 300) AS success_count,
    COUNT(*) FILTER (WHERE status_code >= 400 AND status_code < 500) AS client_error_count,
    COUNT(*) FILTER (WHERE status_code >= 500) AS server_error_count,
    AVG(total_latency_ms) AS avg_latency_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_latency_ms) AS p50_latency_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_latency_ms) AS p95_latency_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY total_latency_ms) AS p99_latency_ms,
    COUNT(*) FILTER (WHERE opa_decisions::TEXT LIKE '%"allow": false%') AS opa_deny_count
FROM gateway_audit_logs
GROUP BY date, gateway_type, user_id, customer_id, trial_mode;

-- Create index on materialized view
CREATE INDEX idx_daily_summary_date ON gateway_audit_logs_daily_summary(date DESC);
CREATE INDEX idx_daily_summary_user ON gateway_audit_logs_daily_summary(user_id, date DESC);

-- Refresh materialized view daily at 3 AM (after cleanup)
SELECT cron.schedule(
    'refresh_audit_summary',
    '0 3 * * *',  -- 3 AM daily
    $$REFRESH MATERIALIZED VIEW CONCURRENTLY gateway_audit_logs_daily_summary$$
);

-- Add comments for documentation
COMMENT ON TABLE gateway_audit_logs IS 'Audit log for all API Gateway requests (CP and PP). Retention: 90 days. Partitioned monthly for performance.';
COMMENT ON COLUMN gateway_audit_logs.correlation_id IS 'Trace ID spanning multiple requests (e.g., user session, async workflow)';
COMMENT ON COLUMN gateway_audit_logs.causation_id IS 'Parent request ID that caused this request (null for root requests)';
COMMENT ON COLUMN gateway_audit_logs.opa_decisions IS 'JSON object with policy evaluation results: {policy_name: {allow: true/false, deny_reason: "..."}}';
COMMENT ON COLUMN gateway_audit_logs.trial_mode IS 'Whether request was from trial user (impacts routing, limits)';
COMMENT ON COLUMN gateway_audit_logs.total_latency_ms IS 'Total request latency (gateway processing + Plant backend)';
COMMENT ON COLUMN gateway_audit_logs.plant_latency_ms IS 'Plant backend latency only (excludes gateway overhead)';

-- Add triggers for data validation and enrichment

-- Trigger 1: Auto-generate correlation_id if not provided
CREATE OR REPLACE FUNCTION set_default_correlation_id()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.correlation_id IS NULL THEN
        NEW.correlation_id := uuid_generate_v4();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_set_correlation_id
    BEFORE INSERT ON gateway_audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION set_default_correlation_id();

-- Trigger 2: Validate OPA decisions structure
CREATE OR REPLACE FUNCTION validate_opa_decisions()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.opa_decisions IS NOT NULL THEN
        -- Ensure it's a valid JSON object
        IF jsonb_typeof(NEW.opa_decisions) != 'object' THEN
            RAISE EXCEPTION 'opa_decisions must be a JSON object';
        END IF;
        
        -- Ensure each policy has required fields
        -- Example: {"trial_mode": {"allow": true}, "budget": {"allow": false, "deny_reason": "..."}}
        -- Note: Validation logic can be extended based on requirements
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_opa_decisions
    BEFORE INSERT OR UPDATE ON gateway_audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION validate_opa_decisions();

-- Create helper functions for common queries

-- Function 1: Get user activity summary
CREATE OR REPLACE FUNCTION get_user_activity_summary(
    p_user_id UUID,
    p_start_date TIMESTAMPTZ DEFAULT NOW() - INTERVAL '30 days',
    p_end_date TIMESTAMPTZ DEFAULT NOW()
)
RETURNS TABLE(
    total_requests BIGINT,
    success_rate NUMERIC,
    avg_latency_ms NUMERIC,
    opa_deny_rate NUMERIC,
    most_common_endpoints TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) AS total_requests,
        ROUND(
            COUNT(*) FILTER (WHERE status_code >= 200 AND status_code < 300)::NUMERIC / 
            NULLIF(COUNT(*), 0) * 100,
            2
        ) AS success_rate,
        ROUND(AVG(total_latency_ms), 2) AS avg_latency_ms,
        ROUND(
            COUNT(*) FILTER (WHERE opa_decisions::TEXT LIKE '%"allow": false%')::NUMERIC / 
            NULLIF(COUNT(*), 0) * 100,
            2
        ) AS opa_deny_rate,
        ARRAY_AGG(DISTINCT endpoint ORDER BY COUNT(*) DESC LIMIT 5) AS most_common_endpoints
    FROM gateway_audit_logs
    WHERE user_id = p_user_id
    AND timestamp BETWEEN p_start_date AND p_end_date;
END;
$$ LANGUAGE plpgsql;

-- Function 2: Find requests by correlation ID (trace all related requests)
CREATE OR REPLACE FUNCTION get_trace_by_correlation_id(p_correlation_id UUID)
RETURNS TABLE(
    id UUID,
    timestamp TIMESTAMPTZ,
    causation_id UUID,
    endpoint VARCHAR,
    status_code INTEGER,
    total_latency_ms INTEGER,
    opa_decisions JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        l.id,
        l.timestamp,
        l.causation_id,
        l.endpoint,
        l.status_code,
        l.total_latency_ms,
        l.opa_decisions
    FROM gateway_audit_logs l
    WHERE l.correlation_id = p_correlation_id
    ORDER BY l.timestamp ASC;
END;
$$ LANGUAGE plpgsql;

-- Sample queries for testing and documentation

-- Query 1: Find all OPA denies in the last 24 hours
-- SELECT * FROM gateway_audit_logs
-- WHERE timestamp > NOW() - INTERVAL '24 hours'
-- AND opa_decisions::TEXT LIKE '%"allow": false%'
-- ORDER BY timestamp DESC;

-- Query 2: Get latency percentiles by gateway type
-- SELECT
--     gateway_type,
--     PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_latency_ms) AS p50,
--     PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_latency_ms) AS p95,
--     PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY total_latency_ms) AS p99
-- FROM gateway_audit_logs
-- WHERE timestamp > NOW() - INTERVAL '24 hours'
-- GROUP BY gateway_type;

-- Query 3: Find all requests in a trace
-- SELECT * FROM get_trace_by_correlation_id('xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx');

-- Query 4: Get user activity summary
-- SELECT * FROM get_user_activity_summary(
--     'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'::UUID,  -- user_id
--     NOW() - INTERVAL '7 days',
--     NOW()
-- );
