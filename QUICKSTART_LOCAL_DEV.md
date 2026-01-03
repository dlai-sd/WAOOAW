# WAOOAW V2 - Local Development Quick Start

> Get the entire v2 stack running locally in 5 minutes

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (optional, for PostgreSQL)
- Google Cloud Console OAuth credentials

---

## 1. Database Setup

### Option A: Docker PostgreSQL (Recommended)

```bash
docker run -d \
  --name waooaw-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=waooaw \
  -p 5432:5432 \
  postgres:15-alpine

# Create schemas
docker exec -it waooaw-postgres psql -U postgres -d waooaw -c "CREATE SCHEMA demo;"
docker exec -it waooaw-postgres psql -U postgres -d waooaw -c "CREATE SCHEMA uat;"
```

### Option B: Local PostgreSQL

```bash
# macOS
brew install postgresql@15
brew services start postgresql@15

# Ubuntu/Debian
sudo apt install postgresql-15
sudo systemctl start postgresql

# Create database and schemas
createdb waooaw
psql waooaw -c "CREATE SCHEMA demo;"
psql waooaw -c "CREATE SCHEMA uat;"
```

---

## 2. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to: **APIs & Services** → **Credentials**
3. Create OAuth 2.0 Client ID:
   - Application type: **Web application**
   - Name: `WAOOAW Local Dev`
   - Authorized redirect URIs:
     ```
     http://localhost:8000/auth/callback
     ```
4. Copy **Client ID** and **Client Secret**

---

## 3. Backend Setup

```bash
cd backend-v2

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
ENV=development
DB_HOST=localhost
DB_PORT=5432
DB_NAME=waooaw
DB_USER=postgres
DB_PASSWORD=postgres
DB_SCHEMA=demo
GOOGLE_CLIENT_ID=your-client-id-here
GOOGLE_CLIENT_SECRET=your-client-secret-here
JWT_SECRET=your-random-secret-here-change-me
EOF

# Run backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend running at**: http://localhost:8000

**Test it**:
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","environment":"development"}
```

---

## 4. WaooawPortal Setup (Customer Frontend)

```bash
# Open new terminal
cd WaooawPortal-v2

# Install dependencies
npm install

# Run development server
npm run dev
```

**WaooawPortal running at**: http://localhost:3000

**Features**:
- Home page with hero section
- Marketplace with agent cards
- OAuth sign-in flow
- Environment badge showing "DEVELOPMENT"

---

## 5. PlatformPortal Setup (Internal Dashboard)

```bash
# Open new terminal
cd PlatformPortal-v2

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Reflex (if requirements.txt has it)
pip install reflex

# Or use existing requirements.txt
pip install -r requirements.txt

# Initialize and run
reflex run
```

**PlatformPortal running at**: http://localhost:8000 (or different port if 8000 is taken)

**Note**: Reflex may use port 3001 if 3000 is taken. Check terminal output.

---

## 6. Full Stack Test

### Test OAuth Flow

1. Open http://localhost:3000/ (WaooawPortal)
2. Click **"Sign In"** button
3. You'll be redirected to Google OAuth
4. Sign in with your Google account
5. After OAuth, you'll be redirected back to http://localhost:3000/auth/callback
6. Token stored in localStorage
7. Redirected to http://localhost:3000/marketplace

### Test Environment Detection

```bash
# Backend detects "development" environment
curl http://localhost:8000/config | jq
{
  "environment": "development",
  "cors_origins": ["http://localhost:3000", "http://localhost:3001", "http://localhost:8000"],
  "database": {
    "host": "localhost",
    "name": "waooaw",
    "schema": "demo"
  }
}
```

### Test PlatformPortal

1. Open http://localhost:8000/ (or whatever port Reflex uses)
2. Click **"Sign in with Google"**
3. OAuth flow same as WaooawPortal
4. View dashboard with metrics

---

## 7. Environment Variables Explained

### Backend (.env)

