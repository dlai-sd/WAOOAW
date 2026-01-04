# OAuth Testing and Configuration Guide

**Date**: 2025-01-03  
**Environment**: Demo  
**Status**: Ready for Testing  
**Previous Work**: Commit caf60b2 (OAuth code implementation)

---

## Overview

OAuth Sign In is now ready for testing with the deployed demo infrastructure. The code is already implemented (see [OAUTH_IMPLEMENTATION.md](OAUTH_IMPLEMENTATION.md)), and the infrastructure is live (see [INFRASTRUCTURE_DEPLOYMENT.md](INFRASTRUCTURE_DEPLOYMENT.md)).

### What's Ready

✅ **Backend** - FastAPI OAuth endpoints deployed to Cloud Run  
✅ **Customer Portal** - React auth.js with Sign In button  
✅ **Platform Portal** - Reflex login_redirect wired up  
✅ **Infrastructure** - HTTPS domains with SSL certificates  
✅ **Credentials** - Client ID/Secret in Secret Manager

### What Needs Configuration

⚠️ **Google Cloud Console** - OAuth consent screen and redirect URIs  
🧪 **Testing** - End-to-end OAuth flow validation

---

## Google Cloud Console Configuration

### Step 1: OAuth Consent Screen

1. Go to: https://console.cloud.google.com/apis/credentials/consent?project=waooaw-oauth

2. Click **"OAuth consent screen"** tab

3. Verify/Update:
   - **Application name**: WAOOAW
   - **User support email**: your-email@gmail.com
   - **Application home page**: https://cp.demo.waooaw.com
   - **Application privacy policy**: https://cp.demo.waooaw.com/privacy
   - **Application terms of service**: https://cp.demo.waooaw.com/terms
   - **Authorized domains**: 
     - `waooaw.com`
     - `demo.waooaw.com`

4. **Scopes** - Add these OAuth scopes:
   - `openid`
   - `email`
   - `profile`

5. **Test users** - Add your email for testing (if app is in "Testing" mode)

### Step 2: OAuth 2.0 Client ID

1. Go to: https://console.cloud.google.com/apis/credentials?project=waooaw-oauth

2. Click on the existing OAuth 2.0 Client ID or create new one

3. **Authorized redirect URIs** - Add ALL of these:
   ```
   https://cp.demo.waooaw.com/auth/callback
   https://pp.demo.waooaw.com/auth/callback
   https://waooaw-api-demo-ryvhxvrdna-el.a.run.app/auth/google/callback
   https://waooaw-portal-demo-ryvhxvrdna-el.a.run.app/auth/callback
   https://waooaw-platform-portal-demo-ryvhxvrdna-el.a.run.app/auth/callback
   ```

4. Click **Save**

5. Note down:
   - **Client ID**: Should match Secret Manager value (270293855600-...)
   - **Client Secret**: Should match Secret Manager value (GOCSPX-...)

---

## Current OAuth Configuration

### Credentials (in Secret Manager)

```bash
# Verify credentials
gcloud secrets versions access latest --secret=GOOGLE_CLIENT_ID
# Output: 270293855600-uoag582a6r5eqq4ho43l3mrvob6gpdmq.apps.googleusercontent.com

gcloud secrets versions access latest --secret=GOOGLE_CLIENT_SECRET
# Output: GOCSPX-Xwuta_OpYNPX3... (truncated for security)
```

### Backend Environment Variables

Cloud Run services already have these environment variables configured:
- `GOOGLE_CLIENT_ID`: (from Secret Manager)
- `GOOGLE_CLIENT_SECRET`: (from Secret Manager)
- `GOOGLE_REDIRECT_URI`: Set per environment (see backend-v2/app/auth/oauth_v2.py)

### Frontend Configuration

**Customer Portal** (`/frontend/js/auth.js`):
```javascript
function getBackendUrl() {
  const hostname = window.location.hostname;
  if (hostname.includes('waooaw-portal-demo') || hostname.includes('cp.demo.waooaw.com')) {
    return 'https://waooaw-api-demo-ryvhxvrdna-el.a.run.app';
  }
  // ... other environments
}
```

**Platform Portal** (`/PlatformPortal-v2/PlatformPortal_v2/PlatformPortal_v2.py`):
```python
def get_backend_url(self):
    if self.environment == 'demo':
        return 'https://waooaw-api-demo-ryvhxvrdna-el.a.run.app'
    # ... other environments
```

---

## OAuth Flow Testing

### Customer Portal Sign In

1. **Navigate to**: https://cp.demo.waooaw.com

2. **Click "Sign In" button**

3. **Expected Flow**:
   ```
   Customer Portal
   └─> Redirects to: https://waooaw-api-demo-ryvhxvrdna-el.a.run.app/auth/google/login
       └─> Backend redirects to: Google OAuth consent screen
           └─> User approves (selects Google account)
               └─> Google redirects to: https://waooaw-api-demo-ryvhxvrdna-el.a.run.app/auth/google/callback
                   └─> Backend exchanges code for tokens
                       └─> Backend redirects to: https://cp.demo.waooaw.com/auth/callback?token=<JWT>
                           └─> Frontend stores token in localStorage
                               └─> Frontend redirects to: https://cp.demo.waooaw.com/marketplace.html
   ```

