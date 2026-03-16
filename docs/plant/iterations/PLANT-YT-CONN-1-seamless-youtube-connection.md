# PLANT-YT-CONN-1 — Seamless YouTube Connection For Digital Marketing Agent

> **Template version**: 2.0

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `PLANT-YT-CONN-1` |
| Feature area | Plant-owned reusable external connection framework with YouTube as the first live customer channel |
| Created | 2026-03-16 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CONTEXT_AND_INDEX.md` §1, §5.2, §5.3, §10, §20 |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 1 |
| Total epics | 2 |
| Total stories | 5 |

---

## Zero-Cost Agent Constraints (READ FIRST)

This plan is designed for autonomous low-context agents. Every story is self-contained so the executing agent does not need to read across the repo to infer intent.

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card names exact files, exact outcome, and exact validation commands |
| No working memory across files | NFR code patterns are embedded inline in the relevant story cards |
| No planning ability | Stories are atomic and sequenced Plant first, CP proxy second, CP UI third |
| Token cost per file read | Each story limits `Files to read first` to 3 files |
| Binary inference only | Acceptance criteria are observable pass/fail behaviours |

> **Agent:** Execute exactly one story at a time. Read only the files named in that story card before editing. Do not improvise architecture outside this plan.

---

## PM Review Checklist

- [x] **EXPERT PERSONAS filled** — each iteration task block has the correct personas for Plant, CP, secrets, Terraform, and customer UI work
- [x] Epic titles name customer outcomes, not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR code snippets inline — no external NFR references required mid-execution
- [x] Every story card has max 3 files in `Files to read first`
- [x] Every story involving CP BackEnd states the exact pattern: A, B, or C
- [x] Every new backend route story embeds the `waooaw_router()` snippet
- [x] Every GET route story card says `get_read_db_session()` not `get_db_session()`
- [x] Every story that adds env vars or secrets lists the exact Terraform file paths to update
- [x] Every story has `BLOCKED UNTIL` (or `none`)
- [x] Each iteration has a time estimate and come-back datetime
- [x] The iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] Stories are sequenced Plant backend before CP proxy before CP frontend
- [x] Related backend/frontend work is kept in one iteration for PR-only delivery
- [x] No placeholders remain

---

## Vision Intake (confirmed)

- **Area:** Plant BackEnd is the implementation owner, CP BackEnd remains thin proxy only, and CP FrontEnd is in scope for hire setup and runtime UI switch-over.
- **Outcome:** A customer hiring the Digital Marketing Agent can connect YouTube once inside WAOOAW, complete Google consent and channel selection seamlessly, and then the agent uses a Plant-owned secret-backed connection without manual token copy/paste.
- **Out of scope:** No multi-platform rollout beyond YouTube, no unrelated CP redesign, no manual token UX, no environment-specific image baking, and no CP BackEnd business logic or direct DB handling.
- **Lane:** Lane B, because new Plant routes, data model changes, secret-store integration, token lifecycle handling, and CP thin-proxy wiring are all required.
- **Urgency:** One iteration only, sized to produce one PR that is expected to pass repo pre-checks and be mergeable to `main`.

---

## Objective

This iteration builds a production-grade, Plant-owned external connection framework with YouTube as the first functional adapter for the Digital Marketing Agent. The customer experience must feel agentic and finite: one Connect YouTube action, one guided Google authorization, one channel selection, one persisted secure connection, and then normal runtime use without asking the customer to fetch or paste credentials.

The implementation must preserve WAOOAW ownership boundaries exactly:

- Plant owns all connection lifecycle logic, persistence, secrets integration, provider-specific implementation, token refresh, verification, auditability, and runtime truth.
- CP FrontEnd owns customer UI, validation, and state presentation in hire setup and runtime surfaces.
- CP BackEnd remains a thin proxy to Plant routes only; no direct DB work, no secret persistence logic, and no provider-specific decision-making.
- Variables and secrets must never be baked into the image. Runtime config follows the existing image-promotion model from demo to UAT to prod.
- Any direct demo Cloud SQL DDL or data work required for this feature must be performed through the repo-supported Auth Proxy flow during story execution and captured in the execution PR.
- If the executing agent encounters repo mismatches, design debts, or follow-up items outside the acceptance criteria, those must be listed under `Open items` in the final iteration PR rather than silently expanded into scope.

---

## Architecture Decisions (read before coding)

### Customer experience rule

The customer must authorize, not configure. WAOOAW orchestrates the provider flow, stores the secret reference, validates the connection, and only exposes simple runtime states such as `Connected`, `Needs attention`, `Reconnect required`, or `Scope upgrade required`.

### Ownership rule

Plant is the source of truth for customer-level platform credentials, hired-agent platform attachments, connection verification state, token refresh lifecycle, and publish-readiness checks. CP consumes those contracts.

### Reusable domain rule

Do not build a YouTube-only storage model. Build a reusable connection domain for future sources such as LinkedIn, Facebook, Instagram, and WhatsApp, then implement YouTube as the first concrete adapter.

### Runtime attachment rule

Separate the customer-level credential record from the hired-agent runtime attachment. A customer should be able to connect YouTube once, then the platform can attach that approved connection to one or more hired-agent skills later without duplicating secrets.

### Security rule

Refresh tokens and rotating access tokens are stored only in the provisioned secret store, never in CP FrontEnd, never in Plant responses, and never in logs. Plant stores only metadata and secret references in the database.

### Deployment rule

All provider client IDs, secrets, callback origins, and secret-store settings must be injected at runtime through Terraform and Cloud Run env or secrets wiring. No image rebakes per environment, no hardcoded demo or prod branches in code.

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Plant-owned reusable connection framework, functional YouTube flow, CP thin proxies, and CP hire/runtime switch-over | E1, E2 | 5 | 6h | 2026-03-16 18:30 IST |

**Estimate basis:** Plant data model and migration = 90 min | Plant OAuth/secrets adapter = 90 min | CP thin proxy = 45 min | CP hire UI switch-over = 75 min | CP runtime UI + regression = 60 min | PR/open-items polish = 20 min.

---

## Story Tracking Table

| Story ID | Title | Status | Branch |
|---|---|---|---|
| E1-S1 | Customer can have one reusable Plant-owned YouTube credential record | Completed | `feat/PLANT-YT-CONN-1-it1-e1` |
| E1-S2 | Customer can complete a secure YouTube connect flow and Plant validates the chosen channel | Completed | `feat/PLANT-YT-CONN-1-it1-e1` |
| E1-S3 | CP can proxy the new YouTube connection flow without owning any business logic | Completed | `feat/PLANT-YT-CONN-1-it1-e2` |
| E2-S1 | Hire setup uses Connect YouTube instead of manual token entry | Planned | `feat/PLANT-YT-CONN-1-it1-e2` |
| E2-S2 | Runtime screens show real YouTube connection readiness and reconnect states | Planned | `feat/PLANT-YT-CONN-1-it1-e2` |

---

## How to Launch Each Iteration

### Iteration 1

**Pre-flight check (run in terminal before launching):**
```bash
git fetch origin && git log --oneline origin/main | head -3
git status
# Must show: clean tree on main
```

**Steps to launch:**
1. Open VS Code
2. Open Copilot Chat: `Ctrl+Alt+I` (Windows/Linux) or `Cmd+Alt+I` (Mac)
3. Click the model dropdown at the top of the chat panel → select **Agent mode**
4. Click `+` to start a new agent session
5. Type `@` in the message box → select **platform-engineer** from the dropdown
6. Copy the block below and paste into the message box → press **Enter**
7. Go away. Come back at: **2026-03-16 18:30 IST**

**Iteration 1 agent task** (paste verbatim — do not modify):

```text
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / SQLAlchemy engineer + Senior OAuth2 / Google API integration engineer + Senior GCP Secret Manager / Terraform / Cloud SQL engineer + Senior React 18 / TypeScript engineer.
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/plant/iterations/PLANT-YT-CONN-1-seamless-youtube-connection.md
YOUR SCOPE: Iteration 1 only — Epics E1 and E2. Do not touch any other iteration plan.
TIME BUDGET: 6h. If you reach 7h without finishing, follow STUCK PROTOCOL now.

