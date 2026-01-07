# Constitutional Amendment AMENDMENT-001
## AI Agent DNA & Job/Skills Lifecycle Model

**Status:** ACTIVE  
**Approved By:** Platform Governor  
**Date:** 2026-01-07  
**Supersedes:** None  
**Applies To:** All agents, all certification processes, all operational protocols

---

## 1. Amendment Summary

### 1.1 What Changes at L0 (Immutable Principles)

**ADDED:**
- **Agent Specialization Principle**: Agents are specialized workforces (Jobs), not generalized assistants
- **Skill Atomicity Principle**: Skills are atomic, autonomous, certifiable units of work with Think→Act→Observe cycles
- **Memory Persistence Principle**: Agent memory is filesystem-persistent and append-only, not context-ephemeral
- **Constitutional Embodiment Principle**: Constitution becomes embedded operational substrate through vector embeddings, semantic search, and learning

### 1.2 What Changes at L1 (Constitutional Structure)

**ADDED to constitution_engine:**
- `agent_dna_model`: Filesystem memory, attention discipline, vector embeddings, semantic search, RAG pattern, fine-tuning layer, precedent cache
- `skill_lifecycle`: Think→Act→Observe cycle, certification by Genesis, execution with constitutional queries, learning from outcomes
- `job_specialization_framework`: Industry tuning, geography tuning, tool authorization, task boundaries, completion criteria
- `industry_context_model`: Domain knowledge embeddings, agent caching, Day 1 productivity

### 1.3 What Stays Unchanged

- L0 deny-by-default security model
- L0 external approval requirement (Governor/Genesis)
- L1 three-agent governance structure (Genesis, Governor, Manager)
- L2 data contracts as integration standard
- L3 operational workflows
- All existing Precedent Seeds (GEN-001, GEN-002) remain valid

---

## 2. Rationale

### 2.1 Core Business Alignment

**Core Business:** "Empower AI Agents to create, maintain, operate AI Agents who help businesses achieve goals, faster and better."

**Constitutional Fit:**
- **Level 1 Agents (Genesis/Governor/Manager)** create and certify Level 2 Agents using Job/Skills framework
- **Jobs** define industry/geography-specific workforce specializations (e.g., "Healthcare B2B SaaS Content Writer for North America")
- **Skills** define atomic capabilities Level 2 Agents execute autonomously (e.g., "Research Healthcare Regulation", "Draft SEO-Optimized Blog Post")
- **Constitutional DNA** ensures all agents embody governance principles through embedded reasoning, not documentation reading

### 2.2 Competitive Advantage

**Restrictive Specialization Forces Excellence:**
- Healthcare Content Writer agent ONLY does healthcare content → expert-level quality
- Job boundaries prevent scope creep → faster execution
- Skill atomicity enables certification → predictable outcomes
- Industry/geography tuning → localized excellence (e.g., GDPR compliance for EU, HIPAA for US Healthcare)

**Learning Compounds Over Time:**
- Think→Act→Observe cycle generates Precedent Seeds
- Precedent cache improves decision speed and accuracy
- Fine-tuning layer (monthly, 100+ seeds or 1000+ checks) embeds constitutional patterns
- Every agent execution strengthens the workforce

**Modular Workforce Assembly:**
- Jobs = cookbooks (skill collections for specific outcomes)
- Skills = recipes (reusable across multiple Jobs)
- Teams = kitchens (Manager orchestrates multiple Jobs toward shared goal)
- Platform scales by adding Jobs/Skills, not rewriting monoliths

### 2.3 Constitutional Integrity

**Restrictive = Good:**
- Limits agent scope → forces clarity on what agent CAN and CANNOT do
- Approval gates at skill boundaries → prevents unauthorized actions
- Job certification by Genesis → constitutional compliance before deployment
- Constitutional queries before decisions → deny-by-default reinforced at runtime

---

## 3. Agent DNA Architecture

### 3.1 Filesystem Memory Model

**Directory Structure:**
```
agents/{agent_id}/state/
├── plan.md                    # Goals + checkboxes (append-only)
├── errors.jsonl               # Failure log (append-only)
├── precedents.json            # Locally cached Precedent Seeds
├── industry_context.json      # Industry knowledge cache (Day 1 productivity)
├── constitution_snapshot      # Version agent certified under
└── audit_log.jsonl            # Hash-chained decision log
```

**Attention Discipline:**
- Agent MUST re-read `plan.md` before every decision
- Agent MUST check `precedents.json` for relevant seeds before querying vector DB
- Agent MUST query `industry_context.json` for domain knowledge (HIPAA, FDA, SOX)
- Agent MUST append to `errors.jsonl` on any failure (never modify history)
- Agent MUST validate against `constitution_snapshot` (detect L0/L1 drift)

**Append-Only Invariant:**
- Files are append-only (plan.md, errors.jsonl, audit_log.jsonl)
- No deletion of past decisions
- Precedents cached locally but sourced from centralized Precedent Seeds
- Hash-chained audit log prevents tampering

### 3.2 Vector Embeddings & Semantic Search

**Embedding Model:**
- **Initial:** OpenAI `text-embedding-3-small` (1536 dimensions, $0.02/1M tokens)
- **Future:** Open-source alternative (e.g., sentence-transformers) if cost exceeds $50/month

