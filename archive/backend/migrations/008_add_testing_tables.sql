-- Migration 008: Add Testing and Benchmarking Tables
-- Epic: 0.1 WowTester + Epic 0.2 WowBenchmark
-- Theme: TEACHER (Training Infrastructure)
-- Version: v0.2.7

-- =========================================================================
-- EVALUATION TABLES (WowTester)
-- =========================================================================

-- Store evaluation results from WowTester
CREATE TABLE IF NOT EXISTS evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(100) NOT NULL,
    agent_output TEXT NOT NULL,
    scenario JSONB NOT NULL,
    criteria JSONB NOT NULL,
    
    -- Dimension scores (0-10)
    scores JSONB NOT NULL,  -- {structural: 9.0, quality: 8.5, domain: 7.0, ...}
    overall_score FLOAT NOT NULL CHECK (overall_score >= 0 AND overall_score <= 10),
    passed BOOLEAN NOT NULL,
    
    -- Feedback
    feedback TEXT,
    strengths TEXT[],
    weaknesses TEXT[],
    suggestions TEXT[],
    
    -- Metadata
    evaluator_version VARCHAR(50) NOT NULL,
    evaluation_time_ms INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Indexes
    CONSTRAINT valid_overall_score CHECK (overall_score >= 0 AND overall_score <= 10)
);

CREATE INDEX idx_evaluations_agent ON evaluations(agent_id);
CREATE INDEX idx_evaluations_score ON evaluations(overall_score DESC);
CREATE INDEX idx_evaluations_passed ON evaluations(passed);
CREATE INDEX idx_evaluations_created ON evaluations(created_at DESC);

-- Training examples for self-training (pre-labeled by human experts)
CREATE TABLE IF NOT EXISTS training_evaluation_examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_output TEXT NOT NULL,
    scenario JSONB NOT NULL,
    
    -- Human expert labels
    expert_scores JSONB NOT NULL,  -- {structural: 9.0, quality: 8.5, ...}
    overall_score FLOAT NOT NULL CHECK (overall_score >= 0 AND overall_score <= 10),
    passed BOOLEAN NOT NULL,
    feedback TEXT NOT NULL,
    
    -- Classification
    domain VARCHAR(50) NOT NULL,  -- marketing, education, sales
    difficulty VARCHAR(20) NOT NULL,  -- simple, moderate, complex, expert
    content_type VARCHAR(50),  -- blog_post, email, social_media, etc.
    
    -- Quality control
    labeled_by VARCHAR(100) NOT NULL,
    labeled_at TIMESTAMP NOT NULL DEFAULT NOW(),
    verified BOOLEAN DEFAULT FALSE,
    verified_by VARCHAR(100),
    verified_at TIMESTAMP,
    
    -- Training metadata
    used_in_training BOOLEAN DEFAULT FALSE,
    training_phase INTEGER,  -- 1=simple, 2=moderate, 3=complex, 4=expert
    
    CONSTRAINT valid_difficulty CHECK (difficulty IN ('simple', 'moderate', 'complex', 'expert'))
);

CREATE INDEX idx_training_domain_difficulty ON training_evaluation_examples(domain, difficulty);
CREATE INDEX idx_training_used ON training_evaluation_examples(used_in_training);
CREATE INDEX idx_training_phase ON training_evaluation_examples(training_phase);

-- Store WowTester training progress
CREATE TABLE IF NOT EXISTS tester_training_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    training_run_id UUID NOT NULL,
    phase INTEGER NOT NULL,  -- 1-4
    phase_name VARCHAR(50) NOT NULL,
    
    -- Performance metrics
    examples_processed INTEGER NOT NULL,
    accuracy FLOAT NOT NULL,
    correlation_with_expert FLOAT,
    
    -- Training details
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR(20) NOT NULL,  -- running, completed, failed
    
    -- Graduation
    passed_phase BOOLEAN,
    notes TEXT
);

CREATE INDEX idx_training_run ON tester_training_progress(training_run_id);
CREATE INDEX idx_training_phase_status ON tester_training_progress(phase, status);

