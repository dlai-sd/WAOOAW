# GCP Monitoring, Alerting, and Cost Tracking

**Document ID:** MONITORING-001  
**Target Region:** asia-south1 (Mumbai)  
**Cost Budget:** $150/month (₹12,500/month)  
**Last Updated:** January 3, 2026

---

## Overview

This document provides complete setup and management procedures for monitoring the WAOOAW platform on GCP, with emphasis on cost tracking to stay within the $150/month budget ceiling defined in POLICY-TECH-001.

---

## 1. Cost Budget Setup

### 1.1 Create Budget with Alerts

**Budget Configuration:**

| Parameter | Value |
|-----------|-------|
| **Budget Name** | WAOOAW Production Budget |
| **Projects** | waooaw-oauth (270293855600) |
| **Budget Amount** | $150 USD per month |
| **Alert Thresholds** | 50%, 80%, 100%, 120% |
| **Email Recipients** | yogeshkhandge@gmail.com |
| **Pubsub Topic** | budget-alerts (for automation) |

**Create via gcloud:**

```bash
# Create budget
gcloud billing budgets create \
    --billing-account=<BILLING_ACCOUNT_ID> \
    --display-name="WAOOAW Production Budget" \
    --budget-amount=150USD \
    --threshold-rule=percent=0.5 \
    --threshold-rule=percent=0.8 \
    --threshold-rule=percent=1.0 \
    --threshold-rule=percent=1.2

# Create Pub/Sub topic for alerts
gcloud pubsub topics create budget-alerts

# Subscribe email to topic
gcloud pubsub subscriptions create budget-email-alert \
    --topic=budget-alerts \
    --push-endpoint=https://api.waooaw.com/webhooks/budget-alert
```

**Via Console:**
1. Go to: Billing → Budgets & alerts → Create Budget
2. Set budget amount: $150
3. Add thresholds: 50%, 80%, 100%, 120%
4. Configure email notifications
5. Link to Pub/Sub for automation

### 1.2 Budget Alert Automation

**Cloud Function to auto-scale down at 100%:**

```python
# functions/budget_enforcer.py
import functions_framework
from google.cloud import run_v2

@functions_framework.cloud_event
def enforce_budget(cloud_event):
    """
    Triggered when budget threshold reached.
    At 100%: Scale all services to min-instances=0
    At 120%: Suspend non-critical services
    """
    data = cloud_event.data
    budget_percent = data['costAmount'] / data['budgetAmount']
    
    if budget_percent >= 1.0:
        # Scale to zero
        services = ['waooaw-marketplace', 'waooaw-dev-portal', 'waooaw-customer-yk']
        for service in services:
            scale_service(service, min_instances=0)
    
    if budget_percent >= 1.2:
        # Critical: Suspend non-essential services
        suspend_service('waooaw-dev-portal')

def scale_service(service_name, min_instances):
    client = run_v2.ServicesClient()
    request = run_v2.UpdateServiceRequest(
        service=f"projects/waooaw-oauth/locations/asia-south1/services/{service_name}",
        # Update minScale annotation
    )
    client.update_service(request=request)
```

---

## 2. Cloud Run Monitoring

### 2.1 Key Metrics to Track

**Per Service:**
- **Request Count**: Total requests/minute
- **Request Latency**: p50, p95, p99
- **Error Rate**: 4xx, 5xx errors
- **Instance Count**: Active instances
- **CPU Utilization**: % CPU used
- **Memory Utilization**: % memory used
- **Billable Time**: Total container execution time

**Dashboard Metrics:**

| Service | Latency Target | Error Rate | Billable Time/day |
|---------|----------------|------------|-------------------|
| waooaw-api | <500ms | <1% | ~$2-4 |
| waooaw-marketplace | <800ms | <0.5% | ~$1-2 |
| waooaw-platform-portal | <600ms | <1% | ~$3-5 |
| waooaw-dev-portal | <800ms | <2% | ~$0.50-1 |
| waooaw-customer-yk | <800ms | <1% | ~$0.50-1 |

