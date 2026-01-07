# CP (Customer Portal) User Journey
**Document Type:** User Experience Specification  
**Version:** 0.5 Draft  
**Date:** 2026-01-07  
**Status:** Pending Approval  
**Audience:** Product, Design, Engineering  
**YAML Specification:** [CP_USER_JOURNEY.yaml](CP_USER_JOURNEY.yaml) (machine-readable, API contracts)  
**Constitutional Alignment:** main/Foundation.md, Governor Charter, Mobile UX Requirements

---

## 📋 Document Synchronization

**Important:** This document (CP_USER_JOURNEY.md) and its YAML counterpart (CP_USER_JOURNEY.yaml) must be updated together:
- **Markdown (.md)**: Human-readable user journey documentation with UI/UX details, wireframe descriptions, gap analysis
- **YAML (.yaml)**: Machine-readable specification with API contracts, data schemas, constitutional cross-references

**Version Control:** Both files share version 0.5 (draft). Any updates require synchronized changes to both files.

---

## 🎯 Executive Summary

The Customer Portal (CP) serves **two distinct user personas** across **seven lifecycle stages**:

**Personas:**
1. **Visitor** (Pre-registration) - Browsing marketplace, evaluating agents/teams, making hire decision
2. **Customer** (Post-registration) - Onboarded user managing active agents/teams, monitoring performance, controlling costs

**Lifecycle Stages:**
1. Discovery & Evaluation (Visitor)
2. Hire Decision & Registration (Visitor → Customer)
3. Onboarding & Setup (Customer)
4. Goal Configuration (Customer)
5. Conformity Testing (Customer + Agent)
6. Go-Live Declaration (Customer)
7. Operations & Optimization (Customer)

---

## 📍 User Journey Stages

### **Stage 1: Discovery & Evaluation** (Visitor - Pre-Registration)

#### 1.1 Browse Agents/Teams (Marketplace)
**User Goal:** Discover specialized AI agents/teams that match business needs

**User Actions:**
- Land on CP homepage (WAOOAW marketplace)
- Browse agent catalog by:
  - **Industry:** Healthcare, Education, Finance, Marketing, Sales
  - **Specialty:** Content Writing, Social Media, SEO, Email Marketing, etc.
  - **Pricing:** ₹8K-18K (single agent), ₹19K-30K (team)
  - **Rating:** 4.5+ stars (customer reviews)
  - **Status:** 🟢 Available, 🟡 Working (limited slots), 🔴 Fully booked
- View agent cards:
  - Avatar, specialty, rating, activity ("Posted 23 times today")
  - Pricing breakdown, trial offer (7-day free)
  - Customer testimonials, sample work

**UI Components:**
- Hero banner: "Try Before Hire - 7 Days Free, Keep All Deliverables"
- Filter sidebar: Industry, specialty, price range, rating, availability
- Agent grid: Card layout with hover states showing quick stats
- Search bar: "Find agents for [your goal]" with autocomplete

**System Behavior:**
- Anonymous browsing (no auth required)
- Agent data fetched from **Manifest Service (Port 8011)** via CP backend (BFF pattern)
- Real-time availability updated via **Cloud Pub/Sub** (agent status changes)

**Exit Criteria:** Visitor identifies 1+ agents/teams of interest

---

#### 1.2 Evaluate Agent/Team Details
**User Goal:** Understand agent capabilities, pricing, trial terms before committing

**User Actions:**
- Click agent card → navigate to Agent Details page
- Review:
  - **Capabilities:** Skills breakdown (Think→Act→Observe cycle descriptions)
  - **Industry Expertise:** Domain knowledge (HIPAA, FDA, FERPA compliance badges)
  - **Pricing Model:** Fixed monthly ₹12K (industry-specialized) vs ₹8K (generic)
  - **Trial Terms:** 7 days free, keep deliverables, no credit card required
  - **Customer Reviews:** 4.8/5 stars (47 reviews), testimonials, sample outputs
  - **Activity Stats:** 156 articles published this month, 98% customer satisfaction
- Compare agents (side-by-side comparison for up to 3 agents)
- Watch demo video (2-min explainer: "How Healthcare Content Writer works")
- View sample outputs (anonymized customer deliverables)

**UI Components:**
- Agent hero section: Avatar, name, specialty, CTA ("Start 7-Day Free Trial")
- Tabbed interface: Overview | Skills | Pricing | Reviews | FAQ
- Comparison widget: "Compare with similar agents" (sticky sidebar)
- Trust indicators: Genesis-certified badge, Industry embeddings verified, Constitutional compliance score

**System Behavior:**
- Agent details fetched from **Manifest Service (Port 8011)** + **Industry Knowledge Service (Port 8004)**
- Customer reviews from **Finance Service (Port 8007)** (subscription satisfaction data)
- Sample outputs from anonymized **trial deliverables archive**

**Exit Criteria:** Visitor decides to hire (or exits to browse more)

---

### **Stage 2: Hire Decision & Registration** (Visitor → Customer Transition)

#### 2.1 Start Trial (No Payment Required)
**User Goal:** Begin 7-day free trial without financial commitment

**User Actions:**
- Click "Start 7-Day Free Trial" button on agent details page
- Prompted to create account:
  - **Social OAuth:** Sign up with Google/GitHub (preferred - 1-click)
  - **Email registration:** Email + password (fallback)
- Accept terms:
  - 7-day trial, keep deliverables regardless of subscription decision
  - Platform absorbs trial cost ($5 cap per agent, synthetic data mode)
  - No credit card required, no auto-charge after trial
- Select trial start date (immediate or scheduled within 7 days)

**UI Components:**
- Trial start modal: Social login buttons (Google, GitHub), email signup form
- Terms acceptance checkbox: "I understand trial terms (7 days free, keep work)"
- Calendar picker: "When do you want to start?" (default: today)

**System Behavior:**
- User account created in **PostgreSQL (auth_users table)**
- Trial subscription created in **Finance Service (Port 8007)**: `subscription_status = trial_active`
- **Policy Service (Port 8013)** enforces trial mode: synthetic data, sandbox routing (Stripe test mode, AI mock)
- Agent instance provisioned (trial mode flag = true)

**Exit Criteria:** User registered, trial subscription active, agent provisioned

---

#### 2.2 Onboarding Flow (First-Time Customer Experience)
**User Goal:** Understand how to set up and manage agent/team

**User Actions:**
- Welcome screen: "Welcome to WAOOAW! Your Healthcare Content Writer is ready to set up."
- Onboarding wizard (5 steps, 3-5 min total):
  1. **Connect accounts** (optional): WordPress, Mailchimp, CRM (OAuth flows)
  2. **Set initial goals** (simplified): "What should your agent accomplish this week?" (3 goals max)
  3. **Review approval settings**: "You'll approve external actions via mobile push notifications"
  4. **Download mobile app** (QR code): iOS/Android app for approvals on-the-go
  5. **Schedule kickoff** (optional): 15-min onboarding call with platform support

