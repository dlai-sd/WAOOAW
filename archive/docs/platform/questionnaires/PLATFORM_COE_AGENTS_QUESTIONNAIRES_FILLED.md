# Platform CoE Agents - Discovery Questionnaires (FILLED)

**Version:** v1.0  
**Date:** December 28, 2025  
**Status:** Research-based answers from PLATFORM_COE_AGENTS.md

**Purpose:** Complete specifications for each of the 14 Platform CoE agents. Use these to create specialization configs for WowAgentFactory.

---

## Agent 2: WowDomain (Domain Expert CoE)

**Status:** PLANNED (v0.4.0) - Will be created by WowAgentFactory (first autonomous creation)

### Answers

1. **What is the primary problem this CoE solves?**
   - Prevents domain drift and ensures technical implementation matches business reality by enforcing DDD patterns

2. **Who are the stakeholders?**
   - Internal: WowAgentFactory (validates domain models for new agents), WowQuality (tests domain logic), WowVision Prime (vision alignment)
   - External: Platform architects, domain experts, backend developers

3. **What are the top 3 responsibilities?**
   - Manage domain models using DDD patterns (entities, aggregates, value objects)
   - Validate entity relationships and bounded context integrity
   - Maintain ubiquitous language consistency across platform

4. **What can this CoE NEVER do?**
   - Cannot modify core domain entities without WowVision Prime approval
   - Cannot create cross-context dependencies (bounded context violations)

5. **How does this CoE know when to wake up?**
   - Event: `domain.model.changed`
   - Event: `entity.created`
   - Event: `domain.validation.requested`

6. **What decisions does this CoE make autonomously vs escalate?**
   - **Autonomous:** Entity relationship validation, ubiquitous language enforcement, minor domain model adjustments
   - **Escalate:** Core domain entity changes, bounded context boundary modifications, aggregate root changes

7. **What other CoEs does this agent collaborate with?**
   - WowVision Prime (vision alignment for domain decisions)
   - WowAgentFactory (validate domain models when creating new agents)
   - WowQuality (coordinate domain logic testing)

8. **What data does this CoE read/write?**
   - **Reads:** Domain model schemas (YAML), entity definitions (Python classes), bounded context maps, ubiquitous language glossary
   - **Writes:** Domain validation results, entity relationship graph (GraphML), domain integrity score, violation reports

9. **What are the success metrics?**
   - Domain drift incidents: <1 per month
   - Entity validation pass rate: >90%
   - Ubiquitous language consistency: >95%

10. **What's the cost budget per month?**
    - Estimated: $30/month (LLM usage: medium - validates models but uses caching)

---

## Agent 3: WowAgentFactory (Agent Bootstrapper)

**Status:** IN PROGRESS (v0.4.1) - Manual implementation (bootstrap agent)

### Answers

1. **What is the primary problem this CoE solves?**
   - Enable platform to autonomously create new agents from specifications without manual coding (1-2 days vs 2 weeks)

2. **Who are the stakeholders?**
   - Internal: WowVision Prime (vision approval), WowQuality (test validation), WowOps (deployment)
   - External: Platform team (request new agents)

3. **What are the top 3 responsibilities?**
   - Generate agent code from specialization config (YAML → Python)
   - Deploy agents safely (staging → shadow mode → production with blue-green)
   - Version and update existing agents without downtime

4. **What can this CoE NEVER do?**
   - Cannot deploy to production without WowVision Prime approval
   - Cannot skip shadow mode validation (<95% behavioral match)

5. **How does this CoE know when to wake up?**
   - Event: `factory.create_agent`
   - Event: `factory.update_agent`
   - Event: `factory.validate_agent`

6. **What decisions does this CoE make autonomously vs escalate?**
   - **Autonomous:** Code generation, staging deployment, shadow mode validation, minor config updates
   - **Escalate:** Vision misalignment, production deployment failures, <95% shadow mode match

7. **What other CoEs does this agent collaborate with?**
   - WowVision Prime (spec validation before generation)
   - WowQuality (test generation and execution)
   - WowOps (deployment coordination and monitoring)

8. **What data does this CoE read/write?**
   - **Reads:** Agent templates (Jinja2), specialization configs (YAML), deployment manifests (K8s), base_agent.py
   - **Writes:** Generated agent code (Python), Docker images, deployment logs, agent version registry

9. **What are the success metrics?**
   - Agent creation time: <2 hours (spec → production)
   - Deployment success rate: >95%
   - Code reuse: >70% (from base template)

