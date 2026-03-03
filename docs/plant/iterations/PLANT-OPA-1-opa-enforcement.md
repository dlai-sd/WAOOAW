# PLANT-OPA-1 — OPA Policy Enforcement Goes Live

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `PLANT-OPA-1` |
| Feature area | Plant Gateway — OPA Policy Enforcement |
| Created | 2026-03-03 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CONTEXT_AND_INDEX.md` §3, §5 |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 2 |
| Total epics | 2 |
| Total stories | 6 |

> **PP DB Updates screen is safe post-OPA.** The DB Updates flow is: PP FrontEnd → PP BackEnd
> `/db/*` (scoped `db_updates` token carrying `roles:["admin"]`) → Plant Gateway → Plant Backend
> `/api/v1/admin/db/*`. OPA sees `resource="admin"`, `action="create"`, `roles:["admin"]`.
> Admin is role level 1 — passes every RBAC action. The screen remains fully accessible.

---

## Zero-Cost Agent Constraints (READ FIRST)

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is fully self-contained — no cross-references |
| No working memory across files | NFR code patterns and OPA input/output schemas embedded inline |
| No planning ability | Stories are atomic — one deliverable, exact files, one test command |
| Max 3 files per story | Pre-identified by PM in each story card |
| Binary inference only | Acceptance criteria are pass/fail |

> **Agent:** Execute exactly ONE story at a time. Read your assigned card, then act.
> Do NOT open NFRReusable.md. All patterns you need are in your card.

---

## Image Promotion Strategy (CRITICAL — read before writing any code)

The OPA service follows the same **build-once, promote-via-env-var** pattern used by every other
service on this platform:

1. One `Dockerfile` in `src/Plant/Gateway/opa/` builds the OPA bundle (Rego policies baked in —
   they are code, not config).
2. The image is pushed as `asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/plant-opa:<TAG>`.
3. The image tag is injected at deploy time via Terraform `-var="plant_opa_image=<TAG>"`.
4. The **same image tag** is promoted demo → uat → prod. No rebuild per environment.
5. Runtime configuration (log level, port) is passed as Cloud Run environment variables at deploy
   time — never baked into the image.
6. OPA is stateless: no database connection, no secrets, no VPC connector needed.

---

## PM Review Checklist

- [x] **EXPERT PERSONAS filled** — each iteration has correct persona list
- [x] Epic titles name outcomes not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds NFR code snippets inline
- [x] Every story card has max 3 files in "Files to read first"
- [x] Every story involving CP BackEnd states the pattern (N/A across this plan)
- [x] Every new backend route uses `waooaw_router()` (N/A — OPA has no FastAPI routes)
- [x] No GET route story touches `get_db_session()` (N/A — OPA is stateless)
- [x] Every story that adds env vars lists exact Terraform file paths
- [x] Every story has `BLOCKED UNTIL` (or "none")
- [x] Each iteration has a time estimate and come-back datetime
- [x] Each iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] Stories sequenced: backend (S1) before dependency (S2/S3)
- [x] No placeholders remain

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane B — Rego bundle + OPA Dockerfile + CI test gate | 1 | 3 | 3h | 2026-03-03 21:00 IST |
| 2 | Lane B — Terraform Cloud Run service + extends waooaw-deploy.yml (no new pipeline) | 1 | 3 | 3h | 2026-03-04 12:00 IST |

**Estimate basis:** Write 5 Rego files + tests = 90 min | OPA Dockerfile = 45 min | CI step = 30 min | Terraform module = 90 min | tfvars update = 30 min | CI deploy = 45 min. Add 20% buffer.

---

## How to Launch Each Iteration

### Iteration 1

**Pre-flight check:**
```bash
git status && git log --oneline -3
# Must show: clean tree on main. If not, resolve before launching.
```

**Steps:**
1. Open VS Code
2. Open Copilot Chat: `Ctrl+Alt+I` (Windows/Linux) or `Cmd+Alt+I` (Mac)
3. Click model dropdown → **Agent mode**
4. Click `+` (new conversation)
5. Type `@` → select **platform-engineer**
6. Paste the block below → press **Enter**
7. Come back at: **2026-03-03 21:00 IST**

**Iteration 1 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Open Policy Agent / Rego engineer + Senior GitHub Actions / CI-CD engineer + Senior Docker / container engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/plant/iterations/PLANT-OPA-1-opa-enforcement.md
YOUR SCOPE: Iteration 1 only — Epic E1 (stories E1-S1, E1-S2, E1-S3). Do not touch Iteration 2.
TIME BUDGET: 3h. If you reach 3.5h without finishing, follow STUCK PROTOCOL now.

EXECUTION ORDER:
1. Run: git status && git log --oneline -3
   You must be on main with a clean tree. If not, post why and HALT.
2. Read the "Agent Execution Rules" section in this plan file.
3. Read the "Iteration 1" section in this plan file.
4. Read nothing else before starting.
5. Execute stories in this order: E1-S1 → E1-S2 → E1-S3
6. When all stories are docker-tested, open the iteration PR. Post the PR URL. HALT.
```

**When you return:** Check Copilot Chat for a PR URL. Draft PR = stuck; read the comment for the blocker.

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Verify merge:**
```bash
git fetch origin && git log --oneline origin/main | head -3
# Must show: feat(PLANT-OPA-1): iteration 1 — rego bundle + OPA dockerfile + CI gate
```

**Iteration 2 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Terraform / GCP Cloud Run engineer + Senior GitHub Actions / CI-CD engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/plant/iterations/PLANT-OPA-1-opa-enforcement.md
YOUR SCOPE: Iteration 2 only — Epic E2 (stories E2-S1, E2-S2, E2-S3). Do not touch Iteration 1 content.
TIME BUDGET: 3h. If you reach 3.5h without finishing, follow STUCK PROTOCOL now.

PREREQUISITE CHECK (do before anything else):
  Run: git log --oneline origin/main | head -5
  Must show: feat(PLANT-OPA-1): iteration 1 — rego bundle + OPA dockerfile + CI gate
  If not: post "Blocked: Iteration 1 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 2" sections. Read nothing else.
3. Execute in this order: E2-S1 → E2-S2 (BLOCKED UNTIL E2-S1) → E2-S3 (BLOCKED UNTIL E2-S1)
4. When all stories are done, open the iteration PR. Post URL. HALT.
```

**Come back at:** 2026-03-04 12:00 IST

---

## Agent Execution Rules

### Rule -1 — Activate Expert Personas (first, before Rule 0)

Read the `EXPERT PERSONAS:` field from the task. Activate each persona. For every epic, open with:
> *"Acting as a [persona], I will [what] by [approach]."*

| Technology area | Expert persona |
|---|---|
| `src/Plant/Gateway/opa/` `.rego` files | Senior Open Policy Agent / Rego engineer |
| `cloud/terraform/stacks/plant/` | Senior Terraform / GCP Cloud Run engineer |
| `.github/workflows/` | Senior GitHub Actions / CI-CD engineer |
| `src/Plant/Gateway/opa/Dockerfile` | Senior Docker / container engineer |

---

### Rule 0 — Open tracking draft PR first

```bash
git checkout main && git pull
git checkout -b feat/PLANT-OPA-1-it1-e1
git commit --allow-empty -m "chore(PLANT-OPA-1): start iteration 1"
git push origin feat/PLANT-OPA-1-it1-e1
gh pr create \
  --base main \
  --head feat/PLANT-OPA-1-it1-e1 \
  --draft \
  --title "tracking: PLANT-OPA-1 Iteration 1 — in progress" \
  --body "## tracking: PLANT-OPA-1 Iteration 1

Subscribe to this PR to receive one notification per story completion.

### Stories
- [ ] [E1-S1] Write 5 Rego policy files + unit tests
- [ ] [E1-S2] OPA Dockerfile (build-once, env vars at runtime)
- [ ] [E1-S3] Add opa test CI step to waooaw-ci.yml

_Live updates posted as comments below ↓_"
```

---

### Rule 1 — Branch discipline
One epic = one branch: `feat/PLANT-OPA-1-itN-eN`. All stories in one epic share the same branch.

### Rule 2 — Scope lock
Implement exactly the acceptance criteria. No refactoring outside scope. Unrelated bugs → TODO comment.

### Rule 3 — Tests before next story
Write every test listed in the story's test table before advancing.

### Rule 4 — Commit + push + notify after every story
```bash
git add -A
git commit -m "feat(PLANT-OPA-1): [story title]"
git push origin feat/PLANT-OPA-1-itN-eN
git add docs/plant/iterations/PLANT-OPA-1-opa-enforcement.md
git commit -m "docs(PLANT-OPA-1): mark [story-id] done"
git push origin feat/PLANT-OPA-1-itN-eN
gh pr comment \
  $(gh pr list --head feat/PLANT-OPA-1-it1-e1 --json number -q '.[0].number') \
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
Exit 0 → mark epic complete ✅, commit, push. Non-zero → fix, retry (max 3). Then: STUCK PROTOCOL.

### Rule 6 — STUCK PROTOCOL
```bash
git add -A && git commit -m "WIP: [story-id] blocked — [exact error]"
git push origin feat/PLANT-OPA-1-itN-eN
gh pr create \
  --base main \
  --head feat/PLANT-OPA-1-itN-eN \
  --title "WIP: [story-id] — blocked" \
  --draft \
  --body "Blocked on: [test name]
Error: [exact error message]
Attempted fixes:
1. [what I tried]
2. [what I tried]"
```
Post the draft PR URL. **HALT.**

### Rule 7 — Iteration PR (after ALL epics complete)
```bash
git checkout main && git pull
git checkout -b feat/PLANT-OPA-1-it1
git merge --no-ff feat/PLANT-OPA-1-it1-e1
git push origin feat/PLANT-OPA-1-it1
gh pr create \
  --base main \
  --head feat/PLANT-OPA-1-it1 \
  --title "feat(PLANT-OPA-1): iteration 1 — rego bundle + OPA dockerfile + CI gate" \
  --body "## PLANT-OPA-1 Iteration 1

### Stories completed
| E1-S1 | Write 5 Rego policy files + unit tests | ✅ |
| E1-S2 | OPA Dockerfile (build-once, env vars at runtime) | ✅ |
| E1-S3 | Add opa test CI step to waooaw-ci.yml | ✅ |

### Docker integration
All containers exited 0 ✅

### NFR checklist
- [ ] No env-specific values baked into Dockerfile
- [ ] OPA image tag injected at runtime via Terraform var (done in Iteration 2)
- [ ] opa test passes for all 5 Rego files
- [ ] Tests >= 80% coverage on new Rego unit test files"
```

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | E1: OPA Rego Bundle | Write 5 Rego policy files + unit tests | 🔴 Not Started | — |
| E1-S2 | 1 | E1: OPA Rego Bundle | OPA Dockerfile (build-once) | 🔴 Not Started | — |
| E1-S3 | 1 | E1: OPA Rego Bundle | Add opa test CI step to waooaw-ci.yml | 🔴 Not Started | — |
| E2-S1 | 2 | E2: Terraform + Deploy | Terraform plant_opa Cloud Run module | 🔴 Not Started | — |
| E2-S2 | 2 | E2: Terraform + Deploy | Add plant_opa_image to all 3 tfvars | 🔴 Not Started | — |
| E2-S3 | 2 | E2: Terraform + Deploy | Build/push plant-opa in waooaw-deploy.yml | 🔴 Not Started | — |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

---

## Iteration 1 — OPA Rego Bundle + Dockerfile + CI Gate

**Scope:** The platform owner can run `opa test` locally and in CI and see all 5 policies pass. The OPA Docker image builds cleanly from the bundle.
**Lane:** B — new component. **No new CI/CD pipeline** — E1-S3 adds one job to the existing `waooaw-ci.yml`.
**⏱ Estimated:** 3h | **Come back:** 2026-03-03 21:00 IST
**Epic:** E1

### Dependency Map (Iteration 1)

```
E1-S1 ──► E1-S3  (E1-S3 blocked until E1-S1 committed)
E1-S2          (independent of E1-S1, own work on Dockerfile)
```

---

### Epic E1: OPA Rego Bundle Serves Real Decisions

**Branch:** `feat/PLANT-OPA-1-it1-e1`
**User story:** As the platform owner, when I deploy the OPA service I can see real RBAC and policy decisions in Cloud Logging instead of 500/OPA-not-found errors.

---

#### Story E1-S1: Write 5 Rego policy files + unit tests

**BLOCKED UNTIL:** none
**Estimated time:** 90 min
**Branch:** `feat/PLANT-OPA-1-it1-e1`
**CP BackEnd pattern:** N/A

**What to do (self-contained):**
Create the directory `src/Plant/Gateway/opa/policies/` and write exactly 5 Rego
files (`rbac_pp.rego`, `agent_budget.rego`, `trial_mode.rego`, `governor_role.rego`,
`sandbox_routing.rego`) plus one unit test file per policy.
Each policy's `allow` rule must return an **object** (not a boolean) because the
Plant Gateway middleware calls `/v1/data/gateway/<policy>/allow` and then does
`.get("result", {}).get("allow", False)` on the response — so OPA's `result`
must be a dict containing an `allow` key.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/Gateway/middleware/rbac.py` | 130–230 | OPA input shape `{resource, action, jwt}` and expected `{result: {allow, user_info, deny_reason}}` |
| `src/Plant/Gateway/middleware/budget.py` | 170–230 | OPA input `{jwt, agent_id, customer_id, path, method}` and `budget_result.get("allow")` usage |
| `src/Plant/Gateway/middleware/policy.py` | 140–220 | Policy input `{jwt, resource, action, method, path}` and `trial_result.get("allow")` usage |

**Files to create:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/Gateway/opa/policies/rbac_pp.rego` | create | 7-role RBAC policy, see schema below |
| `src/Plant/Gateway/opa/policies/agent_budget.rego` | create | Budget passthrough v1, see schema below |
| `src/Plant/Gateway/opa/policies/trial_mode.rego` | create | Trial mode gate, see schema below |
| `src/Plant/Gateway/opa/policies/governor_role.rego` | create | Governor/admin gate for sensitive actions |
| `src/Plant/Gateway/opa/policies/sandbox_routing.rego` | create | Passthrough v1 |
| `src/Plant/Gateway/opa/tests/test_rbac_pp.rego` | create | Unit tests for rbac_pp |
| `src/Plant/Gateway/opa/tests/test_agent_budget.rego` | create | Unit tests for agent_budget |
| `src/Plant/Gateway/opa/tests/test_trial_mode.rego` | create | Unit tests for trial_mode |
| `src/Plant/Gateway/opa/tests/test_governor_role.rego` | create | Unit tests for governor_role |
| `src/Plant/Gateway/opa/tests/test_sandbox_routing.rego` | create | Unit tests for sandbox_routing |

**Code patterns to copy exactly:**

```rego
# src/Plant/Gateway/opa/policies/rbac_pp.rego
# Queries: POST /v1/data/gateway/rbac_pp/allow
# Input:   {"input": {"resource": str, "action": str, "jwt": {"user_id": str, "email": str, "roles": [str], ...}}}
# Output:  {"result": {"allow": bool, "user_info": {...}, "deny_reason": str|null}}

package gateway.rbac_pp

# 7-role hierarchy: level 1 (highest) → level 7 (lowest)
role_hierarchy := {
    "admin":          1,
    "customer_admin": 2,
    "developer":      3,
    "manager":        4,
    "analyst":        5,
    "support":        6,
    "viewer":         7
}

# Minimum level required per action (lower number = more privileged)
action_min_level := {
    "create":  3,
    "update":  3,
    "delete":  2,
    "read":    7,
    "execute": 3,
    "approve": 2,
    "deploy":  3,
    "manage":  2
}

# Resolved role: the highest-privilege (lowest level number) role the user holds
user_best_role := role if {
    some role in input.jwt.roles
    role_hierarchy[role]
    role_hierarchy[role] == min({lvl |
        some r in input.jwt.roles
        lvl := role_hierarchy[r]
    })
}

user_best_level := role_hierarchy[user_best_role]

# Required level for this action
required_level := action_min_level[input.action]

# Allowed when user's best level <= required level (lower = more privileged)
permission_granted if {
    some _ in input.jwt.roles
    user_best_level <= required_level
}

# Default: deny
allow = {
    "allow":      false,
    "user_info":  {},
    "deny_reason": "No recognized role or insufficient privilege"
}

# Override: allow when permission_granted
allow = result if {
    permission_granted
    result := {
        "allow": true,
        "user_info": {
            "user_id":    input.jwt.user_id,
            "email":      input.jwt.email,
            "roles":      input.jwt.roles,
            "role_level": user_best_level,
            "is_admin":   user_best_role == "admin",
            "permissions": []
        },
        "deny_reason": null
    }
}
```

```rego
# src/Plant/Gateway/opa/policies/agent_budget.rego
# Queries: POST /v1/data/gateway/agent_budget/allow
# Input:   {"input": {"jwt": {...}, "agent_id": str, "customer_id": str, "path": str, "method": str}}
# Output:  {"result": {"allow": bool, "alert_level": str, "platform_utilization_percent": int, "agent_utilization_percent": int, "deny_reason": str|null}}
# NOTE: v1 — OPA does not have Redis access. Real budget counters tracked in Redis by middleware.
#       This policy is a constitutional passthrough. OPA will enforce hard limits in v2
#       when budget data is injected via input.budget_data.

package gateway.agent_budget

allow = {
    "allow":                        true,
    "alert_level":                  "normal",
    "platform_utilization_percent": 0,
    "agent_utilization_percent":    0,
    "deny_reason":                  null
}
```

```rego
# src/Plant/Gateway/opa/policies/trial_mode.rego
# Queries: POST /v1/data/gateway/trial_mode/allow
# Input:   {"input": {"jwt": {"trial_mode": bool, "trial_expires_at": str|null, "task_count": int|null}, "resource": str, "action": str, "method": str, "path": str}}
# Output:  {"result": {"allow": bool, "deny_reason": str|null, "task_count": int, "limit": int}}

package gateway.trial_mode

# Paid-only resources trial users cannot access
paid_only_resources := {"invoices", "subscriptions", "billing"}

# Trial task limit (governs trial resource usage)
trial_task_limit := 50

# Default: allow
allow = {
    "allow":       true,
    "deny_reason": null,
    "task_count":  0,
    "limit":       trial_task_limit
}

# Block if user is in trial and tries to access paid-only resource
allow = {
    "allow":       false,
    "deny_reason": "Trial users cannot access billing and subscription features. Please upgrade.",
    "task_count":  0,
    "limit":       trial_task_limit
} if {
    input.jwt.trial_mode == true
    input.resource in paid_only_resources
}
```

```rego
# src/Plant/Gateway/opa/policies/governor_role.rego
# Queries: POST /v1/data/gateway/governor_role/allow
# Input:   {"input": {"jwt": {"roles": [str]}, "resource": str, "action": str}}
# Output:  {"result": {"allow": bool, "deny_reason": str|null}}

package gateway.governor_role

governor_roles := {"admin", "customer_admin"}

allow = {
    "allow":       false,
    "deny_reason": "This action requires admin or customer_admin role"
}

allow = {
    "allow":       true,
    "deny_reason": null
} if {
    some role in input.jwt.roles
    role in governor_roles
}
```

```rego
# src/Plant/Gateway/opa/policies/sandbox_routing.rego
# Queries: POST /v1/data/gateway/sandbox_routing/allow
# Input:   {"input": {"jwt": {...}, "resource": str, "action": str, "method": str, "path": str}}
# Output:  {"result": {"allow": bool, "deny_reason": str|null}}
# NOTE: v1 passthrough — sandbox routing logic added in a future iteration.

package gateway.sandbox_routing

allow = {
    "allow":       true,
    "deny_reason": null
}
```

```rego
# src/Plant/Gateway/opa/tests/test_rbac_pp.rego
# Run: docker run --rm -v $(pwd)/src/Plant/Gateway/opa:/opa openpolicyagent/opa:0.68.0 test /opa -v

package gateway.rbac_pp_test

import data.gateway.rbac_pp

# T1: admin can do anything
test_admin_can_create if {
    result := rbac_pp.allow with input as {
        "resource": "agents",
        "action":   "create",
        "jwt": {"user_id": "u1", "email": "a@b.com", "roles": ["admin"]}
    }
    result.allow == true
    result.user_info.is_admin == true
}

# T2: viewer cannot create
test_viewer_cannot_create if {
    result := rbac_pp.allow with input as {
        "resource": "agents",
        "action":   "create",
        "jwt": {"user_id": "u2", "email": "v@b.com", "roles": ["viewer"]}
    }
    result.allow == false
}

# T3: viewer can read
test_viewer_can_read if {
    result := rbac_pp.allow with input as {
        "resource": "agents",
        "action":   "read",
        "jwt": {"user_id": "u3", "email": "v@b.com", "roles": ["viewer"]}
    }
    result.allow == true
}

# T4: no recognized role → deny
test_unknown_role_denied if {
    result := rbac_pp.allow with input as {
        "resource": "agents",
        "action":   "read",
        "jwt": {"user_id": "u4", "email": "x@b.com", "roles": ["superuser"]}
    }
    result.allow == false
}

# T5: DB Updates screen safety — admin can POST to /api/v1/admin/db/execute
# Path extracts to resource="admin", action="create" (POST).
# The db_updates token carries roles:["admin"] — this must always be allowed.
test_admin_db_updates_allowed if {
    result := rbac_pp.allow with input as {
        "resource": "admin",
        "action":   "create",
        "jwt": {"user_id": "u5", "email": "admin@b.com", "roles": ["admin"]}
    }
    result.allow == true
    result.user_info.is_admin == true
}

# T6: non-admin cannot reach DB Updates (/admin/db routes)
test_non_admin_db_updates_blocked if {
    result := rbac_pp.allow with input as {
        "resource": "admin",
        "action":   "create",
        "jwt": {"user_id": "u6", "email": "dev@b.com", "roles": ["developer"]}
    }
    # developer is level 3; action_min_level["create"] = 3 → 3 <= 3 → allow
    # Developer CAN create — but /admin/db has its own admin-role check in Plant Backend.
    # OPA is the first gate; Plant Backend is the second gate for admin resources.
    result.allow == true  # OPA allows developer to create; Plant Backend enforces admin-only
}
```

```rego
# src/Plant/Gateway/opa/tests/test_trial_mode.rego

package gateway.trial_mode_test

import data.gateway.trial_mode

# T1: trial user accessing paid resource → blocked
test_trial_blocked_on_billing if {
    result := trial_mode.allow with input as {
        "jwt": {"trial_mode": true},
        "resource": "billing",
        "action": "read"
    }
    result.allow == false
}

# T2: trial user accessing a free resource → allowed
test_trial_allowed_on_agents if {
    result := trial_mode.allow with input as {
        "jwt": {"trial_mode": true},
        "resource": "agents",
        "action": "read"
    }
    result.allow == true
}

# T3: paid user accessing billing → allowed
test_paid_user_allowed_billing if {
    result := trial_mode.allow with input as {
        "jwt": {"trial_mode": false},
        "resource": "billing",
        "action": "read"
    }
    result.allow == true
}
```

**Acceptance criteria:**
1. `src/Plant/Gateway/opa/policies/` contains exactly 5 `.rego` files, each with a correct `package gateway.<name>` declaration.
2. `src/Plant/Gateway/opa/tests/` contains exactly 5 test `.rego` files.
3. Running `docker run --rm -v $(pwd)/src/Plant/Gateway/opa:/opa openpolicyagent/opa:0.68.0 test /opa -v` from repo root exits 0 with all tests passing.
4. No `PASS 0` lines — at least 3 tests per policy file.
5. `rbac_pp.rego` `allow` rule returns an object containing `allow`, `user_info`, `deny_reason` keys.
6. **DB Updates safety gate**: `test_admin_db_updates_allowed` passes — admin role with `resource="admin"`, `action="create"` returns `allow==true`. This covers the PP DB Updates screen flow (db_updates token carries `roles:["admin"]`).
7. **Two-gate design confirmed in comments**: OPA is gate 1 (role level); Plant Backend `/admin/db` is gate 2 (hard admin-role check via `_require_admin_via_gateway`). Non-admin roles may pass OPA gate 1 for `resource="admin"` but are blocked by Plant Backend gate 2.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S1-T1 | `opa/tests/test_rbac_pp.rego` | admin role, create action | `allow == true`, `is_admin == true` |
| E1-S1-T2 | `opa/tests/test_rbac_pp.rego` | viewer role, create action | `allow == false` |
| E1-S1-T3 | `opa/tests/test_rbac_pp.rego` | viewer role, read action | `allow == true` |
| E1-S1-T4 | `opa/tests/test_rbac_pp.rego` | unknown role | `allow == false` |
| E1-S1-T5 | `opa/tests/test_rbac_pp.rego` | admin + resource=admin + action=create (DB Updates path) | `allow == true`, `is_admin == true` |
| E1-S1-T6 | `opa/tests/test_rbac_pp.rego` | non-admin + resource=admin + action=create | `allow == true` (OPA level-based; Plant Backend is the 2nd hard admin gate) |
| E1-S1-T7 | `opa/tests/test_trial_mode.rego` | trial user, billing resource | `allow == false` |
| E1-S1-T8 | `opa/tests/test_trial_mode.rego` | trial user, agents resource | `allow == true` |
| E1-S1-T9 | `opa/tests/test_trial_mode.rego` | paid user, billing resource | `allow == true` |

**Test command:**
```bash
docker run --rm \
  -v $(pwd)/src/Plant/Gateway/opa:/opa \
  openpolicyagent/opa:0.68.0 \
  test /opa -v
# Must exit 0. Must show PASS for all test_ functions.
```

**Commit message:** `feat(PLANT-OPA-1): write 5 Rego policy files with unit tests`

**Done signal:** `"E1-S1 done. Changed: opa/policies/ (5 files), opa/tests/ (5 files). Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅ T5 ✅ T6 ✅ T7 ✅ T8 ✅ T9 ✅"`

---

#### Story E1-S2: OPA Dockerfile (build-once, env vars at runtime)

**BLOCKED UNTIL:** none (can be done in parallel with E1-S1, same branch)
**Estimated time:** 45 min
**Branch:** `feat/PLANT-OPA-1-it1-e1` (same branch as E1-S1)
**CP BackEnd pattern:** N/A

**What to do:**
Create `src/Plant/Gateway/opa/Dockerfile` that builds an OPA image with the Rego policies
baked in (policies are code — correct to bake). The image must **not** bake in any environment-
specific values (URLs, secrets, env names). Runtime config (log level) is passed as a Cloud
Run environment variable at deploy time. The image is built once, promoted demo → uat → prod
by injecting the image tag via Terraform `-var="plant_opa_image=<TAG>"`. Also create `.dockerignore`
to exclude the tests directory from the image (tests are for CI only, not production).

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/Gateway/Dockerfile` | 1–55 | Multi-stage pattern, non-root user, health check pattern |

**Files to create:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/Gateway/opa/Dockerfile` | create | Multi-stage OPA image, policies baked in, no env-specific values |
| `src/Plant/Gateway/opa/.dockerignore` | create | Exclude tests/ directory |

**Code patterns to copy exactly:**

```dockerfile
# src/Plant/Gateway/opa/Dockerfile
# Build-once OPA bundle image.
# Rego policies are CODE — they are baked into the image at build time.
# Runtime config (log level, server address) is injected via Cloud Run env vars at deploy time.
# NEVER bake environment-specific URLs, secrets, or env names into this file.
#
# Image promotion: build once, deploy to demo, promote same tag to uat → prod.
# Terraform injects the tag via:  -var="plant_opa_image=<registry>/plant-opa:<TAG>"

# Pin to a specific digest for reproducibility. Use a recent stable release.
FROM openpolicyagent/opa:0.68.0

WORKDIR /app

# Bake policies into the image — these are code, not config.
COPY policies/ ./policies/

# Runtime configuration is passed as Cloud Run environment variables.
# These are non-secret defaults — override at deploy time with env vars.
ENV OPA_LOG_LEVEL=info
ENV PORT=8181

# Health check: OPA has a built-in health endpoint.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["/opa", "health"]

EXPOSE 8181

# OPA runs as non-root by default (uid 1000 in the official image).
# Do not add USER directive — the official image already handles this.

# Start OPA in server mode.
# --addr: bind to all interfaces on PORT (Cloud Run requirement).
# --log-format=json: structured logs for Cloud Logging.
# ./policies: serve the baked bundle.
# Note: OPA_LOG_LEVEL is read from env automatically when --log-level is not set.
CMD ["run", \
     "--server", \
     "--addr=0.0.0.0:8181", \
     "--log-format=json", \
     "./policies"]
```

```
# src/Plant/Gateway/opa/.dockerignore
# Exclude test files from the production image — tests are for CI only.
tests/
*.md
```

**Acceptance criteria:**
1. `docker build -f src/Plant/Gateway/opa/Dockerfile src/Plant/Gateway/opa/ -t plant-opa:test` exits 0.
2. `docker run --rm -d -p 18181:8181 --name opa-test plant-opa:test` starts the container.
3. `curl -s http://localhost:18181/health` returns `{}` (OPA health endpoint).
4. `docker run --rm plant-opa:test` shows OPA server starting (CMD is correct).
5. `docker image inspect plant-opa:test` shows NO environment variables with values like `demo`, `uat`, `prod`, or any GCP project/URL.

**Tests to write:**

| Test ID | What to check | Command |
|---|---|---|
| E1-S2-T1 | Image builds | `docker build -f src/Plant/Gateway/opa/Dockerfile src/Plant/Gateway/opa/ -t plant-opa:test` |
| E1-S2-T2 | Health endpoint responds | Start container on port 18181, `curl http://localhost:18181/health` → `{}` |
| E1-S2-T3 | No env-specific values baked | `docker image inspect plant-opa:test \| grep -E 'demo\|uat\|prod\|run\.app'` → empty |

**Test command:**
```bash
# Build
docker build -f src/Plant/Gateway/opa/Dockerfile src/Plant/Gateway/opa/ -t plant-opa:test

# Start and health-check
docker run --rm -d -p 18181:8181 --name opa-test plant-opa:test
sleep 3
curl -s http://localhost:18181/health
docker stop opa-test

# Verify no env-specific values in the image
docker image inspect plant-opa:test | grep -E 'demo|uat|prod|run\.app' && echo "FAIL: env-specific values found" || echo "PASS: no env-specific values"
```

**Commit message:** `feat(PLANT-OPA-1): OPA Dockerfile with build-once promotion pattern`

**Done signal:** `"E1-S2 done. Changed: opa/Dockerfile, opa/.dockerignore. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

#### Story E1-S3: Add opa test CI step to waooaw-ci.yml

**BLOCKED UNTIL:** E1-S1 committed to `feat/PLANT-OPA-1-it1-e1`
**Estimated time:** 30 min
**Branch:** `feat/PLANT-OPA-1-it1-e1` (same branch)
**CP BackEnd pattern:** N/A

**What to do:**
Add a CI job `opa-policy-test` to `.github/workflows/waooaw-ci.yml` that runs
`opa test` inside the official OPA Docker image against `src/Plant/Gateway/opa/`.
This gate must run on every PR so no Rego change can break existing policies without
failing CI. It should be added as an independent job (not inside the Python test job)
and should use the same `openpolicyagent/opa:0.68.0` tag that the Dockerfile pins to.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `.github/workflows/waooaw-ci.yml` | 1–80 | Existing job structure, trigger events, `runs-on`, how to add an independent job |

**Files to modify:**

| File | Action | Precise instruction |
|---|---|---|
| `.github/workflows/waooaw-ci.yml` | modify | Add `opa-policy-test` job after the last existing job in the file |

**Code patterns to copy exactly:**

```yaml
# Add this job to .github/workflows/waooaw-ci.yml
# Place it alongside (not inside) the existing Python/lint jobs.
# It is a standalone job — no needs: dependency on other jobs.

  opa-policy-test:
    name: OPA Policy Unit Tests
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Run opa test
        run: |
          docker run --rm \
            -v "${{ github.workspace }}/src/Plant/Gateway/opa:/opa" \
            openpolicyagent/opa:0.68.0 \
            test /opa -v
        # Exit non-zero if any test fails. The -v flag shows individual test results.
        # Add this line to the plan's tracking table when merged to main.
```

**Acceptance criteria:**
1. `.github/workflows/waooaw-ci.yml` contains a job named `opa-policy-test`.
2. The job uses `openpolicyagent/opa:0.68.0` (matching the Dockerfile pin).
3. The job mounts `src/Plant/Gateway/opa/` and runs `test /opa -v`.
4. On a local dry-run (`act`) or by inspecting the YAML, the job is syntactically valid.
5. The job runs on `ubuntu-latest` with no extra permissions required.

**Tests to write:**

| Test ID | What to check | Command |
|---|---|---|
| E1-S3-T1 | YAML is valid | `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/waooaw-ci.yml'))"` → no exception |
| E1-S3-T2 | Job exists | `grep -c "opa-policy-test" .github/workflows/waooaw-ci.yml` → `1` |
| E1-S3-T3 | OPA version matches Dockerfile | Both use `openpolicyagent/opa:0.68.0` |

**Test command:**
```bash
# YAML validation
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/waooaw-ci.yml')); print('YAML valid')"

# Job exists
grep -c "opa-policy-test" .github/workflows/waooaw-ci.yml

# OPA version consistency
grep "openpolicyagent/opa:" src/Plant/Gateway/opa/Dockerfile .github/workflows/waooaw-ci.yml
# Both lines must show 0.68.0
```

**Commit message:** `feat(PLANT-OPA-1): add opa test CI gate to waooaw-ci.yml`

**Done signal:** `"E1-S3 done. Changed: .github/workflows/waooaw-ci.yml. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

## Iteration 2 — Terraform Cloud Run Service + Deploy Pipeline

**Scope:** The OPA service runs as a live Cloud Run service on demo. Plant Gateway's `OPA_URL`
points to the real service URL (no more `# TODO` comment). Deploy pipeline builds and promotes
the OPA image via the same pattern as every other service.
**Lane:** B — new Terraform resource + extends `waooaw-deploy.yml` (no new pipeline).
**⏱ Estimated:** 3h | **Come back:** 2026-03-04 12:00 IST
**Epic:** E2

### Dependency Map (Iteration 2)

```
E2-S1 ──► E2-S2  (E2-S2 blocked: needs plant_opa_image variable from E2-S1)
E2-S1 ──► E2-S3  (E2-S3 blocked: needs plant_opa_image variable from E2-S1)
```

---

### Epic E2: Plant Gateway Connects to Real OPA Service

**Branch:** `feat/PLANT-OPA-1-it2-e2`
**User story:** As the platform owner, I can deploy the OPA service to demo with one `terraform apply` and see Plant Gateway routing policy decisions to it — zero `# TODO` placeholders remain in infra code.

---

#### Story E2-S1: Terraform plant_opa Cloud Run module + IAM + wire OPA_URL

**BLOCKED UNTIL:** none
**Estimated time:** 90 min
**Branch:** `feat/PLANT-OPA-1-it2-e2`
**CP BackEnd pattern:** N/A

**What to do:**
Add three changes to `cloud/terraform/stacks/plant/`:
1. In `variables.tf` — add `variable "plant_opa_image"` following the same pattern as `variable "plant_gateway_image"`.
2. In `main.tf` — add `module "plant_opa"` using the existing `../../modules/cloud-run` module; add `google_cloud_run_v2_service_iam_member` granting `local.plant_gateway_sa` the `roles/run.invoker` role on the OPA service; replace the two `# TODO` lines for `OPA_URL` and `OPA_SERVICE_URL` in the plant_gateway module with `module.plant_opa.service_url`.
3. The OPA service needs NO database, NO VPC connector, NO secrets — it is stateless.
   Runtime config (log level only) is passed as `env_vars`, never as secrets.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `cloud/terraform/stacks/plant/main.tf` | 140–215 | pattern for `module "plant_gateway"`, `google_cloud_run_v2_service_iam_member`, `local.plant_gateway_sa`, `allow_unauthenticated` |
| `cloud/terraform/stacks/plant/variables.tf` | 20–40 | `variable "plant_gateway_image"` definition to copy exactly |

**Files to modify:**

| File | Action | Precise instruction |
|---|---|---|
| `cloud/terraform/stacks/plant/variables.tf` | modify | Add `variable "plant_opa_image"` block after `variable "plant_gateway_image"` |
| `cloud/terraform/stacks/plant/main.tf` | modify | (1) Add `module "plant_opa"` + IAM resource before `module "networking"`. (2) Replace the 2 `# TODO` OPA_URL lines in `module "plant_gateway"` env_vars with `module.plant_opa.service_url`. |

**Code patterns to copy exactly:**

```hcl
# Add to cloud/terraform/stacks/plant/variables.tf
# Place immediately after the "plant_gateway_image" variable block.

variable "plant_opa_image" {
  description = "Docker image for the Plant OPA policy engine service. Build once, promote demo → uat → prod by injecting a different tag."
  type        = string
}
```

```hcl
# Add to cloud/terraform/stacks/plant/main.tf
# Place this block BEFORE the "module networking" block.
# OPA is stateless: no Cloud SQL, no VPC connector, no secrets.
# Runtime config (log level) is passed as env_vars — NOT baked into the image.

module "plant_opa" {
  source = "../../modules/cloud-run"

  service_name = "waooaw-plant-opa-${var.environment}"
  region       = var.region
  project_id   = var.project_id
  environment  = var.environment
  service_type = "backend"

  # Image tag injected at deploy time — never baked into the image.
  # Same image promoted demo → uat → prod by passing -var="plant_opa_image=<TAG>"
  image         = var.plant_opa_image
  port          = 8181
  cpu           = "0.5"
  memory        = "256Mi"
  min_instances = var.min_instances
  max_instances = var.max_instances

  # OPA is stateless — no database, no VPC connector required.
  cloud_sql_connection_name = null
  vpc_connector_id          = null

  # Service-to-service only — Plant Gateway invokes OPA via ID token.
  # allUsers must NOT have invoker access.
  allow_unauthenticated = false

  env_vars = {
    ENVIRONMENT = var.environment
    LOG_LEVEL   = "info"
    # No secrets, no URLs, no env-specific values beyond environment label.
  }

  secrets = {}

  depends_on = [module.vpc_connector]
}

# Grant Plant Gateway's service account permission to invoke OPA.
# Same pattern as plant_backend_invoker above.
resource "google_cloud_run_v2_service_iam_member" "plant_opa_invoker" {
  project  = var.project_id
  location = var.region
  name     = module.plant_opa.service_name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${local.plant_gateway_sa}"
}
```

```hcl
# In cloud/terraform/stacks/plant/main.tf — inside module "plant_gateway" env_vars block,
# REPLACE these two lines:
#   OPA_URL         = "https://opa-policy-engine.a.run.app" # TODO: Create OPA service
#   OPA_SERVICE_URL = "https://opa-policy-engine.a.run.app" # Back-compat for older configs
#
# WITH:
    OPA_URL         = module.plant_opa.service_url
    OPA_SERVICE_URL = module.plant_opa.service_url  # Back-compat alias
```

```hcl
# Also add module.plant_opa to the depends_on of module "plant_gateway":
  depends_on = [module.plant_database, module.vpc_connector, module.plant_backend, module.plant_opa]
```

**Acceptance criteria:**
1. `cloud/terraform/stacks/plant/variables.tf` contains `variable "plant_opa_image"`.
2. `cloud/terraform/stacks/plant/main.tf` contains `module "plant_opa"` with `allow_unauthenticated = false`.
3. `cloud/terraform/stacks/plant/main.tf` has `google_cloud_run_v2_service_iam_member.plant_opa_invoker`.
4. `cloud/terraform/stacks/plant/main.tf` has NO lines matching `# TODO: Create OPA service`.
5. `OPA_URL = module.plant_opa.service_url` in plant_gateway env_vars.
6. `/tmp/terraform fmt -check cloud/terraform/stacks/plant/` exits 0 (no formatting issues). Run `/tmp/terraform fmt cloud/terraform/stacks/plant/` to auto-fix if needed.

**Tests to write:**

| Test ID | What to check | Command |
|---|---|---|
| E2-S1-T1 | No TODO placeholder remains | `grep -r "TODO: Create OPA service" cloud/terraform/` → empty |
| E2-S1-T2 | plant_opa_image variable exists | `grep -c "plant_opa_image" cloud/terraform/stacks/plant/variables.tf` → `1` |
| E2-S1-T3 | Terraform fmt passes | `/tmp/terraform fmt -recursive -check cloud/terraform/stacks cloud/terraform/modules` → exit 0 |
| E2-S1-T4 | OPA not publicly accessible | `grep -A5 "plant_opa_invoker" cloud/terraform/stacks/plant/main.tf \| grep allow_unauthenticated` → `false` |

**Test command:**
```bash
# No TODO comments remain
grep -r "TODO: Create OPA service" cloud/terraform/ && echo "FAIL" || echo "PASS: no TODO"

# Variable exists
grep -c "plant_opa_image" cloud/terraform/stacks/plant/variables.tf

# Terraform fmt check (binary at /tmp/terraform)
/tmp/terraform fmt -recursive -check cloud/terraform/stacks cloud/terraform/modules
echo "fmt exit: $?"
```

**Commit message:** `feat(PLANT-OPA-1): terraform plant_opa Cloud Run module + IAM + wire OPA_URL`

**Done signal:** `"E2-S1 done. Changed: variables.tf, main.tf. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

---

#### Story E2-S2: Add plant_opa_image to all 3 environment tfvars

**BLOCKED UNTIL:** E2-S1 committed to `feat/PLANT-OPA-1-it2-e2`
**Estimated time:** 30 min
**Branch:** `feat/PLANT-OPA-1-it2-e2` (same branch)
**CP BackEnd pattern:** N/A

**What to do:**
Add `plant_opa_image` to all three environment tfvars files. Follow the same comment
convention as `plant_backend_image` — note that the lifecycle block in the cloud-run module
means Terraform ignores the image after first creation; the actual deployed image is
passed via `-var="plant_opa_image=<TAG>"` from `waooaw-deploy.yml` CI at runtime.
Run `terraform fmt` after each change.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `cloud/terraform/stacks/plant/environments/demo.tfvars` | 1–15 | `plant_backend_image` line to copy the comment pattern exactly |

**Files to modify:**

| File | Action | Precise instruction |
|---|---|---|
| `cloud/terraform/stacks/plant/environments/demo.tfvars` | modify | Add `plant_opa_image` line after `plant_backend_image` line |
| `cloud/terraform/stacks/plant/environments/uat.tfvars` | modify | Same change |
| `cloud/terraform/stacks/plant/environments/prod.tfvars` | modify | Same change |

**Code patterns to copy exactly:**

```hcl
# Add this line in each *.tfvars file, immediately after the plant_backend_image line.
# The comment must match the indentation of the surrounding block exactly.
# (terraform fmt will align = signs; run /tmp/terraform fmt after adding)

# plant_opa_image is ignored by lifecycle block in cloud-run module
# The actual deployed image will be set by waooaw-deploy.yml: -var="plant_opa_image=<TAG>"
plant_opa_image = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/plant-opa:ignored-by-lifecycle"
```

**Acceptance criteria:**
1. All 3 tfvars files contain `plant_opa_image`.
2. `/tmp/terraform fmt -recursive -check cloud/terraform/stacks` exits 0 (all 3 files are formatted).
3. The value follows the `ignored-by-lifecycle` convention.

**Tests to write:**

| Test ID | What to check | Command |
|---|---|---|
| E2-S2-T1 | All 3 tfvars updated | `grep -l "plant_opa_image" cloud/terraform/stacks/plant/environments/*.tfvars \| wc -l` → `3` |
| E2-S2-T2 | Terraform fmt | `/tmp/terraform fmt -recursive -check cloud/terraform/stacks cloud/terraform/modules` → exit 0 |

**Test command:**
```bash
grep -l "plant_opa_image" cloud/terraform/stacks/plant/environments/*.tfvars | wc -l
/tmp/terraform fmt -recursive -check cloud/terraform/stacks cloud/terraform/modules
echo "fmt exit: $?"
```

**Commit message:** `feat(PLANT-OPA-1): add plant_opa_image to all 3 environment tfvars`

**Done signal:** `"E2-S2 done. Changed: demo.tfvars, uat.tfvars, prod.tfvars. Tests: T1 ✅ T2 ✅"`

---

#### Story E2-S3: Add plant-opa build/push + terraform var to waooaw-deploy.yml

**BLOCKED UNTIL:** E2-S1 committed to `feat/PLANT-OPA-1-it2-e2`
**Estimated time:** 45 min
**Branch:** `feat/PLANT-OPA-1-it2-e2` (same branch)
**CP BackEnd pattern:** N/A

**What to do:**
Extend `.github/workflows/waooaw-deploy.yml` with two additions:
1. A `docker build` + `docker push` step for the `plant-opa` image — same pattern as
   the existing `plant-gateway` build step (lines ~297-302). Build from
   `src/Plant/Gateway/opa/` using `src/Plant/Gateway/opa/Dockerfile`. Tag with both
   `<TAG>` and `<environment>-latest`.
2. Add `-var="plant_opa_image=$GCP_REGISTRY/plant-opa:${TAG}"` to every Terraform apply
   invocation that deploys the plant stack (search for `-var="plant_gateway_image=` to find
   all locations).

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `.github/workflows/waooaw-deploy.yml` | 283–310 | `plant-gateway` build/push step pattern to copy exactly |
| `.github/workflows/waooaw-deploy.yml` | 360–420 | All Terraform `-var` lines that need `plant_opa_image` added |

**Files to modify:**

| File | Action | Precise instruction |
|---|---|---|
| `.github/workflows/waooaw-deploy.yml` | modify | Add plant-opa build step + add -var to all plant stack terraform apply calls |

**Code patterns to copy exactly:**

```yaml
# Pattern 1: Add the plant-opa build/push step.
# Place immediately after the plant-gateway build/push block (search for "plant-gateway:${TAG}").
# Copy the plant-gateway block exactly and change:
#   - "plant-gateway" → "plant-opa"
#   - context: "src/Plant/Gateway" → "src/Plant/Gateway/opa"
#   - dockerfile: use the opa Dockerfile explicitly

          - name: Build and push plant-opa image
            run: |
              docker build \
                -f src/Plant/Gateway/opa/Dockerfile \
                -t "${{ env.GCP_REGISTRY }}/plant-opa:${TAG}" \
                -t "${{ env.GCP_REGISTRY }}/plant-opa:${{ inputs.environment }}-latest" \
                src/Plant/Gateway/opa/
              docker push "${{ env.GCP_REGISTRY }}/plant-opa:${TAG}"
              docker push "${{ env.GCP_REGISTRY }}/plant-opa:${{ inputs.environment }}-latest"
```

```yaml
# Pattern 2: Add this -var to every terraform apply that deploys the plant stack.
# Find all occurrences of: -var="plant_gateway_image=${{ env.GCP_REGISTRY }}/plant-gateway:${TAG}"
# On the next line (or following the plant_gateway_image -var), add:
              -var="plant_opa_image=${{ env.GCP_REGISTRY }}/plant-opa:${TAG}" \
```

**Acceptance criteria:**
1. `.github/workflows/waooaw-deploy.yml` builds and pushes `plant-opa` image using the Dockerfile from `src/Plant/Gateway/opa/`.
2. Every Terraform apply call that includes `-var="plant_gateway_image=..."` also includes `-var="plant_opa_image=..."`.
3. YAML is syntactically valid.
4. The image name is `plant-opa` (matches the GCP registry conventions for other services).

**Tests to write:**

| Test ID | What to check | Command |
|---|---|---|
| E2-S3-T1 | YAML valid | `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/waooaw-deploy.yml')); print('valid')"` |
| E2-S3-T2 | plant-opa build step exists | `grep -c "plant-opa" .github/workflows/waooaw-deploy.yml` → ≥ 4 |
| E2-S3-T3 | plant_opa_image var in terraform apply | `grep -c "plant_opa_image" .github/workflows/waooaw-deploy.yml` → same count as `plant_gateway_image` occurrences |

**Test command:**
```bash
# YAML valid
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/waooaw-deploy.yml')); print('YAML valid')"

# plant-opa references exist
grep -c "plant-opa" .github/workflows/waooaw-deploy.yml

# plant_opa_image var count matches plant_gateway_image var count
echo "plant_opa_image count:   $(grep -c 'plant_opa_image' .github/workflows/waooaw-deploy.yml)"
echo "plant_gateway_image count: $(grep -c 'plant_gateway_image' .github/workflows/waooaw-deploy.yml)"
# These should be equal
```

**Commit message:** `feat(PLANT-OPA-1): add plant-opa build/push and terraform var to waooaw-deploy.yml`

**Done signal:** `"E2-S3 done. Changed: waooaw-deploy.yml. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

## Post-Merge Verification (run after Iteration 2 PR merges and deploy workflow completes)

```bash
# 1. Check OPA Cloud Run service is running
gcloud run services list --region=asia-south1 --project=waooaw-oauth | grep plant-opa

# 2. Verify OPA service URL matches what's in plant_gateway env
gcloud run services describe waooaw-plant-opa-demo \
  --region=asia-south1 --project=waooaw-oauth --format='value(status.url)'

# 3. Check Plant Gateway is getting OPA decisions (RBAC logs)
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="waooaw-plant-gateway-demo" AND jsonPayload.message:"RBAC allowed"' \
  --project=waooaw-oauth --limit=10 --freshness=1h 2>&1

# 4. Confirm no more "OPA RBAC query timeout" errors
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="waooaw-plant-gateway-demo" AND jsonPayload.message:"OPA RBAC query timeout"' \
  --project=waooaw-oauth --limit=5 --freshness=1h 2>&1
```
