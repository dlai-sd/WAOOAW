# Plant Gateway - Multi-stage Docker build
FROM python:3.11-slim as builder

WORKDIR /build

# Install dependencies in builder stage
COPY requirements.txt .
COPY requirements-dev.txt .
ARG INSTALL_DEV_DEPS=false
RUN pip install --user --no-cache-dir -r requirements.txt
RUN if [ "$INSTALL_DEV_DEPS" = "true" ]; then pip install --user --no-cache-dir -r requirements-dev.txt; fi

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user first
RUN useradd -m -u 1000 gateway

# Copy installed packages from builder to user directory
COPY --from=builder /root/.local /home/gateway/.local
RUN chown -R gateway:gateway /home/gateway/.local

# Copy application code
COPY middleware/ ./middleware/
COPY infrastructure/ ./infrastructure/
COPY main.py .

# Set PATH for installed packages
ENV PATH=/home/gateway/.local/bin:$PATH

# Ensure application root is importable for test runners that don't add cwd.
ENV PYTHONPATH=/app

# Environment variables (override at runtime)
ENV PLANT_BACKEND_URL=http://plant-backend:8001
ENV REDIS_URL=redis://redis:6379
ENV OPA_URL=http://opa:8181
ENV ENVIRONMENT=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

# Expose gateway port
EXPOSE 8000

# Set ownership and switch to non-root user
RUN chown -R gateway:gateway /app
USER gateway

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