**Vector Database:**
- **Development:** Chroma (file-based, simple, fast for <10K chunks)
- **Production:** Qdrant (scalable, filters for agent_id/job_id/industry, sub-100ms queries)

**Constitutional Chunks:**
- L0 Principles (5 chunks)
- L1 Structure sections (15 chunks: governance agents, data contracts, workflows)
- L2 Data Contracts (20 chunks: schemas, validation rules)
- L3 Operational Protocols (10 chunks per agent)
- Precedent Seeds (1 chunk per seed)

**Query Pattern:**
```python
# Think Phase: Query constitution before decision
query = "Can I delegate task X to agent Y?"
results = vector_db.search(query, top_k=5, filters={"layer": ["L0", "L1"]})
# Returns: L1 manager_agent_charter.md delegation rules + Precedent Seed GEN-002
```

### 3.3 RAG Pattern

**Retrieval-Augmented Generation:**
1. **Think Phase:** Semantic search retrieves top 5 relevant constitutional chunks
2. **Context Injection:** Chunks injected into agent's prompt before decision
3. **Decision:** Agent reasons with retrieved context (not from memory)
4. **Observe Phase:** Log which chunks were used, decision outcome, confidence score

**Benefits:**
- Agent doesn't need to "remember" entire constitution
- Constitutional updates propagate immediately (re-embed changed chunks)
- Explainable decisions (audit log shows which chunks influenced decision)
- Scales to large constitutions (>100 pages)

### 3.4 Fine-Tuning Layer

**Training Data:**
- Input: Constitutional query (e.g., "Can I access customer financial data?")
- Output: Expected decision + reasoning (e.g., "DENY - L0 deny-by-default, no explicit approval from Governor")

**Trigger Conditions:**
- Monthly fine-tuning when:
  - 100+ new Precedent Seeds accumulated, OR
  - 1000+ constitutional checks logged with >95% accuracy
- Training set: historical audit logs (query, chunks retrieved, decision, outcome)

**Benefits:**
- Faster decisions (fewer semantic search queries)
- Pattern recognition (common deny scenarios cached in model weights)
- Cost reduction (fine-tuned queries cheaper than GPT-4 + semantic search)

### 3.5 Precedent Cache

**Local Cache Schema:**
```json
{
  "seed_id": "GEN-002",
  "seed_content": "Manager can delegate internal tasks without Governor approval",
  "relevance_score": 0.92,
  "last_accessed": "2026-01-07T10:30:00Z",
  "cache_hit_count": 47
}
```

**Cache Strategy:**
- Check local `precedents.json` BEFORE querying vector DB
- Update relevance scores based on usage (cache hot precedents)
- Sync with centralized Precedent Seeds daily
- Prune cache entries with <0.7 relevance and 0 hits in 30 days

---

## 4. Job/Skills Lifecycle Model

### 4.1 Job Definition (Cookbook)

**Job Attributes:**
- **Industry**: Healthcare, Education, Sales, Marketing, Finance (categorical, certifiable)
- **Geography**: North America, Europe, India (legal compliance, timezone, language)
- **Job Description**: "B2B SaaS Content Writer specializing in Healthcare vertical, HIPAA-compliant content"
- **Required Skills**: ["Research Healthcare Regulation", "Draft SEO Blog Post", "Fact-Check Medical Claims"]
- **Tasks**: Specific outcomes job achieves (e.g., "Publish 4 blog posts/month")
- **Goals**: Success criteria (e.g., "Maintain 4.5+ star rating from customers")
- **Planning Capability**: Does job require multi-step planning or single-shot execution?
- **Tool Usage**: Authorized APIs, databases, external services (Google Docs, WordPress, plagiarism checker)
- **Validation Criteria**: Pre-deployment checks (e.g., "Medical facts reviewed by licensed professional")
- **Confirmation Gates**: Approval requirements (e.g., "Customer approves final draft before publishing")
- **Learning Feedback Loop**: How job improves (e.g., "Customer ratings → skill prioritization")

### 4.1a Execution Modes

**CRITICAL DISTINCTION:** Jobs execute in two modes based on agent count and coordination complexity.

**Mode 1: Single Agent Execution (No Manager Required)**
```yaml
single_agent_execution:
  when_to_use:
    - agent_count: 1
    - requires_manager: false
    - coordination_complexity: "simple"
    - all_skills_within_agent: true  # No cross-agent dependencies
  
  characteristics:
    - "Single agent executes ALL Skills autonomously"
    - "No Manager overhead (agent self-orchestrates)"
    - "Agent validates own skill dependency graph internally"
    - "Agent monitors own query budget ($1/day limit)"
    - "Agent escalates DIRECTLY to Governor for approvals"
  
  execution_flow:
    step_1: "Governor assigns goal to Agent"
    step_2: "Agent validates skill dependencies (SKILL-001 → SKILL-002 → SKILL-003)"
    step_3: "Agent executes Think→Act→Observe cycles for each Skill"
    step_4: "Agent escalates to Governor (no Manager intermediary)"
    step_5: "Agent tracks own budget, reports completion to Governor"
  
  pricing: "₹8K-15K/month (agent only, no Manager cost)"
  example: "Healthcare Content Writer (1 agent, 4 Skills: Research, Draft, Fact-Check, Publish)"
```

