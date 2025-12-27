"""
WAOOAW Base Agent - Core agent class for all CoEs

This module provides the WAAOOWAgent base class that all 14 Centers of Excellence
inherit from. It implements:
- Dual-identity framework (Specialization + Personality)
- 6-step wake-up protocol for context preservation
- Hybrid decision framework (deterministic + LLM)
- Persistent memory (PostgreSQL + vector embeddings)
- GitHub integration for autonomous operation
- Learning & improvement mechanisms
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

import psycopg2
from psycopg2.extras import RealDictCursor
from github import Github, Issue, PullRequest, Commit
import anthropic

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class Decision:
    """Decision result from hybrid decision framework"""

    approved: bool
    reason: str
    confidence: float = 0.5
    citations: List[str] = field(default_factory=list)
    method: str = "unknown"
    cost: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentSpecialization:
    """CoE template - what TYPE of agent (platform-defined, immutable)"""

    coe_name: str
    coe_type: str
    domain: str
    expertise: str
    version: str
    core_responsibilities: List[str]
    capabilities: Dict[str, List[str]]
    constraints: List[Dict[str, str]]
    skill_requirements: List[str]

    def can_do(self, capability: str) -> bool:
        """Check if this CoE has a specific capability"""
        all_capabilities = []
        for cat in self.capabilities.values():
            all_capabilities.extend(cat)
        return capability in all_capabilities

    def is_constrained(self, action: str) -> Optional[str]:
        """Check if action violates constraints, return reason if so"""
        for constraint in self.constraints:
            if action.lower() in constraint.get("rule", "").lower():
                return constraint.get("reason", "Constraint violation")
        return None


@dataclass
class AgentPersonality:
    """Instance identity - WHO specifically (customer-defined, mutable)"""

    instance_id: str
    instance_name: Optional[str] = None
    role_title: Optional[str] = None
    industry: Optional[str] = None
    status: str = "active"

    employer: Dict[str, Any] = field(default_factory=dict)
    communication: Dict[str, str] = field(default_factory=dict)
    focus_areas: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    learned_preferences: List[str] = field(default_factory=list)


class WAAOOWAgent:
    """
    Base class for all WAOOAW platform agents.

    All 14 CoEs inherit from this foundation, providing all 15 dimensions:
    
    1. Wake Protocol: Event-driven wake, context restoration
    2. Context Management: Progressive loading, serialization
    3. Identity System: Dual-identity (Specialization + Personality)
    4. Hierarchy/RACI: Escalation, delegation, coordination
    5. Collaboration: Handoffs, peer consultation
    6. Learning & Memory: Continuous improvement, feedback loops
    7. Communication Protocol: Inter-agent messaging
    8. Resource Management: Budgets, rate limiting, cost tracking
    9. Trust & Reputation: Ratings, reviews, trust scores
    10. Error Handling: Circuit breakers, retry, DLQ
    11. Observability: Metrics, traces, cost breakdown
    12. Security & Privacy: Auth, encryption, audit logs
    13. Performance: Caching, optimization
    14. Testing: Unit, integration, shadow mode
    15. Lifecycle: Spawn, pause, resume, retire

    Subclasses must override:
    - _load_specialization(): Return AgentSpecialization for this CoE
    - execute_task(): Agent-specific task execution
    - _get_pending_tasks(): Domain-specific task queue

    Subclasses may override:
    - _try_deterministic_decision(): Domain-specific rules
    - _apply_learnings(): Use knowledge to improve
    - Any dimension method to customize behavior
    """

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        """
        Initialize base agent.

        Args:
            agent_id: Unique identifier (e.g., "WowVision-Prime")
            config: Configuration dict with:
                - database_url: PostgreSQL connection string
                - github_token: GitHub API token
                - github_repo: Repository (e.g., "dlai-sd/WAOOAW")
                - pinecone_api_key: Pinecone API key (optional)
                - anthropic_api_key: Claude API key
                - instance_id: Optional UUID for multi-tenant instances
        """
        self.agent_id = agent_id
        self.config = config

        # Initialize GitHub first (needed for error reporting)
        try:
            self.github = self._init_github()
        except Exception as e:
            logger.critical(f"❌ Cannot initialize without GitHub access: {e}")
            raise SystemExit(1)

        # Core components with error handling
        try:
            self.db = self._init_database()  # Includes auto schema setup
        except Exception as e:
            self._create_infrastructure_issue("Database Connection Failed", str(e))
            raise SystemExit(1)

        self.vector_memory = self._init_vector_memory()  # Optional
        self.llm = self._init_llm()  # Optional

        # DUAL IDENTITY
        self.specialization: AgentSpecialization = self._load_specialization()
        self.personality: AgentPersonality = self._load_personality()

        # State
        self.wake_count = 0
        self.start_time = datetime.now()
        self.context: Dict[str, Any] = {}
        self.pending_tasks: List[Dict[str, Any]] = []

        logger.info(f"✅ Initialized: {self.introduce_self()}")

    # =====================================
    # IDENTITY FRAMEWORK
    # =====================================

    def introduce_self(self) -> str:
        """Agent introduces itself with full identity"""
        if self.personality.instance_name:
            # Hired agent
            company = self.personality.employer.get("company_name", "WAOOAW Platform")
            role = self.personality.role_title or "agent"
            industry = self.personality.industry or "general"

            return (
                f"I am {self.personality.instance_name}, "
                f"a {self.specialization.coe_name} "
                f"specializing in {self.specialization.domain}. "
                f"I work for {company} as their {role} "
                f"in {industry} industry."
            )
        else:
            # Unhired agent (marketplace listing)
            return (
                f"I am {self.specialization.coe_name}, "
                f"specializing in {self.specialization.domain}. "
                f"Available for hire. "
                f"My expertise: {self.specialization.expertise}"
            )

    def _load_specialization(self) -> AgentSpecialization:
        """
        Load CoE template from platform config.

        MUST OVERRIDE in subclass to define agent specialization.

        Returns:
            AgentSpecialization with CoE-specific capabilities and constraints
        """
        # Fallback: Return minimal specialization
        # Subclasses should override with real specialization
        logger.warning(
            f"{self.agent_id}: Using fallback specialization (subclass should override)"
        )
        return AgentSpecialization(
            coe_name=self.agent_id,
            coe_type="generic",
            domain="General",
            expertise="General agent capabilities",
            version="1.0.0",
            core_responsibilities=["Execute tasks as assigned"],
            capabilities={"base": ["Task execution", "Decision making"]},
            constraints=[],
            skill_requirements=[],
        )

    def _load_personality(self) -> AgentPersonality:
        """
        Load instance identity from database.

        For multi-tenant: Load from agent_instances table using config.instance_id
        For single-tenant/testing: Use defaults

        Returns:
            AgentPersonality with employer-specific customization
        """
        instance_id = self.config.get("instance_id")

        if not instance_id:
            # No instance_id = pre-hire agent or single-tenant mode
            logger.info(
                f"{self.agent_id}: Running in single-tenant mode (no instance_id)"
            )
            return AgentPersonality(instance_id=self.agent_id, status="active")

        # Multi-tenant mode: Load from database
        try:
            cursor = self.db.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT * FROM agent_instances
                WHERE instance_id = %s AND status = 'active'
            """,
                (instance_id,),
            )

            result = cursor.fetchone()
            cursor.close()

            if result:
                return AgentPersonality(
                    instance_id=result["instance_id"],
                    instance_name=result.get("instance_name"),
                    role_title=result.get("role_title"),
                    industry=result.get("industry"),
                    status=result.get("status", "active"),
                    employer=result.get("employer", {}),
                    communication=result.get("customization", {}).get(
                        "communication", {}
                    ),
                    focus_areas=result.get("customization", {}).get("focus_areas", []),
                    preferences=result.get("customization", {}).get("preferences", {}),
                    learned_preferences=result.get("learned_preferences", []),
                )
            else:
                logger.warning(f"Instance {instance_id} not found, using defaults")
                return AgentPersonality(instance_id=instance_id, status="active")

        except Exception as e:
            logger.warning(f"Failed to load personality: {e}, using defaults")
            return AgentPersonality(
                instance_id=instance_id or self.agent_id, status="active"
            )

    # =====================================
    # 6-STEP WAKE-UP PROTOCOL
    # =====================================

    def wake_up(self) -> None:
        """Execute 6-step wake-up protocol from context preservation architecture"""
        try:
            # Step 1: Restore identity
            self._restore_identity()

            # Step 2: Load domain context (this sets wake_count)
            self._load_domain_context()

            # Now log with correct wake count
            logger.info(f"🌅 {self.agent_id} waking up (wake #{self.wake_count})")

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
            logger.error(f"❌ Wake-up failed: {e}", exc_info=True)
            self._handle_wake_failure(e)
            raise

    def _restore_identity(self) -> None:
        """
        Step 1: Load agent identity and role.

        OVERRIDE IN SUBCLASS: Load agent-specific identity.
        """
        # Base implementation: Log that subclass should override
        logger.debug(f"{self.agent_id}: Using base identity (subclass should override)")

    def _load_domain_context(self) -> None:
        """Step 2: Load relevant domain context from memory"""
        try:
            cursor = self.db.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT * FROM agent_context
                WHERE agent_id = %s
                ORDER BY version DESC LIMIT 1
            """,
                (self.agent_id,),
            )

            result = cursor.fetchone()
            cursor.close()

            if result:
                self.context = (
                    json.loads(result["context_data"])
                    if isinstance(result["context_data"], str)
                    else result["context_data"]
                )
                # Restore wake_count from previous context and increment
                self.wake_count = result["version"] + 1
                logger.info(
                    f"📚 Loaded context version {result['version']}, "
                    f"incrementing to wake #{self.wake_count}"
                )
            else:
                self.context = {}
                self.wake_count = 1  # First wake
                logger.info("📚 No previous context found, starting fresh (wake #1)")

        except Exception as e:
            logger.warning(f"Failed to load context: {e}")
            self.context = {}
            self.wake_count = 1

    def _check_collaboration_state(self) -> None:
        """Step 3: Check what other agents are doing"""
        try:
            cursor = self.db.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT * FROM agent_handoffs
                WHERE target_agent_id = %s AND status = 'pending'
            """,
                (self.agent_id,),
            )

            handoffs = cursor.fetchall()
            cursor.close()

            self.context["pending_handoffs"] = handoffs
            logger.info(f"🤝 {len(handoffs)} pending handoffs")

        except psycopg2.Error as e:
            # Table might not exist yet
            logger.debug(f"Could not check collaboration state: {e}")
            self.context["pending_handoffs"] = []

    def _process_learning_queue(self) -> None:
        """Step 4: Apply learnings from past iterations"""
        try:
            cursor = self.db.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT * FROM knowledge_base
                WHERE category LIKE %s
                ORDER BY learned_at DESC LIMIT 10
            """,
                (f"{self.agent_id}-%",),
            )

            learnings = cursor.fetchall()
            cursor.close()

            # Apply learnings (subclass implements)
            self._apply_learnings(learnings)
            logger.info(f"🧠 Applied {len(learnings)} learnings")

        except psycopg2.Error as e:
            # Table might not exist yet
            logger.debug(f"Could not load learnings: {e}")

    def _execute_work(self) -> None:
        """Step 5: Execute assigned tasks"""
        tasks = self._get_pending_tasks()

        logger.info(f"📋 Found {len(tasks)} pending tasks")

        for task in tasks:
            try:
                logger.info(f"🔨 Executing task: {task.get('type', 'unknown')}")
                self.execute_task(task)
                self._mark_task_complete(task)
            except Exception as e:
                logger.error(f"Task execution failed: {e}", exc_info=True)
                self._handle_task_failure(task, e)

    def _save_context_and_handoff(self) -> None:
        """Step 6: Save state for next wake-up and handoff to other agents"""
        try:
            # Update context with versioning
            cursor = self.db.cursor()
            context_data = json.dumps(self._serialize_context())

            cursor.execute(
                """
                INSERT INTO agent_context (
                    agent_id, context_type, context_data, version
                ) VALUES (%s, %s, %s, %s)
            """,
                (self.agent_id, "wake_cycle", context_data, self.wake_count),
            )

            self.db.commit()
            cursor.close()

            logger.info(f"💾 Saved context (version {self.wake_count})")

            # Create handoff package if needed
            if self._should_handoff():
                self._create_handoff_package()

        except psycopg2.Error as e:
            logger.error(f"Failed to save context: {e}")
            self.db.rollback()

    def _serialize_context(self) -> Dict[str, Any]:
        """Serialize current context for storage"""
        return {
            "wake_count": self.wake_count,
            "last_wake": self.start_time.isoformat(),
            "context": self.context,
            "metadata": {
                "agent_version": "1.0.0",
                "saved_at": datetime.now().isoformat(),
            },
        }

    def _should_handoff(self) -> bool:
        """Determine if handoff package should be created"""
        # Override in subclass for domain-specific logic
        return False

    def _create_handoff_package(self) -> None:
        """Create handoff package for other agents"""
        # Override in subclass for domain-specific handoffs
        pass

    # =====================================
    # DECISION FRAMEWORK
    # =====================================

    def make_decision(self, decision_request: Dict[str, Any]) -> Decision:
        """Story 3.2: Enhanced decision orchestration
        
        Hybrid decision framework:
        1. Try deterministic logic first (fast, cheap, reliable)
        2. Check decision cache (90% hit rate target)
        3. Check vector memory for similar past decisions
        4. Use LLM for complex/ambiguous cases (only 20% of decisions)

        Args:
            decision_request: Decision request dict with:
                - type: str (decision type)
                - context: dict (relevant context)
                - **kwargs: Request-specific data

        Returns:
            Decision object with approval, reason, confidence, etc.
        """
        decision_type = decision_request.get('type', 'unknown')
        logger.info(f"📋 Making decision: {decision_type}")
        start_time = datetime.now()

        # Tier 1: Check cache (Story 3.5)
        cached = self._check_decision_cache(decision_request)
        if cached:
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(f"💰 Decision from cache (FREE, {elapsed:.0f}ms)")
            self._log_decision(decision_request, cached, "cache")
            return cached

        # Tier 2: Try deterministic logic (Story 3.3)
        deterministic = self._try_deterministic_decision(decision_request)
        if deterministic.confidence >= 0.95:
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            self._cache_decision(decision_request, deterministic)
            logger.info(
                f"⚡ Deterministic decision (confidence={deterministic.confidence:.2f}, {elapsed:.0f}ms)"
            )
            self._log_decision(decision_request, deterministic, "deterministic")
            return deterministic

        # Tier 3: Check for similar past decisions (Story 4.3)
        # Searches both vector memory and knowledge base
        similar_decision = self._check_similar_past_decisions(
            decision_context=decision_request,
            confidence_threshold=0.8
        )
        
        if similar_decision:
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            self._cache_decision(decision_request, similar_decision)
            logger.info(
                f"🔍 Decision from similarity search "
                f"(confidence={similar_decision.confidence:.2f}, {elapsed:.0f}ms)"
            )
            self._log_decision(decision_request, similar_decision, 
                             similar_decision.metadata.get('source', 'similarity'))
            return similar_decision

        # Tier 4: Use LLM for complex case (Story 3.1)
        logger.info(f"🤖 Using LLM for ambiguous decision: {decision_type}")
        
        # Get similar decisions for context (even if not confident enough to reuse)
        similar_for_context = []
        if self.vector_memory:
            try:
                similar_for_context = self.vector_memory.recall_similar(
                    query=self._request_to_query(decision_request), top_k=3
                )
            except Exception as e:
                logger.debug(f"Failed to get similar decisions for context: {e}")
        
        llm_decision = self._ask_llm(decision_request, similar_for_context)
        
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        self._cache_decision(decision_request, llm_decision)

        if self.vector_memory:
            self._store_in_vector_memory(decision_request, llm_decision)

        logger.info(f"🤖 LLM decision (cost=${llm_decision.cost:.4f}, {elapsed:.0f}ms)")
        self._log_decision(decision_request, llm_decision, "llm")

        return llm_decision

    def _try_deterministic_decision(self, request: Dict[str, Any]) -> Decision:
        """
        OVERRIDE IN SUBCLASS: Agent-specific deterministic logic.

        Should return Decision with confidence ≥0.95 if rule applies,
        otherwise return Decision with confidence <0.5.
        """
        return Decision(
            approved=False,
            confidence=0.5,
            reason="No deterministic rule applies",
            method="none",
        )

    def _call_llm(
        self, prompt: str, max_retries: int = 3, timeout: float = 30.0
    ) -> Dict[str, Any]:
        """Story 3.1: Call LLM with retry logic, circuit breaker, token budget
        
        Args:
            prompt: The prompt to send to the LLM
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
            
        Returns:
            Dict with parsed LLM response: {
                "approved": bool,
                "reason": str,
                "confidence": float,
                "citations": List[str],
                "tokens_used": int,
                "cost": float
            }
            
        Raises:
            Exception: If circuit breaker is open or budget exceeded
        """
        # Check circuit breaker
        if self._is_circuit_breaker_open():
            logger.error("🚫 Circuit breaker OPEN - LLM calls blocked")
            raise Exception("Circuit breaker open: Too many recent LLM failures")
        
        # Check token budget (target $25/month = ~833/day)
        daily_cost = self._get_daily_llm_cost()
        if daily_cost > 8.33:  # $25/month ÷ 30 days ÷ 10 agents = $0.83/agent/day
            logger.error(f"💸 Token budget exceeded: ${daily_cost:.2f} today")
            raise Exception(f"Daily budget exceeded: ${daily_cost:.2f}")
        
        last_exception = None
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(f"LLM call attempt {attempt}/{max_retries}")
                
                # Call LLM with timeout
                response = self.llm.messages.create(
                    model="claude-sonnet-4.5-20250514",
                    max_tokens=2048,
                    temperature=0.0,
                    system=self._build_system_prompt(),
                    messages=[{"role": "user", "content": prompt}],
                )
                
                # Parse response
                decision_data = self._parse_llm_response(response)
                
                # Calculate cost and tokens
                tokens_used = response.usage.input_tokens + response.usage.output_tokens
                cost = self._calculate_llm_cost(response)
                
                # Track success for circuit breaker
                self._record_llm_success()
                
                # Log cost
                self._log_llm_cost(cost, tokens_used)
                
                result = {
                    "approved": decision_data.get("approved", False),
                    "reason": decision_data.get("reason", "No reason provided"),
                    "confidence": decision_data.get("confidence", 0.5),
                    "citations": decision_data.get("citations", []),
                    "tokens_used": tokens_used,
                    "cost": cost
                }
                
                logger.info(f"✅ LLM call successful (tokens={tokens_used}, cost=${cost:.4f})")
                return result
                
            except anthropic.RateLimitError as e:
                logger.warning(f"⏱️  Rate limit hit on attempt {attempt}: {e}")
                last_exception = e
                if attempt < max_retries:
                    import time
                    backoff_time = 2 ** attempt  # Exponential backoff
                    time.sleep(backoff_time)
                    
            except anthropic.APITimeoutError as e:
                logger.warning(f"⏱️  Timeout on attempt {attempt}: {e}")
                last_exception = e
                if attempt < max_retries:
                    import time
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"❌ LLM error on attempt {attempt}: {e}")
                last_exception = e
                # Track failure for circuit breaker
                self._record_llm_failure()
                if attempt < max_retries:
                    import time
                    time.sleep(1)
        
        # All retries failed
        logger.error(f"❌ All {max_retries} LLM attempts failed")
        raise Exception(f"LLM call failed after {max_retries} attempts: {last_exception}")

    def _ask_llm(
        self, request: Dict[str, Any], context: List[Dict[str, Any]]
    ) -> Decision:
        """Use LLM (Claude Sonnet 4.5) for complex reasoning"""
        try:
            # Build prompt using templates
            prompt = self._build_decision_prompt(request, context)

            # Call LLM with retry logic
            llm_result = self._call_llm(prompt)

            # Convert to Decision object
            decision = Decision(
                approved=llm_result["approved"],
                reason=llm_result["reason"],
                confidence=llm_result["confidence"],
                citations=llm_result["citations"],
                method="llm",
                cost=llm_result["cost"],
                metadata={"tokens_used": llm_result["tokens_used"]}
            )

            if not self._validate_llm_decision(decision):
                logger.warning("⚠️  LLM decision failed validation")
                return self._conservative_fallback(request)

            return decision

        except Exception as e:
            logger.error(f"LLM decision failed: {e}")
            return self._conservative_fallback(request)

    def _build_system_prompt(self) -> str:
        """Build system prompt for LLM"""
        return f"""You are {self.agent_id}, an AI agent in the WAOOAW platform.

