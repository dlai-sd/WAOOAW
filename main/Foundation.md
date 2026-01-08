...
# WAOOAW Foundation - Constitutional Governance System

**Version:** 1.3 (Post-ML-Dimensions: Skills/JobRole/Team/Industry with 8 ML Models)  
**Last Updated:** 2026-01-08  
**Status:** Constitutional Amendment Complete + 4 ML Dimensions Complete + Phase 2 Infrastructure Ready + Manufacturing Templates Next

---

## � Related Documents (Traceability Chain)

| Document | Purpose | Traceability |
|----------|---------|--------------|
| **[README.md](../README.md)** | Entry point, quick start | → Foundation (you are here) |
| **[policy/tech_stack.yaml](../policy/tech_stack.yaml)** | Machine-readable tech policy enforcement | ← Foundation (constitutional fit validation) |
| **[policy/yaml_manifest.yaml](../policy/yaml_manifest.yaml)** | YAML lineage tracker | ← Foundation (referenced_by) |
| **[Foundation/TOOLING_SELECTION_DECISION.md](Foundation/TOOLING_SELECTION_DECISION.md)** | Architecture decisions | ← Foundation (implementation of principles) |
| **[policy/TECH_STACK_SELECTION_POLICY.md](../policy/TECH_STACK_SELECTION_POLICY.md)** | Human-readable policy | ← Foundation (constitutional alignment) |

**Lineage Path**: README → Foundation → tech_stack.yaml → audit_tech_stack.py (P001 in yaml_manifest.yaml)

---

## �📊 Architecture Visualizations

For comprehensive visual representations of the constitutional architecture:

- **[Tree View (Hierarchical)](Foundation/diagram_graph.md)** - Constitution at root with L0→L1→L2→L3 layers, 7 foundational agents, Industry Component, Vector DBs, Agent Caches
- **[Layer View (Constitution-Centric)](Foundation/diagram_mindmap.md)** - Concentric governance layers showing L0 (Immutable Principles) → L1 (Structure) → L2 (Operations) → L3 (Learning) with feedback loop

---
## 🏗️ Microservices Implementation

Constitutional design maps to **13 microservices** + **8 reusable component library** (Temporal activities):

**Foundational Platform Services (4):**
- **Finance (Port 8007)** - `financials.yml` - Subscription tracking, cost monitoring, MRR/ARR, discount policies, budget alerts (70%/85%/100%)
- **AI Explorer (Port 8008)** - `component_ai_explorer.yml` - Prompt templates, injection detection, token tracking ($1/day per agent), response caching
- **Integrations (Port 8009)** - `component_outside_world_connector.yml` - CRM, payment, communication integrations with sandbox routing, idempotency, credential management
- **Audit (Port 8010)** - `component_system_audit_account.yml` - **CRITICAL** - Privileged SYSTEM_AUDIT account, hash-chained append-only logs, breaks circular governance dependency

**Core Agent Services (6):**
- **Agent Creation (Port 8001)** - `agent_creation_orchestration.yml` - 7-stage Temporal pipeline (Genesis cert → Architect review → Ethics review → Governor approval → Deploy → Health check → Activate)
- **Agent Execution (Port 8002)** - Think→Act→Observe cycles, Skill orchestration, ML inference (DistilBERT, BART, MiniLM), agent caches
- **Governance (Port 8003)** - `governance_protocols.yaml` - Approvals, precedent seeds, vetoes, business rules engine, mobile API for Governor
- **Industry Knowledge (Port 8004)** - Vector DB queries (constitutional + industry), query routing, MiniLM embeddings, **NEW: Constitutional Query API** (GAP-9 resolved)
- **Learning (Port 8005)** - Precedent seed generation, pattern detection, ML clustering
- **Admin Gateway (Port 8006)** - Health checks, metrics, admin operations, JWT auth, rate limiting

**Platform Portal Services (4):**
- **PP Gateway (Port 8015)** - `component_pp_gateway_service.yml` - **NEW (GAP-1)** - Google OAuth @waooaw.com, RBAC, rate limiting, audit logging, proxy routes
- **Mobile Push (Port 8017)** - `component_mobile_push_notification_service.yml` - **NEW (GAP-4)** - FCM integration, device token registry, offline queue
- **Stripe Webhook (Port 8018)** - `component_stripe_webhook_security.yml` - **NEW (GAP-7)** - Signature verification, idempotency, Temporal saga
- **Health Aggregator (Port 8019)** - `component_health_aggregation_service.yml` - **NEW (GAP-10)** - Prometheus scraping, aggregated health API

**Support Services (3):**
- **Manifest (Port 8011)** - `unified_agent_configuration_manifest.yml` - Versioned capability registry, diff/classify API (proposal vs evolution), source of truth for agent capabilities
- **Help Desk (Port 8012)** - 8 YAMLs (intake, triage, case state machine, escalation, evidence, handoff packets HDP-1.0)
- **Policy/OPA (Port 8013)** - `policy_runtime_enforcement.yml` - **CRITICAL** - Open Policy Agent for trial mode enforcement, PDP/PEP split, attested decisions, sandbox routing

**Reusable Component Library (libs/workflows):**
- Genesis Certification Gate, Governor Approval Workflow (mobile push, 24hr veto), Architecture Review Pattern, Ethics Review Pattern, Health Check Protocol, Rollback Procedure, Versioning Scheme, Audit Logging Requirements

---

## 🖥️ User Portal Components

**Customer Portal (CP) - 18 Components** (docs/CP/user_journey/)
- Status: ✅ v1.0 Complete - Ready for implementation
- Lifecycle: 7 stages, 19 sub-journeys, 35+ API endpoints
- Components: Marketplace, Agent Discovery, Trial Management, Subscription, Support, Notifications, Approvals, Analytics

