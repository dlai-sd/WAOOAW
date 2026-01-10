# CI/CD Pipeline for Customer Portal

This folder contains all CI/CD related configurations and documentation for the WAOOAW Customer Portal.

## Contents

- **`cp-pipeline.yml`** - GitHub Actions workflow definition (reference copy from `.github/workflows/`)
- **`docker-compose.yml`** - Docker Compose configuration for local development and testing
- **`PIPELINE.md`** - Complete pipeline documentation, testing guide, and troubleshooting

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
- `../FrontEnd/src/test/setup.ts` - Vitest test setup

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
1. Backend testing & linting
2. Backend security scanning
3. Frontend testing & linting
4. Frontend security scanning
5. Docker image builds
6. Image vulnerability scanning
7. Code quality review

## Documentation

For detailed documentation, see **[PIPELINE.md](./PIPELINE.md)**