### 2.2 Create Cloud Run Dashboard

**Via Console:**
1. Go to: Monitoring → Dashboards → Create Dashboard
2. Name: "WAOOAW Platform Overview"
3. Add widgets:

**Request Count Widget:**
```yaml
resource.type: cloud_run_revision
resource.labels.service_name: [all services]
metric.type: run.googleapis.com/request_count
aggregation: rate, 1 minute
```

**Latency Widget:**
```yaml
metric.type: run.googleapis.com/request_latencies
percentile: 50, 95, 99
group_by: service_name
```

**Instance Count Widget:**
```yaml
metric.type: run.googleapis.com/container/instance_count
aggregation: sum
group_by: service_name
```

**Cost Widget:**
```yaml
metric.type: run.googleapis.com/container/billable_instance_time
aggregation: sum, 1 day
group_by: service_name
```

### 2.3 Create Alerts

**High Error Rate Alert:**

```bash
gcloud alpha monitoring policies create \
    --notification-channels=<CHANNEL_ID> \
    --display-name="Cloud Run High Error Rate" \
    --condition-threshold-value=0.01 \
    --condition-threshold-duration=300s \
    --condition-display-name="Error rate > 1%" \
    --condition-filter='
        resource.type="cloud_run_revision" AND
        metric.type="run.googleapis.com/request_count" AND
        metric.labels.response_code_class="5xx"
    '
```

**High Latency Alert:**

```bash
gcloud alpha monitoring policies create \
    --notification-channels=<CHANNEL_ID> \
    --display-name="Cloud Run High Latency" \
    --condition-threshold-value=2000 \
    --condition-threshold-duration=300s \
    --condition-display-name="p99 latency > 2s" \
    --condition-filter='
        resource.type="cloud_run_revision" AND
        metric.type="run.googleapis.com/request_latencies" AND
        metric.labels.percentile="99"
    '
```

**Instance Count Alert:**

```bash
gcloud alpha monitoring policies create \
    --notification-channels=<CHANNEL_ID> \
    --display-name="Too Many Cloud Run Instances" \
    --condition-threshold-value=5 \
    --condition-threshold-duration=600s \
    --condition-display-name="Instances > 5 for 10 min" \
    --condition-filter='
        resource.type="cloud_run_revision" AND
        metric.type="run.googleapis.com/container/instance_count"
    '
```

---

## 3. Uptime Checks

### 3.1 Configure Uptime Checks for All Domains

**Domains to monitor:**
- https://www.waooaw.com
- https://pp.waooaw.com
- https://dp.waooaw.com
- https://yk.waooaw.com
- https://api.waooaw.com/health

**Create Uptime Check:**

```bash
# Customer Marketplace
gcloud monitoring uptime create www-waooaw-com \
    --display-name="WAOOAW Marketplace Uptime" \
    --resource-type=uptime-url \
    --host=www.waooaw.com \
    --path=/ \
    --check-interval=5m \
    --timeout=10s

# Platform Portal
gcloud monitoring uptime create pp-waooaw-com \
    --display-name="Platform Portal Uptime" \
    --resource-type=uptime-url \
    --host=pp.waooaw.com \
    --path=/ \
    --check-interval=5m \
    --timeout=10s

# API Health Check
gcloud monitoring uptime create api-waooaw-com \
    --display-name="API Health Check" \
    --resource-type=uptime-url \
    --host=api.waooaw.com \
    --path=/health \
    --check-interval=1m \
    --timeout=5s \
    --http-check-path=/health \
    --http-check-expected-status=200
```

### 3.2 Uptime Alert Policy

```bash
gcloud alpha monitoring policies create \
    --notification-channels=<CHANNEL_ID> \
    --display-name="Service Down Alert" \
    --condition-threshold-value=1 \
    --condition-threshold-duration=300s \
    --condition-display-name="Uptime check failed" \
    --condition-filter='
        resource.type="uptime_url" AND
        metric.type="monitoring.googleapis.com/uptime_check/check_passed" AND
        metric.labels.check_id=monitoring.regex.full_match(".*waooaw.*")
    '
```

