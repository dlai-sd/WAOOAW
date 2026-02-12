# Performance Testing with Locust

This directory contains load testing configurations for the Plant Backend API using Locust.

## Quick Start

### 1. Run Basic Smoke Test (1 user)

```bash
# Inside Docker container
docker compose -f docker-compose.local.yml exec plant-backend \
  locust -f tests/performance/locustfile.py \
  --host=http://localhost:8001 \
  --users 1 \
  --spawn-rate 1 \
  --run-time 30s \
  --headless
```

### 2. Run Progressive Load Tests

**10 Concurrent Users (Warm-up):**
```bash
docker compose -f docker-compose.local.yml exec plant-backend \
  locust -f tests/performance/locustfile.py \
  --host=http://localhost:8001 \
  --users 10 \
  --spawn-rate 2 \
  --run-time 5m \
  --headless \
  --html reports/load_10users.html
```

**50 Concurrent Users (Normal Load):**
```bash
docker compose -f docker-compose.local.yml exec plant-backend \
  locust -f tests/performance/locustfile.py \
  --host=http://localhost:8001 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 10m \
  --headless \
  --html reports/load_50users.html
```

**100 Concurrent Users (Peak Load):**
```bash
docker compose -f docker-compose.local.yml exec plant-backend \
  locust -f tests/performance/locustfile.py \
  --host=http://localhost:8001 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 15m \
  --headless \
  --html reports/load_100users.html \
  --csv reports/load_100users
```

### 3. Run Spike Test (0→200 users in 30s)

```bash
docker compose -f docker-compose.local.yml exec plant-backend \
  locust -f tests/performance/locustfile.py \
  --host=http://localhost:8001 \
  --users 200 \
  --spawn-rate 6.67 \
  --run-time 5m \
  --headless \
  --html reports/spike_200users.html
```

### 4. Run 24-Hour Soak Test

```bash
docker compose -f docker-compose.local.yml exec plant-backend \
  locust -f tests/performance/locustfile.py \
  --host=http://localhost:8001 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 24h \
  --headless \
  --html reports/soak_24h.html \
  --csv reports/soak_24h
```

## Web UI Mode

To run with the web interface for real-time monitoring:

```bash
docker compose -f docker-compose.local.yml exec plant-backend \
  locust -f tests/performance/locustfile.py \
  --host=http://localhost:8001 \
  --web-host=0.0.0.0 \
  --web-port=8089
```

Then open browser to `http://localhost:8089` (or your Codespace URL with port 8089).

## Test Scenarios

### PlantBackendUser (Full User Journey)

Simulates a typical customer with weighted task distribution:

- **Health Check (10x)**: `/health` - Checking system availability
- **List Agents (8x)**: `/api/v1/agents` - Browsing available agents
- **Filter Agents (5x)**: `/api/v1/agents?industry=*` - Searching agents
- **Get Customer Agents (6x)**: `/api/v1/customers/:id/agents` - Viewing hired agents
- **Get Configuration (4x)**: `/api/v1/agents/:id/configuration` - Checking agent settings
- **List Goals (3x)**: `/api/v1/agents/:id/goals` - Viewing goals
- **Get Deliverables (2x)**: `/api/v1/agents/:id/deliverables` - Checking outputs
- **Create Goal (1x)**: `POST /api/v1/agents/:id/goals` - Creating new goal

### HealthCheckUser (Lightweight)

Only hits `/health` endpoint for basic availability checks.

## Performance SLA Thresholds

From [AGP2-PERF-1_Implementation_Plan.md](/workspaces/WAOOAW/docs/AGP2-PERF-1_Implementation_Plan.md):

| Endpoint Type | P50 Target | P95 Target | P99 Target |
|---------------|------------|------------|------------|
| Health Check | < 50ms | < 100ms | < 200ms |
| Read (Light) | < 100ms | < 300ms | < 500ms |
| Read (Medium) | < 150ms | < 400ms | < 600ms |
| Read (Heavy) | < 200ms | < 500ms | < 800ms |
| Write (Light) | < 200ms | < 600ms | < 1000ms |
| Write (Heavy) | < 300ms | < 800ms | < 1500ms |

## Success Criteria

✅ **Passed** if:
- P95 latency meets targets for all endpoints
- Error rate < 1% under normal load (50 users)
- Error rate < 5% under peak load (100 users)
- System handles spike to 200 users without crashes
- No memory leaks during 24-hour soak test

❌ **Failed** if:
- Any P95 latency exceeds target by >50%
- Error rate > 5% under normal load
- System crashes or becomes unresponsive
- Memory usage grows unbounded (>20% increase over 24h)

## Reports

HTML reports are saved to `tests/performance/reports/`:
- `load_10users.html` - 10 concurrent users
- `load_50users.html` - 50 concurrent users (normal load)
- `load_100users.html` - 100 concurrent users (peak load)
- `spike_200users.html` - Spike test
- `soak_24h.html` - 24-hour soak test

CSV reports include detailed statistics for further analysis.

## Troubleshooting

**Container not running:**
```bash
docker compose -f docker-compose.local.yml up -d plant-backend
```

**Locust not found:**
```bash
docker compose -f docker-compose.local.yml exec plant-backend pip install locust
```

**Connection refused:**
- Check backend is accessible: `docker compose -f docker-compose.local.yml exec plant-backend curl http://localhost:8001/health`
- Backend runs on port 8001, not 8000

**Reports directory missing:**
```bash
docker compose -f docker-compose.local.yml exec plant-backend mkdir -p tests/performance/reports
```

## Next Steps

After load testing (AGP2-PERF-1.2):
1. ✅ Identify slow endpoints (P95 > target)
2. ✅ Run database query analysis (AGP2-PERF-1.4a)
3. ✅ Implement caching for hot paths (AGP2-PERF-1.4b)
4. ✅ Optimize database connection pooling (AGP2-PERF-1.5)
5. ✅ Re-run load tests to validate improvements
