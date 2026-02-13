# GCP Cloud Monitoring Configuration
# Dashboards, uptime checks, and SLO monitoring for WAOOAW Plant Backend

## Overview
This directory contains Cloud Monitoring configurations for production observability:
- **Dashboards**: Pre-built monitoring dashboards (Executive, Operations, SRE, Business)
- **Uptime Checks**: HTTP health checks for availability monitoring
- **Alert Policies**: Automated alerting for critical issues (P0/P1/P2/P3)
- **SLO Definitions**: Service Level Objectives for availability and latency

## Deployment
```bash
# Deploy all monitoring resources
cd /workspaces/WAOOAW/cloud/<environment>
./deploy-monitoring.sh

# Or apply specific resources
gcloud monitoring dashboards create --config-from-file=dashboards/executive.json
gcloud monitoring uptime-check-configs create --config-from-file=uptime-checks/backend-health.yaml
gcloud alpha monitoring policies create --policy-from-file=alerts/p0-backend-down.yaml
```

## Directory Structure
```
monitoring/
├── README.md                       # This file
├── dashboards/                     # Pre-built monitoring dashboards
│   ├── executive.json              # Executive dashboard (high-level health)
│   ├── operations.json             # Operations dashboard (deployment, errors)
│   ├── sre.json                    # SRE dashboard (latency, availability, saturation)
│   └── business.json               # Business metrics (trials, agents, goals)
├── uptime-checks/                  # HTTP uptime checks
│   ├── backend-health.yaml         # Plant Backend /health endpoint
│   ├── backend-api.yaml            # Plant Backend /api/v1/health
│   └── gateway-health.yaml         # Gateway /health endpoint
├── alerts/                         # Alert policies by severity
│   ├── p0-backend-down.yaml        # Critical: Backend unavailable
│   ├── p0-database-down.yaml       # Critical: Database connection failure
│   ├── p1-high-error-rate.yaml     # High: Error rate >5%
│   ├── p1-high-latency.yaml        # High: P95 latency >500ms
│   ├── p2-disk-space-low.yaml      # Medium: Disk space <20%
│   └── p3-trial-conversion.yaml    # Low: Trial conversion rate anomaly
├── slos/                           # Service Level Objectives
│   ├── availability-slo.yaml       # 99.9% availability target
│   └── latency-slo.yaml            # P95 <200ms, P99 <500ms
└── deploy-monitoring.sh            # Deployment script

```

## Dashboard Overview

### Executive Dashboard
**Purpose**: High-level health for leadership  
**Metrics**:
- Backend status (up/down)
- Request rate (RPM)
- Error rate (%)
- P95 latency (ms)
- Active trials
- Agent availability

**Audience**: CTO, CEO, Product Manager

### Operations Dashboard
**Purpose**: Deployment and operational health  
**Metrics**:
- Deployment status
- Container restarts
- CPU/Memory utilization
- Database connections
- API endpoint health
- Recent errors (log-based)

**Audience**: DevOps, SRE

### SRE Dashboard (Golden Signals)
**Purpose**: Detailed performance monitoring  
**Metrics**:
- **Latency**: P50/P95/P99 request duration
- **Traffic**: Requests per second by endpoint
- **Errors**: Error rate by status code
- **Saturation**: CPU, memory, DB connections

**Audience**: SRE Team

### Business Dashboard
**Purpose**: Product and customer metrics  
**Metrics**:
- Active trials
- Trial conversion rate
- Agents by status (available/working/offline)  - Goals created/executed
- Customer signups
- Goal success rate

**Audience**: Product, Customer Success

## Uptime Checks

### Backend Health Check
**Endpoint**: `https://waooaw-plant-backend-demo-*.run.app/health`  
**Frequency**: 1 minute  
**Timeout**: 10 seconds  
**Regions**: asia-south1, us-central1, europe-west1  
**Alert**: Fail 3 consecutive checks → P0 alert

### Backend API Check
**Endpoint**: `https://waooaw-plant-backend-demo-*.run.app/api/v1/health`  
**Frequency**: 5 minutes  
**Timeout**: 10 seconds  
**Regions**: asia-south1  
**Alert**: Fail 2 consecutive checks → P1 alert

## Alert Policies

### Severity Levels
- **P0 (Critical)**: Production down, immediate page
- **P1 (High)**: Degraded service, page if during business hours
- **P2 (Medium)**: Warning, notify via Slack
- **P3 (Low)**: Info, daily digest email

### P0 Alerts
1. **Backend Down**
   - Trigger: Uptime check fails 3 consecutive times
   - Notification: PagerDuty (immediate page)
   - Action: Auto-rollback to previous revision

2. **Database Down**
   - Trigger: Database connection failure >1 minute
   - Notification: PagerDuty (immediate page)
   - Action: Check Cloud SQL status, manual intervention

### P1 Alerts
3. **High Error Rate**
   - Trigger: Error rate >5% for 5 minutes
   - Notification: PagerDuty (business hours), Slack (off-hours)
   - Action: Check logs, investigate root cause

