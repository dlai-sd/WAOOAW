# Scaling Runbook

Procedures for scaling WAOOAW infrastructure.

## Quick Reference

| Action | Command | Time |
|--------|---------|------|
| Scale backend | `aws ecs update-service --desired-count N` | 2-5 min |
| Scale database | `aws rds modify-db-instance --db-instance-class` | 15-30 min |
| Scale Redis | `aws elasticache modify-replication-group --cache-node-type` | 15-30 min |
| Auto-scaling status | `aws application-autoscaling describe-scalable-targets` | Instant |

## Auto-Scaling (Recommended)

### Setup Auto-Scaling

```bash
# Register ECS service as scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/waooaw-production/waooaw-backend \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# CPU-based scaling policy
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/waooaw-production/waooaw-backend \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleInCooldown": 300,
    "ScaleOutCooldown": 60
  }'

# Request-based scaling policy
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/waooaw-production/waooaw-backend \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name request-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 1000.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ALBRequestCountPerTarget",
      "ResourceLabel": "app/waooaw-alb/xxx/targetgroup/waooaw-backend/yyy"
    }
  }'
```

### Monitor Auto-Scaling

```bash
# Check current scaling status
aws application-autoscaling describe-scalable-targets \
  --service-namespace ecs \
  --resource-ids service/waooaw-production/waooaw-backend

# View scaling activities
aws application-autoscaling describe-scaling-activities \
  --service-namespace ecs \
  --resource-id service/waooaw-production/waooaw-backend \
  --max-results 10
```

## Manual Scaling

### Scale Backend Service

**When to scale:**
- CPU utilization > 70% for 5+ minutes
- Request queue depth increasing
- P95 latency > 1 second
- Anticipated traffic surge (marketing campaign)

**Scale up:**
```bash
# Check current capacity
aws ecs describe-services \
  --cluster waooaw-production \
  --services waooaw-backend \
  --query 'services[0].[desiredCount,runningCount,pendingCount]'

# Increase to 6 tasks
aws ecs update-service \
  --cluster waooaw-production \
  --service waooaw-backend \
  --desired-count 6

# Monitor scaling
watch -n 5 'aws ecs describe-services \
  --cluster waooaw-production \
  --services waooaw-backend \
  --query "services[0].[desiredCount,runningCount]"'
```

**Scale down:**
```bash
# Gradually reduce after traffic decreases
aws ecs update-service \
  --cluster waooaw-production \
  --service waooaw-backend \
  --desired-count 2
```

### Scale Agent Service

```bash
# Scale based on workload
aws ecs update-service \
  --cluster waooaw-production \
  --service waooaw-agent \
  --desired-count 3

# Verify agent distribution
aws ecs list-tasks \
  --cluster waooaw-production \
  --service-name waooaw-agent \
  --query 'taskArns' \
  --output table
```

### Scale Database (RDS)

**When to scale:**
- CPU utilization > 80%
- Database connections > 80% of max
- Disk I/O saturated
- Query latency increasing

**Vertical scaling (instance size):**
```bash
# Check current instance
aws rds describe-db-instances \
  --db-instance-identifier waooaw-postgres-production \
  --query 'DBInstances[0].DBInstanceClass'

# Scale to larger instance
aws rds modify-db-instance \
  --db-instance-identifier waooaw-postgres-production \
  --db-instance-class db.t3.large \
  --apply-immediately

# Monitor modification
aws rds describe-db-instances \
  --db-instance-identifier waooaw-postgres-production \
  --query 'DBInstances[0].[DBInstanceStatus,DBInstanceClass]'
```

**⚠️ Warning**: Scaling database causes ~5-10 minute downtime

**Zero-downtime scaling (read replicas):**
```bash
# Create read replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier waooaw-postgres-production-replica \
  --source-db-instance-identifier waooaw-postgres-production \
  --db-instance-class db.t3.medium \
  --publicly-accessible false

# Update application to use replica for reads
# In backend config: READ_REPLICA_HOST=replica-endpoint
```

### Scale Redis (ElastiCache)

**When to scale:**
- Memory utilization > 75%
- Evictions occurring
- CPU utilization > 70%
- Connection count increasing

**Vertical scaling:**
```bash
# Scale to larger node type
aws elasticache modify-replication-group \
  --replication-group-id waooaw-redis-production \
  --cache-node-type cache.t3.medium \
  --apply-immediately
```

**Horizontal scaling (cluster mode):**
```bash
# Add shard (for cluster-mode enabled)
aws elasticache increase-replica-count \
  --replication-group-id waooaw-redis-production \
  --new-replica-count 2 \
  --apply-immediately
```

## Capacity Planning

### Current Capacity

