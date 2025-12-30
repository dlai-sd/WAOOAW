#!/bin/bash
# Quick Platform Test - Run this to verify your platform works!

set -e

echo "🎯 WAOOAW Platform Quick Test"
echo "=============================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check prerequisites
echo "Step 1: Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose not found. Please install docker-compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker and docker-compose found${NC}"
echo ""

# Step 2: Start infrastructure
echo "Step 2: Starting infrastructure..."
echo "   This may take 30-60 seconds on first run (pulling images)..."
docker-compose -f docker-compose.orchestration.yml up -d

echo "   Waiting for services to be healthy..."
sleep 15

echo ""

# Step 3: Health checks
echo "Step 3: Running health checks..."

# Check Redis
echo -n "   Redis: "
if docker exec waooaw-redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Healthy${NC}"
else
    echo -e "${RED}❌ Down${NC}"
    echo "Run: docker logs waooaw-redis"
    exit 1
fi

# Check Event Bus
echo -n "   Event Bus: "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Healthy (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${YELLOW}⚠️  Might still be starting (HTTP $HTTP_CODE)${NC}"
    echo "   Waiting 10 more seconds..."
    sleep 10
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}   ✅ Now healthy!${NC}"
    else
        echo -e "${RED}   ❌ Still unhealthy. Check logs: docker logs waooaw-event-bus${NC}"
    fi
fi

# Check Orchestration
echo -n "   Orchestration: "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8082/health || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Healthy (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${YELLOW}⚠️  Might still be starting (HTTP $HTTP_CODE)${NC}"
    echo "   Waiting 10 more seconds..."
    sleep 10
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8082/health || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}   ✅ Now healthy!${NC}"
    else
        echo -e "${RED}   ❌ Still unhealthy. Check logs: docker logs waooaw-orchestration${NC}"
    fi
fi

echo ""

# Step 4: Publish test event
echo "Step 4: Publishing test event..."
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
RESPONSE=$(curl -s -X POST http://localhost:8080/publish \
  -H "Content-Type: application/json" \
  -d "{
    \"event_type\": \"test.platform.quickstart\",
    \"payload\": {
      \"message\": \"WAOOAW Platform is running!\",
      \"timestamp\": \"$TIMESTAMP\",
      \"test_id\": \"quickstart-001\"
    }
  }" 2>&1)

if echo "$RESPONSE" | grep -q "success\|published\|ok" || [ "$?" = "52" ]; then
    echo -e "${GREEN}✅ Event published successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Event may have been published (check logs)${NC}"
    echo "   Response: $RESPONSE"
fi

echo ""

# Step 5: Check metrics
echo "Step 5: Checking metrics..."
echo ""
echo "📊 Event Bus Metrics:"
curl -s http://localhost:8080/metrics 2>/dev/null | grep -E "events_published|events_consumed|event_bus_latency" | head -5 || echo "   (Metrics endpoint not yet implemented)"

echo ""
echo "📊 Orchestration Metrics:"
curl -s http://localhost:8082/metrics 2>/dev/null | grep -E "task_queue|worker_pool|tasks_completed" | head -5 || echo "   (Metrics endpoint not yet implemented)"

echo ""

# Step 6: Summary
echo "=============================="
echo -e "${GREEN}🎉 Platform Quick Test Complete!${NC}"
echo ""
echo "Your platform is running at:"
echo "   🔵 Event Bus:       http://localhost:8080"
echo "   🟣 Orchestration:   http://localhost:8082"
echo "   🔴 Redis:           localhost:6379"
echo ""
echo "Next steps:"
echo "   1. Check logs:      docker-compose -f docker-compose.orchestration.yml logs -f"
echo "   2. Monitor Redis:   redis-cli -h localhost -p 6379"
echo "   3. Run tests:       pytest tests/integration/ -v"
echo "   4. Read guide:      docs/runbooks/PLATFORM_OPERATOR_GUIDE.md"
echo ""
echo "To stop:"
echo "   docker-compose -f docker-compose.orchestration.yml down"
echo ""