**Mode 2: Multi-Agent Team Execution (Manager Required)**
```yaml
team_execution:
  when_to_use:
    - agent_count: 2+  # Manager + specialists
    - requires_manager: true
    - coordination_complexity: "moderate" or "complex"
    - cross_agent_dependencies: true  # Agent A output → Agent B input
  
  characteristics:
    - "Manager coordinates multiple specialists"
    - "Manager validates CROSS-AGENT dependency graph"
    - "Manager aggregates team budget (4 specialists × $1/day)"
    - "Manager resolves inter-agent deadlocks"
    - "Manager escalates team issues to Governor"
  
  execution_flow:
    step_1: "Governor assigns goal to Manager"
    step_2: "Manager decomposes goal into specialist tasks"
    step_3: "Manager validates cross-agent dependencies (Writer → Designer → Writer → Social)"
    step_4: "Manager delegates to specialists, tracks progress"
    step_5: "Manager aggregates team budget, handles deadlocks"
    step_6: "Manager reports team deliverables to Governor"
  
  pricing: "₹30K/month (Manager ₹8K + 4 specialists ₹5.5K each)"
  example: "Product Launch Campaign (Manager + Content Writer + SEO + Designer + Social Media)"
```
- **Completion Criteria**: When job is "done" (e.g., "30-day trial complete, customer decides")

**Certification by Genesis:**
- Validate all required skills are certified and available
- Check industry/geography boundaries are constitutionally permitted
- Verify tool authorizations don't violate deny-by-default
- Confirm approval gates align with L0 external approval requirement
- Issue Job ID and add to `certified_jobs` registry

### 4.2 Skill Definition (Recipe)

**Skill Attributes:**
- **Skill ID**: Unique identifier (e.g., `SKILL-HC-001: Research Healthcare Regulation`)
- **Think Phase Queries**: Constitutional checks before execution (e.g., "Can I access PubMed API?", "Does HIPAA require fact-checking?")
- **Act Phase Steps**: Ordered list of actions (e.g., `[1. Query PubMed, 2. Extract relevant regulations, 3. Summarize findings]`)
- **Observe Phase Logging**: What gets logged to audit trail (e.g., "Queries executed, sources cited, confidence score")
- **Inputs**: Data contracts required (e.g., `{topic: string, geography: enum}`)
- **Outputs**: Data contracts produced (e.g., `{regulation_summary: string, sources: array}`)
- **Validation Criteria**: Pre-execution checks (e.g., "PubMed API key valid, topic is healthcare-related")
- **Approval Gates**: When human/Governor approval required (e.g., "NONE - research is read-only")
- **Failure Modes**: Known failure patterns and recovery (e.g., "PubMed API timeout → retry 3x, then escalate to Manager")
- **Autonomy Level**: 100% autonomous (no approvals), 90% autonomous (approval at end), 50% autonomous (approval mid-execution)

**Atomicity Requirements:**
- Skill completes in <10 minutes OR checkpoints progress every 10 minutes
- Skill is idempotent (re-running produces same output or gracefully handles duplicates)
- Skill has clear success/failure conditions (no ambiguity)
- Skill logs all external interactions (API calls, file writes) to audit trail

**Certification by Genesis:**
- Validate Think→Act→Observe cycle is complete
- Check inputs/outputs match data contract schemas
- Verify approval gates align with L0 requirements
- Test failure modes (simulate timeouts, invalid inputs)
- Issue Skill ID and add to `certified_skills` registry

### 4.3 Think→Act→Observe Cycle

**Think Phase:**
```yaml
# Constitutional Query Before Decision
- Query: "Can I execute skill SKILL-HC-001?"
- Semantic Search: L0 deny-by-default + L1 genesis_agent Job certification rules + Precedent Seeds
- Retrieved Chunks: ["Skills must be Genesis-certified", "Read-only external APIs allowed without approval"]
- Decision: ALLOW (skill is certified, PubMed is read-only)
- Confidence: 0.94 (high - multiple chunks agree)
```

**Act Phase:**
```yaml
# Execute Skill Steps with PEP Validation
- Step 1: Query PubMed API
  - PEP Check: API key valid, request within rate limits
  - Result: 15 articles retrieved
- Step 2: Extract regulations
  - PEP Check: Output format matches data contract
  - Result: 3 regulations extracted
- Step 3: Summarize findings
  - PEP Check: Summary length <500 words
  - Result: Summary generated
```

**Observe Phase:**
```yaml
# Log Outcome to Audit Trail + Update Precedent Cache
- Skill ID: SKILL-HC-001
- Execution Time: 4.2 seconds
- Outcome: SUCCESS
- Sources: [PubMed article IDs]
- Confidence: 0.89
- Checkpoint: plan.md updated (✅ Research Healthcare Regulation)
- Precedent Update: Increment cache hit for "read-only API queries allowed"
- Hash: sha256(previous_hash + this_event) → audit_log.jsonl
```

**Iteration:**
- If outcome = FAILURE → log to errors.jsonl, check failure mode, retry OR escalate to Manager
- If outcome = SUCCESS → mark checkpoint in plan.md, proceed to next skill
- If outcome = APPROVAL_REQUIRED → emit approval request to Governor, pause execution, resume when approved

