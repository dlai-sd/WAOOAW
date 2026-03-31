# PLANT-REDIS-1 — Managed Redis Foundation And Reusable Runtime Surface

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `PLANT-REDIS-1` |
| Feature area | Managed Redis on GCP + Plant runtime Redis surface + CP/PP wiring |
| Created | 2026-03-31 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CONTEXT_AND_INDEX.md` §§5, 9, 14, 17 |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 1 |
| Total epics | 3 |
| Total stories | 6 |

---

## Vision Intake (confirmed)

1. **Area:** Infra + Plant BackEnd + Plant Gateway + CP BackEnd, with PP BackEnd wiring included only where it already has an existing Redis consumer.
2. **Outcome:** WAOOAW uses one real managed Redis endpoint on GCP, every backend service uses the intended logical Redis DB index through runtime-injected secrets, Plant exposes reusable Redis-backed runtime endpoints, and CP/PP/mobile consume standard Plant-backed surfaces instead of inventing service-local Redis behavior.
3. **Out of scope:** HA Redis, mobile UI work, PP UI work, unrelated PostgreSQL changes, Redis creation through Terraform, and any image-baked Redis configuration.
4. **Lane:** Lane B — new backend/platform work is required, plus infra-reference changes after live Redis is created by script.
5. **Urgency:** One iteration only. The iteration must include GCP script provisioning, Cloud Run env/secret updates, Plant reusable API surfaces, and CP wiring.

---

## Objective

| Objective | Detail |
|---|---|
| Platform objective | Create one non-HA managed Redis instance on GCP by script, not by Terraform, and make it the single runtime cache/throttle/session endpoint for demo. |
| Runtime objective | Use one real Redis host with service-specific logical DB indices: Plant BackEnd `/0`, Plant Gateway `/1`, PP BackEnd `/2`, CP BackEnd `/3`. |
| Configuration objective | Store all Redis connection strings and all environment-specific Redis-related values in GCP Secret Manager and inject them into Cloud Run as `REDIS_URL`; do not hardcode hostnames, DB indices, or any environment-specific values in images, code, committed `.env` files, or Terraform defaults. |
| API objective | Create standard reusable Plant runtime Redis endpoints so CP, PP, and mobile can rely on one canonical Plant-backed surface for Redis health/config/invalidation concerns. |
| CP objective | Replace CP’s file-backed refresh revocation store with a Redis-backed implementation and add a thin CP proxy for the new Plant runtime Redis endpoints where CP needs them. |

---

## Zero-Cost Agent Constraints (READ FIRST)

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is self-contained and names exact files/lines |
| No working memory across files | Code patterns are embedded inline in each story |
| No planning ability | Each story is atomic, testable, and branch-scoped |
| Token cost per file read | Max 3 files in "Files to read first" per story |
| Binary inference only | Acceptance criteria are pass/fail and test commands are explicit |

> **Agent:** Before touching any story, get familiar with WAOOAW by reading `/workspaces/WAOOAW/docs/CONTEXT_AND_INDEX.md`, then read only the files listed in your story card.
> **Agent:** For any configuration or environment-variable change, keep the image environment-agnostic and move values into GCP Secret Manager or Cloud Run runtime secret references only.

---

## PM Review Checklist

- [x] **EXPERT PERSONAS filled** — iteration launch block names the required personas
- [x] Epic titles name outcomes, not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR snippets inline
- [x] Every story card has max 3 files in "Files to read first"
- [x] Every story involving CP BackEnd states the exact pattern: A, B, C, or N/A
- [x] Every new backend route story embeds the `waooaw_router()` snippet
- [x] Every GET route story card avoids `get_db_session()` for read-only work
- [x] Every story that adds env vars or secrets lists the exact Terraform file paths to update
- [x] Every story has `BLOCKED UNTIL` (or `none`)
- [x] The iteration has a time estimate and a come-back datetime
- [x] The iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules
- [x] Stories are sequenced backend/platform before portal reuse
- [x] Iteration count minimized to one iteration as requested
- [x] No placeholders remain

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane B — create live GCP Redis by script, move all service wiring to secret-backed runtime URLs, add reusable Plant Redis endpoints, and wire CP/PP to standard Redis-backed surfaces | 3 | 6 | 6h | 2026-04-01 16:00 IST |

**Estimate basis:** GCP automation script = 60 min | Cloud Run/Terraform secret reference updates = 60 min | shared Plant Redis service = 45 min | new Plant API surface = 60 min | Gateway hardening = 75 min | CP/PP wiring = 60 min. Add 20% buffer for zero-cost agent context loading.

---

## How to Launch Each Iteration

### Iteration 1

**Pre-flight check (run in terminal before launching):**
```bash
git status && git log --oneline -3
# Must show: clean tree on main. If not, resolve before launching.
```

**Steps to launch:**
1. Open VS Code
2. Open Copilot Chat: `Ctrl+Alt+I` (Windows/Linux) or `Cmd+Alt+I` (Mac)
3. Click the model dropdown at the top of the chat panel → select **Agent mode**
4. Click `+` to start a new agent session
5. Type `@` in the message box → select **platform-engineer** from the dropdown
6. Copy the block below and paste into the message box → press **Enter**
7. Go away. Come back at: **2026-04-01 16:00 IST**

**Iteration 1 agent task** (paste verbatim — do not modify):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Terraform / GCP Cloud Run engineer + GCP Cloud Logging / IAM expert + Senior Python 3.11 / FastAPI engineer + Senior Docker / container engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/plant/iterations/PLANT-REDIS-1-managed-redis-foundation.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2, E3. There is no Iteration 2 in this plan.
TIME BUDGET: 6h. If you reach 7h without finishing, follow STUCK PROTOCOL now.

EXECUTION ORDER:
1. Run: git status && git log --oneline -3
   You must be on main with a clean tree. If not, post why and HALT.
2. Read `/workspaces/WAOOAW/docs/CONTEXT_AND_INDEX.md` first to get familiar with WAOOAW.
3. Read the "Agent Execution Rules" section in this plan file.
4. Read the "Iteration 1" section in this plan file.
5. Read nothing else before starting except the files named in each story card.
6. Execute epics in this order: E1 → E2 → E3.
7. When all epics are docker-tested and the live GCP validation passes, open the iteration PR. Post the PR URL. HALT.
```

