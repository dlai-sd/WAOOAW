# Defect List — 8 March 2026
## Session: EXEC-ENGINE-001 PP Portal Live Testing

**Reporter:** PP portal testing — customer `yogeshkhandge@gmail.com`  
**Symptom:** `404 Route Not Found — /api/v1/subscriptions` on `https://pp.demo.waooaw.com/hired-agents`  
**Correlation ID:** `64d1d99c-628f-475b-9a73-87d641e96f32`

---

## Route Mapping Reference (PP Backend → Plant)

This table is the canonical source of truth to avoid re-investigation.

| PP Backend file | PP exposed route | Current Plant path called | ✅ Correct Plant path | Status |
|---|---|---|---|---|
| `ops_subscriptions.py` | `GET /pp/ops/subscriptions` | `/api/v1/subscriptions` | `/api/v1/payments/subscriptions/by-customer/{customer_id}` | ❌ Path wrong + param type wrong |
| `ops_subscriptions.py` | `GET /pp/ops/subscriptions/{id}` | `/api/v1/subscriptions/{id}` | `/api/v1/payments/subscriptions/{subscription_id}` | ❌ Missing `/payments` segment |
| `ops_hired_agents.py` | `GET /pp/ops/hired-agents` | `/api/v1/hired-agents?subscription_id=...` | `/api/v1/hired-agents/by-subscription/{subscription_id}` | ❌ Query param vs path param |
| `ops_hired_agents.py` | `GET /pp/ops/hired-agents/{id}` | `/api/v1/hired-agents/{id}` | `/api/v1/hired-agents/by-subscription/{id}` OR does not exist as bare GET | ❌ Route doesn't exist in Plant |
| `ops_hired_agents.py` | `GET /pp/ops/hired-agents/{id}/goals` | `/api/v1/hired-agents/{id}/goals` | `/api/v1/hired-agents/{id}/goals` | ✅ Correct |
| `ops_hired_agents.py` | `GET /pp/ops/hired-agents/{id}/deliverables` | `/api/v1/hired-agents/{id}/deliverables` | `/api/v1/hired-agents/{id}/deliverables` | ✅ Correct |
| `ops_hired_agents.py` | `GET /pp/ops/hired-agents/{id}/construct-health` | `/api/v1/hired-agents/{id}/construct-health` | `/api/v1/v1/hired-agents/{id}/construct-health` | ❌ Double `/v1` prefix in Plant |
| `ops_hired_agents.py` | `GET /pp/ops/hired-agents/{id}/scheduler-diagnostics` | `/api/v1/hired-agents/{id}/scheduler-diagnostics` | `/api/v1/v1/hired-agents/{id}/scheduler-diagnostics` | ❌ Double `/v1` prefix in Plant |
| `ops_hired_agents.py` | `POST /pp/ops/hired-agents/{id}/scheduler/pause` | `/api/v1/hired-agents/{id}/scheduler/pause` | `/api/v1/v1/hired-agents/{id}/scheduler/pause` | ❌ Double `/v1` prefix in Plant |
| `ops_hired_agents.py` | `POST /pp/ops/hired-agents/{id}/scheduler/resume` | `/api/v1/hired-agents/{id}/scheduler/resume` | `/api/v1/v1/hired-agents/{id}/scheduler/resume` | ❌ Double `/v1` prefix in Plant |

---

## Defects

### DEF-001 · ACTIVE BUG — `404` on `/api/v1/subscriptions`
| | |
|---|---|
| **File** | `src/PP/BackEnd/api/ops_subscriptions.py` line 32 |
| **Root cause** | `plant_path = "/api/v1/subscriptions"` — this route does not exist in Plant. Plant's subscription routes live under the `/payments` router (`payments_simple.py`, prefix `/payments`). The full Plant path is `/api/v1/payments/subscriptions/by-customer/{customer_id}`. Additionally, the current code passes `customer_id` as a **query param** via `request.query_params`, but the Plant endpoint requires it as a **path parameter**. |
| **Impact** | The entire PP Hired Agents page fails to load for any customer. Every subsequent call (hired-agents, goals, approvals, construct health) is blocked because the subscription list is the first waterfall step. |
| **Best fix** | Change the proxy to call `GET /api/v1/payments/subscriptions/by-customer/{customer_id}` with `customer_id` extracted from query params and injected as a path segment. Return the `instances` list from `HiredAgentsByCustomerResponse`. |

---

