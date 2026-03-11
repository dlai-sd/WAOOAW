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
RUN_NATIVE_E2E=${RUN_MOBILE_NATIVE_E2E:-""}

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
  if [[ -n "$RUN_NATIVE_E2E" ]]; then
    run_stage "M3: Mobile — E2E (Maestro auth)" \
      $DC run --rm maestro maestro test /tests/auth_otp.yaml

    run_stage "M3: Mobile — E2E (Maestro runtime re-entry)" \
      $DC run --rm maestro maestro test /tests/notification_runtime_reentry.yaml
  else
    echo ""
    echo "=== [M3: Mobile — E2E (Maestro)] ==="
    echo "↷ SKIPPED: native mobile E2E is opt-in only. Set RUN_MOBILE_NATIVE_E2E=1 when a real device/emulator target is available."
  fi

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