**Platform Portal (PP) - 10 Core Components + 10 Gap Resolution Components** (docs/PP/user_journey/)
- Status: ✅ v1.0 Gap Resolution Complete - Critical gaps resolved, ready for Plant phase handoff
- Users: 7 roles (Admin, Platform Governor, Agent Orchestrator, Industry Manager, Infrastructure Engineer, Support Agent, Analyst)
- **Phase 1 (Seed):** 10 Core Components + 10 Critical Gap Resolutions (19/19 gaps resolved)
- **Phase 2 (Plant):** Genesis webhook production implementation (Systems Architect + Vision Guardian)

**Core PP Components (10):**
  1. `component_pp_authentication_oauth.yml` - Google OAuth 2.0 (@waooaw.com domain restriction)
  2. `component_pp_rbac_system.yml` - Role-based access control (7 hierarchical roles)
  3. `component_pp_health_dashboard.yml` - Platform health monitoring (13 microservices, ELK logs, queue metrics)
  4. `component_pp_helpdesk_ticketing.yml` - Internal ticketing (support, incident, feature_request with SLA tracking)
  5. `component_pp_user_management.yml` - User CRUD, role assignment (Admin-only)
  6. `component_pp_subscription_management.yml` - Subscription audit, agent run forensics, health scores, incident management
  7. `component_pp_agent_orchestration.yml` - Agent creation (5-step: Genesis validation → CI/CD → handoff), Base Agent Core interface
  8. `component_pp_sla_ola_management.yml` - SLA/OLA tracking, compliance monitoring, breach alerts, SLA credit workflow
  9. `component_pp_industry_knowledge.yml` - Knowledge scraping, embeddings, agent retuning (Genesis approval gate), rejection recovery
  10. `component_pp_cp_integration.yml` - Async PP→CP notifications via GCP Pub/Sub (8 event types)

**Gap Resolution Components (10 Critical):**
  1. `component_pp_gateway_service.yml` (GAP-1) - PP Gateway Port 8015, OAuth, RBAC, rate limiting, audit logging
  2. `component_genesis_webhook_api_stub.yml` (GAP-2) - Genesis webhook contract stub for Plant phase, mock server for testing
  3. `component_mobile_push_notification_service.yml` (GAP-4) - FCM integration, 4 notification types, deep linking
  4. `component_trial_mode_pep_enforcement.yml` (GAP-5) - PEP diagram, trial restrictions (7 days, 10 tasks/day)
  5. `component_database_schema_unification.yml` (GAP-6) - 3 PostgreSQL schemas (public, pp_portal, audit), unified users, RLS
  6. `component_stripe_webhook_security.yml` (GAP-7) - Stripe signature verification, idempotency, Temporal saga
  7. `component_agent_workspace_storage.yml` (GAP-8) - GCS bucket structure, workspace isolation, lifecycle rules
  8. `component_constitutional_query_api.yml` (GAP-9) - Vector search (Pinecone), precedent seeds, confidence scoring
  9. `component_health_aggregation_service.yml` (GAP-10) - Prometheus scraping, aggregated health API
  10. `component_pp_cp_integration.yml` (GAP-3 extension) - Extended with 3 new event types (subscription_created, agent_provisioned, trial_started)

**Deep Audit Findings (2026-01-08):**
- **Total Gaps Identified:** 60 gaps across 6 categories
  * Critical: 10 (RESOLVED ✅)
  * High Priority: 10 (deferred to implementation)
  * Medium: 10 (deferred)
  * Low: 10 (v1.1)
  * Design Inconsistencies: 10 (technical debt)
  * Constitutional Compliance: 5 (implementation phase)
  * Integration: 5 (implementation phase)
- **Documentation:** DEEP_AUDIT_GAP_ANALYSIS.md (6,000 lines), PP_GAP_RESOLUTION_SUMMARY.md (1,500 lines)

**Plant Phase Handoff (Next):**
- Systems Architect: Design Genesis webhook production architecture (scalability, resilience, precedent seed storage)
- Vision Guardian: Define constitutional validation criteria (bias detection, harmful content rules, alignment metrics)
- Genesis Integration: Replace mock server with production webhook, constitutional query API integration
- Timeline: 3-4 weeks after Plant phase kickoff

---

## 🤖 ML-Integrated Foundational Dimensions

**Status:** ✅ Complete (2026-01-08) - 4 dimensions with 8 lightweight CPU-based ML models (<200ms inference, no GPU cost)

### Dimension Architecture

**4 Foundational Dimensions:**
1. **Skills** - Atomic work units (base_skill.yml, 1017 lines)
   * ML Integration: DistilBERT (routing 0.89 confidence), MiniLM (matching 0.92 similarity), LSTM (timeout MAPE 6.7%)
   * 3 Skills Simulated: SKILL-RESEARCH-001 (PubMed), SKILL-WRITE-001 (healthcare content), SKILL-FACT-CHECK-001 (bias detection)
   * 12 Gaps: 2 P0 (Phi-3-mini timeout, PHI detection audit) FIXED ✅, 4 P1, 6 P2
   * Commit: 7697856

2. **JobRole** - Composable skill bundles (base_job_role.yml, 1040 lines)
   * ML Integration: DistilBERT (recommendation), MiniLM (boundary validation 0.8 threshold), Phi-3-mini (parsing)
   * 3 JobRoles Simulated: JOB-HC-001 (Healthcare Content Writer), JOB-EDU-001 (Math Tutor), JOB-SALES-001 (B2B SDR)
   * 10 Gaps: 2 P0 (fast-escalation cache FIXED ✅, MiniLM threshold failed ⚠️), 3 P1, 5 P2
   * Commit: 10c6126

