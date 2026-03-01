# CP-NAV-1 — Navigation Structure

**Date:** 2026-03-01  
**Branch:** `feat/cp-nav-1-navigation-structure`  
**Plan:** Based on `docs/CP/navigation-ux-analysis.md`  
**Testing:** `docker compose -f docker-compose.local.yml run --rm --no-deps cp-frontend npx tsc --noEmit`  
**Status:** 🟡 In Progress

---

## Agent Execution Rules

1. Execute epics in order: E1 → E2 → E3. Do not skip ahead.
2. Read each epic fully before writing a single line.
3. Every story is self-contained — no "see above" references.
4. After all epics are complete, run TypeScript check and existing tests.
5. Do not touch Iteration 2 or 3.

---

## Tracking Table

| # | Epic | Story | Status |
|---|------|-------|--------|
| E1 | Sidebar Restructure | Update nav items to match UX analysis target | 🔴 |
| E2 | Command Centre Page | Rename/replace Dashboard with Command Centre | 🔴 |
| E3 | URL Routing | Wire portal to React Router sub-routes `/portal/*` | 🔴 |

---

## Iteration 1

### Target Navigation (from `docs/CP/navigation-ux-analysis.md`)

| Menu | Route | Notes |
|---|---|---|
| **Command Centre** | `/portal/command-centre` | Live pulse — active agents, alerts, activity feed |
| **My Agents** | `/portal/my-agents` | Hired, trial, paused agents |
| **Discover** | `/portal/discover` | Marketplace browser → Start Trial |
| **Goals** | `/portal/goals` | Cross-agent goal management |
| **Deliverables** | `/portal/deliverables` | Everything agents have produced |
| **Inbox** | `/portal/inbox` | Agent-initiated communications |
| **Subscriptions & Billing** | `/portal/billing` | Plans, trials, invoices, payment |
| **Profile & Settings** | `/portal/settings` | Business identity, team, notifications, API keys |

---

### E1 — Sidebar Navigation Restructure

**File:** `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx`  
**Time budget:** 30 min  
**Goal:** Update the sidebar menu items and the `Page` type to match the target navigation from the UX analysis.

#### What to change

1. Replace the `Page` type union with the 8 target sections.
2. Replace `menuItems` array with the 8 target items and correct Fluent UI icons.
3. Update `renderPage` to render the 8 pages (new imports for CommandCentre, Deliverables, Inbox, ProfileSettings).
4. Wire each sidebar item to navigate to its corresponding route (E3 dependency — use `useNavigate`).

#### Page type (exact)
```typescript
type Page =
  | 'command-centre'
  | 'my-agents'
  | 'discover'
  | 'goals'
  | 'deliverables'
  | 'inbox'
  | 'billing'
  | 'settings'
```

#### Menu items (exact)
```typescript
import {
  Home20Regular,         // Command Centre
  Bot20Regular,          // My Agents
  Search20Regular,       // Discover
  Target20Regular,       // Goals
  DocumentBulletList20Regular, // Deliverables
  Mail20Regular,         // Inbox
  Payment20Regular,      // Subscriptions & Billing
  Settings20Regular,     // Profile & Settings
} from '@fluentui/react-icons'

const menuItems = [
  { id: 'command-centre' as Page, icon: <Home20Regular />, label: 'Command Centre' },
  { id: 'my-agents' as Page, icon: <Bot20Regular />, label: 'My Agents' },
  { id: 'discover' as Page, icon: <Search20Regular />, label: 'Discover' },
  { id: 'goals' as Page, icon: <Target20Regular />, label: 'Goals' },
  { id: 'deliverables' as Page, icon: <DocumentBulletList20Regular />, label: 'Deliverables' },
  { id: 'inbox' as Page, icon: <Mail20Regular />, label: 'Inbox' },
  { id: 'billing' as Page, icon: <Payment20Regular />, label: 'Subscriptions & Billing' },
  { id: 'settings' as Page, icon: <Settings20Regular />, label: 'Profile & Settings' },
]
```

#### Acceptance criteria
- [ ] Sidebar shows exactly 8 items matching the target navigation
- [ ] All existing TypeScript strict checks pass
- [ ] Clicking each sidebar item navigates to the correct URL sub-path

---

### E2 — Command Centre Page

**Files:**
- Create: `src/CP/FrontEnd/src/pages/authenticated/CommandCentre.tsx`
- Delete: `src/CP/FrontEnd/src/pages/authenticated/Dashboard.tsx` (contents moved to CommandCentre)

