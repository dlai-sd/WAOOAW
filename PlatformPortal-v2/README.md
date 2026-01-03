# Platform Portal v2 - Internal Operations Dashboard

**Technology:** Reflex (Python)  
**Purpose:** Internal team portal for agent management, metrics, and operations  
**Domain:** pp.waooaw.com (demo-pp, uat-pp)

## Features

- OAuth login with Google
- Real-time agent metrics dashboard
- System logs and monitoring
- Alert management
- Dark theme with neon accents

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
reflex run

# Build for production
reflex export --backend-only
```

## Environment Variables

```bash
ENV=demo  # demo, uat, or production
BACKEND_URL=https://demo-api.waooaw.com
```

## Deployment

```bash
# Build Docker image
docker build -t asia-south1-docker.pkg.dev/waooaw-oauth/waooaw-containers/waooaw-platform-portal:demo .

# Deploy to Cloud Run
gcloud run deploy waooaw-platform-portal-demo \
    --image=asia-south1-docker.pkg.dev/waooaw-oauth/waooaw-containers/waooaw-platform-portal:demo \
    --region=asia-south1
```
