---
mode: agent
description: Bootstrap agent with full WAOOAW platform context before starting any task
---

Read the following files **in order** before doing anything else:

1. [AGENTS.md](../../AGENTS.md) — architectural invariants and repo layout
2. [CLAUDE.md](../../CLAUDE.md) — compact hard rules (Python, TypeScript, deployment)
3. [docs/CONTEXT_AND_INDEX.md](../../docs/CONTEXT_AND_INDEX.md) — §1 vision, §3 architecture, §5 platform standards, §11 test commands, §17 gotchas
4. [docs/CP/iterations/NFRReusable.md](../../docs/CP/iterations/NFRReusable.md) — §3 mandatory interface definitions, §6 preventive gate stories

Before doing any task-specific work, anchor yourself to this platform objective:

1. WAOOAW builds and rents value-generating agents to customers.
2. First priority is the Digital Marketing Agent (DMA): YouTube first, then broader platform distribution.
3. DMA work should bias toward one theme becoming platform-specific content variants, customer approval, scheduling, posting, and performance-led tuning.
4. Second priority is Share Trader: exchange/API setup, connectivity validation, strategy configuration, trade execution, performance review, and recommendations.
5. Any task that does not directly advance those outcomes, or clearly unblock their deployability/runtime correctness, should be challenged before deep work starts.

Before doing substantial multi-step work after the required reads:

1. Write a short working note to [session_commentary.md](../../session_commentary.md) with the task goal, current branch, a flat todo/checkpoint list, and the next save point.
2. Anticipate request limits: do not keep the whole plan only in chat context. Persist progress in `session_commentary.md` before large investigations, plan writing, or multi-file edits.
3. Commit in small chunks as you go. At minimum, checkpoint prompt/instruction changes first, then each completed major section of work.
4. Push after each checkpoint commit so request limits, disconnects, or model resets do not lose the current state.

Always enforce these configuration rules while preparing or executing work:

1. All environment-specific values must live in GCP Secret Manager or Cloud Run runtime env/secret references only.
2. Do not bake environment-specific values into Dockerfiles, committed `.env` files, Terraform defaults, or source code.
3. Preserve image promotion: the same built image must promote cleanly from demo -> uat -> prod by changing runtime configuration only.
4. Prefer work that increases DMA or Share Trader customer value over generic platform polish.
5. If the task is enablement rather than direct product value, state explicitly which DMA or Share Trader outcome it unlocks.

Do NOT assume any prior task context, previous PRs, or earlier session history — start fresh on whatever task the user describes next. Only the permanent platform rules in the files above are relevant until the user explicitly provides task-specific context.

Confirm you are ready by stating:
1. One sentence: what is the WAOOAW platform?
2. One sentence: what is the current top product priority and why?
3. The **eight architectural invariants** from AGENTS.md (list them by name, one per line).
4. The single most dangerous gotcha from CLAUDE.md's top-gotchas table and why it causes production failures.
