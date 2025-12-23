# WAOOAW Platform - Context Preservation Architecture

**Version:** 1.0  
**Last Updated:** 2025-12-23  
**Priority:** CRITICAL - Foundation for all agent collaboration

---

## Executive Summary

Context preservation is the **#1 priority** for WAOOAW platform success. All 14 CoEs must maintain shared context throughout domain onboarding, agent creation, and customer lifecycle to ensure consistent, high-quality, collaborative autonomous operation.

**Goal:** Enable seamless agent collaboration across sessions, iterations, and lifecycle events without context loss.

---

## 1. Context Preservation Requirements

### 1.1 What Must Be Preserved

**Domain Context (Per Industry)**:
- Domain specification (77-page package from WowDomain CoE)
- Component mappings (LLMs, APIs, integrations)
- Skills catalog (15-25 skills with pricing, confidence %)
- Roles catalog (5-7 agents with tier configurations)
- Team bundle (pricing, discount structure)
- Regulatory requirements
- Market analysis & competitive positioning
- AI confidence analysis (96%+ automation with human-in-loop specs)

**Agent Context (Per CoE)**:
- Mission & vision
- Team structure & agent roster
- Collaboration protocols
- Performance metrics (accuracy, latency, cost)
- Learning history (what worked, what failed)
- Knowledge gaps identified
- Capability updates applied
- Decision rationale (why choices were made)

**Platform Context (Global)**:
- Customer journey state (discovery, trial, hired, active, churned)
- Subscription status (plan, billing, usage)
- Integration connections (active APIs, data flows)
- Compliance status (certifications, audit trails)
- Security events (access logs, threat detection)
- System health (uptime, performance, errors)

**Cross-CoE Context**:
- Collaboration history (which CoEs worked together on what)
- Handoff state (work passed between CoEs)
- Escalation chains (issues flagged, resolved, escalated)
- Learning feedback loops (improvements suggested, implemented)

### 1.2 Context Loss Scenarios to Prevent

❌ **Session-Based Loss**: Agent forgets decisions after conversation ends  
❌ **Iteration Loss**: New phase doesn't know what previous phase decided  
❌ **Handoff Loss**: CoE B doesn't understand what CoE A delivered  
❌ **Escalation Loss**: Human decision not remembered for future cases  
❌ **Learning Loss**: Improvements identified but never applied  
❌ **Configuration Loss**: Agent settings reset between deployments  

---

## 2. Context Storage Architecture

### 2.1 Context Database Schema

**PostgreSQL Schema:**

```sql
-- Core Context Store
CREATE TABLE context_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context_type VARCHAR(50) NOT NULL, -- 'domain', 'agent', 'platform', 'cross_coe'
    entity_id VARCHAR(100) NOT NULL, -- domain_id, coe_id, customer_id, etc.
    context_key VARCHAR(200) NOT NULL, -- specific context identifier
    context_data JSONB NOT NULL, -- flexible JSON storage
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100), -- which agent/human created this
    tags TEXT[], -- searchable tags for context retrieval
    metadata JSONB, -- additional context about the context
    UNIQUE(context_type, entity_id, context_key, version)
);

CREATE INDEX idx_context_type_entity ON context_registry(context_type, entity_id);
CREATE INDEX idx_context_tags ON context_registry USING GIN(tags);
CREATE INDEX idx_context_data ON context_registry USING GIN(context_data);

-- Context Access Log (Who accessed what context when)
CREATE TABLE context_access_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context_id UUID REFERENCES context_registry(id),
    accessed_by VARCHAR(100) NOT NULL, -- agent or user identifier
    accessed_at TIMESTAMP DEFAULT NOW(),
    access_type VARCHAR(20) NOT NULL, -- 'read', 'write', 'update', 'delete'
    access_purpose TEXT -- why was this context accessed
);

-- Context Relationships (Links between related contexts)
CREATE TABLE context_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_context_id UUID REFERENCES context_registry(id),
    target_context_id UUID REFERENCES context_registry(id),
    relationship_type VARCHAR(50) NOT NULL, -- 'depends_on', 'derived_from', 'related_to', 'supersedes'
    strength FLOAT DEFAULT 1.0, -- relationship strength (0-1)
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- Context Snapshots (Point-in-time complete state captures)
CREATE TABLE context_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_name VARCHAR(200) NOT NULL,
    snapshot_type VARCHAR(50) NOT NULL, -- 'domain_complete', 'agent_deployed', 'phase_milestone'
    entity_id VARCHAR(100) NOT NULL,
    context_bundle JSONB NOT NULL, -- complete context at snapshot time
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    description TEXT,
    tags TEXT[]
);

CREATE INDEX idx_snapshots_entity ON context_snapshots(entity_id, created_at DESC);
```

