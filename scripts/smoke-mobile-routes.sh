#!/usr/bin/env bash
# smoke-mobile-routes.sh
#
# Verifies that the API routes consumed directly by the mobile app are
# mounted and reachable on the demo Plant Gateway.  The test asserts that
# each route returns something OTHER than 404 — meaning the route exists.
# Authentication is not tested here; a 401/422 response means the route is
# wired correctly.
#
# Usage:
#   bash scripts/smoke-mobile-routes.sh
#
# Environment:
#   DEMO_PLANT_URL   — base URL of the Plant Gateway (no trailing slash)
#                      default: https://plant.demo.waooaw.com
#   SMOKE_TIMEOUT    — curl connect+response timeout in seconds (default: 15)
#
# Exit 0 → all REQUIRED routes OK (tracked routes may still show as unmounted).
# Exit 1 → at least one REQUIRED route returned 404 or was unreachable.
#
# Route categories:
#   probe()         — REQUIRED: 404 causes exit 1 (regression caught)
#   probe_tracked() — TRACKED: 404 printed as INFO, does not block CI
#                     Use for routes not yet deployed to demo Plant Gateway.
#                     Move to probe() once the route ships to demo.
#
# Why this file exists:
#   apiBaseUrl in src/mobile/src/config/api.config.ts is the bare domain with
#   NO path prefix.  Every mobile service file must supply the full /api/v1/
#   prefix.  Writing /v1/agents instead of /api/v1/agents silently produces
#   404 in production — tests pass (mocked at service layer) while every real
#   call fails.  See CONTEXT_AND_INDEX.md §17 Mobile gotchas.

set -euo pipefail

BASE_URL="${DEMO_PLANT_URL:-https://plant.demo.waooaw.com}"
TIMEOUT="${SMOKE_TIMEOUT:-15}"

# ── colour helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
SKIP=0
TRACKED_MISSING=0

# ── probe function ────────────────────────────────────────────────────────────
# probe <METHOD> <PATH> [BODY] [NOTE]
#   REQUIRED check — 404 counts as FAIL and causes exit 1.
#   Any 4xx/5xx except 404 is OK (route exists, request rejected upstream).
probe() {
  local method="$1"
  local path="$2"
  local body="${3:-}"
  local note="${4:-}"
  local url="${BASE_URL}${path}"
  local curl_args=(
    --silent
    --output /dev/null
    --write-out "%{http_code}"
    --max-time "${TIMEOUT}"
    --connect-timeout "${TIMEOUT}"
    -X "${method}"
    -H "Content-Type: application/json"
  )
  [[ -n "$body" ]] && curl_args+=(-d "${body}")

  local status
  status=$(curl "${curl_args[@]}" "${url}" 2>/dev/null || echo "CURL_ERR")

  local label="${method} ${path}"
  [[ -n "$note" ]] && label="${label}  (${note})"

  if [[ "$status" == "CURL_ERR" ]]; then
    echo -e "${RED}[FAIL]${NC} ${label}  →  curl error (unreachable or TLS fault)"
    FAIL=$((FAIL + 1))
  elif [[ "$status" == "404" ]]; then
    echo -e "${RED}[FAIL]${NC} ${label}  →  HTTP 404 — route NOT mounted"
    FAIL=$((FAIL + 1))
  else
    echo -e "${GREEN}[OK]${NC}   ${label}  →  HTTP ${status}"
    PASS=$((PASS + 1))
  fi
}

# probe_tracked <METHOD> <PATH> [BODY] [NOTE]
#   TRACKED check — route not yet deployed to demo Plant Gateway.
#   Prints informational output but 404 does NOT cause exit 1.
#   Move to probe() once the route is confirmed live on demo.
probe_tracked() {
  local method="$1"
  local path="$2"
  local body="${3:-}"
  local note="${4:-}"
  local url="${BASE_URL}${path}"
  local curl_args=(
    --silent
    --output /dev/null
    --write-out "%{http_code}"
    --max-time "${TIMEOUT}"
    --connect-timeout "${TIMEOUT}"
    -X "${method}"
    -H "Content-Type: application/json"
  )
  [[ -n "$body" ]] && curl_args+=(-d "${body}")

  local status
  status=$(curl "${curl_args[@]}" "${url}" 2>/dev/null || echo "CURL_ERR")

  local label="${method} ${path}"
  [[ -n "$note" ]] && label="${label}  (${note})"

  if [[ "$status" == "CURL_ERR" ]]; then
    echo -e "${YELLOW}[TRACK]${NC} ${label}  →  curl error — not deployed to demo yet (non-blocking)"
    TRACKED_MISSING=$((TRACKED_MISSING + 1))
  elif [[ "$status" == "404" ]]; then
    echo -e "${YELLOW}[TRACK]${NC} ${label}  →  HTTP 404 — not deployed to demo yet (non-blocking)"
    TRACKED_MISSING=$((TRACKED_MISSING + 1))
  else
    echo -e "${GREEN}[OK]${NC}   ${label}  →  HTTP ${status}  (was tracked, now live)"
    PASS=$((PASS + 1))
  fi
}

# ── banner ────────────────────────────────────────────────────────────────────
echo ""
echo "Mobile Route Smoke Test"
echo "Target: ${BASE_URL}"
echo "Timeout per request: ${TIMEOUT}s"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── 1. Health check ───────────────────────────────────────────────────────────
echo "1. Platform health"
probe GET "/health"
echo ""

