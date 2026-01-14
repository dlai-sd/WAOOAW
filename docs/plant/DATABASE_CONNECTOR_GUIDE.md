# Plant Database Connector Guide

**Reference:** `src/Plant/BackEnd/core/database.py`  
**Blueprint Section:** `PLANT_BLUEPRINT.yaml` → `infrastructure.data_layer.database_connector`  
**Date:** January 14, 2026

---

## Overview

The **Database Connector** is the global abstraction layer for all Plant database operations. It provides:

- ✅ **Async-first design** optimized for FastAPI (non-blocking I/O)
- ✅ **Environment-aware** database URL selection (local/demo/uat/prod)
- ✅ **Connection pooling** with per-environment tuning
- ✅ **Cloud SQL Proxy integration** for GCP secure connections
- ✅ **FastAPI dependency injection** via `get_db_session()`
- ✅ **Extension auto-loading** (pgvector, uuid-ossp)
- ✅ **Error handling** with retry logic and circuit breaker
- ✅ **Observability** metrics and logging

**Pattern:** Global Connector with Dependency Injection + Connection Pooling

---

## Architecture

```
┌─────────────────────────────────────────┐
│         FastAPI Application             │
├─────────────────────────────────────────┤
│                                         │
│  @app.get("/skills/")                   │
│  async def list_skills(               │
│      session: AsyncSession              │
│          = Depends(get_db_session)      │
│  ):                                     │
│      result = await session.execute()   │
│                                         │
├─────────────────────────────────────────┤
│     get_db_session() [Dependency]       │
│     Yields AsyncSession per request     │
├─────────────────────────────────────────┤
│    DatabaseConnector (Singleton)        │
│  - Manages async_session_factory        │
│  - Controls connection pooling          │
│  - Handles initialization/shutdown      │
├─────────────────────────────────────────┤
│    Async SQLAlchemy Engine              │
│  - create_async_engine()                │
│  - AsyncQueuePool (connection pool)     │
│  - asyncpg driver (PostgreSQL)          │
├─────────────────────────────────────────┤
│ PostgreSQL / Cloud SQL Proxy            │
│  - Local: localhost:5432 (Docker)       │
│  - Demo: /cloudsql/.../plant-demo       │
│  - UAT: /cloudsql/.../plant-uat         │
│  - Prod: /cloudsql/.../plant-prod       │
└─────────────────────────────────────────┘
```

---

## Usage Examples

### 1. Basic Setup (FastAPI Application)

```python
# main.py
from fastapi import FastAPI
from core.database import initialize_database, shutdown_database

app = FastAPI()

@app.on_event("startup")
async def startup():
    await initialize_database()

@app.on_event("shutdown")
async def shutdown():
    await shutdown_database()
```

### 2. Using Database Session in Endpoint

```python
# api/routes/skills.py
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db_session
from models.skill import Skill

router = APIRouter(prefix="/skills", tags=["skills"])

@router.get("/")
async def list_skills(session: AsyncSession = Depends(get_db_session)):
    """
    List all skills with async database session.
    Session is automatically managed (closed after response).
    """
    stmt = select(Skill).order_by(Skill.name)
    result = await session.execute(stmt)
    return result.scalars().all()

@router.post("/")
async def create_skill(
    name: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Create a new skill."""
    skill = Skill(name=name)
    session.add(skill)
    await session.commit()
    return skill

@router.get("/{skill_id}")
async def get_skill(
    skill_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Get skill by ID."""
    skill = await session.get(Skill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill
```

### 3. Database Health Check

```python
# api/routes/health.py
from fastapi import APIRouter
from core.database import health_check_database

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/db")
async def database_health():
    """
    Check database connectivity and pool health.
    Used by Cloud Run startup/liveness probes.
    """
    is_healthy = await health_check_database()
    status = "healthy" if is_healthy else "unhealthy"
    return {
        "database": status,
        "component": "postgres",
        "environment": os.environ.get("ENVIRONMENT", "unknown")
    }
```

### 4. Manual Session Usage (Advanced)

```python
# For complex transactions or manual session management
from core.database import get_connector

async def complex_transaction():
    connector = get_connector()
    async with connector.get_session() as session:
        try:
            # Transaction 1: Create skill
            skill = Skill(name="Machine Learning")
            session.add(skill)
            
            # Transaction 2: Create job role with skill
            job = JobRole(name="ML Engineer", skills=[skill])
            session.add(job)
            
            # Commit both
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise
```

---

## Configuration per Environment

### Local (Codespace)

