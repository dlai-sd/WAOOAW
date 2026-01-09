# Plant Phase

**Purpose**: Agent manufacturing pipeline - Genesis certification to production deployment.

## Directory Structure

```
Plant/
├── FrontEnd/     # Genesis/Governor UI
├── BackEnd/      # Agent creation & certification services
├── Test/         # Unit & integration tests
├── Sandbox/      # Agent simulation environment
└── Docs/         # Plant-specific documentation
```

## Key Features

- **Genesis Console**: Certify jobs, skills, agents
- **Agent Creation Pipeline**: 7-stage Temporal workflow
- **Agent Simulation**: Test agents before production
- **Constitutional Audit**: L0/L1 compliance validation
- **ML Model Integration**: Integrate 8 ML models into agents

## Lifecycle Stages

1. **Conceive**: Define agent specification
2. **Birth**: Genesis certification
3. **Assembly**: Compose skills into job role
4. **Wiring**: Connect to team, industry
5. **Power On**: Boot sequence validation
6. **Showroom**: Demo mode (trial)
7. **Hired**: Production deployment

## Tech Stack

- **Frontend**: HTML5, CSS3, Modern JavaScript
- **Backend**: Python 3.11, FastAPI, Temporal
- **Database**: PostgreSQL, Redis
- **Infrastructure**: Docker, GCP Cloud Run

## Getting Started

1. **Frontend**: See `FrontEnd/README.md`
2. **Backend**: See `BackEnd/README.md`
3. **Local Dev**: See `Sandbox/README.md`

## Related Documentation

- `/docs/plant/` - High-level Plant documentation
- `Docs/` - Plant-specific implementation docs
- `/main/Foundation/` - Constitutional framework
