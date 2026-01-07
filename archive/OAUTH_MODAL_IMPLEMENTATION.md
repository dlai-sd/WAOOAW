# OAuth Modal Implementation - Google Identity Services

## Overview

Both WAOOAW portals now use **Google Identity Services (GIS)** for authentication with **modal popups** instead of full-page redirects. This provides a modern, seamless user experience.

## Architecture

### Flow:
1. User clicks "Sign in with Google"
2. Modal appears with Google sign-in button
3. Google popup authenticates user (no page redirect!)
4. Frontend receives JWT token from Google
5. Frontend sends token to backend for verification
6. Backend verifies token with Google, creates app session
7. Backend returns app access token
8. User is authenticated - modal closes, dashboard loads

### Key Features:
✅ **No page redirects** - pure modal experience  
✅ **Token-based auth** - JWT tokens, no session cookies  
✅ **Multi-environment** - auto-detects dev/codespace/demo/prod  
✅ **Secure** - Backend verifies all tokens with Google  
✅ **Role-based access** - Admin, Operator, Viewer roles  

---

## 1. WaooawPortal (Customer Portal)

**Stack:** React + Vite + FastAPI backend

### Frontend Implementation

**Component:** `/WaooawPortal/src/components/GoogleSignIn.jsx`
- Uses Google Identity Services library
- Renders Google button in modal
- Handles credential callback
- Sends token to backend for verification

**Styling:** `/WaooawPortal/src/components/GoogleSignIn.css`
- Dark theme compatible
- Modal animations (fadeIn, slideUp)
- Loading states, error handling

**Integration:** `/WaooawPortal/src/pages/Home.jsx`
```jsx
import GoogleSignIn from '../components/GoogleSignIn';

const [showSignInModal, setShowSignInModal] = useState(false);

// In render:
{showSignInModal && (
  <div className="google-signin-modal-overlay">
    <GoogleSignIn 
      onSuccess={handleSignInSuccess}
      onError={handleSignInError}
    />
  </div>
)}
```

**Configuration:** `/WaooawPortal/src/config.js`
```javascript
const GOOGLE_CLIENT_IDS = {
  development: import.meta.env.VITE_GOOGLE_CLIENT_ID,
  demo: 'client-id-for-demo',
  production: 'client-id-for-prod',
};
```

### Backend Implementation

**Endpoint:** `/WaooawPortal/backend/app/auth/oauth_v2.py`

```python
@router.post("/google/verify")
async def verify_google_token(token_request: GoogleTokenRequest):
    """
    Verify Google Identity Services JWT token
    Returns user data + app access token
    """
    # 1. Verify token with Google's tokeninfo endpoint
    verify_response = await client.get(
        f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
    )
    
    # 2. Verify audience (client ID)
    if token_data["aud"] != settings.GOOGLE_CLIENT_ID:
        raise HTTPException(401, "Invalid token")
    
    # 3. Extract user info
    email = token_data["email"]
    role = get_user_role(email)  # admin/operator/viewer
    
    # 4. Create app access token (JWT)
    access_token = jwt.encode({
        "email": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=7)
    }, app_secret, algorithm="HS256")
    
    # 5. Return user data + token
    return {
        "access_token": access_token,
        "email": email,
        "name": name,
        "role": role
    }
```

### Environment Setup

**File:** `/WaooawPortal/.env.example`
```bash
# Frontend (Vite)
VITE_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com

# Backend (FastAPI)
GOOGLE_CLIENT_ID=same-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

**Note:** `VITE_` prefix exposes variable to Vite frontend build.

---

## 2. PlatformPortal (Operations Portal)

**Stack:** Reflex (Pure Python)

### Implementation

**Component:** `/PlatformPortal/PlatformPortal_v2/components/google_signin.py`
```python
def google_signin_modal(state_class) -> rx.Component:
    """Modal with Google Sign-In button"""
    return rx.cond(
        state_class.show_signin_modal,
        rx.box(  # Modal overlay
            rx.box(  # Modal content
                rx.html("""
                    <div id="g_id_onload" 
                         data-client_id="{client_id}"
                         data-callback="handleGoogleSignIn">
                    </div>
                    <div class="g_id_signin"></div>
                """),
            )
        )
    )

def google_signin_script() -> rx.Component:
    """JavaScript for Google Identity Services"""
    return rx.fragment(
        rx.script(src="https://accounts.google.com/gsi/client"),
        rx.script("""
            window.handleGoogleSignIn = async (response) => {
                // Send token to backend
                // Update localStorage
                // Reload page
            };
        """)
    )
```

**State Management:** `/PlatformPortal/PlatformPortal_v2/PlatformPortal_v2.py`
```python
class PlatformState(rx.State):
    show_signin_modal: bool = False
    is_authenticated: bool = False
    user_email: str = ""
    auth_token: str = ""
    
    def open_signin_modal(self):
        self.show_signin_modal = True
    
    def logout(self):
        self.is_authenticated = False
        return rx.call_script("""
            localStorage.clear();
            window.location.reload();
        """)
```

**Integration:**
```python
def dashboard() -> rx.Component:
    return rx.fragment(
        google_signin_script(),  # Include in <head>
        google_signin_modal(PlatformState),  # Modal component
        # Dashboard content...
    )
