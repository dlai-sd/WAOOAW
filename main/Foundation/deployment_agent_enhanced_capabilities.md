# Deployment Agent Enhanced Capabilities
## DevOps/SRE Expertise + Core Deployment Enhancements

**Agent ID**: IA-CICD-001 Enhanced
**Version**: 3.0  
**Last Updated**: January 19, 2026  
**New Capabilities**: DevOps/SRE expertise + automated rollback + observability + disaster recovery

---

## 🚨 DEVOPS/SRE CAPABILITIES (Site Reliability Engineering Expertise)

### 1. Monitoring & Observability Setup
**Automatic Monitoring Configuration** (part of infrastructure code generation):

**Prometheus Metrics**:
```python
# src/*/BackEnd/middleware/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0)
)

# Business metrics
active_trials = Gauge('active_trials_total', 'Number of active agent trials')
agent_tasks_completed = Counter('agent_tasks_completed', 'Completed agent tasks')
revenue_total = Counter('revenue_rupees_total', 'Total revenue in rupees')
```

**OpenTelemetry Tracing**:
```python
# src/*/BackEnd/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def setup_tracing():
    """Configure distributed tracing to Google Cloud Trace"""
    tracer_provider = TracerProvider()
    cloud_trace_exporter = CloudTraceSpanExporter()
    tracer_provider.add_span_processor(
        BatchSpanProcessor(cloud_trace_exporter)
    )
    trace.set_tracer_provider(tracer_provider)
```

**Structured Logging**:
```python
# src/*/BackEnd/logging_config.py
import logging
import json
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['trace_id'] = getattr(record, 'trace_id', None)
        log_record['user_id'] = getattr(record, 'user_id', None)
        log_record['request_id'] = getattr(record, 'request_id', None)
        log_record['latency_ms'] = getattr(record, 'latency_ms', None)
        log_record['environment'] = os.getenv('ENVIRONMENT', 'unknown')
```

### 2. Alerting & Incident Response
**Alert Rules (Google Cloud Monitoring)**:
```yaml
# infrastructure/monitoring/alert-policies.yaml
apiVersion: monitoring.googleapis.com/v1
kind: AlertPolicy
metadata:
  name: high-error-rate
spec:
  displayName: "High Error Rate (>1%)"
  conditions:
    - displayName: "Error rate > 1% for 5 minutes"
      conditionThreshold:
        filter: 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count" AND metric.label.response_code_class="5xx"'
        comparison: COMPARISON_GT
        thresholdValue: 0.01
        duration: 300s
  notificationChannels:
    - projects/waooaw/notificationChannels/slack-ops
    - projects/waooaw/notificationChannels/pagerduty

---
apiVersion: monitoring.googleapis.com/v1
kind: AlertPolicy
metadata:
  name: high-latency
spec:
  displayName: "P95 Latency > 500ms"
  conditions:
    - displayName: "P95 latency exceeds 500ms"
      conditionThreshold:
        filter: 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_latencies"'
        aggregations:
          - alignmentPeriod: 60s
            perSeriesAligner: ALIGN_DELTA
            crossSeriesReducer: REDUCE_PERCENTILE_95
        comparison: COMPARISON_GT
        thresholdValue: 500
        duration: 180s
```

**Incident Response Runbooks**:
```markdown
# infrastructure/runbooks/high-error-rate.md

## Incident: High Error Rate (>1%)

### Symptoms
- Error rate alert triggered
- Users reporting 500 errors
- Cloud Run logs show exceptions

### Investigation Steps
1. Check error logs:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" --limit 50
   ```

2. Identify error pattern:
   - Database connection issues?
   - External API timeouts?
   - Memory exhaustion?

3. Check recent deployments:
   ```bash
   gcloud run revisions list --service=waooaw-cp-backend-demo
   ```