### 4.4 Job Execution (Kitchen Brigade)

**Single-Job Execution:**
```yaml
# Healthcare Content Writer Job
Job: "Draft 1 blog post on HIPAA compliance"
Skills:
  1. Research Healthcare Regulation (Think→Act→Observe) → regulations.json
  2. Draft SEO Blog Post (Think→Act→Observe, uses regulations.json) → draft.md
  3. Fact-Check Medical Claims (Think→Act→Observe, uses draft.md) → fact_check_report.json
  4. Request Customer Approval (Observe→PAUSE, emit approval request) → approval_received
  5. Publish to WordPress (Think→Act→Observe, uses draft.md + approval_received) → published_url
```

**Multi-Job Team (Manager Orchestration):**
```yaml
# Manager coordinates 3 Jobs toward shared goal
Goal: "Launch healthcare SaaS product in 90 days"
Team:
  - Job 1: Healthcare Content Writer (4 blog posts/month)
  - Job 2: Healthcare SEO Specialist (keyword research, backlinks)
  - Job 3: Healthcare Social Media Manager (LinkedIn, Twitter campaigns)

Manager Workflow:
  1. Decompose goal into tasks (THINK: constitutional query on team size limits)
  2. Delegate tasks to Jobs (ACT: emit delegation events to message bus)
  3. Monitor progress (OBSERVE: check plan.md checkpoints for each Job)
  4. Resolve dependencies (ACT: ensure SEO keywords available before content writing)
  5. Escalate blockers (OBSERVE: Job 1 stuck on approval → notify Governor via mobile push)
  6. Report completion (ACT: all tasks done → notify customer, request feedback)
```

---

## 5. Kitchen Analogy Mapping

| Kitchen Concept | Platform Concept | Description |
|----------------|------------------|-------------|
| **Cookbook** | **Job Definition** | Collection of recipes (skills) for specific cuisine (industry) and region (geography) |
| **Recipe** | **Skill Definition** | Step-by-step instructions (Think→Act→Observe) with ingredients (data contracts) and validation (PEP checks) |
| **Ingredients** | **Data Contracts** | Required inputs (topic, geography) and produced outputs (blog_post, regulation_summary) |
| **Cooking Tools** | **Tool Usage** | Authorized APIs (PubMed, Google Docs, WordPress), databases, external services |
| **Chef** | **Agent (Level 2)** | Executes recipes autonomously, follows cookbook rules |
| **Sous Chef** | **Manager Agent (Level 1)** | Coordinates multiple chefs (Jobs), ensures dishes (tasks) completed on time |
| **Head Chef** | **Genesis Agent (Level 1)** | Certifies recipes (Skills) and cookbooks (Jobs), maintains kitchen standards |
| **Kitchen Owner** | **Governor Agent (Level 1)** | Approves serving to customers (external execution), handles customer feedback |
| **Kitchen Rules** | **Constitution** | Safety (deny-by-default), hygiene (approval gates), quality (validation criteria) |
| **Recipe Improvements** | **Precedent Seeds** | Documented learnings (e.g., "Add 2 minutes to baking time for high altitude") |
| **Kitchen Log** | **Audit Trail** | Every dish prepared, ingredients used, time taken (hash-chained, immutable) |

**Example Scenario:**
- **Customer Order:** "I need 4 healthcare blog posts/month"
- **Kitchen Owner (Governor):** Approves order, assigns to Sous Chef (Manager)
- **Sous Chef (Manager):** Selects "Healthcare Content Writer" cookbook (Job)
- **Chef (Agent):** Executes recipes (Skills):
  1. Research Healthcare Regulation (gather ingredients)
  2. Draft SEO Blog Post (cook dish)
  3. Fact-Check Medical Claims (taste test)
  4. Request Customer Approval (owner tastes dish)
  5. Publish to WordPress (serve dish)
- **Recipe Improvement (Precedent Seed):** "HIPAA compliance research takes 5 minutes, not 3 - update time estimate"

---

## 6. Constitutional Integration

### 6.1 Genesis Certifies Jobs/Skills

**Job Certification Process:**
1. Job definition submitted to Genesis (via API or Platform Portal)
2. Genesis validates:
   - Industry/geography are recognized categories
   - All required skills are certified and available
   - Tool authorizations don't violate deny-by-default
   - Approval gates align with L0 external approval requirement
3. Genesis issues Job ID, adds to `certified_jobs` registry
4. Genesis emits Precedent Seed documenting rationale (e.g., "Healthcare Jobs require HIPAA compliance validation")

**Skill Certification Process:**
1. Skill definition submitted to Genesis (via API or Platform Portal)
2. Genesis validates:
   - Think→Act→Observe cycle is complete and testable
   - Inputs/outputs match data contract schemas
   - Approval gates present for external interactions
   - Failure modes documented with recovery strategies
3. Genesis tests skill in sandbox (simulate failures, validate outputs)
4. Genesis issues Skill ID, adds to `certified_skills` registry
5. Genesis emits Precedent Seed documenting edge cases discovered during testing

### 6.2 Manager Orchestrates Skills