```

### Environment Setup

**File:** `/PlatformPortal/.env.example`
```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
ENV=development  # auto-detected
```

---

## Google Cloud Console Setup

### 1. Create OAuth Client

1. Go to https://console.cloud.google.com/
2. Select/create project
3. Navigate to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth 2.0 Client ID**
5. Application type: **Web application**

### 2. Configure Authorized Origins

**For WaooawPortal (Customer Portal):**
```
http://localhost:8080
https://*.app.github.dev
https://www.waooaw.com
https://demo.waooaw.com
```

**For PlatformPortal (Operations Portal):**
```
http://localhost:3000
https://*.app.github.dev
https://pp.waooaw.com
https://pp.demo.waooaw.com
```

### 3. Authorized Redirect URIs

*(Optional - not strictly needed for modal auth, but good practice)*
```
http://localhost:8080/auth/callback
http://localhost:3000/auth/callback
https://*.app.github.dev/auth/callback
https://www.waooaw.com/auth/callback
https://pp.waooaw.com/auth/callback
```

### 4. Download Credentials

- Copy **Client ID** to `.env` files
- Copy **Client Secret** to backend `.env` files
- Never commit these to git!

---

## Testing

### Development (Localhost)

**WaooawPortal:**
```bash
cd WaooawPortal

# Frontend
npm install
npm run dev  # http://localhost:8080

# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload  # http://localhost:8000
```

**PlatformPortal:**
```bash
cd PlatformPortal
pip install -r requirements.txt
reflex run  # http://localhost:3000
```

### Codespaces

Both portals auto-detect Codespace environment:
- Extracts `CODESPACE_NAME` from URL
- Constructs backend URL: `https://{codespace}-8000.app.github.dev`
- Uses Codespace-specific Google Client ID

### Demo/Production

Set environment variables in Cloud Run:
```bash
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx
ENV=demo  # or production
```

---

## Security Considerations

### Token Verification
✅ Backend verifies token with Google's tokeninfo endpoint  
✅ Checks token audience (client ID) matches  
✅ Validates email_verified flag  
✅ No trust-frontend-only authentication

### Token Storage
✅ Access tokens stored in localStorage (7-day expiry)  
✅ Can be revoked by logout  
✅ Backend validates on every request (TODO: implement middleware)

### Role-Based Access
```python
def get_user_role(email: str) -> str:
    if email in ["admin@waooaw.ai", "yogeshkhandge@gmail.com"]:
        return "admin"
    elif email.endswith("@waooaw.ai"):
        return "operator"
    else:
        return "viewer"
```

### HTTPS Only
⚠️ Production must use HTTPS:
- Google requires https:// for OAuth (except localhost)
- Codespaces auto-provide HTTPS
- Cloud Run provides HTTPS by default

---

## Troubleshooting

### "Google Sign-In is not configured"
→ Check `GOOGLE_CLIENT_ID` in `.env` file  
→ Ensure `VITE_GOOGLE_CLIENT_ID` for Vite frontend

### "Token audience mismatch"
→ Frontend and backend using different Client IDs  
→ Verify `.env` files match Google Console credentials

### "Origin not allowed"
→ Add current URL to Authorized JavaScript origins in Google Console  
→ Wildcard `*.app.github.dev` for Codespaces

### Modal not appearing
→ Check browser console for JavaScript errors  
→ Verify Google script loaded: `https://accounts.google.com/gsi/client`  
→ Check `show_signin_modal` state is `true`

### "Email not verified"
→ User's Google account email not verified  
→ Ask user to verify email in Google Account settings

---

## Migration from Redirect-Based OAuth

### Old Flow (Deprecated):
1. User clicks "Sign In"
2. Redirect to `/auth/login`
3. Backend redirects to Google
4. Google redirects back to `/auth/callback`
5. Backend redirects to frontend with token in URL

### New Flow (Current):
1. User clicks "Sign In"
2. Modal opens
3. Google popup authenticates
4. Token sent to backend via API
5. Backend returns app token
6. Modal closes, user authenticated

### Benefits:
✅ No page reloads - smoother UX  
✅ No token in URL - more secure  
✅ Faster - fewer round trips  
✅ Modern - aligns with industry best practices  

---

## Next Steps

### Immediate:
- [ ] Test on Codespaces
- [ ] Test on local development
- [ ] Add Google Client IDs to GitHub Secrets
- [ ] Deploy to demo environment

### Future Enhancements:
- [ ] Add JWT middleware for protected routes
- [ ] Implement token refresh logic
- [ ] Add user database (PostgreSQL)
- [ ] Add audit logging for auth events
- [ ] Support multiple OAuth providers (GitHub, Microsoft)
- [ ] Add 2FA support

---

## Files Changed

### WaooawPortal:
- ✅ `src/components/GoogleSignIn.jsx` - Modal component
- ✅ `src/components/GoogleSignIn.css` - Styling
- ✅ `src/pages/Home.jsx` - Integration
- ✅ `src/config.js` - Client ID config
- ✅ `backend/app/auth/oauth_v2.py` - Token verification endpoint
- ✅ `.env.example` - Environment template

### PlatformPortal:
- ✅ `PlatformPortal_v2/components/google_signin.py` - Modal component
- ✅ `PlatformPortal_v2/PlatformPortal_v2.py` - State & integration
- ✅ `.env.example` - Environment template

### Documentation:
- ✅ This file (`OAUTH_MODAL_IMPLEMENTATION.md`)

---

## Support

For issues or questions:
- Check browser console for JavaScript errors
- Check backend logs for verification errors
- Review Google Cloud Console OAuth settings
- Ensure environment variables are set correctly

**Documentation:** This file  
**Google Identity Services Docs:** https://developers.google.com/identity/gsi/web  
**OAuth 2.0 Spec:** https://oauth.net/2/
