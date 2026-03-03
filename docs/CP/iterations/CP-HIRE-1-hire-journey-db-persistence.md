# CP-HIRE-1 — Hire Journey DB Persistence on GCP

> **Template version**: 2.0

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `CP-HIRE-1` |
| Feature area | Customer Portal — Hire Journey: full DB persistence on GCP |
| Created | 2026-03-03 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CONTEXT_AND_INDEX.md` §6 (service communication) + `docs/CP/iterations/CP-SKILLS-2-goal-config-persistence.md` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 2 |
| Total epics | 2 |
| Total stories | 2 |

---

## Zero-Cost Agent Constraints (READ FIRST)

This plan is designed for **autonomous zero-cost model agents** (Gemini Flash, GPT-4o-mini, etc.)
with limited context windows. Every structural decision in this plan exists to preserve context.

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is fully self-contained — no cross-references, no "see above" |
| No working memory across files | NFR code patterns are embedded **inline** in each story — agent never opens NFRReusable.md |
| No planning ability | Stories are atomic — one deliverable, one set of files, one test command |
| Token cost per file read | Max 3 files to read per story — pre-identified by PM in the card |
| Binary inference only | Acceptance criteria are pass/fail — no judgment calls required from the agent |

> **Agent:** Execute exactly ONE story at a time. Read your assigned story card fully, then act.
> Do NOT read other stories. Do NOT open NFRReusable.md. All patterns you need are in your card.
> Do NOT read files not listed in your story card's "Files to read first" section.

---

## PM Review Checklist

- [x] **EXPERT PERSONAS filled** — each iteration's agent task block has the correct expert persona list
- [x] Epic titles name customer outcomes, not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR code snippets inline — no "see NFRReusable.md"
- [x] Every story card has max 3 files in "Files to read first"
- [x] Every story involving CP BackEnd states the exact pattern: A, B, or C
- [x] Every new backend route story embeds the `waooaw_router()` snippet
- [x] Every GET route story card says `get_read_db_session()` not `get_db_session()`
- [x] Every story that adds env vars lists the exact Terraform file paths to update
- [x] Every story has `BLOCKED UNTIL` (or "none")
- [x] Each iteration has a time estimate and come-back datetime
- [x] Each iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] Stories sequenced: backend before infrastructure
- [x] No placeholders remain

---

## Background — What Already Exists (Do NOT re-implement)

This plan has a carefully scoped gap. Most of the hire journey is already built and
DB-backed. **Read this table before writing a single line of code.**

### Plant BackEnd — already DB-backed (PERSISTENCE_MODE=db is the default)

| Route | File | Status |
|---|---|---|
| `PUT /api/v1/hired-agents/draft` | `hired_agents_simple.py` | ✅ Live, persists to `hired_agents` table |
| `GET /api/v1/hired-agents/by-subscription/{id}` | `hired_agents_simple.py` | ✅ Live, reads from `hired_agents` table |
| `POST /api/v1/hired-agents/{id}/finalize` | `hired_agents_simple.py` | ✅ Live, writes trial state to DB |
| `POST /api/v1/payments/razorpay/order` | `payments_simple.py` | ✅ Live, persists subscription via `SubscriptionRepository` |
| `POST /api/v1/payments/razorpay/confirm` | `payments_simple.py` | ✅ Live, verifies Razorpay signature |
| `GET /api/v1/payments/subscriptions/by-customer/{id}` | `payments_simple.py` | ✅ Live |
| `POST /api/v1/payments/subscriptions/{id}/cancel` | `payments_simple.py` | ✅ Live |

### CP BackEnd — feature-flagged proxy routes

| Route | File | Proxy status |
|---|---|---|
| `PUT /cp/hire/wizard/draft` | `hire_wizard.py` | ✅ Plant proxy exists, gated by `CP_HIRE_USE_PLANT` |
| `POST /cp/hire/wizard/finalize` | `hire_wizard.py` | ✅ Plant proxy exists, gated by `CP_HIRE_USE_PLANT` |
| `GET /cp/hire/wizard/by-subscription/{id}` | `hire_wizard.py` | ❌ **No Plant proxy — always reads in-memory dict** |
| `GET /cp/subscriptions/` | `subscriptions.py` | ✅ Plant proxy gated by `CP_SUBSCRIPTIONS_USE_PLANT` |
| `POST /cp/subscriptions/{id}/cancel` | `subscriptions.py` | ✅ Plant proxy gated by `CP_SUBSCRIPTIONS_USE_PLANT` |

### Terraform — env vars already set on GCP

| Env var | Stack | File | Status |
|---|---|---|---|
| `CP_PAYMENTS_USE_PLANT = "true"` | CP backend | `cloud/terraform/stacks/cp/main.tf:74` | ✅ Set |
| `CP_SUBSCRIPTIONS_USE_PLANT = "true"` | CP backend | `cloud/terraform/stacks/cp/main.tf:75` | ✅ Set |
| `CP_HIRE_USE_PLANT` | CP backend | `cloud/terraform/stacks/cp/main.tf` | ❌ **Missing — defaults to "false"** |
| `PAYMENTS_MODE` | Plant backend | `cloud/terraform/stacks/plant/main.tf` | ❌ **Missing — defaults to "coupon"** |
| `RAZORPAY_KEY_ID` | Plant backend | `cloud/terraform/stacks/plant/main.tf` | ❌ **Missing from secrets block** |
| `RAZORPAY_KEY_SECRET` | Plant backend | `cloud/terraform/stacks/plant/main.tf` | ❌ **Missing from secrets block** |

---

## Problem Statement

Three specific gaps prevent the hire journey from persisting to the GCP SQL DB:

1. **CP BackEnd code bug:** `GET /cp/hire/wizard/by-subscription/{id}` has no Plant proxy path.
   When `CP_HIRE_USE_PLANT=true`, every `draft → GET` round-trip would return 404 because the
   route only reads from an in-memory dict.

2. **Terraform CP flag missing:** `CP_HIRE_USE_PLANT` is absent from the CP backend Cloud Run
   env_vars block. Without it the CP BackEnd falls back to in-memory drafts on every container
   restart — losing all hire progress.

3. **Terraform Plant flags missing:** `PAYMENTS_MODE` is absent from the Plant backend Cloud Run
   env_vars block (defaults to `"coupon"`). Razorpay keys are not injected via Secret Manager,
   so real payment confirmation fails with a 500 (missing env var).

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane B — CP BackEnd: fix GET proxy + tests | 1 | 1 | ~45m | Start + 1h |
| 2 | Terraform: activate hire flags + Razorpay on GCP | 1 | 1 | ~45m | Start + 1h |

**Estimate basis:** Fix existing route = 20 min | Tests (2 cases) = 15 min | PR = 10 min.
Terraform env var addition = 20 min | Secrets block = 10 min | Plan =15 min | PR = 10 min.
Add 20% buffer for zero-cost model context loading.

---

## Story Tracking Table

| Story ID | Title | Status | Branch |
|---|---|---|---|
| E1-S1 | CP BackEnd: add Plant proxy for GET by-subscription | 🔲 Not started | `feat/CP-HIRE-1-it1-e1` |
| E2-S1 | Terraform: activate CP_HIRE_USE_PLANT + Razorpay on GCP | 🔲 Not started | `feat/CP-HIRE-1-it2-e2` |

---

## How to Launch Each Iteration

### Iteration 1

**Pre-flight check (run in terminal before launching):**
```bash
git fetch origin && git log --oneline origin/main | head -3
git status
# Must show: nothing to commit, working tree clean on main
```

**Steps to launch:**
1. Open VS Code
2. Open Copilot Chat: `Ctrl+Alt+I` (Windows/Linux) or `Cmd+Alt+I` (Mac)
3. Click the model dropdown at the top of the chat panel → select **Agent mode**
4. Click `+` to start a new agent session
5. Type `@` in the message box → select **platform-engineer** from the dropdown
6. Copy the block below and paste into the message box → press **Enter**
7. Go away. Come back in 1h.

**Iteration 1 agent task** (paste verbatim — do not modify):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / httpx engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior Python 3.11/FastAPI/httpx engineer, I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-HIRE-1-hire-journey-db-persistence.md
YOUR SCOPE: Iteration 1 only — Epic E1. Do not touch Iteration 2 content.
TIME BUDGET: 1h. If you reach 1h 30m without finishing, follow STUCK PROTOCOL now.

EXECUTION ORDER:
1. Run: git status && git log --oneline -3
   You must be on main with a clean tree. If not, post why and HALT.
2. Read the "Agent Execution Rules" section in this plan file.
3. Read the "Iteration 1" section in this plan file. Read nothing else.
4. Execute Epic E1: E1-S1 only.
5. When docker-tested, open the iteration PR. Post the PR URL. HALT.
```

