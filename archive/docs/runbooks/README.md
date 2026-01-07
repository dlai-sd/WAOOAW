# WAOOAW Production Runbooks

Operational procedures and incident response guides for WAOOAW production.

## Quick Access

### Operational Procedures
- **[Deployment](deployment.md)** - Production deployment procedures
- **[Scaling](scaling.md)** - Auto-scaling and manual scaling procedures
- **[Maintenance](maintenance.md)** - Routine maintenance and updates

### Incident Response
- **[Service Down](incident-service-down.md)** - Complete service outage
- **[High Load/Performance](incident-high-load.md)** - Performance degradation
- **[Database Issues](incident-database.md)** - Database problems

### Support
- **[On-Call Guide](oncall-guide.md)** - On-call engineer handbook
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

## Emergency Contacts

### On-Call Rotation

| Role | Primary | Backup | PagerDuty |
|------|---------|--------|-----------|
| Platform Engineer | @engineer1 | @engineer2 | +1-XXX-XXXX |
| Backend Engineer | @engineer3 | @engineer4 | +1-XXX-YYYY |
| DevOps | @engineer5 | @engineer6 | +1-XXX-ZZZZ |

### Escalation Path

1. **L1**: On-call engineer (responds to PagerDuty)
2. **L2**: Team lead (if issue not resolved in 30 min)
3. **L3**: Engineering manager (for major incidents)
4. **L4**: CTO (for critical business impact)

### External Contacts

- **AWS Support**: Support case via AWS Console
- **GitHub Support**: support@github.com
- **Anthropic Support**: support@anthropic.com

## System Architecture

```
                                    ┌─────────────┐
                                    │   Route53   │
                                    │     DNS     │
                                    └──────┬──────┘
                                           │
                                    ┌──────▼──────┐
                                    │     ALB     │
                                    │  HTTPS 443  │
                                    └──────┬──────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                      │
            ┌───────▼────────┐     ┌───────▼────────┐   ┌───────▼────────┐
            │  Backend API   │     │  Backend API   │   │  Backend API   │
            │   ECS Task     │     │   ECS Task     │   │   ECS Task     │
            │   Port 8000    │     │   Port 8000    │   │   Port 8000    │
            └───────┬────────┘     └───────┬────────┘   └───────┬────────┘
                    │                      │                      │
                    └──────────────────────┼──────────────────────┘
                                           │
                        ┌──────────────────┼──────────────────┐
                        │                  │                  │
                ┌───────▼────────┐  ┌──────▼──────┐  ┌───────▼────────┐
                │  RDS Postgres  │  │   Redis     │  │   Agent ECS    │
                │   Multi-AZ     │  │ ElastiCache │  │   + EFS        │
                └────────────────┘  └─────────────┘  └────────────────┘
```

## Key Services

| Service | Purpose | Port | Health Check |
|---------|---------|------|--------------|
| Backend API | REST API, GraphQL | 8000 | `/health` |
| Agent | WowVision Prime | 9090 | `/metrics` |
| PostgreSQL | Primary database | 5432 | RDS status |
| Redis | Cache, sessions | 6379 | ElastiCache status |
| Prometheus | Metrics collection | 9090 | `/metrics` |
| Grafana | Dashboards | 3000 | `/api/health` |

## Quick Diagnostics

### Check Overall System Health

```bash
# Run comprehensive health check
./scripts/check_deployment_status.sh production

# Check all services
curl -I https://waooaw.ai/health
curl -I https://grafana.waooaw.ai/api/health

# View Grafana dashboard
open https://grafana.waooaw.ai/d/overview
```

### Check Specific Service

```bash
# Backend
aws ecs describe-services \
  --cluster waooaw-production \
  --services waooaw-backend \
  --query 'services[0].[serviceName,status,runningCount,desiredCount]'

# Database
aws rds describe-db-instances \
  --db-instance-identifier waooaw-postgres-production \
  --query 'DBInstances[0].[DBInstanceStatus,Endpoint.Address]'

# Redis
aws elasticache describe-replication-groups \
  --replication-group-id waooaw-redis-production \
  --query 'ReplicationGroups[0].[Status,NodeGroups[0].PrimaryEndpoint.Address]'
```

### Recent Logs

```bash
# Backend logs (last 5 minutes)
aws logs tail /ecs/waooaw-backend-production --since 5m --follow

# Agent logs
aws logs tail /ecs/waooaw-agent-production --since 5m --follow

# Recent errors
aws logs filter-pattern '"ERROR"' \
  --log-group-name /ecs/waooaw-backend-production \
  --start-time $(date -u -d '30 minutes ago' +%s)000
```

## Incident Response Process

### 1. Detect

**Alerting channels:**
- PagerDuty (critical)
- Slack #alerts (warning)
- Grafana alerts
- CloudWatch alarms
- User reports

### 2. Assess

```bash
# Severity levels
# SEV1: Complete outage, data loss
# SEV2: Major feature down, significant degradation
# SEV3: Minor feature affected, workaround available
# SEV4: Cosmetic issue, no business impact

# Quick assessment
./scripts/check_deployment_status.sh production
open https://grafana.waooaw.ai/d/overview
```

### 3. Communicate

