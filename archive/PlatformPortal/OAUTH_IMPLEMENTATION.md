# Platform Portal OAuth Implementation

**Date**: January 4, 2026  
**Status**: ✅ Complete - Backend OAuth flow identical to WaooawPortal

---

## Overview

Platform Portal now uses the **exact same OAuth 2.0 flow** as WaooawPortal for consistency. Users authenticate via Google OAuth through the FastAPI backend, which handles all token exchange and user management.

---

## Architecture

```
User Browser
    ↓
Reflex Frontend (Port 3001)
    ↓ (Click "Sign in with Google")
FastAPI Backend (Port 8000)
    ↓ /auth/login?frontend=pp
Google OAuth Server
    ↓ (User approves)
FastAPI Backend /auth/callback
    ↓ (Exchange code for token)
Google User Info API
    ↓ (JWT creation)
Redirect to Frontend /auth/callback?token=...
    ↓ (Store in localStorage)
Dashboard
```

---

## Components

### 1. Backend OAuth Router (`/backend/oauth.py`)

**Features:**
- ✅ Multi-environment detection (codespace, demo, uat, production)
- ✅ Auto-configured redirect URIs based on X-Forwarded-Host
- ✅ State encoding with CSRF protection
- ✅ JWT token creation with 7-day expiry
- ✅ Role-based access (admin, operator, viewer)
- ✅ Structured logging with structlog

**Endpoints:**
- `GET /auth/login?frontend=pp` - Initiates OAuth flow
- `GET /auth/callback` - Handles Google redirect, creates JWT
- `GET /auth/logout` - Logout endpoint
- `GET /auth/me` - Get current user info (TODO)

### 2. Backend Config (`/backend/config.py`)

**Environment Detection:**
- **Codespace**: `app.github.dev` → Port 3001 frontend, 8000 backend
- **Demo**: `demo.waooaw.com` → Custom domain
- **UAT**: `uat-pp.waooaw.com` → Custom domain
- **Production**: `pp.waooaw.com` → Custom domain
- **Development**: `localhost` → Local ports

**CORS Origins:**
Automatically configures CORS based on environment

### 3. Reflex Frontend (`/PlatformPortal_v2/PlatformPortal_v2.py`)

**Login Page:**
- Detects environment (codespace vs production)
- Constructs backend URL dynamically
- Redirects to `/auth/login?frontend=pp`

**Auth Callback Page:**
- Extracts token, email, name, picture, role from URL params
- Stores in localStorage
- Redirects to dashboard

**Dashboard:**
- Checks localStorage for authentication
- Displays user email and role
- Logout clears localStorage

---

## Environment Variables

Required in `/PlatformPortal/.env`:

```bash
# OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Environment
ENV=codespace  # or demo, uat, production, development

# Optional: Override backend URL
BACKEND_URL=https://YOUR-CODESPACE-8000.app.github.dev
```

---

## Google OAuth Configuration

**Client ID**: `270293855600-uoag582a6r5eqq4ho43l3mrvob6gpdmq`

**Authorized Redirect URIs** (must be added in Google Cloud Console):
- `https://*-8000.app.github.dev/auth/callback` (Codespace)
- `https://demo.waooaw.com/api/auth/callback` (Demo)
- `https://uat-api.waooaw.com/auth/callback` (UAT)
- `https://api.waooaw.com/auth/callback` (Production)
- `http://localhost:8000/auth/callback` (Development)

**How to add wildcards:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. APIs & Services → Credentials
3. OAuth 2.0 Client IDs → Select client
4. Add redirect URI with wildcard for Codespaces

---

## Usage

### Start Platform Portal

```bash
cd /workspaces/WAOOAW/PlatformPortal
./start.sh
```

This starts:
1. **FastAPI Backend** on port 8000 (OAuth endpoints)
2. **Reflex Frontend** on port 3001 (UI)

### Access in Codespace

- **Frontend**: `https://YOUR-CODESPACE-3001.app.github.dev/`
- **Backend**: `https://YOUR-CODESPACE-8000.app.github.dev/docs`
- **Health Check**: `https://YOUR-CODESPACE-8000.app.github.dev/health`

### Test OAuth Flow

1. Open frontend URL
2. Click "Sign in with Google"
3. Approve Google consent screen
4. Redirected back to `/auth/callback`
5. Token stored in localStorage
6. Dashboard displayed with user info

---

## Differences from WaooawPortal

**Identical:**
- OAuth flow logic
- Environment detection
- State encoding/decoding
- JWT creation
- User role assignment

**Different:**
- Default frontend is `pp` (Platform Portal) instead of `www`
- Reflex port is 3001 instead of 8080
- No database integration (yet)
- Simpler state management (Reflex State instead of React)

---

## Security Features

✅ **CSRF Protection**: State parameter with random token  
✅ **JWT Tokens**: 7-day expiry with HS256 signing  
✅ **Role-Based Access**: Admin, Operator, Viewer roles  
✅ **CORS**: Restricted to allowed origins  
✅ **HTTPS Only**: All production traffic encrypted  
✅ **Token Storage**: localStorage (secure in HTTPS)

---

## Debugging

### Check Backend Health

```bash
curl https://YOUR-CODESPACE-8000.app.github.dev/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "codespace",
  "oauth_configured": true
}
```

### View Logs

Backend logs show:
- OAuth login initiation
- Environment detection
- Redirect URI construction
- Token exchange success/failure
- User info retrieval

Look for:
```
oauth_login_initiated environment=codespace
oauth_redirect_to_google redirect_uri=https://...
oauth_callback_started has_code=true
oauth_login_success email=user@example.com role=admin
```

### Common Issues

**Issue**: "Google OAuth not configured"  
**Fix**: Check `.env` file has `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`

**Issue**: "Redirect URI mismatch"  
**Fix**: Add Codespace redirect URI to Google Cloud Console

**Issue**: "Token exchange failed"  
**Fix**: Check backend logs for error details, verify Google credentials

---

## Next Steps

1. ✅ Backend OAuth router created
2. ✅ Environment detection implemented
3. ✅ Reflex frontend updated for OAuth flow
4. ⏳ **Test in Codespace** (ready to test!)
5. 📋 Add user database storage
6. 📋 Implement JWT validation middleware
7. 📋 Add refresh token support

---

## Files Modified

```
PlatformPortal/
├── backend/
│   ├── __init__.py          # New - Package init
│   ├── config.py            # New - Environment config
│   ├── main.py              # New - FastAPI app
│   └── oauth.py             # New - OAuth router (mirrors WaooawPortal)
├── PlatformPortal_v2/
│   └── PlatformPortal_v2.py # Modified - OAuth flow integration
├── requirements.txt         # Modified - Added FastAPI dependencies
├── start.sh                 # New - Startup script
├── .env                     # Existing - OAuth credentials
└── OAUTH_IMPLEMENTATION.md  # New - This file
```

---

## Testing Checklist

- [ ] Backend starts on port 8000
- [ ] Frontend starts on port 3001
- [ ] Health check returns "healthy"
- [ ] Login page loads with Google button
- [ ] Click button redirects to Google
- [ ] Google consent screen appears
- [ ] Approve redirects back to callback page
- [ ] Token appears in URL params
- [ ] localStorage populated with user data
- [ ] Dashboard loads with user email
- [ ] Logout clears localStorage

---

**Status**: Ready for testing! 🚀

Run `./start.sh` to test the full OAuth flow.