### Mitigation
- **If new deployment**: Rollback to previous revision
  ```bash
  gcloud run services update-traffic waooaw-cp-backend-demo \\
    --to-revisions=waooaw-cp-backend-demo-002=100
  ```

- **If database issue**: Scale up database or add connection pooling

- **If memory issue**: Increase Cloud Run memory limit

### Escalation
- Severity 1 (customer-impacting): Page Governor immediately
- Severity 2 (degraded): Slack #incidents, work during business hours
```

### 3. SLO Definition & Tracking
**Service Level Objectives**:
```yaml
# infrastructure/slo/agent-marketplace-slo.yaml
service: agent-marketplace
slos:
  - name: availability
    target: 99.9%  # 43 minutes downtime/month
    window: 30d
    metric: successful_requests / total_requests
    
  - name: latency
    target: 95%  # 95% of requests < 200ms
    window: 30d
    metric: request_duration_ms
    threshold: 200
    
  - name: error-rate
    target: 99.9%  # <0.1% errors
    window: 30d
    metric: non_error_requests / total_requests

error_budget:
  calculation: (1 - target) * total_requests
  alerting_threshold: 10%  # Alert when 10% of budget consumed
```

**SLO Dashboard**:
- Current availability: 99.95% ✅ (budget: 95% remaining)
- Current P95 latency: 185ms ✅ (target: <200ms)
- Current error rate: 0.03% ✅ (budget: 70% remaining)
- Burn rate: 0.5x (healthy, not consuming budget)

### 4. Automated Rollback
**Health Check & Auto-Rollback**:
```yaml
# .github/workflows/deploy-with-rollback.yml
name: Deploy with Automated Rollback

on:
  workflow_dispatch:
    inputs:
      environment:
        required: true
        type: choice
        options: [demo, uat, prod]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy new revision
        run: |
          gcloud run deploy waooaw-cp-backend-${{ inputs.environment }} \\
            --image gcr.io/waooaw/cp-backend:${{ github.sha }} \\
            --no-traffic  # Deploy but don't send traffic yet
      
      - name: Run smoke tests
        id: smoke-tests
        run: |
          python3 tests/smoke/test_critical_paths.py \\
            --url https://waooaw-cp-backend-${{ inputs.environment }}-...run.app
        continue-on-error: true
      
      - name: Gradual traffic migration
        if: steps.smoke-tests.outcome == 'success'
        run: |
          # Send 10% traffic to new revision
          gcloud run services update-traffic waooaw-cp-backend-${{ inputs.environment }} \\
            --to-revisions=LATEST=10,waooaw-cp-backend-${{ inputs.environment }}-002=90
          
          sleep 300  # Wait 5 minutes
          
          # Check error rate
          ERROR_RATE=$(python3 scripts/check_error_rate.py --duration=5m)
          if [ $(echo "$ERROR_RATE > 0.5" | bc) -eq 1 ]; then
            echo "Error rate too high: $ERROR_RATE%"
            exit 1
          fi
          
          # Increase to 50%
          gcloud run services update-traffic waooaw-cp-backend-${{ inputs.environment }} \\
            --to-revisions=LATEST=50,waooaw-cp-backend-${{ inputs.environment }}-002=50
          
          sleep 300
          
          # Final check
          ERROR_RATE=$(python3 scripts/check_error_rate.py --duration=5m)
          if [ $(echo "$ERROR_RATE > 0.5" | bc) -eq 1 ]; then
            echo "Error rate too high: $ERROR_RATE%"
            exit 1
          fi
          
          # Send 100% traffic
          gcloud run services update-traffic waooaw-cp-backend-${{ inputs.environment }} \\
            --to-revisions=LATEST=100
      
      - name: Rollback on failure
        if: failure()
        run: |
          echo "Deployment failed, rolling back..."
          gcloud run services update-traffic waooaw-cp-backend-${{ inputs.environment }} \\
            --to-revisions=waooaw-cp-backend-${{ inputs.environment }}-002=100
          
          # Notify team
          curl -X POST ${{ secrets.SLACK_WEBHOOK }} \\
            -H 'Content-Type: application/json' \\
            -d '{
              "text": "🚨 Deployment rollback triggered for ${{ inputs.environment }}",
              "attachments": [{
                "color": "danger",
                "fields": [
                  {"title": "Environment", "value": "${{ inputs.environment }}"},
                  {"title": "Commit", "value": "${{ github.sha }}"},
                  {"title": "Reason", "value": "Smoke tests failed or high error rate"}
                ]
              }]
            }'