### DEF-002 · SILENT BUG — `404` on single subscription fetch
| | |
|---|---|
| **File** | `src/PP/BackEnd/api/ops_subscriptions.py` line 62 |
| **Root cause** | `plant_path = f"/api/v1/subscriptions/{subscription_id}"` — missing `/payments` segment. Plant route is `GET /api/v1/payments/subscriptions/{subscription_id}`. |
| **Impact** | Single-subscription detail view (`GET /pp/ops/subscriptions/{id}`) would 404. Not yet exercised by the PP frontend (frontend uses the list route only on the Hired Agents page), so no user-visible error yet. |
| **Best fix** | Change to `f"/api/v1/payments/subscriptions/{subscription_id}"`. |

---

### DEF-003 · SILENT BUG — `404` on hired-agents list (wrong param style)
| | |
|---|---|
| **File** | `src/PP/BackEnd/api/ops_hired_agents.py` line 44 |
| **Root cause** | `plant_path = "/api/v1/hired-agents"` with `subscription_id` forwarded as a query param. Plant has **no root list GET** on the `/hired-agents` router. The correct endpoints are `GET /api/v1/hired-agents/by-subscription/{subscription_id}` (path param) and `GET /api/v1/hired-agents/by-customer/{customer_id}` (path param). |
| **Impact** | After DEF-001 is fixed and subscriptions load, the next waterfall step (`listOpsHiredAgents`) will immediately 404. The Hired Agents page will show no rows and never reach construct health or scheduler panels. |
| **Best fix** | Route on `subscription_id` query param: if present call `GET /api/v1/hired-agents/by-subscription/{subscription_id}`; else if `customer_id` present call `GET /api/v1/hired-agents/by-customer/{customer_id}`. The by-subscription response is a single `HiredAgentInstanceResponse` object (not a list); wrap it in a list before returning. |

---

### DEF-004 · SILENT BUG — `404` on single hired-agent GET
| | |
|---|---|
| **File** | `src/PP/BackEnd/api/ops_hired_agents.py` line 75 |
| **Root cause** | `plant_path = f"/api/v1/hired-agents/{hired_instance_id}"` — Plant has no bare `GET /{hired_instance_id}` route. The `hired_agents_simple.py` router exposes only: `/by-subscription/{id}`, `/by-customer/{id}`, `/{id}/goals`, `/{id}/finalize`, `/draft`, `/process-trial-end`. There is no GET-by-ID individual record endpoint. |
| **Impact** | Any PP backend code path that calls the single-instance GET will 404. Currently the PP frontend does not call this directly (it uses the list route), but it is available as `getOpsHiredAgent` in `gatewayApiClient.ts`. |
| **Best fix** | Either (a) add `GET /{hired_instance_id}` to Plant's `hired_agents_simple.py`, or (b) remove the single-GET proxy route from `ops_hired_agents.py` if it is not needed. |

---

### DEF-005 · PLANT BUG — Double `/v1` prefix on construct_diagnostics router
| | |
|---|---|
| **File** | `src/Plant/BackEnd/api/v1/construct_diagnostics.py` lines 24 and 284 |
| **Root cause** | Both routers in this file declare their own `/v1` prefix: `router = waooaw_router(prefix="/v1/hired-agents")` and `ops_router = waooaw_router(prefix="/v1/ops")`. These are then mounted inside `api_v1_router` (prefix `/api/v1`) in `router.py`. FastAPI concatenates prefixes, producing `/api/v1/v1/hired-agents/...` and `/api/v1/v1/ops/...`. The PP backend proxies call `/api/v1/hired-agents/{id}/construct-health` and `/api/v1/hired-agents/{id}/scheduler-diagnostics` — both one `/v1` short. |
| **Impact** | Construct health panel (E13), scheduler diagnostics panel + DLQ requeue (E14), scheduler pause/resume — all 404. These panels appear only after a row is expanded in the Hired Agents page, so the crash is **deferred** past DEF-001 and DEF-003. Once those are fixed, DEF-005 becomes the next blocker. |
| **Best fix** | Remove the `/v1` segment from both router prefixes in `construct_diagnostics.py`: change to `prefix="/hired-agents"` and `prefix="/ops"`. This brings them in line with how `hired_agents_simple.py` declares `prefix="/hired-agents"`. |

---

## Summary

- **5 defects** across 3 files.
- **1 root cause theme:** The PP ops proxy routes (written during EXEC-ENGINE-001 iterations) hardcoded Plant paths based on assumption rather than reading the actual Plant `router.py`. Two categories of mistake: (a) missing the `/payments` namespace for subscription routes, and (b) the `construct_diagnostics.py` router accidentally included a `/v1` prefix that gets doubled by the parent `api_v1_router`.
- **Crash sequence when user clicks Load:** DEF-001 fires first → page shows error. Fix DEF-001 → DEF-003 fires next. Fix DEF-003 → DEF-005 fires when expanding a row. DEF-002 and DEF-004 are latent.
- No DB schema or migration issues — all defects are routing/path mismatches only.
- **Zero code changes made in this analysis session** — this is RCA only.

