# Skill Commentary Log

Purpose: Running commentary of Skills epic execution (story-by-story) with commands, test results, and key decisions.

---

## 2026-02-14

- Initialized this log. Next: SK-2.2 (PP UI: create skill, admin-only).

### SK-2.2 kickoff

- Checked current repo state: clean working tree; starting from branch `feat/skills-sk-2-1-pp-skill-key-ui` at commit `4bae230`.
- Created story branch: `feat/skills-sk-2-2-pp-create-skill-ui`.

### SK-2.2 implementation notes

- Frontend (PP): Added a minimal create-skill form to Genesis Console with required-field gating and an ApiErrorPanel for create failures.
- Frontend (PP): Extended `gatewayApiClient.createSkill()` to accept optional `skill_key`.
- Backend (PP): Extended PP → Plant `SkillCreate` to send optional `skill_key` and updated the PP Genesis create-skill route to forward it.
- Backend (PP): Create-skill now returns RFC7807-like JSON on 409/422 so the UI can render structured ApiErrorPanel output.

### SK-2.2 validation

- PP FrontEnd tests (container): `vitest --run src/pages/GenesisConsole.test.tsx` → 5/5 passed.
- PP BackEnd tests: `pytest tests/test_genesis_routes.py::test_create_skill_success` + `::test_create_skill_duplicate_maps_to_409` passed; note global coverage gate fails without `--no-cov`, so story-level verification used `--no-cov`.

### SK-2.2 delivery

- Commit: `2445bd4` (feat(skills): add create skill form to Genesis Console)
- Pushed branch: `feat/skills-sk-2-2-pp-create-skill-ui`

### SK-2.3 kickoff

- Created story branch: `feat/skills-sk-2-3-pp-certify-tests` (branched from SK-2.2 so PP operators have create + certify in one flow).
- Plan: add explicit frontend coverage that certify triggers refresh and disables once certified.

### SK-2.3 validation

- PP FrontEnd tests (container): `vitest --run src/pages/GenesisConsole.test.tsx` → 6/6 passed (includes certify-refresh/disable coverage).

### SK-2.3 delivery

- Commit: `7196f7e` (test(skills): cover certify refresh in Genesis Console)
- Pushed branch: `feat/skills-sk-2-3-pp-certify-tests`

### SK-2.4 kickoff

- Created story branch: `feat/skills-sk-2-4-seed-gating`.
- Scope: verify seed-defaults remains safe-to-rerun and is blocked in prod-like envs (uat/prod) per existing `is_prod_like` + `ENABLE_AGENT_SEEDING` gating.

### SK-2.4 validation

- PP BackEnd tests: `pytest --no-cov tests/test_agent_seeding_gating.py` → 2/2 passed.

### SK-2.4 delivery

- Commit: `2bbb2be` (test(skills): gate seed-defaults in prod-like envs)
- Pushed branch: `feat/skills-sk-2-4-seed-gating`

### SK-2.5 kickoff

- Created story branch: `feat/skills-sk-2-5-pp-job-roles-ui`.
- Scope: PP Genesis Console job roles get create parity with skills (create + certify) with required skill selection.

### SK-2.5 implementation notes

- Frontend (PP): Added a minimal create-job-role form to Genesis Console (name, seniority, description, required skills selection) + ApiErrorPanel for create failures.
- Frontend (PP): Added focused Vitest coverage for create-role gating, create-role conflict handling, and create-role refresh behavior.
- Backend (PP): Updated `/api/pp/genesis/job-roles` to return RFC7807-like JSON responses (409/404/422/500) consistent with skill create.
- Backend (PP): Added a focused unit test asserting DuplicateEntityError maps to a structured 409 response.

### SK-2.5 validation (Docker-only)

- PP FrontEnd (Docker): `docker compose -f docker-compose.local.yml run --rm pp-frontend-test npm test -- --run src/pages/GenesisConsole.test.tsx` → 9/9 passed.
- PP BackEnd (Docker): `docker compose -f docker-compose.local.yml run --rm pp-backend python -m pytest --no-cov tests/test_genesis_routes.py` → 7/7 passed.

---

### SK-3.1 kickoff

- Created story branch: `feat/skills-sk-3-1-hire-skill-validation`.
- Scope: Plant hire flows must fail-closed when the Agent → JobRole → required Skills chain is not certified.

### SK-3.1 implementation notes

- Plant: Added DB-gated validation in hired-agent draft + finalize to enforce that the agent exists, its job role exists, and every required skill is `status == "certified"`.
- Plant: Kept Phase-1 in-memory unit tests DB-free by only enabling this validation when `PERSISTENCE_MODE=db`.

### SK-3.1 validation (Docker-only)

- Plant BackEnd (Docker):
	- `docker compose -f docker-compose.local.yml run --rm --entrypoint pytest plant-backend --no-cov -q tests/unit/test_hired_agents_api.py tests/unit/test_hired_agents_skill_chain_validation.py` → 7/7 passed.

---

## 2026-02-15

- Session start for SK-3.1 on branch `feat/skills-sk-3-1-hire-skill-validation`.
- Immediate focus: confirm hire flows fail-closed when Agent → JobRole → required Skills are not certified, and keep validation DB-gated behind `PERSISTENCE_MODE=db`.
- Next verification run (Docker): `docker compose -f docker-compose.local.yml run --rm --entrypoint pytest plant-backend --no-cov -q tests/unit/test_hired_agents_api.py tests/unit/test_hired_agents_skill_chain_validation.py`.