**Come back at:** Start + 1h

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Verify merge first:**
```bash
git fetch origin && git log --oneline origin/main | head -3
# Must show: feat(CP-HIRE-1): iteration 1 — CP BackEnd GET hire proxy
```

**Steps to launch:** same as Iteration 1 (VS Code → Copilot Chat → Agent mode → platform-engineer)

**Iteration 2 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Terraform / GCP Cloud Run engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior Terraform/GCP Cloud Run engineer, I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-HIRE-1-hire-journey-db-persistence.md
YOUR SCOPE: Iteration 2 only — Epic E2. Do not touch Iteration 1 content.
TIME BUDGET: 1h. If you reach 1h 30m without finishing, follow STUCK PROTOCOL now.

PREREQUISITE CHECK (do before anything else):
  Run: git log --oneline origin/main | head -5
  Must show: feat(CP-HIRE-1): iteration 1 — CP BackEnd GET hire proxy
  If not: post "Blocked: Iteration 1 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 2" sections. Read nothing else.
3. Execute Epic E2: E2-S1 only.
4. When done, open the iteration PR. Post the PR URL. HALT.
```

**Come back at:** Start + 1h

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all instructions.

### Rule -1 — Activate Expert Personas (first thing, before Rule 0)

Read the `EXPERT PERSONAS:` field from the task you were given.
Activate each persona now. For every epic you execute, open with one line:

> *"Acting as a [persona], I will [what you're building] by [approach]."*

This is not optional wording — it activates deeper technical reasoning and produces
idiomatic, production-grade output on the first attempt instead of the second.

| Technology area | Expert persona to activate |
|---|---|
| `src/CP/BackEnd/` | Senior Python 3.11 / FastAPI / httpx engineer |
| `cloud/terraform/` | Senior Terraform / GCP Cloud Run engineer |

---

### Rule 0 — Open tracking draft PR first (before writing any code)

```bash
git checkout main && git pull
git checkout -b feat/CP-HIRE-1-it1-e1
git commit --allow-empty -m "chore(CP-HIRE-1): start iteration 1"
git push origin feat/CP-HIRE-1-it1-e1
gh pr create \
  --base main \
  --head feat/CP-HIRE-1-it1-e1 \
  --draft \
  --title "tracking: CP-HIRE-1 Iteration 1 — in progress" \
  --body "## tracking: CP-HIRE-1 Iteration 1

