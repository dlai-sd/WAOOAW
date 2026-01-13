#!/bin/bash
# Local validation script - Run the SAME checks as CI before committing
# This prevents "works locally, fails in CI" issues

set -euo pipefail

echo "════════════════════════════════════════════════════════════"
echo "🔍 LOCAL VALIDATION - Running CI checks locally"
echo "════════════════════════════════════════════════════════════"

BACKEND_DIR="src/CP/BackEnd"
FRONTEND_DIR="src/CP/FrontEnd"
FAILED=0

WORKSPACE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${WORKSPACE_ROOT}/.venv/bin/python"

if [ -x "${PYTHON_BIN}" ]; then
    PYTHON="${PYTHON_BIN}"
else
    PYTHON="python3"
fi

run_or_fail() {
    local label="$1"
    shift
    local logfile="$1"
    shift

    if "$@" >"${logfile}" 2>&1; then
        return 0
    fi

    echo "      ❌ ${label} failed"
    echo "      ── last 80 lines ──"
    tail -80 "${logfile}" || true
    echo "      ───────────────────"
    return 1
}

# Backend checks
echo ""
echo "📦 BACKEND CHECKS"
echo "─────────────────────────────────────────────────────────────"

if [ -d "$BACKEND_DIR" ]; then
    cd "$BACKEND_DIR"
    
    echo "  1️⃣  Black formatting..."
    if run_or_fail "Black formatting" "/tmp/black.log" "$PYTHON" -m black --check api core models; then
        echo "      ✅ Black formatting passed"
    else
        echo "      💡 Fix: black api core models"
        FAILED=1
    fi
    
    echo ""
    echo "  2️⃣  Ruff linting..."
    if run_or_fail "Ruff lint" "/tmp/ruff.log" "$PYTHON" -m ruff check api core models --output-format=text; then
        echo "      ✅ Ruff linting passed"
    else
        echo "      💡 Fix: ruff check api core models --fix"
        FAILED=1
    fi
    
    echo ""
    echo "  3️⃣  Import sorting..."
    if run_or_fail "Isort" "/tmp/isort.log" "$PYTHON" -m isort --check-only api core models; then
        echo "      ✅ Import sorting passed"
    else
        echo "      💡 Fix: isort api core models"
        FAILED=1
    fi
    
    echo ""
    echo "  4️⃣  Type checking..."
    if run_or_fail "Mypy" "/tmp/mypy.log" "$PYTHON" -m mypy api core models --ignore-missing-imports; then
        echo "      ✅ Type checking passed"
    else
        echo "      💡 Fix: Add type hints to fix errors"
        FAILED=1
    fi
    
    echo ""
    echo "  5️⃣  Running tests..."
    if run_or_fail "Pytest" "/tmp/pytest.log" "$PYTHON" -m pytest tests/ -v; then
        echo "      ✅ Tests passed"
    else
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
    if run_or_fail "ESLint" "/tmp/eslint.log" npm run lint; then
        echo "      ✅ ESLint passed"
    else
        echo "      💡 Fix: npm run lint:fix"
        FAILED=1
    fi
    
    echo ""
    echo "  2️⃣  TypeScript check..."
    if run_or_fail "TypeScript check" "/tmp/tsc.log" npx tsc --noEmit; then
        echo "      ✅ TypeScript check passed"
    else
        FAILED=1
    fi
    
    echo ""
    echo "  3️⃣  Running tests..."
    if run_or_fail "Frontend tests" "/tmp/frontend-tests.log" npm run test -- --run; then
        echo "      ✅ Tests passed"
    else
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