4. **High Latency**
   - Trigger: P95 response time >500ms for 10 minutes
   - Notification: Slack
   - Action: Check resource utilization, database queries

### P2 Alerts
5. **Disk Space Low**
   - Trigger: Disk usage >80%
   - Notification: Slack
   - Action: Clean up logs, increase storage

### P3 Alerts
6. **Trial Conversion Anomaly**
   - Trigger: Trial→paid conversion <50% (weekly)
   - Notification: Email digest
   - Action: Product review

## Service Level Objectives (SLOs)

### Availability SLO
**Target**: 99.9% uptime (8.76 hours downtime/year)  
**Measurement Window**: 30 days rolling  
**Error Budget**: 43.2 minutes/month  
**Burn Rate Alert**: Alert if consuming >2x error budget

### Latency SLO
**Target**: 
- P95 <200ms
- P99 <500ms  
**Measurement**: HTTP request duration (excluding cold starts)  
**Measurement Window**: 7 days rolling

## Notification Channels

### PagerDuty
**Service**: WAOOAW Production  
**Integration Key**: Stored in Secret Manager (`pagerduty-integration-key`)  
**Escalation Policy**: 
1. On-call SRE (immediate)
2. Backup SRE (+15 min)
3. Engineering Manager (+30 min)

### Slack
**Channel**: `#waooaw-alerts`  
**Webhook URL**: Stored in Secret Manager (`slack-webhook-url`)  
**Formatting**: Include environment, severity, runbook link

### Email
**Recipients**: eng-team@waooaw.ai  
**Frequency**: Daily digest for P3 alerts

## Runbooks

Each alert includes a runbook link for troubleshooting:
- [Backend Down Runbook](/docs/runbooks/backend-down.md)
- [Database Down Runbook](/docs/runbooks/database-down.md)
- [High Error Rate Runbook](/docs/runbooks/high-error-rate.md)
- [High Latency Runbook](/docs/runbooks/high-latency.md)

## Deployment Instructions

### Prerequisites
1. GCP project with Cloud Monitoring API enabled
2. IAM permissions: `roles/monitoring.admin`
3. PagerDuty integration key stored in Secret Manager
4. Slack webhook URL stored in Secret Manager

### Deploy All Monitoring
```bash
cd /workspaces/WAOOAW/cloud/demo
./scripts/deploy-monitoring.sh --environment demo --project waooaw-demo
```

### Deploy Individual Resources
```bash
# Dashboards
gcloud monitoring dashboards create --config-from-file=monitoring/dashboards/executive.json

# Uptime checks
gcloud monitoring uptime-check-configs create --config-from-file=monitoring/uptime-checks/backend-health.yaml

# Alert policies
gcloud alpha monitoring policies create --policy-from-file=monitoring/alerts/p0-backend-down.yaml

# SLOs (requires custom service)
gcloud monitoring services create plant-backend \
  --display-name="WAOOAW Plant Backend"

gcloud alpha monitoring slos create availability-slo \
  --service=plant-backend \
  --config-from-file=monitoring/slos/availability-slo.yaml
```

### Verify Deployment
```bash
# List dashboards
gcloud monitoring dashboards list

# List uptime checks
gcloud monitoring uptime-check-configs list

# List alert policies
gcloud alpha monitoring policies list

# List SLOs
gcloud alpha monitoring slos list --service=plant-backend
```

## Testing Alerts

### Test P0 Alert (Backend Down)
```bash
# Manually stop backend to trigger alert
gcloud run services update waooaw-plant-backend-demo \
  --region=asia-south1 \
  --update-env-vars=FORCE_ERROR=true

# Wait 3 minutes for uptime check to fail
# Verify PagerDuty notification received

# Restore service
gcloud run services update waooaw-plant-backend-demo \
  --region=asia-south1 \
  --remove-env-vars=FORCE_ERROR
```

### Test P1 Alert (High Error Rate)
```bash
# Increase error rate via load test
cd /workspaces/WAOOAW/tests/load
python3 error_injection.py --error-rate=0.1 --duration=600

# Verify Slack notification after 5 minutes
```

## Maintenance

### Review Alerts Weekly
- Check false positive rate
- Adjust thresholds if needed
- Update runbooks basedon incidents

### Update Dashboards Monthly
- Add new metrics as features launch
- Remove deprecated metrics
- Gather feedback from stakeholders

### Test Alert Policies Quarterly
- Simulate outages
- Verify notifications reach correct channels
- Update escalation policies

## Related Documents
- [OperationsAndMaintenanceEpics.md](/workspaces/WAOOAW/src/Plant/Docs/OperationsAndMaintenanceEpics.md) - Epic AGP3-OBS-1
- [Runbooks](/workspaces/WAOOAW/docs/runbooks/) - Incident response procedures
- [INFRASTRUCTURE_DEPLOYMENT.md](/workspaces/WAOOAW/cloud/INFRASTRUCTURE_DEPLOYMENT.md) - Cloud infrastructure
