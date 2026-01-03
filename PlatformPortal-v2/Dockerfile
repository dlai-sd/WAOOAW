# Platform Portal v2 Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install reflex

COPY . .

RUN reflex init

# Export production build
RUN reflex export --backend-only

# Expose port
EXPOSE 3000

# Run application
CMD reflex run --env prod --backend-only
