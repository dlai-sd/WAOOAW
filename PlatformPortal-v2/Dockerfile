# Platform Portal v2 Dockerfile - Static Build Approach
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies required by Reflex
RUN apt-get update && apt-get install -y \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN pip install reflex

COPY . .

# Initialize and export static build
RUN reflex init
RUN reflex export --no-zip

# Production stage - serve with nginx
FROM nginx:alpine

# Copy built static files
COPY --from=builder /app/.web/build/client /usr/share/nginx/html

# Copy nginx config to listen on port 8000
RUN echo 'server { \
    listen 8000; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf && rm -f /etc/nginx/conf.d/default.conf.default

# Expose port 8000
EXPOSE 8000

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
