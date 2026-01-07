# Platform Portal Deployment Guide - Reflex on Cloud Run

**Challenge**: Deploy Reflex (Python web framework with WebSockets) on GCP Cloud Run  
**Date**: January 4, 2026  
**Status**: Planning Phase

---

## 🎯 Core Challenges

### 1. WebSocket Support
- **Issue**: Reflex relies on WebSockets for state synchronization
- **Cloud Run**: Supports WebSockets but requires specific configuration
- **Solution Options**:
  - Option A: Keep WebSockets (requires HTTP/2, session affinity)
  - Option B: Disable WebSockets (production-ready, use polling)

### 2. Port Configuration
- **Reflex Default**: Port 3000 (frontend) + 8000 (backend)
- **Cloud Run**: Single port (configurable via PORT env var)
- **Our Setup**: Nginx on 8080 → proxies to Reflex backend on 8000

### 3. OAuth Redirect URIs
- **Challenge**: Cloud Run URL vs custom domain redirect mismatches
- **Need**: Configure both in Google Cloud Console

---

## 📋 Current Dockerfile Analysis

### Architecture (Multi-stage)
```
Stage 1: Builder
- Python 3.11-slim
- Install Reflex 0.8.24.post1
- Build frontend (reflex export --frontend-only)

Stage 2: Runtime
- Python 3.11-slim + Nginx
- Copy built frontend to /var/www/html/
- Run Nginx (port 8080) + Gunicorn+Uvicorn (port 8000)
- Gunicorn: --workers 1 --worker-class uvicorn.workers.UvicornWorker --timeout 0
```

### Nginx Configuration
```nginx
listen 8080;

location /ping { proxy_pass http://127.0.0.1:8000; }
location /_event { 
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";  # WebSocket support
}
location /_upload { proxy_pass http://127.0.0.1:8000; }
location / { try_files $uri /index.html; }  # SPA fallback
```

### Issues with Current Setup
1. ❌ **Gunicorn doesn't work well with WebSockets** (even with uvicorn workers)
2. ❌ **--timeout 0** is risky on Cloud Run (can cause zombie processes)
3. ⚠️ **WebSocket disabled in rxconfig.py for production** (via `connect_error_component`)
4. ✅ Nginx properly configured for WebSocket proxying

---

## ✅ Recommended Solution

### Option 1: WebSocket-Free (RECOMMENDED)

**Philosophy**: Reflex can work without WebSockets by disabling live state sync

**Changes Needed**:
1. Keep `rxconfig.py` as-is (WebSocket disabled for production)
2. Replace Gunicorn with pure Uvicorn for better async support
3. Use Cloud Run session affinity for consistency

**Updated Dockerfile**:
```dockerfile
# start.sh script:
#!/bin/bash
set -e
echo "Starting Nginx..."
nginx
echo "Starting Reflex backend with Uvicorn..."
cd /app
exec uvicorn asgi:app \\
  --host 0.0.0.0 \\
  --port 8000 \\
  --workers 1 \\
  --log-level info \\
  --access-log \\
  --no-use-colors
```

**Cloud Run Configuration**:
```yaml
env_vars:
  ENV: demo
  PORT: 8080
  BACKEND_URL: https://waooaw-api-demo-ryvhxvrdna-el.a.run.app

resources:
  limits:
    memory: 1Gi
    cpu: 2

# No WebSocket-specific config needed
```

**Pros**:
- ✅ Simpler deployment
- ✅ No WebSocket connection issues
- ✅ Better for serverless (no persistent connections)
- ✅ Works behind load balancers

**Cons**:
- ❌ No live state updates (page refresh needed)
- ❌ Slower perceived performance

---

### Option 2: WebSocket-Enabled (ADVANCED)

**Philosophy**: Keep WebSockets for live state sync (real-time dashboard)

**Changes Needed**:
1. Update `rxconfig.py`:
```python
config = rx.Config(
    app_name="waooaw_portal",
    plugins=[...],
    # Enable WebSocket for production
    connect_error_component=None,  # Always enable WebSocket
)
```

2. Use pure Uvicorn (not Gunicorn):
```bash
uvicorn asgi:app --host 0.0.0.0 --port 8000 --ws websockets
```

