#!/usr/bin/env bash

set -euo pipefail

TARGET_ENV="${WAOOAW_CLOUDSQL_ENV:-demo}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${REPO_ROOT}/.codespace/demo.env"
PROJECT_ID="${WAOOAW_GCP_PROJECT_ID:-waooaw-oauth}"
DATABASE_URL_SECRET="${WAOOAW_DB_URL_SECRET:-${TARGET_ENV}-plant-database-url}"
PROXY_PORT="${WAOOAW_CLOUDSQL_PROXY_PORT:-15432}"
DRY_RUN=false

for arg in "$@"; do
  case "$arg" in
    --dry-run)
      DRY_RUN=true
      ;;
    *)
      echo "Unsupported argument: $arg" >&2
      echo "Usage: $0 [--dry-run]" >&2
      exit 1
      ;;
  esac
done

mkdir -p "$(dirname "$ENV_FILE")"
chmod 700 "$(dirname "$ENV_FILE")"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_command gcloud
require_command python3

read_secret() {
  local secret_name="$1"
  gcloud secrets versions access latest \
    --secret="$secret_name" \
    --project="$PROJECT_ID"
}

normalize_database_url() {
  local raw_url="$1"
  DATABASE_URL="$raw_url" PROXY_PORT="$PROXY_PORT" python3 <<'PY'
import os
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

raw_url = os.environ["DATABASE_URL"]
proxy_port = os.environ["PROXY_PORT"]
parsed = urlparse(raw_url)
userinfo = parsed.netloc.rsplit("@", 1)[0] if "@" in parsed.netloc else ""
query_items = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k != "host"]
netloc = f"{userinfo}@host.docker.internal:{proxy_port}" if userinfo else f"host.docker.internal:{proxy_port}"
normalized = parsed._replace(netloc=netloc, query=urlencode(query_items))
print(urlunparse(normalized))
PY
}

SECRET_NAMES=(
  GOOGLE_CLIENT_ID
  GOOGLE_CLIENT_SECRET
  JWT_SECRET
  CP_REGISTRATION_KEY
  TURNSTILE_SECRET_KEY
  TURNSTILE_SITE_KEY
)

if [[ "$DRY_RUN" == "true" ]]; then
  echo "Dry run: would write ${ENV_FILE}"
  echo "Database URL secret: ${DATABASE_URL_SECRET}"
  printf 'Runtime secrets: %s\n' "${SECRET_NAMES[@]}"
  exit 0
fi

RAW_DATABASE_URL="$(read_secret "$DATABASE_URL_SECRET")"
NORMALIZED_DATABASE_URL="$(normalize_database_url "$RAW_DATABASE_URL")"

GOOGLE_CLIENT_ID="$(read_secret GOOGLE_CLIENT_ID)"
GOOGLE_CLIENT_SECRET="$(read_secret GOOGLE_CLIENT_SECRET)"
JWT_SECRET="$(read_secret JWT_SECRET)"
CP_REGISTRATION_KEY="$(read_secret CP_REGISTRATION_KEY)"
TURNSTILE_SECRET_KEY="$(read_secret TURNSTILE_SECRET_KEY)"
TURNSTILE_SITE_KEY="$(read_secret TURNSTILE_SITE_KEY)"

# Runtime values only — never commit this file and never bake these into images.
# Same image must stay promotable from demo -> uat -> prod.
cat > "$ENV_FILE" <<EOF
PLANT_DATABASE_URL=${NORMALIZED_DATABASE_URL}
PLANT_BACKEND_REDIS_URL=redis://redis:6379/0
PLANT_GATEWAY_REDIS_URL=redis://redis:6379/1
PP_BACKEND_REDIS_URL=redis://redis:6379/2
CP_BACKEND_REDIS_URL=redis://redis:6379/3
GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
JWT_SECRET=${JWT_SECRET}
CP_REGISTRATION_KEY=${CP_REGISTRATION_KEY}
TURNSTILE_SECRET_KEY=${TURNSTILE_SECRET_KEY}
TURNSTILE_SITE_KEY=${TURNSTILE_SITE_KEY}
WAOOAW_CLOUDSQL_ENV=${TARGET_ENV}
ENVIRONMENT=codespace
CP_API_BASE_URL=/api
PP_API_BASE_URL=/api
EOF
chmod 600 "$ENV_FILE"

echo "Wrote ${ENV_FILE}"
