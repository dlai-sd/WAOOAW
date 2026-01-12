# Multi-Component Build Pipeline

Complete CI/CD pipeline for WAOOAW platform with 3 components (CP, PP, Plant), comprehensive testing, security scanning, and conditional deployment.

**Last Updated**: January 12, 2026  
**Architecture**: 3 components, 5 services (CP:2, PP:2, Plant:1) - Health services removed  
**Status**: ✅ Full infrastructure deployed (17 resources) | ⏳ SSL provisioning | ⚠️ Output step cosmetic failure  
**Latest Commit**: `bf81e94` (comprehensive cleanup script + health check fix)

---

## Architecture Overview

```
CP (Customer Portal) - 2 services:
├─ Frontend (React/Nginx, port 8080)
└─ Backend (FastAPI, port 8000, /health endpoint) → calls Plant

PP (Platform Portal) - 2 services:
├─ Frontend (React/Nginx, port 8080)
└─ Backend (FastAPI, port 8000, /health endpoint) → calls Plant

Plant (Core API) - 1 service:
└─ Backend (FastAPI, port 8000, /health endpoint) - shared business logic
```

**Current Deployment**: CP only (2 services + full load balancer on demo)  
**User Controls**: `enable_cp`, `enable_pp`, `enable_plant` flags  
**Removed**: Separate health services (integrated into backends)

---

## Latest Updates (Jan 12, 2026)

### ✅ Run #104: Full Deployment Success
- **Infrastructure**: 17 resources created successfully
  - 2 Cloud Run services (cp-frontend, cp-backend)
  - 2 NEGs (Network Endpoint Groups)
  - 2 Backend services (no health checks - GCP Serverless NEG restriction)
  - 2 Health checks (for URL routing only)
  - 2 Target proxies (HTTPS, HTTP)
  - 2 Forwarding rules (HTTPS, HTTP)
  - 2 URL maps (main, HTTP redirect)
  - 1 SSL certificate (provisioning)
- **Duration**: 10m32s
- **Status**: Infrastructure fully deployed, SSL provisioning in progress
- **Known Issue**: Output step failed (cosmetic only, no impact on infrastructure)

### ⏳ SSL Certificate Provisioning
- **Domain**: cp.demo.waooaw.com
- **Status**: PROVISIONING (15-60 min wait)
- **HTTP**: Working (301 redirect to HTTPS) ✓
- **HTTPS**: Pending SSL ACTIVE status
- **Static IP**: 35.190.6.91 (waooaw-lb-ip)

### ⚠️ Output Step Issue (Non-blocking)
- **Error**: `Invalid format 'not-deployed'`
- **Impact**: Smoke tests and pipeline summary skipped
- **Infrastructure**: Fully functional
- **Fix Needed**: Change fallback to empty string or "NOT_DEPLOYED"

---

## Recent Changes Summary

### Phase 1: Health Services Removed (9 → 5 services)
- Removed separate health modules (cp_health, pp_health, plant_health)
- Backend services have built-in `/health` endpoints
- Load balancer routes `/health` paths to backends
- Simplified architecture and reduced maintenance

### Phase 2: GCP Serverless NEG Health Check Fix
**Critical Discovery**: GCP platform restriction prevents health checks on Serverless NEG backend services
- **Error**: `A backend service cannot have a healthcheck with Serverless network endpoint group backends`
- **Solution**: Removed health_checks parameter from backend service resources
- **Kept**: Health check resources (needed for URL map path routing)
- **Result**: Backend services create successfully

### Phase 3: Comprehensive Cleanup Script
**Problem**: Partial deployments left orphaned resources → Error 409  
**Solution**: Delete ALL resources in dependency order:
1. Forwarding rules → Target proxies → URL maps
2. Backend services → Health checks → NEGs
3. Cloud Run services
**Exclusion**: SSL certificates (15-60 min to provision, kept for reuse)  
**Result**: One-click cleanup prevents state drift issues

### Phase 4: Terraform State Management
- Resolved state drift from partial deployments
- Manual cleanup of orphaned resources when needed
- Comprehensive cleanup script prevents future drift
- ~100 iterations over 3 days to achieve stable deployment
**Removed**: `/var/cache/nginx` chown (read-only in Cloud Run)

**Validation**: Created 9-point validation script, all checks passed before deployment

