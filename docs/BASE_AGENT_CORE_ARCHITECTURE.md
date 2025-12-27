# Base Agent Core Architecture

**WAOOAW Platform - Foundational Agent System**

*Version 1.0 | December 2024*

---

## Executive Summary

This document specifies the **WAAOOWAgent** base class - the foundational architecture for all 14 Centers of Excellence (CoEs) in the WAOOAW platform. It provides:

- **Unified agent framework** for consistent behavior across all agents
- **6-step wake-up protocol** for context preservation and state management
- **Hybrid decision framework** (deterministic + LLM) for cost-effective intelligence
- **Persistent memory system** (PostgreSQL + vector embeddings) for learning
- **GitHub integration** for autonomous operation and human escalation
- **Learning & improvement** mechanisms for continuous optimization

**WowVision Prime** is implemented as the first production agent inheriting from this base, serving as the platform's vision guardian.

---

## Table of Contents

1. [Philosophy & Design Principles](#1-philosophy--design-principles)
2. [Dual-Identity Framework](#2-dual-identity-framework)
3. [Architecture Overview](#3-architecture-overview)
4. [WAAOOWAgent Base Class](#4-waooawagent-base-class)
5. [6-Step Wake-Up Protocol](#5-6-step-wake-up-protocol)
6. [Memory System](#6-memory-system)
7. [Decision Framework](#7-decision-framework)
8. [GitHub Integration](#8-github-integration)
9. [Learning & Improvement](#9-learning--improvement)
10. [Inheritance Model](#10-inheritance-model)
11. [Agent Lifecycle](#11-agent-lifecycle)
12. [Safety & Validation](#12-safety--validation)
13. [Configuration & Deployment](#13-configuration--deployment)
14. [Cost Analysis](#14-cost-analysis)
15. [Example Implementations](#15-example-implementations)

---

## 1. Philosophy & Design Principles

### 1.1 Core Principles

**🎯 Single Responsibility**
- Each agent (CoE) has ONE clear domain of expertise
- Base class provides common capabilities, not domain logic
- Specialization through inheritance, not configuration

**🔄 Context Preservation**
- Agents are ephemeral (wake up, work, sleep)
- State persists between wake cycles in PostgreSQL
- 6-step protocol ensures continuity across restarts

**💰 Cost Optimization**
- LLM calls are expensive (~$15/1M tokens for Claude Sonnet 4.5)
- Deterministic logic handles 80%+ of decisions (free, instant)
- Vector memory reduces redundant LLM queries
- Decision caching prevents duplicate reasoning

**🧠 Learning by Default**
- Every action → outcome logged for learning
- Patterns recognized automatically via vector similarity
- Knowledge base grows with each iteration
- Future agents benefit from past experiences

**🔒 Safety First**
- Human escalation for ambiguous/risky actions
- Validation before execution
- Audit trail for all decisions
- Conservative fallbacks when uncertain

**🤝 Collaboration-Ready**
- Agents communicate via shared database
- Handoff packages for cross-CoE workflows
- Collaboration state tracking
- Event-driven coordination

---

## 2. Dual-Identity Framework

Every agent has **TWO identities** that define who they are and how they operate:

### 2.1 SPECIALIZATION (CoE Template - Immutable)

**What TYPE of agent am I?** (Platform-defined, same for all instances of this CoE)

```yaml
specialization:
  # Core Identity
  coe_name: "WowVision Prime"
  coe_type: "vision_guardian"
  domain: "Vision Enforcement"
  expertise: "3-layer vision stack validation"
  version: "1.0.0"
  
  # Responsibilities
  core_responsibilities:
    - "Validate file creations against vision"
    - "Review PRs for vision compliance"
    - "Process human escalations"
    - "Manage Layer 2 policies autonomously"
  
  # Capabilities (inherited from base + specialized)
  capabilities:
    technical:
      - "Deterministic vision rule validation"
      - "LLM-powered ambiguity resolution"
      - "Pattern recognition for violations"
      - "GitHub issue creation and management"
    business:
      - "Brand consistency enforcement"
      - "Vision alignment validation"
      - "Policy interpretation and application"
  
  # Constraints (immutable rules this CoE must follow)
  constraints:
    - rule: "NEVER generate Python code in Phase 1"
      reason: "Foundation phase focuses on architecture"
    - rule: "Always escalate Layer 1 violations to human"
      reason: "Core vision changes require human approval"
    - rule: "Cannot modify vision stack Layer 1"
      reason: "Layer 1 is immutable foundation"
  
  # Required Skills/Knowledge
  skill_requirements:
    - "Vision stack comprehension (Layers 1-3)"
    - "YAML/JSON parsing and validation"
    - "GitHub API integration"
    - "Brand consistency evaluation"
```

**Source**: Loaded from `waooaw/config/agent_config.yaml` (platform-defined)
**Lifecycle**: Immutable during agent operation, updated only via platform upgrades

---

### 2.2 PERSONALITY (Instance Identity - Mutable)

**Who SPECIFICALLY am I?** (Customer-defined on hire, unique per instance)

```yaml
personality:
  # Instance Identity
  instance_id: "uuid-12345"
  instance_name: "Yogesh"              # Given by hiring manager
  role_title: "Vision Guardian"        # Business context
  industry: "Digital Marketing"        # Domain context
  status: "active"                     # active, paused, terminated
  
  # Employment Context
  employer:
    business_id: "company_abc"
    company_name: "ABC Marketing Inc"
    company_type: "B2B SaaS"
    hired_at: "2025-01-15T10:00:00Z"
    contract_tier: "professional"      # starter, professional, enterprise
  
  # Customization (how this instance behaves)
  communication:
    tone: "professional"               # casual, professional, formal
    verbosity: "concise"               # concise, detailed, comprehensive
    language: "en-US"
    notification_channel: "slack"      # slack, email, github
    
  focus_areas:                         # Employer-specific priorities
    - "B2B brand consistency"
    - "Technical documentation clarity"
    - "Marketing copy alignment"
    
  preferences:
    working_hours: "09:00-18:00 IST"
    timezone: "Asia/Kolkata"
    escalation_contact: "@john_manager"
    approval_required_for:
      - "Layer 1 vision changes"
      - "Major policy updates"
  
  # Learning Context (employer-specific patterns)
  learned_preferences:
    - "Company prefers conversational tone over formal"
    - "Brand color #667eea must appear in all visuals"
    - "Tagline must include 'Agents Earn Your Business'"
```

**Source**: Loaded from `agent_instances` table in PostgreSQL (customer-defined)
**Lifecycle**: Mutable, updated based on employer feedback and learned patterns

---

### 2.3 WORK CONTEXT (Runtime State - Ephemeral)

**What am I CURRENTLY doing?** (Session-specific, resets each wake cycle)

```yaml
work_context:
  # Current Session
  current_wake: 3
  wake_started_at: "2025-12-24T17:58:00Z"
  
  # Active Work
  active_tasks: 12
  tasks_completed_this_wake: 0
  
  # Employer Projects (multi-tenant awareness)
  employer_projects:
    - project_id: "website_redesign"
      status: "in_progress"
      my_role: "Validate all marketing copy against brand vision"
      files_watched: ["frontend/index.html", "docs/BRAND_STRATEGY.md"]
  
  # Recent Activity
  recent_decisions:
    - timestamp: "2025-12-24T16:45:00Z"
      decision: "Approved PR #47 - homepage copy"
      confidence: 0.95
    - timestamp: "2025-12-24T15:30:00Z"
      decision: "Escalated issue #52 - off-brand tagline"
      reason: "Conflicts with Layer 1 brand identity"
  
  # Collaboration State
  pending_handoffs:
    - from_agent: "WowDomain"
      task_type: "validate_entity_naming"
      received_at: "2025-12-24T17:00:00Z"
```

**Source**: Loaded from `agent_context` table (system-tracked)
**Lifecycle**: Ephemeral, persisted between wake cycles, cleared periodically

---

### 2.4 Identity Separation of Concerns

| Component | Defined By | Stored In | Mutability | Scope |
|-----------|-----------|-----------|------------|-------|
| **Specialization** | WAOOAW Platform | Config files | Immutable | All instances of CoE |
| **Personality** | Customer/Employer | Database (`agent_instances`) | Mutable | Single instance |
| **Work Context** | System Runtime | Database (`agent_context`) | Ephemeral | Current session |

**Example:**
- **Specialization**: "I am a WowVision Prime agent - vision enforcement specialist"
- **Personality**: "I am Yogesh, YOUR vision guardian for ABC Marketing"
- **Work Context**: "Currently on wake #3, processing 12 tasks for your website redesign project"

**Marketplace Analogy:**
- **Pre-hire**: Agent shows specialization → "Marketing Agent - Content Specialist"
- **Post-hire**: Agent gains personality → "I'm Yogesh, your content creator, focused on B2B"

---

### 2.5 Identity API

```python
# Agent introduces itself
agent.introduce_self()
# → "I am Yogesh, a WowVision Prime agent specializing in vision enforcement. 
#    I work for ABC Marketing Inc as their Vision Guardian in Digital Marketing."

# Check what the agent can do
agent.specialization.can_do("create_github_issue")  # → True
agent.specialization.can_do("modify_layer1_vision")  # → False (constraint)

# Access employer context
agent.personality.employer.company_name  # → "ABC Marketing Inc"
agent.personality.focus_areas            # → ["B2B brand consistency", ...]

# Check current work state
agent.work_context.current_wake          # → 3
agent.work_context.active_tasks          # → 12
```

---

---

## 3. Architecture Overview

### 3.1 Design Philosophy

```
┌─────────────────────────────────────────────────────────┐
│                    WAOOAW Platform                      │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │         14 Centers of Excellence (CoEs)         │  │
│  │                                                 │  │
│  │  WowVision  WowDomain  WowAgentFactory  ...    │  │
│  │     ↓           ↓           ↓            ↓     │  │
│  └─────┼───────────┼───────────┼────────────┼─────┘  │
│        │           │           │            │        │
│        └───────────┴───────────┴────────────┘        │
│                        ↓                             │
│              ┌─────────────────────┐                 │
│              │   WAAOOWAgent       │                 │
│              │   (Base Class)      │                 │
│              │                     │                 │
│              │  DUAL IDENTITY:     │                 │
│              │  • Specialization   │                 │
│              │  • Personality      │                 │
│              │                     │                 │
│              │                     │                 │
│              │  DUAL IDENTITY:     │                 │
│              │  • Specialization   │                 │
│              │  • Personality      │                 │
│              │                     │                 │
│              │  CAPABILITIES:      │                 │
│              │  • Memory           │                 │
│              │  • Decision         │                 │
│              │  • GitHub           │                 │
│              │  • Learning         │                 │
│              │  • Wake Protocol    │                 │
│              └─────────────────────┘                 │
│                        ↓                             │
│        ┌───────────────┴───────────────┐            │
│        ↓                               ↓            │
│  PostgreSQL + Vector DB          GitHub API         │
└─────────────────────────────────────────────────────┘
```

**Key Design Principle**: 
- **Base Class = Skeleton/Anatomy** (capabilities all agents need)
- **Specialization = CoE Type** (what this agent does)
- **Personality = Instance Identity** (who this specific agent is)
- **Inheritance over Configuration**: Agents extend base class, not configure it

---

### 3.2 System Components

```yaml
WAAOOWAgent (Base Class):
  Core Capabilities:
    - 6-step wake-up protocol
    - Persistent memory (PostgreSQL + vector embeddings)
    - Hybrid decision framework (deterministic + LLM)
    - GitHub integration (issues, comments, PRs)
    - Learning & improvement mechanisms
    - Safety & validation framework
  
  Storage:
    - PostgreSQL: Structured data (context, decisions, tasks)
    - Pinecone: Vector embeddings (semantic memory recall)
    - Redis: Decision cache, session state
  
  External APIs:
    - GitHub: Issue management, PR reviews, comments
    - Anthropic Claude: LLM reasoning (Sonnet 4.5)
    - Pinecone: Vector similarity search
```

### 2.2 Agent Types (14 CoEs)

All inherit from `WAAOOWAgent`:

**1. WowVision Prime** - Vision Guardian (Phase 1)
- Enforces 3-layer vision stack
- Validates file creations against policies
- Processes human escalations

**2. WowDomain** - Domain Architecture (Phase 1)
- Manages domain model
- Validates entity relationships
- Ensures bounded context integrity

**3. WowAgentFactory** - Agent Bootstrapper (Phase 2)
- Creates new agents from templates
- Configures agent environments
- Tests agent capabilities

**4-14. Future CoEs** - Specialized domains
- WowMarketplace, WowAuth, WowPayment, etc.
- Each inherits base capabilities
- Each specializes for domain-specific work

---

## 3. WAAOOWAgent Base Class

### 3.1 Class Signature

```python
class WAAOOWAgent:
    """
    Base class for all WAOOAW platform agents.
    
    Provides common capabilities:
    - Persistent memory (PostgreSQL + vector embeddings)
    - 6-step wake-up protocol for context preservation
    - Hybrid decision framework (deterministic + LLM)
    - GitHub integration for autonomous operation
    - Learning & improvement mechanisms
    - Safety & validation framework
    
    Subclasses override:
    - _restore_identity(): Load agent-specific identity
    - _try_deterministic_decision(): Domain-specific rules
    - execute_task(): Agent-specific task execution
    - _get_pending_tasks(): Domain-specific task queue
    - _apply_learnings(): Use knowledge to improve
    """
    
    def __init__(self, agent_id: str, config: dict):
        """
        Initialize base agent with self-contained infrastructure setup.
        
        Initialization flow:
        1. Connect to database (or create GitHub issue if fails)
        2. Ensure schema exists (auto-create if missing)
        3. Connect to GitHub, Pinecone, Anthropic
        4. Ready for wake_up() protocol
        
        Args:
            agent_id: Unique identifier (e.g., "WowVision-Prime")
            config: Configuration dict with:
                - database_url: PostgreSQL connection string (Supavisor pooler)
                - github_token: GitHub API token
                - github_repo: Repository (e.g., "dlai-sd/WAOOAW")
                - pinecone_api_key: Pinecone API key (optional)
                - anthropic_api_key: Claude API key (optional)
        
        Raises:
            SystemExit: If critical infrastructure fails (after creating GitHub issue)
        """
```

### 3.2 Core Attributes

```python
# Identity
self.agent_id: str                    # Unique identifier
self.config: dict                     # Configuration
self.wake_count: int                  # Number of wake cycles
self.start_time: datetime             # Current wake start time

# Components
self.db: psycopg2.Connection          # PostgreSQL connection
self.github: Github                   # GitHub client
self.vector_memory: VectorMemory      # Pinecone integration
self.llm: anthropic.Anthropic         # Claude client

# State
self.context: dict                    # Current operational context
self.pending_tasks: List[dict]        # Tasks to execute
```

### 3.3 Public Methods

```python
# Lifecycle
wake_up() -> None                     # Execute full wake-up protocol
shutdown() -> None                    # Clean shutdown

# Decision Making
make_decision(request: dict) -> Decision  # Hybrid decision framework

# Memory Management
store_memory(type: str, key: str, data: dict) -> None
recall_memory(query: str, type: str = None) -> List[dict]

# GitHub Integration
create_github_issue(title: str, body: str, labels: List[str]) -> Issue
read_github_comments(issue_number: int) -> List[str]

# Learning
learn_from_outcome(action: dict, outcome: dict) -> None

# Task Execution
execute_task(task: dict) -> None      # OVERRIDE IN SUBCLASS
```

---

## 4. 6-Step Wake-Up Protocol

Based on the context preservation architecture, every agent wake-up follows this protocol:

### 4.1 Protocol Flow

```
┌─────────────────────────────────────────────┐
│         AGENT WAKE-UP PROTOCOL              │
└─────────────────────────────────────────────┘

Step 1: RESTORE IDENTITY
  ├─ Load agent-specific identity from vision/config
  ├─ Set role, responsibilities, constraints
  └─ Log: "✅ Identity: {agent_id} - {role}"

Step 2: LOAD DOMAIN CONTEXT
  ├─ Query PostgreSQL for latest context snapshot
  ├─ Restore operational state (phase, metrics, flags)
  └─ Load recent decisions and outcomes

Step 3: CHECK COLLABORATION STATE
  ├─ Query cross-CoE interaction log
  ├─ Check handoff packages from other agents
  └─ Review pending coordination requests

Step 4: REVIEW LEARNING QUEUE
  ├─ Load learnings from knowledge base
  ├─ Apply patterns to improve decision-making
  └─ Update internal heuristics

Step 5: EXECUTE ASSIGNED WORK
  ├─ Get pending tasks (agent-specific)
  ├─ Execute each task with error handling
  └─ Log outcomes for learning

Step 6: SAVE CONTEXT AND HANDOFF
  ├─ Serialize current context to PostgreSQL
  ├─ Version state snapshot (wake_count)
  ├─ Create handoff packages if needed
  └─ Log: "💤 {agent_id} sleeping (wake #{wake_count})"
```

### 4.2 Implementation

```python
def wake_up(self):
    """Execute 6-step wake-up protocol"""
    logger.info(f"🌅 {self.agent_id} waking up (wake #{self.wake_count})")
    
    try:
        # Step 1: Restore identity
        self._restore_identity()
        
        # Step 2: Load domain context
        self._load_domain_context()
        
        # Step 3: Check collaboration state
        self._check_collaboration_state()
        
        # Step 4: Review learning queue
        self._process_learning_queue()
        
        # Step 5: Execute assigned work
        self._execute_work()
        
        # Step 6: Save context and handoff
        self._save_context_and_handoff()
        
        self.wake_count += 1
        logger.info(f"💤 {self.agent_id} sleeping (wake #{self.wake_count})")
        
    except Exception as e:
        logger.error(f"❌ Wake-up failed: {e}")
        self._handle_wake_failure(e)
        raise
```

### 4.3 Step Details

**Step 1: Restore Identity** (OVERRIDE IN SUBCLASS)
```python
def _restore_identity(self):
    """Load agent-specific identity"""
    # Default: Load from config
    # Subclass: Load from vision stack, domain config, etc.
    pass
```

**Step 2: Load Domain Context**
```python
def _load_domain_context(self):
    """Load operational context from database"""
    context = self.db.execute("""
        SELECT * FROM agent_context 
        WHERE agent_id = %s 
        ORDER BY version DESC LIMIT 1
    """, (self.agent_id,)).fetchone()
    
    self.context = context['context_data'] if context else {}
    logger.info(f"📚 Loaded context version {context['version']}")
```

**Step 3: Check Collaboration State**
```python
def _check_collaboration_state(self):
    """Check what other agents are doing"""
    handoffs = self.db.execute("""
        SELECT * FROM agent_handoffs 
        WHERE target_agent_id = %s AND status = 'pending'
    """, (self.agent_id,)).fetchall()
    
    self.pending_handoffs = handoffs
    logger.info(f"🤝 {len(handoffs)} pending handoffs")
```

**Step 4: Process Learning Queue**
```python
def _process_learning_queue(self):
    """Apply learnings from past iterations"""
    learnings = self.db.execute("""
        SELECT * FROM knowledge_base 
        WHERE category LIKE %s 
        ORDER BY learned_at DESC LIMIT 10
    """, (f"{self.agent_id}-%",)).fetchall()
    
    self._apply_learnings(learnings)  # Subclass implements
    logger.info(f"🧠 Applied {len(learnings)} learnings")
```

**Step 5: Execute Work**
```python
def _execute_work(self):
    """Execute pending tasks"""
    tasks = self._get_pending_tasks()  # Subclass implements
    
    for task in tasks:
        try:
            self.execute_task(task)  # Subclass implements
            self._mark_task_complete(task)
        except Exception as e:
            self._handle_task_failure(task, e)
```

**Step 6: Save Context**
```python
def _save_context_and_handoff(self):
    """Save state for next wake-up"""
    self.db.execute("""
        INSERT INTO agent_context (
            agent_id, context_type, context_data, version
        ) VALUES (%s, %s, %s, %s)
    """, (
        self.agent_id,
        'wake_cycle',
        json.dumps(self._serialize_context()),
        self.wake_count
    ))
    
    if self._should_handoff():
        self._create_handoff_package()
```

---

## 5. Memory System

### 5.1 Architecture

```
┌────────────────────────────────────────────────────┐
│              AGENT MEMORY SYSTEM                   │
├────────────────────────────────────────────────────┤
│                                                    │
│  ┌──────────────────┐      ┌──────────────────┐  │
│  │   PostgreSQL     │      │  Pinecone Vector │  │
│  │  (Structured)    │      │  (Semantic)      │  │
│  │                  │      │                  │  │
│  │ • Context        │◄────►│ • Embeddings     │  │
│  │ • Decisions      │      │ • Similarity     │  │
│  │ • Knowledge      │      │ • Recall         │  │
│  │ • Tasks          │      │                  │  │
│  └──────────────────┘      └──────────────────┘  │
│          ↑                          ↑             │
│          └──────────┬───────────────┘             │
│                     ↓                             │
│            ┌─────────────────┐                    │
│            │  WAAOOWAgent    │                    │
│            │  Memory API     │                    │
│            └─────────────────┘                    │
└────────────────────────────────────────────────────┘
```

### 5.2 Storage Layers

**Layer 1: PostgreSQL (Structured Data)**
- Agent context snapshots (versioned)
- Decision log with outcomes
- Task queue and execution history
- Knowledge base (learnings)
- Collaboration state (handoffs)

**Layer 2: Pinecone (Vector Embeddings)**
- Semantic memory recall
- Similar decision retrieval
- Pattern recognition
- Cross-agent knowledge sharing

**Layer 3: Redis (Cache)**
- Decision cache (prevent redundant LLM calls)
- Session state
- Rate limiting

### 5.3 Memory API

```python
def store_memory(self, memory_type: str, memory_key: str, data: dict):
    """
    Store memory with semantic embedding.
    
    Args:
        memory_type: Category (e.g., "decision", "learning", "context")
        memory_key: Unique key for retrieval
        data: Memory data with optional 'importance' score
    """
    # Store in PostgreSQL
    self.db.execute("""
        INSERT INTO wowvision_memory (
            memory_type, memory_key, memory_data, 
            importance_score, created_at
        ) VALUES (%s, %s, %s, %s, NOW())
    """, (memory_type, memory_key, json.dumps(data), 
          data.get('importance', 0.5)))
    
    # Store embedding in Pinecone
    content = f"{memory_type}: {memory_key} - {json.dumps(data)}"
    self.vector_memory.store_memory(
        memory_key, 
        content, 
        metadata={
            'agent_id': self.agent_id,
            'memory_type': memory_type,
            'importance': data.get('importance', 0.5)
        }
    )

def recall_memory(self, query: str, memory_type: str = None) -> List[dict]:
    """
    Recall relevant memories semantically.
    
    Args:
        query: Natural language query
        memory_type: Optional filter by type
        
    Returns:
        List of memories sorted by relevance
    """
    results = self.vector_memory.recall_similar(
        query=query,
        top_k=5,
        filter={'agent_id': self.agent_id}
    )
    
    return [r['metadata'] for r in results]
```

### 5.4 Database Schema

See `waooaw/database/base_agent_schema.sql` for full schema.

**Key Tables**:
- `agent_context` - Versioned context snapshots
- `wowvision_memory` - Long-term memory
- `conversation_sessions` - Chat history
- `conversation_messages` - Message log
- `knowledge_base` - Learned patterns
- `decision_cache` - Cost optimization
- `agent_handoffs` - Cross-CoE collaboration
- `wowvision_state` - Operational state

---

## 6. Decision Framework

### 6.1 Hybrid Approach

**Goal**: Make intelligent decisions while minimizing LLM costs.

**Strategy**: 4-tier decision hierarchy

```
Decision Request
      ↓
┌─────────────────────────┐
│ 1. Check Cache          │  → Cache hit? Return (FREE, instant)
└─────────────────────────┘
      ↓ Cache miss
┌─────────────────────────┐
│ 2. Deterministic Logic  │  → Confidence ≥95%? Return (FREE, <1ms)
└─────────────────────────┘
      ↓ Ambiguous
┌─────────────────────────┐
│ 3. Vector Memory        │  → Similar past decision? Return (~$0.0001)
└─────────────────────────┘
      ↓ Novel situation
┌─────────────────────────┐
│ 4. LLM Reasoning        │  → Complex reasoning (~$0.05-0.15)
└─────────────────────────┘
      ↓
  Cache result, Store in vector memory
```

### 6.2 Implementation

```python
def make_decision(self, decision_request: dict) -> Decision:
    """
    Hybrid decision framework.
    
    Args:
        decision_request: {
            'type': str,              # Decision type
            'context': dict,          # Relevant context
            'urgency': str,           # high/medium/low
            **kwargs                  # Request-specific data
        }
        
    Returns:
        Decision object with:
            - approved: bool
            - reason: str
            - confidence: float (0-1)
            - citations: List[str]
            - method: str (cache/deterministic/vector/llm)
            - cost: float (USD)
    """
    
    # Tier 1: Check cache
    cached = self._check_decision_cache(decision_request)
    if cached:
        logger.info("💰 Decision from cache (FREE)")
        return cached
    
    # Tier 2: Try deterministic logic
    deterministic = self._try_deterministic_decision(decision_request)
    if deterministic.confidence >= 0.95:
        self._cache_decision(decision_request, deterministic)
        logger.info(f"⚡ Deterministic decision (confidence={deterministic.confidence})")
        return deterministic
    
    # Tier 3: Check vector memory
    similar = self.vector_memory.recall_similar(
        query=self._request_to_query(decision_request),
        top_k=5
    )
    
    if similar and similar[0]['similarity'] > 0.90:
        past_decision = self._reconstruct_decision(similar[0])
        self._cache_decision(decision_request, past_decision)
        logger.info(f"🧠 Decision from memory (similarity={similar[0]['similarity']})")
        return past_decision
    
    # Tier 4: Use LLM for complex reasoning
    llm_decision = self._ask_llm(decision_request, similar)
    self._cache_decision(decision_request, llm_decision)
    self._store_in_vector_memory(decision_request, llm_decision)
    logger.info(f"🤖 LLM decision (cost=${llm_decision.cost:.4f})")
    
    return llm_decision
```

### 6.3 Deterministic Logic (Override in Subclass)

```python
def _try_deterministic_decision(self, request: dict) -> Decision:
    """
    Agent-specific deterministic rules.
    
    Override in subclass to implement domain-specific logic.
    Should return Decision with confidence ≥0.95 if rule applies,
    otherwise return Decision with confidence <0.5.
    """
    # Base class: No deterministic rules
    return Decision(
        approved=None,
        confidence=0.5,
        reason="No deterministic rule applies",
        method='none'
    )
```

### 6.4 LLM Reasoning

```python
def _ask_llm(self, request: dict, context: List[dict]) -> Decision:
    """
    Use Claude Sonnet 4.5 for complex reasoning.
    
    Args:
        request: Decision request
        context: Similar past decisions for few-shot learning
        
    Returns:
        Decision with LLM reasoning
    """
    system_prompt = self._build_system_prompt()
    user_prompt = self._build_decision_prompt(request, context)
    
    response = self.llm.messages.create(
        model="claude-sonnet-4.5-20250514",
        max_tokens=2048,
        temperature=0.0,  # Deterministic reasoning
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    
    decision = self._parse_llm_response(response)
    
    # Validate LLM decision
    if not self._validate_llm_decision(decision):
        logger.warning("⚠️  LLM decision failed validation")
        return self._conservative_fallback(request)
    
    # Calculate cost
    decision.cost = self._calculate_llm_cost(response)
    
    return decision
```

### 6.5 Cost Optimization

**Expected Distribution** (after learning period):
- 60% decisions from cache (FREE)
- 30% decisions from deterministic logic (FREE)
- 8% decisions from vector memory (~$0.0001 each)
- 2% decisions from LLM (~$0.05-0.15 each)

**Monthly cost per agent** (10,000 decisions):
- Cache: 6,000 × $0 = $0
- Deterministic: 3,000 × $0 = $0
- Vector: 800 × $0.0001 = $0.08
- LLM: 200 × $0.10 = $20
- **Total: ~$20/month** per active agent

---

## 7. GitHub Integration

### 7.1 Purpose

Agents operate autonomously on GitHub:
- **Monitoring**: Watch repository for changes
- **Validation**: Check PRs, commits, file creations
- **Escalation**: Create issues for human review
- **Collaboration**: Comment on issues/PRs
- **Learning**: Read human responses to improve

### 7.2 GitHub API Methods

```python
def create_github_issue(self, title: str, body: str, labels: List[str]) -> Issue:
    """
    Create GitHub issue for escalation/notification.
    
    Args:
        title: Issue title
        body: Issue body (markdown)
        labels: Labels to apply
        
    Returns:
        GitHub Issue object
    """
    repo = self.github.get_repo(self.config['github_repo'])
    issue = repo.create_issue(
        title=title,
        body=body,
        labels=labels
    )
    
    logger.info(f"📝 Created issue #{issue.number}: {title}")
    return issue

def read_github_comments(self, issue_number: int) -> List[str]:
    """
    Read comments on GitHub issue.
    
    Args:
        issue_number: Issue number
        
    Returns:
        List of comment bodies
    """
    repo = self.github.get_repo(self.config['github_repo'])
    issue = repo.get_issue(issue_number)
    comments = [comment.body for comment in issue.get_comments()]
    
    logger.info(f"💬 Read {len(comments)} comments on issue #{issue_number}")
    return comments

def comment_on_issue(self, issue_number: int, comment: str):
    """Add comment to GitHub issue"""
    repo = self.github.get_repo(self.config['github_repo'])
    issue = repo.get_issue(issue_number)
    issue.create_comment(comment)

def get_open_prs(self) -> List[PullRequest]:
    """Get open pull requests"""
    repo = self.github.get_repo(self.config['github_repo'])
    return list(repo.get_pulls(state='open'))

def get_recent_commits(self, since: datetime = None) -> List[Commit]:
    """Get recent commits"""
    repo = self.github.get_repo(self.config['github_repo'])
    since = since or (datetime.now() - timedelta(hours=24))
    return list(repo.get_commits(since=since))
```

### 7.3 Escalation Pattern

```python
def _escalate_to_human(self, reason: str, context: dict, urgency: str = "medium"):
    """
    Create escalation issue for human review.
    
    Args:
        reason: Why escalating
        context: Relevant context
        urgency: high/medium/low
    """
    title = f"🚨 {self.agent_id} Escalation: {reason}"
    
    body = f"""
## Escalation Reason
{reason}

## Context
```json
{json.dumps(context, indent=2)}
```

## Agent Request
Please review and provide guidance. Reply with:
- **APPROVE**: Proceed with action
- **REJECT**: Do not proceed
- **MODIFY**: Proceed with modifications (specify)

## Urgency
{urgency.upper()}

---
*Escalated by {self.agent_id} at {datetime.now().isoformat()}*
"""
    
    labels = [
        f'{self.agent_id.lower()}-escalation',
        f'urgency-{urgency}',
        'needs-human-review'
    ]
    
    issue = self.create_github_issue(title, body, labels)
    
    # Log escalation
    self.db.execute("""
        INSERT INTO human_escalations (
            agent_id, escalation_reason, action_data,
            github_issue_number, status, urgency
        ) VALUES (%s, %s, %s, %s, 'pending', %s)
    """, (self.agent_id, reason, json.dumps(context), 
          issue.number, urgency))
    
    return issue
```

---

## 8. Learning & Improvement

### 8.1 Learning Cycle

```
Action → Outcome → Analysis → Learning → Application
   ↓                                         ↑
   └─────────────────────────────────────────┘
```

### 8.2 Learning API

```python
def learn_from_outcome(self, action: dict, outcome: dict):
    """
    Learn from action outcomes.
    
    Args:
        action: {
            'type': str,
            'data': dict,
            'decision': Decision
        }
        outcome: {
            'success': bool,
            'metrics': dict,
            'feedback': str
        }
    """
    # Store as knowledge
    self.db.execute("""
        INSERT INTO knowledge_base (
            category, title, content, confidence, source
        ) VALUES (%s, %s, %s, %s, %s)
    """, (
        f"{self.agent_id}-learnings",
        f"Outcome: {action['type']}",
        json.dumps({'action': action, 'outcome': outcome}),
        outcome.get('success_confidence', 0.8),
        'outcome-feedback'
    ))
    
    # Store in vector memory for future recall
    self.store_memory(
        'learning',
        f"{action['type']}_{datetime.now().isoformat()}",
        {
            'action': action,
            'outcome': outcome,
            'importance': self._calculate_learning_importance(outcome)
        }
    )
    
    logger.info(f"📚 Learned from {action['type']}: {outcome['success']}")
```

### 8.3 Applying Learnings (Override in Subclass)

```python
def _apply_learnings(self, learnings: List[dict]):
    """
    Apply learnings to improve behavior.
    
    Override in subclass to use learnings.
    Base class just logs them.
    """
    for learning in learnings:
        logger.debug(f"💡 Learning: {learning['title']}")
```

### 8.4 Learning Categories

- **Decision Patterns**: When similar decisions succeed/fail
- **Violation Patterns**: Common vision/policy violations
- **Optimization**: What makes tasks faster/cheaper
- **Error Recovery**: How to handle specific failures
- **Human Feedback**: Patterns in human escalation responses

---

## 9. Inheritance Model

### 9.1 How to Extend WAAOOWAgent

```python
from waooaw.agents.base_agent import WAAOOWAgent

class MyCustomAgent(WAAOOWAgent):
    """
    Custom agent for [DOMAIN].
    
    Specialization: [WHAT THIS AGENT DOES]
    Responsibilities:
    - [Responsibility 1]
    - [Responsibility 2]
    """
    
    def __init__(self, config: dict):
        # Call base init with agent ID
        super().__init__(agent_id="MyCustomAgent", config=config)
        
        # Initialize domain-specific components
        self.domain_data = self._load_domain_data()
    
    # REQUIRED OVERRIDES
    
    def _restore_identity(self):
        """Load agent-specific identity"""
        # Load from config, vision stack, etc.
        self.role = "Domain Expert"
        self.responsibilities = ["Task A", "Task B"]
    
    def execute_task(self, task: dict):
        """Execute domain-specific task"""
        if task['type'] == 'validate_something':
            self._validate_something(task['data'])
    
    def _get_pending_tasks(self) -> List[dict]:
        """Get domain-specific pending tasks"""
        # Query GitHub, database, etc.
        return []
    
    # OPTIONAL OVERRIDES
    
    def _try_deterministic_decision(self, request: dict) -> Decision:
        """Domain-specific deterministic rules"""
        # Implement fast rules for common cases
        if self._is_obvious_case(request):
            return Decision(approved=True, confidence=1.0)
        return super()._try_deterministic_decision(request)
    
    def _apply_learnings(self, learnings: List[dict]):
        """Use learnings to improve"""
        for learning in learnings:
            if learning['category'].startswith(f"{self.agent_id}-"):
                # Apply learning
                pass
```

### 9.2 Inheritance Hierarchy

```
WAAOOWAgent (Base Class)
  ├─ WowVision Prime (Vision Guardian)
  ├─ WowDomain (Domain Architecture)
  ├─ WowAgentFactory (Agent Bootstrapper)
  ├─ WowMarketplace (Marketplace Operations)
  ├─ WowAuth (Authentication & Authorization)
  ├─ WowPayment (Payment Processing)
  ├─ WowNotification (Communication)
  ├─ WowAnalytics (Data & Insights)
  ├─ WowQuality (Quality Assurance)
  ├─ WowSecurity (Security & Compliance)
  ├─ WowScaling (Performance & Scaling)
  ├─ WowIntegration (External Integrations)
  ├─ WowSupport (Customer Support)
  └─ WowOps (Operations & DevOps)
```

---

## 10. Agent Lifecycle

### 10.1 Lifecycle States

```
Created → Initialized → Active ⇄ Sleeping → Shutdown
                          ↓
                      Escalated
```

### 10.2 State Transitions

**Created**: Agent registered in system
- Database entry created
- Configuration validated
- Resources allocated

**Initialized**: First wake-up completed
- Identity restored
- Memory loaded
- Ready for tasks

**Active**: Executing work
- Processing tasks
- Making decisions
- Learning from outcomes

**Sleeping**: Between wake cycles
- Context saved to database
- Resources released
- Awaiting next trigger

**Escalated**: Waiting for human
- Issue created on GitHub
- Polling for response
- Will resume when answered

**Shutdown**: Graceful termination
- Pending tasks persisted
- Handoffs created
- State snapshot saved

### 10.3 Wake Triggers

Agents wake up based on:
- **Scheduled**: Cron-like schedules (e.g., every 5 minutes)
- **Event-driven**: GitHub webhooks (new commit, PR, issue comment)
- **On-demand**: Manual trigger via API
- **Collaborative**: Handoff from another agent

---

## 11. Safety & Validation

### 11.1 Safety Principles

**1. Conservative by Default**
- When uncertain → escalate to human
- When ambiguous → ask for clarification
- When risky → require explicit approval

**2. Validation Before Action**
- Validate inputs against schemas
- Check permissions before operations
- Verify resource availability

**3. Audit Everything**
- Log all decisions with reasoning
- Track all actions with outcomes
- Store all escalations with resolutions

**4. Graceful Degradation**
- Fallback to simpler logic on errors
- Preserve partial work on failures
- Enable manual intervention

### 11.2 Validation Framework

```python
def _validate_action(self, action: dict) -> ValidationResult:
    """
    Validate action before execution.
    
    Checks:
    - Schema compliance
    - Permission requirements
    - Resource availability
    - Safety constraints
    """
    # Schema validation
    if not self._validate_schema(action):
        return ValidationResult(
            valid=False,
            reason="Invalid action schema"
        )
    
    # Permission check
    if not self._check_permission(action):
        return ValidationResult(
            valid=False,
            reason="Insufficient permissions"
        )
    
    # Safety check
    if self._is_risky_action(action):
        return ValidationResult(
            valid=False,
            reason="Risky action requires human approval"
        )
    
    return ValidationResult(valid=True)
```

### 11.3 Conservative Fallbacks

```python
def _conservative_fallback(self, request: dict) -> Decision:
    """
    Conservative decision when LLM fails validation.
    
    Default: Reject with escalation
    """
    reason = "Unable to make confident decision"
    
    # Escalate to human
    self._escalate_to_human(
        reason=reason,
        context=request,
        urgency='medium'
    )
    
    return Decision(
        approved=False,
        reason=f"{reason} - escalated to human",
        confidence=0.9,
        method='conservative_fallback'
    )
```

---

## 12. Configuration & Deployment

### 12.1 Configuration File

**File**: `waooaw/config/agent_config.yaml`

```yaml
agent:
  id: "WowVision-Prime"
  version: "1.0.0"
  
database:
  host: "${DB_HOST}"
  port: 5432
  database: "waooaw"
  user: "${DB_USER}"
  password: "${DB_PASSWORD}"
  
github:
  token: "${GITHUB_TOKEN}"
  repo: "dlai-sd/WAOOAW"
  
pinecone:
  api_key: "${PINECONE_API_KEY}"
  environment: "us-west1-gcp"
  index_name: "waooaw-memory"
  
anthropic:
  api_key: "${ANTHROPIC_API_KEY}"
  model: "claude-sonnet-4.5-20250514"
  
logging:
  level: "INFO"
  format: "json"
  
memory:
  vector_dimensions: 1536
  similarity_threshold: 0.85
  
decision:
  cache_ttl: 3600  # 1 hour
  deterministic_threshold: 0.95
  llm_temperature: 0.0
  
wake_schedule:
  type: "cron"
  schedule: "*/5 * * * *"  # Every 5 minutes
```

### 12.2 Environment Variables

```bash
# Database
DB_HOST=localhost
DB_USER=waooaw
DB_PASSWORD=secure_password
DB_NAME=waooaw

# APIs
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
PINECONE_API_KEY=xxxx-xxxx-xxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx

# Application
AGENT_ID=WowVision-Prime
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### 12.3 Deployment Options

**Option 1: GitHub Actions (Recommended)**
```yaml
# .github/workflows/wowvision-prime.yml
name: WowVision Prime Agent

on:
  schedule:
    - cron: '*/5 * * * *'  # Every 5 minutes
  workflow_dispatch:
  repository_dispatch:
    types: [vision-check]

jobs:
  run-agent:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r waooaw/requirements.txt
      - run: python waooaw/main.py wake_up
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          PINECONE_API_KEY: ${{ secrets.PINECONE_API_KEY }}
          DB_HOST: ${{ secrets.DB_HOST }}
          DB_USER: ${{ secrets.DB_USER }}
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
```

**Option 2: Docker Container**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY waooaw/ ./waooaw/
RUN pip install -r waooaw/requirements.txt
CMD ["python", "waooaw/main.py", "wake_up"]
```

**Option 3: Kubernetes CronJob**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: wowvision-prime
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: agent
            image: waooaw/wowvision-prime:latest
            envFrom:
            - secretRef:
                name: agent-secrets
```

---

## 13. Cost Analysis

### 13.1 Per-Agent Monthly Costs

**Infrastructure**:
- PostgreSQL: $0 (shared)
- Redis: $0 (shared)
- Pinecone: $70/month (1M vectors, shared across all agents)
  - Per agent: ~$5/month
- GitHub Actions: Free (2,000 minutes/month)

**API Costs**:
- Claude Sonnet 4.5: ~$20/month per agent
  - Input: $3 per 1M tokens
  - Output: $15 per 1M tokens
  - Estimated: 200 LLM calls/day × $0.10 = $20/month
- OpenAI Embeddings (text-embedding-3-small): ~$0.50/month
  - $0.02 per 1M tokens
  - Estimated: 10,000 embeddings/month = $0.50

**Total per active agent**: ~$26/month

**Total for 14 CoEs**: ~$364/month

### 13.2 Cost Optimization Strategies

1. **Decision Caching**: Reduce LLM calls by 60%
2. **Deterministic Logic**: Handle 30% of decisions for free
3. **Vector Memory**: Avoid redundant reasoning (~$0.0001 vs $0.10)
4. **Batch Processing**: Group similar decisions
5. **Smart Wake Schedules**: Wake only when needed
6. **Shared Infrastructure**: Amortize fixed costs across agents

---

## 14. Example Implementations

### 14.1 WowVision Prime (Included)

See: `waooaw/agents/wowvision_prime.py`

**Specialization**: Vision enforcement
- Validates file creations against vision stack
- Reviews PRs for vision compliance
- Processes human escalations
- Learns violation patterns

### 14.2 Example: WowDomain Agent

```python
from waooaw.agents.base_agent import WAAOOWAgent

class WowDomain(WAAOOWAgent):
    """
    Domain Architecture Agent.
    
    Specialization: Domain model integrity
    Responsibilities:
    - Validate entity relationships
    - Ensure bounded context integrity
    - Review domain model changes
    - Maintain ubiquitous language
    """
    
    def __init__(self, config: dict):
        super().__init__(agent_id="WowDomain", config=config)
        self.domain_model = self._load_domain_model()
    
    def _restore_identity(self):
        """Load domain architecture identity"""
        self.core_identity = {
            'role': 'Domain Architecture Guardian',
            'expertise': ['DDD', 'bounded contexts', 'aggregates'],
            'responsibilities': [
                'Validate entity relationships',
                'Review domain model changes',
                'Maintain ubiquitous language'
            ]
        }
    
    def _try_deterministic_decision(self, request: dict) -> Decision:
        """Domain-specific validation rules"""
        
        if request['type'] == 'add_entity':
            entity = request['data']['entity']
            
            # Rule: Entity must have ID field
            if 'id' not in entity.get('fields', []):
                return Decision(
                    approved=False,
                    reason="Entities must have ID field",
                    confidence=1.0,
                    method='deterministic'
                )
            
            # Rule: Entity name must be singular
            if entity['name'].endswith('s'):
                return Decision(
                    approved=False,
                    reason="Entity names must be singular",
                    confidence=1.0,
                    method='deterministic'
                )
        
        return super()._try_deterministic_decision(request)
    
    def _get_pending_tasks(self) -> List[dict]:
        """Get domain-related tasks"""
        tasks = []
        
        # Check recent commits for domain model changes
        for commit in self._get_recent_commits():
            for file in commit.files:
                if 'models/' in file.filename:
                    tasks.append({
                        'type': 'validate_model_change',
                        'data': {'file': file, 'commit': commit}
                    })
        
        return tasks
    
    def execute_task(self, task: dict):
        """Execute domain validation task"""
        
        if task['type'] == 'validate_model_change':
            self._validate_model_change(task['data'])
    
    def _validate_model_change(self, data: dict):
        """Validate domain model change"""
        file = data['file']
        
        # Use decision framework
        decision = self.make_decision({
            'type': 'model_change',
            'file': file.filename,
            'changes': file.patch
        })
        
        if not decision.approved:
            # Create PR review comment
            self._escalate_to_human(
                reason=f"Domain model violation: {decision.reason}",
                context=data,
                urgency='high'
            )
```

### 14.3 Example: WowAgentFactory

```python
from waooaw.agents.base_agent import WAAOOWAgent

class WowAgentFactory(WAAOOWAgent):
    """
    Agent Bootstrapper.
    
    Specialization: Create new agents
    Responsibilities:
    - Generate agent scaffolding from templates
    - Configure agent environments
    - Test agent capabilities
    - Deploy agents to production
    """
    
    def __init__(self, config: dict):
        super().__init__(agent_id="WowAgentFactory", config=config)
        self.templates = self._load_templates()
    
    def _restore_identity(self):
        """Load factory identity"""
        self.core_identity = {
            'role': 'Agent Creator',
            'expertise': ['templating', 'configuration', 'deployment'],
            'responsibilities': [
                'Create new agents from templates',
                'Configure agent environments',
                'Test agent capabilities'
            ]
        }
    
    def _get_pending_tasks(self) -> List[dict]:
        """Get agent creation requests"""
        # Check for issues with label 'new-agent-request'
        repo = self.github.get_repo(self.config['github_repo'])
        issues = repo.get_issues(state='open', labels=['new-agent-request'])
        
        return [
            {
                'type': 'create_agent',
                'data': {'issue': issue}
            }
            for issue in issues
        ]
    
    def execute_task(self, task: dict):
        """Create new agent"""
        if task['type'] == 'create_agent':
            self._create_agent_from_request(task['data'])
    
    def _create_agent_from_request(self, data: dict):
        """Bootstrap new agent from template"""
        issue = data['issue']
        
        # Parse issue body for agent spec
        spec = self._parse_agent_spec(issue.body)
        
        # Generate agent code from template
        agent_code = self._generate_from_template(spec)
        
        # Create PR with new agent
        self._create_agent_pr(spec, agent_code)
```

---

## Integration with Orchestration Layer

**Related Document**: [ORCHESTRATION_LAYER_DESIGN.md](./ORCHESTRATION_LAYER_DESIGN.md)

### Workflow-Aware Agent Execution

Agents can execute both **standalone** (wake-sleep cycle) and within **orchestrated workflows** (jBPM-inspired):

```python
class WAAOOWAgent:
    """Base agent with workflow execution support"""
    
    def __init__(
        self, 
        agent_id: str, 
        specialization: Specialization,
        workflow_instance: Optional[WorkflowInstance] = None
    ):
        self.agent_id = agent_id
        self.specialization = specialization
        self.workflow_instance = workflow_instance  # NEW: Workflow context
        # ... existing fields ...
    
    async def execute_as_service_task(
        self,
        task_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute as orchestrated workflow task (jBPM Service Task pattern)
        
        Called by orchestration layer when agent is part of a workflow.
        Different from normal wake-execute cycle:
        - No wake-up protocol (already awake)
        - Inputs provided by workflow
        - Outputs expected by workflow
        - Workflow manages context/state
        """
        
        # Log workflow context
        if self.workflow_instance:
            logger.info(
                f"Agent {self.agent_id} executing as service task in "
                f"workflow {self.workflow_instance.instance_id}"
            )
        
        # Execute agent logic (use existing decision framework)
        result = await self.execute(task_input)
        
        # Return structured output for workflow
        return {
            "success": True,
            "output": result,
            "execution_metadata": {
                "duration_ms": self.last_execution_duration,
                "cost": self.last_execution_cost,
                "method": self.last_decision_method,  # deterministic/cached/llm
                "confidence": self.last_confidence_score
            }
        }
    
    def set_workflow_variable(self, name: str, value: Any):
        """
        Convenience method to set workflow variables
        
        Agents can update shared workflow state during execution.
        """
        if self.workflow_instance:
            self.workflow_instance.set_variable(
                name=name,
                value=value,
                actor=self.agent_id
            )
        else:
            logger.warning(
                f"Agent {self.agent_id} attempted to set workflow variable "
                f"but no workflow context exists"
            )
    
    def get_workflow_variable(self, name: str, default: Any = None) -> Any:
        """Get variable from workflow context"""
        if self.workflow_instance:
            return self.workflow_instance.get_variable(name, default)
        return default
```

### Execution Modes Comparison

| Mode | Wake Protocol | Context Source | Output Destination | Use Case |
|------|--------------|----------------|-------------------|----------|
| **Standalone** | 6-step wake-up | PostgreSQL `agent_context_versions` | Database, GitHub issues | Independent agent operation |
| **Workflow Service Task** | Skip (orchestrator manages) | Workflow process variables | Workflow instance | Coordinated multi-agent workflows |
| **Message-Driven** | Event-based wake | Message payload + DB | Message bus reply-to | Async agent communication |

### Example: Agent in Workflow

```python
# Orchestration layer calls agent
workflow_instance = WorkflowInstance(workflow_id="pr_review", version="1.0")
workflow_instance.set_variable("pr_number", 42, actor="system")
workflow_instance.set_variable("files_changed", ["app.py"], actor="system")

# Create agent with workflow context
agent = WowVisionPrime(
    agent_id="wowvision_prime_001",
    workflow_instance=workflow_instance
)

# Execute as service task (no wake-up, direct execution)
result = await agent.execute_as_service_task({
    "pr_number": 42,
    "files_changed": ["app.py"]
})

# Agent can access/update workflow variables during execution
agent.set_workflow_variable("vision_approved", True)
agent.set_workflow_variable("violations", [])

# Result returned to orchestration layer
# {
#   "success": True,
#   "output": {...},
#   "execution_metadata": {
#     "duration_ms": 450,
#     "cost": 0.0,
#     "method": "deterministic",
#     "confidence": 1.0
#   }
# }
```

### Benefits of Dual-Mode Execution

✅ **Flexibility** - Same agent works standalone or orchestrated  
✅ **Reusability** - No workflow-specific code in agents  
✅ **Testability** - Test agents independently, then in workflows  
✅ **Scalability** - Simple agents standalone, complex coordination via workflows  
✅ **Gradual adoption** - Start standalone, add orchestration later

---

## Conclusion

The **WAAOOWAgent** base class provides a robust, scalable foundation for all WAOOAW platform agents. By combining:

- **Context preservation** through 6-step wake-up protocol
- **Cost-effective intelligence** via hybrid decision framework
- **Continuous learning** from outcomes and feedback
- **Autonomous operation** with human escalation
- **Consistent behavior** across all 14 CoEs
- **Workflow integration** for orchestrated multi-agent coordination (NEW)

...we enable a platform where specialized AI agents can work independently yet collaboratively, continuously improving while maintaining safety and transparency.

**WowVision Prime** demonstrates this architecture in production, serving as the blueprint for future CoEs.

---

**Next Steps**:
1. Review this architecture document
2. Set up infrastructure (PostgreSQL, Pinecone, secrets)
3. Deploy WowVision Prime
4. Build WowDomain as second CoE
5. Implement orchestration layer for multi-agent workflows
6. Iterate and refine based on learnings

**Related Documents**:
- [ORCHESTRATION_LAYER_DESIGN.md](./ORCHESTRATION_LAYER_DESIGN.md) - jBPM-inspired workflow orchestration
- [MESSAGE_BUS_ARCHITECTURE.md](./MESSAGE_BUS_ARCHITECTURE.md) - Agent communication
- [AGENT_MESSAGE_HANDLER_DESIGN.md](./AGENT_MESSAGE_HANDLER_DESIGN.md) - Message handling

---

*Document Version: 1.1*  
*Last Updated: December 27, 2025*  
*Author: WAOOAW Platform Team*
