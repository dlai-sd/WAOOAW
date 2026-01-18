# Plant Infrastructure & Deployment - Phase 2

**Document:** Cloud Run, PostgreSQL, Redis, Monitoring Setup  
**Date:** 2026-01-14  
**Status:** Planning Complete, Ready for Deployment  
**Target Environment:** GCP (Google Cloud Platform)  

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    WAOOAW Plant Platform                    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Customer Portal (CP) / Partner Portal (PP)          │  │
│  │  (HTML/CSS/JS, served from Cloud Storage)            │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Cloud Load Balancer                                  │  │
│  │  (SSL/TLS termination, health checks)                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Cloud Run (Plant Backend)                            │  │
│  │  - FastAPI application                                │  │
│  │  - 2-4 instances (auto-scaling)                       │  │
│  │  - CPU: 2 cores, Memory: 4GB                          │  │
│  │  - Timeout: 300 seconds                               │  │
│  └──────────────────────────────────────────────────────┘  │
│           ↓                          ↓                       │
│  ┌──────────────────┐        ┌──────────────────┐          │
│  │  Cloud SQL       │        │  Cloud Memorystore│         │
│  │  (PostgreSQL)    │        │  (Redis)         │         │
│  │  - 2 vCPU        │        │  - 1GB standard  │         │
│  │  - 10GB storage  │        │  - HA enabled    │         │
│  │  - Backup daily  │        │  - Cache layer   │         │
│  └──────────────────┘        └──────────────────┘          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Observability                                        │  │
│  │  - Cloud Logging (application logs)                  │  │
│  │  - Cloud Monitoring (metrics, alerting)              │  │
│  │  - Cloud Trace (request tracing)                     │  │
│  │  - Error Reporting (crash detection)                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Cloud Run (Backend API)

**Purpose:** Managed compute for FastAPI application

**Configuration:**

```yaml
name: plant-backend
service_account: plant-backend-sa@project-id.iam.gserviceaccount.com
docker_image: gcr.io/project-id/plant-backend:latest
memory: "4Gi"
cpu: "2"
timeout: "300s"
min_instances: 1
max_instances: 4
concurrency: 100

environment_variables:
  DATABASE_URL: postgresql+asyncpg://user:pass@cloud-sql-proxy/plant_db
  REDIS_URL: redis://memorystore-redis.internal:6379
  LOG_LEVEL: info
  ENVIRONMENT: production

vpc_connector: plant-vpc-connector
port: 8000
health_check:
  path: /health
  initial_delay: 10
  timeout: 5
  period: 10
```

**Deployment:**

```bash
# Build Docker image
docker build -t gcr.io/project-id/plant-backend:latest .
docker push gcr.io/project-id/plant-backend:latest

# Deploy to Cloud Run
gcloud run deploy plant-backend \
  --image gcr.io/project-id/plant-backend:latest \
  --platform managed \
  --region us-central1 \
  --memory 4Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 4 \
  --timeout 300 \
  --set-env-vars DATABASE_URL=postgresql+asyncpg://...,REDIS_URL=redis://...
```

### 2. Cloud SQL (PostgreSQL Database)

**Purpose:** Primary relational database for agents, skills, job roles

**Configuration:**

```yaml
instance_name: plant-postgres
database_version: POSTGRES_15
tier: db-custom-2-8192  # 2 vCPU, 8GB RAM
storage_gb: 100
storage_auto_increase: true
backup:
  enabled: true
  start_time: "03:00"  # UTC
  backup_location: us
  transaction_log_retention_days: 7
high_availability: true
replica_region: us-east1
```

**Setup:**

```sql
-- Create database
CREATE DATABASE plant_db;

-- Create users
CREATE USER plant_app_user WITH PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE plant_db TO plant_app_user;

-- Create schema
\c plant_db
CREATE SCHEMA plant;
SET search_path TO plant;

-- Run migrations (Alembic)
alembic upgrade head
```

**Connections:**

- **Application Connection:** Cloud SQL Auth proxy on localhost:5432
- **Backup:** Automatic daily, point-in-time recovery (7 days)
- **Monitoring:** Query insights, slow query logging

### 3. Cloud Memorystore (Redis Cache)

**Purpose:** Session cache, rate limiting, background job queue

**Configuration:**

```yaml
instance_id: plant-redis
tier: standard
memory_size_gb: 1
region: us-central1
redis_version: 7.0
vpc_network: plant-network
backup:
  enabled: true
  start_hour: 3  # UTC
monitoring:
  enabled: true
  rdb_size_gb: 1
```

