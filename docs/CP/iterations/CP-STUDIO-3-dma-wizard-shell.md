# CP-STUDIO-3 — DMA Activation Wizard Shell

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `CP-STUDIO-3` |
| Feature area | Customer Portal — My Agents DMA Activation Wizard |
| Created | 2026-03-23 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CP/iterations/CP-STUDIO-2-digital-marketing-activation-wizard.md` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 1 |
| Total epics | 1 |
| Total stories | 6 |

---

## Zero-Cost Agent Constraints (READ FIRST)

This plan is designed for **autonomous zero-cost model agents** (Gemini Flash, GPT-4o-mini, etc.)
with limited context windows. Every structural decision in this plan exists to preserve context.

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is fully self-contained — no cross-references, no "see above" |
| No working memory across files | CSS patterns and Fluent UI patterns are embedded inline in each story |
| No planning ability | Stories are atomic — one deliverable, one set of files, one test command |
| Token cost per file read | Max 3 files to read per story — pre-identified by PM in the card |
| Binary inference only | Acceptance criteria are pass/fail — no judgment calls required from the agent |

> **Agent:** Execute exactly ONE story at a time. Read your assigned story card fully, then act.
> Do NOT read other stories. Do NOT open NFRReusable.md. All patterns you need are in your card.
> Do NOT read files not listed in your story card's "Files to read first" section.

---

## Backend Pre-flight (verified by PM before writing this plan, no agent action required)

| Check | Status |
|---|---|
| Plant DMA routes registered (`src/Plant/BackEnd/api/v1/router.py`) | ✅ Both `digital_marketing_activation.router` and `digital_marketing_activation.theme_router` included |
| CP BackEnd proxy (`src/CP/BackEnd/api/digital_marketing_activation.py`) | ✅ Thin proxy with `waooaw_router`, `PlantGatewayClient`, all routes wired |
| FE service layer (`src/CP/FrontEnd/src/services/digitalMarketingActivation.service.ts`) | ✅ All calls: GET/PUT/PATCH workspace, generate theme, patch theme |
| GCP Secret Manager `XAI_API_KEY` | ✅ Present (created 2026-03-20) |
| Database persistence | ✅ `HiredAgentRepository.update_config()` called by Plant DMA on every upsert |

**Conclusion: This plan is frontend-only. Zero backend, proxy, or GCP changes required.**

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Rebuild `DigitalMarketingActivationWizard.tsx` from milestone-tab layout to 6-step left-rail guided wizard. CSS classes added to `globals.css`. Tests updated. | 1 | 6 | 6h | 6h from launch |

**Estimate basis:** FE shell = 90 min | Per-step panel = 60 min | CSS+tests = 45 min. 20% buffer added.

---

## How to Launch Iteration 1

**Pre-flight check (run in terminal before launching):**
```bash
git fetch origin && git log --oneline origin/main | head -3
# Must show: clean main with last merge commit at top
```

**Steps to launch:**
1. Open VS Code
2. Open Copilot Chat: `Ctrl+Alt+I` (Windows/Linux)
3. Click the model dropdown → select **Agent mode**
4. Click `+` to start a new agent session
5. Type `@` → select **platform-engineer** from dropdown
6. Paste the block below → press **Enter**
7. Come back in 6 hours

**Iteration 1 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React 18 / TypeScript / Fluent UI engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior React 18 / TypeScript / Fluent UI engineer, I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-STUDIO-3-dma-wizard-shell.md
YOUR SCOPE: Iteration 1 only — Epic E1 (all 6 stories S1–S6). Do not modify anything outside CP FrontEnd.
TIME BUDGET: 6h. If you reach 7h without finishing, follow STUCK PROTOCOL now.

EXECUTION ORDER:
1. Run: git fetch origin && git log --oneline origin/main | head -3
   You must be on main or able to branch from main with a clean tree. If not, post why and HALT.
2. Read the "Agent Execution Rules" section in this plan file.
3. Read the "Iteration 1 — Epic E1" section in this plan file.
4. Read nothing else before starting.
5. Execute stories in this order: S1 → S2 → S3 → S4 → S5 → S6
6. When all stories pass their acceptance criteria, open the PR. Post the PR URL. HALT.
```

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all instructions.

### Rule -1 — Activate Expert Persona

Activate: **Senior React 18 / TypeScript / Fluent UI engineer**

Begin every epic with:
> *"Acting as a Senior React 18 / TypeScript / Fluent UI engineer, I will [what] by [approach]."*

### Rule 0 — Branch

```bash
git checkout main && git pull origin main
git checkout -b feat/CP-STUDIO-3-dma-wizard-shell
```

### Rule 1 — CHECKPOINT after every story

After each story's tests pass:
```bash
git add -A && git commit -m "feat(CP-STUDIO-3): [story-id] — [story title]" && git push -u origin feat/CP-STUDIO-3-dma-wizard-shell
```

Do this BEFORE starting the next story. If the session is interrupted, completed stories are already saved.

### Rule 2 — STUCK PROTOCOL

If you are blocked for more than 20 minutes OR encounter a failure you cannot resolve in 2 attempts:
1. `git add -A && git commit -m "WIP: CP-STUDIO-3 stuck at [story-id] — [reason]" && git push`
2. Open a **draft PR** titled `WIP: CP-STUDIO-3 — stuck at [story-id]`
3. In the PR description write: the exact file, the exact error, the two approaches tried
4. HALT