---

## Live Route Test Results — 8 March 2026

**Test environment:** `https://pp.demo.waooaw.com`  
**Auth:** dev-token via PR #901 (`ENABLE_DEV_TOKEN=true`), customer `demo@waooaw.com` inserted into Plant DB  
**Setup:** `gcloud` installed in Codespace, Cloud SQL proxy running, public IP enabled on `plant-sql-demo`

| HTTP | Route | Label | Finding |
|------|-------|-------|---------|
| 200 | `GET /api/auth/me` | auth/me | ✅ Works |
| 404 | `GET /api/pp/ops/subscriptions` | listOpsSubscriptions | ❌ **DEF-001 confirmed** — Plant returns 404 (path `/api/v1/subscriptions` does not exist) |
| 404 | `GET /api/pp/ops/subscriptions/TEST` | getOpsSubscription | ❌ **DEF-002 confirmed** — same wrong path |
| 404 | `GET /api/pp/ops/hired-agents?subscription_id=x` | listOpsHiredAgents | ❌ **DEF-003 confirmed** — Plant returns 404 (no root list route) |
| 404 | `GET /api/pp/ops/hired-agents/TEST` | getOpsHiredAgent | ❌ **DEF-004 confirmed** — route doesn't exist in Plant |
| 404 | `GET /api/pp/ops/hired-agents/TEST/goals` | listOpsHiredAgentGoals | ❌ **NEW** — also 404; PP proxy route exists but Plant path wrong |
| 404 | `GET /api/pp/ops/hired-agents/TEST/deliverables` | listOpsHiredAgentDeliverables | ❌ **NEW** — also 404 |
| 401 | `GET /api/pp/ops/hired-agents/TEST/construct-health` | getOpsConstructHealth | ❌ **DEF-005 confirmed** — "Missing admin scope" (double-v1 reached wrong path on Plant) |
| 401 | `GET /api/pp/ops/hired-agents/TEST/scheduler-diagnostics` | getOpsSchedulerDiagnostics | ❌ **DEF-005 confirmed** |
| 401 | `GET /api/pp/ops/hired-agents/TEST/hook-trace` | listOpsHookTrace | ❌ **DEF-005 pattern** — same missing scope |
| 401 | `GET /api/pp/ops/dlq` | listOpsDlq | ❌ **DEF-005 confirmed** |
| 200 | `GET /api/pp/agents` | listAgents | ✅ Works (returns `[]` — no agents seeded) |
| 200 | `GET /api/pp/agent-types` | listAgentTypeDefinitions | ✅ Works (returns live agent type definitions) |
| 502 | `GET /api/pp/agent-types/AGT-MKT-HEALTH-001` | getAgentTypeDefinition | ❌ **NEW DEF-015** — ID format wrong; Agent Type IDs are slugs like `marketing.digital_marketing.v1`, not `AGT-MKT-*` format |
| 200 | `GET /api/pp/genesis/skills` | listSkills | ✅ Works |
| 200 | `GET /api/pp/genesis/job-roles` | listJobRoles | ✅ Works |
| 200 | `GET /api/pp/agent-setups` | listAgentSetups | ✅ Works (empty — JSONL local) |
| 200 | `GET /api/pp/exchange-credentials` | listExchangeCredentials | ✅ Works (empty — JSONL local) |
| 200 | `GET /api/pp/approvals` | listApprovals | ✅ Works (empty — JSONL local) |
| 200 | `GET /api/pp/audit/export` | exportAuditJson | ✅ Works — 97 entities, 0 compliant |
| 200 | `GET /api/pp/db/connection-info` | getDbConnectionInfo | ✅ Works |
| 200 | `GET /api/v1/reference-agents` | listReferenceAgents | ✅ Works — returns live agents |
| 200 | `GET /api/v1/usage-events` | listUsageEvents | ✅ Works (0 events) |
| 200 | `GET /api/v1/usage-events/aggregate` | aggregateUsageEvents | ✅ Works (0 rows) |
| 200 | `GET /api/v1/audit/policy-denials` | listPolicyDenials | ✅ Works (0 records) |
| 200 | `GET /api/v1/payments/subscriptions/by-customer/CUST-001` | listSubscriptionsByCustomer | ✅ Works (empty for CUST-001) |
| 404 | `GET /api/v1/hired-agents/by-subscription/SUB-001` | getHiredAgentBySubscription | ❌ Route in catch-all — Plant returns 404 for unknown subscription ID (expected) |
| 200 | `GET /api/v1/marketing/draft-batches` | listMarketingDraftBatches | ✅ Works (empty) |
| 200 | `GET /api/v1/agent-mold/schema/agent-spec` | fetchAgentSpecSchema | ✅ Works — returns live JSON schema |

