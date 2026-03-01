# CP-NAV-1 — Customer Portal Navigation & UX Structure

> **Template version**: 2.0

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `CP-NAV-1` |
| Feature area | Customer Portal — Navigation & UX Structure |
| Created | 2026-03-01 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CP/navigation-ux-analysis.md` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 3 |
| Total epics | 6 |
| Total stories | 8 |

---

## Design Decision Log

**6-menu sidebar (not 8):**

| # | Menu | What lives here |
|---|---|---|
| 1 | Command Centre | Pulse — active agent count, recent deliverables, live activity feed |
| 2 | Discover | Browse + hire new agents |
| 3 | My Agents | Cards for each hired agent → drill-in → Configure · Goals · Deliverables · Approvals |
| 4 | Inbox | Cross-agent messages only (not approval actions) |
| 5 | Billing | Subscriptions + payment history + invoices |
| 6 | Profile | Edit profile · Notifications · Help · Sign out |

**Key structural decisions:**
- Goals, Deliverables, Approvals are **agent-scoped** — they live in the agent detail panel, not the sidebar. Every goal/deliverable/approval belongs to one hired agent.
- Inbox is **pure communications** — cross-agent messages only. Approvals are contextual actions on a specific agent.
- The agent detail panel is the primary workspace: `Overview | Goals | Deliverables | Approvals | Configure`
- This replaces the old 10-menu layout: `dashboard → Command Centre`, `approvals/goals/performance → agent detail`, `mobile/notifications/help → Profile`

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
| 1 | Lane A — CP Web: 6-menu sidebar + CommandCentre live wiring + skeleton pages | E1, E2, E3 | 3 | ~2h | +2h from launch |
| 2 | Lane B→A — Profile BE proxy + CP Profile page + Mobile EditProfileScreen | E4, E5 | 3 | ~3h | +3.5h from launch |
| 3 | Lane A — My Agents: agent detail panel with tab navigation (skeleton) | E6 | 2 | ~1.5h | +2h from launch |

**Estimate basis:** FE wiring = 30 min | New BE endpoint = 45 min | Full-stack = 90 min | Docker test = 15 min | PR = 10 min. Add 20% buffer for zero-cost model context loading.

---

## How to Launch Each Iteration

### Iteration 1

**Pre-flight check (run in terminal before launching):**
```bash
git status && git log --oneline -3
# Must show: clean tree on main.
```

**Steps to launch:**
1. Open VS Code
2. Open Copilot Chat: `Ctrl+Alt+I` (Windows/Linux) or `Cmd+Alt+I` (Mac)
3. Click the model dropdown → select **Agent mode** → select **Gemini 2.0 Flash** (free, 1M context — best for this plan)
4. Click `+` to start a new agent session
5. Type `@` → select **platform-engineer**
6. Paste the block below → press **Enter**
7. Come back in ~2 hours

**Iteration 1 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React 18 / TypeScript / Vite / Fluent UI engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior React/TypeScript engineer, I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-NAV-1-navigation-structure.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2, E3. Do not touch Iteration 2 or 3.
TIME BUDGET: 2h. If you reach 2.5h without finishing, follow STUCK PROTOCOL now.

EXECUTION ORDER:
1. Run: git status && git log --oneline -3
   You must be on main with a clean tree. If not, post why and HALT.
2. Read the "Agent Execution Rules" section in this plan file.
3. Read the "Iteration 1" section in this plan file.
4. Read nothing else before starting.
5. Execute in order: E1 → E2 → E3
6. When all epics are docker-tested, open the iteration PR. Post the PR URL. HALT.
```

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Verify merge first:**
```bash
git fetch origin && git log --oneline origin/main | head -3
# Must show: feat(CP-NAV-1): iteration 1 — sidebar + command centre + skeletons
```

**Model:** Copilot Chat → Agent mode → **Gemini 2.0 Flash**

**Iteration 2 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI engineer + Senior React 18 / TypeScript engineer + Senior React Native / Expo / TypeScript engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-NAV-1-navigation-structure.md
YOUR SCOPE: Iteration 2 only — Epics E4, E5. Do not touch Iteration 3.
TIME BUDGET: 3h.

PREREQUISITE CHECK (do before anything else):
  Run: git log --oneline origin/main | head -5
  Must show: feat(CP-NAV-1): iteration 1 — sidebar + command centre + skeletons
  If not: post "Blocked: Iteration 1 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 2" sections. Read nothing else.
3. Execute in order: E4-S1 (backend) → E4-S2 (CP FE) → E5-S1 (mobile)
4. When all epics are docker-tested, open the iteration PR. Post URL. HALT.
```

---

### Iteration 3

> ⚠️ Do NOT launch until Iteration 2 PR is merged to `main`.

**Verify merge:** `git log --oneline origin/main | head -3` → must show Iteration 2 merge commit.

**Model:** Copilot Chat → Agent mode → **Gemini 2.0 Flash**

**Iteration 3 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React 18 / TypeScript / Fluent UI engineer + Senior React Native / Expo / TypeScript engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-NAV-1-navigation-structure.md
YOUR SCOPE: Iteration 3 only — Epics E6. Do not touch other content.
TIME BUDGET: 1.5h.

PREREQUISITE CHECK:
  Run: git log --oneline origin/main | head -5
  Must show: feat(CP-NAV-1): iteration 2 — profile proxy + edit profile
  If not: post "Blocked: Iteration 2 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 3" sections. Read nothing else.
3. Execute in order: E6-S1 (CP Web) → E6-S2 (mobile)
4. Open iteration PR when done. Post URL. HALT.
```

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all instructions.

### Rule -1 — Activate Expert Personas (first thing, before Rule 0)

Read the `EXPERT PERSONAS:` field from the task you were given.
Activate each persona now. For every epic you execute, open with one line:

> *"Acting as a [persona], I will [what you're building] by [approach]."*

Relevant persona table:

| Technology area | Expert persona to activate |
|---|---|
| `src/CP/BackEnd/` | Senior Python 3.11 / FastAPI / SQLAlchemy engineer |
| `src/CP/FrontEnd/` | Senior React 18 / TypeScript / Vite / Fluent UI engineer |
| `src/mobile/` | Senior React Native / Expo / TypeScript engineer |
| `infrastructure/` | Senior Terraform / GCP Cloud Run engineer |

---

### Rule 0 — Open tracking draft PR first

```bash
git checkout main && git pull
git checkout -b feat/CP-NAV-1-it1-e1
git commit --allow-empty -m "chore(CP-NAV-1): start iteration 1"
git push origin feat/CP-NAV-1-it1-e1
gh pr create \
  --base main \
  --head feat/CP-NAV-1-it1-e1 \
  --draft \
  --title "tracking: CP-NAV-1 Iteration 1 — in progress" \
  --body "## tracking: CP-NAV-1 Iteration 1

Subscribe to this PR for story-by-story progress.

### Stories
- [ ] [E1-S1] AuthenticatedPortal.tsx: 6-menu sidebar restructure
- [ ] [E2-S1] CommandCentre.tsx: live agent data wiring
- [ ] [E3-S1] Skeleton pages: Discover, Inbox, Billing, Profile stubs

_Live updates posted as comments below ↓_"
```