**When you return:** Check Copilot Chat for a PR URL. If you see a draft PR titled `WIP:` — an agent got stuck. Read the PR comment for the exact blocker.

---

## Agent Execution Rules

### Rule -1 — Activate Expert Personas (first thing, before Rule 0)

Read the `EXPERT PERSONAS:` field from the task you were given.
Activate each persona now. For every epic you execute, open with one line:

> *"Acting as a [persona], I will [what you're building] by [approach]."*

| Technology area | Expert persona to activate |
|---|---|
| `cloud/scripts/`, `gcloud`, Secret Manager, Memorystore, Cloud Run wiring | Senior Terraform / GCP Cloud Run engineer + GCP Cloud Logging / IAM expert |
| `src/Plant/BackEnd/`, `src/Plant/Gateway/`, `src/CP/BackEnd/`, `src/PP/BackEnd/` | Senior Python 3.11 / FastAPI engineer |
| `Dockerfile`, `docker-compose*.yml`, runtime validation | Senior Docker / container engineer |

### Rule -0 — Update session commentary before writing the epic

Before changing any code or infra references for an epic:

```bash
printf '\n## [%s] Redis iteration checkpoint\n\n**Branch**: `%s`\n**Epic**: [fill epic id]\n**Next save point**: [fill next checkpoint]\n\n### Todo\n- [ ] [story 1]\n- [ ] [story 2]\n' "$(date -u '+%Y-%m-%d %H:%M UTC')" "$(git branch --show-current)" >> session_commentary.md
git add session_commentary.md
git commit -m "docs(PLANT-REDIS-1): checkpoint epic context"
git push origin "$(git branch --show-current)"
```

Update `session_commentary.md` again after each story and after each epic checkpoint so a new session can resume without repeating repo archaeology.

### Rule 0 — Open tracking draft PR first (before writing any code)

```bash
git checkout main && git pull
git checkout -b feat/PLANT-REDIS-1-it1-e1
git commit --allow-empty -m "chore(PLANT-REDIS-1): start iteration 1"
git push origin feat/PLANT-REDIS-1-it1-e1

gh pr create \
  --base main \
  --head feat/PLANT-REDIS-1-it1-e1 \
  --draft \
  --title "tracking: PLANT-REDIS-1 Iteration 1 — in progress" \
  --body "## tracking: PLANT-REDIS-1 Iteration 1

Subscribe to this PR to receive one notification per story completion.

### Stories
- [ ] [E1-S1] Provision managed Redis by script and bootstrap service secrets
- [ ] [E1-S2] Replace hardcoded Redis wiring with Cloud Run secret references
- [ ] [E2-S1] Create shared Plant Redis runtime service
- [ ] [E2-S2] Add reusable Plant Redis runtime endpoints
- [ ] [E3-S1] Harden Plant Gateway Redis integration
- [ ] [E3-S2] Wire CP and PP to the standard Redis-backed surfaces

_Live updates posted as comments below ↓_"
```

### Rule 1 — Branch discipline
One epic = one branch: `feat/PLANT-REDIS-1-it1-e1`, `feat/PLANT-REDIS-1-it1-e2`, `feat/PLANT-REDIS-1-it1-e3`.
All stories in one epic commit to the same branch sequentially.
Never push to `main` directly.

### Rule 2 — Scope lock
Implement exactly the acceptance criteria in the story card.
Do not fix unrelated code. Do not refactor outside scope.
If you notice a bug outside your scope: mention it in the PR description and move on.

### Rule 3 — Tests before the next story
Write every test in the story’s test table before advancing.
Run the exact test command listed in the story card.