Subscribe to this PR to receive one notification per story completion.

### Stories
- [ ] [E1-S1] CP BackEnd: add Plant proxy for GET by-subscription

_Live updates posted as comments below ↓_"
```

---

### Rule 1 — Branch discipline
One epic = one branch: `feat/CP-HIRE-1-itN-eN`.
All stories in one epic commit to the same branch sequentially.
Never push to `main` directly.

### Rule 2 — Scope lock
Implement exactly the acceptance criteria in the story card.
Do not refactor other parts of `hire_wizard.py`. Do not gold-plate.
If you notice a bug outside your scope: add a TODO comment and move on.

### Rule 3 — Tests before the next story
Write every test in the story's test table before advancing.
Run the test command listed in the story card — not a generic command.

### Rule 4 — Commit + push + notify after every story
```bash
git add -A
git commit -m "feat(CP-HIRE-1): [story title]"
git push origin feat/CP-HIRE-1-itN-eN

git add docs/CP/iterations/CP-HIRE-1-hire-journey-db-persistence.md
git commit -m "docs(CP-HIRE-1): mark [story-id] done"
git push origin feat/CP-HIRE-1-itN-eN

gh pr comment \
  $(gh pr list --head feat/CP-HIRE-1-it1-e1 --json number -q '.[0].number') \
  --body "✅ **[story-id] done** — $(git rev-parse --short HEAD)
