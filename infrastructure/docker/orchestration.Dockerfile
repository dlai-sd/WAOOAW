# Orchestration Runtime - Production Dockerfile
FROM python:3.11-slim

LABEL maintainer="WAOOAW Platform <platform@waooaw.com>"
LABEL description="Orchestration Runtime - Task coordination and workflow execution"
LABEL version="0.7.3"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY waooaw/ waooaw/
COPY backend/app/ backend/app/

# Create non-root user
RUN useradd -m -u 1000 waooaw && \
    chown -R waooaw:waooaw /app

USER waooaw

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8082/health || exit 1

# Expose API port
EXPOSE 8082

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV REDIS_URL=redis://redis:6379
ENV ORCHESTRATION_ENABLED=true
ENV LOG_LEVEL=INFO
ENV MAX_WORKERS=10
ENV MIN_WORKERS=2

# Run orchestration service
CMD ["python", "-m", "waooaw.orchestration.service"]
