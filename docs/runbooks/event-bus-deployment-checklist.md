# WowEvent Deployment Checklist

## Pre-Deployment

- [ ] **Code Review**: All PRs approved and merged
- [ ] **Tests**: 133/133 tests passing ✅
- [ ] **Coverage**: 91% overall ✅
- [ ] **Dependencies**: All packages in requirements.txt
- [ ] **Configuration**: Environment variables documented

## Build & Test

- [ ] **Docker Build**: Event Bus image builds successfully
  ```bash
  docker build -f infrastructure/docker/event-bus.Dockerfile -t waooaw/event-bus:0.6.5 .
  ```

- [ ] **Syntax Validation**: Service module compiles ✅
  ```bash
  python -m py_compile waooaw/events/service.py
  ```

- [ ] **Import Test**: Service imports successfully ✅
  ```bash
  python -c "from waooaw.events.service import EventBusService"
  ```

- [ ] **Docker Compose**: Configuration valid
  ```bash
  docker compose -f docker-compose.events.yml config --quiet
  ```

## Local Deployment

- [ ] **Start Redis**
  ```bash
  docker compose -f docker-compose.events.yml up redis -d
  ```

- [ ] **Verify Redis**
  ```bash
  docker exec waooaw-redis redis-cli ping
  ```

- [ ] **Start Event Bus**
  ```bash
  docker compose -f docker-compose.events.yml up event-bus -d
  ```

- [ ] **Health Check**
  ```bash
  curl http://localhost:8080/health
  ```

- [ ] **Metrics Check**
  ```bash
  curl http://localhost:8080/metrics
  ```

- [ ] **Logs Check**
  ```bash
  docker logs waooaw-event-bus
  ```

## Kubernetes Deployment

### Namespace Setup

- [ ] **Create Namespace**
  ```bash
  kubectl create namespace waooaw
  ```

- [ ] **Verify Namespace**
  ```bash
  kubectl get namespace waooaw
  ```

### Redis Deployment

- [ ] **Deploy Redis**
  ```bash
  kubectl apply -f infrastructure/kubernetes/redis-deployment.yaml
  ```

- [ ] **Wait for Redis**
  ```bash
  kubectl wait --for=condition=ready pod -l app=redis -n waooaw --timeout=120s
  ```

- [ ] **Test Redis Connection**
  ```bash
  kubectl exec -n waooaw redis-0 -- redis-cli ping
  ```

### Event Bus Deployment

- [ ] **Deploy Event Bus**
  ```bash
  kubectl apply -f infrastructure/kubernetes/event-bus-deployment.yaml
  ```

- [ ] **Wait for Event Bus**
  ```bash
  kubectl wait --for=condition=ready pod -l app=event-bus -n waooaw --timeout=120s
  ```

- [ ] **Check Pod Status**
  ```bash
  kubectl get pods -n waooaw -l app=event-bus
  ```

- [ ] **Check Logs**
  ```bash
  kubectl logs -n waooaw -l app=event-bus --tail=50
  ```

### Health Verification

- [ ] **Port Forward**
  ```bash
  kubectl port-forward -n waooaw svc/event-bus-service 8080:8080
  ```

- [ ] **Test Health Endpoint**
  ```bash
  curl http://localhost:8080/health
  ```
  Expected: `{"status": "healthy", "redis": "connected", "event_bus": "running"}`

- [ ] **Test Readiness Endpoint**
  ```bash
  curl http://localhost:8080/ready
  ```
  Expected: `{"status": "ready"}`

- [ ] **Test Metrics Endpoint**
  ```bash
  curl http://localhost:8080/metrics
  ```

### Scaling Verification

- [ ] **Check HPA**
  ```bash
  kubectl get hpa -n waooaw event-bus-hpa
  ```

- [ ] **Check PDB**
  ```bash
  kubectl get pdb -n waooaw event-bus-pdb
  ```

- [ ] **Manual Scale Test**
  ```bash
  kubectl scale deployment event-bus -n waooaw --replicas=3
  kubectl get pods -n waooaw -l app=event-bus
  kubectl scale deployment event-bus -n waooaw --replicas=2
  ```

## Integration Testing

- [ ] **Publish Test Event**
  ```python
  import asyncio
  import redis.asyncio as redis
  from waooaw.events import EventBus, Event
  
  async def test():
      client = await redis.from_url("redis://localhost:6379")
      bus = EventBus(client)
      await bus.start()
      
      event = Event(
          event_type="deployment.test",
          source_agent="deployment-script",
          payload={"status": "testing"}
      )
      await bus.publish(event)
      
      await bus.stop()
      await client.close()
  
  asyncio.run(test())
  ```

- [ ] **Subscribe Test**
  ```python
  import asyncio
  import redis.asyncio as redis
  from waooaw.events import EventBus, Event
  
  received = []
  
  async def handler(event: Event):
      received.append(event)
  
  async def test():
      client = await redis.from_url("redis://localhost:6379")
      bus = EventBus(client)
      await bus.start()
      
      await bus.subscribe("deployment.*", handler, "test-subscriber")
      
      event = Event(
          event_type="deployment.test",
          source_agent="deployment-script",
          payload={"status": "testing"}
      )
      await bus.publish(event)
      
      await asyncio.sleep(1)
      assert len(received) == 1
      
      await bus.stop()
      await client.close()
  
  asyncio.run(test())
  ```

- [ ] **Metrics Verification**
  ```bash
  curl http://localhost:8080/metrics | jq '
    .totals.publishes,
    .totals.deliveries,
    .throughput.publishes.per_second,
    .latency.p95
  '
  ```

## Monitoring Setup

- [ ] **Prometheus Scraping**
  - Verify annotations on pod
  - Check Prometheus targets

- [ ] **Grafana Dashboard**
  - Import dashboard
  - Verify metrics display

- [ ] **Alerting Rules**
  - High error rate alert
  - High latency alert
  - Pod crash alert

## Post-Deployment

- [ ] **Update Documentation**
  - [x] README.md updated ✅
  - [x] Runbook created ✅
  - [ ] Architecture diagram in docs

- [ ] **Tag Release**
  ```bash
  git tag -a v0.6.5 -m "WowEvent Event Bus - Production Ready"
  git push origin v0.6.5
  ```

- [ ] **Notify Team**
  - Slack announcement (#platform)
  - Email to stakeholders
  - Update project status

- [ ] **Monitor for 24h**
  - Check error rates
  - Monitor latency
  - Review logs
  - Verify auto-scaling

## Rollback Plan

If issues occur:

1. **Quick Rollback**
   ```bash
   kubectl rollout undo deployment event-bus -n waooaw
   ```

2. **Check Status**
   ```bash
   kubectl rollout status deployment event-bus -n waooaw
   ```

3. **Verify Rollback**
   ```bash
   curl http://localhost:8080/health
   ```

## Sign-Off

- [ ] **Development Lead**: ________________ Date: ________
- [ ] **SRE Lead**: ________________ Date: ________
- [ ] **Platform Lead**: ________________ Date: ________

---

**Deployment Date**: ____________  
**Version**: 0.6.5-dev  
**Epic**: 3.1 Event Bus Implementation  
**Story**: 7 - Deploy WowEvent (2 pts)  
**Status**: ✅ READY FOR DEPLOYMENT