Files changed: [list]
Tests: [T1 ✅ T2 ✅]
Next: [next or DONE]"
```

### Rule 5 — Docker integration test after every epic
```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
```
All containers must exit 0. Do NOT open the PR until this passes.

### Rule 6 — Coverage gate
```bash
docker compose -f docker-compose.test.yml run cp-test \
  pytest --cov=app --cov-fail-under=80 src/CP/BackEnd/tests/test_hire_wizard_routes.py -v
```
Must show ≥ 80% for `hire_wizard.py`. If below 80%, add tests until it passes.

### Rule 7 — Open the iteration PR (not the tracking draft PR)
```bash
gh pr create \
  --base main \
  --head feat/CP-HIRE-1-itN-eN \
  --title "feat(CP-HIRE-1): iteration N — [one-line summary]" \
  --body "## Summary
[What this iteration does in 2 sentences]

## Stories completed
- [x] E1-S1 — [title]

## Test evidence
[paste docker test output last 10 lines]

## Checklist
- [ ] All tests pass
- [ ] Coverage ≥ 80%
- [ ] No hardcoded credentials
- [ ] No commented-out code"
```

### STUCK PROTOCOL

If you have spent more than your TIME BUDGET, or are blocked for more than 15 minutes:

1. Commit all work-in-progress: `git add -A && git commit -m "wip(CP-HIRE-1): [story-id] — blocked: [reason]"`
2. Push: `git push origin feat/CP-HIRE-1-itN-eN`
3. Open a DRAFT PR titled `WIP: CP-HIRE-1 [story-id] — [blocker]`
4. Post one comment: "Stuck: [exact error message or question]. Waiting for human input."
5. HALT — do not attempt to work around the blocker by guessing.

---

## Iteration 1 — Epic E1: Customer hire draft persists correctly through the GET round-trip

> Plant BackEnd already has `GET /api/v1/hired-agents/by-subscription/{id}` (DB-backed).
> CP BackEnd `GET /cp/hire/wizard/by-subscription/{id}` never calls Plant — it silently returns
> stale in-memory data. Fix: add the Plant proxy path, guarded by `CP_HIRE_USE_PLANT`.

---

### E1-S1 — CP BackEnd: add Plant proxy for GET `/cp/hire/wizard/by-subscription/{id}`

| Field | Value |
|---|---|
| Branch | `feat/CP-HIRE-1-it1-e1` |
| Pattern | B — modify existing file `hire_wizard.py` (append Plant proxy path to existing GET route) |
| Story size | 45m |
| BLOCKED UNTIL | none |

**Files to read first (max 3):**
1. `src/CP/BackEnd/api/hire_wizard.py` — read entire file (250 lines) to understand current structure
2. `src/CP/BackEnd/tests/test_hire_wizard_routes.py` — read entire file (122 lines) to copy monkeypatch test pattern
3. *(no third file needed)*

**Exact problem to fix:**

The current GET route at line 177–193 of `hire_wizard.py`:
```python
@router.get("/by-subscription/{subscription_id}", response_model=HireWizardResponse)
async def get_by_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user),
) -> HireWizardResponse:
    _ = current_user

    stored = _drafts_by_subscription.get(subscription_id)
    if not stored:
        raise HTTPException(status_code=404, detail="Wizard draft not found")
    return stored