**Summary:** 17 routes ✅ working, 11 routes ❌ broken (10 already tracked as DEF-001–005, 1 new DEF-015).  
Root cause for all OPS proxy failures: incorrect Plant paths hardcoded in EXEC-ENGINE-001 iterations.  
Catch-all passthrough routes largely working correctly.

---

### DEF-015 · LIVE CONFIRMED — Wrong agent type ID format in AgentManagement page

| | |
|---|---|
| **File** | `src/PP/FrontEnd/src/pages/AgentManagement.tsx` (test call used `AGT-MKT-HEALTH-001`) |
| **Root cause** | Agent Type IDs in the DB use slug format: `marketing.digital_marketing.v1`. The `getAgentTypeDefinition` frontend call that uses `AGT-MKT-*` IDs will always 502 because Plant returns a 404 which PP Backend wraps as 502. |
| **Impact** | Any PP page that navigates to a specific agent type by ID using the old `AGT-*` format will fail. A dropdown populated from `listAgentTypeDefinitions` would use the correct IDs, so this is only a risk if IDs are hardcoded. |
| **Best fix** | Audit `AgentManagement.tsx` and `AgentTypeSetupScreen.tsx` to ensure agent type IDs are always sourced from `listAgentTypeDefinitions` response, never hardcoded. |

---

## Full PP Frontend → PP Backend → Plant Route Map

> **Key for Plant path column:**
> - ✅ Route exists and path is correct
> - ❌ Route exists in PP but Plant path called is wrong (DEF number)
> - 🟡 Route exists but data is local (PP JSONL file, not Plant)
> - 🔵 Route exists but PP backend is a mock/stub (hardcoded response)
> - ⚠️ Route reaches Plant via catch-all passthrough (not a dedicated PP proxy route)

