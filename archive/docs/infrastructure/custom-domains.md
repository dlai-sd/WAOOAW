# Custom Domain Configuration for WAOOAW

## Overview
This document outlines the custom domain setup for WAOOAW platform across all environments.

## Quick Start

```bash
# Setup domains for any environment
cd /workspaces/WAOOAW/infrastructure/gcp
chmod +x deploy.sh

# Choose environment: demo, uat, or production
./deploy.sh demo
```

## Domain Structure

### Demo Environment
- **Backend API**: `demo-api.waooaw.com` → waooaw-api-demo
- **Customer Portal**: `demo-www.waooaw.com` → waooaw-portal-demo
- **Platform Portal**: `demo-pp.waooaw.com` → waooaw-platform-portal-demo

### UAT Environment
- **Backend API**: `uat-api.waooaw.com` → waooaw-api-uat
- **Customer Portal**: `uat-www.waooaw.com` → waooaw-portal-uat
- **Platform Portal**: `uat-pp.waooaw.com` → waooaw-platform-portal-uat

### Production Environment
- **Backend API**: `api.waooaw.com` → waooaw-api-prod
- **Customer Portal**: `www.waooaw.com` → waooaw-portal-prod
- **Platform Portal**: `pp.waooaw.com` → waooaw-platform-portal-prod

## DNS Records (Cloudflare/Namecheap/etc.)

Add these CNAME records in your DNS provider:

```
# Demo Environment
demo-api.waooaw.com    CNAME  ghs.googlehosted.com
demo-www.waooaw.com    CNAME  ghs.googlehosted.com
demo-pp.waooaw.com     CNAME  ghs.googlehosted.com

# UAT Environment
uat-api.waooaw.com     CNAME  ghs.googlehosted.com
uat-www.waooaw.com     CNAME  ghs.googlehosted.com
uat-pp.waooaw.com      CNAME  ghs.googlehosted.com

# Production Environment
api.waooaw.com         CNAME  ghs.googlehosted.com
www.waooaw.com         CNAME  ghs.googlehosted.com
pp.waooaw.com          CNAME  ghs.googlehosted.com
```

## Setup Steps

### 1. Run the automated setup script

```bash
cd /workspaces/WAOOAW/infrastructure/gcp
chmod +x deploy.sh

# Choose your environment
./deploy.sh demo      # For demo environment
./deploy.sh uat       # For UAT environment  
./deploy.sh production # For production environment
```

The script will:
- ✅ Check GCP authentication
- ✅ Create domain mappings for all 3 services
- ✅ Provide DNS configuration instructions
- ✅ Display OAuth Console configuration

### 2. Configure DNS
After running the script, add the DNS records shown above to your domain registrar.

### 3. Wait for SSL provisioning
Google Cloud Run will automatically provision SSL certificates. This takes 15 minutes to 24 hours.

### 4. Verify mappings
```bash
# Check status
gcloud run domain-mappings list --region=asia-south1

# Test endpoints
curl https://demo-api.waooaw.com/health
curl https://demo-www.waooaw.com
curl https://demo-pp.waooaw.com/ping
```

## OAuth Configuration

Once domains are active, update Google OAuth Console:

### Authorized JavaScript Origins
```
https://demo-www.waooaw.com
https://demo-pp.waooaw.com
https://uat-www.waooaw.com
https://uat-pp.waooaw.com
https://www.waooaw.com
https://pp.waooaw.com
```

### Authorized Redirect URIs
```
https://demo-api.waooaw.com/auth/callback
https://uat-api.waooaw.com/auth/callback
https://api.waooaw.com/auth/callback
```

## Troubleshooting

### Certificate Provisioning Failed
```bash
# Check domain mapping status
gcloud run domain-mappings describe demo-api.waooaw.com --region=asia-south1

# Verify DNS records
dig demo-api.waooaw.com CNAME
```

### Domain Not Resolving
- DNS changes can take up to 48 hours to propagate
- Verify CNAME record is correct: `ghs.googlehosted.com`
- Clear DNS cache: `ipconfig /flushdns` (Windows) or `sudo killall -HUP mDNSResponder` (Mac)

### OAuth Errors After Domain Setup
1. Verify domains in Google OAuth Console
2. Check CORS configuration in backend
3. Verify redirect URIs match exactly

## Migration from Cloud Run URLs

After custom domains are working:

1. Update GitHub Secrets (if needed)
2. Test OAuth flow on each environment
3. Update any hardcoded URLs in frontend
4. Monitor for any issues

## Monitoring

```bash
# Watch domain mapping status
watch -n 30 'gcloud run domain-mappings list --region=asia-south1'

# Check SSL certificate status
gcloud run domain-mappings describe demo-api.waooaw.com \
  --region=asia-south1 \
  --format="value(status.conditions)"
```

## Cost Impact

Custom domain mapping: **FREE**
SSL certificates: **FREE** (auto-provisioned by Google)

No additional charges for using custom domains with Cloud Run.