### Rule 1 — Branch discipline
One epic = one branch: `feat/CP-NAV-1-itN-eN`.
All stories in one epic commit to the same branch sequentially.
Never push to `main` directly.

### Rule 2 — Scope lock
Implement exactly the acceptance criteria in the story card.
Do not fix unrelated code. Do not refactor. Do not gold-plate.
If you notice a bug outside scope: add a `// TODO(CP-NAV-1): <description>` comment and move on.

### Rule 3 — Tests before the next story
Write every test in the story's test table before advancing.
Run the exact test command listed in the story card.

### Rule 4 — Commit + push + notify after every story

```bash
git add -A
git commit -m "feat(CP-NAV-1): [story summary]"
git push origin HEAD
gh pr comment <tracking-pr-number> --body "✅ [E1-S1] done — [one line summary]"
```

### Rule 5 — Never edit files outside your story card's scope

### Rule 6 — When blocked: STUCK PROTOCOL

If blocked for more than 15 minutes on a single issue:
1. Commit current state with prefix `WIP:`
2. Push branch
3. Open a draft PR titled `WIP: CP-NAV-1 — stuck on [issue]`
4. Post a comment: "Stuck: [exact error / file / line]. Attempted: [what you tried]. Need: [what you need]."
5. HALT. Do not continue guessing.

### Rule 7 — Final iteration PR

When all epics in your iteration are complete and docker-tested:
```bash
gh pr create \
  --base main \
  --title "feat(CP-NAV-1): iteration N — [summary]" \
  --body "Closes stories: [list story IDs]

## What changed
[bullet list]

## Test evidence
[paste test output]"
```
Post the PR URL in Copilot Chat. HALT.

---

## Iteration 1 — CP Web Sidebar, Command Centre & Skeleton Pages

**Lane A — no new backend required. Plant data already exists at `/api/cp/my-agents/summary`.**

### Epic E1 — Customer sees the correct 6-menu sidebar when they log in

**Branch:** `feat/CP-NAV-1-it1-e1`
**Estimated time:** 30 min

---

#### E1-S1: Restructure AuthenticatedPortal.tsx to 6-menu navigation

**Branch:** `feat/CP-NAV-1-it1-e1`
**BLOCKED UNTIL:** none
**Pattern:** CP FrontEnd only — no backend change

**Context (2 sentences):**
`AuthenticatedPortal.tsx` is the top-level authenticated layout at `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx`. It currently has a 10-item sidebar with wrong page names (`dashboard`, `approvals`, `performance`, `mobile`, `notifications`, `help`) that do not match the target 6-menu structure. This story rewrites only the `Page` type, `menuItems` array, and `renderPage()` switch — no styling changes, no logic changes.

**Files to read first (max 3):**
1. `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx` — full file (147 lines)
2. `src/CP/FrontEnd/src/pages/authenticated/Dashboard.tsx` — to understand the import name to replace (98 lines)

**What to build:**

Replace the `Page` type, `menuItems` array, and `renderPage()` body in `AuthenticatedPortal.tsx`.

New `Page` type:
```typescript
type Page = 'command-centre' | 'discover' | 'my-agents' | 'inbox' | 'billing' | 'profile'
```

New `menuItems` array:
```typescript
const menuItems = [
  { id: 'command-centre' as Page, icon: <Home20Regular />, label: 'Command Centre' },
  { id: 'discover'       as Page, icon: <Search20Regular />, label: 'Discover' },
  { id: 'my-agents'      as Page, icon: <Bot20Regular />, label: 'My Agents' },
  { id: 'inbox'          as Page, icon: <Mail20Regular />, label: 'Inbox' },
  { id: 'billing'        as Page, icon: <Payment20Regular />, label: 'Billing' },
  { id: 'profile'        as Page, icon: <Person20Regular />, label: 'Profile' },
]
```

Add missing Fluent UI icon imports at the top of the file:
```typescript
import {
  Home20Regular,
  Search20Regular,
  Bot20Regular,
  Mail20Regular,
  Payment20Regular,
  Person20Regular,
  WeatherMoon20Regular,
  WeatherSunny20Regular,
  SignOut20Regular,
} from '@fluentui/react-icons'
```

New `renderPage()` — import and use the new components (to be created in E2 and E3). Use lazy inline stubs for pages not yet built:
```typescript
const renderPage = () => {
  switch (currentPage) {
    case 'command-centre': return <CommandCentre />
    case 'my-agents':      return <MyAgents />
    case 'discover':       return <PlaceholderPage title="Discover" icon="🔍" description="Browse and hire new agents" />
    case 'inbox':          return <PlaceholderPage title="Inbox" icon="📬" description="Cross-agent messages and updates" />
    case 'billing':        return <UsageBilling />
    case 'profile':        return <PlaceholderPage title="Profile" icon="👤" description="Profile and settings — coming in Iteration 2" />
    default:               return <CommandCentre />
  }
}
```

Add the `PlaceholderPage` component in the same file (above the default export), so pages not yet built render a clean empty state:
```typescript
function PlaceholderPage({ title, icon, description }: { title: string; icon: string; description: string }) {
  return (
    <div style={{ padding: '2rem', textAlign: 'center', opacity: 0.7 }}>
      <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>{icon}</div>
      <h2>{title}</h2>
      <p style={{ color: 'var(--colorNeutralForeground3)' }}>{description}</p>
    </div>
  )
}
```

Update imports — remove `Dashboard`, `Approvals`, `GoalsSetup`, `Performance`. Add `CommandCentre` (from E2), keep `MyAgents` and `UsageBilling`:
```typescript
import CommandCentre from './authenticated/CommandCentre'
import MyAgents from './authenticated/MyAgents'
import UsageBilling from './authenticated/UsageBilling'
```

Remove the header `<nav>` links that refer to old page names — keep only the sidebar for navigation. Remove `pendingApprovalsCount` (no longer a top-level badge).

**Acceptance criteria:**
- [ ] `Page` type has exactly 6 values: `command-centre | discover | my-agents | inbox | billing | profile`
- [ ] Sidebar renders exactly 6 items — no `approvals`, `goals`, `performance`, `mobile`, `notifications`, `help`
- [ ] Default page on login is `command-centre`
- [ ] `PlaceholderPage` renders for `discover`, `inbox`, `profile`
- [ ] `UsageBilling` renders for `billing`
- [ ] No TypeScript compile errors: `cd src/CP/FrontEnd && npm run build` exits 0

**Test command:**
```bash
cd src/CP/FrontEnd && npm run build 2>&1 | tail -5
# Expected: no errors, output contains "built in"
```

---

### Epic E2 — Customer sees live agent data on Command Centre (not hardcoded mocks)

**Branch:** `feat/CP-NAV-1-it1-e2`  
**Estimated time:** 45 min

---

#### E2-S1: Create CommandCentre.tsx with live agent summary data

**Branch:** `feat/CP-NAV-1-it1-e2`
**BLOCKED UNTIL:** E1-S1 merged (imports CommandCentre in AuthenticatedPortal)
**Pattern:** CP FrontEnd only — Lane A (existing `/api/cp/my-agents/summary` endpoint)