### Rule 3 — Build must pass

After S6 run:
```bash
cd src/CP/FrontEnd && npm run build 2>&1 | tail -20
```
Zero TypeScript errors. Zero Vite build errors. If any: fix before committing S6.

### Rule 4 — Test must pass

Run after S6:
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

All new CSS classes use the `dma-wizard-` prefix. Do NOT reuse `pp-agent-studio-` prefixed classes — those are PP-only. Define new classes in `src/CP/FrontEnd/src/styles/globals.css`.

---

## Iteration 1 — E1: Customer-Guided DMA Activation Wizard

**Outcome**: Customer navigating to My Agents → selecting a hired DMA agent → sees a polished 6-step left-rail wizard. Each step focuses on one concern. Clicking "Continue" auto-saves to GCP SQL before advancing. Clicking "Activate" on step 6 finalizes the agent.

---

### E1-S1: Wizard Shell — Step State Machine + Layout

**Story size**: 90 min  
**Branch**: `feat/CP-STUDIO-3-dma-wizard-shell`  
**BLOCKED UNTIL**: none — first story  

#### Context (read this, not the file list)
`DigitalMarketingActivationWizard.tsx` is currently a scrolling milestone-tab layout with 4 tabs (Induct, Prepare, Theme, Schedule). This story replaces that layout with a left-rail + canvas shell identical in structure to PP's `AgentSetupStudio.tsx`, but using CP-specific CSS classes (`dma-wizard-*`) and 6 steps instead of 5. The step state machine uses `activeStepIndex: number` state and renders only the step panel matching the current index. The per-step content panels are temporarily replaced with placeholder `<div>` elements — subsequent stories fill them in.

#### Files to read first (max 3)
1. `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` — full file (understand all existing state variables and props)
2. `src/CP/FrontEnd/src/styles/globals.css` — last 50 lines (find the insertion point for new CSS)

#### What to build

**A. Replace the component's render output** in `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx`.

Keep ALL existing state variables and hooks at the top of the component unchanged. Only replace the `return (...)` block.

The 6 steps:
```typescript
const DMA_STEPS = [
  { id: 'induct',    title: 'Induct Agent',        description: 'Set the agent nickname and brand identity.' },
  { id: 'platforms', title: 'Choose Platforms',     description: 'Select which social channels this agent will manage.' },
  { id: 'connect',   title: 'Connect Platforms',    description: 'Authorise each selected platform channel.' },
  { id: 'theme',     title: 'Build Master Theme',   description: 'Define brand brief and generate an AI content strategy.' },
  { id: 'schedule',  title: 'Confirm Schedule',     description: 'Set posting frequency and preferred days.' },
  { id: 'activate',  title: 'Review & Activate',    description: 'Check readiness then activate the agent.' },
] as const
type DmaStepId = typeof DMA_STEPS[number]['id']
```

Add `activeStepIndex` state:
```typescript
const [activeStepIndex, setActiveStepIndex] = useState(0)
const currentStep = DMA_STEPS[activeStepIndex]
```

**B. New render output** — replace the existing `return (...)` with this shell:
```tsx
return (
  <div className="dma-wizard-page">
    <div className="dma-wizard-shell">
      {/* LEFT RAIL */}
      <aside className="dma-wizard-rail">
        <Card className="dma-wizard-rail-card">
          <Text as="h2" size={500} weight="semibold">Activation steps</Text>
          <div className="dma-wizard-step-list">
            {DMA_STEPS.map((step, index) => {
              const isActive = index === activeStepIndex
              const isDone = index < activeStepIndex
              return (
                <button
                  key={step.id}
                  type="button"
                  className={`dma-wizard-step-button${isActive ? ' is-active' : ''}${isDone ? ' is-done' : ''}`}
                  onClick={() => setActiveStepIndex(index)}
                >
                  <span className="dma-wizard-step-index">0{index + 1}</span>
                  <span className="dma-wizard-step-copy">
                    <span className="dma-wizard-step-title">{step.title}</span>
                    <span className="dma-wizard-step-description">{step.description}</span>
                  </span>
                  {isDone ? <span className="dma-wizard-step-state dma-wizard-step-state--done">Done</span> : null}
                  {isActive ? <span className="dma-wizard-step-state dma-wizard-step-state--active">Now</span> : null}
                </button>
              )
            })}
          </div>
        </Card>
      </aside>

      {/* CANVAS */}
      <section className="dma-wizard-canvas">
        <Card className="dma-wizard-canvas-card">
          {/* STICKY HEADER */}
          <div className="dma-wizard-canvas-header">
            <CardHeader
              className="dma-wizard-canvas-header-card"
              header={
                <div>
                  <Text as="h2" size={600} weight="semibold">{currentStep.title}</Text>
                  <Text as="p" size={300}>{currentStep.description}</Text>
                </div>
              }
            />
          </div>

          {/* SCROLLABLE BODY */}
          <div className="dma-wizard-canvas-body">
            {isLoading ? (
              <Spinner label="Loading activation workspace..." />
            ) : loadError ? (
              <FeedbackMessage intent="error" title="Load failed" message={loadError} />
            ) : (
              <div data-testid={`dma-step-panel-${currentStep.id}`}>
                {/* STEP PANELS — filled in by S2–S5 */}
                <div style={{ padding: '1rem', opacity: 0.6 }}>Step {activeStepIndex + 1}: {currentStep.title} — panel coming in next stories.</div>
              </div>
            )}
          </div>

          {/* STICKY FOOTER — Back / Continue / Activate */}
          <div className="dma-wizard-action-bar">
            <div className="dma-wizard-action-bar-left">
              <SaveIndicator status={saveStatus} errorMessage={saveError || undefined} />
            </div>
            <div className="dma-wizard-action-bar-right">
              <Button
                appearance="subtle"
                onClick={() => setActiveStepIndex(i => Math.max(0, i - 1))}
                disabled={activeStepIndex === 0}
              >
                Back
              </Button>
              {activeStepIndex < DMA_STEPS.length - 1 ? (
                <Button
                  appearance="primary"
                  onClick={() => void handleContinue()}
                  disabled={saveStatus === 'saving'}
                >
                  {saveStatus === 'saving' ? 'Saving…' : 'Continue'}
                </Button>
              ) : (
                <Button
                  appearance="primary"
                  onClick={() => void handleActivate()}
                  disabled={readOnly || saveStatus === 'saving' || !readiness.can_finalize}
                >
                  {saveStatus === 'saving' ? 'Activating…' : 'Activate Agent'}
                </Button>
              )}
            </div>
          </div>
        </Card>
      </section>
    </div>
  </div>
)
```