```bash
# Backend
BACKEND_TASKS=$(aws ecs describe-services \
  --cluster waooaw-production \
  --services waooaw-backend \
  --query 'services[0].runningCount')

# Each task: 1 vCPU, 2GB RAM
echo "Backend capacity: ${BACKEND_TASKS} tasks"
echo "CPU: $((BACKEND_TASKS * 1)) vCPU"
echo "Memory: $((BACKEND_TASKS * 2)) GB"

# Database
aws rds describe-db-instances \
  --db-instance-identifier waooaw-postgres-production \
  --query 'DBInstances[0].[DBInstanceClass,AllocatedStorage]'

# Redis
aws elasticache describe-replication-groups \
  --replication-group-id waooaw-redis-production \
  --query 'ReplicationGroups[0].[CacheNodeType,NumCacheClusters]'
```

### Traffic Estimation

**Current baseline:**
- 1000 requests/minute
- 2 backend tasks @ 30% CPU
- Each task handles ~500 req/min

**Scaling formula:**
```
Required tasks = (Expected req/min) / 500
Add 20% buffer for spikes
```

**Example:**
```
Marketing campaign: 5000 req/min expected
Tasks needed: 5000 / 500 = 10 tasks
With buffer: 10 * 1.2 = 12 tasks
```

### Pre-Event Scaling

**For planned traffic surges:**

```bash
#!/bin/bash
# Pre-event scaling script

# 1 hour before event
echo "Scaling up for event..."

# Backend: 2 → 8 tasks
aws ecs update-service \
  --cluster waooaw-production \
  --service waooaw-backend \
  --desired-count 8

# Warm up ALB targets
for i in {1..50}; do
  curl -s https://waooaw.ai/health > /dev/null
  sleep 0.5
done

# Disable auto-scaling (prevent scale-down)
aws application-autoscaling deregister-scalable-target \
  --service-namespace ecs \
  --resource-id service/waooaw-production/waooaw-backend \
  --scalable-dimension ecs:service:DesiredCount

echo "✅ Pre-scaled for event"
```

**After event:**
```bash
# Re-enable auto-scaling
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/waooaw-production/waooaw-backend \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# Gradually scale down
aws ecs update-service \
  --cluster waooaw-production \
  --service waooaw-backend \
  --desired-count 2
```

## Cost Optimization

### Right-Sizing

**Check utilization:**
```bash
# Backend CPU utilization (last 7 days)
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=waooaw-backend Name=ClusterName,Value=waooaw-production \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Average \
  --query 'Datapoints[*].Average' \
  --output text | \
  awk '{sum+=$1; count++} END {print "Average CPU:", sum/count "%"}'
```

**If average CPU < 30% for 7 days:**
- Consider reducing task count
- Or reducing CPU allocation per task

### Scheduled Scaling

**Scale down during off-peak hours:**
```bash
# EventBridge rule to scale down at night
aws events put-rule \
  --name waooaw-scale-down \
  --schedule-expression "cron(0 2 * * ? *)"

aws events put-targets \
  --rule waooaw-scale-down \
  --targets "Id"="1","Arn"="arn:aws:lambda:...:function:scale-ecs","Input"='{"count":2}'

# Scale up in the morning
aws events put-rule \
  --name waooaw-scale-up \
  --schedule-expression "cron(0 8 * * ? *)"
```

## Monitoring Scaling

### Key Metrics

```bash
# Dashboard in Grafana
# - ECS service desired/running count
# - CPU/Memory utilization per service
# - Request rate per task
# - Auto-scaling activity

# CloudWatch alarms
aws cloudwatch put-metric-alarm \
  --alarm-name waooaw-high-cpu \
  --alarm-description "Backend CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=ServiceName,Value=waooaw-backend
```

### Scaling Alerts

**Slack notifications:**
```bash
# SNS topic for scaling events
aws sns create-topic --name waooaw-scaling-events

# Subscribe to Slack webhook
aws sns subscribe \
  --topic-arn arn:aws:sns:...:waooaw-scaling-events \
  --protocol https \
  --notification-endpoint https://hooks.slack.com/services/...
```

## Troubleshooting

### Scaling Not Working

**Symptom**: Desired count changes but tasks not starting

**Check:**
```bash
# ECS capacity
aws ecs describe-clusters --clusters waooaw-production

# Task placement failures
aws ecs describe-services \
  --cluster waooaw-production \
  --services waooaw-backend \
  --query 'services[0].events[:5]'
```

### Tasks Flapping

**Symptom**: Tasks constantly starting and stopping

**Possible causes:**
- Health checks too aggressive
- Insufficient memory
- Application crashes

**Action:**
```bash
# Check task stop reasons
aws ecs list-tasks \
  --cluster waooaw-production \
  --desired-status STOPPED \
  --query 'taskArns[0]' | \
  xargs aws ecs describe-tasks --cluster waooaw-production --tasks

# Review logs
aws logs tail /ecs/waooaw-backend-production --since 30m
```

## Best Practices

1. **Use auto-scaling** for predictable scaling
2. **Scale gradually** (avoid sudden jumps)
3. **Monitor for 30 minutes** after scaling
4. **Pre-scale for events** (don't wait for auto-scaling)
5. **Test scaling** in staging first
6. **Document capacity limits** for each component
7. **Set up alerts** for capacity issues

## Related Runbooks

- [Deployment](deployment.md)
- [Incident Response: High Load](../runbooks/incident-high-load.md)
- [Maintenance & Updates](maintenance.md)
