# Google OAuth 2.0 Configuration for WAOOAW Platform

**Document ID:** OAUTH-CONFIG-001  
**Last Updated:** January 3, 2026  
**Region:** asia-south1 (Mumbai)  
**Auth Flow:** Authorization Code with PKCE

---

## Overview

WAOOAW platform uses Google OAuth 2.0 for user authentication across all 5 domains. This document provides complete configuration steps and management procedures.

**OAuth Provider:** Google Cloud Platform  
**Authentication Method:** OAuth 2.0 + JWT tokens  
**Session Storage:** Server-side (Redis) for Reflex apps, localStorage for React apps

---

## 1. Google Cloud Console Configuration

### 1.1 OAuth Consent Screen Setup

**Location:** Google Cloud Console → APIs & Services → OAuth consent screen

**Configuration:**

| Field | Value |
|-------|-------|
| **User Type** | External |
| **App Name** | WAOOAW Platform |
| **User Support Email** | yogeshkhandge@gmail.com |
| **App Logo** | (Upload WAOOAW logo 120x120px) |
| **Application Home Page** | https://www.waooaw.com |
| **Application Privacy Policy** | https://www.waooaw.com/privacy |
| **Application Terms of Service** | https://www.waooaw.com/terms |
| **Authorized Domains** | waooaw.com |
| **Developer Contact Email** | yogeshkhandge@gmail.com |

**Scopes Required:**
```
openid                          (Know user identity)
email                           (View user email address)
profile                         (View user basic profile)
```

**Publishing Status:**
- Development: Test with up to 100 users
- Production: Submit for verification (3-5 business days)

---

### 1.2 OAuth Client ID Configuration

**Location:** Google Cloud Console → APIs & Services → Credentials → Create OAuth Client ID

**Client Type:** Web application  
**Name:** WAOOAW Production

**Authorized JavaScript Origins:**
```
https://www.waooaw.com
https://pp.waooaw.com
https://dp.waooaw.com
https://yk.waooaw.com
https://api.waooaw.com
```

**Authorized Redirect URIs:** (CRITICAL - Must be exact)
```
https://api.waooaw.com/auth/callback         # Backend OAuth handler
https://www.waooaw.com/auth/callback         # Customer marketplace
https://pp.waooaw.com/auth/callback          # Platform portal
https://dp.waooaw.com/auth/callback          # Development portal
https://yk.waooaw.com/auth/callback          # Customer portal
```

**After Creation:**
- Download JSON credentials
- Store Client ID and Client Secret securely
- Never commit credentials to git

---

## 2. GCP Secret Manager Setup

### 2.1 Store OAuth Credentials

**Current Status:** ✅ Already configured
- `google-client-id` (created 2026-01-02)
- `google-client-secret` (created 2026-01-02)

**To update credentials:**

```bash
# Update client ID
echo -n "YOUR_NEW_CLIENT_ID" | gcloud secrets versions add google-client-id --data-file=-

# Update client secret
echo -n "YOUR_NEW_CLIENT_SECRET" | gcloud secrets versions add google-client-secret --data-file=-

# Verify
gcloud secrets versions list google-client-id
gcloud secrets versions list google-client-secret
```

### 2.2 Grant Access to Cloud Run Services

```bash
PROJECT_ID="waooaw-oauth"
PROJECT_NUMBER="270293855600"
SERVICE_ACCOUNT="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

# Grant secret access
gcloud secrets add-iam-policy-binding google-client-id \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding google-client-secret \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

# Verify
gcloud secrets get-iam-policy google-client-id
```

---

## 3. Backend OAuth Implementation

### 3.1 Current Implementation

**File:** `/workspaces/WAOOAW/backend/app/auth/oauth.py`

**Flow:**
1. User clicks "Login" on any frontend
2. Frontend redirects to: `https://api.waooaw.com/auth/login`
3. Backend redirects to Google OAuth consent screen
4. User approves
5. Google redirects to: `https://api.waooaw.com/auth/callback?code=...`
6. Backend exchanges code for access token
7. Backend fetches user info from Google
8. Backend creates JWT token
9. Backend redirects to: `<origin-frontend>/auth/callback?token=...&email=...&name=...`
10. Frontend stores token and redirects to dashboard

### 3.2 Environment Variables (Backend API)

**Service:** waooaw-api  
**Region:** asia-south1

```yaml
ENV: production
FRONTEND_URL: https://www.waooaw.com                     # Primary frontend
GOOGLE_REDIRECT_URI: https://api.waooaw.com/auth/callback  # OAuth callback
CORS_ORIGINS: "https://www.waooaw.com,https://pp.waooaw.com,https://dp.waooaw.com,https://yk.waooaw.com"  # Comma-separated

# From Secret Manager
GOOGLE_CLIENT_ID: <from secret>
GOOGLE_CLIENT_SECRET: <from secret>
```