### Rule 4 — Commit + push + notify after every story
```bash
git add -A
git commit -m "feat(PLANT-REDIS-1): [story title]"
git push origin feat/PLANT-REDIS-1-itN-eN

gh pr comment \
  $(gh pr list --head feat/PLANT-REDIS-1-it1-e1 --json number -q '.[0].number') \
  --body "✅ **[story-id] done** — $(git rev-parse --short HEAD)
Files changed: [list]
Tests: [T1 ✅ T2 ✅ ...]
Next: [next-story-id]"
```

### Rule 5 — Docker integration test after every epic
```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
exit_code=$?; docker compose -f docker-compose.test.yml down; exit $exit_code
```
Exit 0 → add `**Epic complete ✅**` under the epic heading, commit, push.
Non-zero → fix on same branch, retry. Max 3 attempts. Then: STUCK PROTOCOL.

### Rule 6 — STUCK PROTOCOL (3 failures = stop immediately)
```bash
git add -A && git commit -m "WIP: [story-id] blocked — [exact error]"
git push origin feat/PLANT-REDIS-1-itN-eN
gh pr create \
  --base main \
  --head feat/PLANT-REDIS-1-itN-eN \
  --title "WIP: [story-id] — blocked" \
  --draft \
  --body "Blocked on: [test name]
Error: [exact error message — paste in full]
Attempted fixes:
1. [what I tried]
2. [what I tried]"
```
Post the draft PR URL. **HALT. Do not start the next story.**

### Rule 7 — CHECKPOINT RULE

> **CHECKPOINT RULE**: After completing each epic (all tests passing), run:
> ```bash
> git add -A && git commit -m "feat([plan-id]): [epic-id] — [epic title]" && git push
> ```
> Do this BEFORE starting the next epic. If interrupted, completed epics are already saved.

### Rule 8 — Iteration PR (after ALL epics complete)
```bash
git checkout main && git pull
git checkout -b feat/PLANT-REDIS-1-it1
git merge --no-ff feat/PLANT-REDIS-1-it1-e1 feat/PLANT-REDIS-1-it1-e2 feat/PLANT-REDIS-1-it1-e3
git push origin feat/PLANT-REDIS-1-it1

gh pr create \
  --base main \
  --head feat/PLANT-REDIS-1-it1 \
  --title "feat(PLANT-REDIS-1): iteration 1 — managed redis foundation" \
  --body "## PLANT-REDIS-1 Iteration 1

### Stories completed
[paste tracking table rows for this iteration]

### Docker integration
All containers exited 0 ✅

### Live GCP validation
- Managed Redis instance exists and is READY
- Cloud Run services consume secret-backed REDIS_URL values
- Plant Redis runtime health endpoint reports ok

### NFR checklist
- [ ] waooaw_router() — no bare APIRouter
- [ ] GET routes use get_read_db_session() when applicable
- [ ] PIIMaskingFilter on all new loggers
- [ ] circuit_breaker on external HTTP calls preserved
- [ ] No env-specific Redis values in Dockerfile or code
- [ ] Redis secrets injected via Secret Manager only
- [ ] Tests >= 80% coverage on new backend code"
```
Post the PR URL in chat. **HALT.**

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | E1: Live Redis exists and every service has a secret-backed contract | Provision managed Redis by script and bootstrap service secrets | 🔴 Not Started | — |
| E1-S2 | 1 | E1: Live Redis exists and every service has a secret-backed contract | Replace hardcoded Redis wiring with Cloud Run secret references | 🔴 Not Started | — |
| E2-S1 | 1 | E2: Plant owns the reusable Redis runtime contract | Create shared Plant Redis runtime service | 🔴 Not Started | — |
| E2-S2 | 1 | E2: Plant owns the reusable Redis runtime contract | Add reusable Plant Redis runtime endpoints | 🔴 Not Started | — |
| E3-S1 | 1 | E3: Gateway and portals use the standard Redis path | Harden Plant Gateway Redis integration | 🔴 Not Started | — |
| E3-S2 | 1 | E3: Gateway and portals use the standard Redis path | Wire CP and PP to the standard Redis-backed surfaces | 🔴 Not Started | — |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

---

## Iteration 1 — Managed Redis On GCP And Standard Redis Runtime Reuse

**Scope:** WAOOAW gains one real managed Redis instance on GCP, one secret-backed Redis URL per service/DB index, reusable Plant runtime endpoints, and CP/PP service wiring that reuses standard Redis-backed behavior instead of local workarounds.
**Lane:** B — new backend/platform work required.
**⏱ Estimated:** 6h | **Come back:** 2026-04-01 16:00 IST
**Epics:** E1, E2, E3

### Dependency Map (Iteration 1)

```
E1-S1 ──► E1-S2
E2-S1 ──► E2-S2
E1-S2 ──► E3-S1
E2-S2 ──► E3-S2
E3-S1 ──► E3-S2
```

---

### Epic E1: Live Redis Exists And Every Service Has A Secret-Backed Contract

**Branch:** `feat/PLANT-REDIS-1-it1-e1`
**User story:** As a platform operator, I can create one managed Redis instance and inject service-specific Redis URLs through GCP secrets, so that WAOOAW no longer depends on a ghost private IP or image-baked config.

---

