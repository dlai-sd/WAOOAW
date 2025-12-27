# Maintenance & Updates Runbook

Routine maintenance procedures for WAOOAW.

## Maintenance Schedule

| Task | Frequency | Day/Time | Duration |
|------|-----------|----------|----------|
| Security patches | Weekly | Sunday 2am UTC | 1-2 hours |
| Dependency updates | Bi-weekly | Sunday 2am UTC | 2-3 hours |
| Database maintenance | Monthly | First Sunday 2am UTC | 30-60 min |
| Certificate renewal | Automatic | N/A | N/A |
| Log rotation | Daily | Automatic | N/A |
| Backup verification | Weekly | Monday 9am UTC | 30 min |

## Security Patching

### OS/Container Updates

**Weekly Sunday maintenance:**

```bash
# 1. Build new images with latest base
cd backend
docker build -t ghcr.io/dlai-sd/waooaw/backend:$(git rev-parse --short HEAD)-patched .

# 2. Push to registry
docker push ghcr.io/dlai-sd/waooaw/backend:$(git rev-parse --short HEAD)-patched

# 3. Deploy to staging
./scripts/deploy_production.sh staging $(git rev-parse --short HEAD)-patched

# 4. Test staging for 24 hours

# 5. Deploy to production
./scripts/deploy_production.sh production $(git rev-parse --short HEAD)-patched
```

### Critical Security Patches

**For urgent CVE fixes:**

```bash
# Immediate patching (outside schedule)
# 1. Assess severity
echo "CVE-2024-XXXX: Critical RCE in library Y"

# 2. Update dependency
cd backend
pip install library-name==patched-version
pip freeze > requirements.txt

# 3. Test locally
pytest

# 4. Emergency deploy
git checkout -b hotfix/cve-2024-xxxx
git commit -am "security: patch CVE-2024-XXXX"
git push origin hotfix/cve-2024-xxxx

# CI/CD will build and you can deploy
./scripts/deploy_production.sh production <new-tag>
```

## Dependency Updates

### Backend (Python)

```bash
cd backend

# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package-name
pip freeze > requirements.txt

# Or update all (use with caution)
pip-review --auto

# Run tests
pytest

# Update lock file
pip-compile requirements.in > requirements.txt
```

### Frontend (JavaScript)

```bash
cd frontend

# Check for updates
npm outdated

# Update specific package
npm update package-name

# Or use npm-check-updates
npm install -g npm-check-updates
ncu -u
npm install

# Run tests
npm test
npm run build
```

### Security Audit

```bash
# Python
pip-audit

# JavaScript
npm audit
npm audit fix

# Docker images
docker scan ghcr.io/dlai-sd/waooaw/backend:latest
```

## Database Maintenance

### Monthly Maintenance

**First Sunday of each month, 2am UTC:**

```bash
# 1. Create pre-maintenance backup
./scripts/backup_database.sh

# 2. Analyze tables
psql -h prod-db -U admin -d waooaw_production << EOF
ANALYZE VERBOSE;
EOF

# 3. Vacuum (reclaim storage)
psql -h prod-db -U admin -d waooaw_production << EOF
VACUUM ANALYZE;
EOF

# 4. Reindex large tables
psql -h prod-db -U admin -d waooaw_production << EOF
REINDEX TABLE agents;
REINDEX TABLE actions;
REINDEX TABLE messages;
EOF

# 5. Update statistics
psql -h prod-db -U admin -d waooaw_production << EOF
ANALYZE agents;
ANALYZE actions;
ANALYZE messages;
EOF

# 6. Check for bloat
psql -h prod-db -U admin -d waooaw_production -f scripts/check_table_bloat.sql

# 7. Verify health
psql -h prod-db -U admin -d waooaw_production << EOF
SELECT schemaname, tablename, n_live_tup, n_dead_tup
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC
LIMIT 10;
EOF
```

### Index Maintenance

