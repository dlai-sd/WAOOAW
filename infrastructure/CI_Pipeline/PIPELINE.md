# CP Build Pipeline

Complete CI/CD pipeline for Customer Portal (CP) with comprehensive testing, security scanning, and Docker image builds.

**Last Updated**: January 11, 2026  
**Status**: ✅ Pipeline stable; deployment gated by inputs  
**Latest Commit**: d2f3b89 (workflow flag handling)

## Latest Updates (Jan 11, 2026)

**Workflow & CI/CD:**
- **Deployment gating clarified**: `deploy_to_gcp` defaults to `false`. If not explicitly set to `true` when triggering the workflow, all GCP deploy jobs will be skipped by design.
- **Build & Push to GCP fixed**:
  - Job now explicitly depends on `validate-components` to access component enable flags.
  - Step conditions use `fromJson(...) == true` for robust boolean handling (avoids string/whitespace pitfalls).
- **Optional cleanup**: new `clean_services` input deletes existing Cloud Run services before apply, preventing 409 "already exists" errors.

**Container Images & Cloud Run:**
- **Image registry**: GCP pushes target `asia-south1-docker.pkg.dev/waooaw-oauth/waooaw` for `cp-backend` and `cp` images with auto tag `demo-{short-sha}-{run-number}` and `latest`.
- **Backend container**: Dockerfile runs `uvicorn` via `python -m` and honors `$PORT`, resolving Cloud Run boot issues.
- **Frontend (Nginx) container**: Dockerfile now runs as native `nginx` user (instead of custom `appuser`) to ensure write permissions to system pid/log directories required for startup.
- **Both containers**: Use standard port binding (8000 and 8080 respectively) and Cloud Run `$PORT` environment variable support.

**Terraform & Deployment:**
- After clean deletion of Cloud Run services (via `clean_services=true`), applies will recreate services using the pushed images.
- LB updates remain optional and off by default to preserve static IP/DNS.

## Pipeline Overview

The pipeline consists of 8 main stages:

1. **Frontend Testing** - Unit tests, type checking, linting (44s)
2. **Frontend Security** - NPM audit, dependency scanning (20s)
3. **Backend Testing** - Unit tests, integration tests, code coverage (44s)
4. **UI Tests (Playwright)** - End-to-end browser tests with Chromium (1m14s)
5. **Backend Security** - Dependency scanning, vulnerability checks (35s)
6. **Docker Build** - Multi-stage builds for frontend (1m27s) and backend (18s)
7. **Regression Tests** - Compare with baseline (29s)
8. **Code Quality Review** - SonarCloud analysis (19s)

**Total Duration**: ~3-4 minutes

## GCP Deployment Plan (Current)

- Goal: first clean deploy on demo with Terraform fully authoritative afterward.
- Recommended inputs for a fresh deploy using newly built images:
  - `run_tests:false`
  - `build_images:true`
  - `deploy_to_gcp:true` (REQUIRED; defaults to `false`)
  - `terraform_action:apply`
  - `update_load_balancer:false`
  - `target_environment:demo`
- Behavior: builds and pushes images to GCP registry, applies Cloud Run + networking (LB skipped), preserves static IP/DNS.
- Expectation on first apply: existing Cloud Run services may be destroyed/recreated with the same names; subsequent applies stay in sync.

### GCP Deployment Inputs & Defaults

- `deploy_to_gcp` → default `false` (must be set to `true` to run any deploy jobs)
- `build_images` → default `true` (set accordingly based on whether you need fresh images)
- `run_tests` → default `true` (disable for faster deploy-only runs)
- `terraform_action` → `plan` by default; use `apply` to deploy
- `target_environment` → `demo` by default
- `update_load_balancer` → default `false` (preserves static IP/DNS)

### Trigger Checklist (Manual dispatch)

When running via GitHub Actions UI, set all of the following explicitly:

- deploy_to_gcp: true (enables deployment jobs)
- build_images: true (builds fresh images)
- run_tests: false (speeds up deployment)
- terraform_action: apply (applies Terraform changes)
- target_environment: demo (deploys to demo environment)
- update_load_balancer: false (preserves static IP/DNS)
- clean_services: true (deletes old services, prevents 409s)

This ensures images are built/pushed, old services are cleaned, and Terraform applies successfully with proper container startup.