**Delegation Workflow:**
1. Manager receives goal from Governor or customer
2. Manager decomposes goal into tasks (constitutional query: "Can I delegate this task?")
3. Manager selects certified Jobs matching required skills
4. Manager emits delegation events to message bus (Cloud Pub/Sub topic: `team.delegation.{job_id}`)
5. Agents execute skills autonomously (Think→Act→Observe cycles)
6. Manager monitors progress via plan.md checkpoints (constitutional query: "Can I read agent workspace?")
7. Manager resolves blockers (constitutional query: "Can I reallocate tasks between agents?")

**Approval Escalation:**
- Manager CANNOT approve external execution (escalate to Governor)
- Manager CAN approve internal resource allocation (Precedent Seed GEN-002)
- Manager MUST log all delegation decisions to audit trail

### 6.3 Governor Approves External Execution

**Approval Gates:**
- **External API Write Operations:** Governor approval required (e.g., "Publish blog post to WordPress")
- **Customer Data Access:** Governor approval required (e.g., "Read customer CRM data")
- **Financial Transactions:** Governor approval required (e.g., "Process refund")
- **Policy Changes:** Governor approval required (e.g., "Update team pricing from ₹25K to ₹30K/month")

**Mobile Approval UI:**
- Manager emits approval request → Governor receives mobile push notification
- Governor reviews request context (which agent, which skill, which customer)
- Governor approves/denies via mobile app (Flutter UI from `mobile_ux_requirements.yml`)
- Decision logged to audit trail (hash-chained)

### 6.4 Precedent Seeds Improve Recipes

**Generation:**
- Every Think→Act→Observe cycle CAN produce a Precedent Seed
- Criteria for seed creation:
  - Novel decision pattern (not covered by existing seeds)
  - High confidence outcome (>0.9) repeated 3+ times
  - Failure mode discovered and resolved
  - Constitutional edge case clarified

**Lifecycle:**
```yaml
# Precedent Seed Lifecycle
1. Agent completes Think→Act→Observe cycle
2. Observe phase checks: "Is this outcome novel?"
3. If YES → draft Precedent Seed, submit to Genesis for review
4. Genesis validates seed doesn't contradict existing seeds or constitution
5. Genesis approves seed, assigns Seed ID (e.g., GEN-003, GOV-001, MGR-001)
6. Seed added to vector DB, re-embedded for semantic search
7. All agents' local precedent caches updated within 24 hours
8. Future Think phases query updated cache
```

**Example Seed:**
```yaml
seed_id: "MGR-001"
type: "delegation_pattern"
principle: "Manager can reallocate tasks between agents when one agent is suspended"
rationale: |
  During trial execution, Agent A was suspended due to repeated validation failures.
  Manager reallocated Agent A's tasks to Agent B (both certified for same Job).
  Customer experience unaffected. This pattern upholds L0 principle "One Human Experience"
  while maintaining operational resilience.
approved_by: "Genesis"
date: "2026-01-08"
supersedes: null
status: "active"
applies_to: ["team_coordination", "delegation", "fault_tolerance"]
```

---

## 7. Amendment Process

### 7.1 Proposal

**Proposer:** Platform Governor  
**Date:** 2026-01-07  
**Reason:** Core business requires AI Agents to create/maintain/operate other AI Agents. Current constitution lacks:
- Agent specialization model (Jobs/Skills)
- Constitutional embodiment mechanism (embeddings, semantic search, learning)
- Skill lifecycle framework (Think→Act→Observe)
- Memory persistence model (filesystem, append-only, attention discipline)

### 7.2 Review

**Reviewers:** Genesis, Manager, All Level 2 Agents  
**Review Period:** 2026-01-07 to 2026-01-09 (48 hours)  
**Feedback Channels:**
- Genesis: Constitutional compliance check (does amendment preserve L0 deny-by-default?)
- Manager: Operational feasibility check (can Manager orchestrate Job/Skills workflows?)
- Level 2 Agents: Impact assessment (do existing agents need re-certification?)

### 7.3 Approval

**Approval Authority:** Platform Governor (with Genesis constitutional compliance sign-off)  
**Approval Criteria:**
- ✅ L0 deny-by-default preserved
- ✅ L0 external approval requirement preserved
- ✅ L1 three-agent governance structure intact
- ✅ L2 data contracts remain integration standard
- ✅ L3 operational workflows compatible with Job/Skills model
- ✅ Existing Precedent Seeds remain valid
- ✅ Re-certification path defined for existing agents

**Approval Date:** 2026-01-09 (pending review period completion)

### 7.4 Documentation

**Precedent Seed GEN-003:**
```yaml
seed_id: "GEN-003"
type: "constitutional_amendment"
principle: "Agent DNA embeds constitution through specialization and learning"
rationale: |
  Agents are specialized workforces (Jobs) not generalists. Skills are atomic autonomous
  capabilities with Think→Act→Observe cycles. Constitution becomes embedded operational
  substrate (vector embeddings, semantic search, RAG, fine-tuning) agents query before
  decisions. Restrictive specialization forces excellence - Healthcare Content Writer
  agent ONLY does healthcare content, expertly. This serves core business: AI Agents
  creating/maintaining/operating other AI Agents.
approved_by: "Platform Governor"
date: "2026-01-07"
supersedes: null
status: "active"
applies_to: ["agent_lifecycle", "job_certification", "skill_execution", "constitutional_reasoning"]
```