```bash
# Check unused indexes
psql -h prod-db -U admin -d waooaw_production << EOF
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
AND indexrelname NOT LIKE '%_pkey';
EOF

# Drop unused indexes (after verification)
# psql -h prod-db -U admin -d waooaw_production -c "DROP INDEX index_name;"

# Check missing indexes (analyze slow queries first)
# Use pg_stat_statements extension
```

## Redis Maintenance

### Weekly Cleanup

```bash
# Connect to Redis
redis-cli -h prod-redis-endpoint

# Check memory usage
INFO memory

# Check keyspace
INFO keyspace

# Clean expired keys (automatic, but can force)
# Redis auto-expires, but you can check:
# redis-cli --scan --pattern 'cache:*' | wc -l

# If needed, flush specific pattern
redis-cli --scan --pattern 'old-cache:*' | xargs redis-cli DEL
```

### Redis Snapshot

```bash
# Trigger manual snapshot
aws elasticache create-snapshot \
  --replication-group-id waooaw-redis-production \
  --snapshot-name waooaw-redis-maintenance-$(date +%Y%m%d)
```

## Log Management

### CloudWatch Logs

```bash
# Check log retention
aws logs describe-log-groups \
  --log-group-name-prefix /ecs/waooaw \
  --query 'logGroups[*].[logGroupName,retentionInDays]' \
  --output table

# Set retention (if needed)
aws logs put-retention-policy \
  --log-group-name /ecs/waooaw-backend-production \
  --retention-in-days 30
```

### Local Log Cleanup

```bash
# Clean old logs on EFS (agent data)
find /mnt/efs/waooaw/logs -name "*.log" -mtime +30 -delete

# Or via Lambda scheduled function
# (Recommended for EFS-mounted logs)
```

## Certificate Renewal

### SSL/TLS (ACM)

**Automatic renewal** by AWS Certificate Manager.

**Verify certificate status:**
```bash
./scripts/check_certificate_status.sh waooaw.ai

# Check expiry
aws acm describe-certificate \
  --certificate-arn $(aws acm list-certificates \
    --query "CertificateSummaryList[?DomainName=='waooaw.ai'].CertificateArn" \
    --output text) \
  --query 'Certificate.[NotBefore,NotAfter]' \
  --output table
```

**Manual renewal** (if needed):
```bash
# Request new certificate
./scripts/setup_ssl_certificate.sh waooaw.ai admin@waooaw.ai production

# Update ALB
./scripts/update_alb_certificate.sh waooaw-alb <new-cert-arn> <target-group>
```

## Backup Verification

### Weekly Verification

**Every Monday, 9am UTC:**

```bash
# Run backup verification script
./scripts/verify_backups.sh

# If issues found, fix immediately:
# - Missing backups: Trigger manual backup
# - Old backups: Check backup schedule
# - Failed backups: Review CloudWatch Logs
```

### Monthly Restore Test

**First Monday of each month:**

```bash
# Test database restore
LATEST_SNAPSHOT=$(aws rds describe-db-snapshots \
  --db-instance-identifier waooaw-postgres-production \
  --query 'reverse(sort_by(DBSnapshots, &SnapshotCreateTime))[0].DBSnapshotIdentifier' \
  --output text)

# Restore to test instance
./scripts/restore_database.sh ${LATEST_SNAPSHOT} waooaw-postgres-restore-test

# Verify data integrity
psql -h restore-test-endpoint -U admin -d waooaw_production << EOF
SELECT COUNT(*) as agent_count FROM agents;
SELECT COUNT(*) as action_count FROM actions;
SELECT MAX(created_at) as latest_record FROM actions;
EOF

# Clean up test instance
aws rds delete-db-instance \
  --db-instance-identifier waooaw-postgres-restore-test \
  --skip-final-snapshot
```

## Infrastructure Updates

### Terraform Updates

```bash
cd infrastructure/terraform/aws

# Check for provider updates
terraform init -upgrade

# Plan changes
terraform plan -out=maintenance.tfplan

# Review plan carefully
terraform show maintenance.tfplan

# Apply (during maintenance window)
terraform apply maintenance.tfplan

# Verify
./scripts/check_deployment_status.sh production
```

