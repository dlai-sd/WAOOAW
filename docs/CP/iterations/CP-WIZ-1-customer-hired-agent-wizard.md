# CP-WIZ-1 — Customer Hired-Agent Wizard Iteration Plan

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `CP-WIZ-1` |
| Feature area | Customer Portal — Hired Agent Wizard |
| Created | 2026-03-17 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/plant/iterations/CP_MyAgents.md` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 1 |
| Total epics | 3 |
| Total stories | 6 |

---

## Objective

Replace CP's long hired-agent management surface with one wizard-based customer experience. Customers coming from the hire journey should land directly on the newly hired agent's wizard, while customers opening My Agents should begin with agent selection and then follow the same step model for activation or lighter post-activation edits.

The target user experience is one consistent studio pattern inspired by PP Agent Studio: a visible progress rail, one active step at a time, explicit readiness messaging, and no long vertical admin-style configuration surface. Active agents should stay editable through the same step model, but with lighter copy and no trial-activation framing.

---

## Zero-Cost Agent Constraints (READ FIRST)

This plan is designed for autonomous zero-cost model agents with limited context windows.

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is self-contained and names exact files |
| No working memory across files | NFR code patterns are embedded inline in each backend story |
| No planning ability | Stories are atomic, sequential, and acceptance criteria are binary |
| Token cost per file read | Max 3 files to read first per story |
| User requested single iteration | All work is sequenced into one iteration with sequential checkpoints |
| User requested testing at end | Tests are authored story-by-story but executed together in the final validation story |

---

## PM Review Checklist (tick every box before publishing)

- [x] EXPERT PERSONAS filled
- [x] Epic titles name customer outcomes, not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR code snippets inline
- [x] Every story card has max 3 files in Files to read first
- [x] Every story involving CP BackEnd states the exact pattern: A, B, or C
- [x] Every new backend route story embeds the `waooaw_router()` snippet
- [x] Every GET route story card says `get_read_db_session()` not `get_db_session()`
- [x] Every story has `BLOCKED UNTIL` or `none`
- [x] Iteration count minimized to one
- [x] Agent execution rules include sequential push checkpoints and final testing rule
- [x] No placeholders remain

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane B — add a Plant-backed hired-agent studio contract, proxy it through CP, and replace CP's long My Agents surface with one shared wizard used by hire flow and post-activation edits | 3 | 6 | 6h | 2026-03-17 21:00 IST |

**Estimate basis:** Plant backend contract = 90 min, CP thin proxy + FE service = 45 min, shared wizard refactor = 90 min, My Agents migration = 90 min, entry wiring = 45 min, final regression = 30 min.

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
7. Go away. Come back at: **2026-03-17 21:00 IST**

**Iteration 1 agent task** (paste verbatim — do not modify):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / SQLAlchemy engineer + Senior React 18 / TypeScript / Vite engineer + Senior Docker / CI validation engineer
Activate these personas NOW. Begin each epic with:
	"Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-WIZ-1-customer-hired-agent-wizard.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2, E3.
TIME BUDGET: 6h. If you reach 7h without finishing, follow STUCK PROTOCOL now.

EXECUTION ORDER:
1. Run: git status && git log --oneline -3
	 You must be on main with a clean tree. If not, post why and HALT.
2. Read the "Agent Execution Rules" section in this plan file.
3. Read the "Iteration 1" section in this plan file.
4. Read nothing else before starting.
5. Execute Epics in this order: E1 → E2 → E3.
6. Write the tests listed in each story before moving to the next story.
7. Do not run the full regression matrix until E3-S1.
8. When all listed final commands pass, open the iteration PR. Post the PR URL. HALT.
```

---

## Agent Execution Rules

### Rule -1 — Activate Expert Personas

Read the `EXPERT PERSONAS:` field from the task you were given and activate each persona immediately. For every epic you execute, open with one line:

> *"Acting as a [persona], I will [what you're building] by [approach]."*

### Rule 0 — Open the epic branch first

```bash
git checkout main && git pull
git checkout -b feat/cp-wiz-1-it1-e1
git push -u origin feat/cp-wiz-1-it1-e1
```