```

This route **has no Plant proxy path at all**. When `CP_HIRE_USE_PLANT=true`, customer refreshes
the page → CP reads in-memory dict → 404 (dict wiped on restart) or stale data.

**What to build:**

Add a `_plant_get_by_subscription` helper function (parallel to the existing `_plant_upsert_draft`
and `_plant_finalize` helpers already in the file), then add the Plant proxy branch to the route.

**Code pattern — helper function to add** (place after `_plant_finalize`, before the `@router.put` block):

```python
async def _plant_get_by_subscription(
    *,
    subscription_id: str,
    authorization: str | None,
) -> dict:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base_url:
        raise RuntimeError("PLANT_GATEWAY_URL not configured")

    headers: dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{base_url}/api/v1/hired-agents/by-subscription/{subscription_id}",
            headers=headers,
        )

    if resp.status_code >= 400:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Plant get by-subscription failed ({resp.status_code})",
        )
    return resp.json()
```

**Code pattern — updated route** (replace the existing `get_by_subscription` route entirely):

```python
@router.get("/by-subscription/{subscription_id}", response_model=HireWizardResponse)
async def get_by_subscription(
    subscription_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> HireWizardResponse:
    _ = current_user
    authorization = request.headers.get("Authorization")

    if _bool_env("CP_HIRE_USE_PLANT", "false"):
        try:
            plant = await _plant_get_by_subscription(
                subscription_id=subscription_id,
                authorization=authorization,
            )
            return HireWizardResponse(
                hired_instance_id=plant["hired_instance_id"],
                subscription_id=plant["subscription_id"],
                agent_id=plant["agent_id"],
                agent_type_id=plant.get("agent_type_id") or "",
                nickname=plant.get("nickname"),
                theme=plant.get("theme"),
                config=plant.get("config") or {},
                configured=bool(plant.get("configured")),
                goals_completed=bool(plant.get("goals_completed")),
                subscription_status=plant.get("subscription_status"),
                trial_status=plant.get("trial_status") or "not_started",
                trial_start_at=plant.get("trial_start_at"),
                trial_end_at=plant.get("trial_end_at"),
            )
        except RuntimeError:
            pass  # Fall through to CP-local dict

    stored = _drafts_by_subscription.get(subscription_id)
    if not stored:
        raise HTTPException(status_code=404, detail="Wizard draft not found")
    return stored
```

> **Important**: The updated route adds `request: Request` as a parameter (to forward the
> Authorization header to Plant). The existing import `from fastapi import Depends, HTTPException, Request`
> already includes `Request` — no new import needed.

**Acceptance criteria:**

| # | Check | Pass condition |
|---|---|---|
| AC-1 | `CP_HIRE_USE_PLANT=false` (default) | GET reads from in-memory dict, returns stored draft |
| AC-2 | `CP_HIRE_USE_PLANT=true`, Plant returns 200 | GET returns Plant response, not in-memory dict |
| AC-3 | `CP_HIRE_USE_PLANT=true`, Plant returns 404 | GET returns 404 to caller |
| AC-4 | `CP_HIRE_USE_PLANT=true`, PLANT_GATEWAY_URL unset | RuntimeError caught → falls through to in-memory dict |

**Tests to write** (add to `src/CP/BackEnd/tests/test_hire_wizard_routes.py`):

```python
def test_hire_wizard_get_by_subscription_delegates_to_plant(client, auth_headers, monkeypatch):
    """AC-2: When CP_HIRE_USE_PLANT=true, GET by-subscription proxies to Plant."""
    monkeypatch.setenv("CP_HIRE_USE_PLANT", "true")
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")

    from api import hire_wizard as hire_wizard_api

    async def _fake_plant_get_by_subscription(*, subscription_id: str, authorization):
        assert subscription_id == "SUB-plant-get"
        assert authorization and authorization.startswith("Bearer ")
        return {
            "hired_instance_id": "HAI-plant-get-1",
            "subscription_id": "SUB-plant-get",
            "agent_id": "agent-999",
            "agent_type_id": "marketing.digital_marketing.v1",
            "nickname": "MyAgent",
            "theme": "light",
            "config": {"k": "v"},
            "configured": True,
            "goals_completed": False,
            "subscription_status": "active",
            "trial_status": "active",
            "trial_start_at": "2026-03-01T00:00:00Z",
            "trial_end_at": "2026-03-08T00:00:00Z",
        }

    monkeypatch.setattr(hire_wizard_api, "_plant_get_by_subscription", _fake_plant_get_by_subscription)

    r = client.get("/api/cp/hire/wizard/by-subscription/SUB-plant-get", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["hired_instance_id"] == "HAI-plant-get-1"
    assert body["trial_status"] == "active"
    assert body["trial_start_at"] == "2026-03-01T00:00:00Z"
    assert body["config"]["k"] == "v"


def test_hire_wizard_get_by_subscription_plant_404_propagates(client, auth_headers, monkeypatch):
    """AC-3: When Plant returns 404, the 404 is propagated to the caller."""
    monkeypatch.setenv("CP_HIRE_USE_PLANT", "true")
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway")

    from api import hire_wizard as hire_wizard_api
    from fastapi import HTTPException as FastAPIHTTPException

    async def _fake_plant_get_by_subscription(*, subscription_id: str, authorization):
        raise FastAPIHTTPException(status_code=404, detail="Plant get by-subscription failed (404)")

    monkeypatch.setattr(hire_wizard_api, "_plant_get_by_subscription", _fake_plant_get_by_subscription)

    r = client.get("/api/cp/hire/wizard/by-subscription/SUB-missing", headers=auth_headers)
    assert r.status_code == 404
```

**Test command (run exactly this):**
```bash
docker compose -f docker-compose.test.yml run cp-test \
  pytest src/CP/BackEnd/tests/test_hire_wizard_routes.py -v
```
All 5 tests (3 existing + 2 new) must pass. Zero failures.

**Commit message:**
```
feat(CP-HIRE-1): add Plant proxy for GET hire wizard by-subscription
```

---

## Iteration 2 — Epic E2: Hire journey is live on GCP (Terraform flags + Razorpay secrets)

> With E1-S1 merged, the CP BackEnd code is complete. The only thing preventing full DB
> persistence on GCP is: (a) `CP_HIRE_USE_PLANT` not set to `"true"` in CP Terraform, and
> (b) `PAYMENTS_MODE` + Razorpay secret keys missing from Plant Terraform. This story fixes both.

---

### E2-S1 — Terraform: add `CP_HIRE_USE_PLANT` to CP stack + `PAYMENTS_MODE` + Razorpay to Plant stack

| Field | Value |
|---|---|
| Branch | `feat/CP-HIRE-1-it2-e2` |
| Story size | 45m |
| BLOCKED UNTIL | E1-S1 merged to main |

**Files to read first (max 3):**
1. `cloud/terraform/stacks/cp/main.tf` — lines 55–100 (the `module "cp_backend"` env_vars block)
2. `cloud/terraform/stacks/plant/main.tf` — lines 85–135 (the `module "plant_backend"` env_vars + secrets block)
3. *(no third file needed)*

**Change 1 — CP stack: add `CP_HIRE_USE_PLANT = "true"`**

File: `cloud/terraform/stacks/cp/main.tf`

Find the block:
```hcl
    # Route payments + subscription reads through Plant (persistent DB).
    # Without these, CP uses an in-memory stub that is wiped on every container
    # restart, causing My Agents to show 0 after any deployment.
    CP_PAYMENTS_USE_PLANT      = "true"
    CP_SUBSCRIPTIONS_USE_PLANT = "true"
```

Replace with:
```hcl
    # Route payments + subscription reads + hire wizard through Plant (persistent DB).
    # Without these, CP uses in-memory stubs that are wiped on every container
    # restart, losing hire wizard drafts and subscription history.
    CP_PAYMENTS_USE_PLANT      = "true"
    CP_SUBSCRIPTIONS_USE_PLANT = "true"
    CP_HIRE_USE_PLANT          = "true"
```

**Change 2 — Plant stack: add `PAYMENTS_MODE` env var**

File: `cloud/terraform/stacks/plant/main.tf`

Find the env_vars block for `module "plant_backend"` which ends with:
```hcl
    EMAIL_PROVIDER  = "smtp"
    SMTP_HOST       = var.smtp_host
    SMTP_PORT       = var.smtp_port
    SMTP_FROM_EMAIL = var.smtp_from_email
  }
```

Replace with:
```hcl
    EMAIL_PROVIDER  = "smtp"
    SMTP_HOST       = var.smtp_host
    SMTP_PORT       = var.smtp_port
    SMTP_FROM_EMAIL = var.smtp_from_email

    # Payment mode: "razorpay" enables real Razorpay checkout + signature verification.
    # "coupon" is the in-memory stub — never use in prod (Plant will 500 if env=production).
    PAYMENTS_MODE = var.environment == "prod" ? "razorpay" : "coupon"
  }