```yaml
# .env.local
ENVIRONMENT=local
DATABASE_URL=postgresql+asyncpg://user:password@localhost/plant
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10
DATABASE_ECHO=true  # Enable SQL logging in dev
```

**Connection Pool:**
- `pool_size=5`: Low concurrency (developer workstation)
- `max_overflow=10`: Allow overflow for spikes
- `connect_timeout=10s`: Quick fail if DB unavailable

### Demo (GCP Cloud Run + Serverless)

```yaml
# .env.demo
ENVIRONMENT=demo
DATABASE_URL=postgresql+asyncpg://plant_demo:PASSWORD@/plant_demo?unix_sock=/cloudsql/PROJECT:REGION:plant-demo
DATABASE_POOL_SIZE=1
DATABASE_MAX_OVERFLOW=10
DATABASE_ECHO=false
```

**Connection Pool:**
- `pool_size=1`: Cloud Run default concurrency = 1
- `max_overflow=10`: Allow burst for scaling
- `connect_timeout=10s`: Cloud SQL Proxy manages connection

### UAT (GCP Cloud Run + Serverless)

```yaml
# .env.uat
ENVIRONMENT=uat
DATABASE_URL=postgresql+asyncpg://plant_uat:PASSWORD@/plant_uat?unix_sock=/cloudsql/PROJECT:REGION:plant-uat
DATABASE_POOL_SIZE=1
DATABASE_MAX_OVERFLOW=15
DATABASE_ECHO=false
```

**Connection Pool:**
- `pool_size=1`: Matched to auto-scale 1-5 instances
- `max_overflow=15`: Allow higher overflow for test runs

### Production (GCP Cloud Run HA)

```yaml
# .env.prod
ENVIRONMENT=prod
DATABASE_URL=postgresql+asyncpg://plant_prod:PASSWORD@/plant_prod?unix_sock=/cloudsql/PROJECT:REGION:plant-prod
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=20
DATABASE_ECHO=false
DATABASE_STATEMENT_TIMEOUT_MS=60000
```

**Connection Pool:**
- `pool_size=5`: HA guaranteed capacity
- `max_overflow=20`: Allow higher overflow for spikes
- `statement_timeout=60s`: Prevent hung queries

---

## Connection Pool Tuning

### When to Increase Pool Size

```python
# Scenario: Many concurrent requests to same database
pool_size=10  # More concurrent connections available
max_overflow=20  # Allow temporary overflow
```

### When to Decrease Pool Size

```python
# Scenario: Cloud Run concurrency limit is low
pool_size=1  # Only 1 request at a time anyway
max_overflow=5  # Very limited overflow
```

### Cloud SQL Connection Limits

**Important:** Cloud SQL has per-instance connection limits:
- `db-f1-micro`: 40 connections max
- `db-g1-small`: 100 connections max
- `db-n1-standard-1`: 600 connections max

**Calculation:**
```
Total connections = (instances × pool_size) + (instances × max_overflow)

Demo (1 instance, pool_size=1, max_overflow=10):
  = (1 × 1) + (1 × 10) = 11 connections (well under 40 limit)

Prod (1 instance, pool_size=5, max_overflow=20):
  = (1 × 5) + (1 × 20) = 25 connections (well under 600 limit)
```

---

## Cloud SQL Proxy Integration

### Local Testing with Cloud SQL Proxy

```bash
# Terminal 1: Start Cloud SQL Proxy
cloud_sql_proxy -instances=PROJECT:REGION:plant-demo=unix:/tmp/cloudsql/plant-demo

# Terminal 2: Set DATABASE_URL
export DATABASE_URL="postgresql+asyncpg://user:password@/plant_demo?unix_sock=/tmp/cloudsql/plant-demo"

# Terminal 3: Run application
python -m uvicorn main:app --reload
```

### Cloud Run Deployment

Cloud Run automatically injects Unix socket path via `CLOUD_SQL_CONNECTIONS` environment variable.

```yaml
# Terraform example
resource "google_cloud_run_service" "plant" {
  template {
    spec {
      containers {
        env {
          name  = "CLOUD_SQL_CONNECTION_NAME"
          value = "${var.project}:${var.region}:${var.database_instance}"
        }
      }
    }
  }
}
```

---

## Error Handling

### Connection Pool Exhaustion

```python
# Error: sqlalchemy.pool.QueuePool has been recycled due to pool timeout

# Solution: Increase pool_size or max_overflow
DATABASE_POOL_SIZE=3
DATABASE_MAX_OVERFLOW=15
```

### Database Unreachable