**Context (2 sentences):**
`Dashboard.tsx` at `src/CP/FrontEnd/src/pages/authenticated/Dashboard.tsx` is 98 lines of entirely hardcoded static arrays — no API calls, no `useState`, no `useEffect`. This story creates `CommandCentre.tsx` in the same directory, replacing Dashboard with a live-data version that calls the existing service at `src/CP/FrontEnd/src/services/myAgentsSummary.service.ts`.

**Files to read first (max 3):**
1. `src/CP/FrontEnd/src/pages/authenticated/Dashboard.tsx` — current hardcoded structure to replace
2. `src/CP/FrontEnd/src/services/myAgentsSummary.service.ts` — existing service to call

**What to build:**

Create `src/CP/FrontEnd/src/pages/authenticated/CommandCentre.tsx` (do NOT modify Dashboard.tsx — keep it for reference until PR merges):

```typescript
import { useState, useEffect } from 'react'
import { Card } from '@fluentui/react-components'
import { getMyAgentsSummary, type MyAgentInstanceSummary } from '../../services/myAgentsSummary.service'

export default function CommandCentre() {
  const [instances, setInstances] = useState<MyAgentInstanceSummary[]>([])
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState<string | null>(null)

  useEffect(() => {
    getMyAgentsSummary()
      .then(data => setInstances(data.instances))
      .catch(() => setError('Could not load agent data'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="dashboard-page">
      <h1>Command Centre</h1>
      <div style={{ padding: '2rem', opacity: 0.5 }}>Loading agent data…</div>
    </div>
  )

  if (error) return (
    <div className="dashboard-page">
      <h1>Command Centre</h1>
      <div style={{ padding: '1rem', color: 'var(--colorPaletteRedForeground1)', background: 'var(--colorPaletteRedBackground1)', borderRadius: '8px' }}>
        {error}
      </div>
    </div>
  )

  const activeAgents  = instances.filter(i => i.status === 'active').length
  const trialAgents   = instances.filter(i => i.trial_status === 'active').length
  const totalAgents   = instances.length

  return (
    <div className="dashboard-page">
      <h1>Command Centre</h1>

      {/* Live stats */}
      <div className="dashboard-stats">
        <Card className="stat-card">
          <div className="stat-icon">🤖</div>
          <div className="stat-label">{totalAgents} Agents</div>
          <div className="stat-sublabel">Total hired</div>
        </Card>
        <Card className="stat-card">
          <div className="stat-icon">✅</div>
          <div className="stat-label">{activeAgents} Active</div>
          <div className="stat-sublabel">Running now</div>
        </Card>
        <Card className="stat-card">
          <div className="stat-icon">🧪</div>
          <div className="stat-label">{trialAgents} On Trial</div>
          <div className="stat-sublabel">7-day free trial</div>
        </Card>
      </div>

      {/* Agent cards */}
      {totalAgents === 0 ? (
        <div style={{ padding: '2rem', textAlign: 'center', opacity: 0.6 }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🤖</div>
          <h3>No agents yet</h3>
          <p>Go to Discover to hire your first agent.</p>
        </div>
      ) : (
        <section className="activity-section">
          <h2>Your Agents</h2>
          <div className="activity-feed">
            {instances.map(instance => (
              <Card key={instance.subscription_id} className="activity-card">
                <div className="activity-agent">{instance.nickname ?? instance.agent_id}</div>
                <div className="activity-meta">
                  Status: {instance.status}
                  {instance.trial_status === 'active' && ' · 🧪 Trial active'}
                </div>
              </Card>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
```

**Acceptance criteria:**
- [ ] `CommandCentre.tsx` exists at `src/CP/FrontEnd/src/pages/authenticated/CommandCentre.tsx`
- [ ] File uses `useState` + `useEffect` — no hardcoded arrays
- [ ] Loading state renders when data is in flight
- [ ] Error state renders when fetch fails
- [ ] Empty state renders when `instances.length === 0`
- [ ] TypeScript build passes: `cd src/CP/FrontEnd && npm run build` exits 0
- [ ] *(Do NOT delete Dashboard.tsx — leave it until PR review)*

**Test command:**
```bash
cd src/CP/FrontEnd && npm run build 2>&1 | tail -5
```

---

### Epic E3 — Every sidebar menu renders a page (no blank screens)

**Branch:** `feat/CP-NAV-1-it1-e3`  
**Estimated time:** 15 min (PlaceholderPage already built in E1-S1 — this is just a smoke test + build verification)

---

#### E3-S1: Verify all 6 sidebar routes render without crash

**Branch:** `feat/CP-NAV-1-it1-e3` (can commit to same branch as E2 — one commit suffices)
**BLOCKED UNTIL:** E1-S1, E2-S1
**Pattern:** CP FrontEnd only — verification story

**Context (2 sentences):**
After E1-S1 and E2-S1, the 6 menus are wired. This story confirms the full build still passes and that each `Page` value maps to a non-null render in `renderPage()` with no `undefined` returns.

**Files to read first (max 3):**
1. `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx` — verify renderPage switch is exhaustive

**What to build:**

No new files. Verify the `renderPage` switch has a case for every member of the `Page` type. TypeScript's exhaustive check will catch any gap at build time.

If any `Page` variant has no case (TypeScript error about unreachable default or missing case), add the corresponding `PlaceholderPage` entry.

**Acceptance criteria:**
- [ ] `cd src/CP/FrontEnd && npm run build` exits 0 with no warnings about unused imports
- [ ] No `Page` variant resolves to `undefined`

**Test command:**
```bash
cd src/CP/FrontEnd && npm run build 2>&1
# Expected: exit 0
```

---

## Iteration 2 — Profile: BE Proxy + CP Web Profile Page + Mobile EditProfileScreen

**Lane B (E4-S1 backend) then Lane A (E4-S2 FE, E5-S1 mobile).**

### Epic E4 — Customer can view and edit their profile

**Branch:** `feat/CP-NAV-1-it2-e4`
**Estimated time:** 45 min (BE) + 45 min (FE)

---

#### E4-S1: Create cp_profile.py — GET and PATCH /cp/profile proxy

**Branch:** `feat/CP-NAV-1-it2-e4`
**BLOCKED UNTIL:** none (Lane B — new file, no dependencies)
**Pattern:** CP BackEnd — pattern (b): new `api/cp_profile.py` file with `waooaw_router` + `PlantGatewayClient`

**Context (2 sentences):**
No `/cp/profile` endpoint exists in CP BackEnd — `grep` across `src/CP/BackEnd/api/*.py` returns zero matches for "profile". Plant BackEnd already has the customer data: `GET /api/v1/customers/lookup?email=` returns all profile fields, and `POST /api/v1/customers` upserts by email (supports partial updates merged server-side).

**Files to read first (max 3):**
1. `src/CP/BackEnd/api/my_agents_summary.py` — reference for `waooaw_router`, `get_current_user`, `PlantGatewayClient` usage pattern (lines 1–50)
2. `src/CP/BackEnd/services/plant_gateway_client.py` — client interface: constructor takes `base_url`, method is `request_json(method, path, headers, json_body, params)` (full file, ~100 lines)
3. `src/CP/BackEnd/main.py` — to know where to add the router import + `app.include_router` (lines 1–110)

