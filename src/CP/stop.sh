#!/bin/bash
# Stop Script for WAOOAW Customer Portal

echo "🛑 Stopping WAOOAW Customer Portal..."

# Kill by PID if available
if [ -f /tmp/waooaw_backend.pid ]; then
    PID=$(cat /tmp/waooaw_backend.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping backend (PID: $PID)..."
        kill $PID 2>/dev/null || true
    fi
    rm /tmp/waooaw_backend.pid
fi

# Fallback: kill by process name
pkill -f "uvicorn.*8000" 2>/dev/null || true
pkill -f "vite.*3001" 2>/dev/null || true

sleep 1

echo "✅ All processes stopped"
