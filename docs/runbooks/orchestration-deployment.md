# Orchestration Runtime Deployment Runbook

**Version**: 0.7.3  
**Last Updated**: 2025-12-30  
**Owner**: Platform Team

---

## Table of Contents

1. [Overview](#overview)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Docker Compose Deployment](#docker-compose-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Health Validation](#health-validation)
6. [Rollback Procedures](#rollback-procedures)
7. [Troubleshooting](#troubleshooting)
8. [Post-Deployment](#post-deployment)

---

## Overview

The Orchestration Runtime coordinates task execution, manages worker pools, and orchestrates multi-step workflows. It integrates with Event Bus for event-driven orchestration and publishes task lifecycle events.

**Architecture:**
- **Task Queue**: Priority-based task scheduling
- **Worker Pool**: Dynamic worker scaling (2-10 workers)
- **Dependency Graph**: Topological task ordering
- **Event Integration**: Publishes lifecycle events and metrics

**Dependencies:**
- Redis 7.x (shared with Event Bus)
- Event Bus v0.6.5+ (for event-driven orchestration)
- Python 3.11+

---

## Pre-Deployment Checklist

### Infrastructure Requirements

- [ ] Redis instance running and accessible
- [ ] Network connectivity between orchestration and Redis
- [ ] Sufficient resources:
  - **CPU**: 0.5-2.0 cores per instance
  - **Memory**: 512MB-2GB per instance
  - **Storage**: 1GB for logs and state

### Configuration Validation

- [ ] Environment variables set correctly
- [ ] Redis connection string valid
- [ ] Worker pool limits appropriate for workload
- [ ] Task queue capacity configured
- [ ] Event Bus integration enabled (if using event-driven orchestration)

### Testing

- [ ] Unit tests passing: `pytest waooaw/orchestration/tests/`
- [ ] Integration tests passing: `pytest tests/integration/test_event_orchestration.py`
- [ ] Docker image built: `docker build -f infrastructure/docker/orchestration.Dockerfile -t waooaw/orchestration:0.7.3 .`
- [ ] Health check endpoint responding: `curl http://localhost:8082/health`

### Backup

- [ ] Document current task queue state
- [ ] Export in-flight workflow IDs
- [ ] Backup Redis data: `redis-cli BGSAVE`

---

## Docker Compose Deployment

### Step 1: Build Images

```bash
# Build orchestration image
docker build -f infrastructure/docker/orchestration.Dockerfile -t waooaw/orchestration:0.7.3 .

# Verify image
docker images | grep orchestration
```

### Step 2: Configure Environment

Edit `docker-compose.orchestration.yml` and adjust environment variables:

```yaml
environment:
  MAX_WORKERS: "10"              # Adjust based on CPU cores
  TASK_QUEUE_MAX_CAPACITY: "1000" # Adjust based on workload
  DEFAULT_TASK_TIMEOUT: "300"    # 5 minutes default
```

### Step 3: Deploy

```bash
# Start services
docker-compose -f docker-compose.orchestration.yml up -d

# Verify containers running
docker-compose -f docker-compose.orchestration.yml ps

# Check logs
docker-compose -f docker-compose.orchestration.yml logs -f orchestration
```

### Step 4: Validate Health

```bash
# Check orchestration health
curl http://localhost:8082/health

# Expected response:
# {"status": "healthy", "version": "0.7.3", "redis": "connected", "workers": 2}

# Check Redis connectivity
docker exec waooaw-redis redis-cli ping
# Expected: PONG
```

### Step 5: Smoke Test

```bash
# Enqueue a test task (using Python client)
python3 <<EOF
import asyncio
from waooaw.orchestration import TaskQueue, TaskPriority

async def test():
    queue = TaskQueue(name="test-queue")
    task_id = await queue.enqueue(
        name="smoke_test",
        payload={"message": "Hello World"},
        priority=TaskPriority.NORMAL,
        handler=lambda msg: print(msg)
    )
    print(f"Task enqueued: {task_id}")
    
    # Check stats
    stats = await queue.get_statistics()
    print(f"Queue stats: {stats.pending_tasks} pending, {stats.running_tasks} running")

asyncio.run(test())
EOF
```

---

## Kubernetes Deployment

### Step 1: Prerequisites

```bash
# Ensure namespace exists
kubectl create namespace waooaw --dry-run=client -o yaml | kubectl apply -f -

# Verify Redis is running
kubectl get pods -n waooaw -l app=redis

# Verify Event Bus is running (if using event integration)
kubectl get pods -n waooaw -l app=event-bus
```

### Step 2: Push Docker Image

```bash
# Tag image for registry
docker tag waooaw/orchestration:0.7.3 your-registry.com/waooaw/orchestration:0.7.3

# Push to registry
docker push your-registry.com/waooaw/orchestration:0.7.3
```

### Step 3: Update ConfigMap

Review and apply configuration:

```bash
# Review config
kubectl describe configmap orchestration-config -n waooaw

# Apply updated config if needed
kubectl apply -f infrastructure/kubernetes/orchestration-deployment.yaml
```

### Step 4: Deploy

```bash
# Apply all manifests
kubectl apply -f infrastructure/kubernetes/orchestration-deployment.yaml

# Watch rollout
kubectl rollout status deployment/orchestration -n waooaw

# Verify pods
kubectl get pods -n waooaw -l app=orchestration
```

### Step 5: Validate Deployment

```bash
# Check pod status
kubectl get pods -n waooaw -l app=orchestration
# All pods should be Running with 1/1 ready

# Check logs
kubectl logs -n waooaw -l app=orchestration --tail=50

# Port forward for local testing
kubectl port-forward -n waooaw service/orchestration-service 8082:8082

# Test health endpoint
curl http://localhost:8082/health
```

### Step 6: Verify Autoscaling

```bash
# Check HPA status
kubectl get hpa orchestration-hpa -n waooaw

# Expected output:
# NAME                  REFERENCE                TARGETS         MINPODS   MAXPODS   REPLICAS
# orchestration-hpa     Deployment/orchestration 15%/70%, 20%/80%   2         10        2
```

---

## Health Validation

### Service Health Checks

```bash
# 1. Orchestration API health
curl http://localhost:8082/health
# Expected: {"status": "healthy", "version": "0.7.3"}

# 2. Readiness check
curl http://localhost:8082/ready
# Expected: {"ready": true}

# 3. Metrics endpoint
curl http://localhost:8082/metrics
# Expected: Prometheus metrics output
```

### Integration Health

```bash
# 1. Redis connectivity
redis-cli -h localhost -p 6379 ping
# Expected: PONG

# 2. Event Bus connectivity (if enabled)
curl http://localhost:8080/health
# Expected: {"status": "healthy"}

# 3. Task queue statistics
curl http://localhost:8082/api/v1/tasks/stats
# Expected: {"pending": 0, "running": 0, "completed": X}
```

### Worker Pool Status

```python
# Check worker pool health
import asyncio
from waooaw.orchestration import WorkerPool

async def check_workers():
    pool = WorkerPool(max_workers=10)
    await pool.start()
    
    stats = pool.get_statistics()
    print(f"Active workers: {stats['active_workers']}")
    print(f"Idle workers: {stats['idle_workers']}")
    print(f"Tasks processed: {stats['tasks_processed']}")
    
    await pool.stop()

asyncio.run(check_workers())
```

---

## Rollback Procedures

### Docker Compose Rollback

```bash
# 1. Stop current deployment
docker-compose -f docker-compose.orchestration.yml down

# 2. Pull previous version
docker pull waooaw/orchestration:0.7.2

# 3. Update docker-compose.yml image tag
sed -i 's/:0.7.3/:0.7.2/g' docker-compose.orchestration.yml

# 4. Restart with previous version
docker-compose -f docker-compose.orchestration.yml up -d

# 5. Verify rollback
curl http://localhost:8082/health | grep version
```

### Kubernetes Rollback

```bash
# 1. Check rollout history
kubectl rollout history deployment/orchestration -n waooaw

# 2. Rollback to previous version
kubectl rollout undo deployment/orchestration -n waooaw

# Or rollback to specific revision
kubectl rollout undo deployment/orchestration -n waooaw --to-revision=2

# 3. Watch rollback progress
kubectl rollout status deployment/orchestration -n waooaw

# 4. Verify pods
kubectl get pods -n waooaw -l app=orchestration
```

### Emergency Shutdown

```bash
# Docker Compose
docker-compose -f docker-compose.orchestration.yml stop orchestration

# Kubernetes
kubectl scale deployment orchestration -n waooaw --replicas=0
```

---

## Troubleshooting

### Issue: Orchestration Pod CrashLoopBackOff

**Symptoms:**
```bash
kubectl get pods -n waooaw -l app=orchestration
# NAME                            READY   STATUS             RESTARTS
# orchestration-abc123-xyz        0/1     CrashLoopBackOff   5
```

**Diagnosis:**
```bash
# Check logs
kubectl logs -n waooaw orchestration-abc123-xyz --previous

# Common causes:
# - Redis connection failure
# - Invalid configuration
# - Resource limits too low
```

**Resolution:**
```bash
# 1. Verify Redis connectivity
kubectl exec -n waooaw orchestration-abc123-xyz -- redis-cli -h redis-service -p 6379 ping

# 2. Check ConfigMap
kubectl describe configmap orchestration-config -n waooaw

# 3. Increase resources if needed
kubectl edit deployment orchestration -n waooaw
# Update resources.limits.memory and resources.limits.cpu
```

### Issue: High Task Queue Depth

**Symptoms:**
```bash
# Queue depth growing, tasks not processing
curl http://localhost:8082/api/v1/tasks/stats
# {"pending": 500, "running": 50, "completed": 1000}
```

**Diagnosis:**
```bash
# Check worker pool status
curl http://localhost:8082/api/v1/workers/stats
# {"active_workers": 10, "idle_workers": 0}

# Check CPU/Memory usage
kubectl top pods -n waooaw -l app=orchestration
```

**Resolution:**
```bash
# 1. Scale up workers (Docker Compose)
docker-compose -f docker-compose.orchestration.yml exec orchestration \
  python -c "from waooaw.orchestration import WorkerPool; pool.scale_up(5)"

# 2. Scale up replicas (Kubernetes)
kubectl scale deployment orchestration -n waooaw --replicas=5

# 3. Or trigger HPA manually
kubectl autoscale deployment orchestration -n waooaw --cpu-percent=50 --min=2 --max=10
```

### Issue: Redis Connection Timeout

**Symptoms:**
```
ERROR: Failed to connect to Redis at redis://redis:6379
```

**Diagnosis:**
```bash
# Test Redis from orchestration pod
kubectl exec -n waooaw orchestration-abc123-xyz -- redis-cli -h redis-service -p 6379 ping

# Check Redis pod status
kubectl get pods -n waooaw -l app=redis
```

**Resolution:**
```bash
# 1. Verify Redis service exists
kubectl get service redis-service -n waooaw

# 2. Check network policies
kubectl get networkpolicies -n waooaw

# 3. Restart Redis if needed
kubectl rollout restart statefulset/redis -n waooaw
```

### Issue: Memory Leak / OOM

**Symptoms:**
```bash
# Pod restarting with OOMKilled
kubectl describe pod orchestration-abc123-xyz -n waooaw
# Last State: Terminated, Reason: OOMKilled
```

**Diagnosis:**
```bash
# Check memory usage
kubectl top pod -n waooaw orchestration-abc123-xyz

# Check memory limits
kubectl get pod orchestration-abc123-xyz -n waooaw -o yaml | grep -A 5 resources
```

**Resolution:**
```bash
# 1. Increase memory limits
kubectl edit deployment orchestration -n waooaw
# Update resources.limits.memory to 4Gi

# 2. Reduce task queue capacity
kubectl edit configmap orchestration-config -n waooaw
# Set TASK_QUEUE_MAX_CAPACITY: "500"

# 3. Restart pods
kubectl rollout restart deployment orchestration -n waooaw
```

---

## Post-Deployment

### Monitoring Setup

```bash
# 1. Verify metrics are being scraped
curl http://localhost:8082/metrics | grep orchestration_tasks_total

# 2. Set up Grafana dashboard (import dashboard ID: TBD)

# 3. Configure alerts:
#    - High queue depth (>100 pending tasks)
#    - High failure rate (>5% failed tasks)
#    - Worker pool saturation (all workers busy for >5 minutes)
```

### Performance Validation

```bash
# Run load test
python tests/performance/orchestration_load_test.py --tasks=1000 --workers=10

# Expected results:
# - Task throughput: >50 tasks/minute
# - P95 latency: <500ms
# - Worker utilization: 70-80%
```

### Documentation

- [ ] Update runbook with deployment details (date, version, operator)
- [ ] Document any configuration changes
- [ ] Update monitoring dashboards
- [ ] Notify team of successful deployment

### Cleanup

```bash
# Remove old images
docker image prune -a --filter "until=720h"

# Clean up old ReplicaSets
kubectl delete replicaset -n waooaw $(kubectl get rs -n waooaw -o name | grep orchestration | tail -n +4)
```

---

## Quick Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection string | `redis://redis:6379` |
| `MAX_WORKERS` | Maximum worker pool size | `10` |
| `MIN_WORKERS` | Minimum worker pool size | `2` |
| `TASK_QUEUE_MAX_CAPACITY` | Max tasks in queue | `1000` |
| `DEFAULT_TASK_TIMEOUT` | Task timeout (seconds) | `300` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `API_PORT` | API server port | `8082` |

### Useful Commands

```bash
# Docker Compose
docker-compose -f docker-compose.orchestration.yml logs -f orchestration
docker-compose -f docker-compose.orchestration.yml restart orchestration
docker-compose -f docker-compose.orchestration.yml exec orchestration python -m waooaw.orchestration.cli

# Kubernetes
kubectl logs -n waooaw -l app=orchestration -f
kubectl exec -n waooaw orchestration-abc123-xyz -- python -m waooaw.orchestration.cli status
kubectl get events -n waooaw --sort-by='.lastTimestamp' | grep orchestration
```

### Support Contacts

- **Platform Team**: platform@waooaw.com
- **On-Call**: +1-XXX-XXX-XXXX
- **Slack**: #platform-alerts
- **Runbook**: https://docs.waooaw.com/runbooks/orchestration

---

**Document Version**: 1.0  
**Next Review**: 2026-01-30
