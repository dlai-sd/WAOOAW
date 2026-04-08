# WAOOAW — Agent bootstrap guide

This file is read automatically by AI coding agents (OpenAI Codex, Gemini CLI,
and others that follow the AGENTS.md convention).

---

## Platform objective and current priority

WAOOAW exists to develop and rent value-generating agents to customers. Work in
this repo should favor agents that are self-sufficient, autonomous, effective,
efficient, and commercially useful over generic platform polish.

Current product priority order:

1. **Digital Marketing Agent (DMA)** — first commercial priority
2. **YouTube-first DMA execution** — creation, approval, scheduling, posting,
   and performance review must be strongest here first
3. **DMA channel expansion** — adapt one shared theme into platform-native
   variants for LinkedIn, Facebook, X, Instagram, WhatsApp, and later channels
4. **Autonomous DMA tuning** — use outreach or posting performance to improve
   the next cycle of content and recommendations
5. **Share Trader** — next major agent lane after DMA

When assessing scope, explicitly state whether the work advances DMA value, DMA
enablement, Share Trader value, or Share Trader enablement. If it advances none
of these, challenge the task before spending substantial effort.

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
- For persistence or migration stories: apply and smoke-check against Cloud SQL demo via the Auth Proxy first; Docker Postgres is regression-only and not the source of truth for persisted schema changes.

---

## Codespaces build and review path

- Use the existing Codespaces assets only: `.devcontainer/gcp-auth.sh`, `.codespace/demo.env`, `docker-compose.local.yml`, `docker-compose.codespace.yml`, and `scripts/codespace-stack.sh`.
- Do not invent ad-hoc Docker or URL publishing commands when a Codespaces review build is needed.
- Before any fresh Codespaces build, remove stale WAOOAW-local images first: run `bash scripts/codespace-stack.sh clean` and then `docker image prune -f`.
- After cleanup, restore the real stack with `bash .devcontainer/gcp-auth.sh` and `bash scripts/codespace-stack.sh up cp` (or the needed scope).
- Publish review URLs from `bash scripts/codespace-stack.sh urls` so the shared URL matches the actual running stack.

---

## GCP access — Cloud Run logs & debugging

This Codespace is authenticated as `waooaw-codespace-reader@waooaw-oauth.iam.gserviceaccount.com`
against project `waooaw-oauth`. Pull live Cloud Run logs directly — do not guess from CI output.

```bash
# Get all logs for a specific revision
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.revision_name="<REVISION>"' \
  --project=waooaw-oauth --limit=50 --freshness=5d 2>&1 | grep textPayload

# Get recent error logs for a service
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="<SERVICE>" AND severity>=ERROR' \
  --project=waooaw-oauth --limit=30 --freshness=2d 2>&1

# List revisions for a service
gcloud run revisions list --service=<SERVICE> --region=asia-south1 --project=waooaw-oauth
```

> **When Terraform apply fails with** *"container failed to start and listen on PORT"*, always
> fetch the Cloud Run stderr logs for that revision first — they contain the exact Python
> traceback (e.g. `ModuleNotFoundError`) rather than the generic Cloud Run timeout message.

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