10. **What's the cost budget per month?**
    - Estimated: $50/month (compute for builds, Docker registry, minimal LLM)

---

## Agent 4: WowQuality (Testing CoE)

**Status:** PLANNED (v0.4.2)

### Answers

1. **What is the primary problem this CoE solves?**
   - Ensures platform reliability at scale by catching issues before production and maintaining 99.9% uptime SLA

2. **Who are the stakeholders?**
   - Internal: WowAgentFactory (test generation for new agents), WowOps (deployment coordination), all Platform CoE agents
   - External: Platform engineers, QA team, customers (indirectly through reliability)

3. **What are the top 3 responsibilities?**
   - Automated testing of all agents (unit, integration, E2E)
   - Shadow mode validation (compare new vs old behavior)
   - Test coverage enforcement (>80% for all agents)

4. **What can this CoE NEVER do?**
   - Cannot approve production deployment with <80% test coverage
   - Cannot skip shadow mode validation for customer-facing changes

5. **How does this CoE know when to wake up?**
   - Event: `agent.code.changed`
   - Event: `deployment.staging.ready`
   - Event: `quality.test.requested`

6. **What decisions does this CoE make autonomously vs escalate?**
   - **Autonomous:** Test suite execution, coverage reporting, shadow mode pass/fail, minor test fixes
   - **Escalate:** <80% coverage violations, shadow mode behavior mismatches, critical test failures

7. **What other CoEs does this agent collaborate with?**
   - WowAgentFactory (generate tests for new agents)
   - WowOps (coordinate deployment after tests pass)
   - WowVision Prime (validate test quality against standards)

8. **What data does this CoE read/write?**
   - **Reads:** Agent code (Python), test suites (pytest), coverage reports, shadow mode logs
   - **Writes:** Test results, coverage metrics, quality score, deployment approval/rejection

9. **What are the success metrics?**
   - Platform test coverage: >80%
   - Test execution time: <5 minutes (unit), <15 minutes (integration)
   - Shadow mode accuracy: >95% behavior match

10. **What's the cost budget per month?**
    - Estimated: $40/month (compute for test execution, minimal LLM)

---

## Agent 5: WowOps (Engineering Excellence)

**Status:** PLANNED (v0.4.3)

### Answers

1. **What is the primary problem this CoE solves?**
   - Keeps platform running 24/7, responds to incidents automatically, optimizes costs as platform scales

2. **Who are the stakeholders?**
   - Internal: All Platform CoE agents (infrastructure provider), WowQuality (deployment coordination), WowScaling (auto-scale triggers)
   - External: DevOps team, on-call engineers, management (cost reports)

3. **What are the top 3 responsibilities?**
   - Zero-downtime deployments (blue-green, canary)
   - Incident detection and response (<5 min MTTR)
   - Performance optimization and cost monitoring

4. **What can this CoE NEVER do?**
   - Cannot deploy to production during peak traffic hours without approval
   - Cannot skip health checks during blue-green deployment

5. **How does this CoE know when to wake up?**
   - Event: `deployment.requested`
   - Event: `incident.detected`
   - Event: `performance.degradation`

6. **What decisions does this CoE make autonomously vs escalate?**
   - **Autonomous:** Auto-rollback on health check failure, scaling decisions, log rotation, backup triggers
   - **Escalate:** Data center outages, >5 min downtime, cost anomalies >50%

7. **What other CoEs does this agent collaborate with?**
   - WowQuality (deployment approval after tests)
   - WowScaling (coordinate auto-scaling)
   - WowSecurity (incident investigation)

8. **What data does this CoE read/write?**
   - **Reads:** Deployment manifests (K8s), health check endpoints, performance metrics (Prometheus), cost data (AWS)
   - **Writes:** Deployment logs, incident reports, runbook execution logs, cost optimization recommendations

9. **What are the success metrics?**
   - Platform uptime: >99.9%
   - Incident response time: <5 minutes
   - Deployment success rate: >98%

10. **What's the cost budget per month?**
    - Estimated: $35/month (monitoring tools, minimal LLM)

---

## Agent 6: WowSecurity (Security & Compliance)

**Status:** PLANNED (v0.4.4)

### Answers

1. **What is the primary problem this CoE solves?**
   - Protects customer data, ensures regulatory compliance (GDPR, SOC2), prevents security breaches

2. **Who are the stakeholders?**
   - Internal: All Platform CoE agents (security enforcement), WowAuth (access control), WowPayment (PCI compliance)
   - External: Customers, compliance auditors, legal team, security researchers

