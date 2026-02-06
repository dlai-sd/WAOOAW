# Build stage
FROM node:18-alpine as builder

WORKDIR /app

# Accept build arguments for Vite environment variables
ARG VITE_GOOGLE_CLIENT_ID
ARG VITE_ENVIRONMENT=production

# Copy package files
COPY package*.json ./

# Install dependencies (including dev for build)
RUN npm ci

# Copy source code
COPY . .

# Write build args to .env.production for Vite to pick up during build
RUN if [ -n "$VITE_GOOGLE_CLIENT_ID" ] || [ -n "$VITE_ENVIRONMENT" ]; then \
      rm -f .env.production && \
      if [ -n "$VITE_GOOGLE_CLIENT_ID" ]; then echo "VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID" >> .env.production; fi && \
      if [ -n "$VITE_ENVIRONMENT" ]; then echo "VITE_ENVIRONMENT=$VITE_ENVIRONMENT" >> .env.production; fi ; \
    fi

# Build application (Vite will read from .env.production)
RUN npm run build

# Test stage (Node) - used only for running unit tests in Docker
FROM node:18-alpine as test

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

CMD ["npm", "run", "test", "--", "--run"]

# Runtime stage - Nginx
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

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

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
