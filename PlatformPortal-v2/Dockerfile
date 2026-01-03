# Stage 1: Build Frontend
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl unzip && rm -rf /var/lib/apt/lists/*

# Install Reflex
RUN pip install --no-cache-dir reflex

# Copy application code
COPY . .

# Initialize and build frontend
RUN reflex init
RUN reflex export --frontend-only --no-zip

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Copy built app from builder
COPY --from=builder /app /app

# Copy bun installation from builder (Reflex dependency)
COPY --from=builder /root/.local/share/reflex /root/.local/share/reflex

# Install Reflex in runtime
RUN pip install --no-cache-dir reflex

EXPOSE 8080

CMD ["reflex", "run", "--env", "prod", "--loglevel", "info"]
