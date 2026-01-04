#!/usr/bin/env bash
set -euo pipefail

# Grants the CI service account the minimal roles to build/push images
# to Artifact Registry and deploy to Cloud Run.
# Required env vars:
#   PROJECT       - GCP project ID (e.g. waooaw-oauth)
#   LOCATION      - Artifact Registry location (e.g. asia-south1)
#   REPO          - Artifact Registry repo name (e.g. waooaw)
#   SA_EMAIL      - Service account email used by CI
# Optional:
#   ROLE_BIND_TARGET (defaults to the project) - resource scope for Run/SA roles
#
# Example:
#   PROJECT=waooaw-oauth LOCATION=asia-south1 REPO=waooaw \
#   SA_EMAIL=ci-deployer@waooaw-oauth.iam.gserviceaccount.com \
#   bash cloud/scripts/grant-ci-roles.sh

: "${PROJECT:?PROJECT is required}"
: "${LOCATION:?LOCATION is required}"
: "${REPO:?REPO is required}"
: "${SA_EMAIL:?SA_EMAIL is required}"

BIND_SCOPE="projects/${PROJECT}"

# Grant Artifact Registry writer on the specific repository.
# This is needed for docker/build-push-action to push images.
echo "Granting Artifact Registry writer on repo ${REPO} in ${LOCATION} for ${SA_EMAIL}"
gcloud artifacts repositories add-iam-policy-binding "${REPO}" \
  --location="${LOCATION}" \
  --project="${PROJECT}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/artifactregistry.writer"

# Grant Cloud Run admin so the CI account can deploy services.
echo "Granting Cloud Run Admin on ${BIND_SCOPE} for ${SA_EMAIL}"
gcloud projects add-iam-policy-binding "${PROJECT}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.admin"

# Grant Service Account User so deployments can act as the runtime service accounts.
echo "Granting Service Account User on ${BIND_SCOPE} for ${SA_EMAIL}"
gcloud projects add-iam-policy-binding "${PROJECT}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/iam.serviceAccountUser"

echo "All bindings applied. Verify with:"
echo "  gcloud artifacts repositories get-iam-policy ${REPO} --location=${LOCATION} --project=${PROJECT}"
echo "  gcloud projects get-iam-policy ${PROJECT} --flatten=bindings --filter=bindings.members:serviceAccount:${SA_EMAIL}"
