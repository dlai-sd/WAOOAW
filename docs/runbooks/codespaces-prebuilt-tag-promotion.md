# Runbook: Codespaces Prebuilt-Tag Promotion

## Purpose

Use this runbook when today's path is:

1. Validate locally in GitHub Codespaces
2. Build and push one immutable image tag from that Codespace
3. Deploy demo using that exact tag
4. Smoke-test demo
5. Promote the same exact tag to UAT, then prod

This preserves the platform rule that one built image promotes unchanged through demo -> uat -> prod.

---

## Preconditions

Run everything from `/workspaces/WAOOAW` inside the Codespace.

You need:

- Docker working inside the Codespace
- `gcloud` authenticated to project `waooaw-oauth`
- `gh auth status` passing for the repo
- Artifact Registry push permission
- GitHub Actions dispatch permission

Quick checks:

```bash
cd /workspaces/WAOOAW
docker info >/dev/null
gcloud config get-value project
gh auth status
```

Expected GCP project:

```bash
waooaw-oauth
```

---

## Step 1: Bootstrap the local Codespaces stack

Start the demo-aligned local runtime first.

```bash
cd /workspaces/WAOOAW
bash .devcontainer/gcp-auth.sh
bash scripts/codespace-stack.sh bootstrap-env
bash scripts/codespace-stack.sh up all
bash scripts/codespace-stack.sh doctor
bash scripts/codespace-stack.sh urls
```

If you only need a restart after code changes:

```bash
cd /workspaces/WAOOAW
bash scripts/codespace-stack.sh restart all
bash scripts/codespace-stack.sh doctor
```

---

## Step 2: Pick one immutable tag

Use one tag for every service image in this promotion wave.

```bash
cd /workspaces/WAOOAW
export GCP_PROJECT_ID=waooaw-oauth
export GCP_REGION=asia-south1
export GCP_REGISTRY="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/waooaw"
export IMAGE_TAG="$(git rev-parse --short HEAD)-$(date -u +%Y%m%dT%H%M%S)"
printf 'IMAGE_TAG=%s\n' "$IMAGE_TAG"
```

Example output:

```bash
IMAGE_TAG=10da6e2-20260403T154500
```

---

## Step 3: Build and push every deployable image from Codespaces

Authenticate Docker to Artifact Registry:

```bash
cd /workspaces/WAOOAW
gcloud auth configure-docker asia-south1-docker.pkg.dev
docker buildx create --use --name waooaw-builder >/dev/null 2>&1 || docker buildx use waooaw-builder
docker buildx inspect --bootstrap
```

Build and push the exact tag for every service image used by Terraform:

```bash
cd /workspaces/WAOOAW
declare -a BUILDS=(
  "cp-backend|src/CP/BackEnd|src/CP/BackEnd/Dockerfile"
  "cp|src/CP/FrontEnd|src/CP/FrontEnd/Dockerfile"
  "pp-backend|src/PP/BackEnd|src/PP/BackEnd/Dockerfile"
  "pp|src/PP/FrontEnd|src/PP/FrontEnd/Dockerfile"
  "plant-backend|src/Plant/BackEnd|src/Plant/BackEnd/Dockerfile"
  "plant-gateway|src/Plant/Gateway|src/Plant/Gateway/Dockerfile"
  "plant-opa|src/Plant/Gateway/opa|src/Plant/Gateway/opa/Dockerfile"
)

for spec in "${BUILDS[@]}"; do
  IFS='|' read -r image context dockerfile <<< "$spec"
  docker buildx build \
    --platform linux/amd64 \
    --file "$dockerfile" \
    --tag "${GCP_REGISTRY}/${image}:${IMAGE_TAG}" \
    --push \
    "$context"
done
```

Verify the pushed tags exist before dispatching a deployment:

```bash
cd /workspaces/WAOOAW
for image in cp-backend cp pp-backend pp plant-backend plant-gateway plant-opa; do
  gcloud artifacts docker images describe "${GCP_REGISTRY}/${image}:${IMAGE_TAG}" >/dev/null
  echo "verified ${image}:${IMAGE_TAG}"
done
```

