# WAOOAW — UX Design Brainstorm Session 1
## CP + PP Portal Wireframe Design

**Date:** 2026-03-07  
**Status:** PAUSED — resume from §4 (Open Questions)  
**Next action:** Answer the 3 open questions → draw wireframes → plan implementation

---

## 1. Platform Model (Locked — do not re-discuss)

```
PP (Platform Portal = Service Station):
  Defines Components   → LLM config, YouTube connector, Delta Exchange connector
                          Each component has fields; PP decides which are
                          PP-managed (locked) vs customer-fillable (exposed)
  Assembles into Skills → "Execute Trade" = TradingPump + LLMProcessor + DeltaPublisher
                          "Create & Publish" = GoalConfigPump + ContentProcessor + SocialPublisher
  Attaches Skills       → Agent Type: "Share Trader" = [Execute Trade] + [Market Analysis]
  Reviews & publishes   → Approved Agent Type appears on CP marketplace

CP (Customer Portal = Driver):
  Hires Agent           → picks from marketplace, names their hired instance
  Configures Skills     → fills customer-specific field values (API key, channel, brand, risk limit)
  Sets Goals            → condition + schedule + approval rule
  Monitors              → dashboard, notifications, approval queue, deliverables
```

### Hierarchy of composition (reuse at every level)
```
Agent
  └── Skill/s  (reusable across agents)
        └── Component/s  (reusable across skills)
              └── Customer-specific field values
```

### Reusable platform components (Scheduler, Pump, Publisher are shared infrastructure)
- **Scheduler** — common to all agents, all skills, all customers
- **Pump** — data ingestion layer (GoalConfigPump, TradingPump, etc.)
- **Processor** — AI brain (LLM call, strategy execution)
- **Publisher** — destination output (social platform, exchange, webhook)

---

## 2. Skill vs Goal — Key Distinction (Locked)

| | Skill Config | Goal Setting |
|---|---|---|
| **What** | The "plumbing" — what the skill can do and how it connects | The "business rule" — when to act, under what condition, with what approval |
| **When set** | Once during the hire journey | Anytime after hire; re-settable on demand |
| **Example: Share Trader** | Delta Exchange API key, instrument (NIFTY), lot size | "Execute when RSI < 30 · auto-execute within ₹5,000 risk" |
| **Example: Content Creator** | LinkedIn + YouTube connected, brand name, tone, audience | "Create 1 post/day · publish at 5pm · I review first" |

---

## 3. Run Cycle (Locked)

```
Scheduler fires
  → Pump pulls data (from exchange / from goal config)
  → Processor executes (LLM / strategy)
  → Approval gate checks: does customer want to review?
      YES → Notification sent (push + email/SMS + in-app Notifications tab)
           → Customer opens notification or Notifications tab
           → Customer approves/rejects
      NO  → auto-proceeds
  → Publisher posts (to exchange / to social platform)
  → Deliverable saved
  → Audited
```

**Notification channels:** Push notification + Email + SMS + in-app Notifications tab (all supported)

---

## 4. Agents in Scope (Locked)

| Agent | Purpose | Visible on CP? |
|---|---|---|
| Share Trader | Algo trading on Delta Exchange | Yes |
| Digital Marketing | Content creation + social publishing | Yes |
| Dummy | Internal testing only | No (PP only) |

All other `agent_type_entity` rows deleted from DB.

---

## 5. PP Portal Scope (Locked)

- **Now:** Monitoring dashboard — fleet view, construct health, DLQ, RBAC (already built in PP-MOULD-1)
- **Target state:** Full self-serve — PP admin designs agent workflow, Plant team implements, PP reviews and approves, then it is available to customers for hiring
- **Rationale:** Mature product needs a superb self-serve portal for operations, IT desk, and customer support

---

## 6. Open Questions — START HERE NEXT SESSION

Answer these three in order. Each answer unlocks the wireframe for that section.

---

### Q1 — Is Goal Setting mandatory before agent is "active"?

Can a customer complete the hire + skill config and **save without setting a goal** (agent sits idle until goal is set later)?  
Or must at least one goal exist before hire is considered complete?

**Why it matters:** Determines if Goal Setting is Step 3 of the hire wizard, or a separate "My Agent → Goals" section the customer returns to later.

**Options:**
- (a) Goal required in wizard → single linear hire journey, agent starts immediately
- (b) Goal optional in wizard → customer can hire, configure, come back for goal later → agent status = "Not yet active"

---

### Q2 — Multiple skills per agent: unified form or separate cards?

Share Trader has 2 skills: Market Analysis + Execute Order. Content Creator may have: Campaign Brief + Publishing Config.

Does the customer configure them as:
- (a) **Separate skill cards/tabs** — "Market Analysis settings | Execute Order settings" — customer clearly sees and manages each skill independently
- (b) **One unified form** — all fields from all skills merged into a single config screen, skill boundary hidden from customer

**Why it matters:** Drives the structure of the Skill Config screen in the hire wizard and the "Edit Config" screen in My Agents.

---

### Q3 — PP wireframe scope for this design exercise?

Should the wireframe we draw for PP cover:
- (a) **Monitoring only** — what is already built (fleet view, construct health, hook trace, DLQ, constraint policy tune)
- (b) **Target state** — full design including Skill/Component management, Agent workflow design, review/approval queue — even if implementation is months away

**Why it matters:** If (b), PP wireframe is significantly larger and we should timebox it separately from CP.

---

## 7. Wireframe Plan (pending answers to §6)

Once Q1–Q3 are answered, wireframes will cover in this order:

**CP Portal:**
1. Marketplace / Discover screen
2. Hire Wizard (Step 1: Pick → Step 2: Skill Config → Step 3: Goal Setting?)
3. My Agents — hired agent card with health dot, cadence, approval badge
4. Agent Operations — per-agent hub (approval queue, deliverables, connections)
5. Notifications tab — notification-driven approval flow
6. Goals screen — create/edit goals per agent

**PP Portal:**
7. Fleet view — all hires, health status
8. Construct Health panel — per-hire diagnostic drawer
9. (If target state) Skill / Component management
10. (If target state) Agent Type design + review/publish queue

---

## 8. What NOT to Re-discuss

- Governor approval tokens for financial actions — already implemented, keep as-is
- 50 agent test entries — deleted from DB
- Dummy agent on CP marketplace — confirmed internal only
- NFR patterns (waooaw_router, correlation ID, PII masking) — already closed, not in scope here