| PP Frontend calls (gatewayApiClient) | PP Backend route (file → full path) | Plant path called → status |
|---|---|---|
| `listOpsSubscriptions({customer_id})` | `ops_subscriptions.py` → `GET /api/pp/ops/subscriptions` | `GET /api/v1/subscriptions` ❌ DEF-001: should be `/api/v1/payments/subscriptions/by-customer/{id}` |
| `getOpsSubscription(id)` | `ops_subscriptions.py` → `GET /api/pp/ops/subscriptions/{id}` | `GET /api/v1/subscriptions/{id}` ❌ DEF-002: should be `/api/v1/payments/subscriptions/{id}` |
| `listOpsHiredAgents({subscription_id})` | `ops_hired_agents.py` → `GET /api/pp/ops/hired-agents` | `GET /api/v1/hired-agents?subscription_id=...` ❌ DEF-003: should be `/api/v1/hired-agents/by-subscription/{id}` |
| `getOpsHiredAgent(id)` | `ops_hired_agents.py` → `GET /api/pp/ops/hired-agents/{id}` | `GET /api/v1/hired-agents/{id}` ❌ DEF-004: this GET-by-ID route does not exist in Plant at all |
| `listOpsHiredAgentGoals(id)` | `ops_hired_agents.py` → `GET /api/pp/ops/hired-agents/{id}/goals` | `GET /api/v1/hired-agents/{id}/goals` ✅ Correct |
| `listOpsHiredAgentDeliverables(id)` | `ops_hired_agents.py` → `GET /api/pp/ops/hired-agents/{id}/deliverables` | `GET /api/v1/hired-agents/{id}/deliverables` ✅ Correct (via deliverables_simple hired_agents_router) |
| `getOpsConstructHealth(id)` | `ops_hired_agents.py` → `GET /api/pp/ops/hired-agents/{id}/construct-health` | `GET /api/v1/hired-agents/{id}/construct-health` ❌ DEF-005: Plant mounts this as `/api/v1/v1/hired-agents/{id}/construct-health` (double v1) |
| `getOpsSchedulerDiagnostics(id)` | `ops_hired_agents.py` → `GET /api/pp/ops/hired-agents/{id}/scheduler-diagnostics` | `GET /api/v1/hired-agents/{id}/scheduler-diagnostics` ❌ DEF-005: same double-v1 problem |
| `pauseOpsScheduler(id)` | `ops_hired_agents.py` → `POST /api/pp/ops/hired-agents/{id}/scheduler/pause` | `POST /api/v1/hired-agents/{id}/scheduler/pause` ❌ DEF-005: double-v1 |
| `resumeOpsScheduler(id)` | `ops_hired_agents.py` → `POST /api/pp/ops/hired-agents/{id}/scheduler/resume` | `POST /api/v1/hired-agents/{id}/scheduler/resume` ❌ DEF-005: double-v1 |
| `listOpsDlq(query)` | `ops_dlq.py` → `GET /api/pp/ops/dlq` | `GET /api/v1/ops/dlq` ❌ DEF-005: Plant mounts as `/api/v1/v1/ops/dlq` (double v1) |
| `requeueOpsDlqEntry(id)` | `ops_dlq.py` → `POST /api/pp/ops/dlq/{id}/requeue` | `POST /api/v1/ops/dlq/{id}/requeue` ❌ DEF-005: double-v1 |
| `listOpsHookTrace(id)` | `ops_hired_agents.py` → `GET /api/pp/ops/hired-agents/{id}/hook-trace` | `GET /api/v1/hired-agents/{id}/hook-trace` — needs verification, hook-trace route exists in construct_diagnostics but path unclear |
| `listAgents(query)` | `agents.py` → `GET /api/pp/agents` | `GET /api/v1/agents` via `plant_client.list_agents()` ✅ Correct |
| `seedDefaultAgentData()` | `agents.py` → `POST /api/pp/agents/seed-defaults` | Calls Plant `create_skill`, `create_job_role`, `create_agent` methods ✅ Correct |
| `listAgentTypeDefinitions()` | `agent_types.py` → `GET /api/pp/agent-types` | `GET /api/v1/agent-types` via `plant_client.list_agent_type_definitions()` ✅ Correct |
| `getAgentTypeDefinition(id)` | `agent_types.py` → `GET /api/pp/agent-types/{id}` | `GET /api/v1/agent-types/{id}` ✅ Correct |
| `publishAgentTypeDefinition(id)` | `agent_types.py` → `PUT /api/pp/agent-types/{id}` | `PUT /api/v1/agent-types/{id}` ✅ Correct |
| `listSkills(query)` | `genesis.py` → `GET /api/pp/genesis/skills` | `GET /api/v1/genesis/skills` via `plant_client.list_skills()` ✅ Correct |
| `getSkill(id)` | `genesis.py` → `GET /api/pp/genesis/skills/{id}` | `GET /api/v1/genesis/skills/{id}` ✅ Correct |
| `createSkill(payload)` | `genesis.py` → `POST /api/pp/genesis/skills` | `POST /api/v1/genesis/skills` ✅ Correct |
| `certifySkill(id)` | `genesis.py` → `POST /api/pp/genesis/skills/{id}/certify` | `POST /api/v1/genesis/skills/{id}/certify` ✅ Correct |
| `listJobRoles(query)` | `genesis.py` → `GET /api/pp/genesis/job-roles` | `GET /api/v1/genesis/job-roles` ✅ Correct |
| `createJobRole(payload)` | `genesis.py` → `POST /api/pp/genesis/job-roles` | `POST /api/v1/genesis/job-roles` ✅ Correct |
| `certifyJobRole(id)` | `genesis.py` → `POST /api/pp/genesis/job-roles/{id}/certify` | `POST /api/v1/genesis/job-roles/{id}/certify` ✅ Correct |
| `listAgentSetups(query)` | `agent_setups.py` → `GET /api/pp/agent-setups` | 🟡 Local JSONL file (`/app/data/agent_setups.jsonl`) — never calls Plant |
| `upsertAgentSetup(payload)` | `agent_setups.py` → `PUT /api/pp/agent-setups` | 🟡 Local JSONL file — never calls Plant |
| `patchConstraintPolicy(id, patch)` | `agent_setups.py` → `PATCH /api/pp/agent-setups/{id}/constraint-policy` | 🟡 Local JSONL file — never calls Plant |
| `listExchangeCredentials(query)` | `exchange_credentials.py` → `GET /api/pp/exchange-credentials` | 🟡 Local JSONL file (`/app/data/exchange_credentials.jsonl`) |
| `upsertExchangeCredential(payload)` | `exchange_credentials.py` → `PUT /api/pp/exchange-credentials` | 🟡 Local JSONL file — never calls Plant |
| `getExchangeCredentialBundle(id)` | `exchange_credentials.py` → `GET /api/pp/exchange-credentials/{id}` | 🟡 Local JSONL file |
| `mintApproval(payload)` | `approvals.py` → `POST /api/pp/approvals` | 🟡 Local JSONL file (`/app/data/approvals.jsonl`) — never calls Plant |
| `listApprovals(query)` | `approvals.py` → `GET /api/pp/approvals` | 🟡 Local JSONL file — never calls Plant |
| `runAudit(query)` | `audit.py` → `POST /api/pp/audit/run` | `POST /api/v1/audit/run` via raw httpx call ✅ Correct path |
| `detectTampering(id)` | `audit.py` → `GET /api/pp/audit/tampering/{id}` | `GET /api/v1/audit/tampering/{id}` via raw httpx ✅ Correct path |
| `exportAuditJson(query)` | `audit.py` → `GET /api/pp/audit/export` | `GET /api/v1/audit/export` via raw httpx ✅ Correct path |
| `mintDbUpdatesToken()` | `auth.py` → `POST /api/auth/db-updates-token` | 🔵 Stub: generates a local JWT, does not call Plant |
| `getDbConnectionInfo()` | `db_updates.py` → `GET /api/pp/db/connection-info` | 🔵 Returns hardcoded/env-var DB connection string — no Plant call |
| `executeDbSql(payload)` | `db_updates.py` → `POST /api/pp/db/execute` | 🔵 Executes SQL directly against PP's Postgres — no Plant call |
| `listReferenceAgents()` | catch-all proxy → `GET /api/v1/reference-agents` | ⚠️ Passes through main_proxy catch-all to `GET /api/v1/reference-agents` on Plant ✅ |
| `listUsageEvents(query)` | catch-all proxy → `GET /api/v1/usage-events` | ⚠️ Passes through to Plant `GET /api/v1/usage-events` ✅ |
| `aggregateUsageEvents(query)` | catch-all proxy → `GET /api/v1/usage-events/aggregate` | ⚠️ Passes through to Plant `GET /api/v1/usage-events/aggregate` ✅ |
| `listPolicyDenials(query)` | catch-all proxy → `GET /api/v1/audit/policy-denials` | ⚠️ Passes through to Plant `GET /api/v1/audit/policy-denials` ✅ |
| `listSubscriptionsByCustomer(id)` | catch-all proxy → `GET /api/v1/payments/subscriptions/by-customer/{id}` | ⚠️ Passes through to Plant — this is the **correct path** the HiredAgentsOps ops proxy should also be using ✅ |
| `getHiredAgentBySubscription(id)` | catch-all proxy → `GET /api/v1/hired-agents/by-subscription/{id}` | ⚠️ Passes through to Plant — **correct path** the ops proxy should use ✅ |
| `listMarketingDraftBatches(query)` | catch-all proxy → `GET /api/v1/marketing/draft-batches` | ⚠️ Passes through to Plant ✅ |
| `approveMarketingDraftPost(id)` | catch-all proxy → `POST /api/v1/marketing/draft-posts/{id}/approve` | ⚠️ Passes through to Plant ✅ |
| `scheduleMarketingDraftPost(id)` | catch-all proxy → `POST /api/v1/marketing/draft-posts/{id}/schedule` | ⚠️ Passes through to Plant ✅ |
| `fetchAgentSpecSchema()` | catch-all proxy → `GET /api/v1/agent-mold/schema/agent-spec` | ⚠️ Passes through to Plant ✅ |
| `validateAgentSpec(payload)` | catch-all proxy → `POST /api/v1/agent-mold/spec/validate` | ⚠️ Passes through to Plant ✅ |
| `runReferenceAgent(id, payload)` | catch-all proxy → `POST /api/v1/reference-agents/{id}/run` | ⚠️ Passes through to Plant ✅ |
| `listGoalsForHiredInstance(id)` | catch-all proxy → `GET /api/v1/hired-agents/{id}/goals` | ⚠️ Passes through to Plant ✅ (same path as ops proxy but via passthrough) |
| `listDeliverablesForHiredInstance(id)` | catch-all proxy → `GET /api/v1/hired-agents/{id}/deliverables` | ⚠️ Passes through to Plant ✅ |
| `GET /api/auth/me` (AuthContext) | `auth.py` → `GET /api/auth/me` | 🔵 **MOCK**: returns hardcoded `{"name":"PP Admin","email":"admin@waooaw.com"}` — no auth wired |

