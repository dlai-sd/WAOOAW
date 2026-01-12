# Build stage
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (including dev for build)
RUN npm ci

# Copy source code
COPY . .

# Build application
RUN npm run build

# Runtime stage - Nginx
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

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