For later epics, create `feat/cp-wiz-1-it1-e2` and `feat/cp-wiz-1-it1-e3` from `main` after the previous epic branch is safely pushed.

### Rule 1 — Scope lock

Implement exactly the acceptance criteria in the story card. Do not add PP feature work, do not create a separate advanced customer console, and do not move business logic into CP BackEnd.

### Rule 2 — One branch per epic, one push per story

Each epic gets its own branch. After every story, commit the implementation and the authored tests, push that branch, then move to the next story on the same epic branch.

### Rule 3 — Tests are authored during each story, full execution happens at the end

Write every test listed in the story card before moving to the next story. Do not spend time running the full regression matrix after each story unless the story card explicitly asks for a lightweight smoke check.

### Rule 4 — Commit + push after every story

```bash
git add -A
git commit -m "feat(cp-wiz-1): [story title]"
git push origin feat/cp-wiz-1-itN-eN
```

After pushing, update this plan file's Tracking Table status for that story, commit the doc change, and push again before starting the next story.

### Rule 5 — Final testing only in E3-S1

The full test commands listed in E3-S1 are the required end-of-iteration validation gate. Fix only in-scope failures discovered by those commands.

### Rule 6 — STUCK PROTOCOL

If the same failure survives 3 focused attempts:

```bash
git add -A && git commit -m "WIP: [story-id] blocked — [exact error]"
git push origin feat/cp-wiz-1-itN-eN
```

Then open a draft PR titled `WIP: [story-id] — blocked`, paste the exact failing command and error, and HALT.

### Rule 7 — Iteration PR

After E3-S1 passes:

```bash
git checkout main && git pull
git checkout -b feat/cp-wiz-1-it1
git merge --no-ff feat/cp-wiz-1-it1-e1 feat/cp-wiz-1-it1-e2 feat/cp-wiz-1-it1-e3
git push origin feat/cp-wiz-1-it1
gh pr create --base main --head feat/cp-wiz-1-it1 --title "feat(cp-wiz-1): unify hired-agent wizard flow" --body "See docs/CP/iterations/CP-WIZ-1-customer-hired-agent-wizard.md"
```

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | Customer data contract supports one wizard | Add Plant hired-agent studio snapshot route | 🔴 Not Started | — |
| E1-S2 | 1 | Customer data contract supports one wizard | Add Plant studio update route for activation and edit mode | 🔴 Not Started | — |
| E2-S1 | 1 | CP surfaces one shared wizard | Add CP thin proxy and CP frontend studio service | 🔴 Not Started | — |
| E2-S2 | 1 | CP surfaces one shared wizard | Refactor hire flow onto a shared wizard shell | 🔴 Not Started | — |
| E2-S3 | 1 | CP surfaces one shared wizard | Replace My Agents long form with wizard-first agent studio | 🔴 Not Started | — |
| E3-S1 | 1 | Delivery proof closes the iteration | Rewire entry points and run final regression matrix | 🔴 Not Started | — |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

---

## Iteration 1 — Customer Uses One Wizard Everywhere

**Scope:** Customers no longer see a long hired-agent configuration page in CP; both hire flow and My Agents use the same wizard model.
**Lane:** B — new Plant endpoint contract plus CP thin-proxy work required.
**⏱ Estimated:** 6h | **Come back:** 2026-03-17 21:00 IST
**Epics:** E1, E2, E3

### Dependency Map (Iteration 1)

```text
E1-S1 -> E1-S2 -> E2-S1 -> E2-S2 -> E2-S3 -> E3-S1
```

---

### Epic E1: Customer data contract supports one wizard

**Branch:** `feat/cp-wiz-1-it1-e1`
**User story:** As a paying customer, I can load one clear hired-agent wizard state from the backend, so the UI does not have to stitch together a long admin-style screen from scattered calls.

---

#### Story E1-S1: Add Plant hired-agent studio snapshot route

**BLOCKED UNTIL:** none
**Estimated time:** 90 min
**Branch:** `feat/cp-wiz-1-it1-e1`
**CP BackEnd pattern:** N/A