**UI Components:**
- Wizard progress bar: Step 1/5, 2/5, etc.
- Integration cards: Click to connect (OAuth modals), skip option for each
- Goal input: Textarea with examples ("Publish 3 blog posts about diabetes management")
- Mobile app QR codes: iOS App Store, Android Play Store
- Skip/Next buttons: Allow skipping steps (revisit later in settings)

**System Behavior:**
- Integration OAuth tokens stored in **HashiCorp Vault** (via Integrations Service Port 8009)
- Initial goals saved to **agent workspace** (agents/{agent_id}/state/goals.md)
- Mobile app install tracked (for push notification enrollment)
- Onboarding completion status: **PostgreSQL (customer_onboarding table)**

**Exit Criteria:** Customer completes onboarding (or skips steps), ready for goal configuration

---

### **Stage 3: Goal Configuration** (Customer Setup)

#### 3.1 Define Agent/Team Goals
**User Goal:** Configure what agent/team should accomplish (Job definition)

**User Actions:**
- Navigate to "Setup Goals" screen (post-onboarding or from dashboard)
- Define primary goal:
  - **Goal statement:** "Publish 5 HIPAA-compliant blog posts per week about diabetes management"
  - **Success criteria:** 4.5+ star rating, 2-hour response time, 95% fact-check pass rate
  - **Constraints:** No experimental treatments, cite only peer-reviewed sources, ADA guidelines only
  - **Deliverables:** 800-1200 word articles, SEO-optimized, medical fact-checked
  - **Timeline:** Start immediately, ongoing (monthly subscription)
- Add secondary goals (optional, up to 3 total):
  - "Respond to blog comments within 2 hours"
  - "Create 3 social media posts per article (Twitter, LinkedIn, Facebook)"
- Assign priority (P0 = critical, P1 = high, P2 = medium, P3 = low)

**UI Components:**
- Goal form: Multi-step wizard (Goal → Success Criteria → Constraints → Deliverables → Timeline)
- Template library: "Use a template" (pre-filled goals for common use cases)
- Agent recommendation: "Based on your goals, Healthcare Content Writer is a great fit" (validation)
- Save draft: Goals saved as draft, not submitted to agent yet

**System Behavior:**
- Goals validated by **Genesis Service** (via Agent Creation Service Port 8001):
  - Check if goal matches Job capabilities (Healthcare Content Writer can publish blogs, not diagnose patients)
  - Validate constraints are constitutionally enforceable (e.g., "cite only peer-reviewed" = verifiable)
  - Estimate query budget ($0.80/day for 5 articles/week with fact-checking)
- Goals saved to **Manifest Service (Port 8011)**: `customer_goals` schema
- Agent workspace initialized: agents/{agent_id}/state/goals.md, context.md

**Exit Criteria:** Goals defined, validated by Genesis, saved to agent workspace

---

#### 3.2 Configure Agent/Team Settings
**User Goal:** Fine-tune agent behavior, approval preferences, notification settings

**User Actions:**
- Navigate to "Agent Settings" tab
- Configure:
  - **Approval preferences:**
    - Auto-approve low-risk actions (draft creation, research, internal reviews)
    - Require approval for external actions (publishing, sending emails, API writes)
    - Set approval timeout (default 24 hours, escalate to Helpdesk if no response)
  - **Notification preferences:**
    - Push notifications (mobile): Enabled (default), quiet hours 10 PM - 7 AM
    - Email notifications: Approval requests, daily summary, weekly reports
    - Slack notifications (optional): Connect Slack workspace for team coordination
  - **Query budget:**
    - Daily limit: $1/day (default), adjust to $2/day or $5/day (increases monthly cost)
    - Budget alerts: Warn at 70%, require approval at 85%, suspend at 100%
  - **Integration permissions:**
    - WordPress: Publish posts (requires approval), edit drafts (auto-approve)
    - Mailchimp: Send campaigns (requires approval), create drafts (auto-approve)
    - Google Analytics: Read-only (no approval needed)

**UI Components:**
- Settings tabs: Approvals | Notifications | Budget | Integrations | Advanced
- Toggle switches: Enable/disable features with explanatory tooltips
- Budget slider: Visual indicator of cost impact (₹12K/month → ₹15K/month if $2/day)
- Integration permission matrix: Table showing read/write/delete permissions per integration

**System Behavior:**
- Approval preferences saved to **Governance Service (Port 8003)**: `approval_policy` table
- Notification preferences: **Mobile app settings synced via Firebase**
- Query budget: **Finance Service (Port 8007)** validates against plan limits (Starter ₹12K = $1/day max)
- Integration permissions: **Policy Service (Port 8013)** enforces PDP/PEP rules

**Exit Criteria:** Agent configured, settings validated, ready for conformity test

---

### **Stage 4: Agent/Team Setup Wizard** (Goal Setting + Access Provisioning)

#### 4.1 Complete Agent/Team Setup Wizard
**User Goal:** Equip agent/team with business context, access, and goal completion criteria

**User Actions:**
- Navigate to "Agent Setup Wizard" (automatically launched after initial goal configuration)
- **Setup Wizard Steps** (pre-built for every agent/team):
  1. **Business Background:** Provide context about your business
     - Industry vertical (Healthcare, Education, Finance)
     - Target audience (B2B, B2C, Enterprise)
     - Brand voice (Professional, Casual, Technical)
     - Key differentiators (What makes your business unique?)
  2. **Access Provisioning:** Grant agent access to required tools
     - WordPress admin credentials (encrypted storage)
     - Mailchimp API key (OAuth preferred)
     - Google Analytics read access
     - CRM access (Salesforce, HubSpot)
  3. **Goal Completion Criteria:** Define what "success" looks like
     - Acceptance criteria (e.g., "4.5+ star rating, 95% fact-check pass")
     - Quality gates (peer review required, legal review for regulated content)
     - Delivery SLAs (within 24 hours, by EOD Friday)
     - Success metrics (traffic increase, engagement rate, conversion rate)
  4. **Communication Preferences:** How should agent interact with you?
     - Notification frequency (real-time, hourly digest, daily summary)
     - Escalation thresholds (when to ask for help vs proceed autonomously)
     - Approval preferences (review drafts, approve final outputs)
  5. **Conformity Validation:** Agent confirms understanding
     - Agent summarizes business context, goals, access, completion criteria
     - Customer reviews summary: "Does agent understand your requirements?"
     - Agent produces 1 sample deliverable (using synthetic data, no real execution)
     - Customer rates sample: "Is this what you expected?" (⭐⭐⭐⭐⭐)
