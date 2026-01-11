# CI/CD Pipeline for Customer Portal

This folder contains all CI/CD related configurations and documentation for the WAOOAW Customer Portal.

## Status

✅ **Pipeline Status**: All jobs passing (Run #28 - January 10, 2026)  
✅ **UI Tests**: Fixed and stable (Playwright with Chromium)  
✅ **Test Coverage**: 79% backend, improving to 95%  
✅ **Security Scans**: Frontend & Backend passing

## Contents

- **`cp-pipeline.yml`** - GitHub Actions workflow definition (reference copy from `.github/workflows/`)
- **`docker-compose.yml`** - Docker Compose configuration for local development and testing
- **`PIPELINE.md`** - Complete pipeline documentation, testing guide, and troubleshooting
- **`TESTING_STRATEGY.md`** - Comprehensive testing strategy and coverage goals

## Related Files

### Docker Images
- `../BackEnd/Dockerfile` - Backend API Docker image
- `../FrontEnd/Dockerfile` - Frontend UI Docker image
- `../FrontEnd/nginx.conf` - Nginx configuration for frontend

### Tests
- `../BackEnd/tests/` - Backend unit & integration tests (pytest)
- `../BackEnd/pytest.ini` - Pytest configuration
- `../BackEnd/requirements-dev.txt` - Dev dependencies for testing
- `../FrontEnd/src/__tests__/` - Frontend unit tests (vitest)
- `../FrontEnd/src/test/` - Unit test configuration
- `../FrontEnd/e2e/` - End-to-end tests (Playwright)
- `../FrontEnd/playwright.config.ts` - Playwright configuration

## Quick Start

### Run Tests Locally

**Backend:**
```bash
cd ../BackEnd
pip install -r requirements-dev.txt
pytest tests/ -v
```

**Frontend:**
```bash
cd ../FrontEnd
npm test
```

### Build Docker Images

**Local build:**
```bash
cd CI_Pipeline
docker-compose build
docker-compose up
```

**Individual images:**
```bash
# Backend
docker build -t cp-backend:local ../BackEnd/

# Frontend
docker build -t cp-frontend:local ../FrontEnd/
```

## Pipeline Workflow

The GitHub Actions pipeline (`.github/workflows/cp-pipeline.yml`) runs automatically on:
- Pull requests to `main` or `develop`
- Pushes to `main` or `develop`
- When files in `src/CP/` are modified

**Pipeline stages:**
1. Frontend testing & linting (44s)
2. Frontend security scanning (20s)
3. Backend testing & linting (44s)
4. UI Tests - Playwright (1m14s)
5. Backend security scanning (35s)
6. Docker image builds (Frontend: 1m27s, Backend: 18s)
7. Regression tests (29s)
8. Code quality review (19s)

**Total Duration**: ~3-4 minutes

## Documentation

For detailed documentation, see **[PIPELINE.md](./PIPELINE.md)**