Add these two async handlers to the component body (before the return):
```typescript
async function handleContinue() {
  await saveWorkspace()
  setActiveStepIndex(i => Math.min(DMA_STEPS.length - 1, i + 1))
}

async function handleActivate() {
  await saveWorkspace({ activation_complete: true })
  // stay on step 6 after activation, loadState will refresh readiness
  await loadState()
}
```

Note: `saveWorkspace` already exists in the component. Pass an optional partial workspace override:
If `saveWorkspace` does not accept arguments, add an `overrides?: Record<string, unknown>` parameter or create a separate call pattern — read the existing code first and adapt accordingly.

**C. Add CSS** at the end of `src/CP/FrontEnd/src/styles/globals.css`:
```css
/* ── DMA Activation Wizard Shell (CP-STUDIO-3) ─────────────────── */
.dma-wizard-page {
  padding-bottom: 32px;
}

.dma-wizard-shell {
  --dma-wizard-pane-height: min(76vh, 860px);
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 20px;
  align-items: stretch;
}

.dma-wizard-rail {
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: sticky;
  top: 24px;
  height: var(--dma-wizard-pane-height);
  min-height: var(--dma-wizard-pane-height);
  overflow-y: auto;
  padding-right: 6px;
}

.dma-wizard-rail-card,
.dma-wizard-canvas-card {
  padding: 20px;
  border-radius: 24px;
}

.dma-wizard-rail > .dma-wizard-rail-card:first-child {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dma-wizard-step-list {
  display: grid;
  gap: 8px;
  min-height: 0;
}

.dma-wizard-canvas {
  min-height: 0;
}

.dma-wizard-canvas-card {
  height: var(--dma-wizard-pane-height);
  min-height: var(--dma-wizard-pane-height);
  display: flex;
  flex-direction: column;
}

.dma-wizard-canvas-header {
  position: sticky;
  top: 0;
  z-index: 1;
  margin: -4px -4px 0;
  padding: 0 4px 14px;
  border-bottom: 1px solid var(--colorNeutralStroke2);
  background: linear-gradient(180deg, rgba(24,24,27,0.98) 0%, rgba(24,24,27,0.94) 74%, rgba(24,24,27,0) 100%);
}

.dma-wizard-canvas-header-card {
  padding: 0;
}

.dma-wizard-canvas-body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 16px 6px 8px 0;
}

.dma-wizard-action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-top: 14px;
  border-top: 1px solid var(--colorNeutralStroke2);
  margin-top: auto;
  flex-shrink: 0;
}

.dma-wizard-action-bar-left,
.dma-wizard-action-bar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dma-wizard-step-button {
  width: 100%;
  border: 1px solid var(--colorNeutralStroke2);
  background: rgba(255,255,255,0.03);
  color: inherit;
  border-radius: 16px;
  text-align: left;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  padding: 12px;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.dma-wizard-step-button.is-active {
  border-color: rgba(0,242,254,0.6);
  box-shadow: 0 0 0 1px rgba(0,242,254,0.25);
  background: rgba(0,242,254,0.08);
}

.dma-wizard-step-button.is-done {
  border-color: rgba(16,185,129,0.35);
  background: rgba(16,185,129,0.05);
}

.dma-wizard-step-index {
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  background: rgba(255,255,255,0.08);
  font-weight: 700;
  font-size: 0.85rem;
  flex-shrink: 0;
}

.dma-wizard-step-copy {
  display: grid;
  gap: 3px;
}

.dma-wizard-step-title {
  display: block;
  font-weight: 600;
  font-size: 0.9rem;
}

.dma-wizard-step-description {
  display: block;
  color: var(--colorNeutralForeground2);
  font-size: 0.78rem;
  line-height: 1.4;
}

.dma-wizard-step-state {
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
}

.dma-wizard-step-state--active { color: #00f2fe; }
.dma-wizard-step-state--done   { color: #10b981; }

.dma-wizard-form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.dma-wizard-platform-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

.dma-wizard-platform-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px;
  border: 1px solid var(--colorNeutralStroke2);
  border-radius: 14px;
  background: rgba(255,255,255,0.03);
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.dma-wizard-platform-card.is-selected {
  border-color: rgba(0,242,254,0.6);
  background: rgba(0,242,254,0.08);
}

.dma-wizard-section-label {
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  opacity: 0.65;
  margin-bottom: 4px;
}

.dma-wizard-review-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--colorNeutralStroke2);
  gap: 12px;
}

.dma-wizard-review-row:last-child {
  border-bottom: none;
}

@media (max-width: 768px) {
  .dma-wizard-shell {
    grid-template-columns: 1fr;
  }
  .dma-wizard-rail {
    position: static;
    height: auto;
    min-height: 0;
  }
  .dma-wizard-canvas-card {
    height: auto;
    min-height: 60vh;
  }
}
```