- **Time SLA Notification:** "Setup typically takes 10-15 minutes. You're on track!"

**UI Components:**
- Setup wizard progress: Step 1/5, 2/5, etc. with estimated time remaining
- Access provisioning: OAuth connection buttons, credential input forms (encrypted)
- Goal completion criteria builder: Template library + custom criteria input
- Sample deliverable viewer: Side-by-side (Agent draft | Your feedback)
- Star rating: 5-star rating for sample output quality

**System Behavior:**
- **Policy Service (Port 8013)** enforces trial mode: synthetic_data = true, sandbox_routing = true
- **Agent Execution Service (Port 8002)** generates sample deliverable with mock AI (no real API costs)
- **Integrations Service (Port 8009)** validates access credentials (OAuth token test, no real writes)
- **Audit Service (Port 8010)** logs setup completion (correlation_id = setup_wizard_{timestamp})
- Genesis validates setup: Business context sufficient, access provisioned, goals clear
- **Time SLA Tracking:** If setup exceeds 20 minutes, notify: "Taking longer than usual? Need help?"

**Exit Criteria:** Setup wizard completed, agent equipped with context/access/criteria, customer satisfied with sample

---

#### 4.2 Setup Adjustments (If Needed)
**User Goal:** Refine setup if sample deliverable doesn't meet expectations

**User Actions:**
- Review sample deliverable: "1 blog article draft (800 words, healthcare topic)"
- Rate quality: ⭐⭐⭐ (3 stars - needs improvement)
- Provide feedback:
  - "Article missing medical citations (need at least 3 peer-reviewed sources)"
  - "Tone too casual (should be professional, authoritative)"
  - "SEO optimization weak (target keyword not prominent)"
- Make adjustments:
  - Update goal completion criteria: "Cite 3+ peer-reviewed sources per article"
  - Refine brand voice: "Professional, authoritative (not casual)"
  - Add success metric: "Target keyword in H1, first paragraph, meta description"
- Regenerate sample: Agent produces new draft with updated criteria
- Re-rate: ⭐⭐⭐⭐⭐ (5 stars - ready for go-live)
- Complete setup: "Approve Setup & Go Live"

**UI Components:**
- Feedback form: Textarea with character limit 1000, bullet points encouraged
- Adjustment fields: Edit business context, brand voice, goal criteria (inline editing)
- Regenerate button: "Try Again with Updated Criteria" (instant, no cost)
- Go-live approval: "Approve Setup & Go Live" button (green, prominent)

**System Behavior:**
- Adjustments trigger **Genesis re-validation** (if goals/criteria changed significantly)
- Regenerate sample: Agent Execution Service (Port 8002) produces new draft (synthetic data, instant)
- Go-live approval: Customer decision stored in **Audit Service** (attested approval with setup_completion_id)
- **Time SLA Notification:** If adjustments exceed 3 iterations, suggest: "Schedule 15-min call with support?"

**Exit Criteria:** Customer approves setup (4+ stars on sample), agent ready for go-live

---

### **Stage 5: Go-Live Declaration** (Customer-Initiated Production)

#### 5.1 Go-Live Activation
**User Goal:** Activate agent for production use (real data, real integrations, real customers)

**User Actions:**
- Navigate to "Go-Live" screen (post-conformity test approval)
- Review go-live checklist:
  - ✅ Setup wizard completed (business context, access, goal criteria)
  - ✅ Sample deliverable approved (4+ stars rating)
  - ✅ Agent settings configured (approvals, notifications, budget)
  - ✅ Integrations connected and tested (WordPress, Mailchimp)
  - ✅ Mobile app installed (for approvals on-the-go)
  - ⚠️ Trial mode continues (synthetic data disabled, real integrations enabled, platform absorbs costs)
- Confirm go-live: "I understand agent will now work with real data. Let's go live!"
- System transitions agent from trial → production:
  - Trial mode disabled (synthetic_data = false, sandbox_routing = false)
  - Real integrations activated (WordPress real endpoint, Stripe production mode)
  - Agent budget enforcement begins ($1/day limit, alerts at 70%/85%/100%)
  - 7-day trial countdown continues (customer still in trial billing, platform absorbs cost)

**UI Components:**
- Go-live checklist: Green checkmarks for completed items, yellow warnings for optional items
- Confirmation modal: "Are you ready to go live?" with impact summary
- Go-live button: Large, prominent CTA "Activate Agent for Production"
- Success screen: "Your agent is live! First action will require your approval."

**System Behavior:**
- **Policy Service (Port 8013)** disables trial mode: PDP evaluates production policies (no sandbox routing)
- **Agent Execution Service (Port 8002)** switches to real AI APIs (Groq, OpenAI), real integrations
- **Finance Service (Port 8007)** starts cost tracking (queries, API calls, integration usage)
- **Governance Service (Port 8003)** enforces production approval gates (external actions require approval)
- **Audit Service (Port 8010)** logs go-live event (correlation_id = go_live_{timestamp}, customer_id, agent_id)

**Exit Criteria:** Agent live in production, customer notified, first approval request imminent

---

### **Stage 6: Operations & Monitoring** (Customer - Active Management)

#### 6.1 Monitor Agent Actions & Performance
**User Goal:** Observe agent work in real-time, ensure quality, track progress toward goals

**User Actions:**
- Navigate to "Agent Dashboard" (default landing page post-go-live)
- View real-time activity feed:
  - "10:32 AM - Published blog post: 'Managing Type 2 Diabetes with Diet'"
  - "10:45 AM - Sent approval request: 'Publish 3 social media posts'"
  - "11:02 AM - Executed Skill: 'Fact-Check Medical Claims' (8 sources validated)"
- Review performance metrics:
  - **Goals progress:** 3/5 articles published this week (60% complete)
  - **Quality scores:** 4.7/5 average rating, 98% fact-check pass rate
  - **Approval latency:** 4.2 minutes average response time (target <5 min)
  - **Budget utilization:** $0.75/$1.00 daily budget (75%, green status)
- Drill into specific actions:
  - Click activity → view full Think→Act→Observe context
  - Review agent's constitutional queries, decision rationale, output quality
  - See audit trail (correlation_id, timestamps, approvals, vetos)

**UI Components:**
- Dashboard hero section: Agent status (🟢 Active), goals summary, quick actions
- Activity timeline: Scrollable feed with time-series visualization
- Performance KPIs: Card grid (goals, quality, latency, budget) with trend indicators (↑↓)
- Action detail modal: Expandable view with Think→Act→Observe tabs, audit trail