---

## Step 4: Deploy demo from the exact prebuilt tag

Use the copied workflow `.github/workflows/waooaw-promote-prebuilt-tag.yml`.

If this workflow is already merged, dispatch with `--ref main`. If you are testing it before merge, replace `main` with the branch that contains the workflow file.

GitHub CLI dispatch:

```bash
cd /workspaces/WAOOAW
gh workflow run waooaw-promote-prebuilt-tag.yml \
  --ref main \
  -f environment=demo \
  -f terraform_action=apply \
  -f image_tag="${IMAGE_TAG}"
```

Watch the latest run:

```bash
cd /workspaces/WAOOAW
RUN_ID="$(gh run list --workflow waooaw-promote-prebuilt-tag.yml --limit 1 --json databaseId -q '.[0].databaseId')"
gh run watch "$RUN_ID"
```

Equivalent raw dispatch with `gh api`:

```bash
cd /workspaces/WAOOAW
gh api \
  repos/dlai-sd/WAOOAW/actions/workflows/waooaw-promote-prebuilt-tag.yml/dispatches \
  -X POST \
  -f ref=main \
  -f inputs[environment]=demo \
  -f inputs[terraform_action]=apply \
  -f inputs[image_tag]="${IMAGE_TAG}"
```

---

## Step 5: Smoke-test demo before any promotion onward

Health checks:

```bash
curl -fsS https://cp.demo.waooaw.com/health
curl -fsS https://pp.demo.waooaw.com/health
curl -fsS https://plant.demo.waooaw.com/health
```

Browser smoke:

```bash
"$BROWSER" https://cp.demo.waooaw.com/
"$BROWSER" https://pp.demo.waooaw.com/
"$BROWSER" https://plant.demo.waooaw.com/docs
```

If you need recent deploy logs:

```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="waooaw-cp" AND severity>=ERROR' \
  --project=waooaw-oauth --limit=30 --freshness=2d

gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="waooaw-plant" AND severity>=ERROR' \
  --project=waooaw-oauth --limit=30 --freshness=2d
```

Do not promote to UAT until demo smoke passes.

---

## Step 6: Promote the exact same tag to UAT

```bash
cd /workspaces/WAOOAW
gh workflow run waooaw-promote-prebuilt-tag.yml \
  --ref main \
  -f environment=uat \
  -f terraform_action=apply \
  -f image_tag="${IMAGE_TAG}"

RUN_ID="$(gh run list --workflow waooaw-promote-prebuilt-tag.yml --limit 1 --json databaseId -q '.[0].databaseId')"
gh run watch "$RUN_ID"
```

UAT smoke:

```bash
curl -fsS https://cp.uat.waooaw.com/health
curl -fsS https://pp.uat.waooaw.com/health
curl -fsS https://plant.uat.waooaw.com/health
```

---

## Step 7: Promote the exact same tag to prod

Only do this after UAT passes.

```bash
cd /workspaces/WAOOAW
gh workflow run waooaw-promote-prebuilt-tag.yml \
  --ref main \
  -f environment=prod \
  -f terraform_action=apply \
  -f image_tag="${IMAGE_TAG}"

RUN_ID="$(gh run list --workflow waooaw-promote-prebuilt-tag.yml --limit 1 --json databaseId -q '.[0].databaseId')"
gh run watch "$RUN_ID"
```

Prod smoke:

```bash
curl -fsS https://www.waooaw.com/health
curl -fsS https://pp.waooaw.com/health
curl -fsS https://plant.waooaw.com/health
```

---

## Fast rollback

If a promoted tag is bad, redeploy the previous known-good tag using the same workflow.

```bash
cd /workspaces/WAOOAW
export PREVIOUS_TAG="<known-good-tag>"
gh workflow run waooaw-promote-prebuilt-tag.yml \
  --ref main \
  -f environment=demo \
  -f terraform_action=apply \
  -f image_tag="${PREVIOUS_TAG}"
```

Repeat for `uat` or `prod` only after confirming the rollback target is correct.