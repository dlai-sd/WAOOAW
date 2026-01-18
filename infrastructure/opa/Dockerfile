# OPA Service Dockerfile
# Version: 1.0
# Base: Open Policy Agent official image

FROM openpolicyagent/opa:0.60.0-rootless

# Metadata
LABEL maintainer="Platform Team <platform@waooaw.com>"
LABEL description="OPA Policy Service for API Gateway"
LABEL version="1.0"

# Set working directory
WORKDIR /policies

# Copy Rego policies
COPY policies/*.rego ./

# Copy configuration
COPY config/config.yaml /config/

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["/opa", "exec", "--decision", "system/health/check", "--bundle", "/policies"]

# Expose OPA port
EXPOSE 8181

# Run OPA server with configuration
ENTRYPOINT ["/opa"]
CMD ["run", \
     "--server", \
     "--addr=:8181", \
     "--config-file=/config/config.yaml", \
     "--log-level=info", \
     "--log-format=json", \
     "/policies"]