EXECUTION ORDER:
1. Run: git status && git log --oneline -3
   You must be on main with a clean tree. If not, post why and HALT.
2. Read the "Agent Execution Rules" section in this plan file.
3. Read the "Iteration 1" section in this plan file.
4. Read nothing else before starting.
5. Execute Epics in this order: E1 → E2.
6. Apply required demo Cloud SQL DDL/data changes exactly as instructed in the relevant story cards using the repo-supported Auth Proxy flow.
7. When all listed tests and smoke checks pass, open the iteration PR. Include an `Open items` section in the PR body for anything discovered but not fixed by scope. Post the PR URL. HALT.
```

### Iteration 2

This plan intentionally uses one iteration only. Do not launch an Iteration 2 agent task for this plan.

---

## Agent Execution Rules

1. Start from `main` with a clean tree.
2. Execute exactly one story at a time and respect story order.
3. Plant owns DB, DDL, DML, provider logic, secret-store integration, token refresh, verification, and runtime truth.
4. CP BackEnd is thin proxy only. No CP BackEnd story may add business logic or direct DB access.
5. CP FrontEnd owns only UI, validation, and customer state presentation.
6. Do not bake variables, callback URLs, client IDs, or secrets into images. Runtime env vars and Secret Manager only.
7. For persistence work, Cloud SQL demo through the repo-supported Auth Proxy is the source of truth before Docker regression.
8. Record any repo mismatches, follow-up debt, or non-blocking design issues in an `Open items` section of the iteration PR.
9. **CHECKPOINT RULE**: After completing each epic (all tests passing), run:

```bash
git add -A && git commit -m "feat(PLANT-YT-CONN-1): [epic-id] — [epic title]" && git push
```

10. **STUCK PROTOCOL**: if blocked for more than 20 minutes on one story, open a draft PR titled `WIP: PLANT-YT-CONN-1 [story-id] — [blocker]`, post the blocker, and halt.

---

## Iteration 1 — Customer connects YouTube once and the agent can actually use it

**Goal:** Deliver one mergeable vertical slice where Plant owns a reusable connection framework and YouTube works end-to-end for Digital Marketing Agent hire setup and runtime, with CP acting only as UI plus thin proxy.

### Story Table

| Story | Title | Surface | Status | Dependency |
|---|---|---|---|---|
| E1-S1 | Customer can have one reusable Plant-owned YouTube credential record | Plant BackEnd + Demo Cloud SQL | Completed | none |
| E1-S2 | Customer can complete a secure YouTube connect flow and Plant validates the chosen channel | Plant BackEnd + Infra | Completed | E1-S1 |
| E1-S3 | CP can proxy the new YouTube connection flow without owning any business logic | CP BackEnd | Completed | E1-S2 |
| E2-S1 | Hire setup uses Connect YouTube instead of manual token entry | CP FrontEnd | Planned | E1-S3 |
| E2-S2 | Runtime screens show real YouTube connection readiness and reconnect states | CP FrontEnd | Planned | E2-S1 |

### E1 — Customer authorizes once and Plant owns the connection lifecycle

#### E1-S1 — Customer can have one reusable Plant-owned YouTube credential record

| Field | Value |
|---|---|
| Branch | `feat/PLANT-YT-CONN-1-it1-e1` |
| Pattern | Plant-native backend work |
| Story size | 90m |
| BLOCKED UNTIL | none |

**Context**

Today the repo mixes two ownership models: Plant already has `platform_connections`, but social credential resolution still expects CP-owned secret records. This story establishes the Plant-owned reusable credential foundation so a customer-level YouTube connection exists once and hired-agent attachments can reference it without duplicating secrets.

**Files to read first (max 3):**
1. `src/Plant/BackEnd/models/platform_connection.py`
2. `src/Plant/BackEnd/api/v1/platform_connections.py`
3. `src/Plant/BackEnd/database/migrations/versions/022_platform_connections.py`

**Files to create / modify**

- `src/Plant/BackEnd/models/platform_connection.py`
- `src/Plant/BackEnd/models/customer_platform_credential.py` (new)
- `src/Plant/BackEnd/models/oauth_connection_session.py` (new)
- `src/Plant/BackEnd/api/v1/platform_connections.py`
- `src/Plant/BackEnd/api/v1/router.py`
- `src/Plant/BackEnd/database/migrations/versions/0xx_customer_platform_credentials_and_oauth_sessions.py` (new)
- `src/Plant/BackEnd/tests/unit/test_platform_connections_api.py`
- `src/Plant/BackEnd/tests/unit/test_customer_platform_credential_models.py` (new)

**What to build**

- Add a Plant-owned customer-level credential metadata table for reusable external connections with fields for customer id, platform key, provider account id, display name, granted scopes, verification state, connection status, secret ref, created_at, updated_at, and optional token expiry metadata.
- Add a Plant-owned OAuth session table for state/nonce-driven connect handshakes so the callback can be validated server-side.
- Extend or refactor `platform_connections` so hired-agent attachments reference the reusable credential record rather than treating `secret_ref` as the only truth.
- Keep secrets out of response payloads and logs. Plant stores metadata plus the secret reference only.

**Cloud SQL direct apply requirement**

The agent must both create the migration file and apply the required DDL directly to the live demo Cloud SQL during execution.

Use exactly this repo-supported bootstrap flow:

```bash
bash /workspaces/WAOOAW/.devcontainer/gcp-auth.sh
# Confirm output contains:
#   "✅ gcloud authenticated"
#   "✅ Cloud SQL Proxy listening on 127.0.0.1:15432"
#   "✅ DB ready — connect: source /root/.env.db && psql"

