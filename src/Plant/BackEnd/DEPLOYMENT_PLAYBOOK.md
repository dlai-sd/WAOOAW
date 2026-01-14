# Plant Backend Deployment Playbook
## Step-by-Step Guide for Production Deployment

**Document Version:** 1.0  
**Date:** 2026-01-14  
**Target:** Production Environment (GCP Cloud Run + Cloud SQL + Redis)  

---

## Pre-Deployment Checklist

### Infrastructure Ready?
- [ ] GCP project created with billing enabled
- [ ] Service accounts created with proper IAM roles
- [ ] VPC network configured
- [ ] Cloud SQL PostgreSQL 15 instance running
- [ ] Cloud Memorystore Redis instance running
- [ ] Cloud Load Balancer configured
- [ ] SSL certificate provisioned

### Application Ready?
- [ ] All tests passing (unit, integration, load)
- [ ] Code reviewed and merged to main
- [ ] Secrets stored in Secret Manager
- [ ] Environment variables documented
- [ ] Database migrations tested
- [ ] Backup/recovery procedures validated

### Monitoring Ready?
- [ ] Cloud Monitoring dashboards created
- [ ] Alert policies configured
- [ ] Logging sink configured
- [ ] Trace collection enabled
- [ ] Error reporting configured

---

## Deployment Procedure

### Phase 1: Pre-Flight Checks (15 minutes)

**1. Verify GCP Access**
```bash
gcloud auth login
gcloud config set project waooaw-prod
gcloud config list
```

**2. Verify Infrastructure Components**
```bash
# Check Cloud SQL
gcloud sql instances describe plant-postgres

# Check Redis
gcloud redis instances describe plant-redis --region=us-central1

# Check VPC Connector
gcloud compute networks vpc-peerings list --network=plant-network
```

**3. Backup Database**
```bash
# Create backup
gcloud sql backups create \
  --instance=plant-postgres \
  --description="pre-deployment-backup-$(date +%Y%m%d-%H%M%S)"

# Verify backup
gcloud sql backups list --instance=plant-postgres
```

**4. Export Current Secrets**
```bash
# Verify secrets exist in Secret Manager
gcloud secrets list --filter="name:plant-*"

# Example secrets needed:
# - plant-db-password
# - plant-redis-password
# - plant-jwt-secret
# - plant-api-keys
```

### Phase 2: Build & Test (10 minutes)

**1. Build Docker Image**
```bash
export PROJECT_ID=waooaw-prod
export IMAGE_TAG=v1.0.0
export TIMESTAMP=$(date +%Y%m%d-%H%M%S)

cd src/Plant/BackEnd

# Build image
docker build \
  -t gcr.io/$PROJECT_ID/plant-backend:$IMAGE_TAG \
  -t gcr.io/$PROJECT_ID/plant-backend:latest \
  -t gcr.io/$PROJECT_ID/plant-backend:$TIMESTAMP \
  .

echo "✅ Image built successfully"
```

**2. Test Image Locally**
```bash
# Start container with mock environment
docker run -d \
  --name plant-backend-test \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@localhost/test" \
  -e REDIS_URL="redis://localhost:6379" \
  -e LOG_LEVEL="debug" \
  gcr.io/$PROJECT_ID/plant-backend:$IMAGE_TAG

# Wait for startup
sleep 5

# Test health endpoint
curl http://localhost:8000/health
echo "✅ Health check passed"

# Cleanup
docker stop plant-backend-test
docker rm plant-backend-test
```

**3. Scan Image for Vulnerabilities**
```bash
gcloud container images scan gcr.io/$PROJECT_ID/plant-backend:$IMAGE_TAG

# View scan results
gcloud container images describe gcr.io/$PROJECT_ID/plant-backend:$IMAGE_TAG \
  --format="get(image_summary.vulnerability)"
```

**4. Push Image to Registry**
```bash
docker push gcr.io/$PROJECT_ID/plant-backend:$IMAGE_TAG
docker push gcr.io/$PROJECT_ID/plant-backend:latest

echo "✅ Images pushed to Container Registry"
```

### Phase 3: Deploy to Cloud Run (5 minutes)