#### Story E1-S1: Provision Managed Redis By Script And Bootstrap Service Secrets

**BLOCKED UNTIL:** none
**Estimated time:** 60 min
**Branch:** `feat/PLANT-REDIS-1-it1-e1`
**CP BackEnd pattern:** N/A

**What to do (self-contained — read this card, then act):**
> `cloud/scripts/` currently has no Redis automation, while `src/Plant/BackEnd/INFRASTRUCTURE_DEPLOYMENT_GUIDE.md` lines 451–458 show the old manual `gcloud redis instances create plant-redis` path and `cloud/terraform/stacks/plant/environments/demo.tfvars` line 16 shows the active demo VPC is `projects/waooaw-oauth/global/networks/default`. Create one idempotent script at `cloud/scripts/provision-managed-redis.sh` that creates or reuses a Basic non-HA instance named `waooaw-redis-demo` in `asia-south1`, reads its host, and writes four Secret Manager secrets: `demo-plant-backend-redis-url`, `demo-plant-gateway-redis-url`, `demo-pp-backend-redis-url`, and `demo-cp-backend-redis-url` with DB indices `/0`, `/1`, `/2`, and `/3` respectively.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `cloud/scripts/cleanup-demo-cp.sh` | 1–120 | Existing shell style and repo script conventions |
| `src/Plant/BackEnd/INFRASTRUCTURE_DEPLOYMENT_GUIDE.md` | 447–460 | Old Redis creation command shape and naming history |
| `cloud/terraform/stacks/plant/environments/demo.tfvars` | 1–20 | Demo region and `private_network_id` value |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `cloud/scripts/provision-managed-redis.sh` | create | Create an idempotent bash script with `set -euo pipefail`, CLI flags for project/region/environment/network/instance name/tier/memory, create-or-describe logic for Redis, and secret upsert logic for the four service-specific Redis URL secrets. |

**Code patterns to copy exactly** (no other file reads needed for these):

```bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?required}"
REGION="${REGION:?required}"
ENVIRONMENT="${ENVIRONMENT:?required}"
REDIS_NAME="waooaw-redis-${ENVIRONMENT}"

HOST="$(gcloud redis instances describe "$REDIS_NAME" --region="$REGION" --project="$PROJECT_ID" --format='value(host)' 2>/dev/null || true)"
if [[ -z "$HOST" ]]; then
  gcloud redis instances create "$REDIS_NAME" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --network="default" \
    --tier=basic \
    --size=1 \
    --redis-version=redis_7_0
  HOST="$(gcloud redis instances describe "$REDIS_NAME" --region="$REGION" --project="$PROJECT_ID" --format='value(host)')"
fi

printf 'redis://%s:6379/0' "$HOST" | gcloud secrets versions add "${ENVIRONMENT}-plant-backend-redis-url" --data-file=- --project="$PROJECT_ID"
printf 'redis://%s:6379/1' "$HOST" | gcloud secrets versions add "${ENVIRONMENT}-plant-gateway-redis-url" --data-file=- --project="$PROJECT_ID"
printf 'redis://%s:6379/2' "$HOST" | gcloud secrets versions add "${ENVIRONMENT}-pp-backend-redis-url" --data-file=- --project="$PROJECT_ID"
printf 'redis://%s:6379/3' "$HOST" | gcloud secrets versions add "${ENVIRONMENT}-cp-backend-redis-url" --data-file=- --project="$PROJECT_ID"
```

**Acceptance criteria (binary pass/fail only):**
1. Running the script for demo creates or reuses exactly one Redis instance named `waooaw-redis-demo` in `asia-south1`.
2. The script creates or updates four Secret Manager secrets whose latest versions contain the same Redis host with DB indices `/0`, `/1`, `/2`, and `/3`.
3. Re-running the script is idempotent: it does not fail if the Redis instance or the secrets already exist.
4. The script never writes the Redis host or any full Redis URL into Terraform code, Dockerfiles, or committed `.env` files.
5. Every environment-specific Redis value created by the story is stored in GCP Secret Manager so the same image can promote unchanged from demo → uat → prod.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S1-T1 | `cloud/scripts/provision-managed-redis.sh` | Run `bash -n` | Script parses successfully |
| E1-S1-T2 | same | Run with `--help` or `--dry-run` mode | Usage text includes project/region/environment/network flags |
| E1-S1-T3 | same | Execute against demo with existing or empty state | `gcloud redis instances describe waooaw-redis-demo` returns a host |
| E1-S1-T4 | same | Read latest secret values after execution | Secrets resolve to `/0`, `/1`, `/2`, `/3` on the same host |

**Test command:**
```bash
bash -n cloud/scripts/provision-managed-redis.sh && \
bash cloud/scripts/provision-managed-redis.sh --project waooaw-oauth --region asia-south1 --environment demo --network projects/waooaw-oauth/global/networks/default --tier basic --memory-gb 1 --apply && \
gcloud redis instances describe waooaw-redis-demo --region asia-south1 --project waooaw-oauth --format='value(host)'
```

**Commit message:** `feat(PLANT-REDIS-1): provision managed redis by script and bootstrap secrets`

