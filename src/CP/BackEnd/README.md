# CP Backend

FastAPI services for Customer Portal.

## Tech Stack

- Python 3.11
- FastAPI
- PostgreSQL (customer data, subscriptions)
- Redis (cache, sessions)
- Pydantic (data validation)

## Directory Structure (To Be Created)

```
BackEnd/
├── main.py                 # FastAPI app entry
├── requirements.txt        # Python dependencies
├── api/
│   ├── __init__.py
│   ├── agents.py           # GET /agents, GET /agents/{id}
│   ├── trials.py           # POST /trials
│   ├── subscriptions.py    # GET /subscriptions, POST /subscriptions
│   └── customers.py        # GET /me, PATCH /me
├── models/
│   ├── __init__.py
│   ├── agent.py            # Agent Pydantic model
│   ├── trial.py            # Trial Pydantic model
│   └── subscription.py     # Subscription Pydantic model
├── services/
│   ├── __init__.py
│   ├── agent_service.py    # Business logic for agents
│   ├── trial_service.py    # Trial signup logic
│   └── subscription_service.py
├── repositories/
│   ├── __init__.py
│   ├── agent_repository.py # Database queries
│   └── customer_repository.py
└── config.py               # Environment config
```

## API Endpoints

### Agents
- `GET /agents` - List all agents (with filters)
- `GET /agents/{id}` - Get agent details
- `POST /agents/{id}/demo` - Request personalized demo

### Trials
- `POST /trials` - Start 7-day trial
- `GET /trials/{id}` - Get trial status

### Subscriptions
- `GET /subscriptions` - List customer subscriptions
- `POST /subscriptions` - Convert trial to subscription

### Customers
- `GET /me` - Get customer profile
- `PATCH /me` - Update profile

## Getting Started

```bash
# Run (Docker-first)
docker build -t waooaw-cp-backend -f Dockerfile .
docker run --rm -p 8000:8000 waooaw-cp-backend

# Run tests (Docker)
docker run --rm -v "$PWD":/app -w /app python:3.11-slim \
	python -m pip install -q -r requirements.txt && \
	python -m pytest
```

## Environment Variables

```env
DATABASE_URL=postgresql://user:pass@localhost/waooaw
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-secret-key
STRIPE_API_KEY=sk_test_...
```