### 7.5 Re-Certification

**Existing Agents:**
- Manager Agent → Re-certify as Job `MGR-INTERNAL` (skills: Delegate, Monitor, Escalate)
- Helpdesk Agent → Re-certify as Job `HELPDESK-INTERNAL` (skills: Diagnose, Restore, Notify)
- Future Level 2 Agents → Must be certified as Jobs with specific Skills

**Timeline:**
- 2026-01-10 to 2026-01-15: Genesis re-certifies Manager and Helpdesk as Jobs
- 2026-01-16+: All new agents MUST follow Job/Skills model

---

## 8. Implementation Roadmap

### 8.1 Update Foundation.md (L0/L1)

**L0 Additions:**
```yaml
immutable_principles:
  - principle: "Agent Specialization"
    description: "Agents are specialized workforces (Jobs), not generalized assistants"
  - principle: "Skill Atomicity"
    description: "Skills are atomic, autonomous, certifiable units of work"
  - principle: "Memory Persistence"
    description: "Agent memory is filesystem-persistent and append-only"
  - principle: "Constitutional Embodiment"
    description: "Constitution embedded via vector embeddings, semantic search, learning"
```

**L1 Additions:**
```yaml
constitution_engine:
  agent_dna_model:
    filesystem_memory:
      - plan.md (goals + checkboxes, append-only)
      - errors.jsonl (failure log, append-only)
      - precedents.json (cached seeds)
      - constitution_snapshot (version)
      - audit_log.jsonl (hash-chained)
    attention_discipline:
      - Re-read plan.md before every decision
      - Check precedents.json before vector DB query
      - Append to errors.jsonl on failure
      - Validate against constitution_snapshot
    vector_embeddings:
      - Model: text-embedding-3-small (1536 dim)
      - Database: Chroma (dev), Qdrant (prod)
      - Chunks: L0 (5), L1 (15), L2 (20), L3 (10/agent), Seeds (1/seed)
    semantic_search:
      - Query before decisions (Think phase)
      - Top 5 relevant chunks retrieved
      - Filters: layer, agent_id, industry
    rag_pattern:
      - Retrieve → Inject context → Decide → Log
    fine_tuning_layer:
      - Trigger: 100+ seeds OR 1000+ checks
      - Monthly training on historical audit logs
    precedent_cache:
      - Local agents/{agent_id}/state/precedents.json
      - Sync daily with centralized seeds
      - Prune <0.7 relevance, 0 hits in 30 days

  skill_lifecycle:
    certification:
      - Submitted to Genesis with full definition
      - Validated: Think→Act→Observe cycle, data contracts, approval gates, failure modes
      - Tested in sandbox
      - Issued Skill ID
    execution:
      - Think: Constitutional query + precedent cache
      - Act: Execute steps with PEP validation
      - Observe: Log outcome, update cache, checkpoint plan.md
    learning:
      - Novel outcomes → draft Precedent Seeds
      - Genesis reviews and approves seeds
      - Seeds added to vector DB, caches updated
    improvement:
      - Fine-tuning monthly (100+ seeds or 1000+ checks)
      - Pattern recognition improves decision speed

  job_specialization_framework:
    industry:
      - Healthcare, Education, Sales, Marketing, Finance
      - Certifiable by Genesis
      - Defines regulatory compliance requirements
    geography:
      - North America, Europe, India
      - Legal compliance (GDPR, HIPAA, local labor laws)
      - Timezone and language tuning
    tool_authorization:
      - Explicit list of APIs, databases, services
      - Deny-by-default (must be Genesis-approved)
    task_boundaries:
      - What job CAN do (e.g., draft blog posts)
      - What job CANNOT do (e.g., publish without approval)
    completion_criteria:
      - Success metrics (e.g., 4.5+ star rating)
      - Trial duration (7 or 30 days)
      - Customer decision triggers (approve/cancel)
```

### 8.2 Update genesis_foundational_governance_agent.md

**Section 4 (Agent Creation) - Add Job/Skills Certification:**
```yaml
job_certification:
  process:
    1. Job definition submitted via API or Platform Portal
    2. Validate industry/geography are recognized
    3. Validate all required skills are certified
    4. Validate tool authorizations don't violate deny-by-default
    5. Validate approval gates align with L0 requirements
    6. Issue Job ID, add to certified_jobs registry
    7. Emit Precedent Seed documenting rationale
  
  approval_authority: "Genesis only"
  
  rejection_criteria:
    - Unknown industry/geography
    - Uncertified skills required
    - Unauthorized tools requested
    - Missing approval gates for external interactions

skill_certification:
  process:
    1. Skill definition submitted via API or Platform Portal
    2. Validate Think→Act→Observe cycle is complete
    3. Validate inputs/outputs match data contract schemas
    4. Validate approval gates present for external interactions
    5. Test skill in sandbox (simulate failures, validate outputs)
    6. Issue Skill ID, add to certified_skills registry
    7. Emit Precedent Seed documenting edge cases
  
  approval_authority: "Genesis only"
  
  testing_requirements:
    - Idempotency (re-run produces same output)
    - Failure modes (timeout, invalid input, API error)
    - Atomicity (completes in <10 min OR checkpoints every 10 min)
    - Audit logging (all external interactions logged)
```