**Done signal (post as a comment then continue to E1-S2):**
`"E1-S1 done. Changed: cloud/scripts/provision-managed-redis.sh. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

---

#### Story E1-S2: Replace Hardcoded Redis Wiring With Cloud Run Secret References

**BLOCKED UNTIL:** E1-S1 committed to `feat/PLANT-REDIS-1-it1-e1`
**Estimated time:** 60 min
**Branch:** `feat/PLANT-REDIS-1-it1-e1`
**CP BackEnd pattern:** N/A

**What to do:**
> `cloud/terraform/stacks/plant/main.tf` lines 94–99 and 186–191 currently inject `REDIS_URL = var.redis_url`, and `cloud/terraform/stacks/plant/variables.tf` lines 60–64 hardcode `redis://10.0.0.3:6379/0`. `cloud/terraform/stacks/cp/main.tf` and `cloud/terraform/stacks/pp/main.tf` do not inject any `REDIS_URL` at all. Update the Plant, CP, and PP Cloud Run stacks so `REDIS_URL` is provided only through Secret Manager references to the four secrets created in E1-S1, delete the hardcoded Plant `redis_url` variable, and keep all environment-specific Redis values out of image code and plain Terraform env blocks.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `cloud/terraform/stacks/plant/main.tf` | 80–215 | Current Plant backend/gateway `env_vars` and `secrets` blocks |
| `cloud/terraform/stacks/cp/main.tf` | 40–102 | Current CP backend secret injection pattern |
| `cloud/terraform/stacks/pp/main.tf` | 40–75 | Current PP backend env and secret injection pattern |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `cloud/terraform/stacks/plant/main.tf` | modify | Remove `REDIS_URL = var.redis_url` from plain `env_vars`; add `REDIS_URL` to `secrets` for backend and gateway with `demo-plant-backend-redis-url` and `demo-plant-gateway-redis-url` naming derived from `var.environment`. |
| `cloud/terraform/stacks/plant/variables.tf` | modify | Delete the hardcoded `redis_url` variable from the stack so the Plant stack no longer carries a baked Redis host fallback. |
| `cloud/terraform/stacks/cp/main.tf` | modify | Add `REDIS_URL = "${var.environment}-cp-backend-redis-url:latest"` to the CP backend `secrets` block. |
| `cloud/terraform/stacks/pp/main.tf` | modify | Add `REDIS_URL = "${var.environment}-pp-backend-redis-url:latest"` to the PP backend `secrets` block. |

**Code patterns to copy exactly:**

```hcl
# Runtime secret injection only — no hardcoded Redis values in env_vars.
env_vars = {
  ENVIRONMENT = var.environment
  LOG_LEVEL   = "info"
}

secrets = {
  REDIS_URL = "${var.environment}-plant-gateway-redis-url:latest"
}
```

```text
Build once, promote unchanged:
- keep Docker images environment-agnostic
- inject Redis config at Cloud Run revision time
- keep full Redis URLs in Secret Manager, not in Terraform defaults
```

**Acceptance criteria:**
1. No Terraform file under `cloud/terraform/stacks/plant/` contains `redis://10.0.0.3:6379/0` or any other hardcoded Redis URL.
2. Plant BackEnd, Plant Gateway, CP BackEnd, and PP BackEnd all receive `REDIS_URL` through Secret Manager references, not `env_vars` literals.
3. The Plant stack no longer exposes `var.redis_url` as a baked input.
4. `terraform validate` passes for Plant, CP, and PP stacks after the changes.
5. The story keeps Redis values out of Terraform defaults and plain Cloud Run `env_vars`, using only secret references for environment-specific values.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S2-T1 | `cloud/terraform/stacks/plant/main.tf` | `terraform validate` | Plant stack validates |
| E1-S2-T2 | `cloud/terraform/stacks/cp/main.tf` | `terraform validate` | CP stack validates |
| E1-S2-T3 | `cloud/terraform/stacks/pp/main.tf` | `terraform validate` | PP stack validates |
| E1-S2-T4 | same files | grep for `10.0.0.3` and plain `REDIS_URL = var.redis_url` | No matches |

**Test command:**
```bash
terraform -chdir=cloud/terraform/stacks/plant init -backend=false && terraform -chdir=cloud/terraform/stacks/plant validate && \
terraform -chdir=cloud/terraform/stacks/cp init -backend=false && terraform -chdir=cloud/terraform/stacks/cp validate && \
terraform -chdir=cloud/terraform/stacks/pp init -backend=false && terraform -chdir=cloud/terraform/stacks/pp validate && \
! rg -n "10\.0\.0\.3|REDIS_URL\s*=\s*var\.redis_url" cloud/terraform/stacks
```

**Commit message:** `feat(PLANT-REDIS-1): move redis wiring to secret-backed cloud run refs`

