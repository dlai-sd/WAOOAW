#!/bin/bash
# Start Platform Portal with backend OAuth support

set -e

echo "🚀 Starting WAOOAW Platform Portal..."

# Navigate to PlatformPortal directory
cd /workspaces/WAOOAW/PlatformPortal

# Activate virtual environment
if [ -f "../.venv/bin/activate" ]; then
    source ../.venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  No virtual environment found, using system Python"
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

# Start backend API in background
echo "🔧 Starting FastAPI backend on port 8000..."
cd /workspaces/WAOOAW/PlatformPortal
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 3

# Check backend health
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ Backend is healthy"
else
    echo "⚠️  Backend health check failed, but continuing..."
fi

# Start Reflex frontend
echo "🎨 Starting Reflex frontend on port 3001..."
cd /workspaces/WAOOAW/PlatformPortal
reflex run --loglevel info

# Cleanup on exit
trap "kill $BACKEND_PID 2>/dev/null" EXIT
