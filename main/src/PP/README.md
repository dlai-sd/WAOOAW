# Platform Portal (PP)

**Purpose**: Platform admin portal for managing agents, customers, and operations.

## Directory Structure

```
PP/
├── FrontEnd/     # React/HTML/CSS UI for platform admin
├── BackEnd/      # FastAPI services for PP
├── Test/         # Unit & integration tests
├── Sandbox/      # Local dev/testing environment
└── Docs/         # PP-specific documentation
```

## Key Features

- **Agent Management**: Create, certify, deploy agents
- **Customer Management**: View customers, subscriptions, usage
- **Billing Dashboard**: MRR, ARR, churn, revenue metrics
- **Observability**: Logs, metrics, traces for all agents
- **Governor Console**: Approve/reject agent actions
- **Genesis Console**: Certify jobs, skills, agents

## Tech Stack

- **Frontend**: HTML5, CSS3, Modern JavaScript (or React)
- **Backend**: Python 3.11, FastAPI
- **Database**: PostgreSQL, Redis
- **Infrastructure**: Docker, GCP Cloud Run

## Getting Started

1. **Frontend**: See `FrontEnd/README.md`
2. **Backend**: See `BackEnd/README.md`
3. **Local Dev**: See `Sandbox/README.md`

## Related Documentation

- `/docs/PP/` - High-level PP documentation
- `Docs/` - PP-specific implementation docs
- `/main/Foundation/` - Constitutional framework
