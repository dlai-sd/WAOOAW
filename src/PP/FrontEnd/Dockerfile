# Build stage
FROM node:18-alpine as builder

WORKDIR /app

# Optional build-time config.
# In CI we pass build args and write a .env.production so Vite picks them up during `vite build`.
# Locally, if you don't pass build args, we don't override any existing .env files.
ARG VITE_GOOGLE_CLIENT_ID
ARG VITE_ENVIRONMENT
ARG VITE_API_BASE_URL

# Copy package files
COPY package*.json ./

# Install dependencies (including dev for build)
RUN npm ci

# Copy source code
COPY . .

RUN if [ -n "$VITE_GOOGLE_CLIENT_ID" ] || [ -n "$VITE_ENVIRONMENT" ] || [ -n "$VITE_API_BASE_URL" ]; then \
            rm -f .env.production && \
            if [ -n "$VITE_GOOGLE_CLIENT_ID" ]; then echo "VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID" >> .env.production; fi && \
            if [ -n "$VITE_ENVIRONMENT" ]; then echo "VITE_ENVIRONMENT=$VITE_ENVIRONMENT" >> .env.production; fi ; \
            if [ -n "$VITE_API_BASE_URL" ]; then echo "VITE_API_BASE_URL=$VITE_API_BASE_URL" >> .env.production; fi ; \
        fi

# Build application
RUN npm run build

# Runtime stage - Nginx
FROM nginx:alpine

# Copy custom nginx config (replaces default nginx.conf with pid /tmp/nginx.pid)
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Use nginx user and set permissions for directories nginx needs to write to
RUN chown -R nginx:nginx /usr/share/nginx/html && \
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

# Start Nginx in foreground mode
CMD ["nginx", "-g", "daemon off;"]