**System Behavior:**
- Real-time updates via **Cloud Pub/Sub** (agent_state_changed events)
- Metrics aggregated by **Finance Service (Port 8007)** (cost tracking) + **Governance Service (Port 8003)** (approval stats)
- Audit trail fetched from **Audit Service (Port 8010)** (correlation_id lookup)

**Exit Criteria:** Customer observes agent working correctly, no issues

---

#### 6.2 Approve/Deny Agent Actions (Mobile + Web)
**User Goal:** Control agent external execution via approval workflow

**User Actions:**
- Receive push notification: "Healthcare Content Writer needs approval"
- Tap notification → navigate to Approval Request screen
- Review request context:
  - **Summary:** "Publish blog post: 'Managing Type 2 Diabetes with Diet'"
  - **Proposed action:** "Publish to WordPress blog (1,200 words, SEO-optimized)"
  - **Risks:** "Public-facing content, medical topic (HIPAA compliant, fact-checked)"
  - **Alternatives:** "Schedule for tomorrow, request revisions"
- Make decision:
  - **APPROVE** (green ✓): Agent publishes immediately, customer notified
  - **DENY** (red ✗): Agent pauses, customer provides reason ("Article needs more citations")
  - **DEFER** (yellow ⏸): Agent pauses, customer requests more info ("Show me fact-check sources")
  - **ESCALATE** (orange ⚠): Platform Governor reviews (complex decision, customer unsure)

**UI Components:**
- Approval request card: Summary, action, risks, alternatives (mobile-optimized)
- 4-action button row: Full-width buttons, color-coded, icons
- Reason input (if DENY/DEFER): Textarea, character limit 500, suggestions dropdown
- Confirmation dialog: "Are you sure you want to approve?" with impact summary

**System Behavior:**
- Push notification via **Firebase Cloud Messaging** (mobile), email (web fallback)
- Approval decision posted to **Governance Service (Port 8003)**: POST /v1/approvals/{approval_id}
- **Agent Execution Service (Port 8002)** receives decision, resumes or pauses agent
- **Audit Service (Port 8010)** logs approval (decision_id, governor_id, timestamp, reason)

**Exit Criteria:** Customer approves/denies action, agent proceeds or pauses

---

#### 6.3 Configure/Reconfigure Agent Settings (Runtime Adjustments)
**User Goal:** Adjust agent behavior without re-deployment (goal refinement, budget increase, integration changes)

**User Actions:**
- Navigate to "Agent Settings" (from dashboard or action overflow menu)
- Make runtime adjustments:
  - **Goal refinement:** Update goal statement ("Add: Include ADA guidelines link in every article")
  - **Budget increase:** Adjust daily limit $1 → $1.50 (agent hitting 100% frequently)
  - **Approval policy change:** Auto-approve social media posts (low-risk, frequent)
  - **Integration updates:** Connect new integration (Google Analytics for traffic tracking)
  - **Notification preferences:** Disable email, enable Slack notifications
- Save changes: "Apply Changes" button
- System validation:
  - Genesis validates goal changes (if significant, triggers re-certification)
  - Finance validates budget increase (Starter plan allows max $2/day, upgrade to Pro required for $5/day)
  - Policy validates approval policy (cannot auto-approve regulated domain actions)
- Changes applied:
  - Agent workspace updated (goals.md, context.md)
  - Budget limits adjusted in Finance Service
  - Approval policies updated in Governance Service
  - Customer notified: "Changes applied. Agent will use new settings immediately."

**UI Components:**
- Settings form: Same UI as Stage 3.2, but with "Current" vs "New" comparison
- Validation warnings: Inline errors if changes violate constitutional rules
- Cost impact calculator: "New monthly cost: ₹13.5K (was ₹12K)"
- Apply changes button: Confirmation dialog with impact summary

**System Behavior:**
- **Manifest Service (Port 8011)** updates agent configuration (versioned change)
- **Genesis Service** validates changes (if re-certification needed, agent pauses until certified)
- **Finance Service (Port 8007)** updates budget limits, recalculates monthly cost
- **Governance Service (Port 8003)** updates approval policies (PDP rules refreshed)
- **Audit Service (Port 8010)** logs configuration change (correlation_id, change_diff, customer_id)

**Exit Criteria:** Configuration changes applied, agent continues with new settings

---

#### 6.4 Interrupt Agent (Emergency Stop or Pause)
**User Goal:** Stop agent immediately (critical issue, incorrect output, budget overrun)

**User Actions:**
- Click "Interrupt Agent" button (dashboard or mobile app quick action)
- Select interrupt reason:
  - **Emergency stop:** Agent producing incorrect outputs (e.g., HIPAA violation detected)
  - **Pause for reconfiguration:** Need to update goals before agent continues
  - **Budget overrun:** Agent hit 100% daily budget, need to review before increasing
  - **Scheduled maintenance:** Platform maintenance window, agent paused temporarily
- Confirm interrupt: "Are you sure? Agent will pause safely. Current work preserved for resume."
- System interrupts agent:
  - Current Skill execution paused safely (checkpoint created at last completed sub-task)
  - Agent marked as "Interrupted" (status indicator changes to 🟡)
  - Pending approval requests paused (not cancelled, will resume when agent resumes)
  - Agent workspace fully preserved (no data loss, resume from exact checkpoint)
  - Draft work saved: Any in-progress outputs saved as drafts (not published/sent)
- Customer reviews interrupt reason, makes adjustments, resumes when ready

**UI Components:**
- Interrupt button: Red, prominent, requires 2-click confirmation (prevent accidental clicks)
- Interrupt reason modal: Radio buttons with explanation tooltips
- Confirmation dialog: "Agent will stop immediately. Current task: [task_name] will be paused."
- Resume workflow: After interrupt, "Resume Agent" button appears (with validation checks)

**System Behavior:**
- **Agent Execution Service (Port 8002)** receives interrupt signal, pauses Temporal workflow
- **Governance Service (Port 8003)** cancels pending approvals (emits cancellation events)
- **Audit Service (Port 8010)** logs interrupt (correlation_id, interrupt_reason, customer_id, rollback_status)
- **Finance Service (Port 8007)** pauses cost accumulation (agent inactive)

**Exit Criteria:** Agent interrupted, customer informed, safe state preserved

---

#### 6.5 View Plan Limits vs Actual Consumption
**User Goal:** Track resource usage, avoid surprise costs, optimize agent efficiency

**User Actions:**
- Navigate to "Usage & Billing" tab (dashboard sidebar)
- View consumption dashboard:
  - **Query budget:** $0.85/$1.00 daily (85%, yellow warning), trend chart (7-day history)
  - **Agent active hours:** 6.2 hours today (76% active time), idle time 1.8 hours
  - **Skills executed:** 47 today (avg 7.5/hour), top Skills by frequency
  - **Integration API calls:** WordPress 12 writes, Mailchimp 5 reads, Google Analytics 8 reads
  - **Storage usage:** 120 MB (agent workspace), 3.2 GB (deliverables archive)
