#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# GCP Service Account auto-activation + Cloud SQL Proxy for Codespace
#
# Prerequisites (add at github.com/settings/codespaces):
#   GCP_SA_KEY  — single-line JSON of the waooaw-codespace-reader SA key
#                 Repository access = dlai-sd/WAOOAW
#
# What this does:
#   1. Writes SA JSON to /root/.gcp/waooaw-sa.json (persisted, never committed)
#   2. Activates it with gcloud + sets project waooaw-oauth
#   3. Starts Cloud SQL Auth Proxy in background (port 15432 by default)
#   4. Reads DB_USER + DB_PASSWORD from Secret Manager → /root/.env.db
#   5. Prints connection hint
# ---------------------------------------------------------------------------

set -euo pipefail

STRICT_MODE=1

for arg in "$@"; do
    case "$arg" in
        --best-effort)
            STRICT_MODE=0
            ;;
        --strict)
            STRICT_MODE=1
            ;;
    esac
done

finish_with_error() {
    local message="$1"
    shift || true

    echo "$message"
    for extra in "$@"; do
        echo "$extra"
    done

    if [[ "$STRICT_MODE" == "1" ]]; then
        exit 1
    fi

    echo "⚠️  Continuing without GCP bootstrap because this run is best-effort."
    exit 0
}

TARGET_ENV="${WAOOAW_CLOUDSQL_ENV:-demo}"
PROJECT_ID="${WAOOAW_GCP_PROJECT_ID:-waooaw-oauth}"
REGION="${WAOOAW_GCP_REGION:-asia-south1}"

case "$TARGET_ENV" in
    demo|uat|prod)
        ;;
    *)
        finish_with_error \
            "❌ Unsupported WAOOAW_CLOUDSQL_ENV: ${TARGET_ENV}" \
            "   Allowed values: demo, uat, prod"
        ;;
esac

GCP_DIR="/root/.gcp"
KEY_FILE="${GCP_DIR}/waooaw-sa.json"
DB_ENV_FILE="/root/.env.db"
PROXY_LOG="/tmp/cloud-sql-proxy.log"
INSTANCE_NAME="${WAOOAW_CLOUDSQL_INSTANCE_NAME:-plant-sql-${TARGET_ENV}}"
INSTANCE="${PROJECT_ID}:${REGION}:${INSTANCE_NAME}"
PROXY_PORT="${WAOOAW_CLOUDSQL_PROXY_PORT:-15432}"
PROXY_ADDRESS="${WAOOAW_CLOUDSQL_PROXY_ADDRESS:-0.0.0.0}"
DATABASE_URL_SECRET="${WAOOAW_DB_URL_SECRET:-${TARGET_ENV}-plant-database-url}"

# ── 1. Auth ──────────────────────────────────────────────────────────────────
if [[ -z "${GCP_SA_KEY:-}" ]]; then
    echo "⚠️  GCP_SA_KEY not set — skipping GCP auth + DB proxy."
    echo "   Add GCP_SA_KEY at github.com/settings/codespaces (repo: dlai-sd/WAOOAW)"
    exit 0
fi

echo "🔐 Activating GCP service account..."
mkdir -p "$GCP_DIR" && chmod 700 "$GCP_DIR"
printf '%s' "$GCP_SA_KEY" > "$KEY_FILE"
chmod 600 "$KEY_FILE"

gcloud auth activate-service-account --key-file="$KEY_FILE" --quiet
gcloud config set project "$PROJECT_ID" --quiet
echo "✅ GCP auth active: $(gcloud config get-value account 2>/dev/null)"
echo "   Target env: ${TARGET_ENV} | Instance: ${INSTANCE} | Secret: ${DATABASE_URL_SECRET}"

