# WAOOAW Local Development - Quick Reference

## 🚀 Quick Start

```bash
# Rebuild devcontainer (one-time)
Ctrl+Shift+P → "Dev Containers: Rebuild Container"

# Initialize database
bash scripts/init-local-db.sh

# Start server
bash scripts/start-local-server.sh

# Run tests
bash scripts/run-local-tests.sh
```

## 📊 Database

```bash
# Connection
psql -h localhost -U postgres waooaw_plant_dev
# Password: waooaw_dev_password

# Connection String
postgresql+asyncpg://postgres:waooaw_dev_password@localhost:5432/waooaw_plant_dev

# Check status
pg_isready -h localhost -U postgres
```

## 🔧 Development Commands

```bash
# Migrations
cd src/Plant/BackEnd && source venv/bin/activate
alembic upgrade head                    # Apply all migrations
alembic downgrade -1                    # Rollback one
alembic revision --autogenerate -m "msg" # Create new

# Seed data
python3 -m database.seed_data

# Run server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Tests
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest --cov=. --cov-report=html
```

## 🐳 Docker Compose

```bash
# Start services
docker compose -f docker-compose.dev.yml up -d

# Stop services
docker compose -f docker-compose.dev.yml down

# View logs
docker compose -f docker-compose.dev.yml logs postgres

# Status
docker compose -f docker-compose.dev.yml ps
```

## 🌐 URLs

- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health
- Adminer: http://localhost:8081

## 📝 Environment

Located at: `src/Plant/BackEnd/.env.local`

```env
DATABASE_URL=postgresql+asyncpg://postgres:waooaw_dev_password@localhost:5432/waooaw_plant_dev
ENVIRONMENT=development
DEBUG=true
```

## 🧪 Testing

```bash
# All tests
bash scripts/run-local-tests.sh

# Unit only
pytest tests/unit/ -v

# Integration only  
pytest tests/integration/ -v

# Specific test
pytest tests/unit/test_models.py::test_base_entity -v

# With coverage
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

## 🔍 Debugging

```bash
# Check PostgreSQL
pg_isready -h localhost -U postgres

# List databases
psql -h localhost -U postgres -l

# Connect and query
psql -h localhost -U postgres waooaw_plant_dev
\dt                     # List tables
\d base_entity          # Describe table
SELECT * FROM base_entity LIMIT 5;

# Check extensions
SELECT * FROM pg_extension;
```

## 🛠️ Troubleshooting

```bash
# PostgreSQL not responding
docker compose -f docker-compose.dev.yml restart postgres

# Reset database
dropdb -h localhost -U postgres waooaw_plant_dev
createdb -h localhost -U postgres waooaw_plant_dev
bash scripts/init-local-db.sh

# Python dependencies
cd src/Plant/BackEnd
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Clear cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type d -name .pytest_cache -exec rm -rf {} +
```

## 📚 Documentation

- [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md) - Complete guide
- [LOCAL_SETUP_COMPLETE.md](LOCAL_SETUP_COMPLETE.md) - Setup summary
- API Docs: http://localhost:8000/docs (when server running)

## 💡 Tips

- Always activate venv: `source venv/bin/activate`
- Load env vars: `export $(cat .env.local | xargs)`
- Run tests before commits
- Use Adminer UI for visual database management
- Check logs: `docker compose -f docker-compose.dev.yml logs -f`
