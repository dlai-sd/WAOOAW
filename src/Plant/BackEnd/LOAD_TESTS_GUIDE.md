# Load Tests Guide - WAOOAW Plant Backend

**Document:** Load Testing & Performance Validation Guide  
**Date:** 2026-01-14  
**Framework:** pytest-benchmark + locust (optional)  
**SLA Targets:** Response time <500ms (P95), Throughput >1000 req/s  
**Status:** Ready for Configuration  

---

## Overview

Load tests validate that the Plant backend meets Service Level Agreements (SLAs) under expected traffic patterns. Tests measure response time, throughput, and resource utilization.

### Key Metrics

| Metric | Target | Validation |
|--------|--------|-----------|
| **Response Time (P95)** | <500ms | API endpoints |
| **Throughput** | >1000 req/s | Concurrent requests |
| **CPU Utilization** | <70% | System monitoring |
| **Memory Usage** | <2GB | Resource limits |
| **Database Connections** | <20 active | Connection pool |
| **Error Rate** | <0.1% | 404/500 responses |

---

## Load Test Categories

### 1. Benchmark Tests (pytest-benchmark)

**Purpose:** Measure individual operation performance

**Test Structure:**
```python
def test_base_entity_creation_performance(benchmark):
    """Measure BaseEntity creation speed."""
    result = benchmark(BaseEntity.create, name="Test")
    assert result.created_at is not None
    # Expected: <5ms per operation

def test_skill_validation_performance(benchmark):
    """Measure Skill validation speed."""
    skill = Skill(name="Python", category="technical")
    result = benchmark(skill.validate_l0)
    assert result.is_valid
    # Expected: <2ms per operation

def test_hash_chain_validation_performance(benchmark):
    """Measure hash chain integrity check speed."""
    chain = [hash1, hash2, hash3, hash4, hash5]
    result = benchmark(validate_chain, chain)
    assert result is True
    # Expected: <10ms per 5-hash chain
```

**Execution:**
```bash
# Run benchmark tests
pytest tests/performance/ -v --benchmark-only

# Compare with baseline
pytest tests/performance/ -v --benchmark-compare

# Generate benchmark report
pytest tests/performance/ -v --benchmark-json=benchmark.json
```

### 2. Concurrency Tests (locust)

**Purpose:** Simulate real-world concurrent traffic

**Test File:** `tests/performance/locustfile.py`

```python
from locust import HttpUser, task, between

class PlantUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def list_agents(self):
        """Simulate user browsing agents (3x weight)."""
        self.client.get("/api/v1/agents")
    
    @task(2)
    def create_skill(self):
        """Simulate creating skill (2x weight)."""
        self.client.post("/api/v1/skills", json={
            "name": f"Skill_{random.randint(1,1000)}",
            "category": "technical"
        })
    
    @task(1)
    def validate_agent(self):
        """Simulate agent validation (1x weight)."""
        agent_id = random.choice(self.agent_ids)
        self.client.get(f"/api/v1/agents/{agent_id}")
```

**Execution:**
```bash
# Start Plant backend
cd /workspaces/WAOOAW/src/Plant/BackEnd
python main.py &

# Run load test (10 users, 1 minute ramp-up)
locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
  -u 10 -r 1 -t 60s

# Or headless (no web UI)
locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
  -u 100 -r 10 -t 300s --headless -c 100 -s 10
```

### 3. Stress Tests (Apache JMeter / K6)

**Purpose:** Find breaking point under extreme load

**Load Curve:**
```
┌─────────────────────────────────────┐
│  Stress Test Load Profile           │
│                                     │
│         ╱╲                          │
│        ╱  ╲      Spike              │
│       ╱    ╲                        │
│      ╱      ╲___                    │
│     ╱           ╲  ╲               │
│    ╱             ╲  ╲              │
│   ╱               ╲  ╲            │
│  ╱                 ╲  ╲___         │
│ ╱                   ╲      ╲       │
│                      ╲      ╲      │
└─────────────────────────────────────┘
0%    10%    20%    30%    40%    50%
Phase 1: Ramp up (normal)
Phase 2: Sustain (expected)
Phase 3: Spike (surge)
Phase 4: Recovery (degradation)
```

**Test Phases:**
- Phase 1 (Ramp-up): 0→100 users over 5 minutes
- Phase 2 (Sustain): 100 users for 10 minutes (expected load)
- Phase 3 (Spike): 100→500 users over 2 minutes (surge)
- Phase 4 (Recovery): Monitor degradation (5 minutes)

### 4. Endurance Tests

**Purpose:** Validate stability over extended periods

