# WAOOAW Demo Environment

**Environment**: GCP Cloud Run (asia-south1)  
**Purpose**: Public demo for testing and showcasing features

## Services

### Platform Portal
- **URL**: https://waooaw-platform-portal-demo-ryvhxvrdna-el.a.run.app
- **Port**: 8080 (Cloud Run managed)
- **OAuth**: Enabled

### Backend API
- **URL**: https://waooaw-api-demo-ryvhxvrdna-el.a.run.app
- **Port**: 8080 (Cloud Run managed)
- **OAuth**: Enabled

### Customer Portal (WaooawPortal)
- **URL**: https://waooaw-portal-demo-ryvhxvrdna-el.a.run.app
- **Port**: 8080 (Cloud Run managed)

## Deployment

Automatically deployed via GitHub Actions when pushing to `main` branch.

## Verification

```bash
./verify-platform-portal.sh
```

Tests:
- Root path (/)
- Backend API (/ping)
- Dashboard route
- Login page
- Frontend assets

## OAuth Configuration

**Google OAuth Client ID**: 270293855600-uoag582a6r5eqq4ho43l3mrvob6gpdmq.apps.googleusercontent.com

**Authorized Redirect URIs**:
- https://waooaw-api-demo-ryvhxvrdna-el.a.run.app/auth/callback
- https://waooaw-platform-portal-demo-ryvhxvrdna-el.a.run.app/auth/callback

## Monitoring

```bash
# View logs
gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=waooaw-platform-portal-demo' \
  --limit=50 \
  --project=waooaw-oauth
```

## Known Issues

- **Timeout on first access**: Cold start can take 30-60 seconds
- **httpx timeout**: Fixed in latest deployment (timeout=30.0)
