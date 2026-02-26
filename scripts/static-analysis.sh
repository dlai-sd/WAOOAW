#!/usr/bin/env bash
set -euo pipefail
DC="docker compose -f docker-compose.test.yml"
echo "=== Ruff ==="
$DC run plant-backend-test ruff check /app || true
$DC run cp-backend-test ruff check /app || true
$DC run pp-backend-test ruff check /app || true
$DC run plant-gateway-test ruff check /app || true
echo "=== Mypy ==="
$DC run plant-backend-test mypy /app --ignore-missing-imports || true
$DC run cp-backend-test mypy /app --ignore-missing-imports || true
echo "=== Bandit ==="
$DC run plant-backend-test bandit -r /app -f json -o /app/tests/static/bandit-baseline.json --exit-zero
$DC run cp-backend-test bandit -r /app -f json -o /app/tests/static/bandit-baseline.json --exit-zero
$DC run pp-backend-test bandit -r /app -f json -o /app/tests/static/bandit-baseline.json --exit-zero
$DC run plant-gateway-test bandit -r /app -f json -o /app/tests/static/bandit-baseline.json --exit-zero
echo "=== Safety ==="
$DC run plant-backend-test safety check || true
echo "=== DONE ==="
