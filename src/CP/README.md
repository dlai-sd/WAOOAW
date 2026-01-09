# Customer Portal (CP)

**Purpose**: Customer-facing marketplace for browsing, selecting, and managing AI agents.

## 🚀 Quick Start

### Start Application (Single Command)
```bash
./start.sh
```

### Stop Application
```bash
./stop.sh
```

### Access URLs
- **Application**: https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev
- **API Docs**: https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev/docs
- **Health Check**: https://shiny-space-guide-pj4gwgp94gw93557-8000.app.github.dev/health

**Note**: Both frontend and backend run on port 8000 for simplicity.

---

## Directory Structure

```
CP/
├── FrontEnd/     # React/TypeScript UI for customers
├── BackEnd/      # FastAPI services for CP
├── Test/         # Unit & integration tests
├── Sandbox/      # Local dev/testing environment
├── Docs/         # CP-specific documentation
├── start.sh      # Start script (builds & runs everything)
└── stop.sh       # Stop script (clean shutdown)
```

## Key Features

- **Agent Marketplace**: Browse 19+ agents across 3 industries
- **Search & Filters**: By skill, industry, specialty, rating, price
- **Agent Cards**: Avatar, status, rating, specialty, activity
- **Live Activity Feed**: Real-time updates
- **Personalized Demos**: See agents work on YOUR business
- **7-Day Trials**: Keep deliverables regardless of decision

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

- `/docs/CP/` - High-level CP documentation
- `Docs/` - CP-specific implementation docs
- `/main/Foundation/` - Constitutional framework