3. **Team** - Multi-agent coordination (base_team.yml, 567 lines)
   * ML Integration: Prophet (capacity forecasting MAPE <15%), DistilBERT (task assignment), LSTM (communication overhead)
   * 2 Teams Simulated: TEAM-HC-001 (scale-up trigger), TEAM-SALES-001 (team split at 6 agents)
   * 9 Gaps: 1 P0 (immediate Prophet retraining) FIXED ✅, 3 P1, 5 P2
   * Commit: 3b2f266

4. **Industry/Domain** - Compliance enforcement (base_industry.yml, 571 lines)
   * ML Integration: BART (HIPAA-compliant summaries), MiniLM (industry embeddings), Logistic Regression (PHI detection FNR <5%), Phi-3-mini (knowledge extraction)
   * 3 Industries Simulated: IND-HC (Healthcare HIPAA), IND-EDU (Education CBSE), IND-SALES (Sales CAN-SPAM)
   * 8 Gaps: 2 P0 (daily PHI audit, dual-layer fallback) FIXED ✅, 2 P1, 4 P2
   * Commit: 6b5e118
   * **CRITICAL:** Highest ML dependency (HIPAA/FDA/GDPR violations → legal liability)

**Total:** 3,195 lines, 8 ML models, 39 gaps (7 P0, 9 P1, 23 P2), 6/7 P0 fixes (85% success rate)

### ML Models Inventory

**8 Lightweight CPU-Based Models** (No GPU cost, <200ms inference):

1. **DistilBERT** (66MB, ONNX Runtime)
   * Use Cases: Skill routing, JobRole recommendation, task assignment
   * Inference: 50-100ms
   * Accuracy: >0.85 confidence threshold
   * Location: Skills (routing), JobRole (recommendation), Team (assignment)

2. **BART-base** (140MB, ONNX Runtime)
   * Use Cases: Text summarization, HIPAA-compliant summaries, seed extraction
   * Inference: 100-200ms
   * Accuracy: PHI removed, age-appropriate (Education)
   * Location: Skills (summarization), Industry (content summaries)

3. **all-MiniLM-L6-v2** (22MB, sentence-transformers)
   * Use Cases: Semantic embeddings, skill matching, boundary validation
   * Inference: 30-50ms
   * Accuracy: >0.85 similarity (Skills), >0.8 boundary check (JobRole)
   * Storage: Vector DB (Weaviate/Qdrant) with industry namespaces (healthcare, education, sales)
   * Location: Skills (matching), JobRole (boundaries), Industry (embeddings)

4. **Phi-3-mini** (1GB 4-bit quantized, ONNX Runtime)
   * Use Cases: NLU, conversational, request parsing, knowledge extraction
   * Inference: 150-300ms (dynamic timeout: content_length * 0.45s)
   * Fallback: Keyword extraction (regex patterns)
   * Location: Skills (content generation), JobRole (parsing), Industry (extraction)

5. **Prophet** (10MB, Facebook Time-Series)
   * Use Cases: Team capacity forecasting (7/30 day horizon), scale triggers
   * Inference: 50ms
   * Accuracy: MAPE <15%
   * Trigger: Scale-up if predicted_capacity >0.85 for 7 days
   * Location: Team (capacity prediction)

6. **Logistic Regression** (<1MB, scikit-learn)
   * Use Cases: PHI detection (HIPAA compliance), binary classification
   * Inference: 5ms
   * Accuracy: FNR <5% (weekly audit → DAILY after P0 fix)
   * Fallback: Dual-layer (Secondary LR 512 features → Regex last resort)
   * Location: Industry (Healthcare PHI detection) - **CRITICAL P0**

7. **LSTM Tiny** (5MB, TensorFlow Lite)
   * Use Cases: Execution timeout prediction, communication overhead
   * Inference: 10ms
   * Accuracy: MAPE <10% (Skills), <20% (Team)
   * Formula: team_size * (team_size - 1) * 0.5 hours/week (fallback)
   * Location: Skills (timeout), Team (communication)

8. **Vector DB** (Weaviate/Qdrant)
   * Use Cases: Constitutional queries, industry-specific context retrieval
   * Embeddings: MiniLM (384-dim)
   * Namespaces: healthcare (3,245 docs), education (2,891 docs), sales (1,567 docs)
   * Query: Cosine similarity >0.8
   * Location: Constitutional Layer, Industry (domain context)

**Model Versioning (P0 Fix - agent_architecture_layered.yml):**
- ml_models.yml (6th EEPROM file): Exact versions for reproducibility
- Boot validation: Check ml_models.yml vs loaded models, emit agent.model.drift on mismatch
- Governance: Escalate to Governor on version drift

### Constitutional Compliance

**All 4 Dimensions Audited:**
- Skills: ✅ PASS (5 layers integration, deny-by-default, task boundaries)
- JobRole: ✅ PASS (7/8 checks, 1 warning - MiniLM threshold)
- Team: ✅ PASS (8/8 checks - single Governor, Manager mandatory, scaling approval)
- Industry: ✅ PASS (8/8 checks - PHI blocking, boundary enforcement, namespace isolation)

