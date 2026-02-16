# Google Authentication (CP) - Testing Guide

This guide documents how Google authentication works in the Customer Portal (CP), what must be configured, and how to validate it locally and in Codespaces.

## How CP Google auth works

CP supports two Google auth flows:

1) **Google Identity Services (GIS) / “Sign in with Google” button**
- Frontend uses `@react-oauth/google` to obtain an **ID token**.
- Frontend sends the ID token to CP backend: `POST /api/auth/google/verify`.

2) **Backend OAuth redirect flow**
- Frontend navigates to CP backend: `GET /api/auth/google/login`.
- Backend redirects to Google, then handles `GET /api/auth/google/callback`.

## Required configuration

### Frontend (CP FrontEnd)
- `VITE_GOOGLE_CLIENT_ID` (build-time / dev-server-time Vite env var)

### Backend (CP BackEnd)
- `GOOGLE_CLIENT_ID` (must match the frontend client ID for token verification)
- `GOOGLE_CLIENT_SECRET` (required only for the redirect flow that exchanges `code` for tokens)

## Codespaces: what’s possible

Google will not accept wildcards for **Authorized JavaScript origins** or **Redirect URIs**. Because Codespaces hostnames change (per codespace), Google auth will only work in a Codespace after you add that exact Codespace URL to your Google OAuth client configuration.

If you cannot update Google Cloud Console, use **Demo/UAT** (stable domains) or test on **localhost** instead.

## Local / Codespaces ports in this repo

- CP FrontEnd (Vite dev server): `3000`
- CP BackEnd (docker compose): `8020` (FastAPI with `/api` prefix)

## Verification checklist

1) CP backend auth health should report OAuth configured:
- `GET http://localhost:8020/api/auth/health` should return `oauth_configured: true` when `GOOGLE_CLIENT_ID` is set.

2) The backend redirect endpoint should produce a Google URL with a non-empty `client_id`:
- `GET http://localhost:8020/api/auth/google/login?source=cp` should redirect to `https://accounts.google.com/...client_id=...`.

3) GIS flow requires the Codespace origin to be allowed in Google Console:
- Add your forwarded CP FrontEnd origin (example format): `https://<CODESPACE_NAME>-3000.app.github.dev`

4) Redirect flow requires redirect URI allowlisting too:
- Add the CP backend callback (example format): `https://<CODESPACE_NAME>-8020.app.github.dev/api/auth/google/callback`

## Key files

- Frontend provider wiring: `src/CP/FrontEnd/src/main.tsx`
- Frontend config: `src/CP/FrontEnd/src/config/oauth.config.ts`
- Google button: `src/CP/FrontEnd/src/components/auth/GoogleLoginButton.tsx`
- Backend routes: `src/CP/BackEnd/api/auth/routes.py`
- Backend verification: `src/CP/BackEnd/api/auth/google_oauth.py`
