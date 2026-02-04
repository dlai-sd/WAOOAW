# Multi-stage Dockerfile for WAOOAW Plant Backend
# Optimized for production deployment on Cloud Run

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Build wheels for all dependencies
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt


# Stage 2: Runtime
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder
COPY --from=builder /build/wheels /wheels
COPY --from=builder /build/requirements.txt .

# Install dependencies from wheels (no network access needed)
RUN pip install --no-cache /wheels/* && \
    rm -rf /wheels

# Copy application code
COPY --chown=appuser:appuser . .

# Ensure entrypoint is executable (do this before dropping privileges)
USER root
RUN chmod +x /app/docker-entrypoint.sh

# Switch to non-root user
USER appuser

# Health check (use PORT env var with default 8000)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Expose port (Cloud Run provides PORT env var, default 8000)
EXPOSE 8000

# Environment variables (can be overridden by Cloud Run)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=info \
    WORKERS=4 \
    PORT=8000

# Start application (use PORT env var from Cloud Run)
ENTRYPOINT ["/app/docker-entrypoint.sh"]