source /root/.env.db && psql -c "SELECT current_database(), current_user;"
psql -c "SELECT version_num FROM alembic_version;"
```

If the proxy cannot attach because the instance has no public IP, run:

```bash
gcloud sql instances patch plant-sql-demo --assign-ip --project=waooaw-oauth --quiet
bash /workspaces/WAOOAW/.devcontainer/gcp-auth.sh
```

Apply the DDL via `psql` through the proxy. Do not use ad-hoc proxy commands, direct `5432` connections, or local-only Docker DB as the source of truth.

**Code patterns to copy exactly**

Use `waooaw_router()` on any new Plant route:

```python
from core.routing import waooaw_router

router = waooaw_router(prefix="/hired-agents", tags=["platform-connections"])
```

Use read replica for GET routes:

```python
from core.database import get_read_db_session

@router.get("/{hired_instance_id}/platform-connections")
async def list_connections(
    hired_instance_id: str,
    db: AsyncSession = Depends(get_read_db_session),
):
    ...
```

**Acceptance criteria**

- Plant has a reusable customer-level credential model that is not tied to one hired instance.
- Plant still exposes hired-agent platform attachments without ever returning `secret_ref`.
- Live demo Cloud SQL contains the new DDL after execution, and a smoke query proves the new tables or columns exist.
- Unit tests cover response omission of secrets and the new model invariants.

**Validation**

```bash
docker compose -f docker-compose.test.yml run --rm plant-backend-test tests/unit/test_platform_connections_api.py -q --no-cov
docker compose -f docker-compose.test.yml run --rm plant-backend-test tests/unit/test_customer_platform_credential_models.py -q --no-cov
source /root/.env.db && psql -c "\dt *platform*"
```

#### E1-S2 — Customer can complete a secure YouTube connect flow and Plant validates the chosen channel

| Field | Value |
|---|---|
| Branch | `feat/PLANT-YT-CONN-1-it1-e1` |
| Pattern | Plant-native backend + infra |
| Story size | 90m |
| BLOCKED UNTIL | E1-S1 |

**Context**

After the data model exists, Plant must own the actual YouTube connect flow: start OAuth, exchange code, store refresh token in the provisioned secret store, validate `mine=true` channel access, and return customer-safe metadata only. This story makes the connection real instead of treating YouTube as a pasted token.

**Files to read first (max 3):**
1. `src/Plant/BackEnd/integrations/social/youtube_client.py`
2. `src/Plant/BackEnd/services/social_credential_resolver.py`
3. `src/Plant/BackEnd/api/v1/platform_connections.py`

**Files to create / modify**

- `src/Plant/BackEnd/api/v1/platform_connections.py`
- `src/Plant/BackEnd/services/youtube_connection_service.py` (new)
- `src/Plant/BackEnd/services/secret_manager_service.py` or existing Plant secret adapter surface
- `src/Plant/BackEnd/integrations/social/youtube_client.py`
- `src/Plant/BackEnd/core/config.py` or equivalent settings module
- `cloud/terraform/stacks/plant/variables.tf`
- `cloud/terraform/stacks/plant/main.tf`
- `cloud/terraform/stacks/plant/environments/demo.tfvars`
- `cloud/terraform/stacks/plant/environments/uat.tfvars`
- `cloud/terraform/stacks/plant/environments/prod.tfvars`
- `src/Plant/BackEnd/tests/unit/test_youtube_connection_service.py` (new)

**What to build**

- Add Plant routes for: start YouTube connect session, finalize callback or code exchange, list reusable customer connections, fetch one connection status, and attach an approved reusable connection to a hired-agent publish skill.
- Store refresh token and rotating access token in the provisioned secret store, with the database keeping only metadata plus secret reference.
- Validate the selected channel immediately after connect by calling YouTube `channels?mine=true` and persisting provider account id, channel title, scope set, verification status, and failure state if the grant is insufficient.
- Update Terraform so provider client config and secret-manager-related runtime variables are injected at runtime only.
- Keep the legacy CP-owned credential resolver path intact only as a compatibility surface if needed, but do not make it the primary path for new YouTube connections.

**Code patterns to copy exactly**

Use `waooaw_router()` for any new Plant API file:

```python
from core.routing import waooaw_router

