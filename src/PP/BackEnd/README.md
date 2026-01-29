# PP Backend

FastAPI services for Platform Portal.

## Tech Stack

- Python 3.11+
- FastAPI + Uvicorn
- Pydantic v2 (settings + validation)
- Google OAuth (authlib, httpx, PyJWT)
- PostgreSQL + Redis (future)
- SQLAlchemy + Alembic (migrations)

## Quick Start

```bash
# Copy environment file
cp .env.example .env
# Edit .env and configure GOOGLE_CLIENT_ID, JWT_SECRET, etc.

# Build and run (Docker-first)
docker build -t waooaw-pp-backend:dev .
docker run --rm -p 8015:8000 \
	-e PORT=8000 \
	--env-file .env \
	waooaw-pp-backend:dev
```

## API Endpoints

### Health & Info
- `GET /` - Service info
- `GET /health` - Kubernetes health probe
- `GET /api` - API info with environment

### Auth (Placeholder)
- `GET /api/auth/me` - Get current user profile (mock)
- `POST /api/auth/logout` - Logout endpoint

### Agent Management (TODO)
- `GET /api/agents` - List all platform agents
- `POST /api/agents` - Create new agent
- `POST /api/agents/{id}/certify` - Genesis certification
- `POST /api/agents/{id}/deploy` - Deploy to production

### Customer Management (TODO)
- `GET /api/customers` - List all customers
- `GET /api/customers/{id}` - Get customer details
- `GET /api/customers/{id}/agents` - Customer's agents

### Billing (TODO)
- `GET /api/billing/mrr` - Monthly Recurring Revenue
- `GET /api/billing/churn` - Churn metrics
- `GET /api/billing/invoices` - Invoice list

## Project Structure

```
src/PP/BackEnd/
├── api/           # Route modules
│   ├── auth.py    # Auth routes (placeholder)
│   └── ...        # agents, customers, billing (TODO)
├── core/          # Core configuration
│   └── config.py  # Settings with pydantic-settings
├── main.py        # FastAPI app entry
└── requirements.txt
```

## Configuration

Environment variables (see `.env.example`):
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` - OAuth credentials
- `JWT_SECRET` - Secret for signing tokens
- `APP_PORT` - Server port (default 8015)
- `ENVIRONMENT` - codespace | demo | uat | prod
- `CORS_ORIGINS` - Comma-separated allowed origins

## Development Notes

- Port 8015 by default (differs from CP backend on 8000)
- Auth routes are placeholders; wire real OAuth flow next
- CORS allows `*` by default; restrict in production
- Settings loaded from env vars via pydantic-settings

## Testing

```bash
# Run tests in Docker (no local Python environment required)
docker build -t waooaw-pp-backend:test .
docker run --rm --entrypoint pytest waooaw-pp-backend:test -v
```