**What to do (self-contained — read this card, then act):**
> Create a dedicated Plant route file named `src/Plant/BackEnd/api/v1/hired_agent_studio.py` that exposes a customer-facing read model for the wizard instead of forcing CP to stitch together `by-subscription`, platform connection, and goal state on its own. The new `GET /api/v1/hired-agents/{hired_instance_id}/studio` response must return lifecycle mode (`activation` or `edit`), whether agent selection is required, current step key, per-step completion flags, identity fields, connection readiness summary, operating-plan readiness, and review-state messaging derived from existing hired-agent, platform-connection, and goal/config records.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/api/v1/router.py` | 1-40 | Current router import and include pattern |
| `src/Plant/BackEnd/api/v1/hired_agents_simple.py` | 1065-1120 | Current `by-subscription` and hired-agent response shape |
| `src/Plant/BackEnd/api/v1/platform_connections.py` | 158-240 | Current connection status fields and read route behavior |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/api/v1/hired_agent_studio.py` | create | Add the new studio snapshot route, response models, and helper mappers for wizard steps |
| `src/Plant/BackEnd/api/v1/router.py` | modify | Import the new module and include its router in `api_v1_router` |
| `src/Plant/BackEnd/tests/unit/test_hired_agent_studio_api.py` | create | Add ownership, readiness, and mode-mapping tests for the new route |

**Code patterns to copy exactly** (no other file reads needed for these):

```python
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.routing import waooaw_router
from core.database import get_read_db_session

router = waooaw_router(prefix="/hired-agents", tags=["hired-agent-studio"])

@router.get("/{hired_instance_id}/studio")
async def get_hired_agent_studio(
		hired_instance_id: str,
		customer_id: str,
		db: AsyncSession = Depends(get_read_db_session),
):
		if not customer_id.strip():
				raise HTTPException(status_code=400, detail="customer_id is required.")
		...
```

**Acceptance criteria (binary pass/fail only):**
1. `GET /api/v1/hired-agents/{id}/studio?customer_id=...` returns `200` for an owned hired agent and includes `mode`, `current_step`, and a `steps` array.
2. A not-yet-activated hired agent returns `mode="activation"` and a completed/blocked state that reflects existing identity, connection, and operating-plan data.
3. An already active hired agent returns `mode="edit"` and does not report the customer as being in trial-start activation mode.
4. A non-owner request returns a non-leaking `404` or the current platform-safe equivalent.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S1-T1 | `src/Plant/BackEnd/tests/unit/test_hired_agent_studio_api.py` | Owned hired agent with no connection and incomplete plan | Response `200`, `mode=activation`, connection step incomplete |
| E1-S1-T2 | same | Owned active hired agent with connection + goals complete | Response `200`, `mode=edit`, review step present without activation copy |
| E1-S1-T3 | same | Non-owner customer_id | Response hides the record |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/unit/test_hired_agent_studio_api.py -v
```

**Commit message:** `feat(cp-wiz-1): add hired agent studio snapshot route`

**Done signal (post as a comment then continue):**
`"E1-S1 done. Added Plant studio snapshot route and authored T1-T3."`

---

#### Story E1-S2: Add Plant studio update route for activation and edit mode

**BLOCKED UNTIL:** E1-S1 committed to `feat/cp-wiz-1-it1-e1`
**Estimated time:** 90 min
**Branch:** `feat/cp-wiz-1-it1-e1`
**CP BackEnd pattern:** N/A

**What to do:**
> Extend `src/Plant/BackEnd/api/v1/hired_agent_studio.py` with a write route that lets CP save wizard changes through one step-aware contract instead of juggling unrelated mutation calls from the page layer. The new `PATCH /api/v1/hired-agents/{hired_instance_id}/studio` request should support the step-scoped fields needed for customer wizard editing now: identity (`nickname`, `theme`), connection selection/reference fields, operating-plan config deltas, and review/finalization intent, while preserving existing read-only protection for canceled or expired subscriptions.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/api/v1/hired_agent_studio.py` | 1-220 | The snapshot model and helper functions created in E1-S1 |
| `src/Plant/BackEnd/api/v1/hired_agents_simple.py` | 880-1045 | Existing draft upsert and finalize semantics |
| `src/Plant/BackEnd/api/v1/skill_configs.py` | 1-160 | Current customer-config write pattern for operating-plan updates |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/api/v1/hired_agent_studio.py` | modify | Add the PATCH request model and step-aware save handler |
| `src/Plant/BackEnd/tests/unit/test_hired_agent_studio_api.py` | modify | Add write-path tests for identity edit, plan edit, and read-only rejection |

**Code patterns to copy exactly:**

```python
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException

@router.patch("/{hired_instance_id}/studio")
async def update_hired_agent_studio(
		hired_instance_id: str,
		body: StudioUpdateRequest,
		db: AsyncSession = Depends(get_db_session),
):
		record = await _load_owned_record(...)
		await _assert_writable(record, db=db)
		...
```

**Acceptance criteria:**
1. Identity updates save through the studio route and are reflected immediately in the snapshot response.
2. Operating-plan edits do not reset an active agent back into trial activation mode.
3. A canceled or read-only hired agent returns the existing writable-protection error instead of accepting edits.
4. The response remains step-oriented and usable by the CP wizard without additional transformation.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S2-T1 | `src/Plant/BackEnd/tests/unit/test_hired_agent_studio_api.py` | PATCH identity fields on owned active record | Nickname/theme persist and response stays `mode=edit` |
| E1-S2-T2 | same | PATCH operating-plan payload | Config updated without invalid lifecycle reset |
| E1-S2-T3 | same | PATCH against canceled subscription | `409` read-only protection |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/unit/test_hired_agent_studio_api.py -v
```

**Commit message:** `feat(cp-wiz-1): add hired agent studio update route`

**Done signal:** `"E1-S2 done. Added studio write path and authored T1-T3."`

---

### Epic E2: CP surfaces one shared wizard

**Branch:** `feat/cp-wiz-1-it1-e2`
**User story:** As a customer, I use the same step model whether I came from payment-confirmed hire flow or opened My Agents later.

---

#### Story E2-S1: Add CP thin proxy and CP frontend studio service

**BLOCKED UNTIL:** E1-S2 merged into local working context for Iteration 1
**Estimated time:** 45 min
**Branch:** `feat/cp-wiz-1-it1-e2`
**CP BackEnd pattern:** B — create new `api/cp_<resource>.py` proxy

**What to do:**
> Create a new CP thin-proxy route so CP FrontEnd can call a clean customer-facing studio contract instead of reaching into multiple legacy endpoints. Add `src/CP/BackEnd/api/cp_hired_agent_studio.py` to proxy the Plant `GET` and `PATCH` studio routes, then add `src/CP/FrontEnd/src/services/hiredAgentStudio.service.ts` so both HireSetupWizard and MyAgents call one typed service surface.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/BackEnd/api/hire_wizard.py` | 1-180 | Existing CP proxy style for hire-related flows |
| `src/CP/FrontEnd/src/services/hireWizard.service.ts` | 1-60 | Current service typing pattern |
| `src/CP/BackEnd/main.py` | 1-180 | Router include pattern for CP APIs |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/BackEnd/api/cp_hired_agent_studio.py` | create | Add GET and PATCH thin-proxy endpoints under `/cp/hired-agents/{hired_instance_id}/studio` |
| `src/CP/BackEnd/main.py` | modify | Include the new CP studio router |
| `src/CP/BackEnd/tests/test_cp_hired_agent_studio.py` | create | Add proxy tests for GET, PATCH, and auth ownership passthrough |
| `src/CP/FrontEnd/src/services/hiredAgentStudio.service.ts` | create | Add typed GET/PATCH service helpers backed by `gatewayRequestJson` |

**Code patterns to copy exactly:**