**Configuration:**
```bash
# Low-load endurance test (8 hours)
- 50 concurrent users
- Request rate: 500 req/s
- Monitor: Memory leaks, connection pool stability
- Expected: <1% error rate throughout

# Medium-load endurance test (24 hours)
- 100 concurrent users
- Request rate: 1000 req/s
- Monitor: Database performance, cache hit ratio
- Expected: <0.1% error rate, no degradation
```

---

## SLA Validation Checklist

### Response Time SLAs
```yaml
genesis_certification_check:
  endpoint: POST /api/v1/genesis/certify
  p50_target: <100ms
  p95_target: <500ms
  p99_target: <1000ms
  load: 100 concurrent users

agent_list:
  endpoint: GET /api/v1/agents
  p50_target: <50ms
  p95_target: <300ms
  p99_target: <500ms
  load: 1000 concurrent users

agent_search:
  endpoint: GET /api/v1/agents?search=...
  p50_target: <200ms
  p95_target: <800ms
  p99_target: <1500ms
  load: 500 concurrent users, database indexed
```

### Throughput SLAs
```yaml
minimum_throughput:
  baseline: 1000 requests/second
  sustained: 800 requests/second (with P95 <500ms)
  burst: 5000 requests/second (for 30 seconds)

resource_limits:
  cpu_utilization: <70% under normal load, <90% under peak
  memory_usage: <2GB RAM
  database_connections: <20 active
  redis_connections: <10 active
```

### Error Rate SLAs
```yaml
production_targets:
  normal_load: <0.01% (1 error per 10,000 requests)
  peak_load: <0.1% (1 error per 1,000 requests)
  
acceptable_errors:
  5xx: <0.01% (always bad)
  4xx: <0.1% (validation failures acceptable)
  timeouts: <0.05% (network issues)
```

---

## Load Test Scenarios

### Scenario 1: Normal Daily Load
```
Time Period: 9 AM - 5 PM
Users: 100-200 concurrent
Requests: 500-1000 req/s
Expected SLAs: All P95 <500ms
Tools: locust, Prometheus metrics
```

### Scenario 2: Peak Marketing Campaign
```
Time Period: Launch day (24 hours)
Users: 500-1000 concurrent
Requests: 3000-5000 req/s
Expected SLAs: P95 <1000ms (relaxed)
Tools: locust, Datadog, custom monitoring
```

### Scenario 3: Backup/Maintenance Window
```
Time Period: 2 AM - 4 AM
Users: 50 concurrent
Requests: 200-300 req/s
Tasks: Database backups, migrations
Expected SLAs: All P95 <1000ms
Tools: Custom script, cron jobs
```

### Scenario 4: System Upgrade
```
Time Period: Blue-green deployment
Old Version: Gradually drain traffic
New Version: Gradually receive traffic
Overlap: 5-10 minutes
Expected SLAs: <0.1% errors during transition
Tools: Load balancer, health checks
```

---

## Load Test Execution

### Setup Environment
```bash
# 1. Start backend server
cd /workspaces/WAOOAW/src/Plant/BackEnd
python main.py  # Runs on localhost:8000

# 2. Verify health endpoint
curl http://localhost:8000/health
# Expected: {"status": "healthy", "timestamp": "2026-01-14T..."}

# 3. Seed test data
python scripts/seed_test_data.py --agents=100 --skills=50
```

### Option 1: pytest-benchmark (Function-level)
```bash
# Run benchmark tests
cd /workspaces/WAOOAW/src/Plant/BackEnd
pytest tests/performance/ -v --benchmark-only

# Compare with baseline
pytest tests/performance/ -v --benchmark-compare=.benchmarks/0001_*.json
```

### Option 2: Locust (HTTP-level)
```bash
# Terminal 1: Start backend
cd /workspaces/WAOOAW/src/Plant/BackEnd
python main.py

# Terminal 2: Run load test
locust -f tests/performance/locustfile.py \
  --host=http://localhost:8000 \
  -u 100 -r 10 -t 300s

# Or headless
locust -f tests/performance/locustfile.py \
  --host=http://localhost:8000 \
  -u 100 -r 10 -t 300s --headless
```

### Option 3: Custom Script
```python
# tests/performance/custom_load_test.py
import asyncio
import time
from httpx import AsyncClient

async def load_test():
    async with AsyncClient() as client:
        start = time.time()
        tasks = [
            client.get("http://localhost:8000/api/v1/agents")
            for _ in range(1000)
        ]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start
        
        successful = sum(1 for r in results if 200 <= r.status_code < 300)
        print(f"Completed {successful}/1000 in {elapsed:.2f}s")
        print(f"Throughput: {successful/elapsed:.0f} req/s")

asyncio.run(load_test())
```