**Update Command:**
```bash
gcloud run services update waooaw-api \
    --region=asia-south1 \
    --set-env-vars=FRONTEND_URL=https://www.waooaw.com,GOOGLE_REDIRECT_URI=https://api.waooaw.com/auth/callback,CORS_ORIGINS="https://www.waooaw.com,https://pp.waooaw.com,https://dp.waooaw.com,https://yk.waooaw.com"
```

### 3.3 Backend Code Review

**File:** `/workspaces/WAOOAW/backend/app/auth/oauth.py`

**Critical Functions:**

```python
# Lines 62-65: Determine user role
def get_user_role(email: str) -> UserRole:
    if email in ["admin@waooaw.ai", "yogeshkhandge@gmail.com"]:
        return UserRole.ADMIN
    elif email.endswith("@waooaw.ai"):
        return UserRole.OPERATOR
    else:
        return UserRole.VIEWER

# Lines 127-142: Initiate OAuth login
@router.get("/auth/login")
async def oauth_login(request: Request):
    redirect_uri = _get_redirect_uri(request)
    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)

# Lines 151-257: Handle OAuth callback
@router.get("/auth/callback")
async def oauth_callback(code: str, request: Request):
    # Exchange code for token
    # Fetch user info
    # Create JWT
    # Redirect to frontend with token
    frontend_target = _get_frontend_url(request)
    redirect_url = f"{frontend_target}/auth/callback?{params}"
    return RedirectResponse(url=redirect_url)
```

**Current Behavior:**
- `_get_frontend_url()` checks FRONTEND_URL env var first (set to www.waooaw.com)
- Falls back to Origin header, then Referer header
- Logic attempts to detect frontend but **prioritizes FRONTEND_URL**

**Issue for Multi-Domain:**
- FRONTEND_URL is hardcoded to www.waooaw.com in deployment
- Users logging in from pp/dp/yk get redirected to www after login
- Origin/Referer detection is bypassed by explicit FRONTEND_URL

**Fix Required:** Backend should detect which frontend initiated login and redirect accordingly

**Recommended Approach:**
```python
def _get_frontend_url(request: Request) -> str:
    """Detect which frontend initiated the OAuth flow"""
    # First check Referer - most reliable for OAuth flows
    referer = request.headers.get("referer")
    if referer:
        from urllib.parse import urlparse
        parsed = urlparse(referer)
        if parsed.netloc in ["www.waooaw.com", "pp.waooaw.com", "dp.waooaw.com", "yk.waooaw.com"]:
            return f"{parsed.scheme}://{parsed.netloc}"
    
    # Fall back to explicit FRONTEND_URL
    return FRONTEND_URL
```

---

## 4. Frontend OAuth Implementation

### 4.1 React Apps (www, yk)

**Callback Handler:** `/auth/callback`

**Implementation:**
```javascript
// File: frontend/js/auth.js
async function handleOAuthCallback() {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    const email = params.get('email');
    const name = params.get('name');
    const picture = params.get('picture');
    const role = params.get('role');
    
    if (token && email && name) {
        // Store in localStorage
        localStorage.setItem('waooaw_token', token);
        localStorage.setItem('waooaw_user', JSON.stringify({
            email, name, picture, role
        }));
        
        // Redirect to dashboard
        window.location.href = '/dashboard';
    } else {
        window.location.href = '/login?error=auth_failed';
    }
}
```

**Login Button:**
```html
<a href="https://api.waooaw.com/auth/login" class="btn-login">
    Login with Google
</a>
```

### 4.2 Reflex Apps (pp, dp)

**Callback Handler:** `@rx.page(route="/auth/callback")`

**Implementation:**
```python
# File: PlatformPortal/pages/callback.py
@rx.page(route="/auth/callback", title="Logging in...")
def callback_page() -> rx.Component:
    return rx.fragment(
        rx.script("""
            async function handleCallback() {
                const params = new URLSearchParams(window.location.search);
                const token = params.get('token');
                // Store in Reflex state or cookie
                if (token) {
                    sessionStorage.setItem('waooaw_token', token);
                    window.location.href = '/dashboard';
                }
            }
            handleCallback();
        """)
    )
```

---

## 5. OAuth Flow Diagrams

### 5.1 Successful Login Flow

