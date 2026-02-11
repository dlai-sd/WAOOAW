# Plant Database Connectivity Guide (AGP1-DB-0.3)

**Date**: 2026-02-11  
**Purpose**: Document DATABASE_URL patterns for Codespaces (Docker) and GCP (Cloud SQL) environments

---

## Environment Overview

| Environment | DB Runtime | Connection Type | DATABASE_URL Pattern |
|---|---|---|---|
| **Codespaces / Docker Compose** | PostgreSQL container | TCP host:port | `postgresql+asyncpg://user:pass@postgres:5432/dbname` |
| **GCP Demo** | Cloud SQL | Unix socket | `postgresql+asyncpg://user:pass@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE` |
| **GCP UAT** | Cloud SQL | Unix socket | `postgresql+asyncpg://user:pass@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE` |
| **GCP Prod** | Cloud SQL | Unix socket + HA | `postgresql+asyncpg://user:pass@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE` |

---

## Codespaces / Docker Compose (Local Development)

### Connection Details
- **Host**: `postgres` (Docker Compose service name)
- **Port**: `5432` (internal Docker network port)
- **Driver**: `asyncpg` (async PostgreSQL driver)
- **Databases**:
  - `waooaw_db` - main development database
  - `waooaw_test_db` - test database (used by pytest with `DATABASE_URL` env override)

### DATABASE_URL Format
```bash
# Development (used by docker-compose.local.yml)
DATABASE_URL="postgresql+asyncpg://waooaw:waooaw_dev_password@postgres:5432/waooaw_db"

# Testing (override in pytest commands)
DATABASE_URL="postgresql+asyncpg://waooaw:waooaw_dev_password@postgres:5432/waooaw_test_db"
```

### Docker Compose Configuration
See [docker-compose.local.yml](../../docker-compose.local.yml):
```yaml
plant-backend:
  environment:
    - DATABASE_URL=postgresql+asyncpg://waooaw:waooaw_dev_password@postgres:5432/waooaw_db
```

### Health Check
```bash
# Inside container
docker compose -f docker-compose.local.yml exec plant-backend python -c "
from core.database import _connector
import asyncio
async def check():
    return await _connector.health_check()
print(asyncio.run(check()))
"

# Expected output: True
```

---

## GCP Cloud SQL (Demo/UAT/Prod)

### Connection Details
- **Host**: Unix socket path `/cloudsql/<PROJECT_ID>:<REGION>:<INSTANCE_NAME>`
- **No TCP Port**: Cloud SQL Auth Proxy uses unix sockets
- **Driver**: `asyncpg` via SQLAlchemy
- **Authentication**: IAM-based via Cloud SQL Auth Proxy sidecar

### DATABASE_URL Format
```bash
# GCP Demo
DATABASE_URL="postgresql+asyncpg://plant_demo:${DB_PASSWORD}@/plant_demo?host=/cloudsql/${GCP_PROJECT_ID}:${GCP_REGION}:plant-demo"

# GCP UAT
DATABASE_URL="postgresql+asyncpg://plant_uat:${DB_PASSWORD}@/plant_uat?host=/cloudsql/${GCP_PROJECT_ID}:${GCP_REGION}:plant-uat"

# GCP Prod (with HA and read replica)
DATABASE_URL="postgresql+asyncpg://plant_prod:${DB_PASSWORD}@/plant_prod?host=/cloudsql/${GCP_PROJECT_ID}:${GCP_REGION}:plant-prod"
DATABASE_READ_REPLICA_URL="postgresql+asyncpg://plant_prod_readonly:${DB_PASSWORD}@/plant_prod?host=/cloudsql/${GCP_PROJECT_ID}:${GCP_REGION}:plant-prod-replica"
```

### Key Differences from Codespaces
1. **No `@host:port`**: Uses `@/dbname?host=/cloudsql/...` format
2. **Unix Socket**: `host=` query parameter specifies socket path
3. **Cloud SQL Proxy**: Must be running as sidecar or separate process
4. **IAM Auth**: Password can be replaced with IAM token (future)