```python
from fastapi import Depends

from core.routing import waooaw_router
from api.auth.dependencies import get_current_user
from services.plant_gateway_client import PlantGatewayClient
from services.audit_dependency import get_audit_logger

router = waooaw_router(prefix="/cp/hired-agents", tags=["cp-hired-agent-studio"])

@router.get("/{hired_instance_id}/studio")
async def get_hired_agent_studio(hired_instance_id: str, current_user=Depends(get_current_user)):
		client = PlantGatewayClient()
		response = await client.get(f"/api/v1/hired-agents/{hired_instance_id}/studio?customer_id={current_user.id}")
		response.raise_for_status()
		return response.json()
```

```typescript
import { gatewayRequestJson } from './gatewayApiClient'

export async function getHiredAgentStudio(hiredInstanceId: string) {
	return gatewayRequestJson(`/cp/hired-agents/${encodeURIComponent(hiredInstanceId)}/studio`)
}

export async function updateHiredAgentStudio(hiredInstanceId: string, body: Record<string, unknown>) {
	return gatewayRequestJson(`/cp/hired-agents/${encodeURIComponent(hiredInstanceId)}/studio`, {
		method: 'PATCH',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body),
	})
}
```

**Acceptance criteria:**
1. CP FrontEnd has one typed service for hired-agent studio GET/PATCH.
2. CP BackEnd remains a thin proxy and sends `customer_id`/auth context through without owning business logic.
3. PATCH calls emit the normal CP audit path and do not introduce a second bespoke customer wizard route family.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S1-T1 | `src/CP/BackEnd/tests/test_cp_hired_agent_studio.py` | Mock Plant client success on GET | Response `200` and customer-scoped URL used |
| E2-S1-T2 | same | Mock Plant client success on PATCH | Response `200` and payload forwarded |
| E2-S1-T3 | `src/CP/FrontEnd/src/__tests__/hiredAgentStudio.service.test.ts` | Mock `gatewayRequestJson` | Correct CP route and method used |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run cp-test pytest src/CP/BackEnd/tests/test_cp_hired_agent_studio.py -v
cd src/CP/FrontEnd && npx vitest run src/__tests__/hiredAgentStudio.service.test.ts
```

**Commit message:** `feat(cp-wiz-1): add cp hired agent studio proxy`

**Done signal:** `"E2-S1 done. Added CP proxy/service and authored T1-T3."`

---

#### Story E2-S2: Refactor hire flow onto a shared wizard shell

**BLOCKED UNTIL:** E2-S1 committed to `feat/cp-wiz-1-it1-e2`
**Estimated time:** 90 min
**Branch:** `feat/cp-wiz-1-it1-e2`
**CP BackEnd pattern:** C — use existing CP/Plant service contract from FE, no new BE file

**What to do:**
> Extract a shared customer wizard shell from the current hire flow and PP Agent Studio pattern so CP stops owning two different interaction models. Create shared wizard components under `src/CP/FrontEnd/src/components/` and refactor `src/CP/FrontEnd/src/pages/HireSetupWizard.tsx` to use them, with hire entry skipping agent-selection and starting directly at identity for the known hired agent.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/pages/HireSetupWizard.tsx` | 1-220 and 640-860 | Current step flow, copy, and marketing connection logic |
| `src/PP/FrontEnd/src/pages/AgentSetupStudio.tsx` | 312-590 | Step rail, single active canvas, action bar pattern |
| `src/CP/FrontEnd/src/services/hiredAgentStudio.service.ts` | 1-120 | Shared data contract from E2-S1 |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/components/HiredAgentWizardShell.tsx` | create | Add shared rail + canvas + action bar shell |
| `src/CP/FrontEnd/src/components/HiredAgentWizardSteps.tsx` | create | Add step rendering for selection, identity, connection, plan, review |
| `src/CP/FrontEnd/src/pages/HireSetupWizard.tsx` | modify | Replace bespoke page structure with the shared shell and skip selection step when agent is already known |
| `src/CP/FrontEnd/src/styles/globals.css` | modify | Add wizard shell styles aligned with CP/PP studio feel |
| `src/CP/FrontEnd/src/test/HireSetupWizard.test.tsx` | modify | Update and expand tests for shared-shell behavior |

**Code patterns to copy exactly:**

```typescript
const [loading, setLoading] = useState(true)
const [error, setError] = useState<string | null>(null)