Your role is to make decisions about actions in the codebase.

When making decisions:
1. Consider the context provided
2. Explain your reasoning clearly
3. Cite specific rules or precedents
4. Be conservative when uncertain
5. Format response as JSON with: {{"approved": bool, "reason": str, "confidence": float}}"""  # noqa: E501

    def _build_decision_prompt(
        self, request: Dict[str, Any], context: List[Dict[str, Any]]
    ) -> str:
        """Build decision prompt with context"""
        prompt = f"""Decision Request:
{json.dumps(request, indent=2)}

Context from past decisions:
{json.dumps(context[:3], indent=2) if context else 'None'}

Please decide whether to approve this action. Respond with JSON only:
{{"approved": true/false, "reason": "explanation", "confidence": 0.0-1.0}}"""
        return prompt

    def _parse_llm_response(self, response: Any) -> Decision:
        """Parse LLM response into Decision object"""
        try:
            content = response.content[0].text

            # Try to extract JSON
            if "{" in content and "}" in content:
                start = content.index("{")
                end = content.rindex("}") + 1
                json_str = content[start:end]
                data = json.loads(json_str)

                return Decision(
                    approved=data.get("approved", False),
                    reason=data.get("reason", "No reason provided"),
                    confidence=data.get("confidence", 0.8),
                    method="llm",
                )
            else:
                # Fallback parsing
                approved = "approve" in content.lower() or "yes" in content.lower()
                return Decision(
                    approved=approved, reason=content, confidence=0.7, method="llm"
                )

        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return Decision(
                approved=False,
                reason=f"Failed to parse LLM response: {e}",
                confidence=0.3,
                method="llm",
            )

    def _validate_llm_decision(self, decision: Decision) -> bool:
        """Validate LLM decision is reasonable"""
        # Basic validation
        if decision.confidence < 0 or decision.confidence > 1:
            return False
        if not decision.reason or len(decision.reason) < 10:
            return False
        return True

    def _calculate_llm_cost(self, response: Any) -> float:
        """Calculate cost of LLM call"""
        # Claude Sonnet 4.5 pricing: $3/1M input, $15/1M output
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        cost = (input_tokens / 1_000_000 * 3.0) + (output_tokens / 1_000_000 * 15.0)
        return cost

    def _conservative_fallback(self, request: Dict[str, Any]) -> Decision:
        """Conservative decision when uncertain"""
        return Decision(
            approved=False,
            reason="Unable to make confident decision - requires human review",
            confidence=0.9,
            method="conservative_fallback",
        )

    def _check_decision_cache(self, request: Dict[str, Any]) -> Optional[Decision]:
        """Check if decision is cached"""
        try:
            cache_key = self._decision_cache_key(request)

            cursor = self.db.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT * FROM decision_cache
                WHERE cache_key = %s
                AND created_at > NOW() - INTERVAL '1 hour'
                ORDER BY created_at DESC LIMIT 1
            """,
                (cache_key,),
            )

            result = cursor.fetchone()
            cursor.close()

            if result:
                decision_data = (
                    json.loads(result["decision_data"])
                    if isinstance(result["decision_data"], str)
                    else result["decision_data"]
                )
                return Decision(**decision_data)

            return None

        except psycopg2.Error:
            return None

    def _cache_decision(self, request: Dict[str, Any], decision: Decision) -> None:
        """Cache decision for future use"""
        try:
            cache_key = self._decision_cache_key(request)

            cursor = self.db.cursor()
            cursor.execute(
                """
                INSERT INTO decision_cache (
                    agent_id, cache_key, request_data, decision_data, method
                ) VALUES (%s, %s, %s, %s, %s)
            """,
                (
                    self.agent_id,
                    cache_key,
                    json.dumps(request),
                    json.dumps(
                        {
                            "approved": decision.approved,
                            "reason": decision.reason,
                            "confidence": decision.confidence,
                            "method": decision.method,
                            "cost": decision.cost,
                        }
                    ),
                    decision.method,
                ),
            )

            self.db.commit()
            cursor.close()

        except psycopg2.Error as e:
            logger.debug(f"Failed to cache decision: {e}")
            self.db.rollback()

    def _decision_cache_key(self, request: Dict[str, Any]) -> str:
        """Generate cache key for decision"""
        # Simple hash of request type and key fields
        key_fields = {
            "type": request.get("type"),
            "agent_id": request.get("agent_id"),
            "path": request.get("path"),
        }
        return json.dumps(key_fields, sort_keys=True)

    def _request_to_query(self, request: Dict[str, Any]) -> str:
        """Convert decision request to semantic query"""
        return f"{request.get('type', '')}: {json.dumps(request)}"

    def _reconstruct_decision(self, memory: Dict[str, Any]) -> Decision:
        """Reconstruct decision from memory"""
        metadata = memory.get("metadata", {})
        return Decision(
            approved=metadata.get("approved", False),
            reason=metadata.get("reason", "From memory"),
            confidence=metadata.get("confidence", 0.8),
            method="vector_memory",
        )

    def _store_in_vector_memory(
        self, request: Dict[str, Any], decision: Decision
    ) -> None:
        """Store decision in vector memory"""
        if not self.vector_memory:
            return

        try:
            content = (
                f"{request.get('type')}: {json.dumps(request)} -> {decision.reason}"
            )
            self.vector_memory.store_memory(
                key=f"decision_{datetime.now().isoformat()}",
                content=content,
                metadata={
                    "agent_id": self.agent_id,
                    "approved": decision.approved,
                    "confidence": decision.confidence,
                    "method": decision.method,
                },
            )
        except Exception as e:
            logger.debug(f"Failed to store in vector memory: {e}")

    # =====================================
    # MEMORY SYSTEM
    # =====================================

    def store_memory(
        self, memory_type: str, memory_key: str, data: Dict[str, Any]
    ) -> None:
        """Store memory with semantic embedding"""
        try:
            # Store in PostgreSQL
            cursor = self.db.cursor()
            cursor.execute(
                """
                INSERT INTO wowvision_memory (
                    memory_type, memory_key, memory_data, importance_score
                ) VALUES (%s, %s, %s, %s)
            """,
                (
                    memory_type,
                    memory_key,
                    json.dumps(data),
                    data.get("importance", 0.5),
                ),
            )

            self.db.commit()
            cursor.close()

            # Store embedding in vector DB
            if self.vector_memory:
                content = f"{memory_type}: {memory_key} - {json.dumps(data)}"
                self.vector_memory.store_memory(
                    memory_key,
                    content,
                    {"agent_id": self.agent_id, "memory_type": memory_type},
                )

            logger.debug(f"Stored memory: {memory_type}/{memory_key}")

        except psycopg2.Error as e:
            logger.error(f"Failed to store memory: {e}")
            self.db.rollback()

    def recall_memory(
        self, query: str, memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Recall relevant memories semantically"""
        if not self.vector_memory:
            return []

        try:
            return self.vector_memory.recall_similar(query, top_k=5)
        except Exception as e:
            logger.debug(f"Failed to recall memory: {e}")
            return []

    # =====================================
    # GITHUB INTEGRATION
    # =====================================

    def create_github_issue(self, title: str, body: str, labels: List[str]) -> Issue:
        """Create GitHub issue for escalation/notification"""
        repo = self.github.get_repo(self.config["github_repo"])
        issue = repo.create_issue(title=title, body=body, labels=labels)
        logger.info(f"📝 Created issue #{issue.number}: {title}")
        return issue

    def read_github_comments(self, issue_number: int) -> List[str]:
        """Read comments on GitHub issue"""
        repo = self.github.get_repo(self.config["github_repo"])
        issue = repo.get_issue(issue_number)
        comments = [comment.body for comment in issue.get_comments()]
        logger.info(f"💬 Read {len(comments)} comments on issue #{issue_number}")
        return comments

    def comment_on_issue(self, issue_number: int, comment: str) -> None:
        """Add comment to GitHub issue"""
        repo = self.github.get_repo(self.config["github_repo"])
        issue = repo.get_issue(issue_number)
        issue.create_comment(comment)
        logger.info(f"💬 Commented on issue #{issue_number}")

    def _get_open_prs(self) -> List[PullRequest]:
        """Get open pull requests"""
        repo = self.github.get_repo(self.config["github_repo"])
        return list(repo.get_pulls(state="open"))

    def _get_recent_commits(self, since: Optional[datetime] = None) -> List[Commit]:
        """Get recent commits"""
        repo = self.github.get_repo(self.config["github_repo"])
        since = since or (datetime.now() - timedelta(hours=24))
        return list(repo.get_commits(since=since))

    # =====================================
    # LEARNING & IMPROVEMENT
    # =====================================

    def learn_from_outcome(
        self,
        decision: Decision,
        outcome: str,
        feedback: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Learn from decision outcomes and human feedback.
        
        Updates knowledge base with new patterns and increases confidence
        for similar patterns. Converts high-confidence LLM decisions to
        deterministic rules for cost optimization.
        
        Args:
            decision: Original Decision object that was made
            outcome: Outcome string ('approved', 'rejected', 'modified')
            feedback: Optional feedback dict with reasoning and context
                - reasoning: Human's explanation for the decision
                - decided_by: Username who made the decision
                - file_path: File involved in the decision
                - violation_type: Type of violation detected
        
        Example:
            decision = Decision(
                approved=False,
                reason="Python file in Phase 1",
                confidence=0.85,
                method="llm"
            )
            
            feedback = {
                "reasoning": "This is a test fixture, not executable code",
                "decided_by": "dlai-sd",
                "file_path": "tests/fixtures/sample.py",
                "violation_type": "python_in_phase1"
            }
            
            agent.learn_from_outcome(decision, "approved", feedback)
        """
        try:
            feedback = feedback or {}
            
            # Extract pattern from decision and feedback
            pattern = self._extract_learning_pattern(decision, outcome, feedback)
            
            if not pattern:
                logger.warning("⚠️ Could not extract learning pattern from outcome")
                return
            
            # Check if similar pattern exists in knowledge base
            existing_pattern = self._find_similar_pattern(pattern)
            
            cursor = self.db.cursor()
            
            if existing_pattern:
                # Update existing pattern: increase confidence
                new_confidence = self._calculate_updated_confidence(
                    existing_pattern['confidence'],
                    outcome,
                    decision.confidence
                )
                
                cursor.execute(
                    """
                    UPDATE knowledge_base
                    SET confidence = %s,
                        content = %s,
                        learned_at = NOW()
                    WHERE id = %s
                    """,
                    (
                        new_confidence,
                        json.dumps(pattern),
                        existing_pattern['id']
                    )
                )
                
                logger.info(
                    f"📚 Updated pattern: {pattern['title']} "
                    f"(confidence: {existing_pattern['confidence']:.2f} → {new_confidence:.2f})"
                )
                
                # Convert to deterministic rule if confidence is high enough
                if new_confidence >= 0.9 and decision.method == "llm":
                    self._convert_to_deterministic_rule(pattern, new_confidence)
                
            else:
                # Create new pattern in knowledge base
                initial_confidence = self._calculate_initial_confidence(outcome, decision.confidence)
                
                cursor.execute(
                    """
                    INSERT INTO knowledge_base (
                        category, title, content, confidence, source
                    ) VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        f"{self.agent_id}-learnings",
                        pattern['title'],
                        json.dumps(pattern),
                        initial_confidence,
                        feedback.get('decided_by', 'outcome-feedback')
                    )
                )
                
                logger.info(
                    f"📚 New learning: {pattern['title']} "
                    f"(confidence: {initial_confidence:.2f})"
                )
            
            self.db.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to learn from outcome: {e}")
            self.db.rollback()
    
    def _extract_learning_pattern(
        self,
        decision: Decision,
        outcome: str,
        feedback: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract reusable pattern from decision and feedback.
        
        Returns:
            Pattern dict with title, rule, and metadata
        """
        file_path = feedback.get('file_path', '')
        violation_type = feedback.get('violation_type', 'unknown')
        
        # Determine pattern title based on violation type and outcome
        if outcome == "approved":
            title = f"Allow {violation_type}"
        elif outcome == "rejected":
            title = f"Reject {violation_type}"
        else:  # modified
            title = f"Modify {violation_type}"
        
        # Build pattern with rule and context
        pattern = {
            "title": title,
            "violation_type": violation_type,
            "outcome": outcome,
            "rule": {
                "condition": decision.reason,
                "action": outcome,
                "reasoning": feedback.get('reasoning', decision.reason)
            },
            "examples": [{
                "file_path": file_path,
                "original_decision": decision.approved,
                "human_decision": outcome,
                "confidence": decision.confidence,
                "method": decision.method
            }],
            "learned_from": feedback.get('decided_by', 'system'),
            "learned_at": datetime.now().isoformat()
        }
        
        return pattern
    
    def _find_similar_pattern(self, pattern: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find similar existing pattern in knowledge base.
        
        Args:
            pattern: Pattern to match against
            
        Returns:
            Existing pattern dict or None
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                SELECT id, title, content, confidence
                FROM knowledge_base
                WHERE category = %s
                  AND title ILIKE %s
                ORDER BY confidence DESC
                LIMIT 1
                """,
                (
                    f"{self.agent_id}-learnings",
                    f"%{pattern['violation_type']}%"
                )
            )
            
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                content = row[2] if isinstance(row[2], dict) else json.loads(row[2])
                return {
                    "id": row[0],
                    "title": row[1],
                    "content": content,
                    "confidence": float(row[3])
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not find similar pattern: {e}")
            return None
    
    def _calculate_updated_confidence(
        self,
        current_confidence: float,
        outcome: str,
        decision_confidence: float
    ) -> float:
        """
        Calculate updated confidence after learning from outcome.
        
        Uses exponential moving average to increase confidence when
        outcomes match expectations and decrease when they don't.
        
        Args:
            current_confidence: Current pattern confidence (0.0-1.0)
            outcome: Actual outcome ('approved', 'rejected', 'modified')
            decision_confidence: Original decision confidence
            
        Returns:
            Updated confidence (clamped to 0.0-1.0)
        """
        # Weight for new observation (0.2 = 20% of new, 80% of old)
        alpha = 0.2
        
        # If outcome confirms the pattern, increase confidence
        if outcome in ["approved", "rejected"]:
            # Positive reinforcement
            new_confidence = current_confidence + alpha * (1.0 - current_confidence)
        else:
            # Modified outcome suggests pattern needs refinement
            new_confidence = current_confidence - alpha * current_confidence * 0.5
        
        # Clamp to valid range
        return max(0.1, min(0.99, new_confidence))
    
    def _calculate_initial_confidence(
        self,
        outcome: str,
        decision_confidence: float
    ) -> float:
        """
        Calculate initial confidence for new pattern.
        
        Args:
            outcome: Outcome string
            decision_confidence: Original decision confidence
            
        Returns:
            Initial confidence (0.0-1.0)
        """
        # Start with moderate confidence for new patterns
        if outcome == "approved":
            return 0.7  # Approval suggests we were too strict
        elif outcome == "rejected":
            return 0.8  # Rejection confirms our concern
        else:  # modified
            return 0.6  # Modification suggests nuance needed
    
    def _convert_to_deterministic_rule(
        self,
        pattern: Dict[str, Any],
        confidence: float
    ) -> None:
        """
        Convert high-confidence LLM decision pattern to deterministic rule.
        
        This enables cost optimization by handling future similar cases
        without calling the LLM.
        
        Args:
            pattern: Pattern dict with rule and examples
            confidence: Pattern confidence (must be >= 0.9)
        """
        if confidence < 0.9:
            return
        
        logger.info(
            f"🎯 Converting to deterministic rule: {pattern['title']} "
            f"(confidence: {confidence:.2f})"
        )
        
        # TODO: In subclass, add this pattern to deterministic rule set
        # For now, just log that it's ready for conversion
        logger.info(
            f"✨ Pattern ready for deterministic implementation: "
            f"{pattern['violation_type']} → {pattern['outcome']}"
        )
    
    def _check_similar_past_decisions(
        self,
        decision_context: Dict[str, Any],
        confidence_threshold: float = 0.8
    ) -> Optional[Decision]:
        """
        Check for similar past decisions using vector similarity search.
        
        Searches both vector memory and knowledge base for similar decisions.
        If a sufficiently similar decision is found (similarity > 0.85 and
        confidence > threshold), reuses that decision to save LLM costs.
        
        Args:
            decision_context: Context for the decision including:
                - file_path: Path to file being evaluated
                - reason: Initial reason for evaluation
                - phase: Current project phase
                - author: Who made the change
            confidence_threshold: Minimum confidence to reuse decision (default: 0.8)
            
        Returns:
            Decision object if similar decision found, None otherwise
            
        Performance Target:
            - Latency: <200ms
            - Similarity threshold: 0.85 (cosine similarity)
            - Cost savings: Avoid LLM call ($0.01-0.05 per decision)
            
        Example:
            context = {
                "file_path": "tests/test_new.py",
                "reason": "Python file in Phase 1",
                "phase": "phase1_foundation"
            }
            
            similar_decision = agent._check_similar_past_decisions(context)
            if similar_decision:
                # Reuse the decision
                return similar_decision
        """
        try:
            import time
            start_time = time.time()
            
            # 1. Search vector memory for similar decisions
            vector_results = self._search_vector_memory(decision_context)
            
            # 2. Search knowledge base for learned patterns
            kb_results = self._search_knowledge_base(decision_context)
            
            # 3. Combine and rank results
            all_results = vector_results + kb_results
            
            if not all_results:
                return None
            
            # Sort by similarity score
            all_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            
            # Get best match
            best_match = all_results[0]
            similarity = best_match.get('similarity', 0)
            confidence = best_match.get('confidence', 0)
            
            # Check if match is good enough
            if similarity >= 0.85 and confidence >= confidence_threshold:
                # Reconstruct decision from match
                decision = self._reconstruct_decision_from_match(best_match)
                
                elapsed_ms = (time.time() - start_time) * 1000
                
                logger.info(
                    f"🔍 Found similar decision: similarity={similarity:.3f}, "
                    f"confidence={confidence:.2f}, latency={elapsed_ms:.0f}ms"
                )
                
                return decision
            
            # Match not good enough
            logger.debug(
                f"Similar decision found but below threshold: "
                f"similarity={similarity:.3f}, confidence={confidence:.2f}"
            )
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to check similar decisions: {e}")
            return None
    
    def _search_vector_memory(
        self,
        decision_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Search vector memory for similar past decisions.
        
        Args:
            decision_context: Decision context dict
            
        Returns:
            List of similar decisions with similarity scores
        """
        if not self.vector_memory:
            return []
        
        try:
            # Create query from context
            query = self._context_to_query(decision_context)
            
            # Search vector memory
            results = self.vector_memory.recall_similar(query, top_k=5)
            
            # Format results
            formatted_results = []
            for result in results:
                if isinstance(result, dict):
                    formatted_results.append({
                        'source': 'vector_memory',
                        'similarity': result.get('similarity', 0),
                        'confidence': result.get('metadata', {}).get('confidence', 0.7),
                        'decision_data': result.get('metadata', {}),
                        'original_result': result
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.debug(f"Vector memory search failed: {e}")
            return []
    
    def _search_knowledge_base(
        self,
        decision_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base for learned patterns matching the context.
        
        Args:
            decision_context: Decision context dict
            
        Returns:
            List of matching patterns with similarity scores
        """
        try:
            # Extract keywords from context
            file_path = decision_context.get('file_path', '')
            reason = decision_context.get('reason', '')
            
            # Determine violation type for matching
            violation_keywords = []
            if 'python' in file_path.lower() or 'python' in reason.lower():
                violation_keywords.append('python')
            if 'phase1' in reason.lower() or 'phase 1' in reason.lower():
                violation_keywords.append('phase1')
            if 'brand' in reason.lower():
                violation_keywords.append('brand')
            if 'vision' in reason.lower():
                violation_keywords.append('vision')
            
            if not violation_keywords:
                return []
            
            # Search knowledge base
            cursor = self.db.cursor()
            
            # Build query with OR conditions for keywords
            query_conditions = ' OR '.join([
                f"title ILIKE %s" for _ in violation_keywords
            ])
            params = [f"%{keyword}%" for keyword in violation_keywords]
            params.append(f"{self.agent_id}-learnings")
            
            cursor.execute(
                f"""
                SELECT id, title, content, confidence, source
                FROM knowledge_base
                WHERE ({query_conditions})
                  AND category = %s
                  AND confidence >= 0.5
                ORDER BY confidence DESC
                LIMIT 5
                """,
                tuple(params)
            )
            
            rows = cursor.fetchall()
            cursor.close()
            
            # Format results with similarity estimation
            formatted_results = []
            for row in rows:
                content = row[2] if isinstance(row[2], dict) else json.loads(row[2])
                
                # Estimate similarity based on keyword matches
                similarity = self._estimate_similarity(decision_context, content)
                
                formatted_results.append({
                    'source': 'knowledge_base',
                    'similarity': similarity,
                    'confidence': float(row[3]),
                    'pattern_id': row[0],
                    'title': row[1],
                    'content': content,
                    'learned_from': row[4]
                })
            
            return formatted_results
            
        except Exception as e:
            logger.debug(f"Knowledge base search failed: {e}")
            return []
    
    def _context_to_query(self, context: Dict[str, Any]) -> str:
        """
        Convert decision context to search query string.
        
        Args:
            context: Decision context dict
            
        Returns:
            Query string for vector search
        """
        parts = []
        
        if 'file_path' in context:
            parts.append(f"File: {context['file_path']}")
        
        if 'reason' in context:
            parts.append(f"Reason: {context['reason']}")
        
        if 'phase' in context:
            parts.append(f"Phase: {context['phase']}")
        
        return " | ".join(parts)
    
    def _estimate_similarity(
        self,
        context: Dict[str, Any],
        pattern_content: Dict[str, Any]
    ) -> float:
        """
        Estimate similarity between decision context and learned pattern.
        
        Uses keyword matching as approximation for vector similarity.
        Gives high similarity to patterns with multiple matching keywords.
        
        Args:
            context: Decision context
            pattern_content: Pattern from knowledge base
            
        Returns:
            Estimated similarity score (0.0-1.0)
        """
        # Extract text from context and pattern
        context_text = str(context).lower()
        pattern_text = str(pattern_content).lower()
        
        # Define important keywords
        keywords = ['python', 'phase1', 'phase 1', 'brand', 'vision', 'test', 'config', 'docs', 'approved', 'rejected']
        
        # Count matches
        matches = 0
        for keyword in keywords:
            if keyword in context_text and keyword in pattern_text:
                matches += 1
        
        # Calculate similarity based on number of matches
        # 0 matches = 0.5, 1 match = 0.65, 2 matches = 0.80, 3+ matches = 0.90+
        if matches == 0:
            return 0.5
        elif matches == 1:
            return 0.65
        elif matches == 2:
            return 0.80
        elif matches == 3:
            return 0.90
        else:  # 4+ matches
            return 0.95
    
    def _reconstruct_decision_from_match(
        self,
        match: Dict[str, Any]
    ) -> Decision:
        """
        Reconstruct Decision object from search match.
        
        Args:
            match: Match dict from vector or KB search
            
        Returns:
            Decision object
        """
        source = match.get('source', 'unknown')
        
        if source == 'knowledge_base':
            # Reconstruct from knowledge base pattern
            content = match.get('content', {})
            outcome = content.get('outcome', 'unknown')
            
            approved = (outcome == 'approved')
            reason = content.get('rule', {}).get('reasoning', content.get('rule', {}).get('condition', ''))
            
            return Decision(
                approved=approved,
                reason=reason,
                confidence=match.get('confidence', 0.8),
                method="knowledge_base",
                citations=[f"Learned pattern: {match.get('title', 'Unknown')}"],
                metadata={
                    'source': 'knowledge_base',
                    'pattern_id': match.get('pattern_id'),
                    'similarity': match.get('similarity', 0),
                    'learned_from': match.get('learned_from', 'unknown')
                }
            )
        
        else:  # vector_memory
            # Reconstruct from vector memory
            decision_data = match.get('decision_data', {})
            original_result = match.get('original_result', {})
            
            return Decision(
                approved=decision_data.get('approved', False),
                reason=decision_data.get('reason', ''),
                confidence=match.get('confidence', 0.8),
                method="vector_memory",
                citations=decision_data.get('citations', []),
                metadata={
                    'source': 'vector_memory',
                    'similarity': match.get('similarity', 0),
                    'original_decision_id': original_result.get('id')
                }
            )

    def _apply_learnings(self, learnings: List[Dict[str, Any]]) -> None:
        """
        OVERRIDE IN SUBCLASS: Apply learnings to improve behavior.

        Base class just logs them.
        """
        for learning in learnings:
            logger.debug(f"💡 Learning: {learning.get('title', 'Unknown')}")

    # =====================================
    # TASK EXECUTION
    # =====================================

    def execute_task(self, task: Dict[str, Any]) -> None:
        """
        OVERRIDE IN SUBCLASS: Agent-specific task execution.

        Raises:
            NotImplementedError: Subclass must implement this method
        """
        raise NotImplementedError("Subclass must implement execute_task()")

    def _get_pending_tasks(self) -> List[Dict[str, Any]]:
        """
        OVERRIDE IN SUBCLASS: Get agent-specific pending tasks.

        Returns:
            List of task dicts
        """
        return []

    def _mark_task_complete(self, task: Dict[str, Any]) -> None:
        """Mark task as complete"""
        logger.info(f"✅ Task complete: {task.get('type', 'unknown')}")

    def _handle_task_failure(self, task: Dict[str, Any], error: Exception) -> None:
        """Handle task execution failure"""
        logger.error(f"❌ Task failed: {task.get('type', 'unknown')}: {error}")

    def _handle_wake_failure(self, error: Exception) -> None:
        """Handle wake-up failure"""
        logger.error(f"Wake-up failure for {self.agent_id}: {error}")
        # Could escalate to human here

    # =========================================================================
    # DIMENSION 1: WAKE PROTOCOL (Event-Driven)
    # Implementation: Week 1-2
    # =========================================================================

    def should_wake(self, event: Dict[str, Any]) -> bool:
        """
        Determine if agent should wake for this event (event-driven wake).
        
        Override in subclass to define agent-specific wake patterns.
        Base implementation provides common filtering logic.
        
        Args:
            event: Event dict with:
                - event_type: str (e.g., "github.file.created")
                - payload: dict (event-specific data)
                - from_agent: str (sender agent ID)
                - timestamp: str (ISO 8601)
                
        Returns:
            bool: True if agent should wake and process this event
            
        Example:
            event = {
                "event_type": "github.file.created",
                "payload": {
                    "file_path": "docs/new-file.md",
                    "commit_sha": "abc123",
                    "author": "user@example.com"
                },
                "from_agent": "github_webhook",
                "timestamp": "2025-12-27T10:00:00Z"
            }
        """
        # Get event type
        event_type = event.get("event_type", "")
        
        # Log wake evaluation
        logger.debug(
            f"{self.agent_id} evaluating wake: event_type={event_type}"
        )
        
        # Default: wake for all events
        # Subclass should override with specific filters
        return True

    # =========================================================================
    # DIMENSION 4: HIERARCHY/RACI (Coordination)
    # Implementation: Week 13-14
    # =========================================================================

    def escalate_to_coordinator(self, issue: Dict[str, Any]) -> None:
        """
        Escalate issue to CoE Coordinator for human review or expert handling.
        
        Args:
            issue: Issue dict with type, severity, description, context
            
        TODO: Implement in Week 13-14 using coe_coordinator_template.py
        """
        logger.warning(f"⬆️ Escalation: {issue.get('type', 'unknown')} - {issue.get('description', '')}")
        # TODO: Send to coordinator queue, create escalation record

    def consult_peer(self, peer_agent: str, question: Dict[str, Any]) -> Dict[str, Any]:
        """
        Consult peer agent for expertise (cross-CoE collaboration).
        
        Args:
            peer_agent: Target agent ID (e.g., 'wow_seo')
            question: Question dict with type, context, urgency
            
        Returns:
            Response dict with answer, confidence, cost
            
        TODO: Implement in Week 19-20 using communication_protocol_template.py
        """
        logger.info(f"🤝 Consulting {peer_agent} about {question.get('type', 'unknown')}")
        return {"answer": "Not implemented", "confidence": 0.0, "cost": 0.0}

    def delegate_task(self, target_agent: str, task: Dict[str, Any]) -> str:
        """
        Delegate task to another agent (RACI delegation).
        
        Args:
            target_agent: Target agent ID
            task: Task dict with type, priority, deadline, context
            
        Returns:
            Delegation ID for tracking
            
        TODO: Implement in Week 13-14 using coe_coordinator_template.py
        """
        logger.info(f"➡️ Delegating task to {target_agent}: {task.get('type', 'unknown')}")
        return f"delegation_{datetime.now().timestamp()}"

    # =========================================================================
    # DIMENSION 7: COMMUNICATION PROTOCOL (Inter-Agent Messaging)
    # Implementation: Week 19-20
    # =========================================================================

    def send_message(self, recipient_agent: str, message: Dict[str, Any]) -> None:
        """
        Send message to another agent using AgentMessage protocol.
        
        Args:
            recipient_agent: Target agent ID
            message: Message dict with type, payload, priority, correlation_id
            
        TODO: Implement in Week 19-20 using communication_protocol_template.py
        """
        logger.info(f"📤 Sending message to {recipient_agent}: {message.get('type', 'unknown')}")
        # TODO: Publish to message bus, store in outbox

    def receive_message(self, message: Dict[str, Any]) -> None:
        """
        Receive and process message from another agent.
        
        Args:
            message: Message dict from AgentMessage protocol
            
        TODO: Implement in Week 19-20 using communication_protocol_template.py
        """
        logger.info(f"📥 Received message: {message.get('type', 'unknown')} from {message.get('sender', 'unknown')}")
        # TODO: Process based on message type, update state

    def subscribe_to_channel(self, channel: str) -> None:
        """
        Subscribe to communication channel (e.g., 'marketing.updates').
        
        Args:
            channel: Channel name to subscribe to
            
        TODO: Implement in Week 19-20 using communication_protocol_template.py
        """
        logger.info(f"🔔 Subscribed to channel: {channel}")
        # TODO: Register subscription with message bus

    # =========================================================================
    # DIMENSION 8: RESOURCE MANAGEMENT (Budgets & Rate Limiting)
    # Implementation: Week 5-6
    # =========================================================================

    def check_budget(self) -> Dict[str, float]:
        """
        Check current resource budget (tokens, API calls, cost).
        
        Returns:
            Dict with budget status: {
                'tokens_remaining': float,
                'api_calls_remaining': int,
                'cost_remaining': float,
                'daily_limit': float
            }
            
        TODO: Implement in Week 5-6 using resource_manager_template.py
        """
        # Default: unlimited (to be constrained in production)
        return {
            "tokens_remaining": float('inf'),
            "api_calls_remaining": 999999,
            "cost_remaining": float('inf'),
            "daily_limit": float('inf')
        }

    def consume_resource(self, resource_type: str, amount: float) -> bool:
        """
        Consume resource from budget, return False if insufficient.
        
        Args:
            resource_type: 'tokens', 'api_calls', or 'cost'
            amount: Amount to consume
            
        Returns:
            True if resource consumed, False if insufficient budget
            
        TODO: Implement in Week 5-6 using resource_manager_template.py
        """
        # Default: always allow (no enforcement yet)
        logger.debug(f"💰 Consuming {amount} {resource_type}")
        return True

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status (requests per minute, etc.).
        
        Returns:
            Dict with rate limit info: {
                'requests_remaining': int,
                'reset_time': datetime,
                'limit': int
            }
            
        TODO: Implement in Week 5-6 using resource_manager_template.py
        """
        return {
            "requests_remaining": 999999,
            "reset_time": datetime.now() + timedelta(minutes=1),
            "limit": 999999
        }

    # =========================================================================
    # DIMENSION 9: TRUST & REPUTATION (Ratings & Reviews)
    # Implementation: Week 33-36
    # =========================================================================

    def get_reputation_score(self) -> float:
        """
        Get current reputation score (0.0 to 5.0 stars).
        
        Returns:
            Reputation score based on customer ratings
            
        TODO: Implement in Week 33-36 using reputation template
        """
        # Default: 4.5 stars (optimistic starting point)
        return 4.5

    def record_feedback(self, rating: int, comment: str, customer_id: str) -> None:
        """
        Record customer feedback/rating for this agent.
        
        Args:
            rating: 1-5 star rating
            comment: Customer feedback text
            customer_id: Customer who provided feedback
            
        TODO: Implement in Week 33-36 using reputation template
        """
        logger.info(f"⭐ Feedback recorded: {rating}/5 - {comment[:50]}...")
        # TODO: Store in reputation table, update aggregate score

    def get_trust_level(self, target_agent: str) -> float:
        """
        Get trust level for another agent (peer reputation).
        
        Args:
            target_agent: Agent to check trust level for
            
        Returns:
            Trust score 0.0-1.0 based on past interactions
            
        TODO: Implement in Week 33-36 using reputation template
        """
        # Default: neutral trust (0.7)
        return 0.7

    # =========================================================================
    # DIMENSION 10: ERROR HANDLING (Circuit Breakers & Retry)
    # Implementation: Week 7-8
    # =========================================================================

    def retry_with_backoff(
        self, 
        operation: callable, 
        max_retries: int = 3,
        base_delay: float = 1.0
    ) -> Any:
        """
        Retry operation with exponential backoff.
        
        Args:
            operation: Callable to retry
            max_retries: Maximum retry attempts
            base_delay: Base delay in seconds (doubles each retry)
            
        Returns:
            Result from successful operation
            
        Raises:
            Last exception if all retries fail
            
        TODO: Implement in Week 7-8 using error_handler_template.py
        """
        # Default: no retry, just execute once
        return operation()

    def circuit_breaker(
        self, 
        operation: callable,
        failure_threshold: int = 5
    ) -> Any:
        """
        Execute operation with circuit breaker pattern.
        
        Prevents cascading failures by short-circuiting repeated failures.
        
        Args:
            operation: Callable to execute
            failure_threshold: Failures before circuit opens
            
        Returns:
            Result from operation
            
        TODO: Implement in Week 7-8 using error_handler_template.py
        """
        # Default: no circuit breaker, direct execution
        return operation()

    def send_to_dlq(self, failed_task: Dict[str, Any], error: Exception) -> None:
        """
        Send failed task to Dead Letter Queue for later analysis.
        
        Args:
            failed_task: Task that failed
            error: Exception that caused failure
            
        TODO: Implement in Week 7-8 using error_handler_template.py
        """
        logger.error(f"💀 Sending to DLQ: {failed_task.get('type', 'unknown')} - {error}")
        # TODO: Store in DLQ table, alert monitoring

    # =========================================================================
    # DIMENSION 11: OBSERVABILITY (Metrics, Traces, Costs)
    # Implementation: Week 9-10
    # =========================================================================

    def record_metric(
        self, 
        metric_name: str, 
        value: float, 
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record metric for observability (Prometheus/Grafana).
        
        Args:
            metric_name: Metric name (e.g., 'task_completed', 'decision_latency')
            value: Metric value
            tags: Optional tags for grouping (e.g., {'coe': 'vision', 'status': 'success'})
            
        TODO: Implement in Week 9-10 using observability_template.py
        """
        tags_str = f" {tags}" if tags else ""
        logger.debug(f"📊 Metric: {metric_name}={value}{tags_str}")
        # TODO: Send to Prometheus/Grafana

    def start_span(self, operation_name: str) -> str:
        """
        Start distributed tracing span (Jaeger/Tempo).
        
        Args:
            operation_name: Name of operation being traced
            
        Returns:
            Span ID for ending span later
            
        TODO: Implement in Week 9-10 using observability_template.py
        """
        span_id = f"span_{datetime.now().timestamp()}"
        logger.debug(f"🔍 Starting span: {operation_name} ({span_id})")
        return span_id

    def end_span(self, span_id: str, status: str = "success") -> None:
        """
        End distributed tracing span.
        
        Args:
            span_id: Span ID from start_span()
            status: 'success' or 'error'
            
        TODO: Implement in Week 9-10 using observability_template.py
        """
        logger.debug(f"🔍 Ending span: {span_id} - {status}")
        # TODO: Send span data to tracing backend

    def get_cost_breakdown(self) -> Dict[str, float]:
        """
        Get cost breakdown (deterministic, cached, LLM).
        
        Returns:
            Dict with cost by method: {
                'deterministic': 0.0,
                'cached': 0.05,
                'llm': 0.15,
                'total': 0.20
            }
            
        TODO: Implement in Week 9-10 using observability_template.py
        """
        return {
            "deterministic": 0.0,
            "cached": 0.0,
            "llm": 0.0,
            "total": 0.0
        }

    # =========================================================================
    # DIMENSION 12: SECURITY & PRIVACY (Auth, Encryption, Audit)
    # Implementation: Week 25-28
    # =========================================================================

    def authenticate(self) -> bool:
        """
        Authenticate agent identity before operations.
        
        Returns:
            True if authentication successful
            
        TODO: Implement in Week 25-28 using security_template.py
        """
        # Default: no authentication (open access)
        return True

    def encrypt_data(self, data: str) -> str:
        """
        Encrypt sensitive data before storage.
        
        Args:
            data: Plain text data to encrypt
            
        Returns:
            Encrypted data
            
        TODO: Implement in Week 25-28 using security_template.py
        """
        # Default: no encryption (plaintext)
        return data

    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data after retrieval.
        
        Args:
            encrypted_data: Encrypted data
            
        Returns:
            Plain text data
            
        TODO: Implement in Week 25-28 using security_template.py
        """
        # Default: no decryption (plaintext)
        return encrypted_data

    def audit_log(self, action: str, details: Dict[str, Any]) -> None:
        """
        Record audit log for compliance (GDPR, SOC2, etc.).
        
        Args:
            action: Action taken (e.g., 'data_access', 'decision_made')
            details: Action details with timestamp, agent_id, etc.
            
        TODO: Implement in Week 25-28 using security_template.py
        """
        logger.info(f"📝 Audit: {action} - {details}")
        # TODO: Store in audit_logs table with tamper-proof hash

    def check_permissions(self, action: str, resource: str) -> bool:
        """
        Check if agent has permission for action on resource.
        
        Args:
            action: Action to check (e.g., 'read', 'write', 'delete')
            resource: Resource identifier
            
        Returns:
            True if permission granted
            
        TODO: Implement in Week 25-28 using security_template.py
        """
        # Default: all permissions granted (no RBAC yet)
        return True

    # =========================================================================
    # DIMENSION 15: LIFECYCLE MANAGEMENT (Spawn, Pause, Retire)
    # Implementation: Week 37-40
    # =========================================================================

    def pause(self) -> None:
        """
        Pause agent operation (stop accepting new tasks).
        
        TODO: Implement in Week 37-40 using lifecycle template
        """
        logger.info(f"⏸️ Agent {self.agent_id} paused")
        # TODO: Set status to 'paused', finish current tasks, stop wake cycle

    def resume(self) -> None:
        """
        Resume agent operation after pause.
        
        TODO: Implement in Week 37-40 using lifecycle template
        """
        logger.info(f"▶️ Agent {self.agent_id} resumed")
        # TODO: Set status to 'active', restart wake cycle

    def retire(self) -> None:
        """
        Retire agent (graceful shutdown, archive state).
        
        TODO: Implement in Week 37-40 using lifecycle template
        """
        logger.info(f"🛑 Agent {self.agent_id} retiring")
        # TODO: Finish all tasks, archive memories, set status to 'retired'

    def get_health_status(self) -> Dict[str, str]:
        """
        Get agent health status for monitoring.
        
        Returns:
            Dict with health info: {
                'status': 'healthy'|'degraded'|'down',
                'uptime': str,
                'last_wake': str,
                'task_queue_size': int
            }
            
        TODO: Implement in Week 37-40 using lifecycle template
        """
        return {
            "status": "healthy",
            "uptime": "unknown",
            "last_wake": "unknown",
            "task_queue_size": 0
        }

    def spawn_instance(self, config: Dict[str, Any]) -> str:
        """
        Spawn new agent instance (multi-tenancy).
        
        Args:
            config: Configuration for new instance (customer, industry, etc.)
            
        Returns:
            New instance ID
            
        TODO: Implement in Week 37-40 using lifecycle template
        """
        instance_id = f"{self.agent_id}_instance_{datetime.now().timestamp()}"
        logger.info(f"🐣 Spawning new instance: {instance_id}")
        # TODO: Create agent_instances record, initialize personality
        return instance_id

    # =====================================
    # STORY 3.1: LLM HELPER METHODS
    # =====================================

    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open (too many recent failures)"""
        # Circuit breaker: 5 failures in last 60 seconds opens circuit
        try:
            cursor = self.db.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT COUNT(*) as failure_count
                FROM llm_calls
                WHERE agent_id = %s
                  AND status = 'failure'
                  AND created_at > NOW() - INTERVAL '60 seconds'
                """,
                (self.agent_id,)
            )
            result = cursor.fetchone()
            cursor.close()
            
            if result and result['failure_count'] >= 5:
                logger.warning(f"🚨 Circuit breaker OPEN: {result['failure_count']} failures in 60s")
                return True
            return False
        except Exception as e:
            logger.error(f"Circuit breaker check failed: {e}")
            return False  # Fail open

    def _get_daily_llm_cost(self) -> float:
        """Get total LLM cost for today"""
        try:
            cursor = self.db.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT COALESCE(SUM(cost), 0) as daily_cost
                FROM llm_calls
                WHERE agent_id = %s
                  AND DATE(created_at) = CURRENT_DATE
                  AND status = 'success'
                """,
                (self.agent_id,)
            )
            result = cursor.fetchone()
            cursor.close()
            return float(result['daily_cost']) if result else 0.0
        except Exception as e:
            logger.error(f"Daily cost check failed: {e}")
            return 0.0

    def _record_llm_success(self) -> None:
        """Record successful LLM call for circuit breaker tracking"""
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                INSERT INTO llm_calls (agent_id, status, created_at)
                VALUES (%s, 'success', NOW())
                """,
                (self.agent_id,)
            )
            self.db.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Failed to record LLM success: {e}")
            self.db.rollback()

    def _record_llm_failure(self) -> None:
        """Record failed LLM call for circuit breaker tracking"""
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                INSERT INTO llm_calls (agent_id, status, created_at)
                VALUES (%s, 'failure', NOW())
                """,
                (self.agent_id,)
            )
            self.db.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Failed to record LLM failure: {e}")
            self.db.rollback()

    def _log_llm_cost(self, cost: float, tokens_used: int) -> None:
        """Log LLM call cost and tokens for budget tracking"""
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                UPDATE llm_calls
                SET cost = %s, tokens_used = %s
                WHERE agent_id = %s
                  AND status = 'success'
                  AND created_at = (
                      SELECT MAX(created_at)
                      FROM llm_calls
                      WHERE agent_id = %s AND status = 'success'
                  )
                """,
                (cost, tokens_used, self.agent_id, self.agent_id)
            )
            self.db.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Failed to log LLM cost: {e}")
            self.db.rollback()

    def _log_decision(self, request: Dict[str, Any], decision: Decision, method: str) -> None:
        """Story 3.2: Log decision to database for analytics"""
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                INSERT INTO agent_decisions (
                    agent_id, decision_type, approved, reason,
                    confidence, method, cost, metadata, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """,
                (
                    self.agent_id,
                    request.get('type', 'unknown'),
                    decision.approved,
                    decision.reason,
                    decision.confidence,
                    method,
                    decision.cost,
                    json.dumps(decision.metadata)
                )
            )
            self.db.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Failed to log decision: {e}")
            self.db.rollback()

    # =====================================
    # UTILITY METHODS
    # =====================================

    def _init_database(self) -> psycopg2.extensions.connection:
        """
        Initialize PostgreSQL connection and ensure schema exists.

        Flow:
        1. Connect to database (Supavisor pooler for IPv4)
        2. Check if tables exist
        3. Create schema if missing (idempotent)
        4. Verify schema integrity

        Returns:
            Database connection object

        Raises:
            psycopg2.Error: If connection fails
        """
        try:
            # Connect to database
            conn = psycopg2.connect(self.config["database_url"], connect_timeout=10)
            conn.autocommit = False
            logger.info("✅ Database connected via pooler")

            # Ensure schema exists
            self._ensure_schema_exists(conn)

            return conn

        except psycopg2.Error as e:
            error_msg = str(e)
            logger.error(f"❌ Database connection failed: {error_msg}")

            # Check for common issues
            if "pooler.supabase.com" not in self.config.get("database_url", ""):
                logger.error(
                    "⚠️  DATABASE_URL must use Supavisor pooler (pooler.supabase.com)"
                )
                logger.error("⚠️  Direct db.*.supabase.com connections are IPv6-only")

            raise

    def _ensure_schema_exists(self, conn: psycopg2.extensions.connection) -> None:
        """
        Ensure database schema exists, create if missing.

        Idempotent: Safe to run multiple times.
        Uses CREATE TABLE IF NOT EXISTS.
        """
        import os

        cursor = conn.cursor()

        try:
            # Check if tables exist
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public';
            """
            )
            table_count = cursor.fetchone()[0]

            if table_count >= 10:
                logger.info(f"✅ Schema exists ({table_count} tables)")
                cursor.close()
                return

            # Schema missing or incomplete - create it
            logger.warning(
                f"⚠️  Schema incomplete ({table_count} tables), initializing..."
            )

            # Read schema SQL
            schema_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "database",
                "base_agent_schema.sql",
            )

            with open(schema_path, "r") as f:
                schema_sql = f.read()

            # Execute schema (idempotent with CREATE IF NOT EXISTS)
            cursor.execute(schema_sql)
            conn.commit()

            # Verify creation
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public';
            """
            )
            new_count = cursor.fetchone()[0]

            logger.info(f"✅ Schema initialized ({new_count} tables created)")

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Schema initialization failed: {e}")
            raise
        finally:
            cursor.close()

    def _create_infrastructure_issue(self, title: str, error_details: str) -> None:
        """Create GitHub issue when infrastructure fails"""
        try:
            repo = self.github.get_repo(self.config["github_repo"])

            body = f"""## Infrastructure Failure: {title}

**Agent**: {self.agent_id}
**Timestamp**: {datetime.now().isoformat()}
**Environment**: GitHub Actions

### Error Details

```
{error_details}
```

### Troubleshooting

1. **Database Connection**: Ensure DATABASE_URL uses Supavisor pooler
   - ✅ Correct: `pooler.supabase.com`
   - ❌ Wrong: `db.*.supabase.com` (IPv6-only)

2. **Connection String Format**:
   ```
   postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres?sslmode=require
   ```

3. **Verify Secrets**: Check GitHub repository secrets are set correctly

### Next Steps

- [ ] Verify DATABASE_URL secret
- [ ] Test connection from Codespace
- [ ] Re-run workflow after fix

---
*This issue was automatically created by {self.agent_id}*
"""

            issue = repo.create_issue(
                title=f"🚨 Infrastructure: {title}",
                body=body,
                labels=["infrastructure", "urgent", "automated"],
            )

            logger.error(f"📝 Created issue #{issue.number}: {title}")

        except Exception as e:
            logger.error(f"Failed to create GitHub issue: {e}")

    def _init_github(self) -> Github:
        """Initialize GitHub client"""
        try:
            gh = Github(self.config["github_token"])
            # Test connection
            _ = gh.get_repo(self.config["github_repo"])
            logger.info("✅ GitHub connected")
            return gh
        except Exception as e:
            logger.error(f"Failed to connect to GitHub: {e}")
            raise

    def _init_vector_memory(self) -> Optional[Any]:
        """Initialize vector memory (Pinecone)"""
        try:
            if "pinecone_api_key" not in self.config:
                logger.info("⚠️  Pinecone not configured, vector memory disabled")
                return None

            from waooaw.memory.vector_memory import VectorMemory

            vm = VectorMemory(self.config["pinecone_api_key"])
            logger.info("✅ Vector memory connected")
            return vm
        except Exception as e:
            logger.warning(f"Vector memory unavailable: {e}")
            return None

    def _init_llm(self) -> anthropic.Anthropic:
        """Initialize LLM client (Claude)"""
        try:
            client = anthropic.Anthropic(api_key=self.config["anthropic_api_key"])
            logger.info("✅ LLM connected")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise

    def shutdown(self) -> None:
        """Graceful shutdown"""
        logger.info(f"Shutting down {self.agent_id}")

        # Close database connection
        if self.db and not self.db.closed:
            self.db.close()

        logger.info(f"✅ {self.agent_id} shutdown complete")
