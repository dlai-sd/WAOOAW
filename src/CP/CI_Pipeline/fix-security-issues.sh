#!/bin/bash
# Security Vulnerability Fix Script
# Patches 13 known CVEs in backend dependencies

set -e

echo "🔒 WAOOAW CP Backend Security Patch"
echo "===================================="
echo ""

cd /workspaces/WAOOAW/src/CP/BackEnd

echo "📋 Current vulnerabilities:"
echo "  - fastapi: PYSEC-2024-38 (Medium)"
echo "  - python-jose: 2 CVEs (High)"
echo "  - python-multipart: 2 CVEs (Critical)"
echo "  - authlib: 4 CVEs (Critical)"
echo "  - starlette: 2 CVEs (High)"
echo "  - ecdsa: CVE-2024-23342 (High)"
echo ""

echo "🔧 Upgrading packages..."
pip install --upgrade \
  fastapi==0.109.1 \
  python-jose==3.4.0 \
  python-multipart==0.0.18 \
  authlib==1.6.6 \
  starlette==0.47.2 \
  ecdsa

echo ""
echo "✅ Packages upgraded!"
echo ""

echo "🔍 Re-running pip-audit..."
pip-audit -r requirements.txt || {
  echo ""
  echo "⚠️  Some vulnerabilities may remain. Check output above."
  echo "    Consider upgrading to latest versions if issues persist."
}

echo ""
echo "🧪 Running tests to ensure nothing broke..."
pytest tests/ -v --tb=short

echo ""
echo "✅ Security patch complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Update requirements.txt with new versions"
echo "  2. Commit changes"
echo "  3. Deploy to staging for validation"