useEffect(() => {
	loadWizard()
		.catch((e) => setError(e instanceof Error ? e.message : 'Failed to load wizard'))
		.finally(() => setLoading(false))
}, [])

if (loading) return <LoadingIndicator message="Loading wizard..." size="medium" />
if (error) return <FeedbackMessage intent="error" message={error} />
```

**Acceptance criteria:**
1. Hire flow no longer uses its own bespoke hero + pill layout; it renders through the shared wizard shell.
2. Customers coming from hire flow do not see an agent-selection step before identity.
3. Existing marketing connection behavior still lands inside the connection step of the shared wizard.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S2-T1 | `src/CP/FrontEnd/src/test/HireSetupWizard.test.tsx` | Render known subscription route | Selection step absent and identity step is current |
| E2-S2-T2 | same | Marketing agent with existing YouTube connection mock | Connection step renders inside shared shell |
| E2-S2-T3 | same | Wizard load failure | Error state visible instead of blank screen |

**Test command:**
```bash
cd src/CP/FrontEnd && npx vitest run src/test/HireSetupWizard.test.tsx
```

**Commit message:** `feat(cp-wiz-1): refactor hire flow onto shared wizard shell`

**Done signal:** `"E2-S2 done. Shared shell added and hire-flow tests authored."`

---

#### Story E2-S3: Replace My Agents long form with wizard-first agent studio

**BLOCKED UNTIL:** E2-S2 committed to `feat/cp-wiz-1-it1-e2`
**Estimated time:** 90 min
**Branch:** `feat/cp-wiz-1-it1-e2`
**CP BackEnd pattern:** C — use existing CP studio service from FE, no new BE file

**What to do:**
> Replace the current long My Agents detail page with the shared wizard shell so customers never fall back to a vertical configuration console. `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` must become a wizard-first entry surface where step 1 is always agent selection, then the same step model drives both pending activation and lighter active-agent edits using the studio snapshot contract.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | 1806-2290 | Current selector, tab row, and long render stack |
| `src/CP/FrontEnd/src/components/HiredAgentWizardShell.tsx` | 1-240 | Shared shell from E2-S2 |
| `src/CP/FrontEnd/src/services/myAgentsSummary.service.ts` | 1-40 | Current subscription list source for step-1 selection |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | modify | Remove the default Configure/Goal Setting/Skills/Performance stack and replace it with wizard-first flow |
| `src/CP/FrontEnd/src/components/AgentSelector.tsx` | modify | Ensure the selector can act as a true step-1 wizard control with clear empty and single-agent states |
| `src/CP/FrontEnd/src/__tests__/MyAgents.test.tsx` | modify | Replace long-form expectations with wizard-first assertions |
| `src/CP/FrontEnd/src/styles/globals.css` | modify | Remove or demote styles that only exist for the old long management stack |

**Code patterns to copy exactly:**

```typescript
if (loading) return <LoadingIndicator message="Loading your agents..." size="medium" />
if (error) return <FeedbackMessage intent="error" message={error} />
if (!instances.length) return <EmptyState />

