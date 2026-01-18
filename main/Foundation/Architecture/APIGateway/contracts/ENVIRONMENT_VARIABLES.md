# Environment Variables Configuration

**Version**: 1.0  
**Status**: DRAFT  
**Owner**: Platform Team  
**Last Updated**: 2026-01-17

## Purpose

This document defines all environment variables required for Phase 4 API Gateway implementation. Variables are organized by service and deployment environment.

## Service Overview

| Service | Port | Environment Variables | Secrets |
|---------|------|----------------------|---------|
| API Gateway (CP) | 8001 | 15 vars | 2 secrets |
| API Gateway (PP) | 8002 | 17 vars | 2 secrets |
| OPA Service | 8181 | 8 vars | 1 secret |
| Plant Backend | 8000 | 12 vars | 2 secrets |

## 1. API Gateway - Customer Platform (CP)

### Authentication & JWT

```bash
# JWT secret key for token validation
JWT_SECRET_CP=""  # Secret Manager: jwt-secret-cp
JWT_ALGORITHM="HS256"
JWT_ISSUER="cp.waooaw.com"
JWT_MAX_LIFETIME_SECONDS=86400
```

### Service URLs

```bash
# OPA policy engine endpoint
OPA_SERVICE_URL="http://opa-service:8181"

# Plant backend API endpoint
PLANT_API_URL="https://plant.waooaw.com"
PLANT_API_TIMEOUT_SECONDS=30

# Sandbox Plant API (for trial users)
PLANT_SANDBOX_URL="https://plant.sandbox.waooaw.com"
```

### Database & Cache

```bash
# PostgreSQL connection for audit logs
DATABASE_URL="postgresql://gateway:password@db-gateway:5432/gateway_audit"  # Secret Manager: database-password

# Redis connection for rate limiting & budget tracking
REDIS_HOST="redis-gateway"
REDIS_PORT=6379
REDIS_PASSWORD=""  # Secret Manager: redis-password
REDIS_DB=0
```

### Rate Limiting

```bash
# Rate limits per customer tier
RATE_LIMIT_TRIAL=100  # requests per hour
RATE_LIMIT_PAID=1000
RATE_LIMIT_ENTERPRISE=10000
RATE_LIMIT_BURST_TRIAL=10
RATE_LIMIT_BURST_PAID=50
RATE_LIMIT_BURST_ENTERPRISE=200
```

### Budget Guards

```bash
# Agent budget cap (per day)
AGENT_BUDGET_CAP_USD=1.00

# Platform budget cap (per month)
PLATFORM_BUDGET_CAP_USD=100.00

# Cost guard thresholds (trigger alerts)
COST_GUARD_THRESHOLD_80=80.00
COST_GUARD_THRESHOLD_95=95.00
COST_GUARD_THRESHOLD_100=100.00
```

### Trial Mode

```bash
# Trial task limits
TRIAL_TASK_LIMIT_PER_DAY=10
TRIAL_DURATION_DAYS=7
```

### Feature Flags

```bash
# Feature flags for gradual rollout
FEATURE_FLAG_OPA_POLICY=true
FEATURE_FLAG_BUDGET_GUARD=true
FEATURE_FLAG_RATE_LIMITING=true
FEATURE_FLAG_CIRCUIT_BREAKER=false
FEATURE_FLAG_OPENTELEMETRY=false
```

### Circuit Breaker

```bash
# Circuit breaker settings for Plant API
CIRCUIT_BREAKER_ENABLED=false
CIRCUIT_BREAKER_FAIL_MAX=5
CIRCUIT_BREAKER_TIMEOUT_DURATION=30
CIRCUIT_BREAKER_RESET_TIMEOUT=60
```

### Logging & Monitoring

```bash
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL="INFO"

# GCP project for Cloud Logging
GCP_PROJECT_ID="waooaw-oauth"

# Enable OpenTelemetry tracing
OTEL_ENABLED=false
OTEL_SERVICE_NAME="api-gateway-cp"
```

### Environment

```bash
# Deployment environment
ENVIRONMENT="production"  # production, demo, staging, local
```

---

## 2. API Gateway - Partner Platform (PP)

### Authentication & JWT

```bash
JWT_SECRET_PP=""  # Secret Manager: jwt-secret-pp
JWT_ALGORITHM="HS256"
JWT_ISSUER="pp.waooaw.com"
JWT_MAX_LIFETIME_SECONDS=86400
```

### RBAC (PP Only)

```bash
# Enable role-based access control
RBAC_ENABLED=true

# Role hierarchy (7 roles)
RBAC_ROLES="admin,subscription_manager,agent_orchestrator,infrastructure_engineer,helpdesk_agent,industry_manager,viewer"
```

### Governor Approval (PP Only)

