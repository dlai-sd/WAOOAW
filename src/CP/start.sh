#!/bin/bash
# Clean Start Script for WAOOAW Customer Portal
# Serves both frontend and backend on port 8000

set -e

echo "🧹 Cleaning up any existing processes..."
pkill -9 -f "uvicorn.*8000" 2>/dev/null || true
pkill -9 -f "vite.*3001" 2>/dev/null || true
sleep 1

echo "📦 Building frontend..."
cd /workspaces/WAOOAW/src/CP/FrontEnd
npm run build

echo "🚀 Starting backend server on port 8000..."
cd /workspaces/WAOOAW/src/CP/BackEnd
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > /tmp/waooaw.log 2>&1 &
BACKEND_PID=$!

# Save PID for stop script
echo $BACKEND_PID > /tmp/waooaw_backend.pid

# Give it a moment to start
sleep 2

echo "✅ Backend started (PID: $BACKEND_PID)"
echo "🌐 Application available at:"
echo "   https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev"
echo ""
echo "📊 API Docs:"
echo "   https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev/docs"
echo ""
echo "💡 To stop: ./stop.sh"
echo "📝 Logs: tail -f /tmp/waooaw.log"