return (
	<HiredAgentWizardShell
		mode={selectedStudio.mode}
		selectionRequired
		...
	/>
)
```

**Acceptance criteria:**
1. My Agents no longer shows the old Configure/Goal Setting/Skills/Performance button row as the default customer path.
2. Step 1 in My Agents is agent selection, even when the selected agent is already active.
3. Active agents use the same step model with lighter edit wording instead of activation wording.
4. Customers can switch agents and stay inside the wizard model instead of dropping into a separate operations page.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S3-T1 | `src/CP/FrontEnd/src/__tests__/MyAgents.test.tsx` | Multiple hired agents in summary | Step 1 selection is visible |
| E2-S3-T2 | same | Active hired agent studio snapshot | Shared wizard renders in edit mode |
| E2-S3-T3 | same | Empty summary | Empty state shown without old management card |

**Test command:**
```bash
cd src/CP/FrontEnd && npx vitest run src/__tests__/MyAgents.test.tsx
```

**Commit message:** `feat(cp-wiz-1): replace my agents long form with wizard`

**Done signal:** `"E2-S3 done. My Agents is wizard-first and tests are authored."`

---

### Epic E3: Delivery proof closes the iteration

**Branch:** `feat/cp-wiz-1-it1-e3`
**User story:** As a PM or reviewer, I can see one coherent CP wizard flow with working entry points and regression proof, so the iteration can merge without guessing.

---

#### Story E3-S1: Rewire entry points and run final regression matrix

**BLOCKED UNTIL:** E2-S3 committed to `feat/cp-wiz-1-it1-e2`
**Estimated time:** 45 min
**Branch:** `feat/cp-wiz-1-it1-e3`
**CP BackEnd pattern:** C — FE wiring only, using existing service routes

**What to do:**
> Clean up the CP entry points so payment-confirmed and portal-return flows land in the right wizard state and no copy implies that customers should return to a long operations screen. Update `HireReceipt.tsx`, `AuthenticatedPortal.tsx`, and any route-level handoff state needed for wizard entry, then run the full end-of-iteration regression commands after merging the epic branches locally or cherry-picking the iteration scope into the validation branch.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/pages/HireReceipt.tsx` | 1-120 | Current post-payment CTA behavior |
| `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx` | 150-455 | Current portalEntry handling and My Agents navigation |
| `docs/CP/iterations/CP-WIZ-1-customer-hired-agent-wizard.md` | Tracking Table + Iteration 1 | Story test matrix to execute |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/pages/HireReceipt.tsx` | modify | Make the primary continuation and supporting copy align with the new wizard entry model |
| `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx` | modify | Pass selected subscription / wizard context cleanly into My Agents and shared wizard mode |
| `src/CP/FrontEnd/src/__tests__/AuthenticatedPortal.test.tsx` | modify | Cover portal entry into the wizard-first My Agents flow |
| `src/CP/FrontEnd/src/__tests__/AuthenticatedPortal.test.tsx` | modify | Update any broken expectations caused by removing the old management surface |

**Code patterns to copy exactly:**

```bash
cd src/CP/FrontEnd && npx vitest run src/test/HireSetupWizard.test.tsx src/__tests__/MyAgents.test.tsx src/__tests__/AuthenticatedPortal.test.tsx
cd /workspaces/WAOOAW && docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/unit/test_hired_agent_studio_api.py -v
cd /workspaces/WAOOAW && docker compose -f docker-compose.test.yml run cp-test pytest src/CP/BackEnd/tests/test_cp_hired_agent_studio.py -v
cd src/CP/FrontEnd && npm run build
```

**Acceptance criteria:**
1. Payment-confirmed hire flow and portal entry both land the customer in the wizard model, not in a legacy long-form operations page.
2. All tests authored in E1 and E2 run successfully in the final regression pass.
3. CP frontend production build succeeds after the wizard refactor.
4. Tracking Table is updated to reflect completed stories before the iteration PR is opened.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S1-T1 | `src/CP/FrontEnd/src/__tests__/AuthenticatedPortal.test.tsx` | Portal entry with payment-confirmed context | My Agents opens into wizard-first flow |
| E3-S1-T2 | same | Portal entry with active hired agent | Edit-mode wizard copy appears |

**Test command:**
```bash
cd src/CP/FrontEnd && npx vitest run src/test/HireSetupWizard.test.tsx src/__tests__/MyAgents.test.tsx src/__tests__/AuthenticatedPortal.test.tsx
cd /workspaces/WAOOAW && docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/unit/test_hired_agent_studio_api.py -v
cd /workspaces/WAOOAW && docker compose -f docker-compose.test.yml run cp-test pytest src/CP/BackEnd/tests/test_cp_hired_agent_studio.py -v
cd src/CP/FrontEnd && npm run build
```

**Commit message:** `feat(cp-wiz-1): wire wizard entry points and validate regression`

**Done signal:** `"E3-S1 done. Entry points rewired, final tests passed, iteration PR ready."`