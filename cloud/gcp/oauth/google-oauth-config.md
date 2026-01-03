# Google OAuth 2.0 Configuration for WAOOAW Platform - v2 Architecture

**Document ID:** OAUTH-CONFIG-v2  
**Last Updated:** January 3, 2026  
**Region:** asia-south1 (Mumbai)  
**Auth Flow:** Authorization Code (centralized backend)

---

## Overview

WAOOAW v2 platform uses Google OAuth 2.0 with **centralized backend authentication**. All OAuth flows are handled by the Backend API, which then redirects users back to the appropriate frontend.

**OAuth Provider:** Google Cloud Platform  
**Authentication Method:** OAuth 2.0 → JWT tokens  
**Backend Implementation:** `/backend-v2/app/auth/oauth_v2.py`  
**Current Status:** ✅ Code ready, ⚠️ Domains not mapped yet

---

## Current State (January 3, 2026)

### ✅ What's Working
- Backend API deployed with OAuth endpoints (`/auth/login`, `/auth/callback`)
- OAuth secrets in Secret Manager (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)
- Multi-environment support (demo/uat/production)
- Auto-detection of environment from hostname
- State parameter encoding with frontend URL tracking

### ⚠️ What's Pending
- Custom domain mapping (using *.run.app URLs currently)
- DNS CNAME records for custom domains
- Google OAuth Console configuration with custom domains
- Frontend OAuth integration (Sign In buttons not connected yet)

---

## 1. Google Cloud Console Configuration

### 1.1 OAuth Consent Screen Setup

