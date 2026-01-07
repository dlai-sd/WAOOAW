# Platform CoE Agents - Discovery Questionnaires

**Purpose:** Gather requirements for each of the 14 Platform CoE agents to create detailed specialization configs

**Usage:** Answer these questions for each CoE before creating their specialization YAML. WowAgentFactory will use these answers to generate the agent.

---

## General Questions (All CoEs)

These questions apply to every Platform CoE agent:

1. **What is the primary problem this CoE solves?**
2. **Who are the stakeholders (internal: other agents, external: humans)?**
3. **What are the top 3 responsibilities (must-do tasks)?**
4. **What can this CoE NEVER do (hard constraints)?**
5. **How does this CoE know when to wake up (event triggers)?**
6. **What decisions does this CoE make autonomously vs escalate to humans?**
7. **What other CoEs does this agent collaborate with most?**
8. **What data does this CoE read/write (databases, APIs)?**
9. **What are the success metrics (how do we measure effectiveness)?**
10. **What's the cost budget per month (LLM, compute, storage)?**

---

## Agent 1: WowVision Prime ✅ (COMPLETE - Reference)

**Status:** PRODUCTION (v0.3.6)

### Answers (Reference for Other CoEs)

1. **Problem:** Ensure all platform decisions align with WAOOAW's 3-layer vision stack
2. **Stakeholders:** All 13 other CoEs (internal), Platform team (external)
3. **Top 3 Responsibilities:**
   - Validate file creations against vision
   - Review PRs for vision compliance
   - Process human escalations
4. **Constraints:**
   - NEVER modify Layer 1 vision (immutable foundation)
   - NEVER approve Layer 2 changes without clear Layer 1 alignment
   - NEVER generate Python code in Phase 1
5. **Wake Triggers:**
   - New file created in repository
   - PR opened/updated
   - Human escalation requested
6. **Autonomous vs Escalate:**
   - Autonomous: Layer 2/3 validation, pattern recognition
   - Escalate: Layer 1 violations, ambiguous cases
7. **Collaborates With:** All CoEs (validates their work)
8. **Data:**
   - Reads: Vision stack (YAML), GitHub files, PR data
   - Writes: GitHub issues, agent_decisions table, vector memory
9. **Success Metrics:**
   - Vision compliance rate: >95%
   - False positive rate: <5%
   - Response time: <2 seconds
10. **Budget:** $25/month (LLM calls minimized via caching)

---

## Agent 2: WowDomain (Domain Expert CoE)

**Status:** PLANNED (v0.4.0)  
**Will be created by:** WowAgentFactory (first autonomous creation)

### Questions

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
   - **Escalate:** Core domain entity changes, bounded context boundary modifications, aggregatroot changes

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

**Status:** IN PROGRESS (v0.4.1)  
**Will be created by:** Manual implementation (this is the bootstrap agent)

### Questions

1. **What is the primary problem this CoE solves?**
   - Enable platform to autonomously create new agents from specifications without manual coding?

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

### Questions

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

### Questions

1. **What is the primary problem this CoE solves?**
   - [ ] _______________________________________________

2. **Who are the stakeholders?**
   - Internal: _______________________________________________
   - External: _______________________________________________

3. **What are the top 3 responsibilities?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________
   - [ ] _______________________________________________

4. **What can this CoE NEVER do?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

5. **How does this CoE know when to wake up?**
   - [ ] Event: _______________________________________________
   - [ ] Event: _______________________________________________

6. **What decisions does this CoE make autonomously vs escalate?**
   - **Autonomous:** _______________________________________________
   - **Escalate:** _______________________________________________

7. **What other CoEs does this agent collaborate with?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

8. **What data does this CoE read/write?**
   - **Reads:** _______________________________________________
   - **Writes:** _______________________________________________

9. **What are the success metrics?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

10. **What's the cost budget per month?**
    - Estimated: $___________ (LLM usage: low/medium/high)

---

## Agent 6: WowSecurity (Security & Compliance)

**Status:** PLANNED (v0.4.4)

### Questions

1. **What is the primary problem this CoE solves?**
   - [ ] _______________________________________________

2. **Who are the stakeholders?**
   - Internal: _______________________________________________
   - External: _______________________________________________

3. **What are the top 3 responsibilities?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________
   - [ ] _______________________________________________

4. **What can this CoE NEVER do?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

5. **How does this CoE know when to wake up?**
   - [ ] Event: _______________________________________________
   - [ ] Event: _______________________________________________

6. **What decisions does this CoE make autonomously vs escalate?**
   - **Autonomous:** _______________________________________________
   - **Escalate:** _______________________________________________

7. **What other CoEs does this agent collaborate with?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

8. **What data does this CoE read/write?**
   - **Reads:** _______________________________________________
   - **Writes:** _______________________________________________

9. **What are the success metrics?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

10. **What's the cost budget per month?**
    - Estimated: $___________ (LLM usage: low/medium/high)

---