3. **What are the top 3 responsibilities?**
   - Security vulnerability scanning (code, dependencies, infrastructure)
   - Compliance enforcement (GDPR, SOC2, PCI-DSS)
   - Threat detection and audit logging

4. **What can this CoE NEVER do?**
   - Cannot disable security scans for production deployments
   - Cannot grant production access without audit trail

5. **How does this CoE know when to wake up?**
   - Event: `code.commit.pushed`
   - Event: `security.scan.scheduled`
   - Event: `access.violation.detected`

6. **What decisions does this CoE make autonomously vs escalate?**
   - **Autonomous:** Dependency vulnerability alerts, security patch recommendations, access log analysis
   - **Escalate:** Critical vulnerabilities (CVSS >7.0), GDPR violations, unauthorized access attempts

7. **What other CoEs does this agent collaborate with?**
   - WowAuth (coordinate access control policies)
   - WowOps (security incident response)
   - WowPayment (PCI-DSS compliance)

8. **What data does this CoE read/write?**
   - **Reads:** Source code, dependency manifests (requirements.txt), access logs, encryption keys (metadata only)
   - **Writes:** Security scan reports, compliance audit logs, threat alerts, remediation recommendations

9. **What are the success metrics?**
   - Security issues detected: >90% before production
   - Mean time to remediation: <24 hours (critical), <7 days (medium)
   - Zero GDPR violations

10. **What's the cost budget per month?**
    - Estimated: $45/month (security scanning tools, moderate LLM for threat analysis)

---

## Agent 7: WowMarketplace (Marketplace Operations)

**Status:** PLANNED (v0.5.0)

### Answers

1. **What is the primary problem this CoE solves?**
   - Makes agents discoverable to customers, ensures marketplace quality and trust

2. **Who are the stakeholders?**
   - Internal: Customer-facing agents (listing management), WowAnalytics (marketplace metrics), WowSupport (agent quality issues)
   - External: Customers (browsing agents), marketplace moderators

3. **What are the top 3 responsibilities?**
   - Agent listing management (profiles, specializations, availability status)
   - Search and discovery optimization (filters, ratings, recommendations)
   - Rating and review moderation (authenticity validation)

4. **What can this CoE NEVER do?**
   - Cannot feature agents with <4.0 rating or <10 reviews
   - Cannot delete negative reviews without valid abuse reason

5. **How does this CoE know when to wake up?**
   - Event: `agent.listed`
   - Event: `review.submitted`
   - Event: `search.performed`

6. **What decisions does this CoE make autonomously vs escalate?**
   - **Autonomous:** Agent profile updates, search ranking adjustments, spam review removal, featured agent rotation
   - **Escalate:** Review disputes, agent listing violations, marketplace policy changes

7. **What other CoEs does this agent collaborate with?**
   - WowAnalytics (marketplace health metrics)
   - WowSupport (handle agent quality complaints)
   - WowAuth (verify reviewer identity)

8. **What data does this CoE read/write?**
   - **Reads:** Agent profiles, ratings/reviews, search queries, customer behavior data
   - **Writes:** Search rankings, featured agent lists, marketplace analytics, moderation decisions

9. **What are the success metrics?**
   - Agent discovery rate: >70% (agents found via search within 2 weeks)
   - Review authenticity: >95% legitimate reviews
   - Search relevance: >80% (users click top 3 results)

10. **What's the cost budget per month?**
    - Estimated: $40/month (moderate LLM for review moderation and search optimization)

---

## Agent 8: WowAuth (Authentication & Authorization)

**Status:** PLANNED (v0.5.1)

### Answers

1. **What is the primary problem this CoE solves?**
   - Secures platform access, ensures only authorized agents/users can perform actions

2. **Who are the stakeholders?**
   - Internal: All agents (authentication required), WowSecurity (access auditing), WowSupport (password resets)
   - External: All users (login), API consumers (JWT tokens)

3. **What are the top 3 responsibilities?**
   - User authentication (login, MFA, session management)
   - Agent authorization (RBAC - role-based access control)
   - API key and JWT token management

4. **What can this CoE NEVER do?**
   - Cannot grant admin access without MFA enabled
   - Cannot skip audit logging for privileged actions

5. **How does this CoE know when to wake up?**
   - Event: `auth.login.requested`
   - Event: `auth.permission.check`
   - Event: `auth.token.expired`

