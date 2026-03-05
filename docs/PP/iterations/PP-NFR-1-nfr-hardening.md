# PP-NFR-1 — PP Backend NFR Hardening

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `PP-NFR-1` |
| Feature area | PP BackEnd — Platform NFR Standards & Image Promotion Safety |
| Created | 2026-03-05 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CONTEXT_AND_INDEX.md` §5.6 — Platform NFR Standards |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 2 |
| Total epics | 9 |
| Total stories | 9 |

---

## Zero-Cost Agent Constraints (READ FIRST)

This plan is designed for **autonomous zero-cost model agents** (Gemini Flash, GPT-4o-mini, etc.)
with limited context windows. Every structural decision exists to preserve context.

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is fully self-contained — no cross-references, no "see above" |
| No working memory across files | NFR code patterns are embedded **inline** in each story |
| No planning ability | Stories are atomic — one deliverable, one set of files, one test command |
| Token cost per file read | Max 3 files to read per story — pre-identified by PM in the card |
| Binary inference only | Acceptance criteria are pass/fail — no judgment calls required from the agent |

> **Agent:** Execute exactly ONE story at a time. Read your assigned story card fully, then act.
> Do NOT read other stories. Do NOT open NFRReusable.md. All patterns you need are in your card.
> Do NOT read files not listed in your story card's "Files to read first" section.
> **EXCEPTION: `src/PP/BackEnd/api/db_updates.py` — DO NOT TOUCH THIS FILE under any circumstances.**

---

## PM Review Checklist

- [x] Epic titles name IT ops outcomes, not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR code snippets inline
- [x] Every story card has max 3 files in "Files to read first"
- [x] Every new backend route story embeds the `waooaw_router()` snippet
- [x] Every story that adds env vars lists exact Terraform file paths
- [x] Every story has `BLOCKED UNTIL` (or "none")
- [x] Each iteration has a time estimate and come-back datetime
- [x] Each iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] No placeholders remain
- [x] db_updates.py is explicitly excluded from scope in every iteration

---

## Vision Intake

1. **Area:** PP BackEnd — all non-db_updates routes
2. **Outcome:** IT ops and support can trust that PP BackEnd meets all WAOOAW platform NFR standards — no raw PII in logs, all sensitive mutations have audit trails, the image fails fast on missing secrets rather than running with placeholder values, the Docker image promotes correctly through demo→uat→prod with no environment-baked logic.
3. **Out of scope:** DB Management screen (`db_updates.py`) — preserved as-is. PP FrontEnd changes. Any new functional endpoints.
4. **Lane:** A — all changes within existing PP BackEnd code and Terraform; no new Plant endpoints needed.
5. **Urgency:** None.

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Secrets safety, Terraform alignment, PII masking, Audit wiring, Env gates | E1–E5 | 5 | 3h | 2026-03-05 06:00 UTC |
| 2 | Config deduplication, OTel spans, Prometheus metrics, Health probe | E6–E9 | 4 | 3h | 2026-03-05 09:00 UTC |

**Estimate basis:** Config fix = 30 min | Terraform 5-file update = 30 min | PII wiring = 30 min | Audit wiring 6 files = 45 min | Env gate = 30 min | Main cleanup = 30 min | OTel spans = 45 min | Prometheus metrics = 45 min | Health probe = 30 min. Add 20% buffer.

---

## Agent Execution Rules

1. **Start**: `git status && git log --oneline -3` — must be on `main` with clean tree.
2. **Branch**: create the exact branch listed in the story card before touching any file.
3. **Test**: run the exact test command in the story card before marking done.
4. **db_updates.py**: `src/PP/BackEnd/api/db_updates.py` is **permanently excluded**. Do not read, modify, or move it.
5. **STUCK PROTOCOL**: If blocked for more than 15 min on a single story, open a draft PR titled `WIP: PP-NFR-1 [story-id] — [blocker description]`. Post the PR URL, then HALT. Do not continue to the next story.
6. **PR**: One PR per iteration. Squash-merge to `main`. Title: `feat(pp-nfr-1): iteration N — [scope]`.

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
3. Click the model dropdown → select **Agent mode**
4. Click `+` (new conversation)
5. Type `@` → select **platform-engineer** from the agent list
6. Paste the task below and press **Enter**
7. Come back at: **2026-03-05 06:00 UTC**

**Iteration 1 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python/FastAPI security engineer + Senior Terraform/GCP Cloud Run engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/PP/iterations/PP-NFR-1-nfr-hardening.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2, E3, E4, E5. Do not touch Iteration 2 content.
TIME BUDGET: 3h. If you reach 3h15m without finishing, follow STUCK PROTOCOL now.

CRITICAL: NEVER touch src/PP/BackEnd/api/db_updates.py under any circumstances.

EXECUTION ORDER:
1. Run: git status && git log --oneline -3
   You must be on main with a clean tree. If not, post why and HALT.
2. Read the "Agent Execution Rules" section in this plan file.
3. Read the "Iteration 1" section in this plan file.
4. Read nothing else before starting.
5. Execute Epics in this order: E1 → E2 → E3 → E4 → E5
6. When all epics are docker-tested, open the iteration PR. Post the PR URL. HALT.
```

**When you return:** Check Copilot Chat for a PR URL. If you see a draft PR titled `WIP:` — an agent got stuck. Read the PR comment for the exact blocker.

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Verify merge first:**
```bash
git fetch origin && git log --oneline origin/main | head -3
# Must show: feat(pp-nfr-1): iteration 1 — secrets, pii, audit, env-gates
```

**Iteration 2 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python/FastAPI observability engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/PP/iterations/PP-NFR-1-nfr-hardening.md
YOUR SCOPE: Iteration 2 only — Epics E6, E7, E8, E9. Do not touch Iteration 1 content.
TIME BUDGET: 3h. If you reach 3h15m without finishing, follow STUCK PROTOCOL now.

CRITICAL: NEVER touch src/PP/BackEnd/api/db_updates.py under any circumstances.