#### Required imports to add (if not already present)
Add to existing import block at top of `DigitalMarketingActivationWizard.tsx`:
```typescript
import { CardHeader, Spinner, Text } from '@fluentui/react-components'
```
(Do not duplicate imports that already exist — check first.)

#### Acceptance criteria
- [ ] `npm run build` in `src/CP/FrontEnd` exits 0
- [ ] Left rail renders 6 step buttons
- [ ] Active step shows `is-active` class and cyan highlight
- [ ] Back button disabled on step 1
- [ ] Continue button present on steps 1–5
- [ ] "Activate Agent" button present on step 6
- [ ] Clicking a step in the rail navigates to that step
- [ ] Each step body shows `data-testid="dma-step-panel-{id}"` wrapper

---

### E1-S2: Step Panels — Induct Agent (Step 1) + Choose Platforms (Step 2)

**Story size**: 60 min  
**Branch**: `feat/CP-STUDIO-3-dma-wizard-shell`  
**BLOCKED UNTIL**: E1-S1 committed  

#### Context
After S1 is committed, the canvas body shows placeholder divs for all steps. This story fills in steps 1 and 2 with real form controls. All state variables (`nickname`, `theme`, `selectedPlatforms`) already exist in the component — this story only wires them into the new per-step panels.

Step 1 (Induct Agent): Nickname text input, Theme text input, and a readiness badge showing whether the identity is configured.

Step 2 (Choose Platforms): A tile grid of 6 platform options. Clicking a tile toggles the platform in `selectedPlatforms` state. The list of platforms is defined inline.

#### Files to read first (max 3)
1. `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` — top 200 lines (state variables and load/save logic)

#### What to build

In `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx`, replace the placeholder div inside `data-testid="dma-step-panel-induct"` with:

```tsx
{/* STEP 1 — Induct Agent */}
{currentStep.id === 'induct' && (
  <div className="dma-wizard-step-content" data-testid="dma-step-panel-induct">
    <div style={{ display: 'grid', gap: '1.25rem' }}>
      <div>
        <div className="dma-wizard-section-label">Agent identity</div>
        <div className="dma-wizard-form-grid">
          <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <span>Nickname</span>
            <Input
              aria-label="Nickname"
              value={nickname}
              onChange={(_, data) => setNickname(data.value)}
              disabled={readOnly}
              placeholder="e.g. Growth Copilot"
            />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <span>Theme</span>
            <Input
              aria-label="Theme"
              value={theme}
              onChange={(_, data) => setTheme(data.value)}
              disabled={readOnly}
              placeholder="e.g. dark"
            />
          </label>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <Badge appearance="outline" color={readiness.configured ? 'success' : 'warning'}>
          {readiness.configured ? 'Identity configured ✓' : 'Nickname and theme required'}
        </Badge>
        {hiredInstanceId ? (
          <span style={{ opacity: 0.65, fontSize: '0.85rem' }}>
            Hire ID: {hiredInstanceId}
          </span>
        ) : null}
      </div>
    </div>
  </div>
)}
```

Replace the placeholder div inside `data-testid="dma-step-panel-platforms"` with:

```tsx
{/* STEP 2 — Choose Platforms */}
{currentStep.id === 'platforms' && (
  <div className="dma-wizard-step-content" data-testid="dma-step-panel-platforms">
    <div style={{ display: 'grid', gap: '1.25rem' }}>
      <div>
        <div className="dma-wizard-section-label">Select the channels for this agent to manage</div>
        <div className="dma-wizard-platform-grid">
          {[
            { key: 'youtube',   label: 'YouTube' },
            { key: 'instagram', label: 'Instagram' },
            { key: 'facebook',  label: 'Facebook' },
            { key: 'linkedin',  label: 'LinkedIn' },
            { key: 'whatsapp',  label: 'WhatsApp' },
            { key: 'x',        label: 'X (Twitter)' },
          ].map(({ key, label }) => {
            const isSelected = selectedPlatforms.includes(key)
            return (
              <button
                key={key}
                type="button"
                className={`dma-wizard-platform-card${isSelected ? ' is-selected' : ''}`}
                onClick={() => {
                  if (readOnly) return
                  setSelectedPlatforms(prev =>
                    isSelected ? prev.filter(p => p !== key) : [...prev, key]
                  )
                }}
                disabled={readOnly}
                aria-pressed={isSelected}
                data-testid={`platform-toggle-${key}`}
              >
                <span style={{ fontWeight: 600 }}>{label}</span>
                {isSelected ? <span style={{ color: '#00f2fe', marginLeft: 'auto' }}>✓</span> : null}
              </button>
            )
          })}
        </div>
      </div>

      {selectedPlatforms.length > 0 ? (
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {selectedPlatforms.map(p => (
            <Badge key={p} appearance="outline" color="informative">{p}</Badge>
          ))}
        </div>
      ) : (
        <div style={{ opacity: 0.6, fontSize: '0.9rem' }}>Select at least one platform to continue.</div>
      )}
    </div>
  </div>
)}
```

