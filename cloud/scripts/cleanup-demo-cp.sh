#!/usr/bin/env bash
set -euo pipefail

# Deletes demo CP Cloud Run services + serverless NEGs so Terraform can recreate them cleanly.
# Keeps the shared static IP (foundation stack) untouched.

PROJECT_ID="${PROJECT_ID:-waooaw-oauth}"
REGION="${REGION:-asia-south1}"
ENVIRONMENT="${ENVIRONMENT:-demo}"

# Resource naming (matches terraform stacks/modules)
CP_BACKEND_SERVICE="${CP_BACKEND_SERVICE:-waooaw-cp-backend-${ENVIRONMENT}}"
CP_FRONTEND_SERVICE="${CP_FRONTEND_SERVICE:-waooaw-cp-frontend-${ENVIRONMENT}}"

CP_BACKEND_NEG="${CP_BACKEND_NEG:-waooaw-${ENVIRONMENT}-cp-backend-neg}"
CP_FRONTEND_NEG="${CP_FRONTEND_NEG:-waooaw-${ENVIRONMENT}-cp-frontend-neg}"

KEY_FILE_DEFAULT="/workspaces/WAOOAW/cloud/terraform/terraform-admin-key.json"
KEY_FILE="${KEY_FILE:-$KEY_FILE_DEFAULT}"

if [[ "${CONFIRM:-}" != "yes" ]]; then
  echo "Refusing to run without CONFIRM=yes" >&2
  echo "This will DELETE demo CP Cloud Run services + NEGs in project '${PROJECT_ID}' (${REGION})." >&2
  exit 2
fi

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud not found on PATH" >&2
  exit 1
fi

if [[ ! -f "$KEY_FILE" ]]; then
  echo "Service account key file not found: $KEY_FILE" >&2
  exit 1
fi

echo "Authenticating gcloud (service account key file)..."
gcloud auth activate-service-account --key-file="$KEY_FILE" >/dev/null

gcloud config set project "$PROJECT_ID" >/dev/null

echo "Target: project=$PROJECT_ID region=$REGION env=$ENVIRONMENT"

delete_run_service_if_exists() {
  local name="$1"
  if gcloud run services describe "$name" --region "$REGION" --project "$PROJECT_ID" >/dev/null 2>&1; then
    echo "Deleting Cloud Run service: $name"
    gcloud run services delete "$name" --region "$REGION" --project "$PROJECT_ID" --quiet
  else
    echo "Cloud Run service not found (skip): $name"
  fi
}

delete_neg_if_exists() {
  local name="$1"
  if gcloud compute network-endpoint-groups describe "$name" --region "$REGION" --project "$PROJECT_ID" >/dev/null 2>&1; then
    echo "Deleting regional NEG: $name"
    gcloud compute network-endpoint-groups delete "$name" --region "$REGION" --project "$PROJECT_ID" --quiet
  else
    echo "NEG not found (skip): $name"
  fi
}

delete_global_forwarding_rule_if_exists() {
  local name="$1"
  if gcloud compute forwarding-rules describe "$name" --global --project "$PROJECT_ID" >/dev/null 2>&1; then
    echo "Deleting global forwarding rule: $name"
    gcloud compute forwarding-rules delete "$name" --global --project "$PROJECT_ID" --quiet
  else
    echo "Forwarding rule not found (skip): $name"
  fi
}

delete_target_http_proxy_if_exists() {
  local name="$1"
  if gcloud compute target-http-proxies describe "$name" --global --project "$PROJECT_ID" >/dev/null 2>&1; then
    echo "Deleting target HTTP proxy: $name"
    gcloud compute target-http-proxies delete "$name" --global --project "$PROJECT_ID" --quiet
  else
    echo "Target HTTP proxy not found (skip): $name"
  fi
}

delete_target_https_proxy_if_exists() {
  local name="$1"
  if gcloud compute target-https-proxies describe "$name" --global --project "$PROJECT_ID" >/dev/null 2>&1; then
    echo "Deleting target HTTPS proxy: $name"
    gcloud compute target-https-proxies delete "$name" --global --project "$PROJECT_ID" --quiet
  else
    echo "Target HTTPS proxy not found (skip): $name"
  fi
}

delete_url_map_if_exists() {
  local name="$1"
  if gcloud compute url-maps describe "$name" --global --project "$PROJECT_ID" >/dev/null 2>&1; then
    echo "Deleting URL map: $name"
    gcloud compute url-maps delete "$name" --global --project "$PROJECT_ID" --quiet
  else
    echo "URL map not found (skip): $name"
  fi
}

delete_backend_service_if_exists() {
  local name="$1"
  if gcloud compute backend-services describe "$name" --global --project "$PROJECT_ID" >/dev/null 2>&1; then
    echo "Deleting backend service: $name"
    gcloud compute backend-services delete "$name" --global --project "$PROJECT_ID" --quiet
  else
    echo "Backend service not found (skip): $name"
  fi
}

delete_ssl_certificate_if_exists() {
  local name="$1"
  if gcloud compute ssl-certificates describe "$name" --global --project "$PROJECT_ID" >/dev/null 2>&1; then
    echo "Deleting SSL certificate: $name"
    gcloud compute ssl-certificates delete "$name" --global --project "$PROJECT_ID" --quiet
  else
    echo "SSL certificate not found (skip): $name"
  fi
}

cleanup_legacy_demo_lb_if_present() {
  # These are legacy demo LB resources currently holding serverless NEGs "in use".
  # Static IP (global address) is kept/reserved separately and is NOT deleted here.

  echo "Cleaning up legacy demo load balancer resources (keeps reserved IP)..."

  # Detach entry points first
  delete_global_forwarding_rule_if_exists "demo-https-forwarding-rule"
  delete_global_forwarding_rule_if_exists "demo-http-forwarding-rule"

  # Then proxies
  delete_target_https_proxy_if_exists "demo-https-proxy"
  delete_target_http_proxy_if_exists "demo-http-proxy"

  # Then URL maps
  delete_url_map_if_exists "demo-url-map"
  delete_url_map_if_exists "demo-http-redirect-map"

  # Then backend services that reference NEGs
  delete_backend_service_if_exists "demo-cp-frontend-backend"
  delete_backend_service_if_exists "demo-cp-backend-backend"

  # Finally, SSL certs (will require re-issue after recreate)
  delete_ssl_certificate_if_exists "demo-cp-ssl"
}

# Delete services first to reduce chance of downstream references.
delete_run_service_if_exists "$CP_FRONTEND_SERVICE"
delete_run_service_if_exists "$CP_BACKEND_SERVICE"

# Delete NEGs to avoid "already exists" on next apply.
# NOTE: If these NEGs are attached to an LB backend service, deletion may fail with "resource is in use".

set +e
delete_neg_if_exists "$CP_FRONTEND_NEG"
neg_frontend_rc=$?
delete_neg_if_exists "$CP_BACKEND_NEG"
neg_backend_rc=$?
set -e

if [[ "$neg_frontend_rc" -ne 0 || "$neg_backend_rc" -ne 0 ]]; then
  cleanup_legacy_demo_lb_if_present
  delete_neg_if_exists "$CP_FRONTEND_NEG"
  delete_neg_if_exists "$CP_BACKEND_NEG"
fi

echo "Cleanup complete (demo CP)."