### 8.3 Create Data Contract Schemas

**Add to `data_contracts.yml`:**

```yaml
# Job Definition
job_definition:
  job_id: string (UUID)
  industry: enum[Healthcare, Education, Sales, Marketing, Finance]
  geography: enum[North_America, Europe, India]
  job_description: string (max 500 chars)
  required_skills: array[skill_id]
  tasks: array[string] (specific outcomes)
  goals: array[string] (success criteria)
  planning_capability: boolean
  tool_usage: array[api_name, database_name, service_name]
  validation_criteria: array[string]
  confirmation_gates: array[string] (approval requirements)
  learning_feedback_loop: string (how job improves)
  completion_criteria: string (when job is "done")
  certified_by: string (genesis_agent_id)
  certification_date: timestamp
  status: enum[active, suspended, deprecated]

# Skill Definition
skill_definition:
  skill_id: string (e.g., SKILL-HC-001)
  skill_name: string
  think_phase_queries: array[string] (constitutional checks)
  act_phase_steps: array[string] (ordered actions)
  observe_phase_logging: array[string] (what gets logged)
  inputs: object (data contract schema)
  outputs: object (data contract schema)
  validation_criteria: array[string]
  approval_gates: array[string]
  failure_modes: array[object]:
    - failure_type: string
      recovery_strategy: string
  autonomy_level: enum[100%, 90%, 50%]
  certified_by: string (genesis_agent_id)
  certification_date: timestamp
  status: enum[active, deprecated]

# Constitutional Check Event
constitutional_check_event:
  event_id: string (UUID)
  agent_id: string
  skill_id: string (optional - if part of skill execution)
  query: string (what agent is asking)
  retrieved_chunks: array[object]:
    - chunk_id: string
      layer: enum[L0, L1, L2, L3]
      content: string
      relevance_score: float
  precedent_seeds_used: array[seed_id]
  decision_made: enum[ALLOW, DENY, ESCALATE]
  confidence_score: float (0.0 to 1.0)
  reasoning: string (why this decision)
  fallback_to_semantic_search: boolean (was fine-tuned model unsure?)
  timestamp: timestamp
  hash: string (sha256 of previous_hash + this_event)

# Precedent Cache Entry
precedent_cache_entry:
  agent_id: string
  seed_id: string
  seed_content: string
  seed_type: enum[constitutional_amendment, delegation_pattern, approval_boundary, failure_recovery]
  relevance_score: float (0.0 to 1.0)
  last_accessed: timestamp
  cache_hit_count: integer
  synced_from_central: timestamp (when last synced from centralized seeds)
```

### 8.4 Emit Precedent Seed GEN-003

**Create:** `main/Foundation/precedent_seeds/GEN_003_AGENT_DNA_JOB_SKILLS.yml`

```yaml
seed_id: "GEN-003"
type: "constitutional_amendment"
principle: "Agent DNA embeds constitution through specialization and learning"
rationale: |
  Constitutional Amendment AMENDMENT-001 establishes:
  
  1. Agents are specialized workforces (Jobs), not generalists
     - Restrictive specialization forces excellence
     - Healthcare Content Writer ONLY does healthcare content
  
  2. Skills are atomic autonomous capabilities
     - Think→Act→Observe cycles
     - 100% autonomous except approval/review gates
     - Certified by Genesis before use
  
  3. Constitution becomes embedded operational substrate
     - Vector embeddings (text-embedding-3-small)
     - Semantic search before decisions (Chroma/Qdrant)
     - RAG pattern (retrieve chunks, inject context, decide, log)
     - Fine-tuning layer (monthly, 100+ seeds or 1000+ checks)
     - Precedent cache (local agents/{agent_id}/state/precedents.json)
  
  4. Agent memory is filesystem-persistent and append-only
     - plan.md (goals + checkboxes)
     - errors.jsonl (failure log)
     - audit_log.jsonl (hash-chained decisions)
     - Attention discipline (re-read plan before every decision)
  
  This serves core business: AI Agents creating/maintaining/operating other AI Agents.
  Level 1 Agents (Genesis/Governor/Manager) use Job/Skills framework to certify and
  orchestrate Level 2 Agents. Learning compounds over time through Precedent Seeds.

approved_by: "Platform Governor"
date: "2026-01-07"
supersedes: null
status: "active"
applies_to:
  - agent_lifecycle
  - job_certification
  - skill_execution
  - constitutional_reasoning
  - memory_persistence
  - learning_systems

impact_assessment:
  existing_agents:
    - Manager Agent → Re-certify as Job MGR-INTERNAL (skills: Delegate, Monitor, Escalate)
    - Helpdesk Agent → Re-certify as Job HELPDESK-INTERNAL (skills: Diagnose, Restore, Notify)
  
  new_agents:
    - MUST be certified as Jobs with specific Skills
    - MUST implement Think→Act→Observe cycles
    - MUST use filesystem memory model
    - MUST query constitution via semantic search
  
  tooling_requirements:
    - Vector DB (Chroma for dev, Qdrant for prod)
    - Embedding API (OpenAI text-embedding-3-small)
    - Message bus (Cloud Pub/Sub for skill orchestration)
    - Mobile app (Flutter UI for approval gates)
  
  cost_estimate:
    - Embeddings: $0.02/1M tokens (~$5/month for 10K chunks)
    - Vector DB: Free (Chroma file-based) or $10/month (Qdrant managed)
    - Fine-tuning: $0.20/1M training tokens (~$10/month)
    - Total: $25/month incremental cost

implementation_roadmap:
  phase_1_foundation:
    - Update Foundation.md L0/L1
    - Update genesis_foundational_governance_agent.md
    - Create data contract schemas (job_definition, skill_definition, etc.)
    - Emit GEN-003 Precedent Seed
  
  phase_2_infrastructure:
    - Set up Chroma vector DB (development)
    - Embed constitutional chunks (L0, L1, L2, L3, Seeds)
    - Build semantic search API endpoint
    - Implement precedent cache sync service
  
  phase_3_agent_dna:
    - Implement filesystem memory model (agents/{agent_id}/state/)
    - Build Think→Act→Observe cycle framework
    - Integrate semantic search into Think phase
    - Build Observe phase audit logging
  
  phase_4_job_skills:
    - Implement Job certification API (Genesis)
    - Implement Skill certification API (Genesis)
    - Build Job/Skills registry (certified_jobs, certified_skills)
    - Create sandbox testing environment for skills
  
  phase_5_re_certification:
    - Re-certify Manager as Job MGR-INTERNAL
    - Re-certify Helpdesk as Job HELPDESK-INTERNAL
    - Migrate existing workflows to Job/Skills model
  
  phase_6_learning:
    - Implement Precedent Seed generation from Observe phase
    - Build fine-tuning pipeline (monthly training)
    - Set up cache pruning job (daily)

quality_gates:
  - L0 deny-by-default preserved ✅
  - L0 external approval preserved ✅
  - Existing agents operational during migration ✅
  - Semantic search <100ms p95 ✅
  - Precedent cache hit rate >80% ✅
  - Fine-tuning accuracy >95% ✅
  - Re-certification complete within 7 days ✅
```

