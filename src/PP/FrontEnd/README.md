# PP Frontend

Platform admin UI for WAOOAW operations.

## Tech Stack

- React 18 + TypeScript
- Vite (build tool)
- Fluent UI v9 (Microsoft design system)
- Google OAuth via `@react-oauth/google`
- Vitest (testing)

## Quick Start

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env
# Edit .env and add VITE_GOOGLE_CLIENT_ID

# Start dev server (port 8080)
npm run dev

# Build for production
npm run build

# Run tests
npm test
```

## Key Pages

1. **Dashboard**: Overview metrics (MRR, agents, customers)
2. **Agent Management**: List, create, certify, deploy agents
3. **Customer Management**: View customers, subscriptions
4. **Billing**: Revenue, churn, invoices
5. **Governor Console**: Approval queue, decisions
6. **Genesis Console**: Job/skill certification

## Project Structure

```
src/
├── config/         # OAuth/API configuration
├── context/        # React contexts (Auth)
├── styles/         # Global CSS
├── App.tsx         # Main app shell
├── main.tsx        # Entry point
└── theme.ts        # Fluent UI theme (WAOOAW brand colors)
```

## Development Notes

- Default API base: `http://localhost:8015/api`
- Backend must be running on port 8015
- OAuth client ID required for Google login
- Dark theme by default (matches WAOOAW brand)

## Backend Integration

The frontend expects the PP backend API on port 8015. See `src/PP/BackEnd/README.md` for backend setup.
