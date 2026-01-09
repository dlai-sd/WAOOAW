# Plant Backend

FastAPI services for agent manufacturing pipeline.

## API Endpoints

### Genesis Certification
- `POST /jobs` - Create job role
- `POST /jobs/{id}/certify` - Certify job role
- `POST /skills` - Create skill
- `POST /skills/{id}/certify` - Certify skill

### Agent Creation
- `POST /agents` - Create agent specification
- `POST /agents/{id}/pipeline` - Start 7-stage pipeline
- `GET /agents/{id}/status` - Get pipeline status

### Simulation
- `POST /agents/{id}/simulate` - Simulate agent execution
- `GET /simulations/{id}` - Get simulation results

### Constitutional Audit
- `POST /agents/{id}/audit` - Run constitutional compliance audit
- `GET /audits/{id}` - Get audit results

## Getting Started

See `/main/src/CP/BackEnd/README.md` for similar structure.
