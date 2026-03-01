#!/bin/sh
# Runtime config injection — runs as the nginx user at container start.
# Writes window.__WAOOAW_PP_RUNTIME_CONFIG__ from Cloud Run env vars so that
# the same Docker image can be promoted through dev → uat → prod without a
# rebuild. Secrets come from GCP Secret Manager mounted as env vars.
set -eu

CONFIG_PATH="/usr/share/nginx/html/pp-runtime-config.js"

cat > "$CONFIG_PATH" <<EOF
window.__WAOOAW_PP_RUNTIME_CONFIG__ = {
  environment: "${ENVIRONMENT:-}",
  apiBaseUrl: "${PP_API_BASE_URL:-}",
  googleClientId: "${GOOGLE_CLIENT_ID:-}"
};
EOF

exec nginx -g 'daemon off;'
