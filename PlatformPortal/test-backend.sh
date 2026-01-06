#!/bin/bash
# Quick test script for Platform Portal OAuth backend

echo "Testing Platform Portal Backend..."

# Test root endpoint
echo ""
echo "1. Testing root endpoint (/):"
curl -s http://localhost:8000/ | python3 -m json.tool

# Test health endpoint
echo ""
echo "2. Testing health endpoint (/health):"
curl -s http://localhost:8000/health | python3 -m json.tool

# Test OAuth endpoints (should get redirects)
echo ""
echo "3. Testing OAuth login endpoint (should redirect to Google):"
curl -I -s http://localhost:8000/auth/login | head -n 1

echo ""
echo "✅ Backend tests complete!"
echo ""
echo "To test full OAuth flow:"
echo "1. Make sure backend is running on port 8000"
echo "2. Start Reflex: cd /workspaces/WAOOAW/PlatformPortal && reflex run"
echo "3. Open frontend URL in browser"
echo "4. Click 'Sign in with Google' button"
