-- =============================================================================
-- seed_demo_hired_agents.sql
-- Plant PostgreSQL — demo hired agents for yogesh + rupali
-- =============================================================================
-- STEP 1: Get customer_ids from Plant's customer_entity table.
--   Run:  python scripts/get_customer_ids.py yogeshkhandge@gmail.com rupalikhandge@gmail.com
--   (Requires INDEX_KEY env var to be set if running against demo/prod DB)
--
-- STEP 2: Replace the two placeholder strings below with real UUIDs, then run:
--   psql $PLANT_DB_URL -f scripts/seed_demo_hired_agents.sql
--
-- STEP 3: Update alembic version so 024 migration is not re-run:
--   UPDATE alembic_version SET version_num = '024_seed_demo_hired_agents';
-- =============================================================================

-- ─── Confirmed UUIDs from demo DB (customer_entity — 2026-03-01) ─────────────
\set customer_yogesh  '1a9c1294-073e-4565-a359-27eae94a05b4'  -- yogeshkhandge@gmail.com
\set customer_rupali  '8a8e1d58-949f-41f3-81ff-7abf5d4a172e'  -- rupalikhandge@gmail.com
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

-- NOTE: agent_type_id column does NOT exist in the demo DB (migration 015 was not applied).
-- ── Yogesh — Agent 1: Content Creator & Publisher ───────────────────────────
INSERT INTO hired_agents (
    hired_instance_id, subscription_id, agent_id,
    customer_id, nickname, theme, config,
    configured, goals_completed, active,
    trial_status, trial_start_at, trial_end_at,
    created_at, updated_at
)
VALUES (
    'INST-YOGESH-01', 'SUB-YOGESH-01', 'AGT-MKT-001',
    :'customer_yogesh', 'Content Creator & Publisher', 'purple', '{}',
    false, false, true,
    'active',
    now() - interval '30 days',
    now() + interval '30 days',
    now(), now()
)
ON CONFLICT (subscription_id) DO NOTHING;

-- ── Yogesh — Agent 2: Share Trader ──────────────────────────────────────────
INSERT INTO hired_agents (
    hired_instance_id, subscription_id, agent_id,
    customer_id, nickname, theme, config,
    configured, goals_completed, active,
    trial_status, trial_start_at, trial_end_at,
    created_at, updated_at
)
VALUES (
    'INST-YOGESH-02', 'SUB-YOGESH-02', 'AGT-TRD-001',
    :'customer_yogesh', 'Share Trader', 'cyan', '{}',
    false, false, true,
    'active',
    now() - interval '30 days',
    now() + interval '30 days',
    now(), now()
)
ON CONFLICT (subscription_id) DO NOTHING;

-- ── Rupali — Agent 1: Content Creator & Publisher ───────────────────────────
INSERT INTO hired_agents (
    hired_instance_id, subscription_id, agent_id,
    customer_id, nickname, theme, config,
    configured, goals_completed, active,
    trial_status, trial_start_at, trial_end_at,
    created_at, updated_at
)
VALUES (
    'INST-RUPALI-01', 'SUB-RUPALI-01', 'AGT-MKT-001',
    :'customer_rupali', 'Content Creator & Publisher', 'purple', '{}',
    false, false, true,
    'active',
    now() - interval '30 days',
    now() + interval '30 days',
    now(), now()
)
ON CONFLICT (subscription_id) DO NOTHING;

-- ── Rupali — Agent 2: Share Trader ──────────────────────────────────────────
INSERT INTO hired_agents (
    hired_instance_id, subscription_id, agent_id,
    customer_id, nickname, theme, config,
    configured, goals_completed, active,
    trial_status, trial_start_at, trial_end_at,
    created_at, updated_at
)
VALUES (
    'INST-RUPALI-02', 'SUB-RUPALI-02', 'AGT-TRD-001',
    :'customer_rupali', 'Share Trader', 'cyan', '{}',
    false, false, true,
    'active',
    now() - interval '30 days',
    now() + interval '30 days',
    now(), now()
)
ON CONFLICT (subscription_id) DO NOTHING;

-- ── Mark Alembic as up-to-date so migration 024 is not re-run ───────────────
INSERT INTO alembic_version (version_num)
VALUES ('024_seed_demo_hired_agents')
ON CONFLICT (version_num) DO NOTHING;

COMMIT;

-- ── Verify ───────────────────────────────────────────────────────────────────
SELECT hired_instance_id, subscription_id, agent_id, nickname, trial_status,
       trial_end_at::date AS trial_ends,
       customer_id
FROM hired_agents
WHERE subscription_id LIKE 'SUB-YOGESH-%' OR subscription_id LIKE 'SUB-RUPALI-%'
ORDER BY subscription_id;
