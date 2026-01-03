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

# Initialize Reflex project and build frontend during image build
RUN reflex init
RUN reflex export --no-zip

# Expose port 8000 (Reflex serves both frontend and backend from this port)
EXPOSE 8000

# Run in production mode serving the pre-built frontend
CMD ["reflex", "run", "--env", "prod", "--loglevel", "debug"]