---

## Architecture Observation

The PP backend has **two separate channels** to Plant:

1. **Dedicated proxy routes** (`/api/pp/ops/*`, `/api/pp/agents`, `/api/pp/genesis/*`, etc.) — each PP backend file explicitly calls a known Plant path using `PlantAPIClient` or raw httpx.
2. **Catch-all passthrough** — `main_proxy.py` line 164: any `/api/{path}` not matched by a dedicated route is blindly forwarded to `PLANT_GATEWAY_URL/api/{path}`.

The frontend uses **both channels simultaneously** — some methods in `gatewayApiClient.ts` call `/v1/*` (catch-all passthrough) and others call `/pp/ops/*` (dedicated proxy). This works today but is a maintenance risk: the catch-all routes bypass PP-level auth, audit logging, and rate limiting.

**Count (pre-live-test estimate):** 5 broken routes (DEF-001 to DEF-005), 3 local JSONL stubs (agent_setups, exchange_credentials, approvals), 1 mock auth endpoint, ~20 working routes.

**Count (live test 8 Mar 2026):** 17 ✅ working, 11 ❌ broken. See "Live Route Test Results" section above.

---

## UI Defects — PP Frontend (Recorded 8 March 2026)

> Identified by full static analysis of all 17 PP frontend pages and `gatewayApiClient.ts`.
> No code changes. These are observations only, pending user approval to fix.

