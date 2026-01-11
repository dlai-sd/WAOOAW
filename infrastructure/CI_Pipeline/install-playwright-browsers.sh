#!/bin/bash
# Install all Playwright browsers for cross-browser testing

set -e

echo "🎭 WAOOAW CP Playwright Browser Installation"
echo "============================================"
echo ""

cd /workspaces/WAOOAW/src/CP/FrontEnd

echo "📦 Current status:"
npx playwright --version

echo ""
echo "🔧 Installing browsers..."
echo "  - Chromium (already installed)"
echo "  - Firefox"
echo "  - WebKit (Safari)"
echo "  - Including system dependencies"
echo ""

npx playwright install --with-deps

echo ""
echo "✅ All browsers installed!"
echo ""

echo "🧪 Running smoke test..."
npx playwright test e2e/app.spec.ts --project=chromium --grep "should load landing page"

echo ""
echo "✅ Installation complete!"
echo ""
echo "📊 Expected test results:"
echo "  - 70 tests across 7 browser configurations"
echo "  - Target: >95% pass rate"
echo ""
echo "📝 Run full test suite:"
echo "  npx playwright test"