**Important**: The `data-testid` on the outer placeholder divs added in S1 should now be moved to the real step content div. Remove the old placeholder divs and replace with the JSX above.

**State variable check**: The component must have `selectedPlatforms` as a `string[]` state variable. Search for it in the component. If it is named differently (e.g. `platforms`), use that exact name.

#### Acceptance criteria
- [ ] Step 1 renders Nickname and Theme inputs with current values
- [ ] Step 1 badge shows green "Identity configured ✓" when both nickname and theme are non-empty
- [ ] Step 2 renders 6 platform tiles
- [ ] Clicking a tile toggles it selected (cyan border)
- [ ] `data-testid="dma-step-panel-induct"` exists when on step 1
- [ ] `data-testid="dma-step-panel-platforms"` exists when on step 2
- [ ] `npm run build` exits 0

---

### E1-S3: Step Panel — Connect Platforms (Step 3)

**Story size**: 60 min  
**Branch**: `feat/CP-STUDIO-3-dma-wizard-shell`  
**BLOCKED UNTIL**: E1-S2 committed  

#### Context
Step 3 shows platform connection flows. The existing `PlatformConnectionsPanel` component handles the OAuth/credential flow per platform. This story renders that component once per selected platform and shows a per-platform completion badge. If no platforms are selected it shows a "Go back to step 2" prompt.

The component already imports `PlatformConnectionsPanel`. The `platformConnections` state variable (or equivalent) and the `platformBindings` state already exist in the component.

#### Files to read first (max 3)
1. `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` — lines 1–150 (find `PlatformConnectionsPanel` import usage and `platformBindings` / `platformConnections` state)
2. `src/CP/FrontEnd/src/components/PlatformConnectionsPanel.tsx` — top 60 lines (understand its props interface)

#### What to build

Replace the placeholder div inside `data-testid="dma-step-panel-connect"` with:

```tsx
{/* STEP 3 — Connect Platforms */}
{currentStep.id === 'connect' && (
  <div className="dma-wizard-step-content" data-testid="dma-step-panel-connect">
    {selectedPlatforms.length === 0 ? (
      <div style={{ padding: '2rem', textAlign: 'center', opacity: 0.7 }}>
        <div style={{ fontSize: '1rem', marginBottom: '0.75rem' }}>No platforms selected yet.</div>
        <Button appearance="secondary" onClick={() => setActiveStepIndex(1)}>
          Go back to Choose Platforms
        </Button>
      </div>
    ) : (
      <div style={{ display: 'grid', gap: '1.5rem' }}>
        {selectedPlatforms.map((platformKey) => {
          const binding = platformBindings[platformKey] ?? {}
          const isConnected = Boolean(binding.connected)
          return (
            <div key={platformKey} style={{ display: 'grid', gap: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span style={{ fontWeight: 700, textTransform: 'capitalize', fontSize: '1rem' }}>
                  {platformKey}
                </span>
                <Badge appearance="outline" color={isConnected ? 'success' : 'warning'}>
                  {isConnected ? 'Connected ✓' : 'Not connected'}
                </Badge>
              </div>
              <PlatformConnectionsPanel
                hiredInstanceId={hiredInstanceId ?? ''}
                platformKey={platformKey}
                disabled={readOnly}
                onConnectionChange={() => void loadState()}
              />
            </div>
          )
        })}

        {readiness.youtube_selected && !readiness.youtube_connection_ready ? (
          <FeedbackMessage
            intent="warning"
            title="YouTube not connected"
            message="Connect YouTube above before continuing. The agent needs channel access to publish."
          />
        ) : null}
      </div>
    )}
  </div>
)}
```

**Note on PlatformConnectionsPanel props**: Read its actual props interface from the source file and adapt the props passed above to match exactly. If `onConnectionChange` is not a valid prop, remove it and call `loadState()` via a different mechanism (e.g. retry button or a periodic refresh already in the component).

**Note on `platformBindings` variable**: Search the existing component code for `platformBindings` (it may be named `bindings` or computed via `buildMarketingPlatformBindings`). Use the correct variable name.

#### Acceptance criteria
- [ ] Step 3 renders one connection panel per selected platform
- [ ] If no platforms selected: "No platforms selected yet" + back button shown
- [ ] Connected platforms show green "Connected ✓" badge
- [ ] YouTube warning shown when YouTube selected but not connected
- [ ] `data-testid="dma-step-panel-connect"` present on step 3
- [ ] `npm run build` exits 0

---

### E1-S4: Step Panel — Build Master Theme (Step 4)

**Story size**: 60 min  
**Branch**: `feat/CP-STUDIO-3-dma-wizard-shell`  
**BLOCKED UNTIL**: E1-S3 committed  

#### Context
Step 4 has two sub-sections: the business brief form (brand name, location, primary language, timezone, offerings/services textarea, business context textarea) and the Grok AI theme generation panel. The brief fields feed the Grok prompt. The user fills in the brief, then clicks "Generate with AI" to call `generateDigitalMarketingThemePlan`. The response renders as the master theme headline and derived theme tiles. The user can also type a manual master theme.