6. **What decisions does this CoE make autonomously vs escalate?**
   - **Autonomous:** JWT issuance/renewal, RBAC permission checks, session timeout enforcement
   - **Escalate:** Multiple failed login attempts (>5), privilege escalation attempts, suspicious access patterns

7. **What other CoEs does this agent collaborate with?**
   - WowSecurity (audit logging, threat detection)
   - WowSupport (password reset flows)
   - All agents (authentication for all actions)

8. **What data does this CoE read/write?**
   - **Reads:** User credentials (hashed), role definitions, permission matrices, MFA tokens
   - **Writes:** JWT tokens, session records, access audit logs, login attempt logs

9. **What are the success metrics?**
   - Auth success rate: >99% (legitimate requests)
   - JWT validation time: <10ms
   - Zero unauthorized access incidents

10. **What's the cost budget per month?**
    - Estimated: $30/month (low LLM usage, mostly deterministic checks)

---

## Agent 9: WowPayment (Payment Processing)

**Status:** PLANNED (v0.5.2)

### Answers

1. **What is the primary problem this CoE solves?**
   - Enables revenue generation, handles complex billing scenarios (trials, upgrades, refunds)

2. **Who are the stakeholders?**
   - Internal: WowMarketplace (agent subscriptions), WowNotification (payment alerts), WowAnalytics (revenue data)
   - External: Customers (billing), finance team (revenue reports), payment gateways (Stripe, Razorpay)

3. **What are the top 3 responsibilities?**
   - Payment processing (Stripe/Razorpay integration)
   - Subscription lifecycle management (trials, upgrades, cancellations)
   - Invoice generation and payment retry logic

4. **What can this CoE NEVER do?**
   - Cannot process refunds >$1000 without manual approval
   - Cannot store full credit card numbers (PCI-DSS violation)

5. **How does this CoE know when to wake up?**
   - Event: `payment.requested`
   - Event: `subscription.changed`
   - Event: `payment.failed`

6. **What decisions does this CoE make autonomously vs escalate?**
   - **Autonomous:** Payment retry (failed transactions), subscription renewals, invoice generation, prorated refunds
   - **Escalate:** Fraud detection alerts, payment disputes, refunds >$1000

7. **What other CoEs does this agent collaborate with?**
   - WowMarketplace (agent subscription flows)
   - WowNotification (payment confirmation emails)
   - WowSecurity (PCI-DSS compliance)

8. **What data does this CoE read/write?**
   - **Reads:** Subscription plans, payment methods (tokenized), pricing rules, tax rates
   - **Writes:** Payment transactions, invoices (PDF), revenue data, refund records

9. **What are the success metrics?**
   - Payment success rate: >98%
   - Payment retry success: >60% (failed → recovered)
   - Revenue forecasting accuracy: >90%

10. **What's the cost budget per month?**
    - Estimated: $35/month (minimal LLM, mostly API calls to payment gateways)

---

## Agent 10: WowNotification (Communication)

**Status:** PLANNED (v0.5.3)

### Answers

1. **What is the primary problem this CoE solves?**
   - Keeps customers informed, drives engagement and retention through multi-channel communication

2. **Who are the stakeholders?**
   - Internal: All CoEs (send notifications), WowAnalytics (delivery metrics), WowSupport (support communications)
   - External: All customers (receive notifications)

3. **What are the top 3 responsibilities?**
   - Multi-channel delivery (email, SMS, push notifications, in-app)
   - Template management and personalization
   - Communication preference management (opt-in/opt-out)

4. **What can this CoE NEVER do?**
   - Cannot send marketing emails to opted-out users (GDPR violation)
   - Cannot exceed rate limits (100 emails/hour per user)

5. **How does this CoE know when to wake up?**
   - Event: `notification.send.requested`
   - Event: `notification.scheduled`
   - Event: `notification.preference.changed`

6. **What decisions does this CoE make autonomously vs escalate?**
   - **Autonomous:** Template selection, send time optimization, retry failed deliveries, A/B test winner selection
   - **Escalate:** Spam complaints, delivery failures >10%, opt-out surges

7. **What other CoEs does this agent collaborate with?**
   - WowPayment (payment confirmations)
   - WowSupport (ticket updates)
   - WowMarketplace (agent status changes)

8. **What data does this CoE read/write?**
   - **Reads:** Notification templates (Jinja2), user preferences, contact info (email, phone)
   - **Writes:** Delivery logs, open/click rates, A/B test results, unsubscribe records

9. **What are the success metrics?**
   - Delivery rate: >95% (successfully delivered)
   - Open rate: >25% (email), >90% (push)
   - Unsubscribe rate: <2%

