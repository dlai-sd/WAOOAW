# Incident Response Procedures

**Document Version**: 1.0  
**Last Updated**: 2026-02-12  
**Owner**: SRE & Engineering Teams  
**Purpose**: Standard procedures for detecting, responding to, and  resolving incidents

---

## Overview

This document defines WAOOAW's incident response framework, including severity classification, roles and responsibilities, communication protocols, resolution procedures, and post-incident review processes.

**Incident Definition**: Any unplanned interruption or degradation of service that impacts customers or poses security/data risk

**Target Audience**: On-call engineers, incident commanders, all engineering team members

---

## Table of Contents

1. [Severity Levels](#severity-levels)
2. [Incident Lifecycle](#incident-lifecycle)
3. [Roles & Responsibilities](#roles--responsibilities)
4. [Response Procedures](#response-procedures)
5. [Communication Templates](#communication-templates)
6. [Post-Incident Review](#post-incident-review)

---

## Severity Levels

### P0 - Critical (SEV-1)

**Definition**: Complete or near-complete service outage affecting all or most customers

**Examples**:
- API completely down (returning 500/503)
- Database inaccessible
- Authentication system down (no one can login)
- Data loss or corruption
- Security breach or active attack
- Payment processing completely broken

**Impact**:
- >90% of customers affected
- Core functionality unavailable
- Revenue impact significant
- Potential legal/compliance issues

**Response Requirements**:
- **Acknowledgment**: <5 minutes
- **Page**: Incident Commander + On-call SRE + On-call Backend Engineer
- **Update Frequency**: Every 15 minutes
- **Customer Communication**: Immediate (within 15 minutes)
- **Executive Notification**: Immediate (CTO, CEO)
- **Target Resolution**: 1-4 hours
- **Post-Incident Review**: Mandatory within 48 hours

### P1 - High (SEV-2)

**Definition**: Major degradation affecting significant portion of customers or critical feature unavailable

**Examples**:
- Scheduler not executing goals
- Social platform integrations failing (all platforms)
- Trading functionality broken
- Severe performance degradation (>5 second response times)
- Credential rotation system down
- Backup failure

**Impact**:
- 30-90% of customers affected
- Major feature unavailable
- Workarounds difficult or impossible
- Moderate revenue impact

**Response Requirements**:
- **Acknowledgment**: <15 minutes
- **Page**: On-call SRE
- **Update Frequency**: Every 30 minutes
- **Customer Communication**: Within 1 hour
- **Executive Notification**: CTO, Engineering Manager
- **Target Resolution**: 4-24 hours
- **Post-Incident Review**: Mandatory within 1 week

### P2 - Medium (SEV-3)

**Definition**: Partial degradation or non-critical feature impaired, affecting subset of customers

**Examples**:
- Single platform integration failing (Instagram only)
- Performance degradation (<5 second response times)
- Non-critical API endpoints down
- Intermittent errors (<10% failure rate)
- CP UI bug affecting workflow

**Impact**:
- <30% of customers affected
- Workarounds available
- Minor revenue impact
- Business continuity maintained

**Response Requirements**:
- **Acknowledgment**: <30 minutes (business hours only)
- **Page**: No page, Slack notification
- **Update Frequency**: Every 2 hours
- **Customer Communication**: If affecting >10 customers
- **Executive Notification**: Not required
- **Target Resolution**: 1-3 days
- **Post-Incident Review**: Optional

### P3 - Low (SEV-4)

**Definition**: Minor issues, cosmetic bugs, or isolated customer issues

**Examples**:
- Single customer experiencing unique issue
- UI cosmetic bug
- Documentation incorrect
- Non-customer-facing system degraded
- Monitoring alert with no customer impact

**Impact**:
- <5% of customers (or single customer)
- No business impact
- Easy workarounds

**Response Requirements**:
- **Acknowledgment**: Next business day
- **Page**: No
- **Update Frequency**: Not required
- **Customer Communication**: Direct to affected customer only
- **Executive Notification**: Not required
- **Target Resolution**: 1-2 weeks
- **Post-Incident Review**: Not required

---

## Incident Lifecycle

### Phase 1: Detection

**How Incidents Are Detected**:
1. **Automated Monitoring**: PagerDuty alert from Prometheus/Grafana
2. **Customer Report**: Support ticket or direct customer escalation
3. **Internal Discovery**: Team member notices issue
4. **Security Alert**: Security scanning tool or threat detection

**Initial Assessment** (Within 5 minutes):
- Is this a real incident or false alarm?
- What is the severity? (P0/P1/P2/P3)
- What is the scope? (% of customers affected)
- Is there immediate workaround?

### Phase 2: Declaration

**Declare Incident** (Slack: #incidents):
```
🚨 INCIDENT DECLARED 🚨

Incident ID: INC-2026-02-12-001
Severity: P1
Status: Investigating

Summary: Scheduler not executing goals, all customers affected

Incident Commander: @sarah-sre
Responders: @on-call-backend, @on-call-ops

Investigation started: 14:23 UTC
Next update: 14:45 UTC (22 minutes)

War room: #incident-inc-001
```

**Actions**:
- Create dedicated Slack channel: `#incident-inc-XXX`
- Create incident Google Doc for timeline/notes
- Page required responders
- Start status page update (if customer-facing)

### Phase 3: Investigation

**Gather Information**:
1. Review monitoring dashboards
2. Check recent deployments (last 24 hours)
3. Review logs for errors
4. Identify affected components
5. Formulate hypotheses

**Assign Tasks**:
- Incident Commander delegates investigation tasks
- Each responder updates their findings in incident doc
- Avoid duplicate investigation (coordinate via Slack)

**5 Why's Analysis** (Quick root cause):
Example:
- Why are goals not executing? → Scheduler service is down
- Why is scheduler down? → Pod crashed
- Why did pod crash? → Out of memory error
- Why out of memory? → Memory leak in new code
- Why memory leak? → Recent deployment didn't free resources

### Phase 4: Mitigation

**Immediate Relief** (Stop the bleeding):
- Rollback recent deployment
- Restart failing service
- Redirect traffic to healthy instances
- Apply temporary workaround
- Disable buggy feature

**Verify Mitigation**:
- Check monitoring: Metrics recovering?
- Test functionality: Does it work now?
- Customer validation: Random sample of customers test
- Monitor for recurrence: Watch for 30 minutes

### Phase 5: Resolution

**Full Resolution**:
- Root cause identified
- Permanent fix applied (not just mitigation)
- System fully recovered
- Monitoring confirms stability for 1+ hour
- No customer reports of ongoing issues

**Declare Resolved**:
```
✅ INCIDENT RESOLVED ✅

Incident ID: INC-2026-02-12-001
Severity: P1
Duration: 2 hours 37 minutes

Summary: Scheduler not executing goals - RESOLVED

Root Cause: Memory leak in scheduler service from deployment at 12:00 UTC
Resolution: Rolled back to previous version, scheduler resumed normal operation

Impact:
- Goals missed: ~450 across 87 customers
- Goals manually triggered: 450 (all recovered)
- Customer complaints: 12 support tickets

Next Steps:
- Post-incident review: Scheduled for 2026-02-14 10:00 AM
- Bug fix PR: #1234 (will include memory profiling)
- Prevention: Add memory leak detection to CI pipeline

Timeline: [Link to incident doc]

Thanks to: @sarah-sre, @mike-backend, @ops-team
```

### Phase 6: Post-Incident Review (PIR)

**Schedule Within**:
- P0: 48 hours
- P1: 1 week
- P2: Optional

**Attendees**:
- Incident Commander
- All responders
- Engineering Manager
- Product Manager (if user-facing)
- CTO (for P0 only)

**Agenda** (60 minutes):
1. Incident timeline review (10 min)
2. What went well? (10 min)
3. What went wrong? (15 min)
4. Root cause validation (10 min)
5. Action items (10 min)
6. Process improvements (5 min)

---

## Roles & Responsibilities

### Incident Commander (IC)

**Responsibilities**:
- Declares incident and assigns severity
- Coordinates all response activities
- Decides on mitigation strategies
- Maintains incident timeline
- Communicates to stakeholders
- Declares incident resolved
- Schedules post-incident review

**Authority**:
- Can page anyone, even off-duty
- Can make rollback decisions without approval
- Can declare code freeze
- Can escalate to executives

**Who**: On-call SRE Lead (primary), Engineering Manager (backup)

### Technical Lead (TL)

**Responsibilities**:
- Leads technical investigation
- Proposes mitigation strategies
- Coordinates with other engineers
- Reviews code/config changes
- Validates fixes before deployment

**Who**: On-call Backend Engineer or most experienced engineer available

### Communications Lead (CL)

**Responsibilities**:
- Drafts customer communications
- Updates status page
- Handles executive updates
- Manages support ticket responses
- Coordinates with PR/marketing (if public incident)

**Who**: Operations Lead or Customer Success Manager

### Scribe

**Responsibilities**:
- Documents timeline in incident doc
- Records decisions made
- Notes action items
- Captures metrics (time to detect, time to mitigate, etc.)
- Prepares PIR summary

**Who**: Any available team member (rotates)

---

## Response Procedures

### Procedure 1: API outage (P0)

**Symptoms**: Health check failing, 500/503 errors, no responses

**Immediate Actions** (First 5 minutes):
1. Declare P0 incident
2. Page Incident Commander + On-call SRE + On-call Backend
3. Check infrastructure status:
   ```bash
   kubectl get pods -n waooaw-prod
   docker ps | grep plant
   ```
4. Check recent deployments:
   ```bash
   kubectl rollout history deployment/plant-backend -n waooaw-prod
   ```

**Investigation Steps**:
1. Review logs for error spike:
   ```bash
   kubectl logs -n waooaw-prod deployment/plant-backend --tail=100
   ```
2. Check database connectivity
3. Check external service dependencies
4. Review monitoring dashboards

**Mitigation Options** (Choose fastest):
- **Option A**: Rollback recent deployment
  ```bash
  kubectl rollout undo deployment/plant-backend -n waooaw-prod
  ```
- **Option B**: Restart pods
  ```bash
  kubectl rollout restart deployment/plant-backend -n waooaw-prod
  ```
- **Option C**: Scale up replicas (if capacity issue)
  ```bash
  kubectl scale deployment/plant-backend --replicas=10 -n waooaw-prod
  ```

**Customer Communication** (Within 15 min):
- Update status page: "Investigating API service disruption"
- Send email to all active users (template: incident_notification.html)
- Post to Twitter/LinkedIn: "We're aware of service issues..."

### Procedure 2: Scheduler Failure (P1)

**Symptoms**: Goals not executing, scheduler health check failed

**Immediate Actions**:
1. Declare P1 incident
2. Check scheduler status:
   ```bash
   docker compose ps plant-scheduler
   docker compose logs plant-scheduler --tail=50
   ```
3. Check database access from scheduler

**Investigation**:
1. Recent config changes?
2. Database migration in progress?
3. Resource exhaustion (memory/CPU)?

**Mitigation**:
1. Restart scheduler:
   ```bash
   docker compose restart plant-scheduler
   ```
2. If persists, rollback to previous version
3. Manually trigger missed goals:
   ```bash
   docker compose exec plant-backend \
     python -m src.Plant.BackEnd.scripts.trigger_missed_goals \
     --since "2 hours ago"
   ```

### Procedure 3: Data Corruption (P0)

**Symptoms**: Reports of incorrect data, database integrity check failure

**Immediate Actions** (Critical: DO NOT MAKE WORSE):
1. Declare P0 incident + page engineering leadership immediately
2. **DO NOT** restart services (may propagate corruption)
3. **DO NOT** run migrations or schema changes
4. **DO NOT** delete anything
5. Take database snapshot immediately:
   ```bash
   pg_dump waooaw > /backup/emergency-$(date +%s).sql
   ```

**Investigation**:
1. Identify scope of corruption (which tables, how many rows)
2. Identify time corruption started (transaction logs)
3. Identify cause (buggy code, failed migration, manual error)

**Mitigation**:
1. If recent (< 1 hour), consider point-in-time recovery
2. If contained to specific customers, quarantine affected data
3. Restore from last known good backup (if severe)
4. **Always prefer data preservation over service restoration**

**Communication**:
- Notify customers immediately if their data affected
- Transparent about root cause and recovery plan
- Legal/compliance teams notified (GDPR, data breach protocols)

### Procedure 4: Security Breach (P0)

**Symptoms**: Unauthorized access, suspicious activity, data exfiltration

**Immediate Actions** (First 15 minutes):
1. Declare P0 incident + page CTO + Security team immediately
2. Isolate affected systems (may mean taking offline)
3. Preserve forensic evidence:
   ```bash
   # Capture current state before any changes
   docker compose logs > incident-$(date +%s)-logs.txt
   kubectl get pods -o yaml > incident-$(date +%s)-pods.yaml
   ```
4. Rotate all credentials (API keys, database passwords)
5. Notify legal/compliance teams

**DO NOT**:
- Delete logs (evidence needed for forensics)
- Notify attacker (don't tip them off you've detected them)
- Make public statements until legal review

**Follow**: [Security Incident Response Plan](./security_incident_response.md) (separate document)

---

## Communication Templates

### Internal: Incident Declaration

**Slack (#incidents)**:
```
🚨 INCIDENT DECLARED 🚨

ID: INC-YYYY-MM-DD-XXX
Severity: [P0/P1/P2/P3]
Status: Investigating

Summary: [One-line description]

Incident Commander: @username
Responders: @user1, @user2

War room: #incident-inc-XXX
Doc: [Google Doc Link]

Impact: [Brief description]
Start time: [Time]
Next update: [Time + 15/30 min]
```

### External: Status Page Update (P0/P1)

**Investigating**:
```
Investigating: We are currently investigating intermittent errors affecting API requests. Our team is actively working to identify the cause.

Update frequency: Every 15 minutes
Posted: 2026-02-12 14:23 UTC
```

**Identified**:
```
Identified: We have identified the root cause as [brief description]. Our team is implementing a fix.

Impact: ~40% of API requests may experience delays or errors
Workaround: [If available]
ETA: Resolution expected within 1 hour

Posted: 2026-02-12 14:45 UTC
```

**Monitoring**:
```
Monitoring: A fix has been deployed and the system is recovering. We are monitoring to ensure stability.

Impact: Service is restored for most customers. Some may experience brief delays as system catches up.

Posted: 2026-02-12 16:30 UTC
```

**Resolved**:
```
Resolved: The incident has been resolved. All systems are operating normally.

Summary: [Brief explanation]
Duration: 2 hours 7 minutes
Root cause: [One paragraph]

We apologize for the inconvenience. A detailed post-mortem will be published within 48 hours.

Posted: 2026-02-12 16:45 UTC
```

### External: Customer Email (P0/P1)

**Subject**: Service Disruption Update - [Date]

```
Dear WAOOAW Customers,

We experienced a service disruption today between [Time] and [Time] UTC.

What Happened:
[2-3 sentence description]

Impact:
- [Specific impact on customer experience]
- [Features affected]
- [Data integrity status - if relevant]

Resolution:
Our team responded immediately and [what we did to fix it].

Your Action Required:
[If any - otherwise say "None"]

We sincerely apologize for the inconvenience. We take reliability seriously and are implementing measures to prevent recurrence.

Questions? Contact support@waooaw.com

Detailed post-mortem: [Link - when available]

Thank you for your patience,
The WAOOAW Team
```

---

## Post-Incident Review

### PIR Document Template

```
# Post-Incident Review: INC-YYYY-MM-DD-XXX

Date: [Date of review]
Incident Date: [Date incident occurred]
Attendees: [List names and roles]

## Incident Summary

**Severity**: P0/P1/P2
**Duration**: X hours Y minutes
**Customers Affected**: X (Y% of total)
**Revenue Impact**: ₹X (if applicable)

**Brief Description**:
[2-3 sentences]

## Timeline

| Time (UTC) | Event |
|------------|-------|
| 14:00 | Deployment of v2.3.1 to production |
| 14:15 | First automated alert: API response time elevated |
| 14:18 | Customer support ticket: "Can't login" |
| 14:23 | Incident declared (IC: @sarah) |
| 14:30 | Root cause identified: Memory leak in new code |
| 14:35 | Decision made: Rollback deployment |
| 14:42 | Rollback complete |
| 14:50 | Service recovered, monitoring |
| 16:00 | Incident declared resolved |

## Root Cause

**Immediate Cause**:
[What directly caused the incident]

**Underlying Causes** (5 Why's):
1. Why did X happen? → Y
2. Why did Y happen? → Z
3. ...

**Contributing Factors**:
- [Factor 1]
- [Factor 2]

## Detection & Response

**What Went Well** ✅:
- Fast detection (3 minutes from deployment to alert)
- Clear escalation path followed
- Quick decision on rollback
- Good communication to customers

**What Went Wrong** ❌:
- Monitoring didn't catch issue in staging
- Took 12 minutes to identify root cause (too long)
- Rollback process manual and slow
- Customer communication delayed (should be <15 min)

## preventive Actions

| Action Item | Owner | Due Date | Priority | Status |
|-------------|-------|----------|----------|--------|
| Add memory leak detection to CI pipeline | @mike-backend | 2026-02-20 | P0 | In Progress |
| Automate deployment rollback | @devops-team | 2026-02-28 | P1 | Not Started |
| Improve staging environment parity with prod | @sre-team | 2026-03-15 | P1 | Not Started |
| Create customer communication playbook | @ops-lead | 2026-02-25 | P2 | Not Started |

## Lessons Learned

- **Lesson 1**: Staging environment missed this because [reason] → Action: [solution]
- **Lesson 2**: Rollback took 7 minutes due to manual process → Action: Automate
- **Lesson 3**: Customer communication template needs improvement → Action: Create templates

## Appendix

- Incident Slack channel: #incident-inc-001
- Incident doc: [Link]
- Monitoring dashboard during incident: [Screenshot/Link]
- Customer support tickets: [Links]
```

### PIR Distribution

**Internal**:
- Email to eng-all@ and leadership
- Post in Slack #engineering
- Add to knowledge base

**External** (P0 only, optional for P1):
- Publish redacted version to blog (transparency)
- Link from status page
- Include in next customer newsletter

---

## Metrics & Reporting

**Metrics to Track**:
- **MTTD** (Mean Time To Detect): Alert fired → Incident declared
- **MTTA** (Mean Time To Acknowledge): Incident declared → First responder engaged
- **MTTI** (Mean Time To Identify): Investigation started → Root cause identified
- **MTTM** (Mean Time To Mitigate): Root cause identified → Service restored
- **MTTR** (Mean Time To Resolve): Incident declared → Fully resolved

**Targets**:
- P0 MTTD: <5 minutes
- P0 MTTA: <5 minutes
- P0 MTTR: <4 hours
- P1 MTTR: <24 hours

**Monthly Report**:
- Total incidents by severity
- Average MTTR by severity
- Most common root causes
- Action item completion rate
- Repeat incidents (same root cause)

---

## continuous Improvement

**Quarterly Review**:
- Review all PIR action items (completion rate?)
- Identify systemic issues (same problems recurring)
- Update incident response procedures
- Conduct incident response drill (tabletop exercise)

**Blameless Culture**:
- PIRs focus on systems and processes, not individuals
- Assume everyone acted with best intentions
- Encourage transparency and honesty
- Action items improve systems, not punish people

---

**Version History**

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-12 | Initial incident response procedures |

---

**Questions?**  
Contact: sre-team@waooaw.com or Slack #sre