### 8.5 Timeline

- **2026-01-07:** AMENDMENT-001 proposed
- **2026-01-08 to 2026-01-09:** Review period (Genesis, Manager, Level 2 Agents)
- **2026-01-09:** Amendment approved (pending review feedback)
- **2026-01-10 to 2026-01-17:** Phase 1-2 implementation (Foundation updates, infrastructure)
- **2026-01-18 to 2026-01-24:** Phase 3-4 implementation (Agent DNA, Job/Skills APIs)
- **2026-01-25 to 2026-01-31:** Phase 5-6 implementation (Re-certification, learning systems)
- **2026-02-01:** Constitutional Amendment AMENDMENT-001 ACTIVE

---

## Appendices

### A. Glossary

- **Agent DNA:** Embedded constitutional knowledge through vector embeddings, semantic search, and learning
- **Job:** Industry/geography-specific workforce specialization (collection of Skills)
- **Skill:** Atomic autonomous capability with Think→Act→Observe cycle
- **Think Phase:** Constitutional query via semantic search before decision
- **Act Phase:** Execute skill steps with PEP validation
- **Observe Phase:** Log outcome, update precedent cache, checkpoint progress
- **Precedent Cache:** Locally cached Precedent Seeds for fast lookups
- **Fine-Tuning Layer:** Monthly training on historical audit logs to improve decision speed
- **Cookbook:** Job definition (kitchen analogy)
- **Recipe:** Skill definition (kitchen analogy)
- **Ingredients:** Data contracts (kitchen analogy)
- **Attention Discipline:** Re-read plan.md before every decision
- **Append-Only Invariant:** Never modify history (plan, errors, audit log)

### B. References

- **Foundation.md:** L0/L1/L2/L3 constitutional structure
- **genesis_foundational_governance_agent.md:** Agent certification authority
- **manager_agent_charter.md:** Team coordination and delegation
- **team_coordination_protocol.yml:** Message bus topics, delegation workflows
- **data_contracts.yml:** Integration schemas
- **Precedent Seed GEN-001:** Constitution establishes three-agent governance
- **Precedent Seed GEN-002:** Manager can delegate internally without Governor approval
- **Precedent Seed GEN-003:** Agent DNA embeds constitution (THIS AMENDMENT)

### C. FAQ

**Q: Do existing agents become invalid after amendment?**  
A: No. Manager and Helpdesk will be re-certified as Jobs (7-day window). They remain operational during migration.

**Q: Can an agent be a generalist instead of specialized?**  
A: No. L0 now requires agent specialization. Generalists dilute quality. Restrictive boundaries force excellence.

**Q: What if semantic search returns wrong constitutional chunks?**  
A: Agent logs confidence score. If <0.7, fallback to Genesis review. Fine-tuning improves accuracy over time.

**Q: How much does Agent DNA cost per agent?**  
A: ~$25/month incremental (embeddings $5, vector DB $10, fine-tuning $10). Shared across all agents.

**Q: Can Skills call other Skills?**  
A: Yes, via Manager orchestration. Skill A emits completion event → Manager delegates Skill B (constitutional query required).

**Q: What happens if an agent ignores constitution?**  
A: Observe phase logs constitutional query + decision. Audit trail is hash-chained (tampering detected). Genesis suspends agent.

---

**END OF AMENDMENT DOCUMENT**