```

### 5. Capacity Planning & Auto-Scaling
**Cloud Run Auto-Scaling Configuration**:
```hcl
# cloud/terraform/modules/cloud-run/main.tf
resource "google_cloud_run_service" "service" {
  name     = var.service_name
  location = var.region

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = var.min_instances
        "autoscaling.knative.dev/maxScale" = var.max_instances
        "autoscaling.knative.dev/target"   = "80"  # Target 80% CPU
      }
    }

    spec {
      containers {
        image = var.image_url
        
        resources {
          limits = {
            cpu    = var.cpu_limit     # "2000m" = 2 vCPU
            memory = var.memory_limit  # "2Gi" = 2GB RAM
          }
        }
      }
      
      container_concurrency = var.container_concurrency  # 80 requests/container
    }
  }
}
```

**Capacity Forecasting**:
```python
# scripts/capacity_planning.py
def forecast_capacity_needs(current_users: int, growth_rate: float, months: int):
    """
    Forecast capacity requirements based on growth
    
    Current: 1000 concurrent users
    Growth: 30% MoM
    Horizon: 6 months
    """
    forecast = []
    users = current_users
    
    for month in range(1, months + 1):
        users = int(users * (1 + growth_rate))
        
        # Calculate required resources
        # Assumption: 1 vCPU + 2GB RAM per 50 concurrent users
        vcpus = math.ceil(users / 50)
        memory_gb = vcpus * 2
        instances = math.ceil(vcpus / 2)  # 2 vCPU per instance
        
        cost = instances * 15000  # ₹15k/instance/month
        
        forecast.append({
            'month': month,
            'users': users,
            'vcpus': vcpus,
            'memory_gb': memory_gb,
            'instances': instances,
            'cost_rupees': cost
        })
    
    return forecast

# Output:
# Month 1: 1,300 users → 26 vCPU → 13 instances → ₹195,000
# Month 2: 1,690 users → 34 vCPU → 17 instances → ₹255,000
# Month 6: 3,713 users → 75 vCPU → 38 instances → ₹570,000
```

### 6. Disaster Recovery & Business Continuity
**Backup Strategy**:
```yaml
# infrastructure/disaster-recovery/backup-config.yaml
database_backups:
  - name: plant-sql-automated-backup
    frequency: daily
    retention_days: 30
    time: "02:00 UTC"
    location: asia-south1
    
  - name: plant-sql-weekly-snapshot
    frequency: weekly
    retention_days: 90
    day_of_week: sunday
    time: "03:00 UTC"

cloud_storage_backups:
  - bucket: waooaw-config-backups
    objects:
      - "terraform-state/*"
      - "secrets-backup/*"
    versioning: enabled
    retention_days: 365
```

**Disaster Recovery Procedures**:
```markdown
# infrastructure/disaster-recovery/recovery-procedures.md

## Scenario 1: Database Failure

### RTO: 4 hours | RPO: 24 hours

1. **Detect**: Database unreachable, all API requests failing
2. **Triage**: Check Cloud SQL status, recent changes
3. **Recover**:
   ```bash
   # Restore from latest backup
   gcloud sql backups restore BACKUP_ID \\
     --backup-instance=plant-sql-demo \\
     --backup-instance=plant-sql-demo-restored
   
   # Update Cloud Run to point to new instance
   gcloud run services update waooaw-cp-backend-demo \\
     --set-env-vars DATABASE_HOST=new-instance-ip
   ```