PREREQUISITE CHECK (do before anything else):
  Run: git log --oneline origin/main | head -5
  Must show: feat(pp-nfr-1): iteration 1 commit. If not — HALT and tell the user.

EXECUTION ORDER:
1. Run prerequisite check above.
2. Read the "Agent Execution Rules" section in this plan file.
3. Read the "Iteration 2" section in this plan file.
4. Execute Epics: E6 → E7 → E8 → E9
5. When all epics are docker-tested, open the iteration PR. Post the PR URL. HALT.
```

Come back at: **2026-03-05 09:00 UTC**

---

## Iteration 1 — Secrets Safety, Terraform Alignment, PII, Audit, Env Gates

**Scope:** IT ops team can rely on PP BackEnd failing fast at startup if secrets are absent, never logging raw PII, recording audit trails for every sensitive mutation, and running with environment-appropriate gates on dev-only endpoints.
**Lane:** A (existing code only — no new Plant endpoints)
**⏱ Estimated:** 3h | **Come back:** 2026-03-05 06:00 UTC
**Prerequisite:** clean `main` branch

### Dependency Map (Iteration 1)

```
E1 (config safety) ──► independent
E2 (terraform align) ──► independent
E3 (PII masking) ──► independent
E4 (audit wiring) ──► independent
E5 (env gates) ──► depends on E1 (ENABLE_DEV_TOKEN field needed in Settings)
```

---

### Epic E1: PP startup fails fast when secrets are absent

**Branch:** `feat/pp-nfr-1-it1-e1-secret-safety`
**User story:** As an IT ops engineer, I know the PP backend will not start silently with a guessable JWT signing key, so that compromised tokens are impossible in UAT and prod.

---

#### Story E1-S1: Remove hardcoded secret fallbacks — BACKEND

**BLOCKED UNTIL:** none
**Estimated time:** 30 min
**Branch:** `feat/pp-nfr-1-it1-e1-secret-safety`

**What to do:**
Three files currently silently accept a placeholder secret. Change `JWT_SECRET` default in `config.py` from the literal `"dev-secret-change-in-production"` to empty string `""` and add a Pydantic `@validator` that raises `ValueError` at app startup when empty. Remove the `or "dev-secret"` fallback literals from the two service files. This ensures a promoted image to UAT/prod fails with a clear startup error rather than signing tokens with a known key.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/BackEnd/core/config.py` | 1–65 | `JWT_SECRET` field definition, existing validators, `model_config` block |
| `src/PP/BackEnd/services/exchange_credentials.py` | 30–50 | `or "dev-secret"` fallback line |
| `src/PP/BackEnd/services/agent_setups.py` | 30–50 | `or "dev-secret"` fallback line |

**Files to modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/BackEnd/core/config.py` | modify | Change `JWT_SECRET: str = "dev-secret-change-in-production"` to `JWT_SECRET: str = ""`. Add Pydantic v2 `@model_validator(mode="after")` that raises `ValueError("JWT_SECRET must be set — refusing to start with empty secret")` when `self.JWT_SECRET == ""` and `self.ENVIRONMENT not in {"development", "codespace", "test"}`. Also change `DATABASE_URL: str = "sqlite:///./waooaw_pp.db"` to `DATABASE_URL: str = ""`. |
| `src/PP/BackEnd/services/exchange_credentials.py` | modify | Replace the line `secret = (os.getenv("PP_EXCHANGE_CREDENTIALS_SECRET") or os.getenv("JWT_SECRET") or "dev-secret").strip()` with `secret = (os.getenv("PP_EXCHANGE_CREDENTIALS_SECRET") or os.getenv("JWT_SECRET") or "").strip()` then add: `if not secret: raise RuntimeError("PP_EXCHANGE_CREDENTIALS_SECRET or JWT_SECRET must be set")` |
| `src/PP/BackEnd/services/agent_setups.py` | modify | Same pattern as exchange_credentials.py — remove `or "dev-secret"` fallback, add RuntimeError if empty |

**Code patterns to copy exactly:**
```python
# src/PP/BackEnd/core/config.py — add after existing field definitions
from pydantic import model_validator

class Settings(BaseSettings):
    # ... existing fields ...
    JWT_SECRET: str = ""          # Must be injected via GCP Secret Manager in UAT/prod
    DATABASE_URL: str = ""        # Must be injected at runtime; no SQLite default

    @model_validator(mode="after")
    def _require_secrets_in_live_envs(self) -> "Settings":
        live = {"demo", "uat", "prod", "production"}
        if self.ENVIRONMENT.lower() in live and not self.JWT_SECRET:
            raise ValueError(
                "JWT_SECRET must be set — refusing to start with empty secret. "
                "Inject via GCP Secret Manager."
            )
        return self
```

**Acceptance criteria:**
1. `Settings(ENVIRONMENT="uat", JWT_SECRET="")` raises `ValueError` at instantiation
2. `Settings(ENVIRONMENT="codespace", JWT_SECRET="")` does NOT raise (local dev allowed)
3. `exchange_credentials.py` raises `RuntimeError` when both env vars are empty
4. `agent_setups.py` raises `RuntimeError` when both env vars are empty
5. All 3 literal occurrences of `"dev-secret"` or `"dev-secret-change-in-production"` are gone from the codebase (verify with `grep -r "dev-secret" src/PP/BackEnd/`)

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S1-T1 | `src/PP/BackEnd/tests/test_config.py` | Instantiate `Settings(ENVIRONMENT="uat", JWT_SECRET="")` | `ValueError` raised |
| E1-S1-T2 | `src/PP/BackEnd/tests/test_config.py` | Instantiate `Settings(ENVIRONMENT="codespace", JWT_SECRET="")` | No error raised |
| E1-S1-T3 | `src/PP/BackEnd/tests/test_config.py` | Instantiate `Settings(ENVIRONMENT="demo", JWT_SECRET="real-secret-value")` | No error, `settings.JWT_SECRET == "real-secret-value"` |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run pp-test \
  pytest src/PP/BackEnd/tests/test_config.py -v --cov=src/PP/BackEnd/core/config --cov-fail-under=80
```

