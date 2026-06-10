#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: demo-runtime-batch.sh <stop|start>

Environment variables:
  GCP_PROJECT_ID          GCP project (default: waooaw-oauth)
  GCP_REGION              GCP region (default: asia-south1)
  TARGET_ENVIRONMENT      Must be demo for this workflow (default: demo)
  DRY_RUN                 true|false (default: false)

  START_MIN_CP_FRONTEND   Start min instances for CP frontend (default: 0)
  START_MIN_CP_BACKEND    Start min instances for CP backend (default: 0)
  START_MIN_PP_FRONTEND   Start min instances for PP frontend (default: 0)
  START_MIN_PP_BACKEND    Start min instances for PP backend (default: 0)
  START_MIN_GATEWAY       Start min instances for Plant API Gateway (default: 1)
EOF
}

if [[ $# -ne 1 ]]; then
  usage
  exit 2
fi

ACTION="$1"
if [[ "$ACTION" != "stop" && "$ACTION" != "start" ]]; then
  usage
  exit 2
fi

PROJECT_ID="${GCP_PROJECT_ID:-waooaw-oauth}"
REGION="${GCP_REGION:-asia-south1}"
TARGET_ENVIRONMENT="${TARGET_ENVIRONMENT:-demo}"
DRY_RUN="${DRY_RUN:-false}"

if [[ "$TARGET_ENVIRONMENT" != "demo" ]]; then
  echo "Refusing to run outside demo. TARGET_ENVIRONMENT=$TARGET_ENVIRONMENT" >&2
  exit 3
fi

# Runtime assets explicitly requested by user scope:
# - CP (frontend + backend)
# - PP (frontend + backend)
# - API Gateway (plant gateway)
SERVICES=(
  "waooaw-cp-frontend-${TARGET_ENVIRONMENT}"
  "waooaw-cp-backend-${TARGET_ENVIRONMENT}"
  "waooaw-pp-frontend-${TARGET_ENVIRONMENT}"
  "waooaw-pp-backend-${TARGET_ENVIRONMENT}"
  "waooaw-plant-gateway-${TARGET_ENVIRONMENT}"
)

start_min_for() {
  case "$1" in
    "waooaw-cp-frontend-${TARGET_ENVIRONMENT}") echo "${START_MIN_CP_FRONTEND:-0}" ;;
    "waooaw-cp-backend-${TARGET_ENVIRONMENT}") echo "${START_MIN_CP_BACKEND:-0}" ;;
    "waooaw-pp-frontend-${TARGET_ENVIRONMENT}") echo "${START_MIN_PP_FRONTEND:-0}" ;;
    "waooaw-pp-backend-${TARGET_ENVIRONMENT}") echo "${START_MIN_PP_BACKEND:-0}" ;;
    "waooaw-plant-gateway-${TARGET_ENVIRONMENT}") echo "${START_MIN_GATEWAY:-1}" ;;
    *)
      echo "Unknown service mapping: $1" >&2
      exit 4
      ;;
  esac
}

run_cmd() {
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "DRY_RUN: $*"
  else
    "$@"
  fi
}

ensure_gcloud_available() {
  if [[ "$DRY_RUN" == "true" ]]; then
    return 0
  fi
  if ! command -v gcloud >/dev/null 2>&1; then
    echo "gcloud is required for non-dry-run execution." >&2
    exit 5
  fi
}

ensure_service_exists() {
  local service="$1"
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "DRY_RUN: verify service exists: $service"
    return 0
  fi
  gcloud run services describe "$service" \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --format="value(metadata.name)" >/dev/null
}

update_min_instances() {
  local service="$1"
  local min_instances="$2"

  run_cmd gcloud run services update "$service" \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --min-instances "$min_instances" \
    --quiet
}

ensure_gcloud_available

echo "Action: $ACTION"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Environment: $TARGET_ENVIRONMENT"
echo "Dry run: $DRY_RUN"

for service in "${SERVICES[@]}"; do
  ensure_service_exists "$service"

  if [[ "$ACTION" == "stop" ]]; then
    target_min="0"
  else
    target_min="$(start_min_for "$service")"
  fi

  update_min_instances "$service" "$target_min"
  echo "Applied min_instances=$target_min for $service"
done

echo "Completed action: $ACTION"
