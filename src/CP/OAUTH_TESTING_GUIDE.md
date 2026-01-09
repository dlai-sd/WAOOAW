# Google OAuth Integration - Testing Guide

## ✅ Implementation Complete!

### **Single Port Setup (Port 8000)**

Both frontend and backend are served on a single port (8000) for simplicity in Codespaces.

---

## 🚀 Quick Start

### Start the Application:
```bash
cd /workspaces/WAOOAW/src/CP
./start.sh
```

### Stop the Application:
```bash
cd /workspaces/WAOOAW/src/CP
./stop.sh
```

---

## 🌐 Access URLs

**Application:** https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev  
**API Docs:** https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev/docs  
**Health Check:** https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev/health

---

## 📋 Before Testing - Update Google OAuth Console

Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials) and add:

**Authorized JavaScript origins:**
```
https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev
```

**Authorized redirect URIs:**
```
https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev/api/auth/google/callback
https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev/auth/callback
```

### 2. **Servers Running**

✅ **Backend:** https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev
✅ **Frontend:** https://shiny-space-guide-pj4gwgp94gw93557-3001.app.github.dev

### 3. **Test the Flow**

1. **Open the frontend** in your browser
2. **Click "Sign In"** button in the header
3. **Auth modal appears** with Google Sign-In button
4. **Click "Sign in with Google"**
5. **Select your Google account**
6. **Authorize the app**
7. **You'll be redirected** to the dashboard

### 4. **Verify API**

Check backend health:
```bash
curl https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev/health
```

Check auth health:
```bash
curl https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev/api/auth/health
```

### 5. **View API Docs**

FastAPI automatic documentation:
- **Swagger UI:** https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev/docs
- **ReDoc:** https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev/redoc

---

## 🔧 Configuration Files

### Backend `.env`
```
/workspaces/WAOOAW/src/CP/BackEnd/.env
```

### Frontend `.env`
```
/workspaces/WAOOAW/src/CP/FrontEnd/.env
```

---

## 🌍 Multi-Environment Support

The implementation supports:

### ✅ **Codespace** (Current)
- Frontend: Port 3001
- Backend: Port 8000
- Dynamic URL detection

### ✅ **Demo**
- Frontend: `https://cp.demo.waooaw.com`
- Backend: `https://cp.demo.waooaw.com/api`

### ✅ **UAT**
- Frontend: `https://cp.uat.waooaw.com`
- Backend: `https://cp.uat.waooaw.com/api`

### ✅ **Production**
- Frontend: `https://www.waooaw.com`
- Backend: `https://www.waooaw.com/api`

### ✅ **Mobile App Support**
- Add redirect URI: `com.waooaw.app:/oauth2callback`
- Use `source` parameter to identify app (cp, pp, mobile)

---

## 📦 Key Features

### Security
- ✅ CSRF protection via state parameter
- ✅ JWT tokens with expiry (15 min access, 7 days refresh)
- ✅ Secure HTTP-only token storage
- ✅ Token auto-refresh before expiry

### User Experience
- ✅ Google One Tap sign-in
- ✅ Account selection prompt
- ✅ Persistent sessions
- ✅ Automatic redirect after login
- ✅ Clean URL after OAuth callback

### Architecture
- ✅ Shared OAuth backend for CP, PP, Mobile
- ✅ Environment-specific configuration
- ✅ In-memory user store (ready for database)
- ✅ Modular code structure

---

## 🔑 Token Flow

1. **User clicks Sign In** → Opens auth modal
2. **Clicks Google button** → Sends ID token to backend
3. **Backend verifies** with Google → Creates user
4. **Backend generates** JWT tokens (access + refresh)
5. **Frontend stores** tokens in localStorage
6. **Frontend makes** authenticated requests with Bearer token
7. **Token expires** → Auto-refresh with refresh token
8. **User accesses** protected routes/data

---

## 📝 Next Steps

### For Production Deployment:

1. **Database Integration**
   - Replace in-memory user store with PostgreSQL
   - Add `users` and `sessions` tables
   - Store refresh tokens securely

2. **Secret Management**
   - Add secrets to GCP Secret Manager:
     ```bash
     gcloud secrets create GOOGLE_CLIENT_ID --data-file=<(echo -n "YOUR_CLIENT_ID")
     gcloud secrets create GOOGLE_CLIENT_SECRET --data-file=<(echo -n "YOUR_SECRET")
     gcloud secrets create JWT_SECRET --data-file=<(echo -n "$(openssl rand -base64 32)")
     ```

3. **Redis for Sessions**
   - Store refresh tokens in Redis
   - Implement token blacklist for logout
   - Enable session management

4. **Update OAuth Redirect URIs**
   - Add production domains to Google Console
   - Update `.env` files for each environment

5. **Testing**
   - Unit tests for auth flow
   - Integration tests for token refresh
   - E2E tests for login/logout

---

## 🐛 Troubleshooting

### "Invalid OAuth client"
→ Update redirect URIs in Google Console

### "CORS error"
→ Check `CORS_ORIGINS` in backend `.env`

### "Token expired"
→ Normal - will auto-refresh

### "User not found"
→ Clear localStorage and try again

---

## 📚 File Structure

```
src/CP/
├── BackEnd/
│   ├── .env                          # Backend config
│   ├── main.py                       # FastAPI app
│   ├── requirements.txt              # Dependencies
│   ├── api/
│   │   └── auth/
│   │       ├── routes.py             # Auth API routes
│   │       ├── google_oauth.py       # Google OAuth logic
│   │       ├── user_store.py         # User storage
│   │       └── dependencies.py       # Auth dependencies
│   ├── core/
│   │   ├── config.py                 # Settings
│   │   └── jwt_handler.py            # JWT logic
│   └── models/
│       └── user.py                   # User models
│
└── FrontEnd/
    ├── .env                          # Frontend config
    ├── src/
    │   ├── config/
    │   │   └── oauth.config.ts       # OAuth config
    │   ├── services/
    │   │   └── auth.service.ts       # Auth API calls
    │   ├── context/
    │   │   └── AuthContext.tsx       # Auth state
    │   ├── hooks/
    │   │   └── useAuth.ts            # Auth hook
    │   ├── components/
    │   │   └── auth/
    │   │       ├── GoogleLoginButton.tsx
    │   │       └── AuthModal.tsx
    │   └── pages/
    │       └── AuthCallback.tsx      # OAuth callback
```

---

**Status: ✅ Ready for Testing!**

Open the frontend and click "Sign In" to test the flow!
