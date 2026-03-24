# CP-STUDIO-4 — Wizard Agent-Select Step + YouTube OAuth Connect

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `CP-STUDIO-4` |
| Feature area | Customer Portal — DMA Activation Wizard |
| Created | 2026-03-24 |
| Author | GitHub Copilot (PM mode) |
| Predecessor | `docs/CP/iterations/CP-STUDIO-3-dma-wizard-shell.md` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 1 |
| Total epics | 2 |
| Total stories | 6 |

---

## Zero-Cost Agent Constraints (READ FIRST)

This plan targets **autonomous zero-cost model agents** (Gemini Flash, GPT-4o-mini) with limited
context windows. Every story is fully self-contained — no cross-references, no "see above".

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is self-contained — no "see above" |
| Max 3 files per story | PM has pre-identified every file to read |
| Binary acceptance | Pass/fail criteria only, no judgment calls |
| Token cost per file read | NFR code patterns embedded inline in each card |

> **Agent:** Read ONE story card fully, then act. Do NOT read other stories. All patterns are in your card.

---

## Backend Pre-flight (verified by PM — no agent action required)

| Check | Status |
|---|---|
| CP backend: `cp_youtube_connections.py` routes `/connect/start`, `/connect/finalize`, `/{id}/attach` | ✅ All present |
| FE service: `youtubeConnections.service.ts` — `startYouTubeConnection`, `finalizeYouTubeConnection`, `listYouTubeConnections`, `attachYouTubeConnection` | ✅ All present |
| GCP Secret Manager: `YOUTUBE_CLIENT_ID` (created 2026-03-17) | ✅ Present |
| GCP Secret Manager: `YOUTUBE_CLIENT_SECRET` (created 2026-03-17) | ✅ Present |
| Plant backend reads `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` env vars | ✅ Confirmed |
| GCP SQL persistence via `HiredAgentRepository.update_config()` | ✅ Called on every wizard save |

**Conclusion: This plan is 100% frontend-only. Zero backend, proxy, or infrastructure changes required.**

---

## Problem Statement

After CP-STUDIO-3 implemented the 6-step DMA wizard, the deployed app shows two problems:

1. **Agent selection is outside the wizard.** The My Agents page renders an `AgentSelector` dropdown + 4 tab buttons (Configure / Goal Setting / Skills / Performance) above the wizard. For DMA agents the 4 tabs are not relevant — selection and these tabs should disappear and be replaced by a "Select Agent" step 0 inside the wizard itself.

2. **Connect Platforms step has no connect button.** Step 3 (Connect Platforms) currently renders the generic `PlatformConnectionsPanel` which shows an API key/secret form and a "YouTube not connected" warning — but no real OAuth connect button. A proper "Connect with Google" OAuth flow is required.

---

## Design Decisions (resolved by PM — no agent inference required)

### E1 — Agent Selection Step

- `DigitalMarketingActivationWizard.tsx` gains a new required prop `instances: MyAgentInstanceSummary[]`
- A new `Step 0` is prepended to `DMA_STEPS`: id `'select'`, title `'Select Agent'`, description `'Choose which hired agent to configure.'`
- DMA_STEPS becomes 7 entries. Existing indices shift by 1 (induct → 1, platforms → 2, etc.)
- Step 0 panel renders a card grid of hired DMA agents (name, status badge, billing info). Clicking a card calls `setSelectedInstance(instance)` and advances to step 1.
- If `instances.length === 1`, auto-select that instance + auto-advance on mount (skip right to step 1).
- `MyAgents.tsx`: when `selectedInstance` is a DMA agent, render the wizard full-width without the outer `Card.agent-detail-card` header row (AgentSelector + 4 tab buttons). The wizard becomes the entire content of the card. Pass `instances` filtered to DMA instances.

### E2 — YouTube OAuth Connect

- The wizard's Connect Platforms step (now step 3 after adding step 0) renders a per-platform section.
- For YouTube: a "Connect with Google" `<Button>` calls `startYouTubeConnection(redirectUri)` where `redirectUri = window.location.origin + window.location.pathname` (NO query string, so same image works in demo/uat/prod).
- Before redirecting, store `state` in `sessionStorage` key `yt_oauth_state`.
- On component mount, check `new URLSearchParams(window.location.search)` for `code` and `state`. If both present:
  1. Call `finalizeYouTubeConnection({ state, code, redirect_uri: window.location.origin + window.location.pathname })`
  2. Call `attachYouTubeConnection(credential_id, { hired_instance_id, skill_id: defaultSkillId })`
  3. Clear URL params: `window.history.replaceState({}, '', window.location.pathname)`
  4. Set local state to show "YouTube connected" badge
- For other platforms (not yet implemented): show a "coming soon" badge

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | E1: Step 0 agent select. E2: YouTube OAuth in Connect step. CSS + tests. | 2 | 6 | 6h | 6h from launch |

---

## How to Launch Iteration 1

**Pre-flight check (run in terminal):**
```bash
git fetch origin && git log --oneline origin/main | head -3
```

**Steps:**
1. Open VS Code → Copilot Chat (`Ctrl+Alt+I`)
2. Model dropdown → Agent mode
3. Click `+` → type `@` → select **platform-engineer**
4. Paste the block below → Enter
5. Come back in 6 hours