**Time Saved**: Avoided 2-3 additional runs (20-30 minutes of iteration)

### Earlier Fixes (Runs #81-86)
- **Backend container fixes**:
  - System-wide pip install: Packages installed to `/usr/local` instead of `--user` flag
  - Shell path fix: Changed CMD from `["sh", "-c", ...]` to `["/bin/sh", "-c", ...]`
  - Uvicorn invocation: `python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}`
- **Frontend container fixes**:
  - Nginx PID location: Use `/tmp/nginx/nginx.pid` instead of `/var/run/nginx.pid`
  - Removed unresolvable proxy: Commented out `proxy_pass http://backend:8000`
  - Runs as `nginx` user with proper permissions

---

## Deployment Configuration

- **Deployment gating clarified**: `deploy_to_gcp` defaults to `false`. If not explicitly set to `true` when triggering the workflow, all GCP deploy jobs will be skipped by design.
- **Build & Push to GCP fixed**:
  - Job now explicitly depends on `validate-components` to access component enable flags.
  - Step conditions use `fromJson(...) == true` for robust boolean handling (avoids string/whitespace pitfalls).
- **Image registry**: GCP pushes target `asia-south1-docker.pkg.dev/waooaw-oauth/waooaw` for `cp-backend` and `cp` images with auto tag `demo-{short-sha}-{run-number}` and `latest`.
- **Terraform apply**: After clean deletion of Cloud Run services, applies will recreate services using the pushed images; LB updates remain optional and off by default.

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

- deploy_to_gcp: true
- build_images: true
- run_tests: false
- terraform_action: apply
- target_environment: demo
- update_load_balancer: false

This ensures images are built/pushed and Terraform applies successfully.

## Debugging Failed Runs

### Fetch Run Logs via GitHub CLI

```bash
# Install gh CLI (if needed)
sudo apt-get update && sudo apt-get install -y gh

# Authenticate
gh auth login

# List recent runs
gh run list -R dlai-sd/WAOOAW --limit 20

# View specific run (e.g., run #85)
RUN_NUMBER=85
RUN_ID=$(gh run list -R dlai-sd/WAOOAW --limit 200 --json id,runNumber | jq -r ".[] | select(.runNumber == $RUN_NUMBER) | .id")
gh run view $RUN_ID -R dlai-sd/WAOOAW

# Fetch job logs for failed Terraform job
TERRAFORM_JOB_ID=$(gh run view $RUN_ID -R dlai-sd/WAOOAW --json jobs | jq -r '.jobs[] | select(.name | contains("Terraform Deploy")) | .id' | head -n1)
gh run view $RUN_ID -R dlai-sd/WAOOAW --job $TERRAFORM_JOB_ID --log > terraform.log
```

### Fetch Cloud Run Container Logs via gcloud CLI

```bash
# Authenticate with GCP
gcloud auth login
gcloud config set project waooaw-oauth

# List Cloud Run services
gcloud run services list --region asia-south1

# Check SSL certificate status
gcloud compute ssl-certificates list --project=waooaw-oauth
gcloud compute ssl-certificates describe demo-cp-ssl --global --project=waooaw-oauth

# Check load balancer components
gcloud compute forwarding-rules list --global --project=waooaw-oauth
gcloud compute target-https-proxies list --global --project=waooaw-oauth
gcloud compute backend-services list --global --project=waooaw-oauth
gcloud compute network-endpoint-groups list --regions=asia-south1 --project=waooaw-oauth

# Test endpoints
curl -I http://cp.demo.waooaw.com  # Should return 301 redirect
curl -I https://cp.demo.waooaw.com  # Will work after SSL is ACTIVE

# Get logs for specific service (last 50 lines)
SERVICE_NAME="waooaw-cp-frontend-demo"  # or waooaw-cp-backend-demo
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=$SERVICE_NAME" \
  --region asia-south1 \
  --limit 50 \
  --format=json \
  --project waooaw-oauth | jq -r '.[] | "\(.timestamp) [\(.severity)] \(.textPayload // .jsonPayload.message)"'

# Get logs for specific revision (from Terraform error message)
REVISION_NAME="waooaw-cp-frontend-demo-00001-abc"
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.revision_name=$REVISION_NAME" \
  --limit 100 \
  --format=json \
  --project waooaw-oauth | jq -r '.[] | "\(.timestamp) [\(.severity)] \(.textPayload)"'

# Check service status
gcloud run services describe $SERVICE_NAME --region asia-south1 --format=json | jq '.status'
```

