# DB Updates Token Transmission - Root Cause Analysis & Fix

## Issue Summary

**Error 1: Agent Management** → `500: Customer not found`  
**Error 2: DB Updates** → `401: [object Object]`

## Root Cause: DB Updates 401 Error

### Investigation Results

The 401 error when accessing DB Updates is caused by **token validation failure** at the PP Backend's `/api/auth/db-updates-token` endpoint.

### Flow Analysis

```
1. User logs in → PP stores JWT in localStorage['pp_access_token']
2. DB Updates page loads → calls gatewayApiClient.mintDbUpdatesToken()
3. Frontend sends: POST https://pp.demo.waooaw.com/api/auth/db-updates-token
   Headers: {
     Authorization: Bearer <access_token_from_localStorage>
   }
4. PP Backend receives request → require_admin() dependency validates JWT
5. Validation fails → 401 Unauthorized
```

### Likely Causes (Priority Order)

| Cause | Probability | How to Verify |
|---|---|---|
| **JWT_SECRET not set/mismatch** | 🔴 HIGH | Check env vars in deployed services |
| **Token expired** | 🟡 MEDIUM | Check JWT exp claim vs current time |
| **Token not in localStorage** | 🟡 MEDIUM | Check browser DevTools → Application → Local Storage |
| **Wrong JWT_ALGORITHM** | 🟢 LOW |Should be HS256 consistently |
| **ENABLE_DB_UPDATES=false** | 🟢 LOW | Returns 404, not 401 |

## Diagnostic Commands

### For Local/Codespace Environment

```bash
# 1. Check if services are running
docker ps | grep -E "(pp-backend|plant-gateway)"

# 2. Check environment variables
docker exec <pp-backend-container> env | grep -E "(JWT_SECRET|ENABLE_DB_UPDATES|JWT_ALGORITHM)"

# 3. Test token flow manually
# Login to PP frontend, get token from localStorage
curl -X POST http://localhost:8015/api/auth/dev-token \
  -H 'Content-Type: application/json'

# Use returned token to mint DB updates token
curl -X POST http://localhost:8015/api/auth/db-updates-token \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H 'Content-Type: application/json'
```

### For Deployed Environment (GCP Cloud Run)

```bash
# Run diagnostic script
bash scripts/diagnose_db_updates_auth.sh demo

# Manual service check
gcloud run services describe waooaw-pp-backend-demo \
  --region us-central1 \
  --format="yaml(spec.template.spec.containers[0].env)"
```

### Browser DevTools Check

1. Open PP application in browser
2. Login with Google OAuth
3. **F12** → **Application** tab → **Local Storage**
4. Check for key: `pp_access_token`
5. **Network** tab → Filter: `db-updates-token`
6. Check request headers: `Authorization: Bearer ...`
7. Check response: status code & body

## Fix Instructions

### Fix #1: Set JWT_SECRET Consistently

**Terraform (for deployed environments):**

```bash
# Ensure JWT_SECRET is in Secret Manager
gcloud secrets create JWT_SECRET --data-file=<(openssl rand -base64 32)

# Verify all services reference it
# cloud/terraform/stacks/pp/main.tf
# cloud/terraform/stacks/plant/main.tf

secrets = {
  JWT_SECRET = "JWT_SECRET:latest"
  ...
}

# Redeploy
terraform apply
```

**Docker Compose (for local):**

```yaml
# docker-compose.local.yml or .env
PP_BACKEND:
  environment:
    - JWT_SECRET=<SAME_SECRET_HERE>

PLANT_GATEWAY:
  environment:
    - JWT_SECRET=<SAME_SECRET_HERE>

PLANT_BACKEND:
  environment:
    - JWT_SECRET=<SAME_SECRET_HERE>
```

### Fix #2: Verify Token Persistence

**Add debugging to frontend (already included in DbUpdates.tsx):**

The debug output will show:
- Whether access token exists in localStorage
- Token length and preview
- Minting attempt result
- HTTP status and error details

### Fix #3: Customer Bootstrap (Agent Management)

The "Customer not found" error requires seeding a demo customer. Add to Plant Backend startup:

```python
# src/Plant/BackEnd/main.py

@app.on_event("startup")
async def startup_event():
    # ... existing code ...
    
    # Seed demo customer for non-prod environments
    if settings.environment in {"demo", "development", "local"}:
        try:
            from models.customer import Customer
            from services.customer_service import CustomerService
            from core.database import get_db_session
            
            async for session in get_db_session():
                service = CustomerService(session)
                existing = await service.get_by_email("demo@waooaw.com")
                if not existing:
                    from schemas.customer import CustomerCreate
                    demo = CustomerCreate(
                        fullName="Demo User",
                        businessName="WAOOAW Demo Co",
                        businessIndustry="software",
                        businessAddress="Demo Street 1",
                        email="demo@waooaw.com",
                        phone="+15555555555",
                        preferredContactMethod="email",
                        consent=True
                    )
                    await service.upsert_by_email(demo)
                    logging.info("   ✅ Seeded demo customer")
                break
        except Exception as e:
            logging.warning(f"   ⚠️  Demo customer seed failed: {e}")
```

## Verification Steps

After applying fixes:

### 1. Verify JWT_SECRET Consistency

```bash
# Local
docker-compose exec pp-backend env | grep JWT_SECRET
docker-compose exec plant-gateway env | grep JWT_SECRET
docker-compose exec plant-backend env | grep JWT_SECRET

# All should output the same value
```

### 2. Test Token Minting

```bash
# Get access token
TOKEN=$(curl -sS -X POST http://localhost:8015/api/auth/dev-token | jq -r '.access_token')

# Mint DB updates token
curl -X POST http://localhost:8015/api/auth/db-updates-token \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -v

# Expected: 200 OK with { "access_token": "...", "scope": "db_updates" }
```

### 3. Test Agent Management

```bash
# With same token from above
curl -X GET "http://localhost:8000/api/v1/agents?limit=10" \
  -H "Authorization: Bearer $TOKEN" \
  -v

# Expected: 200 OK with agent list (not 500 "Customer not found")
```

## Environment Variable Checklist

| Service | Var | Expected Value | Purpose |
|---|---|---|---|
| PP Backend | `JWT_SECRET` | `<32-byte-base64>` | Sign/verify JWTs |
| PP Backend | `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| PP Backend | `ENABLE_DB_UPDATES` | `true` (demo/prod) | Enable DB tooling |
| Plant Gateway | `JWT_SECRET` | `<SAME>` | Verify user JWTs |
| Plant Backend | `JWT_SECRET` | `<SAME>` | Verify enriched JWTs |
| Plant Backend | `ENABLE_DB_UPDATES` | `true` (optional) | Plant-side DB endpoints |

## Summary

**DB Updates 401** → JWT validation fails  
**Agent Management 500** → No demo customer in DB  

**Quick Fix Order:**
1. Verify/set `JWT_SECRET` consistently across all services
2. Restart services
3. Test token flow via curl
4. Check browser DevTools for `pp_access_token`
5. Apply customer bootstrap for Agent Management

**Permanent Fix:**
- Add JWT_SECRET to terraform secrets
- Add demo customer seed to startup
- Add health check that validates auth flow
- Add frontend debug logging (already done)