```bash
# Enable Governor approval workflows
GOVERNOR_APPROVAL_ENABLED=true

# Governor agent ID (from JWT claims)
GOVERNOR_AGENT_ID_REQUIRED=true
```

### Service URLs (same as CP)

```bash
OPA_SERVICE_URL="http://opa-service:8181"
PLANT_API_URL="https://plant.waooaw.com"
PLANT_API_TIMEOUT_SECONDS=30
```

### Database & Cache (same as CP)

```bash
DATABASE_URL="postgresql://gateway:password@db-gateway:5432/gateway_audit"
REDIS_HOST="redis-gateway"
REDIS_PORT=6379
REDIS_PASSWORD=""
REDIS_DB=1  # Different Redis DB for PP
```

### Rate Limiting (same as CP, but higher limits)

```bash
RATE_LIMIT_TRIAL=1000  # PP users start with Paid tier
RATE_LIMIT_PAID=1000
RATE_LIMIT_ENTERPRISE=10000
```

### Budget Guards (same as CP)

```bash
AGENT_BUDGET_CAP_USD=1.00
PLATFORM_BUDGET_CAP_USD=100.00
COST_GUARD_THRESHOLD_80=80.00
COST_GUARD_THRESHOLD_95=95.00
COST_GUARD_THRESHOLD_100=100.00
```

### Feature Flags (same as CP)

```bash
FEATURE_FLAG_OPA_POLICY=true
FEATURE_FLAG_BUDGET_GUARD=true
FEATURE_FLAG_RATE_LIMITING=true
FEATURE_FLAG_CIRCUIT_BREAKER=false
FEATURE_FLAG_OPENTELEMETRY=false
```

### Logging (PP specific)

```bash
LOG_LEVEL="INFO"
GCP_PROJECT_ID="waooaw-oauth"
OTEL_ENABLED=false
OTEL_SERVICE_NAME="api-gateway-pp"
ENVIRONMENT="production"
```

---

## 3. OPA Policy Service

### OPA Configuration

```bash
# OPA server configuration
OPA_ADDR=":8181"
OPA_LOG_LEVEL="info"
OPA_LOG_FORMAT="json"
```

### Policy Bundle

```bash
# Bundle URL for Rego policies
OPA_BUNDLE_SERVICE_URL="https://storage.googleapis.com/waooaw-opa-bundles"
OPA_BUNDLE_NAME="gateway-policies"
OPA_BUNDLE_POLLING_INTERVAL="30s"
OPA_BUNDLE_KEY=""  # Secret Manager: opa-bundle-key
```

### External Data

```bash
# Redis connection for budget data queries
REDIS_HOST="redis-gateway"
REDIS_PORT=6379
REDIS_PASSWORD=""
```

### Health Check

```bash
# Health check endpoint
OPA_HEALTH_CHECK_ENABLED=true
OPA_READY_CHECK_ENABLED=true
```

---

## 4. Plant Backend (Updated for Gateway)

### Gateway Integration

```bash
# Enable gateway mode (trust gateway headers)
GATEWAY_MODE_ENABLED=true

# Validate correlation IDs
CORRELATION_ID_REQUIRED=true
REQUEST_ID_REQUIRED=true
```

### JWT Validation (Optional - Gateway handles)

```bash
# JWT secrets (if Plant validates directly)
JWT_SECRET_CP=""
JWT_SECRET_PP=""
JWT_VALIDATION_ENABLED=false  # Disabled when gateway handles auth
```

### Database