**Done signal:** `"E1-S2 done. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

---

### Epic E2: Plant Owns The Reusable Redis Runtime Contract

**Branch:** `feat/PLANT-REDIS-1-it1-e2`
**User story:** As a backend and portal consumer, I can rely on one canonical Plant runtime Redis contract and API surface, so that CP, PP, and mobile do not reinvent Redis health, config, or invalidation logic.

---

#### Story E2-S1: Create Shared Plant Redis Runtime Service

**BLOCKED UNTIL:** none
**Estimated time:** 45 min
**Branch:** `feat/PLANT-REDIS-1-it1-e2`
**CP BackEnd pattern:** N/A

**What to do:**
> `src/Plant/BackEnd/main.py` lines 672–712 perform an ad hoc Redis `ping()` directly inside the readiness handler, which means Redis health logic has no reusable home. Create `src/Plant/BackEnd/services/redis_runtime.py` as the single Plant BackEnd owner for Redis client construction, namespace metadata, parsed DB-index reporting, health checks, and cache invalidation helpers, then refactor the readiness route in `main.py` to use that service instead of creating a raw Redis client inline.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/main.py` | 672–712 | Current deep readiness Redis check |
| `src/Plant/BackEnd/core/config.py` | 88–98 | Existing `redis_url` setting |
| `docs/CONTEXT_AND_INDEX.md` | 1228–1240 | Intended Redis DB ownership by service |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/services/redis_runtime.py` | create | Add a reusable async Redis runtime service exposing `get_client()`, `health_check()`, `effective_db_index()`, `namespace_catalog()`, and `invalidate(namespace, key)` helpers; keep all Redis URL parsing and ping logic inside this file. |
| `src/Plant/BackEnd/main.py` | modify | Replace the inline `aioredis.from_url(...).ping()` logic in `/health/ready` with the new service helper. |

**Code patterns to copy exactly:**

```python
import logging
from core.logging import PiiMaskingFilter

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())
```

```python
async def health_check() -> dict[str, str]:
    client = await get_client()
    await client.ping()
    return {"redis": "ok", "db_index": str(effective_db_index())}
```

**Acceptance criteria:**
1. Plant BackEnd has exactly one reusable service file that owns Redis client creation and health/config helpers.
2. `/health/ready` in Plant BackEnd uses the new service helper instead of constructing a raw Redis client inline.
3. The service reports the configured logical DB index from the runtime `REDIS_URL` without exposing the full URL.
4. New Plant BackEnd tests cover Redis health success, Redis failure, and DB-index parsing.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S1-T1 | `src/Plant/BackEnd/tests/unit/test_redis_runtime.py` | Fake Redis client ping succeeds | `health_check()` returns `redis=ok` |
| E2-S1-T2 | same | Fake Redis client ping raises | `health_check()` raises or returns error state as designed |
| E2-S1-T3 | same | `REDIS_URL=redis://host:6379/0` | `effective_db_index()` returns `0` |
| E2-S1-T4 | `src/Plant/BackEnd/tests/test_health_ready.py` | Patch runtime service | `/health/ready` uses helper result |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-backend-test \
  pytest src/Plant/BackEnd/tests/unit/test_redis_runtime.py src/Plant/BackEnd/tests/test_health_ready.py -v --cov=src/Plant/BackEnd/services/redis_runtime.py --cov-fail-under=80
```

**Commit message:** `feat(PLANT-REDIS-1): add shared plant redis runtime service`

**Done signal:** `"E2-S1 done. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

---

#### Story E2-S2: Add Reusable Plant Redis Runtime Endpoints

**BLOCKED UNTIL:** E2-S1 committed to `feat/PLANT-REDIS-1-it1-e2`
**Estimated time:** 60 min
**Branch:** `feat/PLANT-REDIS-1-it1-e2`
**CP BackEnd pattern:** N/A

**What to do:**
> Plant currently has no canonical runtime API for Redis health, config, or cache invalidation, which forces portal-specific workarounds. Create `src/Plant/BackEnd/api/v1/runtime_redis.py` and mount it from `src/Plant/BackEnd/api/v1/router.py` with three endpoints: `GET /api/v1/runtime/redis/health`, `GET /api/v1/runtime/redis/config`, and `POST /api/v1/runtime/redis/invalidate`; the first two must expose only safe operational metadata, and the invalidation endpoint must be an authenticated admin/governor surface that uses the shared Redis runtime service from E2-S1.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/api/v1/router.py` | 1–60 | Router include pattern |
| `src/Plant/BackEnd/services/redis_runtime.py` | 1–220 | Shared helper API from E2-S1 |
| `docs/CP/iterations/NFRReusable.md` | 69–114 | `waooaw_router()` and logging/audit route rules |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/api/v1/runtime_redis.py` | create | Add `waooaw_router(prefix="/runtime/redis", tags=["runtime-redis"])` plus the three endpoints described above; expose safe fields only (`status`, `db_index`, `service`, `namespaces`), never the full Redis URL. |
| `src/Plant/BackEnd/api/v1/router.py` | modify | Include the new `runtime_redis.router`. |
| `src/Plant/BackEnd/tests/api/test_runtime_redis.py` | create | Add route tests for health, config, and invalidate behavior. |

**Code patterns to copy exactly:**

