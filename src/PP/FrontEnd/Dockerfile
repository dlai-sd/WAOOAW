# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (including dev for build)
RUN npm ci

# Copy source code
COPY . .

# Build application. All environment-specific values are injected at runtime
# via docker-entrypoint.sh → window.__WAOOAW_PP_RUNTIME_CONFIG__. Do NOT bake
# VITE_* secrets here — the same image is promoted through dev → uat → prod.
RUN npm run build

# Test stage (Node) - used only for running unit tests in Docker
FROM node:20-alpine AS test

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

CMD ["npm", "run", "test", "--", "--run"]

# Runtime stage - Nginx
FROM nginx:alpine

# Ship both configs in the same image and choose at container start.
COPY nginx.conf /etc/nginx/nginx.cloudrun.conf
COPY nginx.local.conf /etc/nginx/nginx.local.conf

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Runtime config entrypoint (writes /pp-runtime-config.js based on env vars at startup)
COPY docker-entrypoint.sh /docker-entrypoint.sh

# Use nginx user and set permissions for directories nginx needs to write to
RUN chmod +x /docker-entrypoint.sh && \
    chown -R nginx:nginx /usr/share/nginx/html && \
    mkdir -p /var/log/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    mkdir -p /tmp/nginx /tmp/client_temp /tmp/proxy_temp /tmp/fastcgi_temp /tmp/uwsgi_temp /tmp/scgi_temp && \
    chown -R nginx:nginx /tmp/nginx /tmp/client_temp /tmp/proxy_temp /tmp/fastcgi_temp /tmp/uwsgi_temp /tmp/scgi_temp

USER nginx

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/ || exit 1

# Expose port
EXPOSE 8080

# Writes pp-runtime-config.js from env vars, then starts nginx
ENTRYPOINT ["/docker-entrypoint.sh"]
