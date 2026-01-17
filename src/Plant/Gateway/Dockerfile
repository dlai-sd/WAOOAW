# Plant Gateway - Multi-stage Docker build
FROM python:3.11-slim as builder

WORKDIR /build

# Install dependencies in builder stage
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY middleware/ ./middleware/
COPY infrastructure/ ./infrastructure/
COPY main.py .

# Set PATH for installed packages
ENV PATH=/root/.local/bin:$PATH

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

# Run as non-root user
RUN useradd -m -u 1000 gateway && chown -R gateway:gateway /app
USER gateway

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