All the relevant state variables (`brandName`, `location`, `primaryLanguage`, `timezone`, `offeringsText`, `businessContext`, `masterTheme`, `derivedThemes`, `isGeneratingTheme`) already exist. The Grok call logic (`generateThemePlan` handler) also exists — only the render is being replaced.

#### Files to read first (max 3)
1. `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` — lines 100–280 (find all brief + theme state variables and `generateThemePlan` / `isGeneratingTheme` handler)

#### What to build

Replace the placeholder div inside `data-testid="dma-step-panel-theme"` with:

```tsx
{/* STEP 4 — Build Master Theme */}
{currentStep.id === 'theme' && (
  <div className="dma-wizard-step-content" data-testid="dma-step-panel-theme">
    <div style={{ display: 'grid', gap: '1.75rem' }}>

      {/* Business brief */}
      <div>
        <div className="dma-wizard-section-label">Business brief</div>
        <div className="dma-wizard-form-grid" style={{ marginBottom: '0.85rem' }}>
          <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <span>Brand name</span>
            <Input aria-label="Brand name" value={brandName} onChange={(_, data) => setBrandName(data.value)} disabled={readOnly} />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <span>Location</span>
            <Input aria-label="Location" value={location} onChange={(_, data) => setLocation(data.value)} disabled={readOnly} />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <span>Primary language</span>
            <Input aria-label="Primary language" value={primaryLanguage} onChange={(_, data) => setPrimaryLanguage(data.value)} disabled={readOnly} />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <span>Timezone</span>
            <Input aria-label="Timezone" value={timezone} onChange={(_, data) => setTimezone(data.value)} disabled={readOnly} placeholder="e.g. Asia/Kolkata" />
          </label>
        </div>
        <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginBottom: '0.85rem' }}>
          <span>Offerings and services</span>
          <Textarea
            aria-label="Offerings and services"
            value={offeringsText}
            onChange={(_, data) => setOfferingsText(data.value)}
            disabled={readOnly}
            resize="vertical"
            rows={3}
            placeholder="Comma-separated list of what you sell or offer"
          />
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
          <span>Business context</span>
          <Textarea
            aria-label="Business context"
            value={businessContext}
            onChange={(_, data) => setBusinessContext(data.value)}
            disabled={readOnly}
            resize="vertical"
            rows={3}
            placeholder="Describe your business, target audience, key differentiators"
          />
        </label>
      </div>

      {/* AI theme generation */}
      <div>
        <div className="dma-wizard-section-label">AI-generated content strategy</div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', marginBottom: '1rem' }}>
          <Button
            appearance="primary"
            onClick={() => void generateThemePlan()}
            disabled={readOnly || isGeneratingTheme || !brandName.trim()}
          >
            {isGeneratingTheme ? 'Generating…' : 'Generate with AI'}
          </Button>
          {isGeneratingTheme ? <Spinner size="tiny" /> : null}
          {!brandName.trim() ? <span style={{ opacity: 0.6, fontSize: '0.85rem' }}>Enter brand name first</span> : null}
        </div>

        {masterTheme ? (
          <div style={{ display: 'grid', gap: '1rem' }}>
            <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              <span style={{ fontWeight: 600 }}>Master theme</span>
              <Input
                aria-label="Master theme"
                value={masterTheme}
                onChange={(_, data) => setMasterTheme(data.value)}
                disabled={readOnly}
              />
            </label>
            {derivedThemes.length > 0 ? (
              <div>
                <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Derived themes ({derivedThemes.length})</div>
                <div style={{ display: 'grid', gap: '0.6rem' }}>
                  {derivedThemes.map((dt, idx) => (
                    <div key={idx} style={{ padding: '0.75rem', border: '1px solid var(--colorNeutralStroke2)', borderRadius: '10px', background: 'rgba(255,255,255,0.03)' }}>
                      <div style={{ fontWeight: 600 }}>{dt.title}</div>
                      {dt.description ? <div style={{ opacity: 0.75, fontSize: '0.85rem', marginTop: '0.2rem' }}>{dt.description}</div> : null}
                      {dt.frequency ? <div style={{ opacity: 0.5, fontSize: '0.78rem', marginTop: '0.2rem' }}>Frequency: {dt.frequency}</div> : null}
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        ) : (
          <div style={{ opacity: 0.6, fontSize: '0.9rem' }}>
            Fill in the brief above then click "Generate with AI" to create a tailored content strategy.
          </div>
        )}
      </div>
    </div>
  </div>
)}
```

**State variable names**: The names `brandName`, `setBrandName`, `location`, `setLocation`, `primaryLanguage`, `setPrimaryLanguage`, `timezone`, `setTimezone`, `offeringsText`, `setOfferingsText`, `businessContext`, `setBusinessContext`, `masterTheme`, `setMasterTheme`, `derivedThemes`, `isGeneratingTheme`, `generateThemePlan` may differ in the actual file. Read the file first (lines 100–280) and use the exact names you find.

**`Textarea` import**: Verify `Textarea` is imported from `@fluentui/react-components`. Add to the import if missing.

#### Acceptance criteria
- [ ] Step 4 renders business brief form with 6 fields
- [ ] "Generate with AI" button disabled when brand name is empty
- [ ] After generation (mocked in test), master theme input shows the generated value
- [ ] Derived themes render as cards below master theme
- [ ] `data-testid="dma-step-panel-theme"` present on step 4
- [ ] `npm run build` exits 0

---

### E1-S5: Step Panels — Confirm Schedule (Step 5) + Review & Activate (Step 6)

