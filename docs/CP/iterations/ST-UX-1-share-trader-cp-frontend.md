# ST-UX-1 — Share Trader CP Web Portal UI/UX

> **Advances**: Share Trader value — web portal parity with mobile so paying customers can manage the full trading lifecycle from a browser.
> **Depends on**: ST-MVP-1 (PR #1090) must be merged before Iteration 1 launches — all API endpoints are provided by ST-MVP-1.

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `ST-UX-1` |
| Feature area | CP FrontEnd — Share Trader web UI (React 18 + TypeScript + Vite + FluentUI) |
| Created | 2026-06-28 |
| Author | GitHub Copilot (PM mode) |
| Backend plan | ST-MVP-1 `docs/CP/iterations/ST-MVP-1-share-trader-lifecycle.md` (PR #1090) |
| Platform index | `docs/CONTEXT_AND_INDEX.md` §4.3, §13 |
| Total iterations | 2 |
| Total epics | 3 |
| Total stories | 8 |
| Branch | `docs/ST-UX-1-share-trader-cp-frontend` |

---

## Zero-Cost Agent Constraints (READ FIRST)

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story is fully self-contained — no "see above" |
| No working memory | All patterns embedded inline in each card |
| Max 3 file reads per story | Pre-identified in "Files to read first" |
| Binary AC | Every acceptance criterion is pass/fail |

> **Agent:** One story at a time. Read the story card fully, then act. Do NOT open other story cards.

---

## Vision Intake Summary

- **Area**: CP FrontEnd (`src/CP/FrontEnd/src/`) — React 18, TypeScript, Vite, FluentUI components
- **Outcome**: A customer on the CP web portal configures Share Trader via a chat wizard, approves/rejects trade plans, views live trading performance, browses trade history, and downloads P&L tax reports — none of which exists on web today
- **Out of scope**: Mobile (ST-MVP-1), Plant/CP BackEnd (ST-MVP-1), PP Portal, DMA features, LLM wizard (Phase 2)
- **Lane**: Lane A — all endpoints provided by ST-MVP-1; this plan wires the React UI to those endpoints only
- **Dependency**: ST-MVP-1 must be merged to `main` before launching Iteration 1

---

## Existing Patterns (agent must follow these, not invent new ones)

| Pattern | Where it lives | Rule |
|---|---|---|
| API calls | `services/gatewayApiClient.ts` → `gatewayRequestJson<T>(path, init?)` | All HTTP calls go through this function |
| FluentUI components | `@fluentui/react-components` | Use `Card`, `Button`, `Badge`, `Spinner`, `TabList`, `Tab`, `Dialog` |
| Design tokens | `#0a0a0a` bg, `#18181b` card, `#00f2fe` cyan, `#10b981` green, `#ef4444` red, `#f59e0b` yellow | Never hard-code other colours |
| Trading agent detection | `isTradingOrExchangeAgent(agentId, agentTypeId)` in `MyAgents.tsx` | Already defined — import or copy inline |
| Loading state | `FeedbackMessage`, `LoadingIndicator` from `../../components/FeedbackIndicators` | Use these, not custom spinners |
| DMA panel pattern | `DigitalMarketingActivationWizard` in `MyAgents.tsx` | Share Trader panels follow the same conditional-render pattern |
| Sub-page navigation | Tab sections within `MyAgents.tsx` — no new page routes needed | All Share Trader panels render inside the existing authenticated shell |

---

## PM Review Checklist

- [x] Epic titles = customer outcomes
- [x] Stories have exact branch names
- [x] NFR patterns embedded inline (no external references)
- [x] Every story has max 3 files in "Files to read first"
- [x] All `gatewayRequestJson` calls use `/cp/` prefix routes from ST-MVP-1
- [x] All stories have `BLOCKED UNTIL`
- [x] BDD scenarios present for every customer-facing flow
- [x] Design tokens used throughout (no hardcoded colours outside the list above)
- [x] No placeholders remain

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Service layer + chat configure wizard + trade approvals | E1, E2 | 4 | 4h | 2026-06-29 12:00 UTC |
| 2 | Dashboard + history + tax report + navigation integration | E3 | 4 | 4h | 2026-06-29 20:00 UTC |

**Estimate basis:** New service file = 30 min | New component = 60 min | Portal integration = 45 min. Buffer: 20%.

---

## Integration Baseline Gate

> **Agent: run these before writing any code. Any 404 = HALT — ST-MVP-1 is not merged yet.**

```bash
# Trading setup endpoint exists (expects 401, NOT 404)
curl -sS -o /dev/null -w "%{http_code}\n" \
  https://cp.demo.waooaw.com/api/cp/trading-setup/test

# Trade performance endpoint exists (expects 401, NOT 404)
curl -sS -o /dev/null -w "%{http_code}\n" \
  https://cp.demo.waooaw.com/api/cp/trading/performance/test

# Trade history endpoint exists (expects 401, NOT 404)
curl -sS -o /dev/null -w "%{http_code}\n" \
  https://cp.demo.waooaw.com/api/cp/trading/history/test
```

**If any returns 404**: ST-MVP-1 (PR #1090) has not been deployed. Do not proceed — post `Blocked at baseline: ST-MVP-1 endpoints not deployed` and HALT.

---

## Agent Execution Rules

1. Work on the GitHub task branch for this run. Do not assume manual checkout.
2. Execute stories in stated order within each iteration.
3. Every story: write tests first (component tests with React Testing Library), then implementation.
4. Run `cd src/CP/FrontEnd && npm test -- --watchAll=false` (or equivalent) after each story.
5. After all iteration stories: open PR to `main` with title `feat(share-trader): ST-UX-1 Iteration N — [scope]`.
6. Post PR URL and HALT.

**STUCK PROTOCOL**: Blocked > 15 min → post `STUCK: [story ID] — [exact blocker]` and move to next story.

**EXECUTION AGENT AUDIT ROUND**: Before submitting PR, re-read each story's acceptance criteria and post ✓/✗ per criterion in the PR body.

---

## How to Launch Each Iteration

### Iteration 1

> ⚠️ ST-MVP-1 (PR #1090) must be merged to `main` first. Verify baseline gate before launching.

**Steps:**
1. Open https://github.com/dlai-sd/WAOOAW → **Agents** tab
2. Start new agent task; select **platform-engineer** if shown
3. Paste task block below and start run
4. Come back at **2026-06-29 12:00 UTC**

**Iteration 1 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React 18/TypeScript engineer with FluentUI experience + Senior UI/UX engineer with dark-theme design system expertise.
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/ST-UX-1-share-trader-cp-frontend.md
YOUR SCOPE: Iteration 1 only — Epics E1 and E2 (Stories S1–S4). Do NOT touch Iteration 2 content.
TIME BUDGET: 4h. If you reach 5h without finishing, follow STUCK PROTOCOL now.

PREREQUISITE CHECK (do this before any code change):
1. Verify ST-MVP-1 endpoints exist using the Integration Baseline Gate curls in the plan.
2. If any baseline curl returns 404, post "Blocked at baseline: ST-MVP-1 not deployed" and HALT.

FAIL-FAST VALIDATION GATE:
1. Verify plan file is readable and contains "Iteration 1" section.
2. Verify this surface allows repository writes on the task branch.
3. Verify a PR to `main` can be opened.
4. If any gate fails: post "Blocked at validation gate: [reason]" and HALT.

EXECUTION ORDER:
1. Read "Agent Execution Rules" in this plan file.
2. Read "Iteration 1" section only.
3. Read nothing else before starting.
4. Execute: E1-S1 → E1-S2 → E2-S3 → E2-S4
5. Write component tests before implementation for each story.
6. Run `cd src/CP/FrontEnd && npm test -- --watchAll=false` after each story.
7. Open PR to `main` titled "feat(share-trader): ST-UX-1 It1 — service layer + configure chat + approvals"
8. Post PR URL and HALT.
```

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Prerequisite evidence:**
- Iteration 1 PR: `[PENDING — fill after merge]`
- Merge commit: `[PENDING]`

**Steps:** Same as Iteration 1. Come back at **2026-06-29 20:00 UTC**.

**Iteration 2 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React 18/TypeScript engineer with data-table and CSV-export experience + Senior UI/UX engineer specialising in financial dashboards.
Activate these personas NOW.

PLAN FILE: docs/CP/iterations/ST-UX-1-share-trader-cp-frontend.md
YOUR SCOPE: Iteration 2 only — Epic E3 (Stories S5–S8). Do NOT touch Iteration 1 content.
TIME BUDGET: 4h. Follow STUCK PROTOCOL if you reach 5h.

PREREQUISITE CHECK:
1. Verify `TradingSetupChatPanel.tsx` exists in `src/CP/FrontEnd/src/components/`.
2. Verify `tradingSetup.service.ts` exists in `src/CP/FrontEnd/src/services/`.
3. If either is missing, post "Blocked at prerequisite: Iteration 1 not merged" and HALT.

FAIL-FAST VALIDATION GATE: Same as Iteration 1.

EXECUTION ORDER:
1. Read "Agent Execution Rules" in this plan file.
2. Read "Iteration 2" section only.
3. Execute: E3-S5 → E3-S6 → E3-S7 → E3-S8
4. Write tests before implementation for each story.
5. Open PR to `main` titled "feat(share-trader): ST-UX-1 It2 — dashboard + history + tax report"
6. Post PR URL and HALT.
```

---

---

# Iteration 1 — Service Layer + Chat Configure Wizard + Trade Approvals

**Objective alignment**: Share Trader value — the service layer and chat wizard unlock the full web configuration lifecycle; the approval panel lets web users action trade plans without needing the mobile app.

---

## Epic E1: Share Trader API Service Layer Ready for All Web Panels

---

### S1 — `tradingSetup.service.ts` — all new ST-MVP-1 trading endpoints wired

**Advances**: Share Trader enablement (unlocks all subsequent UI stories in this plan)
**Branch**: `feat/ST-UX-1-s1-trading-service`
**Estimate**: 30 min
**BLOCKED UNTIL**: ST-MVP-1 merged to main

**Context** (2 sentences):
The CP FrontEnd already has `trading.service.ts` (draft/approve) and `tradingStrategy.service.ts` (interval config) but has no service for the ST-MVP-1 chat wizard, emergency stop, trade history, tax report, or recommendations endpoints. This story creates `tradingSetup.service.ts` which all subsequent stories import.

**Files to read first** (max 3):
1. `src/CP/FrontEnd/src/services/trading.service.ts` — exact `gatewayRequestJson` import pattern
2. `src/CP/FrontEnd/src/services/tradingStrategy.service.ts` — type definition pattern
3. `src/CP/FrontEnd/src/services/gatewayApiClient.ts` — confirm `gatewayRequestJson` signature

**Files to create / edit**:
- `src/CP/FrontEnd/src/services/tradingSetup.service.ts` — new file with 7 functions
- `src/CP/FrontEnd/src/__tests__/tradingSetup.service.test.ts` — new test file

**Acceptance criteria**:
1. `getTradingSetup(hiredInstanceId)` calls `GET /cp/trading-setup/{id}` and returns typed response.
2. `sendTradingSetupMessage(hiredInstanceId, content)` calls `POST /cp/trading-setup/{id}/message`.
3. `emergencyStop(hiredInstanceId)` calls `POST /cp/trading-setup/{id}/emergency-stop`.
4. `getTradePerformance(hiredInstanceId, periodDays?)` calls `GET /cp/trading/performance/{id}`.
5. `getTradeHistory(hiredInstanceId, page?, pageSize?)` calls `GET /cp/trading/history/{id}`.
6. `getTaxReport(hiredInstanceId, year, period, month?, quarter?)` calls `GET /cp/trading/tax-report/{id}`.
7. `getRecommendations(hiredInstanceId)` calls `GET /cp/trading/recommendations/{id}`.
8. All 7 functions have TypeScript return types — no `any`.

**Code patterns to copy exactly**:

```typescript
// src/CP/FrontEnd/src/services/tradingSetup.service.ts
import { gatewayRequestJson } from './gatewayApiClient'

// ── Types ─────────────────────────────────────────────────────────────────

export type TradingSetupMessage = {
  role: 'assistant' | 'user'
  content: string
  masked: boolean
}

export type TradingSetupReadiness = {
  configured: boolean
  step: string
  has_credentials: boolean
  credentials_valid: boolean
  has_instrument: boolean
  has_rsi_period: boolean
  has_risk_limits: boolean
}

export type TradingSetupState = {
  step: string
  messages: TradingSetupMessage[]
  collected: Record<string, unknown>
  validation_status: 'pending' | 'valid' | 'invalid'
  configured: boolean
}

export type TradingSetupResponse = {
  hired_instance_id: string
  state: TradingSetupState
  readiness: TradingSetupReadiness
}

export type TradePerformanceSummary = {
  hired_instance_id: string
  period_days: number
  trades_count: number
  pnl_pct_avg: number
  win_rate: number
  stop_loss_count: number
  profit_count: number
  last_stat_date: string | null
}

export type TradeHistoryRow = {
  stat_date: string
  skill_id: string
  trades_count: number
  pnl_pct_avg: number
  win_rate: number
  stop_loss_count: number
}

export type TradeHistoryResponse = {
  hired_instance_id: string
  trades: TradeHistoryRow[]
  total: number
  page: number
  page_size: number
}

export type TaxReportEntry = {
  date: string
  skill_id: string
  trades_count: number
  pnl_pct: number
  win_rate: number
  stop_loss_count: number
}

export type TaxReportResponse = {
  hired_instance_id: string
  period: string
  year: number
  total_trades: number
  total_pnl_pct: number
  profitable_trades: number
  loss_trades: number
  stop_loss_exits: number
  trades: TaxReportEntry[]
}

export type TradeRecommendation = {
  hired_instance_id: string
  current_rsi_buy_threshold: number
  current_rsi_sell_threshold: number
  suggested_rsi_buy_threshold: number
  suggested_rsi_sell_threshold: number
  confidence: number
  rationale: string
  sample_size: number
  engine: string
}

// ── API functions ──────────────────────────────────────────────────────────

export async function getTradingSetup(hiredInstanceId: string): Promise<TradingSetupResponse> {
  return gatewayRequestJson<TradingSetupResponse>(
    `/cp/trading-setup/${encodeURIComponent(hiredInstanceId)}`
  )
}

export async function sendTradingSetupMessage(
  hiredInstanceId: string,
  content: string
): Promise<TradingSetupResponse> {
  return gatewayRequestJson<TradingSetupResponse>(
    `/cp/trading-setup/${encodeURIComponent(hiredInstanceId)}/message`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }) }
  )
}

export async function emergencyStop(hiredInstanceId: string): Promise<{ status: string; stopped_at: string }> {
  return gatewayRequestJson<{ status: string; stopped_at: string }>(
    `/cp/trading-setup/${encodeURIComponent(hiredInstanceId)}/emergency-stop`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }
  )
}

export async function getTradePerformance(
  hiredInstanceId: string,
  periodDays = 90
): Promise<TradePerformanceSummary> {
  return gatewayRequestJson<TradePerformanceSummary>(
    `/cp/trading/performance/${encodeURIComponent(hiredInstanceId)}?period_days=${periodDays}`
  )
}

export async function getTradeHistory(
  hiredInstanceId: string,
  page = 1,
  pageSize = 20
): Promise<TradeHistoryResponse> {
  return gatewayRequestJson<TradeHistoryResponse>(
    `/cp/trading/history/${encodeURIComponent(hiredInstanceId)}?page=${page}&page_size=${pageSize}`
  )
}

export async function getTaxReport(
  hiredInstanceId: string,
  year: number,
  period: 'monthly' | 'quarterly',
  month?: number,
  quarter?: string
): Promise<TaxReportResponse> {
  const qs = new URLSearchParams({ year: String(year), period })
  if (period === 'monthly' && month != null) qs.append('month', String(month))
  if (period === 'quarterly' && quarter) qs.append('quarter', quarter)
  return gatewayRequestJson<TaxReportResponse>(
    `/cp/trading/tax-report/${encodeURIComponent(hiredInstanceId)}?${qs}`
  )
}

export async function getRecommendations(hiredInstanceId: string): Promise<TradeRecommendation> {
  return gatewayRequestJson<TradeRecommendation>(
    `/cp/trading/recommendations/${encodeURIComponent(hiredInstanceId)}`
  )
}
```

**Test table**:

| # | Type | Description | File |
|---|---|---|---|
| T1 | Unit | `getTradingSetup` calls correct path | `__tests__/tradingSetup.service.test.ts` |
| T2 | Unit | `sendTradingSetupMessage` sends POST with `{content}` body | `__tests__/tradingSetup.service.test.ts` |
| T3 | Unit | `emergencyStop` sends POST to `/emergency-stop` | `__tests__/tradingSetup.service.test.ts` |
| T4 | Unit | `getTaxReport` with monthly+month builds correct query string | `__tests__/tradingSetup.service.test.ts` |

---

### S2 — `TradingSetupChatPanel.tsx` — chat wizard UI for the 10-step configuration flow

**Advances**: Share Trader value (customer configures agent from browser for the first time)
**Branch**: `feat/ST-UX-1-s2-chat-panel`
**Estimate**: 60 min
**BLOCKED UNTIL**: S1 merged

**Context** (2 sentences):
The mobile `TradingSetupScreen.tsx` is the reference UX — same 10-step flow, same step labels, same masked input for api_key/api_secret. This component renders in the web portal using FluentUI and the WAOOAW dark design system, not React Native primitives.

**Files to read first** (max 3):
1. `src/CP/FrontEnd/src/services/tradingSetup.service.ts` — just created; all API types
2. `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` — existing chat-style component for pattern reference
3. `src/CP/FrontEnd/src/components/FeedbackIndicators.tsx` — `LoadingIndicator`, `FeedbackMessage`

**Files to create / edit**:
- `src/CP/FrontEnd/src/components/TradingSetupChatPanel.tsx` — new component
- `src/CP/FrontEnd/src/__tests__/TradingSetupChatPanel.test.tsx` — new test file

**Acceptance criteria**:
1. Renders chat bubble list from `state.messages`; assistant bubbles left-aligned, user bubbles right-aligned.
2. Sensitive steps (`api_key`, `api_secret`) show `<input type="password">` and display a green `🔒 Secure Input` badge above the input bar.
3. Step progress label displays current step (e.g. "Step 1 of 10 — API Key").
4. Send button (or Enter key) calls `sendTradingSetupMessage` and re-renders updated message list.
5. Spinner shown while `sending` is true; input disabled during send.
6. On `step === "done"`: input bar hidden; red `🛑 Emergency Stop` button visible with confirmation dialog before calling `emergencyStop()`.
7. Error state shown with `FeedbackMessage` when API call fails.
8. Auto-scrolls to latest message after each send.
9. All WAOOAW design tokens used (no inline hex outside the canonical list).

**Code patterns to copy exactly**:

```typescript
// src/CP/FrontEnd/src/components/TradingSetupChatPanel.tsx
import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Badge, Button, Card, Dialog, DialogActions, DialogBody,
  DialogContent, DialogSurface, DialogTitle, Spinner,
} from '@fluentui/react-components'
import { FeedbackMessage } from './FeedbackIndicators'
import {
  getTradingSetup, sendTradingSetupMessage, emergencyStop,
  type TradingSetupMessage, type TradingSetupResponse,
} from '../services/tradingSetup.service'

// Design tokens — never use other hex values
const COLOURS = {
  bg: '#0a0a0a',
  card: '#18181b',
  cyan: '#00f2fe',
  green: '#10b981',
  red: '#ef4444',
  yellow: '#f59e0b',
  textPrimary: '#f4f4f5',
  textSecondary: '#71717a',
  border: '#27272a',
}

const SECURE_STEPS = new Set(['api_key', 'api_secret'])

const STEP_LABEL: Record<string, string> = {
  welcome: 'Welcome',
  api_key: 'Step 1 of 10 — API Key',
  api_secret: 'Step 2 of 10 — API Secret',
  validate: 'Step 3 of 10 — Validating…',
  instrument: 'Step 4 of 10 — Instrument',
  rsi_period: 'Step 5 of 10 — RSI Period',
  risk_limits: 'Step 6 of 10 — Risk Limits',
  capital_pct: 'Step 7 of 10 — Capital Deployment',
  leverage: 'Step 8 of 10 — Leverage',
  autonomous_mode: 'Step 9 of 10 — Autonomous Mode',
  risk_disclosure: 'Step 10 of 10 — Risk Disclosure',
  done: 'Setup Complete ✅',
}

interface Props {
  hiredInstanceId: string
}

export function TradingSetupChatPanel({ hiredInstanceId }: Props) {
  const [messages, setMessages] = useState<TradingSetupMessage[]>([])
  const [step, setStep] = useState('welcome')
  const [inputText, setInputText] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [stopDialogOpen, setStopDialogOpen] = useState(false)
  const [stopping, setStopping] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  const isSecure = SECURE_STEPS.has(step)

  useEffect(() => {
    getTradingSetup(hiredInstanceId)
      .then((resp: TradingSetupResponse) => {
        setMessages(resp.state.messages)
        setStep(resp.state.step)
      })
      .catch(() => setError('Failed to load trading setup.'))
      .finally(() => setLoading(false))
  }, [hiredInstanceId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = useCallback(async () => {
    const text = inputText.trim()
    if (!text || sending) return
    setInputText('')
    setSending(true)
    setError(null)
    try {
      const resp = await sendTradingSetupMessage(hiredInstanceId, text)
      setMessages(resp.state.messages)
      setStep(resp.state.step)
    } catch {
      setError('Failed to send. Please try again.')
    } finally {
      setSending(false)
    }
  }, [hiredInstanceId, inputText, sending])

  const handleEmergencyStop = async () => {
    setStopping(true)
    try {
      await emergencyStop(hiredInstanceId)
      setStopDialogOpen(false)
      setError(null)
    } catch {
      setError('Emergency stop failed. Please try again.')
    } finally {
      setStopping(false)
    }
  }

  if (loading) return <Spinner label="Loading trading setup…" />
  if (error) return <FeedbackMessage type="error" message={error} />

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 8 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 0' }}>
        <div>
          <span style={{ color: COLOURS.textPrimary, fontWeight: 600 }}>⚙️ Configure Trading</span>
          <span style={{ color: COLOURS.textSecondary, fontSize: 12, marginLeft: 12 }}>
            {STEP_LABEL[step] ?? step}
          </span>
        </div>
        {isSecure && (
          <Badge appearance="tint" color="success" size="small">🔒 Secure Input</Badge>
        )}
      </div>

      {/* Autonomous mode warning */}
      {step === 'autonomous_mode' && (
        <div style={{ background: `${COLOURS.yellow}18`, border: `1px solid ${COLOURS.yellow}55`,
          borderRadius: 8, padding: '8px 12px', fontSize: 12, color: COLOURS.yellow }}>
          ⚠️ Autonomous mode: trades will execute without approval. You will be notified after each.
        </div>
      )}

      {/* Message list */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 8, padding: '4px 0' }}>
        {messages.map((msg, i) => (
          <div key={i} style={{
            alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: '80%',
            background: msg.role === 'user'
              ? (msg.masked ? `${COLOURS.green}18` : `${COLOURS.cyan}18`)
              : COLOURS.card,
            border: `1px solid ${msg.role === 'user' ? (msg.masked ? `${COLOURS.green}55` : `${COLOURS.cyan}55`) : COLOURS.border}`,
            borderRadius: 12, padding: '8px 12px',
          }}>
            {msg.masked && (
              <div style={{ color: COLOURS.green, fontSize: 10, marginBottom: 4, fontWeight: 600 }}>
                🔒 Encrypted
              </div>
            )}
            <p style={{ color: COLOURS.textPrimary, fontSize: 14, margin: 0, whiteSpace: 'pre-wrap' }}>
              {msg.content}
            </p>
          </div>
        ))}
        {sending && <Spinner size="tiny" style={{ alignSelf: 'flex-start', margin: '4px 0' }} />}
        <div ref={bottomRef} />
      </div>

      {/* Input bar — hidden on done step */}
      {step !== 'done' && (
        <div style={{ display: 'flex', gap: 8, borderTop: `1px solid ${COLOURS.border}`, paddingTop: 8 }}>
          {isSecure && (
            <div style={{ fontSize: 11, color: COLOURS.green, width: '100%', marginBottom: 4 }}>
              🔒 Your input is masked and encrypted
            </div>
          )}
          <input
            type={isSecure ? 'password' : 'text'}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            disabled={sending}
            placeholder={isSecure ? 'Enter securely…' : 'Type your reply…'}
            data-testid="trading-chat-input"
            style={{
              flex: 1, background: COLOURS.card, border: `1px solid ${COLOURS.border}`,
              borderRadius: 8, padding: '8px 12px', color: COLOURS.textPrimary,
              fontSize: 14, outline: 'none',
            }}
          />
          <Button
            appearance="primary"
            onClick={handleSend}
            disabled={sending || !inputText.trim()}
            data-testid="trading-chat-send"
          >
            Send
          </Button>
        </div>
      )}

      {/* Done step: Emergency Stop */}
      {step === 'done' && (
        <>
          <Button
            appearance="subtle"
            onClick={() => setStopDialogOpen(true)}
            data-testid="emergency-stop-btn"
            style={{ borderColor: `${COLOURS.red}55`, color: COLOURS.red, alignSelf: 'flex-start' }}
          >
            🛑 Emergency Stop
          </Button>
          <Dialog open={stopDialogOpen} onOpenChange={(_, d) => setStopDialogOpen(d.open)}>
            <DialogSurface style={{ background: COLOURS.card }}>
              <DialogBody>
                <DialogTitle style={{ color: COLOURS.red }}>⚠️ Confirm Emergency Stop</DialogTitle>
                <DialogContent style={{ color: COLOURS.textSecondary }}>
                  This will halt all trading immediately and pause your agent. Are you sure?
                </DialogContent>
                <DialogActions>
                  <Button appearance="subtle" onClick={() => setStopDialogOpen(false)}>Cancel</Button>
                  <Button
                    appearance="primary"
                    onClick={handleEmergencyStop}
                    disabled={stopping}
                    style={{ background: COLOURS.red }}
                    data-testid="emergency-stop-confirm"
                  >
                    {stopping ? <Spinner size="tiny" /> : 'Yes, stop trading'}
                  </Button>
                </DialogActions>
              </DialogBody>
            </DialogSurface>
          </Dialog>
        </>
      )}
    </div>
  )
}
```

**Test table**:

| # | Type | Description | File |
|---|---|---|---|
| T1 | Unit | Renders message list from loaded state | `__tests__/TradingSetupChatPanel.test.tsx` |
| T2 | Unit | `api_key` step shows password input and secure badge | `__tests__/TradingSetupChatPanel.test.tsx` |
| T3 | Unit | Send button calls `sendTradingSetupMessage` with input text | `__tests__/TradingSetupChatPanel.test.tsx` |
| T4 | Unit | Done step hides input bar and shows emergency stop button | `__tests__/TradingSetupChatPanel.test.tsx` |
| T5 | Unit | Emergency stop confirm button calls `emergencyStop()` | `__tests__/TradingSetupChatPanel.test.tsx` |
| T6 | BDD | Full configure: 10 sends advance steps; done step reached | `__tests__/TradingSetupChatPanel.test.tsx` |

**BDD scenario**:
```
Given a Share Trader agent in the configure state
When the customer opens the web portal Configure tab
Then they see the chat wizard at current step
When they send "start"
Then the next assistant message appears
When they reach step api_key
Then the input field is type="password"
And a green "🔒 Secure Input" badge is visible
When setup reaches "done"
Then the input bar disappears
And the "🛑 Emergency Stop" button is visible
```

---

## Epic E2: Customer Reviews and Actions Trade Plans on Web

---

### S3 — Integrate TradingSetupChatPanel into MyAgents.tsx Configure section

**Advances**: Share Trader value (web customers can configure without leaving the portal)
**Branch**: `feat/ST-UX-1-s3-myagents-trading-section`
**Estimate**: 60 min
**BLOCKED UNTIL**: S2 merged

**Context** (2 sentences):
`MyAgents.tsx` already detects trading agents via `isTradingOrExchangeAgent()` (line ~412) and renders an exchange credentials form for them. This story replaces that form with `TradingSetupChatPanel` and adds a readiness status card showing configuration completeness with a CTA — mirroring how the DMA agent shows `DigitalMarketingActivationWizard`.

**Files to read first** (max 3):
1. `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` — lines 405–450 (the `isTradingOrExchangeAgent` conditional block)
2. `src/CP/FrontEnd/src/components/TradingSetupChatPanel.tsx` — just created
3. `src/CP/FrontEnd/src/services/tradingSetup.service.ts` — `TradingSetupReadiness` type

**Files to create / edit**:
- `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` — replace exchange form with `TradingSetupChatPanel` for trading agents
- `src/CP/FrontEnd/src/components/TradingReadinessCard.tsx` — new: compact status card
- `src/CP/FrontEnd/src/__tests__/TradingReadinessCard.test.tsx` — new test

**Acceptance criteria**:
1. When `isTradingOrExchangeAgent()` is true, `MyAgents.tsx` renders `TradingSetupChatPanel` and NOT the generic exchange setup form.
2. `TradingReadinessCard` shows five status indicators: Credentials ✓/✗, Validated ✓/✗, Instrument ✓/✗, RSI period ✓/✗, Risk limits ✓/✗.
3. When all readiness checks pass (`readiness.configured === true`), card shows green banner: "✅ Agent is configured and ready to trade."
4. When `configured === false`, card shows "Complete setup →" CTA that scrolls to the chat panel.
5. `TradingReadinessCard` appears above the chat panel in the Configure tab.
6. DMA agents are unaffected — `DigitalMarketingActivationWizard` still renders for DMA.

**Code patterns to copy exactly**:

```typescript
// TradingReadinessCard.tsx — compact status indicator
import { Badge, Card } from '@fluentui/react-components'
import type { TradingSetupReadiness } from '../services/tradingSetup.service'

interface Props {
  readiness: TradingSetupReadiness
  onConfigureCta?: () => void
}

const CHECK_ITEMS: Array<{ key: keyof TradingSetupReadiness; label: string }> = [
  { key: 'has_credentials', label: 'Credentials entered' },
  { key: 'credentials_valid', label: 'Credentials validated' },
  { key: 'has_instrument', label: 'Instrument selected' },
  { key: 'has_rsi_period', label: 'RSI period set' },
  { key: 'has_risk_limits', label: 'Risk limits set' },
]

export function TradingReadinessCard({ readiness, onConfigureCta }: Props) {
  const allReady = readiness.configured
  return (
    <Card style={{ background: '#18181b', border: `1px solid ${allReady ? '#10b98155' : '#27272a'}`,
      borderRadius: 12, padding: 16, marginBottom: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ color: '#f4f4f5', fontWeight: 600, fontSize: 14 }}>Configuration Readiness</span>
        {allReady
          ? <Badge appearance="filled" color="success">✅ Ready to trade</Badge>
          : <button onClick={onConfigureCta} style={{ color: '#00f2fe', background: 'none',
              border: '1px solid #00f2fe55', borderRadius: 6, padding: '4px 10px',
              fontSize: 12, cursor: 'pointer' }}>Complete setup →</button>
        }
      </div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {CHECK_ITEMS.map(({ key, label }) => (
          <Badge
            key={key}
            appearance="tint"
            color={readiness[key] ? 'success' : 'danger'}
            size="small"
            data-testid={`readiness-${key}`}
          >
            {readiness[key] ? '✓' : '✗'} {label}
          </Badge>
        ))}
      </div>
    </Card>
  )
}

// In MyAgents.tsx — replace the isTradingOrExchangeAgent block with:
// (Find the block around line 412 and replace the exchange setup form content)
import { TradingSetupChatPanel } from '../../components/TradingSetupChatPanel'
import { TradingReadinessCard } from '../../components/TradingReadinessCard'
import { getTradingSetup } from '../../services/tradingSetup.service'

// Inside the trading agent section conditional:
{isTradingAgent && (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
    {tradingReadiness && (
      <TradingReadinessCard
        readiness={tradingReadiness}
        onConfigureCta={() => chatPanelRef.current?.scrollIntoView({ behavior: 'smooth' })}
      />
    )}
    <div ref={chatPanelRef} style={{ minHeight: 400 }}>
      <TradingSetupChatPanel hiredInstanceId={instance.hired_instance_id} />
    </div>
  </div>
)}
```

**Test table**:

| # | Type | Description | File |
|---|---|---|---|
| T1 | Unit | Trading agent renders `TradingSetupChatPanel`, not exchange form | `test/MyAgents.test.tsx` |
| T2 | Unit | DMA agent still renders `DigitalMarketingActivationWizard` | `test/MyAgents.test.tsx` |
| T3 | Unit | All 5 readiness badges render with correct ✓/✗ state | `__tests__/TradingReadinessCard.test.tsx` |
| T4 | Unit | "Complete setup →" CTA hidden when `configured === true` | `__tests__/TradingReadinessCard.test.tsx` |

---

### S4 — `TradingApprovalPanel.tsx` — trade plan approval queue on web

**Advances**: Share Trader value (customers approve/reject trades from browser without mobile app)
**Branch**: `feat/ST-UX-1-s4-approval-panel`
**Estimate**: 60 min
**BLOCKED UNTIL**: S3 merged

**Context** (2 sentences):
The existing `listHiredAgentDeliverables` and `reviewHiredAgentDeliverable` services (already used in `MyAgents.tsx` for DMA approvals) provide the trade plan queue — we just need a trading-specific approval card that shows instrument, direction, stop-loss price, take-profit price, and risk. This panel will be embedded in a new "Approvals" tab within the trading agent section of `MyAgents.tsx`.

**Files to read first** (max 3):
1. `src/CP/FrontEnd/src/services/hiredAgentDeliverables.service.ts` — `listHiredAgentDeliverables`, `reviewHiredAgentDeliverable`, `Deliverable` type
2. `src/CP/FrontEnd/src/components/DigitalMarketingApprovalCard.tsx` — existing approval card pattern
3. `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` — how DMA approval is rendered (search for `DigitalMarketingApprovalCard`)

**Files to create / edit**:
- `src/CP/FrontEnd/src/components/TradingApprovalCard.tsx` — single trade plan card
- `src/CP/FrontEnd/src/components/TradingApprovalPanel.tsx` — list of pending trade approvals
- `src/CP/FrontEnd/src/__tests__/TradingApprovalPanel.test.tsx` — new test file

**Acceptance criteria**:
1. `TradingApprovalPanel` calls `listHiredAgentDeliverables(hiredInstanceId)` and filters for `status === "pending"`.
2. Each card shows: instrument symbol, BUY/SELL chip (green/red), units, stop-loss price, take-profit price, risk rating badge.
3. Approve button calls `reviewHiredAgentDeliverable(deliverableId, "approved")` and removes card from list.
4. Reject button calls `reviewHiredAgentDeliverable(deliverableId, "rejected")` and removes card from list.
5. Each button shows a spinner while the API call is in progress.
6. Empty state message: "No pending trade approvals — your agent will notify you when a signal fires."
7. Signal age warning shown if deliverable `created_at` is > 15 minutes old: "⚠️ Signal is 18 min old — market may have moved."

**Code patterns to copy exactly**:

```typescript
// TradingApprovalCard.tsx
import { Badge, Button, Card, Spinner } from '@fluentui/react-components'
import { useState } from 'react'
import { reviewHiredAgentDeliverable, type Deliverable } from '../services/hiredAgentDeliverables.service'

interface Props {
  deliverable: Deliverable
  onActionComplete: (id: string) => void
}

function signalAgeMinutes(createdAt: string): number {
  return Math.floor((Date.now() - new Date(createdAt).getTime()) / 60000)
}

export function TradingApprovalCard({ deliverable, onActionComplete }: Props) {
  const [acting, setActing] = useState<'approving' | 'rejecting' | null>(null)
  const payload = (deliverable.payload ?? {}) as Record<string, unknown>
  const action = String(payload.side ?? payload.action ?? '').toUpperCase()
  const isBuy = action === 'LONG' || action === 'BUY' || action === 'ENTER'
  const ageMin = signalAgeMinutes(deliverable.created_at ?? '')

  const handle = async (decision: 'approved' | 'rejected') => {
    setActing(decision === 'approved' ? 'approving' : 'rejecting')
    try {
      await reviewHiredAgentDeliverable(deliverable.id, decision)
      onActionComplete(deliverable.id)
    } finally {
      setActing(null)
    }
  }

  return (
    <Card style={{ background: '#18181b', border: '1px solid #27272a', borderRadius: 12, padding: 16 }}
      data-testid={`trade-approval-card-${deliverable.id}`}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ color: '#f4f4f5', fontWeight: 700, fontSize: 16 }}>
          {String(payload.coin ?? payload.symbol ?? '—')}
        </span>
        <Badge appearance="filled" color={isBuy ? 'success' : 'danger'} size="medium">
          {isBuy ? 'BUY' : 'SELL'}
        </Badge>
      </div>
      {ageMin > 15 && (
        <div style={{ color: '#f59e0b', fontSize: 12, marginBottom: 8 }}>
          ⚠️ Signal is {ageMin} min old — market may have moved
        </div>
      )}
      <div style={{ display: 'flex', gap: 16, fontSize: 13, color: '#a1a1aa', marginBottom: 16 }}>
        {payload.units != null && <span>Qty: <strong style={{ color: '#f4f4f5' }}>{String(payload.units)}</strong></span>}
        {payload.stop_loss_price != null && <span>SL: <strong style={{ color: '#ef4444' }}>₹{Number(payload.stop_loss_price).toLocaleString('en-IN')}</strong></span>}
        {payload.take_profit_price != null && <span>TP: <strong style={{ color: '#10b981' }}>₹{Number(payload.take_profit_price).toLocaleString('en-IN')}</strong></span>}
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <Button
          appearance="primary"
          onClick={() => handle('approved')}
          disabled={acting !== null}
          data-testid={`approve-btn-${deliverable.id}`}
          style={{ background: '#10b981' }}
        >
          {acting === 'approving' ? <Spinner size="tiny" /> : '✓ Approve'}
        </Button>
        <Button
          appearance="subtle"
          onClick={() => handle('rejected')}
          disabled={acting !== null}
          data-testid={`reject-btn-${deliverable.id}`}
          style={{ borderColor: '#ef444455', color: '#ef4444' }}
        >
          {acting === 'rejecting' ? <Spinner size="tiny" /> : '✗ Reject'}
        </Button>
      </div>
    </Card>
  )
}
```

**Test table**:

| # | Type | Description | File |
|---|---|---|---|
| T1 | Unit | Pending deliverables render as TradingApprovalCard list | `__tests__/TradingApprovalPanel.test.tsx` |
| T2 | Unit | Empty state renders when no pending deliverables | `__tests__/TradingApprovalPanel.test.tsx` |
| T3 | Unit | Approve button calls `reviewHiredAgentDeliverable` with "approved" | `__tests__/TradingApprovalPanel.test.tsx` |
| T4 | Unit | Signal age warning shown when created_at > 15 min ago | `__tests__/TradingApprovalPanel.test.tsx` |

**BDD scenario**:
```
Given a Share Trader agent with one pending trade deliverable
When customer opens the Approvals tab
Then one TradingApprovalCard is visible with instrument, BUY/SELL, SL price, TP price
When customer clicks Approve
Then the card disappears from the list
And the empty state message appears
```

---

---

# Iteration 2 — Dashboard + Trade History + Tax Reports + Navigation Integration

**Objective alignment**: Share Trader value — these 4 stories close the review and reporting lifecycle on web, giving a paying customer the full performance view and tax-ready records they need to trust and renew the subscription.

---

## Epic E3: Customer Reviews Performance, History and Tax Reports on Web

---

### S5 — `TradingDashboardPanel.tsx` — live performance + RSI recommendations

**Advances**: Share Trader value (customer sees proof of agent value — required for subscription renewal)
**Branch**: `feat/ST-UX-1-s5-dashboard-panel`
**Estimate**: 60 min
**BLOCKED UNTIL**: Iteration 1 merged to main

**Context** (2 sentences):
The existing `TradePerformanceCard.tsx` (mobile) is the reference design. The web version adds RSI threshold recommendations from `getRecommendations()` and a 30-day performance summary cards row, all using FluentUI and the WAOOAW dark design system.

**Files to read first** (max 3):
1. `src/CP/FrontEnd/src/services/tradingSetup.service.ts` — `TradePerformanceSummary` and `TradeRecommendation` types
2. `src/CP/FrontEnd/src/services/performanceStats.service.ts` — existing stats service for pattern reference
3. `src/CP/FrontEnd/src/components/FeedbackIndicators.tsx` — loading/error pattern

**Files to create / edit**:
- `src/CP/FrontEnd/src/components/TradingDashboardPanel.tsx` — new component
- `src/CP/FrontEnd/src/__tests__/TradingDashboardPanel.test.tsx` — new test file

**Acceptance criteria**:
1. Loads data from `getTradePerformance(hiredInstanceId, 90)` and `getRecommendations(hiredInstanceId)` in parallel.
2. Shows three stat cards in a row: Total Trades, Avg P&L%, Win Rate — with correct colour coding (green if positive, red if negative P&L).
3. Shows RSI recommendation section when `recommendation.confidence >= 0.7`: "Suggested RSI: Buy < {n}, Sell > {n} — {rationale}".
4. Shows `LoadingIndicator` while fetching; `FeedbackMessage` on error.
5. Period selector (30d / 90d / 180d) refetches performance for chosen period.
6. All zero/empty states handled: "No performance data yet — your agent will appear here after its first trade."

**Code patterns to copy exactly**:

```typescript
// TradingDashboardPanel.tsx — key structure
import { useEffect, useState } from 'react'
import { Badge, Card, Select } from '@fluentui/react-components'
import { LoadingIndicator, FeedbackMessage } from './FeedbackIndicators'
import { getTradePerformance, getRecommendations,
  type TradePerformanceSummary, type TradeRecommendation } from '../services/tradingSetup.service'

const PERIODS = [{ label: '30 days', value: 30 }, { label: '90 days', value: 90 }, { label: '180 days', value: 180 }]

interface Props { hiredInstanceId: string }

export function TradingDashboardPanel({ hiredInstanceId }: Props) {
  const [perf, setPerf] = useState<TradePerformanceSummary | null>(null)
  const [rec, setRec] = useState<TradeRecommendation | null>(null)
  const [period, setPeriod] = useState(90)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    Promise.all([getTradePerformance(hiredInstanceId, period), getRecommendations(hiredInstanceId)])
      .then(([p, r]) => { setPerf(p); setRec(r) })
      .catch(() => setError('Failed to load trading performance.'))
      .finally(() => setLoading(false))
  }, [hiredInstanceId, period])

  if (loading) return <LoadingIndicator message="Loading performance…" />
  if (error) return <FeedbackMessage type="error" message={error} />

  const pnlColour = (perf?.pnl_pct_avg ?? 0) >= 0 ? '#10b981' : '#ef4444'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }} data-testid="trading-dashboard">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ color: '#f4f4f5', fontWeight: 600 }}>Trading Performance</span>
        <Select
          value={String(period)}
          onChange={(_, d) => setPeriod(Number(d.value))}
          style={{ minWidth: 120 }}
        >
          {PERIODS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
        </Select>
      </div>

      {/* Stat cards */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        {[
          { label: 'Total Trades', value: String(perf?.trades_count ?? 0), colour: '#f4f4f5', testId: 'stat-trades' },
          { label: 'Avg P&L', value: `${(perf?.pnl_pct_avg ?? 0).toFixed(1)}%`, colour: pnlColour, testId: 'stat-pnl' },
          { label: 'Win Rate', value: `${((perf?.win_rate ?? 0) * 100).toFixed(0)}%`, colour: '#00f2fe', testId: 'stat-winrate' },
        ].map((stat) => (
          <Card key={stat.label} style={{ background: '#18181b', border: '1px solid #27272a',
            borderRadius: 12, padding: '16px 24px', flex: 1, minWidth: 120, textAlign: 'center' }}>
            <div style={{ fontSize: 24, fontWeight: 700, color: stat.colour }} data-testid={stat.testId}>
              {stat.value}
            </div>
            <div style={{ fontSize: 12, color: '#71717a', marginTop: 4 }}>{stat.label}</div>
          </Card>
        ))}
      </div>

      {/* RSI recommendations */}
      {rec && rec.confidence >= 0.7 && (
        <Card style={{ background: '#18181b', border: '1px solid #667eea55', borderRadius: 12, padding: 16 }}>
          <Badge appearance="tint" color="informative" size="small" style={{ marginBottom: 8 }}>
            RSI Recommendation (confidence: {(rec.confidence * 100).toFixed(0)}%)
          </Badge>
          <p style={{ color: '#f4f4f5', fontSize: 13, margin: '4px 0' }} data-testid="rec-text">
            Suggested: Buy when RSI &lt; <strong>{rec.suggested_rsi_buy_threshold}</strong>,
            Sell when RSI &gt; <strong>{rec.suggested_rsi_sell_threshold}</strong>
          </p>
          <p style={{ color: '#71717a', fontSize: 12, margin: '4px 0' }}>{rec.rationale}</p>
        </Card>
      )}

      {perf?.trades_count === 0 && (
        <p style={{ color: '#71717a', textAlign: 'center', padding: 32 }}>
          No performance data yet — your agent will appear here after its first trade.
        </p>
      )}
    </div>
  )
}
```

**Test table**:

| # | Type | Description | File |
|---|---|---|---|
| T1 | Unit | Three stat cards render with correct values | `__tests__/TradingDashboardPanel.test.tsx` |
| T2 | Unit | RSI recommendation shown only when confidence ≥ 0.7 | `__tests__/TradingDashboardPanel.test.tsx` |
| T3 | Unit | Period change to 30d triggers re-fetch | `__tests__/TradingDashboardPanel.test.tsx` |
| T4 | Unit | Zero trades shows empty state text | `__tests__/TradingDashboardPanel.test.tsx` |

---

### S6 — `TradeHistoryPanel.tsx` — paginated trade history table

**Advances**: Share Trader value (customer audits every trade the agent made — required for trust)
**Branch**: `feat/ST-UX-1-s6-history-panel`
**Estimate**: 60 min
**BLOCKED UNTIL**: S5 merged

**Context** (2 sentences):
There is no per-trade history view anywhere in the web portal today. This panel renders a paginated table of `TradeHistoryRow` records using FluentUI and the existing `getTradeHistory` service function.

**Files to read first** (max 3):
1. `src/CP/FrontEnd/src/services/tradingSetup.service.ts` — `TradeHistoryRow`, `TradeHistoryResponse`, `getTradeHistory`
2. `src/CP/FrontEnd/src/pages/authenticated/UsageBilling.tsx` — existing paginated list pattern in the portal
3. `src/CP/FrontEnd/src/components/FeedbackIndicators.tsx` — loading/error

**Files to create / edit**:
- `src/CP/FrontEnd/src/components/TradeHistoryPanel.tsx` — new component
- `src/CP/FrontEnd/src/__tests__/TradeHistoryPanel.test.tsx` — new test file

**Acceptance criteria**:
1. Renders a table with columns: Date, Trades, Avg P&L%, Win Rate, Stop-Losses.
2. P&L% column uses green for positive, red for negative values.
3. Pagination: "← Prev" / "Next →" buttons; current page shown as "Page 2 of 5".
4. Page size selector: 10 / 20 / 50.
5. Empty state: "No trade history yet."
6. Loads first page on mount; prev/next buttons fetch adjacent pages.

**Code patterns to copy exactly**:

```typescript
// TradeHistoryPanel.tsx
import { useEffect, useState } from 'react'
import { Button, Card, Select, Spinner } from '@fluentui/react-components'
import { FeedbackMessage } from './FeedbackIndicators'
import { getTradeHistory, type TradeHistoryRow } from '../services/tradingSetup.service'

interface Props { hiredInstanceId: string }

export function TradeHistoryPanel({ hiredInstanceId }: Props) {
  const [rows, setRows] = useState<TradeHistoryRow[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    getTradeHistory(hiredInstanceId, page, pageSize)
      .then((resp) => { setRows(resp.trades); setTotal(resp.total) })
      .catch(() => setError('Failed to load trade history.'))
      .finally(() => setLoading(false))
  }, [hiredInstanceId, page, pageSize])

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  if (error) return <FeedbackMessage type="error" message={error} />

  return (
    <div data-testid="trade-history-panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ color: '#f4f4f5', fontWeight: 600 }}>Trade History</span>
        <Select value={String(pageSize)} onChange={(_, d) => { setPageSize(Number(d.value)); setPage(1) }}>
          {[10, 20, 50].map((n) => <option key={n} value={n}>{n} per page</option>)}
        </Select>
      </div>
      {loading ? <Spinner label="Loading…" /> : rows.length === 0 ? (
        <p style={{ color: '#71717a', textAlign: 'center', padding: 32 }}>No trade history yet.</p>
      ) : (
        <Card style={{ background: '#18181b', border: '1px solid #27272a', borderRadius: 12, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #27272a' }}>
                {['Date', 'Trades', 'Avg P&L%', 'Win Rate', 'Stop-Losses'].map((h) => (
                  <th key={h} style={{ padding: '10px 16px', textAlign: 'left', color: '#71717a', fontSize: 12, fontWeight: 500 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={i} style={{ borderBottom: '1px solid #27272a22' }}>
                  <td style={{ padding: '10px 16px', color: '#f4f4f5', fontSize: 13 }}>{row.stat_date}</td>
                  <td style={{ padding: '10px 16px', color: '#f4f4f5', fontSize: 13 }}>{row.trades_count}</td>
                  <td style={{ padding: '10px 16px', fontSize: 13,
                    color: row.pnl_pct_avg >= 0 ? '#10b981' : '#ef4444', fontWeight: 600 }}>
                    {row.pnl_pct_avg.toFixed(1)}%
                  </td>
                  <td style={{ padding: '10px 16px', color: '#00f2fe', fontSize: 13 }}>
                    {(row.win_rate * 100).toFixed(0)}%
                  </td>
                  <td style={{ padding: '10px 16px', color: '#f4f4f5', fontSize: 13 }}>{row.stop_loss_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
      {total > pageSize && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 16, marginTop: 12 }}>
          <Button appearance="subtle" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>← Prev</Button>
          <span style={{ color: '#71717a', fontSize: 12 }} data-testid="page-indicator">Page {page} of {totalPages}</span>
          <Button appearance="subtle" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>Next →</Button>
        </div>
      )}
    </div>
  )
}
```

**Test table**:

| # | Type | Description | File |
|---|---|---|---|
| T1 | Unit | 20 rows render in table with correct column data | `__tests__/TradeHistoryPanel.test.tsx` |
| T2 | Unit | Positive P&L% shown in green; negative in red | `__tests__/TradeHistoryPanel.test.tsx` |
| T3 | Unit | Next → button disabled on last page | `__tests__/TradeHistoryPanel.test.tsx` |
| T4 | Unit | Empty state shown when `trades.length === 0` | `__tests__/TradeHistoryPanel.test.tsx` |

---

### S7 — `TaxReportPanel.tsx` — period selector, P&L summary, CSV download

**Advances**: Share Trader value (monthly/quarterly tax statement is a commercial differentiator — customers expect it before renewing)
**Branch**: `feat/ST-UX-1-s7-tax-report-panel`
**Estimate**: 60 min
**BLOCKED UNTIL**: S6 merged

**Context** (2 sentences):
Indian customers declare crypto P&L for income tax — there is no report anywhere in the web portal today. This panel provides a year/period selector, a P&L summary card, and a "Download CSV" button that generates the file client-side from the API response.

**Files to read first** (max 3):
1. `src/CP/FrontEnd/src/services/tradingSetup.service.ts` — `TaxReportResponse`, `getTaxReport`
2. `src/CP/FrontEnd/src/components/TradingDashboardPanel.tsx` — stat card pattern just created
3. `src/CP/FrontEnd/src/components/FeedbackIndicators.tsx` — loading/error

**Files to create / edit**:
- `src/CP/FrontEnd/src/components/TaxReportPanel.tsx` — new component
- `src/CP/FrontEnd/src/__tests__/TaxReportPanel.test.tsx` — new test file

**Acceptance criteria**:
1. Period type selector: Monthly / Quarterly.
2. Year selector: 2024, 2025, 2026, 2027.
3. Month selector (1–12) shown when `period === 'monthly'`; quarter selector (Q1–Q4) shown when `period === 'quarterly'`.
4. "Generate Report" button calls `getTaxReport()` and renders result.
5. Summary shows: Total Trades, Total P&L%, Profitable Trades, Loss Trades, Stop-Loss Exits.
6. "Download CSV" button triggers browser download of a CSV file named `waooaw-trade-report-{year}-{period}.csv`.
7. CSV columns: `date,skill_id,trades,pnl_pct,win_rate,stop_losses`.
8. Empty report (total_trades = 0) shows "No trades recorded for this period."

**Code patterns to copy exactly**:

```typescript
// TaxReportPanel.tsx — CSV download helper:
function downloadCsv(report: TaxReportResponse) {
  const header = 'date,skill_id,trades,pnl_pct,win_rate,stop_losses'
  const rows = report.trades.map(
    (t) => `${t.date},${t.skill_id},${t.trades_count},${t.pnl_pct},${t.win_rate},${t.stop_loss_count}`
  )
  const csv = [header, ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `waooaw-trade-report-${report.year}-${report.period}.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// Period/year selectors pattern:
const YEARS = [2024, 2025, 2026, 2027]
const MONTHS = [
  { value: 1, label: 'January' }, { value: 2, label: 'February' }, /* ... */ { value: 12, label: 'December' }
]
const QUARTERS = ['Q1', 'Q2', 'Q3', 'Q4']
```

**Test table**:

| # | Type | Description | File |
|---|---|---|---|
| T1 | Unit | Month selector visible for monthly period, hidden for quarterly | `__tests__/TaxReportPanel.test.tsx` |
| T2 | Unit | Quarter selector visible for quarterly period | `__tests__/TaxReportPanel.test.tsx` |
| T3 | Unit | Summary card shows correct total_trades after generate | `__tests__/TaxReportPanel.test.tsx` |
| T4 | Unit | Download CSV button triggers anchor click | `__tests__/TaxReportPanel.test.tsx` |

**BDD scenario**:
```
Given a customer selects Monthly, year=2026, month=6 and clicks Generate Report
When the API returns a report with 15 trades and total_pnl_pct = 3.2
Then the summary card shows "15 Trades" and "3.2% Avg P&L"
When customer clicks Download CSV
Then a file named "waooaw-trade-report-2026-monthly.csv" is downloaded
```

---

### S8 — Tab navigation for all 4 panels in MyAgents; CommandCentre approval badge

**Advances**: Share Trader value (unified navigation ties all panels into a coherent agent management surface)
**Branch**: `feat/ST-UX-1-s8-navigation-integration`
**Estimate**: 45 min
**BLOCKED UNTIL**: S7 merged

**Context** (2 sentences):
The four panels (`TradingSetupChatPanel`, `TradingApprovalPanel`, `TradingDashboardPanel`, `TradingHistoryPanel`) exist as standalone components but there is no tab bar to navigate between them in `MyAgents.tsx`. This story adds a `TabList` for trading agents and a pending-approval count badge on the CommandCentre dashboard.

**Files to read first** (max 3):
1. `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` — lines 400–460 (trading conditional block added in S3)
2. `src/CP/FrontEnd/src/pages/authenticated/CommandCentre.tsx` — `readinessCards` array for badge injection
3. `src/CP/FrontEnd/src/components/TradingApprovalPanel.tsx` — to read `listHiredAgentDeliverables` import

**Files to create / edit**:
- `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` — add `TabList` + `Tab` for trading agent section
- `src/CP/FrontEnd/src/pages/authenticated/CommandCentre.tsx` — add "Pending trade approvals" metric card

**Acceptance criteria**:
1. Trading agent section has four tabs: **Configure** | **Approvals** | **Performance** | **History** | **Tax Report**.
2. Default tab is **Configure** when `readiness.configured === false`; else **Performance**.
3. Each tab renders the correct panel component.
4. Active tab persists to `sessionStorage` key `cp_trading_active_tab_{hiredInstanceId}` across page refresh.
5. `CommandCentre` shows a new metric card: "Pending trade approvals" with count badge in red when count > 0.
6. Clicking the metric card navigates to the `MyAgents` page with the Approvals tab pre-selected.

**Code patterns to copy exactly**:

```typescript
// In MyAgents.tsx — trading section with tabs:
import { Tab, TabList } from '@fluentui/react-components'
import { TradingDashboardPanel } from '../../components/TradingDashboardPanel'
import { TradeHistoryPanel } from '../../components/TradeHistoryPanel'
import { TaxReportPanel } from '../../components/TaxReportPanel'

type TradingTab = 'configure' | 'approvals' | 'performance' | 'history' | 'tax-report'

// Inside the trading agent conditional block:
const [tradingTab, setTradingTab] = useState<TradingTab>(() => {
  const saved = sessionStorage.getItem(`cp_trading_active_tab_${instance.hired_instance_id}`)
  if (saved) return saved as TradingTab
  return tradingReadiness?.configured ? 'performance' : 'configure'
})

const handleTabChange = (_: unknown, data: { value: string }) => {
  const t = data.value as TradingTab
  setTradingTab(t)
  sessionStorage.setItem(`cp_trading_active_tab_${instance.hired_instance_id}`, t)
}

// Render:
<TabList selectedValue={tradingTab} onTabSelect={handleTabChange}>
  <Tab value="configure">⚙️ Configure</Tab>
  <Tab value="approvals">📋 Approvals {pendingCount > 0 && <Badge color="danger" size="small">{pendingCount}</Badge>}</Tab>
  <Tab value="performance">📈 Performance</Tab>
  <Tab value="history">📜 History</Tab>
  <Tab value="tax-report">📄 Tax Report</Tab>
</TabList>
{tradingTab === 'configure' && <TradingSetupChatPanel hiredInstanceId={instance.hired_instance_id} />}
{tradingTab === 'approvals' && <TradingApprovalPanel hiredInstanceId={instance.hired_instance_id} />}
{tradingTab === 'performance' && <TradingDashboardPanel hiredInstanceId={instance.hired_instance_id} />}
{tradingTab === 'history' && <TradeHistoryPanel hiredInstanceId={instance.hired_instance_id} />}
{tradingTab === 'tax-report' && <TaxReportPanel hiredInstanceId={instance.hired_instance_id} />}
```

**Test table**:

| # | Type | Description | File |
|---|---|---|---|
| T1 | Unit | Default tab is "configure" when `configured === false` | `test/MyAgents.test.tsx` |
| T2 | Unit | Default tab is "performance" when `configured === true` | `test/MyAgents.test.tsx` |
| T3 | Unit | Tab switch renders correct panel component | `test/MyAgents.test.tsx` |
| T4 | Unit | Active tab saved to sessionStorage on change | `test/MyAgents.test.tsx` |
| T5 | Unit | CommandCentre shows "Pending trade approvals" metric card | `test/CommandCentre.test.tsx` |

**BDD scenario**:
```
Given a fully configured Share Trader agent
When customer opens MyAgents page
Then the Performance tab is active by default
When customer clicks History tab
Then TradeHistoryPanel renders
When customer refreshes the page
Then History tab is still active (persisted in sessionStorage)
When there are 2 pending trade approvals
Then Approvals tab shows a red badge with "2"
And CommandCentre shows "2 Pending trade approvals" metric
```

---

## Future Phase 2 (out of scope for ST-UX-1)

| Item | Reason deferred |
|---|---|
| LLM-guided strategy wizard on web | Requires LLM_PROVIDER wiring — step-machine proves UX pattern first |
| Real-time WebSocket updates for RSI signals | Requires Plant BE WebSocket endpoint — polling via periodic re-fetch is sufficient for MVP |
| Candlestick + RSI chart visualization | Requires a charting library (TradingView widget or recharts) — high value but out of P0 scope |
| Portfolio / positions live view | Requires Delta Exchange position polling — add after trade execution proven in production |