**Commit message:** `feat(pp-nfr-1): remove hardcoded secret fallbacks, startup safety validator`

**Done signal:** `"E1-S1 done. Tests: T1 ✅ T2 ✅ T3 ✅. Zero 'dev-secret' literals in PP BackEnd."`

---

### Epic E2: PP Terraform promotes one image unchanged through demo→uat→prod

**Branch:** `feat/pp-nfr-1-it1-e2-terraform-align`
**User story:** As an IT ops engineer, I know that deploying a new PP image to UAT or prod never requires editing the Terraform template — only the tfvars values change, so environment-specific logic cannot be accidentally hardcoded.

---

#### Story E2-S1: Move baked env ternaries to tfvars — TERRAFORM

**BLOCKED UNTIL:** none
**Estimated time:** 30 min
**Branch:** `feat/pp-nfr-1-it1-e2-terraform-align`

**What to do:**
`cloud/terraform/stacks/pp/main.tf` currently contains two ternary expressions that bake environment-name logic into the Terraform template — a violation of the image promotion mandate. Move `ENABLE_DB_UPDATES` and `ALLOWED_EMAIL_DOMAINS` to per-environment tfvars. Add a new `ENABLE_DEV_TOKEN` variable (off by default everywhere) to support the env gate story (E5). Also add `ENABLE_METERING_DEBUG` variable.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `cloud/terraform/stacks/pp/main.tf` | 60–100 | Ternary expressions for `ENABLE_DB_UPDATES` and `ALLOWED_EMAIL_DOMAINS` |
| `cloud/terraform/stacks/pp/variables.tf` | 1–end | Existing variable declarations to understand naming convention |
| `cloud/terraform/stacks/pp/environments/demo.tfvars` | 1–end | Existing variable assignments to mirror format |

**Files to modify:**

| File | Action | Precise instruction |
|---|---|---|
| `cloud/terraform/stacks/pp/main.tf` | modify | Replace `ENABLE_DB_UPDATES = (var.environment == "demo" \|\| var.environment == "uat") ? "true" : "false"` with `ENABLE_DB_UPDATES = var.enable_db_updates`. Replace `ALLOWED_EMAIL_DOMAINS = var.environment == "demo" ? "dlaisd.com,waooaw.com,gmail.com,googlemail.com" : "dlaisd.com,waooaw.com"` with `ALLOWED_EMAIL_DOMAINS = var.allowed_email_domains`. Add `ENABLE_DEV_TOKEN = var.enable_dev_token` and `ENABLE_METERING_DEBUG = var.enable_metering_debug` to `env_vars` block. |
| `cloud/terraform/stacks/pp/variables.tf` | modify | Add four new variable blocks (see code pattern below) |
| `cloud/terraform/stacks/pp/environments/demo.tfvars` | modify | Add `enable_db_updates = "true"`, `allowed_email_domains = "dlaisd.com,waooaw.com,gmail.com,googlemail.com"`, `enable_dev_token = "false"`, `enable_metering_debug = "false"` |
| `cloud/terraform/stacks/pp/environments/uat.tfvars` | modify | Add `enable_db_updates = "true"`, `allowed_email_domains = "dlaisd.com,waooaw.com"`, `enable_dev_token = "false"`, `enable_metering_debug = "false"` |
| `cloud/terraform/stacks/pp/environments/prod.tfvars` | modify | Add `enable_db_updates = "false"`, `allowed_email_domains = "dlaisd.com,waooaw.com"`, `enable_dev_token = "false"`, `enable_metering_debug = "false"` |

**Code patterns to copy exactly:**
```hcl
# Add to cloud/terraform/stacks/pp/variables.tf:

variable "enable_db_updates" {
  description = "Enable break-glass DB update endpoints (true for demo/uat, false for prod)"
  type        = string
  default     = "false"
}

variable "allowed_email_domains" {
  description = "Comma-separated list of allowed email domains for PP admin login"
  type        = string
  default     = "dlaisd.com,waooaw.com"
}

variable "enable_dev_token" {
  description = "Enable /auth/dev-token endpoint (development only — always false in UAT/prod)"
  type        = string
  default     = "false"
}

variable "enable_metering_debug" {
  description = "Enable /metering/debug endpoints (development only — always false in UAT/prod)"
  type        = string
  default     = "false"
}
```

**Acceptance criteria:**
1. `cloud/terraform/stacks/pp/main.tf` contains zero ternary expressions (`? "true" : "false"` or `? "dlaisd.com` strings)
2. All four new variables declared in `variables.tf` with `default`
3. All four variables explicitly set in `demo.tfvars`, `uat.tfvars`, `prod.tfvars`
4. `terraform validate` passes in `cloud/terraform/stacks/pp/` (run: `cd cloud/terraform/stacks/pp && terraform init -backend=false && terraform validate`)
5. `src/PP/BackEnd/core/config.py` already has matching `ENABLE_DEV_TOKEN: bool = False` and `ENABLE_METERING_DEBUG: bool = False` fields (add them if absent)

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S1-T1 | terminal | `cd cloud/terraform/stacks/pp && terraform init -backend=false && terraform validate` | Exit code 0, "Success!" in output |

**Test command:**
```bash
cd cloud/terraform/stacks/pp && terraform init -backend=false && terraform validate
```

**Commit message:** `feat(pp-nfr-1): move PP env ternaries to tfvars, add ENABLE_DEV_TOKEN + ENABLE_METERING_DEBUG`

**Done signal:** `"E2-S1 done. terraform validate ✅. No ternaries in main.tf env_vars block."`

---

### Epic E3: PP backend never logs raw PII

**Branch:** `feat/pp-nfr-1-it1-e3-pii-masking`
**User story:** As an IT ops engineer, I know that PP backend logs never contain raw email addresses, phone numbers, or IP addresses — protecting user privacy in Cloud Logging.

