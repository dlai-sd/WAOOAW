# Multi-stage Dockerfile for Reflex Frontend (Platform Portal)
# Optimized for production deployment on Cloud Run
# Prebuilds app at build time to avoid runtime compilation

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

# Install Node.js 20.x (required by Reflex for frontend compilation)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Prebuild: Initialize and export production build
RUN reflex init && reflex export --frontend-only --no-zip

# Stage 2: Production
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x for Reflex runtime
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code and prebuilt frontend from builder
COPY --from=builder /app .

# Create non-root user
RUN useradd -m -u 1000 waooaw && chown -R waooaw:waooaw /app
USER waooaw

# Expose port (Cloud Run expects PORT env variable)
ENV PORT=3000
EXPOSE 3000

# Health check (fast on prebuilt app)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:3000/ || exit 1

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    REFLEX_ENV=production

# Start command - Serve prebuilt production app
CMD ["reflex", "run", "--env", "prod", "--loglevel", "warning"]