### 2.2 Context Retrieval API

**RESTful API Endpoints:**

```python
# Context Management API

# Store new context
POST /api/context
Body: {
    "context_type": "domain",
    "entity_id": "digital-marketing",
    "context_key": "skills_catalog_v1",
    "context_data": { ... },
    "tags": ["skills", "pricing", "digital-marketing"],
    "created_by": "WoW Domain - Skills Discovery Agent"
}

# Retrieve context by key
GET /api/context/{context_type}/{entity_id}/{context_key}

# Retrieve all context for entity
GET /api/context/{context_type}/{entity_id}

# Search context by tags
GET /api/context/search?tags=skills,pricing&context_type=domain

# Get context history (all versions)
GET /api/context/{context_type}/{entity_id}/{context_key}/history

# Create snapshot
POST /api/context/snapshot
Body: {
    "snapshot_name": "digital_marketing_domain_complete",
    "snapshot_type": "domain_complete",
    "entity_id": "digital-marketing",
    "description": "Complete domain spec after WowDomain CoE Phase 7"
}

# Restore from snapshot
POST /api/context/snapshot/{snapshot_id}/restore

# Get context relationships
GET /api/context/{context_id}/relationships?type=depends_on

# Batch context retrieval (for agent wake-up)
POST /api/context/batch
Body: {
    "contexts": [
        {"type": "domain", "entity_id": "digital-marketing", "keys": ["skills_catalog", "roles_catalog"]},
        {"type": "agent", "entity_id": "wowdomain-coe", "keys": ["performance_metrics", "learning_history"]}
    ]
}
```

---

## 3. Agent Wake-Up Protocol (Context Loading)

### 3.1 Wake-Up Sequence

Every agent follows this sequence when starting work:

```
WAKE UP
  ↓
1. IDENTITY RETRIEVAL
   - Load: My CoE identity, role, responsibilities
   - Load: My team structure, collaborators
   - Load: My performance baseline (accuracy, speed, cost)
  ↓
2. DOMAIN CONTEXT LOAD (if working on specific domain)
   - Load: Complete domain specification
   - Load: Current phase & status
   - Load: Previous decisions made (by me or others)
   - Load: Open issues, escalations
  ↓
3. COLLABORATION CONTEXT LOAD
   - Load: Which other CoEs am I working with?
   - Load: What did they deliver to me?
   - Load: What am I expected to deliver to them?
   - Load: Handoff status & quality checks
  ↓
4. LEARNING CONTEXT LOAD
   - Load: Knowledge gaps I identified last time
   - Load: New skills/capabilities available since last wake
   - Load: Feedback from humans or other agents
   - Load: Performance improvements suggested
  ↓
5. WORK EXECUTION
   - Execute my tasks with full context
   - Log all decisions with rationale
   - Update context as work progresses
  ↓
6. CONTEXT SAVE & HANDOFF
   - Save: Work completed, decisions made
   - Save: Issues encountered, resolutions applied
   - Save: New knowledge gaps identified
   - Notify: Next CoE in workflow with handoff package
  ↓
SLEEP (Context preserved for next wake-up)
```

