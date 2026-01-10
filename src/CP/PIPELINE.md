# CP Build Pipeline

Complete CI/CD pipeline for Customer Portal (CP) with comprehensive testing, security scanning, and Docker image builds.

## Pipeline Overview

The pipeline consists of 6 main stages:

1. **Backend Testing** - Unit tests, integration tests, code coverage
2. **Backend Security** - Dependency scanning, vulnerability checks
3. **Frontend Testing** - Unit tests, type checking, linting
4. **Frontend Security** - NPM audit, dependency scanning
5. **Docker Build & Scan** - Multi-stage builds, Trivy security scanning
6. **Code Review** - SonarCloud quality gate

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
- `safety` - Known security vulnerabilities
- Generates JSON reports

### 3. Frontend Test (`frontend-test`)
- Node.js 18 environment
- ESLint for code quality
- TypeScript type checking
- Vitest unit tests with coverage
- Uploads coverage to Codecov

### 4. Frontend Security (`frontend-security`)
- `npm audit` for dependency vulnerabilities
- Generates JSON reports

### 5. Build Images (`build-images`)
- Multi-stage Docker builds
- Pushes to GitHub Container Registry
- Tagged with branch/SHA
- Build cache optimization

### 6. Scan Images (`scan-images`)
- Trivy vulnerability scanner
- Scans for CRITICAL and HIGH severity
- Uploads results to GitHub Security
- Generates SARIF and JSON reports

### 7. Code Review (`code-review`)
- SonarCloud code quality analysis
- Combines coverage from backend + frontend
- Comments on PRs with results

### 8. Pipeline Status (`pipeline-status`)
- Aggregates all job results
- Fails pipeline if critical tests fail
- Provides summary

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
- Backend security reports (JSON)
- Frontend security reports (JSON)
- Trivy scan results (JSON)
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
npm run test:coverage   # With coverage
```

### Lint checks
```bash
# Backend
cd src/CP/BackEnd
ruff check api core models
black --check api core models
isort --check-only api core models
mypy api core models

# Frontend
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
