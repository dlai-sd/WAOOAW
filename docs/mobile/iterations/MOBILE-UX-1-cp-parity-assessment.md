# MOBILE-UX-1 — Mobile App vs CP Application Gap Assessment

**Date**: 2026-04-01
**Purpose**: Honest comparison of mobile app state against CP web application, identifying what needs fixing before we can charge customers for this experience.

---

## What's Actually Broken (Not Cosmetic — Blocking Revenue)

### 1. CP "My Agents" Wizard Is a Customer Time-Sink

The DMA wizard has **7 steps and 20+ form fields** before a customer sees ANY output. The customer fills business_name, location, timezone in GoalsSetup, then fills them AGAIN in the DMA wizard. Platform credential forms (exchange API keys, social OAuth) show up mixed with agent configuration regardless of agent type.

| Problem | Evidence | Impact |
|---|---|---|
| Fields duplicated across GoalsSetup and DMA Wizard | `GoalsSetup.tsx` L269 asks brand_name, location, timezone; `DigitalMarketingActivationWizard.tsx` L1320 asks same fields | Customer fills same data 2-3x |
| Exchange/trading fields shown for DMA agents | `MyAgents.tsx` L269-280 shows allowed_coins, risk_limits for ALL agent types | Confuses DMA customers |
| Blind strategy approval | `DMAWizard.tsx` L903 gates draft generation on `!isThemeApproved` | Customer approves strategy without seeing draft |
| Silent success after brief save | `GoalsSetup.tsx` L123 shows text message, no next-step guidance | Customer doesn't know what happens next |
| 5 platforms shown as "Unavailable" | `DMAWizard.tsx` L1490-1505 soft-disabled Instagram, Facebook, LinkedIn, WhatsApp, X | Signals incomplete product |

### 2. Deliverables Page Is 100% Placeholder

`Deliverables.tsx` (28 lines total) renders hardcoded healthcare examples. Zero API calls. The `listHiredAgentDeliverables()` service function exists but is never imported or called. Customer cannot see generated content, approval status, or publishing outcomes.

### 3. Command Centre Is Fake

`CommandCentre.tsx` has all-static arrays. "Today's Flight Plan" is 3 hardcoded strings. Workspace metrics show "0 Pinned alerts, 1 Billing area" — never computed from real data. Agent activity feed says "No live agent activity yet" with no API call to check.

### 4. Inbox Works But Is Disconnected

`Inbox.tsx` has proper approval workflow UX (pending/approved/rejected tabs, publishReadiness states) but depends on props from parent component. It's not clear whether data actually flows there. The 8 publish readiness states defined in `hiredAgentDeliverables.service.ts` are never surfaced to the customer.

### 5. MyAgentsSummary Missing Critical Fields

The summary service returns subscription/config status but NOT: `last_run_at`, `is_active`, `deliverables_count`, `pending_approvals_count`, `next_scheduled_run`. Customer has zero visibility into whether their agent is actually working.

---

## Customer Journey Walkthrough: Hire DMA → Get Value

1. **Discover + Hire** — Works well. Agent cards, search, filters, payment all functional.
2. **Configure** — Hits Configure tab. Sees nickname + platform credential forms + exchange fields. Confusing for DMA customer. Fills nickname, skips rest.
3. **GoalsSetup** — Fills 4-step brief (business context, audience, YouTube angle, voice). Saves. Gets text message "Brief saved." No next step shown.
4. **DMA Wizard** — Does 7 more steps. Fills brand_name/location/timezone AGAIN. Goes through AI strategy workshop. Approves strategy WITHOUT seeing a draft. Sets schedule. Clicks Activate.
5. **After Activation** — Goes to Deliverables page → placeholder data. Goes to Command Centre → "No activity." Goes to Inbox → empty. **Dead end. No way to know if agent is working.**
6. **Days Later** — IF content appears in Inbox, customer can approve. But they can't preview the actual content text, just see a title.

**Bottom line**: 30+ form fields, duplicate data entry, blind approval, no feedback = customer pays ₹12K/month and has no idea if they're getting value.

---

## Mobile App Current State

### What Works
- 4 bottom tabs (Today, Discover, Ops, Profile) with proper dark theme
- Agent discovery with search and industry filters
- Agent detail with pricing, rating, specialty
- Hire wizard with Razorpay payment
- My Agents with trial/hired tabs and sorting
- Agent Operations screen with DMA brief capture
- Google OAuth sign-in
- Pull-to-refresh on key screens
- Design tokens match brand (dark #0a0a0a, neon cyan #00f2fe, proper typography)

### What's Broken or Stub

| Screen | Problem |
|---|---|
| **SearchResultsScreen** | TODO comment "Render agent cards matching search query" — shows query text only |
| **FilterAgentsScreen** | TODO comment "Add filter action button" — inputs exist but no apply/reset |
| **PaymentMethodsScreen** | Static placeholder array (UPI, Card) — comment says "replace with real API" |
| **SubscriptionManagementScreen** | Placeholder — cancel flow unclear |
| **HomeScreen hero** | Mock banner content — priority pills are live but hero is static |
| **HireConfirmationScreen** | Minimal implementation |
| **Bottom tab icons** | Emoji (🏠🔍🤖👤) instead of proper vector icons |
| **No tab badges** | No notification counts on any tab |
| **No Inbox/Deliverables** | Missing entirely — can't approve work on mobile |
| **No Subscriptions & Billing** | Can't view invoices/receipts on mobile |
| **No haptic feedback** | Doesn't feel native |
| **Default navigation transitions** | No custom animations |

---

## What Needs to Happen (Prioritized)

### Must-Fix: Revenue-Blocking

1. **CP: Wire Deliverables page to real API** — replace placeholder with `listHiredAgentDeliverables()` calls, show actual content
2. **CP: Wire Command Centre to real data** — agent status, pending approvals count, last run time
3. **CP: Deduplicate wizard fields** — pull brand_name, location, timezone from customer profile instead of asking again
4. **CP: Show draft preview BEFORE approval** — remove the gate that blocks draft generation until blind approval
5. **Mobile: Add Inbox/Deliverables screen** — customers must approve work from phone
6. **Mobile: Fix SearchResults + FilterAgents stubs** — broken search/filter kills marketplace discovery

### Should-Fix: Professional Quality

7. **Mobile: Replace emoji tab icons** with `@expo/vector-icons`
8. **Mobile: Add tab badges** for pending approvals
9. **Mobile: Wire Subscriptions & Billing** to real API
10. **Mobile: HomeScreen live dashboard** — pull from MyAgentsSummary
11. **Mobile: Haptic feedback + transitions** — feel like a real app
12. **CP: Remove "Unavailable" platform badges** — hide unsupported platforms instead of advertising incompleteness