```

**Change 3 — Plant stack: add Razorpay keys to secrets block**

File: `cloud/terraform/stacks/plant/main.tf`

Find the secrets block for `module "plant_backend"`:
```hcl
  secrets = var.attach_secret_manager_secrets ? merge(
    {
      GOOGLE_CLIENT_ID     = "GOOGLE_CLIENT_ID:latest"
      GOOGLE_CLIENT_SECRET = "GOOGLE_CLIENT_SECRET:latest"
      JWT_SECRET           = "JWT_SECRET:latest"
      SMTP_USERNAME        = "${var.smtp_username_secret}:latest"
      SMTP_PASSWORD        = "${var.smtp_password_secret}:latest"
    },
    {
      DATABASE_URL = "${module.plant_database.database_url_secret_id}:latest"
    }
    ) : {
    DATABASE_URL = "${module.plant_database.database_url_secret_id}:latest"
  }
```

Replace with:
```hcl
  secrets = var.attach_secret_manager_secrets ? merge(
    {
      GOOGLE_CLIENT_ID     = "GOOGLE_CLIENT_ID:latest"
      GOOGLE_CLIENT_SECRET = "GOOGLE_CLIENT_SECRET:latest"
      JWT_SECRET           = "JWT_SECRET:latest"
      SMTP_USERNAME        = "${var.smtp_username_secret}:latest"
      SMTP_PASSWORD        = "${var.smtp_password_secret}:latest"
      # Razorpay keys — required when PAYMENTS_MODE=razorpay (prod + uat environments).
      # Store in GCP Secret Manager before deploying: gcloud secrets create RAZORPAY_KEY_ID --data-file=<file>
      RAZORPAY_KEY_ID     = "RAZORPAY_KEY_ID:latest"
      RAZORPAY_KEY_SECRET = "RAZORPAY_KEY_SECRET:latest"
    },
    {
      DATABASE_URL = "${module.plant_database.database_url_secret_id}:latest"
    }
    ) : {
    DATABASE_URL = "${module.plant_database.database_url_secret_id}:latest"
  }