### 3.2 Wake-Up Context Bundle (Per Agent)

```json
{
  "agent_identity": {
    "coe_id": "wowdomain-coe",
    "agent_id": "wowdomain-skills-discovery",
    "agent_name": "WoW Domain - Skills Discovery Agent",
    "version": "1.2.3",
    "capabilities": ["skill_decomposition", "pricing_estimation", "confidence_analysis"],
    "model": "gpt-4-turbo",
    "status": "active"
  },
  "current_work": {
    "domain_id": "digital-marketing",
    "phase": "specification_generation",
    "task": "identify_15_25_skills",
    "started_at": "2025-12-23T10:00:00Z",
    "deadline": "2025-12-23T18:00:00Z",
    "priority": "high"
  },
  "domain_context": {
    "domain_specification": { ... }, // Complete 77-page spec
    "components_identified": [ ... ],
    "research_report": { ... },
    "regulatory_requirements": [ ... ]
  },
  "collaboration_context": {
    "upstream_coes": [
      {
        "coe_id": "wowdomain-coe",
        "agent_id": "wowdomain-research",
        "delivered": "research_report_v1.0",
        "quality_score": 0.95,
        "handoff_notes": "Industry research complete. 10 key workflows identified."
      }
    ],
    "downstream_coes": [
      {
        "coe_id": "wowdomain-coe",
        "agent_id": "wowdomain-role-definition",
        "expects": "skills_catalog_v1.0",
        "deadline": "2025-12-23T20:00:00Z"
      }
    ]
  },
  "learning_context": {
    "performance_metrics": {
      "accuracy": 0.96,
      "avg_completion_time_hours": 6.2,
      "cost_per_run_usd": 12.50,
      "escalation_rate": 0.08
    },
    "knowledge_gaps": [
      "Need more data on healthcare skill pricing",
      "Improve automation confidence calculation for regulatory-heavy domains"
    ],
    "recent_updates": [
      {
        "date": "2025-12-20",
        "update": "New skill: Compliance documentation generation",
        "impact": "Can now handle regulated industries better"
      }
    ],
    "feedback_received": [
      {
        "from": "wowdomain-critique-agent",
        "date": "2025-12-22",
        "feedback": "Skills too granular for enterprise customers. Consider bundling.",
        "action_taken": "Introduced skill bundles in catalog generation"
      }
    ]
  },
  "previous_decisions": [
    {
      "decision": "Priced 'Blog Writing' skill at ₹3,000/month",
      "rationale": "Market analysis showed competitors at ₹2,500-3,500 range. Positioned at mid-high for quality perception.",
      "made_by": "wowdomain-skills-discovery",
      "made_at": "2025-12-15T14:30:00Z",
      "validated_by": "wowdomain-qa-agent",
      "outcome": "Customer acceptance rate: 78%"
    }
  ]
}
```

---

## 4. Cross-CoE Collaboration Protocol

### 4.1 Handoff Package Structure

When one CoE completes work and hands off to another:

```json
{
  "handoff_id": "uuid-12345",
  "from_coe": "wowdomain-coe",
  "from_agent": "wowdomain-skills-discovery",
  "to_coe": "wowdomain-coe",
  "to_agent": "wowdomain-role-definition",
  "handoff_type": "sequential_workflow", // or "parallel_review", "escalation", "feedback_loop"
  "domain_id": "digital-marketing",
  "phase": "specification_generation",
  "deliverable": {
    "artifact_type": "skills_catalog",
    "artifact_id": "digital-marketing-skills-v1.0",
    "artifact_location": "s3://waooaw-artifacts/domains/digital-marketing/skills-catalog-v1.0.json",
    "artifact_summary": {
      "skills_identified": 17,
      "pricing_range": "₹2,500 - ₹5,000/month",
      "avg_confidence": 0.94,
      "human_in_loop_required": ["Tax planning (25%)", "Brand strategy (15%)"]
    }
  },
  "context_bundle": {
    "decisions_made": [ ... ],
    "assumptions": [ ... ],
    "edge_cases_identified": [ ... ],
    "quality_score": 0.93,
    "qa_passed": true,
    "critique_notes": "No concerns raised"
  },
  "next_steps": [
    "Role Definition Agent: Combine skills into 7 agent roles",
    "Ensure each role has 4-10 skills",
    "Calculate role pricing with bundle discounts"
  ],
  "handoff_time": "2025-12-23T16:00:00Z",
  "deadline": "2025-12-23T20:00:00Z",
  "priority": "high",
  "metadata": {
    "upstream_handoffs": ["research_report", "component_mapping"],
    "downstream_dependencies": ["team_bundle_pricing", "marketplace_listing"]
  }
}
```