**Critical P0 Fixes Applied:**
1. Skills: Phi-3-mini dynamic timeout (content_length * 0.45s) - handles >2000 word generation
2. Skills: PHI detection weekly audit (Vision Guardian retrains if FNR >5%)
3. JobRole: Fast-escalation cache (common ambiguous tasks pre-approved, <500ms)
4. Team: Immediate Prophet retraining after scaling (no 24-hour delay)
5. Industry: Daily PHI audit (not weekly) with real-time FNR monitoring
6. Industry: Dual-layer PHI fallback (Secondary LR → Regex) - 8% FNR acceptable for fallback

**Gap Distribution:**
- P0 (Critical): 7 gaps → 6 FIXED ✅ (85% success rate), 1 FAILED ⚠️ (JobRole MiniLM threshold text not found)
- P1 (High): 9 gaps → Deferred to Sprint 2 (logging, re-certification, cache cloning)
- P2 (Medium): 23 gaps → Deferred to Sprint 3 (monitoring, cost tracking, fallback testing)

### Integration with Agent Architecture

**Layer Mapping:**
- **Domain Layer:** Skills execution (SkillExecutor component)
- **Application Layer:** JobRole decision-making (DecisionEngine), Team coordination (Manager Agent)
- **Constitutional Layer:** Industry compliance enforcement (PHI detection, boundary validation)
- **Infrastructure Layer:** ML model inference (ONNX Runtime, scikit-learn, TensorFlow Lite)

**Manufacturing Process:**
- Genesis certifies: Skills → JobRoles → Teams → Industries
- Validation: Constitutional compliance, ML accuracy thresholds, boundary correctness
- Deployment: Hot-swap skills, blue-green JobRoles, team scaling, industry evolution

**Next Phase (Manufacturing Templates):**
- agent_design_template.yml: How Genesis designs new agents
- agent_specification_template.yml: Formal agent spec format
- Genesis rendering logic: Instantiate agent from spec (Skills + JobRole + Team + Industry)
- First Agent Implementation: Manager, Healthcare Content Writer, Math Tutor, or Sales SDR

**Constitutional Mandates (PP):**
- ❌ PP users **cannot** access customer core data (industry_data, strategic_plans)
- ✅ PP users **can** view agent run logs (forensics: inputs, outputs, errors)
- ✅ All agent creations/retuning require Genesis validation
- ❌ Admin **cannot** override Genesis rejection
- ✅ Force actions (cancel subscription) require Admin approval + reason
- ✅ Blue-green deployment with rollback safety
- ✅ Full audit trails (pp_audit_logs)

---

**Architecture Compliance**: See [ARCHITECTURE_COMPLIANCE_AUDIT.md](../ARCHITECTURE_COMPLIANCE_AUDIT.md) for gap analysis and implementation roadmap

**Implementation Proposal**: See [ARCHITECTURE_PROPOSAL.md](../ARCHITECTURE_PROPOSAL.md) for complete technical specification

---
## Constitutional Engine