---

#### Story E3-S1: Wire PIIMaskingFilter at root logger — BACKEND

**BLOCKED UNTIL:** none
**Estimated time:** 30 min
**Branch:** `feat/pp-nfr-1-it1-e3-pii-masking`

**What to do:**
PP BackEnd has no `core/logging.py` and no `PIIMaskingFilter`. Create `src/PP/BackEnd/core/logging.py` with the `PIIMaskingFilter` class (copy from Plant pattern). Wire it at the root logger in `main_proxy.py` at startup so all loggers across all modules are automatically protected.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/BackEnd/main_proxy.py` | 1–40 | Import block and app startup sequence — where to add the filter call |
| `src/PP/BackEnd/core/observability.py` | 1–30 | Import pattern to follow for the new core/logging.py module |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/BackEnd/core/logging.py` | create | New file with `PIIMaskingFilter` class as shown in code pattern below |
| `src/PP/BackEnd/main_proxy.py` | modify | After the `setup_pp_observability()` call at the top, add: `import logging as _logging` and `from core.logging import PIIMaskingFilter as _PIIMaskingFilter` then `_logging.getLogger().addFilter(_PIIMaskingFilter())` |

**Code patterns to copy exactly:**
```python
# src/PP/BackEnd/core/logging.py  (create this file)
"""PP BackEnd — PII masking log filter.

Wired at root logger in main_proxy.py. All module loggers inherit it automatically.
Masks email, phone numbers, and IP addresses before emission to Cloud Logging.
"""
from __future__ import annotations

import logging
import re


class PIIMaskingFilter(logging.Filter):
    """Masks PII in any log record before emission. Zero-overhead when no PII present."""

    _EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
    _PHONE_RE = re.compile(r'(\+?\d{1,3})[\s\-]?\d{3,5}[\s\-]?\d{4,6}')
    _IP_LAST  = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3})\.\d{1,3}')

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._mask(str(record.msg))
        record.args = tuple(self._mask(str(a)) for a in (record.args or ()))
        return True

    def _mask(self, text: str) -> str:
        text = self._EMAIL_RE.sub(lambda m: self._mask_email(m.group()), text)
        text = self._PHONE_RE.sub(
            lambda m: m.group(1) + "******" + m.group()[-4:], text
        )
        text = self._IP_LAST.sub(r'\1.XXX', text)
        return text

    @staticmethod
    def _mask_email(email: str) -> str:
        user, domain = email.split("@", 1)
        return f"{user[0]}***@{domain}"

# Wire at startup — call this once in main_proxy.py:
#   from core.logging import PIIMaskingFilter
#   logging.getLogger().addFilter(PIIMaskingFilter())
```

**Acceptance criteria:**
1. `src/PP/BackEnd/core/logging.py` exists with `PIIMaskingFilter`
2. `main_proxy.py` calls `logging.getLogger().addFilter(PIIMaskingFilter())` before any route is registered
3. `PIIMaskingFilter().filter(record)` with `record.msg = "user@example.com logged in"` returns `True` and `record.msg` becomes `"u***@example.com logged in"`
4. `grep -rn "PIIMaskingFilter" src/PP/BackEnd/main_proxy.py` returns a match

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S1-T1 | `src/PP/BackEnd/tests/test_config.py` (or new `test_logging.py`) | Create `PIIMaskingFilter`, build LogRecord with `msg="admin@waooaw.com"`, call `.filter(record)` | `record.msg == "a***@waooaw.com"` |
| E3-S1-T2 | same | `msg="IP 192.168.1.145 access"` | `record.msg == "IP 192.168.1.XXX access"` |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run pp-test \
  pytest src/PP/BackEnd/tests/test_logging.py -v
```

**Commit message:** `feat(pp-nfr-1): add PIIMaskingFilter, wire at root logger in main_proxy.py`

**Done signal:** `"E3-S1 done. Tests: T1 ✅ T2 ✅. core/logging.py created and wired."`

---

### Epic E4: Every sensitive PP mutation has an audit trail

**Branch:** `feat/pp-nfr-1-it1-e4-audit-wiring`
**User story:** As an IT ops engineer, I have a complete audit record of every agent type change, credential upsert, authentication event, and security action — with no gaps — so compliance reviews can trace all admin operations.

---

#### Story E4-S1: Wire audit dependency into 6 missing route files — BACKEND

**BLOCKED UNTIL:** none
**Estimated time:** 45 min
**Branch:** `feat/pp-nfr-1-it1-e4-audit-wiring`

**What to do:**
`src/PP/BackEnd/services/audit_dependency.py` already provides `AuditLogger` and `get_audit_logger`. Currently only `agents.py`, `approvals.py`, and `genesis.py` import and use it. Wire it into the 6 remaining route files that have sensitive mutations. Also add `Depends(get_audit_log)` to the app-level `dependencies=[]` in `main_proxy.py` (platform standard requires both `require_correlation_id` and `get_audit_log` at app level). **Do not touch `db_updates.py`.**

Files needing audit wiring:
- `src/PP/BackEnd/api/agent_setups.py` — upsert/list credentials
- `src/PP/BackEnd/api/agent_types.py` — PUT agent type updates
- `src/PP/BackEnd/api/auth.py` — Google verify, dev-token issue, logout
- `src/PP/BackEnd/api/exchange_credentials.py` — PUT exchange credential upsert
- `src/PP/BackEnd/api/metering_debug.py` — POST mint envelope
- `src/PP/BackEnd/api/security.py` — any admin security actions

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/BackEnd/services/audit_dependency.py` | 1–end | `AuditLogger` class interface, `get_audit_logger` signature |
| `src/PP/BackEnd/api/agents.py` | 1–50 | How `AuditLogger` is imported and called — copy this exact pattern |
| `src/PP/BackEnd/api/agent_setups.py` | 1–end | Current route signatures to see where to inject `audit: AuditLogger = Depends(get_audit_logger)` |