```
[#incidents]
🚨 INCIDENT - SEV2
Title: Backend API returning 500 errors
Started: 2024-01-27 14:32 UTC
Impact: 10% of requests failing
Status: Investigating
Responder: @oncall-engineer
```

### 4. Mitigate

Follow relevant runbook:
- [Service Down](incident-service-down.md)
- [High Load](incident-high-load.md)
- [Database Issues](incident-database.md)

### 5. Resolve

```bash
# Verify resolution
curl -I https://waooaw.ai/health
./scripts/check_deployment_status.sh production

# Monitor for 30 minutes
watch -n 60 'curl -s https://waooaw.ai/health | jq .status'
```

### 6. Post-Mortem

**Within 48 hours of major incidents:**
- Timeline of events
- Root cause analysis
- Impact assessment
- Action items to prevent recurrence
- Update runbooks with lessons learned

## Monitoring & Alerting

### Dashboards

- **Overview**: https://grafana.waooaw.ai/d/overview
- **Backend API**: https://grafana.waooaw.ai/d/backend
- **Database**: https://grafana.waooaw.ai/d/database
- **Agent**: https://grafana.waooaw.ai/d/agent

### Key Metrics

| Metric | Normal | Warning | Critical |
|--------|--------|---------|----------|
| HTTP 2xx rate | > 99% | < 99% | < 95% |
| HTTP 5xx rate | < 0.1% | > 0.1% | > 1% |
| Response time P95 | < 500ms | > 500ms | > 1000ms |
| CPU utilization | < 70% | > 70% | > 90% |
| Memory utilization | < 80% | > 80% | > 95% |
| Database connections | < 80 | > 80 | > 95 |
| Disk usage | < 80% | > 80% | > 90% |

### Alert Routing

```
Critical → PagerDuty + Slack #incidents
Warning → Slack #alerts
Info → Slack #monitoring
```

## Access & Permissions

### AWS Console

- **Production**: Requires MFA
- **Role**: `WaooawProductionEngineer`
- **URL**: https://console.aws.amazon.com

### Database

```bash
# Via bastion host only
ssh bastion.waooaw.ai
psql -h prod-db-internal -U admin -d waooaw_production
```

### ECS Exec

```bash
# Shell into running container
aws ecs execute-command \
  --cluster waooaw-production \
  --task <task-id> \
  --container backend \
  --interactive \
  --command "/bin/bash"
```

### Secrets

```bash
# Retrieve from AWS Secrets Manager
aws secretsmanager get-secret-value \
  --secret-id waooaw/prod/postgres \
  --query SecretString \
  --output text | jq -r .password
```

## Useful Commands

### Quick Rollback

```bash
./scripts/rollback_production.sh production
```

### Scale Immediately

```bash
aws ecs update-service \
  --cluster waooaw-production \
  --service waooaw-backend \
  --desired-count 6
```

### Create Database Backup

```bash
./scripts/backup_database.sh
```

### Check Recent Deployments

```bash
git log --oneline --grep="deploy" -10
aws ecs list-task-definitions --family-prefix waooaw-backend | tail -5
```

### View Recent Changes

```bash
# Terraform
cd infrastructure/terraform/aws
terraform show

# ECS services
aws ecs describe-services \
  --cluster waooaw-production \
  --services waooaw-backend \
  --query 'services[0].events[:5]'
```

## Training & Resources

### New Team Member Onboarding

1. Read all runbooks (this directory)
2. Get AWS access (MFA required)
3. Join #incidents, #deployments, #alerts Slack channels
4. Shadow on-call engineer for 1 week
5. Perform test deployment to staging
6. Review recent post-mortems
7. Add to on-call rotation

### Learning Resources

- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [PostgreSQL Administration](https://www.postgresql.org/docs/current/admin.html)
- [Redis Operations](https://redis.io/docs/management/)
- [Incident Response](https://response.pagerduty.com/)

### Practice Exercises

- Deploy to staging
- Scale backend service up and down
- Simulate database failover
- Test backup and restore
- Run disaster recovery drill

## Maintenance Schedule

| Day | Time (UTC) | Task |
|-----|------------|------|
| Daily | 02:00 | Automated backups |
| Monday | 09:00 | Backup verification |
| Sunday | 02:00 | Security patches |
| First Sunday | 02:00 | Database maintenance |
| Monthly | 09:00 | Restore test |
| Quarterly | TBD | DR drill |

## Change Management

### Standard Changes

**Low risk, pre-approved:**
- Security patches
- Dependency updates
- Configuration changes
- Scaling operations

**Process**: Follow deployment runbook

### Major Changes

**High risk or significant impact:**
- Database schema changes
- Infrastructure changes
- Major version upgrades

**Process**:
1. Create RFC (Request for Change)
2. Review with team
3. Test in staging
4. Schedule maintenance window
5. Execute during window
6. Post-change verification

### Emergency Changes

**Critical fixes:**
- Security vulnerabilities
- Data loss prevention
- Complete outages

**Process**:
1. Page on-call + team lead
2. Assess impact
3. Execute fix
4. Verify resolution
5. Post-mortem within 24 hours

## Document Updates

**Keep runbooks current:**
- Update after every major incident
- Review quarterly for accuracy
- Version control in Git
- Notify team of significant changes

**Last Updated**: 2024-01-27
**Version**: 1.0.0
**Maintained By**: Platform Engineering Team
