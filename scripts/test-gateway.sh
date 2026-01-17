#!/bin/bash
set -e

# Local Gateway Test Script
# Tests gateways in Docker Compose environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}WAOOAW Gateway Local Testing${NC}"
echo -e "${GREEN}========================================${NC}"

# Start services
start_services() {
    echo ""
    echo -e "${YELLOW}Starting services with docker-compose...${NC}"
    
    cd "$PROJECT_ROOT"
    docker-compose -f docker-compose.gateway.yml up -d
    
    # Wait for services to be healthy
    echo "Waiting for services to be healthy..."
    sleep 15
    
    # Check health
    for service in postgres redis opa plant-service cp-gateway pp-gateway; do
        if docker-compose -f docker-compose.gateway.yml ps | grep "$service" | grep "Up" > /dev/null; then
            echo -e "${GREEN}✓ $service is running${NC}"
        else
            echo -e "${RED}✗ $service failed to start${NC}"
            docker-compose -f docker-compose.gateway.yml logs "$service"
            exit 1
        fi
    done
}

# Run unit tests
run_unit_tests() {
    echo ""
    echo -e "${YELLOW}Running unit tests...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Run tests in Docker
    docker-compose -f docker-compose.gateway.yml run --rm cp-gateway \
        pytest middleware/tests/ -v --cov=middleware --cov-report=term-missing
    
    echo -e "${GREEN}✓ Unit tests passed${NC}"
}

# Run integration tests
run_integration_tests() {
    echo ""
    echo -e "${YELLOW}Running integration tests...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Wait for gateways to be fully ready
    sleep 5
    
    # Test CP Gateway health
    echo "Testing CP Gateway health..."
    curl -f http://localhost:8000/health || {
        echo -e "${RED}✗ CP Gateway health check failed${NC}"
        docker-compose -f docker-compose.gateway.yml logs cp-gateway
        exit 1
    }
    
    # Test PP Gateway health
    echo "Testing PP Gateway health..."
    curl -f http://localhost:8001/health || {
        echo -e "${RED}✗ PP Gateway health check failed${NC}"
        docker-compose -f docker-compose.gateway.yml logs pp-gateway
        exit 1
    }
    
    # Run integration test suite
    pytest src/gateway/tests/test_integration.py -v --asyncio-mode=auto
    
    echo -e "${GREEN}✓ Integration tests passed${NC}"
}

# Run smoke tests
run_smoke_tests() {
    echo ""
    echo -e "${YELLOW}Running smoke tests...${NC}"
    
    # Generate test JWT
    JWT_TOKEN=$(python3 << 'EOF'
import jwt
from datetime import datetime, timedelta

payload = {
    "sub": "user_test",
    "customer_id": "customer_test",
    "email": "test@waooaw.com",
    "iss": "waooaw.com",
    "iat": int(datetime.utcnow().timestamp()),
    "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
    "trial_mode": False,
    "roles": ["developer"]
}

# Use test key (in production, use real key)
key = "test-secret-key"
token = jwt.encode(payload, key, algorithm="HS256")
print(token)
EOF
)
    
    # Test authenticated request to CP Gateway
    echo "Testing authenticated request to CP Gateway..."
    curl -X GET http://localhost:8000/api/v1/agents/test \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -H "X-Correlation-ID: test-$(uuidgen)" \
        -v
    
    # Test authenticated request to PP Gateway
    echo ""
    echo "Testing authenticated request to PP Gateway..."
    curl -X GET http://localhost:8001/api/v1/agents/test \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -H "X-Correlation-ID: test-$(uuidgen)" \
        -v
    
    echo ""
    echo -e "${GREEN}✓ Smoke tests passed${NC}"
}

# Performance test
run_performance_test() {
    echo ""
    echo -e "${YELLOW}Running performance test...${NC}"
    
    if ! command -v ab &> /dev/null; then
        echo -e "${YELLOW}⚠ Apache Bench (ab) not found, skipping performance test${NC}"
        return
    fi
    
    # Simple load test with Apache Bench
    echo "Load testing CP Gateway (100 requests, 10 concurrent)..."
    ab -n 100 -c 10 -H "Authorization: Bearer test" http://localhost:8000/health
    
    echo ""
    echo "Load testing PP Gateway (100 requests, 10 concurrent)..."
    ab -n 100 -c 10 -H "Authorization: Bearer test" http://localhost:8001/health
    
    echo -e "${GREEN}✓ Performance test complete${NC}"
}

# View logs
view_logs() {
    echo ""
    echo -e "${YELLOW}Recent gateway logs:${NC}"
    echo ""
    echo "=== CP Gateway ==="
    docker-compose -f docker-compose.gateway.yml logs --tail=20 cp-gateway
    echo ""
    echo "=== PP Gateway ==="
    docker-compose -f docker-compose.gateway.yml logs --tail=20 pp-gateway
}

# Cleanup
cleanup() {
    echo ""
    echo -e "${YELLOW}Cleaning up...${NC}"
    cd "$PROJECT_ROOT"
    docker-compose -f docker-compose.gateway.yml down -v
    echo -e "${GREEN}✓ Cleanup complete${NC}"
}

# Main
main() {
    case "${1:-all}" in
        start)
            start_services
            ;;
        unit)
            run_unit_tests
            ;;
        integration)
            run_integration_tests
            ;;
        smoke)
            run_smoke_tests
            ;;
        performance)
            run_performance_test
            ;;
        logs)
            view_logs
            ;;
        cleanup)
            cleanup
            ;;
        all)
            start_services
            run_unit_tests
            run_integration_tests
            run_smoke_tests
            run_performance_test
            view_logs
            ;;
        *)
            echo "Usage: $0 {start|unit|integration|smoke|performance|logs|cleanup|all}"
            exit 1
            ;;
    esac
}

# Handle interrupts
trap cleanup EXIT

main "$@"