-- Graduation reports (evidence of agent readiness)
CREATE TABLE IF NOT EXISTS graduation_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(100) NOT NULL,
    agent_version VARCHAR(50) NOT NULL,
    
    -- Graduation status
    graduated BOOLEAN NOT NULL,
    maturity_level VARCHAR(20) NOT NULL,  -- PROFICIENT, EXPERT, etc.
    graduated_at TIMESTAMP,
    
    -- Performance evidence
    evaluation_metrics JSONB NOT NULL,  -- {accuracy: 0.92, correlation: 0.91, ...}
    test_results JSONB NOT NULL,  -- detailed test results
    
    -- Documentation
    report_summary TEXT NOT NULL,
    capabilities_validated TEXT[],
    limitations_identified TEXT[],
    recommendations TEXT[],
    
    -- Metadata
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_graduation_agent ON graduation_reports(agent_id);
CREATE INDEX idx_graduation_status ON graduation_reports(graduated);
CREATE INDEX idx_graduation_date ON graduation_reports(graduated_at DESC);

-- =========================================================================
-- BENCHMARKING TABLES (WowBenchmark)
-- =========================================================================

-- Store competitor outputs for comparison
CREATE TABLE IF NOT EXISTS competitor_outputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competitor_name VARCHAR(100) NOT NULL,  -- Jasper.ai, Copy.ai, OpenAI, etc.
    scenario JSONB NOT NULL,
    output TEXT NOT NULL,
    
    -- Metadata
    collected_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP,  -- 90-day TTL
    cost FLOAT,  -- API cost
    response_time_ms INTEGER,
    
    -- API details
    api_endpoint VARCHAR(200),
    api_version VARCHAR(50),
    parameters JSONB
);

CREATE INDEX idx_competitor_name ON competitor_outputs(competitor_name);
CREATE INDEX idx_competitor_expires ON competitor_outputs(expires_at);

-- Store benchmark comparison results
CREATE TABLE IF NOT EXISTS benchmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario JSONB NOT NULL,
    
    -- Outputs being compared
    waooaw_agent_id VARCHAR(100) NOT NULL,
    waooaw_output TEXT NOT NULL,
    competitor_outputs JSONB NOT NULL,  -- [{competitor: "Jasper", output: "...", id: uuid}]
    
    -- Comparison results
    dimension_scores JSONB NOT NULL,  -- Per dimension, per competitor
    rankings JSONB NOT NULL,  -- {1: "WowAgent", 2: "Jasper", 3: "Copy.ai"}
    best_in_class VARCHAR(100) NOT NULL,
    
    -- Analysis
    waooaw_advantages TEXT[],
    waooaw_disadvantages TEXT[],
    competitive_gaps TEXT[],
    
    -- Metadata
    benchmark_version VARCHAR(50) NOT NULL,
    benchmarked_at TIMESTAMP NOT NULL DEFAULT NOW(),
    benchmarker_confidence FLOAT  -- 0-1
);

CREATE INDEX idx_benchmarks_agent ON benchmarks(waooaw_agent_id);
CREATE INDEX idx_benchmarks_best ON benchmarks(best_in_class);
CREATE INDEX idx_benchmarks_date ON benchmarks(benchmarked_at DESC);

-- Evidence reports (marketing-ready documentation)
CREATE TABLE IF NOT EXISTS evidence_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(100) NOT NULL,
    report_title VARCHAR(200) NOT NULL,
    
    -- Evidence
    benchmark_results JSONB NOT NULL,  -- Summary of all benchmarks
    win_rate FLOAT NOT NULL,  -- % of times agent was best-in-class
    metrics_won TEXT[],  -- Which metrics did agent win on
    
    -- Marketing claims
    claims TEXT[],  -- Auto-generated, substantiated claims
    proof_points JSONB NOT NULL,  -- Supporting data for each claim
    
    -- Report document
    report_markdown TEXT NOT NULL,
    report_html TEXT,
    
    -- Metadata
    generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    valid_until TIMESTAMP,  -- Quarterly refresh
    approved_for_marketing BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_evidence_agent ON evidence_reports(agent_id);
CREATE INDEX idx_evidence_approved ON evidence_reports(approved_for_marketing);
CREATE INDEX idx_evidence_valid ON evidence_reports(valid_until);

-- Store WowBenchmark training progress
CREATE TABLE IF NOT EXISTS benchmark_training_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    training_run_id UUID NOT NULL,
    phase INTEGER NOT NULL,  -- 1-4
    
    -- Performance metrics
    examples_processed INTEGER NOT NULL,
    ranking_accuracy FLOAT NOT NULL,  -- % of times correctly identified best-in-class
    
    -- Training details
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR(20) NOT NULL,  -- running, completed, failed
    
    passed_phase BOOLEAN,
    notes TEXT
);

