# PP Gateway Dockerfile
# Multi-stage build for production-ready container

FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create build directory
WORKDIR /build

# Copy requirements and install dependencies
COPY src/gateway/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt


FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 gateway && \
    mkdir -p /app && \
    chown -R gateway:gateway /app

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/gateway/.local

# Copy application code
COPY src/gateway/middleware ./middleware
COPY src/gateway/pp_gateway ./pp_gateway
COPY infrastructure/feature_flags ./infrastructure/feature_flags

# Set environment variables
ENV PATH=/home/gateway/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production \
    PORT=8001 \
    GATEWAY_TYPE=PP

# Switch to non-root user
USER gateway

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Expose port
EXPOSE 8001

# Run application
CMD ["python", "-m", "uvicorn", "pp_gateway.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
