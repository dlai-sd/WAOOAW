#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/smoke_deploy_agent.sh --epic-number <N> --epic-branch <branch>

What it does:
  - Fetches and checks out the epic branch
  - Overlays scripts/deploy_agent.py from origin/main (so you test the latest agent logic)
  - Runs the Deploy Agent (expects GITHUB_TOKEN to be set)

Required env:
  - (Either) GITHUB_TOKEN: token that can read PRs and comment on issues in the repo
  - (Or) be already authenticated via `gh auth login`

Optional env:
  - GITHUB_REPOSITORY: e.g. dlai-sd/WAOOAW (auto-detected from origin remote if missing)

Example:
  export GITHUB_TOKEN=...
  scripts/smoke_deploy_agent.sh --epic-number 439 --epic-branch epic-439-foo
EOF
}

epic_number=""
epic_branch=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --epic-number)
      epic_number="${2:-}"; shift 2 ;;
    --epic-branch)
      epic_branch="${2:-}"; shift 2 ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "[smoke] Unknown arg: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ -z "$epic_number" || -z "$epic_branch" ]]; then
  echo "[smoke] Missing required args." >&2
  usage
  exit 2
fi

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  # Allow using existing gh auth to avoid requiring manual token export.
  if ! gh auth status >/dev/null 2>&1; then
    echo "[smoke] No GITHUB_TOKEN set and gh is not authenticated." >&2
    echo "[smoke] Fix: either export GITHUB_TOKEN=... or run 'gh auth login' once." >&2
    exit 2
  fi
fi

infer_repo() {
  local url
  url="$(git config --get remote.origin.url || true)"
  # Supports:
  # - https://github.com/OWNER/REPO.git
  # - git@github.com:OWNER/REPO.git
  if [[ "$url" =~ github.com[:/]+([^/]+)/([^/.]+)(\.git)?$ ]]; then
    echo "${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
    return 0
  fi
  return 1
}

if [[ -z "${GITHUB_REPOSITORY:-}" ]]; then
  if repo="$(infer_repo)"; then
    export GITHUB_REPOSITORY="$repo"
  fi
fi

starting_ref="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
starting_sha="$(git rev-parse HEAD 2>/dev/null || true)"

cleanup() {
  # Best-effort restore.
  if [[ -n "$starting_ref" && "$starting_ref" != "HEAD" ]]; then
    git checkout -q "$starting_ref" 2>/dev/null || true
    git reset --hard -q "$starting_sha" 2>/dev/null || true
  fi
}
trap cleanup EXIT

echo "[smoke] Repo: ${GITHUB_REPOSITORY:-<unknown>}"
echo "[smoke] Epic: #$epic_number"
echo "[smoke] Branch: $epic_branch"

echo "[smoke] Fetch + checkout epic branch"
git fetch origin "$epic_branch"
git checkout -q "$epic_branch"

echo "[smoke] Overlay latest Deploy Agent from origin/main"
git fetch origin main
git checkout origin/main -- scripts/deploy_agent.py

echo "[smoke] Run Deploy Agent"
python scripts/deploy_agent.py \
  --epic-number "$epic_number" \
  --epic-branch "$epic_branch"

echo "[smoke] ✅ Success"