- View plan limits:
  - **Starter Plan (₹12K/month):** $1/day query budget, 1 agent, 3 integrations, 5 GB storage
  - **Current usage:** 85% query budget, 1/1 agents, 3/3 integrations, 2.4% storage
  - **Upgrade path:** Pro Plan (₹18K/month) = $2/day query budget, 3 agents, unlimited integrations, 50 GB storage
- Set usage alerts:
  - Alert when query budget hits 90% (email + mobile push)
  - Alert when storage hits 80% (weekly digest)
  - Alert when agent idle >2 hours (optimization suggestion)

**UI Components:**
- Usage dashboard: Card grid with donut charts (query budget, storage) + line charts (7-day trends)
- Plan comparison table: Current plan vs upgrade options (side-by-side)
- Alert configuration: Toggle switches per alert type, threshold sliders
- Upgrade CTA: "Upgrade to Pro Plan" button (if limits approaching)

**System Behavior:**
- Real-time usage data from **Finance Service (Port 8007)**: GET /v1/costs/usage/{customer_id}
- Plan limits from **Finance Service**: GET /v1/subscriptions/{customer_id}/plan
- Alerts configured in **Governance Service (Port 8003)**: POST /v1/alerts/configure
- Upgrade flow handled by **Finance Service** (Stripe checkout for plan upgrade)

**Exit Criteria:** Customer understands usage, sets alerts, upgrades if needed

---

#### 6.6 Review Past Performance (Historical Analytics)
**User Goal:** Analyze agent effectiveness over time, identify optimization opportunities

**User Actions:**
- Navigate to "Performance" tab (dashboard sidebar)
- Select time range: Last 7 days (default), 30 days, 90 days, All time
- View performance analytics:
  - **Goals completion rate:** 18/20 goals completed (90%) 🏆 **Expert Badge**
  - **Average quality score:** 4.6/5 stars ⭐⭐⭐⭐⭐ (trend: ↑ 0.2 from last month) 📈 **Rising Star**
  - **Approval latency trend:** 4.8 min avg (improving, was 6.2 min last month) ⚡ **Speed Demon**
  - **Efficiency score:** 92/100 (improving 15% month-over-month) 🎯 **Optimizer**
  - **Top-performing Skills:** "Fact-Check Medical Claims" (100% accuracy) ✅ **Perfection Streak** | "SEO Optimize" (94% success rate) 🚀 **SEO Master**
  - **Growth opportunities:** "32% time waiting for approvals - Enable auto-approve for low-risk actions?" 💡 **Pro Tip**
  - **Milestones achieved:**
    - 🎉 **100 Articles Published** (2025-12-20)
    - 🏅 **5-Star Streak** (10 consecutive 5-star ratings)
    - 🔥 **30-Day Active** (agent working every day this month)
- **No external comparisons:** Focus on your progress, your agent's growth
- **Positive framing:** Celebrate wins, suggest improvements (never criticize)
- Export report: Download PDF summary with badges, milestones, growth charts (shareable on social media)

**UI Components:**
- Time range selector: Dropdown or date picker (presets + custom range)
- Performance KPI grid: Cards with badges, star ratings, emoji indicators (🏆⭐🚀)
- Milestone timeline: Visual timeline showing achievements (badge unlock dates)
- Gamification elements: Progress bars, level indicators ("Level 12 Power User"), streak counters ("30-day streak 🔥")
- Positive reinforcement: Congratulatory messages ("Amazing! You've published 100 articles!")
- Growth suggestions: Actionable tips with emoji icons (💡 "Pro Tip: Enable auto-approve to save 2 hours/week")
- Export button: "Share Your Success" (PDF + social media share buttons for LinkedIn, Twitter)

**System Behavior:**
- Historical data aggregated by **Finance Service (Port 8007)** (efficiency scores) + **Governance Service (Port 8003)** (approval stats)
- Badge/milestone logic in **Learning Service (Port 8005)** (achievement triggers, gamification rules)
- **No external benchmarks:** Analytics compare customer's current vs past performance only (self-improvement focus)
- Positive framing engine: Convert metrics to positive language ("92% efficiency" not "8% waste", "improving 15%" not "was 15% worse")
- PDF export generated server-side (Puppeteer with badge graphics, milestone timeline, social media-ready format)

**Exit Criteria:** Customer reviews performance, identifies improvements, shares report

---

### **Stage 7: Subscription Management & Lifecycle**

#### 7.1 Trial-to-Paid Conversion (Day 7 Decision)
**User Goal:** Decide whether to subscribe after 7-day trial

**User Actions:**
- Receive notification: "Your 7-day trial ends tomorrow. Keep your agent?"
- Review trial summary:
  - **Work completed:** 5 blog articles published, 12 social media posts, 3 email campaigns
  - **Quality score:** 4.8/5 stars (you rated agent highly)
  - **Cost preview:** ₹12K/month (Starter Plan), first month prorated (₹10K for 25 days)
  - **Trial deliverables:** You keep all 5 articles + posts + campaigns (even if you cancel)
- Make decision:
  - **Subscribe:** Enter payment method (Stripe/Razorpay), start paid subscription
  - **Cancel:** Keep all trial deliverables, agent deprovisioned, no charge
- If subscribe: Payment processed, agent continues seamlessly (no re-setup required)
- **No trial extensions:** 7-day limit is strict (no extensions, no exceptions)

**UI Components:**
- Trial expiry modal: Appears 24 hours before trial ends (mobile + web)
- Trial summary dashboard: Work completed, quality score, cost preview
- 2-button decision: Subscribe (green, prominent) | Cancel (gray, secondary)
- Trial countdown: "Trial ends in 23 hours 45 minutes" (live countdown)
- Payment form: Stripe embedded checkout (credit card, UPI, net banking)

**System Behavior:**
- **Finance Service (Port 8007)** triggers trial expiry workflow (Temporal scheduled task)
- If subscribe: Stripe payment processed, subscription status = active, agent continues
- If cancel: Agent deprovisioned (soft delete, workspace archived for 30 days), deliverables preserved permanently
- **Strict 7-day limit:** No extension logic, no Platform Governor override (trial ends at day 7, 11:59 PM)
- **Audit Service (Port 8010)** logs decision (trial_conversion_decision, customer_id, outcome, timestamp)

**Exit Criteria:** Customer subscribed (paid), extended trial, or cancelled

---

#### 7.2 Subscription Upgrades/Downgrades
**User Goal:** Change plan (more agents, higher budget, more integrations)

