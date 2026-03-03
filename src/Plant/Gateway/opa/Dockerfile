# src/Plant/Gateway/opa/Dockerfile
# Build-once OPA bundle image.
# Rego policies are CODE — they are baked into the image at build time.
# Runtime config (log level, server address) is injected via Cloud Run env vars at deploy time.
# NEVER bake environment-specific URLs, secrets, or env names into this file.
#
# Image promotion: build once, deploy to demo, promote same tag to uat → prod.
# Terraform injects the tag via:  -var="plant_opa_image=<registry>/plant-opa:<TAG>"

# Pin to a specific digest for reproducibility. Use a recent stable release.
FROM openpolicyagent/opa:0.68.0

WORKDIR /app

# Bake policies into the image — these are code, not config.
COPY policies/ ./policies/

# Runtime configuration is passed as Cloud Run environment variables.
# These are non-secret defaults — override at deploy time with env vars.
ENV OPA_LOG_LEVEL=info
ENV PORT=8181

# Health check: OPA has a built-in health endpoint.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["/opa", "health"]

EXPOSE 8181

# OPA runs as non-root by default (uid 1000 in the official image).
# Do not add USER directive — the official image already handles this.

# Start OPA in server mode.
# --addr: bind to all interfaces on PORT (Cloud Run requirement).
# --log-format=json: structured logs for Cloud Logging.
# ./policies: serve the baked bundle.
# Note: OPA_LOG_LEVEL is read from env automatically when --log-level is not set.
CMD ["run", \
     "--server", \
     "--addr=0.0.0.0:8181", \
     "--log-format=json", \
     "./policies"]
