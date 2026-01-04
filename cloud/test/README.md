# WAOOAW Test Environment (Codespace)

**Environment**: GitHub Codespaces  
**Purpose**: Local development and testing before deployment

## Services

### Platform Portal v2
- **Frontend**: Port 3001
- **Backend**: Port 3000
- **OAuth**: Enabled (requires Codespace URLs in OAuth Console)

### Backend API v2
- **Port**: 8000
- **OAuth**: Enabled
- **Hot Reload**: Yes

## Quick Start

```bash
# Start all services
./portal-v2.sh start

# Check status
./portal-v2.sh status

# View logs
./portal-v2.sh logs backend
./portal-v2.sh logs portal

# Restart
./portal-v2.sh restart

# Stop
./portal-v2.sh stop
```

## URLs

When running in Codespace `shiny-space-guide-pj4gwgp94gw93557`:

- **Platform Portal**: https://shiny-space-guide-pj4gwgp94gw93557-3001.app.github.dev
- **Backend API**: https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev

## OAuth Configuration

**Required Redirect URI in Google Console**:
```
https://{CODESPACE_NAME}-8000.app.github.dev/auth/callback
```

Example for current Codespace:
```
https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev/auth/callback
```

**Note**: You must add your Codespace's redirect URI to Google OAuth Console before testing OAuth.

## Port Forwarding

Ensure ports are set to **PUBLIC** visibility in Codespace:
- Port 3001: Platform Portal Frontend
- Port 3000: Platform Portal Backend (Reflex API)
- Port 8000: Backend API

## Environment Detection

Services automatically detect Codespace environment using:
- `CODESPACE_NAME` environment variable (set by GitHub)
- X-Forwarded-Host headers for OAuth redirect_uri

## Testing OAuth Flow

1. Start services: `./portal-v2.sh start`
2. Get URL: `./portal-v2.sh status`
3. Click Platform Portal URL
4. Click "Sign in with Google"
5. Approve OAuth consent
6. Should redirect to dashboard

## Troubleshooting

### OAuth "invalid_client" error
- Check redirect URI matches exactly in Google Console
- Ensure port 8000 is PUBLIC in Codespace
- Verify `.env.local` has correct GOOGLE_CLIENT_ID

### Backend not responding
- Check logs: `./portal-v2.sh logs backend`
- Verify `.env.local` exists with OAuth secrets
- Check port 8000 not in use: `lsof -i :8000`

### Portal not loading
- Check logs: `./portal-v2.sh logs portal`
- Wait 15-20s for Reflex compilation
- Verify port 3001 is PUBLIC in Codespace

## Files

- `portal-v2.sh`: Main management script
- `../../backend-v2/.env.local`: OAuth secrets
- `/tmp/waooaw_backend_v2.log`: Backend logs
- `/tmp/waooaw_platform_portal_v2.log`: Portal logs
