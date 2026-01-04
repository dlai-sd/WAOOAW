# Enabling Multi-Zone High Availability

**Runbook ID:** RB-GCP-002  
**Purpose:** Enable multi-zone deployment for high availability  
**Target:** asia-south1 zones a + b  
**Prerequisites:** Phase 1 or 2 deployed and stable

---

## Overview

This runbook guides you through enabling multi-zone HA for WAOOAW services, transitioning from single-zone deployment to dual-zone with automatic failover.

**When to use:**
- Customer SLA requirements
- Revenue >$5K/month
- Traffic >1M requests/month
- Need <10s RTO (Recovery Time Objective)

**Cost Impact:** +$60-90/month (requires CTO approval per policy)

---

## Phase Comparison

| Phase | Zones | Min Instances | Cost | RTO on Zone Failure |
|-------|-------|--------------|------|---------------------|
| **Current (1 or 2)** | 1 (a) | 0-1 | $86-177/month | 5-10 seconds (cold start) |
| **Target (3)** | 2 (a, b) | 1 per zone | $145-190/month | <1 second (instant failover) |

---

## Pre-Deployment Checklist

### Business Approval
- [ ] Monthly cost will increase by $60-90
- [ ] Budget variance >$150/month requires CTO approval (per POLICY-TECH-001)
- [ ] Business justification documented (SLA, revenue, customer requirement)
- [ ] Approval email/ticket obtained

### Technical Readiness
- [ ] Phase 1 or 2 deployed successfully
- [ ] All 5 services operational
- [ ] Load balancer health checks passing
- [ ] Cost alerts configured at $150 threshold
- [ ] Monitoring dashboards active

### Communication
- [ ] Team notified of deployment window
- [ ] Customer notification (if SLA-driven)
- [ ] Rollback plan reviewed

---

## Step 1: Enable Multi-Zone for Critical Services

### 1.1 Backend API (api.waooaw.com)

**Priority:** Critical - enable first

```bash
# Update waooaw-api service
gcloud run services update waooaw-api \
    --region=asia-south1 \
    --min-instances=1 \
    --execution-environment=gen2 \
    --zones=asia-south1-a,asia-south1-b

# Verify deployment
gcloud run services describe waooaw-api --region=asia-south1 \
    --format="value(spec.template.spec.containers[0].resources.limits.memory,spec.template.metadata.annotations['autoscaling.knative.dev/minScale'])"

# Expected output:
# 1Gi
# 1

# Check instances across zones
gcloud run revisions list --service=waooaw-api --region=asia-south1
```

**Expected Behavior:**
- 1 instance in zone a
- 1 instance in zone b
- Total: 2 warm instances
- Load balancer distributes traffic evenly

**Cost Impact:** +$22-28/month

### 1.2 Customer Marketplace (www.waooaw.com)

**Priority:** High - customer-facing

```bash
gcloud run services update waooaw-marketplace \
    --region=asia-south1 \
    --min-instances=1 \
    --execution-environment=gen2 \
    --zones=asia-south1-a,asia-south1-b

# Verify
gcloud run services describe waooaw-marketplace --region=asia-south1
```

**Cost Impact:** +$17-22/month

---

## Step 2: Verify Multi-Zone Deployment

### 2.1 Check Instance Distribution

```bash
# List all revisions for api service
gcloud run revisions list \
    --service=waooaw-api \
    --region=asia-south1 \
    --format="table(metadata.name,status.conditions[0].status,spec.template.metadata.annotations['run.googleapis.com/zones'])"

# Expected output shows zones: a,b
```

### 2.2 Test Zone Failover (Simulated)

```bash
# Send test traffic to specific zone
for i in {1..20}; do
    curl -H "X-Cloud-Trace-Context: test-$i" https://api.waooaw.com/health
    sleep 0.5
done

# Check Cloud Logging for zone distribution
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=waooaw-api" \
    --limit 20 \
    --format="value(resource.labels.location)"

# Should see mix of asia-south1-a and asia-south1-b
```

### 2.3 Verify Load Balancer Backend Health

```bash
# Check backend service health
gcloud compute backend-services get-health waooaw-backend-service --global

# Expected output:
# Both backends (zone a and b) should show HEALTHY
```

---

## Step 3: Configure Internal Services (Optional)

Platform Portal and Dev Portal typically stay single-zone (internal tools, cost priority).

**If business requires HA for internal tools:**

```bash
# Platform Portal (pp.waooaw.com) - rarely needed
gcloud run services update waooaw-platform-portal \
    --region=asia-south1 \
    --min-instances=1 \
    --zones=asia-south1-a,asia-south1-b

# Cost Impact: +$18-22/month

# Dev Portal (dp.waooaw.com) - rarely needed
gcloud run services update waooaw-dev-portal \
    --region=asia-south1 \
    --min-instances=1 \
    --zones=asia-south1-a,asia-south1-b

# Cost Impact: +$15-18/month
```

**Recommendation:** Leave internal portals in single zone unless customer SLA requires.

---

## Step 4: Update Monitoring & Alerts

### 4.1 Update Cost Alert Threshold

```bash
# Update budget alert (from $150 to $190)
gcloud billing budgets update <budget-id> \
    --budget-amount=190 \
    --threshold-rule=percent=50 \
    --threshold-rule=percent=80 \
    --threshold-rule=percent=100

# Replace <budget-id> with actual budget ID
# Get budget ID: gcloud billing budgets list
```

### 4.2 Add Zone-Level Monitoring

