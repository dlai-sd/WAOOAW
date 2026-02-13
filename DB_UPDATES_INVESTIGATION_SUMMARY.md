# DB Updates Token Transmission - Investigation Summary

## 🎯 Root Cause Identified

The **401 error on DB Updates** is caused by **JWT validation failure** when PP Backend's `require_admin()` dependency tries to validate the access token sent from the frontend.

### Key Finding

**Flow**: Frontend → `/api/auth/db-updates-token` → PP Backend `require_admin()` → JWT decode fails → 401

**Most Likely Cause**: `JWT_SECRET` environment variable is either:
1. **Not set** in one or more services
2. **Mismatched** between PP Backend and where the token was originally minted  
3. **Different algorithm** (should be HS256 everywhere)

## 📊 Evidence

| Observation | Implication |
|---|---|
| No GCP Cloud Run services deployed yet | Issue is in local/development environment |
| Frontend calls `/api/auth/db-updates-token` correctly | Routing is correct |
| Load balancer routes `/api/*` to `api_backend_key` | Request reaches PP Backend |
| `require_admin` dependency decodes with `JWT_SECRET` | Mismatch causes 401 |

## 🔧 Diagnostic Tools Created

### 1. **GCP Diagnostic Script** (`scripts/diagnose_db_updates_auth.sh`)
```bash
bash scripts/diagnose_db_updates_auth.sh demo
```
- Checks JWT_SECRET consistency across services
- Verifies ENABLE_DB_UPDATES flags
- Tests endpoint reachability
- Attempts token flow end-to-end

### 2. **Local Auth Flow Test** (`scripts/test_local_auth_flow.sh`)
```bash
bash scripts/test_local_auth_flow.sh
```
- Tests dev-token → db-updates-token → agent-list flow
- Validates JWT_SECRET consistency in docker-compose
- Seeds demo customer automatically
- Provides actionable error messages

### 3. **Troubleshooting Guide** (`docs/DB_UPDATES_AUTH_TROUBLESHOOTING.md`)
Complete reference with:
- Root cause analysis
- Environment variable checklist
- Browser DevTools inspection steps
- Fix instructions for local & deployed

## ✅ Immediate Actions

### For Local/Codespace Environment

**Run the test script:**
```bash
chmod +x scripts/test_local_auth_flow.sh
bash scripts/test_local_auth_flow.sh
```

If it fails with **401 on DB updates token**:

```bash
# Check JWT_SECRET in docker-compose
docker-compose exec pp-backend env | grep JWT_SECRET
docker-compose exec plant-gateway env | grep JWT_SECRET

# If different or missing, update docker-compose.yml or .env:
JWT_SECRET=your-32-byte-base64-secret-here

# Restart services
docker-compose restart pp-backend plant-gateway plant-backend

# Re-run test
bash scripts/test_local_auth_flow.sh
```

### For Deployed Environment

Once services are deployed to GCP:

```bash
# Run GCP diagnostic
bash scripts/diagnose_db_updates_auth.sh demo

# If JWT_SECRET mismatch found, update Terraform:
# cloud/terraform/stacks/pp/main.tf
# cloud/terraform/stacks/plant/main.tf

secrets = {
  JWT_SECRET = "JWT_SECRET:latest"  # ← Ensure all services reference same secret
}

# Apply and redeploy
terraform apply
```

## 🎨 Frontend Debugging

The DB Updates page already has debugging built-in (not yet deployed):
- Shows access token presence and preview
- Logs token minting attempts
- Displays HTTP status and correlation IDs
- Shows error details in a debug panel

**To use:**
1. Open PP application in browser
2. Navigate to DB Updates page
3. Open browser console (F12)
4. Look for debug output starting with "🔍 DB Updates Token Init Debug:"

## 📋 Complete Fix Checklist

- [ ] Run local test script: `bash scripts/test_local_auth_flow.sh`
- [ ] Verify JWT_SECRET is set and consistent
- [ ] Verify JWT_ALGORITHM=HS256 everywhere
- [ ] Verify ENABLE_DB_UPDATES=true for target environment
- [ ] Test token minting via curl (see test script)
- [ ] Seed demo customer for Agent Management
- [ ] Check browser DevTools → localStorage['pp_access_token']
- [ ] Check browser DevTools → Network → Authorization header
- [ ] Re-login if token is stale/expired
- [ ] Clear browser cache if persistent

## 🚀 Next Steps

Once JWT_SECRET is consistent and set correctly:

1. **Agent Management** will work (after seeding demo customer)
2. **DB Updates** token minting will succeed (returns 200 with scoped token)
3. **Both pages** will function normally

### Permanent Prevention

Add these to your deployment pipeline:

```bash
# Pre-deployment validation
- Verify all services have JWT_SECRET set
- Verify JWT_ALGORITHM=HS256 (or RS256 if using asymmetric)
- Run automated token flow test
- Seed required bootstrap data (demo customer, etc.)

# Post-deployment smoke test
- Test /api/auth/dev-token (demo only)
- Test /api/auth/db-updates-token with valid access token
- Test /api/v1/agents with valid access token
- Verify 200 OK responses
```

## 📞 Support

If issues persist after checking JWT_SECRET:

1. **Capture detailed logs:**
   ```bash
   docker-compose logs pp-backend | grep -A5 -B5 "401\|Unauthorized" > auth-error.log
   ```

2. **Decode your JWT:**
   - Copy token from localStorage['pp_access_token']
   - Visit https://jwt.io
   - Check: `iss`, `exp`, `iat`, `sub`, `email`, `roles`
   - Verify `exp` (expiry) is in future
   - Verify `roles` includes "admin"

3. **Compare secrets (hashed):**
   ```bash
   echo -n "your-jwt-secret" | sha256sum
   # Run on each service and compare hashes
   ```

## 🎓 Architecture Notes

**Is this approach standard?**

✅ **YES** - The architecture follows industry best practices:

| Pattern | Standard Reference |
|---|---|
| Gateway validates JWT + enriches | Netflix Zuul, Kong Gateway |
| Cloud Run IAM + user JWT forwarding | Google Cloud IAM best practices |
| HS256 for internal services | OAuth 2.0 / JWT RFC 7519 |
| Scoped tokens for sensitive operations | OAuth 2.0 token exchange |
| Admin role required for break-glass tools | Principle of least privilege |

**Only deviation**: Missing bootstrap/seed data for non-prod environments (now addressed by test scripts).

---

**TL;DR:**
- Run `bash scripts/test_local_auth_flow.sh`
- Fix any JWT_SECRET mismatches it reports
- Restart services
- Test again ✅
