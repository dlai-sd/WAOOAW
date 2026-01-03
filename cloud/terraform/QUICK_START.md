# 🚀 Quick Start - Demo Testing

## Current Status
✅ Infrastructure deployed  
⏳ SSL provisioning  
❌ DNS not configured  

## 3 Steps to Test OAuth Fix

### Step 1: Configure DNS (5 min)
Login to GoDaddy → DNS Management → Add A Records:
```
cp.demo.waooaw.com  →  35.190.6.91
pp.demo.waooaw.com  →  35.190.6.91
```

### Step 2: Update OAuth Console (3 min)
https://console.cloud.google.com/apis/credentials

Add these exact URLs:
```
Origins:
• https://cp.demo.waooaw.com
• https://pp.demo.waooaw.com

Redirects:
• https://cp.demo.waooaw.com/api/auth/callback
• https://pp.demo.waooaw.com/api/auth/callback
```

### Step 3: Wait for SSL → Test (15 min)
```bash
# Monitor SSL (wait for ACTIVE)
watch -n 30 'gcloud compute ssl-certificates list --global | grep demo'

# Once ACTIVE, test OAuth
open https://pp.demo.waooaw.com
# Click "Sign in with Google"
# Should complete in ~3 seconds (not 2 minutes!)
```

## Quick Commands

```bash
# Check status
/workspaces/WAOOAW/cloud/terraform/check-status.sh

# Run full tests (after DNS)
/workspaces/WAOOAW/cloud/terraform/test-infrastructure.sh

# View Terraform state
cd /workspaces/WAOOAW/cloud/terraform
terraform show

# Deploy UAT (when ready)
terraform workspace new uat
terraform apply -var-file=environments/uat.tfvars
```

## Why This Fixes OAuth

**Before**: waooaw-api-demo-xxx.run.app → waooaw-platform-portal-xxx.run.app  
❌ Cross-origin redirect = Browser blocks for 2 minutes

**After**: pp.demo.waooaw.com/api → pp.demo.waooaw.com/callback  
✅ Same domain = Browser allows redirect instantly

## Need Help?

See [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) for full details.
