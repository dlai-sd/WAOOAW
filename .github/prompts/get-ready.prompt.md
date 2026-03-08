---
mode: agent
description: Bootstrap agent with full WAOOAW platform context before starting any task
---

Read the following files **in order** before doing anything else:

1. [AGENTS.md](../../AGENTS.md) — architectural invariants and repo layout
2. [CLAUDE.md](../../CLAUDE.md) — compact hard rules (Python, TypeScript, deployment)
3. [docs/CONTEXT_AND_INDEX.md](../../docs/CONTEXT_AND_INDEX.md) — §1 vision, §3 architecture, §5 platform standards, §11 test commands, §17 gotchas
4. [docs/CP/iterations/NFRReusable.md](../../docs/CP/iterations/NFRReusable.md) — §3 mandatory interface definitions, §6 preventive gate stories

Do NOT assume any prior task context, previous PRs, or earlier session history — start fresh on whatever task the user describes next. Only the permanent platform rules in the files above are relevant until the user explicitly provides task-specific context.

Confirm you are ready by stating:
1. One sentence: what is the WAOOAW platform?
2. The **eight architectural invariants** from AGENTS.md (list them by name, one per line).
3. The single most dangerous gotcha from CLAUDE.md's top-gotchas table and why it causes production failures.
