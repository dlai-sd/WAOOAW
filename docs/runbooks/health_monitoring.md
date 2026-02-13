# Agent Health Monitoring Playbook

**Document Version**: 1.0  
**Last Updated**: 2026-02-12  
**Owner**: Operations & SRE Teams  
**Purpose**: Comprehensive guide for monitoring WAOOAW platform health and agent operations

---

## Overview

This playbook defines health metrics, alert thresholds, monitoring procedures, and escalation paths for the WAOOAW platform. Ensures proactive detection and resolution of issues before customer impact.

**Monitoring Philosophy**: Monitor symptoms (customer-facing issues) more than causes (internal metrics)

**Target Audience**: On-call engineers, SRE team, operations team  
**Tools**: Prometheus, Grafana, PagerDuty, DataDog (optional)

---

## Table of Contents

1. [Health Metrics Overview](#health-metrics-overview)
2. [Alert Thresholds](#alert-thresholds)
3. [Monitoring Dashboards](#monitoring-dashboards)
4. [Health Check Procedures](#health-check-procedures)
5. [Escalation Procedures](#escalation-procedures)
6. [Incident Response Integration](#incident-response-integration)

---

## Health Metrics Overview

### Tier 1: Critical - Customer-Facing Services

**Metric**: API Availability  
**Description**: Percentage of successful API requests  
**Target**: 99.9% uptime (43.2 minutes downtime/month)  
**Alert**: <99.5% over 5-minute window  
**Impact**: Customers cannot use platform

**Metric**: Goal Execution Success Rate  
**Description**: Percentage of goals executed without errors  
**Target**: >98%  
**Alert**: <95% over 15-minute window  
**Impact**: Agents not performing tasks

**Metric**: Authentication Success Rate  
**Description**: Percentage of successful customer logins  
**Target**: >99%  
**Alert**: <97% over 5-minute window  
**Impact**: Customers cannot access CP

**Metric**: Deliverable Creation Success Rate  
**Description**: Percentage of goals that create deliverables successfully  
**Target**: >97%  
**Alert**: <90% over 15-minute window  
**Impact**: Customers don't receive agent work product

### Tier 2: Important - Service Quality

**Metric**: API Response Time (P95)  
**Description**: 95th percentile API response time  
**Target**: <200ms  
**Alert**: >500ms for 5 minutes  
**Impact**: Slow customer experience

**Metric**: Goal Execution Latency (P95)  
**Description**: Time from scheduled execution to deliverable creation  
**Target**: <2 minutes  
**Alert**: >5 minutes for 15 minutes  
**Impact**: Delayed agent responses

**Metric**: Platform Integration Success Rate  
**Description**: Success rate for Instagram, LinkedIn, Delta Exchange API calls  
**Target**: >95%  
**Alert**: <90% over 10-minute window  
**Impact**: Posts/trades failing

**Metric**: Approval Queue Latency  
**Description**: Time deliverable spends waiting for approval  
**Target**: Median <2 hours (during business hours)  
**Alert**: P95 >24 hours  
**Impact**: Customer frustration, delayed value

### Tier 3: Infrastructure - System Health

**Metric**: Database Connection Pool Utilization  
**Description**: Percentage of database connections in use  
**Target**: <80%  
**Alert**: >90% for 5 minutes  
**Impact**: API requests may fail/slow

**Metric**: Scheduler Health  
**Description**: Scheduler heartbeat and execution cadence  
**Target**: Heartbeat every 60 seconds  
**Alert**: No heartbeat for 3 minutes  
**Impact**: No goals execute

**Metric**: Database Query Performance  
**Description**: Slow query count (>1 second)  
**Target**: <5 queries/minute  
**Alert**: >20 queries/minute for 5 minutes  
**Impact**: Platform slowdown

**Metric**: Error Rate (5xx)  
**Description**: Server error percentage of all requests  
**Target**: <0.1%  
**Alert**: >1% for 5 minutes  
**Impact**: Platform instability

### Tier 4: Business Metrics

**Metric**: Active Agent Count  
**Description**: Number of agents executing goals in last 24 hours  
**Target**: Upward trend  
**Alert**: >20% decrease day-over-day  
**Impact**: Platform usage declining

**Metric**: Trial Conversion Rate  
**Description**: Percentage of trials converting to paid  
**Target**: >30%  
**Alert**: <20% over 7-day rolling window  
**Impact**: Revenue impact

**Metric**: Platform Credential Health  
**Description**: Percentage of credentials active and valid  
**Target**: >95%  
**Alert**: <85% of customers have valid credentials  
**Impact**: Agents unable to operate

---

## Alert Thresholds

### Severity Definitions

**P0 - Critical (Page On-Call + Incident Commander)**
- Customer-facing outage
- Data loss or corruption
- Security breach
- **Response Time**: 15 minutes
- **Resolution Time**: 1-4 hours

**P1 - High (Page On-Call)**
- Significant degradation (>50% of customers affected)
- Core feature unavailable
- Major integration failure
- **Response Time**: 30 minutes
- **Resolution Time**: 4-24 hours

**P2 - Medium (Slack Alert + Email)**
- Minor degradation (<50% customers affected)
- Non-critical feature unavailable
- Performance degradation
- **Response Time**: 1 hour (during business hours)
- **Resolution Time**: 1-3 days

**P3 - Low (Email/Ticket)**
- Cosmetic issues
- Minor performance issues
- Non-urgent improvements
- **Response Time**: Next business day
- **Resolution Time**: 1-2 weeks

### Alert Configuration Example

```yaml
# Prometheus AlertManager config
groups:
  - name: waooaw_critical
    interval: 1m
    rules:
      - alert: APIAvailabilityLow
        expr: |
          (
            sum(rate(api_requests_total{status!~"5.."}[5m])) 
            / 
            sum(rate(api_requests_total[5m]))
          ) < 0.995
        for: 5m
        labels:
          severity: P0
        annotations:
          summary: "API availability below 99.5%"
          description: "Only {{ $value | humanizePercentage }} of requests succeeding in last 5 minutes"
          runbook: "https://docs.waooaw.com/runbooks/api_availability"
          
      - alert: SchedulerHealthCheckFailed
        expr: |
          time() - scheduler_heartbeat_timestamp_seconds > 180
        for: 0m
        labels:
          severity: P0
        annotations:
          summary: "Scheduler heartbeat missing"
          description: "No scheduler heartbeat for {{ $value }}s"
          runbook: "https://docs.waooaw.com/runbooks/scheduler_health"
          
      - alert: GoalExecutionFailureRateHigh
        expr: |
          (
            sum(rate(goal_executions_total{status="failed"}[15m])) 
            / 
            sum(rate(goal_executions_total[15m]))
          ) > 0.05
        for: 15m
        labels:
          severity: P1
        annotations:
          summary: "Goal execution failure rate >5%"
          description: "{{ $value | humanizePercentage }} of goals failing"
```

---

## Monitoring Dashboards

### Dashboard 1: Platform Overview (Executive View)

**URL**: [Grafana Dashboard - Platform Overview](https://grafana.waooaw.com/d/platform-overview)

**Panels**:
1. **API Availability** (last 24 hours) - Line graph
2. **Active Customers** (last 7 days) - Area chart
3. **Goal Executions** (today vs yesterday) - Bar chart
4. **Deliverables Created** (today) - Single stat
5. **Open Incidents** (P0/P1) - Alert list
6. **Top 5 Errors** (last 1 hour) - Table

**Audience**: Leadership, product managers  
**Refresh**: 1 minute

### Dashboard 2: Operations Dashboard (Ops Team View)

**URL**: [Grafana Dashboard - Operations](https://grafana.waooaw.com/d/operations)

**Panels**:
1. **Goal Execution Success Rate** (last 1 hour) - Gauge
2. **Pending Approvals by Urgency** - Table
3. **Credential Expiration Timeline** (next 14 days) - Timeline
4. **Customer Support Tickets** (open) - List
5. **Scheduler Queue Depth** - Line graph
6. **Platform Integration Status** (Instagram, LinkedIn, Delta) - Status grid
7. **Recent Errors** (last 15 minutes) - Logs

**Audience**: Operations team, customer support  
**Refresh**: 30 seconds

### Dashboard 3: SRE Dashboard (Engineering View)

**URL**: [Grafana Dashboard - SRE](https://grafana.waooaw.com/d/sre)

**Panels**:
1. **API Response Time** (P50/P95/P99) - Multi-line graph
2. **Error Rate by Endpoint** (last 1 hour) - Heatmap
3. **Database Connection Pool** - Gauge (current/max)
4. **Database Query Performance** - Table (slowest queries)
5. **Memory Usage** (all services) - Multi-line graph
6. **CPU Usage** (all services) - Multi-line graph
7. **Network I/O** - Line graph
8. **Kubernetes Pod Status** - Status grid

**Audience**: SRE, on-call engineers  
**Refresh**: 15 seconds (during incidents)

### Dashboard 4: Business Metrics (Product View)

**URL**: [Grafana Dashboard - Business](https://grafana.waooaw.com/d/business)

**Panels**:
1. **MAU/DAU** (Monthly/Daily Active Users) - Line graph
2. **Trial Signups** (last 30 days) - Bar chart
3. **Trial Conversion Rate** (rolling 7-day) - Line with target
4. **Revenue Run Rate** - Single stat
5. **Churn Rate** (last 3 months) - Percentage
6. **Agent Utilization** (active agents / total hired) - Gauge
7. **Top Performing Agents** (by customer satisfaction) - Table

**Audience**: Product managers, executives  
**Refresh**: 5 minutes

---

## Health Check Procedures

### Daily Health Check (10 minutes)

**When**: 9 AM local time (start of business day)  
**Who**: Operations lead on duty

**Checklist**:

1. **Check Dashboard Overview**
   - [ ] API availability >99.9% (last 24 hours)
   - [ ] No open P0/P1 incidents
   - [ ] Goal execution success rate >98%
   - [ ] No critical alerts firing

2. **Review Overnight Activity**
   - [ ] Check scheduler logs for errors (last 16 hours)
   - [ ] Verify all scheduled goals executed
   - [ ] No unexpected database alerts
   - [ ] No security alerts

3. **Customer Impact Check**
   - [ ] Review support tickets (0 critical, <5 high priority)
   - [ ] Check NPS/CSAT feedback (if available)
   - [ ] Verify no customer-reported outages

4. **Infrastructure Health**
   - [ ] All Kubernetes pods running (no crash loops)
   - [ ] Database connections healthy (<80% utilization)
   - [ ] Redis/cache hit rate >85%
   - [ ] Disk space >20% free on all volumes

5. **Upcoming Concerns**
   - [ ] Credentials expiring in next 3 days (proactive notification)
   - [ ] Scheduled maintenance windows documented
   - [ ] Capacity planning (if nearing limits)

**Action**: Document findings in Slack #ops-daily-standup

### Weekly Health Review (30 minutes)

**When**: Monday 10 AM  
**Who**: Operations + SRE leads

**Checklist**:

1. **Weekly Metrics Review**
   - [ ] API availability (target: >99.9%)
   - [ ] Average goal execution latency (target: <2 min P95)
   - [ ] Customer satisfaction score (target: >4.5/5)
   - [ ] Trial conversion rate (target: >30%)

2. **Incident Review**
   - [ ] Count and severity of incidents (last 7 days)
   - [ ] Mean time to detect (MTTD)
   - [ ] Mean time to resolve (MTTR)
   - [ ] Post-mortems completed for P0/P1

3. **Capacity Planning**
   - [ ] Database growth rate
   - [ ] Storage usage trend
   - [ ] Connection pool utilization trend
   - [ ] Projected capacity for next 30/90 days

4. **Security Review**
   - [ ] Failed authentication attempts (anomaly detection)
   - [ ] Unusual API access patterns
   - [ ] Credential rotation compliance
   - [ ] Pending security patches

5. **Action Items**
   - [ ] Assign owners to identified issues
   - [ ] Set due dates
   - [ ] Communicate to stakeholders

**Output**: Weekly health report (email to eng-all@ and leadership)

### Monthly Health Audit (2 hours)

**When**: First Monday of month  
**Who**: SRE team, security team, operations lead

**Checklist**:

1. **Performance Baseline Review**
   - [ ] Update performance baselines if system improved
   - [ ] Identify performance regressions
   - [ ] Review slow queries (>1 second)
   - [ ] Database index optimization opportunities

2. **Reliability Report**
   - [ ] Calculate SLA compliance (target: 99.9%)
   - [ ] Error budget remaining
   - [ ] Incident retrospective analysis
   - [ ] SLO adjustments needed?

3. **Security Posture**
   - [ ] All credentials rotated per schedule
   - [ ] Security patchesapplied
   - [ ] Vulnerability scans reviewed
   - [ ] Access audit (remove stale accounts)

4. **Customer Health**
   - [ ] Churn analysis (identify at-risk customers)
   - [ ] Feature adoption rates
   - [ ] Agent utilization trends
   - [ ] Support ticket volume & categories

5. **Infrastructure**
   - [ ] Cost optimization opportunities
   - [ ] Scaling strategy for next quarter
   - [ ] Tech debt prioritization
   - [ ] Tool/vendor evaluation

**Output**: Monthly health audit document (stored in Confluence)

---

## Health Check Scripts

### Script 1: Full Platform Health Check

```bash
#!/bin/bash
# full_health_check.sh
# Runs comprehensive health check across all services

echo "=== WAOOAW Platform Health Check ==="
echo "Timestamp: $(date)"
echo ""

# API Health
echo "1. API Health"
http_code=$(curl -s -o /dev/null -w "%{http_code}" https://api.waooaw.com/health)
if [ "$http_code" == "200" ]; then
  echo "   ✓ API: Healthy"
else
  echo "   ✗ API: Unhealthy (HTTP $http_code)"
fi

# Scheduler Health
echo "2. Scheduler Health"
docker compose exec -T plant-backend \
  python -m src.Plant.BackEnd.health.scheduler_health_check | \
  grep -q "Scheduler: Healthy" && \
  echo "   ✓ Scheduler: Running" || \
  echo "   ✗ Scheduler: Not running"

# Database Health
echo "3. Database Health"
docker compose exec -T postgres pg_isready -U waooaw > /dev/null 2>&1 && \
  echo "   ✓ Database: Accessible" || \
  echo "   ✗ Database: Not accessible"

# Connection Pool
echo "4. Connection Pool"
pool_util=$(docker compose exec -T plant-backend \
  python -c "from src.Plant.Core.database import engine; print(engine.pool.checkedin())")
pool_max=$(docker compose exec -T plant-backend \
  python -c "from src.Plant.Core.database import engine; print(engine.pool.size())")
pool_pct=$((100 * pool_util / pool_max))
if [ "$pool_pct" -lt 80 ]; then
  echo "   ✓ Connection Pool: $pool_pct% utilization"
else
  echo "   ⚠ Connection Pool: $pool_pct% utilization (high)"
fi

# Recent Errors
echo "5. Recent Errors (last 5 minutes)"
error_count=$(docker compose logs --since 5m 2>&1 | grep -i "error\|exception" | wc -l)
if [ "$error_count" -lt 10 ]; then
  echo "   ✓ Error count: $error_count (normal)"
else
  echo "   ⚠ Error count: $error_count (elevated)"
fi

# Goal Execution
echo "6. Recent Goal Executions"
docker compose exec -T postgres psql -U waooaw -d waooaw -tAc \
  "SELECT COUNT(*) FROM goal_runs WHERE created_at > NOW() - INTERVAL '1 hour' AND status = 'completed';" | \
  xargs -I {} echo "   ✓ Completed in last hour: {}"

docker compose exec -T postgres psql -U waooaw -d waooaw -tAc \
  "SELECT COUNT(*) FROM goal_runs WHERE created_at > NOW() - INTERVAL '1 hour' AND status = 'failed';" | \
  xargs -I {} echo "   ✗ Failed in last hour: {}"

echo ""
echo "=== Health Check Complete ==="
```

### Script 2: Credential Expiration Check

```bash
#!/bin/bash
# check_expiring_credentials.sh
# Alerts on credentials expiring in next 7 days

docker compose exec -T plant-backend \
  python -m src.Plant.BackEnd.scripts.check_expiring_credentials \
  --days 7 \
  --format table

# Example output:
# Customer ID | Platform  | Expires At          | Days Left | Action
# cust_123    | instagram | 2026-02-19 10:00:00 | 7         | Auto-refresh
# cust_456    | delta_ex  | 2026-02-20 15:30:00 | 8         | Notify customer
```

### Script 3: Alert Test (Verification)

```bash
#!/bin/bash
# test_alerts.sh
# Verify all critical alerts configured and working

echo "Testing PagerDuty integration..."
curl -X POST https://events.pagerduty.com/v2/enqueue \
  -H "Content-Type: application/json" \
  -d '{
    "routing_key": "'$PD_ROUTING_KEY'",
    "event_action": "trigger",
    "payload": {
      "summary": "TEST ALERT - Health check verification",
      "severity": "info",
      "source": "health_monitoring_playbook"
    }
  }'

echo ""
echo "Testing Slack integration..."
curl -X POST $SLACK_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"text": "TEST: Health monitoring alert verification"}'

echo ""
echo "Alert test complete. Verify alerts received."
```

---

## Escalation Procedures

### Escalation Matrix

| Alert Type | First Responder | After 15 min | After 30 min | After 1 hour |
|------------|----------------|--------------|--------------|--------------|
| P0: API Down | On-call SRE | SRE Lead | Eng Manager | CTO |
| P0: Data Loss | On-call SRE | SRE Lead + Security Lead | CTO | Exec Team |
| P1: Service Degradation | On-call SRE | SRE Lead | Eng Manager | - |
| P1: Integration Failure | On-call Ops | Backend Eng | Eng Manager | - |
| P2: Performance Issues | On-call Ops | SRE Team | - | - |
| P2: Credential Issues | Customer Support | Operations Lead | - | - |

### Escalation Contacts

**On-Call SRE**: PagerDuty rotation (primary + backup)  
**On-Call Operations**: Email ops-oncall@waooaw.com  
**SRE Lead**: sre-lead@waooaw.com / +91-XXXX-XXXXXX  
**Engineering Manager**: eng-manager@waooaw.com / +91-XXXX-XXXXXX  
**CTO**: cto@waooaw.com / +91-XXXX-XXXXXX  

### When to Escalate

**Escalate immediately if**:
- P0 alert not resolved within 30 minutes
- Data loss or corruption detected
- Security breach suspected
- Customer escalation to executive level
- Multiple alerts firing simultaneously (cascading failure)

**Do NOT escalate if**:
- Single P2 alert with known workaround
- Issue already being actively worked
- Resolution in progress and on track

### Escalation Message Template

```
ESCALATION REQUIRED

Incident: [Incident ID]
Severity: [P0/P1]
Started: [Timestamp]
Duration: [X minutes]

Summary: [Brief description]

Current Status:
- [What's been tried]
- [Current impact]
- [Blockers]

Escalating because: [Reason]

Incident Commander: [Name]
Active Responders: [Names]
```

---

## Incident Response Integration

This playbook integrates with the [Incident Response Procedures](./incident_response.md) runbook:

**When Alert Fires**:
1. On-call receives PagerDuty alert
2. Acknowledge within 5 minutes
3. Assess severity (P0/P1 = incident, P2/P3 = ticket)
4. If incident (P0/P1):
   - Declare incident in Slack #incidents
   - Follow [Incident Response Procedures](./incident_response.md)
   - Incident Commander takes over
5. If ticket (P2/P3):
   - Create ticket in Jira
   - Assign to appropriate team
   - Monitor until resolved

---

## Continuous Improvement

### Monthly Review Checklist

- [ ] Review alert noise (false positive rate <10%)
- [ ] Update thresholds based on new baseline
- [ ] Add new metrics as features launched
- [ ] Remove deprecated metrics
- [ ] Update runbook links in alert annotations
- [ ] Test escalation paths (quarterly drill)

### Feedback Loop

**Submit Improvements**:
- Slack: #sre-feedback
- Monthly SRE retrospective
- Post-incident action items

---

**Version History**

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-12 | Initial health monitoring playbook |

---

**Questions?**  
Contact: sre-team@waooaw.com or Slack #sre