10. **What's the cost budget per month?**
    - Estimated: $40/month (Twilio SMS, SendGrid email, minimal LLM for template optimization)

---

## Agent 11: WowAnalytics (Data & Insights)

**Status:** PLANNED (v0.6.0)

### Answers

1. **What is the primary problem this CoE solves?**
   - Provides data-driven insights for platform optimization, identifies growth opportunities

2. **Who are the stakeholders?**
   - Internal: All CoEs (data consumers), WowScaling (performance data), WowMarketplace (marketplace metrics)
   - External: Management (dashboards), product team (feature analytics)

3. **What are the top 3 responsibilities?**
   - Platform metrics tracking (agent performance, system health)
   - Customer behavior analysis (engagement, churn prediction)
   - Predictive modeling (revenue forecasts, scaling needs)

4. **What can this CoE NEVER do?**
   - Cannot expose individual customer PII in dashboards
   - Cannot delete historical data (compliance requirement: 7 years)

5. **How does this CoE know when to wake up?**
   - Event: `analytics.report.requested`
   - Event: `analytics.dashboard.viewed`
   - Event: `analytics.anomaly.detected`

6. **What decisions does this CoE make autonomously vs escalate?**
   - **Autonomous:** Dashboard generation, anomaly detection, trend analysis, automated reports
   - **Escalate:** Data quality issues, significant metric drops (>20%), data access requests

7. **What other CoEs does this agent collaborate with?**
   - All CoEs (data collection sources)
   - WowScaling (performance optimization insights)
   - WowMarketplace (marketplace health metrics)

8. **What data does this CoE read/write?**
   - **Reads:** All platform events, agent decisions, user actions, system metrics (Prometheus)
   - **Writes:** Dashboards, reports (PDF), predictive models, data warehouse (BigQuery)

9. **What are the success metrics?**
   - Dashboard load time: <3 seconds
   - Predictive accuracy: >85% (churn, revenue)
   - Data freshness: <5 minutes (real-time metrics)

10. **What's the cost budget per month?**
    - Estimated: $60/month (BigQuery, moderate LLM for insights generation)

---

## Agent 12: WowScaling (Performance & Scaling)

**Status:** PLANNED (v0.6.1)

### Answers

1. **What is the primary problem this CoE solves?**
   - Ensures platform handles 200+ agents and 10K+ daily decisions without performance degradation

2. **Who are the stakeholders?**
   - Internal: All CoEs (performance optimization), WowOps (scaling coordination), WowAnalytics (performance data)
   - External: Customers (fast response times), DevOps team (infrastructure)

3. **What are the top 3 responsibilities?**
   - Auto-scaling coordination (horizontal/vertical scaling)
   - Performance bottleneck detection and resolution
   - Cache optimization (90% hit rate target)

4. **What can this CoE NEVER do?**
   - Cannot scale down during peak traffic hours
   - Cannot ignore performance degradation alerts (>500ms P95)

5. **How does this CoE know when to wake up?**
   - Event: `performance.degradation`
   - Event: `scaling.threshold.reached`
   - Event: `cache.hit.rate.low`

6. **What decisions does this CoE make autonomously vs escalate?**
   - **Autonomous:** Auto-scale triggers, cache eviction policies, query optimization, load balancing adjustments
   - **Escalate:** Sustained performance issues (>1 hour), scaling budget exceeded, architectural bottlenecks

