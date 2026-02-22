#!/bin/bash
# Quick development server for GitHub Codespaces
# Starts Expo with tunnel for mobile device testing

set -e

echo "🚀 Starting WAOOAW Mobile App in Codespaces..."
echo ""

# Check if running in Codespace
if [ -n "$CODESPACE_NAME" ]; then
    echo "✅ Running in GitHub Codespace: $CODESPACE_NAME"
    echo ""
fi

cd "$(dirname "$0")"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start Expo with tunnel (works in Codespaces)
echo "🌐 Starting Expo with tunnel mode..."
echo "📱 Scan QR code with Expo Go app to test on your phone"
echo ""

npx expo start --tunnel --port 8081
