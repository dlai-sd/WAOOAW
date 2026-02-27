# WAOOAW — Claude Code context

> **Start every session**: read `docs/CONTEXT_AND_INDEX.md` §1, §3, §5, §11,
> §17 before writing any code. It is the authoritative platform reference.

## What this repo is

AI agent marketplace platform. Four Python/FastAPI backends + React Native
mobile app + GCP infrastructure. Branch: always target `main`.

```
src/CP/BackEnd/      ← Customer Portal backend (Python / FastAPI)
src/Plant/BackEnd/   ← Plant (agent-side) backend
src/Plant/Gateway/   ← Plant API gateway / middleware
src/PP/BackEnd/      ← Partner Portal backend
src/mobile/          ← React Native / Expo app (TypeScript)
infrastructure/      ← Docker, Terraform, GCP Cloud Run
.github/agents/      ← Reusable Copilot coding-agent personas
docs/                ← All platform documentation
```

---

## Hard rules — never break these

### Python
```python
# 1. Router factory — CI ruff ban on bare APIRouter
from core.routing import waooaw_router
router = waooaw_router(prefix="/resource", tags=["resource"])

# 2. Global deps on every FastAPI() app
app = FastAPI(dependencies=[Depends(get_correlation_id), Depends(get_audit_log)])

# 3. Read replica on GET routes
async def list_things(db = Depends(get_read_db_session)):  # not get_db_session

# 4. PII masking on every logger
logger.addFilter(PIIMaskingFilter())

# 5. Circuit breaker on every external call
@circuit_breaker(service="name")
async def call_external(): ...
```

### TypeScript / Mobile
```typescript
// Add X-Correlation-ID on every outgoing request
config.headers['X-Correlation-ID'] = generateCorrelationId();
// Strip body/params from __DEV__ logs (PII risk)
// Retry 429/5xx/network-drop with exponential backoff (3×, 1s/2s/4s+jitter)
```

### Deployment (most important architectural rule)
- **Image promotion**: build one image, promote it through dev→uat→prod by
  injecting different env vars / secrets. This is NOT a rebuild-per-environment.
- **Never bake** env-specific values into code, `Dockerfile`, or compose files.
- **Never import** a GCP-specific SDK in business logic — use an adapter so the
  same code runs on AWS/Azure tomorrow.
- Secrets: GCP Secret Manager in production; `.env` files only for local dev,
  never committed.

---

## Testing

```bash
# Python — minimum 80% coverage required, no merge below that
docker-compose -f docker-compose.test.yml run <service>-test \
  pytest --cov=app --cov-report=xml --cov-fail-under=80

# Mobile
cd src/mobile && node_modules/.bin/jest --forceExit

# Check specific service
docker-compose -f docker-compose.test.yml run cp-test pytest -x -v
```

---

## Git
```bash
# Branch naming: feat/scope-desc | fix/scope-desc | docs/topic | refactor/scope
# Commits: conventional format — feat(scope): description
# PRs: always --base main — never an intermediate branch
gh pr create --base main --title "feat(scope): ..." --body "..."
```

---

## Observability — every new route must have

1. Structured log with `correlation_id`, `user_id`, `duration_ms`
2. Audit record (via global `audit_dependency`)
3. OTel span: `tracer.start_as_current_span("service.operation")`
4. Prometheus metric: counter + histogram in `core/metrics.py`

---

## NFR reference

Full mandatory interface definitions are in
`docs/CP/iterations/NFRReusable.md` §3.  
Platform standards (Section 5.6) are in `docs/CONTEXT_AND_INDEX.md`.

---

## Top gotchas

| Mistake | Consequence | Fix |
|---------|-------------|-----|
| Bare `APIRouter` | CI fails; correlation/audit missing | `waooaw_router()` |
| `get_db_session` on GET | Primary DB hammered | `get_read_db_session` |
| Logging `email`/`phone` raw | PII incident | `PIIMaskingFilter` |
| Hardcoding env values | Image cannot be promoted | Runtime env vars only |
| PR targeting non-main branch | Work never ships | `--base main` always |
| External call without CB | Cascading failure | `@circuit_breaker` |