```

**⚠️ Pre-requisite — GCP Secret Manager:** Before running `terraform apply`, verify the Razorpay
secrets exist in GCP Secret Manager for the target project:
```bash
gcloud secrets list --project=waooaw-oauth | grep -i razorpay
# Expected: RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET listed
# If missing: create them before applying Terraform or the Cloud Run deploy will fail at boot.
```
If they do NOT exist yet, add a TODO comment in main.tf and skip Change 3 for now.
Only Change 1 and Change 2 are required for the hire wizard DB persistence to work;
Razorpay keys are only needed for real payment confirmation (PAYMENTS_MODE=razorpay).

**Acceptance criteria:**

| # | Check | Pass condition |
|---|---|---|
| AC-1 | `terraform plan` on cp stack | Shows `CP_HIRE_USE_PLANT = "true"` being added to cp_backend env_vars, 0 destroy |
| AC-2 | `terraform plan` on plant stack | Shows `PAYMENTS_MODE` being added to plant_backend env_vars, 0 destroy |
| AC-3 | `terraform plan` on plant stack | Shows `RAZORPAY_KEY_ID` + `RAZORPAY_KEY_SECRET` in secrets block (or skipped with TODO comment) |
| AC-4 | No hardcoded secret values | All secret values are Secret Manager references (`"SECRET_NAME:latest"`) |

**Terraform plan commands:**
```bash
cd cloud/terraform
terraform init -reconfigure
terraform plan -var-file=environments/prod.tfvars \
  -target=module.cp_stack.module.cp_backend \
  -target=module.plant_stack.module.plant_backend \
  -out=CP-HIRE-1.tfplan 2>&1 | tail -30
