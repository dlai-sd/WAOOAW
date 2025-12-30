# WowEvent Event Bus - Production Dockerfile
FROM python:3.11-slim

LABEL maintainer="WAOOAW Platform <platform@waooaw.com>"
LABEL description="WowEvent Event Bus - Inter-agent communication system"
LABEL version="0.6.5-dev"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
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
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import redis.asyncio as redis; import asyncio; asyncio.run(redis.from_url('redis://redis:6379').ping())" || exit 1

# Expose metrics port
EXPOSE 8080

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV REDIS_URL=redis://redis:6379
ENV EVENT_BUS_ENABLED=true
ENV LOG_LEVEL=INFO

# Run event bus service
CMD ["python", "-m", "waooaw.events.service"]