```python
from core.routing import waooaw_router

router = waooaw_router(prefix="/runtime/redis", tags=["runtime-redis"])

@router.get("/health")
async def get_redis_health():
    return await redis_runtime.health_check()
```

```python
from core.logging import PiiMaskingFilter
import logging

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())
```

**Acceptance criteria:**
1. Plant exposes `GET /api/v1/runtime/redis/health` and `GET /api/v1/runtime/redis/config` through the main v1 router.
2. The response never returns the full `REDIS_URL`; only safe metadata like DB index, status, and namespace names are returned.
3. `POST /api/v1/runtime/redis/invalidate` reuses the shared runtime service and is restricted to the intended privileged role path.
4. New tests cover success and failure paths for all three endpoints.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S2-T1 | `src/Plant/BackEnd/tests/api/test_runtime_redis.py` | Mock health helper success | `/api/v1/runtime/redis/health` returns 200 |
| E2-S2-T2 | same | Mock config helper | `/api/v1/runtime/redis/config` returns DB index and namespaces only |
| E2-S2-T3 | same | Authenticated privileged caller posts invalidate | Response 200 and helper invoked |
| E2-S2-T4 | same | Non-privileged caller posts invalidate | Request rejected |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-backend-test \
  pytest src/Plant/BackEnd/tests/api/test_runtime_redis.py -v --cov=src/Plant/BackEnd/api/v1/runtime_redis.py --cov-fail-under=80
```

**Commit message:** `feat(PLANT-REDIS-1): add plant redis runtime endpoints`

**Done signal:** `"E2-S2 done. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

---

### Epic E3: Gateway And Portals Use The Standard Redis Path

**Branch:** `feat/PLANT-REDIS-1-it1-e3`
**User story:** As a customer or operator, I can use WAOOAW flows without paying a ghost Redis timeout or file-backed workaround penalty, because Gateway, CP, and PP all use the standard managed Redis path.

---

#### Story E3-S1: Harden Plant Gateway Redis Integration

**BLOCKED UNTIL:** E1-S2 committed to `feat/PLANT-REDIS-1-it1-e1`
**Estimated time:** 75 min
**Branch:** `feat/PLANT-REDIS-1-it1-e3`
**CP BackEnd pattern:** N/A

**What to do:**
> `src/Plant/Gateway/middleware/auth.py` lines 44–52 create a raw module-level Redis client directly from `REDIS_URL`, and `src/Plant/Gateway/middleware/budget.py` lines 128–145 and 261–280 construct the client with 2 second timeouts and then perform a post-response Redis write that still stalls user-facing latency when the private path is broken. Create one shared Gateway Redis helper in `src/Plant/Gateway/services/redis_runtime.py`, move auth and budget middleware to it, and change the budget update path so the request no longer pays the full Redis timeout cost while still logging and degrading safely.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/Gateway/middleware/auth.py` | 40–70 | Current gateway Redis singleton |
| `src/Plant/Gateway/middleware/budget.py` | 120–320 | Raw Redis client and post-response write path |
| `docs/CP/iterations/NFRReusable.md` | 129–166 | Circuit breaker and logging rules to preserve |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/Gateway/services/redis_runtime.py` | create | Add the Gateway-owned Redis helper for client creation, timeout configuration, DB-index reporting, and `enqueue_budget_update()` / `mark_token_revoked()` style helpers. |
| `src/Plant/Gateway/middleware/auth.py` | modify | Replace `_get_gateway_redis()` with the shared helper. |
| `src/Plant/Gateway/middleware/budget.py` | modify | Replace inline Redis client creation with the shared helper and remove the user-visible 2 second synchronous stall from the post-response budget update path. |

**Code patterns to copy exactly:**

```python
logger = logging.getLogger(__name__)
logger.addFilter(PIIMaskingFilter())
```

```python
try:
    await redis_runtime.enqueue_budget_update(agent_id, customer_id, cost)
except Exception as exc:
    logger.error("Failed to update budget in Redis: %s", exc)
```

**Acceptance criteria:**
1. Plant Gateway auth and budget middleware no longer create their own raw Redis clients directly.
2. The gateway budget update path no longer adds a full 2 second delay to user-facing requests when Redis is unavailable.
3. Gateway still degrades safely: auth and budget failures are logged with masked output and do not crash the process.
4. New Gateway tests cover successful Redis use and degraded Redis-unavailable behavior.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S1-T1 | `src/Plant/Gateway/tests/test_redis_runtime.py` | Fake Redis ping/update success | Helper returns connected client/state |
| E3-S1-T2 | same | Fake Redis connect timeout | Helper degrades without raising through middleware surface |
| E3-S1-T3 | `src/Plant/Gateway/tests/test_budget_middleware.py` | Mock unavailable Redis | Request completes without 2 second blocking path |
| E3-S1-T4 | `src/Plant/Gateway/tests/test_auth_middleware.py` | Mock shared helper | Revocation path uses helper |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-gateway-test \
  pytest src/Plant/Gateway/tests/test_redis_runtime.py src/Plant/Gateway/tests/test_budget_middleware.py src/Plant/Gateway/tests/test_auth_middleware.py -v --cov=src/Plant/Gateway/services/redis_runtime.py --cov-fail-under=80