**Story size**: 60 min  
**Branch**: `feat/CP-STUDIO-3-dma-wizard-shell`  
**BLOCKED UNTIL**: E1-S4 committed  

#### Context
Step 5 captures posting schedule preferences. Step 6 shows a readiness summary and the Activate button. The `readiness` object (from the API response) drives the summary: `readiness.configured`, `readiness.brief_complete`, `readiness.youtube_connection_ready`, `readiness.can_finalize`, `readiness.missing_requirements`. Schedule state variables include `scheduleStartDate`, `schedulePostsPerWeek`, `schedulePreferredDays`, `schedulePreferredHours` (or similar names — verify in the file).

#### Files to read first (max 3)
1. `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` — lines 100–200 (find schedule state variables and `readiness` usage)

#### What to build

Replace placeholder div for step 5 with:

```tsx
{/* STEP 5 — Confirm Schedule */}
{currentStep.id === 'schedule' && (
  <div className="dma-wizard-step-content" data-testid="dma-step-panel-schedule">
    <div style={{ display: 'grid', gap: '1.25rem' }}>
      <div>
        <div className="dma-wizard-section-label">Posting schedule</div>
        <div className="dma-wizard-form-grid">
          <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <span>Start date</span>
            <Input
              type="date"
              aria-label="Start date"
              value={scheduleStartDate}
              onChange={(_, data) => setScheduleStartDate(data.value)}
              disabled={readOnly}
            />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <span>Posts per week</span>
            <Input
              type="number"
              aria-label="Posts per week"
              value={String(schedulePostsPerWeek ?? 3)}
              onChange={(_, data) => setSchedulePostsPerWeek(Number(data.value))}
              disabled={readOnly}
              min="1"
              max="21"
            />
          </label>
        </div>
      </div>

      <div>
        <div className="dma-wizard-section-label">Preferred days</div>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map((day) => {
            const isSelected = (schedulePreferredDays ?? []).includes(day)
            return (
              <button
                key={day}
                type="button"
                style={{
                  padding: '0.4rem 0.9rem',
                  borderRadius: '999px',
                  border: '1px solid var(--colorNeutralStroke2)',
                  background: isSelected ? 'rgba(0,242,254,0.1)' : 'rgba(255,255,255,0.03)',
                  borderColor: isSelected ? 'rgba(0,242,254,0.5)' : undefined,
                  color: 'inherit',
                  cursor: readOnly ? 'default' : 'pointer',
                  fontWeight: isSelected ? 700 : 400,
                }}
                onClick={() => {
                  if (readOnly) return
                  setSchedulePreferredDays((prev: string[]) =>
                    isSelected ? prev.filter((d: string) => d !== day) : [...(prev ?? []), day]
                  )
                }}
                aria-pressed={isSelected}
              >
                {day}
              </button>
            )
          })}
        </div>
      </div>

      {scheduleStartDate ? (
        <Badge appearance="outline" color="success">
          Schedule set: {schedulePostsPerWeek ?? 3}×/week from {scheduleStartDate}
        </Badge>
      ) : (
        <div style={{ opacity: 0.6, fontSize: '0.9rem' }}>Set a start date to confirm the schedule.</div>
      )}
    </div>
  </div>
)}
```

Replace placeholder div for step 6 with:

```tsx
{/* STEP 6 — Review & Activate */}
{currentStep.id === 'activate' && (
  <div className="dma-wizard-step-content" data-testid="dma-step-panel-activate">
    <div style={{ display: 'grid', gap: '1.5rem' }}>

      {/* Readiness checklist */}
      <div>
        <div className="dma-wizard-section-label">Activation readiness</div>
        <div style={{ border: '1px solid var(--colorNeutralStroke2)', borderRadius: '14px', overflow: 'hidden' }}>
          {[
            { label: 'Agent identity configured',   ok: readiness.configured },
            { label: 'Business brief complete',      ok: readiness.brief_complete },
            { label: 'Platform connections ready',   ok: !readiness.youtube_selected || readiness.youtube_connection_ready },
            { label: 'Campaign theme generated',     ok: Boolean(masterTheme) },
          ].map(({ label, ok }) => (
            <div key={label} className="dma-wizard-review-row" style={{ padding: '0.85rem 1rem' }}>
              <span>{label}</span>
              <Badge appearance="outline" color={ok ? 'success' : 'warning'}>
                {ok ? '✓ Ready' : 'Incomplete'}
              </Badge>
            </div>
          ))}
        </div>
      </div>

      {/* Missing requirements */}
      {readiness.missing_requirements?.length > 0 ? (
        <FeedbackMessage
          intent="warning"
          title="Complete these before activating"
          message={readiness.missing_requirements.join(' · ')}
        />
      ) : null}

      {/* Activation status */}
      {readiness.can_finalize ? (
        <div style={{ display: 'grid', gap: '0.6rem' }}>
          <div style={{ color: '#10b981', fontWeight: 600 }}>
            ✓ Agent is ready to activate
          </div>
          {readOnly ? (
            <Badge appearance="outline" color="informative">This hire has ended — activation workspace is read-only.</Badge>
          ) : null}
        </div>
      ) : (
        <div style={{ opacity: 0.7, fontSize: '0.9rem' }}>
          Complete the missing items above, then return to this step to activate.
        </div>
      )}

      {/* Save error */}
      {saveError ? <FeedbackMessage intent="error" title="Save failed" message={saveError} /> : null}
    </div>
  </div>
)}
```

