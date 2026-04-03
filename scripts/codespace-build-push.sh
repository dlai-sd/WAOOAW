#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$REPO_ROOT"

GCP_PROJECT_ID="${GCP_PROJECT_ID:-waooaw-oauth}"
GCP_REGION="${GCP_REGION:-asia-south1}"
GCP_REGISTRY="${GCP_REGISTRY:-${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/waooaw}"
BUILDER_NAME="${BUILDX_BUILDER_NAME:-waooaw-builder}"
SCOPE="all"
VERIFY_PUSH=true
DRY_RUN=false
IMAGE_TAG=""

usage() {
  cat <<'EOF'
Usage: bash scripts/codespace-build-push.sh [options]

Options:
  --tag <tag>         Use an explicit immutable image tag
  --scope <scope>     all | cp | pp | plant
  --no-verify         Skip post-push Artifact Registry verification
  --dry-run           Print planned builds without executing them
  -h, --help          Show this help

Defaults:
  tag   = <git-short-sha>-<UTC timestamp>
  scope = all

Examples:
  bash scripts/codespace-build-push.sh
  bash scripts/codespace-build-push.sh --tag 405a5ec-20260403T080000
  bash scripts/codespace-build-push.sh --scope cp
EOF
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tag)
      IMAGE_TAG="$2"
      shift 2
      ;;
    --scope)
      SCOPE="$2"
      shift 2
      ;;
    --no-verify)
      VERIFY_PUSH=false
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unsupported argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

case "$SCOPE" in
  all|cp|pp|plant) ;;
  *)
    echo "Unsupported scope: $SCOPE" >&2
    usage >&2
    exit 1
    ;;
esac

if [[ -z "$IMAGE_TAG" ]]; then
  require_command git
  IMAGE_TAG="$(git rev-parse --short HEAD)-$(date -u +%Y%m%dT%H%M%S)"
fi

require_command docker
require_command gcloud

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon unavailable." >&2
  exit 1
fi

build_specs=()

add_spec() {
  build_specs+=("$1|$2|$3")
}

if [[ "$SCOPE" == "all" || "$SCOPE" == "cp" ]]; then
  add_spec cp-backend src/CP/BackEnd src/CP/BackEnd/Dockerfile
  add_spec cp src/CP/FrontEnd src/CP/FrontEnd/Dockerfile
fi

if [[ "$SCOPE" == "all" || "$SCOPE" == "pp" ]]; then
  add_spec pp-backend src/PP/BackEnd src/PP/BackEnd/Dockerfile
  add_spec pp src/PP/FrontEnd src/PP/FrontEnd/Dockerfile
fi

if [[ "$SCOPE" == "all" || "$SCOPE" == "plant" ]]; then
  add_spec plant-backend src/Plant/BackEnd src/Plant/BackEnd/Dockerfile
  add_spec plant-gateway src/Plant/Gateway src/Plant/Gateway/Dockerfile
  add_spec plant-opa src/Plant/Gateway/opa src/Plant/Gateway/opa/Dockerfile
fi

echo "Using registry: ${GCP_REGISTRY}"
echo "Using scope: ${SCOPE}"
echo "Using tag: ${IMAGE_TAG}"

if [[ "$DRY_RUN" == "true" ]]; then
  for spec in "${build_specs[@]}"; do
    IFS='|' read -r image context dockerfile <<< "$spec"
    echo "Would build ${GCP_REGISTRY}/${image}:${IMAGE_TAG} from ${dockerfile} (${context})"
  done
  exit 0
fi

echo "Authenticating Docker to Artifact Registry..."
gcloud auth configure-docker "${GCP_REGION}-docker.pkg.dev" --quiet

if docker buildx inspect "$BUILDER_NAME" >/dev/null 2>&1; then
  docker buildx use "$BUILDER_NAME"
else
  docker buildx create --name "$BUILDER_NAME" --use >/dev/null
fi

docker buildx inspect --bootstrap >/dev/null

for spec in "${build_specs[@]}"; do
  IFS='|' read -r image context dockerfile <<< "$spec"
  target_image="${GCP_REGISTRY}/${image}:${IMAGE_TAG}"
  echo "Building and pushing ${target_image}"
  docker buildx build \
    --platform linux/amd64 \
    --file "$dockerfile" \
    --tag "$target_image" \
    --push \
    "$context"
done

if [[ "$VERIFY_PUSH" == "true" ]]; then
  echo "Verifying pushed images..."
  for spec in "${build_specs[@]}"; do
    IFS='|' read -r image _ _ <<< "$spec"
    target_image="${GCP_REGISTRY}/${image}:${IMAGE_TAG}"
    if gcloud artifacts docker images describe "$target_image" >/dev/null 2>&1; then
      echo "verified ${target_image}"
    else
      echo "warning: unable to verify ${target_image} via Artifact Registry metadata" >&2
    fi
  done
fi

echo
echo "Build-and-push completed."
echo "Export this tag for deploy steps:"
echo "export IMAGE_TAG=${IMAGE_TAG}"