---

## Expected Results

### Benchmark Results Example
```
test_base_entity_creation_performance
  rounds: 1000
  mean: 3.45 ms
  stddev: 0.12 ms
  min: 3.21 ms
  max: 3.89 ms
  ✓ PASS (target: <5ms)

test_hash_chain_validation_performance
  rounds: 500
  mean: 8.92 ms
  stddev: 0.34 ms
  min: 8.45 ms
  max: 9.78 ms
  ✓ PASS (target: <10ms)
```

### Locust Results Example
```
Response time percentiles (in milliseconds):
  50%: 45ms
  66%: 89ms
  75%: 125ms
  90%: 287ms
  95%: 412ms  ✓ PASS (target: <500ms)
  99%: 785ms

Requests/sec: 1,045 req/s ✓ PASS (target: >1000)
Error rate: 0.03% ✓ PASS (target: <0.1%)
```

---

## Monitoring During Load Tests

### Metrics to Track
```bash
# CPU & Memory (in separate terminal)
watch -n 1 'ps aux | grep "[p]ython main.py"'

# Database connections
psql -U postgres -d plant_db -c "SELECT count(*) FROM pg_stat_activity;"

# Network traffic
nethogs -d 1

# Container stats (if using Docker)
docker stats --no-stream plant-backend
```

### Grafana Dashboard
```yaml
Dashboards:
  - Request Rate (req/s over time)
  - Response Time (P50, P95, P99)
  - Error Rate (4xx, 5xx)
  - CPU Usage (%)
  - Memory Usage (GB)
  - Database Connections (active count)
  - Cache Hit Ratio (%)
```

---

## Common Issues & Solutions

### Issue: Response time > 500ms
**Diagnosis:**
```bash
# Check slow queries
tail -f /var/log/postgresql/postgresql.log | grep "duration: [1-9][0-9][0-9][0-9]"

# Check database indexes
psql -U postgres -d plant_db -c "SELECT * FROM pg_stat_user_indexes WHERE idx_scan < 100;"

# Check connection pool
curl http://localhost:8000/metrics | grep "db_pool"
```

**Solution:** Add database indexes, increase pool size, optimize query

### Issue: Error rate > 0.1%
**Diagnosis:**
```bash
# Check error logs
grep "ERROR" /var/log/plant-backend.log | head -20

# Check timeout errors
grep "TimeoutError" /var/log/plant-backend.log | wc -l
```

**Solution:** Increase timeout, add retry logic, scale horizontally

### Issue: Memory leak (memory grows over time)
**Diagnosis:**
```bash
# Monitor memory during long test
while true; do ps aux | grep python | grep -v grep | awk '{print $6}'; sleep 5; done

# Check for circular references
python -m memory_profiler tests/performance/memory_leak_test.py
```

**Solution:** Fix circular references, add proper cleanup in fixtures

---

## CI/CD Integration

### GitHub Actions Workflow
```yaml
name: Load Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r src/Plant/BackEnd/requirements.txt locust
      
      - name: Start backend
        run: |
          cd src/Plant/BackEnd
          python main.py &
          sleep 5
      
      - name: Run load tests
        run: |
          cd src/Plant/BackEnd
          locust -f tests/performance/locustfile.py \
            --host=http://localhost:8000 \
            -u 100 -r 10 -t 300s --headless \
            -c 100 -s 10 \
            --csv=load-test-results
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: src/Plant/BackEnd/load-test-results*
```

---

## SLA Dashboard

**Prometheus Queries:**
```promql
# Response time P95
histogram_quantile(0.95, http_request_duration_seconds_bucket)

# Throughput
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Database connection pool usage
pg_stat_database_numbackends / max_connections
```

---

## Next Steps

1. **Configure pytest-benchmark:** Add benchmark tests to `tests/performance/`
2. **Setup Locust:** Create `tests/performance/locustfile.py` with realistic scenarios
3. **Define SLA Targets:** Document response time, throughput, error rate targets
4. **Integrate with CI/CD:** Add load tests to GitHub Actions (daily, on-demand)
5. **Setup Monitoring:** Prometheus + Grafana dashboard
6. **Setup Sonar:** (Future phase - for code quality analysis)

---

**Last Updated:** 2026-01-14  
**Status:** Ready for Configuration  
**Frameworks:** pytest-benchmark, locust (optional)  
**SLA Targets:** P95 <500ms, >1000 req/s, <0.1% error rate