---

## 4. Log-Based Metrics

### 4.1 OAuth Failure Metric

**Purpose:** Track OAuth authentication failures

```bash
gcloud logging metrics create oauth_failures \
    --description="OAuth authentication failures" \
    --log-filter='
        resource.type="cloud_run_revision"
        resource.labels.service_name="waooaw-api"
        jsonPayload.message=~"oauth_error|oauth_.*_failed"
    '
```

**Alert on OAuth Failures:**

```bash
gcloud alpha monitoring policies create \
    --notification-channels=<CHANNEL_ID> \
    --display-name="OAuth Failure Rate High" \
    --condition-threshold-value=10 \
    --condition-threshold-duration=600s \
    --condition-display-name="OAuth failures > 10 in 10 min" \
    --condition-filter='
        metric.type="logging.googleapis.com/user/oauth_failures"
    '
```

### 4.2 API Response Time Metric

```bash
gcloud logging metrics create api_slow_requests \
    --description="API requests slower than 2 seconds" \
    --log-filter='
        resource.type="cloud_run_revision"
        resource.labels.service_name="waooaw-api"
        httpRequest.latency>2s
    ' \
    --value-extractor='EXTRACT(httpRequest.latency)'
```

### 4.3 Database Error Metric

```bash
gcloud logging metrics create database_errors \
    --description="Database connection or query errors" \
    --log-filter='
        resource.type="cloud_run_revision"
        (jsonPayload.message=~"database error" OR
         jsonPayload.message=~"connection refused" OR
         jsonPayload.message=~"timeout")
    '
```

---

## 5. Cost Attribution and Analysis

### 5.1 Enable Detailed Cost Breakdown

**Labels for cost attribution:**

```bash
# Label services by team/function
gcloud run services update waooaw-api \
    --region=asia-south1 \
    --labels=team=backend,function=api,cost-center=engineering

gcloud run services update waooaw-marketplace \
    --region=asia-south1 \
    --labels=team=frontend,function=customer,cost-center=product

gcloud run services update waooaw-platform-portal \
    --region=asia-south1 \
    --labels=team=frontend,function=internal,cost-center=operations
```

### 5.2 Cost Breakdown Query

**Daily cost by service (BigQuery):**

```sql
-- Export billing data to BigQuery first
-- Go to: Billing → Billing Export → Enable BigQuery Export

SELECT
  service.description AS service_name,
  sku.description AS sku_description,
  labels.value AS service_label,
  SUM(cost) AS total_cost,
  DATE(usage_start_time) AS usage_date
FROM
  `waooaw-oauth.billing_export.gcp_billing_export_v1_*`
LEFT JOIN
  UNNEST(labels) AS labels
WHERE
  DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  AND project.id = 'waooaw-oauth'
  AND labels.key = 'function'
GROUP BY
  service_name, sku_description, service_label, usage_date
ORDER BY
  total_cost DESC
```

### 5.3 Cost by Phase

**Track spending per deployment phase:**

| Phase | Expected Cost | Services | Alerts |
|-------|---------------|----------|--------|
| Phase 1 (Single Zone) | $86-127 | All 5, min=0 | Alert at $130 |
| Phase 2 (Warm Instances) | $125-177 | www+api warm | Alert at $180 |
| Phase 3 (Multi-Zone HA) | $145-190 | Zones a+b | Alert at $195 |

**Set phase-specific budgets:**

```bash
# Phase 1 budget
gcloud billing budgets create \
    --billing-account=<BILLING_ACCOUNT_ID> \
    --display-name="Phase 1 Budget" \
    --budget-amount=127USD \
    --filter-labels=phase=1

# Phase 2 budget (requires CTO approval per policy)
gcloud billing budgets create \
    --billing-account=<BILLING_ACCOUNT_ID> \
    --display-name="Phase 2 Budget" \
    --budget-amount=177USD \
    --filter-labels=phase=2 \
    --all-updates-rule-monitoring-notification-channels=<CHANNEL_ID>
```