4. **Verify**:
   - Check browser localStorage: `localStorage.getItem('authToken')`
   - Check localStorage: `localStorage.getItem('userEmail')`
   - Navbar should show user email instead of "Sign In"

### Platform Portal Sign In

1. **Navigate to**: https://pp.demo.waooaw.com

2. **Click "Sign In" button**

3. **Expected Flow**:
   ```
   Platform Portal (Reflex)
   └─> Python calls: PlatformState.login_redirect()
       └─> Redirects to: https://waooaw-api-demo-ryvhxvrdna-el.a.run.app/auth/google/login
           └─> Backend redirects to: Google OAuth consent screen
               └─> User approves
                   └─> Google redirects to: https://waooaw-api-demo-ryvhxvrdna-el.a.run.app/auth/google/callback
                       └─> Backend exchanges code for tokens
                           └─> Backend redirects to: https://pp.demo.waooaw.com/auth/callback?token=<JWT>
                               └─> Frontend stores token (Reflex session)
                                   └─> Redirects to dashboard
   ```

4. **Verify**:
   - Reflex session contains user email
   - Dashboard shows authenticated user
   - Token stored in Reflex State

---

## Testing Commands

### Test Backend OAuth Endpoints

```bash
# Health check
curl https://waooaw-api-demo-ryvhxvrdna-el.a.run.app/health
# Expected: {"status": "healthy"}

# Test OAuth login endpoint (will redirect to Google)
curl -I https://waooaw-api-demo-ryvhxvrdna-el.a.run.app/auth/google/login
# Expected: HTTP/2 307 (redirect to accounts.google.com)

# Check backend logs
gcloud run services logs read waooaw-api-demo --region=asia-south1 --limit=50
```

### Test Frontend Sign In Button

**Customer Portal**:
```bash
# Open browser console at https://cp.demo.waooaw.com
# In console:
document.getElementById('sign-in-btn').click()
# Should redirect to Google OAuth
```

**Platform Portal**:
```bash
# Open browser console at https://pp.demo.waooaw.com
# Click Sign In button
# Should redirect to Google OAuth
```

### Verify Token Storage

**After successful sign in**:
```javascript
// Browser console:
localStorage.getItem('authToken')
// Expected: Long JWT string (ey...)

localStorage.getItem('userEmail')
// Expected: your-email@gmail.com

localStorage.getItem('userName')
// Expected: Your Name
```

---

## Troubleshooting

### Error: `redirect_uri_mismatch`

**Symptom**: Google shows "Error 400: redirect_uri_mismatch"

**Cause**: Redirect URI not configured in Google Cloud Console

**Solution**:
1. Go to https://console.cloud.google.com/apis/credentials?project=waooaw-oauth
2. Edit OAuth 2.0 Client ID
3. Add exact redirect URI from error message
4. Wait 5 minutes for changes to propagate

### Error: `invalid_client`

**Symptom**: Backend logs show "invalid_client" error

**Cause**: CLIENT_ID or CLIENT_SECRET mismatch

**Solution**:
```bash
# Verify credentials match
gcloud secrets versions access latest --secret=GOOGLE_CLIENT_ID
gcloud secrets versions access latest --secret=GOOGLE_CLIENT_SECRET

# Check Cloud Run environment variables
gcloud run services describe waooaw-api-demo --region=asia-south1 --format=yaml | grep -A 5 env
```

### Error: `access_denied`

**Symptom**: User clicks "Deny" on Google consent screen

**Cause**: User rejected OAuth consent

**Solution**: User must click "Allow" to proceed

### Error: Token not stored in localStorage

**Symptom**: After OAuth redirect, localStorage.getItem('authToken') returns null

**Cause**: Frontend callback handler not executing

**Solution**:
1. Check browser console for JavaScript errors
2. Verify auth.js is loaded: `document.querySelector('script[src*="auth.js"]')`
3. Check callback URL includes `?token=` parameter
4. Verify `handleOAuthCallback()` is called on page load

### Error: CORS issues

**Symptom**: Browser console shows CORS error

**Cause**: Backend not allowing frontend origin