### ECS Task Definition Updates

```bash
# Update task definitions with new configs
# Edit: infrastructure/ecs/backend-task-definition.json

# Register new revision
aws ecs register-task-definition \
  --cli-input-json file://infrastructure/ecs/backend-task-definition.json

# Update service (zero downtime)
aws ecs update-service \
  --cluster waooaw-production \
  --service waooaw-backend \
  --task-definition waooaw-backend-production:new-revision
```

## Monitoring System Maintenance

### Prometheus

```bash
# Compact old data (reclaim storage)
curl -X POST http://prometheus:9090/api/v1/admin/tsdb/clean_tombstones

# Check storage
curl http://prometheus:9090/api/v1/status/tsdb

# Rotate logs (handled by retention)
# Prometheus automatically deletes data older than retention period
```

### Grafana

```bash
# Update Grafana
docker pull grafana/grafana:latest

# Backup dashboards (export JSON)
# Via Grafana UI: Dashboards → Manage → Export

# Update and restart
docker-compose up -d grafana
```

## Disaster Recovery Drills

### Quarterly DR Test

**Schedule: Every quarter (Jan, Apr, Jul, Oct)**

```bash
# 1. Simulate complete failure
echo "DR Drill: $(date)" > /tmp/dr-drill-log.txt

# 2. Execute full recovery
./scripts/disaster_recovery.sh
# Select option 3: Full infrastructure recovery

# 3. Document results
echo "Recovery Time: X minutes" >> /tmp/dr-drill-log.txt
echo "Issues encountered: ..." >> /tmp/dr-drill-log.txt

# 4. Update runbooks based on findings

# 5. Clean up DR test resources
```

## Maintenance Windows

### Announcing Maintenance

**48 hours before:**
```
[#announcements + Status Page]
🔧 Scheduled Maintenance
Date: Sunday, Jan 28, 2024
Time: 2:00-4:00 AM UTC
Impact: Minimal, some features may be briefly unavailable
Details: Security patches and database optimization
```

**During maintenance:**
```
[Status Page]
🔧 Maintenance in Progress
Started: 2:00 AM UTC
Expected completion: 4:00 AM UTC
Current status: Applying security patches [25% complete]
```

**After maintenance:**
```
[#announcements + Status Page]
✅ Maintenance Complete
Duration: 1.5 hours (completed ahead of schedule)
Results: Security patches applied, database optimized
Status: All systems operational
```

## Emergency Maintenance

**For critical issues requiring immediate maintenance:**

```bash
# 1. Assess impact
echo "Critical issue: Database corruption detected"

# 2. Page on-call
# (Automatic via PagerDuty for critical alerts)

# 3. Announce
# [#incidents + Status Page]
# 🚨 Emergency Maintenance in Progress

# 4. Execute fix
./scripts/disaster_recovery.sh
# Or specific fix procedures

# 5. Verify
./scripts/verify_backups.sh
curl -I https://waooaw.ai/health

# 6. Post-mortem
# Document incident, root cause, fix, prevention
```

## Maintenance Checklist

### Pre-Maintenance

- [ ] Announce maintenance window
- [ ] Create fresh backups
- [ ] Verify rollback procedures
- [ ] Test in staging
- [ ] Ensure on-call coverage

### During Maintenance

- [ ] Monitor system health
- [ ] Document all changes
- [ ] Take snapshots before critical changes
- [ ] Test after each change

### Post-Maintenance

- [ ] Verify all services operational
- [ ] Check monitoring dashboards
- [ ] Review logs for errors
- [ ] Update status page
- [ ] Document any issues encountered

## Best Practices

1. **Always backup before maintenance**
2. **Test changes in staging first**
3. **Make one change at a time**
4. **Document everything**
5. **Monitor for 1 hour after changes**
6. **Have rollback plan ready**
7. **Communicate clearly with team**

## Related Runbooks

- [Deployment](deployment.md)
- [Backup & Recovery](../infrastructure/backup/README.md)
- [Incident Response](incident-service-down.md)
