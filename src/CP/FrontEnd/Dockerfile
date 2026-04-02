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
# via docker-entrypoint.sh → window.__WAOOAW_RUNTIME_CONFIG__. Do NOT bake
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

# Runtime config entrypoint (writes /runtime-config.js based on env vars)
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Create non-root user
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser && \
    chown -R appuser:appuser /usr/share/nginx/html && \
    chown -R appuser:appuser /var/cache/nginx && \
    chown -R appuser:appuser /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R appuser:appuser /var/run/nginx.pid

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/ || exit 1

# Expose port
EXPOSE 8080

# Start Nginx (after generating runtime-config.js)
ENTRYPOINT ["/docker-entrypoint.sh"]