**Solution**:
```python
# backend-v2/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://cp.demo.waooaw.com",
        "https://pp.demo.waooaw.com",
        "https://waooaw-portal-demo-ryvhxvrdna-el.a.run.app",
        "https://waooaw-platform-portal-demo-ryvhxvrdna-el.a.run.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Manual Testing Checklist

### Pre-Flight Checks

- [ ] OAuth credentials verified in Secret Manager
- [ ] Redirect URIs added to Google Cloud Console
- [ ] Authorized domains added to OAuth consent screen
- [ ] Test user email added (if app in "Testing" mode)
- [ ] Backend health endpoint returns 200 OK
- [ ] Frontend Sign In button is visible

### Customer Portal Testing

- [ ] Navigate to https://cp.demo.waooaw.com
- [ ] Click "Sign In" button
- [ ] Redirected to Google OAuth consent screen
- [ ] Select Google account
- [ ] Click "Allow"
- [ ] Redirected back to cp.demo.waooaw.com/auth/callback
- [ ] Redirected to marketplace.html
- [ ] localStorage contains authToken
- [ ] localStorage contains userEmail
- [ ] Navbar shows user email
- [ ] Click "Sign Out" clears localStorage
- [ ] Navbar shows "Sign In" after sign out

### Platform Portal Testing

- [ ] Navigate to https://pp.demo.waooaw.com
- [ ] Click "Sign In" button
- [ ] Redirected to Google OAuth consent screen
- [ ] Select Google account
- [ ] Click "Allow"
- [ ] Redirected back to pp.demo.waooaw.com/auth/callback
- [ ] Redirected to dashboard
- [ ] Reflex session contains user info
- [ ] Dashboard shows authenticated state
- [ ] Sign out clears session

### Backend Testing

- [ ] `/health` returns 200 OK
- [ ] `/auth/google/login` returns 307 redirect to Google
- [ ] `/auth/google/callback` exchanges code for token
- [ ] Logs show successful OAuth flow
- [ ] JWT token generated and returned to frontend

---

## Security Verification

### Check Token Expiry

```javascript
// Browser console after sign in:
const token = localStorage.getItem('authToken');
const payload = JSON.parse(atob(token.split('.')[1]));
console.log('Token expires:', new Date(payload.exp * 1000));
console.log('Issued at:', new Date(payload.iat * 1000));
console.log('User email:', payload.email);
```

### Verify HTTPS Only

- [ ] All requests use HTTPS (no HTTP)
- [ ] SSL certificates are valid (green lock icon)
- [ ] No mixed content warnings

### Check CORS Configuration

```javascript
// Browser console:
fetch('https://waooaw-api-demo-ryvhxvrdna-el.a.run.app/health')
  .then(r => r.json())
  .then(data => console.log('CORS OK:', data))
  .catch(err => console.error('CORS Error:', err));
```

---

## Next Steps After Successful Testing

### 1. Deploy to UAT Environment

Once demo testing is complete:
```bash
cd cloud/terraform
terraform plan -var-file=environments/uat.tfvars
terraform apply -var-file=environments/uat.tfvars
```

Add UAT redirect URIs to Google Cloud Console:
- https://cp.uat.waooaw.com/auth/callback
- https://pp.uat.waooaw.com/auth/callback

### 2. Implement Refresh Token Mechanism

Update backend to support refresh tokens:
- Store refresh tokens securely (encrypted database or Secret Manager)
- Add `/auth/refresh` endpoint
- Frontend calls refresh before token expiry

### 3. Replace localStorage with httpOnly Cookies

For production security:
- Backend sets httpOnly cookie instead of returning JWT in URL
- Frontend reads cookie automatically (no localStorage)
- CSRF token in localStorage for double-submit cookie pattern

### 4. Add Multi-Factor Authentication (Optional)

If required for production:
- Enable 2FA for sensitive operations
- Integrate Google Authenticator or SMS OTP
- Add backup codes for account recovery

### 5. Implement Role-Based Access Control

Enhance backend to assign roles:
```python
# backend-v2/app/auth/oauth_v2.py
def assign_role(email: str) -> str:
    # Admin users
    if email in ["admin@waooaw.com"]:
        return "admin"
    
    # Platform portal users (agents)
    if email.endswith("@agent.waooaw.com"):
        return "agent"
    
    # Default: customer
    return "customer"
```

---

## Reference Documents

- [OAUTH_IMPLEMENTATION.md](OAUTH_IMPLEMENTATION.md) - Code implementation details
- [INFRASTRUCTURE_DEPLOYMENT.md](INFRASTRUCTURE_DEPLOYMENT.md) - Deployed infrastructure
- [backend-v2/app/auth/oauth_v2.py](backend-v2/app/auth/oauth_v2.py) - Backend OAuth logic
- [frontend/js/auth.js](frontend/js/auth.js) - Customer portal OAuth handler
- [PlatformPortal-v2/PlatformPortal_v2/PlatformPortal_v2.py](PlatformPortal-v2/PlatformPortal_v2/PlatformPortal_v2.py) - Platform portal OAuth logic

---

## Contact

For issues or questions during testing:
1. Check backend logs: `gcloud run services logs read waooaw-api-demo --region=asia-south1`
2. Check browser console for JavaScript errors
3. Verify OAuth configuration in Google Cloud Console
4. Review this guide's troubleshooting section

---

**Ready to test!** 🎯  
Follow the manual testing checklist and report any issues found.
