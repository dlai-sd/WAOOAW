#!/bin/bash
# Connection Pool Validation Script for AGP2-PERF-1.5
#
# Monitors PostgreSQL connections during load testing to validate:
# - Pool size is adequate
# - No connection exhaustion
# - Connection reuse is efficient

set -e

echo "================================================================================"
echo "AGP2-PERF-1.5: Database Connection Pool Validation"
echo "================================================================================"
echo ""

# Configuration
USERS=100
DURATION="5m"
SPAWN_RATE=10

echo "Test Configuration:"
echo "  • Concurrent Users: $USERS"
echo "  • Test Duration: $DURATION"
echo "  • Spawn Rate: $SPAWN_RATE users/second"
echo ""

# Check current pool configuration
echo "📊 Current Pool Configuration:"
echo "--------------------------------------------------------------------------------"
docker compose -f /workspaces/WAOOAW/docker-compose.local.yml exec plant-backend python -c "
from core.config import settings
print(f'  • Pool Size: {settings.database_pool_size} (core connections)')
print(f'  • Max Overflow: {settings.database_max_overflow} (additional connections)') 
print(f'  • Total Capacity: {settings.database_pool_size + settings.database_max_overflow} connections')
print(f'  • Pool Timeout: {settings.database_pool_timeout} seconds')
print(f'  • Pool Pre-ping: {settings.database_pool_pre_ping}')
"
echo ""

# Function to get connection stats
get_connection_stats() {
    docker compose -f /workspaces/WAOOAW/docker-compose.local.yml exec postgres psql -U waooaw -d waooaw_db -t -c "
        SELECT 
            count(*) FILTER (WHERE state = 'active') as active,
            count(*) FILTER (WHERE state = 'idle') as idle,
            count(*) as total
        FROM pg_stat_activity 
        WHERE datname = 'waooaw_db' AND usename = 'waooaw';
    " | tr -s ' ' | sed 's/^ //'
}

echo "🔍 Pre-Test Connection Baseline:"
echo "--------------------------------------------------------------------------------"
BASELINE=$(get_connection_stats)
echo "  Current connections: $BASELINE"
echo ""

echo "🚀 Starting load test with connection monitoring..."
echo "--------------------------------------------------------------------------------"
echo ""

# Start load test in background
docker compose -f /workspaces/WAOOAW/docker-compose.local.yml exec -T plant-backend \
    /home/appuser/.local/bin/locust \
    -f tests/performance/locustfile.py \
    --host http://localhost:8001 \
    --users $USERS \
    --spawn-rate $SPAWN_RATE \
    --run-time $DURATION \
    --headless \
    --html tests/performance/reports/pool_validation_100users.html \
    --csv tests/performance/reports/pool_validation_100users \
    > /tmp/pool_validation_loadtest.log 2>&1 &

LOAD_TEST_PID=$!

# Monitor connections every 5 seconds
echo "📈 Connection Monitoring (sampling every 5 seconds):"
echo "--------------------------------------------------------------------------------"
echo "Time(s) | Active | Idle | Total | Utilization"
echo "------------------------------------------------"

INTERVAL=5
ELAPSED=0
MAX_TOTAL=0
MAX_ACTIVE=0
SAMPLES=0

# Convert duration to seconds
if [[ $DURATION == *"m" ]]; then
    DURATION_SECONDS=$((${DURATION%m} * 60))
else
    DURATION_SECONDS=${DURATION%s}
fi

while [ $ELAPSED -lt $DURATION_SECONDS ]; do
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
    
    # Get connection stats
    STATS=$(get_connection_stats)
    ACTIVE=$(echo "$STATS" | awk '{print $1}' | sed 's/|//g')
    IDLE=$(echo "$STATS" | awk '{print $2}' | sed 's/|//g')
    TOTAL=$(echo "$STATS" | awk '{print $3}' | sed 's/|//g')
    
    # Calculate utilization (assuming capacity of 60)
    UTILIZATION=$((TOTAL * 100 / 60))
    
    printf "%7d | %6s | %4s | %5s | %5d%%\n" $ELAPSED "$ACTIVE" "$IDLE" "$TOTAL" "$UTILIZATION"
    
    # Track maximums
    if [ "$TOTAL" -gt "$MAX_TOTAL" ]; then
        MAX_TOTAL=$TOTAL
    fi
    if [ "$ACTIVE" -gt "$MAX_ACTIVE" ]; then
        MAX_ACTIVE=$ACTIVE
    fi
    
    SAMPLES=$((SAMPLES + 1))
done

echo ""
echo "⏳ Waiting for load test to complete..."
wait $LOAD_TEST_PID

echo ""
echo "📊 Post-Test Connection Status:"
echo "--------------------------------------------------------------------------------"
FINAL_STATS=$(get_connection_stats)
echo "  Final connections: $FINAL_STATS"
echo ""

# Get load test results
echo "📈 Load Test Results:"
echo "--------------------------------------------------------------------------------"
tail -50 /tmp/pool_validation_loadtest.log
echo ""

echo "================================================================================"
echo "CONNECTION POOL VALIDATION SUMMARY"
echo "================================================================================"
echo ""
echo "Pool Configuration:"
echo "  • Configured Capacity: 60 connections (20 pool + 40 overflow)"
echo ""
echo "Observed Connection Usage:"
echo "  • Peak Total Connections: $MAX_TOTAL"
echo "  • Peak Active Connections: $MAX_ACTIVE"
echo "  • Peak Utilization: $((MAX_TOTAL * 100 / 60))%"
echo ""

# Assessment
echo "✅ ASSESSMENT:"
if [ "$MAX_TOTAL" -le 40 ]; then
    echo "  ✅ Excellent - Pool size (20) is more than adequate"
    echo "     Peak usage ($MAX_TOTAL) well below total capacity (60)"
elif [ "$MAX_TOTAL" -le 50 ]; then
    echo "  ✅ Good - Pool size adequate with some overflow usage"
    echo "     Peak usage ($MAX_TOTAL) within comfortable range"
elif [ "$MAX_TOTAL" -le 58 ]; then
    echo "  ⚠️  Moderate - Pool approaching capacity"
    echo "     Peak usage ($MAX_TOTAL) close to limit (60)"
    echo "     Consider increasing pool_size or max_overflow"
else
    echo "  ❌ Critical - Pool at or near capacity!"
    echo "     Peak usage ($MAX_TOTAL) at limit (60)"
    echo "     MUST increase pool_size or max_overflow"
fi
echo ""

echo "Reports saved to:"
echo "  • tests/performance/reports/pool_validation_100users.html"
echo "  • tests/performance/reports/pool_validation_100users_*.csv"
echo ""
echo "================================================================================"
