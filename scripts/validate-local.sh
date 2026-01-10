#!/bin/bash
# Local validation script - Run the SAME checks as CI before committing
# This prevents "works locally, fails in CI" issues

set -e

echo "════════════════════════════════════════════════════════════"
echo "🔍 LOCAL VALIDATION - Running CI checks locally"
echo "════════════════════════════════════════════════════════════"

BACKEND_DIR="src/CP/BackEnd"
FRONTEND_DIR="src/CP/FrontEnd"
FAILED=0

# Backend checks
echo ""
echo "📦 BACKEND CHECKS"
echo "─────────────────────────────────────────────────────────────"

if [ -d "$BACKEND_DIR" ]; then
    cd "$BACKEND_DIR"
    
    echo "  1️⃣  Black formatting..."
    if black --check api core models 2>&1 | tee /tmp/black.log; then
        echo "      ✅ Black formatting passed"
    else
        echo "      ❌ Black formatting failed"
        echo "      💡 Fix: black api core models"
        FAILED=1
    fi
    
    echo ""
    echo "  2️⃣  Ruff linting..."
    if ruff check api core models --output-format=text 2>&1; then
        echo "      ✅ Ruff linting passed"
    else
        echo "      ❌ Ruff linting failed"
        echo "      💡 Fix: ruff check api core models --fix"
        FAILED=1
    fi
    
    echo ""
    echo "  3️⃣  Import sorting..."
    if isort --check-only api core models 2>&1; then
        echo "      ✅ Import sorting passed"
    else
        echo "      ❌ Import sorting failed"
        echo "      💡 Fix: isort api core models"
        FAILED=1
    fi
    
    echo ""
    echo "  4️⃣  Type checking..."
    if mypy api core models --ignore-missing-imports 2>&1; then
        echo "      ✅ Type checking passed"
    else
        echo "      ❌ Type checking failed"
        echo "      💡 Fix: Add type hints to fix errors"
        FAILED=1
    fi
    
    echo ""
    echo "  5️⃣  Running tests..."
    if pytest tests/ -v 2>&1 | tail -20; then
        echo "      ✅ Tests passed"
    else
        echo "      ❌ Tests failed"
        FAILED=1
    fi
    
    cd - > /dev/null
fi

# Frontend checks
echo ""
echo "🎨 FRONTEND CHECKS"
echo "─────────────────────────────────────────────────────────────"

if [ -d "$FRONTEND_DIR" ]; then
    cd "$FRONTEND_DIR"
    
    echo "  1️⃣  ESLint..."
    if npm run lint 2>&1; then
        echo "      ✅ ESLint passed"
    else
        echo "      ❌ ESLint failed"
        echo "      💡 Fix: npm run lint:fix"
        FAILED=1
    fi
    
    echo ""
    echo "  2️⃣  TypeScript check..."
    if npx tsc --noEmit 2>&1; then
        echo "      ✅ TypeScript check passed"
    else
        echo "      ❌ TypeScript check failed"
        FAILED=1
    fi
    
    echo ""
    echo "  3️⃣  Running tests..."
    if npm test 2>&1 | tail -20; then
        echo "      ✅ Tests passed"
    else
        echo "      ❌ Tests failed"
        FAILED=1
    fi
    
    cd - > /dev/null
fi

echo ""
echo "════════════════════════════════════════════════════════════"
if [ $FAILED -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED - Ready to commit!"
    echo "════════════════════════════════════════════════════════════"
    exit 0
else
    echo "❌ SOME CHECKS FAILED - Fix issues before committing"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "💡 Quick fixes:"
    echo "   Backend:  cd $BACKEND_DIR && black api core models && isort api core models"
    echo "   Frontend: cd $FRONTEND_DIR && npm run lint:fix"
    echo ""
    exit 1
fi