---

## 6. Notification Channels

### 6.1 Create Email Channel

```bash
gcloud alpha monitoring channels create \
    --display-name="Engineering Email" \
    --type=email \
    --channel-labels=email_address=yogeshkhandge@gmail.com
```

### 6.2 Create Slack Channel (Optional)

```bash
# Requires Slack webhook URL
gcloud alpha monitoring channels create \
    --display-name="WAOOAW Alerts Slack" \
    --type=slack \
    --channel-labels=url=<SLACK_WEBHOOK_URL>
```

### 6.3 Create PagerDuty Channel (Optional)

```bash
gcloud alpha monitoring channels create \
    --display-name="WAOOAW PagerDuty" \
    --type=pagerduty \
    --channel-labels=service_key=<PAGERDUTY_SERVICE_KEY>
```

---

## 7. Log Retention and Analysis

### 7.1 Configure Log Retention

**Default:** 30 days (included)  
**Long-term:** Export to Cloud Storage or BigQuery

```bash
# Create log sink to BigQuery
gcloud logging sinks create waooaw-logs-bigquery \
    bigquery.googleapis.com/projects/waooaw-oauth/datasets/logs \
    --log-filter='resource.type="cloud_run_revision"'

# Create log sink to Cloud Storage (for compliance)
gcloud logging sinks create waooaw-logs-storage \
    storage.googleapis.com/waooaw-logs-archive \
    --log-filter='resource.type="cloud_run_revision" AND severity>=ERROR'
```

### 7.2 Common Log Queries

**All errors in last hour:**
```
resource.type="cloud_run_revision"
severity>=ERROR
timestamp>="2026-01-03T00:00:00Z"
```

**OAuth related logs:**
```
resource.type="cloud_run_revision"
resource.labels.service_name="waooaw-api"
jsonPayload.message=~"oauth"
```

**Slow requests (>2s):**
```
resource.type="cloud_run_revision"
httpRequest.latency>2s
```

**5xx errors:**
```
resource.type="cloud_run_revision"
httpRequest.status>=500
```

---

## 8. Performance Monitoring

### 8.1 Cloud Trace Integration

**Enable Trace in backend:**

```python
# backend/app/main.py
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Initialize tracer
tracer_provider = TracerProvider()
cloud_trace_exporter = CloudTraceSpanExporter()
tracer_provider.add_span_processor(
    BatchSpanProcessor(cloud_trace_exporter)
)
trace.set_tracer_provider(tracer_provider)
```

**View traces:**
```bash
# List traces
gcloud trace traces list --limit=10

# Get trace details
gcloud trace traces describe <TRACE_ID>
```

### 8.2 Cloud Profiler (Optional - Phase 3)

**Enable Profiler for CPU/memory analysis:**

```python
# backend/app/main.py
import googlecloudprofiler

googlecloudprofiler.start(
    service='waooaw-api',
    service_version='1.0.0',
    verbose=3
)
```

**Cost:** ~$0.50/month per service

---

## 9. Multi-Zone Monitoring (Phase 3)

### 9.1 Zone Distribution Metric

```bash
gcloud logging metrics create zone_distribution \
    --description="Cloud Run instances by zone" \
    --log-filter='
        resource.type="cloud_run_revision"
        jsonPayload.message="instance started"
    ' \
    --value-extractor='EXTRACT(resource.labels.location)'
```

### 9.2 Failover Detection

**Alert when all instances in one zone:**

```bash
gcloud alpha monitoring policies create \
    --notification-channels=<CHANNEL_ID> \
    --display-name="Single Zone Failure" \
    --condition-threshold-value=1 \
    --condition-threshold-duration=300s \
    --condition-display-name="All instances in one zone" \
    --condition-filter='
        resource.type="cloud_run_revision" AND
        metric.type="run.googleapis.com/container/instance_count"
    '
```

