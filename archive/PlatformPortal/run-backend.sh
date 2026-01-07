#!/bin/bash
# Run Platform Portal Backend with OAuth

cd /workspaces/WAOOAW/PlatformPortal

# Load environment variables
export GOOGLE_CLIENT_ID="${GOOGLE_CLIENT_ID}"
export GOOGLE_CLIENT_SECRET="${GOOGLE_CLIENT_SECRET}"
export ENV="${ENV:-codespace}"
export CODESPACE_NAME="${CODESPACE_NAME}"

echo "🚀 Starting Platform Portal Backend..."
echo "📍 Environment: $ENV"
echo "🔐 OAuth Configured: Yes"

# Start backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