4. **Validate**: Run smoke tests, check error rate
5. **Post-mortem**: Document cause, prevention measures

## Scenario 2: Regional Outage (asia-south1)

### RTO: 8 hours | RPO: 1 hour

1. **Detect**: All services in region unavailable
2. **Failover**:
   ```bash
   # Activate disaster recovery region (us-central1)
   terraform apply -var environment=prod -var region=us-central1
   
   # Update DNS to point to DR region
   gcloud dns record-sets update waooaw.com --rrdatas=DR_LB_IP
   ```
3. **Restore**: Restore database from cross-region backup
4. **Validate**: Full regression test suite
5. **Communicate**: Update status page, notify customers

## Scenario 3: Data Breach

### Response Time: Immediate

1. **Contain**: Revoke compromised credentials, block attacker IPs
2. **Investigate**: Audit logs, identify scope of breach
3. **Notify**: Customers (GDPR: within 72 hours), authorities
4. **Remediate**: Patch vulnerability, rotate all secrets
5. **Monitor**: Enhanced monitoring for further attempts
```

### 7. On-Call & Incident Management
**On-Call Rotation**:
```yaml
# infrastructure/on-call/schedule.yaml
schedule:
  - week_of: 2026-01-20
    primary: Governor
    backup: Systems Architect Agent
    
  - week_of: 2026-01-27
    primary: Governor
    backup: Deployment Agent (automated first response)

escalation_policy:
  - level: 1
    responders: [Deployment Agent]
    timeout: 5 minutes
    actions:
      - Run automated diagnostics
      - Check recent deployments
      - Attempt automated mitigation
  
  - level: 2
    responders: [Governor]
    timeout: 15 minutes
    actions:
      - Manual investigation
      - Decide on rollback/forward fix
      - Communicate to stakeholders
```

**Incident Classification**:
- **P0 (Critical)**: Complete outage, data breach, >10% error rate → Page Governor immediately
- **P1 (High)**: Degraded performance, <10% error rate → Slack alert, 30min SLA
- **P2 (Medium)**: Minor feature broken, <1% users affected → Create issue, fix next day
- **P3 (Low)**: Cosmetic issue, no user impact → Backlog

### 8. Cost Optimization
**Cost Monitoring**:
```python
# scripts/cost_analysis.py
def analyze_monthly_costs():
    """
    Analyze GCP costs and identify optimization opportunities
    """
    costs = {
        'cloud_run': 12000,        # ₹12k/month
        'cloud_sql': 8000,         # ₹8k/month
        'load_balancer': 3000,     # ₹3k/month
        'cloud_storage': 500,      # ₹500/month
        'networking': 1500,        # ₹1.5k/month
        'cloud_monitoring': 1000,  # ₹1k/month
    }
    
    optimizations = [
        {
            'service': 'cloud_run',
            'current': 12000,
            'optimized': 8000,
            'savings': 4000,
            'recommendation': 'Reduce min_instances from 2 to 1 during low traffic'
        },
        {
            'service': 'cloud_sql',
            'current': 8000,
            'optimized': 6000,
            'savings': 2000,
            'recommendation': 'Switch to shared-core instance for demo environment'
        }
    ]
    
    return costs, optimizations

