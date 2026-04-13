# DMA-CONV-1 — DMA Conversation-to-Content Pipeline Overhaul

**Objective**
Fix the DMA conversation loop so customers can brief the agent in a structured, concluding conversation → produce a master theme and supporting sub-themes → get schedule approval → generate platform-specific content with brand voice, niche hashtags, and optimized posting times → review content in platform-accurate previews → approve → publish → feed performance data back into the next content cycle. This plan also diagnoses and fixes artifact rendering from DMA-MEDIA-1 (#1035) which is not rendering tables after deploy.

Every story in this plan directly advances DMA value (P1/P2) or DMA enablement (P3/P4). No generic polish.

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `DMA-CONV-1` |
| Feature area | Plant BackEnd (prompt, validation, analytics) + CP FrontEnd (wizard UX, previews) |
| Created | 2026-04-13 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CONTEXT_AND_INDEX.md` §1.1 |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 3 |
| Total epics | 9 |
| Total stories | 15 |

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

## Synthesized Objectives

| # | Objective | DMA Priority | Iteration |
|---|---|---|---|
| O1 | Inject required-fields checklist into prompt so the agent knows exactly when to conclude | P1 | 1 |
| O2 | Lock-and-confirm behaviour: customer answers → dimension locked, never re-asked | P1 | 1 |
| O3 | Send full structured summary as locked context every call (not just last 4 messages) | P1 | 1 |
| O4 | Field-level progress tracking visible to customer ("8/11 locked") | P1 | 1 |
| O5 | Server-side validation gate: all required fields populated before allowing approval_ready | P1 | 1 |
| O6 | When customer requests a deliverable, produce it immediately — no deflection | P1 | 1 |
| O7 | Align workshop summary fields to required-fields list and CampaignBrief model | P1 | 1 |
| O8 | Diagnose and fix artifact rendering from DMA-MEDIA-1 (table not rendering after deploy) | P1 | 1 |
| O9 | Content-pillar framework guidance embedded in prompt (3-5 recurring pillars) | P2 | 2 |
| O10 | Brand voice auto-injection: load existing BrandVoiceModel into conversation and content prompts | P2 | 2 |
| O11 | Competitor/niche context input: prompt asks for competitor names and niche keywords during discovery | P2 | 2 |
| O12 | Niche-specific hashtag and SEO keyword strategy injected into content generation | P2 | 2 |
| O13 | Posting-time optimization: recommend optimal times based on audience and industry data | P2 | 2 |
| O14 | Performance feedback loop: inject content_analytics recommendations into next theme cycle prompt | P4 | 3 |
| O15 | Platform-accurate content previews in the approval UI (YouTube/LinkedIn/Instagram format) | P2 | 3 |

---

## PM Review Checklist

- [x] **EXPERT PERSONAS filled** — each iteration's agent task block has the correct expert persona list
- [x] Epic titles name customer outcomes, not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR code snippets inline — no "see NFRReusable.md"
- [x] Every story card has max 3 files in "Files to read first"
- [x] Every story involving CP BackEnd states the exact pattern: A, B, or C
- [x] Every GET route story card says `get_read_db_session()` not `get_db_session()`
- [x] Every story that adds env vars lists the exact Terraform file paths to update
- [x] Every story has `BLOCKED UNTIL` (or "none")
- [x] Each iteration has a time estimate and come-back datetime
- [x] Each iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] Stories sequenced: backend (S1) before frontend (S2)
- [x] No placeholders remain

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Fix conversation loop — prompt rewrite, required-fields gate, lock-and-confirm, full context injection, progress tracking, artifact rendering fix | 3 | 6 | 6h | 2026-04-14 06:00 UTC |
| 2 | Content quality — brand voice injection, content pillars, competitor/niche input, hashtag/SEO strategy, posting-time optimization | 3 | 5 | 5h | 2026-04-15 06:00 UTC |
| 3 | Feedback loop + platform previews — performance analytics injection, platform-accurate content previews in approval UI | 3 | 4 | 5h | 2026-04-16 06:00 UTC |

**Estimate basis:** FE wiring = 30 min | New BE endpoint = 45 min | Full-stack = 90 min | Prompt rewrite = 90 min | Docker test = 15 min | PR = 10 min. Add 20% buffer for zero-cost model context loading.

**Why 3 iterations:** Iteration 1 fixes the broken conversation loop (customers currently cannot reach theme approval). Iteration 2 makes the content commercially competitive. Iteration 3 closes the autonomous improvement loop. Each is a meaningful product slice that delivers value after merge.

---

## How to Launch Each Iteration

### Iteration 1

**Steps to launch:**
1. Open this repository on GitHub
2. Open the **Agents** tab
3. Start a new agent task
4. If the UI exposes repository agents, select **platform-engineer**; otherwise use the default coding agent
5. Copy the block below and paste it into the task
6. Start the run
7. Go away. Come back at: **2026-04-14 06:00 UTC**

**Iteration 1 agent task** (paste verbatim — do not modify):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI engineer + Senior React/TypeScript engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/DMA-CONV-1-conversation-to-content.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2, E3. Do not touch Iteration 2 or 3 content.
TIME BUDGET: 6h. If you reach 7h without finishing, follow STUCK PROTOCOL now.

ENVIRONMENT REQUIREMENT:
- This task is intended for the GitHub repository Agents tab.
- Shell/git/gh/docker tools may be unavailable on this execution surface.
- Do not HALT only because terminal tools are unavailable; use the GitHub task branch/PR flow for this run.

FAIL-FAST VALIDATION GATE (complete before reading story cards or editing files):
1. Verify the plan file is readable and the assigned iteration section exists.
2. Verify this execution surface allows repository writes on the current task branch.
3. Verify this execution surface allows opening or updating a PR to `main`, or at minimum posting that PR controls are unavailable.
4. If any validation gate fails: post `Blocked at validation gate: [exact reason]` and HALT before code changes.

EXECUTION ORDER:
1. Read the "Agent Execution Rules" section in this plan file.
2. Read the "Iteration 1" section in this plan file.
3. Read nothing else before starting.
4. Work on the GitHub task branch created for this run. Do not assume terminal checkout or manual branch creation.
5. Execute Epics in this order: E1 → E2 → E3
6. Add or update the tests listed in each story before moving on.
7. If this execution surface exposes validation tools, run the narrowest relevant tests and record the result. If not, state: "Validation deferred: GitHub Agents tab on this run did not expose shell/docker test execution."
8. Open or update the iteration PR to `main`, post the PR URL, and HALT.
```

**When you return:** Check Copilot Chat for a PR URL. If you see a draft PR titled `WIP:` — an agent got stuck. Read the PR comment for the exact blocker.

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Prerequisite evidence:**
- Iteration 1 merge status: **MERGED**
- Iteration 1 PR: https://github.com/dlai-sd/WAOOAW/pull/1046
- Merge commit on `main`: `ebba193a`
- Merged at: 2026-04-13 UTC

**Steps to launch:** same as Iteration 1 (GitHub repository → Agents tab)

**Iteration 2 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI engineer + Senior React/TypeScript engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/DMA-CONV-1-conversation-to-content.md
YOUR SCOPE: Iteration 2 only — Epics E4, E5, E6. Do not touch Iteration 3.
TIME BUDGET: 5h.

ENVIRONMENT REQUIREMENT:
- This task is intended for the GitHub repository Agents tab.
- Shell/git/gh/docker tools may be unavailable on this execution surface.
- Do not HALT only because terminal tools are unavailable; use the GitHub task branch/PR flow for this run.

PREREQUISITE CHECK (do before anything else):
  Read the "Prerequisite evidence" block under Iteration 2 in this plan file.
  Treat Iteration 2 as unlaunchable only if that block is still marked pending or does not include both a merged PR reference and a merge commit on `main`.
  If the block is still pending or incomplete: post "Blocked: Iteration 1 merge evidence has not been recorded in the plan." and HALT.

FAIL-FAST VALIDATION GATE (complete before reading story cards or editing files):
1. Verify the plan file is readable and the assigned iteration section exists.
2. Verify the Prerequisite evidence block for Iteration 2 is complete and not pending.
3. Verify this execution surface allows repository writes on the current task branch.
4. Verify this execution surface allows opening or updating a PR to `main`, or at minimum posting that PR controls are unavailable.
5. If any validation gate fails: post `Blocked at validation gate: [exact reason]` and HALT before code changes.

EXECUTION ORDER:
1. Read "Agent Execution Rules" and "Iteration 2" sections. Read nothing else.
2. Work on the GitHub task branch created for this run. Do not assume terminal checkout or manual branch creation.
3. Respect backend-before-frontend ordering in the Dependency Map.
4. Add or update the tests listed in each story before moving on.
5. If this execution surface exposes validation tools, run the narrowest relevant tests and record the result. If not, state: "Validation deferred: GitHub Agents tab on this run did not expose shell/docker test execution."
6. Open or update the iteration PR to `main`, post URL, and HALT.
```

**Come back at:** 2026-04-15 06:00 UTC

---

### Iteration 3

> ⚠️ Do NOT launch until Iteration 2 PR is merged to `main`.

**Prerequisite evidence:**
- Iteration 2 merge status: `[PENDING HUMAN UPDATE BEFORE LAUNCH]`
- Iteration 2 PR: `[PR URL or #NUMBER]`
- Merge commit on `main`: `[FULL SHA]`
- Merged at: `[UTC TIMESTAMP]`

**Steps to launch:** same as Iteration 1 (GitHub repository → Agents tab)

**Iteration 3 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI engineer + Senior React/TypeScript engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/DMA-CONV-1-conversation-to-content.md
YOUR SCOPE: Iteration 3 only — Epics E7, E8, E9. 
TIME BUDGET: 5h.

ENVIRONMENT REQUIREMENT:
- This task is intended for the GitHub repository Agents tab.
- Shell/git/gh/docker tools may be unavailable on this execution surface.
- Do not HALT only because terminal tools are unavailable; use the GitHub task branch/PR flow for this run.

PREREQUISITE CHECK (do before anything else):
  Read the "Prerequisite evidence" block under Iteration 3 in this plan file.
  If the block is still pending or incomplete: post "Blocked: Iteration 2 merge evidence has not been recorded in the plan." and HALT.

FAIL-FAST VALIDATION GATE (complete before reading story cards or editing files):
1. Verify the plan file is readable and the assigned iteration section exists.
2. Verify the Prerequisite evidence block for Iteration 3 is complete and not pending.
3. Verify this execution surface allows repository writes on the current task branch.
4. Verify this execution surface allows opening or updating a PR to `main`.
5. If any validation gate fails: post `Blocked at validation gate: [exact reason]` and HALT before code changes.

EXECUTION ORDER:
1. Read "Agent Execution Rules" and "Iteration 3" sections. Read nothing else.
2. Work on the GitHub task branch created for this run.
3. Respect backend-before-frontend ordering in the Dependency Map.
4. Add or update the tests listed in each story before moving on.
5. Run narrowest relevant tests if tools available. Otherwise state validation deferred.
6. Open or update the iteration PR to `main`, post URL, and HALT.
```

**Come back at:** 2026-04-16 06:00 UTC

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all instructions.

### Rule -2 — Fail-fast validation gate

Before reading story cards in detail or making any code changes, validate all of the following:

- The plan file is readable and your assigned iteration section exists.
- Any required `Prerequisite evidence` block for this iteration is complete and not marked pending.
- The GitHub execution surface lets you save repository changes on the current task branch.
- The GitHub execution surface lets you open or update a PR to `main`, or you can explicitly report that PR controls are unavailable.

If any check fails, post `Blocked at validation gate: [exact reason]` and HALT immediately.

### Rule -1 — Activate Expert Personas (first thing, before Rule 0)

Read the `EXPERT PERSONAS:` field from the task you were given.
Activate each persona now. For every epic you execute, open with one line:

> *"Acting as a [persona], I will [what you're building] by [approach]."*

| Technology area | Expert persona to activate |
|---|---|
| `src/Plant/BackEnd/` | Senior Python 3.11 / FastAPI / SQLAlchemy engineer |
| `src/CP/FrontEnd/` | Senior React / TypeScript engineer |
| `src/CP/BackEnd/` | Senior Python 3.11 / FastAPI engineer (thin proxy only) |

### Rule 0 — Use the GitHub task branch and open the iteration PR early

GitHub-hosted agents usually start on a task-specific branch. Keep the entire iteration on that branch.
Open a draft PR to `main` as soon as PR controls are available and keep updating that same PR through the iteration.

### Rule 1 — Branch discipline
One iteration = one GitHub task branch and one PR.
Never push or merge directly to `main`.

### Rule 2 — Scope lock
Implement exactly the acceptance criteria in the story card.
Do not fix unrelated code. Do not refactor. Do not gold-plate.
**File scope**: Only create or modify files listed in your story card's "Files to create / modify" table.

### Rule 3 — Tests before the next story
Write every test in the story's test table before advancing to the next story.

### Rule 4 — Save progress after every story
Update this plan file's Tracking Table: change the story status to Done or Blocked.
Save code and plan updates to the GitHub task branch for this run.

### Rule 5 — Validate after every epic
Run the narrowest relevant automated validation for the files you changed if tools are available.

### Rule 6 — STUCK PROTOCOL (3 failures = stop immediately)
- Mark the blocked story as `🚫 Blocked` in the Tracking Table.
- Open or update a draft PR titled `WIP: [story-id] — blocked`.
- Include the exact blocker, the exact error message, and 1-2 attempted fixes.
- **HALT. Do not start the next story.**

### Rule 7 — Iteration PR (after ALL epics complete)
- Title format: `feat(DMA-CONV-1): iteration N — [one-line summary]`.
- PR body must include: completed stories, validation status, and the NFR checklist.
- Post the PR URL in the task thread. **HALT — do not start the next iteration.**

**CHECKPOINT RULE**: After completing each epic:
```bash
git add -A && git commit -m "feat(DMA-CONV-1): [epic-id] — [epic title]" && git push origin HEAD
```

---

## NFR Quick Reference

| # | Rule | Consequence of violation |
|---|---|---|
| 1 | `waooaw_router()` factory — never bare `APIRouter` | CI ruff ban — PR blocked |
| 2 | `get_read_db_session()` on all GET routes | Primary DB overloaded |
| 3 | `PIIMaskingFilter()` on every logger | PII incident |
| 4 | `@circuit_breaker(service=...)` on every external HTTP call | Cascading failure |
| 5 | `dependencies=[Depends(get_correlation_id), Depends(get_audit_log)]` on FastAPI() | Audit trail missing |
| 6 | `X-Correlation-ID` header on every outgoing HTTP request | Trace broken |
| 7 | Loading + error + empty states on every FE data-fetching component | Silent failures |
| 8 | Tests >= 80% coverage on all new BE code | PR blocked by CI |
| 9 | Never embed env-specific values in Dockerfile or code | Image cannot be promoted |
| 10 | CP BackEnd is a thin proxy only — no business logic | Architecture violation |

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | Prompt rewrite with required-fields gate | Rewrite system prompt with field checklist, lock-and-confirm rules, and full context injection | 🟢 Done | copilot/iteration-1-epics-e1-e2-e3 |
| E1-S2 | 1 | Prompt rewrite with required-fields gate | Server-side field-completeness validation before approval_ready transition | 🟢 Done | copilot/iteration-1-epics-e1-e2-e3 |
| E2-S1 | 1 | Customer sees conversation progress | Add field-level progress counter to response contract and wizard UI | 🟢 Done | copilot/iteration-1-epics-e1-e2-e3 |
| E2-S2 | 1 | Customer sees conversation progress | Align workshop summary fields to required-fields list and CampaignBrief model | 🟢 Done | copilot/iteration-1-epics-e1-e2-e3 |
| E3-S1 | 1 | Artifact rendering fix | Diagnose and fix table artifact not rendering after DMA-MEDIA-1 deploy | 🟢 Done | copilot/iteration-1-epics-e1-e2-e3 |
| E3-S2 | 1 | Artifact rendering fix | Verify image/video/audio artifact request-to-preview path works end-to-end | 🟢 Done | copilot/iteration-1-epics-e1-e2-e3 |
| E4-S1 | 2 | Brand voice feeds content quality | Inject brand voice into conversation prompt and content generation | 🔴 Not Started | — |
| E4-S2 | 2 | Brand voice feeds content quality | Add content-pillar framework to prompt guidance | 🔴 Not Started | — |
| E5-S1 | 2 | Market-aware theme creation | Add competitor/niche context fields to discovery and prompt | 🔴 Not Started | — |
| E5-S2 | 2 | Market-aware theme creation | Inject niche hashtags and SEO keywords into content generation | 🔴 Not Started | — |
| E6-S1 | 2 | Optimal posting schedule | Add posting-time recommendation based on industry and audience data | 🔴 Not Started | — |
| E7-S1 | 3 | Agent improves from performance data | Inject content_analytics recommendations into theme cycle prompt | 🔴 Not Started | — |
| E7-S2 | 3 | Agent improves from performance data | Surface performance-driven suggestions in wizard UI | 🔴 Not Started | — |
| E8-S1 | 3 | Platform-accurate content previews | Build YouTube/LinkedIn/Instagram preview components for approval UI | 🔴 Not Started | — |
| E9-S1 | 3 | Docker validation and PR | End-to-end Docker validation for conversation → content → preview → publish path | 🔴 Not Started | — |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

---

## Iteration 1 — Fix the Conversation Loop

**Scope:** Rewrite the DMA conversation prompt to stop the endless loop, add server-side required-fields validation, show progress to customer, fix artifact rendering from DMA-MEDIA-1.
**Lane:** B — Plant BackEnd prompt and validation changes + CP FrontEnd progress UI
**⏱ Estimated:** 6h | **Come back:** 2026-04-14 06:00 UTC
**Epics:** E1, E2, E3
**Advances:** P1 DMA value — customers can finally complete the conversation and reach theme approval, content generation, and publishing.

### Dependency Map (Iteration 1)

```
E1-S1 ──► E1-S2    (S2 uses the new prompt fields from S1)
E2-S1 ──► E2-S2    (S2 aligns field names that S1 progress counter depends on)
E3-S1 ──► E3-S2    (S2 verifies non-table artifacts after S1 fixes rendering)
```

All three epics are independent of each other and can execute in parallel, but within each epic the stories are sequential.

---

### Epic E1: Customer completes the strategy conversation instead of looping forever

**Branch:** `feat/DMA-CONV-1-iteration-1` (GitHub Agents auto-creates the task branch)
**User story:** As a customer, I can brief my DMA in a conversation that concludes when I've given enough information, so that I get a master theme and supporting themes instead of endless questions.

---

#### Story E1-S1: Rewrite system prompt with required-fields checklist, lock-and-confirm rules, and full structured context

**BLOCKED UNTIL:** none
**Estimated time:** 90 min
**Branch:** `feat/DMA-CONV-1-iteration-1` (GitHub Agents auto-creates the task branch)
**CP BackEnd pattern:** N/A — Plant BackEnd only

**What to do (self-contained):**

The current system prompt in `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` lines 1082-1088 tells the LLM to "Ask probing questions only until the strategy is strong enough for approval, then return a clear master theme" but never defines what "strong enough" means — there is no checklist of required fields. The 11 required fields exist in `src/Plant/BackEnd/agent_mold/reference_agents.py` lines 52-63 (`THEME_DISCOVERY_REQUIRED_FIELDS`) but are never mentioned in the prompt. The message history is truncated to the last 4 messages (line 388 `normalized[-4:]`) which causes the agent to forget earlier answers.

Changes:
1. In `_theme_workshop_prompt()` (line 533), inject the `THEME_DISCOVERY_REQUIRED_FIELDS` list into the prompt payload as a `required_fields_checklist` with current fill status (filled/empty for each field based on the workshop summary).
2. In the system prompt (line 1082), add explicit rules: (a) "Here are the 11 fields you must collect. When a field has a value, it is LOCKED — never ask about it again." (b) "When the customer gives a direct answer, lock that field and confirm in one sentence. Do NOT re-offer locked fields as next-step options." (c) "When all 11 fields are filled, you MUST set status to approval_ready and present the master theme for approval. Do not ask more questions." (d) "When the customer asks for any concrete deliverable (plan, table, draft, schedule), produce it immediately. Do not deflect with more questions."
3. Change `_normalize_workshop_messages()` line 388 from `normalized[-4:]` to `normalized[-12:]` so the LLM retains more conversation context.
4. In the `workshop_state` section of the prompt payload, add `locked_fields` (dict of field_name → value for all non-empty fields) and `missing_fields` (list of field names still empty) derived from the workshop summary.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | 373-390, 545-620, 1078-1100 | `_normalize_workshop_messages` truncation (L373, returns `normalized[-4:]` at L387), `_theme_workshop_prompt` payload construction (L545), system prompt text (L1082) |
| `src/Plant/BackEnd/agent_mold/reference_agents.py` | 52-63 | `THEME_DISCOVERY_REQUIRED_FIELDS` list |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | modify | 1. Line 387: change `normalized[-4:]` to `normalized[-12:]`. 2. In `_theme_workshop_prompt()`: add `required_fields_checklist`, `locked_fields`, `missing_fields` to the JSON payload under `workshop_state`. 3. In `generate_theme_plan()` system prompt (line 1088): add the four rules listed above. |

**Code patterns to copy exactly:**

```python
# Import at top of file (add near other imports from agent_mold):
from agent_mold.reference_agents import THEME_DISCOVERY_REQUIRED_FIELDS

# Inside _theme_workshop_prompt(), after building the workshop_state dict,
# compute field fill status from the summary:
summary = workshop["summary"]
_FIELD_TO_SUMMARY_KEY = {
    "business_background": "business_focus",
    "objective": "business_goal",
    "industry": "profession_name",
    "locality": "location_focus",
    "target_audience": "audience",
    "persona": "customer_profile",
    "tone": "tone",
    "offer": "cta",
    "channel_intent": "youtube_angle",
    "posting_cadence": "first_content_direction",
    "success_metrics": "positioning",
}
locked_fields = {}
missing_fields = []
for req_field in THEME_DISCOVERY_REQUIRED_FIELDS:
    summary_key = _FIELD_TO_SUMMARY_KEY.get(req_field, req_field)
    value = str(summary.get(summary_key) or "").strip()
    if value:
        locked_fields[req_field] = value
    else:
        missing_fields.append(req_field)

# Add to the workshop_state section of the prompt JSON:
"required_fields_checklist": {
    "total": len(THEME_DISCOVERY_REQUIRED_FIELDS),
    "filled": len(locked_fields),
    "missing": len(missing_fields),
    "locked_fields": locked_fields,
    "missing_fields": missing_fields,
},
```

**Acceptance criteria:**
1. The system prompt sent to Grok contains explicit instructions about the 11 required fields, lock-and-confirm behaviour, and immediate artifact production when requested.
2. The prompt payload includes `required_fields_checklist` with `locked_fields` and `missing_fields` derived from current workshop summary state.
3. Message history window is 12 messages instead of 4.
4. The system prompt contains an explicit rule: when the customer asks for a deliverable (plan, table, draft, schedule), produce it immediately — do not deflect with more questions. *(This enforces O6.)*
5. All existing tests in `src/Plant/BackEnd/tests/` that reference `digital_marketing_activation` still pass.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S1-T1 | `src/Plant/BackEnd/tests/unit/test_dma_prompt_fields.py` | Call `_theme_workshop_prompt()` with a workspace where 6 of 11 summary fields are filled | `required_fields_checklist.filled == 6`, `required_fields_checklist.missing == 5`, `locked_fields` has 6 keys |
| E1-S1-T2 | same | Call `_normalize_workshop_messages()` with 15 messages | Returns exactly 12 messages (not 4) |
| E1-S1-T3 | same | Call `_theme_workshop_prompt()` with all 11 fields filled | `missing_fields` is empty list |
| E1-S1-T4 | same | Extract system prompt text from the Grok call | System prompt contains the substring "produce it immediately" (case-insensitive) — validates O6 enforcement |

**Test command:**
```bash
cd src/Plant/BackEnd && pytest tests/unit/test_dma_prompt_fields.py -v
```

**Commit message:** `feat(DMA-CONV-1): E1-S1 — rewrite prompt with required-fields gate and lock-and-confirm rules`

**Done signal:** `"E1-S1 done. Changed: digital_marketing_activation.py. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

#### Story E1-S2: Server-side field-completeness validation before approval_ready transition

**BLOCKED UNTIL:** E1-S1 committed
**Estimated time:** 45 min
**Branch:** `feat/DMA-CONV-1-iteration-1` (GitHub Agents auto-creates the task branch)
**CP BackEnd pattern:** N/A — Plant BackEnd only

**What to do (self-contained):**

Currently `_parse_theme_workshop_response()` (line 693) sets `status = "approval_ready"` based solely on whether the LLM returned a master theme and derived themes — there is no server-side check that the required fields are actually populated. Add a validation gate: after parsing the LLM response, compute the field-completeness from the workshop summary. If fewer than 9 of 11 required fields are filled, force the status back to `discovery` regardless of what the LLM said. Log a warning when the LLM tried to approve prematurely.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | 690-780 | `_parse_theme_workshop_response` — where status is set |
| `src/Plant/BackEnd/agent_mold/reference_agents.py` | 52-63 | `THEME_DISCOVERY_REQUIRED_FIELDS` |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | modify | At the end of `_parse_theme_workshop_response()`, after the workshop dict is fully built, add a validation gate that counts filled fields in the summary using `_FIELD_TO_SUMMARY_KEY` (from E1-S1). If `filled_count < 9`, override `workshop["status"] = "discovery"` and log a warning. |

**Code patterns to copy exactly:**

```python
# Add at the end of _parse_theme_workshop_response(), just before the return statement:
filled_count = sum(
    1 for req_field in THEME_DISCOVERY_REQUIRED_FIELDS
    if str(workshop["summary"].get(_FIELD_TO_SUMMARY_KEY.get(req_field, req_field)) or "").strip()
)
if workshop["status"] == "approval_ready" and filled_count < 9:
    logger.warning(
        "LLM tried approval_ready with only %d/%d fields filled — forcing discovery",
        filled_count, len(THEME_DISCOVERY_REQUIRED_FIELDS),
    )
    workshop["status"] = "discovery"
    if not workshop["current_focus_question"]:
        workshop["current_focus_question"] = "A few details are still needed before I can lock the strategy. What is the primary business result this content should drive?"
```

**Acceptance criteria:**
1. When the LLM returns `approval_ready` but fewer than 9 of 11 fields are filled, the API response status is forced to `discovery`.
2. When all 11 fields are filled, the LLM's `approval_ready` status passes through unchanged.
3. A warning log is emitted when the override fires.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S2-T1 | `src/Plant/BackEnd/tests/unit/test_dma_prompt_fields.py` | Call `_parse_theme_workshop_response` with valid JSON where LLM says approval_ready but summary has only 5 fields filled | Returned workshop status is `discovery` |
| E1-S2-T2 | same | Same call but summary has all 11 fields filled | Returned workshop status is `approval_ready` |

**Test command:**
```bash
cd src/Plant/BackEnd && pytest tests/unit/test_dma_prompt_fields.py -v
```

**Commit message:** `feat(DMA-CONV-1): E1-S2 — server-side field-completeness validation gate`

**Done signal:** `"E1-S2 done. Changed: digital_marketing_activation.py. Tests: T1 ✅ T2 ✅"`

---

### Epic E2: Customer sees how close they are to finishing the brief

**Branch:** `feat/DMA-CONV-1-iteration-1` (GitHub Agents auto-creates the task branch)
**User story:** As a customer, I can see a progress indicator ("8/11 fields locked") during the DMA conversation, so that I know how close I am to finishing and feel motivated to complete.

---

#### Story E2-S1: Add field-level progress counter to response contract and wizard UI

**BLOCKED UNTIL:** none
**Estimated time:** 90 min
**Branch:** `feat/DMA-CONV-1-iteration-1` (GitHub Agents auto-creates the task branch)
**CP BackEnd pattern:** N/A — Plant BackEnd response + CP FrontEnd display

**What to do (self-contained):**

The `ThemePlanResponse` model (line 82) and the `_parse_theme_workshop_response` function return a workshop dict that has `status` but no field-level progress. Add a `brief_progress` object to the workshop dict returned by the API containing `{ filled: number, total: 11, missing_fields: string[], locked_fields: { field: value } }`. On the frontend in `DigitalMarketingActivationWizard.tsx`, display this as a progress badge near the chat header showing "X/11 fields locked".

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | 82-90, 690-780 | `ThemePlanResponse` model, `_parse_theme_workshop_response` return shape |
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | 2625-2640 | Chat header with existing badges |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | modify | In `_parse_theme_workshop_response()`, compute `filled_count` (same logic as E1-S2 validation gate — use `_FIELD_TO_SUMMARY_KEY` and `THEME_DISCOVERY_REQUIRED_FIELDS`), then build `brief_progress` dict and add it to the `workshop` dict before returning. If E1-S2 has already been committed on this branch, reuse its `filled_count` variable; if not, compute it independently. |
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | modify | Extract `brief_progress` from the strategy workshop state. Add a Badge component next to existing badges in the chat header showing "{filled}/{total} fields locked". |
| `src/CP/FrontEnd/src/services/digitalMarketingActivation.service.ts` | modify | Add `brief_progress` to the `DigitalMarketingStrategyWorkshop` TypeScript type. |

**Code patterns to copy exactly:**

```python
# In _parse_theme_workshop_response, add brief_progress to workshop dict:
workshop["brief_progress"] = {
    "filled": filled_count,
    "total": len(THEME_DISCOVERY_REQUIRED_FIELDS),
    "missing_fields": [
        req_field for req_field in THEME_DISCOVERY_REQUIRED_FIELDS
        if not str(workshop["summary"].get(_FIELD_TO_SUMMARY_KEY.get(req_field, req_field)) or "").strip()
    ],
    "locked_fields": {
        req_field: str(workshop["summary"].get(_FIELD_TO_SUMMARY_KEY.get(req_field, req_field)) or "").strip()
        for req_field in THEME_DISCOVERY_REQUIRED_FIELDS
        if str(workshop["summary"].get(_FIELD_TO_SUMMARY_KEY.get(req_field, req_field)) or "").strip()
    },
}
```

```typescript
// In DigitalMarketingActivationWizard.tsx, inside the chat header badges div:
{strategyWorkshop.brief_progress ? (
  <Badge appearance="outline" color={
    strategyWorkshop.brief_progress.filled >= strategyWorkshop.brief_progress.total ? 'success' : 'informative'
  }>
    {strategyWorkshop.brief_progress.filled}/{strategyWorkshop.brief_progress.total} fields locked
  </Badge>
) : null}
```

**Acceptance criteria:**
1. API response workshop dict contains `brief_progress` with `filled`, `total`, `missing_fields`, and `locked_fields`.
2. The wizard UI shows a badge like "7/11 fields locked" that updates after each conversation turn.
3. When all 11 fields are filled, the badge shows "11/11 fields locked" in green.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S1-T1 | `src/Plant/BackEnd/tests/unit/test_dma_prompt_fields.py` | Parse a workshop response with 7 filled summary fields | `brief_progress.filled == 7`, `brief_progress.total == 11`, `missing_fields` has 4 items |
| E2-S1-T2 | `src/CP/FrontEnd/src/__tests__/DigitalMarketingActivationWizard.test.tsx` | Render wizard with mock workshop containing `brief_progress: { filled: 8, total: 11 }` | Badge with text "8/11 fields locked" is in DOM |

**Test command:**
```bash
cd src/Plant/BackEnd && pytest tests/unit/test_dma_prompt_fields.py -v
cd src/CP/FrontEnd && npx vitest run src/__tests__/DigitalMarketingActivationWizard.test.tsx
```

**Commit message:** `feat(DMA-CONV-1): E2-S1 — field-level progress counter in API and wizard UI`

**Done signal:** `"E2-S1 done. Changed: digital_marketing_activation.py, DigitalMarketingActivationWizard.tsx, digitalMarketingActivation.service.ts. Tests: T1 ✅ T2 ✅"`

---

#### Story E2-S2: Align workshop summary field names to required-fields list

**BLOCKED UNTIL:** E2-S1 committed
**Estimated time:** 45 min
**Branch:** `feat/DMA-CONV-1-iteration-1` (GitHub Agents auto-creates the task branch)
**CP BackEnd pattern:** N/A — Plant BackEnd only

**What to do (self-contained):**

The workshop summary uses 14 fields with names like `profession_name`, `location_focus`, `customer_profile` while the required-fields list uses 11 fields like `industry`, `locality`, `target_audience`. The `_FIELD_TO_SUMMARY_KEY` mapping (from E1-S1) bridges this gap at the prompt layer, but the response contract still sends the old summary field names to the frontend. Add canonical aliases: when building `brief_progress.locked_fields`, use the `THEME_DISCOVERY_REQUIRED_FIELDS` names as keys (not the summary names). Also add the canonical field name to the `response_contract.summary` section of the prompt so the LLM populates fields with the correct names.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | 533-620 | `_theme_workshop_prompt` response_contract.summary section |
| `src/Plant/BackEnd/agent_mold/reference_agents.py` | 52-63 | `THEME_DISCOVERY_REQUIRED_FIELDS` |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | modify | In the `response_contract.summary` section of `_theme_workshop_prompt()`, add a comment line mapping each summary field to its canonical required-field name. Add canonical aliases to the summary instructions so the LLM includes both vocabulary sets. |

**Acceptance criteria:**
1. The prompt's response contract summary section includes clear field-name annotations mapping to `THEME_DISCOVERY_REQUIRED_FIELDS`.
2. `brief_progress.locked_fields` uses canonical required-field names as keys.
3. Existing tests still pass.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S2-T1 | `src/Plant/BackEnd/tests/unit/test_dma_prompt_fields.py` | Call `_theme_workshop_prompt` and parse the JSON | `response_contract.summary` dict keys can be mapped to all 11 items in `THEME_DISCOVERY_REQUIRED_FIELDS` |

**Test command:**
```bash
cd src/Plant/BackEnd && pytest tests/unit/test_dma_prompt_fields.py -v
```

**Commit message:** `feat(DMA-CONV-1): E2-S2 — align workshop summary fields to required-fields vocabulary`

**Done signal:** `"E2-S2 done. Changed: digital_marketing_activation.py. Tests: T1 ✅"`

---

### Epic E3: Artifact rendering works end-to-end after deploy

**Branch:** `feat/DMA-CONV-1-iteration-1` (GitHub Agents auto-creates the task branch)
**User story:** As a customer, I can see tables, images, and media artifacts rendered in the DMA wizard after the agent generates them, so that I can review and approve real content instead of seeing blank cards.

---

#### Story E3-S1: Diagnose and fix table artifact not rendering after DMA-MEDIA-1 deploy

**BLOCKED UNTIL:** none
**Estimated time:** 90 min
**Branch:** `feat/DMA-CONV-1-iteration-1` (GitHub Agents auto-creates the task branch)
**CP BackEnd pattern:** N/A — Plant BackEnd data shape + CP FrontEnd rendering

**What to do (self-contained):**

After deploying DMA-MEDIA-1 (#1035), table artifacts are not rendering in the wizard. The `DigitalMarketingArtifactPreviewCard` component (line 8) checks `post.artifact_metadata?.table_preview` for `columns` and `rows` arrays but the backend `_build_auto_draft()` (line 164) builds table content as a GFM markdown string in `post.text` — it never populates `artifact_metadata.table_preview` with structured columns/rows data. The preview card's `renderTablePreview()` function therefore always returns null because `table_preview` is undefined.

Fix by:
1. In Plant BackEnd `_build_auto_draft()`, when building a TABLE artifact, also populate `artifact_metadata.table_preview` with `{ columns: [...], rows: [{...}, ...] }` parsed from the derived_themes data.
2. In the FrontEnd `DigitalMarketingArtifactPreviewCard`, add a fallback: if `table_preview` is missing but `post.text` contains GFM markdown table syntax, render the text content as markdown using ReactMarkdown (already imported in the parent wizard).

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | 164-230 | `_build_auto_draft` TABLE artifact path — how `posts` are built |
| `src/CP/FrontEnd/src/components/DigitalMarketingArtifactPreviewCard.tsx` | 1-100 | `renderTablePreview` checks `artifact_metadata.table_preview.columns/rows` |
| `src/Plant/BackEnd/services/draft_batches.py` | 1-60 | `DraftPostRecord` schema — what fields exist for artifact_metadata |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | modify | In `_build_auto_draft()`, in the TABLE branch (around line 190), after building `table_text`, also build `table_preview = {"columns": ["#", "Theme", "Description", "Frequency"], "rows": [...]}` from `derived_themes` and set it on the `DraftPostRecord` as `artifact_metadata={"table_preview": table_preview}`. |
| `src/CP/FrontEnd/src/components/DigitalMarketingArtifactPreviewCard.tsx` | modify | In `renderTablePreview`, add a fallback: if `table_preview` is missing/empty but `post.text` contains a markdown table (`|`), render `<ReactMarkdown remarkPlugins={[remarkGfm]}>{post.text}</ReactMarkdown>` instead of returning null. Add the necessary imports. |

**Code patterns to copy exactly:**

```python
# In _build_auto_draft(), TABLE branch, after building table_text:
table_preview_rows = []
for i, theme in enumerate(derived_themes, 1):
    table_preview_rows.append({
        "#": str(i),
        "Theme": str(theme.get("title") or ""),
        "Description": str(theme.get("description") or ""),
        "Frequency": str(theme.get("frequency") or "weekly"),
    })

posts.append(
    DraftPostRecord(
        post_id=str(uuid4()),
        channel="youtube",
        text=table_text,
        artifact_type="table",
        hashtags=[],
        artifact_metadata={
            "table_preview": {
                "columns": ["#", "Theme", "Description", "Frequency"],
                "rows": table_preview_rows,
            }
        },
    )
)
```

```typescript
// In DigitalMarketingArtifactPreviewCard.tsx, add imports at top:
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

// In renderTablePreview, add markdown fallback before the final return null:
if (!preview?.columns?.length || !preview?.rows?.length) {
  // Fallback: render raw markdown table if post.text contains pipe characters
  if (post.text && post.text.includes('|')) {
    return (
      <div style={{ overflowX: 'auto' }}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{post.text}</ReactMarkdown>
      </div>
    )
  }
  return null
}
```

**Acceptance criteria:**
1. When the DMA generates a table artifact, the preview card renders a visible table with theme rows — not a blank card.
2. Both structured `table_preview` rendering and GFM markdown fallback rendering work.
3. Existing artifact preview tests pass.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S1-T1 | `src/Plant/BackEnd/tests/unit/test_dma_auto_draft.py` | Call `_build_auto_draft` with 3 derived themes and TABLE artifact type | Returned batch has a post with `artifact_metadata.table_preview.columns` containing 4 items and `rows` containing 3 items |
| E3-S1-T2 | `src/CP/FrontEnd/src/__tests__/DigitalMarketingArtifactPreviewCard.test.tsx` | Render component with a post that has `artifact_type: 'table'` and text containing GFM markdown but no `artifact_metadata.table_preview` | Markdown table is rendered in DOM (contains `<table>` element) |

**Test command:**
```bash
cd src/Plant/BackEnd && pytest tests/unit/test_dma_auto_draft.py -v
cd src/CP/FrontEnd && npx vitest run src/__tests__/DigitalMarketingArtifactPreviewCard.test.tsx
```

**Commit message:** `feat(DMA-CONV-1): E3-S1 — fix table artifact rendering with structured preview and markdown fallback`

**Done signal:** `"E3-S1 done. Changed: digital_marketing_activation.py, DigitalMarketingArtifactPreviewCard.tsx. Tests: T1 ✅ T2 ✅"`

---

#### Story E3-S2: Verify image/video/audio artifact request-to-preview path works

**BLOCKED UNTIL:** E3-S1 committed
**Estimated time:** 45 min
**Branch:** `feat/DMA-CONV-1-iteration-1` (GitHub Agents auto-creates the task branch)
**CP BackEnd pattern:** N/A

**What to do (self-contained):**

After E3-S1 fixes table rendering, verify that non-table artifact types (image, video, audio, video_audio) have a working request → queued → status display path. The `DigitalMarketingArtifactPreviewCard` already handles queued and failed states for non-table types (lines 64-80). This story adds a test for each artifact type to confirm the preview card renders the correct status message and, once an artifact_uri is set, renders the "Open generated asset" link.

If the backend `_build_auto_draft()` does not properly set `artifact_type` on non-table `DraftPostRecord` objects, fix the attribute assignment.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingArtifactPreviewCard.tsx` | 40-100 | How non-table artifact types display status |
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | 230-260 | Non-table artifact branch of `_build_auto_draft` |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/__tests__/DigitalMarketingArtifactPreviewCard.test.tsx` | modify | Add test cases for image, video, audio artifact types: queued state shows message, failed state shows error, artifact_uri renders link. |
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | modify (if needed) | In the non-table branch of `_build_auto_draft`, ensure `artifact_type` is set to the correct type string from `non_table_types[0].value`, not hardcoded. |

**Acceptance criteria:**
1. Rendering a draft post with `artifact_type: 'image'` and `artifact_generation_status: 'queued'` shows the queued message.
2. Rendering with `artifact_generation_status: 'failed'` shows the error message.
3. Rendering with `artifact_uri` set shows the "Open generated asset" link.
4. Same behaviour for video, audio, and video_audio types.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S2-T1 | `src/CP/FrontEnd/src/__tests__/DigitalMarketingArtifactPreviewCard.test.tsx` | Render with `artifact_type: 'image', artifact_generation_status: 'queued'` | DOM contains "queued generation" text |
| E3-S2-T2 | same | Render with `artifact_type: 'video', artifact_generation_status: 'failed'` | DOM contains "generation failed" text |
| E3-S2-T3 | same | Render with `artifact_type: 'audio', artifact_uri: 'https://example.com/audio.mp3'` | DOM contains link with href |

**Test command:**
```bash
cd src/CP/FrontEnd && npx vitest run src/__tests__/DigitalMarketingArtifactPreviewCard.test.tsx
```

**Commit message:** `feat(DMA-CONV-1): E3-S2 — verify non-table artifact preview rendering`

**Done signal:** `"E3-S2 done. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

## Iteration 2 — Content Quality Features

**Scope:** Brand voice injection, content-pillar framework, competitor/niche context, hashtag/SEO strategy, posting-time optimization.
**Lane:** B — Plant BackEnd service integration + prompt enhancement + CP FrontEnd UX
**⏱ Estimated:** 5h | **Come back:** 2026-04-15 06:00 UTC
**Epics:** E4, E5, E6
**Advances:** P2 DMA value — generated content is commercially competitive (branded, niche-aware, SEO-optimized, timed correctly).

### Dependency Map (Iteration 2)

```
E4-S1 ──► E4-S2    (S2 content pillars build on brand voice context from S1)
E5-S1 ──► E5-S2    (S2 hashtag injection needs competitor/niche data from S1)
E6-S1              (independent — posting-time optimization)
```

All three epics are independent of each other, but within E4 and E5, stories are sequential.

---

### Epic E4: Brand voice feeds content quality

**Branch:** `feat/DMA-CONV-1-iteration-2` (GitHub Agents auto-creates the task branch)
**User story:** As a customer, my brand voice is automatically loaded into every DMA conversation and content generation call, so that all generated content sounds like my brand without me repeating preferences.

---

#### Story E4-S1: Inject brand voice into conversation prompt and content generation

**BLOCKED UNTIL:** Iteration 1 PR merged to main
**Estimated time:** 90 min
**Branch:** `feat/DMA-CONV-1-iteration-2` (GitHub Agents auto-creates the task branch)
**CP BackEnd pattern:** N/A — Plant BackEnd only

**What to do (self-contained):**

`BrandVoiceModel` already exists at `src/Plant/BackEnd/models/brand_voice.py` with fields `tone_keywords`, `vocabulary_preferences`, `messaging_patterns`, `example_phrases`, `voice_description`. The service at `src/Plant/BackEnd/services/brand_voice_service.py` has `get_brand_voice(customer_id, db)`. Neither is called from the DMA conversation prompt or content generation path.

Changes:
1. In `_theme_workshop_prompt()`, load the customer's brand voice via `brand_voice_service.get_brand_voice()` and inject it into the prompt payload as a `brand_voice_context` section.
2. Add a system prompt instruction: "Use this brand voice throughout the conversation and generated content. Match tone, vocabulary, and messaging patterns exactly."
3. In `src/Plant/BackEnd/agent_mold/skills/content_creator.py`, in `generate_theme_list()` (not `generate_posts_for_theme`), pass brand voice as the `brand_voice_context: str` parameter (already exists as empty string default). Note: `generate_posts_for_theme()` takes a `PostGeneratorInput` object — do NOT add loose keyword arguments to it.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/services/brand_voice_service.py` | 1-42 | `get_brand_voice(customer_id, db)` signature and return shape |
| `src/Plant/BackEnd/agent_mold/skills/content_creator.py` | 75-120 | `generate_theme_list()` (L78) has `brand_voice_context: str = ""` param. `generate_posts_for_theme(inp: PostGeneratorInput)` (L107) takes a Pydantic input — no loose kwargs |
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | 533-620 | `_theme_workshop_prompt()` — where to add brand voice |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | modify | In `_theme_workshop_prompt()`: call `brand_voice_service.get_brand_voice(customer_id, db)` where `customer_id` is extracted from the hired agent relation. If a brand voice exists, add a `brand_voice_context` section to the prompt payload with the tone_keywords, vocabulary_preferences, messaging_patterns, example_phrases, and voice_description. In the system prompt, add: "The customer's brand voice is provided. Use this exact tone, vocabulary, and messaging patterns in all conversation responses and generated content." |
| `src/Plant/BackEnd/agent_mold/skills/content_creator.py` | modify | In `generate_theme_list()` (L78): the `brand_voice_context: str = ""` param already exists. At the call site in `digital_marketing_activation.py` where `generate_theme_list()` is invoked, format the loaded BrandVoiceModel into a summary string and pass it as `brand_voice_context`. Do NOT modify `generate_posts_for_theme()` — it takes `PostGeneratorInput`, not loose kwargs. |

**Code patterns to copy exactly:**

```python
# In digital_marketing_activation.py, import:
from services.brand_voice_service import get_brand_voice

# In _theme_workshop_prompt(), before building final payload:
brand_voice = await get_brand_voice(customer_id=hired_agent.customer_id, db=db)
brand_voice_section = {}
if brand_voice:
    brand_voice_section = {
        "tone_keywords": brand_voice.tone_keywords or [],
        "vocabulary_preferences": brand_voice.vocabulary_preferences or [],
        "messaging_patterns": brand_voice.messaging_patterns or [],
        "example_phrases": brand_voice.example_phrases or [],
        "voice_description": brand_voice.voice_description or "",
    }

# Add to prompt payload:
"brand_voice_context": brand_voice_section,
```

**Acceptance criteria:**
1. When a customer has a saved brand voice, the DMA prompt payload includes `brand_voice_context` with all five fields.
2. When no brand voice exists, `brand_voice_context` is an empty dict (graceful degradation).
3. Content generation in `generate_theme_list()` uses brand voice when available via its existing `brand_voice_context: str` parameter.
4. All existing tests pass.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E4-S1-T1 | `src/Plant/BackEnd/tests/unit/test_dma_brand_voice.py` | Mock `get_brand_voice()` to return a BrandVoiceModel with tone_keywords=["bold","direct"]. Call `_theme_workshop_prompt()` | Prompt payload contains `brand_voice_context.tone_keywords == ["bold","direct"]` |
| E4-S1-T2 | same | Mock `get_brand_voice()` to return None. Call `_theme_workshop_prompt()` | Prompt payload contains `brand_voice_context == {}` |

**Test command:**
```bash
cd src/Plant/BackEnd && pytest tests/unit/test_dma_brand_voice.py -v
```

**Commit message:** `feat(DMA-CONV-1): E4-S1 — inject brand voice into DMA prompt and content generation`

**Done signal:** `"E4-S1 done. Changed: digital_marketing_activation.py, content_creator.py. Tests: T1 ✅ T2 ✅"`

---

#### Story E4-S2: Add content-pillar framework to prompt guidance

**BLOCKED UNTIL:** E4-S1 committed
**Estimated time:** 45 min
**Branch:** `feat/DMA-CONV-1-iteration-2` (GitHub Agents auto-creates the task branch)
**CP BackEnd pattern:** N/A — Plant BackEnd only

**What to do (self-contained):**

Content pillars are recurring categories (3-5) that anchor a content strategy — e.g., "Educational", "Behind the scenes", "Customer stories", "Industry trends", "Product showcase". Currently the DMA prompt has no content-pillar concept. The LLM generates themes ad hoc without strategic structure.

Changes:
1. In the system prompt within `_theme_workshop_prompt()`, add guidance: "During discovery, help the customer define 3-5 content pillars — recurring categories that all content should map to. Examples: Educational, Behind the scenes, Customer stories, Industry trends, Product showcase. Each derived theme must map to one pillar. Include `content_pillars` in the summary."
2. Add `content_pillars` to the response contract summary section as an optional list of strings.
3. Add content pillars to `_FIELD_TO_SUMMARY_KEY` mapping and update the progress counter logic to count it as a bonus field (not required, but tracked).

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | 533-620, 1080-1130 | System prompt, response contract summary section |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | modify | 1. System prompt: add content-pillar guidance text. 2. Response contract summary: add `content_pillars: ["pillar1", ...]` as optional field. 3. In derived_themes response contract: add `pillar: "pillar_name"` field. |

**Acceptance criteria:**
1. System prompt includes content-pillar guidance with examples.
2. Response contract summary section includes `content_pillars` as an optional list.
3. Derived themes response contract includes `pillar` field.
4. Existing tests pass.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E4-S2-T1 | `src/Plant/BackEnd/tests/unit/test_dma_brand_voice.py` | Call `_theme_workshop_prompt()` | System prompt text contains the substring "content pillars" (case-insensitive) |

**Test command:**
```bash
cd src/Plant/BackEnd && pytest tests/unit/test_dma_brand_voice.py -v
```

**Commit message:** `feat(DMA-CONV-1): E4-S2 — content-pillar framework in DMA prompt guidance`

**Done signal:** `"E4-S2 done. Changed: digital_marketing_activation.py. Tests: T1 ✅"`

---

### Epic E5: Market-aware theme creation

**Branch:** `feat/DMA-CONV-1-iteration-2` (GitHub Agents auto-creates the task branch)
**User story:** As a customer, the DMA asks about my competitors and niche keywords during discovery, and uses that context to generate differentiated themes with niche-specific hashtags and SEO terms.

---

#### Story E5-S1: Add competitor/niche context fields to discovery and prompt

**BLOCKED UNTIL:** Iteration 1 PR merged to main
**Estimated time:** 45 min
**Branch:** `feat/DMA-CONV-1-iteration-2` (GitHub Agents auto-creates the task branch)
**CP BackEnd pattern:** N/A — Plant BackEnd only

**What to do (self-contained):**

The DMA conversation currently never asks about competitors or niche-specific keywords. Add two new fields to the discovery prompt:
- `competitor_names`: list of 2-5 competitor names/handles the customer wants to differentiate from
- `niche_keywords`: list of 5-10 niche-specific keywords relevant to the customer's industry

Changes:
1. In the system prompt, add instructions: "Ask the customer to name 2-5 competitors or industry peers they want to differentiate from. Also ask for 5-10 niche keywords or topics that are trending in their space."
2. Add `competitor_names` and `niche_keywords` to the response contract summary section.
3. Add both fields to `_FIELD_TO_SUMMARY_KEY` mapping — these are optional fields (not in the 11 required, but tracked in the summary).

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | 533-620, 1080-1130 | System prompt, response contract summary section |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | modify | 1. System prompt: add competitor and niche discovery instructions. 2. Response contract summary: add `competitor_names: [...]` and `niche_keywords: [...]` fields. |

**Acceptance criteria:**
1. System prompt instructs the LLM to ask about competitors and niche keywords.
2. Response contract summary includes both new fields.
3. Existing tests pass.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E5-S1-T1 | `src/Plant/BackEnd/tests/unit/test_dma_market_context.py` | Call `_theme_workshop_prompt()` | System prompt text contains "competitor" |
| E5-S1-T2 | same | Same call | Response contract summary section contains keys `competitor_names` and `niche_keywords` |

**Test command:**
```bash
cd src/Plant/BackEnd && pytest tests/unit/test_dma_market_context.py -v
```

**Commit message:** `feat(DMA-CONV-1): E5-S1 — competitor/niche context in DMA discovery prompt`

**Done signal:** `"E5-S1 done. Changed: digital_marketing_activation.py. Tests: T1 ✅ T2 ✅"`

---

#### Story E5-S2: Inject niche hashtags and SEO keywords into content generation

**BLOCKED UNTIL:** E5-S1 committed
**Estimated time:** 45 min
**Branch:** `feat/DMA-CONV-1-iteration-2` (GitHub Agents auto-creates the task branch)
**CP BackEnd pattern:** N/A — Plant BackEnd only

**What to do (self-contained):**

After discovery captures `competitor_names` and `niche_keywords`, the content generation pipeline in `content_creator.py` should use these to produce more targeted hashtags and SEO keywords in each post.

**Important:** `generate_posts_for_theme()` takes `PostGeneratorInput` (a Pydantic model), not loose keyword arguments. The niche/competitor context must be added to `PostGeneratorInput` or injected via the existing prompt-construction path in the `_grok_posts()` / `_deterministic_posts()` internal methods.

Changes:
1. In `content_creator.py`, add `niche_keywords: list[str] = []` and `competitor_context: list[str] = []` fields to the `PostGeneratorInput` model (in `content_models.py`).
2. In `_grok_posts()` (the internal method that builds the Grok prompt for post generation), read `inp.niche_keywords` and `inp.competitor_context` and include: "Use these niche keywords where relevant: {niche_keywords}. Differentiate from these competitors: {competitor_context}. Include 3-5 niche-specific hashtags per post."
3. In `digital_marketing_activation.py`, when building the `PostGeneratorInput` object, populate `niche_keywords` and `competitor_context` from the workshop summary.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/agent_mold/skills/content_creator.py` | 107-160 | `generate_posts_for_theme(inp: PostGeneratorInput)` and internal `_grok_posts()` — prompt construction |
| `src/Plant/BackEnd/agent_mold/skills/content_models.py` | 1-60 | `PostGeneratorInput` model definition — where to add niche_keywords and competitor_context fields |
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | 280-320 | Where `PostGeneratorInput` is constructed and passed to `generate_posts_for_theme()` |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/agent_mold/skills/content_models.py` | modify | Add `niche_keywords: list[str] = []` and `competitor_context: list[str] = []` fields to the `PostGeneratorInput` model. |
| `src/Plant/BackEnd/agent_mold/skills/content_creator.py` | modify | In `_grok_posts()`, read `inp.niche_keywords` and `inp.competitor_context` and inject into the Grok prompt. |
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | modify | At the site where `PostGeneratorInput` is constructed, populate `niche_keywords` and `competitor_context` from workshop summary. |

**Acceptance criteria:**
1. `PostGeneratorInput` model has `niche_keywords` and `competitor_context` fields.
2. The Grok prompt for post generation (in `_grok_posts()`) includes the niche keywords and competitor names when populated.
3. Existing tests pass.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E5-S2-T1 | `src/Plant/BackEnd/tests/unit/test_dma_market_context.py` | Build a `PostGeneratorInput` with `niche_keywords=["ai tutoring", "edtech"]`, call `_grok_posts()` | The prompt sent to Grok contains "ai tutoring" and "edtech" |
| E5-S2-T2 | same | Build `PostGeneratorInput` with empty lists | Prompt does not contain "niche keywords" section (graceful degradation) |

**Test command:**
```bash
cd src/Plant/BackEnd && pytest tests/unit/test_dma_market_context.py -v
```

**Commit message:** `feat(DMA-CONV-1): E5-S2 — niche hashtags and SEO in content generation`

**Done signal:** `"E5-S2 done. Changed: content_models.py, content_creator.py, digital_marketing_activation.py. Tests: T1 ✅ T2 ✅"`

---

### Epic E6: Optimal posting schedule

**Branch:** `feat/DMA-CONV-1-iteration-2` (GitHub Agents auto-creates the task branch)
**User story:** As a customer, the DMA recommends the best posting times based on my industry and audience, so I maximize engagement without manual research.

---

#### Story E6-S1: Add posting-time recommendation based on industry and audience data

**BLOCKED UNTIL:** Iteration 1 PR merged to main
**Estimated time:** 90 min
**Branch:** `feat/DMA-CONV-1-iteration-2` (GitHub Agents auto-creates the task branch)
**CP BackEnd pattern:** N/A — Plant BackEnd only + CP FrontEnd display

**What to do (self-contained):**

`content_analytics.py` already has `get_content_recommendations()` which returns `best_posting_hours` (list of hours). This data is never surfaced to the customer during the scheduling step.

Changes:
1. In Plant BackEnd: create a new helper `get_posting_time_suggestions(industry: str, channel: str, audience_profile: str)` in `src/Plant/BackEnd/services/content_analytics.py` that combines the existing `best_posting_hours` from historical performance data with industry-standard defaults if no data exists. Returns a list of `{ day: str, time: str, reason: str }` recommendations.
2. In the schedule-related prompt/response: when the conversation reaches the scheduling step (status near approval_ready), include posting-time suggestions in the prompt context.
3. In CP FrontEnd `DigitalMarketingActivationWizard.tsx`: in Step 3 (Plan step), display posting-time recommendations as a subtle info card alongside the schedule selector. Data comes from the workshop response.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/services/content_analytics.py` | 1-129 | `get_content_recommendations()` return shape, `best_posting_hours` |
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | 1250-1350 | Step 3 (Plan) schedule selector UI |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/services/content_analytics.py` | modify | Add `get_posting_time_suggestions(industry, channel, audience_profile)` function that returns industry-standard posting time suggestions as a list of dicts. Use existing `best_posting_hours` if available from performance data, otherwise use hardcoded industry defaults. |
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | modify | In the workshop response, when status is `approval_ready` or workshop progress shows 9+ fields filled, add `posting_time_suggestions` to the response by calling `get_posting_time_suggestions()`. |
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | modify | In Step 3, render posting-time suggestions as a card: "Recommended posting times" with day, time, and reason per row. |

**Code patterns to copy exactly:**

```python
# In content_analytics.py:
_INDUSTRY_POSTING_DEFAULTS = {
    "marketing": [
        {"day": "Tuesday", "time": "10:00 AM", "reason": "Highest B2B engagement window"},
        {"day": "Thursday", "time": "2:00 PM", "reason": "Pre-weekend content consumption spike"},
        {"day": "Saturday", "time": "9:00 AM", "reason": "Weekend discovery browsing"},
    ],
    "education": [
        {"day": "Monday", "time": "8:00 AM", "reason": "Start-of-week study planning"},
        {"day": "Wednesday", "time": "4:00 PM", "reason": "After-school content peak"},
        {"day": "Sunday", "time": "7:00 PM", "reason": "Weekend revision session"},
    ],
    "sales": [
        {"day": "Tuesday", "time": "9:00 AM", "reason": "Decision-maker morning email window"},
        {"day": "Wednesday", "time": "11:00 AM", "reason": "Mid-week pipeline review"},
        {"day": "Thursday", "time": "3:00 PM", "reason": "Pre-Friday urgency window"},
    ],
}

async def get_posting_time_suggestions(
    industry: str,
    channel: str = "youtube",
    audience_profile: str = "",
) -> list[dict]:
    """Return posting-time recommendations for the given industry and channel."""
    defaults = _INDUSTRY_POSTING_DEFAULTS.get(industry.lower(), _INDUSTRY_POSTING_DEFAULTS["marketing"])
    return defaults
```

**Acceptance criteria:**
1. `get_posting_time_suggestions()` returns a list of 3+ posting time recommendations with day, time, and reason.
2. The workshop response includes `posting_time_suggestions` when the customer is near the scheduling step.
3. Step 3 of the wizard displays posting-time recommendations.
4. If no industry match, falls back to marketing defaults.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E6-S1-T1 | `src/Plant/BackEnd/tests/unit/test_posting_time.py` | Call `get_posting_time_suggestions("education", "youtube")` | Returns 3 items each with day, time, reason keys |
| E6-S1-T2 | same | Call with `"unknown_industry"` | Returns marketing defaults (3 items) |
| E6-S1-T3 | `src/CP/FrontEnd/src/__tests__/DigitalMarketingActivationWizard.test.tsx` | Render Step 3 with mock `posting_time_suggestions` data | DOM contains "Recommended posting times" text and 3 time entries |

**Test command:**
```bash
cd src/Plant/BackEnd && pytest tests/unit/test_posting_time.py -v
cd src/CP/FrontEnd && npx vitest run src/__tests__/DigitalMarketingActivationWizard.test.tsx
```

**Commit message:** `feat(DMA-CONV-1): E6-S1 — posting-time optimization recommendations`

**Done signal:** `"E6-S1 done. Changed: content_analytics.py, digital_marketing_activation.py, DigitalMarketingActivationWizard.tsx. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

## Iteration 3 — Feedback Loop and Platform Previews

**Scope:** Performance analytics injection into the next theme cycle, platform-accurate content previews in approval UI, end-to-end Docker validation.
**Lane:** B — Plant BackEnd analytics integration + CP FrontEnd preview components
**⏱ Estimated:** 5h | **Come back:** 2026-04-16 06:00 UTC
**Epics:** E7, E8, E9
**Advances:** P4 DMA value (feedback loop) + P2 DMA value (previews) — the DMA autonomously improves over time and customers see exactly what will be posted before approving.

### Dependency Map (Iteration 3)

```
E7-S1 ──► E7-S2    (S2 surfaces recommendations from S1 in UI)
E8-S1              (independent — preview components)
E9-S1              (runs after E7 and E8 are complete — full-path validation)

E7 + E8 ──► E9
```

E7 and E8 are independent. E9 depends on both.

---

### Epic E7: Agent improves from performance data

**Branch:** `feat/DMA-CONV-1-iteration-3` (GitHub Agents auto-creates the task branch)
**User story:** As a customer, my DMA learns from past content performance and uses that data to suggest better themes and content in the next cycle, so that engagement improves automatically over time.

---

#### Story E7-S1: Inject content_analytics recommendations into theme cycle prompt

**BLOCKED UNTIL:** Iteration 2 PR merged to main
**Estimated time:** 90 min
**Branch:** `feat/DMA-CONV-1-iteration-3` (GitHub Agents auto-creates the task branch)
**CP BackEnd pattern:** N/A — Plant BackEnd only

**What to do (self-contained):**

`content_analytics.py` already has `get_content_recommendations(hired_instance_id, db)` which returns `top_dimensions`, `best_posting_hours`, `avg_engagement_rate`, and `recommendation_text` from `PerformanceStatModel`. This data is never fed back into the DMA conversation prompt.

Changes:
1. In `_theme_workshop_prompt()`, when the hired agent has performance history (PerformanceStatModel records exist), call `get_content_recommendations(hired_instance_id=hired_agent.id, db=db)` and inject the results into the prompt payload as a `performance_insights` section.
2. In the system prompt, add: "Performance insights from previous content cycles are provided below. Use these to guide theme recommendations — favor topics and formats that drove higher engagement. Reference specific performance data when making suggestions."
3. When no performance data exists (new customer), omit the section gracefully.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/services/content_analytics.py` | 1-129 | `get_content_recommendations()` — return shape, what metrics it provides |
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | 533-620 | `_theme_workshop_prompt()` — where to add performance insights |
| `src/Plant/BackEnd/models/performance_stat.py` | 1-40 | `PerformanceStatModel` fields |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | modify | In `_theme_workshop_prompt()`: call `get_content_recommendations(hired_instance_id=hired_agent.id, db=db)`. If results exist and `avg_engagement_rate > 0`, add `performance_insights` section to the prompt payload. Add system prompt instruction to use performance data. |

**Code patterns to copy exactly:**

```python
# Import at top:
from services.content_analytics import get_content_recommendations

# In _theme_workshop_prompt(), after brand_voice_section computation:
performance_insights = {}
try:
    recommendations = await get_content_recommendations(
        hired_instance_id=hired_agent.id, db=db
    )
    if recommendations and recommendations.get("avg_engagement_rate", 0) > 0:
        performance_insights = {
            "top_performing_dimensions": recommendations.get("top_dimensions", []),
            "best_posting_hours": recommendations.get("best_posting_hours", []),
            "avg_engagement_rate": recommendations["avg_engagement_rate"],
            "recommendation_summary": recommendations.get("recommendation_text", ""),
        }
except Exception:
    logger.warning("Could not load performance insights — proceeding without")

# Add to prompt payload:
"performance_insights": performance_insights,
```

**Acceptance criteria:**
1. When the hired agent has performance data, the prompt payload includes `performance_insights` with top_performing_dimensions, best_posting_hours, avg_engagement_rate, and recommendation_summary.
2. When no performance data exists, `performance_insights` is an empty dict — no error.
3. The system prompt instructs the LLM to use performance data.
4. Existing tests pass.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E7-S1-T1 | `src/Plant/BackEnd/tests/unit/test_dma_feedback_loop.py` | Mock `get_content_recommendations()` to return `{"avg_engagement_rate": 4.2, "top_dimensions": ["video", "carousel"]}`. Call `_theme_workshop_prompt()` | `performance_insights.avg_engagement_rate == 4.2` and `top_performing_dimensions` contains "video" |
| E7-S1-T2 | same | Mock `get_content_recommendations()` to return `{"avg_engagement_rate": 0}` | `performance_insights == {}` |
| E7-S1-T3 | same | Mock `get_content_recommendations()` to raise Exception | `performance_insights == {}`, no exception propagated |

**Test command:**
```bash
cd src/Plant/BackEnd && pytest tests/unit/test_dma_feedback_loop.py -v
```

**Commit message:** `feat(DMA-CONV-1): E7-S1 — inject performance analytics into DMA conversation prompt`

**Done signal:** `"E7-S1 done. Changed: digital_marketing_activation.py. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

#### Story E7-S2: Surface performance-driven suggestions in wizard UI

**BLOCKED UNTIL:** E7-S1 committed
**Estimated time:** 45 min
**Branch:** `feat/DMA-CONV-1-iteration-3` (GitHub Agents auto-creates the task branch)
**CP BackEnd pattern:** N/A — Plant BackEnd response + CP FrontEnd display

**What to do (self-contained):**

After E7-S1, the backend includes `performance_insights` in the workshop response. Surface this in the wizard UI as a collapsible "Performance Insights" card in the Brief Chat step (Step 2), so the customer can see what content worked before.

Changes:
1. In `DigitalMarketingActivationWizard.tsx`, extract `performance_insights` from the strategy workshop response.
2. Add a collapsible Accordion section below the chat thread (when performance data exists) showing: "Your top-performing content types: {dimensions}. Average engagement: {rate}%. Recommendation: {text}."
3. TypeScript interface update: add `performance_insights` type to the workshop response.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | 2500-2640 | Brief Chat step layout, where to add the insights card |
| `src/CP/FrontEnd/src/services/digitalMarketingActivation.service.ts` | 1-60 | Workshop response TypeScript types |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | modify | In Step 2 (Brief Chat), after the chat messages div, add a collapsible Accordion section that renders performance insights when `strategyWorkshop.performance_insights` has data. |
| `src/CP/FrontEnd/src/services/digitalMarketingActivation.service.ts` | modify | Add `performance_insights?: { top_performing_dimensions: string[], best_posting_hours: number[], avg_engagement_rate: number, recommendation_summary: string }` to the workshop TypeScript interface. |

**Acceptance criteria:**
1. When performance data exists in the workshop response, Step 2 shows a "Performance Insights" accordion.
2. When no performance data exists, no accordion is shown (no empty state).
3. Accordion shows top dimensions, engagement rate, and recommendation text.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E7-S2-T1 | `src/CP/FrontEnd/src/__tests__/DigitalMarketingActivationWizard.test.tsx` | Render wizard with mock workshop containing `performance_insights: { avg_engagement_rate: 4.2, top_performing_dimensions: ["video"], recommendation_summary: "Focus on video" }` | DOM contains "Performance Insights" heading and "video" text |
| E7-S2-T2 | same | Render with `performance_insights: {}` | DOM does NOT contain "Performance Insights" heading |

**Test command:**
```bash
cd src/CP/FrontEnd && npx vitest run src/__tests__/DigitalMarketingActivationWizard.test.tsx
```

**Commit message:** `feat(DMA-CONV-1): E7-S2 — performance insights card in wizard UI`

**Done signal:** `"E7-S2 done. Changed: DigitalMarketingActivationWizard.tsx, digitalMarketingActivation.service.ts. Tests: T1 ✅ T2 ✅"`

---

### Epic E8: Platform-accurate content previews

**Branch:** `feat/DMA-CONV-1-iteration-3` (GitHub Agents auto-creates the task branch)
**User story:** As a customer, I see platform-accurate previews (YouTube thumbnail card, LinkedIn post card, Instagram square, etc.) of each content piece before approving, so I know exactly what will be posted.

---

#### Story E8-S1: Build YouTube/LinkedIn/Instagram preview components for approval UI

**BLOCKED UNTIL:** Iteration 2 PR merged to main
**Estimated time:** 90 min
**Branch:** `feat/DMA-CONV-1-iteration-3` (GitHub Agents auto-creates the task branch)
**CP BackEnd pattern:** N/A — CP FrontEnd only

**What to do (self-contained):**

Currently, generated content is shown as plain text/markdown in the approval step. Customers cannot visualize how it will look on each platform. Build platform-specific preview card components that approximate the real platform appearance.

Changes:
1. Create `src/CP/FrontEnd/src/components/PlatformPreviewCards.tsx` with 3 components:
   - `YouTubePreviewCard`: Mimics a YouTube video card — thumbnail placeholder (16:9 aspect ratio), title (max 2 lines), channel name, view/date metadata.
   - `LinkedInPreviewCard`: Mimics a LinkedIn post — profile header, post text, image placeholder, engagement bar (like/comment/repost/send).
   - `InstagramPreviewCard`: Mimics an Instagram post — square image placeholder, caption below with hashtags.
2. Each component accepts: `title: string`, `text: string`, `hashtags: string[]`, `thumbnailUrl?: string`, `channelName: string`.
3. In `DigitalMarketingActivationWizard.tsx`, in the approval step (Step 4), replace the plain text rendering of posts with the appropriate platform preview component based on `post.channel`.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | 2700-2964 | Step 4 (Review & Activate) — how posts are currently rendered for approval |
| `src/CP/FrontEnd/src/components/DigitalMarketingArtifactPreviewCard.tsx` | 1-85 | Existing artifact preview patterns and styles |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/components/PlatformPreviewCards.tsx` | create | Create file with YouTubePreviewCard, LinkedInPreviewCard, and InstagramPreviewCard React components. Use WAOOAW dark theme (--bg-black: #0a0a0a, --color-neon-cyan: #00f2fe). Each component mimics the target platform layout. Export all three. |
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | modify | In Step 4 post rendering, import the preview cards and conditionally render the appropriate one based on `post.channel`. Default to plain markdown if channel is unknown. |

**Code patterns to copy exactly:**

```typescript
// PlatformPreviewCards.tsx — Component structure
import React from 'react'

interface PlatformPreviewProps {
  title: string
  text: string
  hashtags: string[]
  thumbnailUrl?: string
  channelName: string
}

export const YouTubePreviewCard: React.FC<PlatformPreviewProps> = ({
  title, text, hashtags, thumbnailUrl, channelName
}) => (
  <div style={{
    background: '#0f0f0f', borderRadius: '12px', overflow: 'hidden',
    maxWidth: '360px', fontFamily: 'Roboto, sans-serif',
  }}>
    <div style={{
      width: '100%', aspectRatio: '16/9',
      background: thumbnailUrl ? `url(${thumbnailUrl}) center/cover` : 'linear-gradient(135deg, #667eea, #00f2fe)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      color: '#fff', fontSize: '48px',
    }}>▶</div>
    <div style={{ padding: '12px' }}>
      <div style={{
        color: '#f1f1f1', fontSize: '14px', fontWeight: 500,
        display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
        overflow: 'hidden', lineHeight: '20px', marginBottom: '8px',
      }}>{title}</div>
      <div style={{ color: '#aaa', fontSize: '12px' }}>{channelName}</div>
    </div>
  </div>
)

// LinkedInPreviewCard and InstagramPreviewCard follow the same pattern
// with platform-appropriate layouts
```

**Acceptance criteria:**
1. `YouTubePreviewCard` renders a video card with 16:9 thumbnail, title, and channel name.
2. `LinkedInPreviewCard` renders a post with profile header, text, and engagement bar.
3. `InstagramPreviewCard` renders a square image post with caption and hashtags.
4. Step 4 of the wizard uses the correct preview component per channel.
5. All components use WAOOAW dark theme colors.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E8-S1-T1 | `src/CP/FrontEnd/src/__tests__/PlatformPreviewCards.test.tsx` | Render `YouTubePreviewCard` with title="Test" channelName="WAOOAW" | DOM contains "Test" title and "WAOOAW" channel name |
| E8-S1-T2 | same | Render `LinkedInPreviewCard` with text="Hello world" | DOM contains "Hello world" text and engagement bar icons |
| E8-S1-T3 | same | Render `InstagramPreviewCard` with hashtags=["#ai", "#marketing"] | DOM contains "#ai" and "#marketing" |

**Test command:**
```bash
cd src/CP/FrontEnd && npx vitest run src/__tests__/PlatformPreviewCards.test.tsx
```

**Commit message:** `feat(DMA-CONV-1): E8-S1 — platform-accurate preview cards (YouTube, LinkedIn, Instagram)`

**Done signal:** `"E8-S1 done. Created: PlatformPreviewCards.tsx. Changed: DigitalMarketingActivationWizard.tsx. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

### Epic E9: End-to-end Docker validation

**Branch:** `feat/DMA-CONV-1-iteration-3` (GitHub Agents auto-creates the task branch)
**User story:** As a platform engineer, I can run a Docker-based test that validates the full DMA conversation → theme → content → preview → publish path end-to-end, so that regressions are caught before deploy.

---

#### Story E9-S1: End-to-end Docker validation for conversation → content → preview → publish path

**BLOCKED UNTIL:** E7-S2 and E8-S1 committed
**Estimated time:** 90 min
**Branch:** `feat/DMA-CONV-1-iteration-3` (GitHub Agents auto-creates the task branch)
**CP BackEnd pattern:** N/A

**What to do (self-contained):**

Create an integration test that exercises the full DMA path: conversation discovery (with required fields), theme generation, content generation with brand voice, artifact rendering, and schedule creation. This test runs against the local Docker stack using `docker-compose.test.yml`.

Changes:
1. Create `src/Plant/BackEnd/tests/integration/test_dma_e2e.py` with a test that:
   a. Creates a mock hired agent with a DMA skill configuration.
   b. Simulates a theme workshop conversation that fills all 11 required fields.
   c. Verifies the conversation transitions to `approval_ready` status.
   d. Verifies the workshop response contains `brief_progress.filled == 11`.
   e. Verifies a master theme and derived themes are returned.
   f. Triggers content generation and verifies posts are created with brand voice context.
   g. Verifies artifact_metadata is populated for table artifacts.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/tests/` | directory listing | Existing test structure and fixtures |
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | 1-30, 90-120 | Route definitions, request/response models |
| `docker-compose.test.yml` | 1-50 | How Plant BackEnd tests are configured |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/tests/integration/test_dma_e2e.py` | create | Create an integration test file with test_full_dma_conversation_to_content_path that exercises the complete DMA workflow. Use TestClient from FastAPI and mock the Grok client to return predetermined responses that fill all required fields over 3 conversation turns. |

**Code patterns to copy exactly:**

```python
"""End-to-end integration test for DMA conversation → content pipeline."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

# NFR: waooaw_router pattern — test must use the app that uses waooaw_router
from app.main import app

client = TestClient(app)


class TestDMAE2E:
    """Full-path DMA conversation → theme → content → artifact."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Mock external dependencies for isolated testing."""
        # Mock Grok client, database sessions, etc.
        pass

    def test_conversation_reaches_approval_ready(self):
        """After filling all 11 required fields, status transitions to approval_ready."""
        # Test implementation
        pass

    def test_artifact_metadata_populated_for_table(self):
        """Table artifacts include artifact_metadata.table_preview with columns and rows."""
        # Test implementation
        pass

    def test_brand_voice_injected_when_available(self):
        """When customer has a brand voice, it appears in the prompt payload."""
        # Test implementation
        pass
```

**Acceptance criteria:**
1. Integration test file exists and can be discovered by pytest.
2. `test_conversation_reaches_approval_ready` validates the full 11-field collection → approval_ready transition.
3. `test_artifact_metadata_populated_for_table` validates table artifacts have structured preview data.
4. `test_brand_voice_injected_when_available` validates brand voice injection.
5. All tests pass with mocked Grok client (no real LLM calls).

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E9-S1-T1 | `src/Plant/BackEnd/tests/integration/test_dma_e2e.py` | Simulate 3 conversation turns filling all 11 fields | Final response status is `approval_ready`, `brief_progress.filled == 11` |
| E9-S1-T2 | same | Generate table artifact from derived themes | `artifact_metadata.table_preview.columns` has 4 items |
| E9-S1-T3 | same | Load brand voice before prompt call | Prompt payload contains `brand_voice_context.tone_keywords` |

**Test command:**
```bash
cd src/Plant/BackEnd && pytest tests/integration/test_dma_e2e.py -v
# Or via Docker:
docker-compose -f docker-compose.test.yml run plant-test pytest tests/integration/test_dma_e2e.py -v
```

**Commit message:** `feat(DMA-CONV-1): E9-S1 — end-to-end DMA integration test`

**Done signal:** `"E9-S1 done. Created: test_dma_e2e.py. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

## Appendix: File Index

All files referenced in this plan, grouped by service:

### Plant BackEnd
| File | Purpose | Stories |
|---|---|---|
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | Main DMA API — prompt, parsing, draft builder | E1-S1, E1-S2, E2-S1, E2-S2, E3-S1, E4-S1, E4-S2, E5-S1, E5-S2, E6-S1, E7-S1 |
| `src/Plant/BackEnd/agent_mold/reference_agents.py` | THEME_DISCOVERY_REQUIRED_FIELDS | E1-S1, E1-S2, E2-S2 |
| `src/Plant/BackEnd/agent_mold/skills/content_creator.py` | Theme and post generation | E4-S1, E5-S2 |
| `src/Plant/BackEnd/agent_mold/skills/content_models.py` | PostGeneratorInput, CampaignBrief, ThemeDiscoveryBrief models | E5-S2 |
| `src/Plant/BackEnd/services/brand_voice_service.py` | Brand voice CRUD | E4-S1 |
| `src/Plant/BackEnd/services/content_analytics.py` | Performance recommendations + posting times | E6-S1, E7-S1 |
| `src/Plant/BackEnd/models/brand_voice.py` | BrandVoiceModel | E4-S1 |
| `src/Plant/BackEnd/models/performance_stat.py` | PerformanceStatModel | E7-S1 |
| `src/Plant/BackEnd/services/draft_batches.py` | DraftPostRecord schema | E3-S1 |

### CP FrontEnd
| File | Purpose | Stories |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | 4-step DMA wizard UI | E2-S1, E3-S1, E6-S1, E7-S2, E8-S1 |
| `src/CP/FrontEnd/src/components/DigitalMarketingArtifactPreviewCard.tsx` | Artifact preview rendering | E3-S1, E3-S2 |
| `src/CP/FrontEnd/src/components/PlatformPreviewCards.tsx` | Platform preview components (new) | E8-S1 |
| `src/CP/FrontEnd/src/services/digitalMarketingActivation.service.ts` | Workshop TypeScript types | E2-S1, E7-S2 |

### Tests
| File | Purpose | Stories |
|---|---|---|
| `src/Plant/BackEnd/tests/unit/test_dma_prompt_fields.py` (new) | Prompt field injection, validation gate, progress | E1-S1, E1-S2, E2-S1, E2-S2 |
| `src/Plant/BackEnd/tests/unit/test_dma_auto_draft.py` (new) | Auto-draft table artifact | E3-S1 |
| `src/Plant/BackEnd/tests/unit/test_dma_brand_voice.py` (new) | Brand voice injection, content pillars | E4-S1, E4-S2 |
| `src/Plant/BackEnd/tests/unit/test_dma_market_context.py` (new) | Competitor/niche context, hashtags | E5-S1, E5-S2 |
| `src/Plant/BackEnd/tests/unit/test_posting_time.py` (new) | Posting time recommendations | E6-S1 |
| `src/Plant/BackEnd/tests/unit/test_dma_feedback_loop.py` (new) | Performance analytics injection | E7-S1 |
| `src/Plant/BackEnd/tests/integration/test_dma_e2e.py` (new) | End-to-end DMA path | E9-S1 |
| `src/CP/FrontEnd/src/__tests__/DigitalMarketingArtifactPreviewCard.test.tsx` | Artifact preview tests | E3-S1, E3-S2 |
| `src/CP/FrontEnd/src/__tests__/DigitalMarketingActivationWizard.test.tsx` | Wizard UI tests | E2-S1, E6-S1, E7-S2 |
| `src/CP/FrontEnd/src/__tests__/PlatformPreviewCards.test.tsx` (new) | Platform preview tests | E8-S1 |