## Agent 7: WowMarketplace (Marketplace Operations)

**Status:** PLANNED (v0.5.0)

### Questions

1. **What is the primary problem this CoE solves?**
   - [ ] _______________________________________________

2. **Who are the stakeholders?**
   - Internal: _______________________________________________
   - External: _______________________________________________

3. **What are the top 3 responsibilities?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________
   - [ ] _______________________________________________

4. **What can this CoE NEVER do?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

5. **How does this CoE know when to wake up?**
   - [ ] Event: _______________________________________________
   - [ ] Event: _______________________________________________

6. **What decisions does this CoE make autonomously vs escalate?**
   - **Autonomous:** _______________________________________________
   - **Escalate:** _______________________________________________

7. **What other CoEs does this agent collaborate with?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

8. **What data does this CoE read/write?**
   - **Reads:** _______________________________________________
   - **Writes:** _______________________________________________

9. **What are the success metrics?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

10. **What's the cost budget per month?**
    - Estimated: $___________ (LLM usage: low/medium/high)

---

## Agent 8: WowAuth (Authentication & Authorization)

**Status:** PLANNED (v0.5.1)

### Questions

1. **What is the primary problem this CoE solves?**
   - [ ] _______________________________________________

2. **Who are the stakeholders?**
   - Internal: _______________________________________________
   - External: _______________________________________________

3. **What are the top 3 responsibilities?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________
   - [ ] _______________________________________________

4. **What can this CoE NEVER do?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

5. **How does this CoE know when to wake up?**
   - [ ] Event: _______________________________________________
   - [ ] Event: _______________________________________________

6. **What decisions does this CoE make autonomously vs escalate?**
   - **Autonomous:** _______________________________________________
   - **Escalate:** _______________________________________________

7. **What other CoEs does this agent collaborate with?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

8. **What data does this CoE read/write?**
   - **Reads:** _______________________________________________
   - **Writes:** _______________________________________________

9. **What are the success metrics?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

10. **What's the cost budget per month?**
    - Estimated: $___________ (LLM usage: low/medium/high)

---

## Agent 9: WowPayment (Payment Processing)

**Status:** PLANNED (v0.5.2)

### Questions

1. **What is the primary problem this CoE solves?**
   - [ ] _______________________________________________

2. **Who are the stakeholders?**
   - Internal: _______________________________________________
   - External: _______________________________________________

3. **What are the top 3 responsibilities?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________
   - [ ] _______________________________________________

4. **What can this CoE NEVER do?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

5. **How does this CoE know when to wake up?**
   - [ ] Event: _______________________________________________
   - [ ] Event: _______________________________________________

6. **What decisions does this CoE make autonomously vs escalate?**
   - **Autonomous:** _______________________________________________
   - **Escalate:** _______________________________________________

7. **What other CoEs does this agent collaborate with?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

8. **What data does this CoE read/write?**
   - **Reads:** _______________________________________________
   - **Writes:** _______________________________________________

9. **What are the success metrics?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

10. **What's the cost budget per month?**
    - Estimated: $___________ (LLM usage: low/medium/high)

---

## Agent 10: WowNotification (Communication)

**Status:** PLANNED (v0.5.3)

### Questions

1. **What is the primary problem this CoE solves?**
   - [ ] _______________________________________________

2. **Who are the stakeholders?**
   - Internal: _______________________________________________
   - External: _______________________________________________

3. **What are the top 3 responsibilities?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________
   - [ ] _______________________________________________

4. **What can this CoE NEVER do?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

5. **How does this CoE know when to wake up?**
   - [ ] Event: _______________________________________________
   - [ ] Event: _______________________________________________

6. **What decisions does this CoE make autonomously vs escalate?**
   - **Autonomous:** _______________________________________________
   - **Escalate:** _______________________________________________

7. **What other CoEs does this agent collaborate with?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

8. **What data does this CoE read/write?**
   - **Reads:** _______________________________________________
   - **Writes:** _______________________________________________

9. **What are the success metrics?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

10. **What's the cost budget per month?**
    - Estimated: $___________ (LLM usage: low/medium/high)

---

## Agent 11: WowAnalytics (Data & Insights)

**Status:** PLANNED (v0.5.4)

### Questions

1. **What is the primary problem this CoE solves?**
   - [ ] _______________________________________________

2. **Who are the stakeholders?**
   - Internal: _______________________________________________
   - External: _______________________________________________

3. **What are the top 3 responsibilities?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________
   - [ ] _______________________________________________

4. **What can this CoE NEVER do?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

5. **How does this CoE know when to wake up?**
   - [ ] Event: _______________________________________________
   - [ ] Event: _______________________________________________

6. **What decisions does this CoE make autonomously vs escalate?**
   - **Autonomous:** _______________________________________________
   - **Escalate:** _______________________________________________

7. **What other CoEs does this agent collaborate with?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

8. **What data does this CoE read/write?**
   - **Reads:** _______________________________________________
   - **Writes:** _______________________________________________

