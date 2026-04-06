#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$REPO_ROOT"

COMPOSE_FILES=(-f docker-compose.local.yml -f docker-compose.codespace.yml)
ENV_FILE=".codespace/demo.env"
DC=(docker compose --env-file "$ENV_FILE" "${COMPOSE_FILES[@]}")
PORT_DOMAIN="${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}"
CP_FRONTEND_PORT="${WAOOAW_CP_FRONTEND_PORT:-3002}"
PP_FRONTEND_PORT="${WAOOAW_PP_FRONTEND_PORT:-3001}"
CP_BACKEND_PORT="${WAOOAW_CP_BACKEND_PORT:-8020}"
PP_BACKEND_PORT="${WAOOAW_PP_BACKEND_PORT:-8015}"
PLANT_GATEWAY_PORT="${WAOOAW_PLANT_GATEWAY_PORT:-8000}"
PLANT_BACKEND_PORT="${WAOOAW_PLANT_BACKEND_PORT:-8001}"

export PORT_DOMAIN
export CP_FRONTEND_PORT
export PP_FRONTEND_PORT
export CP_BACKEND_PORT
export PP_BACKEND_PORT
export PLANT_GATEWAY_PORT
export PLANT_BACKEND_PORT

case "${1:-}" in
  up|build|restart|down|logs|status|urls|bootstrap-env|doctor|clean) ;;
  *) echo "Usage: $0 {bootstrap-env|build|up|restart|down|logs|status|urls|doctor|clean} [all|plant|cp|pp]"; exit 1 ;;
esac

command_name="${1:-}"
scope="${2:-all}"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1"
    exit 1
  fi
}

ensure_env_file() {
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "Missing ${ENV_FILE}. Run: bash scripts/codespace-stack.sh bootstrap-env"
    exit 1
  fi
}

require_docker() {
  require_command docker
  if ! docker info >/dev/null 2>&1; then
    echo "Docker is not available in this Codespace."
    exit 1
  fi
}

require_proxy() {
  if ! pgrep -fa cloud-sql-proxy >/dev/null 2>&1; then
    echo "Cloud SQL proxy not running. Run: bash .devcontainer/gcp-auth.sh"
    exit 1
  fi
}

scope_services() {
  case "$1" in
    all)
      printf '%s\n' redis plant-migrations plant-backend plant-worker plant-flower plant-gateway pp-backend pp-frontend cp-backend cp-frontend adminer
      ;;
    plant)
      printf '%s\n' redis plant-migrations plant-backend plant-worker plant-flower plant-gateway
      ;;
    cp)
      printf '%s\n' redis plant-migrations plant-backend plant-gateway cp-backend cp-frontend
      ;;
    pp)
      printf '%s\n' redis plant-migrations plant-backend plant-gateway pp-backend pp-frontend
      ;;
    *)
      echo "Unsupported scope: $1"
      echo "Supported scopes: all, plant, cp, pp"
      exit 1
      ;;
  esac
}

load_services() {
  mapfile -t SERVICES < <(scope_services "$scope")
}

print_urls() {
  if [[ -n "${CODESPACE_NAME:-}" ]]; then
    echo "CP Frontend: https://${CODESPACE_NAME}-${CP_FRONTEND_PORT}.${PORT_DOMAIN}/"
    echo "PP Frontend: https://${CODESPACE_NAME}-${PP_FRONTEND_PORT}.${PORT_DOMAIN}/"
    echo "CP Backend: https://${CODESPACE_NAME}-${CP_BACKEND_PORT}.${PORT_DOMAIN}/"
    echo "PP Backend: https://${CODESPACE_NAME}-${PP_BACKEND_PORT}.${PORT_DOMAIN}/"
    echo "Plant Gateway: https://${CODESPACE_NAME}-${PLANT_GATEWAY_PORT}.${PORT_DOMAIN}/"
    echo "Plant Backend: https://${CODESPACE_NAME}-${PLANT_BACKEND_PORT}.${PORT_DOMAIN}/"
    return
  fi

  echo "CP Frontend: http://localhost:${CP_FRONTEND_PORT}/"
  echo "PP Frontend: http://localhost:${PP_FRONTEND_PORT}/"
  echo "CP Backend: http://localhost:${CP_BACKEND_PORT}/"
  echo "PP Backend: http://localhost:${PP_BACKEND_PORT}/"
  echo "Plant Gateway: http://localhost:${PLANT_GATEWAY_PORT}/"
  echo "Plant Backend: http://localhost:${PLANT_BACKEND_PORT}/"
}

