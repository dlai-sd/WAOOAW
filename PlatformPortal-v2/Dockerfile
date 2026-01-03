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

# Stage 2: Runtime with Nginx
FROM python:3.11-slim

WORKDIR /app

# Install Nginx and runtime dependencies
RUN apt-get update && apt-get install -y nginx unzip curl && rm -rf /var/lib/apt/lists/*

# Copy built app from builder
COPY --from=builder /app /app

# Copy bun installation from builder (Reflex dependency)
COPY --from=builder /root/.local/share/reflex /root/.local/share/reflex

# Install Reflex and production server in runtime
RUN pip install --no-cache-dir reflex gunicorn uvicorn[standard]

# Copy static frontend build to Nginx directory
RUN cp -r /app/.web/build/client/* /var/www/html/ 2>/dev/null || \
    (echo "Frontend not pre-built, will serve from .web directory" && \
     mkdir -p /var/www/html && echo "<h1>Building...</h1>" > /var/www/html/index.html)

# Create Nginx config
RUN echo 'server {\n\
    listen 8080;\n\
    server_name _;\n\
    \n\
    # Serve static frontend files\n\
    root /var/www/html;\n\
    index index.html;\n\
    \n\
    # Backend API endpoints (Reflex uses /ping, /_event etc)\n\
    location /ping {\n\
        proxy_pass http://127.0.0.1:8000/ping;\n\
    }\n\
    \n\
    location /_event {\n\
        proxy_pass http://127.0.0.1:8000/_event;\n\
        proxy_http_version 1.1;\n\
        proxy_set_header Upgrade $http_upgrade;\n\
        proxy_set_header Connection "upgrade";\n\
        proxy_set_header Host $host;\n\
    }\n\
    \n\
    location /_upload {\n\
        proxy_pass http://127.0.0.1:8000/_upload;\n\
    }\n\
    \n\
    # Try static files first, then fallback to index.html (SPA)\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
}' > /etc/nginx/sites-available/default

# Create startup script with Gunicorn (significantly faster than reflex run)
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Starting Nginx..."\n\
nginx\n\
echo "Starting Reflex backend with Gunicorn..."\n\
cd /app\n\
exec gunicorn --bind 0.0.0.0:8000 --workers 1 --worker-class uvicorn.workers.UvicornWorker --threads 16 --timeout 0 --access-logfile - --error-logfile - "PlatformPortal_v2.PlatformPortal_v2:app()"\n\
' > /app/start.sh && chmod +x /app/start.sh

EXPOSE 8080

CMD ["/app/start.sh"]
