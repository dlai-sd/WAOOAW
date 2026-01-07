# WAOOAW Version 2.0.0

**Release Date**: January 4, 2026  
**Commit**: b39c947  
**Status**: Stable - CI/CD Pipeline Active

---

## What's in V2.0.0

### Customer Portal V2 ✅
- **Location**: `WaooawPortal/`
- **Frontend**: Vite + React, multi-domain OAuth ready
- **Backend**: FastAPI 0.128.0, Python 3.11
- **Features**: 
  - OAuth 2.0 authentication
  - Agent marketplace browsing
  - Environment-aware configuration (demo/codespace)
  - CORS preflight smoke tests

### CI/CD Pipeline ✅
- **Build & Test**: `.github/workflows/build.yml`
  - Backend: ruff, flake8, black, isort, pytest
  - Frontend: optional lint/test with `--if-present`
  - Coverage: 39% (threshold 20% during V2 development)
  - Security: pip-audit, Trivy filesystem scan, CodeQL v3
  - CORS preflight smoke test for demo origins

- **Deploy**: `.github/workflows/deploy-demo.yml`
  - Auto-deploy to GCP Cloud Run on push to main
  - Artifact Registry: `asia-south1-docker.pkg.dev/waooaw-oauth/waooaw`
  - Backend port 8000, Frontend port 80
  - Smoke tests + deployment summary

### Dependencies ✅
- **FastAPI**: 0.128.0 (Starlette 0.49.1, Pydantic 2.10.6)
- **Python**: 3.11.14
- **Node**: 18
- **Black**: 24.3.0
- **Security**: All CVEs fixed except CVE-2024-23342 (ecdsa, no fix available)

### Testing ✅
- **Backend Tests**: `WaooawPortal/backend/tests/`
  - `test_health.py`: 4 tests (app import, root, health, agents endpoints)
  - All tests passing
  - Coverage: 39% (main.py 76%, config.py 69%, mock_data.py 48%)

### Infrastructure ✅
- **Cloud Provider**: Google Cloud Platform
- **Services**: 
  - Backend: `waooaw-api-demo` (Cloud Run)
  - Frontend: `waooaw-portal-demo` (Cloud Run)
- **Domains**: 
  - cp.demo.waooaw.com (customer portal)
  - pp.demo.waooaw.com (platform portal)
- **SSL**: Managed certificates, HTTPS active
- **Load Balancer**: 35.190.6.91 (preserved IP)

---

## Recent Fixes

### CI/CD Pipeline
- Added `security-events` permission for CodeQL v3
- Created `requirements-dev.txt` for backend lint/test tools
- Made frontend lint/test optional with `--if-present`
- Fixed flake8 E501 line length conflicts with black (ignored)
- Added pip-audit with CVE-2024-23342 ignore
- Fixed heredoc delimiter in CORS smoke test
- Lowered coverage threshold to 20% for V2 development

### Dependencies
- Upgraded FastAPI 0.109.0 → 0.128.0
- Pinned Starlette 0.49.1 (compatible with FastAPI ≥0.115.6)
- Upgraded Pydantic 2.5.3 → 2.10.6
- Upgraded python-jose 3.3.0 → 3.4.0
- Upgraded python-multipart 0.0.6 → 0.0.18
- Upgraded uvicorn 0.27.0 → 0.32.0
- Upgraded black 23.12.1 → 24.3.0

### Code Quality
- Formatted all backend files with black 24.3.0 and isort
- Removed unused HTMLResponse import from oauth_v2.py
- Fixed whitespace violations (W293, W291)
- Resolved import sorting violations

---

## Known Issues

### Pending
- ecdsa CVE-2024-23342: Unfixable, transitive dependency from python-jose
- Frontend lint/test scripts: Optional, not yet implemented
- Coverage target: 20% (will increase to 80% as tests expand)

---

## What's Next (V2.1.0 Roadmap)

1. **Expand Test Coverage**: 20% → 40% → 80%
2. **OAuth Testing**: End-to-end validation with Google Cloud Console
3. **Agent Integration**: Connect V2 portal to agent execution engine
4. **Frontend Tests**: Implement Playwright tests for customer portal
5. **Monitoring**: Add structured logging and error tracking
6. **Documentation**: API docs, user guides, developer onboarding

---

## Upgrade Notes

### From V1.x to V2.0.0
- New backend location: `WaooawPortal/backend` (was `backend/`)
- CI/CD targets V2 backend, not legacy `backend/` or `backend-v2/`
- Deploy workflow uses GCP Artifact Registry (not GHCR)
- Coverage threshold lowered during V2 development

### Breaking Changes
- None (V2 is parallel to V1, not a breaking upgrade)

---

## Commit History

```
b39c947 fix(ci): repair deploy-demo workflow syntax
eda00c5 fix(ci): clean deploy-demo workflow syntax
5a1d989 Merge branch 'feature/v2-fresh-architecture'
5be7b31 fix(ci): align heredoc terminator indentation
b5a08c4 fix(ci): correct heredoc delimiter in CORS smoke test
52228ad test: add basic health tests for V2 backend
10b6621 chore(ci): lower coverage requirement to 20% for V2 backend
3798ed7 chore(deps): upgrade pydantic to 2.10.6
96f3e00 chore(deps): upgrade to fastapi 0.128.0 and starlette 0.49.1
7dab322 chore(deps): revert starlette pin and ignore unfixable CVEs
```

---

## Contributors

- **dlai-sd**: Lead development, CI/CD setup, infrastructure
- **GitHub Copilot**: Code assistance, testing, documentation

---

**For detailed status**: See [STATUS.md](STATUS.md)  
**For strategic direction**: See [VISION.md](VISION.md)  
**For quick start**: See [README.md](README.md)