run_doctor() {
  local failures=0

  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker missing. Install or enable Docker-in-Docker for this Codespace."
    failures=1
  elif ! docker info >/dev/null 2>&1; then
    echo "Docker daemon unavailable. Restart the Codespace or Docker service."
    failures=1
  else
    echo "Docker: OK"
  fi

  if [[ ! -f "$ENV_FILE" ]]; then
    echo "Env file missing. Run: bash scripts/codespace-stack.sh bootstrap-env"
    failures=1
  else
    echo "Env file: OK ($ENV_FILE)"
  fi

  if ! pgrep -fa cloud-sql-proxy >/dev/null 2>&1; then
    echo "Cloud SQL proxy not running. Run: bash .devcontainer/gcp-auth.sh"
    failures=1
  else
    echo "Cloud SQL proxy: OK"
  fi

  if [[ "$failures" -ne 0 ]]; then
    return 1
  fi

  if ! "${DC[@]}" config >/dev/null; then
    echo "Compose config invalid. Inspect docker-compose.local.yml and docker-compose.codespace.yml."
    return 1
  fi
  echo "Compose config: OK"

  local names=(
    "cp-frontend|http://127.0.0.1:${CP_FRONTEND_PORT}/health"
    "pp-frontend|http://127.0.0.1:${PP_FRONTEND_PORT}/health"
    "cp-backend|http://127.0.0.1:${CP_BACKEND_PORT}/health"
    "pp-backend|http://127.0.0.1:${PP_BACKEND_PORT}/health"
    "plant-gateway|http://127.0.0.1:${PLANT_GATEWAY_PORT}/health"
    "plant-backend|http://127.0.0.1:${PLANT_BACKEND_PORT}/health"
  )

  for entry in "${names[@]}"; do
    local name="${entry%%|*}"
    local url="${entry#*|}"
    if curl --silent --fail "$url" >/dev/null 2>&1; then
      echo "Health: ${name} OK"
    else
      echo "Health: ${name} unhealthy or not running. Start the stack with: bash scripts/codespace-stack.sh up all"
    fi
  done
}

run_clean() {
  ensure_env_file
  require_docker
  docker compose --env-file "$ENV_FILE" "${COMPOSE_FILES[@]}" down --remove-orphans --rmi local -v || true
  echo "Removed WAOOAW-local Docker artifacts."
}

case "$command_name" in
  bootstrap-env)
    bash scripts/codespace-demo-env.sh
    ;;
  urls)
    print_urls
    ;;
  doctor)
    run_doctor
    ;;
  clean)
    run_clean
    ;;
  down)
    ensure_env_file
    require_docker
    "${DC[@]}" down --remove-orphans
    ;;
  status)
    ensure_env_file
    require_docker
    require_proxy
    "${DC[@]}" ps
    ;;
  build)
    ensure_env_file
    require_docker
    require_proxy
    load_services
    "${DC[@]}" build "${SERVICES[@]}"
    ;;
  up)
    ensure_env_file
    require_docker
    require_proxy
    load_services
    "${DC[@]}" up -d --build "${SERVICES[@]}"
    print_urls
    ;;
  restart)
    ensure_env_file
    require_docker
    require_proxy
    load_services
    "${DC[@]}" up -d --build --force-recreate "${SERVICES[@]}"
    ;;
  logs)
    ensure_env_file
    require_docker
    load_services
    "${DC[@]}" logs -f "${SERVICES[@]}"
    ;;
esac