**Code patterns to copy exactly:**
```python
# Import to add at top of each of the 6 files:
from services.audit_dependency import AuditLogger, get_audit_logger  # PP-N4

# Add to each mutating route function signature:
audit: AuditLogger = Depends(get_audit_logger),

# Call after successful operation (fire-and-forget, never blocks response):
await audit.log(
    screen="pp_agent_types",          # use file-specific screen name
    action="agent_type_updated",      # use operation-specific action
    outcome="success",
    user_id=None,                     # extract from request if available
    detail=f"agent_type_id={agent_type_id}",
)

# For auth.py — add to /auth/google/verify route:
await audit.log(
    screen="pp_auth",
    action="google_login",
    outcome="success",
    email=idinfo.get("email"),        # AuditLogger masks PII automatically
)
```

**For main_proxy.py — add get_audit_log to app-level deps:**
```python
# main_proxy.py — import the audit dependency:
from services.audit_dependency import get_audit_logger

# Modify the FastAPI() constructor to add get_audit_logger:
app = FastAPI(
    ...
    dependencies=[
        Depends(require_correlation_id),  # already present
        Depends(get_audit_logger),         # ADD THIS
    ],
)
```

**Acceptance criteria:**
1. All 6 files import `from services.audit_dependency import AuditLogger, get_audit_logger`
2. Every mutating route in those 6 files has `audit: AuditLogger = Depends(get_audit_logger)` in its signature
3. Every mutating route calls `await audit.log(...)` after the successful operation
4. `main_proxy.py` FastAPI constructor has `Depends(get_audit_logger)` in `dependencies=[]`
5. `grep -rn "get_audit_logger" src/PP/BackEnd/api/` returns ≥ 9 matches (3 existing + 6 new)
6. `db_updates.py` is unchanged — verify with `git diff src/PP/BackEnd/api/db_updates.py` showing no changes

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E4-S1-T1 | `src/PP/BackEnd/tests/test_agent_types_routes.py` | `PUT /agent-types/{id}` with valid admin token, mock audit to capture calls | `audit_mock.log` called once with `action="agent_type_updated"` |
| E4-S1-T2 | `src/PP/BackEnd/tests/test_audit_routes.py` | `POST /auth/google/verify` with mocked Google token | `audit_mock.log` called with `screen="pp_auth"` |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run pp-test \
  pytest src/PP/BackEnd/tests/test_agent_types_routes.py src/PP/BackEnd/tests/test_audit_routes.py -v --cov-fail-under=80
```

**Commit message:** `feat(pp-nfr-1): wire audit dependency into 6 route files + app-level deps`

**Done signal:** `"E4-S1 done. Tests: T1 ✅ T2 ✅. 9+ get_audit_logger usages in api/."`

---

### Epic E5: Dev-only PP endpoints are inaccessible in UAT and prod

**Branch:** `feat/pp-nfr-1-it1-e5-env-gates`
**User story:** As an IT ops engineer, I know that `/auth/dev-token` and metering debug endpoints are completely unreachable in UAT and production environments, so a misconfigured deployment cannot expose unauthenticated token generation.

---

#### Story E5-S1: Add ENABLE_DEV_TOKEN and ENABLE_METERING_DEBUG gates — BACKEND

**BLOCKED UNTIL:** E1-S1 merged (needs `ENABLE_DEV_TOKEN: bool = False` field in Settings from E1)
**Estimated time:** 30 min
**Branch:** `feat/pp-nfr-1-it1-e5-env-gates`

**What to do:**
Add `ENABLE_DEV_TOKEN: bool = False` and `ENABLE_METERING_DEBUG: bool = False` to `Settings` in `config.py` (if not already added in E1 fix). Wire a startup guard in `auth.py` for the `/auth/dev-token` route and in `metering_debug.py` for all routes. The guard pattern mirrors the existing `_enforce_enabled(app_settings)` pattern used by `db_updates.py`.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/BackEnd/api/db_updates.py` | 55–75 | `_enforce_enabled()` pattern and `ENABLE_DB_UPDATES` check — copy exactly |
| `src/PP/BackEnd/api/auth.py` | 185–210 | `/auth/dev-token` route signature to add guard call |
| `src/PP/BackEnd/api/metering_debug.py` | 1–end | Route signatures to protect |

**Code patterns to copy exactly:**
```python
# Pattern copied from db_updates.py — apply in auth.py and metering_debug.py:
def _enforce_dev_token_enabled(app_settings: Settings) -> None:
    """Raise 404 unless ENABLE_DEV_TOKEN is explicitly on."""
    if not app_settings.ENABLE_DEV_TOKEN:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

# Wire into /auth/dev-token route:
@router.post("/dev-token", response_model=TokenResponse)
async def dev_token(
    app_settings: Settings = Depends(get_settings),
) -> TokenResponse:
    _enforce_dev_token_enabled(app_settings)   # ← add as FIRST line
    ...

# In metering_debug.py — add at top of every @router route:
def _enforce_metering_debug_enabled(app_settings: Settings) -> None:
    if not app_settings.ENABLE_METERING_DEBUG:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
```

**Config fields to add to `src/PP/BackEnd/core/config.py` if not present from E1:**
```python
# Admin tools (disabled by default; enable only in safe environments)
ENABLE_AGENT_SEEDING: bool = False     # already exists
ENABLE_DB_UPDATES: bool = False        # already exists
ENABLE_DEV_TOKEN: bool = False         # ADD if not added in E1
ENABLE_METERING_DEBUG: bool = False    # ADD if not added in E1
```