### SK-3.1 execution

- Plant BackEnd (Docker): `docker compose -f docker-compose.local.yml run --rm --entrypoint pytest plant-backend --no-cov -q tests/unit/test_hired_agents_api.py tests/unit/test_hired_agents_skill_chain_validation.py` → 7/7 passed (2.29s).
- Added unit coverage to ensure SK-3.1 enforcement triggers at *draft upsert* (not only finalize), including missing required skills + uncertified required skills.
- Plant BackEnd (Docker): `docker compose -f docker-compose.local.yml run --rm --entrypoint pytest plant-backend --no-cov -q tests/unit/test_hired_agents_skill_chain_validation.py` → 2/2 passed (1.11s).

### Plant unit-suite hardening (supporting SK-3.1 confidence)

- Plant BackEnd (Docker): initial run of `pytest --no-cov -q tests/unit` hit DB-safety guard because `DATABASE_URL` pointed at `waooaw_db` (non-test).
- Created dedicated DB: `docker compose -f docker-compose.local.yml exec -T postgres psql -U waooaw -d postgres -c "CREATE DATABASE waooaw_db_test;"`.
- Fixed Alembic chain: `014_seed_demo_customer` incorrectly referenced `013_subscriptions` instead of the actual revision id `b906e19d2162` (was breaking migration graph).
- Stabilized caplog-based tests: observability setup now only removes handlers it installed (keeps pytest caplog), and test autouse fixture clears any lingering `logger.disabled=True` across the suite.
- Optional deps polish: switched Cloud Trace/OpenTelemetry imports to runtime `importlib` loading to avoid local editor import-resolution noise when the optional packages aren't installed.
- Plant BackEnd (Docker): clean unit run with test DB override:
	- `docker compose -f docker-compose.local.yml run --rm -e DATABASE_URL=postgresql+asyncpg://waooaw:waooaw_dev_password@postgres:5432/waooaw_db_test --entrypoint pytest plant-backend --no-cov -q tests/unit` → 526 passed, 5 skipped (31.84s).

### SK-3.2 kickoff

- Scope: agent type definitions must declare and publish a `required_skill_keys: string[]` contract, and Plant must reject publish when required skills are unknown or uncertified.

### SK-3.2 implementation notes

- Plant: extended agent type schema to include `required_skill_keys`.
- Plant: added publish-time validation (DB-gated behind `PERSISTENCE_MODE=db`) that maps each key to `Skill.external_id` and requires `status == "certified"`.
- PP BackEnd: updated AgentTypeDefinition schema to accept/forward `required_skill_keys`.
- PP FrontEnd: added minimal editor validation + inline guidance requiring `required_skill_keys` be a non-empty string array before enabling Publish.

### SK-3.2 validation (Docker-only)

- Plant BackEnd (Docker):
	- `docker compose -f docker-compose.local.yml run --rm --entrypoint pytest plant-backend -q tests/unit/test_agent_types_required_skill_keys_validation.py tests/unit/test_agent_types_simple_api.py` → 8/8 passed.
- PP BackEnd (Docker):
	- `docker compose -f docker-compose.local.yml run --rm --entrypoint pytest pp-backend -q --cov-fail-under=0 tests/test_agent_types_routes.py` → 4/4 passed.

### SK-3.3 kickoff

- Scope: Plant Agent Mold execution endpoints must fail-closed when the requested skill is not allowed for the agent type / hired instance.

### SK-3.3 implementation notes

- Plant: extended `ExecuteMarketingMultichannelRequest` to accept `skill_key` (preferred), `skill_id` (compat when DB-enabled), and `hired_instance_id` (optional context).
- Plant: added non-bypassable runtime enforcement for `POST /api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute`:
	- canonical skill key is `marketing.multichannel-post-v1` and requests must resolve to this key,
	- deny (403) if the agent type’s `required_skill_keys` does not include the skill,
	- if `hired_instance_id` is provided and the record has `config.skill_configs`, deny (403) if the skill block is not present.
- Plant: wrote policy denial audit records for `skill_not_allowed` / `skill_not_configured` using existing audit store patterns.

### SK-3.3 validation (Docker-only)

- Plant BackEnd (Docker):
	- `docker compose -f docker-compose.local.yml run --rm --entrypoint pytest plant-backend --no-cov -q tests/unit/test_agent_mold_enforcement_api.py` → 17/17 passed.

### SK-3.4 kickoff

- Scope: reference agent runs must return auditable `skill_key` attribution and PP must display it.

### SK-3.4 implementation notes

- Plant: extended `SkillExecutionResult` to include `skill_key` and set it for `multichannel-post-v1` executions.
- Plant: fixed reference agent runner to pass `policy_audit` explicitly when calling the Agent Mold handler directly (avoids FastAPI `Depends(...)` placeholder objects in unit tests/runtime).
- PP FrontEnd: ReferenceAgents page now displays `Skill Key` when present in the returned draft.

### SK-3.4 validation (Docker-only)

- Plant BackEnd (Docker):
	- `docker compose -f docker-compose.local.yml run --rm --entrypoint pytest plant-backend --no-cov -q tests/unit/test_reference_agents_api.py` → 15/15 passed.
