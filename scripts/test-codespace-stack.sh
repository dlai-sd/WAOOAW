#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$REPO_ROOT"

bash -n scripts/codespace-stack.sh
CODESPACE_NAME=test-space bash scripts/codespace-stack.sh urls | grep 'app.github.dev'

mkdir -p .codespace
trap 'rm -f .codespace/demo.env' EXIT
printf '%s\n' \
	'PLANT_DATABASE_URL=postgresql://user:pass@host.docker.internal:15432/app' \
	'PLANT_BACKEND_REDIS_URL=redis://redis:6379/0' \
	'PLANT_GATEWAY_REDIS_URL=redis://redis:6379/1' \
	'PP_BACKEND_REDIS_URL=redis://redis:6379/2' \
	'CP_BACKEND_REDIS_URL=redis://redis:6379/3' \
	'GOOGLE_CLIENT_ID=test-client-id' \
	'GOOGLE_CLIENT_SECRET=test-client-secret' \
	'JWT_SECRET=test-jwt-secret' \
	'CP_REGISTRATION_KEY=test-registration-key' \
	'TURNSTILE_SECRET_KEY=test-turnstile-secret' \
	'TURNSTILE_SITE_KEY=test-turnstile-site' \
	'WAOOAW_CLOUDSQL_ENV=demo' \
	'ENVIRONMENT=codespace' \
	'CP_API_BASE_URL=/api' \
	'PP_API_BASE_URL=/api' > .codespace/demo.env

CODESPACE_NAME=test-space GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN=app.github.dev \
	docker compose --env-file .codespace/demo.env -f docker-compose.local.yml -f docker-compose.codespace.yml config >/dev/null