3. Cloud Run service.yaml:
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: waooaw-platform-portal-demo
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/sessionAffinity: true  # Critical for WebSocket
    spec:
      containers:
      - image: ...
        ports:
        - containerPort: 8080
          name: h2c  # HTTP/2 for WebSocket support
```

4. Update Nginx for proper WebSocket handling:
```nginx
location /_event {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # WebSocket timeouts
    proxy_read_timeout 86400s;
    proxy_send_timeout 86400s;
}
```

**Pros**:
- ✅ Live state updates (real-time dashboard)
- ✅ Better UX for monitoring/alerts
- ✅ True Reflex experience

**Cons**:
- ❌ More complex deployment
- ❌ Requires session affinity (Cloud Run can have issues)
- ❌ May not work well behind Load Balancer
- ❌ Higher resource usage (persistent connections)

---

## 🔐 OAuth Configuration

### Current Setup (from PlatformPortal_v2.py)
```python
def get_backend_url(self) -> str:
    if self.environment == 'codespace':
        return f'https://{codespace_name}-8000.app.github.dev'
    elif self.environment == 'demo':
        return 'https://demo.waooaw.com/api'
    elif self.environment == 'uat':
        return 'https://uat-api.waooaw.com'
    elif self.environment == 'production':
        return 'https://api.waooaw.com'
```

### OAuth Flow
1. User clicks "Sign In" → Opens modal (google_signin_modal)
2. Modal triggers backend `/auth/google/login`
3. Backend redirects to Google OAuth
4. Google redirects back to `/auth/google/callback`
5. Backend processes callback, generates JWT
6. Backend redirects to Platform Portal with token in URL params
7. Portal extracts token, stores in state

### Required Redirect URIs (Google Cloud Console)

Add these to OAuth 2.0 Client:
```
# Development
https://<codespace-name>-8000.app.github.dev/auth/google/callback

# Demo (current)
https://waooaw-api-demo-ryvhxvrdna-el.a.run.app/auth/google/callback
https://cp.demo.waooaw.com/auth/google/callback
https://pp.demo.waooaw.com/auth/google/callback

# UAT (future)
https://uat-api.waooaw.com/auth/google/callback
https://uat.waooaw.com/auth/google/callback

# Production (future)
https://api.waooaw.com/auth/google/callback
https://waooaw.com/auth/google/callback
```

### Environment Variables Needed
```bash
# Platform Portal container
ENV=demo
PORT=8080  # Cloud Run listens here
BACKEND_URL=https://waooaw-api-demo-ryvhxvrdna-el.a.run.app

# Backend container (already configured)
GOOGLE_CLIENT_ID=<from-gcp>
GOOGLE_CLIENT_SECRET=<from-gcp>
GOOGLE_REDIRECT_URI=https://waooaw-api-demo-ryvhxvrdna-el.a.run.app/auth/google/callback
```

---

## 🚀 Deployment Steps

### Step 1: Choose WebSocket Strategy
- [ ] **Decision**: WebSocket-Free (Option 1) or WebSocket-Enabled (Option 2)?
- [ ] **Recommendation**: Start with Option 1, upgrade to Option 2 if needed

### Step 2: Update Dockerfile
- [ ] Replace Gunicorn with Uvicorn in start.sh
- [ ] Add PORT environment variable support
- [ ] Test local build: `docker build -t platform-portal .`

### Step 3: Build and Push Image
```bash
# Build
docker build -t asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/platform-portal-demo:latest \\
  -f PlatformPortal/Dockerfile \\
  PlatformPortal/

# Push
docker push asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/platform-portal-demo:latest
```

### Step 4: Deploy to Cloud Run
```bash
gcloud run deploy waooaw-platform-portal-demo \\
  --image asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/platform-portal-demo:latest \\
  --region asia-south1 \\
  --platform managed \\
  --allow-unauthenticated \\
  --port 8080 \\
  --memory 1Gi \\
  --cpu 2 \\
  --min-instances 0 \\
  --max-instances 5 \\
  --set-env-vars "ENV=demo,BACKEND_URL=https://waooaw-api-demo-ryvhxvrdna-el.a.run.app" \\
  --session-affinity  # Only if using WebSocket (Option 2)
```

### Step 5: Configure OAuth
- [ ] Go to [Google Cloud Console → APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials)
- [ ] Find OAuth 2.0 Client ID for WAOOAW
- [ ] Add redirect URIs for demo environment
- [ ] Test OAuth flow end-to-end

### Step 6: Test Deployment
```bash
# Health check
curl https://pp.demo.waooaw.com/ping

