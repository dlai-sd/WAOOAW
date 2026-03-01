# CP + Mobile Navigation & UX Analysis

**Date**: 28 February 2026  
**Context**: Post-registration milestone. Login + registration working. Next stretch: completing profile and full navigation structure.

---

## Design Principle

> Every menu is an **action or a state**, never a form.  
> Menus map to **customer intent states**, not database tables.

The application — web or mobile — focuses on context-sensitive, agent-driven navigation. Customers act around agents: configure, set goals, monitor execution, manage subscriptions and hiring.

---

## Web Portal (CP) — Left Sidebar / Top Nav

| Menu | Description |
|---|---|
| **Command Centre** | The home dashboard — live pulse of all active agents: what they're doing right now, pending goals, alerts, and next actions. Think Bloomberg terminal for your AI workforce. |
| **My Agents** | All agents in your roster — hired, on trial, paused. Each card shows agent health, last activity, active goal, and one-click access to configure or message. |
| **Discover** | Marketplace browser — search by industry, skill, specialty, rating. Leads directly into "Start Trial" — not a product page. |
| **Goals** | Cross-agent goal management — create, assign, track, and review goals across your entire agent workforce. Goals drive agents, not task lists. |
| **Deliverables** | Everything agents have produced — content, reports, campaigns, analyses — filterable by agent, date, goal. Download or share in one click. |
| **Inbox** | Agent-initiated communications — status updates, blockers, clarification requests, and trial completion summaries requiring your approval or input. |
| **Subscriptions & Billing** | Active plans, trial countdowns, renewal dates, invoices, payment methods. Hire or cancel directly from here — no separate admin screen. |
| **Profile & Settings** | Business identity (name, industry, logo), team members, notification preferences, API keys for integrations. |

---

## Mobile App — Bottom Tabs

| Tab | Description |
|---|---|
| **Home** | Contextual feed — "what needs your attention right now": agent alerts, goals due, deliverables ready to review, trial days remaining. Cards, not lists. |
| **Discover** | Browse and compare agents. Swipe-friendly cards with personality, ratings, live status. Tap → agent profile → Start Trial in 2 taps. |
| **My Agents** | Your workforce at a glance. Each agent chip shows live status (working / idle / needs input). Tap into an agent → Goals, Deliverables, Configure, Message. |
| **Profile** | Account, preferences, subscription, support — surfaced contextually (e.g. trial expiring → subscription card floats to top). Not a settings dump. |

### Profile Tab — Section Detail

| Section | Items |
|---|---|
| **Account** | Edit Profile (full name, phone, business name, industry), My Subscription (plan, billing cycle, renewal), Payment Methods (cards/UPI, invoices), Active Trials (days remaining, deliverables) |
| **Preferences** | Notifications (email/push toggles for agent updates, trial expiry, deliverable alerts), Agent Preferences (default industry filter, shortlist), Language & Region (locale, ₹ currency, timezone) |
| **Support** | Help Center (FAQs, how trials/hiring work), Contact Support (ticket or live chat), Privacy Policy (DPDP Act compliance), Terms of Service (marketplace T&Cs, refund policy) |

---

## The Agent Context Sheet (both platforms)

When a customer taps any agent they enter an **Agent Context** — a unified sheet/screen that adapts based on relationship stage:

| Stage | Actions Surfaced |
|---|---|
| **Browsing** | View portfolio, ratings, specialisation → Start Trial |
| **On Trial** | Days left, goals running, deliverables produced → Hire / Extend / Cancel |
| **Hired** | Active goals, configure, pause, view all deliverables, renew subscription |
| **Paused / Ended** | Summary of work done, re-hire, leave review |

---

## Current State vs Target

| Area | Current State | Target |
|---|---|---|
| Mobile Profile | Skeleton — all menu items empty `() => {}` | Wired Edit Profile, Subscription, Notifications |
| Mobile tabs | Home, Discover, My Agents, Profile — screens exist | Context-driven content within each tab |
| CP Web | Landing + Auth (login/registration) working | Command Centre dashboard + sidebar nav |
| Agent Context | Not built | Unified sheet replacing separate screens |

---

## Recommended Build Order

1. **Edit Profile** (mobile + `PATCH /cp/profile` backend) — data quality, post-registration completion
2. **CP Web sidebar + Command Centre skeleton** — authenticated home experience
3. **Agent Context Sheet** (mobile) — powers Discover → Trial → Hire flow
4. **Goals** (cross-platform) — core engagement loop
5. **Deliverables** (cross-platform) — value demonstration, "try before hire" proof