### Cloud SQL Proxy Setup
```yaml
# Example Cloud Run / GKE sidecar
- name: cloud-sql-proxy
  image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.8.0
  args:
    - "--port=5432"
    - "--structured-logs"
    - "PROJECT_ID:REGION:INSTANCE_NAME"
  securityContext:
    runAsNonRoot: true
```

---

## Migration Commands (Environment-Specific)

### Codespaces / Docker
```bash
# Run migrations in Plant backend container
docker compose -f docker-compose.local.yml exec -T plant-backend alembic upgrade head

# Check current revision
docker compose -f docker-compose.local.yml exec -T plant-backend alembic current

# Downgrade one revision
docker compose -f docker-compose.local.yml exec -T plant-backend alembic downgrade -1
```

### GCP Cloud Run / GKE
```bash
# Run migrations via dedicated job/pod
gcloud run jobs execute plant-migrations \
  --region=${GCP_REGION} \
  --project=${GCP_PROJECT_ID}

# Or via kubectl (GKE)
kubectl apply -f infrastructure/k8s/jobs/alembic-migrate-head.yaml
```

---

## Testing Database Connectivity

### From Codespaces
```bash
# Test connection to Postgres container
docker compose -f docker-compose.local.yml exec -T postgres psql -U waooaw -d waooaw_db -c "SELECT version();"

# Test Plant backend can connect
docker compose -f docker-compose.local.yml exec -T plant-backend python -c "
import asyncio
from core.database import _connector
asyncio.run(_connector.health_check())
"
```

### From GCP (Cloud Run)
```bash
# Check /health endpoint (includes DB check)
curl https://plant-backend-<hash>-uc.a.run.app/health

# Expected response:
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-02-11T..."
}
```

---

## Connection Pool Settings

### Codespaces / Docker (Low Concurrency)
```bash
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=5
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_PRE_PING=true
DATABASE_ECHO=true  # Enable SQL logging for dev
```

### GCP Prod (High Concurrency)
```bash
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_PRE_PING=true
DATABASE_ECHO=false  # Disable SQL logging for perf
```

---

## Troubleshooting

### Codespaces: "connection refused"
**Cause**: Postgres container not running or wrong host
```bash
# Check postgres container
docker compose -f docker-compose.local.yml ps postgres

# Restart if needed
docker compose -f docker-compose.local.yml restart postgres
```

### GCP: "unix socket not found"
**Cause**: Cloud SQL Proxy not running or wrong instance path
```bash
# Verify instance name
gcloud sql instances describe INSTANCE_NAME --project=PROJECT_ID

# Check proxy logs
kubectl logs -l app=plant-backend -c cloud-sql-proxy
```

### Alembic: "target database is not empty"
**Cause**: Trying to run migrations on a DB that already has tables but no alembic_version
```bash
# Stamp current state (use carefully!)
docker compose -f docker-compose.local.yml exec -T plant-backend alembic stamp head
```

---

## Security Best Practices

1. **Never commit `.env` files**: Use `.env.*.template` only
2. **Use Secret Manager** (GCP): Store `DB_PASSWORD` in GCP Secret Manager
3. **Rotate passwords**: Schedule quarterly password rotation
4. **Principle of least privilege**: Use read-only accounts for read replicas
5. **Audit logs**: Enable Cloud SQL audit logging in prod

---

## Summary

- **Codespaces**: TCP connection to Docker Postgres container (`postgres:5432`)
- **GCP**: Unix socket connection via Cloud SQL Proxy (`/cloudsql/...`)
- **Both**: Use `asyncpg` driver via SQLAlchemy async engine
- **Migrations**: Alembic `upgrade head` works identically in both environments
- **Testing**: Docker-based tests use `waooaw_test_db` with env override

**Key Principle**: Application code is **DB-agnostic** and relies only on `DATABASE_URL` environment variable.
