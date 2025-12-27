# Deployment Runbook

Production deployment procedures for WAOOAW.

## Quick Reference

| Task | Command | Time |
|------|---------|------|
| Deploy to production | `./scripts/deploy_production.sh production <tag>` | 15-20 min |
| Check status | `./scripts/check_deployment_status.sh production` | Instant |
| Rollback | `./scripts/rollback_production.sh production` | 5-10 min |

## Pre-Deployment Checklist

**Before every production deployment:**

- [ ] All tests passing in CI/CD
- [ ] Staging environment tested and verified
- [ ] Database migrations reviewed and tested
- [ ] Rollback plan identified
- [ ] Team notified (#deployments Slack channel)
- [ ] No ongoing incidents
- [ ] Outside of peak traffic hours (if possible)

## Standard Deployment

### 1. Prepare

```bash
# Switch to deployment branch
git checkout main
git pull origin main

# Verify latest commit
git log -1 --oneline

# Check CI/CD status
gh run list --limit 1

# Tag release
git tag v1.2.3
git push origin v1.2.3
```

### 2. Deploy

```bash
# Set environment variables
export AWS_REGION="us-east-1"
export ENVIRONMENT="production"

# Run deployment
./scripts/deploy_production.sh production v1.2.3
```

**Expected output:**
```
🚀 WAOOAW Production Deployment
================================
Environment: production
Image: ghcr.io/dlai-sd/waooaw/backend:v1.2.3

✅ Image exists
✅ Task definition registered (revision 42)
✅ ECS service updated
⏳ Waiting for deployment...
✅ Deployment stable
✅ Migrations completed
✅ Health checks passed

Deployment completed in 16 minutes
```

### 3. Verify

```bash
# Check deployment status
./scripts/check_deployment_status.sh production

# Test health endpoint
curl -I https://waooaw.ai/health

# Check logs
aws logs tail /ecs/waooaw-backend-production --follow --since 5m

# Monitor dashboards
open https://grafana.waooaw.ai/d/overview
```

### 4. Monitor

**First 30 minutes after deployment:**
- Watch Grafana dashboards for anomalies
- Monitor error rates in Sentry
- Check CloudWatch Logs for errors
- Verify key user flows

**Success criteria:**
- ✅ HTTP 2xx response rate > 99%
- ✅ P95 latency < 500ms
- ✅ Error rate < 1%
- ✅ All health checks passing

## Deployment with Database Migrations

### Pre-Migration

```bash
# Review migration SQL
cat backend/alembic/versions/001_add_agent_status.py

# Test on staging
ENVIRONMENT=staging ./scripts/deploy_production.sh staging v1.2.3

# Verify data integrity
psql -h staging-db -U admin -c "SELECT COUNT(*) FROM agents;"
```

### Deploy with Migrations

```bash
# Deployment script automatically runs migrations
./scripts/deploy_production.sh production v1.2.3

# Or manually run migrations
export DB_HOST=$(terraform output -raw rds_endpoint)
export DB_PASSWORD=$(aws secretsmanager get-secret-value --secret-id waooaw/prod/postgres --query SecretString --output text | jq -r .password)

cd backend
alembic upgrade head
```

### Post-Migration

```bash
# Verify migration applied
psql -h prod-db -U admin -c "SELECT version_num FROM alembic_version;"

# Check data integrity
psql -h prod-db -U admin -c "SELECT COUNT(*), status FROM agents GROUP BY status;"
```

## Rollback Procedures

### Automatic Rollback

Deployment script automatically rolls back on:
- Deployment timeout (15 minutes)
- Health check failures
- Service instability

### Manual Rollback

```bash
# Quick rollback to previous version
./scripts/rollback_production.sh production

# Rollback to specific revision
./scripts/rollback_production.sh production 41

# Verify rollback
./scripts/check_deployment_status.sh production
curl -I https://waooaw.ai/health
```

### Database Rollback

```bash
# Rollback migration (use with caution)
cd backend
alembic downgrade -1

# Or restore from backup
./scripts/restore_database.sh waooaw-production-20240127-020000
```

## Emergency Deployment

**Use only for critical production issues:**

```bash
# Skip CI/CD and deploy immediately
./scripts/deploy_production.sh production v1.2.4 --force

# Deploy specific commit (without tag)
./scripts/deploy_production.sh production $(git rev-parse HEAD) --force
```

**After emergency deployment:**
1. Create incident report
2. Schedule proper deployment with full testing
3. Update runbooks with lessons learned

## Blue-Green Deployment

Default deployment strategy. Zero downtime.

**How it works:**
1. New tasks start alongside old tasks (Blue + Green)
2. Health checks validate new tasks
3. Load balancer shifts traffic to new tasks
4. Old tasks drain and terminate

**Monitor during deployment:**
```bash
# Watch task status
watch -n 5 './scripts/check_deployment_status.sh production'

# Monitor ALB target health
aws elbv2 describe-target-health \
  --target-group-arn $(terraform output -raw target_group_arn) \
  --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State]' \
  --output table
```

## Canary Deployment

**For high-risk changes:**

```bash
# Deploy to 10% of traffic
aws ecs update-service \
  --cluster waooaw-production \
  --service waooaw-backend \
  --deployment-configuration "maximumPercent=110,minimumHealthyPercent=100"

# Monitor for 30 minutes
# If successful, scale to 100%
```

## Scheduled Deployments

**Recommended deployment windows:**
- **Best**: Tuesday-Thursday, 10am-2pm UTC
- **Avoid**: Friday, Monday morning, weekends
- **Never**: During marketing campaigns or major events

## Post-Deployment

### Announce

```
[Slack #deployments]
🚀 Production deployed: v1.2.3
✅ Backend: revision 42
✅ Agent: revision 31
📊 Grafana: https://grafana.waooaw.ai/d/overview
⏱️ Deployed at: 2024-01-27 14:30 UTC
```

### Document

Update deployment log:
```bash
echo "$(date -u +%Y-%m-%d\ %H:%M:%S) | v1.2.3 | revision-42 | deployed" >> docs/deployment-log.txt
```

### Cleanup

```bash
# Remove old Docker images (keep last 5)
docker image prune -a --filter "until=720h"

# Clean old ECS task definitions (keep last 10)
# AWS automatically manages this
```

## Troubleshooting

### Deployment Timeout

**Symptom**: Deployment stuck for > 15 minutes

**Action**:
```bash
# Check service events
aws ecs describe-services \
  --cluster waooaw-production \
  --services waooaw-backend \
  --query 'services[0].events[:10]' \
  --output table

# Check task failures
aws ecs list-tasks \
  --cluster waooaw-production \
  --desired-status STOPPED \
  --query 'taskArns' \
  --output text | head -1 | xargs aws ecs describe-tasks --cluster waooaw-production --tasks
```

### Health Check Failures

**Symptom**: Tasks failing health checks

**Action**:
```bash
# Check task logs
aws logs tail /ecs/waooaw-backend-production --follow

# Test health endpoint from within VPC
aws ecs run-task --cluster waooaw-production --task-definition debug-task
# Then: curl http://task-ip:8000/health
```

### Database Connection Errors

**Symptom**: "Connection refused" or timeout errors

**Action**:
```bash
# Verify security group rules
aws ec2 describe-security-groups --group-ids sg-xxxxx

# Test database connectivity
psql -h prod-db-endpoint -U admin -c "SELECT 1;"

# Check RDS status
aws rds describe-db-instances --db-instance-identifier waooaw-postgres-production
```

## Communication Templates

### Pre-Deployment Notification

```
[#deployments] 
⏰ Scheduled Deployment: v1.2.3
📅 Time: 2024-01-27 14:00 UTC
⏱️ Duration: ~20 minutes
📝 Changes: Bug fixes, performance improvements
🔗 Release notes: https://github.com/dlai-sd/WAOOAW/releases/tag/v1.2.3
```

### Deployment Complete

```
[#deployments]
✅ Deployment Complete: v1.2.3
⏱️ Completed in: 18 minutes
📊 Status: All systems operational
🔍 Monitoring: https://grafana.waooaw.ai
```

### Deployment Failed

```
[#deployments + @oncall]
❌ Deployment Failed: v1.2.3
⏱️ Failed after: 8 minutes
🔄 Status: Rolled back to v1.2.2
🔍 Investigating: [link to incident]
```

## Best Practices

1. **Always deploy to staging first**
2. **Deploy during business hours** (easier to get help)
3. **One change at a time** (easier to debug)
4. **Monitor for 30+ minutes** after deployment
5. **Document everything** in deployment log
6. **Communicate clearly** with team
7. **Have rollback plan ready** before deploying

## Related Runbooks

- [Scaling Procedures](scaling.md)
- [Maintenance & Updates](maintenance.md)
- [Incident Response](../runbooks/incident-service-down.md)
- [Database Operations](database-operations.md)
