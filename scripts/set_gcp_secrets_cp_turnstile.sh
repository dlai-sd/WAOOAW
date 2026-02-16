#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="waooaw-oauth"
SECRETS=("TURNSTILE_SITE_KEY" "TURNSTILE_SECRET_KEY")

usage() {
  cat <<'EOF'
Usage:
  ./scripts/set_gcp_secrets_cp_turnstile.sh [--project <gcp-project-id>] [--include-cp-registration-key]

Default behavior:
  Updates only TURNSTILE_SITE_KEY and TURNSTILE_SECRET_KEY.

Optional:
  --include-cp-registration-key  Also updates CP_REGISTRATION_KEY.

Notes:
  - Prompts are hidden (no echo).
  - The script never prints secret values.
  - Adds new Secret Manager versions; does not delete old versions.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)
      PROJECT_ID="${2:-}"
      shift 2
      ;;
    --include-cp-registration-key)
      SECRETS+=("CP_REGISTRATION_KEY")
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "ERROR: Missing required command: $1" >&2
    exit 1
  }
}

require_cmd gcloud
require_cmd wc

# Ensure gcloud is authenticated and the project is set.
gcloud config set project "$PROJECT_ID" >/dev/null

echo "Target GCP project: $PROJECT_ID"

# Show secret existence + latest version metadata (no secret values).
for s in "${SECRETS[@]}"; do
  echo "--- $s"
  gcloud secrets describe "$s" --format='value(name)' >/dev/null || {
    echo "ERROR: Secret $s does not exist in $PROJECT_ID" >&2
    exit 1
  }
  gcloud secrets versions describe latest --secret "$s" --format='value(state,name)' || true
  echo "Current latest byte count (value not shown): $(gcloud secrets versions access latest --secret "$s" | wc -c)"
  echo
done

echo "This will ADD a NEW VERSION for each secret (it will not delete old versions)."
read -r -p "Continue? (y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

echo
for s in "${SECRETS[@]}"; do
  # Hidden prompt for secret input.
  read -r -s -p "$s (input hidden): " value
  echo

  if [[ -z "${value}" ]]; then
    echo "ERROR: $s was empty; refusing to write." >&2
    exit 1
  fi

  # Write a new version without printing the secret.
  printf %s "$value" | gcloud secrets versions add "$s" --data-file=- >/dev/null
  unset value

  echo "Wrote new version for $s."
  gcloud secrets versions describe latest --secret "$s" --format='value(state,name)'
  echo "New latest byte count (value not shown): $(gcloud secrets versions access latest --secret "$s" | wc -c)"
  echo
done

echo "Done. Next: redeploy/restart services that consume these secrets."