### 4.2 Collaboration Memory

All CoE interactions are logged for future reference:

```sql
CREATE TABLE coe_collaboration_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_coe VARCHAR(100) NOT NULL,
    to_coe VARCHAR(100) NOT NULL,
    interaction_type VARCHAR(50) NOT NULL, -- 'handoff', 'review', 'critique', 'escalation', 'feedback'
    domain_id VARCHAR(100),
    context_shared JSONB, -- what context was passed
    outcome VARCHAR(50), -- 'success', 'revision_needed', 'escalated', 'blocked'
    duration_minutes INTEGER,
    quality_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    notes TEXT,
    metadata JSONB
);
```

---

## 5. Context Versioning & Time Travel

### 5.1 Version Control for Context

Every context update creates a new version:

```sql
-- Example: Skills catalog evolves over time
Version 1 (2025-12-23 10:00): Initial skills identified (15 skills)
Version 2 (2025-12-23 14:00): After critique feedback (17 skills, 2 merged, 4 added)
Version 3 (2025-12-23 18:00): After QA validation (17 skills, pricing adjusted)
Version 4 (2025-12-24 09:00): After market analysis update (18 skills, 1 new regulatory skill)
```

**Time Travel Queries:**
```sql
-- What did the skills catalog look like at specific time?
SELECT context_data 
FROM context_registry 
WHERE context_type = 'domain' 
  AND entity_id = 'digital-marketing' 
  AND context_key = 'skills_catalog'
  AND created_at <= '2025-12-23 14:00:00'
ORDER BY version DESC 
LIMIT 1;

-- What changed between versions?
SELECT 
  v1.version as old_version,
  v2.version as new_version,
  v1.context_data as old_data,
  v2.context_data as new_data,
  v2.updated_at - v1.updated_at as time_diff
FROM context_registry v1
JOIN context_registry v2 ON v1.context_key = v2.context_key 
  AND v1.entity_id = v2.entity_id
  AND v2.version = v1.version + 1
WHERE v1.context_key = 'skills_catalog';
```

---

## 6. Context Preservation in Practice

### 6.1 Example: Digital Marketing Domain Onboarding

**Phase 1: WowDomain CoE Research (Hours 0-6)**

```python
# WoW Domain - Research Agent wakes up
research_agent.wake_up()

# Loads minimal context (no prior work on this domain)
context = research_agent.load_context(
    domain_id="digital-marketing",
    phase="research_discovery"
)

# Executes research
research_report = research_agent.conduct_research()

# Saves context with full decisions & rationale
research_agent.save_context({
    "artifact": research_report,
    "decisions": [
        {"what": "Identified 10 core workflows", "why": "Industry analysis + SME interviews"},
        {"what": "Focused on B2B SaaS companies", "why": "Highest willingness to pay for AI agents"}
    ],
    "assumptions": ["GDPR compliance mandatory", "Content creation is #1 pain point"],
    "next_phase": "component_mapping",
    "quality_score": 0.95
})

# Hands off to Component Mapper Agent
research_agent.handoff_to("wowdomain-component-mapper", research_report)
```