**Acceptance criteria:**
1. `POST /auth/dev-token` with `ENABLE_DEV_TOKEN=False` returns HTTP 404
2. `POST /auth/dev-token` with `ENABLE_DEV_TOKEN=True` proceeds normally
3. All routes in `metering_debug.py` return HTTP 404 when `ENABLE_METERING_DEBUG=False`
4. `grep -n "ENABLE_DEV_TOKEN\|ENABLE_METERING_DEBUG" src/PP/BackEnd/core/config.py` returns 2 matches
5. `db_updates.py` is unchanged

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E5-S1-T1 | `src/PP/BackEnd/tests/test_pp_admin_auth.py` | Mock `get_settings` with `ENABLE_DEV_TOKEN=False`, call `POST /auth/dev-token` | Response 404 |
| E5-S1-T2 | `src/PP/BackEnd/tests/test_metering_debug.py` | Mock `get_settings` with `ENABLE_METERING_DEBUG=False`, call metering endpoint | Response 404 |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run pp-test \
  pytest src/PP/BackEnd/tests/test_pp_admin_auth.py src/PP/BackEnd/tests/test_metering_debug.py -v --cov-fail-under=80
```

**Commit message:** `feat(pp-nfr-1): ENABLE_DEV_TOKEN and ENABLE_METERING_DEBUG env gates`

**Done signal:** `"E5-S1 done. Tests: T1 ✅ T2 ✅ dev-token and metering debug gated."`

---

## Iteration 2 — Config Deduplication, OTel Spans, Prometheus Metrics, Health Probe

**Scope:** IT ops and SRE can trace individual PP operations in Cloud Trace, alert on PP-specific error rates and latency in Cloud Monitoring, and diagnose downstream failures from the health endpoint — without accessing GCP console for routine investigation.
**Lane:** A (changes within existing PP BackEnd code only)
**⏱ Estimated:** 3h | **Come back:** 2026-03-05 09:00 UTC
**Prerequisite:** Iteration 1 PR merged to `main`

### Dependency Map (Iteration 2)

```
E6 (config dedup) ──► independent, but do first (other stories read Settings)
E7 (OTel spans) ──► independent
E8 (Prometheus metrics) ──► independent
E9 (health probe) ──► independent
```

---

### Epic E6: PP main entry point reads from a single config source

**Branch:** `feat/pp-nfr-1-it2-e6-config-dedup`
**User story:** As a platform engineer, I know there is exactly one source of truth for PP configuration — `core/config.py Settings` — so that a promoted image cannot silently pick up a conflicting `os.getenv()` value.

---

#### Story E6-S1: Remove duplicate os.getenv() calls from main_proxy.py — BACKEND

**BLOCKED UNTIL:** Iteration 1 merged to `main`
**Estimated time:** 30 min
**Branch:** `feat/pp-nfr-1-it2-e6-config-dedup`

**What to do:**
`main_proxy.py` currently declares `ENVIRONMENT`, `PLANT_GATEWAY_URL`, `CORS_ORIGINS`, and `DEBUG_VERBOSE` via raw `os.getenv()` in parallel to `core/config.py Settings`. This means two config systems that can drift. Remove all the top-level `os.getenv()` declarations and replace them with `get_settings()` calls. The `Settings` object already has all these fields.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/BackEnd/main_proxy.py` | 1–80 | All `os.getenv()` and `os.environ` calls in the module — count them |
| `src/PP/BackEnd/core/config.py` | 1–70 | Confirm `ENVIRONMENT`, `PLANT_GATEWAY_URL`, `CORS_ORIGINS`, `DEBUG_VERBOSE` all exist in `Settings` |

**Files to modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/BackEnd/main_proxy.py` | modify | Remove the top-level `ENVIRONMENT = os.getenv(...)`, `PLANT_GATEWAY_URL = os.getenv(...)`, `CORS_ORIGINS = os.getenv(...).split(",")`, `DEBUG_VERBOSE = os.getenv(...)` assignments. Replace any subsequent references — e.g. in `CORSMiddleware`, `health_check` response — with `get_settings().cors_origins_list`, `get_settings().ENVIRONMENT`, `get_settings().DEBUG_VERBOSE`. Remove `import os` if it is no longer used anywhere else in the file. |

**Code patterns to copy exactly:**
```python
# main_proxy.py — after cleanup, initialization looks like:
from core.config import get_settings as _get_settings

_startup_settings = _get_settings()  # read once at module load for CORS etc.