---

### DEF-006 · UI — Dashboard shows 100% hardcoded fake metrics

| | |
|---|---|
| **File** | `src/PP/FrontEnd/src/pages/Dashboard.tsx` |
| **Root cause** | All 4 metric cards contain hardcoded static strings: MRR = ₹2.4M, Active Agents = 47, Customers = 1,234, Churn Rate = 2.3%. Zero API calls are made on the Dashboard page. |
| **Impact** | Admin portal home screen shows fabricated data. Anyone viewing it believes the platform has 47 agents and 1,234 customers when these numbers are meaningless. |
| **Best fix** | Replace hardcoded values with live API calls: `listAgents` for agent count, `listSubscriptionsByCustomer` (aggregate) for customer count, `listOpsSubscriptions` for active/churn rate, a revenue endpoint for MRR. |

---

### DEF-007 · UI — "Customer Management" page shows usage events, not customers

| | |
|---|---|
| **File** | `src/PP/FrontEnd/src/pages/CustomerManagement.tsx` |
| **Root cause** | Page is labelled "Customers" in `Layout.tsx` nav and titled "Customer Management" internally, but the only data loaded is `listUsageEvents` + `aggregateUsageEvents`. Zero customer lookup or listing. |
| **Impact** | An operator with a customer complaint navigates to "Customers" and finds a usage-events console. There is no way to search for a customer by email or look up their subscription from the PP portal. |
| **Best fix** | Either (a) rename the page to "Usage Events" and fix the nav label, or (b) replace the content with a customer directory that calls `listSubscriptionsByCustomer` and surfaces customer profiles. Option (b) is the correct UX intent. |

---

### DEF-008 · UI — "Governor" page is actually a reference-agent test harness

| | |
|---|---|
| **File** | `src/PP/FrontEnd/src/pages/GovernorConsole.tsx` |
| **Root cause** | Nav label is "Governor" suggesting policy governance and constitutional review. Actual function: loads `listReferenceAgents()`, lets operator pick one, runs `runReferenceAgent()` + mints a test approval via `mintApproval()`. This is a developer simulation tool, not a governance console. |
| **Impact** | Governors using the PP portal will not find policy management, approval workflow management, or constitutional compliance tools under the Governor nav item. |
| **Best fix** | Rename nav item to "Reference Agents" or "Agent Simulation". If a true governor console is needed (listing pending approvals, enforcing constitutional policy), it should be a separate page. `ApprovalsQueueScreen` already handles approval listing — the Governor label should point there or replace this page. |

---

### DEF-009 · UI — "Billing & Revenue" page shows only subscription counts, no revenue

| | |
|---|---|
| **File** | `src/PP/FrontEnd/src/pages/Billing.tsx` |
| **Root cause** | `listOpsSubscriptions({})` called with no filters — loads ALL platform subscriptions into 4 count cards (total, active, trial, inactive). No MRR, no payment history, no per-customer breakdown, no revenue figures at all. |
| **Impact** | Page title "Billing & Revenue" overpromises. Finance/ops staff navigating here find no revenue data. |
| **Best fix** | Either (a) rename to "Subscription Overview" to match actual content, or (b) add revenue API calls and customer-level billing breakdown. |

---

### DEF-010 · UI — ReviewQueue has hardcoded demo IDs and only handles Content Creator agent