| Variable | Example | Description |
|----------|---------|-------------|
| `ENV` | `development` | Environment name (auto-detected in production) |
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_NAME` | `waooaw` | Database name |
| `DB_USER` | `postgres` | Database user |
| `DB_PASSWORD` | `postgres` | Database password |
| `DB_SCHEMA` | `demo` | Schema to use (demo/uat/public) |
| `GOOGLE_CLIENT_ID` | `123...apps.googleusercontent.com` | From Google Console |
| `GOOGLE_CLIENT_SECRET` | `GOCSPX-...` | From Google Console |
| `JWT_SECRET` | `random-secret-here` | Secret for JWT signing (min 32 chars) |

### Frontend (No .env needed)

Environment detection is **automatic** based on hostname:
- `localhost` → development (API: http://localhost:8000)
- `demo-www.waooaw.com` → demo (API: https://demo-api.waooaw.com)
- `uat-www.waooaw.com` → uat (API: https://uat-api.waooaw.com)
- `www.waooaw.com` → production (API: https://api.waooaw.com)

---

## 8. Development Workflow

### Making Changes

**Backend**:
1. Edit files in `backend-v2/app/`
2. uvicorn auto-reloads on file changes
3. Check logs in terminal
4. Test with `curl` or browser

**WaooawPortal**:
1. Edit files in `WaooawPortal-v2/src/`
2. Vite hot-reloads automatically
3. Check browser console for errors
4. Refresh browser if needed

**PlatformPortal**:
1. Edit files in `PlatformPortal-v2/PlatformPortal_v2/`
2. Reflex recompiles on save
3. Browser auto-refreshes
4. Check terminal for compile errors

### Testing OAuth Locally

**Important**: Google OAuth redirect URIs must exactly match:
- ✅ `http://localhost:8000/auth/callback` (backend)
- ❌ `http://127.0.0.1:8000/auth/callback` (won't work, different host)

Always use **localhost**, not 127.0.0.1.

### Database Migrations

```bash
# Connect to database
psql waooaw

# Switch to demo schema
SET search_path TO demo;

# Create tables (example)
CREATE TABLE agents (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  industry VARCHAR(50),
  specialty VARCHAR(255),
  rating DECIMAL(2,1),
  price VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);

# Insert seed data
INSERT INTO agents (name, industry, specialty, rating, price) VALUES
  ('Content Marketing Agent', 'marketing', 'Healthcare', 4.9, '₹12,000/month'),
  ('Math Tutor Agent', 'education', 'JEE/NEET', 4.8, '₹8,000/month'),
  ('SDR Agent', 'sales', 'B2B SaaS', 5.0, '₹15,000/month');
```

---

## 9. Troubleshooting

### Port Already in Use

**Backend (port 8000)**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn app.main:app --reload --port 8001
```

**Frontend (port 3000)**:
```bash
# Vite will automatically try next available port
# Or specify in vite.config.js:
{
  server: {
    port: 3001
  }
}
```

### Database Connection Failed

```bash
# Check PostgreSQL is running
docker ps  # If using Docker
brew services list  # If using Homebrew

# Test connection
psql -h localhost -U postgres -d waooaw

# Check .env file has correct credentials
cat backend-v2/.env
```

### OAuth Redirect URI Mismatch

**Error**: `redirect_uri_mismatch`

**Solution**:
1. Check Google Cloud Console redirect URIs
2. Must have: `http://localhost:8000/auth/callback`
3. Use `localhost`, not `127.0.0.1`
4. No trailing slash

### CORS Errors

**Error**: `Access-Control-Allow-Origin` error in browser console

**Solution**:
- Backend automatically allows `http://localhost:3000` in development
- Check `backend-v2/app/config.py` → `CORS_ORIGINS` property
- Add your frontend URL if using different port

### Module Not Found

**Backend**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Frontend**:
```bash
# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

---

## 10. VS Code Setup (Optional)

### Recommended Extensions

- **Python**: ms-python.python
- **Pylance**: ms-python.vscode-pylance
- **ESLint**: dbaeumer.vscode-eslint
- **Prettier**: esbenp.prettier-vscode
- **Tailwind CSS IntelliSense**: bradlc.vscode-tailwindcss

### Launch Configuration (.vscode/launch.json)

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Backend: uvicorn",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "cwd": "${workspaceFolder}/backend-v2",
      "env": {
        "ENV": "development"
      }
    },
    {
      "name": "Frontend: npm dev",
      "type": "node",
      "request": "launch",
      "cwd": "${workspaceFolder}/WaooawPortal-v2",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "dev"]
    }
  ]
}
```

---

## 11. Testing Checklist

- [ ] Backend health check returns 200
- [ ] Backend /config shows correct environment
- [ ] WaooawPortal home page loads
- [ ] WaooawPortal marketplace page loads
- [ ] WaooawPortal "Sign In" redirects to Google
- [ ] OAuth callback stores token
- [ ] PlatformPortal dashboard loads
- [ ] PlatformPortal shows environment badge
- [ ] Database connection works
- [ ] No CORS errors in browser console

---

## 12. Next Steps

After local development works:

1. **Push to GitHub**:
   ```bash
   git checkout -b feature/v2-demo
   git add .
   git commit -m "feat: v2 architecture implementation"
   git push origin feature/v2-demo
   ```

2. **GitHub Actions will auto-deploy to demo**:
   - Watch workflow: GitHub → Actions tab
   - Services deployed to demo-*.waooaw.com

3. **Test demo environment**:
   - https://demo-www.waooaw.com/
   - https://demo-pp.waooaw.com/
   - https://demo-api.waooaw.com/health

---

## 📚 Documentation

- **Backend**: [backend-v2/README.md](backend-v2/README.md)
- **WaooawPortal**: [WaooawPortal-v2/README.md](WaooawPortal-v2/README.md)
- **PlatformPortal**: [PlatformPortal-v2/README.md](PlatformPortal-v2/README.md)
- **Full Implementation**: [V2_IMPLEMENTATION_SUMMARY.md](V2_IMPLEMENTATION_SUMMARY.md)

---

**Happy Coding! 🚀**  
**WAOOAW - "Agents Earn Your Business"**
