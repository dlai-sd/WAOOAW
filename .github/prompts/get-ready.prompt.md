---
mode: agent
description: Bootstrap agent with full WAOOAW platform context before starting any task
---

Read the following files **in order** before doing anything else:

1. [AGENTS.md](../../AGENTS.md) — architectural invariants and repo layout
2. [CLAUDE.md](../../CLAUDE.md) — compact hard rules (Python, TypeScript, deployment)
3. [docs/CONTEXT_AND_INDEX.md](../../docs/CONTEXT_AND_INDEX.md) — §1 vision, §3 architecture, §5 platform standards, §11 test commands, §17 gotchas
4. [docs/CP/iterations/NFRReusable.md](../../docs/CP/iterations/NFRReusable.md) — §3 mandatory interface definitions, §6 preventive gate stories

Before doing substantial multi-step work after the required reads:

1. Write a short working note to [session_commentary.md](../../session_commentary.md) with the task goal, current branch, a flat todo/checkpoint list, and the next save point.
2. Anticipate request limits: do not keep the whole plan only in chat context. Persist progress in `session_commentary.md` before large investigations, plan writing, or multi-file edits.
3. Commit in small chunks as you go. At minimum, checkpoint prompt/instruction changes first, then each completed major section of work.
4. Push after each checkpoint commit so request limits, disconnects, or model resets do not lose the current state.

Always enforce these configuration rules while preparing or executing work:

1. All environment-specific values must live in GCP Secret Manager or Cloud Run runtime env/secret references only.
2. Do not bake environment-specific values into Dockerfiles, committed `.env` files, Terraform defaults, or source code.
3. Preserve image promotion: the same built image must promote cleanly from demo -> uat -> prod by changing runtime configuration only.

Do NOT assume any prior task context, previous PRs, or earlier session history — start fresh on whatever task the user describes next. Only the permanent platform rules in the files above are relevant until the user explicitly provides task-specific context.

Confirm you are ready by stating:
1. One sentence: what is the WAOOAW platform?
2. The **eight architectural invariants** from AGENTS.md (list them by name, one per line).
3. The single most dangerous gotcha from CLAUDE.md's top-gotchas table and why it causes production failures.