```bash
DATABASE_URL="postgresql://plant:password@db-plant:5432/plant"
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

### Redis

```bash
REDIS_HOST="redis-plant"
REDIS_PORT=6379
REDIS_PASSWORD=""
```

### Rate Limiting (Plant enforces if gateway disabled)

```bash
RATE_LIMITING_ENABLED=false  # Gateway handles this
```

### Audit Logging

```bash
# Log all requests with correlation IDs
AUDIT_LOG_ENABLED=true
AUDIT_LOG_TABLE="plant_audit_logs"
```

---

## 5. Shared Infrastructure

### PostgreSQL (gateway_audit database)

```bash
POSTGRES_DB="gateway_audit"
POSTGRES_USER="gateway"
POSTGRES_PASSWORD=""  # Secret Manager: database-password
POSTGRES_PORT=5432
```

### Redis (rate limiting & budget tracking)

```bash
REDIS_HOST="redis-gateway"
REDIS_PORT=6379
REDIS_PASSWORD=""  # Secret Manager: redis-password
REDIS_MAX_CONNECTIONS=50
```

---

## Environment-Specific Overrides

### Local Development

```bash
ENVIRONMENT="local"
OPA_SERVICE_URL="http://localhost:8181"
PLANT_API_URL="http://localhost:8000"
DATABASE_URL="postgresql://gateway:gateway@localhost:5432/gateway_audit"
REDIS_HOST="localhost"
LOG_LEVEL="DEBUG"
FEATURE_FLAG_CIRCUIT_BREAKER=false
```

### Demo Environment

```bash
ENVIRONMENT="demo"
OPA_SERVICE_URL="https://opa.demo.waooaw.com"
PLANT_API_URL="https://plant.demo.waooaw.com"
PLANT_SANDBOX_URL="https://plant.sandbox.demo.waooaw.com"
DATABASE_URL="postgresql://gateway:password@10.20.0.3:5432/gateway_audit"
REDIS_HOST="10.20.0.4"
LOG_LEVEL="INFO"
```

### Production Environment

```bash
ENVIRONMENT="production"
OPA_SERVICE_URL="https://opa.waooaw.com"
PLANT_API_URL="https://plant.waooaw.com"
PLANT_SANDBOX_URL="https://plant.sandbox.waooaw.com"
DATABASE_URL="postgresql://gateway:password@10.10.0.3:5432/gateway_audit"
REDIS_HOST="10.10.0.4"
LOG_LEVEL="WARNING"
FEATURE_FLAG_CIRCUIT_BREAKER=true
FEATURE_FLAG_OPENTELEMETRY=true
```

---

## Secret Manager Mappings

All sensitive values stored in GCP Secret Manager:

| Environment Variable | Secret Name | Service | Description |
|---------------------|-------------|---------|-------------|
| `JWT_SECRET_CP` | `jwt-secret-cp` | API Gateway CP | JWT signing key for CP |
| `JWT_SECRET_PP` | `jwt-secret-pp` | API Gateway PP | JWT signing key for PP |
| `DATABASE_PASSWORD` | `database-password` | Gateway, Plant | PostgreSQL password |
| `REDIS_PASSWORD` | `redis-password` | Gateway, OPA, Plant | Redis password |
| `OPA_BUNDLE_KEY` | `opa-bundle-key` | OPA Service | Bundle encryption key |

### Accessing Secrets in Docker Compose

```yaml
services:
  api-gateway-cp:
    environment:
      - JWT_SECRET_CP=${JWT_SECRET_CP}  # Load from .env file
    secrets:
      - jwt-secret-cp

secrets:
  jwt-secret-cp:
    external: true  # Managed by GCP Secret Manager
```

### Accessing Secrets in Cloud Run

```bash
gcloud run services update api-gateway-cp \
  --update-secrets=JWT_SECRET_CP=jwt-secret-cp:latest
```

---

## Validation

### Required Variables Check

```bash
#!/bin/bash
# scripts/validate-env.sh

required_vars=(
  "JWT_SECRET_CP"
  "OPA_SERVICE_URL"
  "PLANT_API_URL"
  "DATABASE_URL"
  "REDIS_HOST"
  "AGENT_BUDGET_CAP_USD"
  "PLATFORM_BUDGET_CAP_USD"
)

for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    echo "ERROR: $var is not set"
    exit 1
  fi
done

echo "All required environment variables are set"
```

### Testing Connectivity

```bash
# Test OPA connection
curl -s "$OPA_SERVICE_URL/health" || echo "OPA unreachable"

# Test Plant API connection
curl -s "$PLANT_API_URL/health" || echo "Plant unreachable"

# Test Redis connection
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" PING

# Test PostgreSQL connection
psql "$DATABASE_URL" -c "SELECT 1" || echo "Database unreachable"
```

---

## Template Files

### `.env.template` (for local development)

```bash
# Copy this file to .env and fill in values
# DO NOT commit .env to git

# Authentication
JWT_SECRET_CP=your-secret-key-here
JWT_SECRET_PP=your-secret-key-here

# Services
OPA_SERVICE_URL=http://localhost:8181
PLANT_API_URL=http://localhost:8000

# Database
DATABASE_URL=postgresql://gateway:gateway@localhost:5432/gateway_audit

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Budget
AGENT_BUDGET_CAP_USD=1.00
PLATFORM_BUDGET_CAP_USD=100.00

# Trial
TRIAL_TASK_LIMIT_PER_DAY=10

# Feature Flags
FEATURE_FLAG_OPA_POLICY=true
FEATURE_FLAG_BUDGET_GUARD=true
FEATURE_FLAG_RATE_LIMITING=true

# Logging
LOG_LEVEL=DEBUG
ENVIRONMENT=local
```

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-17 | Platform Team | Initial 40+ variable definitions |

## References

- JWT_CONTRACT.md
- PLANT_API_CONTRACT.md
- Gateway Final IMPLEMENTATION_PLAN.md (GW-00P)
- PEER_REVIEW_ENHANCEMENTS.md
