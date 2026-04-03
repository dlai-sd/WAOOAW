#!/bin/sh
set -eu

CONFIG_PATH="/usr/share/nginx/html/runtime-config.js"
NGINX_MODE_VALUE="${NGINX_MODE:-cloudrun}"

ENVIRONMENT_VALUE="${ENVIRONMENT:-}"
API_BASE_URL_VALUE="${CP_API_BASE_URL:-}"
GOOGLE_CLIENT_ID_VALUE="${GOOGLE_CLIENT_ID:-}"
TURNSTILE_SITE_KEY_VALUE="${TURNSTILE_SITE_KEY:-}"

cat > "$CONFIG_PATH" <<EOF
window.__WAOOAW_RUNTIME_CONFIG__ = {
  environment: "${ENVIRONMENT_VALUE}",
  apiBaseUrl: "${API_BASE_URL_VALUE}",
  googleClientId: "${GOOGLE_CLIENT_ID_VALUE}",
  turnstileSiteKey: "${TURNSTILE_SITE_KEY_VALUE}"
};
EOF

case "$NGINX_MODE_VALUE" in
  local)
    exec nginx -c /etc/nginx/nginx.local.conf -g 'daemon off;'
    ;;
  cloudrun|*)
    exec nginx -c /etc/nginx/nginx.cloudrun.conf -g 'daemon off;'
    ;;
esac