**Iteration 1 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React 18 / TypeScript / Fluent UI engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior React 18 / TypeScript / Fluent UI engineer, I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-STUDIO-4-wizard-agent-select-youtube-oauth.md
YOUR SCOPE: Iteration 1 only — Epic E1 (S1–S3) then Epic E2 (S4–S6). Do not touch anything outside src/CP/FrontEnd/.
TIME BUDGET: 6h. If you reach 7h without finishing, follow STUCK PROTOCOL.

EXECUTION ORDER:
1. Run: git fetch origin && git log --oneline origin/main | head -3
   You must be on main or branch from main with a clean tree. If not, post why and HALT.
2. Read "Agent Execution Rules" in this plan file.
3. Read "Iteration 1" in this plan file.
4. Read nothing else before starting.
5. Execute: S1 → S2 → S3 → S4 → S5 → S6
6. When all stories pass acceptance criteria, open the PR. Post the PR URL. HALT.
```

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all other instructions.

### Rule -1 — Activate Expert Persona

Activate: **Senior React 18 / TypeScript / Fluent UI engineer**

Begin every epic with:
> *"Acting as a Senior React 18 / TypeScript / Fluent UI engineer, I will [what] by [approach]."*

### Rule 0 — Branch

```bash
git checkout main && git pull origin main
git checkout -b feat/CP-STUDIO-4-wizard-agent-select-youtube-oauth
```

### Rule 1 — CHECKPOINT after every story

```bash
git add -A && git commit -m "feat(CP-STUDIO-4): [story-id] — [story title]" && git push -u origin feat/CP-STUDIO-4-wizard-agent-select-youtube-oauth
```

Do this BEFORE starting the next story.

### Rule 2 — STUCK PROTOCOL

If blocked > 20 min OR can't resolve a failure in 2 attempts:
1. `git add -A && git commit -m "WIP: CP-STUDIO-4 stuck at [story-id] — [reason]" && git push`
2. Open a **draft PR** titled `WIP: CP-STUDIO-4 — stuck at [story-id]`
3. Write: the exact file, the exact error, the two approaches tried
4. HALT

### Rule 3 — Build must pass

After S6:
```bash
cd src/CP/FrontEnd && npm run build 2>&1 | tail -20
```
Zero TypeScript errors. Zero Vite build errors. Fix any before committing S6.

### Rule 4 — Tests must pass

After S6:
```bash
cd src/CP/FrontEnd && npx vitest run src/test/MyAgentsDigitalMarketingWizard.test.tsx 2>&1 | tail -30
```
All tests green before opening PR.

### Rule 5 — Do NOT touch

- Any Python file
- Any `src/CP/BackEnd/` file
- Any `src/Plant/` file
- Any Terraform or infrastructure file
- Any file outside `src/CP/FrontEnd/`

### Rule 6 — CSS namespace

All new CSS classes use the `dma-wizard-` prefix. Define in `src/CP/FrontEnd/src/styles/globals.css`.

### Rule 7 — Image promotion (critical)

Never hardcode a domain, env URL, or port. Always derive `redirect_uri` from:
```typescript
const redirectUri = window.location.origin + window.location.pathname
```
This ensures the same Docker image works in demo → uat → prod without rebuild.

---

## Iteration 1 — E1: Agent Selection as Wizard Step 0

**Outcome**: Customer navigating to My Agents → sees the DMA wizard fullscreen without the dropdown/tabs header. Step 0 shows their hired DMA agents as clickable cards. Clicking one selects it and advances to Step 1 (Induct Agent). If only one agent is hired, it auto-selects and jumps straight to Step 1.

---

### E1-S1: MyAgents.tsx — DMA full-width render + pass instances to wizard

**Story size**: 60 min
**Branch**: `feat/CP-STUDIO-4-wizard-agent-select-youtube-oauth`
**BLOCKED UNTIL**: none — first story

#### Context

`src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` currently renders (starting around line 2077):
```
{instances.length > 0 ? (
  <Card className="agent-detail-card">
    <div style={{ display: 'flex', ... }}>
      <AgentSelector ...>          ← to remove for DMA layout
      <div> 4 tab buttons </div>   ← to remove for DMA layout
    </div>
    {selectedInstance ? (
      ...
      {activeSection === 'configure' && isDigitalMarketingAgent(...) && (
        <DigitalMarketingActivationWizard
          instance={selectedInstance}
          readOnly={...}
          onSaved={...}
        />
      )}
```

**Required change**: When ALL `instances` are DMA agents (or the only selected instance is a DMA agent), skip the header row (AgentSelector + 4 tab buttons) and render only the `DigitalMarketingActivationWizard` inside the card, full-width. Non-DMA flows remain unchanged.

The simplest safe logic: if every instance in `instances` is a DMA agent, replace the entire Card content with just the wizard.

New `allDma` flag (add near other `useMemo` calls, after line ~1913):
```typescript
const allDma = useMemo(
  () => instances.length > 0 && instances.every((x) => isDigitalMarketingAgent(x.agent_id, x.agent_type_id)),
  [instances]
)
```

When `allDma` is true, replace the `<Card className="agent-detail-card">` block with:
```tsx
<Card className="agent-detail-card dma-wizard-fullwidth-card">
  <DigitalMarketingActivationWizard
    instances={instances}
    instance={selectedInstance}
    readOnly={selectedReadOnlyExpired || selectedInReadOnlyRetention}
    onSaved={(updated) => {
      setInstances((prev) =>
        prev.map((x) =>
          x.subscription_id === (selectedInstance?.subscription_id ?? '')
            ? {
                ...x,
                nickname: updated.nickname ?? x.nickname,
                configured: updated.configured ?? x.configured,
                goals_completed: updated.goals_completed ?? x.goals_completed,
                hired_instance_id: updated.hired_instance_id ?? x.hired_instance_id,
                agent_type_id: updated.agent_type_id ?? x.agent_type_id,
                catalog_release_id: updated.catalog_release_id ?? x.catalog_release_id,
                internal_definition_version_id: updated.internal_definition_version_id ?? x.internal_definition_version_id,
                external_catalog_version: updated.external_catalog_version ?? x.external_catalog_version,
                catalog_status_at_hire: updated.catalog_status_at_hire ?? x.catalog_status_at_hire
              }
            : x
        )
      )
    }}
    onSelectedInstanceChange={(sub_id) => setSelectedSubscriptionId(sub_id)}
  />
</Card>
```

When `allDma` is false, render the existing Card with AgentSelector + tabs (no change to that branch).

#### Files to read first (max 3)
1. `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` — lines 1830–1920 (state variables + allDma insertion point) and lines 2075–2260 (the Card/AgentSelector/tabs + wizard render block)

#### Acceptance criteria
- [ ] When all hired instances are DMA agents, the AgentSelector dropdown and 4 tab buttons do NOT render
- [ ] `DigitalMarketingActivationWizard` receives `instances` prop (array of all DMA instances)
- [ ] `DigitalMarketingActivationWizard` receives `onSelectedInstanceChange` prop
- [ ] When not all instances are DMA agents, original layout (dropdown + tabs) renders unchanged
- [ ] `npm run build` exits 0 (TypeScript may warn about unknown `instances` prop on the wizard until S2 adds it — that's expected; a `// @ts-expect-error` comment is acceptable as a temporary shim)

---

### E1-S2: DigitalMarketingActivationWizard.tsx — Add instances prop + Step 0 Select Agent panel

**Story size**: 60 min
**Branch**: `feat/CP-STUDIO-4-wizard-agent-select-youtube-oauth`
**BLOCKED UNTIL**: E1-S1 committed

#### Context

`src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` currently has:

```typescript
// Line 25 — current DMA_STEPS (6 entries)
const DMA_STEPS = [
  { id: 'induct',    title: 'Induct Agent',      description: 'Set the agent nickname and brand identity.' },
  { id: 'platforms', title: 'Choose Platforms',  description: 'Select which social channels this agent will manage.' },
  { id: 'connect',   title: 'Connect Platforms', description: 'Authorise each selected platform channel.' },
  { id: 'theme',     title: 'Build Master Theme',description: 'Define brand brief and generate an AI content strategy.' },
  { id: 'schedule',  title: 'Confirm Schedule',  description: 'Set posting frequency and preferred days.' },
  { id: 'activate',  title: 'Review & Activate', description: 'Check readiness then activate the agent.' },
] as const

// Line 43 — current props interface
type DigitalMarketingActivationWizardProps = {
  instance?: MyAgentInstanceSummary | null
  selectedInstance?: MyAgentInstanceSummary | null
  readOnly: boolean
  onSaved?: (updated: HiredAgentInstance) => void
  onSavedInstance?: (patch: { ... }) => void
}
```

State variable `activeStepIndex` already exists (line ~112). Import for `MyAgentInstanceSummary` already exists (line 9).

#### What to build

**A. Prepend Step 0 to DMA_STEPS** (replacing the existing `const DMA_STEPS` definition):
```typescript
const DMA_STEPS = [
  { id: 'select',    title: 'Select Agent',      description: 'Choose which hired agent to configure.' },
  { id: 'induct',    title: 'Induct Agent',       description: 'Set the agent nickname and brand identity.' },
  { id: 'platforms', title: 'Choose Platforms',   description: 'Select which social channels this agent will manage.' },
  { id: 'connect',   title: 'Connect Platforms',  description: 'Authorise each selected platform channel.' },
  { id: 'theme',     title: 'Build Master Theme', description: 'Define brand brief and generate an AI content strategy.' },
  { id: 'schedule',  title: 'Confirm Schedule',   description: 'Set posting frequency and preferred days.' },
  { id: 'activate',  title: 'Review & Activate',  description: 'Check readiness then activate the agent.' },
] as const
```

**B. Add new props to the interface**:
```typescript
type DigitalMarketingActivationWizardProps = {
  instances?: MyAgentInstanceSummary[]          // all DMA instances to show in Step 0
  instance?: MyAgentInstanceSummary | null
  selectedInstance?: MyAgentInstanceSummary | null
  readOnly: boolean
  onSaved?: (updated: HiredAgentInstance) => void
  onSavedInstance?: (patch: {
    nickname?: string | null
    configured?: boolean
    goals_completed?: boolean
    hired_instance_id?: string | null
    agent_type_id?: string | null
  }) => void
  onSelectedInstanceChange?: (subscriptionId: string) => void  // called when Step 0 picks an agent
}
```

**C. Destructure new props** in the function signature:
```typescript
function DigitalMarketingActivationWizard({
  instances = [],
  instance,
  selectedInstance,
  readOnly,
  onSaved,
  onSavedInstance,
  onSelectedInstanceChange,
}: DigitalMarketingActivationWizardProps) {
```

**D. Auto-advance logic** — add a `useEffect` after existing state declarations:
```typescript
// Auto-select + advance if only one instance and we are on step 0
useEffect(() => {
  if (activeStepIndex === 0 && instances.length === 1) {
    onSelectedInstanceChange?.(instances[0].subscription_id)
    setActiveStepIndex(1)
  }
}, [instances, activeStepIndex, onSelectedInstanceChange])
```

**E. Step 0 panel content** — find the section in the render where step panels are rendered (look for `data-testid="dma-step-panel-induct"` or similar pattern from CP-STUDIO-3 S1). Add a new panel for `'select'` before the `'induct'` panel:

```tsx
{currentStep.id === 'select' && (
  <div data-testid="dma-step-panel-select" className="dma-wizard-canvas-body-inner">
    {instances.length === 0 ? (
      <div>No agents found.</div>
    ) : (
      <div className="dma-wizard-agent-select-grid">
        {instances.map((inst) => (
          <button
            key={inst.subscription_id}
            type="button"
            className={`dma-wizard-agent-card${inst.subscription_id === instance?.subscription_id ? ' is-selected' : ''}`}
            onClick={() => {
              onSelectedInstanceChange?.(inst.subscription_id)
              setActiveStepIndex(1)
            }}
          >
            <div className="dma-wizard-agent-card-name">
              {inst.nickname || inst.agent_id}
            </div>
            <div className="dma-wizard-agent-card-meta">
              {inst.status}
            </div>
          </button>
        ))}
      </div>
    )}
  </div>
)}
```

**F. Back button** — the Back button should call `setActiveStepIndex(i => Math.max(0, i - 1))`. On step 0 (index 0), Back is disabled. This logic should already work correctly since `activeStepIndex === 0` will disable Back — but confirm by reading the existing Back button code before editing.

#### Files to read first (max 3)
1. `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` — lines 1–60 (imports + DMA_STEPS + props interface)
2. `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` — lines 100–135 (state declarations, where to add useEffect)
3. `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` — the step panel rendering section (search for `dma-step-panel` or `currentStep.id ===`)

#### Acceptance criteria
- [ ] `DMA_STEPS` has 7 entries (select + existing 6)
- [ ] `instances` and `onSelectedInstanceChange` are valid TypeScript props (no ts-expect-error needed)
- [ ] Step 0 renders agent cards for each instance in `instances`
- [ ] Clicking an agent card calls `onSelectedInstanceChange` and advances to step 1
- [ ] When `instances.length === 1`, component auto-advances on mount
- [ ] Back button disabled when `activeStepIndex === 0`
- [ ] `npm run build` exits 0

---

### E1-S3: CSS — Agent select grid + agent card styles

**Story size**: 30 min
**Branch**: `feat/CP-STUDIO-4-wizard-agent-select-youtube-oauth`
**BLOCKED UNTIL**: E1-S2 committed

#### Context

`src/CP/FrontEnd/src/styles/globals.css` already contains `dma-wizard-*` classes (added by CP-STUDIO-3). This story adds the new classes for the agent-select grid and agent cards introduced in S2, plus the full-width card override for MyAgents.

#### What to build

Append to the end of `src/CP/FrontEnd/src/styles/globals.css`:

```css
/* ── DMA Wizard Agent Select Step (CP-STUDIO-4 E1) ─────────────── */
.dma-wizard-fullwidth-card {
  padding: 0;
}

.dma-wizard-agent-select-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
  padding: 8px 0;
}

.dma-wizard-agent-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px;
  border: 1px solid var(--colorNeutralStroke2);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.03);
  cursor: pointer;
  text-align: left;
  width: 100%;
  transition: background 0.15s ease, border-color 0.15s ease, transform 0.15s ease;
}

.dma-wizard-agent-card:hover {
  background: rgba(255, 255, 255, 0.07);
  border-color: rgba(0, 242, 254, 0.35);
  transform: translateY(-2px);
}

.dma-wizard-agent-card.is-selected {
  border-color: rgba(0, 242, 254, 0.6);
  background: rgba(0, 242, 254, 0.08);
  box-shadow: 0 0 0 1px rgba(0, 242, 254, 0.25);
}

.dma-wizard-agent-card-name {
  font-weight: 600;
  font-size: 0.95rem;
}

.dma-wizard-agent-card-meta {
  font-size: 0.78rem;
  color: var(--colorNeutralForeground3);
  text-transform: capitalize;
}
```

#### Files to read first (max 1)
1. `src/CP/FrontEnd/src/styles/globals.css` — last 30 lines (find the correct insertion point — append after existing content)

#### Acceptance criteria
- [ ] CSS file builds without errors (`npm run build` exits 0)
- [ ] Agent cards have hover and selected states visible in browser
- [ ] `.dma-wizard-fullwidth-card` removes default Card padding for full-bleed wizard

---

## Iteration 1 — E2: YouTube OAuth Connect in Step 3

**Outcome**: Customer on Connect Platforms step (step 3 in the 7-step wizard, index 3) sees a "Connect with Google" button for YouTube. Clicking it redirects to Google OAuth. After Google redirects back, the app detects `?code&state`, calls finalize + attach, and shows a "YouTube connected" green badge. Other platforms show "coming soon".

---

### E2-S4: Wizard Connect Step — YouTube OAuth button + redirect

**Story size**: 60 min
**Branch**: `feat/CP-STUDIO-4-wizard-agent-select-youtube-oauth`
**BLOCKED UNTIL**: E1-S3 committed

#### Context

After S2, `DigitalMarketingActivationWizard.tsx` renders step panels matched by `currentStep.id`. The Connect Platforms step (`id: 'connect'`) currently renders a `<PlatformConnectionsPanel>` component. This story replaces that panel with a custom per-platform section for YouTube (Google OAuth) and a "coming soon" badge for other platforms.

**Critical import**: `youtubeConnections.service.ts` already exports:
```typescript
startYouTubeConnection(redirectUri: string): Promise<{ state: string, authorization_url: string, expires_at: string }>
finalizeYouTubeConnection(payload: { state: string, code: string, redirect_uri: string }): Promise<YouTubeConnection>
attachYouTubeConnection(credentialId: string, payload: { hired_instance_id: string, skill_id: string }): Promise<void>
listYouTubeConnections(): Promise<YouTubeConnection[]>
```

**Image promotion rule** (MUST FOLLOW):
```typescript
// Derive redirectUri from window.location — no hardcoded domain
const redirectUri = window.location.origin + window.location.pathname
```

**State storage before redirect** (sessionStorage is preserved across redirects within a session):
```typescript
// Before calling window.location.href = authorization_url:
sessionStorage.setItem('yt_oauth_state', state)
```

#### What to build

**A. Add imports** at top of `DigitalMarketingActivationWizard.tsx` (do not duplicate existing imports):
```typescript
import {
  startYouTubeConnection,
  finalizeYouTubeConnection,
  attachYouTubeConnection,
  listYouTubeConnections,
} from '../services/youtubeConnections.service'
```

**B. Add local state** (near existing state declarations):
```typescript
const [youtubeConnected, setYoutubeConnected] = useState(false)
const [oauthLoading, setOauthLoading] = useState(false)
const [oauthError, setOauthError] = useState<string | null>(null)
```

**C. Load existing YouTube connection on mount** — inside the existing `useEffect` that loads state (or add a new one):
```typescript
useEffect(() => {
  listYouTubeConnections().then((connections) => {
    if (connections.length > 0) setYoutubeConnected(true)
  }).catch(() => {/* silently ignore — not connected is the default */})
}, [])
```

**D. handleConnectYouTube function** (add to component body before return):
```typescript
async function handleConnectYouTube() {
  setOauthLoading(true)
  setOauthError(null)
  try {
    const redirectUri = window.location.origin + window.location.pathname
    const { state, authorization_url } = await startYouTubeConnection(redirectUri)
    sessionStorage.setItem('yt_oauth_state', state)
    window.location.href = authorization_url
  } catch (err) {
    setOauthError('Could not start YouTube connection. Please try again.')
    setOauthLoading(false)
  }
}
```

**E. Connect step panel** — find the `currentStep.id === 'connect'` panel (or the PlatformConnectionsPanel render) and replace it with:
```tsx
{currentStep.id === 'connect' && (
  <div data-testid="dma-step-panel-connect" className="dma-wizard-canvas-body-inner">
    <div className="dma-wizard-platform-connect-list">

      {/* YouTube */}
      <div className="dma-wizard-platform-connect-row">
        <div className="dma-wizard-platform-connect-info">
          <span className="dma-wizard-platform-connect-name">YouTube</span>
          <span className="dma-wizard-platform-connect-desc">
            Connect your YouTube channel to allow the agent to manage uploads and publishing.
          </span>
        </div>
        <div className="dma-wizard-platform-connect-action">
          {youtubeConnected ? (
            <span className="dma-wizard-connected-badge">✓ Connected</span>
          ) : (
            <Button
              appearance="primary"
              disabled={oauthLoading || readOnly}
              onClick={handleConnectYouTube}
            >
              {oauthLoading ? 'Connecting…' : 'Connect with Google'}
            </Button>
          )}
        </div>
      </div>

      {oauthError && (
        <div className="dma-wizard-oauth-error">{oauthError}</div>
      )}

      {/* Other platforms — coming soon */}
      {(['Instagram', 'Facebook', 'LinkedIn', 'WhatsApp', 'X'] as const).map((name) => (
        <div key={name} className="dma-wizard-platform-connect-row dma-wizard-platform-connect-row--disabled">
          <div className="dma-wizard-platform-connect-info">
            <span className="dma-wizard-platform-connect-name">{name}</span>
          </div>
          <div className="dma-wizard-platform-connect-action">
            <span className="dma-wizard-coming-soon-badge">Coming soon</span>
          </div>
        </div>
      ))}
    </div>
  </div>
)}
```

**F. Remove the `PlatformConnectionsPanel` import and usage** from `DigitalMarketingActivationWizard.tsx` if it is only used in the connect step. If it is used elsewhere, keep the import.

#### Files to read first (max 3)
1. `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` — lines 1–25 (imports block, check existing imports)
2. `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` — the section containing `currentStep.id === 'connect'` or `PlatformConnectionsPanel` render
3. `src/CP/FrontEnd/src/services/youtubeConnections.service.ts` — full file (confirm function signatures and return types)

#### Acceptance criteria
- [ ] Connect step renders "Connect with Google" button for YouTube
- [ ] Button calls `startYouTubeConnection` with `redirectUri = window.location.origin + window.location.pathname`
- [ ] State is stored in `sessionStorage` key `yt_oauth_state` before redirect
- [ ] When `youtubeConnected` is true (from `listYouTubeConnections` on mount), button is replaced by "✓ Connected" badge
- [ ] Five other platforms show "Coming soon" badges
- [ ] No hardcoded domain, port, or environment URL
- [ ] `npm run build` exits 0

---

### E2-S5: Wizard OAuth callback handler — finalize + attach on return

**Story size**: 60 min
**Branch**: `feat/CP-STUDIO-4-wizard-agent-select-youtube-oauth`
**BLOCKED UNTIL**: E2-S4 committed

#### Context

After Google OAuth, Google redirects back to the CP app at the same URL with `?code=CODE&state=STATE` query params. The wizard's `useEffect` on mount must detect these params, call `finalizeYouTubeConnection` then `attachYouTubeConnection`, clear the URL, and set `youtubeConnected = true`.

The `hired_instance_id` (UUID of the specific hire) is available as `instance?.hired_instance_id`. The `skill_id` for the YouTube connection is available as the first key in `instance?.skills ?? {}` (the DMA agent has a single skill mapped to YouTube).

Derive `defaultSkillId` from instance:
```typescript
const defaultSkillId = Object.keys(instance?.skills ?? {})[0] ?? ''
```

#### What to build

**A. OAuth callback useEffect** — Add as the FIRST useEffect in the component (before other useEffects):
```typescript
useEffect(() => {
  const params = new URLSearchParams(window.location.search)
  const code = params.get('code')
  const state = params.get('state')
  if (!code || !state) return

  const storedState = sessionStorage.getItem('yt_oauth_state')
  if (!storedState || storedState !== state) {
    // State mismatch — do not process (CSRF protection)
    return
  }

  const redirectUri = window.location.origin + window.location.pathname
  const hiredInstanceId = instance?.hired_instance_id ?? ''
  const skillId = Object.keys(instance?.skills ?? {})[0] ?? ''

  ;(async () => {
    try {
      setOauthLoading(true)
      const connection = await finalizeYouTubeConnection({ state, code, redirect_uri: redirectUri })
      await attachYouTubeConnection(connection.id, {
        hired_instance_id: hiredInstanceId,
        skill_id: skillId,
      })
      sessionStorage.removeItem('yt_oauth_state')
      // Clean URL params without full reload
      window.history.replaceState({}, '', window.location.pathname)
      setYoutubeConnected(true)
      // Re-navigate to the connect step so the user sees the green badge
      setActiveStepIndex(DMA_STEPS.findIndex((s) => s.id === 'connect'))
    } catch (err) {
      setOauthError('YouTube connection failed. Please try again.')
    } finally {
      setOauthLoading(false)
    }
  })()
}, []) // eslint-disable-line react-hooks/exhaustive-deps — intentionally runs once on mount
```

**B. CSRF validation note**: The `storedState !== state` check prevents CSRF attacks — never remove this check.

#### Files to read first (max 2)
1. `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` — lines 100–180 (all existing useEffect calls, to find the correct insertion point)
2. `src/CP/FrontEnd/src/services/youtubeConnections.service.ts` — full file (confirm `finalizeYouTubeConnection` return shape — need the `id` field for `attachYouTubeConnection`)

#### Acceptance criteria
- [ ] On mount, if `?code=` and `?state=` are in the URL, the handler calls `finalizeYouTubeConnection` then `attachYouTubeConnection`
- [ ] `state` from URL is validated against `sessionStorage.getItem('yt_oauth_state')` before processing (CSRF check)
- [ ] On success, URL is cleaned (`window.history.replaceState`), wizard navigates to connect step, `youtubeConnected` is true
- [ ] On error, `oauthError` shows an error message
- [ ] `sessionStorage` key `yt_oauth_state` is removed after successful connection
- [ ] `npm run build` exits 0

---

### E2-S6: CSS + tests

**Story size**: 45 min
**Branch**: `feat/CP-STUDIO-4-wizard-agent-select-youtube-oauth`
**BLOCKED UNTIL**: E2-S5 committed

#### Context

This story adds CSS for the OAuth connect list layout, updates the existing wizard tests to handle the 7-step wizard (Step 0 added), and validates the build.

Current test file: `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx`
The tests were written for the 6-step wizard. After S2, there are now 7 steps. The test that checks "Continue × 5 reaches Activate" must now use "Continue × 6" (or simulate clicking past Step 0 first). Update tests to pass.

#### A. CSS additions — append to `src/CP/FrontEnd/src/styles/globals.css`

```css
/* ── DMA Wizard YouTube OAuth Connect (CP-STUDIO-4 E2) ─────────── */
.dma-wizard-platform-connect-list {
  display: grid;
  gap: 12px;
  padding: 8px 0;
}

.dma-wizard-platform-connect-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border: 1px solid var(--colorNeutralStroke2);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.03);
}

.dma-wizard-platform-connect-row--disabled {
  opacity: 0.55;
}

.dma-wizard-platform-connect-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.dma-wizard-platform-connect-name {
  font-weight: 600;
  font-size: 0.92rem;
}

.dma-wizard-platform-connect-desc {
  font-size: 0.78rem;
  color: var(--colorNeutralForeground3);
}

.dma-wizard-platform-connect-action {
  flex-shrink: 0;
}

.dma-wizard-connected-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 12px;
  border-radius: 999px;
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  font-size: 0.82rem;
  font-weight: 700;
}

.dma-wizard-coming-soon-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--colorNeutralForeground3);
  font-size: 0.78rem;
}

.dma-wizard-oauth-error {
  padding: 10px 14px;
  border-radius: 10px;
  background: rgba(239, 68, 68, 0.12);
  color: #f87171;
  font-size: 0.85rem;
}
```

#### B. Test updates — `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx`

Read the current test file first. Update the following:

1. Any mock/render of `DigitalMarketingActivationWizard` must pass `instances={[mockInstance]}` (or an empty array) to satisfy the new prop.

2. Any test that advances through all 6 steps (e.g., "Continue × 5 reaches Activate") must now advance through 7 steps: the wizard starts at Step 0 (Select Agent). If `instances` has 1 entry, it auto-advances to Step 1 (Induct Agent) — in that case, the test just needs 6 Continue clicks (same as before, since step 0 is skipped automatically). If the test uses multiple instances, add a "click an agent card" action before the Continue clicks.

3. Add one new test: `'renders Step 0 agent select panel when instances provided'`:
   - Render wizard with `instances={[mockInstance1, mockInstance2]}`
   - Expect `screen.getByTestId('dma-step-panel-select')` to be in the document
   - Expect both agent names to be visible
   - Click one agent card
   - Expect `onSelectedInstanceChange` to have been called with the correct subscription_id
   - Expect `screen.getByTestId('dma-step-panel-induct')` to be in the document (advanced past Step 0)

#### Files to read first (max 3)
1. `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` — full file (understand current test structure and mocks)
2. `src/CP/FrontEnd/src/styles/globals.css` — last 30 lines (find append insertion point)
3. `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` — lines 25–45 (DMA_STEPS and Props to confirm shape for mock)

#### Final validation sequence

After all CSS and test updates:
```bash
cd src/CP/FrontEnd && npm run build 2>&1 | tail -20
```
Must exit 0.

```bash
cd src/CP/FrontEnd && npx vitest run src/test/MyAgentsDigitalMarketingWizard.test.tsx 2>&1 | tail -30
```
All tests green.

```bash
git add -A && git commit -m "feat(CP-STUDIO-4): S6 — CSS + tests, all green" && git push
```

Then open the PR:
```bash
gh pr create \
  --base main \
  --title "feat(CP-STUDIO-4): Wizard agent-select step + YouTube OAuth connect" \
  --body "## CP-STUDIO-4

Two improvements to the DMA Activation Wizard:

### E1 — Agent Selection as Step 0
- Removes AgentSelector dropdown and 4 tab buttons for DMA agents
- Adds Step \`select\` as step 0 in the 7-step wizard
- Agent cards rendered inline; clicking selects + advances
- Auto-advances when only 1 instance

### E2 — YouTube OAuth Connect
- Step 3 (Connect Platforms) now shows 'Connect with Google' button
- Uses \`startYouTubeConnection\` → redirect → \`finalizeYouTubeConnection\` → \`attachYouTubeConnection\`
- CSRF protection via sessionStorage state validation
- redirect\_uri derived from \`window.location.origin + window.location.pathname\` (image-promotion safe)
- Other platforms show 'Coming soon'

### Testing
- All existing wizard tests updated for 7-step layout
- New test for Step 0 agent selection

Closes CP-STUDIO-4"
```

Post the PR URL. HALT.

#### Acceptance criteria
- [ ] `npm run build` exits 0, no TypeScript errors
- [ ] All existing wizard tests pass (updated for 7 steps)
- [ ] New Step 0 agent select test passes
- [ ] PR opened with description above

---

## PM Review Checklist

- [x] Every story has ≤ 3 files to read
- [x] No story says "see above" or "similar to X"
- [x] No story says "refactor while you're there"
- [x] No story has business logic in CP BackEnd (100% FE-only plan)
- [x] NFR compliance: no new Python, no new GCP resources, no new backend routes
- [x] Image promotion: `redirect_uri` derived from `window.location` only
- [x] CSRF protection: state validation documented in S5
- [x] CSS namespace: all new classes use `dma-wizard-` prefix
- [x] Stories ordered correctly: S1 (MyAgents) → S2 (Wizard props) → S3 (CSS) → S4 (OAuth button) → S5 (callback) → S6 (CSS + tests)
- [x] Backend pre-flight verified: all OAuth routes + GCP secrets confirmed present

---

## Defect Addendum — Live RCA From GCP Logs (2026-03-24)

### Defect

The deployed DMA wizard is still trying to load and save activation state against stale hired-agent and subscription records that no longer exist for customer `33eb5ebb-69f6-4341-b16e-f73ae2537d00` (`yogeshk7377@gmail.com`). That stale client-side selection then cascades into two visible failures:

1. DMA workspace load/save calls hit 404 on deleted `hired_instance_id` values.
2. The UI surfaces the backend failure poorly as `[object Object]` instead of a human-readable recovery message.
3. The YouTube OAuth callback reaches the backend, but finalize is rejected with 400 and the user is left in a broken connect flow.

### RCA

| Root cause | Impact | Best possible solution/fix |
|---|---|---|
| Wizard state is holding stale `subscription_id` / `hired_instance_id` values after old hires were deleted from live GCP SQL. | Every workspace read or save against that stale hire returns 404, so the activation wizard cannot load readiness, save progress, or continue the flow. | Rehydrate wizard state from the latest `instances` prop on mount and whenever instance lookup fails; if `by-subscription` or `digital-marketing-activation` returns 404, clear the stale selection, force the new in-wizard Step 0 agent picker, and never keep a deleted `hired_instance_id` in local state. |
| Frontend error normalization is weak, so structured API problem details are coerced into a string and rendered as `[object Object]`. | User sees `Activation unavailable[object Object]Retry` instead of a clear message like `This agent record no longer exists. Please reselect your hired agent.` | Normalize `GatewayApiError.problem.detail` into a readable string in the shared gateway client, and map 404 stale-hire responses to a targeted recovery message plus a reset action. |
| YouTube OAuth finalize is reaching Plant successfully, but the callback/finalize step is not completing with a valid payload in the live wizard flow. | User can start OAuth, return from Google, and still end up with a failed YouTube connect state because finalize is rejected with 400. | Implement the full frontend callback flow described in E2-S4 and E2-S5: persist `yt_oauth_state`, validate returned `state`, use `redirect_uri = window.location.origin + window.location.pathname`, call `finalizeYouTubeConnection`, then `attachYouTubeConnection` only after a valid active hire is selected. |

### Evidence

#### Confirmed stale-hire / stale-subscription evidence

- `2026-03-24T09:14:22.816943Z` — `waooaw-cp-backend-demo` proxied `GET .../api/v1/hired-agents/by-subscription/SUB-230ec0ee-91a4-4aa9-bd11-a31679fda7d3?customer_id=33eb5ebb-69f6-4341-b16e-f73ae2537d00` and received `404 Not Found`.
- `2026-03-24T09:14:22.841652Z` — `waooaw-cp-backend-demo` proxied `GET .../api/v1/hired-agents/by-subscription/SUB-a28327bc-6813-4677-a78d-8ff6d789db90?...` and received `404 Not Found`.
- `2026-03-24T09:14:22.893288Z` — `waooaw-cp-backend-demo` proxied `GET .../api/v1/hired-agents/by-subscription/SUB-f80d06ab-15d5-47e4-bd82-4b34290062de?...` and received `404 Not Found`.
- `2026-03-24T09:14:23.376154Z` — `waooaw-cp-backend-demo` proxied `GET https://waooaw-plant-gateway-demo-.../api/v1/hired-agents/HAI-42539934-e996-4a6e-8a03-ae24b3834fc8/digital-marketing-activation?...` and received `404 Not Found`.
- `2026-03-24T10:31:19.537538Z` — `waooaw-cp-backend-demo` proxied `GET https://waooaw-plant-gateway-demo-.../api/v1/hired-agents/HAI-9c2878bd-2140-4a4b-ba99-20423eedc51c/digital-marketing-activation?...` and received `404 Not Found`.
- `2026-03-24T10:31:19.477527Z` — `waooaw-plant-gateway-demo` logged `Authenticated user 33eb5ebb-69f6-4341-b16e-f73ae2537d00 for GET /api/v1/hired-agents/HAI-9c2878bd-2140-4a4b-ba99-20423eedc51c/digital-marketing-activation`, proving this is not primarily an auth failure.

#### Confirmed YouTube finalize evidence

- `2026-03-24T10:29:22.978500Z` — `waooaw-cp-backend-demo` returned `POST /api/cp/youtube-connections/connect/finalize HTTP/1.1` → `400 Bad Request`.
- `2026-03-24T10:29:22.964404Z` — `waooaw-plant-backend-demo` returned `POST /api/v1/customer-platform-connections/youtube/connect/finalize HTTP/1.1` → `400 Bad Request`.
- `2026-03-24T10:31:01.298679Z` and `2026-03-24T10:31:19.466630Z` — the same CP finalize endpoint kept returning `400 Bad Request` on repeated retries.
- `2026-03-24T10:29:22.623205Z` and `2026-03-24T10:31:19.287983Z` — `waooaw-plant-gateway-demo` logged `Authenticated user 33eb5ebb-69f6-4341-b16e-f73ae2537d00 for POST /api/v1/customer-platform-connections/youtube/connect/finalize`, again showing the request is authenticated and reaching the backend.

#### UX evidence

- Browser symptom reported during the same window: `Activation unavailable[object Object]Retry`.
- This aligns with the 404 chain above and indicates the UI is rendering a structured backend error object directly instead of translating it into a readable message.

### Best Solution

1. Treat stale-hire recovery as the first fix, not the YouTube OAuth UI as the first fix.
2. Make the wizard source of truth the live `instances` list passed from My Agents, with Step 0 selection inside the wizard.
3. On any `404` from `by-subscription`, `deliverables`, or `digital-marketing-activation`, clear the selected hire, reset to Step 0, and show a plain-English recovery message.
4. After stale-hire recovery is in place, implement the full YouTube OAuth callback contract from E2-S4 and E2-S5 so finalize cannot run with missing or mismatched callback state.
5. Fix shared API error formatting so users never see `[object Object]` again.

### Plain-English Summary

The main break is not Google login itself. The wizard is still pointing at old hired-agent records that were deleted, so the backend correctly returns 404 and the UI turns that into `[object Object]`. The YouTube callback is also reaching the backend, but finalize is being rejected with 400, most likely because the wizard is not completing the callback state and attach flow cleanly after redirect. The best fix is to reset stale agent selection first, then complete the OAuth callback flow, and finally clean up the shared error messages.
