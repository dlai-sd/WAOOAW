# Platform Portal v2 Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required by Reflex
RUN apt-get update && apt-get install -y \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN pip install reflex

COPY . .

# Initialize Reflex project
RUN reflex init

# Expose port 8000 (Reflex backend/API) and 3000 (frontend)
EXPOSE 8000 3000

# Run in production mode (serves both frontend and backend)
CMD ["reflex", "run", "--env", "prod", "--loglevel", "info"]