PUBLIC_IP_ENABLED=$(gcloud sql instances describe "$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --format='value(settings.ipConfiguration.ipv4Enabled)' 2>/dev/null || true)

if [[ "$PUBLIC_IP_ENABLED" != "True" && "$PUBLIC_IP_ENABLED" != "true" ]]; then
    finish_with_error \
        "❌ Cloud SQL public IP is disabled for ${INSTANCE_NAME}." \
        "   Codespaces uses the public-IP-backed Auth Proxy path documented in docs/CONTEXT_AND_INDEX.md." \
        "   Fix: gcloud sql instances patch ${INSTANCE_NAME} --assign-ip --project=${PROJECT_ID} --quiet"
fi

# ── 2. Cloud SQL Auth Proxy ───────────────────────────────────────────────────
PROXY_BIN="/usr/local/bin/cloud-sql-proxy"
if [[ ! -x "$PROXY_BIN" ]]; then
    echo "📥 Installing Cloud SQL Auth Proxy v2..."
    curl -fsSL \
        "https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.14.2/cloud-sql-proxy.linux.amd64" \
        -o "$PROXY_BIN"
    chmod +x "$PROXY_BIN"
fi

# Kill any stale proxy
pkill -f "cloud-sql-proxy" 2>/dev/null || true
sleep 1

"$PROXY_BIN" \
    --credentials-file="$KEY_FILE" \
    --address="${PROXY_ADDRESS}" \
    "$INSTANCE" \
    --port="${PROXY_PORT}" \
    > "$PROXY_LOG" 2>&1 &

PROXY_PID=$!
sleep 4

if kill -0 "$PROXY_PID" 2>/dev/null && grep -q "ready for new connections" "$PROXY_LOG"; then
    echo "✅ Cloud SQL Proxy listening on ${PROXY_ADDRESS}:${PROXY_PORT} (PID ${PROXY_PID})"
else
    PROXY_FAILURE_NOTE=""
    if grep -q 'instance does not have IP of type "PUBLIC"' "$PROXY_LOG"; then
        PROXY_FAILURE_NOTE="   Fix: gcloud sql instances patch ${INSTANCE_NAME} --assign-ip --project=${PROJECT_ID} --quiet"
    fi
    finish_with_error \
        "❌ Cloud SQL Proxy failed to start — check $PROXY_LOG" \
        "$(cat "$PROXY_LOG" 2>/dev/null || true)" \
        "$PROXY_FAILURE_NOTE"
fi

# ── 3. DB credentials from Secret Manager ────────────────────────────────────
echo "🔑 Reading DB credentials from Secret Manager..."

DB_URL=$(gcloud secrets versions access latest \
    --secret="$DATABASE_URL_SECRET" \
    --project="$PROJECT_ID" 2>/dev/null) || true

if [[ -n "$DB_URL" ]]; then
    # Parse user/password/db from postgresql+asyncpg://user:pass@/db?host=...
    DB_USER=$(python3 -c "from urllib.parse import urlparse, unquote; u=urlparse('${DB_URL}'.replace('+asyncpg','')); print(unquote(u.username))" 2>/dev/null)
    DB_PASS=$(python3 -c "from urllib.parse import urlparse, unquote; u=urlparse('${DB_URL}'.replace('+asyncpg','')); print(unquote(u.password))" 2>/dev/null)
    DB_NAME=$(python3 -c "from urllib.parse import urlparse; u=urlparse('${DB_URL}'.replace('+asyncpg','')); print(u.path.lstrip('/'))" 2>/dev/null)

    # Write .pgpass for passwordless psql
    echo "127.0.0.1:${PROXY_PORT}:${DB_NAME}:${DB_USER}:${DB_PASS}" > /root/.pgpass
    chmod 600 /root/.pgpass

    cat > "$DB_ENV_FILE" <<EOF
# Auto-generated by gcp-auth.sh — DO NOT COMMIT
export PGHOST=127.0.0.1
export PGPORT=${PROXY_PORT}
export PGUSER=${DB_USER}
export PGDATABASE=${DB_NAME}
EOF
    chmod 600 "$DB_ENV_FILE"
    echo "✅ DB ready — connect: source ${DB_ENV_FILE} && psql"
    echo "   Environment: ${TARGET_ENV} | Instance: ${INSTANCE_NAME} | DB: ${DB_NAME} | User: ${DB_USER}"
else
    finish_with_error \
        "⚠️  Could not read DB credentials from Secret Manager." \
        "   SA may need roles/secretmanager.secretAccessor" \
        "   Expected secret: ${DATABASE_URL_SECRET}" \
        "   Once granted or corrected, re-run: bash .devcontainer/gcp-auth.sh"
fi
