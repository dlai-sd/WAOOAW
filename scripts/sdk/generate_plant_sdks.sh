#!/usr/bin/env bash
set -euo pipefail

# CI/local helper: generate Plant SDKs from the Gateway OpenAPI spec.
# - Does NOT commit generated artifacts.
# - Output is written under .generated/plant-sdk/

GATEWAY_OPENAPI_URL="${GATEWAY_OPENAPI_URL:-http://localhost:8000/api/openapi.json}"
OUT_DIR="${OUT_DIR:-.generated/plant-sdk}"
GENERATOR_IMAGE="${OPENAPI_GENERATOR_IMAGE:-openapitools/openapi-generator-cli:v7.6.0}"

mkdir -p "$OUT_DIR"

SPEC_PATH="$OUT_DIR/openapi.json"
PY_OUT="$OUT_DIR/python"
JS_OUT="$OUT_DIR/js"

echo "Fetching OpenAPI spec from: $GATEWAY_OPENAPI_URL"
curl -fsSL "$GATEWAY_OPENAPI_URL" > "$SPEC_PATH"

rm -rf "$PY_OUT" "$JS_OUT"

echo "Generating Python client SDK..."
docker run --rm \
  -v "$PWD:/work" \
  -w /work \
  "$GENERATOR_IMAGE" generate \
  -i "/work/$SPEC_PATH" \
  -g python \
  -o "/work/$PY_OUT" \
  --additional-properties=packageName=waooaw_plant_sdk,projectName=waooaw-plant-sdk

echo "Generating JavaScript (TypeScript fetch) client SDK..."
docker run --rm \
  -v "$PWD:/work" \
  -w /work \
  "$GENERATOR_IMAGE" generate \
  -i "/work/$SPEC_PATH" \
  -g typescript-fetch \
  -o "/work/$JS_OUT" \
  --additional-properties=npmName=@waooaw/plant-sdk,supportsES6=true

# Basic sanity checks ("generated and tested", not stubs)
if [[ ! -f "$PY_OUT/setup.py" && ! -f "$PY_OUT/pyproject.toml" ]]; then
  echo "ERROR: Python SDK generation missing packaging metadata" >&2
  exit 1
fi

if [[ ! -f "$JS_OUT/package.json" ]]; then
  echo "ERROR: JS SDK generation missing package.json" >&2
  exit 1
fi

echo "SDK generation complete: $OUT_DIR"