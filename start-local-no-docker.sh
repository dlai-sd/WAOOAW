#!/bin/bash
# Quick Start Script - No Docker (DEPRECATED)
# WAOOAW is Docker-first. This script is intentionally disabled.

set -e

echo "=== WAOOAW Local Setup (No Docker) ==="
echo ""
echo "This repository is Docker-first (Docker-only)."
echo "Use: docker compose -f docker-compose.local.yml up --build"
echo ""
exit 1

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Setup Plant Backend
echo "📦 Setting up Plant Backend..."
cd src/Plant/BackEnd

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   Created virtual environment"
fi

source venv/bin/activate
pip install -q -r requirements.txt
echo "   ✅ Dependencies installed"

# Use SQLite for testing (no PostgreSQL needed)
export DATABASE_URL="sqlite+aiosqlite:///./waooaw_test.db"
export REDIS_URL="redis://fake"  # Disable Redis
export PORT=8001
export ENVIRONMENT=development

echo "   Starting Plant Backend on port 8001..."
uvicorn main:app --host 127.0.0.1 --port 8001 --reload &
PLANT_PID=$!
sleep 3

cd ../../..

# Setup Plant Gateway
echo "📦 Setting up Plant Gateway..."
cd src/Plant/Gateway

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   Created virtual environment"
fi

source venv/bin/activate
pip install -q -r requirements.txt
echo "   ✅ Dependencies installed"

export PLANT_BACKEND_URL="http://127.0.0.1:8001"
export PORT=8000
export ENVIRONMENT=development

echo "   Starting Plant Gateway on port 8000..."
uvicorn main:app --host 127.0.0.1 --port 8000 --reload &
GATEWAY_PID=$!
sleep 3

cd ../../..

# Setup PP Backend
echo "📦 Setting up PP Backend..."
cd src/PP/BackEnd

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   Created virtual environment"
fi

source venv/bin/activate
pip install -q -r requirements.txt
echo "   ✅ Dependencies installed"

export DATABASE_URL="sqlite+aiosqlite:///./waooaw_test.db"
export REDIS_URL="redis://fake"
export PORT=8015
export PLANT_GATEWAY_URL="http://127.0.0.1:8000"
export ENVIRONMENT=development

echo "   Starting PP Backend on port 8015..."
uvicorn main:app --host 127.0.0.1 --port 8015 --reload &
PP_PID=$!
sleep 3

cd ../../..

echo ""
echo "==================================="
echo "✅ All services started!"
echo "==================================="
echo ""
echo "📍 URLs (open in browser):"
echo "   Plant Backend: http://localhost:8001/docs"
echo "   Plant Gateway: http://localhost:8000/docs"
echo "   PP Backend:    http://localhost:8015/docs"
echo ""
echo "🔍 Test Health:"
echo "   curl http://localhost:8001/health"
echo "   curl http://localhost:8000/health"
echo "   curl http://localhost:8015/health"
echo ""
echo "🛑 To stop all services:"
echo "   kill $PLANT_PID $GATEWAY_PID $PP_PID"
echo ""
echo "📝 Process IDs saved to .pids file"
echo "$PLANT_PID $GATEWAY_PID $PP_PID" > .pids

# Wait for user interrupt
echo "Press Ctrl+C to stop all services..."
wait
