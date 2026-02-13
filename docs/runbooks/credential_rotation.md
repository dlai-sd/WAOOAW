# Platform Credential Rotation Procedures

**Document Version**: 1.0  
**Last Updated**: 2026-02-12  
**Owner**: Security & Operations Teams  
**Purpose**: Procedures for rotating platform credentials with zero downtime

---

## Overview

This document outlines procedures for rotating OAuth tokens, API keys, and other platform credentials for WAOOAW customers. Credential rotation is critical for security and compliance, ensuring expired or compromised credentials are updated without service disruption.

**Rotation Frequency**:
- OAuth Tokens: Auto-refresh (no customer action needed)
- API Keys (Trading): Every 90 days (recommended)
- Master Credentials: Every 180 days (WAOOAW platform keys)

**Target Audience**: Operations team, security team  
**Zero-Downtime Requirement**: All rotations must maintain service continuity

---

## Table of Contents

1. [Rotation Types](#rotation-types)
2. [OAuth Token Rotation (Automatic)](#oauth-token-rotation-automatic)
3. [API Key Rotation (Manual)](#api-key-rotation-manual)
4. [Emergency Rotation (Compromised Credentials)](#emergency-rotation-compromised-credentials)
5. [Customer Notification](#customer-notification)
6. [Validation & Rollback](#validation--rollback)

---

## Rotation Types

### Type 1: Automatic OAuth Token Refresh

**Platforms**: Instagram, Facebook, LinkedIn, YouTube  
**Frequency**: Automatic (7 days before expiry)  
**Customer Action**: None (seamless)  
**Risk**: Low

### Type 2: Scheduled API Key Rotation

**Platforms**: Delta Exchange, WhatsApp Business API  
**Frequency**: Every 90 days  
**Customer Action**: Required (generate new key)  
**Risk**: Medium (requires coordination)

### Type 3: Emergency Rotation

**Trigger**: Security incident, credential compromise, breach detection  
**Frequency**: As needed  
**Customer Action**: Required (immediate)  
**Risk**: High

### Type 4: Platform-Initiated Rotation

**Trigger**: Platform (Instagram, LinkedIn) forces token refresh  
**Frequency**: Varies by platform  
**Customer Action**: May be required  
**Risk**: Medium

---

## OAuth Token Rotation (Automatic)

### Overview

OAuth tokens (Instagram, Facebook, LinkedIn, YouTube) are automatically refreshed by WAOOAW using refresh tokens. No customer action required unless refresh fails.

### Automatic Refresh Process

**Trigger**: 7 days before token expiry

**Steps** (automated):
1. Scheduler detects token expiring soon
2. Calls platform's token refresh endpoint with refresh token
3. Receives new access token + refresh token
4. Updates credential in database
5. Logs rotation event
6. Continues normal operations

**Success Criteria**:
- New token valid
- All subsequent API calls use new token
- No service interruption
- Customer unaware rotation happened

### Monitoring

```bash
# Check upcoming token expirations
docker compose exec plant-backend \
  python -m src.Plant.BackEnd.scripts.check_expiring_tokens \
  --days 7

# Output:
# Customer ID | Platform | Expires At | Days Remaining
# cust_123    | instagram | 2026-02-19 | 7
# cust_456    | linkedin  | 2026-02-20 | 8
```

### Manual Refresh (If Automatic Fails)

```bash
# Refresh specific customer's token
docker compose exec plant-backend \
  python -m src.Plant.BackEnd.integrations.social.refresh_token \
  --customer_id <customer_id> \
  --platform instagram

# Verify refresh successful
# PP > Credentials > [Customer] > [Platform]
# Check: token_expires_at updated, status "active"
```

### Failure Handling

**If Refresh Token Invalid**:
1. Automatic retry (3 attempts with backoff)
2. If all retries fail, mark credential as "refresh_failed"
3. Send notification to customer: "Please reconnect Instagram"
4. Agent pauses (does not fail completely)
5. Customer re-authorizes in CP > My Agents > Configuration

**Notification Template** (`token_refresh_failed.html`):
```
Subject: Action Required: Reconnect Your Instagram Account

Hi [Customer Name],

We were unable to automatically refresh your Instagram access token. 
This happens when:
- You changed your Instagram password
- You revoked WAOOAW's access
- Instagram updated their security policies

To restore your agent:
1. Go to https://app.waooaw.com/portal/my-agents
2. Click "Reconnect Instagram"
3. Authorize WAOOAW with all requested permissions

Your agent will resume automatically once reconnected.

Need help? Contact support@waooaw.com
```

---

## API Key Rotation (Manual)

### Overview

API keys (Delta Exchange, WhatsApp Business API) require manual rotation. Customer generates new key, updates in WAOOAW, old key deprecated gracefully.

### Scheduled Rotation Process

**Timeline**: 90-day rotation cycle

**Day 85** (5 days before rotation):
1. Email customer: "Upcoming credential rotation required"
2. Include step-by-step guide
3. Schedule optional rotation call

**Day 90** (rotation day):
1. Customer generates new API key in exchange dashboard
2. Customer updates key in CP > My Agents > Configuration
3. WAOOAW validates new key (test connection)
4. Old key remains active for 24 hours (grace period)
5. After 24 hours, old key disabled in exchange dashboard

### Zero-Downtime Rotation Steps

**Phase 1: Generate New Credential (Customer)**

1. Customer logs into Delta Exchange > Settings > API Management
2. Click "Create New API Key"
3. Set same permissions as old key: `read`, `trade`
4. Set IP whitelist: Same as before (WAOOAW IPs)
5. Generate key - Copy API Key and Secret
6. **Important**: Keep old key active (don't delete yet)

**Phase 2: Update in WAOOAW**

1. Customer goes to CP > My Agents > [Trading Agent] > Configuration
2. Under "Exchange Credentials" section:
   - Paste new API Key
   - Paste new API Secret
3. Click "Test Connection" - verify success
4. Click "Save Configuration"

**Phase 3: Cutover (WAOOAW Backend)**

```bash
# Verify new credential active
docker compose exec plant-backend \
  python -m src.Plant.BackEnd.scripts.test_exchange_connection \
  --customer_id <customer_id>

# If successful, credential automatically switches to new key
# Old credential marked as "deprecated" (kept for 24h audit)
```

**Phase 4: Deprecate Old Key (Customer - 24 hours later)**

1. After confirming new key works for 24 hours
2. Customer deletes old API key in Delta Exchange dashboard
3. Notifies WAOOAW support: "Old key deleted"

### Validation

```bash
# Test all trading operations with new key
docker compose exec plant-backend \
  python -m src.Plant.BackEnd.scripts.test_trading_operations \
  --customer_id <customer_id> \
  --operations "auth,balance,place_order_test,cancel_order"

# Expected output:
# ✓ Authentication: Success
# ✓ Balance check: Success
# ✓ Test order placement: Success
# ✓ Order cancellation: Success
```

### Rollback Plan

**If New Key Fails**:
1. Immediately revert to old key in database:
   ```sql
   UPDATE exchange_setups
   SET api_key = (SELECT old_api_key FROM exchange_setups_audit 
                   WHERE customer_id = '<id>' 
                   ORDER BY created_at DESC LIMIT 1)
   WHERE customer_id = '<customer_id>';
   ```
2. Verify old key still active in exchange
3. Resume normal operations
4. Schedule new rotation attempt

---

## Emergency Rotation (Compromised Credentials)

### Overview

Emergency rotation when credentials are compromised, leaked, or suspected of unauthorized access.

**Triggers**:
- Customer reports unauthorized access
- Credential exposed in GitHub, Slack, email
- Suspicious activity detected (unusual API usage)
- Security audit findings

### Emergency Response Timeline

**0-15 minutes (Immediate)**:
1. Disable compromised credential in WAOOAW:
   ```bash
   docker compose exec plant-backend \
     python -m src.Plant.BackEnd.scripts.disable_credential \
     --customer_id <customer_id> \
     --platform <platform> \
     --reason "Security incident - credential compromise"
   ```

2. Notify customer immediately (phone + email + Slack)
3. Customer revokes key in platform (Delta Exchange, etc.)
4. Agent paused automatically

**15-60 minutes (Containment)**:
1. Audit all API calls made with compromised credential (last 7 days)
2. Check for unauthorized actions:
   - Trading: Unexpected orders or position changes
   - Marketing: Unauthorized posts
3. Document findings in incident report
4. Assess damage/impact

**1-4 hours (Recovery)**:
1. Customer generates new credential
2. Customer updates in WAOOAW
3. WAOOAW validates new credential
4. Agent resumes operations
5. Monitor closely for 24 hours

**Post-Incident (1-7 days)**:
1. Root cause analysis: How was credential compromised?
2. Implement preventive measures
3. Customer education on secure credential management
4. Update security procedures if needed

### Compromise Detection

**Automated Monitoring**:
```bash
# Check for suspicious API usage
docker compose exec plant-backend \
  python -m src.Plant.BackEnd.security.detect_anomalies \
  --customer_id <customer_id> \
  --lookback_hours 24

# Flags:
# - API calls from unexpected IP addresses
# - Unusually high request volume
# - Sensitive operations at unusual times
# - Failed authentication attempts spike
```

**Manual Review** (PP > Security > Credential Audit):
- Failed API calls: Sudden spike
- Successful API calls: Unusual patterns
- IP addresses: Compare to whitelist
- Timestamps: Activity during off-hours

---

## Customer Notification

### Notification Templates

**Upcoming Rotation (85 days)**:
```
Subject: Action Required in 5 Days: Rotate Delta Exchange API Key

Hi [Customer Name],

Your Delta Exchange API key for [Agent Nickname] will need rotation in 5 days for security best practices.

What You Need to Do:
1. Generate new API key in Delta Exchange (keep old key active)
2. Update key in WAOOAW agent configuration
3. Test connection succeeds
4. After 24 hours, delete old key

When: By [Date]
Estimated Time: 10 minutes
Need Help? Schedule a call: [Calendly Link]

Guide: [Link to detailed rotation guide]

Thanks for keeping your account secure!
WAOOAW Operations Team
```

**Rotation Reminder (Day 90)**:
```
Subject: Today: Rotate Your Delta Exchange API Key

Hi [Customer Name],

Today is rotation day for your Delta Exchange API key. This ensures your account stays secure.

Quick steps: [Link to video tutorial]

Need help? Reply to this email or call support.
```

**Post-Rotation Confirmation**:
```
Subject: ✓ API Key Rotation Successful

Hi [Customer Name],

Your Delta Exchange API key has been successfully rotated. Your agent [Nickname] is operating normally with the new credentials.

Old key can be safely deleted from Delta Exchange dashboard.

Next rotation due: [Date + 90 days]
```

**Emergency Rotation**:
```
Subject: URGENT: Credential Rotation Required Immediately

Hi [Customer Name],

We detected a potential security issue with your [Platform] credentials. 

IMMEDIATE ACTION REQUIRED:
1. Generate new API key/token NOW
2. Update in WAOOAW immediately
3. Delete old credential

Your agent is temporarily paused for security.

Contact support immediately: support@waooaw.com / [Phone]

Incident ID: [ID]
```

---

## Validation & Rollback

### Post-Rotation Validation Checklist

After any rotation, verify:

- [ ] New credential status: "active"
- [ ] Test connection: Pass
- [ ] Agent status: "running" (not "paused")
- [ ] Recent goal execution: Success
- [ ] No error spikes in logs (last 1 hour)
- [ ] Customer notified of successful rotation
- [ ] Old credential marked "deprecated" (not "active")

**Validation Script**:
```bash
docker compose exec plant-backend \
  python -m src.Plant.BackEnd.scripts.verify_credential_rotation \
  --customer_id <customer_id> \
  --platform <platform> \
  --rotation_id <rotation_id>

# Output:
# ✓ Credential status: active
# ✓ Connection test: passed
# ✓ Agent operational: yes
# ✓ Recent goals executed: 3/3 success
# ✓ Error rate: 0.0%
# ✓ Rotation: SUCCESSFUL
```

### Rollback Procedure

**When to Rollback**:
- New credential fails validation after 3 retry attempts
- Agent unable to execute goals with new credential
- Platform API errors increase significantly
- Customer reports issues immediately after rotation

**Rollback Steps**:
```bash
# 1. Check old credential still valid
docker compose exec plant-backend \
  python -m src.Plant.BackEnd.scripts.test_credential \
  --credential_id <old_credential_id>

# 2. If valid, revert active credential
docker compose exec plant-backend \
  python -m src.Plant.BackEnd.scripts.rollback_credential_rotation \
  --customer_id <customer_id> \
  --platform <platform> \
  --to_credential_id <old_credential_id> \
  --reason "New credential validation failed"

# 3. Verify rollback successful
# Agent should resume with old credential

# 4. Investigate why new credential failed
# 5. Schedule new rotation attempt
```

---

## Audit & Compliance

### Audit Trail

All credential rotations logged to audit table:

```sql
SELECT 
  cr.id,
  cr.customer_id,
  cr.platform,
  cr.old_credential_id,
  cr.new_credential_id,
  cr.rotation_type,  -- 'scheduled', 'emergency', 'platform_initiated'
  cr.initiated_by,    -- 'system', 'customer', 'ops'
  cr.status,          -- 'success', 'failed', 'rolled_back'
  cr.started_at,
  cr.completed_at,
  cr.notes
FROM credential_rotations cr
WHERE customer_id = '<customer_id>'
ORDER BY started_at DESC;
```

### Compliance Requirements

**SOC 2 Type II**:
- All credentials rotated within 90 days
- Emergency rotations completed within 4 hours of detection
- Audit trail maintained for 7 years

**PCI DSS** (if applicable):
- API keys with payment access rotated every 90 days
- Compromised credentials revoked immediately
- Access logs reviewed quarterly

---

## Best Practices

### For Operations Team

1. **Monitor Expiration Dashboard Daily**
   - PP > Security > Credential Expirations
   - Proactively contact customers 7 days before expiry

2. **Test Rotation Process Quarterly**
   - Pick non-critical customer (or test account)
   - Run full rotation end-to-end
   - Document any issues

3. **Maintain Rotation Calendar**
   - Schedule rotations during low-traffic hours
   - Avoid weekend rotations (support availability)
   - Batch similar customers (same platform)

4. **Document Every Rotation**
   - Even successful ones
   - Capture lessons learned
   - Update runbook as needed

### For Customers

**Educate customers to**:
1. Never share API secrets via email, Slack, or screenshots
2. Use IP whitelisting whenever possible
3. Enable 2FA on platform accounts
4. Monitor their own API usage dashboards
5. Report suspicious activity immediately

---

## Common Issues & Troubleshooting

### Issue: OAuth Refresh Failing Repeatedly

**Symptoms**: Token refresh fails 3+ times in a row

**Causes**:
- Platform API outage
- Customer revoked app access
- OAuth app misconfigured on platform side

**Resolution**:
1. Check platform status page (facebook.com/status)
2. Verify customer hasn't revoked WAOOAW access
3. Test OAuth flow with test account
4. If platform issue, wait and retry
5. If persistent, escalate to engineering

### Issue: New API Key Not Recognized

**Symptoms**: New key fails immediately after rotation

**Causes**:
- Key not activated yet (some platforms have delay)
- IP whitelist not updated
- Permissions missing
- Copy-paste error (whitespace)

**Resolution**:
1. Wait 5 minutes for key activation
2. Verify IP whitelist includes WAOOAW IPs
3. Check permissions match old key
4. Re-copy key (use "Show" button, avoid typing)
5. Test with curl directly to platform API

### Issue: Old Key Deleted Too Soon

**Symptoms**: Service disruption when customer deletes old key before 24-hour grace period

**Causes**:
- Customer didn't read instructions fully
- Misunderstood timeline

**Resolution**:
1. If new key valid, no action needed (brief interruption only)
2. If new key not working, customer must regenerate
3. Emergency rotation process applies
4. Better customer communication next time

---

## Metrics & Reporting

### Key Metrics

- **Auto-Refresh Success Rate**: >99% (alert if <95%)
- **Manual Rotation Completion Rate**: >90% within 7 days
- **Emergency Rotation Time**: <4 hours (median)
- **Rollback Rate**: <5% (indicates quality issues if higher)

### Monthly Report

**To Be Submitted**: First business day of each month

**Contains**:
- Total rotations: Auto vs Manual vs Emergency
- Success rate by platform
- Average rotation time
- Customer support tickets related to rotation
- Lessons learned
- Upcoming rotations (next 30 days)

---

## Document Maintenance

**Owner**: Security Team Lead  
**Review Frequency**: Quarterly  
**Contributors**: Operations team, engineering team

**Update Triggers**:
- Platform API changes affecting rotation
- Security incident learnings
- Process improvements identified
- Compliance requirement updates

---

**Version History**

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-12 | Initial credential rotation procedures |

---

**Questions or Feedback?**  
Contact: security-team@waooaw.com or Slack #security-runbooks