**1. Prepare Deployment Configuration**
```bash
# Get secret values for environment variables
export DB_PASSWORD=$(gcloud secrets versions access latest --secret="plant-db-password")
export REDIS_PASSWORD=$(gcloud secrets versions access latest --secret="plant-redis-password")
export JWT_SECRET=$(gcloud secrets versions access latest --secret="plant-jwt-secret")

# Get Cloud SQL connection name
export SQL_CONNECTION=$(gcloud sql instances describe plant-postgres --format='value(connectionName)')
export REDIS_HOST=$(gcloud redis instances describe plant-redis --region=us-central1 --format='value(host)')
```

**2. Deploy New Version**
```bash
gcloud run deploy plant-backend \
  --image=gcr.io/$PROJECT_ID/plant-backend:$IMAGE_TAG \
  --platform=managed \
  --region=us-central1 \
  --memory=4Gi \
  --cpu=2 \
  --timeout=300 \
  --min-instances=1 \
  --max-instances=4 \
  --concurrency=100 \
  --service-account=plant-backend-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --set-cloudsql-instances=$SQL_CONNECTION \
  --set-env-vars=\
DATABASE_URL=postgresql+asyncpg://plant_app:$DB_PASSWORD@localhost/plant_db,\
REDIS_URL=redis://:$REDIS_PASSWORD@$REDIS_HOST:6379,\
JWT_SECRET_KEY=$JWT_SECRET,\
ENVIRONMENT=production,\
LOG_LEVEL=info

echo "✅ Deployment completed"
```

**3. Get Service URL**
```bash
export SERVICE_URL=$(gcloud run services describe plant-backend \
  --region=us-central1 \
  --format='value(status.url)')

echo "Service URL: $SERVICE_URL"
```

### Phase 4: Verification (10 minutes)

**1. Check Service Status**
```bash
gcloud run services describe plant-backend --region=us-central1 --format=yaml | grep -A 5 "status:"
```

**2. Test Health Endpoint**
```bash
# Test health check
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  $SERVICE_URL/health

# Should return: {"status": "healthy", "service": "plant-backend", ...}
echo "✅ Health check passed"
```

**3. Test Database Connectivity**
```bash
# Create a test agent
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Agent",
    "specialization": "test",
    "industry": "marketing",
    "hourly_rate": 85.0
  }' \
  $SERVICE_URL/api/v1/agents/

echo "✅ API endpoint working"
```

**4. Check Cloud Logs**
```bash
# View recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=plant-backend" \
  --limit 50 \
  --format=json

# Check for errors
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" \
  --limit 10 \
  --format=json
```

**5. Monitor Metrics**
```bash
# View Cloud Run metrics
gcloud monitoring time-series list \
  --filter='resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count"'
```

### Phase 5: Traffic Migration (5-10 minutes)

**1. Gradual Traffic Shift (if using traffic splitting)**
```bash
# Update load balancer to route traffic gradually
# Step 1: 10% to new version
gcloud compute backend-services update plant-backend-service \
  --global \
  --session-affinity=CLIENT_IP

# Monitor error rates
watch -n 1 'gcloud logging read "severity=ERROR" --limit=5 --format=json'

# Step 2: If no errors, increase to 50%
# Step 3: If stable, move to 100%
```

**2. Verify Traffic is Routing**
```bash
# Check request count
gcloud monitoring read \
  --filter='metric.type="run.googleapis.com/request_count" AND resource.labels.service_name="plant-backend"' \
  --format=json

# Should show increasing request count
```

### Phase 6: Post-Deployment Validation (15 minutes)

**1. Run Smoke Tests**
```bash
# Test critical endpoints
bash scripts/smoke-tests.sh $SERVICE_URL

# Expected: All tests PASS
```

**2. Check Monitoring Dashboard**
```bash
# Open monitoring dashboard
echo "Dashboard: https://console.cloud.google.com/monitoring/dashboards/custom/plant-backend"

# Verify metrics are flowing:
# - Request count increasing
# - Error rate < 0.1%
# - P99 latency < 500ms
# - Database connections healthy
```

**3. Database Health Check**
```bash
# Check database queries are working
gcloud sql connect plant-postgres \
  --user=plant_app \
  --quiet << EOF
SELECT COUNT(*) as agent_count FROM plant.agents;
\q
EOF
```

**4. Cache Health Check**
```bash
# Test Redis connectivity
redis-cli -h $REDIS_HOST -a $REDIS_PASSWORD ping
# Expected: PONG
```