# WebSocket test (if enabled)
wscat -c wss://pp.demo.waooaw.com/_event

# OAuth test
# 1. Open https://pp.demo.waooaw.com
# 2. Click "Sign In"
# 3. Verify Google OAuth flow
# 4. Check dashboard loads
```

### Step 7: Update Load Balancer (if needed)
```bash
# If using existing load balancer, add backend service for Platform Portal
gcloud compute backend-services create platform-portal-backend \\
  --global \\
  --load-balancing-scheme=EXTERNAL \\
  --protocol=HTTP2  # Required for WebSocket

# Add NEG
gcloud compute network-endpoint-groups create platform-portal-neg \\
  --region=asia-south1 \\
  --network-endpoint-type=serverless \\
  --cloud-run-service=waooaw-platform-portal-demo

# Add to URL map
gcloud compute url-maps add-path-matcher ... \\
  --path-matcher-name=platform-portal \\
  --default-service=platform-portal-backend
```

---

## 🐛 Troubleshooting

### Issue: WebSocket connection fails
**Symptoms**: "WebSocket connection to 'wss://...' failed"
**Solutions**:
1. Check `rxconfig.py` has `connect_error_component=None`
2. Verify Cloud Run has `sessionAffinity: true`
3. Ensure Nginx proxy_http_version is 1.1
4. Check Uvicorn started with `--ws websockets`

### Issue: OAuth redirect fails
**Symptoms**: "redirect_uri_mismatch" error
**Solutions**:
1. Copy exact redirect URI from error message
2. Add to Google Cloud Console OAuth client
3. Wait 5 minutes for propagation
4. Clear browser cache and retry

### Issue: Container crashes on startup
**Symptoms**: Cloud Run shows "Container failed to start"
**Solutions**:
1. Check logs: `gcloud run services logs read waooaw-platform-portal-demo`
2. Verify frontend build exists: `docker run -it <image> ls -la /var/www/html/`
3. Test locally: `docker run -p 8080:8080 <image>`
4. Check Nginx config syntax: `nginx -t`

### Issue: 502 Bad Gateway
**Symptoms**: Nginx returns 502
**Solutions**:
1. Check backend is running: `curl localhost:8000/ping` (inside container)
2. Verify Uvicorn binding to 0.0.0.0:8000 (not 127.0.0.1)
3. Check firewall/network policies
4. Increase Nginx proxy timeout

---

## 📊 Comparison: WebSocket vs WebSocket-Free

| Feature | WebSocket-Free | WebSocket-Enabled |
|---------|----------------|-------------------|
| **Deployment Complexity** | Simple | Complex |
| **Real-time Updates** | No (refresh needed) | Yes |
| **Cloud Run Compatibility** | Excellent | Good |
| **Load Balancer Support** | Excellent | Limited |
| **Resource Usage** | Low | Medium |
| **Cost** | Lower | Higher |
| **Session Affinity** | Not needed | Required |
| **User Experience** | Good | Excellent |
| **Recommended For** | Production start | After validation |

---

## 🎯 Recommendation: Phased Approach

### Phase 1: Deploy WebSocket-Free (MVP)
- ✅ Quick to deploy
- ✅ Reliable on Cloud Run
- ✅ Works with load balancer
- ✅ Test OAuth flow first

### Phase 2: Add WebSocket (Enhancement)
- After OAuth is validated
- After load testing
- When real-time updates become critical
- Consider dedicated WebSocket service

---

## 📝 Next Steps

1. **Decision**: Choose WebSocket strategy (recommend: WebSocket-Free first)
2. **Update**: Modify Dockerfile based on chosen strategy
3. **Build**: Docker image for Platform Portal
4. **Deploy**: To Cloud Run with proper env vars
5. **Configure**: OAuth redirect URIs in Google Cloud Console
6. **Test**: End-to-end OAuth + dashboard flow
7. **Monitor**: Check logs for errors
8. **Optimize**: Add caching, CDN if needed

---

**Questions to Decide**:
- [ ] Do we need real-time updates immediately? (WebSocket)
- [ ] Is Platform Portal behind load balancer? (affects WebSocket)
- [ ] What's priority: quick deployment or best UX?