CREATE INDEX idx_benchmark_training_run ON benchmark_training_progress(training_run_id);

-- =========================================================================
-- UTILITY FUNCTIONS
-- =========================================================================

-- Calculate average score from JSONB scores object
CREATE OR REPLACE FUNCTION calculate_average_score(scores JSONB)
RETURNS FLOAT AS $$
DECLARE
    total FLOAT := 0;
    count INTEGER := 0;
    score_key TEXT;
BEGIN
    FOR score_key IN SELECT jsonb_object_keys(scores)
    LOOP
        total := total + (scores->>score_key)::FLOAT;
        count := count + 1;
    END LOOP;
    
    IF count = 0 THEN
        RETURN 0;
    END IF;
    
    RETURN total / count;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Get training examples for a specific phase
CREATE OR REPLACE FUNCTION get_training_examples_for_phase(
    p_phase INTEGER,
    p_limit INTEGER DEFAULT 100
)
RETURNS TABLE (
    id UUID,
    agent_output TEXT,
    scenario JSONB,
    expert_scores JSONB,
    overall_score FLOAT,
    feedback TEXT
) AS $$
DECLARE
    phase_difficulty TEXT;
BEGIN
    -- Map phase to difficulty
    phase_difficulty := CASE p_phase
        WHEN 1 THEN 'simple'
        WHEN 2 THEN 'moderate'
        WHEN 3 THEN 'complex'
        WHEN 4 THEN 'expert'
        ELSE 'simple'
    END;
    
    RETURN QUERY
    SELECT 
        te.id,
        te.agent_output,
        te.scenario,
        te.expert_scores,
        te.overall_score,
        te.feedback
    FROM training_evaluation_examples te
    WHERE te.difficulty = phase_difficulty
      AND te.verified = TRUE
    ORDER BY RANDOM()
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- =========================================================================
-- DATA VIEWS
-- =========================================================================

-- View: Agent evaluation summary
CREATE OR REPLACE VIEW agent_evaluation_summary AS
SELECT 
    agent_id,
    COUNT(*) as total_evaluations,
    AVG(overall_score) as avg_score,
    STDDEV(overall_score) as score_stddev,
    SUM(CASE WHEN passed THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as pass_rate,
    MAX(created_at) as last_evaluated
FROM evaluations
GROUP BY agent_id;

-- View: Training dataset statistics
CREATE OR REPLACE VIEW training_dataset_stats AS
SELECT 
    domain,
    difficulty,
    COUNT(*) as total_examples,
    AVG(overall_score) as avg_expert_score,
    SUM(CASE WHEN verified THEN 1 ELSE 0 END) as verified_count,
    SUM(CASE WHEN used_in_training THEN 1 ELSE 0 END) as used_count
FROM training_evaluation_examples
GROUP BY domain, difficulty;

-- View: Benchmark win rate by agent
CREATE OR REPLACE VIEW benchmark_win_rates AS
SELECT 
    waooaw_agent_id,
    COUNT(*) as total_benchmarks,
    SUM(CASE WHEN best_in_class = waooaw_agent_id THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN best_in_class = waooaw_agent_id THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as win_rate,
    MAX(benchmarked_at) as last_benchmarked
FROM benchmarks
GROUP BY waooaw_agent_id;

-- =========================================================================
-- COMMENTS
-- =========================================================================

COMMENT ON TABLE evaluations IS 'WowTester evaluation results - all agent output evaluations';
COMMENT ON TABLE training_evaluation_examples IS 'Pre-labeled examples for WowTester self-training';
COMMENT ON TABLE graduation_reports IS 'Evidence-based graduation reports for agent readiness';
COMMENT ON TABLE competitor_outputs IS 'Cached competitor outputs for benchmarking (90-day TTL)';
COMMENT ON TABLE benchmarks IS 'WowBenchmark comparison results - WAOOAW vs competitors';
COMMENT ON TABLE evidence_reports IS 'Marketing-ready evidence reports with substantiated claims';

-- =========================================================================
-- MIGRATION COMPLETE
-- =========================================================================

-- Track migration
INSERT INTO migrations (version, description, applied_at) VALUES 
    ('008', 'Add testing and benchmarking tables for WowTester and WowBenchmark agents', NOW())
ON CONFLICT (version) DO NOTHING;
