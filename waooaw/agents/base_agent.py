"""
WAOOAW Base Agent - Core agent class for all CoEs

This module provides the WAAOOWAgent base class that all 14 Centers of Excellence
inherit from. It implements:
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


class WAAOOWAgent:
    """
    Base class for all WAOOAW platform agents.
    
    All 14 CoEs inherit from this foundation.
    Provides:
    - Persistent memory (PostgreSQL + vector embeddings)
    - 6-step wake-up protocol
    - Decision framework (deterministic + LLM)
    - GitHub integration
    - Learning & improvement
    - Safety & validation
    
    Subclasses must override:
    - _restore_identity(): Load agent-specific identity
    - execute_task(): Agent-specific task execution
    - _get_pending_tasks(): Domain-specific task queue
    
    Subclasses should override:
    - _try_deterministic_decision(): Domain-specific rules
    - _apply_learnings(): Use knowledge to improve
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
        """
        self.agent_id = agent_id
        self.config = config
        
        # Core components
        self.db = self._init_database()
        self.github = self._init_github()
        self.vector_memory = self._init_vector_memory()
        self.llm = self._init_llm()
        
        # State
        self.wake_count = 0
        self.start_time = datetime.now()
        self.context: Dict[str, Any] = {}
        self.pending_tasks: List[Dict[str, Any]] = []
        
        logger.info(f"Initialized agent: {agent_id}")
    
    # =====================================
    # 6-STEP WAKE-UP PROTOCOL
    # =====================================
    
    def wake_up(self) -> None:
        """Execute 6-step wake-up protocol from context preservation architecture"""
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
        if not self.db:
            logger.warning("⏩ Skipping domain context load (database not available)")
            self.context = {}
            return
        
        try:
            cursor = self.db.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM agent_context 
                WHERE agent_id = %s 
                ORDER BY version DESC LIMIT 1
            """, (self.agent_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                self.context = json.loads(result['context_data']) if isinstance(result['context_data'], str) else result['context_data']
                logger.info(f"📚 Loaded context version {result['version']}")
            else:
                self.context = {}
                logger.info("📚 No previous context found, starting fresh")
                
        except Exception as e:
            logger.warning(f"Failed to load context: {e}")
            self.context = {}
    
    def _check_collaboration_state(self) -> None:
        """Step 3: Check what other agents are doing"""
        if not self.db:
            logger.warning("⏩ Skipping collaboration state check (database not available)")
            self.context['pending_handoffs'] = []
            return
        
        try:
            cursor = self.db.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM agent_handoffs 
                WHERE target_agent_id = %s AND status = 'pending'
            """, (self.agent_id,))
            
            handoffs = cursor.fetchall()
            cursor.close()
            
            self.context['pending_handoffs'] = handoffs
            logger.info(f"🤝 {len(handoffs)} pending handoffs")
            
        except psycopg2.Error as e:
            # Table might not exist yet
            logger.debug(f"Could not check collaboration state: {e}")
            self.context['pending_handoffs'] = []
    
    def _process_learning_queue(self) -> None:
        """Step 4: Apply learnings from past iterations"""
        if not self.db:
            logger.warning("⏩ Skipping learning queue (database not available)")
            return
        
        try:
            cursor = self.db.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM knowledge_base 
                WHERE category LIKE %s 
                ORDER BY learned_at DESC LIMIT 10
            """, (f"{self.agent_id}-%",))
            
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
        if not self.db:
            logger.warning("⏩ Skipping context save (database not available)")
            return
        
        try:
            # Update context with versioning
            cursor = self.db.cursor()
            context_data = json.dumps(self._serialize_context())
            
            cursor.execute("""
                INSERT INTO agent_context (
                    agent_id, context_type, context_data, version
                ) VALUES (%s, %s, %s, %s)
            """, (
                self.agent_id,
                'wake_cycle',
                context_data,
                self.wake_count
            ))
            
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
            'wake_count': self.wake_count,
            'last_wake': self.start_time.isoformat(),
            'context': self.context,
            'metadata': {
                'agent_version': '1.0.0',
                'saved_at': datetime.now().isoformat()
            }
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
        """
        Hybrid decision framework:
        1. Try deterministic logic first (fast, cheap, reliable)
        2. Check decision cache
        3. Check vector memory for similar past decisions
        4. Use LLM for complex/ambiguous cases
        
        Args:
            decision_request: Decision request dict with:
                - type: str (decision type)
                - context: dict (relevant context)
                - **kwargs: Request-specific data
        
        Returns:
            Decision object with approval, reason, confidence, etc.
        """
        logger.debug(f"Making decision: {decision_request.get('type', 'unknown')}")
        
        # Tier 1: Check cache
        cached = self._check_decision_cache(decision_request)
        if cached:
            logger.info("💰 Decision from cache (FREE)")
            return cached
        
        # Tier 2: Try deterministic logic
        deterministic = self._try_deterministic_decision(decision_request)
        if deterministic.confidence >= 0.95:
            self._cache_decision(decision_request, deterministic)
            logger.info(f"⚡ Deterministic decision (confidence={deterministic.confidence:.2f})")
            return deterministic
        
        # Tier 3: Check vector memory (if available)
        if self.vector_memory:
            similar = self.vector_memory.recall_similar(
                query=self._request_to_query(decision_request),
                top_k=5
            )
            
            if similar and len(similar) > 0 and similar[0].get('similarity', 0) > 0.90:
                past_decision = self._reconstruct_decision(similar[0])
                self._cache_decision(decision_request, past_decision)
                logger.info(f"🧠 Decision from memory (similarity={similar[0]['similarity']:.2f})")
                return past_decision
        
        # Tier 4: Use LLM for complex case
        llm_decision = self._ask_llm(decision_request, [] if not self.vector_memory else similar)
        self._cache_decision(decision_request, llm_decision)
        
        if self.vector_memory:
            self._store_in_vector_memory(decision_request, llm_decision)
        
        logger.info(f"🤖 LLM decision (cost=${llm_decision.cost:.4f})")
        
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
            method='none'
        )
    
    def _ask_llm(self, request: Dict[str, Any], context: List[Dict[str, Any]]) -> Decision:
        """Use LLM (Claude Sonnet 4.5) for complex reasoning"""
        try:
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_decision_prompt(request, context)
            
            # Call LLM
            response = self.llm.messages.create(
                model="claude-sonnet-4.5-20250514",
                max_tokens=2048,
                temperature=0.0,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            
            # Parse and validate
            decision = self._parse_llm_response(response)
            
            if not self._validate_llm_decision(decision):
                logger.warning("⚠️  LLM decision failed validation")
                return self._conservative_fallback(request)
            
            # Calculate cost
            decision.cost = self._calculate_llm_cost(response)
            decision.method = 'llm'
            
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
5. Format response as JSON with: {{"approved": bool, "reason": str, "confidence": float}}"""
    
    def _build_decision_prompt(self, request: Dict[str, Any], context: List[Dict[str, Any]]) -> str:
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
            if '{' in content and '}' in content:
                start = content.index('{')
                end = content.rindex('}') + 1
                json_str = content[start:end]
                data = json.loads(json_str)
                
                return Decision(
                    approved=data.get('approved', False),
                    reason=data.get('reason', 'No reason provided'),
                    confidence=data.get('confidence', 0.8),
                    method='llm'
                )
            else:
                # Fallback parsing
                approved = 'approve' in content.lower() or 'yes' in content.lower()
                return Decision(
                    approved=approved,
                    reason=content,
                    confidence=0.7,
                    method='llm'
                )
                
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return Decision(
                approved=False,
                reason=f"Failed to parse LLM response: {e}",
                confidence=0.3,
                method='llm'
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
            method='conservative_fallback'
        )
    
    def _check_decision_cache(self, request: Dict[str, Any]) -> Optional[Decision]:
        """Check if decision is cached"""
        try:
            cache_key = self._decision_cache_key(request)
            
            cursor = self.db.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM decision_cache 
                WHERE cache_key = %s 
                AND created_at > NOW() - INTERVAL '1 hour'
                ORDER BY created_at DESC LIMIT 1
            """, (cache_key,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                decision_data = json.loads(result['decision_data']) if isinstance(result['decision_data'], str) else result['decision_data']
                return Decision(**decision_data)
            
            return None
            
        except psycopg2.Error:
            return None
    
    def _cache_decision(self, request: Dict[str, Any], decision: Decision) -> None:
        """Cache decision for future use"""
        try:
            cache_key = self._decision_cache_key(request)
            
            cursor = self.db.cursor()
            cursor.execute("""
                INSERT INTO decision_cache (
                    agent_id, cache_key, request_data, decision_data, method
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                self.agent_id,
                cache_key,
                json.dumps(request),
                json.dumps({
                    'approved': decision.approved,
                    'reason': decision.reason,
                    'confidence': decision.confidence,
                    'method': decision.method,
                    'cost': decision.cost
                }),
                decision.method
            ))
            
            self.db.commit()
            cursor.close()
            
        except psycopg2.Error as e:
            logger.debug(f"Failed to cache decision: {e}")
            self.db.rollback()
    
    def _decision_cache_key(self, request: Dict[str, Any]) -> str:
        """Generate cache key for decision"""
        # Simple hash of request type and key fields
        key_fields = {
            'type': request.get('type'),
            'agent_id': request.get('agent_id'),
            'path': request.get('path')
        }
        return json.dumps(key_fields, sort_keys=True)
    
    def _request_to_query(self, request: Dict[str, Any]) -> str:
        """Convert decision request to semantic query"""
        return f"{request.get('type', '')}: {json.dumps(request)}"
    
    def _reconstruct_decision(self, memory: Dict[str, Any]) -> Decision:
        """Reconstruct decision from memory"""
        metadata = memory.get('metadata', {})
        return Decision(
            approved=metadata.get('approved', False),
            reason=metadata.get('reason', 'From memory'),
            confidence=metadata.get('confidence', 0.8),
            method='vector_memory'
        )
    
    def _store_in_vector_memory(self, request: Dict[str, Any], decision: Decision) -> None:
        """Store decision in vector memory"""
        if not self.vector_memory:
            return
        
        try:
            content = f"{request.get('type')}: {json.dumps(request)} -> {decision.reason}"
            self.vector_memory.store_memory(
                key=f"decision_{datetime.now().isoformat()}",
                content=content,
                metadata={
                    'agent_id': self.agent_id,
                    'approved': decision.approved,
                    'confidence': decision.confidence,
                    'method': decision.method
                }
            )
        except Exception as e:
            logger.debug(f"Failed to store in vector memory: {e}")
    
    # =====================================
    # MEMORY SYSTEM
    # =====================================
    
    def store_memory(self, memory_type: str, memory_key: str, data: Dict[str, Any]) -> None:
        """Store memory with semantic embedding"""
        try:
            # Store in PostgreSQL
            cursor = self.db.cursor()
            cursor.execute("""
                INSERT INTO wowvision_memory (
                    memory_type, memory_key, memory_data, importance_score
                ) VALUES (%s, %s, %s, %s)
            """, (memory_type, memory_key, json.dumps(data), data.get('importance', 0.5)))
            
            self.db.commit()
            cursor.close()
            
            # Store embedding in vector DB
            if self.vector_memory:
                content = f"{memory_type}: {memory_key} - {json.dumps(data)}"
                self.vector_memory.store_memory(memory_key, content, {
                    'agent_id': self.agent_id,
                    'memory_type': memory_type
                })
            
            logger.debug(f"Stored memory: {memory_type}/{memory_key}")
            
        except psycopg2.Error as e:
            logger.error(f"Failed to store memory: {e}")
            self.db.rollback()
    
    def recall_memory(self, query: str, memory_type: Optional[str] = None) -> List[Dict[str, Any]]:
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
        repo = self.github.get_repo(self.config['github_repo'])
        issue = repo.create_issue(
            title=title,
            body=body,
            labels=labels
        )
        logger.info(f"📝 Created issue #{issue.number}: {title}")
        return issue
    
    def read_github_comments(self, issue_number: int) -> List[str]:
        """Read comments on GitHub issue"""
        repo = self.github.get_repo(self.config['github_repo'])
        issue = repo.get_issue(issue_number)
        comments = [comment.body for comment in issue.get_comments()]
        logger.info(f"💬 Read {len(comments)} comments on issue #{issue_number}")
        return comments
    
    def comment_on_issue(self, issue_number: int, comment: str) -> None:
        """Add comment to GitHub issue"""
        repo = self.github.get_repo(self.config['github_repo'])
        issue = repo.get_issue(issue_number)
        issue.create_comment(comment)
        logger.info(f"💬 Commented on issue #{issue_number}")
    
    def _get_open_prs(self) -> List[PullRequest]:
        """Get open pull requests"""
        repo = self.github.get_repo(self.config['github_repo'])
        return list(repo.get_pulls(state='open'))
    
    def _get_recent_commits(self, since: Optional[datetime] = None) -> List[Commit]:
        """Get recent commits"""
        repo = self.github.get_repo(self.config['github_repo'])
        since = since or (datetime.now() - timedelta(hours=24))
        return list(repo.get_commits(since=since))
    
    # =====================================
    # LEARNING & IMPROVEMENT
    # =====================================
    
    def learn_from_outcome(self, action: Dict[str, Any], outcome: Dict[str, Any]) -> None:
        """Learn from action outcomes"""
        try:
            # Store as knowledge
            cursor = self.db.cursor()
            cursor.execute("""
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
            
            self.db.commit()
            cursor.close()
            
            logger.info(f"📚 Learned from {action['type']}: {outcome.get('success', 'unknown')}")
            
        except psycopg2.Error as e:
            logger.error(f"Failed to store learning: {e}")
            self.db.rollback()
    
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
    
    # =====================================
    # UTILITY METHODS
    # =====================================
    
    def _init_database(self) -> psycopg2.extensions.connection:
        """Initialize PostgreSQL connection"""
        try:
            conn = psycopg2.connect(self.config['database_url'], connect_timeout=10)
            conn.autocommit = False
            logger.info("✅ Database connected")
            return conn
        except psycopg2.Error as e:
            error_msg = str(e)
            # Check if it's a known connectivity issue (IPv6 in GitHub Actions)
            if "Network is unreachable" in error_msg or "2406:" in error_msg:
                logger.warning(f"⚠️  Database connection failed (IPv6 connectivity issue): {e}")
                logger.warning(f"⚠️  Continuing without database - state will not persist")
                return None
            else:
                logger.error(f"Failed to connect to database: {e}")
                raise
    
    def _init_github(self) -> Github:
        """Initialize GitHub client"""
        try:
            gh = Github(self.config['github_token'])
            # Test connection
            _ = gh.get_repo(self.config['github_repo'])
            logger.info("✅ GitHub connected")
            return gh
        except Exception as e:
            logger.error(f"Failed to connect to GitHub: {e}")
            raise
    
    def _init_vector_memory(self) -> Optional[Any]:
        """Initialize vector memory (Pinecone)"""
        try:
            if 'pinecone_api_key' not in self.config:
                logger.info("⚠️  Pinecone not configured, vector memory disabled")
                return None
            
            from waooaw.memory.vector_memory import VectorMemory
            vm = VectorMemory(self.config['pinecone_api_key'])
            logger.info("✅ Vector memory connected")
            return vm
        except Exception as e:
            logger.warning(f"Vector memory unavailable: {e}")
            return None
    
    def _init_llm(self) -> anthropic.Anthropic:
        """Initialize LLM client (Claude)"""
        try:
            client = anthropic.Anthropic(api_key=self.config['anthropic_api_key'])
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
