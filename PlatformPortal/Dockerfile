# Multi-stage Dockerfile for Reflex Frontend (Platform Portal)
# Optimized for production deployment on Cloud Run

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    unzip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (required by Reflex for frontend compilation)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Pre-build: Initialize Reflex (keep export out to avoid flag mismatch in CI)
RUN reflex init

# Stage 2: Production
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for Reflex runtime
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code from builder (includes pre-compiled frontend)
COPY --from=builder /app .

# Create non-root user
RUN useradd -m -u 1000 waooaw && chown -R waooaw:waooaw /app
USER waooaw

# Expose port (Cloud Run expects PORT env variable)
ENV PORT=3000
EXPOSE 3000

# Health check (lenient for slow Reflex startup)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
  CMD curl -f http://localhost:3000/ || exit 1

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    REFLEX_ENV=production

# Start command - Reflex production server
# Reflex automatically binds to 0.0.0.0 when PORT env var is set
CMD ["reflex", "run", "--env", "prod", "--loglevel", "warning"]
