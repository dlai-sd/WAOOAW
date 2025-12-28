# 🚀 WAOOAW Quick Start Guide

Get the WAOOAW platform running in under 5 minutes!

## Prerequisites

- Docker & Docker Compose installed
- Git installed
- (Optional) Python 3.11+ for local development

## Option 1: GitHub Codespaces (Recommended) ⭐

**One-click setup - everything configured automatically!**

1. Click **Code** → **Codespaces** → **Create codespace on main**
2. Wait for container to build (~2 minutes)
3. Services start automatically via `postStartCommand`
4. Access:
   - Frontend: Click "Open in Browser" for port 3000
   - Backend API: Port 8000 → `/api/docs`
   - Database UI: Port 8081 (Adminer)

**That's it!** The DevContainer handles everything.

## Option 2: Automated Setup Script

```bash
# Clone repository
git clone https://github.com/dlai-sd/WAOOAW.git
cd WAOOAW

# Run setup (creates .env, installs deps, starts Docker)
./scripts/setup.sh
```

**Services will be available at:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Adminer: http://localhost:8081

## Option 3: Manual Setup

```bash
# Clone repository
git clone https://github.com/dlai-sd/WAOOAW.git
cd WAOOAW

# Create backend .env file
cat > backend/.env << 'EOF'
DATABASE_URL=postgresql://waooaw:waooaw_dev_password@postgres:5432/waooaw_db
REDIS_URL=redis://redis:6379/0
ENV=development
DEBUG=true
SECRET_KEY=dev_secret_change_in_production
EOF

# Start all services
docker-compose -f infrastructure/docker/docker-compose.yml up -d

# Check logs
docker-compose -f infrastructure/docker/docker-compose.yml logs -f
```

## Verify Installation

### 1. Check Backend Health
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","service":"waooaw-backend"}
```

### 2. Check API Docs
Open http://localhost:8000/api/docs - you should see Swagger UI

### 3. Check Frontend
Open http://localhost:3000/marketplace.html - WAOOAW marketplace with dark theme

### 4. Check Database
- Open http://localhost:8081 (Adminer)
- System: PostgreSQL
- Server: postgres
- Username: waooaw
- Password: waooaw_dev_password
- Database: waooaw_db

### 5. Run Tests (Optional)
```bash
# Run all tests
cd /workspaces/WAOOAW
pytest

# Run with coverage
pytest --cov=waooaw --cov-report=html

# Run specific test suites
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m "not slow"     # Skip slow tests

# View coverage report
open htmlcov/index.html  # Or navigate to file in browser
```

**Expected Results:**
- 162+ tests passing (78%+)
- 37%+ code coverage
- All health checks pass

## Common Commands

```bash
# View logs
docker-compose -f infrastructure/docker/docker-compose.yml logs -f

# Stop services
docker-compose -f infrastructure/docker/docker-compose.yml down

# Restart a service
docker-compose -f infrastructure/docker/docker-compose.yml restart backend

# Rebuild after code changes
docker-compose -f infrastructure/docker/docker-compose.yml up -d --build

# Access backend shell
docker exec -it waooaw-backend bash

# Run backend tests
cd backend && pytest
```

## Development Workflow

### Making Changes

1. **Create feature branch**
   ```bash
   git checkout develop
   git checkout -b feature/your-feature-name
   ```

2. **Make changes** - Code hot-reloads automatically

3. **Run tests**
   ```bash
   cd backend
   pytest
   ```

4. **Commit using Conventional Commits**
   ```bash
   git add .
   git commit -m "feat: add new agent card component"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create PR to develop branch
   ```

### Backend Development

```bash
# Install dependencies locally (optional - for IDE)
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt -r requirements-dev.txt

# Run tests with coverage
pytest --cov=app --cov-report=html

# Format code
black app/
isort app/

# Lint
flake8 app/
```

### Frontend Development

```bash
cd frontend

# Install dependencies (for linting)
npm install

# Lint JavaScript
npm run lint

# Format code
npm run format

# Serve locally (alternative to Docker)
python -m http.server 3000
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000
# Kill it
kill -9 <PID>

# Or use different ports in docker-compose.yml
```

### Database Connection Failed
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Restart PostgreSQL
docker-compose -f infrastructure/docker/docker-compose.yml restart postgres

# Check logs
docker logs waooaw-postgres
```

### Backend Not Starting
```bash
# Check backend logs
docker logs waooaw-backend

# Common issues:
# 1. Missing .env file → Create backend/.env
# 2. Database not ready → Wait 10s and restart
# 3. Port conflict → Change port in docker-compose.yml
```

### Frontend CORS Issues
Make sure backend is running and CORS is configured in [backend/app/main.py](backend/app/main.py#L26-L35). Codespaces URLs are already whitelisted.

## Next Steps

1. ✅ **Explore API** - http://localhost:8000/api/docs
2. ✅ **View Marketplace** - http://localhost:3000/marketplace.html
3. ✅ **Read Docs** - Check [docs/](docs/) folder
4. ✅ **Make Changes** - Code hot-reloads automatically
5. ✅ **Run Tests** - `cd backend && pytest`
6. ✅ **Deploy** - CI/CD triggers on push to main

## Production Deployment

See [README.md](README.md#deployment) for production deployment instructions.

**Branch Strategy:**
- `main` → Production (protected, requires PR + tests passing)
- `develop` → Staging (auto-deploys on merge)
- `feature/*` → Development (create PR to develop)

## Support

- 📖 Documentation: [docs/](docs/)
- 🤖 Copilot Context: [.github/copilot-instructions.md](.github/copilot-instructions.md)
- 🐛 Issues: Use GitHub Issues
- 💬 Questions: Use GitHub Discussions

---

**Ready to build?** Start with the [API documentation](http://localhost:8000/api/docs) and [brand guidelines](docs/BRAND_GUIDELINES.md).

**WAOOAW** - _Agents Earn Your Business_ 🚀