```bash
# Create uptime check for zone failover
gcloud monitoring uptime-checks create \
    --display-name="WAOOAW API Multi-Zone Health" \
    --resource-type=UPTIME_URL \
    --monitored-resource=https://api.waooaw.com/health \
    --check-interval=60s \
    --timeout=10s

# Create alert policy
gcloud alpha monitoring policies create \
    --notification-channels=<channel-id> \
    --display-name="Multi-Zone Failover Alert" \
    --condition-display-name="API Zone Failure" \
    --condition-expression="resource.type='cloud_run_revision' AND metric.type='run.googleapis.com/request_count'" \
    --condition-threshold-value=0 \
    --condition-threshold-duration=300s
```

---

## Step 5: Validate High Availability

### 5.1 Load Test

```bash
# Generate sustained traffic (use Apache Bench or similar)
ab -n 10000 -c 50 https://api.waooaw.com/health

# Check instance distribution in Cloud Console
# Navigate to: Cloud Run → waooaw-api → Logs
# Filter by zone, should see traffic to both zones
```

### 5.2 Failover Simulation

**⚠️ DO NOT RUN IN PRODUCTION WITHOUT APPROVAL**

This test intentionally degrades one zone to verify failover:

```bash
# Temporarily scale down zone A instances
# (Cloud Run will auto-recover, but this tests behavior)

# Monitor during failover
watch -n 1 'gcloud run services describe waooaw-api --region=asia-south1 --format="value(status.conditions[0].status)"'

# Send continuous requests
while true; do curl https://api.waooaw.com/health; sleep 0.5; done
```

**Expected Result:**
- Traffic continues with <10s disruption
- Zone B instances handle full load
- Zone A recovers automatically

---

## Step 6: Document Changes

### 6.1 Update Policy Variance

Create policy variance document:

**File:** `/policy/supporting/multi-zone-variance-2026-01.md`

```markdown
# Policy Variance Request - Multi-Zone HA

**Request Date:** [Date]
**Policy:** POLICY-TECH-001 (Tech Stack Selection)
**Variance:** Monthly cost exceeds $150 limit ($145-190)

## Business Justification
- Customer SLA requirement: 99.5% uptime
- Revenue: >$5K/month
- Zone-level failover needed

## Cost Impact
- Current: $125-177/month (Phase 2)
- Proposed: $145-190/month (Phase 3)
- Increase: $20-40/month

## Approval
- CTO Approval: [Name, Date]
```

### 6.2 Update Architecture Docs

```bash
# Add entry to cloud/gcp/CURRENT_STATE.md
echo "Multi-zone enabled: $(date)" >> /workspaces/WAOOAW/cloud/gcp/CURRENT_STATE.md
```

---

## Rollback Plan

If issues arise, revert to single zone:

### Immediate Rollback (5 minutes)

```bash
# Revert API to single zone
gcloud run services update waooaw-api \
    --region=asia-south1 \
    --min-instances=1 \
    --zones=asia-south1-a

# Revert Marketplace
gcloud run services update waooaw-marketplace \
    --region=asia-south1 \
    --min-instances=1 \
    --zones=asia-south1-a

# Verify
gcloud run services list --region=asia-south1
```

### Full Rollback to Phase 1 (10 minutes)

```bash
# Scale all to zero (Phase 1 config)
gcloud run services update waooaw-api --region=asia-south1 --min-instances=0
gcloud run services update waooaw-marketplace --region=asia-south1 --min-instances=0

# Cost returns to $86-127/month
```

---

## Cost Tracking

After enabling multi-zone, monitor costs daily for first week:

```bash
# Check daily costs
gcloud billing accounts get-billing-info --billing-account=<account-id>

# Or use GCP Console → Billing → Cost Table
# Filter by: asia-south1, Cloud Run
```

**Alert Triggers:**
- 50% of $190 ($95) → Email notification
- 80% of $190 ($152) → Slack alert
- 100% of $190 → Urgent CTO review

---

## Success Criteria

✅ **Technical:**
- [ ] 2 instances per critical service (api, www)
- [ ] Instances distributed across zones a and b
- [ ] Health checks passing in both zones
- [ ] Load balancer distributing traffic evenly
- [ ] Failover test completes successfully (<10s recovery)

✅ **Business:**
- [ ] CTO approval obtained (if cost >$150)
- [ ] Cost monitoring updated
- [ ] Team trained on new architecture
- [ ] Documentation updated

✅ **Operational:**
- [ ] Rollback plan tested
- [ ] Alerts configured
- [ ] Monthly cost review scheduled

---

## Troubleshooting

### Issue: Instances not distributing across zones

**Symptoms:** All instances in one zone

**Solution:**
```bash
# Force new revision deployment
gcloud run services update waooaw-api \
    --region=asia-south1 \
    --update-env-vars=FORCE_REDEPLOY="$(date +%s)" \
    --zones=asia-south1-a,asia-south1-b
```

### Issue: Cost exceeding $190/month

**Check:**
```bash
# Verify min instances
gcloud run services list --region=asia-south1 \
    --format="table(metadata.name,spec.template.metadata.annotations['autoscaling.knative.dev/minScale'])"

# Expected: api=1, marketplace=1, others=0
```

**Action:** Scale down non-critical services

### Issue: Zone failover not working

**Check backend health:**
```bash
gcloud compute backend-services get-health waooaw-backend-service --global
```

**Fix:** Update backend service timeouts

---

## Post-Deployment

### Week 1 Tasks
- [ ] Daily cost check
- [ ] Monitor instance distribution
- [ ] Review error rates (should be unchanged)
- [ ] Customer feedback (performance, availability)

### Week 2-4 Tasks
- [ ] Weekly cost review
- [ ] Tune autoscaling (if needed)
- [ ] Document lessons learned
- [ ] Update runbook based on experience

---

**Runbook Owner:** Platform Architecture Team  
**Review Schedule:** Quarterly  
**Last Updated:** January 3, 2026  
**Next Review:** April 3, 2026
