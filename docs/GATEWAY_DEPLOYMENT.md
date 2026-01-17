# API Gateway Deployment Guide

## Overview

This guide covers deploying the WAOOAW API Gateway (CP Gateway and PP Gateway) to Google Cloud Platform using Cloud Run.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│   Clients   │────▶│  CP Gateway  │────▶│ Plant Service │
│  (Customers)│     │   (Port 8000)│     │               │
└─────────────┘     └──────────────┘     └───────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  OPA Service │
                    │  Redis Cache │
                    │  PostgreSQL  │
                    └──────────────┘

┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│   Partners  │────▶│  PP Gateway  │────▶│ Plant Service │
│ (Developers)│     │   (Port 8001)│     │               │
└─────────────┘     └──────────────┘     └───────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  OPA Service │
                    │  Redis Cache │
                    │  PostgreSQL  │
                    └──────────────┘
```

## Prerequisites

### Local Development
- Docker 20.10+
- Docker Compose 2.0+
- Python 3.11+
- Make (optional)

### GCP Deployment
- gcloud CLI
- Terraform 1.6+
- GCP Project with billing enabled
- Artifact Registry repository
- Cloud SQL instance (PostgreSQL 15)
- Redis instance (Memorystore)

## Local Development Setup

### 1. Start Services

```bash
# Start all services
docker-compose -f docker-compose.gateway.yml up -d

# View logs
docker-compose -f docker-compose.gateway.yml logs -f cp-gateway pp-gateway

# Check health
curl http://localhost:8000/health  # CP Gateway
curl http://localhost:8001/health  # PP Gateway
```

### 2. Run Tests

```bash
# Run all tests
./scripts/test-gateway.sh all

# Run specific test suites
./scripts/test-gateway.sh unit          # Unit tests only
./scripts/test-gateway.sh integration   # Integration tests
./scripts/test-gateway.sh smoke         # Smoke tests
./scripts/test-gateway.sh performance   # Load tests
```

### 3. Development Workflow

```bash
# Make code changes
# Hot reload is enabled, changes apply automatically

# View logs
docker-compose -f docker-compose.gateway.yml logs -f cp-gateway

# Restart specific service
docker-compose -f docker-compose.gateway.yml restart cp-gateway

# Cleanup
docker-compose -f docker-compose.gateway.yml down -v
```

## GCP Deployment

### 1. Set Up GCP Environment

```bash
# Set environment variables
export GCP_PROJECT_ID="waooaw-production"
export GCP_REGION="us-central1"
export ARTIFACT_REGISTRY="us-central1-docker.pkg.dev"

# Authenticate
gcloud auth login
gcloud config set project $GCP_PROJECT_ID

# Enable required APIs
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    sqladmin.googleapis.com \
    redis.googleapis.com \
    secretmanager.googleapis.com
```

### 2. Create Infrastructure

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Review plan
terraform plan \
    -var="project_id=$GCP_PROJECT_ID" \
    -var="region=$GCP_REGION"

# Apply
terraform apply \
    -var="project_id=$GCP_PROJECT_ID" \
    -var="region=$GCP_REGION"
```

### 3. Store Secrets

```bash
# JWT Public Key
gcloud secrets create jwt-public-key \
    --data-file=./keys/jwt_public.pem \
    --replication-policy=automatic

# Database URL
echo "postgresql://user:pass@/waooaw?host=/cloudsql/$GCP_PROJECT_ID:$GCP_REGION:waooaw-postgres" | \
    gcloud secrets create database-url --data-file=-

# LaunchDarkly SDK Key
echo "$LAUNCHDARKLY_SDK_KEY" | \
    gcloud secrets create launchdarkly-sdk-key --data-file=-
```

### 4. Build and Push Images

```bash
# Build images
docker build -f infrastructure/docker/cp_gateway.Dockerfile \
    -t $ARTIFACT_REGISTRY/$GCP_PROJECT_ID/waooaw/cp-gateway:latest .

docker build -f infrastructure/docker/pp_gateway.Dockerfile \
    -t $ARTIFACT_REGISTRY/$GCP_PROJECT_ID/waooaw/pp-gateway:latest .

# Push to Artifact Registry
gcloud auth configure-docker $ARTIFACT_REGISTRY
docker push $ARTIFACT_REGISTRY/$GCP_PROJECT_ID/waooaw/cp-gateway:latest
docker push $ARTIFACT_REGISTRY/$GCP_PROJECT_ID/waooaw/pp-gateway:latest
```

### 5. Deploy to Cloud Run

```bash
# Deploy using script (recommended)
./scripts/deploy-gateway.sh

# Or deploy manually
gcloud run deploy cp-gateway \
    --image=$ARTIFACT_REGISTRY/$GCP_PROJECT_ID/waooaw/cp-gateway:latest \
    --region=$GCP_REGION \
    --platform=managed \
    --allow-unauthenticated \
    --min-instances=1 \
    --max-instances=10 \
    --cpu=2 \
    --memory=1Gi \
    --set-env-vars="ENVIRONMENT=production,PORT=8000" \
    --set-secrets="DATABASE_URL=database-url:latest,JWT_PUBLIC_KEY=jwt-public-key:latest"

gcloud run deploy pp-gateway \
    --image=$ARTIFACT_REGISTRY/$GCP_PROJECT_ID/waooaw/pp-gateway:latest \
    --region=$GCP_REGION \
    --platform=managed \
    --allow-unauthenticated \
    --min-instances=1 \
    --max-instances=10 \
    --cpu=2 \
    --memory=1Gi \
    --set-env-vars="ENVIRONMENT=production,PORT=8001" \
    --set-secrets="DATABASE_URL=database-url:latest,JWT_PUBLIC_KEY=jwt-public-key:latest"
```