### Phase 7: Rollback Plan (if needed)

**If deployment fails, rollback to previous version:**

```bash
# Step 1: Identify previous revision
PREV_REVISION=$(gcloud run revisions list --region=us-central1 \
  --service=plant-backend \
  --format='value(name)' | sed -n '2p')

echo "Previous revision: $PREV_REVISION"

# Step 2: Route traffic back to previous revision
gcloud run services update-traffic plant-backend \
  --region=us-central1 \
  --to-revisions=$PREV_REVISION=100

echo "✅ Rolled back to $PREV_REVISION"

# Step 3: Verify rollback
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  $SERVICE_URL/health
```

---

## Monitoring During & After Deployment

### During Deployment (first 30 minutes)

```bash
# Watch logs in real-time
gcloud logging tail --limit=50 \
  "resource.type=cloud_run_revision AND resource.labels.service_name=plant-backend"

# Watch metrics dashboard
watch -n 5 'gcloud monitoring read \
  "metric.type=\"run.googleapis.com/request_count\"" \
  --format=json | jq ".[] | select(.points | length > 0) | .points[0]"'

# Alert thresholds to watch:
# - Error rate rises above 1%
# - Latency spikes above 1 second
# - Memory usage > 90%
# - CPU usage > 80%
```

### After Deployment (first 24 hours)

- [ ] Monitor error rates (should be <0.1%)
- [ ] Monitor latency percentiles (P99 <500ms)
- [ ] Monitor database connection pool
- [ ] Monitor Redis cache hit rate
- [ ] Monitor billing (check for cost anomalies)

---

## Troubleshooting Deployment

### Issue: Cloud Run fails to start

**Symptoms:** Service shows "Error" status

**Diagnosis:**
```bash
# Check logs
gcloud logging read "resource.type=cloud_run_revision AND severity=ERROR"

# Check container startup
gcloud run services describe plant-backend --format=yaml | grep -A 10 "conditions"
```

**Solutions:**
- Verify environment variables are set
- Check database connectivity
- Check Redis connectivity
- Review application startup code

### Issue: High latency after deployment

**Symptoms:** P99 latency > 1 second

**Diagnosis:**
```bash
# Check database query performance
gcloud sql connect plant-postgres --user=plant_app << EOF
SELECT query, calls, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;
\q
EOF

# Check Cloud Run metrics
gcloud monitoring read "metric.type=\"run.googleapis.com/request_latencies\""
```

**Solutions:**
- Add database indexes
- Increase Cloud Run memory/CPU
- Optimize slow queries
- Check for N+1 query patterns

### Issue: Database connection pool exhaustion

**Symptoms:** "Connection pool is exhausted" errors

**Diagnosis:**
```bash
# Check active connections
gcloud sql connect plant-postgres --user=plant_app << EOF
SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;
\q
EOF
```

**Solutions:**
- Increase database max_connections
- Reduce connection pool timeout
- Check for connection leaks in code
- Increase Cloud Run instances

---

## Successful Deployment Checklist

✅ **Green Light to Production When:**
- [ ] All smoke tests passing
- [ ] Error rate < 0.1% for 5 minutes
- [ ] P99 latency < 500ms for 5 minutes
- [ ] Database queries performing normally
- [ ] Redis cache functioning
- [ ] No critical errors in logs
- [ ] Monitoring dashboards showing normal metrics
- [ ] All dependent services responding

---

## Post-Deployment Tasks

1. **Update Documentation**
   - [ ] Record deployment date and version
   - [ ] Document any configuration changes
   - [ ] Update runbooks if needed

2. **Team Communication**
   - [ ] Notify team of successful deployment
   - [ ] Share deployment report
   - [ ] Schedule post-deployment retrospective

3. **Monitoring Setup**
   - [ ] Verify all alerts are active
   - [ ] Configure escalation procedures
   - [ ] Setup on-call rotation

4. **Backup & Recovery**
   - [ ] Verify database backup completed
   - [ ] Test backup restoration procedure
   - [ ] Document recovery steps

---

**Estimated Total Deployment Time:** 45-60 minutes  
**Estimated Rollback Time (if needed):** 5-10 minutes  

**Contact:** DevOps Team / Escalation: [on-call phone]
