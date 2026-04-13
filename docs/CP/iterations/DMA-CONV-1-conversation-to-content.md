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
- Iteration 1 merge status: `[PENDING HUMAN UPDATE BEFORE LAUNCH]`
- Iteration 1 PR: `[PR URL or #NUMBER]`
- Merge commit on `main`: `[FULL SHA]`
- Merged at: `[UTC TIMESTAMP]`

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
| E1-S1 | 1 | Prompt rewrite with required-fields gate | Rewrite system prompt with field checklist, lock-and-confirm rules, and full context injection | 🔴 Not Started | — |
| E1-S2 | 1 | Prompt rewrite with required-fields gate | Server-side field-completeness validation before approval_ready transition | 🔴 Not Started | — |
| E2-S1 | 1 | Customer sees conversation progress | Add field-level progress counter to response contract and wizard UI | 🔴 Not Started | — |
| E2-S2 | 1 | Customer sees conversation progress | Align workshop summary fields to required-fields list and CampaignBrief model | 🔴 Not Started | — |
| E3-S1 | 1 | Artifact rendering fix | Diagnose and fix table artifact not rendering after DMA-MEDIA-1 deploy | 🔴 Not Started | — |
| E3-S2 | 1 | Artifact rendering fix | Verify image/video/audio artifact request-to-preview path works end-to-end | 🔴 Not Started | — |
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

**Branch:** `feat/DMA-CONV-1-it1-e1`
**User story:** As a customer, I can brief my DMA in a conversation that concludes when I've given enough information, so that I get a master theme and supporting themes instead of endless questions.

---

#### Story E1-S1: Rewrite system prompt with required-fields checklist, lock-and-confirm rules, and full structured context

**BLOCKED UNTIL:** none
**Estimated time:** 90 min
**Branch:** `feat/DMA-CONV-1-it1-e1`
**CP BackEnd pattern:** N/A — Plant BackEnd only

**What to do (self-contained):**

The current system prompt in `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` lines 1088-1094 tells the LLM to "move to approval_ready as soon as coherent" but never defines what coherent means. The 11 required fields exist in `src/Plant/BackEnd/agent_mold/reference_agents.py` lines 52-63 (`THEME_DISCOVERY_REQUIRED_FIELDS`) but are never mentioned in the prompt. The message history is truncated to the last 4 messages (line 388 `normalized[-4:]`) which causes the agent to forget earlier answers.

Changes:
1. In `_theme_workshop_prompt()` (line 533), inject the `THEME_DISCOVERY_REQUIRED_FIELDS` list into the prompt payload as a `required_fields_checklist` with current fill status (filled/empty for each field based on the workshop summary).
2. In the system prompt (line 1088), add explicit rules: (a) "Here are the 11 fields you must collect. When a field has a value, it is LOCKED — never ask about it again." (b) "When the customer gives a direct answer, lock that field and confirm in one sentence. Do NOT re-offer locked fields as next-step options." (c) "When all 11 fields are filled, you MUST set status to approval_ready and present the master theme for approval. Do not ask more questions." (d) "When the customer asks for any concrete deliverable (plan, table, draft, schedule), produce it immediately. Do not deflect with more questions."
3. Change `_normalize_workshop_messages()` line 388 from `normalized[-4:]` to `normalized[-12:]` so the LLM retains more conversation context.
4. In the `workshop_state` section of the prompt payload, add `locked_fields` (dict of field_name → value for all non-empty fields) and `missing_fields` (list of field names still empty) derived from the workshop summary.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | 375-395, 480-620, 1080-1130 | `_normalize_workshop_messages` truncation, `_theme_workshop_prompt` payload construction, system prompt text |
| `src/Plant/BackEnd/agent_mold/reference_agents.py` | 52-63 | `THEME_DISCOVERY_REQUIRED_FIELDS` list |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | modify | 1. Line 388: change `normalized[-4:]` to `normalized[-12:]`. 2. In `_theme_workshop_prompt()`: add `required_fields_checklist`, `locked_fields`, `missing_fields` to the JSON payload under `workshop_state`. 3. In `generate_theme_plan()` system prompt (line 1088): add the four rules listed above. |

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
4. All existing tests in `src/Plant/BackEnd/tests/` that reference `digital_marketing_activation` still pass.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S1-T1 | `src/Plant/BackEnd/tests/unit/test_dma_prompt_fields.py` | Call `_theme_workshop_prompt()` with a workspace where 6 of 11 summary fields are filled | `required_fields_checklist.filled == 6`, `required_fields_checklist.missing == 5`, `locked_fields` has 6 keys |
| E1-S1-T2 | same | Call `_normalize_workshop_messages()` with 15 messages | Returns exactly 12 messages (not 4) |
| E1-S1-T3 | same | Call `_theme_workshop_prompt()` with all 11 fields filled | `missing_fields` is empty list |

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
**Branch:** `feat/DMA-CONV-1-it1-e1`
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

**Branch:** `feat/DMA-CONV-1-it1-e2`
**User story:** As a customer, I can see a progress indicator ("8/11 fields locked") during the DMA conversation, so that I know how close I am to finishing and feel motivated to complete.

---

#### Story E2-S1: Add field-level progress counter to response contract and wizard UI

**BLOCKED UNTIL:** none
**Estimated time:** 90 min
**Branch:** `feat/DMA-CONV-1-it1-e2`
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
| `src/Plant/BackEnd/api/v1/digital_marketing_activation.py` | modify | In `_parse_theme_workshop_response()`, after the validation gate from E1-S2, compute `brief_progress` dict and add it to the `workshop` dict before returning. |
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
**Branch:** `feat/DMA-CONV-1-it1-e2`
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

**Branch:** `feat/DMA-CONV-1-it1-e3`
**User story:** As a customer, I can see tables, images, and media artifacts rendered in the DMA wizard after the agent generates them, so that I can review and approve real content instead of seeing blank cards.

---

#### Story E3-S1: Diagnose and fix table artifact not rendering after DMA-MEDIA-1 deploy

**BLOCKED UNTIL:** none
**Estimated time:** 90 min
**Branch:** `feat/DMA-CONV-1-it1-e3`
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
**Branch:** `feat/DMA-CONV-1-it1-e3`
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

> Stories for Iteration 2 will be committed in the next chunk.

---

## Iteration 3 — Feedback Loop and Platform Previews

> Stories for Iteration 3 will be committed in the next chunk.