app = FastAPI(
    title="WAOOAW Platform Portal",
    description="Platform Portal - Thin proxy to Plant Gateway",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    dependencies=[
        Depends(require_correlation_id),
        Depends(get_audit_logger),
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_startup_settings.cors_origins_list,  # not os.getenv
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Acceptance criteria:**
1. `grep "os.getenv" src/PP/BackEnd/main_proxy.py` returns zero matches
2. Health endpoint still returns `{"status": "healthy", "service": "pp-proxy"}`
3. CORS middleware uses `settings.cors_origins_list` — not a manually split string
4. All existing tests pass without modification

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E6-S1-T1 | `src/PP/BackEnd/tests/test_health_routes.py` | `GET /health` | Response 200, `status == "healthy"` |
| E6-S1-T2 | terminal grep | `grep "os.getenv" src/PP/BackEnd/main_proxy.py` | Zero matches |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run pp-test \
  pytest src/PP/BackEnd/tests/test_health_routes.py -v
```

**Commit message:** `feat(pp-nfr-1): remove duplicate os.getenv() from main_proxy, consolidate to Settings`

**Done signal:** `"E6-S1 done. Test: T1 ✅. Zero os.getenv() in main_proxy.py."`

---

### Epic E7: Critical PP operations are traceable in Cloud Trace

**Branch:** `feat/pp-nfr-1-it2-e7-otel-spans`
**User story:** As an IT ops engineer, I can open Cloud Trace and find a named span for any PP login, agent create, approval mint, or genesis certification — allowing millisecond-level diagnosis without log trawling.

---

#### Story E7-S1: Add OTel named spans to critical PP routes — BACKEND

**BLOCKED UNTIL:** Iteration 1 merged to `main`
**Estimated time:** 45 min
**Branch:** `feat/pp-nfr-1-it2-e7-otel-spans`

**What to do:**
`core/observability.py` already sets up the OTel tracer provider via `setup_pp_observability()` and exposes a `tracer` object. Add named `tracer.start_as_current_span()` context managers around the business logic in 4 critical routes: `POST /auth/google/verify`, `POST /agents` (agent create), `POST /approvals` (approval mint), `POST /genesis/skills/{id}/certify`.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/BackEnd/core/observability.py` | 1–end | How to import and use the `tracer` — look for `get_tracer()` or module-level `tracer` |
| `src/PP/BackEnd/api/auth.py` | 170–210 | `POST /auth/google/verify` route body — where to wrap with span |
| `src/PP/BackEnd/api/agents.py` | 120–270 | Agent create route body — where to wrap with span |

**Code patterns to copy exactly:**
```python
# In each target route file — import the tracer:
from core.observability import get_pp_tracer  # or however observability.py exports it

# If observability.py doesn't export get_pp_tracer, use opentelemetry directly:
try:
    from opentelemetry import trace as _otel_trace
    _tracer = _otel_trace.get_tracer("pp-backend")
except ImportError:
    _tracer = None  # OTel not installed — no-op

# Usage in route body (wraps the core business logic only, not the whole function):
@router.post("/google/verify", response_model=TokenResponse)
async def google_verify(
    body: GoogleVerifyRequest,
    audit: AuditLogger = Depends(get_audit_logger),
    app_settings: Settings = Depends(get_settings),
) -> TokenResponse:
    span_ctx = _tracer.start_as_current_span("pp.auth.google_verify") if _tracer else nullcontext()
    with span_ctx as span:
        if span and hasattr(span, "set_attribute"):
            span.set_attribute("pp.auth.provider", "google")
        idinfo = await _verify_google_id_token(app_settings, body.credential)
        token = _issue_jwt(app_settings, idinfo)
        await audit.log("pp_auth", "google_login", "success", email=idinfo.get("email"))
        return TokenResponse(access_token=token, ...)
```

**Span names to use (exact):**

| Route | Span name |
|---|---|
| `POST /auth/google/verify` | `pp.auth.google_verify` |
| `POST /agents` (create) | `pp.agents.create` |
| `POST /approvals` (mint) | `pp.approvals.mint` |
| `POST /genesis/skills/{id}/certify` | `pp.genesis.certify_skill` |

**Acceptance criteria:**
1. All 4 routes have `tracer.start_as_current_span(...)` wrapping the core logic
2. If `opentelemetry` package is absent, the route still works (OTel import is guarded by try/except)
3. Span attributes include at least one business identifier (`agent_id`, `skill_id`, etc.)
4. All 4 routes still return correct HTTP responses with valid auth tokens in tests

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E7-S1-T1 | `src/PP/BackEnd/tests/test_proxy.py` | `POST /auth/google/verify` with mocked Google token verify | Response 200, `access_token` present |
| E7-S1-T2 | `src/PP/BackEnd/tests/test_agents_routes.py` | `POST /agents` with valid admin token | Response 201 |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run pp-test \
  pytest src/PP/BackEnd/tests/test_proxy.py src/PP/BackEnd/tests/test_agents_routes.py -v --cov-fail-under=80
```

**Commit message:** `feat(pp-nfr-1): OTel named spans for auth, agent create, approvals, genesis certify`

**Done signal:** `"E7-S1 done. Tests: T1 ✅ T2 ✅. 4 spans added across 4 route files."`

---

### Epic E8: SRE has PP-specific error rate and latency metrics

**Branch:** `feat/pp-nfr-1-it2-e8-prometheus`
**User story:** As an SRE, I can create a Cloud Monitoring alert on PP login failure rate and agent creation latency — without reading raw logs — so I am paged before customers notice.

---

#### Story E8-S1: Create core/metrics.py and wire counters in 3 routes — BACKEND

**BLOCKED UNTIL:** Iteration 1 merged to `main`
**Estimated time:** 45 min
**Branch:** `feat/pp-nfr-1-it2-e8-prometheus`

**What to do:**
Create `src/PP/BackEnd/core/metrics.py` with Prometheus counters and a histogram. Wire `pp_login_total` counter (labels: outcome=success|failure) into `POST /auth/google/verify`, `pp_agent_ops_total` counter into `POST /agents`, `pp_approval_minted_total` into `POST /approvals`. Expose metrics at `GET /metrics` endpoint in `main_proxy.py` if not already there. All Prometheus imports are optional (try/except) so the app runs without prometheus-client installed.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/BackEnd/main_proxy.py` | 60–140 | Whether a `/metrics` endpoint already exists; where to add it |
| `src/PP/BackEnd/api/auth.py` | 170–220 | `POST /auth/google/verify` body — where to increment counter |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/PP/BackEnd/core/metrics.py` | create | New file with optional Prometheus metrics (see code pattern) |
| `src/PP/BackEnd/api/auth.py` | modify | Import `pp_login_counter` from `core.metrics` and call `.labels(outcome="success").inc()` after successful Google verify |
| `src/PP/BackEnd/api/agents.py` | modify | Import `pp_agent_ops_counter` from `core.metrics` and call `.labels(operation="create", outcome="success").inc()` |
| `src/PP/BackEnd/api/approvals.py` | modify | Import `pp_approval_counter` from `core.metrics` and call `.labels(outcome="success").inc()` |
| `src/PP/BackEnd/main_proxy.py` | modify | Add `GET /metrics` endpoint that returns `generate_latest()` if prometheus-client installed, else 501 |

**Code patterns to copy exactly:**
```python
# src/PP/BackEnd/core/metrics.py  (create this file)
"""PP BackEnd — optional Prometheus metrics.

All imports guarded with try/except so the app starts without prometheus-client.
"""
from __future__ import annotations

_PROM_AVAILABLE = False

try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
    _PROM_AVAILABLE = True
except ImportError:
    pass

if _PROM_AVAILABLE:
    pp_login_counter = Counter(
        "pp_login_total",
        "PP admin login attempts",
        ["outcome"],             # outcome: success | failure
    )
    pp_agent_ops_counter = Counter(
        "pp_agent_ops_total",
        "PP agent CRUD operations",
        ["operation", "outcome"],  # operation: create|update|status; outcome: success|failure
    )
    pp_approval_counter = Counter(
        "pp_approval_minted_total",
        "PP approvals minted",
        ["outcome"],
    )
    pp_request_latency = Histogram(
        "pp_request_duration_seconds",
        "PP request latency",
        ["route"],
    )
else:
    # No-op stubs so import never fails
    class _Noop:
        def labels(self, **_): return self
        def inc(self): pass
        def observe(self, _): pass

    pp_login_counter = _Noop()         # type: ignore[assignment]
    pp_agent_ops_counter = _Noop()     # type: ignore[assignment]
    pp_approval_counter = _Noop()      # type: ignore[assignment]
    pp_request_latency = _Noop()       # type: ignore[assignment]

def get_metrics_response():
    """Return (body_bytes, content_type) for /metrics endpoint."""
    if not _PROM_AVAILABLE:
        return None, None
    return generate_latest(), CONTENT_TYPE_LATEST
```

**Acceptance criteria:**
1. `src/PP/BackEnd/core/metrics.py` exists with 4 metric objects
2. `GET /metrics` endpoint returns 200 when prometheus-client is installed, 501 when not
3. `POST /auth/google/verify` success path calls `pp_login_counter.labels(outcome="success").inc()`
4. App starts without error when prometheus-client is NOT installed

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E8-S1-T1 | `src/PP/BackEnd/tests/test_health_and_api_root.py` | `GET /metrics` | Response 200 or 501 (never 500) |
| E8-S1-T2 | `src/PP/BackEnd/tests/test_proxy.py` | Import `core.metrics` with prometheus-client absent (mock import error) | No ImportError raised |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run pp-test \
  pytest src/PP/BackEnd/tests/test_health_and_api_root.py src/PP/BackEnd/tests/test_proxy.py -v
```

**Commit message:** `feat(pp-nfr-1): Prometheus metrics in core/metrics.py, wire into auth/agents/approvals`

**Done signal:** `"E8-S1 done. Tests: T1 ✅ T2 ✅. core/metrics.py created and wired."`

---

### Epic E9: PP health endpoint shows per-component downstream status

**Branch:** `feat/pp-nfr-1-it2-e9-health-probe`
**User story:** As an IT ops engineer, I call `GET /health` and immediately see whether Plant Gateway, the PP database connection, and the overall service are healthy — without opening the GCP console to diagnose an alert.

---

#### Story E9-S1: Enhance /health to probe downstream dependencies — BACKEND

**BLOCKED UNTIL:** Iteration 1 merged to `main`
**Estimated time:** 30 min
**Branch:** `feat/pp-nfr-1-it2-e9-health-probe`

**What to do:**
Extend the existing `GET /health` route in `main_proxy.py` to probe Plant Gateway's own `/health` endpoint via `httpx` and report a per-component status dict. If Plant Gateway is reachable and returns 2xx, `plant_gateway: "healthy"`. If not, `plant_gateway: "degraded"`. The overall `status` becomes `"degraded"` if any component is degraded but does not return 503 (to not break Kubernetes liveness probes). Timeout for the probe: 3 seconds.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/PP/BackEnd/main_proxy.py` | 90–130 | Existing `GET /health` route body and response shape |
| `src/PP/BackEnd/core/config.py` | 40–60 | `PLANT_GATEWAY_URL` / `plant_base_url` property — the URL to probe |

**Code patterns to copy exactly:**
```python
# main_proxy.py — replace existing /health handler:
@app.get("/health")
async def health_check(app_settings: Settings = Depends(get_settings)) -> dict:
    """Deep health probe — checks PP and downstream Plant Gateway."""
    components: dict[str, str] = {}

    # Probe Plant Gateway
    plant_url = (app_settings.plant_base_url or "").rstrip("/")
    if plant_url:
        try:
            async with httpx.AsyncClient(timeout=3.0) as hc:
                resp = await hc.get(f"{plant_url}/health")
            components["plant_gateway"] = "healthy" if resp.status_code < 400 else "degraded"
        except Exception:
            components["plant_gateway"] = "degraded"
    else:
        components["plant_gateway"] = "unconfigured"

    overall = "degraded" if "degraded" in components.values() else "healthy"
    return {
        "status": overall,
        "service": "pp-backend",
        "version": "2.0.0",
        "components": components,
    }
```

**Acceptance criteria:**
1. `GET /health` returns `{"status": ..., "service": "pp-backend", "components": {"plant_gateway": ...}}`
2. When Plant Gateway is unreachable, `plant_gateway == "degraded"` and `status == "degraded"`
3. Response is always HTTP 200 (never 503 — Kubernetes liveness must not fail on degraded downstream)
4. Probe timeout is 3 seconds maximum

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E9-S1-T1 | `src/PP/BackEnd/tests/test_health_routes.py` | Mock `httpx.AsyncClient.get` returns 200 | Response body `status=="healthy"`, `components.plant_gateway=="healthy"` |
| E9-S1-T2 | `src/PP/BackEnd/tests/test_health_routes.py` | Mock `httpx.AsyncClient.get` raises `httpx.ConnectError` | Response 200, `status=="degraded"`, `plant_gateway=="degraded"` |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run pp-test \
  pytest src/PP/BackEnd/tests/test_health_routes.py -v --cov=src/PP/BackEnd --cov-fail-under=80
```

**Commit message:** `feat(pp-nfr-1): deep health probe with per-component Plant Gateway status`

**Done signal:** `"E9-S1 done. Tests: T1 ✅ T2 ✅. /health reports plant_gateway component."`

---

## Rollback

```bash
# If merged iteration causes a regression:
git log --oneline -10 origin/main          # find merge commit SHA
git revert -m 1 <merge-commit-sha>
git push origin main
# Open fix/pp-nfr-1-rollback branch for the root-cause fix
```
