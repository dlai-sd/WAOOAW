# INFRA-CODESPACE-1 — Fast Local Loop in GitHub Codespaces

> **Objective guardrail — read first**
> This plan exists to create a Docker-first local iteration loop inside GitHub Codespaces so WAOOAW engineers can rebuild, restart, and verify Plant, CP, PP, and routing quickly against demo-grade cloud dependencies without waiting for PR merge and Cloud Run deployment cycles.
> Every story in this plan must preserve that objective: reduce iteration latency, keep runtime behavior close to demo, and avoid drift into production deploy redesign, unrelated UX work, or backend business-feature expansion.

> **Template version**: 2.0
> **How to use**: Fill every placeholder before publishing the final plan.

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `INFRA-CODESPACE-1` |
| Feature area | `Infrastructure — GitHub Codespaces fast local iteration loop` |
| Created | `2026-04-02` |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `User request in chat — Codespaces fast local loop using Docker against demo assets` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | `1` |
| Total epics | `[TBD after vision confirmation]` |
| Total stories | `[TBD after vision confirmation]` |

---

## Objective

1. Run WAOOAW local application surfaces in GitHub Codespaces through Docker images and Docker Compose.
2. Point the local stack at demo-grade dependencies where safe and practical: Cloud SQL, demo secrets, managed Redis, Google OAuth, and routed public callback URLs.
3. Give developers one repeatable local command surface to build, restart, clean stale images, and reopen the stack on Codespaces URLs.
4. Keep CP BackEnd as a thin proxy and avoid mixing this plan with unrelated product-scope work.

> **Agent instruction**
> Before executing any epic or story, re-read this Objective section and verify the change still reduces local iteration time without drifting into production-only deployment work, unrelated feature development, or environment-specific hacks that would break image promotion.

---

## Vision Intake

- **Area**: `infra` with cross-service local runtime wiring for Plant, CP, PP, and routing inside GitHub Codespaces.
- **Outcome**: A developer can rebuild or restart the local Docker stack in Codespaces, have it run against demo-aligned cloud dependencies, and open the live Codespaces URLs from a laptop for fast iteration.
- **Out of scope**: Production Cloud Run deployment redesign, unrelated product UX changes, and broad backend feature work outside the local iteration loop.
- **Lane**: `Lane B` — new infra scripts/configuration and likely new local orchestration surfaces are required.
- **Urgency**: `Single iteration only`; optimize for one merge that materially reduces local iteration latency.

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | `[Pending vision confirmation]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` |

---

## Agent Execution Rules

This section will be completed after vision confirmation. It will include the required fail-fast validation gate, GitHub Agents-tab launch block, and objective anti-drift rule for the single iteration.