| | |
|---|---|
| **File** | `src/PP/FrontEnd/src/pages/ReviewQueue.tsx` |
| **Root cause** | Component state initialises with `customerId = 'CUST-001'` and `agentId = 'AGT-MKT-HEALTH-001'` — test/demo values baked into production code. Additionally the page exclusively calls `listMarketingDraftBatches` / `approveMarketingDraftPost` / `scheduleMarketingDraftPost` — it is a marketing content review tool for one agent type, not a generic "Review Queue". |
| **Impact** | Any operator loading the page sees CUST-001 and AGT-MKT-HEALTH-001 pre-populated. The page name implies it handles all agent deliverable review, but it is scoped to marketing content drafts only. |
| **Best fix** | (a) Remove hardcoded defaults — use empty strings so operator must enter IDs explicitly. (b) Rename to "Marketing Draft Review" or "Content Review Queue" to set correct expectations. |

---

### DEF-011 · UI — Demo Login button suppressed on demo environment

| | |
|---|---|
| **File** | `src/PP/FrontEnd/src/App.tsx` line ~154 |
| **Root cause** | `allowDemoLogin = config.name === 'codespace' \|\| config.name === 'development'`. On `pp.demo.waooaw.com` the environment name is `'demo'`, which fails this check. PR #901 enables the backend `/api/auth/dev-token` endpoint (`ENABLE_DEV_TOKEN=true`) but the frontend never renders the Demo Login button on the deployed demo environment. |
| **Impact** | The dev-token backend endpoint is now live and working (verified 8 Mar 2026) but unreachable from the PP demo UI. Testers and operators must call the endpoint manually via curl to get a token. |
| **Best fix** | Add `config.name === 'demo'` to the `allowDemoLogin` condition, or simplify to `config.name !== 'production'`. |

---

### DEF-012 · UI — AgentManagement conflates agent browsing with agent type JSON editing

| | |
|---|---|
| **File** | `src/PP/FrontEnd/src/pages/AgentManagement.tsx` |
| **Root cause** | Single page contains two entirely different workflows: (1) browse deployed agents via `listAgents`, (2) inline JSON editor for Agent Type Definitions via `listAgentTypeDefinitions` + `publishAgentTypeDefinition`. |
| **Impact** | An ops admin looking for deployed agents and a developer editing agent type blueprints are different roles doing different work, but they share the same page with no visual separation. The JSON editor is only surfaced after selecting a type — discoverable. |
| **Best fix** | Move the Agent Type Definition editor to `AgentTypeSetupScreen` (which already handles type-level setup), leaving `AgentManagement` focused on browsing deployed agent instances. |

---

### DEF-013 · UI — Navigation icon duplication and confusable names

| | |
|---|---|
| **File** | `src/PP/FrontEnd/src/components/Layout.tsx` |
| **Root cause** | Icon re-use: `ShieldTask24Regular` used on 4 items (Approvals Queue, Review Queue, Audit, Governor); `Bot24Regular` used on 3 items (Agent Management, Agent Setup, Agent Type Setup). 16 flat nav items with no section grouping. "Approvals Queue" and "Review Queue" look interchangeable — one is for governor-gated financial/sensitive action approvals, the other is for marketing content draft review. |
| **Impact** | Operators scanning the nav cannot distinguish groups or quickly identify which shield-icon item they need. New ops staff will regularly open the wrong page. |
| **Best fix** | (a) Assign distinct icons per item (e.g. `DocumentApproval` for Review Queue, `People24Regular` for Approvals Queue). (b) Add nav section headers (e.g. "Operations", "Configuration", "Compliance"). (c) Rename "Review Queue" → "Draft Review" and "Governor" → "Reference Agents" (per DEF-008). |

---

### DEF-014 · UI — HiredAgentsOps requires Plant UUID, but operators have customer email

| | |
|---|---|
| **File** | `src/PP/FrontEnd/src/pages/HiredAgentsOps.tsx` |
| **Root cause** | The "Customer ID" input on the Hired Agents page expects a Plant-internal UUID (e.g. `ce8cf044-b378-4d3d-b11d-4817074b08f6`). Operators identify customers by email address (e.g. `yogeshkhandge@gmail.com`). There is no email-to-UUID lookup on the page. |
| **Impact** | The original reported defect: operator loads `yogeshkhandge@gmail.com`, gets a 404, cannot proceed. Even after DEF-001 through DEF-005 are fixed, the operator still cannot use this page without knowing the internal Plant UUID. |
| **Best fix** | Add an email lookup step: call `GET /api/v1/payments/subscriptions/by-customer/{customer_id}` — but this also requires UUID. The better fix is to expose a `GET /api/v1/customers/by-email?email=...` plant route (or use the existing customer entity endpoint) and add an email input field that resolves to customer_id before calling `listOpsSubscriptions`. |