**What to build:**

Create `src/CP/BackEnd/api/cp_profile.py`:

```python
"""Customer profile proxy — CP-NAV-1.

GET  /cp/profile       → Plant GET /api/v1/customers/lookup?email=
PATCH /cp/profile      → Plant POST /api/v1/customers (upsert by email)

Pattern (b): new api/cp_profile.py with waooaw_router + PlantGatewayClient.
Never places business logic in CP BackEnd — thin proxy only.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import Depends, HTTPException, Request
from core.routing import waooaw_router
from pydantic import BaseModel

from api.auth.dependencies import get_current_user
from models.user import User
from services.plant_gateway_client import PlantGatewayClient

router = waooaw_router(prefix="/cp/profile", tags=["cp-profile"])

logger = logging.getLogger(__name__)
# NOTE: PIIMaskingFilter is applied globally via app-level logging config.
# Do not log email, phone, full_name, business_name raw in this module.


def _plant_client() -> PlantGatewayClient:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base_url:
        raise RuntimeError("PLANT_GATEWAY_URL not configured")
    return PlantGatewayClient(base_url=base_url)


class ProfileResponse(BaseModel):
    customer_id: str
    email: str
    phone: Optional[str] = None
    full_name: Optional[str] = None
    business_name: Optional[str] = None
    business_industry: Optional[str] = None
    business_address: Optional[str] = None
    website: Optional[str] = None
    gst_number: Optional[str] = None
    preferred_contact_method: Optional[str] = None
    consent: bool = False


class ProfilePatchRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    business_name: Optional[str] = None
    business_industry: Optional[str] = None
    business_address: Optional[str] = None
    website: Optional[str] = None
    gst_number: Optional[str] = None
    preferred_contact_method: Optional[str] = None


@router.get("", response_model=ProfileResponse)
async def get_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    """Fetch current customer's profile from Plant."""
    client = _plant_client()
    auth = request.headers.get("Authorization", "")
    resp = await client.request_json(
        method="GET",
        path="/api/v1/customers/lookup",
        headers={"Authorization": auth},
        params={"email": current_user.email},
    )
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Profile not found")
    if resp.status_code != 200:
        logger.warning("cp_profile: Plant GET returned %s", resp.status_code)
        raise HTTPException(status_code=502, detail="Could not fetch profile")
    return ProfileResponse(**resp.json)


@router.patch("", response_model=ProfileResponse)
async def patch_profile(
    request: Request,
    body: ProfilePatchRequest,
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    """Partial-update current customer's profile via Plant upsert."""
    client = _plant_client()
    auth = request.headers.get("Authorization", "")

    # Build upsert payload — email is the identity key, merge only provided fields
    upsert_payload: dict = {"email": current_user.email}
    for field, value in body.model_dump(exclude_none=True).items():
        upsert_payload[field] = value

    resp = await client.request_json(
        method="POST",
        path="/api/v1/customers",
        headers={"Authorization": auth},
        json_body=upsert_payload,
    )
    if resp.status_code not in (200, 201):
        logger.warning("cp_profile: Plant POST returned %s", resp.status_code)
        raise HTTPException(status_code=502, detail="Could not update profile")

    data = resp.json
    # Plant upsert response has customer_id inside CustomerUpsertResponse shape
    return ProfileResponse(
        customer_id=data.get("customer_id", ""),
        email=data.get("email", current_user.email),
        phone=data.get("phone"),
        full_name=data.get("full_name"),
        business_name=data.get("business_name"),
        business_industry=data.get("business_industry"),
        business_address=data.get("business_address"),
        website=data.get("website"),
        gst_number=data.get("gst_number"),
        preferred_contact_method=data.get("preferred_contact_method"),
        consent=bool(data.get("consent", False)),
    )
```

Register in `src/CP/BackEnd/main.py` — add after `feature_flags_proxy_router` import and include_router lines:

```python
# In imports section (add after existing router imports):
from api.cp_profile import router as cp_profile_router

# In app.include_router section (add after feature_flags_proxy_router line):
app.include_router(cp_profile_router, prefix="/api")
```

**Acceptance criteria:**
- [ ] `src/CP/BackEnd/api/cp_profile.py` exists
- [ ] `GET /api/cp/profile` is registered in `main.py`
- [ ] `PATCH /api/cp/profile` is registered in `main.py`
- [ ] `waooaw_router` used (not bare `APIRouter`)
- [ ] `PlantGatewayClient` used for all Plant calls (circuit breaker inherited)
- [ ] No `email`, `full_name`, `phone` logged raw
- [ ] Test passes:

```bash
docker-compose -f docker-compose.test.yml run cp-test \
  pytest src/CP/BackEnd/tests/ -k "profile" -v 2>&1 | tail -20
```

**Tests to write** (in `src/CP/BackEnd/tests/test_cp_profile.py`):

```python
"""Tests for GET/PATCH /cp/profile — CP-NAV-1 E4-S1"""
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import pytest


def _mock_user():
    user = MagicMock()
    user.email = "test@example.com"
    return user


def _plant_response(status_code: int, payload: dict):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json = payload
    return resp


def test_get_profile_returns_200(test_client, mock_get_current_user):
    with patch("api.cp_profile._plant_client") as mock_factory:
        mock_client = AsyncMock()
        mock_factory.return_value = mock_client
        mock_client.request_json = AsyncMock(return_value=_plant_response(200, {
            "customer_id": "abc", "email": "test@example.com",
            "full_name": "Test User", "business_name": "Acme",
            "business_industry": None, "phone": None,
            "business_address": None, "website": None,
            "gst_number": None, "preferred_contact_method": None, "consent": True,
        }))
        resp = test_client.get("/api/cp/profile")
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Test User"


def test_get_profile_plant_404_returns_404(test_client, mock_get_current_user):
    with patch("api.cp_profile._plant_client") as mock_factory:
        mock_client = AsyncMock()
        mock_factory.return_value = mock_client
        mock_client.request_json = AsyncMock(return_value=_plant_response(404, {}))
        resp = test_client.get("/api/cp/profile")
        assert resp.status_code == 404


def test_patch_profile_returns_200(test_client, mock_get_current_user):
    with patch("api.cp_profile._plant_client") as mock_factory:
        mock_client = AsyncMock()
        mock_factory.return_value = mock_client
        mock_client.request_json = AsyncMock(return_value=_plant_response(200, {
            "customer_id": "abc", "email": "test@example.com",
            "full_name": "Updated Name", "business_name": "NewCo",
            "business_industry": None, "phone": None,
            "business_address": None, "website": None,
            "gst_number": None, "preferred_contact_method": None, "consent": True,
        }))
        resp = test_client.patch("/api/cp/profile", json={"full_name": "Updated Name"})
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Updated Name"
```