**Phase 2: WowDomain CoE Component Mapping (Hours 6-10)**

```python
# WoW Domain - Component Mapper Agent wakes up
mapper_agent.wake_up()

# Loads FULL context including upstream work
context = mapper_agent.load_context(
    domain_id="digital-marketing",
    phase="component_mapping",
    include_upstream=True  # Gets research report + decisions
)

# Now has COMPLETE picture:
# - 10 workflows identified by Research Agent
# - Pain points: Content creation, SEO, social media
# - Target customer: B2B SaaS companies
# - Regulatory: GDPR compliance

# Maps components based on this context
component_map = mapper_agent.map_components(context["research_report"])

# Saves NEW context that builds on previous
mapper_agent.save_context({
    "artifact": component_map,
    "based_on": context["research_report"]["id"],  # Links to upstream work
    "decisions": [
        {"what": "Selected GPT-4 for content generation", "why": "Superior quality needed for B2B audience"},
        {"what": "Added WordPress API", "why": "Research showed 70% of customers use WordPress"}
    ],
    "quality_score": 0.92
})

# Hands off to Skills Discovery Agent
mapper_agent.handoff_to("wowdomain-skills-discovery", component_map)
```

**Phase 3: WowDomain CoE Skills Discovery (Hours 10-16)**

```python
# WoW Domain - Skills Discovery Agent wakes up
skills_agent.wake_up()

# Loads CUMULATIVE context from ALL previous phases
context = skills_agent.load_context(
    domain_id="digital-marketing",
    phase="specification_generation",
    include_upstream=True  # Gets research + components + all decisions
)

# Now has COMPLETE understanding:
# - 10 workflows (from research)
# - Pain points & target customers (from research)
# - 10 components available (from mapper)
# - WHY each component was selected (from mapper's decisions)

# Discovers skills with full context awareness
skills_catalog = skills_agent.discover_skills(
    workflows=context["research_report"]["workflows"],
    components=context["component_map"]["components"],
    target_customer=context["research_report"]["target_customer"]
)

# Critique Agent reviews WITH FULL CONTEXT
critique_agent.review(skills_catalog, context)
# Critique can see: "Why was GPT-4 chosen? Because B2B needs quality."
# Critique can validate: "Does 'Blog Writing' skill align with identified pain points? Yes."

# Saves context with lineage
skills_agent.save_context({
    "artifact": skills_catalog,
    "lineage": ["research_report", "component_map"],  # Traces back to source decisions
    "decisions": [...],
    "quality_score": 0.94
})
```

---

## 7. Context Preservation for Learning

### 7.1 Learning Feedback Loop

Every agent outcome feeds back into context for future improvement:

```python
# After domain deployment
outcome = {
    "domain_id": "digital-marketing",
    "deployed_at": "2025-12-24T00:00:00Z",
    "customer_id": "customer-123",
    "trial_conversion": True,
    "subscription_plan": "team_bundle",
    "monthly_revenue": 75000  # ₹75K
}

# Extract learnings
learnings = [
    {
        "agent": "wowdomain-skills-discovery",
        "learning": "Skills priced at ₹3-5K converted at 78%. Sweet spot confirmed.",
        "confidence": 0.85,
        "recommendation": "Continue this pricing strategy for similar domains"
    },
    {
        "agent": "wowdomain-role-definition",
        "learning": "Team bundle (7 agents) preferred over individual roles (68% chose bundle)",
        "confidence": 0.92,
        "recommendation": "Emphasize team bundles in marketplace for enterprise customers"
    }
]

# Save learnings to context for all future domains
for learning in learnings:
    save_learning_context(
        agent_id=learning["agent"],
        learning=learning["learning"],
        confidence=learning["confidence"],
        evidence=outcome,
        apply_to_future_domains=True
    )

# Next time Skills Discovery Agent wakes up for NEW domain:
context = skills_agent.load_context(domain_id="healthcare")
# Gets: "Previous learning: ₹3-5K pricing converts well for B2B. Consider for healthcare."
```