```python
# Error: asyncpg.exceptions.ClientConfigError: cannot find /cloudsql/...

# Solution: Verify Cloud SQL Proxy is running or Unix socket path is correct
# For Cloud Run, ensure CLOUD_SQL_CONNECTION_NAME is set
```

### Query Timeout

```python
# Error: sqlalchemy.exc.TimeoutError: 60s statement timeout

# Solution: Increase DATABASE_STATEMENT_TIMEOUT_MS or optimize query
DATABASE_STATEMENT_TIMEOUT_MS=120000  # 120 seconds
```

### RLS Policy Violation

```python
# Error: new row violates row-level security policy for table "agent_entity"

# Solution: Ensure session has proper governance context (governance_agent_id)
# This is caught by our RLS trigger and appended to audit trail
```

---

## Observability

### Metrics to Monitor

| Metric | Alert Threshold | Action |
|--------|---|---|
| `db_pool_checkedout` | > 80% of pool_size | Increase pool_size or check for stuck connections |
| `db_pool_exhaustion_events` | > 5/hour | Application load increasing, consider scaling |
| `db_query_duration_ms (p99)` | > 1000ms | Slow query, optimize or add index |
| `db_connection_timeout` | > 1/hour | Database or network issue, investigate |

### Logging Example

```python
# All database operations include correlation ID
import logging
import uuid
from contextvars import ContextVar

correlation_id_var: ContextVar[str] = ContextVar("correlation_id")

logger = logging.getLogger(__name__)

async def list_skills(session: AsyncSession = Depends(get_db_session)):
    correlation_id = correlation_id_var.get(str(uuid.uuid4()))
    logger.info(
        "Fetching skills",
        extra={
            "correlation_id": correlation_id,
            "component": "database",
            "operation": "select",
        }
    )
    
    result = await session.execute(select(Skill))
    return result.scalars().all()
```

### Cloud Trace Integration

```yaml
# Cloud Run automatically traces database requests
# Visible in: Cloud Console → Trace → Trace Details
#
# Each database operation appears as a span:
# - Trace ID: Correlates all operations in request
# - Span name: "database.select" | "database.insert" | etc
# - Latency: Query execution time in ms
```

---

## Testing

### Unit Tests with Test Database

```python
# tests/conftest.py
import pytest
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine
from core.database import Base

@pytest.fixture(scope="session")
def test_db_container():
    """Spin up PostgreSQL container for tests."""
    container = PostgresContainer("postgres:15-alpine")
    container.start()
    yield container
    container.stop()

@pytest.fixture
async def test_db(test_db_container):
    """Create test database engine."""
    url = test_db_container.get_connection_url()
    # Convert to async URL
    url = url.replace("postgresql://", "postgresql+asyncpg://")
    
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def test_session(test_db):
    """Create test session."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.ext.asyncio import async_sessionmaker
    
    session_factory = async_sessionmaker(test_db, class_=AsyncSession)
    async with session_factory() as session:
        yield session
        await session.rollback()
```

### Integration Tests

```python
# tests/integration/test_skills.py
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_create_skill():
    """Test creating a skill via API."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/skills/",
            json={"name": "Python"}
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Python"

@pytest.mark.asyncio
async def test_list_skills():
    """Test listing skills."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/skills/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
```

---

## Troubleshooting Checklist

- [ ] `.env` file exists in `src/Plant/BackEnd/` directory
- [ ] `DATABASE_URL` is correctly formatted (`postgresql+asyncpg://...`)
- [ ] For local: Docker PostgreSQL container is running (`docker-compose up -d`)
- [ ] For GCP: Cloud SQL Proxy is configured or Cloud Run service has `CLOUD_SQL_CONNECTIONS`
- [ ] Connection pool size matches Cloud Run concurrency limit (usually 1)
- [ ] `asyncpg` driver is installed (`pip list | grep asyncpg`)
- [ ] Database extensions are auto-loaded (pgvector, uuid-ossp)
- [ ] Alembic migrations have been applied (`alembic upgrade head`)
- [ ] Health check endpoint is responding (`/health/db`)

---

## References

- **PLANT_BLUEPRINT.yaml:** `infrastructure.data_layer.database_connector`
- **Implementation:** `src/Plant/BackEnd/core/database.py`
- **Config:** `src/Plant/BackEnd/core/config.py`
- **SQLAlchemy Async:** https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- **Cloud SQL Proxy:** https://cloud.google.com/sql/docs/postgres/cloud-sql-proxy
- **asyncpg:** https://magicstack.github.io/asyncpg/

---

**Last Updated:** January 14, 2026  
**Maintained By:** Systems Architect Agent  
**Status:** Production Ready