# Must show: Plan: N to add, N to change, 0 to destroy.
```

> Note: In lower envs, `attach_secret_manager_secrets=false` so Razorpay secrets won't be
> injected in demo/test — this is expected. `PAYMENTS_MODE=coupon` will still apply in those
> environments (from Change 2), so hire wizard drafts persist to DB without needing Razorpay.

**Commit message:**
```
feat(CP-HIRE-1): activate CP_HIRE_USE_PLANT + PAYMENTS_MODE + Razorpay secrets on GCP
```

---

## End-to-End Hire Journey Flow (After Both Iterations Merged)

```
Customer clicks "Hire Agent" in CP FrontEnd
  │
  ├─► POST /api/cp/payments/razorpay/order (CP BackEnd)
  │     → Plant Gateway → POST /api/v1/payments/razorpay/order
  │     → Creates Razorpay order + SubscriptionModel row in DB
  │     → Returns: order_id, subscription_id, razorpay_order_id, amount
  │
  ├─► [Razorpay checkout widget opens in browser]
  │
  ├─► POST /api/cp/payments/razorpay/confirm (CP BackEnd)
  │     → Plant Gateway → POST /api/v1/payments/razorpay/confirm
  │     → Verifies Razorpay signature → marks subscription "active"
  │
  ├─► PUT /api/cp/hire/wizard/draft (CP BackEnd) ← CP_HIRE_USE_PLANT=true
  │     → Plant Gateway → PUT /api/v1/hired-agents/draft
  │     → Creates/updates HiredAgentModel row in DB (trial_status=not_started)
  │     → Returns: hired_instance_id
  │
  ├─► GET /api/cp/hire/wizard/by-subscription/{id} (CP BackEnd) ← Fixed in E1-S1
  │     → Plant Gateway → GET /api/v1/hired-agents/by-subscription/{id}
  │     → Reads HiredAgentModel from DB (persists across container restarts ✅)
  │
  └─► POST /api/cp/hire/wizard/finalize (CP BackEnd) ← CP_HIRE_USE_PLANT=true
        → Plant Gateway → POST /api/v1/hired-agents/{id}/finalize
        → Sets goals_completed=True, starts 7-day trial
        → HiredAgentModel: trial_status="active", trial_start_at=now, trial_end_at=now+7d
```

All rows persist in Cloud SQL PostgreSQL on GCP. Container restarts do not lose hire progress.
