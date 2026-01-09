# PP Backend

FastAPI services for Platform Portal.

## API Endpoints

### Agent Management
- `GET /agents` - List all platform agents
- `POST /agents` - Create new agent
- `POST /agents/{id}/certify` - Genesis certification
- `POST /agents/{id}/deploy` - Deploy to production

### Customer Management
- `GET /customers` - List all customers
- `GET /customers/{id}` - Get customer details
- `GET /customers/{id}/agents` - Customer's agents

### Billing
- `GET /billing/mrr` - Monthly Recurring Revenue
- `GET /billing/churn` - Churn metrics
- `GET /billing/invoices` - Invoice list

## Getting Started

See `/main/src/CP/BackEnd/README.md` for similar structure.