## IAM Permissions Required

### GitHub Actions Service Account Roles

**Currently Configured** ✅:
- `roles/run.admin` - Deploy and manage Cloud Run services
- `roles/iam.serviceAccountUser` - Act as service accounts
- `roles/storage.admin` - Push to Artifact Registry
- `roles/artifactregistry.writer` - Write Docker images
- `roles/compute.loadBalancerAdmin` - Create/manage load balancer components (NEGs, backend services, etc.)

**Resolved Issues**:
- ✅ Service account: `waooaw-demo-deployer@waooaw-oauth.iam.gserviceaccount.com`
- ✅ All necessary permissions granted
- ✅ IAM propagation completed (5 min wait after grant)

**Specific Permissions Confirmed**:
- `compute.regionNetworkEndpointGroups.create`
- `compute.regionNetworkEndpointGroups.delete`
- `compute.regionNetworkEndpointGroups.get`
- `compute.backendServices.create`
- `compute.backendServices.update`
- `compute.healthChecks.create`
- `compute.healthChecks.update`
- `compute.regionNetworkEndpointGroups.list`
- `compute.regionNetworkEndpointGroups.use`

**Alternative - Custom Role (Least Privilege)**:
```bash
# Create custom role with only NEG permissions
gcloud iam roles create cloudRunLbIntegration \
  --project=waooaw-oauth \
  --title="Cloud Run Load Balancer Integration" \
  --description="Permissions for NEG creation in Cloud Run deployments" \
  --permissions=compute.regionNetworkEndpointGroups.create,compute.regionNetworkEndpointGroups.delete,compute.regionNetworkEndpointGroups.get,compute.regionNetworkEndpointGroups.list,compute.regionNetworkEndpointGroups.use \
  --stage=GA

# Grant custom role
gcloud projects add-iam-policy-binding waooaw-oauth \
  --member="serviceAccount:$SA_EMAIL" \
  --role="projects/waooaw-oauth/roles/cloudRunLbIntegration"
```

---

## Debugging Failed Runs

### Fetch Run Logs via GitHub CLI

```bash
# Install gh CLI (if needed)
sudo apt-get update && sudo apt-get install -y gh

# Authenticate
gh auth login

# List recent runs
gh run list -R dlai-sd/WAOOAW --limit 20

# View specific run (e.g., run #89)
RUN_NUMBER=89
RUN_ID=$(gh run list -R dlai-sd/WAOOAW --limit 200 --json id,runNumber | jq -r ".[] | select(.runNumber == $RUN_NUMBER) | .id")
gh run view $RUN_ID -R dlai-sd/WAOOAW

# Fetch job logs for failed Terraform job
TERRAFORM_JOB_ID=$(gh run view $RUN_ID -R dlai-sd/WAOOAW --json jobs | jq -r '.jobs[] | select(.name | contains("Terraform Deploy")) | .id' | head -n1)
gh run view $RUN_ID -R dlai-sd/WAOOAW --job $TERRAFORM_JOB_ID --log > terraform.log

# Get only failed job logs
gh run view $RUN_ID -R dlai-sd/WAOOAW --log-failed
```

### Fetch Cloud Run Container Logs via gcloud CLI

```bash
# Set project
gcloud config set project waooaw-oauth

# Get recent backend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=waooaw-api-demo" \
  --limit 50 \
  --format=json \
  --project waooaw-oauth | jq -r '.[] | "\(.timestamp) [\(.severity)] \(.textPayload // .jsonPayload.message)"'

# Get recent frontend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=waooaw-portal-demo" \
  --limit 50 \
  --format=json \
  --project waooaw-oauth | jq -r '.[] | "\(.timestamp) [\(.severity)] \(.textPayload // .jsonPayload.message)"'

# Get logs for specific revision (from Terraform error message)
REVISION_NAME="waooaw-api-demo-00001-abc"
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.revision_name=$REVISION_NAME" \
  --limit 100 \
  --format=json \
  --project waooaw-oauth | jq -r '.[] | "\(.timestamp) [\(.severity)] \(.textPayload)"'
```

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
