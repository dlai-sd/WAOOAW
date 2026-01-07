# WowEvent Event Bus Deployment Runbook

## Overview

This runbook covers deployment, monitoring, and troubleshooting of the WowEvent Event Bus system.

**Component**: WowEvent Event Bus  
**Version**: 0.6.5-dev  
**Owner**: Platform Team  
**Last Updated**: December 29, 2025

---

## Architecture

```
┌─────────────────┐
│   Agents        │
│  (Publishers &  │
│  Subscribers)   │
└────────┬────────┘
         │
    ┌────▼─────┐
    │ Event    │
    │ Bus      │◄──── Health Checks (/health)
    │ Service  │◄──── Metrics (/metrics)
    └────┬─────┘
         │
    ┌────▼─────┐
    │  Redis   │
    │  Pub/Sub │
    └──────────┘
```

**Components**:
- **Event Bus Service**: aiohttp server with EventBus, EventMetrics, EventStore
- **Redis**: Message broker for pub/sub
- **Agents**: Publishers and subscribers

---

## Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Docker registry access
- Redis 7.x

---

## Deployment

### 1. Build Docker Image

```bash
cd /workspaces/WAOOAW

# Build image
docker build -f infrastructure/docker/event-bus.Dockerfile -t waooaw/event-bus:0.6.5 .

# Tag for registry
docker tag waooaw/event-bus:0.6.5 your-registry/waooaw/event-bus:0.6.5

# Push to registry
docker push your-registry/waooaw/event-bus:0.6.5
```

### 2. Create Namespace

```bash
kubectl create namespace waooaw
```

### 3. Deploy Redis

```bash
kubectl apply -f infrastructure/kubernetes/redis-deployment.yaml

# Wait for Redis to be ready
kubectl wait --for=condition=ready pod -l app=redis -n waooaw --timeout=120s
```

### 4. Deploy Event Bus

```bash
kubectl apply -f infrastructure/kubernetes/event-bus-deployment.yaml

# Wait for Event Bus to be ready
kubectl wait --for=condition=ready pod -l app=event-bus -n waooaw --timeout=120s
```

### 5. Verify Deployment

```bash
# Check pod status
kubectl get pods -n waooaw -l app=event-bus

# Check logs
kubectl logs -n waooaw -l app=event-bus --tail=50

# Test health endpoint
kubectl port-forward -n waooaw svc/event-bus-service 8080:8080
curl http://localhost:8080/health
```

Expected response:
```json
{
  "status": "healthy",
  "redis": "connected",
  "event_bus": "running"
}
```

---

## Monitoring

### Health Checks

**Liveness Probe**: `/health`  
**Readiness Probe**: `/ready`

```bash
# Check health
kubectl exec -n waooaw -it deployment/event-bus -- \
  curl http://localhost:8080/health

# Check readiness
kubectl exec -n waooaw -it deployment/event-bus -- \
  curl http://localhost:8080/ready
```

### Metrics

**Endpoint**: `/metrics`

```bash
# Get metrics
kubectl port-forward -n waooaw svc/event-bus-service 8080:8080
curl http://localhost:8080/metrics
```

**Key Metrics**:
- `totals.publishes`: Total events published
- `totals.deliveries`: Total successful deliveries
- `totals.errors`: Total errors
- `throughput.publishes.per_second`: Publishing rate
- `latency.p95`: 95th percentile latency
- `subscribers.health`: Subscriber health summary

### Logs

```bash
# Tail logs
kubectl logs -n waooaw -l app=event-bus -f

# Search for errors
kubectl logs -n waooaw -l app=event-bus | grep ERROR

# Check specific pod
kubectl logs -n waooaw event-bus-xxxxx-yyyyy
```

---

## Scaling

### Manual Scaling

```bash
# Scale to 5 replicas
kubectl scale deployment event-bus -n waooaw --replicas=5

# Check scaling status
kubectl get hpa -n waooaw event-bus-hpa
```

### Auto-Scaling

**HPA Configuration**:
- Min replicas: 2
- Max replicas: 10
- CPU target: 70%
- Memory target: 80%

```bash
# View HPA status
kubectl get hpa -n waooaw event-bus-hpa

# Describe HPA
kubectl describe hpa -n waooaw event-bus-hpa
```

---

## Troubleshooting

### Pod Not Starting

**Symptoms**: Pods stuck in `Pending`, `CrashLoopBackOff`, or `Error`

**Diagnosis**:
```bash
# Check pod status
kubectl describe pod -n waooaw -l app=event-bus

# Check events
kubectl get events -n waooaw --sort-by='.lastTimestamp'

# Check logs
kubectl logs -n waooaw -l app=event-bus --previous
```

**Common Causes**:
1. **Redis not available**: Ensure Redis is running
2. **Image pull error**: Check registry credentials
3. **Resource limits**: Check node resources

