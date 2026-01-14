# WAOOAW Local Development Setup

Complete guide for setting up and running WAOOAW Plant backend locally with PostgreSQL.

## Quick Start

### Option 1: Using Devcontainer (Recommended)

The devcontainer is pre-configured with PostgreSQL 15 + pgvector extension.

1. **Rebuild Container**
   ```bash
   # In VS Code: Command Palette (Ctrl+Shift+P)
   # Run: "Dev Containers: Rebuild Container"
   ```

2. **Verify PostgreSQL**
   ```bash
   psql -h localhost -U postgres waooaw_plant_dev
   # Password: waooaw_dev_password
   ```

3. **Initialize Database**
   ```bash
   bash scripts/init-local-db.sh
   ```

4. **Start Development Server**
   ```bash
   bash scripts/start-local-server.sh
   ```

5. **Access API**
   - API Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - Health: http://localhost:8000/health

### Option 2: Using Docker Compose

For development without devcontainer rebuild:

1. **Start Services**
   ```bash
   # Start PostgreSQL + Redis + Adminer
   docker-compose -f docker-compose.dev.yml up -d

   # Start all services including backend
   docker-compose -f docker-compose.dev.yml --profile full up -d
   ```

2. **Initialize Database**
   ```bash
   bash scripts/init-local-db.sh
   ```

3. **Access Services**
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379
   - Adminer UI: http://localhost:8081
   - Backend API: http://localhost:8000 (if using --profile full)

4. **Stop Services**
   ```bash
   docker-compose -f docker-compose.dev.yml down
   ```

## Database Configuration

### Connection Details

| Property | Value |
|----------|-------|
| Host | localhost |
| Port | 5432 |
| User | postgres |
| Password | waooaw_dev_password |
| Dev Database | waooaw_plant_dev |
| Test Database | waooaw_plant_test |

### Connection Strings

```bash
# Development
DATABASE_URL=postgresql+asyncpg://postgres:waooaw_dev_password@localhost:5432/waooaw_plant_dev

# Testing
TEST_DATABASE_URL=postgresql+asyncpg://postgres:waooaw_dev_password@localhost:5432/waooaw_plant_test

# Sync (for Alembic)
DATABASE_URL_SYNC=postgresql://postgres:waooaw_dev_password@localhost:5432/waooaw_plant_dev
```

## Development Workflow

### 1. Database Migrations

```bash
cd src/Plant/BackEnd
source venv/bin/activate

# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### 2. Seed Database

```bash
cd src/Plant/BackEnd
source venv/bin/activate
export $(cat .env.local | xargs)

python3 -m database.seed_data
```

### 3. Run Tests

```bash
# All tests
bash scripts/run-local-tests.sh

# Unit tests only
cd src/Plant/BackEnd
source venv/bin/activate
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# With coverage
pytest --cov=. --cov-report=html
```

### 4. Start Development Server

```bash
# Using helper script
bash scripts/start-local-server.sh

# Or manually
cd src/Plant/BackEnd
source venv/bin/activate
export $(cat .env.local | xargs)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Database Management

```bash
# Connect to database
psql -h localhost -U postgres waooaw_plant_dev

# List tables
\dt

# Describe table
\d base_entity

# Query data
SELECT * FROM base_entity LIMIT 10;

# Check extensions
SELECT * FROM pg_extension;
```

## Troubleshooting

### PostgreSQL Not Starting

```bash
# Check PostgreSQL status
pg_isready -h localhost -p 5432 -U postgres

# Restart PostgreSQL (devcontainer)
sudo service postgresql restart

# View logs (docker-compose)
docker-compose -f docker-compose.dev.yml logs postgres
```

### pgvector Extension Missing

```bash
# Verify extension
psql -h localhost -U postgres waooaw_plant_dev -c "SELECT * FROM pg_extension WHERE extname='vector';"

# Install manually
sudo apt-get update
sudo apt-get install postgresql-15-pgvector

# Or rebuild from source (see .devcontainer/setup.sh)
```