**Usage:**

```python
# Connection string
redis_url = "redis://10.0.0.3:6379/0"

# Session management
session_ttl = 86400  # 24 hours

# Rate limiting
rate_limit_key = f"rate_limit:{user_id}:{endpoint}"
rate_limit_window = 60  # seconds

# Cache layer
cache_ttl = 3600  # 1 hour
```

### 4. Cloud Load Balancer

**Purpose:** Distribute traffic, SSL/TLS termination, DDoS protection

**Configuration:**

```yaml
name: plant-backend-lb
protocol: HTTPS
port: 443
ssl_certificate:
  name: plant-backend-cert
  domains:
    - api.waooaw.com
    - api-staging.waooaw.com
health_check:
  path: /health
  interval: 10
  timeout: 5
  healthy_threshold: 2
  unhealthy_threshold: 3
backend_services:
  - plant-backend-bes
session_affinity: CLIENT_IP
cdn_enabled: true
```

---

## Deployment Checklist

### Pre-Deployment (Week 1)

- [ ] **GCP Project Setup**
  - [ ] Create GCP project
  - [ ] Enable required APIs (Cloud Run, Cloud SQL, Memorystore, etc.)
  - [ ] Set up billing alerts
  - [ ] Configure IAM roles

- [ ] **Network Setup**
  - [ ] Create VPC network
  - [ ] Create VPC connector for Cloud Run ↔ Cloud SQL
  - [ ] Configure firewall rules
  - [ ] Setup Cloud NAT for outbound internet access

- [ ] **Service Accounts**
  - [ ] Create `plant-backend-sa` service account
  - [ ] Grant required IAM roles (Cloud SQL client, Monitoring, Logging)
  - [ ] Create and download service account key

- [ ] **Secret Management**
  - [ ] Create Secret Manager secrets:
    - [ ] DATABASE_PASSWORD
    - [ ] REDIS_PASSWORD
    - [ ] JWT_SECRET_KEY
    - [ ] API_KEYS

### Phase 1: Database Setup (Week 1)

- [ ] **PostgreSQL Instance**
  - [ ] Create Cloud SQL PostgreSQL 15 instance
  - [ ] Configure machine type (db-custom-2-8192)
  - [ ] Set up backup schedule (daily at 3 AM UTC)
  - [ ] Enable high availability (HA replica)
  - [ ] Create database `plant_db`

- [ ] **Database Initialization**
  - [ ] Run Alembic migrations
  - [ ] Create default seed data
  - [ ] Set up indexes for performance
  - [ ] Configure Query Insights logging

- [ ] **Cloud SQL Auth Proxy**
  - [ ] Install Cloud SQL proxy in Cloud Run
  - [ ] Test local connection
  - [ ] Verify SSL/TLS handshake

### Phase 2: Cache Setup (Week 1)

- [ ] **Redis Instance**
  - [ ] Create Cloud Memorystore Redis instance
  - [ ] Configure 1GB standard tier
  - [ ] Enable backup and point-in-time recovery
  - [ ] Set up monitoring and alerting

- [ ] **Redis Client Setup**
  - [ ] Install redis-py in backend
  - [ ] Test connection and basic operations
  - [ ] Setup connection pooling
  - [ ] Verify failover behavior (if HA enabled)

### Phase 3: Backend Deployment (Week 2)

- [ ] **Docker Image**
  - [ ] Create Dockerfile (multi-stage build)
  - [ ] Build image: `docker build -t gcr.io/PROJECT/plant-backend:v1.0.0 .`
  - [ ] Push to Container Registry: `docker push ...`
  - [ ] Scan image for vulnerabilities

- [ ] **Cloud Run Service**
  - [ ] Deploy to Cloud Run
  - [ ] Configure 2 vCPU, 4GB memory
  - [ ] Set min instances = 1, max = 4
  - [ ] Configure environment variables from Secret Manager
  - [ ] Setup VPC connector

- [ ] **Health Checks**
  - [ ] Test `/health` endpoint
  - [ ] Verify database connectivity
  - [ ] Verify Redis connectivity
  - [ ] Test startup/shutdown lifecycle

### Phase 4: Load Balancer & CDN (Week 2)

- [ ] **Load Balancer Setup**
  - [ ] Create Cloud Load Balancer
  - [ ] Provision SSL certificate (Google-managed or custom)
  - [ ] Configure backend service pointing to Cloud Run
  - [ ] Setup health check policy
  - [ ] Enable Cloud CDN for static assets