### 6. Configure DNS

```bash
# Get service URLs
CP_GATEWAY_URL=$(gcloud run services describe cp-gateway \
    --region=$GCP_REGION \
    --format="value(status.url)")

PP_GATEWAY_URL=$(gcloud run services describe pp-gateway \
    --region=$GCP_REGION \
    --format="value(status.url)")

# Configure DNS (in your DNS provider)
# cp.waooaw.com → CNAME $CP_GATEWAY_URL
# pp.waooaw.com → CNAME $PP_GATEWAY_URL

# Add domain mapping
gcloud run domain-mappings create \
    --service=cp-gateway \
    --domain=cp.waooaw.com \
    --region=$GCP_REGION

gcloud run domain-mappings create \
    --service=pp-gateway \
    --domain=pp.waooaw.com \
    --region=$GCP_REGION
```

## Verification

### Health Checks

```bash
# CP Gateway
curl https://cp.waooaw.com/health
curl https://cp.waooaw.com/healthz
curl https://cp.waooaw.com/ready

# PP Gateway
curl https://pp.waooaw.com/health
curl https://pp.waooaw.com/healthz
curl https://pp.waooaw.com/ready
```

### Integration Tests

```bash
# Run against production
GATEWAY_URL=https://cp.waooaw.com pytest src/gateway/tests/test_integration.py -v
```

### Load Testing

```bash
# Install k6
brew install k6  # macOS
# or download from https://k6.io/

# Run load test
k6 run load-tests/k6-cp-gateway.js --env URL=https://cp.waooaw.com
```

## Monitoring

### Cloud Logging

```bash
# View CP Gateway logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=cp-gateway" \
    --limit=50 \
    --format=json

# View PP Gateway logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=pp-gateway" \
    --limit=50 \
    --format=json
```

### Cloud Monitoring

```bash
# View metrics in Cloud Console
open "https://console.cloud.google.com/monitoring/dashboards?project=$GCP_PROJECT_ID"

# Create alert policy
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="Gateway High Error Rate" \
    --condition-display-name="Error rate > 5%" \
    --condition-threshold-value=0.05 \
    --condition-threshold-duration=300s
```

## Troubleshooting

### Common Issues

**Issue: Gateway returns 503**
- Check OPA service is healthy
- Check Redis connection
- View logs: `docker-compose logs opa redis`

**Issue: Gateway returns 401**
- Verify JWT_PUBLIC_KEY environment variable
- Check JWT token is valid and not expired
- Verify issuer matches "waooaw.com"

**Issue: Trial limit errors**
- Check OPA policies are deployed
- Verify Redis is accessible
- Check trial_mode and trial_expires_at in JWT

**Issue: Database connection errors**
- Check PostgreSQL is running
- Verify DATABASE_URL format
- Check Cloud SQL Proxy (production)

### Debug Mode

```bash
# Enable debug logging
docker-compose -f docker-compose.gateway.yml \
    -f docker-compose.debug.yml up -d

# Or set environment variable
export LOG_LEVEL=DEBUG
```

### Check Service Dependencies

```bash
# Test OPA
curl http://opa:8181/health

# Test Redis
redis-cli -h redis ping

# Test PostgreSQL
psql "$DATABASE_URL" -c "SELECT 1"

# Test Plant Service
curl http://plant-service:8080/health
```

## Rollback

```bash
# List revisions
gcloud run revisions list --service=cp-gateway --region=$GCP_REGION

# Rollback to previous revision
gcloud run services update-traffic cp-gateway \
    --to-revisions=cp-gateway-00002-xyz=100 \
    --region=$GCP_REGION
```

## Performance Tuning

### Cloud Run Configuration

```bash
# Increase resources for high load
gcloud run services update cp-gateway \
    --cpu=4 \
    --memory=2Gi \
    --max-instances=20 \
    --region=$GCP_REGION

# Configure concurrency
gcloud run services update cp-gateway \
    --concurrency=100 \
    --region=$GCP_REGION
```

### Redis Caching

```bash
# Increase OPA cache TTL (in gateway code)
OPA_CACHE_TTL=300  # 5 minutes

# Monitor cache hit rate
redis-cli INFO stats | grep keyspace_hits
```

## Security

### Network Policies

```bash
# Restrict ingress (production)
gcloud run services update cp-gateway \
    --ingress=internal-and-cloud-load-balancing \
    --region=$GCP_REGION
```

### Secrets Rotation

```bash
# Rotate JWT keys
gcloud secrets versions add jwt-public-key --data-file=./keys/jwt_public_new.pem

# Rotate database password
gcloud sql users set-password postgres \
    --instance=waooaw-postgres \
    --password=$(openssl rand -base64 32)

# Update secret
echo "postgresql://user:newpass@..." | \
    gcloud secrets versions add database-url --data-file=-
```

## Maintenance

### Database Migrations

```bash
# Run migrations
./cloud_sql_proxy -instances=$INSTANCE_CONNECTION_NAME=tcp:5432 &
psql "postgresql://postgres@localhost:5432/waooaw" \
    < infrastructure/database/migrations/gateway_audit_logs.sql
```

### OPA Policy Updates

```bash
# Deploy new policies
cd infrastructure/opa
./build-and-deploy.sh
```

## Support

For issues or questions:
- Slack: #waooaw-gateway
- Email: devops@waooaw.com
- Runbook: [RUNBOOK.md](./RUNBOOK.md)