*(Note: `test_client` and `mock_get_current_user` fixtures are expected to exist in `tests/conftest.py`. If they don't, create minimal versions following the pattern in existing test files in that directory.)*

---

#### E4-S2: Create ProfilePage.tsx + profile.service.ts in CP FrontEnd

**Branch:** `feat/CP-NAV-1-it2-e4` (same branch, sequential after E4-S1)
**BLOCKED UNTIL:** E4-S1 merged to main
**Pattern:** CP FrontEnd only — Lane A (new proxy now exists)

**Context (2 sentences):**
The `profile` route in `AuthenticatedPortal.tsx` currently renders a `PlaceholderPage`. This story replaces it with a real `ProfilePage.tsx` that shows the customer's profile data from `GET /cp/profile` (built in E4-S1) and provides an Edit button that opens an edit form in place.

**Files to read first (max 3):**
1. `src/CP/FrontEnd/src/services/myAgentsSummary.service.ts` — canonical pattern for `gatewayRequestJson` service (read full ~35-line file)
2. `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx` — to replace `PlaceholderPage` for `profile` with `<ProfilePage />`

**What to build:**

Create `src/CP/FrontEnd/src/services/profile.service.ts`:

```typescript
import { gatewayRequestJson } from './gatewayApiClient'

export type ProfileData = {
  customer_id: string
  email: string
  phone?: string | null
  full_name?: string | null
  business_name?: string | null
  business_industry?: string | null
  business_address?: string | null
  website?: string | null
  gst_number?: string | null
  preferred_contact_method?: string | null
  consent: boolean
}

export type ProfilePatchRequest = Partial<Omit<ProfileData, 'customer_id' | 'email' | 'consent'>>

export async function getProfile(): Promise<ProfileData> {
  return gatewayRequestJson<ProfileData>('/cp/profile', { method: 'GET' })
}

export async function patchProfile(body: ProfilePatchRequest): Promise<ProfileData> {
  return gatewayRequestJson<ProfileData>('/cp/profile', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}
```

Create `src/CP/FrontEnd/src/pages/authenticated/ProfilePage.tsx`:

```typescript
import { useState, useEffect } from 'react'
import { Card, Button, Input, Field } from '@fluentui/react-components'
import { getProfile, patchProfile, type ProfileData } from '../../services/profile.service'

export default function ProfilePage() {
  const [profile, setProfile]   = useState<ProfileData | null>(null)
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState<string | null>(null)
  const [editing, setEditing]   = useState(false)
  const [saving, setSaving]     = useState(false)
  const [form, setForm]         = useState<Partial<ProfileData>>({})

  useEffect(() => {
    getProfile()
      .then(data => { setProfile(data); setForm(data) })
      .catch(() => setError('Could not load profile'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div style={{ padding: '2rem' }}>Loading profile…</div>
  if (error)   return <div style={{ padding: '1rem', color: 'var(--colorPaletteRedForeground1)' }}>{error}</div>
  if (!profile) return null

  const handleSave = async () => {
    setSaving(true)
    try {
      const updated = await patchProfile({
        full_name: form.full_name ?? undefined,
        phone: form.phone ?? undefined,
        business_name: form.business_name ?? undefined,
        business_industry: form.business_industry ?? undefined,
        business_address: form.business_address ?? undefined,
        website: form.website ?? undefined,
      })
      setProfile(updated)
      setEditing(false)
    } catch {
      setError('Could not save profile. Try again.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '600px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ margin: 0 }}>Profile</h1>
        {!editing && (
          <Button appearance="primary" onClick={() => setEditing(true)}>Edit Profile</Button>
        )}
      </div>

      <Card style={{ padding: '1.5rem' }}>
        {editing ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <Field label="Full Name">
              <Input value={form.full_name ?? ''} onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))} />
            </Field>
            <Field label="Phone">
              <Input value={form.phone ?? ''} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} />
            </Field>
            <Field label="Business Name">
              <Input value={form.business_name ?? ''} onChange={e => setForm(f => ({ ...f, business_name: e.target.value }))} />
            </Field>
            <Field label="Industry">
              <Input value={form.business_industry ?? ''} onChange={e => setForm(f => ({ ...f, business_industry: e.target.value }))} />
            </Field>
            <Field label="Website">
              <Input value={form.website ?? ''} onChange={e => setForm(f => ({ ...f, website: e.target.value }))} />
            </Field>
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
              <Button appearance="primary" onClick={handleSave} disabled={saving}>
                {saving ? 'Saving…' : 'Save Changes'}
              </Button>
              <Button onClick={() => { setEditing(false); setForm(profile) }}>Cancel</Button>
            </div>
            {error && <div style={{ color: 'var(--colorPaletteRedForeground1)' }}>{error}</div>}
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <ProfileRow label="Email" value={profile.email} />
            <ProfileRow label="Name" value={profile.full_name} />
            <ProfileRow label="Phone" value={profile.phone} />
            <ProfileRow label="Business" value={profile.business_name} />
            <ProfileRow label="Industry" value={profile.business_industry} />
            <ProfileRow label="Website" value={profile.website} />
          </div>
        )}
      </Card>
    </div>
  )
}

function ProfileRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <div style={{ display: 'flex', gap: '1rem' }}>
      <span style={{ width: '100px', color: 'var(--colorNeutralForeground3)', flexShrink: 0 }}>{label}</span>
      <span>{value ?? '—'}</span>
    </div>
  )
}
```

Update `AuthenticatedPortal.tsx` — replace `PlaceholderPage` for profile:
```typescript
// Add import:
import ProfilePage from './authenticated/ProfilePage'

// In renderPage(), replace:
case 'profile':        return <PlaceholderPage title="Profile" icon="👤" description="Profile and settings — coming in Iteration 2" />
// With:
case 'profile':        return <ProfilePage />
```

**Acceptance criteria:**
- [ ] `profile.service.ts` exists with `getProfile()` and `patchProfile()`
- [ ] `ProfilePage.tsx` renders loading / error / data states
- [ ] Edit form shows all editable fields; Save calls `patchProfile()`; Cancel reverts form
- [ ] Profile sidebar menu now renders `ProfilePage`, not `PlaceholderPage`
- [ ] `cd src/CP/FrontEnd && npm run build` exits 0

**Test command:**
```bash
cd src/CP/FrontEnd && npm run build 2>&1 | tail -5
```

---

### Epic E5 — Mobile customer can edit their profile from the Profile tab

**Branch:** `feat/CP-NAV-1-it2-e5`
**Estimated time:** 45 min

---

#### E5-S1: Create EditProfileScreen.tsx + register in ProfileNavigator

**Branch:** `feat/CP-NAV-1-it2-e5`
**BLOCKED UNTIL:** E4-S1 merged to main (needs `GET /cp/profile` and `PATCH /cp/profile`)
**Pattern:** Mobile only — React Native / Expo / TypeScript

**Context (2 sentences):**
`ProfileScreen.tsx` at `src/mobile/src/screens/profile/ProfileScreen.tsx` has all `action: () => {}` empty stubs. The `ProfileStackParamList` in `src/mobile/src/navigation/types.ts` already declares `EditProfile: undefined` (line 108) — the type is ready, but no screen exists and the `ProfileNavigator` in `MainNavigator.tsx` (line ~100) only registers the `Profile` screen.

**Files to read first (max 3):**
1. `src/mobile/src/screens/profile/ProfileScreen.tsx` — lines 1–60 (to find the `action: () => {}` stub for Edit Profile and import/navigation patterns)
2. `src/mobile/src/navigation/MainNavigator.tsx` — lines 100–120 (ProfileNavigator component to add EditProfile screen registration)

**What to build:**

**Step 1:** Create `src/mobile/src/screens/profile/EditProfileScreen.tsx`:

```typescript
import React, { useState, useEffect } from 'react'
import {
  View, Text, TextInput, TouchableOpacity, ScrollView,
  SafeAreaView, ActivityIndicator, StyleSheet,
} from 'react-native'
import { useNavigation } from '@react-navigation/native'
import type { ProfileStackScreenProps } from '../../navigation/types'
import { useTheme } from '../../hooks/useTheme'
import { useAuth } from '../../hooks/useAuth'

type EditProfileScreenProps = ProfileStackScreenProps<'EditProfile'>

// Inline API helpers — mirrors gatewayApiClient pattern used elsewhere in mobile
const API_BASE = process.env.EXPO_PUBLIC_API_URL ?? ''

async function fetchProfile(token: string) {
  const resp = await fetch(`${API_BASE}/api/cp/profile`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!resp.ok) throw new Error('Failed to load profile')
  return resp.json()
}

async function saveProfile(token: string, body: Record<string, string>) {
  const resp = await fetch(`${API_BASE}/api/cp/profile`, {
    method: 'PATCH',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!resp.ok) throw new Error('Failed to save profile')
  return resp.json()
}

export const EditProfileScreen: React.FC<EditProfileScreenProps> = () => {
  const navigation = useNavigation<EditProfileScreenProps['navigation']>()
  const { colors, spacing, typography } = useTheme()
  const { token } = useAuth()

  const [loading, setLoading]   = useState(true)
  const [saving, setSaving]     = useState(false)
  const [error, setError]       = useState<string | null>(null)
  const [form, setForm]         = useState({
    full_name: '',
    phone: '',
    business_name: '',
    business_industry: '',
    website: '',
  })

  useEffect(() => {
    if (!token) return
    fetchProfile(token)
      .then(data => setForm({
        full_name: data.full_name ?? '',
        phone: data.phone ?? '',
        business_name: data.business_name ?? '',
        business_industry: data.business_industry ?? '',
        website: data.website ?? '',
      }))
      .catch(() => setError('Could not load profile'))
      .finally(() => setLoading(false))
  }, [token])

  const handleSave = async () => {
    if (!token) return
    setSaving(true)
    setError(null)
    try {
      await saveProfile(token, form)
      navigation.goBack()
    } catch {
      setError('Could not save. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  const field = (label: string, key: keyof typeof form, placeholder?: string) => (
    <View style={[styles.fieldGroup, { marginBottom: spacing.lg }]}>
      <Text style={[styles.fieldLabel, { color: colors.textSecondary, marginBottom: spacing.xs, fontSize: 13, fontFamily: typography.fontFamily.bodyBold }]}>
        {label}
      </Text>
      <TextInput
        style={[styles.input, {
          backgroundColor: colors.card,
          color: colors.textPrimary,
          borderRadius: spacing.sm,
          padding: spacing.md,
          fontFamily: typography.fontFamily.body,
          fontSize: 16,
          borderWidth: 1,
          borderColor: colors.textSecondary + '30',
        }]}
        value={form[key]}
        onChangeText={text => setForm(f => ({ ...f, [key]: text }))}
        placeholder={placeholder ?? label}
        placeholderTextColor={colors.textSecondary}
      />
    </View>
  )

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: colors.black }]}>
      {/* Header */}
      <View style={[styles.header, { padding: spacing.lg, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }]}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={{ color: colors.neonCyan, fontSize: 16 }}>← Back</Text>
        </TouchableOpacity>
        <Text style={[styles.title, { color: colors.textPrimary, fontSize: 20, fontFamily: typography.fontFamily.display }]}>
          Edit Profile
        </Text>
        <TouchableOpacity onPress={handleSave} disabled={saving}>
          <Text style={{ color: saving ? colors.textSecondary : colors.neonCyan, fontSize: 16, fontFamily: typography.fontFamily.bodyBold }}>
            {saving ? 'Saving…' : 'Save'}
          </Text>
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <ActivityIndicator color={colors.neonCyan} />
        </View>
      ) : (
        <ScrollView style={{ flex: 1 }} contentContainerStyle={{ padding: spacing.lg }}>
          {error && (
            <View style={{ backgroundColor: colors.error + '20', borderRadius: spacing.sm, padding: spacing.md, marginBottom: spacing.lg }}>
              <Text style={{ color: colors.error }}>{error}</Text>
            </View>
          )}
          {field('Full Name', 'full_name')}
          {field('Phone', 'phone', '+91 ...')}
          {field('Business Name', 'business_name')}
          {field('Industry', 'business_industry', 'e.g. Healthcare, EdTech')}
          {field('Website', 'website', 'https://')}
        </ScrollView>
      )}
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  header: {},
  title: {},
  fieldGroup: {},
  fieldLabel: {},
  input: {},
})
```

**Step 2:** Register `EditProfileScreen` in `ProfileNavigator` inside `src/mobile/src/navigation/MainNavigator.tsx`.

Find the `ProfileNavigator` function (around line 100). It currently only has one screen:
```tsx
<ProfileStack.Screen name="Profile" component={ProfileScreen} />
```

Add the import and the new screen:
```tsx
// Add import at top of file (with other screen imports):
import { EditProfileScreen } from '../screens/profile/EditProfileScreen'

// In ProfileNavigator, add after the Profile screen:
<ProfileStack.Screen name="EditProfile" component={EditProfileScreen} />
```

**Step 3:** Wire the `Edit Profile` action in `ProfileScreen.tsx`.

Find the `menuSections` definition (around line 20–50 in ProfileScreen.tsx). The Account section item for Edit Profile currently has `action: () => {}`. Replace:
```tsx
// Replace:
action: () => {}
// With:
action: () => navigation.navigate('EditProfile')
```

Also ensure `useNavigation` is imported and called:
```tsx
import { useNavigation } from '@react-navigation/native'
import type { ProfileStackScreenProps } from '../../navigation/types'
// Inside component:
const navigation = useNavigation<ProfileStackScreenProps<'Profile'>['navigation']>()
```

**Acceptance criteria:**
- [ ] `EditProfileScreen.tsx` exists at `src/mobile/src/screens/profile/EditProfileScreen.tsx`
- [ ] `EditProfileScreen` is registered in `ProfileStack` in `MainNavigator.tsx`
- [ ] Tapping "Edit Profile" in `ProfileScreen` navigates to `EditProfileScreen` (not `() => {}`)
- [ ] `EditProfileScreen` shows loading → form → loading skeleton on save
- [ ] Back button returns to `ProfileScreen`
- [ ] TypeScript build: `cd src/mobile && npx tsc --noEmit 2>&1 | head -20` — zero errors on new files
- [ ] Existing mobile tests pass: `cd src/mobile && node_modules/.bin/jest --forceExit 2>&1 | tail -10`

**Test command:**
```bash
cd src/mobile && npx tsc --noEmit 2>&1 | head -20
cd src/mobile && node_modules/.bin/jest --forceExit 2>&1 | tail -10
```

---

## Iteration 3 — My Agents: Agent Detail Panel

**Lane A — no new backend required. Agent data already available from `/api/cp/my-agents/summary`.**

### Epic E6 — Customer can manage a specific agent by tapping its card

**Branch:** `feat/CP-NAV-1-it3-e6`
**Estimated time:** 45 min (CP Web) + 30 min (mobile)

---

#### E6-S1: AgentDetailPanel — CP Web in-page panel with tab navigation

**Branch:** `feat/CP-NAV-1-it3-e6`
**BLOCKED UNTIL:** none (Lane A, builds on Iteration 1 `CommandCentre.tsx`)
**Pattern:** CP FrontEnd only

**Context (3 sentences):**
`MyAgents.tsx` at `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` currently shows a list of agents. The UX vision defines a detail panel that slides in (or replaces content) when an agent card is clicked, showing tabs: `Overview | Goals | Deliverables | Approvals | Configure`. This story adds an in-page `AgentDetailPanel` component that renders when an agent is selected, with skeleton tab content — no backend wiring for Goals/Deliverables/Approvals (those are separate future iterations).

**Files to read first (max 3):**
1. `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` — current structure to understand agent card interaction
2. `src/CP/FrontEnd/src/services/myAgentsSummary.service.ts` — `MyAgentInstanceSummary` type for the detail panel

**What to build:**

Create `src/CP/FrontEnd/src/pages/authenticated/AgentDetailPanel.tsx`:

```typescript
import { useState } from 'react'
import { Card, Tab, TabList } from '@fluentui/react-components'
import type { MyAgentInstanceSummary } from '../../services/myAgentsSummary.service'

type AgentTab = 'overview' | 'goals' | 'deliverables' | 'approvals' | 'configure'

interface AgentDetailPanelProps {
  agent: MyAgentInstanceSummary
  onClose: () => void
}

export function AgentDetailPanel({ agent, onClose }: AgentDetailPanelProps) {
  const [activeTab, setActiveTab] = useState<AgentTab>('overview')

  const tabContent: Record<AgentTab, React.ReactNode> = {
    overview: (
      <div style={{ padding: '1.5rem' }}>
        <h3>{agent.nickname ?? agent.agent_id}</h3>
        <p><strong>Status:</strong> {agent.status}</p>
        <p><strong>Subscription:</strong> {agent.subscription_id}</p>
        {agent.trial_status === 'active' && (
          <p style={{ color: 'var(--colorPalettePurpleForeground1)' }}>
            🧪 Trial active — ends {agent.trial_end_at ? new Date(agent.trial_end_at).toLocaleDateString() : 'soon'}
          </p>
        )}
      </div>
    ),
    goals: (
      <div style={{ padding: '1.5rem', opacity: 0.6 }}>
        <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>🎯</div>
        <h4>Goals</h4>
        <p>Goal management coming soon.</p>
      </div>
    ),
    deliverables: (
      <div style={{ padding: '1.5rem', opacity: 0.6 }}>
        <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>📦</div>
        <h4>Deliverables</h4>
        <p>Deliverables tracking coming soon.</p>
      </div>
    ),
    approvals: (
      <div style={{ padding: '1.5rem', opacity: 0.6 }}>
        <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>✅</div>
        <h4>Approvals</h4>
        <p>Approval requests coming soon.</p>
      </div>
    ),
    configure: (
      <div style={{ padding: '1.5rem', opacity: 0.6 }}>
        <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>⚙️</div>
        <h4>Configure</h4>
        <p>Agent configuration coming soon.</p>
      </div>
    ),
  }

  return (
    <div style={{
      position: 'fixed', right: 0, top: 0, height: '100vh',
      width: '480px', background: 'var(--colorNeutralBackground2)',
      borderLeft: '1px solid var(--colorNeutralStroke1)',
      boxShadow: '-4px 0 24px rgba(0,0,0,0.3)', zIndex: 100,
      display: 'flex', flexDirection: 'column',
    }}>
      {/* Header */}
      <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--colorNeutralStroke1)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.125rem' }}>{agent.nickname ?? agent.agent_id}</h2>
          <span style={{ fontSize: '0.875rem', color: 'var(--colorNeutralForeground3)' }}>{agent.status}</span>
        </div>
        <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.25rem', color: 'var(--colorNeutralForeground2)' }}>✕</button>
      </div>

      {/* Tabs */}
      <TabList
        selectedValue={activeTab}
        onTabSelect={(_, data) => setActiveTab(data.value as AgentTab)}
        style={{ padding: '0 1rem', borderBottom: '1px solid var(--colorNeutralStroke1)' }}
      >
        <Tab value="overview">Overview</Tab>
        <Tab value="goals">Goals</Tab>
        <Tab value="deliverables">Deliverables</Tab>
        <Tab value="approvals">Approvals</Tab>
        <Tab value="configure">Configure</Tab>
      </TabList>

      {/* Tab content */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {tabContent[activeTab]}
      </div>
    </div>
  )
}
```

Update `MyAgents.tsx` — add import and wire click-to-open:

Find the agent card in `MyAgents.tsx`. Add:
```typescript
// Add import:
import { AgentDetailPanel } from './AgentDetailPanel'
import type { MyAgentInstanceSummary } from '../../services/myAgentsSummary.service'

// Add state near top of component:
const [selectedAgent, setSelectedAgent] = useState<MyAgentInstanceSummary | null>(null)

// Wrap agent card with onClick:
onClick={() => setSelectedAgent(instance)}

// Render panel (at bottom of return JSX, before closing div):
{selectedAgent && (
  <AgentDetailPanel agent={selectedAgent} onClose={() => setSelectedAgent(null)} />
)}
```

**Acceptance criteria:**
- [ ] `AgentDetailPanel.tsx` exists
- [ ] Clicking an agent card in `MyAgents.tsx` opens the panel
- [ ] Panel shows 5 tabs: Overview, Goals, Deliverables, Approvals, Configure
- [ ] Close button dismisses the panel
- [ ] Goals/Deliverables/Approvals/Configure tabs show skeleton "coming soon" state
- [ ] `cd src/CP/FrontEnd && npm run build` exits 0

**Test command:**
```bash
cd src/CP/FrontEnd && npm run build 2>&1 | tail -5
```

---

#### E6-S2: Mobile — Agent card tap shows context bottom sheet with tabs

**Branch:** `feat/CP-NAV-1-it3-e6` (same branch, sequential after E6-S1)
**BLOCKED UNTIL:** none (Lane A — uses existing `MyAgentsScreen` data)
**Pattern:** Mobile only — React Native / Expo

**Context (2 sentences):**
`MyAgentsScreen.tsx` at `src/mobile/src/screens/agents/MyAgentsScreen.tsx` shows hired agents but tapping a card has no action. This story adds a bottom sheet (using React Native `Modal`) that appears on agent card tap, showing tabs: Overview | Goals | Deliverables | Approvals | Configure — all skeleton content, same as the CP Web panel.

**Files to read first (max 3):**
1. `src/mobile/src/screens/agents/MyAgentsScreen.tsx` — lines 1–80 to understand agent card structure and what data is available per card

**What to build:**

Create `src/mobile/src/screens/agents/AgentContextSheet.tsx`:

```typescript
import React, { useState } from 'react'
import {
  View, Text, Modal, TouchableOpacity, ScrollView,
  StyleSheet, SafeAreaView,
} from 'react-native'
import { useTheme } from '../../hooks/useTheme'

type SheetTab = 'overview' | 'goals' | 'deliverables' | 'approvals' | 'configure'

interface AgentContextSheetProps {
  agent: { agent_id: string; nickname?: string | null; status: string; trial_status?: string | null }
  visible: boolean
  onClose: () => void
}

export const AgentContextSheet: React.FC<AgentContextSheetProps> = ({ agent, visible, onClose }) => {
  const { colors, spacing, typography } = useTheme()
  const [activeTab, setActiveTab] = useState<SheetTab>('overview')

  const tabs: { key: SheetTab; label: string }[] = [
    { key: 'overview',     label: 'Overview' },
    { key: 'goals',        label: 'Goals' },
    { key: 'deliverables', label: 'Deliverables' },
    { key: 'approvals',    label: 'Approvals' },
    { key: 'configure',    label: 'Configure' },
  ]

  const skeletonContent = (icon: string, title: string) => (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl }}>
      <Text style={{ fontSize: 40, marginBottom: spacing.md }}>{icon}</Text>
      <Text style={{ color: colors.textSecondary, fontFamily: typography.fontFamily.body }}>{title} coming soon</Text>
    </View>
  )

  const tabContent: Record<SheetTab, React.ReactNode> = {
    overview: (
      <View style={{ padding: spacing.lg }}>
        <Text style={[styles.agentName, { color: colors.textPrimary, fontFamily: typography.fontFamily.display, fontSize: 20, marginBottom: spacing.sm }]}>
          {agent.nickname ?? agent.agent_id}
        </Text>
        <Text style={{ color: colors.textSecondary }}>Status: {agent.status}</Text>
        {agent.trial_status === 'active' && (
          <Text style={{ color: colors.neonCyan, marginTop: spacing.xs }}>🧪 Trial active</Text>
        )}
      </View>
    ),
    goals:        skeletonContent('🎯', 'Goals'),
    deliverables: skeletonContent('📦', 'Deliverables'),
    approvals:    skeletonContent('✅', 'Approvals'),
    configure:    skeletonContent('⚙️', 'Configure'),
  }

  return (
    <Modal visible={visible} animationType="slide" transparent presentationStyle="overFullScreen" onRequestClose={onClose}>
      <TouchableOpacity style={[styles.backdrop, { backgroundColor: 'rgba(0,0,0,0.6)' }]} activeOpacity={1} onPress={onClose} />

      <View style={[styles.sheet, { backgroundColor: colors.card, borderTopLeftRadius: 20, borderTopRightRadius: 20 }]}>
        {/* Handle + header */}
        <View style={[styles.handle, { backgroundColor: colors.textSecondary + '40', alignSelf: 'center', width: 40, height: 4, borderRadius: 2, marginTop: spacing.md, marginBottom: spacing.md }]} />
        <View style={[styles.sheetHeader, { paddingHorizontal: spacing.lg, paddingBottom: spacing.md, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }]}>
          <Text style={{ color: colors.textPrimary, fontFamily: typography.fontFamily.display, fontSize: 18 }}>
            {agent.nickname ?? agent.agent_id}
          </Text>
          <TouchableOpacity onPress={onClose}>
            <Text style={{ color: colors.textSecondary, fontSize: 20 }}>✕</Text>
          </TouchableOpacity>
        </View>

        {/* Tab bar */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ maxHeight: 44 }} contentContainerStyle={{ paddingHorizontal: spacing.md }}>
          {tabs.map(tab => (
            <TouchableOpacity
              key={tab.key}
              onPress={() => setActiveTab(tab.key)}
              style={[styles.tab, {
                paddingHorizontal: spacing.md, paddingVertical: spacing.sm,
                borderBottomWidth: activeTab === tab.key ? 2 : 0,
                borderBottomColor: colors.neonCyan,
                marginRight: spacing.sm,
              }]}
            >
              <Text style={{
                color: activeTab === tab.key ? colors.neonCyan : colors.textSecondary,
                fontFamily: typography.fontFamily.bodyBold,
                fontSize: 14,
              }}>
                {tab.label}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Content */}
        <View style={{ flex: 1, borderTopWidth: 1, borderTopColor: colors.textSecondary + '20' }}>
          {tabContent[activeTab]}
        </View>
      </View>
    </Modal>
  )
}

const styles = StyleSheet.create({
  backdrop: { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 },
  sheet: { position: 'absolute', bottom: 0, left: 0, right: 0, height: '70%' },
  handle: {},
  sheetHeader: {},
  tab: {},
  agentName: {},
})
```

Update `MyAgentsScreen.tsx` — wire card tap:

```typescript
// Add import:
import { AgentContextSheet } from './AgentContextSheet'

// Add state inside component:
const [selectedAgent, setSelectedAgent] = useState<{agent_id: string; nickname?: string | null; status: string; trial_status?: string | null} | null>(null)

// On agent card TouchableOpacity, add:
onPress={() => setSelectedAgent({ agent_id: item.agent_id, nickname: item.nickname, status: item.status, trial_status: item.trial_status })}

// At bottom of return JSX:
<AgentContextSheet
  agent={selectedAgent ?? { agent_id: '', status: '' }}
  visible={selectedAgent !== null}
  onClose={() => setSelectedAgent(null)}
/>
```

**Acceptance criteria:**
- [ ] `AgentContextSheet.tsx` exists
- [ ] Tapping an agent card in `MyAgentsScreen` opens the bottom sheet
- [ ] Sheet shows 5 tabs: Overview, Goals, Deliverables, Approvals, Configure
- [ ] ✕ button and tapping backdrop both close the sheet
- [ ] TypeScript: `cd src/mobile && npx tsc --noEmit 2>&1 | head -10` — zero errors on new files
- [ ] Mobile tests still pass: `cd src/mobile && node_modules/.bin/jest --forceExit 2>&1 | tail -5`

**Test command:**
```bash
cd src/mobile && npx tsc --noEmit 2>&1 | head -10
cd src/mobile && node_modules/.bin/jest --forceExit 2>&1 | tail -5
```

---

## Dependency Map

```
E1-S1 (sidebar restructure)
    └── E2-S1 (CommandCentre.tsx) — E1 must be on same branch or merged
        └── E3-S1 (smoke test / build verification)

E4-S1 (cp_profile.py BE proxy — Lane B)
    ├── E4-S2 (ProfilePage.tsx — BLOCKED until E4-S1 merged)
    └── E5-S1 (EditProfileScreen mobile — BLOCKED until E4-S1 merged)

E6-S1 (AgentDetailPanel CP Web) — independent
E6-S2 (AgentContextSheet mobile) — independent
```

## Out of Scope (this plan)

- Goals backend logic (Plant-side goal management)
- Deliverables backend logic (Plant-side deliverable tracking)
- Inbox backend logic (communications/messaging system)
- Agent Configure backend wiring
- Discover search backend
- Notifications push infrastructure
- Billing backend changes
- Agent Context Sheet sub-screen actions (Approve / Reject deliverables)