- [ ] **DNS Configuration**
  - [ ] Create DNS A record: `api.waooaw.com` → Load Balancer IP
  - [ ] Setup CAA records for SSL certificate validation
  - [ ] Test DNS resolution

### Phase 5: Monitoring & Observability (Week 2)

- [ ] **Logging**
  - [ ] Configure Cloud Logging sink for application logs
  - [ ] Setup structured logging (JSON format)
  - [ ] Create log filters for errors/warnings
  - [ ] Setup log-based metrics

- [ ] **Monitoring**
  - [ ] Create monitoring dashboard
  - [ ] Setup metrics:
    - [ ] Request count / latency
    - [ ] Error rates
    - [ ] Database connection pool
    - [ ] Redis cache hit rate
    - [ ] Cloud Run CPU / Memory / Concurrent requests

- [ ] **Alerting**
  - [ ] Error rate > 1% → Alert
  - [ ] P99 latency > 1s → Alert
  - [ ] Database CPU > 80% → Alert
  - [ ] Redis memory > 90% → Alert

- [ ] **Tracing**
  - [ ] Enable Cloud Trace
  - [ ] Configure sampling rate (10%)
  - [ ] Verify trace collection

### Phase 6: Security & Compliance (Week 3)

- [ ] **Network Security**
  - [ ] Enable VPC Service Controls
  - [ ] Configure firewall rules (deny all, allow specific)
  - [ ] Setup Cloud Armor for DDoS protection
  - [ ] Enable binary authorization

- [ ] **Data Security**
  - [ ] Enable encryption at rest (Cloud SQL, Redis)
  - [ ] Enable encryption in transit (TLS 1.3)
  - [ ] Rotate credentials quarterly
  - [ ] Implement secret rotation policy

- [ ] **Audit & Compliance**
  - [ ] Enable Cloud Audit Logs
  - [ ] Setup data loss prevention (DLP)
  - [ ] Review IAM assignments quarterly
  - [ ] Document security policies

### Phase 7: Testing & Validation (Week 3)

- [ ] **Functional Tests**
  - [ ] Run API test suite against production
  - [ ] Verify database queries work
  - [ ] Test cache invalidation
  - [ ] Validate error handling

- [ ] **Load Tests**
  - [ ] Execute load test scenarios (see LOAD_TESTS_GUIDE.md)
  - [ ] Verify SLA targets met:
    - [ ] P95 latency < 500ms
    - [ ] Throughput > 1000 req/s
    - [ ] Error rate < 0.1%

- [ ] **Failover Tests**
  - [ ] Test Cloud Run instance failure recovery
  - [ ] Test Cloud SQL replica failover
  - [ ] Test connection timeout handling
  - [ ] Verify backup restoration

---

## Deployment Commands

### GCP Project Setup

```bash
# Set project ID
export PROJECT_ID=waooaw-prod
gcloud config set project $PROJECT_ID

# Enable APIs
gcloud services enable \
  compute.googleapis.com \
  run.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com

# Create service account
gcloud iam service-accounts create plant-backend-sa \
  --display-name="Plant Backend Service Account"

# Grant roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:plant-backend-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:plant-backend-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/monitoring.metricWriter"
```

### PostgreSQL Setup

```bash
# Create instance
gcloud sql instances create plant-postgres \
  --database-version=POSTGRES_15 \
  --tier=db-custom-2-8192 \
  --storage-size=100GB \
  --backup-start-time=03:00 \
  --availability-type=REGIONAL

# Create database
gcloud sql databases create plant_db \
  --instance=plant-postgres

# Create user
gcloud sql users create plant_app \
  --instance=plant-postgres \
  --password=<SECURE-PASSWORD>

# Get connection name
gcloud sql instances describe plant-postgres \
  --format='value(connectionName)'
```

### Redis Setup

```bash
# Create instance
gcloud redis instances create plant-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=7.0 \
  --backup-start-hour=3

# Get IP address
gcloud redis instances describe plant-redis \
  --region=us-central1 \
  --format='value(host)'
```

### Cloud Run Deployment

```bash
# Build and push image
docker build -t gcr.io/$PROJECT_ID/plant-backend:v1.0.0 .
docker push gcr.io/$PROJECT_ID/plant-backend:v1.0.0

# Deploy
gcloud run deploy plant-backend \
  --image=gcr.io/$PROJECT_ID/plant-backend:v1.0.0 \
  --platform=managed \
  --region=us-central1 \
  --memory=4Gi \
  --cpu=2 \
  --min-instances=1 \
  --max-instances=4 \
  --service-account=plant-backend-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars DATABASE_URL=postgresql+asyncpg://user:pass@...
```

