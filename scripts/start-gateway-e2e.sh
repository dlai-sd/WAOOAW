#!/bin/bash
# Start gateway for E2E testing

# Source environment
source .env.gateway

# Export configuration
export GATEWAY_URL=http://localhost:8000
export PLANT_URL=http://localhost:8001
export REDIS_URL=redis://localhost:6380/0
export OPA_URL=http://localhost:8181
export JWT_PUBLIC_KEY="$JWT_PUBLIC_KEY"
export JWT_PRIVATE_KEY="$JWT_PRIVATE_KEY"

# Start gateway
cd /workspaces/WAOOAW
python -m uvicorn gateway.main:app --host 0.0.0.0 --port 8000 --reload &

GATEWAY_PID=$!
echo "Gateway started with PID: $GATEWAY_PID"

# Wait for gateway to be ready
sleep 3
curl -s http://localhost:8000/health

echo "Gateway ready for E2E testing"