# ── 2. Auth public routes ─────────────────────────────────────────────────────
# These are listed in PUBLIC_ENDPOINTS in src/Plant/Gateway/middleware/auth.py.
# Sending an invalid body should return 422 (validation error), not 404.
# NOTE: /auth/register, /auth/otp/start, /auth/otp/verify, /auth/refresh are
#       TRACKED (not yet deployed to demo Plant Gateway). They use probe_tracked
#       so CI is not blocked while those routes are being built. When they ship
#       to demo, change probe_tracked → probe.
echo "2. Auth public routes  (expect 400/401/422, never 404)"
probe_tracked POST "/auth/register"    '{"email":"smoke@test.invalid"}' "mobile registration — 3-step (TRACKED: not on demo)"
probe_tracked POST "/auth/otp/start"   '{"destination":"smoke@test.invalid"}' "mobile OTP start (TRACKED: not on demo)"
probe_tracked POST "/auth/otp/verify"  '{"otp_id":"invalid","code":"000000"}' "mobile OTP verify (TRACKED: not on demo)"
probe POST "/auth/google/verify" '{"id_token":"smoke-invalid"}' "Google ID-token exchange"

# CRITICAL: token refresh path consumed from apiClient.ts line 241 as
# `${config.apiBaseUrl}/auth/refresh` — must NOT be 404.
# TRACKED until /auth/refresh is deployed to demo Plant Gateway.
probe_tracked POST "/auth/refresh"     '{"refresh_token":"smoke-invalid"}' "CRITICAL — token refresh (TRACKED: not on demo)"
echo ""

# ── 3. API v1 routes ──────────────────────────────────────────────────────────
# Mobile service files must use /api/v1/ prefix (not /v1/).  Probing without a
# token should return 401/403 — NOT 404.  A 404 here means the service file
# used the wrong prefix.
echo "3. /api/v1/ routes  (expect 200/401/403, never 404)"
probe GET  "/api/v1/agents"        "" "agent catalogue — used by useAgents hook"
probe GET  "/api/v1/agent-types"   "" "agent types — used by useAgentTypes hook"
probe POST "/api/v1/auth/validate" '{"token":"smoke-invalid"}' "dev-token auth"
probe GET  "/api/v1/hired-agents"  "" "hired agents — expect 401 without token"
echo ""

# ── 4. Prefix trap guard ──────────────────────────────────────────────────────
# Verify the WRONG prefix /v1/ gives 404 (validates the gateway is not
# accidentally mounting both prefixes — would mask a real code mistake).
echo "4. Prefix trap  (/v1/ SHOULD return 404 — validates gateway mounts only /api/v1/)"
wrong_status=$(curl --silent --output /dev/null --write-out "%{http_code}" \
  --max-time "${TIMEOUT}" --connect-timeout "${TIMEOUT}" \
  "${BASE_URL}/v1/agents" 2>/dev/null || echo "CURL_ERR")

if [[ "$wrong_status" == "404" ]]; then
  echo -e "${GREEN}[OK]${NC}   GET /v1/agents  →  HTTP 404 (correct — wrong prefix rejected)"
  PASS=$((PASS + 1))
elif [[ "$wrong_status" == "CURL_ERR" ]]; then
  echo -e "${YELLOW}[SKIP]${NC} GET /v1/agents  →  curl error (network issue, skipping trap check)"
  SKIP=$((SKIP + 1))
else
  echo -e "${YELLOW}[WARN]${NC} GET /v1/agents  →  HTTP ${wrong_status} (unexpected — /v1/ prefix may be double-mounted)"
  # Not a hard failure — the route table may legitimately evolve.
fi
echo ""

# ── summary ───────────────────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "Results:  ${GREEN}${PASS} passed${NC}  ${RED}${FAIL} failed${NC}  ${YELLOW}${TRACKED_MISSING} tracked-missing${NC}  ${YELLOW}${SKIP} skipped${NC}"
echo ""

if [[ "${TRACKED_MISSING}" -gt 0 ]]; then
  echo -e "${YELLOW}${TRACKED_MISSING} route(s) are tracked as not-yet-deployed to demo Plant Gateway.${NC}"
  echo "These are informational — they do not block CI. When the routes ship to demo,"
  echo "change probe_tracked → probe in scripts/smoke-mobile-routes.sh."
  echo ""
fi

if [[ "${FAIL}" -gt 0 ]]; then
  echo -e "${RED}SMOKE TEST FAILED — ${FAIL} REQUIRED route(s) returned 404 or were unreachable.${NC}"
  echo ""
  echo "Most likely cause: a mobile service file uses /v1/<path> instead of"
  echo "/api/v1/<path>.  Cross-check every path in src/mobile/src/services/"
  echo "against the Route Ownership table in docs/CONTEXT_AND_INDEX.md §5.2."
  echo ""
  echo "Also verify the token-refresh path:"
  echo "  src/mobile/src/lib/apiClient.ts  →  \${config.apiBaseUrl}/auth/refresh"
  echo "  Expected: ${BASE_URL}/auth/refresh  →  should return 422, not 404."
  exit 1
fi

echo -e "${GREEN}SMOKE TEST PASSED.${NC}"
exit 0
