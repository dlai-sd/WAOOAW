# CP Sandbox

Local development and testing environment for Customer Portal.

## Quick Start

```bash
# Start local environment
docker-compose up -d

# Check services
docker-compose ps

# View logs
docker-compose logs -f

# Stop environment
docker-compose down
```

## Services

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Adminer** (DB UI): http://localhost:8081

## Files (To Be Created)

```
Sandbox/
├── docker-compose.yml      # Local services
├── .env.example            # Environment variables template
├── seed_data.sql           # Test data
└── README.md               # This file
```

## Test Data

Seed data includes:
- 3 sample agents (Healthcare, Education, Sales)
- 2 test customers
- 1 active trial
- 1 active subscription

## Environment Variables

Copy `.env.example` to `.env` and update values:

```env
DATABASE_URL=postgresql://waooaw:password@postgres:5432/waooaw_cp
REDIS_URL=redis://redis:6379
JWT_SECRET=dev-secret-key
STRIPE_API_KEY=sk_test_...
```
