#!/usr/bin/env bash
# Static analysis pipeline for all Python services
set -euo pipefail

DC="docker compose -f docker-compose.test.yml"
REPORTS_DIR="tests/security/reports"
mkdir -p "$REPORTS_DIR"

echo "=== Ruff lint ==="
$DC run --no-deps plant-backend-test ruff check /app --output-format json > "$REPORTS_DIR/ruff-plant.json" || true
$DC run --no-deps cp-backend-test ruff check /app --output-format json > "$REPORTS_DIR/ruff-cp.json" || true
$DC run --no-deps pp-backend-test ruff check /app --output-format json > "$REPORTS_DIR/ruff-pp.json" || true

echo "=== Mypy type check ==="
$DC run --no-deps plant-backend-test mypy /app --ignore-missing-imports --no-error-summary || true
$DC run --no-deps cp-backend-test mypy /app --ignore-missing-imports --no-error-summary || true

echo "=== Bandit SAST ==="
$DC run --no-deps plant-backend-test bandit -r /app -f json \
  -o /app/tests/static/bandit-plant.json --exit-zero || true
$DC run --no-deps cp-backend-test bandit -r /app -f json \
  -o /app/tests/static/bandit-cp.json --exit-zero || true
$DC run --no-deps pp-backend-test bandit -r /app -f json \
  -o /app/tests/static/bandit-pp.json --exit-zero || true

echo "=== Safety dependency scan ==="
$DC run --no-deps plant-backend-test safety check --json > "$REPORTS_DIR/safety-plant.json" || true
$DC run --no-deps cp-backend-test safety check --json > "$REPORTS_DIR/safety-cp.json" || true
$DC run --no-deps pp-backend-test safety check --json > "$REPORTS_DIR/safety-pp.json" || true

echo "=== Static analysis complete. Reports in $REPORTS_DIR ==="
