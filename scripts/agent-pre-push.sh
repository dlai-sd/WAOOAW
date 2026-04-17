#!/usr/bin/env bash
# =============================================================================
# agent-pre-push.sh — Pre-push checks that agents CAN run without Docker
#
# PURPOSE: Catch the CI failures that agents introduce but cannot detect because
#          they cannot run Docker test containers. Run this before every push.
#
# USAGE:
#   bash scripts/agent-pre-push.sh              # check everything
#   bash scripts/agent-pre-push.sh --skip-audit # skip pip-audit (slow first run)
#
# WHAT THIS CHECKS (no Docker required):
#   1. Python dep pinning  — no >= ~= ^= in requirements.txt files
#   2. pip-audit CVE scan  — authlib, starlette, etc. (takes ~30s on first run)
#   3. TypeScript tsc      — zero type errors in src/mobile
#   4. ESLint              — zero lint errors in src/mobile
#   5. YAML workflow lint  — detect broken CI YAML before it fails in GitHub
#
# WHAT THIS DOES NOT CHECK (needs Docker):
#   - Python unit tests + coverage gate  → CI will catch; note in PR body
#   - Smoke routes (live demo)           → CI will catch; note in PR body
#
# Exit code: 0 = all checks passed, 1 = any check failed
# =============================================================================
set -euo pipefail

SKIP_AUDIT=false
for arg in "$@"; do
  [[ "$arg" == "--skip-audit" ]] && SKIP_AUDIT=true
done

PASS=0
FAIL=0
WARN=0
ERRORS=()

log_ok()   { echo -e "\033[0;32m[OK]\033[0m   $*"; ((PASS++)) || true; }
log_fail() { echo -e "\033[0;31m[FAIL]\033[0m $*"; ERRORS+=("$*"); ((FAIL++)) || true; }
log_warn() { echo -e "\033[1;33m[WARN]\033[0m $*"; ((WARN++)) || true; }
log_info() { echo -e "       $*"; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo ""
echo "WAOOAW Agent Pre-Push Checks"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ─── 1. Python dep pinning ────────────────────────────────────────────────────
echo "1. Python dependency pinning"
REQ_FILES=(
  "src/CP/BackEnd/requirements.txt"
  "src/Plant/BackEnd/requirements.txt"
  "src/Plant/Gateway/requirements.txt"
  "src/PP/BackEnd/requirements.txt"
)
for f in "${REQ_FILES[@]}"; do
  if [[ ! -f "$f" ]]; then
    log_warn "$f not found — skipping"
    continue
  fi
  if grep -Eq "[>~^]=" "$f"; then
    log_fail "$f has unpinned specifiers (>=, ~=, ^=):"
    grep -E "[>~^]=" "$f" | while read -r line; do log_info "  $line"; done
  else
    log_ok   "$f — all deps pinned"
  fi
done
echo ""

# ─── 2. pip-audit CVE scan ────────────────────────────────────────────────────
echo "2. pip-audit CVE scan"
if [[ "$SKIP_AUDIT" == "true" ]]; then
  log_warn "Skipped (--skip-audit flag set). Run without flag before merging."
elif ! command -v pip-audit &>/dev/null; then
  log_warn "pip-audit not installed. Run: pip install pip-audit"
  log_warn "Skipping CVE scan — CI will catch any new vulnerabilities."
else
  # Use same ignore list as CI (keep in sync with .github/workflows/waooaw-ci.yml)
  IGNORE_FLAGS=(
    "--ignore-vuln" "CVE-2024-23342"   # ecdsa transitive — no fix
    "--ignore-vuln" "CVE-2025-62727"   # starlette — tracked for pydantic upgrade
    "--ignore-vuln" "CVE-2026-4539"    # pygments ReDoS — no fix yet
  )
  AUDIT_FAILED=false
  for f in "${REQ_FILES[@]}"; do
    [[ ! -f "$f" ]] && continue
    if pip-audit -r "$f" --desc on "${IGNORE_FLAGS[@]}" -q 2>&1 | grep -qE "^(Found|Name)"; then
      log_fail "$f — known CVE found (see above). Fix before pushing."
      AUDIT_FAILED=true
    else
      log_ok   "$f — no actionable CVEs"
    fi
  done
  if [[ "$AUDIT_FAILED" == "true" ]]; then
    log_info "Tip: check https://pypi.org/project/<package>/ for the fixed version"
    log_info "     then pin to that exact version in requirements.txt"
  fi
fi
echo ""

# ─── 3. TypeScript type check ─────────────────────────────────────────────────
echo "3. TypeScript type check (src/mobile)"
if [[ ! -d "src/mobile" ]]; then
  log_warn "src/mobile not found — skipping TypeScript check"
elif ! command -v node &>/dev/null; then
  log_warn "node not found — skipping TypeScript check"
elif [[ ! -f "src/mobile/node_modules/.bin/tsc" ]]; then
  log_warn "node_modules not installed. Run: cd src/mobile && npm ci"
  log_warn "Skipping TypeScript check."
else
  if (cd src/mobile && npx tsc --noEmit 2>&1); then
    log_ok "TypeScript — 0 type errors"
  else
    log_fail "TypeScript — type errors found. Fix before pushing."
  fi
fi
echo ""

# ─── 4. ESLint ────────────────────────────────────────────────────────────────
echo "4. ESLint (src/mobile)"
if [[ ! -d "src/mobile" ]]; then
  log_warn "src/mobile not found — skipping ESLint"
elif [[ ! -f "src/mobile/node_modules/.bin/eslint" ]]; then
  log_warn "node_modules not installed — skipping ESLint"
else
  if (cd src/mobile && npm run lint -- --max-warnings=0 2>&1); then
    log_ok "ESLint — 0 errors"
  else
    log_fail "ESLint — lint errors found. Fix before pushing."
  fi
fi
echo ""

# ─── 5. Workflow YAML syntax ──────────────────────────────────────────────────
echo "5. Workflow YAML syntax (.github/workflows/)"
if ! command -v python3 &>/dev/null; then
  log_warn "python3 not found — skipping YAML check"
else
  YAML_OK=true
  for wf in .github/workflows/*.yml .github/workflows/*.yaml; do
    [[ ! -f "$wf" ]] && continue
    if python3 -c "import yaml,sys; yaml.safe_load(open('$wf'))" 2>&1; then
      log_ok "$wf — valid YAML"
    else
      log_fail "$wf — invalid YAML syntax"
      YAML_OK=false
    fi
  done
fi
echo ""

# ─── Summary ──────────────────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "Results:  \033[0;32m${PASS} passed\033[0m  \033[0;31m${FAIL} failed\033[0m  \033[1;33m${WARN} warnings\033[0m"
echo ""

if [[ "${#ERRORS[@]}" -gt 0 ]]; then
  echo -e "\033[0;31mPRE-PUSH BLOCKED — fix the following before pushing:\033[0m"
  for err in "${ERRORS[@]}"; do
    echo "  • $err"
  done
  echo ""
  echo "Note: Python coverage gate and smoke-route tests require Docker/live-demo"
  echo "      and will be caught by CI. Add a note in your PR body explaining"
  echo "      which coverage delta to expect."
  echo ""
  exit 1
fi

echo -e "\033[0;32mAll pre-push checks passed. Safe to push.\033[0m"
echo ""
echo "Reminder: CI will also run:"
echo "  • Python unit tests + 80% coverage gate (Docker)"
echo "  • Mobile route smoke test against live demo"
echo "  • Verify these pass too before requesting review."
echo ""
