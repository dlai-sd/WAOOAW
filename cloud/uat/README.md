# WAOOAW UAT Environment

**Environment**: GCP Cloud Run + Load Balancer  
**Purpose**: User Acceptance Testing with custom domains

## Services

### Platform Portal
- **URL**: https://uat-pp.waooaw.com
- **Backend**: Cloud Run
- **Load Balancer**: Yes (with SSL)
- **OAuth**: Enabled

### Backend API
- **URL**: https://uat-api.waooaw.com
- **Backend**: Cloud Run
- **Load Balancer**: Yes (with SSL)

### Customer Portal
- **URL**: https://uat-www.waooaw.com
- **Backend**: Cloud Run
- **Load Balancer**: Yes (with SSL)

## Deployment

**Method**: Manual deployment via gcloud CLI

```bash
# Deploy Backend
cd backend-v2
gcloud run deploy waooaw-backend-uat \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENV=uat

# Deploy Platform Portal
cd PlatformPortal
gcloud run deploy waooaw-platform-portal-uat \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENV=uat
```

## OAuth Configuration

Add these redirect URIs to Google OAuth Console:
- https://uat-api.waooaw.com/auth/callback
- https://uat-pp.waooaw.com/auth/callback

## DNS Configuration

**Cloud DNS** zones with A/AAAA records pointing to Load Balancer IP:
- uat-api.waooaw.com
- uat-pp.waooaw.com
- uat-www.waooaw.com

## SSL Certificates

Managed by Google Cloud Load Balancer (auto-renewal).

## Testing

Access: https://uat-pp.waooaw.com

Expected flow:
1. Landing page with "Sign in with Google"
2. OAuth flow
3. Dashboard with metrics