**Location:** [Google Cloud Console](https://console.cloud.google.com) → APIs & Services → OAuth consent screen

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

### 1.2 OAuth Client ID Configuration (AFTER Domain Mapping)

**Location:** Google Cloud Console → APIs & Services → Credentials → Create OAuth Client ID

**Client Type:** Web application  
**Name:** WAOOAW v2

**⚠️ IMPORTANT:** Only configure this AFTER custom domains are mapped and SSL certificates are active!

**Authorized JavaScript Origins:**
```
# Demo Environment
https://demo-www.waooaw.com
https://demo-pp.waooaw.com

# UAT Environment
https://uat-www.waooaw.com
https://uat-pp.waooaw.com

# Production Environment
https://www.waooaw.com
https://pp.waooaw.com
```

**Authorized Redirect URIs:** (CRITICAL - Must be exact)
```
# Demo Environment
https://demo-api.waooaw.com/auth/callback

# UAT Environment
https://uat-api.waooaw.com/auth/callback

# Production Environment
https://api.waooaw.com/auth/callback
```

**Why these specific URIs?**
- Frontend initiates login by redirecting to: `{api-domain}/auth/login`
- Google redirects back to: `{api-domain}/auth/callback`
- Backend parses state, creates JWT, redirects to: `{frontend-domain}/auth/callback?token=...`

---

## 2. Backend OAuth Implementation (v2)

### 2.1 Architecture Overview

```
User Flow:
1. User clicks "Sign In" button on frontend (demo-www.waooaw.com or demo-pp.waooaw.com)
2. Frontend redirects to: https://demo-api.waooaw.com/auth/login
3. Backend detects environment (demo) from hostname
4. Backend detects which frontend initiated login from Referer header
5. Backend encodes state with: {frontend URL, CSRF token, environment}
6. Backend redirects to Google OAuth consent screen
7. User approves on Google
8. Google redirects to: https://demo-api.waooaw.com/auth/callback?code=...&state=...
9. Backend exchanges code for access token
10. Backend fetches user info from Google
11. Backend determines user role (admin/operator/viewer)
12. Backend creates JWT token
13. Backend redirects to: https://demo-www.waooaw.com/auth/callback?token=...&email=...&name=...&role=...
14. Frontend stores token in localStorage and redirects to dashboard
```

### 2.2 Environment Detection

**File:** `/backend-v2/app/auth/oauth_v2.py`

```python
def detect_environment(request: Request) -> str:
    """Auto-detect environment from hostname"""
    host = request.headers.get("host", "")
    
    if "demo-" in host or "demo." in host:
        return "demo"
    elif "uat-" in host or "uat." in host:
        return "uat"
    elif "localhost" in host:
        return "development"
    else:
        return "production"
```

**Domain Configuration** (`/backend-v2/app/config.py`):
```python
DOMAIN_CONFIG = {
    "demo": {
        "api": "https://demo-api.waooaw.com",
        "www": "https://demo-www.waooaw.com",
        "pp": "https://demo-pp.waooaw.com",
    },
    "uat": {
        "api": "https://uat-api.waooaw.com",
        "www": "https://uat-www.waooaw.com",
        "pp": "https://uat-pp.waooaw.com",
    },
    "production": {
        "api": "https://api.waooaw.com",
        "www": "https://www.waooaw.com",
        "pp": "https://pp.waooaw.com",
    },
}
```

### 2.3 Frontend Detection

```python
def get_frontend_from_referer(request: Request, env: str) -> str:
    """Detect which frontend initiated OAuth from Referer header"""
    referer = request.headers.get("referer", "")
    config = settings.DOMAIN_CONFIG[env]
    
    if not referer:
        return config.get("www", "")  # Default to customer portal
    
    parsed = urlparse(referer)
    referer_host = f"{parsed.scheme}://{parsed.netloc}"
    
    # Check which domain the user came from
    for key, url in config.items():
        if url == referer_host:
            return url
    
    return config.get("www", "")
```

### 2.4 User Role Assignment

```python
def get_user_role(email: str) -> str:
    """Determine user role based on email"""
    if email in ["admin@waooaw.ai", "yogeshkhandge@gmail.com"]:
        return "admin"
    elif email.endswith("@waooaw.ai"):
        return "operator"
    else:
        return "viewer"  # Customers
```

### 2.5 Current Deployment Status

**Service:** waooaw-api-demo  
**Region:** asia-south1  
**URL:** https://waooaw-api-demo-270293855600.asia-south1.run.app

**Endpoints:**
- `GET /auth/login` - Initiate OAuth flow
- `GET /auth/callback` - Handle Google callback
- `GET /auth/logout` - Logout (not implemented yet)
- `GET /auth/me` - Get current user (not implemented yet)

**Secrets (from Secret Manager):**
```yaml
GOOGLE_CLIENT_ID: <secret>
GOOGLE_CLIENT_SECRET: <secret>
JWT_SECRET: <secret>
```

---

## 3. Frontend OAuth Integration

### 3.1 WaooawPortal (Customer Marketplace) - React

**Status:** ⚠️ Sign In button not connected yet

**File:** `/frontend/index.html`

**Required Implementation:**
```javascript
// Add to /frontend/js/auth.js
function handleSignIn() {
    // Get backend API URL based on current hostname
    const hostname = window.location.hostname;
    let apiUrl;
    
    if (hostname.includes('demo-www')) {
        apiUrl = 'https://demo-api.waooaw.com';
    } else if (hostname.includes('uat-www')) {
        apiUrl = 'https://uat-api.waooaw.com';
    } else if (hostname === 'www.waooaw.com') {
        apiUrl = 'https://api.waooaw.com';
    } else {
        apiUrl = 'http://localhost:8000';  // Development
    }
    
    // Redirect to backend OAuth endpoint
    window.location.href = `${apiUrl}/auth/login`;
}

// OAuth callback handler
async function handleOAuthCallback() {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    const email = params.get('email');
    const name = params.get('name');
    const picture = params.get('picture');
    const role = params.get('role');
    
    if (token && email) {
        // Store auth data
        localStorage.setItem('auth_token', token);
        localStorage.setItem('user_email', email);
        localStorage.setItem('user_name', name);
        localStorage.setItem('user_picture', picture);
        localStorage.setItem('user_role', role);
        
        // Redirect to dashboard/home
        window.location.href = '/dashboard.html';
    } else {
        // Handle error
        const error = params.get('error');
        alert(`Login failed: ${error}`);
        window.location.href = '/';
    }
}

// Check if on callback page
if (window.location.pathname === '/auth/callback') {
    handleOAuthCallback();
}
```

**HTML Update Required:**
```html
<!-- In navigation bar -->
<button onclick="handleSignIn()" class="btn-primary">Sign In</button>

<!-- Create callback page: /auth/callback.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Signing In...</title>
    <script src="/js/auth.js"></script>
</head>
<body>
    <div>Processing sign in...</div>
</body>
</html>
```

### 3.2 Platform Portal - Reflex

**Status:** ⚠️ Sign In button exists but has no handler

**File:** `/PlatformPortal-v2/PlatformPortal_v2/PlatformPortal_v2.py`

**Current Issue:** Button renders but doesn't have `on_click` event:
```python
# Current (line ~30):
rx.button("Sign In", color_scheme="cyan", size="2")

# Required Fix:
rx.button(
    "Sign In",
    on_click=lambda: rx.redirect(PlatformState.get_oauth_login_url()),
    color_scheme="cyan",
    size="2"
)
```

**Required State Method:**
```python
class PlatformState(rx.State):
    # ... existing state variables ...
    
    def get_oauth_login_url(self) -> str:
        """Get OAuth login URL based on current environment"""
        import os
        env = os.getenv("ENV", "development")
        
        if env == "demo":
            return "https://demo-api.waooaw.com/auth/login"
        elif env == "uat":
            return "https://uat-api.waooaw.com/auth/login"
        elif env == "production":
            return "https://api.waooaw.com/auth/login"
        else:
            return "http://localhost:8000/auth/login"
```

**OAuth Callback Page** (create `/PlatformPortal-v2/PlatformPortal_v2/pages/auth_callback.py`):
```python
import reflex as rx

def auth_callback() -> rx.Component:
    """Handle OAuth callback from backend"""
    return rx.fragment(
        rx.script("""
            // Get params from URL
            const params = new URLSearchParams(window.location.search);
            const token = params.get('token');
            const email = params.get('email');
            
            if (token && email) {
                // Store in localStorage
                localStorage.setItem('auth_token', token);
                localStorage.setItem('user_email', email);
                
                // Redirect to dashboard
                window.location.href = '/';
            } else {
                // Handle error
                alert('Login failed');
                window.location.href = '/';
            }
        """)
    )
```

**Register Route:**
```python
# In PlatformPortal_v2.py or pages/__init__.py
app.add_page(auth_callback, route="/auth/callback")
```

---

## 4. Complete Setup Checklist

### Phase 1: Infrastructure (Current - ✅ Completed)
- [x] Deploy Backend API with OAuth endpoints
- [x] Deploy WaooawPortal (React customer marketplace)
- [x] Deploy Platform Portal (Reflex admin portal)
- [x] Store OAuth secrets in Secret Manager
- [x] Configure Cloud Run services with secrets

### Phase 2: Custom Domain Setup (⏳ In Progress)
- [ ] Run domain mapping script: `cd /workspaces/WAOOAW/infrastructure/gcp && ./deploy.sh demo`
- [ ] Add DNS CNAME records in domain registrar (pointing to ghs.googlehosted.com)
- [ ] Wait for SSL certificate provisioning (15 min - 24 hours)
- [ ] Verify domains are accessible

### Phase 3: OAuth Console Configuration (⏳ Pending)
- [ ] Add Authorized JavaScript Origins in Google OAuth Console
- [ ] Add Authorized Redirect URIs in Google OAuth Console
- [ ] Test OAuth flow manually from demo domains

### Phase 4: Frontend Integration (⏳ Pending)
- [ ] Update WaooawPortal Sign In button to call `/auth/login`
- [ ] Create WaooawPortal `/auth/callback.html` page
- [ ] Add auth.js script to handle token storage
- [ ] Update Platform Portal Sign In button with `on_click` event
- [ ] Create Platform Portal `/auth/callback` page
- [ ] Add ENV variable to Platform Portal deployment
- [ ] Test OAuth flow end-to-end

---

## 5. Testing OAuth Flow

### 5.1 Manual Test (After Domain Setup)

**Test Demo Environment:**

1. **Navigate to Customer Portal:**
   ```
   https://demo-www.waooaw.com
   ```

2. **Click "Sign In" button**
   - Should redirect to: `https://demo-api.waooaw.com/auth/login`

3. **Backend redirects to Google:**
   - URL should contain: `accounts.google.com/o/oauth2/v2/auth`
   - Check state parameter is present

4. **Login with Google account**
   - Use test account or real account

5. **Google redirects to backend callback:**
   - URL: `https://demo-api.waooaw.com/auth/callback?code=...&state=...`

6. **Backend processes and redirects to frontend:**
   - URL: `https://demo-www.waooaw.com/auth/callback?token=...&email=...&name=...`

7. **Frontend stores token and redirects:**
   - Check localStorage has `auth_token`, `user_email`, etc.
   - Should redirect to dashboard

### 5.2 Troubleshooting

**Error: "redirect_uri_mismatch"**
- Check Google OAuth Console Authorized Redirect URIs
- Must exactly match: `https://demo-api.waooaw.com/auth/callback`

**Error: "origin_mismatch"**
- Check Google OAuth Console Authorized JavaScript Origins
- Must include: `https://demo-www.waooaw.com` and `https://demo-pp.waooaw.com`

**Error: "Google OAuth not configured"**
- Check Secret Manager has GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
- Check Cloud Run service has secret bindings

**Token not stored in frontend:**
- Check browser console for JavaScript errors
- Verify `/auth/callback` page exists and loads auth.js
- Check URL parameters contain token

---

## 6. Next Steps

### Immediate (Today):
1. ✅ Review OAuth documentation (this file)
2. ⏳ Run domain mapping script for demo environment
3. ⏳ Configure DNS CNAME records

### Short-term (This Week):
1. ⏳ Update Google OAuth Console with custom domains
2. ⏳ Implement frontend Sign In button handlers
3. ⏳ Test OAuth flow end-to-end
4. ⏳ Deploy UAT environment
5. ⏳ Deploy Production environment

### Future Enhancements:
1. Implement proper JWT token generation (currently using `demo_token_`)
2. Add token refresh mechanism
3. Implement `/auth/logout` endpoint
4. Implement `/auth/me` endpoint for token validation
5. Add session management and expiration
6. Add rate limiting on OAuth endpoints
7. Add audit logging for auth events

---

## 7. Security Considerations

### Current State:
- ✅ OAuth secrets stored in Secret Manager (not in code)
- ✅ HTTPS enforced on all services
- ✅ CORS configured for specific domains
- ✅ State parameter used to prevent CSRF
- ⚠️ JWT implementation pending (using demo tokens currently)
- ⚠️ No token expiration or refresh mechanism yet
- ⚠️ No rate limiting on auth endpoints

### Production Requirements (Before Launch):
1. Implement proper JWT with expiration (use PyJWT library)
2. Add refresh token mechanism
3. Implement rate limiting (e.g., 10 login attempts per IP per hour)
4. Add audit logging to track all auth events
5. Submit OAuth consent screen for Google verification
6. Add session management with Redis
7. Implement PKCE (Proof Key for Code Exchange) for extra security
8. Add IP whitelisting for admin accounts

---

## Appendix: File Locations

### Backend (v2 Architecture):
- OAuth Implementation: `/backend-v2/app/auth/oauth_v2.py`
- Configuration: `/backend-v2/app/config.py`
- Main App: `/backend-v2/app/main.py`

### Frontend - WaooawPortal (React):
- Main HTML: `/frontend/index.html`
- Auth Script: `/frontend/js/auth.js` (to be created)
- Callback Page: `/frontend/auth/callback.html` (to be created)

### Frontend - Platform Portal (Reflex):
- Main App: `/PlatformPortal-v2/PlatformPortal_v2/PlatformPortal_v2.py`
- Callback Page: `/PlatformPortal-v2/PlatformPortal_v2/pages/auth_callback.py` (to be created)

### Infrastructure:
- Domain Mapping Script: `/infrastructure/gcp/deploy.sh`
- OAuth Config Doc: `/cloud/gcp/oauth/google-oauth-config.md` (this file)
- Domain Setup Doc: `/docs/infrastructure/custom-domains.md`

---

**Last Updated:** January 3, 2026  
**Next Review:** After Phase 2 completion (custom domains active)
    
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