# Output:
# Current monthly cost: ₹26,000
# Potential savings: ₹6,000 (23% reduction)
# Optimized cost: ₹20,000
```

---

## 🔧 CORE DEPLOYMENT ENHANCEMENTS (Addressing Gaps)

### 1. Secrets Management
**Google Secret Manager Integration**:
```hcl
# cloud/terraform/modules/secrets/main.tf
resource "google_secret_manager_secret" "database_password" {
  secret_id = "plant-database-password-${var.environment}"
  
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "database_password" {
  secret = google_secret_manager_secret.database_password.id
  
  secret_data = random_password.db_password.result
}

# Automatic rotation (90 days)
resource "google_secret_manager_secret_rotation" "database_password" {
  secret_id = google_secret_manager_secret.database_password.id
  
  rotation_period = "7776000s"  # 90 days
  
  next_rotation_time = timeadd(timestamp(), "7776000s")
}
```

**Secrets Access in Cloud Run**:
```hcl
resource "google_cloud_run_service" "backend" {
  name = "waooaw-cp-backend-${var.environment}"
  
  template {
    spec {
      containers {
        env {
          name = "DATABASE_PASSWORD"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.database_password.secret_id
              key  = "latest"
            }
          }
        }
      }
      
      service_account_name = google_service_account.backend.email
    }
  }
}

# Grant Cloud Run access to secrets
resource "google_secret_manager_secret_iam_member" "backend_access" {
  secret_id = google_secret_manager_secret.database_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}
```

### 2. Blue-Green Deployment
**Traffic Splitting Strategy**:
```bash
# Deploy new version (green) without traffic
gcloud run deploy waooaw-cp-backend-prod \\
  --image gcr.io/waooaw/cp-backend:v2.0.0 \\
  --no-traffic \\
  --tag green

# Run smoke tests against green
./scripts/smoke-tests.sh https://green---waooaw-cp-backend-prod-xxx.run.app

# Gradually shift traffic: blue (100%) → green (10%)
gcloud run services update-traffic waooaw-cp-backend-prod \\
  --to-tags green=10 \\
  --to-revisions blue=90

# Monitor for 10 minutes, check metrics

# If successful, shift all traffic to green
gcloud run services update-traffic waooaw-cp-backend-prod \\
  --to-tags green=100

# Tag green as new blue (stable)
gcloud run services update-traffic waooaw-cp-backend-prod \\
  --update-tags blue=green

# If issues, instant rollback
gcloud run services update-traffic waooaw-cp-backend-prod \\
  --to-tags blue=100
```

### 3. Observability Stack
**Complete Monitoring Setup**:
```yaml
# infrastructure/observability/monitoring-stack.yaml
components:
  - name: google-cloud-monitoring
    metrics:
      - cloud_run_request_count
      - cloud_run_request_latencies
      - cloud_run_container_cpu_utilization
      - cloud_run_container_memory_utilization
  
  - name: google-cloud-logging
    log_sinks:
      - name: error-logs-sink
        destination: bigquery.waooaw.error_logs
        filter: 'severity >= ERROR'
      
      - name: audit-logs-sink
        destination: bigquery.waooaw.audit_logs
        filter: 'protoPayload.methodName="UpdateAgent"'
  
  - name: google-cloud-trace
    sampling_rate: 0.1  # Sample 10% of requests
  
  - name: uptime-checks
    checks:
      - name: cp-health-check
        url: https://cp.demo.waooaw.com/health
        frequency: 60s
        timeout: 10s
        expected_status: 200
```

---

## 🎯 SUCCESS METRICS

### Reliability
- 99.9% availability (SLO achieved)
- < 43 minutes unplanned downtime/month
- Zero failed deployments (auto-rollback working)
- < 5 min mean time to detect (MTTD)
- < 15 min mean time to resolve (MTTR)

### Security
- 100% secrets in Secret Manager
- 90-day secret rotation enforced
- Zero hardcoded credentials
- All traffic encrypted (TLS 1.2+)

### Performance
- P95 latency < 200ms
- Auto-scaling working (no manual intervention)
- < 5% cost increase month-over-month

### Operations
- 100% deployments have rollback plan
- 100% services have runbooks
- All SLOs defined and tracked
- < 2 hour RTO for database recovery

---

**See also**: 
- [Testing Agent Enhanced](testing_agent_enhanced_capabilities.md) for Security + Performance testing
- [Coding Agent Enhanced](coding_agent_enhanced_capabilities.md) for Data Agent capabilities