## Triggers

- **Pull Requests**: To `main` or `develop` branches
- **Push**: To `main` or `develop` branches
- **Paths**: Only runs when files in `src/CP/` are modified

## Test Structure

### Backend Tests (`src/CP/BackEnd/tests/`)
```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_auth.py             # Auth endpoint tests
├── test_jwt.py              # JWT token tests
└── test_integration.py      # End-to-end flow tests
```

**Run locally:**
```bash
cd src/CP/BackEnd
pip install -r requirements-dev.txt
pytest tests/ -v
```

### Frontend Tests (`src/CP/FrontEnd/src/__tests__/`)
```
__tests__/
├── sample.test.ts           # Basic tests
├── GoogleLoginButton.test.tsx
└── AuthContext.test.tsx
```

**Run locally:**
```bash
cd src/CP/FrontEnd
npm test
npm run test:coverage
```

## Docker Images

### Build Locally
```bash
cd src/CP

# Build backend
docker build -t cp-backend:local BackEnd/

# Build frontend
docker build -t cp-frontend:local FrontEnd/

# Or use docker-compose
docker-compose build
docker-compose up
```

### Image Security
- Multi-stage builds for smaller images
- Non-root user execution
- Security headers in Nginx
- Health checks configured
- Trivy vulnerability scanning in CI

## Pipeline Jobs

### 1. Backend Test (`backend-test`)
- Python 3.11 environment
- Linting: Ruff, Black, isort, MyPy
- Unit tests with 70% coverage threshold
- Integration tests
- Uploads coverage to Codecov

### 2. Backend Security (`backend-security`)
- `pip-audit` - Python dependency vulnerabilities
- `bandit` - Python security linter
### 6. Backend Security (`backend-security`)
- `pip-audit` - Python dependency vulnerabilities
- `bandit` - Python security linter
- `safety` - Known security vulnerabilities
- Generates JSON reports

### 7. Build Images (`build-images`)
- Node.js 18 environment
- ESLint for code quality
- TypeScript type checking
- Vitest unit tests with coverage
- Uploads coverage to Codecov

### 4. UI Tests - Playwright (`ui-tests`)
- End-to-end browser testing
- Chromium browser (headless)
- 10 test scenarios covering:
  - Landing page load
  - Theme toggle functionality
  - Authentication modal flow
  - Modal close (Escape key)
  - Responsive design (mobile, tablet, desktop)
  - Keyboard navigation
  - Performance (load time < 3s)
- **Duration**: ~1m14s
- **Configuration**: `playwright.config.ts`
- **Tests**: `e2e/app.spec.ts`

**Recent Fixes** (Commit d7acbec):
- Fixed modal close test to use Escape key instead of backdrop click
- Resolved port conflict with `reuseExistingServer: !!process.env.CI`
- Limited to Chromium browser in CI to prevent hanging

### 5. Frontend Security (`frontend-security`)
### 7. Build Images (`build-images`)
- Multi-stage Docker builds
- Pushes to GitHub Container Registry
- Tagged with branch/SHA
- Build cache optimization

### 8. Regression Tests (`regression-tests`)
- Runs full test suite
- Compares with baseline results
- Detects breaking changes
- Duration: ~29s

### 9. Code Review (`code-review`)ty
- Generates SARIF and JSON reports

### 9. Code Review (`code-review`)
- SonarCloud code quality analysis (optional)
- Combines coverage from backend + frontend
- Comments on PRs with results

### 10. Pipeline Summary (`pipeline-summary`)
- Aggregates all job results
- Provides comprehensive summary
- Uploads pipeline artifacts

## Required Secrets

Configure in GitHub repository settings:

- `GITHUB_TOKEN` - Automatically provided
- `SONAR_TOKEN` - SonarCloud token (optional)

## Coverage Thresholds

- **Backend**: 70% minimum coverage
- **Frontend**: Standard Vitest coverage
- **Overall**: Tracked in SonarCloud

## Security Scanning

### Backend
- **pip-audit**: CVE scanning for Python packages
- **bandit**: Static security analysis
- **safety**: Known vulnerability database

### Frontend
- **npm audit**: NPM package vulnerabilities