**Time budget:** 30 min  
**Goal:** Rename Dashboard → Command Centre with updated heading and CSS class.

#### What to build

```typescript
// src/CP/FrontEnd/src/pages/authenticated/CommandCentre.tsx
// Same content as Dashboard.tsx with:
// - Component name: CommandCentre (was Dashboard)
// - Heading text: "Command Centre" (was "Dashboard")
// - CSS class prefix: command-centre (was dashboard)
```

The content (stats, activity feed, quick actions) stays the same — only the naming changes.

#### CSS changes (globals.css)
- Add `.command-centre-page` aliases for `.dashboard-page`, `.dashboard-stats` etc.
- Keep existing `.dashboard-*` classes for now to avoid breaking other references.

#### Acceptance criteria
- [ ] `CommandCentre.tsx` exists and renders heading "Command Centre"
- [ ] Component is exported as default `CommandCentre`
- [ ] All existing tests pass

---

### E3 — URL-Based Portal Routing

**Files:**
- `src/CP/FrontEnd/src/App.tsx` — change `/portal` to `/portal/*`
- `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx` — use `useNavigate` + `useLocation` for active state; add `<Routes>` inside

**Time budget:** 45 min  
**Goal:** Each portal section gets its own URL so browser back/forward works and deep links are bookmarkable.

#### App.tsx change (minimal)
```typescript
// Before
<Route path="/portal" element={...AuthenticatedPortal...} />

// After
<Route path="/portal/*" element={...AuthenticatedPortal...} />
```

#### AuthenticatedPortal routing
```typescript
import { Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom'

// In sidebar button onClick:
onClick={() => navigate(`/portal/${item.id}`)

// Active state detection (replaces useState currentPage):
const location = useLocation()
const currentPage = location.pathname.split('/').pop() as Page || 'command-centre'

// renderPage → replace with Routes/Route inside <main>:
<main className="portal-content">
  <Routes>
    <Route index element={<Navigate to="command-centre" replace />} />
    <Route path="command-centre" element={<CommandCentre />} />
    <Route path="my-agents" element={<MyAgents />} />
    <Route path="discover" element={<AgentDiscovery />} />
    <Route path="goals" element={<GoalsSetup />} />
    <Route path="deliverables" element={<Deliverables />} />
    <Route path="inbox" element={<Inbox />} />
    <Route path="billing" element={<UsageBilling />} />
    <Route path="settings" element={<ProfileSettings />} />
    <Route path="*" element={<Navigate to="command-centre" replace />} />
  </Routes>
</main>
```

#### New placeholder pages
```typescript
// src/CP/FrontEnd/src/pages/authenticated/Deliverables.tsx
export default function Deliverables() {
  return (
    <div className="page-placeholder">
      <h1>Deliverables</h1>
      <p>Everything your agents have produced will appear here.</p>
    </div>
  )
}

// src/CP/FrontEnd/src/pages/authenticated/Inbox.tsx
export default function Inbox() {
  return (
    <div className="page-placeholder">
      <h1>Inbox</h1>
      <p>Agent-initiated updates, approvals, and requests will appear here.</p>
    </div>
  )
}

// src/CP/FrontEnd/src/pages/authenticated/ProfileSettings.tsx
export default function ProfileSettings() {
  return (
    <div className="page-placeholder">
      <h1>Profile & Settings</h1>
      <p>Business identity, team members, notifications, and API keys.</p>
    </div>
  )
}
```

#### Acceptance criteria
- [ ] `/portal` redirects to `/portal/command-centre`
- [ ] `/portal/command-centre` renders Command Centre
- [ ] `/portal/my-agents` renders My Agents
- [ ] `/portal/discover` renders AgentDiscovery inline
- [ ] `/portal/billing` renders Subscriptions & Billing
- [ ] Browser back/forward works across portal sections
- [ ] All existing tests pass

---

## Epic Completion — Docker Integration Test

```bash
# TypeScript check
docker compose -f docker-compose.local.yml run --rm --no-deps cp-frontend npx tsc --noEmit

# Unit tests
docker compose -f docker-compose.local.yml run --rm --no-deps cp-frontend npx vitest run

# Visual check — start frontend and navigate to /portal
docker compose -f docker-compose.local.yml up -d cp-frontend
```

All TypeScript errors must be zero. All existing tests must pass.