```
User (Browser)          Frontend              Backend API           Google OAuth
      |                    |                      |                      |
      |--Click Login------>|                      |                      |
      |                    |                      |                      |
      |--Redirect----------|---/auth/login------->|                      |
      |                                            |                      |
      |<--------Redirect to Google-----------------|                      |
      |                                                                   |
      |--Login & Approve---------------------------------------->|
      |                                                                   |
      |<--------Redirect with code---------------------------------|
      |                                            |                      |
      |--code----------------/auth/callback------->|                      |
      |                                            |--Exchange code------>|
      |                                            |<--Access token-------|
      |                                            |                      |
      |                                            |--Get user info------>|
      |                                            |<--User data----------|
      |                                            |                      |
      |                                            |--Create JWT          |
      |<--Redirect with token----------------------|                      |
      |                    |                      |                      |
      |--/auth/callback--->|                      |                      |
      |    ?token=xxx      |                      |                      |
      |                    |--Store token         |                      |
      |                    |--Redirect to /dashboard                     |
      |<---Dashboard-------|                      |                      |
```

### 5.2 Error Handling Flow

```
Scenario 1: User denies consent
Google OAuth --> Backend: error=access_denied
Backend --> Frontend: /login?error=access_denied

Scenario 2: Invalid client credentials
Backend --> Google: 401 Unauthorized
Backend --> Frontend: /login?error=invalid_credentials

Scenario 3: Missing redirect URI
Google OAuth: redirect_uri_mismatch error
Check: Authorized redirect URIs in Google Console

Scenario 4: Expired authorization code
Backend --> Google: 400 Bad Request (code expired)
Backend --> Frontend: /login?error=code_expired
```

---

## 6. Security Considerations

### 6.1 Token Storage

**React Apps:**
- Store JWT in localStorage (XSS risk - acceptable for now)
- Alternative: httpOnly cookie (more secure, needs backend change)

**Reflex Apps:**
- Store in server-side state (Redis)
- Session ID in cookie
- More secure, survives page refresh

### 6.2 Token Expiry

**JWT Configuration:**
```python
# backend/app/auth/jwt_handler.py
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
```

**Refresh Token:** Not implemented yet (Phase 2 enhancement)

### 6.3 CORS Configuration

**Backend API:**
```python
# backend/app/main.py
CORS_ORIGINS = [
    "https://www.waooaw.com",
    "https://pp.waooaw.com",
    "https://dp.waooaw.com",
    "https://yk.waooaw.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 6.4 Rate Limiting

**Current:** Not implemented  
**Recommended:** Limit OAuth callback attempts

```python
# Future enhancement
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@router.get("/auth/callback")
@limiter.limit("10/minute")
async def oauth_callback(...):
    ...
```

---

## 7. Testing OAuth Configuration

### 7.1 Manual Testing Checklist

**For each domain (www, pp, dp, yk):**

- [ ] Click "Login" button → Redirects to Google
- [ ] Google consent screen shows "WAOOAW Platform"
- [ ] Scopes shown: email, profile, openid
- [ ] After approval → Redirects to correct domain
- [ ] Token appears in URL parameters
- [ ] Token stored in localStorage/cookie
- [ ] Redirects to dashboard
- [ ] User info displayed (name, email, avatar)
- [ ] API calls include Authorization header
- [ ] Logout clears token

### 7.2 Test with Multiple Accounts

```bash
# Test with admin user
Email: yogeshkhandge@gmail.com
Expected Role: ADMIN

# Test with operator user
Email: operator@waooaw.ai
Expected Role: OPERATOR

# Test with customer user
Email: customer@gmail.com
Expected Role: VIEWER
```

### 7.3 Test Error Scenarios

- [ ] Deny consent → Redirects to /login?error=access_denied
- [ ] Close consent screen → User returns, can retry
- [ ] Use invalid token → API returns 401
- [ ] Token expired → Re-login required

---

## 8. Common Issues & Troubleshooting

### Issue 1: redirect_uri_mismatch

**Symptom:** Google error page: "redirect_uri_mismatch"

**Cause:** Redirect URI not in authorized list

**Fix:**
1. Go to Google Cloud Console → Credentials
2. Edit OAuth 2.0 Client ID
3. Add exact URI to "Authorized redirect URIs"
4. Wait 5 minutes for changes to propagate
5. Clear browser cache and retry

### Issue 2: CORS error in browser console

**Symptom:** `Access-Control-Allow-Origin` error

**Cause:** Frontend domain not in CORS_ORIGINS

**Fix:**
```bash
# Update backend CORS configuration
gcloud run services update waooaw-api \
    --region=asia-south1 \
    --update-env-vars="CORS_ORIGINS=https://www.waooaw.com,https://pp.waooaw.com,https://dp.waooaw.com,https://yk.waooaw.com"