---

## 8. Context Preservation Guarantees

### 8.1 System Guarantees

✅ **Durability**: All context persisted to PostgreSQL with replication  
✅ **Versioning**: Every change creates new version, old versions never deleted  
✅ **Traceability**: Full lineage from decision → outcome → learning  
✅ **Searchability**: Tags + JSONB indexes enable fast context retrieval  
✅ **Snapshotting**: Point-in-time complete state snapshots at milestones  
✅ **Relationships**: Explicit links between related contexts  
✅ **Access Logging**: Who accessed what context when (audit trail)  

### 8.2 Agent Guarantees

✅ **Wake-Up Context**: Every agent gets complete context on wake-up  
✅ **Handoff Context**: Downstream agents get full upstream context  
✅ **Critique Context**: QA/Critique agents see full decision history  
✅ **Learning Context**: Performance data feeds back for improvement  
✅ **Time Travel**: Can reconstruct state at any point in time  
✅ **Conflict Resolution**: Version conflicts detected & resolved  

---

## 9. Implementation Checklist

**Infrastructure:**
- [ ] Deploy PostgreSQL with context schema
- [ ] Implement Context Management API (FastAPI)
- [ ] Set up S3 for artifact storage (large files)
- [ ] Configure Redis for context caching (hot paths)
- [ ] Implement context search (Elasticsearch integration)

**Agent Integration:**
- [ ] Update all 14 CoEs to use Context API
- [ ] Implement wake-up protocol in agent base class
- [ ] Add context save calls after all operations
- [ ] Implement handoff protocol between CoEs
- [ ] Add context lineage tracking

**Monitoring:**
- [ ] Context access metrics (who, what, when)
- [ ] Context freshness alerts (stale data detection)
- [ ] Context completeness checks (missing required keys)
- [ ] Storage growth monitoring
- [ ] Performance metrics (context load time)

**Testing:**
- [ ] Unit tests for Context API
- [ ] Integration tests for agent wake-up flow
- [ ] End-to-end test: Full domain onboarding with context preservation
- [ ] Stress test: 1000 concurrent agents loading context
- [ ] Disaster recovery test: Restore from snapshots

---

## 10. Success Metrics

**Context Preservation KPIs:**
- **Context Completeness**: 100% of required context available on agent wake-up
- **Context Freshness**: <5 seconds lag between update & availability
- **Context Accuracy**: 0% data loss or corruption
- **Lineage Depth**: Average 4+ levels of decision traceability
- **Learning Application**: 90%+ of learnings applied to future domains
- **Handoff Success**: 98%+ handoffs with complete context
- **Time Travel Accuracy**: 100% ability to reconstruct past states

**Business Impact:**
- **Faster Domain Onboarding**: 30% reduction in time (context reuse)
- **Higher Quality**: 20% fewer revisions (fewer context gaps)
- **Better Learning**: 50% improvement rate per quarter
- **Reduced Escalations**: 40% fewer human interventions needed
- **Customer Satisfaction**: 95%+ satisfaction with agent consistency

---

## Conclusion

Context preservation is not a feature—it's the **foundation** of WAOOAW's autonomous agent platform. Without it, agents are stateless, forgetful, and ineffective. With it, agents become **intelligent, learning, collaborative** systems that improve over time.

**Next Steps:**
1. Implement context architecture (this document)
2. Integrate with all 14 CoEs
3. Test with Digital Marketing domain end-to-end
4. Monitor, measure, iterate

**Vision:** Every agent wakes up knowing **everything** it needs to know, remembers **everything** it learned, and builds on **everything** that came before.

---

**Document Status:** ✅ COMPLETE - Ready for implementation  
**Priority:** CRITICAL - Foundation for Phase 1  
**Owner:** WoW Platform - Vision Agent  
**Review Required:** Yes - Technical feasibility, cost analysis
