# WAOOAW — Agent bootstrap guide

This file is read automatically by AI coding agents (OpenAI Codex, Gemini CLI,
and others that follow the AGENTS.md convention).

---

## Required reading before touching any code

Read these files in order — they prevent 90 % of mistakes:

1. `docs/CONTEXT_AND_INDEX.md` — master platform reference (§1 vision, §3
   architecture, §5 platform standards, §11 test commands, §17 gotchas)
2. `docs/CP/iterations/NFRReusable.md` — mandatory NFR patterns every route
   must follow (§3 interface definitions, §5 preventive gate stories)
3. `CLAUDE.md` in this repo root — compact distillation of critical rules

For GitHub Copilot users: see `.github/agents/platform-engineer.agent.md` for
the full persona with more detailed patterns.

---

## Repository layout

```
src/CP/BackEnd/      Python 3.11 / FastAPI — Customer Portal
src/Plant/BackEnd/   Python 3.11 / FastAPI — Plant (agent-facing) service
src/Plant/Gateway/   Python 3.11 / FastAPI — API gateway + middleware
src/PP/BackEnd/      Python 3.11 / FastAPI — Partner Portal
src/mobile/          React Native / Expo / TypeScript — mobile app
infrastructure/      Docker, Terraform, GCP Cloud Run
docs/                All platform docs (start with CONTEXT_AND_INDEX.md)
.github/agents/      Reusable GitHub Copilot coding-agent persona files
.github/workflows/   CI/CD pipelines
```

---

## Architectural invariants — never violate

1. **Router**: `waooaw_router()` factory, never bare `APIRouter`
2. **App-level deps**: every `FastAPI()` constructor has
   `dependencies=[Depends(get_correlation_id), Depends(get_audit_log)]`
3. **Read replica**: GET routes use `get_read_db_session()` not `get_db_session()`
4. **PII**: `PIIMaskingFilter` on every logger; never log email/phone/name raw
5. **Resilience**: `@circuit_breaker(service=...)` on every external HTTP call
6. **Correlation**: every outgoing HTTP request (mobile or backend) carries
   `X-Correlation-ID` header
7. **Image promotion**: one Docker image built once, promoted through
   dev → uat → prod by injecting env vars. Never embed environment-specific
   values in code or Dockerfile.
8. **Cloud portability**: no GCP SDK in business logic — wrap behind adapters.
   The same codebase must be deployable to AWS or Azure without code changes.

---

## Testing requirements

- Python: pytest, **≥ 80 % coverage required** — PRs below threshold are blocked
- Mobile: Jest, all existing tests must pass
- Run commands are in `docs/CONTEXT_AND_INDEX.md` §11

---

## Commit and branch conventions

```
Branch:  feat/<scope>-<desc> | fix/<scope>-<desc> | docs/<topic>
Commit:  feat(scope): present-tense description  (Conventional Commits)
PR:      always --base main — intermediate branches are never a target
```

---

## Definition of done (user journeys / features)

A feature is production-ready only when ALL of these are true:

- [ ] Backend route: NFR patterns applied, tests ≥ 80 %, audit trail, OTel span
- [ ] Frontend / Mobile: loading + error + success states, form validation
- [ ] Config: all env vars documented, no hardcoded values, secrets in Secret Manager
- [ ] Observability: log, metric, and alert/dashboard exist for new flow
- [ ] Security: auth, RBAC, input validation, no raw PII in logs
- [ ] Cloud-portability: no provider-specific SDK in business logic