```yaml
constitution_engine:
  version: "1.2"
  ...

  ethics:
    doctrine:
      - "Ethics is structural: enforced through gates, routing, auditability, and containment."
      - "When ethical uncertainty exists, default behavior is refuse/escalate/contain (not improvise)."
      - "Speed, revenue, or customer pressure must not bypass ethics gates."
    
    immutable_agent_principles:
      # Constitutional Amendment AMENDMENT-001 (2026-01-07)
      - principle: "Agent Specialization"
        description: "Agents are specialized workforces (Jobs), not generalized assistants. Restrictive boundaries force excellence."
      - principle: "Skill Atomicity"
        description: "Skills are atomic, autonomous, certifiable units of work with Think→Act→Observe cycles."
      - principle: "Memory Persistence"
        description: "Agent memory is filesystem-persistent and append-only. No context-ephemeral state."
      - principle: "Constitutional Embodiment"
        description: "Constitution embedded via vector embeddings, semantic search, RAG, and learning. Agents query constitution before decisions."

    risk_triggers:
      # Risk-based triage with graduated escalation (prevents Vision Guardian bottleneck)
      level_1_auto_block:
        - "deceptive_intent_detected"
        - "regulated_domain_without_approval"  # healthcare, financial advice
        - "privacy_breach_certain"
        - "irreversible_harm_possible"
      
      level_2_escalate_to_vision_guardian:
        - "uncertain_truth_claims_with_high_blast_radius"  # narrowed from original
        - "sensitive_context_requires_human_review"  # politics, religion, health
        - "commitment_made_without_approval"
        - "data_minimization_violated"
      
      level_3_allow_with_disclaimer:
        - "uncertain_truth_claims_with_low_blast_radius"  # auto-inject hedging
        - "subjective_opinion_stated_as_fact"
        - "minor_ambiguity_in_communication"
      
      level_4_log_only:
        - "routine_communication"
        - "internal_coordination"
        - "artifact_draft_not_sent"
        - "manager_internal_delegation"  # Manager assigns tasks to team members (Precedent Seed GEN-002)
        - "team_member_draft_submission"  # Team member submits output to Manager

    mandatory_gates:
      communication:
        required_checks:
          - "no_deception_or_misrepresentation"
          - "no_unapproved_commitments"
          - "state_uncertainty_when_not_certain"
          - "trace_link_required"
        on_triggered_risk:
          required_behavior:
            - "escalate_to_vision_guardian"
            - "request_governor_clarification"
      execution:
        required_checks:
          - "minimize_blast_radius"
          - "rollback_or_containment_path_exists"
          - "permissions_are_minimal"
          - "trace_link_required"
        on_triggered_risk:
          required_behavior:
            - "escalate_to_vision_guardian"
            - "require_explicit_governor_approval"

    incident_codes:
      - code: "ETH-UNCLEAR"
        meaning: "Ethical implications unclear; requires escalation and possible containment."
      - code: "ETH-DECEPTION-RISK"
        meaning: "Risk of misleading/deceptive output or omission."
      - code: "ETH-PRIVACY-RISK"
        meaning: "Risk of privacy breach, data misuse, or sensitive exposure."
      - code: "ETH-HARM-RISK"
        meaning: "Risk of harm to user/third party."
      - code: "ETH-REGULATED"
        meaning: "Regulated/safety-critical context detected; default posture tightens."

    precedent_seed_prefix: "ETH-"
    seed_rule:
      - "Ethics-related Precedent Seeds may only add gates or clarify definitions; never weaken protections."
    
    precedent_seed_lifecycle:
      states: ["active", "superseded", "deprecated", "archived"]
      versioning: "seeds evolve via supersession (new version replaces old); immutability preserved"
      query_behavior: "default returns active seeds; historical analysis available via archive API"
      
  governance_session_rules:
    single_governor_invariant:
      platform_scope: "Exactly one Platform Governor session active at any time"
      engagement_scope: "Exactly one Engagement Governor per engagement_id"
    
    enforcement: "session_manager + distributed locks on approval_request_id"
    violation_detection: "concurrent login OR lock conflict → reject + CONSTITUTIONAL-VIOLATION audit"
    
    break_glass_override:
      who: "Vision Guardian agent"
      when: "Governor session exhibits ethics violation pattern"
      action: "forcibly terminate session + escalate to constitutional review"
  
  governance_agent_isolation:
    constitutional_requirement: "Genesis, Systems Architect, Vision Guardian must not share fate or collude"
    
    minimum_viable_isolation:
      mvp: "separate processes with separate credentials on shared infrastructure ($40/month)"
      production: "separate nodes/services with network isolation ($150-300/month)"
      enterprise: "separate infrastructure projects with separate billing ($2000+/month)"
    
    verification_requirement:
      frequency: "daily"
      check: "no cross-agent IAM access in audit logs"
      on_violation: "constitutional breach → suspend all + Governor escalation"
  
  platform_budget_constraint:
    total_monthly_cap: "$100 USD (infrastructure + APIs + tools)"
    enforcement:
      - "80% utilization: agents propose cost optimizations"
      - "95% utilization: suspend non-critical agents (preserve governance)"
      - "100% utilization: halt all except Governor escalations"
    
    cost_guards:
      per_agent_daily_cap: "$5"
      per_execution_cap: "$0.50"
      on_breach: "suspend agent + escalate with cost report"
  
  tooling_selection_policy:
    constitutional_requirement: "All platform tools must be explicitly documented with rationale, cost, and alternatives considered"
    selection_criteria:
      - "open_source_free_secured_preferred"
      - "lightweight_low_cost_high_availability"
      - "gcp_native_where_possible"
      - "cloud_run_first_for_scale_flexibility"
      - "budget_governance_enforced"
    
    approved_stack:
      database: "PostgreSQL Cloud SQL (managed, HA, append-only via triggers)"
      message_bus: "Google Cloud Pub/Sub (schema enforcement, DLQ, at-least-once delivery)"
      secrets: "Google Secret Manager (per-engagement isolation, rotation, audit)"
      compute: "Google Cloud Run (serverless, scale-to-zero, blue/green deployments)"
      observability: "Google Cloud Monitoring + Logging (GCP-native, free tier)"
      frontend_web: "React 18 + Vite + FastAPI + Tortoise ORM"
      frontend_mobile: "Flutter 3.x (iOS/Android single codebase)"
      ai_api: "Groq primary (cost), OpenAI GPT-4o fallback (quality)"
      iac: "Terraform with single YAML driver (infrastructure.yaml)"
      pdp: "Open Policy Agent (OPA) on Cloud Run"
      development: "GitHub Codespaces (cloud-based, consistent environment)"
    
    tooling_changes:
      requires: "Evolution proposal (Genesis classification)"
      rationale_mandatory: true
      cost_impact_assessment: true
      migration_strategy_required: true
    
    authoritative_document: "main/Foundation/TOOLING_SELECTION_DECISION.md"
  
  agent_coordination_models:
    # Evolution EVOLUTION-001 (2026-01-06), Precedent Seed GEN-002
    
    individual_agent:
      description: "Single agent executes work, Governor approves external execution"
      pricing: "₹8,000-18,000/month (skill-dependent)"
      approval_boundary: "Governor approves ALL external communication and execution"
      use_cases: ["focused skills", "simple workflows", "single deliverable type"]
    
    team_coordination:
      description: "Manager Agent coordinates 2-4 specialists, internal delegation permitted"
      pricing: "₹19,000-30,000/month (team of 3-5: Manager + specialists)"
      
      delegation_boundary:
        manager_internal_authority:
          - "task_decomposition_and_assignment"  # Decompose goal into tasks, assign to team members
          - "draft_review_and_feedback"  # Review team outputs, request revisions
          - "progress_tracking"  # Monitor velocity, identify blockers
          - "shared_context_management"  # Update team workspace with customer feedback
          governor_approval_not_required: true
        
        governor_external_authority:
          - "external_communication"  # Send to customer or external systems
          - "external_execution"  # Write/delete/execute on external systems
          governor_approval_required: true
      
      team_workspace:
        isolation: "per_team_per_engagement"  # Each team has isolated shared context
        access_control:
          manager: ["read: all", "write: reviews, shared_context"]
          team_members: ["read: assigned_tasks_only", "write: own_outputs_only"]
          customer_governor: ["read: all", "write: customer_feedback, goals"]
          helpdesk: ["read: all", "write: none"]  # Read-only during Manager suspension
      
      genesis_certification:
        required_before_activation: true
        validates: ["team_composition", "skill_coverage", "engagement_scope_match"]
        outputs: ["team_manifest", "team_workspace_provisioned", "manager_assigned"]
      
      helpdesk_mode:
        trigger: "Manager suspended (policy violation or performance failure)"
        helpdesk_scope: ["answer_customer_questions", "provide_workspace_access", "coordinate_genesis_remediation"]
        helpdesk_prohibitions: ["no_task_assignment", "no_draft_review", "no_external_execution"]
        duration: "2-3 days (until new Manager assigned or team dissolved)"
        cost: "$2/day (platform absorbs)"
      
      mobile_approvals:
        push_notifications: true
        approval_target_latency: "<5 minutes (from Manager request to Governor decision)"
        offline_support: "queue decisions for sync when connectivity restored"
      
      authoritative_charters:
        - "main/Foundation/manager_agent_charter.md"
        - "main/Foundation/helpdesk_agent_charter.md"
      
      authoritative_protocols:
        - "main/Foundation/policies/team_coordination_protocol.yml"
        - "main/Foundation/policies/team_governance_policy.yml"
        - "main/Foundation/policies/mobile_ux_requirements.yml"
  
  agent_dna_model:
    # Constitutional Amendment AMENDMENT-001 (2026-01-07)
    # Authoritative Document: main/Foundation/amendments/AMENDMENT_001_AI_AGENT_DNA_JOB_SKILLS.md
    
    filesystem_memory:
      agent_state_directory: "agents/{agent_id}/state/"
      
      initialization_authority: "Genesis only (part of Job certification)"
      initialization_timing: "Before Job marked certified (status: draft → certified only after DNA initialized)"
      initialization_validation:
        - "All 5 files present (plan.md, errors.jsonl, precedents.json, constitution_snapshot, audit_log.jsonl)"
        - "Write permissions verified"
        - "Disk space >100MB available"
        - "Hash chain root established"
      
      initialization_failure_handling:
        - "Retry 3x with exponential backoff (1s, 2s, 4s)"
        - "If all retries fail → REJECT Job certification"
        - "Log to genesis audit trail with failure reason"
        - "Escalate to Platform Governor if infrastructure issue (disk full, permission denied)"
      
      required_files:
        - "plan.md"  # Goals + checkboxes (append-only)
        - "errors.jsonl"  # Failure log (append-only)
        - "precedents.json"  # Locally cached Precedent Seeds (seeded with GEN-001, GEN-002, GEN-003)
        - "constitution_snapshot"  # Version agent certified under (e.g., 'constitution_version: 1.2, certified_date: 2026-01-07, amendments: [AMENDMENT-001]')
        - "audit_log.jsonl"  # Hash-chained decision log (Genesis_hash as first entry)
    
    attention_discipline:
      - "Re-read plan.md before every decision"
      - "Check precedents.json before vector DB query"
      - "Append to errors.jsonl on any failure (never modify history)"
      - "Validate against constitution_snapshot (detect L0/L1 drift)"
    
    append_only_invariant:
      - "plan.md: append checkpoints, never delete past goals"
      - "errors.jsonl: append failures, never modify entries"
      - "audit_log.jsonl: hash-chained (sha256), tampering detected"
    
    vector_embeddings:
      embedding_model:
        development: "OpenAI text-embedding-3-small (1536 dimensions, $0.02/1M tokens)"
        production: "OpenAI or open-source (sentence-transformers) if cost >$50/month"
      
      vector_database:
        development: "Chroma (file-based, <10K chunks, simple)"
        production: "Qdrant (scalable, filters for agent_id/job_id/industry, <100ms queries)"
      
      constitutional_chunks:
        L0_principles: 5
        L1_structure: 15
        L2_data_contracts: 20
        L3_operational_protocols: 10  # per agent
        precedent_seeds: 1  # per seed
    
    semantic_search:
      query_routing:
        step_1_classify_query:
          constitutional_indicators: ["can I", "should I", "allowed to", "approval required", "authority", "delegate", "escalate"]
          industry_indicators: ["HIPAA", "FDA", "FERPA", "SOX", "GDPR", "medical", "patient", "clinical", "financial", "educational"]
          classification_logic: "If query contains constitutional_indicators → route to precedents.json + Constitutional Vector DB. If query contains industry_indicators → route to industry_context.json + Industry Vector DB. If ambiguous → constitutional first (deny-by-default principle)."
        
        step_2_cache_first:
          constitutional_queries: "Check precedents.json cache → if miss, query Constitutional Vector DB"
          industry_queries: "Check industry_context.json cache → if miss, query Industry Vector DB"
        
        step_3_result_caching:
          constitutional_queries: "DO NOT cache locally (precedents.json synced daily from central seeds)"
          industry_queries: "CACHE if query frequency >= 3 (add to industry_context.json top 100 terms)"
      
      query_pattern:
        - "Think Phase: Query constitution before decision"
        - "Classify query: Constitutional (approval/authority) or Industry (domain knowledge)"
        - "Route to appropriate Vector DB (Constitutional or Industry)"
        - "Retrieve top 5 relevant chunks (filters: layer, agent_id, industry)"
        - "Example: 'Can I delegate task X?' → Constitutional DB → L1 manager_agent_charter + GEN-002"
        - "Example: 'HIPAA patient communication requirements?' → Industry DB → industries/healthcare/regulations/hipaa_guidelines.md"
      
      cost_control:
        query_budget_per_agent_daily: "$1"  # Max $1/day per agent (30 agents = $30/month, leaves $70 for other services)
        query_cost_estimate: "$0.001"  # Per-query cost (Qdrant managed tier)
        max_queries_per_skill: 10  # Limit queries during Think phase (forces efficient constitutional design)
        budget_exhaustion_behavior:
          - "80% utilization: Agent logs warning, continues execution"
          - "95% utilization: Agent escalates to Manager (review skill efficiency)"
          - "100% utilization: Agent pauses execution, escalates to Governor (approve emergency budget increase OR suspend agent)"
        
        cache_optimization:
          - "Check precedent cache FIRST (free)"
          - "Query vector DB ONLY if cache miss (<20% of queries if cache hit rate >80%)"
          - "Fine-tuned model bypasses vector DB for common queries (target: 50% reduction in queries by Month 3)"
    
    rag_pattern:
      steps:
        - "Retrieve: Semantic search top 5 chunks"
        - "Inject: Chunks into agent prompt context"
        - "Decide: Agent reasons with retrieved context (not from memory)"
        - "Log: Which chunks used, decision outcome, confidence score"
      
      benefits:
        - "Agent doesn't need to remember entire constitution"
        - "Constitutional updates propagate immediately (re-embed changed chunks)"
        - "Explainable decisions (audit log shows which chunks influenced)"
        - "Scales to large constitutions (>100 pages)"
    
    fine_tuning_layer:
      trigger_conditions:
        - "Monthly fine-tuning when: 100+ new Precedent Seeds OR 1000+ checks with >95% accuracy"
      
      training_data:
        - "Input: Constitutional query (e.g., 'Can I access customer financial data?')"
        - "Output: Expected decision + reasoning (e.g., 'DENY - L0 deny-by-default, no Governor approval')"
      
      benefits:
        - "Faster decisions (fewer semantic search queries)"
        - "Pattern recognition (common deny scenarios cached in model weights)"
        - "Cost reduction (fine-tuned queries cheaper than GPT-4 + semantic search)"
    
    precedent_cache:
      location: "agents/{agent_id}/state/precedents.json"
      
      cache_strategy:
        - "Check local precedents.json BEFORE querying vector DB"
        - "Update relevance scores based on usage (cache hot precedents)"
        - "Sync with centralized Precedent Seeds daily"
        - "Prune cache entries with <0.7 relevance and 0 hits in 30 days"
      
      schema:
        fields:
          - "seed_id (e.g., GEN-002)"
          - "seed_content (full text)"
          - "relevance_score (0.0 to 1.0)"
          - "last_accessed (timestamp)"
          - "cache_hit_count (integer)"
  
  skill_lifecycle:
    # Constitutional Amendment AMENDMENT-001 (2026-01-07)
    # Skills are atomic autonomous capabilities with Think→Act→Observe cycles
    
    certification:
      authority: "Genesis only"
      
      process:
        - "Skill definition submitted via API or Platform Portal"
        - "Validate Think→Act→Observe cycle is complete and testable"
        - "Validate inputs/outputs match data contract schemas"
        - "Validate approval gates present for external interactions"
        - "Test skill in sandbox (simulate failures, validate outputs)"
        - "Issue Skill ID (e.g., SKILL-HC-001), add to certified_skills registry"
        - "Emit Precedent Seed documenting edge cases discovered"
      
      atomicity_requirements:
        - "Skill completes in <10 minutes OR checkpoints progress every 10 minutes"
        - "Skill is idempotent (re-running produces same output or gracefully handles duplicates)"
        - "Skill has clear success/failure conditions (no ambiguity)"
        - "Skill logs all external interactions (API calls, file writes) to audit trail"
      
      rejection_criteria:
        - "Incomplete Think→Act→Observe cycle"
        - "Inputs/outputs don't match data contracts"
        - "Missing approval gates for external interactions"
        - "Undocumented failure modes"
        - "Non-idempotent execution"
    
    execution:
      think_phase:
        - "Constitutional query via semantic search"
        - "Check precedent cache for relevant seeds"
        - "Determine if approval required (escalate to Governor if yes)"
        - "Example: 'Can I execute SKILL-HC-001?' → query L0 deny-by-default + GEN certification rules"
      
      act_phase:
        - "Execute skill steps with PEP validation"
        - "Validate inputs against data contract schemas"
        - "Check rate limits, API quotas, resource availability"
        - "Log all external interactions to audit trail"
      
      observe_phase:
        - "Log outcome to audit_log.jsonl (SUCCESS, FAILURE, APPROVAL_REQUIRED)"
        - "Update precedent cache if novel pattern detected"
        - "Mark checkpoint in plan.md (✅ Skill completed)"
        - "Hash outcome: sha256(previous_hash + this_event)"
      
      iteration:
        - "If FAILURE → log to errors.jsonl, check failure mode, retry OR escalate to Manager"
        - "If SUCCESS → mark checkpoint, proceed to next skill"
        - "If APPROVAL_REQUIRED → emit approval request to Governor, pause, resume when approved"
      
      orchestration_safety:
        max_call_depth: 5  # Prevent infinite recursion (Skill A → B → C → D → E max)
        timeout_per_skill: 600  # 10 minutes (atomicity requirement)
        deadlock_detection_window: 1800  # 30 minutes (if 2+ skills waiting for dependencies)
        circular_dependency_detection: true  # Manager validates dependency graph before delegation
        
        on_timeout:
          - "Mark skill FAILURE"
          - "Log to errors.jsonl with timeout reason"
          - "Move to next skill in execution plan"
          - "If 3+ timeouts in sequence → suspend agent, escalate to Genesis"
        
        on_deadlock:
          - "Fail lowest-priority skill (break deadlock)"
          - "Log deadlock pattern to audit trail"
          - "Retry execution graph without failed skill"
          - "Draft Precedent Seed documenting deadlock pattern for Genesis review"
    
    learning:
      precedent_seed_generation:
        trigger_criteria:
          - "Novel decision pattern (not covered by existing seeds)"
          - "High confidence outcome (>0.9) repeated 3+ times"
          - "Failure mode discovered and resolved"
          - "Constitutional edge case clarified"
        
        lifecycle:
          - "Agent completes Think→Act→Observe cycle"
          - "Observe phase checks: 'Is this outcome novel?'"
          - "If YES → draft Precedent Seed, submit to Genesis for review"
          - "Genesis validates seed doesn't contradict existing seeds or constitution"
          - "Genesis approves seed, assigns Seed ID (e.g., MGR-001)"
          - "Seed added to vector DB, re-embedded for semantic search"
          - "All agents' local precedent caches updated within 24 hours"
    
    improvement:
      fine_tuning:
        - "Monthly fine-tuning (100+ seeds or 1000+ checks)"
        - "Pattern recognition improves decision speed and accuracy"
        - "Training set: historical audit logs (query, chunks retrieved, decision, outcome)"
      
      accuracy_tracking:
        - "Log confidence score for every decision"
        - "If <0.7 confidence → fallback to Genesis review"
        - "Track accuracy over time (expected vs actual outcome)"
  
  job_specialization_framework:
    # Constitutional Amendment AMENDMENT-001 (2026-01-07)
    # Jobs are industry/geography-specific workforce specializations
    
    job_definition_attributes:
      - "industry (Healthcare, Education, Sales, Marketing, Finance)"
      - "geography (North America, Europe, India)"
      - "job_description (e.g., 'B2B SaaS Content Writer for Healthcare')"
      - "required_skills (array of certified Skill IDs)"
      - "tasks (specific outcomes job achieves)"
      - "goals (success criteria, e.g., '4.5+ star rating')"
      - "planning_capability (boolean: multi-step planning or single-shot execution)"
      - "tool_usage (authorized APIs, databases, services)"
      - "validation_criteria (pre-deployment checks)"
      - "confirmation_gates (approval requirements)"
      - "learning_feedback_loop (how job improves)"
      - "completion_criteria (when job is 'done', e.g., '30-day trial complete')"
    
    certification:
      authority: "Genesis only"
      
      process:
        - "Job definition submitted via API or Platform Portal"
        - "Validate industry/geography are recognized categories"
        - "Validate all required skills are certified and available"
        - "Validate tool authorizations don't violate deny-by-default"
        - "Validate approval gates align with L0 external approval requirement"
        - "Issue Job ID, add to certified_jobs registry"
        - "Emit Precedent Seed documenting rationale"
      
      rejection_criteria:
        - "Unknown industry/geography"
        - "Uncertified skills required"
        - "Unauthorized tools requested"
        - "Missing approval gates for external interactions"
    
    industry_tuning:
      healthcare:
        - "Regulatory compliance: HIPAA (US), GDPR (EU)"
        - "Validation: Medical facts reviewed by licensed professional"
        - "Specialized skills: Research Healthcare Regulation, Fact-Check Medical Claims"
      
      education:
        - "Regulatory compliance: FERPA (US student privacy)"
        - "Validation: Content aligns with curriculum standards (CBSE, ICSE, State Boards)"
        - "Specialized skills: Personalize Learning Path, Assess Student Progress"
      
      sales:
        - "Regulatory compliance: CAN-SPAM (email), GDPR (lead data)"
        - "Validation: No unapproved commitments (pricing, features)"
        - "Specialized skills: Qualify Lead, Draft Outreach Email, Update CRM"
    
    geography_tuning:
      north_america:
        - "Legal compliance: CAN-SPAM, CCPA (California), sector-specific (HIPAA, SOX)"
        - "Timezone: ET, CT, MT, PT (business hours)"
        - "Language: English (US)"
      
      europe:
        - "Legal compliance: GDPR (strict), ePrivacy Directive, sector-specific (MDR for medical)"
        - "Timezone: GMT, CET, EET (business hours)"
        - "Language: English (UK), German, French, Spanish (multi-language support)"
      
      india:
        - "Legal compliance: IT Act 2000, DPDP Act 2023, sector-specific (RBI for fintech)"
        - "Timezone: IST (business hours)"
        - "Language: English, Hindi, regional languages (multi-language support)"
    
    tool_authorization:
      - "Explicit list of APIs, databases, external services per job"
      - "Deny-by-default: tools must be Genesis-approved"
      - "Example: Healthcare Content Writer authorized for [PubMed API, Google Docs, WordPress, Grammarly]"
      - "Tools NOT authorized: [Customer CRM, Financial systems, Code repositories]"
    
    task_boundaries:
      what_job_can_do:
        - "Example (Healthcare Content Writer): Draft blog posts, research regulations, fact-check medical claims"
      
      what_job_cannot_do:
        - "Example (Healthcare Content Writer): Publish without approval, access patient data, diagnose conditions"
    
    completion_criteria:
      trial_duration:
        - "7-day trial (quick validation, customer keeps deliverables)"
        - "30-day trial (full evaluation, monthly billing cycle)"
      
      success_metrics:
        - "Customer rating (e.g., 4.5+ stars out of 5)"
        - "Deliverables completed (e.g., 4 blog posts published)"
        - "Responsiveness (e.g., 2-hour average response time)"
      
      customer_decision_triggers:
        - "Approve: Continue subscription (auto-renew)"
        - "Cancel: End subscription (customer keeps trial deliverables)"
```