**State variable names**: `scheduleStartDate`, `setScheduleStartDate`, `schedulePostsPerWeek`, `setSchedulePostsPerWeek`, `schedulePreferredDays`, `setSchedulePreferredDays` may be named differently. Read lines 100–200 of the component and use the exact names. If there is a single `schedule` object state, destructure from it.

**`masterTheme` in step 6**: Use the same variable name found in S4.

#### Acceptance criteria
- [ ] Step 5 renders start date field, posts-per-week input, and 7 day-of-week buttons
- [ ] Day buttons toggle on/off with cyan highlight
- [ ] Step 6 renders 4-row readiness checklist
- [ ] Rows show green badge when condition is met, amber when incomplete
- [ ] "Activate Agent" button in the action bar is enabled only when `readiness.can_finalize` is true
- [ ] `data-testid="dma-step-panel-schedule"` and `data-testid="dma-step-panel-activate"` present
- [ ] `npm run build` exits 0

---

### E1-S6: CSS Polish + Update Tests + Build Validation

**Story size**: 45 min  
**Branch**: `feat/CP-STUDIO-3-dma-wizard-shell`  
**BLOCKED UNTIL**: E1-S5 committed  

#### Context
S1–S5 built the wizard. This final story (a) updates the existing test file to match the new step-based structure, (b) resolves any remaining TypeScript errors, and (c) runs a production build to confirm zero errors.

The test file `MyAgentsDigitalMarketingWizard.test.tsx` currently tests milestone-based `data-testid` attributes (`dma-help-panel-primary`, milestone buttons, etc.). The new tests assert step navigation and per-step `data-testid` panels.

#### Files to read first (max 3)
1. `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` — full file (understand existing test structure)
2. `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` — first 80 lines (confirm props interface)

#### What to build

**A. Update tests** in `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx`.

Keep all existing mock setup (`vi.mock(...)` blocks). Replace or add test cases to cover:

```typescript
describe('DMA Activation Wizard — step navigation', () => {
  it('renders wizard shell with 6 step buttons', async () => {
    // mock getDigitalMarketingActivationWorkspace to return defaultWorkspace
    // render <DigitalMarketingActivationWizard hiredInstanceId="HAI-1" customerId="CUS-1" />
    // expect: 6 elements matching role="button" with step titles
    // expect: step 1 button has is-active class or "Now" text
  })

  it('starts on step 1 — Induct Agent panel visible', async () => {
    // render wizard
    // await: data-testid="dma-step-panel-induct" visible
    // expect: Nickname input present
  })

  it('Continue button advances to step 2', async () => {
    // render wizard
    // click "Continue" button
    // expect: data-testid="dma-step-panel-platforms" visible
  })

  it('Back button goes back from step 2 to step 1', async () => {
    // click Continue to reach step 2
    // click Back
    // expect: data-testid="dma-step-panel-induct" visible
  })

  it('Back button disabled on step 1', async () => {
    // render wizard
    // expect: Back button is disabled
  })

  it('Activate Agent button visible on step 6', async () => {
    // render wizard
    // click Continue 5 times to reach step 6
    // expect: button with text "Activate Agent" visible
  })
})
```

Implement these 6 test cases using the existing mock infrastructure in the file. Use `fireEvent.click` for button clicks and `waitFor` + `screen.findBy*` for async resolution.

**B. TypeScript errors**: run `cd src/CP/FrontEnd && npx tsc --noEmit 2>&1 | grep "error TS"` — fix any errors introduced by S1–S5 before committing.

**C. Production build**: run `cd src/CP/FrontEnd && npm run build 2>&1 | tail -20` — must exit 0.

**D. Run tests**: `cd src/CP/FrontEnd && npx vitest run src/test/MyAgentsDigitalMarketingWizard.test.tsx 2>&1 | tail -30` — all green.

#### Acceptance criteria
- [ ] 6 new step-navigation tests all pass (green in vitest)
- [ ] No TypeScript errors (`npx tsc --noEmit` exits 0)
- [ ] `npm run build` exits 0
- [ ] No existing passing tests have been broken

---

## PR Template

After all 6 stories pass, open the PR with:

```bash
git push -u origin feat/CP-STUDIO-3-dma-wizard-shell

gh pr create --base main \
  --title "feat(CP-STUDIO-3): DMA activation wizard — 6-step left-rail guided shell" \
  --body "## What
Rebuilds \`DigitalMarketingActivationWizard.tsx\` from a scrolling milestone-tab layout into a 6-step left-rail wizard (inspired by PP AgentSetupStudio). Each step focuses on one concern; Continue auto-saves to GCP SQL before advancing.

## Steps
1. Induct Agent — nickname + theme
2. Choose Platforms — channel selection tiles
3. Connect Platforms — OAuth/credential flow per selected channel
4. Build Master Theme — business brief + Grok AI generation
5. Confirm Schedule — posting frequency and preferred days
6. Review & Activate — readiness checklist + Activate button

## Backend changes
None. All backend, proxy and service layer were already complete.

## CSS
New \`dma-wizard-*\` classes added to \`src/CP/FrontEnd/src/styles/globals.css\`. Responsive breakpoint at 768px collapses to single-column.

## Tests
6 new step-navigation tests added to \`MyAgentsDigitalMarketingWizard.test.tsx\`. All existing tests preserved. Build exits 0.

CP-STUDIO-3"
```