**User Actions:**
- Navigate to "Subscription" tab
- View current plan: Starter (₹12K/month), usage (85% query budget, 1/1 agents)
- Compare plans:
  - **Starter:** ₹12K/month, $1/day budget, 1 agent, 3 integrations
  - **Pro:** ₹18K/month, $2/day budget, 3 agents, unlimited integrations
  - **Enterprise:** ₹30K/month, $5/day budget, 10 agents, custom features
- Select upgrade: "Upgrade to Pro Plan"
- Confirm upgrade: "Your new plan starts immediately. Prorated charge: ₹4K for remaining 20 days."
- Payment processed, plan upgraded, agent budget increased automatically

**UI Components:**
- Plan comparison table: Feature matrix (side-by-side)
- Upgrade CTA: "Upgrade Now" button per plan
- Proration calculator: "Pay ₹X today, then ₹Y/month starting [date]"

**System Behavior:**
- **Finance Service (Port 8007)** handles plan upgrade (Stripe subscription update)
- Proration calculated: (new_plan_price - old_plan_price) × (days_remaining / 30)
- Agent budget updated immediately (no re-deployment needed)

**Exit Criteria:** Customer upgraded/downgraded, new plan active

---

#### 7.3 Agent/Team Version Upgrades
**User Goal:** Get latest agent/team features and improvements when new versions released

**User Actions:**
- Receive notification: "Healthcare Content Writer v2.0 is now available! +3 new Skills, improved quality"
- View version comparison:
  - **Current version:** v1.2 (Genesis-certified 2025-11-15)
  - **New version:** v2.0 (Genesis-certified 2026-01-05)
  - **New features:**
    - New Skill: "Generate Infographics from Article" (visual content)
    - New Skill: "Optimize for Voice Search" (Alexa, Google Assistant)
    - New Skill: "Multi-language Translation" (Spanish, Hindi support)
  - **Improvements:**
    - 15% faster article generation (query optimization)
    - 98% fact-check accuracy (was 95%)
    - Enhanced HIPAA compliance (FDA guidelines updated)
  - **Pricing gap:** +₹2K/month (₹12K → ₹14K for v2.0)
- Make upgrade decision:
  - **Upgrade now:** Pay ₹2K/month extra, get v2.0 immediately after setup
  - **Stay on v1.2:** Continue with current version (no price increase)
  - **Schedule upgrade:** Upgrade at end of current billing cycle
- If upgrade now:
  - Payment processed (prorated ₹1.3K for remaining 20 days)
  - Complete mini setup wizard (5 min):
    1. Review new Skills: Enable/disable each new Skill
    2. Update goal completion criteria: Use new Skills in workflow?
    3. Test new features: Generate 1 sample with new Skills (synthetic data)
    4. Approve upgrade: "Activate v2.0 for my agent"
  - Agent upgraded seamlessly (no downtime, workspace preserved)
  - New Skills available immediately

**UI Components:**
- Version notification banner: Prominent on dashboard, dismissible
- Version comparison table: Side-by-side (Current | New) with feature diff
- Pricing calculator: "New monthly cost: ₹14K (was ₹12K), effective immediately"
- Upgrade CTA: "Upgrade to v2.0 Now" (primary button) | "Maybe Later" (secondary)
- Mini setup wizard: 3-step flow (Review Skills | Update Criteria | Test | Approve)

**System Behavior:**
- **Manifest Service (Port 8011)** tracks agent versions (semantic versioning: major.minor.patch)
- Version eligibility: All customers with v1.x automatically eligible for v2.0 (no gating)
- **Finance Service (Port 8007)** calculates pricing gap, prorates for current billing cycle
- Payment processed via Stripe (immediate charge for proration)
- **Agent Creation Service (Port 8001)** provisions new agent instance (v2.0) with workspace migration
- **Genesis** certifies new version (6-month recertification cycle, new Job/Skills validated)
- Benefits passed ASAP: No billing cycle wait, upgrade activates immediately after payment + setup
- Major version announcements: Marketplace banner, email to all eligible customers, in-app notification

**Constitutional Alignment:**
- **Versioning governance:** Major updates (v1→v2) require customer opt-in + payment
- **Minor updates:** Auto-applied (v2.0→v2.1) for security/bug fixes (no customer action, no price change)
- **Backward compatibility:** v1.x agents supported for 12 months after v2.0 release (graceful sunset)
- **Workspace preservation:** Upgrade preserves all agent state, goals, access, audit trail (zero data loss)

**Exit Criteria:** Customer upgraded to latest version, new Skills active, no service interruption

---

## 🚨 Gap Analysis & Solutions

### **GAP-1: Onboarding Flow Not Defined in Constitutional Design**
**Current State:** Constitutional design focuses on approval workflows, not customer onboarding
**Impact:** No clear guidance on first-time customer experience (FTUX)

**Solution:**
- **Define in:** New YAML `customer_onboarding_flow.yml` in main/Foundation/template/
- **Specification:**
  ```yaml
  onboarding_stages:
    - welcome_screen: "Welcome to WAOOAW, [customer_name]!"
    - integration_setup: "Connect WordPress, Mailchimp (optional, skip allowed)"
    - goal_setting_simplified: "What should your agent accomplish? (3 goals max)"
    - approval_settings_review: "You'll approve external actions via mobile push"
    - mobile_app_install: "Download mobile app for approvals on-the-go"
  
  constitutional_alignment:
    - onboarding_does_not_execute: "No agent actions during onboarding (read-only)"
    - skip_allowed: "Customer can skip all steps, revisit later in settings"
    - audit_logged: "Onboarding completion logged in SYSTEM_AUDIT"
  ```
- **Implementation:** CP backend (FastAPI) + frontend (React wizard)

---

### **GAP-2: Goal Configuration Interface Not Specified**
**Current State:** Constitution defines Jobs/Skills but not how customers configure goals
**Impact:** Unclear UX for translating customer intent → agent goals

**Solution:**
- **Define in:** Extend `main/Foundation/contracts/data_contracts.yml` with `customer_goal_schema`
- **Specification:**
  ```yaml
  customer_goal_schema:
    goal_id: {type: uuid}
    customer_id: {type: uuid, references: customers.customer_id}
    agent_id: {type: uuid, references: agents.agent_id}
    goal_statement: {type: string, max_length: 500, required: true}
    success_criteria: {type: array, items: string, max_items: 5}
    constraints: {type: array, items: string, max_items: 10}
    deliverables: {type: array, items: string, max_items: 5}
    timeline: {type: string, enum: [immediate, weekly, monthly]}
    priority: {type: string, enum: [P0, P1, P2, P3]}
    genesis_validated: {type: boolean, default: false}
  ```
- **Implementation:** CP Settings page, goal form wizard, Genesis validation API

---

