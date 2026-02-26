## Description
<!-- What does this PR do? Why? -->

## Type of change
- [ ] Bug fix
- [ ] New feature
- [ ] Refactor / cleanup
- [ ] Documentation
- [ ] Infrastructure / CI

## Testing
- [ ] Unit tests pass (`docker compose -f docker-compose.local.yml run --rm --no-deps plant-backend pytest`)
- [ ] CP backend tests pass (`docker compose -f docker-compose.local.yml run --rm --no-deps cp-backend pytest`)
- [ ] New tests added for new functionality

## Database migrations
- [ ] No migration in this PR
- [ ] Migration included — `downgrade()` is fully implemented and tested locally
  - Run: `alembic upgrade head && alembic downgrade -1 && alembic upgrade head`
  - No data loss on downgrade

## Reliability checklist
- [ ] No hardcoded URLs, IPs, or secrets in application code
- [ ] All new config values added to `.env.example` for both services
- [ ] CORS origins remain explicit (no wildcard `*` added to staging/prod config)
- [ ] Circuit breaker: Plant calls go through `PlantClient`, not raw `httpx`
- [ ] Idempotent: write endpoints that create/modify records handle retry safely

## Security
- [ ] No secrets in code or logs
- [ ] Auth/authz checked on new endpoints
- [ ] Input validation on all user-facing fields

## Linked issues
Closes #