router = waooaw_router(prefix="/customer-platform-connections", tags=["customer-platform-connections"])
```

Use audit dependency pattern where route actions are sensitive and customer-visible:

```python
from services.audit_dependency import AuditLogger, get_audit_logger

@router.post("/youtube/connect/start")
async def start_connect(
    body: StartConnectRequest,
    audit: AuditLogger = Depends(get_audit_logger),
):
    result = await do_work(body)
    await audit.log("customer_platform_connections", "youtube_connect_started", "success", user_id=..., metadata={...})
    return result
```

Image-promotion rule for new config:

```hcl
variable "youtube_client_id" {
  type        = string
  description = "Google OAuth client ID for YouTube platform connections"
}

env {
  name  = "YOUTUBE_CLIENT_ID"
  value = var.youtube_client_id
}
```

**Acceptance criteria**

- Plant can start a valid YouTube connect session and verify callback state securely.
- Plant stores refresh token material in the secret store and persists only secret references plus metadata in the DB.
- A connected customer record shows channel title, provider account id, status, granted scopes, and last verified timestamp without exposing secrets.
- Terraform is updated for all required runtime config or secrets; no environment-specific logic is baked into code or image.
- Demo Cloud SQL has any required DML or seed/backfill applied through the proxy flow if this route depends on new reference or status data.

**Validation**

```bash
docker compose -f docker-compose.test.yml run --rm plant-backend-test tests/unit/test_youtube_connection_service.py -q --no-cov
docker compose -f docker-compose.test.yml run --rm plant-backend-test tests/unit/test_platform_connections_api.py -q --no-cov
source /root/.env.db && psql -c "SELECT COUNT(*) FROM platform_connections;"
```

#### E1-S3 — CP can proxy the new YouTube connection flow without owning any business logic

| Field | Value |
|---|---|
| Branch | `feat/PLANT-YT-CONN-1-it1-e2` |
| Pattern | B — new thin CP proxy route if no existing `/cp/*` route exists |
| Story size | 45m |
| BLOCKED UNTIL | E1-S2 |

**Context**

CP FrontEnd needs customer-facing endpoints for connect-start, callback finalize, and reusable connection status, but CP BackEnd must remain a thin proxy. Existing `cp_skills.py` already proxies hired-agent platform attachments; this story only adds missing customer-facing YouTube connection proxy surfaces.

**Files to read first (max 3):**
1. `src/CP/BackEnd/api/cp_skills.py`
2. `src/CP/BackEnd/services/plant_gateway_client.py`
3. `src/CP/BackEnd/api/platform_credentials.py`

**Files to create / modify**

- `src/CP/BackEnd/api/cp_youtube_connections.py` (new)
- `src/CP/BackEnd/main.py`
- `src/CP/BackEnd/tests/test_cp_youtube_connections_routes.py` (new)

**What to build**

- Add thin proxy routes for start-connect, finalize-connect, customer connection list or status, and attach-selected-connection-to-hire if a customer-facing `/cp/*` path is missing.
- Reuse `PlantGatewayClient` and forwarded auth/correlation headers only.
- Do not store secrets, do not read DB, do not compute OAuth details in CP BackEnd.

**Code patterns to copy exactly**

Use `waooaw_router()` and `PlantGatewayClient` only:

```python
from core.routing import waooaw_router
from services.plant_gateway_client import PlantGatewayClient

router = waooaw_router(prefix="/cp/youtube-connections", tags=["cp-youtube-connections"])
```

Circuit-breaker-safe upstream usage stays in the gateway client:

```python
resp = await plant.request_json(
    method="POST",
    path="api/v1/customer-platform-connections/youtube/connect/start",
    headers=_forward_headers(request),
    json_body=body.model_dump(),
)
```

**Acceptance criteria**

- CP BackEnd exposes the customer-facing proxy routes needed by the frontend.
- Route tests prove CP is only forwarding and returning upstream result shapes.
- No CP BackEnd file persists data or owns provider logic.

**Validation**

```bash
docker compose -f docker-compose.test.yml run --rm cp-backend-test tests/test_cp_youtube_connections_routes.py -q --no-cov
```

### E2 — Customer setup and runtime feel seamless instead of credential-driven

#### E2-S1 — Hire setup uses Connect YouTube instead of manual token entry

| Field | Value |
|---|---|
| Branch | `feat/PLANT-YT-CONN-1-it1-e2` |
| Pattern | CP FrontEnd wiring onto existing or new CP thin-proxy routes |
| Story size | 75m |
| BLOCKED UNTIL | E1-S3 |

**Context**

The current hire setup asks the customer for raw access and refresh tokens, which is the wrong product shape and the wrong security posture. This story replaces that with a guided Connect YouTube flow, selection of the verified reusable connection, and clear readiness messaging inside the existing hire setup screen.

**Files to read first (max 3):**
1. `src/CP/FrontEnd/src/pages/HireSetupWizard.tsx`
2. `src/CP/FrontEnd/src/services/platformConnections.service.ts`
3. `src/CP/FrontEnd/src/services/platformCredentials.service.ts`

**Files to create / modify**

- `src/CP/FrontEnd/src/pages/HireSetupWizard.tsx`
- `src/CP/FrontEnd/src/services/youtubeConnections.service.ts` (new)
- `src/CP/FrontEnd/src/test/HireSetupWizard.test.tsx`
- `src/CP/FrontEnd/src/components/DigitalMarketingChannelStatusCard.tsx` if needed for setup reuse

**What to build**

- Remove manual `access_token` and `refresh_token` entry from the YouTube path in hire setup.
- Add `Connect YouTube`, `Reconnect`, `Use connected channel`, and clear validation states such as `Not connected`, `Connected`, `Needs attention`, and `Scope upgrade required`.
- Let the customer choose from their verified Plant-owned YouTube connections when finalizing hire setup for the Digital Marketing Agent.
- Persist only the selected reusable connection reference in hire config or runtime attach request, never raw credential material.

**Acceptance criteria**

- Hire setup no longer asks the customer to paste YouTube tokens.
- Customer can initiate connect from the hire screen, return, and see the verified channel state.
- The selected YouTube connection is attached to the hired-agent publish workflow through CP → Plant contracts.
- Existing non-YouTube paths remain unaffected.

**Validation**

```bash
cd /workspaces/WAOOAW/src/CP/FrontEnd && npm test -- HireSetupWizard.test.tsx --runInBand
```

#### E2-S2 — Runtime screens show real YouTube connection readiness and reconnect states

| Field | Value |
|---|---|
| Branch | `feat/PLANT-YT-CONN-1-it1-e2` |
| Pattern | CP FrontEnd runtime wiring |
| Story size | 60m |
| BLOCKED UNTIL | E2-S1 |

**Context**

After setup, the customer must see whether the agent is truly ready to act on YouTube. Runtime screens should show current connection state, verification state, and reconnect guidance without leaking any token details or forcing a return to manual credential concepts.

**Files to read first (max 3):**
1. `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx`
2. `src/CP/FrontEnd/src/components/DigitalMarketingChannelStatusCard.tsx`
3. `src/CP/FrontEnd/src/test/MyAgents.test.tsx`

**Files to create / modify**

- `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx`
- `src/CP/FrontEnd/src/components/DigitalMarketingChannelStatusCard.tsx`
- `src/CP/FrontEnd/src/test/MyAgents.test.tsx`
- `src/CP/FrontEnd/e2e/hire-journey.spec.ts` if existing scenario needs alignment

**What to build**

- Replace connection summaries that assume pasted `credential_ref` flows with summaries driven by the new Plant connection status contract.
- Show runtime-safe labels such as verified channel title, last verified time, reconnect required, or approval blocked.
- Ensure deliverable and publish-readiness states remain approval-gated and do not imply publish access if the connection is stale or invalid.

**Acceptance criteria**

- My Agents and related runtime surfaces show correct YouTube readiness state from Plant-backed data.
- Reconnect-required states are visible and actionable.
- Approval gating remains explicit: valid YouTube connection does not bypass customer approval requirements.

**Validation**

```bash
cd /workspaces/WAOOAW/src/CP/FrontEnd && npm test -- MyAgents.test.tsx --runInBand
```

### Iteration 1 — Completion checkpoint

Before opening the PR, the executing agent must verify all of the following:

- Plant migration file exists and the required DDL has been applied directly to demo Cloud SQL through the supported Auth Proxy flow.
- Any required demo DML or seed/backfill has been applied and smoke-queried.
- Docker-based backend regression commands listed in the stories have passed.
- CP frontend targeted tests for hire setup and runtime status have passed.
- New runtime config and secrets are wired through Terraform only, not baked into images.
- The final PR body includes an `Open items` section for anything discovered but intentionally left out of scope.