9. **What are the success metrics?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

10. **What's the cost budget per month?**
    - Estimated: $___________ (LLM usage: low/medium/high)

---

## Agent 12: WowScaling (Performance & Scaling)

**Status:** PLANNED (v0.5.5)

### Questions

1. **What is the primary problem this CoE solves?**
   - [ ] _______________________________________________

2. **Who are the stakeholders?**
   - Internal: _______________________________________________
   - External: _______________________________________________

3. **What are the top 3 responsibilities?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________
   - [ ] _______________________________________________

4. **What can this CoE NEVER do?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

5. **How does this CoE know when to wake up?**
   - [ ] Event: _______________________________________________
   - [ ] Event: _______________________________________________

6. **What decisions does this CoE make autonomously vs escalate?**
   - **Autonomous:** _______________________________________________
   - **Escalate:** _______________________________________________

7. **What other CoEs does this agent collaborate with?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

8. **What data does this CoE read/write?**
   - **Reads:** _______________________________________________
   - **Writes:** _______________________________________________

9. **What are the success metrics?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

10. **What's the cost budget per month?**
    - Estimated: $___________ (LLM usage: low/medium/high)

---

## Agent 13: WowIntegration (External Integrations)

**Status:** PLANNED (v0.5.6)

### Questions

1. **What is the primary problem this CoE solves?**
   - [ ] _______________________________________________

2. **Who are the stakeholders?**
   - Internal: _______________________________________________
   - External: _______________________________________________

3. **What are the top 3 responsibilities?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________
   - [ ] _______________________________________________

4. **What can this CoE NEVER do?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

5. **How does this CoE know when to wake up?**
   - [ ] Event: _______________________________________________
   - [ ] Event: _______________________________________________

6. **What decisions does this CoE make autonomously vs escalate?**
   - **Autonomous:** _______________________________________________
   - **Escalate:** _______________________________________________

7. **What other CoEs does this agent collaborate with?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

8. **What data does this CoE read/write?**
   - **Reads:** _______________________________________________
   - **Writes:** _______________________________________________

9. **What are the success metrics?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

10. **What's the cost budget per month?**
    - Estimated: $___________ (LLM usage: low/medium/high)

---

## Agent 14: WowSupport (Customer Support)

**Status:** PLANNED (v0.5.7)

### Questions

1. **What is the primary problem this CoE solves?**
   - [ ] _______________________________________________

2. **Who are the stakeholders?**
   - Internal: _______________________________________________
   - External: _______________________________________________

3. **What are the top 3 responsibilities?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________
   - [ ] _______________________________________________

4. **What can this CoE NEVER do?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

5. **How does this CoE know when to wake up?**
   - [ ] Event: _______________________________________________
   - [ ] Event: _______________________________________________

6. **What decisions does this CoE make autonomously vs escalate?**
   - **Autonomous:** _______________________________________________
   - **Escalate:** _______________________________________________

7. **What other CoEs does this agent collaborate with?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

8. **What data does this CoE read/write?**
   - **Reads:** _______________________________________________
   - **Writes:** _______________________________________________

9. **What are the success metrics?**
   - [ ] _______________________________________________
   - [ ] _______________________________________________

10. **What's the cost budget per month?**
    - Estimated: $___________ (LLM usage: low/medium/high)

---

## How to Use These Questionnaires

### Step 1: Answer Questions
Fill in the blanks for each CoE agent. Be specific and concrete.

### Step 2: Create Specialization YAML
Use answers to populate `waooaw/factory/examples/{agent_name}_spec.yaml`

Example:
```yaml
agent_name: "WowDomain"
coe_type: "domain_expert"

specialization:
  domain: "Domain Architecture & Business Logic"  # From Q1
  core_responsibilities:  # From Q3
    - "Manage domain models (DDD patterns)"
    - "Validate entity relationships"
    - "Ensure bounded context integrity"
  
  constraints:  # From Q4
    - rule: "Cannot modify core domain entities without approval"
      reason: "Domain changes affect entire platform"
  
  wake_triggers:  # From Q5
    - topic: "domain.model.changed"
    - topic: "entity.created"
  
  # ... continue for all questions
```

### Step 3: Submit to WowAgentFactory
```python
# After WowAgentFactory is deployed
factory.create_agent(spec_path="waooaw/factory/examples/wowdomain_spec.yaml")
```

### Step 4: Validate & Deploy
WowAgentFactory automatically:
1. Validates spec with WowVision Prime
2. Generates code
3. Deploys to staging
4. Runs shadow mode tests
5. Deploys to production

**Timeline: 1-2 days per agent (vs 2 weeks manual)**

---

## Next Steps

1. **Complete this questionnaire for all 13 remaining CoEs**
2. **Review answers with platform team**
3. **Create specialization YAML files**
4. **Deploy WowAgentFactory (Week 5-8)**
5. **Let Factory create agents (Week 9-14)**

---

**End of Questionnaires**
