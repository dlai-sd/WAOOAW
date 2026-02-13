# Customer Onboarding Runbook

**Document Version**: 1.0  
**Last Updated**: 2026-02-12  
**Owner**: Operations Team  
**Purpose**: Step-by-step guide for onboarding new WAOOAW customers

---

## Overview

This runbook guides operations team through the complete customer onboarding process, from initial signup to first agent hire and configuration. Ensures consistent, high-quality onboarding experience.

**Target Audience**: Operations team, customer success managers  
**Prerequisites**: Access to PP (Platform Portal), CP admin access, customer email  
**Estimated Time**: 30-45 minutes per customer

---

## Table of Contents

1. [Pre-Onboarding Checklist](#pre-onboarding-checklist)
2. [Account Creation & Verification](#account-creation--verification)
3. [Trial Setup](#trial-setup)
4. [Platform Credential Setup](#platform-credential-setup)
5. [Agent Configuration Guidance](#agent-configuration-guidance)
6. [First Goal Setup](#first-goal-setup)
7. [Validation & Handoff](#validation--handoff)
8. [Common Issues & Solutions](#common-issues--solutions)

---

## Pre-Onboarding Checklist

Before starting customer onboarding, verify:

- [ ] Customer has completed signup form (email, company name, industry)
- [ ] Email verification completed
- [ ] Customer inquiry form filled (which agents interested in)
- [ ] Business case documented (marketing or trading use case)
- [ ] Customer contact information available (email, phone, Slack/WhatsApp)

**Action**: Create customer record in CRM before proceeding.

---

## Account Creation & Verification

### Step 1: Verify Email Domain

**Purpose**: Prevent fraudulent signups, validate business legitimacy

```bash
# Check email domain reputation
dig MX customer-domain.com
whois customer-domain.com
```

**Red Flags**:
- Disposable email domains (mailinator, tempmail, etc.)
- Recently registered domains (<30 days)
- No MX records or website

**Action**: If red flags detected, escalate to security team before proceeding.

### Step 2: Create Customer Account

**Location**: PP > Customers > Create New

**Required Fields**:
- Email: `customer@example.com`
- Company Name: Full legal name
- Industry: `marketing`, `education`, `sales`
- Country: For compliance and billing
- Timezone: For scheduling goals appropriately

**Validation**:
- Email format valid
- Company name not duplicate (check existing customers)
- Industry matches available agents

### Step 3: Send Welcome Email

**Template**: `customer_welcome_email.html`

**Contents**:
- Welcome message and WAOOAW benefits
- Link to customer portal: `https://app.waooaw.com/portal`
- Temporary password (force reset on first login)
- Link to onboarding calendar invite
- Customer success manager contact info

**Action**: Schedule 30-minute onboarding call within 24 hours of signup.

---

## Trial Setup

### Step 4: Create Trial Subscription

**Location**: PP > Customers > [Customer ID] > Trials > Create

**Trial Parameters**:
- **Duration**: 7 days (168 hours) from activation
- **Agent Type**: Based on customer inquiry (marketing or trading)
- **Trial Limits**:
  - Daily task limit: 5 executions/day
  - Token limit: 10,000 tokens total
  - High-cost actions: Require approval (all external posts/trades)
- **Status**: `pending` (activate after credential setup)

**Important**: Do NOT activate trial until customer has configured credentials. Trial clock starts on activation.

### Step 5: Explain Trial Benefits

**During Onboarding Call**:
1. "Your 7-day trial starts after you set up credentials"
2. "You'll keep all deliverables even if you cancel"
3. "Trial includes 5 agent tasks per day - enough to see real value"
4. "All external actions (posting, trading) require your approval first"
5. "We'll help you configure everything in this call"

**Key Messaging**: Try before hire, keep results, no risk.

---

## Platform Credential Setup

### Step 6: Identify Required Credentials

**For Marketing Agents**:
- [ ] YouTube: OAuth2 (channel access)
- [ ] Instagram: Facebook Graph API token (business account)
- [ ] Facebook: Page access token
- [ ] LinkedIn: Organization token (company page)
- [ ] WhatsApp: Business API credentials

**For Trading Agents**:
- [ ] Delta Exchange: API key + secret
- [ ] Exchange account verified and funded

**Action**: Share credential setup guide specific to customer's agent type.

### Step 7: Guide Credential Setup (Screen Share)

**Marketing Agent - Example: Instagram**

1. Navigate to CP > My Agents > [Select Agent] > Configuration
2. Under "Platform Credentials" section, click "Connect Instagram"
3. Customer clicks "Authorize with Facebook"
4. Facebook OAuth flow:
   - Login to Facebook account
   - Select business Instagram account
   - Grant permissions: `pages_manage_posts`, `instagram_basic`, `instagram_content_publish`
   - Approve access
5. Verify green checkmark appears: "Instagram Connected ✓"

**Trading Agent - Example: Delta Exchange**

1. Customer opens Delta Exchange > Settings > API Management
2. Click "Create New API Key"
3. Set permissions: `read`, `trade` (NOT `withdraw`)
4. Set IP whitelist: WAOOAW platform IPs (provide list)
5. Copy API Key and Secret
6. In CP > My Agents > [Agent] > Configuration:
   - Paste API Key
   - Paste API Secret
   - Select default coin: BTC
   - Set max units per order: 1 (recommend conservative start)
   - Set max notional: ₹10,000
7. Click "Test Connection" - verify success

**Security Reminders**:
- Never share API secrets via email/Slack
- Use screen share only during live call
- Confirm IP whitelisting enabled (for trading)
- Explain credential rotation schedule (90 days)

### Step 8: Validate Credentials

**Location**: PP > Credentials > [Customer ID]

**Check**:
- [ ] All required credentials present
- [ ] Status: `active` (not `expired` or `invalid`)
- [ ] Last validated: Within last 5 minutes
- [ ] Permissions: Correct scopes (verify with test API call)

**Validation Tests**:
```bash
# Marketing - Test Instagram connection
docker compose -f docker-compose.local.yml exec plant-backend \
  python -m src.Plant.BackEnd.scripts.test_platform_credential \
  --customer_id <customer_id> \
  --platform instagram

# Trading - Test Delta Exchange auth
docker compose -f docker-compose.local.yml exec plant-backend \
  python -m src.Plant.BackEnd.scripts.test_exchange_connection \
  --customer_id <customer_id>
```

**Expected Output**: "✓ Connection successful, permissions validated"

---

## Agent Configuration Guidance

### Step 9: Configure Agent Settings

**Location**: CP > My Agents > [Agent] > Configuration

**Marketing Agent Configuration**:

1. **Nickname**: "Sarah - LinkedIn Expert" (friendly, memorable)
2. **Theme**: e.g., "Healthcare marketing for hospitals"
3. **Target Platforms**: Select 2-3 platforms (don't overwhelm with all 5)
4. **Content Guidelines**:
   - Tone: Professional, friendly, educational
   - Topics: Customer's industry focus
   - Forbidden topics: Politics, religion, controversial content
5. **Constraints**:
   - Posting hours: 9 AM - 6 PM customer timezone
   - Max posts per day: 3
   - Review all drafts before posting (trial mode)

**Trading Agent Configuration**:

1. **Nickname**: "Alex - BTC Futures Trader"
2. **Theme**: Conservative, risk-managed trading
3. **Risk Limits** (Critical - guide carefully):
   - Max units per order: 1 (start small)
   - Max notional per trade: ₹10,000
   - Allowed coins: BTC only (simplest)
   - Daily trade limit: 5 trades max
4. **Trading Hours**: 9 AM - 9 PM (avoid overnight volatility)
5. **Approval Mode**: All trades require approval (mandatory for trials)

**Validation**:
- [ ] All required fields filled
- [ ] Risk limits appropriate for trial
- [ ] Customer understands approval process
- [ ] Configuration saved successfully (green checkmark)

---

## First Goal Setup

### Step 10: Create First Goal (Guided)

**Marketing Agent - Example Goal: "Daily LinkedIn Post"**

1. Navigate to CP > Goals > Create New Goal
2. Select agent from dropdown
3. Goal template: "Social Media Post"
4. Goal parameters:
   - Platform: LinkedIn
   - Frequency: Daily at 10 AM customer timezone
   - Content type: Industry news + insights
   - Hashtags: 3-5 relevant hashtags
   - Deliverable: Draft post (require approval before publishing)
5. Click "Create Goal"
6. Status: "Pending Approval" (ops must approve first goal)

**Trading Agent - Example Goal: "BTC Price Monitoring"**

1. Navigate to CP > Goals > Create New Goal
2. Goal template: "Market Monitoring"
3. Goal parameters:
   - Coin: BTC
   - Frequency: Every 6 hours
   - Action: Generate market analysis report
   - Trade signal: Only suggest trades, require approval
   - Deliverable: Market analysis + optional trade recommendation
4. Click "Create Goal"

**Ops Approval** (PP):
1. Navigate to PP > Goal Approvals
2. Review goal for safety:
   - Frequency not excessive
   - Risk limits within trial bounds
   - Approval gates enabled
3. Click "Approve Goal"

### Step 11: Execute First Goal (Demo)

**Purpose**: Show customer the value immediately

**Live Demo**:
1. In PP > Goals > [Goal ID], click "Trigger Now"
2. Monitor execution in real-time (show customer)
3. Wait for deliverable (typically 30-120 seconds)
4. Customer sees draft in CP > Approvals
5. Walk through approval interface:
   - Preview deliverable
   - Edit if needed
   - Approve or reject
   - See confirmation

**Success Message**: "Your agent just completed its first task! Review the draft and approve when ready."

---

## Validation & Handoff

### Step 12: Onboarding Validation Checklist

Before ending onboarding call, verify:

- [ ] Customer can login to CP successfully
- [ ] Agent configured with correct credentials
- [ ] At least 1 goal created and approved
- [ ] Customer executed and approved first deliverable
- [ ] Trial activated (7-day countdown started)
- [ ] Customer understands approval workflow
- [ ] Calendar invite sent for day 5 check-in (trial conversion discussion)
- [ ] Customer has access to support resources (email, Slack, docs)

### Step 13: Document Onboarding Session

**Location**: PP > Customers > [Customer ID] > Notes

**Document**:
- Date/time of onboarding call
- Attendees (customer contacts)
- Agent type and configuration
- Goals created
- Credentials configured (list platforms only, not secrets)
- Issues encountered and resolutions
- Customer feedback/concerns
- Next steps and follow-up scheduled

**Template**:
```
Onboarding Call - 2026-02-12 10:00 AM PST
Attendee: John Doe (john@example.com)
Agent: Marketing Agent (Healthcare)
Platforms: LinkedIn, Instagram
Goals: Daily LinkedIn post (10 AM), Instagram story (6 PM)
Trial Activated: Yes (expires 2026-02-19 10:00 AM)
Next Check-in: 2026-02-17 (Day 5)
Notes: Customer excited about LinkedIn automation. Slight confusion on approval workflow - sent follow-up email with screenshots.
```

### Step 14: Send Post-Onboarding Email

**Template**: `post_onboarding_summary.html`

**Contents**:
- Thank you for onboarding call
- Summary of what was configured
- Quick reference: How to approve deliverables
- Trial expiration date (with urgency: "7 days to explore!")
- Link to help docs
- Customer success manager contact
- Invitation to Slack community (optional)

---

## Common Issues & Solutions

### Issue 1: OAuth Credentials Not Working

**Symptoms**: "Authorization failed" or "Invalid token"

**Root Causes**:
- Customer logged into wrong account (personal vs business)
- Insufficient permissions granted
- Token expired during onboarding

**Solution**:
1. Click "Disconnect" in CP
2. Clear browser cookies for platform (Instagram, Facebook, etc.)
3. Re-attempt OAuth flow
4. Ensure customer selects BUSINESS account
5. Grant ALL requested permissions
6. Verify connection with test post

### Issue 2: Delta Exchange API Key Rejected

**Symptoms**: "Authentication failed" or "API key invalid"

**Root Causes**:
- IP whitelist not configured
- Incorrect API secret copied (whitespace)
- Insufficient permissions (missing `trade` permission)

**Solution**:
1. Verify API key active in Delta Exchange dashboard
2. Check IP whitelist includes WAOOAW IPs: `<IP_LIST>`
3. Re-copy API secret (use "Show" button, avoid typing)
4. Verify permissions include `read` AND `trade`
5. Test connection again

### Issue 3: Agent Configuration Not Saving

**Symptoms**: "Save failed" or fields reset after save

**Root Causes**:
- Required field missing (not visually obvious)
- JSON configuration invalid (for advanced users)
- Network timeout during save

**Solution**:
1. Check browser console for validation errors
2. Verify all required fields filled (marked with *)
3. If using JSON config, validate at jsonlint.com
4. Retry save with better internet connection
5. If persists: Escalate to engineering (potential backend issue)

### Issue 4: First Goal Not Executing

**Symptoms**: Goal status "Pending", no deliverable after 10+ minutes

**Root Causes**:
- Scheduler not running (infrastructure issue)
- Goal not approved by ops
- Credentials expired after configuration

**Solution**:
1. Check goal status in PP > Goals > [Goal ID]
2. Verify status is "Approved" (not "Pending Approval")
3. Check scheduler health: PP > Health > Scheduler
4. Manually trigger: PP > Goals > [Goal ID] > "Trigger Now"
5. If still fails: Check logs and escalate

### Issue 5: Customer Can't Login to CP

**Symptoms**: "Invalid credentials" on login

**Root Causes**:
- Temporary password not reset on first login
- Email typo during account creation
- Account not activated

**Solution**:
1. Verify email in PP > Customers matches what customer is using
2. Send password reset email: PP > Customers > [Customer] > "Reset Password"
3. Check account status is `Active` (not `Suspended`)
4. If still fails: Check auth service logs

---

## Escalation Paths

### When to Escalate

**To Engineering** (Slack: #eng-support):
- Platform integration failing consistently (not credential issue)
- Scheduler not executing goals
- Data loss or corruption
- Performance issues (slow loading, timeouts)

**To Security** (Slack: #security):
- Suspicious signup (fraud indicators)
- Compromised credentials detected
- Customer reporting unauthorized access
- Data privacy concerns

**To Product** (Slack: #product-feedback):
- Customer requests feature not available
- Onboarding flow confusing (3+ customers report same issue)
- Missing agent capability customer expected
- Pricing/packaging concerns

---

## Success Metrics

Track for each onboarding:
- Time to first goal execution: Target <30 minutes
- Credentials configured successfully: Target 100%
- First deliverable approved: Target within 24 hours
- Customer satisfaction (post-call survey): Target 4.5/5
- Trial conversion rate: Target >30%

**Report these metrics weekly** to ops leadership.

---

## Appendix

### A. WAOOAW Platform IP Addresses (for Exchange API Whitelisting)

```
Production IPs:
- 34.123.45.67
- 34.123.45.68
- 34.123.45.69

Staging IPs:
- 35.234.56.78
```

### B. Standard Credential Permissions

**Instagram (Facebook Graph API)**:
- `instagram_basic`
- `instagram_content_publish`
- `pages_read_engagement`

**LinkedIn**:
- `w_member_social`
- `w_organization_social`

**Delta Exchange**:
- `read` (view account, positions)
- `trade` (place/cancel orders)
- NEVER `withdraw` (security)

### C. Customer Success Manager Assignment

Assign based on industry:
- **Marketing customers**: Sarah Johnson (sarah@waooaw.com)
- **Trading customers**: Alex Kumar (alex@waooaw.com)
- **Education customers**: Priya Sharma (priya@waooaw.com)

### D. Onboarding Call Recording

All onboarding calls should be recorded (with customer permission) and stored at:
`gs://waooaw-customer-onboarding/recordings/YYYY-MM-DD_customer-id.mp4`

Retention: 90 days

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-12 | Ops Team | Initial runbook creation |

---

**Questions or Issues?**  
Contact: ops-team@waooaw.com or Slack #ops-runbooks