### 9.3 Recovery Time Objective (RTO) Tracking

**Target:** <10 seconds for zone failover

**Test command:**
```bash
# Simulate zone failure
gcloud compute instances stop <instance-in-zone-a>

# Monitor time to recovery
watch -n 1 'curl -w "@curl-format.txt" -o /dev/null -s https://api.waooaw.com/health'
```

---

## 10. Monthly Cost Review Process

### 10.1 Review Checklist

**First Monday of each month:**

- [ ] Export last month's billing data to CSV
- [ ] Review cost by service (target vs actual)
- [ ] Identify cost anomalies (>20% variance)
- [ ] Check budget alert history
- [ ] Review instance scaling patterns
- [ ] Optimize cold start counts
- [ ] Update cost forecast for next month
- [ ] Document deviations from $150 budget
- [ ] Request CTO approval if >$150

### 10.2 Cost Report Template

**Monthly Cost Summary:**

```markdown
# WAOOAW Platform Cost Report - [Month Year]

## Executive Summary
- Total Cost: $XXX
- Budget: $150
- Variance: +/- $XX (+/-XX%)
- Status: ✅ Within Budget / ⚠️ Over Budget

## Cost by Service

| Service | This Month | Last Month | Change | Notes |
|---------|-----------|-----------|--------|-------|
| waooaw-api | $XX | $XX | +X% | - |
| waooaw-marketplace | $XX | $XX | +X% | - |
| waooaw-platform-portal | $XX | $XX | +X% | - |
| waooaw-dev-portal | $XX | $XX | +X% | - |
| waooaw-customer-yk | $XX | $XX | +X% | - |
| Load Balancer | $XX | $XX | +X% | - |
| Cloud Storage | $XX | $XX | +X% | - |
| **TOTAL** | **$XXX** | **$XXX** | **+X%** | - |

## Traffic Analysis
- Total Requests: XXX
- Peak Traffic Hour: XX:XX UTC
- Average Requests/day: XXX

## Optimization Opportunities
1. [Action item]
2. [Action item]

## Next Month Forecast
- Expected Cost: $XXX
- Drivers: [new feature, traffic growth, etc.]
- Approval Status: [Approved/Pending] by [Name]
```

### 10.3 Automated Cost Report

**Cloud Function to generate monthly report:**

```python
# functions/monthly_cost_report.py
from google.cloud import billing_v1
from google.cloud import storage
import datetime

def generate_monthly_report(event, context):
    """
    Triggered on 1st of each month.
    Generates cost report and emails to stakeholders.
    """
    billing_client = billing_v1.CloudBillingClient()
    
    # Get last month's costs
    end_date = datetime.date.today().replace(day=1)
    start_date = (end_date - datetime.timedelta(days=1)).replace(day=1)
    
    # Query costs by service
    # Generate report
    # Upload to Cloud Storage
    # Send email notification
```

---

## 11. Cost Optimization Strategies

### 11.1 Immediate Optimizations (Phase 1)

**Scale to Zero:**
```bash
# All services scale to zero when idle
gcloud run services update <SERVICE> \
    --region=asia-south1 \
    --min-instances=0
```

**Right-size Memory:**
```bash
# Reduce memory if utilization <50%
gcloud run services update waooaw-marketplace \
    --region=asia-south1 \
    --memory=512Mi  # Down from 1Gi
```

**Reduce CPU:**
```bash
# Use fractional CPUs for low-traffic services
gcloud run services update waooaw-dev-portal \
    --region=asia-south1 \
    --cpu=0.5  # Down from 1 CPU
```

### 11.2 Traffic-Based Optimizations (Phase 2)

**Keep warm instances only for high-traffic services:**
```bash
# API and marketplace get warm instances
gcloud run services update waooaw-api \
    --region=asia-south1 \
    --min-instances=1

# Dev portal stays cold (low traffic)
gcloud run services update waooaw-dev-portal \
    --region=asia-south1 \
    --min-instances=0
```

