#!/usr/bin/env bash
# scripts/test-mobile.sh — Local mobile test runner
# Usage: bash scripts/test-mobile.sh [--quick]
#   --quick  Skip E2E and mutation stages
# All commands run via docker compose — no host node/npm required.
set -euo pipefail

QUICK=${1:-""}
DC="docker compose -f docker-compose.test.yml"
PASS=0
FAIL=0

run_stage() {
  local stage_name="$1"
  shift
  echo ""
  echo "=== [$stage_name] ==="
  if "$@"; then
    echo "✅ $stage_name PASSED"
    PASS=$((PASS + 1))
  else
    echo "❌ $stage_name FAILED"
    FAIL=$((FAIL + 1))
  fi
}

echo "========================================"
echo "  WAOOAW Mobile Test Runner"
echo "  Mode: $([ "$QUICK" = "--quick" ] && echo "quick" || echo "full")"
echo "========================================"

run_stage "M1: Mobile — unit + UI tests" \
  $DC run --rm mobile-test --runInBand --coverage --passWithNoTests

run_stage "M2: Mobile — accessibility tests" \
  $DC run --rm mobile-test --testPathPattern="accessibility" --runInBand --passWithNoTests

if [[ "$QUICK" != "--quick" ]]; then
  run_stage "M3: Mobile — E2E (Maestro)" \
    $DC run --rm maestro maestro test /tests/auth_otp.yaml

  run_stage "M4: Mobile — mutation testing (Stryker)" \
    $DC run --rm mobile-test npx stryker run
fi

echo ""
echo "========================================"
echo "  RESULTS: ${PASS} passed, ${FAIL} failed"
echo "========================================"

if [[ $FAIL -gt 0 ]]; then
  exit 1
fi