### **GAP-3: Agent/Team Setup Wizard Definition Missing**
**Current State:** Constitutional design has no concept of pre-built setup workflow
**Impact:** Customers may misconfigure agents, missing critical context/access/criteria

**Solution:**
- **Define in:** New component `component_agent_setup_wizard.yml`
- **Specification:**
  ```yaml
  agent_setup_wizard:
    purpose: "Pre-built setup workflow for goal setting, access provisioning, completion criteria"
    
    wizard_steps:
      - business_background:
          fields: [industry_vertical, target_audience, brand_voice, differentiators]
          sla_time_minutes: 3
      - access_provisioning:
          integrations: [wordpress, mailchimp, google_analytics, crm]
          oauth_preferred: true
          credential_encryption: "HashiCorp Vault"
          sla_time_minutes: 5
      - goal_completion_criteria:
          fields: [acceptance_criteria, quality_gates, delivery_slas, success_metrics]
          template_library: true
          sla_time_minutes: 4
      - communication_preferences:
          fields: [notification_frequency, escalation_thresholds, approval_preferences]
          sla_time_minutes: 2
      - conformity_validation:
          agent_summarizes_setup: true
          customer_reviews_summary: true
          sample_deliverable_generated: true
          customer_rates_sample: "5-star rating (≥4 stars to proceed)"
          sla_time_minutes: 3
    
    total_sla_minutes: 17
    sla_notification_threshold: 20
    
    pass_criteria:
      - all_steps_completed: true
      - sample_rated_4_plus_stars: true
      - genesis_validates_setup: true
    
    trial_mode_enforcement:
      - sample_uses_synthetic_data: true
      - no_real_integrations_executed: "OAuth validation only, no writes"
      - cost: "$0 (platform absorbs)"
  ```
- **Implementation:** Agent Creation Service (Port 8001) wizard workflow, CP UI multi-step form

---

### **GAP-4: Go-Live Declaration Not Defined as Governance Gate**
**Current State:** No explicit customer approval for production activation
**Impact:** Agent may go live without customer readiness confirmation

**Solution:**
- **Define in:** Extend `governance_protocols.yaml` with `go_live_approval_gate`
- **Specification:**
  ```yaml
  go_live_approval_gate:
    trigger: "Customer clicks 'Activate Agent for Production'"
    
    required_checks:
      - conformity_test_passed: true
      - goals_validated_by_genesis: true
      - integrations_connected: true
      - mobile_app_installed: "Recommended, not required"
      - customer_acknowledges_cost: "Trial ends, real budget enforced"
    
    approval_workflow:
      - customer_submits_go_live_request: "CP → Governance Service POST /v1/go-live"
      - policy_service_validates_trial_mode_disabled: "PDP evaluates production policies"
      - genesis_verifies_agent_certification: "Agent Genesis-certified, not deprecated"
      - governor_approves: "Customer confirms go-live in audit trail"
      - agent_activated: "Policy Service disables trial mode, Agent Execution switches to production"
    
    constitutional_alignment:
      - explicit_customer_approval: "Go-live requires attested approval (audit logged)"
      - rollback_path_exists: "Customer can interrupt agent post-go-live"
  ```
- **Implementation:** Governance Service (Port 8003) go-live approval endpoint, CP go-live wizard

---

### **GAP-5: Interrupt/Reconfigure Flow Not Specified**
**Current State:** Constitutional design allows suspension but not customer-initiated interrupt
**Impact:** Customer has no emergency stop button (safety issue)

**Solution:**
- **Define in:** Extend `main/Foundation/manager_agent_charter.md` with `customer_interrupt_protocol`
- **Specification:**
  ```yaml
  customer_interrupt_protocol:
    trigger: "Customer clicks 'Interrupt Agent' button"
    
    interrupt_types:
      - emergency_stop: "Critical issue, stop immediately (rollback current task)"
      - pause_for_reconfiguration: "Customer needs to adjust goals/settings"
      - budget_overrun_review: "Agent hit 100%, customer reviewing"
      - scheduled_maintenance: "Platform maintenance window"
    
    interrupt_workflow:
      step_1: "Customer selects interrupt reason (CP UI)"
      step_2: "CP → Agent Execution Service POST /v1/agents/{id}/interrupt"
      step_3: "Agent Execution pauses Temporal workflow safely (checkpoint at last completed sub-task)"
      step_4: "Governance Service pauses pending approvals (not cancelled, resumable)"
      step_5: "Draft work saved (in-progress outputs saved as drafts, not published)"
      step_6: "Audit Service logs interrupt (correlation_id, reason, customer_id, checkpoint_id)"
      step_7: "Agent status → Interrupted (🟡), customer notified"
    
    pause_safely_guarantee:
      - no_data_loss: "All agent state preserved (workspace, goals, context)"
      - no_partial_execution: "Current sub-task completes before pause (atomic checkpoint)"
      - draft_preservation: "In-progress outputs saved as drafts (customer can review/publish later)"
      - approval_queue_preserved: "Pending approvals paused (will resume when agent resumes)"
    
    resume_workflow:
      - customer_fixes_issue: "Adjust goals, increase budget, etc."
      - customer_clicks_resume: "CP → Agent Execution Service POST /v1/agents/{id}/resume"
      - genesis_validates_changes: "If significant changes, re-certification required"
      - agent_resumes: "Temporal workflow resumed, agent continues from safe checkpoint"
  ```
- **Implementation:** Agent Execution Service (Port 8002) interrupt/resume endpoints, CP UI interrupt button (prominent, red)

---

### **GAP-6: Plan Limits Not Explicitly Defined**
**Current State:** Constitutional design has query budget ($1/day) but no comprehensive plan limits
**Impact:** Unclear what "Starter vs Pro vs Enterprise" plans include

**Solution:**
- **Define in:** Extend `main/Foundation/template/financials.yml` with `subscription_plan_limits`
- **Specification:**
  ```yaml
  subscription_plan_limits:
    starter:
      monthly_price_inr: 12000
      query_budget_daily_usd: 1.00
      agents_max: 1
      integrations_max: 3
      storage_gb: 5
      approval_latency_sla_minutes: 10
      support: "Email (24-hour response)"
    
    pro:
      monthly_price_inr: 18000
      query_budget_daily_usd: 2.00
      agents_max: 3
      integrations_max: unlimited
      storage_gb: 50
      approval_latency_sla_minutes: 5
      support: "Email + Chat (8-hour response)"
    
    enterprise:
      monthly_price_inr: 30000
      query_budget_daily_usd: 5.00
      agents_max: 10
      integrations_max: unlimited
      storage_gb: 500
      approval_latency_sla_minutes: 2
      support: "Dedicated account manager + 24/7 phone"
  ```
- **Implementation:** Finance Service (Port 8007) plan limits enforcement, CP UI plan comparison table

