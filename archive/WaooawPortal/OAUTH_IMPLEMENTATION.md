# OAuth Sign In Implementation - Deployment #34

**Date**: 2026-01-03  
**Commit**: caf60b2  
**Status**: ✅ Deployed to GitHub - Awaiting Cloud Run deployment

---

## Changes Implemented

### 1. Platform Portal (Reflex) - Fixed Backend URL ✅

**File**: `/PlatformPortal-v2/PlatformPortal_v2/PlatformPortal_v2.py`

**Problem**: `get_backend_url()` returned old custom domain for demo environment
```python
# OLD (WRONG)
if self.environment == 'demo':
    return 'https://demo-api.waooaw.com'
```

**Solution**: Updated to use Cloud Run URL
```python
# NEW (CORRECT)
if self.environment == 'demo':
    return 'https://waooaw-api-demo-ryvhxvrdna-el.a.run.app'
```

**Status**: Sign In button already wired to `on_click=PlatformState.login_redirect` - now points to correct backend!

---

### 2. Customer Portal (React) - OAuth Integration ✅

#### Created `/WaooawPortal-v2/src/config.js` (OAuth config)

**Key Functions**:
- `getBackendUrl()` - Environment detection (demo/uat/production)
- `handleSignIn()` - Redirects to backend OAuth endpoint
- `handleOAuthCallback()` - Stores token, redirects to marketplace
- `isAuthenticated()` - Checks localStorage for token
- `getCurrentUser()` - Returns user info from localStorage
- `handleSignOut()` - Clears localStorage, redirects to home
- `updateAuthUI()` - Shows user email or "Sign In" based on auth state

**Environment Detection**:
```javascript
if (hostname.includes('waooaw-portal-demo')) {
    return 'https://waooaw-api-demo-ryvhxvrdna-el.a.run.app';
}
else if (hostname.includes('uat-www')) {
    return 'https://uat-api.waooaw.com';
}
else if (hostname === 'www.waooaw.com') {
    return 'https://api.waooaw.com';
}
```

#### Updated `/frontend/marketplace.html`

**Added Script Tag**:
```html
<script src="js/auth.js"></script>
```

**Updated Sign In Button**:
```html
<!-- OLD -->
<button class="btn-ghost">Sign In</button>

<!-- NEW -->
<button class="btn-ghost" onclick="handleSignIn()">Sign In</button>
```

#### Created `/frontend/auth/callback.html`

OAuth callback page with:
- WAOOAW branding
- Loading spinner
- Error handling (5-second timeout)
- Auto-redirect after token storage

---

## OAuth Flow (End-to-End)

### For Platform Portal (Reflex)
1. User clicks "Sign In" button
2. `PlatformState.login_redirect` executes
3. Redirects to: `https://waooaw-api-demo-ryvhxvrdna-el.a.run.app/auth/login?frontend=pp`
4. Backend redirects to Google OAuth
5. User authorizes
6. Google redirects back to backend `/auth/callback`
7. Backend creates JWT, redirects to Platform Portal with token in URL
8. Reflex State stores token
9. User logged in ✅

### For Customer Portal (React)
1. User clicks "Sign In" button
2. `handleSignIn()` executes
3. Redirects to: `https://waooaw-api-demo-ryvhxvrdna-el.a.run.app/auth/login`
4. Backend redirects to Google OAuth
5. User authorizes
6. Google redirects back to backend `/auth/callback`
7. Backend creates JWT, redirects to `/marketplace.html?token=xxx&email=xxx`
8. `auth.js` detects token in URL, stores in localStorage
9. Redirects to clean `/marketplace.html` URL
10. User logged in ✅

---

## Testing Checklist (After Deployment)

### Platform Portal
- [ ] Open https://waooaw-platform-portal-demo-ryvhxvrdna-el.a.run.app
- [ ] Click "Sign In" button
- [ ] Should redirect to accounts.google.com
- [ ] Login with Google account
- [ ] Should redirect back to Platform Portal
- [ ] Dashboard should show logged-in state

### Customer Portal
- [ ] Open https://waooaw-portal-demo-ryvhxvrdna-el.a.run.app/marketplace.html
- [ ] Click "Sign In" button
- [ ] Should redirect to accounts.google.com
- [ ] Login with Google account
- [ ] Should redirect to callback page (loading spinner)
- [ ] Should auto-redirect to marketplace
- [ ] Button should now show user email

### Backend Verification
- [x] OAuth login endpoint works: `curl -L https://waooaw-api-demo-ryvhxvrdna-el.a.run.app/auth/login` ✅
- [ ] OAuth callback returns JWT token
- [ ] CORS allows Cloud Run frontend URLs
- [ ] Token verification works on protected endpoints

---

## URLs Reference

### Demo Environment (Current)
- **Backend API**: https://waooaw-api-demo-ryvhxvrdna-el.a.run.app
- **Customer Portal**: https://waooaw-portal-demo-ryvhxvrdna-el.a.run.app
- **Platform Portal**: https://waooaw-platform-portal-demo-ryvhxvrdna-el.a.run.app

### OAuth Endpoints
- **Login**: `/auth/login` (redirects to Google)
- **Callback**: `/auth/callback` (exchanges code for token)
- **Redirect URI** (configured in OAuth Console):
  - https://waooaw-api-demo-ryvhxvrdna-el.a.run.app/auth/callback

---

## Files Modified/Created

```
PlatformPortal/PlatformPortal_v2/PlatformPortal_v2.py  (UPDATED)
frontend/js/auth.js                                       (NEW)
frontend/marketplace.html                                 (UPDATED)
frontend/auth/callback.html                               (NEW)
```

---

## Next Steps

1. **Wait for GitHub Actions deployment** (#34)
2. **Test Platform Portal OAuth flow**
3. **Test Customer Portal OAuth flow**
4. **Verify token storage and persistence**
5. **Check CORS for any issues**
6. **Document any issues found**

---

## Known Considerations

- **Environment Detection**: Based on hostname matching
- **Token Storage**: localStorage (client-side, not secure for production - should be httpOnly cookies)
- **CSRF Protection**: State parameter used in OAuth flow
- **Role Assignment**: Backend assigns role based on email (configurable)
- **Session Expiry**: JWT tokens expire after X hours (configured in backend)

---

## Security Notes

⚠️ **For Production**:
- Replace localStorage with httpOnly cookies
- Add refresh token mechanism
- Implement proper session management
- Add rate limiting to auth endpoints
- Enable additional OAuth scopes as needed
- Implement proper logout on backend

Currently implemented for **demo purposes** with reasonable security for UAT environment.

---

**Status**: Code deployed to GitHub. Waiting for Cloud Run deployment. Will test OAuth flow once services are updated.