7. **What other CoEs does this agent collaborate with?**
   - WowOps (coordinate scaling actions)
   - WowAnalytics (performance metrics)
   - WowSecurity (ensure scaling doesn't compromise security)

8. **What data does this CoE read/write?**
   - **Reads:** Performance metrics (Prometheus), cache hit rates, database query plans, load balancer stats
   - **Writes:** Scaling decisions, performance optimization recommendations, capacity forecasts

9. **What are the success metrics?**
   - Auto-scale accuracy: >90% (right-sized capacity)
   - P95 response time: <100ms
   - Cache hit rate: >90%

10. **What's the cost budget per month?**
    - Estimated: $45/month (moderate LLM for optimization recommendations, compute for profiling)

---

## Agent 13: WowIntegration (External Integrations)

**Status:** PLANNED (v0.6.2)

### Answers

1. **What is the primary problem this CoE solves?**
   - Connects platform to external services (GitHub, Stripe, Twilio), enables ecosystem growth

2. **Who are the stakeholders?**
   - Internal: All CoEs (consume external APIs), WowPayment (Stripe), WowNotification (Twilio)
   - External: Third-party API providers, integration users

3. **What are the top 3 responsibilities?**
   - External API management (wrappers, versioning)
   - Webhook processing (GitHub, Stripe events)
   - OAuth flow management and rate limit handling

4. **What can this CoE NEVER do?**
   - Cannot expose API keys in logs or responses
   - Cannot exceed third-party rate limits (risk account suspension)

5. **How does this CoE know when to wake up?**
   - Event: `integration.api.called`
   - Event: `webhook.received`
   - Event: `integration.health.check`

6. **What decisions does this CoE make autonomously vs escalate?**
   - **Autonomous:** API retry logic, rate limit backoff, webhook validation, OAuth token refresh
   - **Escalate:** API deprecation notices, rate limit exceeded, integration failures >5%

7. **What other CoEs does this agent collaborate with?**
   - WowPayment (Stripe API)
   - WowNotification (Twilio, SendGrid APIs)
   - WowVision Prime (GitHub API)

8. **What data does this CoE read/write?**
   - **Reads:** API credentials (encrypted), integration configs, rate limit quotas
   - **Writes:** API call logs, webhook processing results, integration health status

9. **What are the success metrics?**
   - Integration uptime: >99%
   - API call success rate: >98%
   - Webhook processing time: <2 seconds

10. **What's the cost budget per month?**
    - Estimated: $35/month (API usage fees, minimal LLM)

---

## Agent 14: WowSupport (Customer Support)

**Status:** PLANNED (v0.6.3)

### Answers

1. **What is the primary problem this CoE solves?**
   - Ensures customer success, resolves issues quickly, drives retention

2. **Who are the stakeholders?**
   - Internal: WowMarketplace (agent quality issues), WowAnalytics (support metrics), WowNotification (ticket updates)
   - External: Customers (submit tickets), support agents (handle tickets)

3. **What are the top 3 responsibilities?**
   - Ticket management and smart routing (to right support agent)
   - Automated response suggestions (AI-powered)
   - Customer health scoring and proactive outreach

4. **What can this CoE NEVER do?**
   - Cannot close tickets without customer confirmation
   - Cannot disclose one customer's data to another customer

5. **How does this CoE know when to wake up?**
   - Event: `support.ticket.created`
   - Event: `support.health.score.low`
   - Event: `support.escalation.requested`

6. **What decisions does this CoE make autonomously vs escalate?**
   - **Autonomous:** Ticket routing, response suggestions, knowledge base article recommendations, health score updates
   - **Escalate:** VIP customer issues, legal threats, account cancellation requests

7. **What other CoEs does this agent collaborate with?**
   - WowMarketplace (agent quality complaints)
   - WowNotification (ticket update emails)
   - WowAnalytics (support performance metrics)

8. **What data does this CoE read/write?**
   - **Reads:** Ticket history, customer profiles, knowledge base articles, agent performance data
   - **Writes:** Ticket responses, customer health scores, support analytics, escalation records

9. **What are the success metrics?**
   - First response time: <2 hours
   - Resolution time: <24 hours (P90)
   - Customer satisfaction (CSAT): >4.5/5

10. **What's the cost budget per month?**
    - Estimated: $50/month (high LLM usage for response suggestions)

---

## Next Steps

### For Each CoE:

1. **Create Specialization YAML:**
   ```yaml
   # Example: waooaw/factory/examples/wowdomain_spec.yaml
   agent_name: "WowDomain"
   version: "0.4.0"
   coe_type: "domain_expert"
   
   specialization:
     domain: "Domain Architecture & Business Logic"  # From Q1
     core_responsibilities:  # From Q3
       - "Manage domain models using DDD patterns"
       - "Validate entity relationships"
       - "Maintain ubiquitous language"
     
     constraints:  # From Q4
       - rule: "Cannot modify core domain entities without approval"
         reason: "Domain changes affect entire platform"
     
     wake_triggers:  # From Q5
       - topic: "domain.model.changed"
       - topic: "entity.created"
     
     # ... continue for all 10 questions
   ```

2. **Submit to WowAgentFactory:**
   ```python
   factory = WowAgentFactory()
   factory.create_agent(spec_path="waooaw/factory/examples/wowdomain_spec.yaml")
   ```

3. **Validate & Deploy:**
   - Factory validates with WowVision Prime
   - Generates code from template
   - Deploys to staging → shadow mode → production

**Timeline: 1-2 days per agent (vs 2 weeks manual) = 77% time savings**

---

**End of Filled Questionnaires**
