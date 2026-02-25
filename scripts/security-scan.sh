#!/usr/bin/env bash
# Security scanning pipeline: Bandit + Safety + Semgrep for all Python services
set -euo pipefail

DC="docker compose -f docker-compose.test.yml"
REPORTS_DIR="tests/security/reports"
mkdir -p "$REPORTS_DIR"

echo "=== Bandit SAST ==="
$DC run --no-deps plant-backend-test bandit -r /app -f json \
  -o /app/tests/static/bandit-plant.json --exit-zero || true
$DC run --no-deps cp-backend-test bandit -r /app -f json \
  -o /app/tests/static/bandit-cp.json --exit-zero || true
$DC run --no-deps pp-backend-test bandit -r /app -f json \
  -o /app/tests/static/bandit-pp.json --exit-zero || true

# Copy bandit reports to shared reports dir
cp -f src/Plant/BackEnd/tests/static/bandit-plant.json "$REPORTS_DIR/bandit-plant.json" 2>/dev/null || true
cp -f src/CP/BackEnd/tests/static/bandit-cp.json "$REPORTS_DIR/bandit-cp.json" 2>/dev/null || true
cp -f src/PP/BackEnd/tests/static/bandit-pp.json "$REPORTS_DIR/bandit-pp.json" 2>/dev/null || true

echo "=== Safety dependency scan ==="
$DC run --no-deps plant-backend-test safety check --json > "$REPORTS_DIR/safety-plant.json" || true
$DC run --no-deps cp-backend-test safety check --json > "$REPORTS_DIR/safety-cp.json" || true
$DC run --no-deps pp-backend-test safety check --json > "$REPORTS_DIR/safety-pp.json" || true

echo "=== Semgrep SAST ==="
docker run --rm \
  -v "$(pwd):/src" \
  returntocorp/semgrep \
  semgrep scan --config auto --json /src/src > "$REPORTS_DIR/semgrep.json" || true

echo "=== Security scans complete. Reports in $REPORTS_DIR ==="
