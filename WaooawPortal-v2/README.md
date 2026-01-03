# WaooawPortal v2 (Customer Frontend)

> Customer-facing marketplace for browsing and hiring AI agents

## Tech Stack

- **Framework**: React 18 with Vite
- **Routing**: React Router DOM v6
- **Styling**: CSS3 with CSS Variables (Dark Theme)
- **Build Tool**: Vite

## Environment Detection

The app automatically detects its environment based on hostname:
- `demo-www.waooaw.com` or `demo.waooaw.com` → **demo**
- `uat-www.waooaw.com` or `uat.waooaw.com` → **uat**
- `www.waooaw.com` → **production**
- `localhost` → **development**

API URLs are configured automatically:
- **Development**: `http://localhost:8000`
- **Demo**: `https://demo-api.waooaw.com`
- **UAT**: `https://uat-api.waooaw.com`
- **Production**: `https://api.waooaw.com`

## Features

### Pages

1. **Home** (`/`)
   - Hero section with WAOOAW branding
   - Environment badge (DEMO/UAT/PRODUCTION)
   - Features showcase (Try Before Hire, Marketplace DNA, Agentic Vibe, Zero Risk)
   - Industries overview (Marketing, Education, Sales)
   - CTA sections

2. **Marketplace** (`/marketplace`)
   - Agent browsing with cards
   - Search functionality
   - Industry filters (All, Marketing, Education, Sales)
   - Agent details: avatar, status, rating, specialty, activity, price
   - "Start 7-Day Trial" CTA

3. **Auth Callback** (`/auth/callback`)
   - Handles OAuth callback from backend
   - Exchanges code for token
   - Stores token and user info in localStorage
   - Redirects to marketplace after successful auth

### Design System

**Colors** (Dark Theme):
- Background: `#0a0a0a` (black), `#18181b` (gray-900)
- Neon Accents: `#00f2fe` (cyan), `#667eea` (purple), `#f093fb` (pink)
- Status: `#10b981` (green/available), `#f59e0b` (yellow/working), `#ef4444` (red/offline)

**Fonts**:
- Display: Space Grotesk (700)
- Headings: Outfit (600)
- Body: Inter (400)

**Components**:
- Agent Cards: Hover effects with neon glow
- Buttons: Primary (gradient), Secondary (gray)
- Filters: Active state with cyan highlight
- Status Dots: Color-coded by agent availability

## Development

### Install Dependencies
```bash
cd WaooawPortal-v2
npm install
```

### Run Development Server
```bash
npm run dev
```
Starts on `http://localhost:3000`

### Build for Production
```bash
npm run build
```
Output in `dist/` directory

### Preview Production Build
```bash
npm run preview
```

## OAuth Flow

1. User clicks "Sign In" → Frontend redirects to `${apiUrl}/auth/login?frontend=www`
2. Backend redirects to Google OAuth
3. Google redirects back to `${apiUrl}/auth/callback?code=...`
4. Backend validates, creates JWT, redirects to `${frontendUrl}/auth/callback?access_token=...`
5. Frontend stores token in localStorage
6. Frontend redirects to `/marketplace`

## Docker Deployment

```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Environment Variables (Build Time)

No environment variables needed - environment detection is automatic based on hostname.

## Deployment Targets

- **Demo**: `demo-www.waooaw.com` (Cloud Run: `waooaw-portal-demo`)
- **UAT**: `uat-www.waooaw.com` (Cloud Run: `waooaw-portal-uat`)
- **Production**: `www.waooaw.com` (Cloud Run: `waooaw-portal-prod`)

## Brand Compliance

✅ Dark theme (#0a0a0a background)
✅ Neon cyan/purple accents
✅ "WAOOAW" name (all caps, palindrome)
✅ "Agents Earn Your Business" tagline
✅ Marketplace DNA (browse/compare/discover)
✅ Agentic vibe (avatars, status, personality)
✅ Try-before-hire messaging
✅ Space Grotesk display font

## API Integration

All API calls go through `config.js`:
```javascript
import config from './config';

fetch(`${config.apiUrl}/agents`)
```

Current API endpoints used:
- `GET /auth/login?frontend=www` - Initiate OAuth
- `GET /auth/callback?code=...&state=...` - OAuth callback
- `GET /agents` (planned) - Fetch agents list
- `POST /trials` (planned) - Start agent trial

## Next Steps

1. ✅ Basic structure and pages created
2. ⏳ Add Docker deployment
3. ⏳ Integrate real agents API
4. ⏳ Implement trial management
5. ⏳ Add user dashboard
6. ⏳ Deploy to demo-www.waooaw.com
