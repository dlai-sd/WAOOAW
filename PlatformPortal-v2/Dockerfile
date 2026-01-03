# Platform Portal v2 - Reflex Full Stack Application
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Reflex
RUN pip install --no-cache-dir reflex

# Copy application code
COPY . .

# Initialize Reflex (creates .web directory structure)
RUN reflex init

# Expose port 8000 (Reflex backend + frontend)
EXPOSE 8000

# Run Reflex in production mode
# This starts both the FastAPI backend and serves the frontend
CMD ["reflex", "run", "--env", "prod", "--loglevel", "info"]
