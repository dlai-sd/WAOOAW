# OAuth Testing Instructions

**Date:** January 2, 2026  
**Feature:** Google OAuth2 Authentication  
**Status:** Ready for Testing ✅

---

## 🔐 OAuth Configuration

### Backend (.env file)
```
GOOGLE_CLIENT_ID=***-***.apps.googleusercontent.com  # Ask admin for credentials
GOOGLE_CLIENT_SECRET=***  # Ask admin for credentials
GOOGLE_REDIRECT_URI=https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev/auth/callback
JWT_SECRET=***  # Configured securely
```

**Note:** OAuth credentials are stored securely in backend/.env (not committed to git)

### Authorized Users
- **Admin**: yogeshkhandge@gmail.com (full access)
- **Operators**: *@waooaw.ai (operator access)
- **Viewers**: All other Google accounts (read-only)

---

## 🚀 Testing Steps

### 1. Access Login Page
Open in browser:
```
https://shiny-space-guide-pj4gwgp94gw93557-3000.app.github.dev/login
```

**Expected:** 
- WAOOAW branding (cyan/purple theme)
- "Sign in with Google" button

### 2. Click "Sign in with Google"

**Flow:**
1. Redirects to `https://.../auth/login` (backend)
2. Backend redirects to Google OAuth consent screen
3. You see Google account selection
4. Click your account (yogeshkhandge@gmail.com)
5. Google asks for consent (first time only)
6. Click "Allow"
7. Google redirects to `https://.../auth/callback` (backend)
8. Backend exchanges code for token
9. Backend redirects to `https://.../auth/callback` (frontend)
10. Frontend stores JWT in localStorage
11. Frontend redirects to `/dashboard`

### 3. Verify Dashboard Access

**Expected:**
- Dashboard loads with metrics
- 4 metric cards visible
- Agent list displayed
- No errors in browser console

### 4. Check Session Persistence

**Test:**
1. Refresh the page
2. Open new tab to same URL

**Expected:**
- Still logged in (no redirect to login)
- Dashboard loads immediately

### 5. Test Logout (if implemented)

**Expected:**
- JWT removed from localStorage
- Redirected to `/login`

---

## 🔍 Debugging

### Check Backend Logs
```bash
tail -f /tmp/backend.log
```

**Look for:**
```
[info] oauth_login_initiated
[info] oauth_login_success email=yogeshkhandge@gmail.com role=admin
[info] oauth_redirect url=https://...
```

### Check Frontend Console (Browser DevTools)
Press `F12` and check:
1. **Console tab**: No errors
2. **Application tab > localStorage**:
   - `waooaw_token`: JWT string
   - `waooaw_user`: JSON with email, name, role
3. **Network tab**: All requests return 200

### Common Issues

#### Issue: "Google OAuth not configured"
**Solution:** Backend .env file not loaded. Restart:
```bash
cd /workspaces/WAOOAW/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --env-file .env
```

#### Issue: Redirect URI mismatch
**Solution:** Check Google Cloud Console:
1. Go to https://console.cloud.google.com/apis/credentials
2. Click OAuth 2.0 Client ID
3. Add redirect URI: `https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev/auth/callback`

#### Issue: CORS error in browser
**Solution:** Backend CORS is configured, but check browser console:
```
Access-Control-Allow-Origin: https://shiny-space-guide-pj4gwgp94gw93557-3000.app.github.dev
```

---

## 📊 OAuth Flow Diagram

```
User                     Reflex Portal           Backend API            Google
 |                            |                       |                    |
 |-- Click "Sign in" -------->|                       |                    |
 |                            |-- GET /auth/login --->|                    |
 |                            |                       |-- Redirect ------->|
 |<---------------------------------------------------|                    |
 |                                                     |                    |
 |-- Select Google Account ------------------------------------------------>|
 |<-- Consent Screen --------------------------------------------------------|
 |-- Click "Allow" --------------------------------------------------------->|
 |                                                     |<-- code ----------|
 |                            |                       |-- Exchange code -->|
 |                            |                       |<-- access_token ---|
 |                            |                       |-- Get userinfo --->|
 |                            |                       |<-- email, name ----|
 |                            |<-- Redirect with JWT--|                    |
 |<-- /dashboard -------------|                       |                    |
 |                            |                       |                    |
```

---

## ✅ Success Criteria

- [ ] Login page loads without errors
- [ ] "Sign in with Google" redirects to Google
- [ ] After consent, returns to callback page
- [ ] JWT stored in localStorage
- [ ] Dashboard loads with data
- [ ] Session persists on refresh
- [ ] Admin user sees admin-level access
- [ ] Logout clears session (if implemented)

---

## 🔗 URLs

| Service | URL |
|---------|-----|
| **Login** | https://shiny-space-guide-pj4gwgp94gw93557-3000.app.github.dev/login |
| **Dashboard** | https://shiny-space-guide-pj4gwgp94gw93557-3000.app.github.dev/dashboard |
| **Backend API** | https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev |
| **API Docs** | https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev/api/docs |
| **OAuth Endpoint** | https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev/auth/login |

---

## 🧪 Manual Test Script

```bash
# 1. Start servers (already running)
ps aux | grep -E "(uvicorn|reflex)"

# 2. Test OAuth login endpoint
curl -I "https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev/auth/login"
# Expected: 302 redirect to Google

# 3. Open login page in browser
# Navigate to: https://shiny-space-guide-pj4gwgp94gw93557-3000.app.github.dev/login
# Click "Sign in with Google"
# Complete OAuth flow

# 4. Verify JWT stored
# In browser DevTools console:
localStorage.getItem('waooaw_token')
# Should see JWT string

# 5. Access dashboard
# Navigate to: https://shiny-space-guide-pj4gwgp94gw93557-3000.app.github.dev/dashboard
# Should load with metrics
```

---

**Ready to test! Try logging in with your Google account.** 🔐
