# JWT_SECRET Synchronization Fix - Root Cause and Solution

## Issue Summary
After merging PR #652, all PP (Platform Portal) screens started failing with "401: Invalid token" errors in production. The root cause was JWT token validation failure between microservices due to JWT_SECRET mismatch.

## Root Cause Analysis

### What Changed
PR #652 changed `GW_ALLOW_PLANT_CUSTOMER_ENRICHMENT` default from `false` to `true` in Plant Gateway middleware (`src/Plant/Gateway/middleware/auth.py`).

### Authentication Flow
```
PP Frontend → PP Backend → Plant Gateway → Plant Backend
     |            |               |              |
     |            |               |              |
Request → Issues JWT → Validates JWT → Verifies JWT with SECRET
```

### The Problem
1. **PP Backend** issues JWT tokens signed with its own `JWT_SECRET`
2. **Plant Gateway** (with `GW_ALLOW_PLANT_CUSTOMER_ENRICHMENT=true`) calls Plant Backend's `/api/v1/auth/validate` for every request
3. **Plant Backend** tries to verify the JWT using its own `JWT_SECRET`
4. If secrets don't match → JWT verification fails → 401 Unauthorized

### Why It Worked Locally But Failed in Production
- **Local Development** (`docker-compose.local.yml`): All services inherit same `JWT_SECRET` from environment variable
- **Production** (`cloud/infrastructure.yaml`): Only `backend` service had `JWT_SECRET` configured; `platform_portal` service was missing it entirely

## Permanent Solution

### Changes Made

#### 1. Cloud Infrastructure Configuration (`cloud/infrastructure.yaml`)
**Added JWT_SECRET to platform_portal service:**
```yaml
platform_portal:
  secrets:
    - name: JWT_SECRET
      secret_name: JWT_SECRET
      version: latest
    - name: GOOGLE_CLIENT_ID
      secret_name: GOOGLE_CLIENT_ID
      version: latest
```

#### 2. Docker Compose Configuration (`docker-compose.local.yml`)
**Standardized JWT_SECRET usage for Plant Backend:**
```yaml
plant-backend:
  environment:
    - JWT_SECRET=${JWT_SECRET:-dev-secret-change-in-production}
    - SECRET_KEY=${JWT_SECRET:-dev-secret-change-in-production}  # Alias for compatibility
```

#### 3. Environment Variables Documentation (`.env.example`)
**Added comprehensive JWT_SECRET documentation:**
```bash
# JWT Authentication (CRITICAL: Must be the same across ALL services)
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
# This secret is used by CP, PP, Plant Backend, and Plant Gateway
# ALL services must use the EXACT SAME value for token validation to work
JWT_SECRET=dev-secret-change-in-production-REPLACE-ME
JWT_ALGORITHM=HS256
JWT_ISSUER=waooaw.com
ACCESS_TOKEN_EXPIRE_MINUTES=15
```

## Deployment Instructions

### Google Cloud Secret Manager Update
Ensure the `JWT_SECRET` is stored in Google Cloud Secret Manager before deploying:

```bash
# Check if JWT_SECRET exists
gcloud secrets describe JWT_SECRET --project=YOUR_PROJECT_ID

# Create if doesn't exist
echo -n "YOUR_STRONG_SECRET_HERE" | gcloud secrets create JWT_SECRET \
  --data-file=- \
  --replication-policy="automatic" \
  --project=YOUR_PROJECT_ID

# Or update existing
echo -n "YOUR_STRONG_SECRET_HERE" | gcloud secrets versions add JWT_SECRET \
  --data-file=- \
  --project=YOUR_PROJECT_ID
```

### Deployment Steps
1. Merge this PR to `main`
2. Verify JWT_SECRET exists in Secret Manager (see above)
3. Deploy all services (backend and platform_portal must use same JWT_SECRET)
4. Test authentication flow through PP application

## Testing Checklist

### Local Testing (Docker Compose)
- [ ] Set JWT_SECRET in `.env` file
- [ ] Run `docker-compose -f docker-compose.local.yml up --build`
- [ ] Access PP Frontend at http://localhost:8080
- [ ] Login with Google OAuth
- [ ] Verify DB Updates menu works
- [ ] Verify all CRUD operations succeed (no 401 errors)
- [ ] Check Plant Gateway logs for successful token validation

### Production Testing (Post-Deployment)
- [ ] Login to PP application
- [ ] Navigate through all menus (DB Updates, Skill Management, etc.)
- [ ] Perform CRUD operations on each entity
- [ ] Verify no 401 authentication errors
- [ ] Check Cloud Run logs for both backend and platform_portal services
- [ ] Verify token validation succeeds in Plant Gateway logs

## Services Affected
All services must share the same JWT_SECRET:
1. **CP Backend** (`src/CP/BackEnd`) - Issues tokens for CP API
2. **PP Backend** (`src/PP/BackEnd`) - Issues tokens for PP Frontend
3. **Plant Backend** (`src/Plant/BackEnd`) - Validates tokens via `/api/v1/auth/validate`
4. **Plant Gateway** (`src/Plant/Gateway`) - Proxies requests and validates tokens

## Configuration Files Modified
- `cloud/infrastructure.yaml` - Added JWT_SECRET to platform_portal service
- `docker-compose.local.yml` - Standardized JWT_SECRET usage for Plant Backend
- `.env.example` - Added JWT_SECRET documentation with generation instructions

## Validation
- **Local**: All services using same JWT_SECRET from environment
- **Production**: All Cloud Run services pulling JWT_SECRET from Secret Manager
- **Compatibility**: Plant Backend accepts both JWT_SECRET and SECRET_KEY (alias)

## Related PRs
- PR #652 - Changed `GW_ALLOW_PLANT_CUSTOMER_ENRICHMENT` default (triggered the issue)
- PR #653 - Phase 2 Production Readiness (where issue was discovered)
- This PR - Permanent fix for JWT_SECRET synchronization

## Files Changed
```
cloud/infrastructure.yaml
docker-compose.local.yml
.env.example
docs/JWT_SECRET_SYNCHRONIZATION_FIX.md (this document)
```

## Prevention
To prevent similar issues in the future:
1. **Always use JWT_SECRET** (not SECRET_KEY) as the primary environment variable name
2. **Document critical shared secrets** in .env.example with clear warnings
3. **Ensure cloud infrastructure mirrors local configuration** for all authentication-related secrets
4. **Test authentication flows end-to-end** before merging PRs that change auth middleware behavior
5. **Add integration tests** that verify token validation across microservices

## Questions?
Contact: DevOps Team / Infrastructure Lead
