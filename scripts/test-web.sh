#!/usr/bin/env bash
# scripts/test-web.sh — Local web backend test runner
# Usage: bash scripts/test-web.sh [--quick]
#   --quick  Skip performance and DAST stages
# All commands run via docker compose — no host python/pip required.
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
echo "  WAOOAW Web Backend Test Runner"
echo "  Mode: $([ "$QUICK" = "--quick" ] && echo "quick" || echo "full")"
echo "========================================"

run_stage "S1: Plant BackEnd — ruff" \
  $DC run --rm plant-backend-test ruff check /app --no-fix

run_stage "S1: CP BackEnd — ruff" \
  $DC run --rm cp-backend-test ruff check /app --no-fix

run_stage "S1: PP BackEnd — ruff" \
  $DC run --rm pp-backend-test ruff check /app --no-fix

run_stage "S2: Plant BackEnd — unit + api tests" \
  $DC run --rm plant-backend-test -m "unit or api" --tb=short -q

run_stage "S2: CP BackEnd — unit + api tests" \
  $DC run --rm cp-backend-test -m "unit or api" --tb=short -q

run_stage "S2: PP BackEnd — unit + api tests" \
  $DC run --rm pp-backend-test -m "unit or api" --tb=short -q

run_stage "S2: Plant Gateway — unit tests" \
  $DC run --rm plant-gateway-test -m "unit or api" --tb=short -q

run_stage "S3: Plant BackEnd — integration tests" \
  $DC run --rm plant-backend-test -m integration --tb=short -q

run_stage "S4: Plant BackEnd — e2e tests" \
  $DC run --rm plant-backend-test -m e2e --tb=short -q

run_stage "S5: CP FrontEnd — Playwright hire journey" \
  docker run --rm -v "$PWD/src/CP/FrontEnd":/work -w /work mcr.microsoft.com/playwright:v1.57.0-noble \
    sh -lc "npm install --silent && npx playwright test e2e/hire-journey.spec.ts --project=chromium"

run_stage "S5: PP FrontEnd — Playwright operator smoke" \
  docker run --rm -v "$PWD/src/PP/FrontEnd":/work -w /work mcr.microsoft.com/playwright:v1.58.0-noble \
    sh -lc "npm install --silent && npx playwright test e2e/operator-smoke.spec.ts --project=chromium"

if [[ "$QUICK" != "--quick" ]]; then
  run_stage "S6: Performance — Locust load test" \
    $DC run --rm locust --headless -u 50 -r 5 --run-time 60s \
      --html /mnt/locust/reports/report.html

  run_stage "S7: Security — OWASP ZAP DAST" \
    $DC run --rm zap
fi

echo ""
echo "========================================"
echo "  RESULTS: ${PASS} passed, ${FAIL} failed"
echo "========================================"

if [[ $FAIL -gt 0 ]]; then
  exit 1
fi