### 11.3 Long-term Optimizations (Phase 3+)

- [ ] Implement caching (Redis) to reduce compute
- [ ] Use CDN for static assets
- [ ] Optimize database queries
- [ ] Implement request batching
- [ ] Use Cloud Scheduler for batch jobs (cheaper than always-on)

---

## 12. Incident Response Integration

### 12.1 On-Call Playbook

**High Priority Alerts:**
1. Service down (uptime check failed)
2. High error rate (>5%)
3. Budget exceeded (>100%)

**Medium Priority Alerts:**
1. High latency (>2s p99)
2. OAuth failures (>10/10min)
3. Too many instances (cost concern)

**Low Priority Alerts:**
1. Budget warning (50%, 80%)
2. Slow log queries
3. Low traffic anomaly

### 12.2 Escalation Path

```
Level 1: Auto-remediation (scale down, restart)
   ↓ (if not resolved in 5 minutes)
Level 2: Email alert to engineering team
   ↓ (if not resolved in 15 minutes)
Level 3: Page on-call engineer
   ↓ (if not resolved in 30 minutes)
Level 4: Escalate to CTO
```

---

## 13. Compliance and Audit

### 13.1 Log Audit Trail

**Enable Data Access Logs:**
```bash
gcloud logging settings update \
    --project=waooaw-oauth \
    --audit-logging-enabled
```

**Required for:**
- Who accessed what service when
- Configuration changes
- Secret access
- Cost anomaly investigation

### 13.2 Budget Variance Reporting

**Policy requirement (TECH-001):**
- >$150/month requires CTO approval
- Monthly variance report
- Quarterly cost review

**Audit log format:**
```json
{
  "month": "2026-01",
  "total_cost": 145.23,
  "budget": 150.00,
  "variance": -4.77,
  "variance_percent": -3.18,
  "approved_by": "CTO",
  "approval_date": "2026-01-01",
  "notes": "Within budget, no approval needed"
}
```

---

## 14. Dashboard URLs (Quick Access)

**Monitoring:**
- Cloud Run Metrics: https://console.cloud.google.com/run?project=waooaw-oauth
- Logs Explorer: https://console.cloud.google.com/logs?project=waooaw-oauth
- Trace List: https://console.cloud.google.com/traces?project=waooaw-oauth
- Uptime Checks: https://console.cloud.google.com/monitoring/uptime?project=waooaw-oauth

**Billing:**
- Cost Table: https://console.cloud.google.com/billing/cost-table?project=waooaw-oauth
- Budgets & Alerts: https://console.cloud.google.com/billing/budgets?project=waooaw-oauth
- Reports: https://console.cloud.google.com/billing/reports?project=waooaw-oauth

**Alerting:**
- Alert Policies: https://console.cloud.google.com/monitoring/alerting?project=waooaw-oauth
- Notification Channels: https://console.cloud.google.com/monitoring/alerting/notifications?project=waooaw-oauth

---

## 15. Next Steps

### Immediate (Week 1)
1. Create budget with $150 limit and alert thresholds
2. Set up uptime checks for all 5 domains
3. Create notification channel (email)
4. Enable billing export to BigQuery

### Short-term (Month 1)
1. Create Cloud Run dashboard with key metrics
2. Set up log-based metrics (OAuth failures, slow requests)
3. Create alert policies (high error rate, high latency)
4. Document first monthly cost review

### Long-term (Quarter 1)
1. Implement automated cost report generation
2. Set up Cloud Trace for performance analysis
3. Create cost optimization runbook
4. Quarterly cost review with CTO

---

**Document Owner:** Platform Architecture Team  
**Review Schedule:** Monthly (with cost review)  
**Last Reviewed:** January 3, 2026  
**Next Review:** February 3, 2026  

**Contact:** yogeshkhandge@gmail.com  
**Escalation:** Refer to /cloud/gcp/runbooks/incident-response.md