### Docker Images
- **Trivy**: Container image vulnerability scanner
- Checks OS packages + application dependencies
- Uploads to GitHub Security tab

## Artifacts

Pipeline generates downloadable artifacts:
- **frontend-security-reports** - NPM audit results (JSON)
- **backend-security-reports** - pip-audit, bandit, safety results (JSON)
- **playwright-report** - HTML report with screenshots/videos of UI tests
- **regression-test-results** - Baseline comparison data
- Coverage reports (XML/HTML)

## Local Testing

### Run all backend tests
```bash
cd src/CP/BackEnd
pip install -r requirements-dev.txt
pytest tests/ -v --cov=api --cov=core --cov=models
```

### Run specific test markers
```bash
pytest tests/ -m unit           # Unit tests only
pytest tests/ -m integration    # Integration tests only
pytest tests/ -m auth           # Auth tests only
```

### Run frontend tests
```bash
cd src/CP/FrontEnd
npm test                # Run once
npm run test:ui         # Interactive UI
npm

### Run UI (E2E) tests
```bash
cd src/CP/FrontEnd

# Install Playwright browsers (first time only)
npx playwright install chromium --with-deps

# Build and preview
npm run build
npm run preview -- --port 4173 &

# Run tests
npx playwright test --project=chromium

# Run with UI mode (interactive)
npx playwright test --ui

# View last report
npx playwright show-report
``` run test:coverage   # With coverage
```

### Lint checks
```bash
# Backend
cd src/CP/BackEnd
ruff check api core models
black --check api core models
isorUI Tests (Playwright) Issues

**Port conflict errors:**
- Ensure no other process using port 4173
- Check `playwright.config.ts` has `reuseExistingServer: !!process.env.CI`
- Kill any hanging preview servers: `lsof -ti :4173 | xargs kill -9`

**Tests hanging or timing out:**
- Verify only Chromium browser installed in CI: `npx playwright install chromium --with-deps`
- Check workflow uses `--project=chromium` flag
- Increase timeout if needed in `playwright.config.ts`

**Modal/dialog tests failing:**
- Use Escape key to close modals (standard behavior)
- Don't rely on backdrop elements with `role="presentation"`
- Ensure accessible names/labels on interactive elements
Pipeline Success Criteria

✅ **All jobs must pass:**
- Frontend tests & linting
- Backend tests & linting (70% coverage minimum)
- UI tests (10/10 passing)
- Security scans (no critical vulnerabilities)
- Docker builds succeed
- Regression tests show no breaking changes

## Recent Improvements (January 2026)

1. **UI Test Stability** - Fixed Playwright tests with proper modal handling
2. **Performance** - Pipeline completes in ~3-4 minutes
3. **Browser Testing** - Optimized to use only Chromium in CI
4. **Port Management** - Resolved conflicts with preview server
5. **Accessibility** - Using Escape key for modal close (standard UX)

## Next Steps

1. ~~Add E2E tests~~ ✅ Complete (Playwright with 10 scenarios)
2. **Performance tests** - Load testing with Locust
3. **Deploy stage** - Auto-deploy to demo/staging on success
4. **Visual regression** - Screenshot comparison tests
5. **Increase coverage** - Target 95% for backend
cd src/CP/FrontEnd
npm run lint
```

### Security scans
```bash
# Backend
cd src/CP/BackEnd
pip-audit
bandit -r api core models

# Frontend
cd src/CP/FrontEnd
npm audit
```

## Troubleshooting

### Tests failing locally but pass in CI
- Ensure all dev dependencies installed
- Check Python/Node versions match pipeline
- Clear `__pycache__` and `node_modules`

### Docker build issues
- Check `.dockerignore` files
- Verify all required files copied
- Test multi-stage build locally

### Coverage below threshold
- Run `pytest --cov-report=html` to see missing lines
- Add tests for uncovered code paths
- Check if fixtures are properly configured

## Next Steps

1. **Add E2E tests** - Playwright/Cypress for full flow testing
2. **Performance tests** - Load testing with Locust
3. **Deploy stage** - Auto-deploy to demo/staging on success
4. **Slack notifications** - Pipeline results to team channel

## Related Documentation

- [OAuth Implementation](../../docs/CP/user_journey/OAUTH_IMPLEMENTATION.md)
- [CP README](./README.md)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