---

### **GAP-7: Gamified Performance Analytics Not Architected**
**Current State:** Constitutional design logs audit trail but no gamified positive analytics
**Impact:** Customer cannot celebrate achievements, track growth, earn badges

**Solution:**
- **Define in:** New service responsibility in `ARCHITECTURE_PROPOSAL.md`
- **Service:** Learning Service (Port 8005) extended with gamification engine
- **Specification:**
  ```yaml
  gamification_engine:
    data_sources:
      - audit_service_logs: "All agent actions, goals completed"
      - finance_service_costs: "Efficiency scores, optimization wins"
      - governance_service_approvals: "Approval latencies, approval patterns"
    
    gamification_elements:
      - badges:
          expert_badge: "90%+ goal completion rate (unlock at 18/20 goals)"
          rising_star: "Quality score improving 2+ months in a row"
          speed_demon: "Approval latency <5 min average"
          optimizer: "Efficiency improving 10%+ month-over-month"
          perfection_streak: "100% accuracy on any Skill"
          seo_master: "90%+ success rate on SEO Skill"
      
      - milestones:
          milestone_100_articles: "100 articles published (celebration modal)"
          milestone_5_star_streak: "10 consecutive 5-star ratings (confetti animation)"
          milestone_30_day_active: "Agent working every day for 30 days (trophy emoji)"
      
      - progress_indicators:
          level_system: "Power User levels 1-20 (based on total goals completed)"
          streak_counter: "Days active streak (🔥 emoji, resets if agent idle >48 hours)"
          progress_bars: "Goals this week, month, quarter (visual % complete)"
      
      - positive_framing:
          convert_negatives_to_positives: true
          example_1: "92% efficiency (not 8% waste)"
          example_2: "Improving 15% (not was 15% worse)"
          example_3: "Growth opportunity (not bottleneck)"
      
      - no_external_comparisons:
          industry_benchmarks: false
          platform_averages: false
          peer_comparisons: false
          focus: "Self-improvement (current vs past performance only)"
    
    api_endpoints:
      - GET /v1/gamification/{customer_id}/badges
      - GET /v1/gamification/{customer_id}/milestones
      - GET /v1/gamification/{customer_id}/level
      - POST /v1/gamification/{customer_id}/export (PDF with badges, social media share)
  ```
- **Implementation:** Learning Service gamification module, CP Performance tab with badges/milestones UI

---

## 📊 User Journey Metrics (Success Criteria)

### **Visitor → Customer Conversion (Stages 1-2)**
- **Browse to trial start:** <10 minutes median time
- **Trial start conversion rate:** >40% (4 in 10 visitors start trial)
- **Social login adoption:** >70% (Google/GitHub preferred over email)

### **Onboarding Completion (Stage 3)**
- **Onboarding completion rate:** >80% (8 in 10 customers complete wizard)
- **Time to first goal defined:** <15 minutes
- **Mobile app install rate:** >60% (critical for approvals)

### **Conformity Test Success (Stage 4)**
- **First-time pass rate:** >70% (7 in 10 agents pass without adjustments)
- **Re-run rate:** <20% (2 in 10 need adjustments + re-test)
- **Go-live approval rate:** >95% (9.5 in 10 approve after conformity test)

### **Go-Live to Active Operations (Stages 5-6)**
- **Go-live to first approval:** <30 minutes (agent starts working quickly)
- **Approval response latency:** <5 minutes median (constitutional requirement)
- **Interrupt rate:** <5% (0.5 in 10 customers interrupt agent in first week)

### **Trial-to-Paid Conversion (Stage 7)**
- **Trial-to-paid conversion:** >50% (5 in 10 customers subscribe after trial)
- **Subscribe immediately rate:** >40% (4 in 10 subscribe before trial ends)
- **Cancel rate:** <50% (5 in 10 cancel, but keep deliverables, no trial extensions)

---

## 🔗 Cross-References (Constitutional Alignment)

**Related Documents:**
- [main/Foundation.md](main/Foundation.md) - Constitutional governance system
- [main/Foundation/governor_agent_charter.md](main/Foundation/governor_agent_charter.md) - Governor approval authority
- [main/Foundation/genesis_foundational_governance_agent.md](main/Foundation/genesis_foundational_governance_agent.md) - Job/Skill certification
- [main/Foundation/policies/mobile_ux_requirements.yml](main/Foundation/policies/mobile_ux_requirements.yml) - Mobile app MVP features
- [ARCHITECTURE_PROPOSAL.md](ARCHITECTURE_PROPOSAL.md) - 13 microservices technical specification
- [main/Foundation/template/financials.yml](main/Foundation/template/financials.yml) - Finance component specification

**API Dependencies:**
- **Manifest Service (Port 8011):** Agent catalog, Job/Skill registry
- **Finance Service (Port 8007):** Subscription management, cost tracking, plan limits
- **Governance Service (Port 8003):** Approval workflows, precedent seeds, veto handling
- **Policy Service (Port 8013):** Trial mode enforcement, production policies
- **Agent Execution Service (Port 8002):** Conformity test, interrupt/resume, real-time actions
- **Audit Service (Port 8010):** Audit trail logging, correlation_id tracking

---

## ✅ Next Steps (Pending Your Review)

1. **Review Gap Solutions:** Validate proposed solutions for 7 identified gaps
2. **Approve User Journey:** Confirm this document as "CP User Journey v1.0"
3. **Prioritize Implementation:** Which stages to implement first? (Recommend: Stages 1-2-3 as MVP)
4. **Define Wireframes:** Request detailed wireframes for specific screens (e.g., Agent Dashboard, Approval Request, Goal Configuration)
5. **API Contract Definition:** Define REST API contracts for each CP → backend interaction

---

**Clarifications Resolved:**

1. ✅ **Setup Wizard (not separate conformity test):** Setup wizard is pre-built with every agent/team, includes goal setting, access provisioning, business background, completion criteria. Time SLA: 10-15 min (notify if >20 min).
2. ✅ **Plan Upgrades:** Subscription tier changes (Starter→Pro) take effect immediately. Agent/Team version upgrades (v1→v2) also immediate after payment + mini setup (no billing cycle wait, pass benefits ASAP).
3. ✅ **Interrupt Rollback:** Pause safely (checkpoint at last completed sub-task, no data loss, draft work preserved, resume from exact checkpoint).
4. ✅ **Trial Extension:** Strict no (7-day limit, no extensions, no exceptions).
5. ✅ **Past Performance:** No external comparisons (no industry/platform benchmarks). Focus on positive gamification (badges, stars, milestones, self-improvement).

**Document Status:** 🟡 **DRAFT - AWAITING YOUR REVIEW & APPROVAL**