```

### Issue 3: Token not being set

**Symptom:** User logs in, but remains on login page

**Cause:** JavaScript error in callback handler

**Debug:**
```javascript
// Add console logs
console.log('URL params:', window.location.search);
console.log('Token:', params.get('token'));
console.log('Stored token:', localStorage.getItem('waooaw_token'));
```

### Issue 4: Wrong redirect after login

**Symptom:** User on pp.waooaw.com redirected to www.waooaw.com

**Cause:** Backend `_get_frontend_url()` not detecting origin correctly

**Fix:** Update backend logic to read Origin/Referer header

---

## 9. Updating OAuth Configuration

### 9.1 Adding New Domain

**Steps:**
1. Add DNS A record pointing to 35.190.6.91
2. Update SSL certificate to include new domain
3. Update load balancer host rules
4. Add redirect URI in Google Console:
   ```
   https://newdomain.waooaw.com/auth/callback
   ```
5. Update backend CORS_ORIGINS
6. Test OAuth flow on new domain

### 9.2 Rotating Client Secret

**When to rotate:**
- Security breach
- Employee offboarding
- Every 90 days (recommended)

**Steps:**
```bash
# 1. Generate new credentials in Google Console
# 2. Update Secret Manager
echo -n "NEW_CLIENT_SECRET" | gcloud secrets versions add google-client-secret --data-file=-

# 3. Redeploy services (picks up latest secret version)
gcloud run services update waooaw-api --region=asia-south1

# 4. Test OAuth flow
# 5. Disable old secret version (after 24 hours)
gcloud secrets versions disable 1 --secret=google-client-secret
```

### 9.3 Adding New OAuth Scope

**Example:** Add Google Calendar scope

**Steps:**
1. Update OAuth consent screen in Google Console
2. Add scope: `https://www.googleapis.com/auth/calendar.readonly`
3. Update backend OAuth scope list:
   ```python
   "scope": "openid email profile https://www.googleapis.com/auth/calendar.readonly"
   ```
4. Users must re-consent (logout and login again)

---

## 10. Production Verification Checklist

Before going live:

### Google Cloud Console
- [ ] OAuth consent screen fully configured
- [ ] All 5 redirect URIs added and verified
- [ ] Client ID and Secret stored in Secret Manager
- [ ] Service account has secret accessor role
- [ ] Publishing status: Production (if >100 users)

### Backend API
- [ ] CORS_ORIGINS includes all 5 domains
- [ ] GOOGLE_REDIRECT_URI set to https://api.waooaw.com/auth/callback
- [ ] FRONTEND_URL points to correct domain
- [ ] Secrets mounted via environment variables
- [ ] JWT secret is strong (not default)

### Each Frontend
- [ ] Login button points to https://api.waooaw.com/auth/login
- [ ] Callback page handles token extraction
- [ ] Token stored (localStorage or server-side)
- [ ] API calls include Authorization header
- [ ] Logout clears all auth state

### Testing
- [ ] Test login flow on all 5 domains
- [ ] Test with admin, operator, and viewer roles
- [ ] Test error scenarios (deny, expired, invalid)
- [ ] Cross-browser testing (Chrome, Firefox, Safari)
- [ ] Mobile testing (responsive, OAuth popup)

---

## 11. Monitoring OAuth Health

### 11.1 Key Metrics

**Success Rate:**
```sql
-- Cloud Logging query
resource.type="cloud_run_revision"
resource.labels.service_name="waooaw-api"
jsonPayload.message="oauth_login_success"
```

**Error Rate:**
```sql
resource.type="cloud_run_revision"
resource.labels.service_name="waooaw-api"
jsonPayload.message=~"oauth_error|oauth_.*_failed"
```

**Average Login Time:**
- Measure: Time from /auth/login to successful callback
- Target: <5 seconds
- Alert: >10 seconds

### 11.2 Alert Configuration

**High Error Rate:**
```bash
# Create alert
gcloud alpha monitoring policies create \
    --display-name="OAuth Error Rate High" \
    --condition-threshold-value=10 \
    --condition-threshold-duration=300s \
    --notification-channels=<channel-id>
```

---

## 12. Future Enhancements

### Phase 2 (Month 4-6)
- [ ] Implement refresh tokens (extend session beyond 24h)
- [ ] Add rate limiting on OAuth endpoints
- [ ] Implement "Remember Me" functionality
- [ ] Add 2FA/MFA support

### Phase 3 (Month 7+)
- [ ] Support multiple OAuth providers (GitHub, Microsoft)
- [ ] SSO for enterprise customers
- [ ] OAuth audit trail (who logged in when)
- [ ] Anomaly detection (unusual login locations)

---

**Document Owner:** Platform Architecture Team  
**Review Schedule:** Monthly  
**Last Reviewed:** January 3, 2026  
**Next Review:** February 3, 2026  

**Contact:** yogeshkhandge@gmail.com  
**Support:** Create ticket in /cloud/gcp/runbooks/oauth-issues.md