---

## Monitoring & Alerting

### Key Metrics to Monitor

```
Backend Health:
- Request count (per second)
- Response latency (P50, P95, P99)
- Error rate (4xx, 5xx)
- Request size distribution

Database Health:
- Connection count
- Query latency
- Slow queries (>1s)
- CPU/Memory usage
- Storage usage

Cache Health:
- Cache hit rate
- Eviction rate
- Memory usage
- Connection count

Cloud Run Health:
- CPU usage
- Memory usage
- Concurrent requests
- Billing estimate
```

### Alert Thresholds

```yaml
alerts:
  - name: high_error_rate
    condition: error_rate > 1%
    severity: critical
    window: 5m
    
  - name: high_latency
    condition: p99_latency > 1000ms
    severity: high
    window: 10m
    
  - name: database_cpu_high
    condition: database_cpu > 80%
    severity: high
    window: 5m
    
  - name: redis_memory_high
    condition: redis_memory > 90%
    severity: medium
    window: 5m
    
  - name: cloud_run_oom
    condition: out_of_memory_errors > 5
    severity: critical
    window: 1m
```

---

## Cost Estimation (Monthly)

| Component | Size | Cost |
|-----------|------|------|
| Cloud Run | 2 vCPU, 4GB | $60-150 (varies by traffic) |
| Cloud SQL | db-custom-2-8192 | $150-200 |
| Cloud Memorystore | 1GB Redis | $20-30 |
| Load Balancer | Fixed + per GB | $20-50 |
| Data transfer | Outbound | $0.12/GB |
| **Total** | | **$250-430/month** |

*Costs scale with traffic; higher traffic = more Cloud Run instances*

---

## Backup & Recovery

### Automated Backups

```sql
-- PostgreSQL Backups
-- - Daily automated backup (3 AM UTC)
-- - 7-day retention with transaction logs
-- - Point-in-time recovery available

-- Redis Backups
-- - Daily automated backup (3 AM UTC)
-- - Stored in Google Cloud Storage
-- - 30-day retention
```

### Manual Backup

```bash
# Export PostgreSQL to Cloud Storage
gcloud sql backups create \
  --instance=plant-postgres \
  --description="manual-backup-2026-01-14"

# Export data to CSV
gcloud sql export csv gs://plant-backups/agents.csv \
  --instance=plant-postgres \
  --query="SELECT * FROM plant.agents"
```

### Restore Procedures

```bash
# Restore PostgreSQL to point-in-time
gcloud sql backups restore BACKUP_ID \
  --instance=plant-postgres \
  --backup-instance=plant-postgres-old

# Restore Redis from snapshot
gcloud redis instances restore plant-redis \
  --snapshot-name=plant-redis-snapshot-2026-01-14
```

---

## Troubleshooting

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Cloud Run → Cloud SQL connection fails | Network config | Verify VPC connector, check firewall rules |
| High API latency | Database slow queries | Enable Query Insights, add indexes |
| Redis cache misses | Eviction policy | Increase Redis memory or adjust TTLs |
| Out of memory (OOM) | Memory leak | Review logs, profile application, increase instance memory |
| SSL certificate errors | Certificate expired | Renew certificate, verify DNS CAA records |
| High GCP costs | Excessive traffic/storage | Optimize queries, compress responses, adjust instance sizes |

---

## Security Best Practices

1. **Network Isolation**
   - Use VPC to isolate databases from public internet
   - Enable Private IP for Cloud SQL and Redis
   - Use VPC Service Controls for data exfiltration prevention

2. **Access Control**
   - Use IAM for service account management
   - Enable MFA for human users
   - Implement least-privilege access

3. **Encryption**
   - Enable encryption at rest (default in GCP)
   - Enforce TLS 1.3 for in-transit data
   - Rotate credentials quarterly

4. **Monitoring & Logging**
   - Enable Cloud Audit Logs for compliance
   - Monitor for suspicious activity
   - Setup alerts for unauthorized access attempts

---

## Success Criteria

✅ **Phase 2 Deployment Complete When:**
- [ ] Cloud Run serving 100+ requests/second
- [ ] P95 latency < 500ms
- [ ] Error rate < 0.1%
- [ ] Database backup working automatically
- [ ] Monitoring dashboards showing real-time metrics
- [ ] All security policies enforced
- [ ] Load balancer distributing traffic correctly

---

**Status:** Ready for Phase 2 Deployment ✅  
**Next Review:** After first week of production monitoring
