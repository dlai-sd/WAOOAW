#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: provision-managed-redis.sh [options]

Create or reuse one managed Redis instance and upsert service-specific REDIS_URL secrets.

Options:
  --project <id>          GCP project ID
  --region <region>       GCP region
  --environment <env>     Environment name, e.g. demo
  --network <network>     VPC network resource, e.g. projects/<project>/global/networks/default
  --instance-name <name>  Redis instance name override (default: waooaw-redis-<env>)
  --tier <tier>           Redis tier (default: basic)
  --memory-gb <size>      Redis size in GB (default: 1)
  --redis-version <ver>   Redis version (default: redis_7_0)
  --connect-mode <mode>   Connect mode (default: DIRECT_PEERING)
  --reserved-ip-range <r> Reserved IP range name for authorized network peering
  --apply                 Execute gcloud mutations
  --dry-run               Print planned actions only
  --help                  Show this help text

Environment overrides:
  GCLOUD_BIN              gcloud executable to use (default: gcloud)

Examples:
  bash cloud/scripts/provision-managed-redis.sh \
    --project waooaw-oauth \
    --region asia-south1 \
    --environment demo \
    --network projects/waooaw-oauth/global/networks/default \
    --tier basic \
    --memory-gb 1 \
    --apply
EOF
}

log() {
  printf '[redis-script] %s\n' "$*" >&2
}

fail() {
  printf '[redis-script] ERROR: %s\n' "$*" >&2
  exit 1
}

PROJECT_ID=""
REGION=""
ENVIRONMENT=""
NETWORK=""
INSTANCE_NAME=""
TIER="basic"
MEMORY_GB="1"
REDIS_VERSION="redis_7_0"
CONNECT_MODE="DIRECT_PEERING"
RESERVED_IP_RANGE=""
APPLY_MODE="false"
GCLOUD_BIN="${GCLOUD_BIN:-gcloud}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)
      PROJECT_ID="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --network)
      NETWORK="$2"
      shift 2
      ;;
    --instance-name)
      INSTANCE_NAME="$2"
      shift 2
      ;;
    --tier)
      TIER="$2"
      shift 2
      ;;
    --memory-gb)
      MEMORY_GB="$2"
      shift 2
      ;;
    --redis-version)
      REDIS_VERSION="$2"
      shift 2
      ;;
    --connect-mode)
      CONNECT_MODE="$2"
      shift 2
      ;;
    --reserved-ip-range)
      RESERVED_IP_RANGE="$2"
      shift 2
      ;;
    --apply)
      APPLY_MODE="true"
      shift
      ;;
    --dry-run)
      APPLY_MODE="false"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      usage >&2
      fail "Unknown argument: $1"
      ;;
  esac
done

[[ -n "$PROJECT_ID" ]] || fail "--project is required"
[[ -n "$REGION" ]] || fail "--region is required"
[[ -n "$ENVIRONMENT" ]] || fail "--environment is required"
[[ -n "$NETWORK" ]] || fail "--network is required"

if [[ -z "$INSTANCE_NAME" ]]; then
  INSTANCE_NAME="waooaw-redis-${ENVIRONMENT}"
fi

if ! command -v "$GCLOUD_BIN" >/dev/null 2>&1; then
  fail "${GCLOUD_BIN} not found on PATH"
fi

declare -a SECRET_NAMES=(
  "${ENVIRONMENT}-plant-backend-redis-url"
  "${ENVIRONMENT}-plant-gateway-redis-url"
  "${ENVIRONMENT}-pp-backend-redis-url"
  "${ENVIRONMENT}-cp-backend-redis-url"
)
declare -a SECRET_DBS=(0 1 2 3)

describe_host() {
  "$GCLOUD_BIN" redis instances describe "$INSTANCE_NAME" \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --format='value(host)' 2>/dev/null || true
}

ensure_redis_instance() {
  local host
  host="$(describe_host)"
  if [[ -n "$host" ]]; then
    log "Redis instance ${INSTANCE_NAME} already exists in ${REGION} with host ${host}"
    printf '%s' "$host"
    return 0
  fi

  log "Redis instance ${INSTANCE_NAME} does not exist yet"
  log "Planned create: project=${PROJECT_ID} region=${REGION} network=${NETWORK} tier=${TIER} memory_gb=${MEMORY_GB} redis_version=${REDIS_VERSION} connect_mode=${CONNECT_MODE}"
  if [[ "$APPLY_MODE" != "true" ]]; then
    printf 'DRY_RUN_REDIS_HOST_%s' "$ENVIRONMENT"
    return 0
  fi

  declare -a create_cmd=(
    "$GCLOUD_BIN" redis instances create "$INSTANCE_NAME"
    --project "$PROJECT_ID"
    --region "$REGION"
    --network "$NETWORK"
    --tier "$TIER"
    --size "$MEMORY_GB"
    --redis-version "$REDIS_VERSION"
    --connect-mode "$CONNECT_MODE"
  )
  if [[ -n "$RESERVED_IP_RANGE" ]]; then
    create_cmd+=(--reserved-ip-range "$RESERVED_IP_RANGE")
  fi

  if ! "${create_cmd[@]}"; then
    fail "Redis instance ${INSTANCE_NAME} creation failed. Check redis.instances.create permissions or existing network prerequisites."
  fi
  host="$(describe_host)"
  [[ -n "$host" ]] || fail "Redis instance ${INSTANCE_NAME} was created but host lookup returned empty"
  printf '%s' "$host"
}

ensure_secret() {
  local secret_name="$1"
  if "$GCLOUD_BIN" secrets describe "$secret_name" --project "$PROJECT_ID" >/dev/null 2>&1; then
    log "Secret ${secret_name} already exists"
    return 0
  fi

  log "Secret ${secret_name} does not exist yet"
  if [[ "$APPLY_MODE" != "true" ]]; then
    return 0
  fi

  "$GCLOUD_BIN" secrets create "$secret_name" \
    --project "$PROJECT_ID" \
    --replication-policy automatic >/dev/null
}

upsert_secret_version() {
  local secret_name="$1"
  local secret_value="$2"
  log "Upserting latest version for ${secret_name}"
  if [[ "$APPLY_MODE" != "true" ]]; then
    log "Dry run value: ${secret_value}"
    return 0
  fi

  printf '%s' "$secret_value" | "$GCLOUD_BIN" secrets versions add "$secret_name" \
    --project "$PROJECT_ID" \
    --data-file=- >/dev/null
}

HOST="$(ensure_redis_instance)"
log "Using Redis host: ${HOST}"

for index in "${!SECRET_NAMES[@]}"; do
  secret_name="${SECRET_NAMES[$index]}"
  db_index="${SECRET_DBS[$index]}"
  secret_value="redis://${HOST}:6379/${db_index}"
  ensure_secret "$secret_name"
  upsert_secret_version "$secret_name" "$secret_value"
done

log "Completed Redis provisioning flow for environment ${ENVIRONMENT}"