### Database Connection Errors

```bash
# Check environment variables
echo $DATABASE_URL

# Verify credentials
psql postgresql://postgres:waooaw_dev_password@localhost:5432/waooaw_plant_dev

# Reset database
dropdb -h localhost -U postgres waooaw_plant_dev
createdb -h localhost -U postgres waooaw_plant_dev
bash scripts/init-local-db.sh
```

### Python Dependencies Issues

```bash
cd src/Plant/BackEnd

# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## Environment Files

### `.env.local` (Auto-generated)

Located at `src/Plant/BackEnd/.env.local`. Created automatically by setup script.

```env
DATABASE_URL=postgresql+asyncpg://postgres:waooaw_dev_password@localhost:5432/waooaw_plant_dev
ENVIRONMENT=development
DEBUG=true
...
```

### Custom Configuration

To override defaults, create `.env.local.custom`:

```env
# Custom overrides
LOG_LEVEL=DEBUG
CORS_ORIGINS=["http://localhost:3000"]
```

## Useful Scripts

All scripts located in `scripts/` directory:

| Script | Description |
|--------|-------------|
| `init-local-db.sh` | Initialize database with migrations + seed data |
| `run-local-tests.sh` | Run all tests (unit + integration) |
| `start-local-server.sh` | Start development server with auto-reload |

## Testing Endpoints

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# List agents
curl http://localhost:8000/api/v1/agents

# Create skill
curl -X POST http://localhost:8000/api/v1/genesis/skills \
  -H "Content-Type: application/json" \
  -d '{"name": "Python Programming", "category": "Technical"}'
```

### Using httpie

```bash
# Install httpie
pip install httpie

# List agents
http GET http://localhost:8000/api/v1/agents

# Create agent
http POST http://localhost:8000/api/v1/agents \
  name="AI Agent" \
  skill_id="..." \
  job_role_id="..." \
  industry_id="..."
```

## Database Tools

### Adminer (Web UI)

When using docker-compose, Adminer is available at http://localhost:8081

- System: PostgreSQL
- Server: postgres (or localhost)
- Username: postgres
- Password: waooaw_dev_password
- Database: waooaw_plant_dev

### pgAdmin (Alternative)

```bash
# Add to docker-compose.dev.yml if needed
docker run -d \
  -p 5050:80 \
  -e PGADMIN_DEFAULT_EMAIL=admin@waooaw.com \
  -e PGADMIN_DEFAULT_PASSWORD=admin \
  dpage/pgadmin4
```

## Performance Testing

```bash
cd src/Plant/BackEnd
source venv/bin/activate

# Benchmark tests
pytest tests/performance/ --benchmark-only

# Load testing with locust
pip install locust
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

## CI/CD Integration

Local setup mirrors production environment:

- PostgreSQL 15 (same as Cloud SQL)
- pgvector extension (same version)
- Python 3.11+ (same as Cloud Run)
- Async patterns (same as production)

## Best Practices

1. **Always use virtual environment**
   ```bash
   source venv/bin/activate
   ```

2. **Load environment variables**
   ```bash
   export $(cat .env.local | xargs)
   ```

3. **Run tests before commits**
   ```bash
   bash scripts/run-local-tests.sh
   ```

4. **Keep migrations clean**
   - Review auto-generated migrations
   - Test upgrade and downgrade
   - Don't edit applied migrations

5. **Use transactions in tests**
   - Tests should be isolated
   - Use pytest fixtures for database setup
   - Rollback after each test

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [PostgreSQL 15 Documentation](https://www.postgresql.org/docs/15/)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review devcontainer logs: `.devcontainer/setup.sh` output
3. Check docker-compose logs: `docker-compose -f docker-compose.dev.yml logs`
4. Verify PostgreSQL: `pg_isready -h localhost -U postgres`
