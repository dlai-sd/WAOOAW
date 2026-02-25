#!/usr/bin/env bash
# Security scan script — Bandit, Safety, Semgrep via Docker
set -euo pipefail
DC="docker compose -f docker-compose.test.yml"
REPORT_DIR="tests/security/reports"
mkdir -p "$REPORT_DIR"

echo "=== [1/3] Bandit SAST ==="
for svc in plant-backend-test cp-backend-test pp-backend-test plant-gateway-test; do
  echo "-- Bandit: $svc --"
  $DC run "$svc" bandit -r /app \
    -f json \
    -o "/app/tests/static/bandit-report.json" \
    --severity-level high \
    --exit-zero || true
done

echo "=== [2/3] Safety dependency audit ==="
$DC run plant-backend-test safety check --output text || true
$DC run cp-backend-test safety check --output text || true

echo "=== [3/3] Semgrep SAST ==="
docker run --rm \
  -v "$(pwd)/src:/src" \
  returntocorp/semgrep:latest \
  semgrep --config=p/python --json \
  --output /src/semgrep-report.json \
  /src || true

echo "=== Security scan complete. Reports in $REPORT_DIR ==="
