# WAOOAW Troubleshooting Guide

**Document Version**: 1.0  
**Last Updated**: 2026-02-12  
**Owner**: Operations Team  
**Purpose**: Comprehensive guide for diagnosing and resolving common WAOOAW platform issues

---

## Overview

This document provides diagnosis steps and resolution procedures for the Top 20 most common issues reported by customers and detected by monitoring systems. Each scenario includes symptoms, root causes, step-by-step resolution, and prevention strategies.

**Target Audience**: Operations team, customer support, on-call engineers  
**Severity Levels**: P0 (Critical), P1 (High), P2 (Medium), P3 (Low)

---

## Table of Contents

### Platform Issues
1. [Agent Not Executing Goals](#1-agent-not-executing-goals)
2. [Deliverables Not Appearing](#2-deliverables-not-appearing)
3. [Scheduler Health Check Failing](#3-scheduler-health-check-failing)
4. [Database Connection Pool Exhausted](#4-database-connection-pool-exhausted)

### Authentication & Credentials
5. [OAuth Token Expired](#5-oauth-token-expired)
6. [Platform Credential Invalid](#6-platform-credential-invalid)
7. [Customer Login Failed](#7-customer-login-failed)
8. [API Rate Limit Exceeded](#8-api-rate-limit-exceeded)

### Social Platform Issues
9. [Instagram Post Failed](#9-instagram-post-failed)
10. [LinkedIn Authorization Error](#10-linkedin-authorization-error)
11. [YouTube Quota Exceeded](#11-youtube-quota-exceeded)
12. [WhatsApp Message Delivery Failed](#12-whatsapp-message-delivery-failed)

### Trading Issues
13. [Delta Exchange Authentication Failed](#13-delta-exchange-authentication-failed)
14. [Order Placement Rejected](#14-order-placement-rejected)
15. [Risk Limit Violation](#15-risk-limit-violation)
16. [Position Close Failed](#16-position-close-failed)

### Trial & Billing
17. [Trial Limits Exceeded](#17-trial-limits-exceeded)
18. [Payment Processing Failed](#18-payment-processing-failed)
19. [Subscription Not Activated](#19-subscription-not-activated)

### Performance
20. [CP Dashboard Loading Slowly](#20-cp-dashboard-loading-slowly)

---

## Troubleshooting Scenarios

---

## 1. Agent Not Executing Goals

**Severity**: P1 (High)  
**Frequency**: Common (5-10 tickets/week)

### Symptoms
- Goal status stuck on "Pending" or "Scheduled"
- No deliverables created after expected execution time
- Customer reports "agent not working"
- Goal execution logs show no recent activity

### Root Causes
1. Scheduler service not running
2. Goal not approved by operations
3. Agent credentials expired/invalid
4. Goal schedule misconfigured (timezone issues)
5. Database connection issue preventing scheduler queries

### Diagnosis Steps

**Step 1: Check Goal Status**
```bash
# PP > Goals > Search by customer
# Or via API:
curl -H "Authorization: Bearer $PP_TOKEN" \
  https://api.waooaw.com/pp/goals?customer_id=<customer_id>
```

Expected: `status: "approved"`, `next_run_at` should be populated

**Step 2: Check Scheduler Health**
```bash
# PP > Health > Scheduler Dashboard
# Or check directly:
docker compose -f docker-compose.local.yml exec plant-backend \
  python -m src.Plant.BackEnd.health.scheduler_health
```

Expected output:
```
✓ Scheduler running: Yes
✓ Last heartbeat: <2 minutes ago
✓ Pending goals: X
✓ Running goals: Y
```

**Step 3: Check Goal Run History**
```bash
# PP > Goals > [Goal ID] > Execution History
# Look for:
# - Recent execution attempts
# - Error messages
# - Last successful run
```

**Step 4: Check Agent Credentials**
```bash
# PP > Credentials > [Customer ID]
# Verify status: "active" (not "expired" or "invalid")
```

### Resolution

**If Scheduler Not Running**:
```bash
# Restart scheduler service
docker compose -f docker-compose.local.yml restart plant-scheduler

# Verify restart
docker compose logs -f plant-scheduler | grep "Scheduler started"
```

**If Goal Not Approved**:
```bash
# PP > Goal Approvals > [Goal ID] > Approve
# Or via API:
curl -X POST -H "Authorization: Bearer $PP_TOKEN" \
  https://api.waooaw.com/pp/goals/<goal_id>/approve
```

**If Credentials Expired**:
1. Notify customer via email: "Platform credentials expired, please reconnect"
2. Customer re-authorizes platform in CP > My Agents > Configuration
3. Verify connection successful
4. Manually trigger goal to test

**If Timezone Misconfigured**:
1. Check customer timezone: PP > Customers > [Customer ID]
2. Check goal schedule timezone: PP > Goals > [Goal ID]
3. If mismatch, update goal schedule:
   ```bash
   # Update via PP or API
   PUT /pp/goals/<goal_id>
   { "schedule": "0 10 * * *", "timezone": "Asia/Kolkata" }
   ```

### Prevention
- Automated credential expiry notifications (7 days before expiry)
- Scheduler health monitoring with PagerDuty alerts
- Goal approval SLA: <2 hours during business hours

### Related Documentation
- [Scheduler Architecture](../architecture/scheduler.md)
- [Credential Management](./credential_rotation.md)

---

## 2. Deliverables Not Appearing

**Severity**: P1 (High)  
**Frequency**: Occasional (2-3 tickets/week)

### Symptoms
- Goal executed successfully (logs show completion)
- No deliverable visible in CP > Approvals
- Customer reports "agent ran but I don't see the result"

### Root Causes
1. Deliverable created but not linked to correct customer/agent
2. Database write failed (rollback after creation)
3. CP frontend filtering deliverables incorrectly
4. Deliverable status incorrect (hidden from UI)

### Diagnosis Steps

**Step 1: Verify Goal Execution**
```bash
# Check goal run logs
docker compose logs plant-backend | grep "Goal execution completed" | grep <goal_id>
```

Expected: Log entry with `deliverable_id` created

**Step 2: Query Database Directly**
```sql
-- In PP > Database > Query Tool
SELECT d.id, d.status, d.created_at, d.agent_id, d.customer_id
FROM deliverables d
WHERE d.goal_instance_id = '<goal_id>'
ORDER BY d.created_at DESC
LIMIT 5;
```

**Step 3: Check Customer's Deliverable List**
```bash
# Via API
curl -H "Authorization: Bearer $PP_TOKEN" \
  https://api.waooaw.com/pp/deliverables?customer_id=<customer_id>&limit=10
```

### Resolution

**If Deliverable Exists But Not Visible**:
1. Check `status` field - should be `pending_review` (not `hidden` or `deleted`)
2. Check `customer_id` matches - if wrong, update:
   ```sql
   UPDATE deliverables 
   SET customer_id = '<correct_customer_id>'
   WHERE id = '<deliverable_id>';
   ```

**If Deliverable Missing from Database**:
1. Check goal execution logs for errors
2. Manually recreate deliverable:
   ```bash
   # Trigger goal again
   curl -X POST -H "Authorization: Bearer $PP_TOKEN" \
     https://api.waooaw.com/pp/goals/<goal_id>/trigger
   ```

**If CP UI Filtering Issue**:
1. Ask customer to clear browser cache and reload
2. Check for JavaScript errors in browser console
3. Test with different browser
4. If issue persists, escalate to frontend team

### Prevention
- Add database transaction logging for deliverable creation
- Implement deliverable creation webhook notification
- Add CP UI "Recent Activity" debugging panel for ops

---

## 3. Scheduler Health Check Failing

**Severity**: P0 (Critical)  
**Frequency**: Rare (1-2 incidents/month)

### Symptoms
- Health endpoint returns 503 or timeout
- Goals not executing across all customers
- PagerDuty alert: "Scheduler health check failed"
- Scheduler process not responsive

### Root Causes
1. Scheduler process crashed
2. Database connection pool exhausted
3. Deadlock in scheduler task loop
4. Memory leak causing OOM (out of memory)
5. Redis connection lost (if used for state)

### Diagnosis Steps

**Step 1: Check Scheduler Process**
```bash
# Is scheduler container running?
docker ps | grep plant-scheduler

# Check process inside container
docker exec plant-scheduler ps aux | grep scheduler
```

**Step 2: Check Recent Logs**
```bash
docker compose logs plant-scheduler --tail 100

# Look for:
# - Exception traces
# - "Out of memory" errors
# - Database connection errors
# - Deadlock messages
```

**Step 3: Check Resource Usage**
```bash
# Memory usage
docker stats plant-scheduler --no-stream

# Database connections
docker compose exec postgres \
  psql -U waooaw -c "SELECT count(*) FROM pg_stat_activity;"
```

**Step 4: Check Database Health**
```bash
# Can we connect?
docker compose exec plant-backend \
  python -c "from src.Plant.Core.database import get_db; next(get_db())"
```

### Resolution

**If Process Crashed**:
```bash
# Restart scheduler
docker compose restart plant-scheduler

# Monitor startup
docker compose logs -f plant-scheduler

# Verify health after 30 seconds
curl https://api.waooaw.com/health/scheduler
```

**If Database Connection Issue**:
```bash
# Check connection pool status
docker compose exec plant-backend \
  python -m src.Plant.BackEnd.health.connection_pool_status

# If pool exhausted, restart backend to reset
docker compose restart plant-backend plant-scheduler
```

**If Memory Leak Detected**:
```bash
# Emergency restart
docker compose restart plant-scheduler

# File bug report with memory dump
docker exec plant-scheduler kill -USR1 $(pidof python)
# Dumps memory profile to /tmp/scheduler_memdump.txt

# Escalate to engineering immediately
```

**If Deadlock**:
```bash
# Find deadlocked queries
docker compose exec postgres \
  psql -U waooaw -c "SELECT * FROM pg_locks WHERE NOT granted;"

# Force kill deadlocked connection (extreme measure)
docker compose exec postgres \
  psql -U waooaw -c "SELECT pg_terminate_backend(<pid>);"

# Restart scheduler
docker compose restart plant-scheduler
```

### Prevention
- Implement scheduler watchdog (auto-restart on hang)
- Database connection pool monitoring
- Memory leak detection in CI/CD
- Weekly scheduler log review for early warnings

---

## 4. Database Connection Pool Exhausted

**Severity**: P0 (Critical)  
**Frequency**: Rare (1 incident/quarter)

### Symptoms
- API requests timing out
- "Connection pool exhausted" errors in logs
- Slow response times platform-wide
- Health checks failing

### Root Causes
1. Too many concurrent requests
2. Connection leaks (not released after use)
3. Pool size too small for load
4. Long-running transactions holding connections

### Diagnosis Steps

**Step 1: Check Pool Status**
```bash
# Via monitoring dashboard
# PP > Health > Database > Connection Pool

# Or query directly
docker compose exec plant-backend \
  python -m src.Plant.BackEnd.health.connection_pool_status
```

Expected output:
```
Pool Size: 20/40
Active: 8
Idle: 12
Overflow: 0
```

**Step 2: Check Active Connections**
```sql
SELECT 
  pid, 
  usename, 
  application_name, 
  client_addr,
  state, 
  query_start,
  state_change
FROM pg_stat_activity
WHERE datname = 'waooaw'
ORDER BY query_start;
```

**Step 3: Identify Long-Running Queries**
```sql
SELECT 
  pid, 
  now() - query_start AS duration, 
  query
FROM pg_stat_activity
WHERE state = 'active' 
  AND now() - query_start > interval '30 seconds';
```

### Resolution

**Immediate (Emergency)**:
```bash
# Increase pool size temporarily
docker compose exec plant-backend \
  python -c "from src.Plant.Core.database import engine; \
             engine.pool.dispose(); \
             engine.pool._pool.maxsize = 60"

# Restart services to apply
docker compose restart plant-backend
```

**Kill Long-Running Queries**:
```sql
-- Identify problematic query
SELECT pg_terminate_backend(<pid>);
```

**Find and Fix Connection Leaks**:
```bash
# Check for unclosed database sessions in code
grep -r "get_db()" src/ | grep -v "with.*get_db"

# All database access must use context manager:
# ✓ with get_db() as db:
# ✗ db = get_db()
```

### Prevention
- Set max query timeout: 30 seconds
- Implement connection leak detector in tests
- Monitor pool utilization with alerts at 80%
- Load test before scaling to new user levels

---

## 5. OAuth Token Expired

**Severity**: P2 (Medium)  
**Frequency**: Common (10-15 tickets/week)

### Symptoms
- Platform posting fails with "401 Unauthorized"
- Error message: "Token expired" or "Invalid access token"
- Customer can't post to Instagram/LinkedIn/Facebook

### Root Causes
1. OAuth refresh token not properly renewed
2. Customer revoked access to WAOOAW app
3. Token expiry not detected before use
4. Refresh token endpoint failed

### Diagnosis Steps

**Step 1: Check Credential Status**
```bash
# PP > Credentials > [Customer ID] > [Platform]
# Check fields:
# - status: should be "active"
# - token_expires_at: check if in past
# - last_refreshed_at: should be recent
```

**Step 2: Attempt Manual Token Refresh**
```bash
docker compose exec plant-backend \
  python -m src.Plant.BackEnd.integrations.social.refresh_token \
  --customer_id <customer_id> \
  --platform instagram
```

Expected: "✓ Token refreshed successfully"

**Step 3: Check Platform OAuth Status**
```bash
# For Instagram/Facebook:
# Customer goes to facebook.com/settings?tab=business_tools
# Verify "WAOOAW" app listed under "Active"

# For LinkedIn:
# Customer goes to linkedin.com/psettings/permitted-services
# Verify "WAOOAW" listed
```

### Resolution

**If Refresh Token Valid**:
```bash
# Trigger automatic refresh
curl -X POST -H "Authorization: Bearer $PP_TOKEN" \
  https://api.waooaw.com/pp/credentials/<credential_id>/refresh
```

**If Refresh Token Invalid**:
1. Send email to customer: "Platform reconnection required"
2. Customer clicks "Reconnect Instagram" in CP
3. Goes through OAuth flow again
4. Verify new token works:
   ```bash
   # Test post
   curl -X POST https://api.waooaw.com/pp/test-credential \
     --data '{"customer_id": "<id>", "platform": "instagram", "test_type": "connection"}'
   ```

**If Customer Revoked Access**:
1. No automatic fix possible
2. Contact customer to understand why they revoked
3. Guide through re-authorization process
4. Document reason in customer notes

### Prevention
- Automatic token refresh 7 days before expiry
- Email notification to customer at 3 days before expiry
- Background job checks token validity daily
- Graceful degradation: Agent pauses (not fails) on expired token

---

## 6. Platform Credential Invalid

**Severity**: P2 (Medium)  
**Frequency**: Occasional (5-7 tickets/week)

### Symptoms
- "Invalid credentials" error when posting
- Test connection fails
- Platform API returns 403 Forbidden

### Root Causes
1. Insufficient permissions granted during OAuth
2. Platform API changes breaking integration
3. Customer account suspended by platform
4. Credentials misconfigured (wrong API key/secret)

### Diagnosis Steps

**Step 1: Test Credential Directly**
```bash
# For marketing platforms
docker compose exec plant-backend \
  python -m src.Plant.BackEnd.scripts.test_platform_credential \
  --customer_id <customer_id> \
  --platform <platform> \
  --verbose

# For trading
docker compose exec plant-backend \
  python -m src.Plant.BackEnd.scripts.test_exchange_connection \
  --customer_id <customer_id> \
  --verbose
```

**Step 2: Check Platform API Status**
```bash
# Instagram/Facebook
curl https://graph.facebook.com/v19.0/me?access_token=<token>

# LinkedIn
curl -H "Authorization: Bearer <token>" \
  https://api.linkedin.com/v2/me

# Delta Exchange
curl -H "api-key: <key>" \
  -H "signature: <sig>" \
  https://api.delta.exchange/v2/profile
```

**Step 3: Verify Permissions**
```bash
# For OAuth tokens, decode and check scopes
python -c "import jwt; print(jwt.decode('<token>', options={'verify_signature': False}))"
# Look for required scopes in 'scope' field
```

### Resolution

**If Insufficient Permissions**:
1. Customer must re-authorize with all required permissions
2. Guide customer to:
   - CP > My Agents > Configuration
   - Click "Reconnect [Platform]"
   - **Important**: Grant ALL requested permissions (don't skip any)
   - Verify green checkmark appears

**If Platform Account Suspended**:
1. Customer must resolve suspension with platform directly
2. Common reasons:
   - Instagram: Posting too frequently (spam detection)
   - LinkedIn: Violated content policies
   - Delta Exchange: KYC incomplete or account flagged
3. After resolution, test credential again
4. May need to wait 24-48 hours for platform to clear suspension

**If API Key Wrong (Trading)**:
1. Customer generates new API key in exchange dashboard
2. Updates in CP > My Agents > Configuration
3. Verifies connectivity with test connection button

### Prevention
- Validate all required permissions during OAuth flow
- Graceful error messages guide customer to resolution
- Platform API status monitoring (detect outages)

---

## 7. Customer Login Failed

**Severity**: P3 (Low)  
**Frequency**: Common (20-30 tickets/week)

### Symptoms
- "Invalid email or password" error
- Password reset not working
- Account locked after multiple failed attempts

### Root Causes
1. Customer forgot password
2. Email typo during account creation
3. Account not activated
4. Browser cache preventing login

### Diagnosis Steps

**Step 1: Verify Account Exists**
```bash
# PP > Customers > Search by email
# Or query:
docker compose exec postgres \
  psql -U waooaw -c "SELECT id, email, status, email_verified FROM customers WHERE email = '<email>';"
```

**Step 2: Check Account Status**
```bash
# Expected:
# status: 'active' (not 'suspended' or 'pending')
# email_verified: true
```

**Step 3: Check Failed Login Attempts**
```bash
# PP > Audit > Login Attempts
# Filter by customer email
# Look for pattern of failures
```

### Resolution

**If Password Forgotten**:
```bash
# Send password reset  email
curl -X POST https://api.waooaw.com/auth/password-reset \
  --data '{"email": "<customer_email>"}'

# Customer receives email with reset link
# Link valid for 1 hour
```

**If Account Not Activated**:
```bash
# Manually activate account
docker compose exec plant-backend \
  python -m src.Plant.BackEnd.scripts.activate_customer \
  --email <customer_email>

# Resend verification email
curl -X POST https://api.waooaw.com/auth/resend-verification \
  --data '{"email": "<customer_email>"}'
```

**If Account Locked (Too Many Failed Attempts)**:
```bash
# Unlock account (ops override)
docker compose exec plant-backend \
  python -m src.Plant.BackEnd.scripts.unlock_customer \
  --email <customer_email> \
  --reason "Customer support request - ticket #12345"

# Notify customer via email that account unlocked
```

**If Email Typo in Account**:
```sql
-- Update email address (rare, verify customer identity first!)
UPDATE customers 
SET email = '<correct_email>', email_verified = false
WHERE id = '<customer_id>';

-- Send verification email to new address
```

### Prevention
- Clear password requirements during signup
- Email verification before account activation
- Account lockout after 5 failed attempts with 30-min cooldown
- Better error messages guide customer to solution

---

## 8. API Rate Limit Exceeded

**Severity**: P2 (Medium)  
**Frequency**: Occasional (3-5 tickets/week)

### Symptoms
- API returns 429 Too Many Requests
- Error: "Rate limit exceeded, retry after X seconds"
- Customer reports sporadic failures

### Root Causes
1. Customer hitting WAOOAW API rate limits
2. Platform (Instagram, LinkedIn) rate limits hit
3. Aggressive goal scheduling (too frequent)
4. Bug causing retry storm

### Diagnosis Steps

**Step 1: Check Customer's API Usage**
```bash
# PP > Usage > API Rate Limits > [Customer ID]
# Shows:
# - Requests in last hour
# - Current rate limit tier
# - Remaining quota
```

**Step 2: Check Platform Rate Limit Status**
```bash
# For Instagram/Facebook
curl -I https://graph.facebook.com/v19.0/me?access_token=<token>
# Check headers:
# X-Business-Use-Case-Usage: {"<app_id>":{"call_count":95,"total_cputime":25}}
# If call_count > 95, you're near the limit

# For LinkedIn
# Check X-RateLimit-* headers in response
```

**Step 3: Identify Source of Excessive Requests**
```bash
# PP > Audit > API Logs
# Filter by customer_id
# Group by endpoint
# Identify which API endpoint causing issues
```

### Resolution

**If WAOOAW Rate Limit Hit**:
```bash
# Temporary increase (ops override)
docker compose exec plant-backend \
  python -m src.Plant.BackEnd.scripts.adjust_rate_limit \
  --customer_id <customer_id> \
  --tier "premium" \
  --duration "24h" \
  --reason "Support ticket #12345"

# Or advise customer to upgrade plan
```

**If Platform Rate Limit Hit**:
1. Inform customer they're hitting Instagram/LinkedIn limits
2. Recommend reducing posting frequency:
   - Instagram: Max 200 API calls/hour per token
   - LinkedIn: Max 500 posts/day per company
3. Adjust goal schedules to spread out over time
4. Consider rotating between multiple platform accounts (advanced)

**If Retry Storm Detected**:
```bash
# Identify problematic goal
# PP > Goals > [Goal ID] > Pause

# Fix underlying issue causing retries
# Usually credential expiry or platform downtime

# Resume goal after fix
```

### Prevention
- Implement exponential backoff for retries
- Monitor customer approaching rate limits (alert at 80%)
- Better goal scheduling recommendations during onboarding
- Platform-specific rate limit headers parsed and respected

---

*(Continuing with scenarios 9-20...)*

## 9. Instagram Post Failed

**Severity**: P2  
**Common Errors**: Media upload failed, hashtag limit exceeded, content policy violation

**Quick Resolution**:
1. Check image dimensions (1080x1080 recommended)
2. Verify hashtag count ≤30
3. Check caption length ≤2,200 chars
4. Ensure business account (not personal)
5. Retry with smaller image file

---

## 10. LinkedIn Authorization Error  

**Severity**: P2  
**Common Errors**: Insufficient permissions, organization not found

**Quick Resolution**:
1. Verify customer has admin rights to company page
2. Re-authenticate with organization permissions (not just member)
3. Check company page ID is correct
4. Ensure permissions include `w_organization_social`

---

## 11. YouTube Quota Exceeded

**Severity**: P2  
**Error**: "Quota exceeded for quota metric YouTube Data API"

**Quick Resolution**:
1. YouTube has 10,000 units/day quota per project
2. Each video upload costs ~1,600 units
3. Solution: Customer must request quota increase from Google
4. Temporary: Reduce posting frequency to stay under quota

---

## 12. WhatsApp Message Delivery Failed

**Severity**: P2  
**Common Errors**: Template not approved, invalid phone number, quality rating low

**Quick Resolution**:
1. Verify message template approved by WhatsApp
2. Check phone number in E.164 format (+91XXXXXXXXXX)
3. Check account quality rating (must be "green")
4. Ensure recipient opted in to receive messages

---

## 13. Delta Exchange Authentication Failed

**Severity**: P1  
**Error**: "Invalid API key" or "Signature mismatch"

**Quick Resolution**:
```bash
# Test connection
docker compose exec plant-backend \
  python -m src.Plant.BackEnd.scripts.test_exchange_connection \
  --customer_id <id>

# Common fixes:
# 1. Verify API key active in Delta dashboard
# 2. Check IP whitelist includes WAOOAW IPs
# 3. Regenerate API key and update in CP
# 4. Verify permissions include 'trade'
```

---

## 14. Order Placement Rejected

**Severity**: P1  
**Common Errors**: Insufficient balance, risk limit exceeded, invalid symbol

**Quick Resolution**:
1. Check customer's Delta Exchange balance
2. Verify risk limits in agent configuration
3. Ensure trading pair exists (BTC-USD vs BTCUSD)
4. Check if customer's position limit reached
5. Verify market hours (crypto trades 24/7 but may have maintenance)

---

## 15. Risk Limit Violation

**Severity**: P1  
**Error**: "Trade blocked: Exceeds max notional" or "Exceeds max units"

**Quick Resolution**:
```bash
# Check current risk limits
# PP > Agents > [Agent ID] > Risk Configuration

# View violations
# PP > Audit > Risk Violations > [Customer ID]

# If legitimate, increase limits (ops approval required)
# Ensure customer understands risk implications
```

---

## 16. Position Close Failed

**Severity**: P0  
**Error**: "Unable to close position" or "Position not found"

**Quick Resolution**:
```bash
# Check current positions
curl -H "Authorization: Bearer $CUSTOMER_TOKEN" \
  https://api.delta.exchange/v2/positions

# Force close via exchange UI (extreme measure)
# Or manually place opposite order to close

# File incident report if data sync issue
```

---

## 17. Trial Limits Exceeded

**Severity**: P3  
**Error**: "Daily task limit reached" or "Token limit exceeded"

**Quick Resolution**:
```bash
# Check trial status
# PP > Trials > [Customer ID]
# Shows:
# - Daily tasks used: X/5
# - Total tokens used: Y/10,000

# Options:
# 1. Customer waits until tomorrow (daily reset at midnight)
# 2. Upgrade to paid plan (removes limits)
# 3. Ops override (rare, requires approval)
```

---

## 18. Payment Processing Failed

**Severity**: P2  
**Common Errors**: Card declined, insufficient funds, bank authentication failed

**Quick Resolution**:
1. Verify payment method valid in Razorpay dashboard
2. Check for 3D Secure authentication requirement
3. Common fixes:
   - Customer updates payment method
   - Retry payment after 1 hour
   - Try different payment method
4. Check if customer's bank blocking international transactions

---

## 19. Subscription Not Activated

**Severity**: P2  
**Symptoms**: Customer paid but trial not converted, paid features not accessible

**Quick Resolution**:
```bash
# Check payment status
# PP > Billing > Payments > [Customer ID]

# If payment successful but subscription not updated:
docker compose exec plant-backend \
  python -m src.Plant.BackEnd.scripts.sync_subscription_status \
  --customer_id <customer_id>

# Manually activate if sync fails
UPDATE subscriptions 
SET status = 'active', trial_status = 'converted'
WHERE customer_id = '<customer_id>';
```

---

## 20. CP Dashboard Loading Slowly

**Severity**: P3  
**Symptoms**: Dashboard takes >5 seconds to load, intermittent timeouts

**Quick Resolution**:
```bash
# Check backend API health
curl https://api.waooaw.com/health

# Check database query performance
# PP > Performance > Slow Queries
# Look for queries >1 second

# Customer-side fixes:
# 1. Clear browser cache
# 2. Disable browser extensions
# 3. Try incognito mode

# Server-side:
# - Check connection pool utilization
# - Verify CDN serving static assets
# - Check for N+1 query issues in logs
```

---

## Escalation Matrix

| Issue Type | First Contact | Escalation Level 1 | Escalation Level 2 |
|------------|---------------|--------------------|--------------------|
| **Platform Integration** | Ops team | Backend engineers | Platform vendor support |
| **Trading Execution** | Ops team | Trading team | Delta Exchange support |
| **Authentication** | Customer support | Security team | Auth vendor (Auth0) |
| **Performance** | Ops team | Backend engineers | Infrastructure team |
| **Billing** | Customer support | Finance team | Payment provider (Razorpay) |
| **Critical Outage** | On-call engineer | Engineering manager | CTO |

---

## Monitoring & Alerting

### Key Metrics to Watch

**Platform Health**:
- API response time P95 <200ms (alert if >500ms)
- Error rate <0.1% (alert if >1%)
- Scheduler execution success rate >99% (alert if <95%)

**Customer Experience**:
- Goal execution latency P95 <2 minutes (alert if >5 minutes)
- Credential validation success rate >95% (alert if <90%)
- Deliverable creation success rate >98% (alert if <95%)

**System Resources**:
- Database connection pool utilization <80% (alert if >90%)
- API rate limit hit rate <5% (alert if >10%)
- Memory usage <70% (alert if >85%)

---

## Common Commands Reference

```bash
# Restart all services
docker compose restart

# View logs for specific service
docker compose logs -f <service_name>

# Check service health
docker compose ps

# Access database
docker compose exec postgres psql -U waooaw -d waooaw

# Run diagnostic script
docker compose exec plant-backend python -m src.Plant.BackEnd.health.full_diagnostic

# Force sync customer state
docker compose exec plant-backend \
  python -m src.Plant.BackEnd.scripts.sync_customer_state \
  --customer_id <id>

# Clear cache (Redis)
docker compose exec redis redis-cli FLUSHDB
```

---

## Document Maintenance

**Review Schedule**: Monthly  
**Owner**: Operations Team Lead  
**Contributors**: All ops team members reporting new issues

**To Add New Scenario**:
1. Document 3+ occurrences of same issue
2. Follow scenario template (Symptoms, Root Causes, Diagnosis, Resolution, Prevention)
3. Include actual commands and outputs
4. Get peer review before committing

---

## Feedback & Improvements

Found an issue not covered? Discovered better resolution?

**Submit via**:
- Slack: #ops-runbooks
- Email: ops-team@waooaw.com  
- GitHub: Create issue in internal-docs repo

---

**Version History**

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-12 | Initial troubleshooting guide |
