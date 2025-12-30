# Message Bus & Orchestration Troubleshooting Runbook

**Version**: v0.8.0  
**Last Updated**: 2024-01-15  
**Owner**: Platform Team  
**Related**: [Orchestration Deployment](./orchestration-deployment.md), [Event Bus Runbook](./event-bus-runbook.md)

---

## Overview

This runbook covers troubleshooting the integration between the Event Bus and Orchestration Runtime. For component-specific issues, see individual runbooks.

### Quick Links
- [High Task Queue Depth](#high-task-queue-depth)
- [High Worker Utilization](#high-worker-utilization)
- [High Event-to-Task Latency](#high-event-to-task-latency)
- [High Task Failure Rate](#high-task-failure-rate)
- [DLQ Growth](#dlq-growth-anomaly)
- [Worker Pool Exhaustion](#worker-pool-exhaustion)
- [Event Backpressure](#event-backpressure)
- [Task Dependency Deadlock](#task-dependency-deadlock)
- [Redis Connection Loss](#redis-connection-loss)

---

## Alert Response Procedures

### High Task Queue Depth

**Alert**: `HighTaskQueueDepth` (>800 tasks pending)  
**Severity**: Warning  
**SLA**: Respond within 15 minutes

#### Symptoms
- Task queue metrics show >80% capacity utilization
- Orchestration dashboard shows high pending count
- Application response times increasing

#### Diagnosis

1. **Check current queue state**:
```bash
# Get current metrics
curl -s http://orchestration-service:8082/metrics | grep orchestration_task_queue

# Expected output:
# orchestration_task_queue_pending 850
# orchestration_task_queue_running 45
# orchestration_task_queue_completed 12340
```

2. **Check worker pool utilization**:
```bash
curl -s http://orchestration-service:8082/metrics | grep orchestration_worker_pool

# Look for:
# orchestration_worker_pool_active vs orchestration_worker_pool_max
```

3. **Identify slow tasks**:
```bash
# Check task duration distribution
curl -s http://orchestration-service:8082/metrics | grep task_duration_seconds

# View recent task logs
kubectl logs -l app=orchestration --tail=50 | grep "task_duration"
```

#### Resolution

**Option 1: Scale workers horizontally** (if HPA not triggered):
```bash
# Manual scale-up
kubectl scale deployment orchestration --replicas=5

# Verify scaling
kubectl get deployment orchestration
```

**Option 2: Increase worker pool size** (if CPU/memory available):
```bash
# Edit ConfigMap
kubectl edit configmap orchestration-config

# Change:
# ORCHESTRATION_WORKER_POOL_SIZE: "15"  # from 10

# Restart pods to apply
kubectl rollout restart deployment orchestration
```

**Option 3: Rate limit event ingestion** (if queue not draining):
```bash
# Temporarily reduce event publisher rate
kubectl scale deployment event-publishers --replicas=1

# Monitor queue drain rate
watch "kubectl exec -it orchestration-0 -- curl -s localhost:8082/metrics | grep queue_pending"
```

#### Validation
- Queue depth drops below 800 within 10 minutes
- Worker utilization stabilizes between 60-80%
- Alert resolves automatically

---

### Critical Task Queue Depth

**Alert**: `CriticalTaskQueueDepth` (>950 tasks)  
**Severity**: Critical  
**SLA**: Respond immediately

#### Symptoms
- Queue near capacity (>95%)
- Tasks may be rejected
- Application timeouts increasing

#### Immediate Actions

1. **Emergency scale-up**:
```bash
# Scale to maximum capacity immediately
kubectl scale deployment orchestration --replicas=10

# Increase worker pool to maximum
kubectl set env deployment/orchestration ORCHESTRATION_WORKER_POOL_SIZE=20
```

2. **Pause non-critical event sources**:
```bash
# Stop analytics events
kubectl scale deployment analytics-publisher --replicas=0

# Stop background job events
kubectl scale deployment background-job-publisher --replicas=0
```

3. **Monitor queue recovery**:
```bash
# Watch queue drain in real-time
watch -n 5 "curl -s http://orchestration-service:8082/metrics | grep orchestration_task_queue_pending"
```

#### Follow-up
- Investigate root cause (slow tasks, insufficient capacity)
- Update capacity planning
- Gradually restore event sources after queue < 500

---

### High Worker Utilization

**Alert**: `HighWorkerUtilization` (>90%)  
**Severity**: Warning  
**SLA**: Respond within 15 minutes

#### Symptoms
- Worker pool at or near maximum capacity
- Task throughput plateaued
- Queue depth may be increasing

#### Diagnosis

1. **Check worker distribution**:
```bash
# Get worker metrics per pod
for pod in $(kubectl get pods -l app=orchestration -o name); do
  echo "=== $pod ==="
  kubectl exec $pod -- curl -s localhost:8082/metrics | grep worker_pool
done
```

2. **Identify long-running tasks**:
```bash
# Check task duration P95
kubectl exec -it orchestration-0 -- curl -s localhost:8082/metrics | grep "task_duration_seconds_bucket"

# View tasks in "running" state >1 minute
kubectl logs -l app=orchestration --tail=100 | grep "task_running" | grep "duration_ms"
```

3. **Check for CPU/memory bottlenecks**:
```bash
# Get resource utilization
kubectl top pods -l app=orchestration

# Check if pods are being throttled
kubectl describe pods -l app=orchestration | grep -A 5 "Limits:"
```

#### Resolution

**Option 1: Horizontal scaling** (preferred):
```bash
# Scale replicas
kubectl scale deployment orchestration --replicas=5

# Verify HPA configuration
kubectl get hpa orchestration
```

**Option 2: Increase worker pool per pod**:
```bash
# Edit ConfigMap
kubectl edit configmap orchestration-config

# Increase ORCHESTRATION_WORKER_POOL_SIZE
# WARNING: Ensure CPU/memory resources are sufficient

# Restart to apply
kubectl rollout restart deployment orchestration
```

**Option 3: Optimize slow tasks**:
```bash
# Identify top 10 slowest task types
kubectl logs -l app=orchestration --tail=1000 | grep "task_completed" | \
  jq -r '[.task_name, .duration_ms] | @csv' | \
  sort -t',' -k2 -rn | head -10

# Review task handler implementations
# Consider async I/O, caching, or batching optimizations
```

#### Validation
- Worker utilization drops below 80%
- Task throughput increases or stabilizes
- No new tasks queued

---

### High Event-to-Task Latency

**Alert**: `HighEventToTaskLatency` (P95 >500ms)  
**Severity**: Warning  
**SLA**: Respond within 30 minutes

#### Symptoms
- Increased time between event receipt and task creation
- Dashboard shows elevated latency metrics
- End-to-end workflow duration increasing

#### Diagnosis

1. **Check latency distribution**:
```bash
# Get latency percentiles
curl -s http://orchestration-service:8082/metrics | grep "event_to_task_duration_seconds"

# Expected output shows buckets:
# orchestration_event_to_task_duration_seconds_bucket{le="0.1"} 5000
# orchestration_event_to_task_duration_seconds_bucket{le="0.5"} 9500
# orchestration_event_to_task_duration_seconds_bucket{le="1.0"} 9950
```

2. **Check event adapter health**:
```bash
# View event adapter logs
kubectl logs -l app=orchestration --tail=50 | grep "EventToTaskMapper"

# Look for error patterns
kubectl logs -l app=orchestration --since=10m | grep -i "error\|exception" | grep -i "event"
```

3. **Check Redis latency** (event bus backend):
```bash
# Test Redis connection
kubectl exec -it redis-0 -- redis-cli --latency

# Check event bus metrics
curl -s http://event-bus-service:8080/metrics | grep "event_bus_publish_latency"
```

4. **Check task queue contention**:
```bash
# Check if queue operations are slow
kubectl logs -l app=orchestration --tail=100 | grep "enqueue_duration"
```

#### Resolution

**Option 1: Scale event handlers**:
```bash
# Increase orchestration replicas for event processing
kubectl scale deployment orchestration --replicas=5

# Verify event distribution
kubectl logs -l app=orchestration --tail=20 | grep "event_received"
```

**Option 2: Optimize event-to-task mapping**:
```python
# Review EventToTaskMapper in waooaw/orchestration/event_adapter.py
# Consider:
# - Caching frequent mappings
# - Pre-validating event schemas
# - Reducing unnecessary data transformations
```

**Option 3: Increase Redis resources** (if bottleneck):
```bash
# Check Redis CPU/memory
kubectl top pods -l app=redis

# Scale Redis resources
kubectl edit deployment redis
# Update resources.requests and resources.limits
```

#### Validation
- P95 latency drops below 500ms
- Event throughput remains stable
- No increase in error rates

---

### Critical Event-to-Task Latency

**Alert**: `CriticalEventToTaskLatency` (P95 >1s)  
**Severity**: Critical  
**SLA**: Respond immediately

#### Immediate Actions

1. **Check for service degradation**:
```bash
# Verify all services healthy
kubectl get pods -l 'app in (orchestration, event-bus, redis)'

# Check for OOM or restarts
kubectl describe pods -l app=orchestration | grep -A 3 "Last State"
```

2. **Emergency diagnostics**:
```bash
# Capture current state
kubectl get pods -o wide > /tmp/pod-state.txt
kubectl top pods > /tmp/resource-usage.txt
curl http://orchestration-service:8082/metrics > /tmp/metrics.txt

# Check event bus backlog
curl http://event-bus-service:8080/metrics | grep "pending\|backlog"
```

3. **Mitigate immediately**:
```bash
# If Redis is bottleneck, add read replicas
kubectl scale statefulset redis-replica --replicas=2

# If orchestration is bottleneck, emergency scale
kubectl scale deployment orchestration --replicas=10
```

#### Follow-up
- Analyze captured diagnostics
- Identify root cause (network, Redis, application logic)
- Implement permanent fix
- Update capacity planning

---

### High Task Failure Rate

**Alert**: `HighTaskFailureRate` (>5%)  
**Severity**: Warning  
**SLA**: Respond within 15 minutes

#### Symptoms
- Dashboard shows elevated failure rate
- Increased error logs
- Certain task types consistently failing

#### Diagnosis

1. **Identify failing task types**:
```bash
# Get failure breakdown by task name
kubectl logs -l app=orchestration --since=30m | grep "task_failed" | \
  jq -r '.task_name' | sort | uniq -c | sort -rn

# Example output:
# 45 email_sender
# 23 webhook_notifier
# 12 data_transformer
```

2. **Check failure reasons**:
```bash
# Get recent error messages
kubectl logs -l app=orchestration --since=30m | grep "task_failed" | \
  jq -r '[.task_name, .error] | @csv' | head -20

# Common patterns:
# - Connection timeouts
# - Validation errors
# - Dependency failures
```

3. **Check retry behavior**:
```bash
# Verify retry configuration
kubectl get configmap orchestration-config -o yaml | grep -i retry

# Check if tasks are being retried
kubectl logs -l app=orchestration --since=10m | grep "task_retry"
```

4. **Check downstream dependencies**:
```bash
# Test external service connectivity
kubectl exec -it orchestration-0 -- curl -v https://external-api.example.com/health

# Check database connections
kubectl exec -it orchestration-0 -- psql -h postgres -U app -c "SELECT 1"
```

#### Resolution

**Option 1: Fix upstream issue** (if dependency failure):
```bash
# Example: Restart failing external service
kubectl rollout restart deployment email-service

# Wait for health
kubectl wait --for=condition=ready pod -l app=email-service --timeout=60s
```

**Option 2: Update retry configuration**:
```bash
# Edit ConfigMap
kubectl edit configmap orchestration-config

# Add or update:
# ORCHESTRATION_MAX_RETRIES: "5"
# ORCHESTRATION_RETRY_BACKOFF: "exponential"
# ORCHESTRATION_RETRY_MAX_DELAY: "300"

# Restart to apply
kubectl rollout restart deployment orchestration
```

**Option 3: Deploy hotfix** (if application bug):
```bash
# Build and deploy fixed version
docker build -t orchestration:v0.7.4-hotfix .
docker push orchestration:v0.7.4-hotfix

# Update deployment
kubectl set image deployment/orchestration orchestration=orchestration:v0.7.4-hotfix

# Monitor rollout
kubectl rollout status deployment orchestration
```

#### Validation
- Failure rate drops below 5%
- Specific task types recover
- No new error patterns emerge

---

### DLQ Growth Anomaly

**Alert**: `DLQGrowthAnomaly` (DLQ growing >0.5 events/sec)  
**Severity**: Warning  
**SLA**: Respond within 15 minutes

#### Symptoms
- Dead Letter Queue accumulating events
- Events repeatedly failing processing
- Specific event types may be problematic

#### Diagnosis

1. **Check DLQ size and growth**:
```bash
# Get current DLQ metrics
curl -s http://event-bus-service:8080/metrics | grep dlq

# Example output:
# event_bus_dlq_size 245
# event_bus_dlq_growth_rate 0.8
```

2. **Sample DLQ events**:
```bash
# Get DLQ contents (first 10 events)
curl -s http://event-bus-service:8080/admin/dlq | jq '.[0:10]'

# Check for patterns
curl -s http://event-bus-service:8080/admin/dlq | jq -r '.[].event_type' | \
  sort | uniq -c | sort -rn
```

3. **Check event handler errors**:
```bash
# Get errors from orchestration event handler
kubectl logs -l app=orchestration --since=30m | grep -i "event.*error\|event.*exception"

# Look for:
# - Validation failures
# - Serialization errors
# - Handler exceptions
```

#### Resolution

**Option 1: Fix event schema issues**:
```bash
# Identify malformed events
curl -s http://event-bus-service:8080/admin/dlq | jq '.[] | select(.error | contains("validation"))'

# Deploy schema fix
# Update event publisher to match expected schema
kubectl rollout restart deployment event-publisher

# Replay fixed events
curl -X POST http://event-bus-service:8080/admin/dlq/replay \
  -H "Content-Type: application/json" \
  -d '{"event_types": ["user.created"]}'
```

**Option 2: Update event handler**:
```bash
# If handler is rejecting valid events, deploy fix
kubectl set image deployment/orchestration orchestration=orchestration:v0.7.4-dlq-fix

# Monitor DLQ drain
watch "curl -s http://event-bus-service:8080/metrics | grep dlq_size"
```

**Option 3: Manual intervention** (if events are invalid):
```bash
# Drain DLQ without replay (discard invalid events)
curl -X DELETE http://event-bus-service:8080/admin/dlq?purge=true

# WARNING: Only use if events are confirmed invalid
```

#### Validation
- DLQ size stops growing
- DLQ drains to <50 events
- No new events added to DLQ

---

### Worker Pool Exhaustion

**Alert**: `WorkerPoolExhaustion` (all workers busy, queue >50)  
**Severity**: Warning  
**SLA**: Respond within 10 minutes

#### Symptoms
- All workers at maximum capacity
- Task queue growing
- No available workers for new tasks

#### Diagnosis

1. **Check worker state**:
```bash
# Get worker pool metrics
curl -s http://orchestration-service:8082/metrics | grep worker_pool

# orchestration_worker_pool_active 10
# orchestration_worker_pool_max 10
# orchestration_task_queue_pending 87
```

2. **Identify blocking tasks**:
```bash
# Check for long-running tasks
kubectl logs -l app=orchestration --tail=100 | grep "task_running" | \
  awk '{print $NF}' | sort -n | tail -10

# Look for tasks running >60 seconds
```

3. **Check for deadlock**:
```bash
# Check if tasks are waiting on each other
kubectl logs -l app=orchestration --tail=200 | grep "waiting_for_dependency"

# Review dependency chains
curl -s http://orchestration-service:8082/admin/dependencies | jq '.blocked_tasks'
```

#### Resolution

**Option 1: Emergency scale-up**:
```bash
# Immediate horizontal scaling
kubectl scale deployment orchestration --replicas=5

# Increase per-pod worker pool
kubectl set env deployment/orchestration ORCHESTRATION_WORKER_POOL_SIZE=15
```

**Option 2: Kill stuck tasks** (if deadlock suspected):
```bash
# Get tasks running >5 minutes
curl -s http://orchestration-service:8082/admin/tasks?status=running&duration_gt=300

# Cancel specific stuck task
curl -X DELETE http://orchestration-service:8082/admin/tasks/{task_id}

# Monitor worker availability
watch "curl -s http://orchestration-service:8082/metrics | grep worker_pool_active"
```

**Option 3: Restart workers** (last resort):
```bash
# Rolling restart to clear stuck workers
kubectl rollout restart deployment orchestration

# Monitor recovery
kubectl rollout status deployment orchestration
```

#### Validation
- Worker utilization drops below 90%
- Queue starts draining
- Task throughput resumes

---

### Event Backpressure

**Alert**: `EventBackpressure` (events published >2x task completion rate)  
**Severity**: Warning  
**SLA**: Respond within 20 minutes

#### Symptoms
- Events arriving faster than processing capacity
- Task queue growing continuously
- Orchestration falling behind event stream

#### Diagnosis

1. **Check rate differential**:
```bash
# Get event publish rate (events/sec)
curl -s http://event-bus-service:8080/metrics | grep "events_published_total" | \
  awk '{print $2}' | head -1

# Get task completion rate (tasks/sec)
curl -s http://orchestration-service:8082/metrics | grep "tasks_completed_total" | \
  awk '{print $2}' | head -1

# Calculate ratio
```

2. **Identify event sources**:
```bash
# Get event breakdown by type
curl -s http://event-bus-service:8080/metrics | grep "events_published_total{event_type=" | \
  sort -t'=' -k2 -rn | head -10
```

3. **Check task processing bottlenecks**:
```bash
# Check task duration by type
kubectl logs -l app=orchestration --since=10m | grep "task_completed" | \
  jq -r '[.task_name, .duration_ms] | @csv' | \
  awk -F',' '{sum[$1]+=$2; count[$1]++} END {for(t in sum) print t","sum[t]/count[t]}' | \
  sort -t',' -k2 -rn | head -10
```

#### Resolution

**Option 1: Rate limit event publishers**:
```bash
# Reduce publisher replicas
kubectl scale deployment event-publisher --replicas=2  # from 5

# Add rate limiting to event publishers
kubectl set env deployment/event-publisher EVENT_RATE_LIMIT=50  # events/sec
```

**Option 2: Scale orchestration capacity**:
```bash
# Aggressive horizontal scaling
kubectl scale deployment orchestration --replicas=10

# Increase worker pools
kubectl set env deployment/orchestration ORCHESTRATION_WORKER_POOL_SIZE=20
```

**Option 3: Implement buffering** (if temporary spike):
```bash
# Configure event bus buffering
kubectl set env deployment/event-bus EVENT_BUFFER_SIZE=10000

# Monitor buffer utilization
watch "curl -s http://event-bus-service:8080/metrics | grep buffer"
```

**Option 4: Defer non-critical events**:
```bash
# Pause analytics event publishers
kubectl scale deployment analytics-publisher --replicas=0

# Pause audit log publishers
kubectl scale deployment audit-publisher --replicas=0

# Resume after queue drains below 200
```

#### Validation
- Event and task rates converge (ratio <1.5)
- Task queue stabilizes or shrinks
- No tasks timing out

---

### Task Dependency Deadlock

**Alert**: `TaskDependencyDeadlock` (tasks pending, no workers active, no completions)  
**Severity**: Warning  
**SLA**: Respond within 15 minutes

#### Symptoms
- Tasks in queue but no processing
- All workers idle
- No tasks completing
- Dependency chains blocked

#### Diagnosis

1. **Verify deadlock condition**:
```bash
# Check metrics match alert condition
curl -s http://orchestration-service:8082/metrics | grep -E "queue_pending|worker_pool_active|tasks_completed"

# Expected:
# orchestration_task_queue_pending > 0
# orchestration_worker_pool_active == 0
# rate(orchestration_tasks_completed_total) == 0
```

2. **Check dependency graph**:
```bash
# Get dependency relationships
curl -s http://orchestration-service:8082/admin/dependencies | jq '.dependency_graph'

# Look for circular dependencies
curl -s http://orchestration-service:8082/admin/dependencies?check_circular=true
```

3. **Identify blocked tasks**:
```bash
# Get tasks waiting on dependencies
kubectl logs -l app=orchestration --tail=200 | grep "waiting_on_dependency"

# Example output:
# task_id=123 waiting_on_dependency=456
# task_id=456 waiting_on_dependency=789
# task_id=789 waiting_on_dependency=123  # CIRCULAR!
```

#### Resolution

**Option 1: Break circular dependency**:
```bash
# Identify circular chain
curl -s http://orchestration-service:8082/admin/dependencies?check_circular=true | \
  jq '.circular_chains[0]'

# Cancel one task to break cycle
curl -X DELETE http://orchestration-service:8082/admin/tasks/{task_id}

# Monitor queue recovery
watch "curl -s http://orchestration-service:8082/metrics | grep worker_pool_active"
```

**Option 2: Clear dependency metadata** (if stale):
```bash
# Reset dependencies for blocked tasks
curl -X POST http://orchestration-service:8082/admin/dependencies/reset \
  -H "Content-Type: application/json" \
  -d '{"task_ids": ["123", "456", "789"]}'
```

**Option 3: Restart orchestration** (if graph corrupted):
```bash
# Full restart to rebuild dependency state
kubectl rollout restart deployment orchestration

# Wait for restart
kubectl rollout status deployment orchestration

# Verify queue processing resumes
kubectl logs -l app=orchestration --tail=50 | grep "task_completed"
```

#### Prevention
- Review workflow designs for circular dependencies
- Implement dependency validation at task submission
- Add timeout mechanisms for dependency waits
- Monitor dependency chain depth

#### Validation
- Workers become active
- Tasks start completing
- Queue drains normally

---

### Redis Connection Loss

**Alert**: `RedisConnectionLoss` (Redis unreachable)  
**Severity**: Critical  
**SLA**: Respond immediately

#### Symptoms
- Both Event Bus and Orchestration affected
- Connection errors in logs
- All event-driven workflows stopped

#### Immediate Actions

1. **Check Redis status**:
```bash
# Verify Redis pods
kubectl get pods -l app=redis

# Check Redis logs
kubectl logs -l app=redis --tail=50

# Test connectivity
kubectl exec -it orchestration-0 -- redis-cli -h redis ping
```

2. **Common causes**:

**Case 1: Redis pod crashed**:
```bash
# Check pod events
kubectl describe pod redis-0

# If OOM, increase memory limits
kubectl edit statefulset redis
# Update resources.limits.memory: "2Gi"

# If disk full, clean up AOF/RDB
kubectl exec -it redis-0 -- redis-cli BGREWRITEAOF
```

**Case 2: Network issue**:
```bash
# Test network connectivity
kubectl exec -it orchestration-0 -- nc -zv redis 6379

# Check Service
kubectl get svc redis
kubectl describe svc redis

# Check NetworkPolicies
kubectl get networkpolicy
```

**Case 3: Redis overloaded**:
```bash
# Check Redis stats
kubectl exec -it redis-0 -- redis-cli INFO stats

# Check slow queries
kubectl exec -it redis-0 -- redis-cli SLOWLOG GET 10

# Restart Redis if needed
kubectl delete pod redis-0  # StatefulSet will recreate
```

#### Resolution

1. **Restore Redis service**:
```bash
# If Redis is down, restore from backup
kubectl exec -it redis-0 -- redis-cli SHUTDOWN SAVE

# Apply latest backup
kubectl cp /backups/redis-dump.rdb redis-0:/data/dump.rdb

# Start Redis
kubectl delete pod redis-0  # Auto-restart
```

2. **Reconnect services**:
```bash
# Restart dependent services
kubectl rollout restart deployment orchestration
kubectl rollout restart deployment event-bus

# Verify connections
kubectl logs -l app=orchestration --tail=20 | grep "redis.*connected"
kubectl logs -l app=event-bus --tail=20 | grep "redis.*connected"
```

3. **Verify data integrity**:
```bash
# Check Redis data
kubectl exec -it redis-0 -- redis-cli DBSIZE

# Check Event Bus queues
kubectl exec -it redis-0 -- redis-cli LLEN event:queue

# Check Orchestration task state
kubectl exec -it redis-0 -- redis-cli HLEN orchestration:tasks
```

#### Post-Incident
- Review Redis resource allocation
- Implement Redis HA (master-replica setup)
- Configure connection pooling
- Set up Redis Sentinel for automatic failover

#### Validation
- Redis responds to PING
- Event Bus reconnects successfully
- Orchestration reconnects successfully
- Event processing resumes

---

## Common Diagnostic Commands

### Quick Health Check
```bash
#!/bin/bash
# check-integration-health.sh

echo "=== Service Status ==="
kubectl get pods -l 'app in (orchestration, event-bus, redis)' -o wide

echo -e "\n=== Redis Health ==="
kubectl exec -it redis-0 -- redis-cli PING

echo -e "\n=== Event Bus Metrics ==="
curl -s http://event-bus-service:8080/metrics | grep -E "events_(published|consumed)_total|dlq_size"

echo -e "\n=== Orchestration Metrics ==="
curl -s http://orchestration-service:8082/metrics | grep -E "task_queue_(pending|running|completed)|worker_pool_(active|max)"

echo -e "\n=== Integration Latency ==="
curl -s http://orchestration-service:8082/metrics | grep "event_to_task_duration_seconds"

echo -e "\n=== Recent Errors ==="
kubectl logs -l app=orchestration --since=5m | grep -i "error\|exception" | tail -10
```

### Performance Snapshot
```bash
#!/bin/bash
# capture-performance-snapshot.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="/tmp/perf-snapshot-${TIMESTAMP}"
mkdir -p ${OUTPUT_DIR}

echo "Capturing performance snapshot to ${OUTPUT_DIR}..."

# Metrics
curl -s http://orchestration-service:8082/metrics > ${OUTPUT_DIR}/orchestration-metrics.txt
curl -s http://event-bus-service:8080/metrics > ${OUTPUT_DIR}/eventbus-metrics.txt

# Logs (last 5 minutes)
kubectl logs -l app=orchestration --since=5m > ${OUTPUT_DIR}/orchestration-logs.txt
kubectl logs -l app=event-bus --since=5m > ${OUTPUT_DIR}/eventbus-logs.txt

# Resource usage
kubectl top pods > ${OUTPUT_DIR}/pod-resources.txt
kubectl top nodes > ${OUTPUT_DIR}/node-resources.txt

# Current state
kubectl get pods -o yaml > ${OUTPUT_DIR}/pods-state.yaml
kubectl get hpa -o yaml > ${OUTPUT_DIR}/hpa-state.yaml

echo "Snapshot complete: ${OUTPUT_DIR}"
tar -czf ${OUTPUT_DIR}.tar.gz ${OUTPUT_DIR}
echo "Archive: ${OUTPUT_DIR}.tar.gz"
```

### Stress Test Validation
```bash
#!/bin/bash
# stress-test-integration.sh

echo "=== Starting stress test ==="

# Publish 1000 events
for i in {1..1000}; do
  curl -X POST http://event-bus-service:8080/publish \
    -H "Content-Type: application/json" \
    -d "{\"event_type\": \"test.stress\", \"payload\": {\"id\": $i}}" &
  
  if [ $((i % 100)) -eq 0 ]; then
    echo "Published $i events..."
    wait
  fi
done

wait

echo -e "\n=== Monitoring processing ==="
for i in {1..30}; do
  PENDING=$(curl -s http://orchestration-service:8082/metrics | grep "task_queue_pending" | awk '{print $2}')
  COMPLETED=$(curl -s http://orchestration-service:8082/metrics | grep "tasks_completed_total" | awk '{print $2}')
  echo "Iteration $i: Pending=$PENDING, Completed=$COMPLETED"
  sleep 5
done

echo -e "\n=== Final metrics ==="
curl -s http://orchestration-service:8082/metrics | grep -E "task_queue|event_to_task_duration"
```

---

## Escalation Paths

### Level 1: On-Call Engineer
- **Scope**: Respond to alerts, follow runbook procedures
- **Authority**: Scale services, restart pods, apply configuration changes
- **Escalate if**: Issue persists >30 minutes, data loss suspected, security incident

### Level 2: Platform Team Lead
- **Scope**: Complex debugging, code hotfixes, architecture decisions
- **Authority**: Deploy code changes, modify infrastructure, coordinate with other teams
- **Escalate if**: Issue requires multi-team coordination, affects multiple services

### Level 3: Engineering Management
- **Scope**: Incident command, customer communication, post-mortem coordination
- **Authority**: Emergency decisions, resource allocation, external communication

### Contacts
- On-Call: PagerDuty rotation
- Platform Team: #platform-team Slack channel
- Engineering Manager: [manager@waooaw.com](mailto:manager@waooaw.com)
- Incident Commander: #incidents Slack channel

---

## Post-Incident Checklist

After resolving any incident:

- [ ] Verify alert has cleared
- [ ] Confirm metrics returned to normal
- [ ] Document root cause
- [ ] Create GitHub issue for permanent fix
- [ ] Update runbook if new scenario
- [ ] Schedule post-mortem (if severity: critical)
- [ ] Update on-call playbook
- [ ] Notify stakeholders of resolution

---

## Related Documentation

- [Orchestration Deployment Runbook](./orchestration-deployment.md)
- [Event Bus Runbook](./event-bus-runbook.md)
- [Orchestration README](../../waooaw/orchestration/README.md)
- [Grafana Dashboard](../../infrastructure/monitoring/grafana-dashboard-orchestration.json)
- [Prometheus Alerts](../../infrastructure/monitoring/prometheus-alerts-orchestration.yml)

---

**Questions or issues with this runbook?** Contact Platform Team or create an issue in [WAOOAW/platform-docs](https://github.com/WAOOAW/platform-docs).