```

**Commit message:** `feat(PLANT-REDIS-1): harden plant gateway redis integration`

**Done signal:** `"E3-S1 done. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

---

#### Story E3-S2: Wire CP And PP To The Standard Redis-Backed Surfaces

**BLOCKED UNTIL:** E2-S2 and E3-S1 committed to `main`-bound branches
**Estimated time:** 60 min
**Branch:** `feat/PLANT-REDIS-1-it1-e3`
**CP BackEnd pattern:** B — create new `api/cp_runtime_redis.py` thin proxy for Plant runtime Redis endpoints; keep local auth business rules in CP.

**What to do:**
> `src/CP/BackEnd/services/cp_refresh_revocations.py` lines 1–94 still use a file-backed JSONL store and `src/CP/BackEnd/api/auth/routes.py` comments still say “use Redis in production”. `src/PP/BackEnd/services/ops_cache.py` already supports Redis but `cloud/terraform/stacks/pp/main.tf` does not inject `REDIS_URL`. Replace CP’s revocation store with a Redis-backed implementation keyed to DB `/3`, add `src/CP/BackEnd/api/cp_runtime_redis.py` as a thin proxy to the new Plant runtime Redis endpoints using `PlantGatewayClient`, and ensure PP’s ops cache becomes live once the new `REDIS_URL` secret wiring from E1-S2 is present.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/BackEnd/services/cp_refresh_revocations.py` | 1–94 | File-backed revocation store to replace |
| `src/CP/BackEnd/services/plant_gateway_client.py` | 1–82 | Existing CP thin-proxy client with circuit breaker |
| `src/PP/BackEnd/services/ops_cache.py` | 1–118 | Existing optional Redis cache path |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/BackEnd/services/cp_refresh_revocations.py` | modify | Replace the file-backed store with a Redis-backed store implementation that keeps the same public interface (`revoke_user`, `revoked_at_for_user`, `is_refresh_token_revoked`) and reads `REDIS_URL` from runtime config. |
| `src/CP/BackEnd/api/cp_runtime_redis.py` | create | Add thin CP proxy routes for `GET /cp/runtime/redis/health` and `GET /cp/runtime/redis/config`, delegating to the Plant runtime endpoints via `PlantGatewayClient`. |
| `src/CP/BackEnd/main.py` | modify | Include the new `cp_runtime_redis.router`. |
| `src/CP/BackEnd/api/auth/routes.py` | modify | Keep logout/refresh logic intact but switch it to the Redis-backed revocation store dependency. |
| `src/PP/BackEnd/services/ops_cache.py` | modify | Keep graceful degradation but add one successful connection test path and masked logging now that PP has a real `REDIS_URL` secret. |

**Code patterns to copy exactly:**

```python
from core.routing import waooaw_router
from services.plant_gateway_client import PlantGatewayClient

router = waooaw_router(prefix="/cp/runtime/redis", tags=["cp-runtime-redis"])

@router.get("/health")
async def get_redis_health():
    client = PlantGatewayClient(base_url=_plant_base_url())
    resp = await client.request_json(method="GET", path="/api/v1/runtime/redis/health")
    return resp.json
```

```python
import logging
from core.logging import PiiMaskingFilter

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())
```

**Acceptance criteria:**
1. CP refresh-token revocation no longer depends on a local JSONL file when `REDIS_URL` is configured.
2. CP exposes thin proxy endpoints for Plant runtime Redis health and config, with no Redis business logic added to CP.
3. PP ops cache connects successfully when `REDIS_URL` is present and still degrades safely when Redis is unavailable.
4. New CP and PP tests cover the Redis-backed paths and the no-Redis fallback paths.
5. No CP or PP code path introduces a baked Redis hostname, DB index, or environment-specific value in source or image config.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S2-T1 | `src/CP/BackEnd/tests/test_cp_refresh_revocations.py` | Mock Redis client | `revoke_user` and `is_refresh_token_revoked` use Redis store |
| E3-S2-T2 | `src/CP/BackEnd/tests/test_cp_runtime_redis.py` | Mock `PlantGatewayClient.request_json` | `/cp/runtime/redis/health` returns proxied payload |
| E3-S2-T3 | `src/PP/BackEnd/tests/test_ops_cache.py` | Provide `REDIS_URL` and fake Redis client | Cache connect/get/set succeeds |
| E3-S2-T4 | same PP test file | Redis unavailable | Cache still degrades without failing route code |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run cp-test \
  pytest src/CP/BackEnd/tests/test_cp_refresh_revocations.py src/CP/BackEnd/tests/test_cp_runtime_redis.py -v && \
docker compose -f docker-compose.test.yml run pp-test \
  pytest src/PP/BackEnd/tests/test_ops_cache.py -v --cov=src/PP/BackEnd/services/ops_cache.py --cov-fail-under=80
```

**Commit message:** `feat(PLANT-REDIS-1): wire cp and pp to redis-backed runtime surfaces`

**Done signal:** `"E3-S2 done. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`