**Resolution**:
```bash
# Fix Redis connection
kubectl exec -n waooaw deployment/event-bus -- \
  python -c "import redis.asyncio as redis; import asyncio; asyncio.run(redis.from_url('redis://redis-service:6379').ping())"

# Check resource availability
kubectl top nodes
kubectl top pods -n waooaw
```

### High Latency

**Symptoms**: `latency.p95` > 1s, slow event delivery

**Diagnosis**:
```bash
# Check metrics
curl http://localhost:8080/metrics | jq '.latency'

# Check Redis performance
kubectl exec -n waooaw redis-0 -- redis-cli info stats
```

**Common Causes**:
1. Redis overloaded
2. Network issues
3. Too many subscribers

**Resolution**:
```bash
# Scale Event Bus
kubectl scale deployment event-bus -n waooaw --replicas=5

# Check Redis memory
kubectl exec -n waooaw redis-0 -- redis-cli info memory

# Increase Redis resources
kubectl edit statefulset redis -n waooaw
# Update resources.limits.memory and resources.limits.cpu
```

### Events Not Delivered

**Symptoms**: `totals.deliveries` not increasing, subscribers not receiving events

**Diagnosis**:
```bash
# Check subscriber health
curl http://localhost:8080/metrics | jq '.subscribers.health'

# Check Event Bus logs
kubectl logs -n waooaw -l app=event-bus | grep "subscription\|delivery"

# Check Redis pub/sub
kubectl exec -n waooaw redis-0 -- redis-cli pubsub channels
```

**Common Causes**:
1. Subscriber disconnected
2. Pattern mismatch
3. Redis connection lost

**Resolution**:
```bash
# Restart Event Bus
kubectl rollout restart deployment event-bus -n waooaw

# Check Redis connectivity
kubectl exec -n waooaw redis-0 -- redis-cli ping
```

### High Error Rate

**Symptoms**: `totals.errors` > 5% of publishes, unhealthy subscribers

**Diagnosis**:
```bash
# Check error metrics
curl http://localhost:8080/metrics | jq '.totals.errors, .event_types'

# Check DLQ
# (DLQ accessible via application logs)
kubectl logs -n waooaw -l app=event-bus | grep "DLQ\|dead_letter"

# Check subscriber health
curl http://localhost:8080/metrics | jq '.subscribers'
```

**Common Causes**:
1. Validation errors
2. Handler failures
3. Timeout issues

**Resolution**:
```bash
# Check validation errors
kubectl logs -n waooaw -l app=event-bus | grep "validation"

# Identify unhealthy subscribers
curl http://localhost:8080/metrics | jq '.subscribers.health.unhealthy'

# Review event schemas
# (Check application code for schema definitions)
```

---

## Rollback

### Quick Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment event-bus -n waooaw

# Check rollback status
kubectl rollout status deployment event-bus -n waooaw
```

### Rollback to Specific Version

```bash
# View revision history
kubectl rollout history deployment event-bus -n waooaw

# Rollback to specific revision
kubectl rollout undo deployment event-bus -n waooaw --to-revision=3
```

---

## Maintenance

### Update Configuration

```bash
# Edit ConfigMap
kubectl edit configmap event-bus-config -n waooaw

# Restart pods to apply changes
kubectl rollout restart deployment event-bus -n waooaw
```

### Upgrade Event Bus

```bash
# Update image version in deployment
kubectl set image deployment/event-bus -n waooaw \
  event-bus=waooaw/event-bus:0.7.0

# Monitor rollout
kubectl rollout status deployment event-bus -n waooaw
```

### Backup Redis Data

```bash
# Create backup
kubectl exec -n waooaw redis-0 -- redis-cli BGSAVE

# Copy RDB file
kubectl cp waooaw/redis-0:/data/dump.rdb ./redis-backup-$(date +%Y%m%d).rdb
```

---

## Performance Tuning

### Redis Optimization

```bash
# Increase Redis memory
kubectl edit statefulset redis -n waooaw
# Update: resources.limits.memory: "4Gi"

# Tune maxmemory-policy
kubectl edit configmap redis-config -n waooaw
# Update: maxmemory-policy allkeys-lru
```

### Event Bus Optimization

```bash
# Increase replica count
kubectl scale deployment event-bus -n waooaw --replicas=10

# Increase resource limits
kubectl edit deployment event-bus -n waooaw
# Update: resources.limits.memory: "1Gi"
# Update: resources.limits.cpu: "1000m"
```

---

## Security

### Network Policies

```yaml
# Restrict Event Bus traffic
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: event-bus-netpol
  namespace: waooaw
spec:
  podSelector:
    matchLabels:
      app: event-bus
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          component: agent
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```

---

## Contact

**Escalation Path**:
1. Platform Team (Slack: #platform-oncall)
2. SRE Team (PagerDuty: platform-sre)
3. Engineering Lead

**Documentation**:
- Architecture: `/docs/platform/PLATFORM_ARCHITECTURE.md`
- Event Bus API: `/waooaw/events/README.md`
- Runbooks: `/docs/runbooks/`
