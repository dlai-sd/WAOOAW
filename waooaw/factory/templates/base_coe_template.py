"""
Base Platform CoE Template - Foundation for all Platform CoE agents

This template provides the common structure that all 14 Platform CoE agents
inherit from. It includes:
- WAAOOWAgent inheritance with full 15-dimension support
- Common Components integration (cache, errors, observability, etc.)
- Standardized should_wake(), make_decision(), act() methods
- Specialization injection points for unique agent behavior

Story: #74 Base CoE Template (3 pts)
Epic: #68 WowAgentFactory Core (v0.4.1)
Theme: CONCEIVE

Usage:
    from waooaw.factory.templates import BasePlatformCoE
    
    class WowDomain(BasePlatformCoE):
        def _load_specialization(self):
            return AgentSpecialization(
                coe_name="WowDomain",
                domain="domain-driven-design",
                ...
            )
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from waooaw.agents.base_agent import WAAOOWAgent, Decision, AgentSpecialization

# Common Components (will be imported when available)
# from waooaw.common import (
#     CacheHierarchy, ErrorHandler, ObservabilityStack,
#     StateManager, SecurityLayer, ResourceManager
# )

logger = logging.getLogger(__name__)


class BasePlatformCoE(WAAOOWAgent):
    """
    Base template for all Platform CoE agents.
    
    Provides standard infrastructure while allowing specialization
    for each CoE's unique domain expertise.
    
    All 14 Platform CoE agents inherit from this template:
    - WowVision Prime (already implemented, will migrate to this)
    - WowAgentFactory
    - WowDomain
    - WowEvent
    - WowCommunication
    - WowMemory
    - WowCache
    - WowSearch
    - WowSecurity
    - WowScaling
    - WowIntegration
    - WowSupport
    - WowNotification
    - WowAnalytics
    
    Key Features:
    - Inherits all 15 dimensions from WAAOOWAgent
    - Integrates Common Components (cache, errors, observability, etc.)
    - Provides wake protocol for event-driven activation
    - Standardized decision framework (deterministic → cached → LLM)
    - Action execution with audit trail
    - Self-documenting through specialization
    
    Subclasses must override:
    - _load_specialization(): Define CoE identity and capabilities
    - _try_deterministic_decision(): Domain-specific decision rules
    - execute_task(): Agent-specific task execution
    
    Subclasses may override:
    - should_wake(): Custom wake triggers beyond default
    - _apply_learnings(): Use domain knowledge to improve
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        """
        Initialize Platform CoE agent.
        
        Args:
            agent_id: Unique identifier (e.g., "WowDomain", "WowEvent")
            config: Configuration dict with:
                - database_url: PostgreSQL connection string
                - github_token: GitHub API token
                - github_repo: Repository (e.g., "dlai-sd/WAOOAW")
                - anthropic_api_key: Claude API key
                - redis_url: Redis connection (optional)
                - pinecone_api_key: Pinecone API key (optional)
        """
        # Initialize base agent (handles DB, GitHub, LLM, memory)
        super().__init__(agent_id, config)
        
        # Common Components (placeholder for future integration)
        # Will be uncommented when common components are available
        # self.cache = CacheHierarchy(redis_url=config.get('redis_url'))
        # self.error_handler = ErrorHandler()
        # self.observability = ObservabilityStack(agent_id)
        # self.state_manager = StateManager(self.db)
        # self.security = SecurityLayer()
        # self.resource_manager = ResourceManager()
        
        logger.info(f"✅ {self.agent_id} initialized with BasePlatformCoE template")
    
    # =========================================================================
    # WAKE PROTOCOL - Event-driven activation
    # =========================================================================
    
    def should_wake(self, event: Dict[str, Any]) -> bool:
        """
        Determine if this CoE should wake up for an event.
        
        Default implementation wakes on:
        1. Messages to this CoE's topic: "{agent_id}.*"
        2. Cron schedule if configured
        3. Manual wake via API
        
        Override in specialization for custom wake logic.
        
        Args:
            event: Event dict with keys:
                - topic: Event topic (e.g., "domain.model.created")
                - data: Event payload
                - timestamp: Event time
                - source: Event source agent
        
        Returns:
            bool: True if agent should wake, False otherwise
        
        Examples:
            # WowDomain wakes on domain events
            event = {"topic": "domain.model.created", "data": {...}}
            should_wake(event) -> True
            
            # WowEvent wakes on all events (message bus)
            event = {"topic": "*.*.created", "data": {...}}
            should_wake(event) -> True
        """
        topic = event.get("topic", "")
        
        # Wake on messages to this CoE's namespace
        if topic.startswith(f"{self.agent_id.lower()}."):
            logger.info(f"🔔 {self.agent_id} waking: topic matches {self.agent_id}.*")
            return True
        
        # Wake on broadcast messages
        if topic == "platform.broadcast":
            logger.info(f"🔔 {self.agent_id} waking: broadcast message")
            return True
        
        # Default: don't wake
        logger.debug(f"😴 {self.agent_id} sleeping: topic {topic} not relevant")
        return False
    
    # =========================================================================
    # DECISION FRAMEWORK - Hybrid deterministic + LLM
    # =========================================================================
    
    def make_decision(self, request: Dict[str, Any]) -> Decision:
        """
        Make decision using hybrid framework (inherited from WAAOOWAgent).
        
        Decision flow:
        1. Try deterministic rules (_try_deterministic_decision)
        2. Check decision cache (Redis)
        3. Search vector memory for similar past decisions
        4. Use LLM for complex reasoning (Claude)
        
        Args:
            request: Decision request with context
        
        Returns:
            Decision: Decision result with reason, confidence, method, cost
        """
        # Use parent's hybrid decision framework
        # This handles the 4-tier decision flow automatically
        return super().make_decision(request)
    
    def _try_deterministic_decision(self, request: Dict[str, Any]) -> Optional[Decision]:
        """
        Try to make decision using deterministic rules.
        
        OVERRIDE IN SUBCLASS to implement domain-specific rules.
        
        Default implementation: No deterministic rules (always returns None)
        
        Args:
            request: Decision request
        
        Returns:
            Decision if rule matched, None if LLM needed
        
        Example Override (WowDomain):
            if request.get('entity_type') == 'aggregate':
                # Rule: Aggregates must have ID field
                if 'id' in request.get('fields', []):
                    return Decision(
                        approved=True,
                        reason="Aggregate has required ID field",
                        confidence=1.0,
                        method="deterministic_rule",
                        cost=0.0
                    )
        """
        # Default: No domain-specific rules, defer to LLM
        return None
    
    # =========================================================================
    # ACTION EXECUTION - Task processing
    # =========================================================================
    
    def act(self, decision: Decision, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute action based on decision.
        
        Default implementation logs decision and returns result.
        Override in specialization for domain-specific actions.
        
        Args:
            decision: Decision from make_decision()
            context: Execution context
        
        Returns:
            dict: Action result with status and details
        
        Example Override (WowDomain):
            if decision.approved:
                domain_model = self._create_domain_model(context)
                self._publish_event("domain.model.created", domain_model)
                return {"status": "completed", "model_id": domain_model.id}
        """
        # Log action
        logger.info(
            f"🎬 {self.agent_id} executing action: "
            f"decision={decision.approved}, "
            f"reason='{decision.reason}', "
            f"confidence={decision.confidence:.2f}"
        )
        
        # Store decision in audit trail
        self._log_action(decision, context)
        
        # Return result
        return {
            "status": "completed",
            "agent_id": self.agent_id,
            "decision": decision.approved,
            "reason": decision.reason,
            "confidence": decision.confidence,
            "method": decision.method,
            "cost": decision.cost,
            "timestamp": datetime.now().isoformat()
        }
    
    def _log_action(self, decision: Decision, context: Dict[str, Any]) -> None:
        """
        Log action to database for audit trail.
        
        Args:
            decision: Decision executed
            context: Execution context
        """
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO agent_actions 
                    (agent_id, decision_approved, decision_reason, confidence, 
                     method, cost, context, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        self.agent_id,
                        decision.approved,
                        decision.reason,
                        decision.confidence,
                        decision.method,
                        decision.cost,
                        str(context),
                        datetime.now()
                    )
                )
                self.db.commit()
                logger.debug(f"✅ Action logged for {self.agent_id}")
        except Exception as e:
            logger.error(f"❌ Failed to log action: {e}")
            # Don't fail action if logging fails
    
    # =========================================================================
    # TASK EXECUTION - Inherited from WAAOOWAgent
    # =========================================================================
    
    def execute_task(self, task: Dict[str, Any]) -> None:
        """
        Execute agent-specific task.
        
        OVERRIDE IN SUBCLASS to implement domain-specific logic.
        
        Default implementation logs task and does nothing.
        
        Args:
            task: Task dict with type and data
        
        Example Override (WowEvent):
            if task['type'] == 'publish_event':
                self._publish_to_redis(task['data'])
            elif task['type'] == 'subscribe':
                self._subscribe_agent(task['data'])
        """
        logger.info(f"📋 {self.agent_id} received task: {task.get('type', 'unknown')}")
        logger.warning(
            f"⚠️  No task execution logic defined for {self.agent_id}. "
            "Override execute_task() in subclass."
        )
    
    def _get_pending_tasks(self) -> List[Dict[str, Any]]:
        """
        Get pending tasks for this agent.
        
        OVERRIDE IN SUBCLASS for domain-specific task sources.
        
        Default implementation returns empty list.
        
        Returns:
            List of task dicts
        
        Example Override (WowAgentFactory):
            # Check for GitHub issues with label 'new-agent-request'
            repo = self.github.get_repo(self.config['github_repo'])
            issues = repo.get_issues(state='open', labels=['new-agent-request'])
            return [
                {'type': 'create_agent', 'data': {'issue': issue}}
                for issue in issues
            ]
        """
        return []
    
    # =========================================================================
    # SPECIALIZATION - Identity and capabilities
    # =========================================================================
    
    def _load_specialization(self) -> AgentSpecialization:
        """
        Load CoE specialization from configuration.
        
        MUST OVERRIDE IN SUBCLASS to define agent identity.
        
        Returns:
            AgentSpecialization with CoE details
        
        Example Override (WowDomain):
            return AgentSpecialization(
                coe_name="WowDomain",
                coe_type="specialist",
                domain="domain-driven-design",
                expertise="DDD patterns, bounded contexts, ubiquitous language",
                version="0.4.2",
                core_responsibilities=[
                    "Define domain models",
                    "Maintain ubiquitous language",
                    "Create bounded contexts"
                ],
                capabilities={
                    "modeling": ["entities", "aggregates", "value_objects"],
                    "validation": ["domain_integrity", "ddd_rules"],
                    "events": ["domain_events"]
                },
                constraints=[
                    {"rule": "cannot modify infrastructure", 
                     "reason": "Domain layer independence"}
                ],
                skill_requirements=["DDD", "Event Storming", "CQRS"]
            )
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must override _load_specialization(). "
            "This method defines the CoE's identity, capabilities, and constraints."
        )
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def get_capabilities(self) -> Dict[str, List[str]]:
        """
        Get agent capabilities from specialization.
        
        Returns:
            dict: Capabilities by category
        """
        return self.specialization.capabilities
    
    def can_do(self, capability: str) -> bool:
        """
        Check if agent has a specific capability.
        
        Args:
            capability: Capability name
        
        Returns:
            bool: True if agent has capability
        """
        return self.specialization.can_do(capability)
    
    def introduce(self) -> str:
        """
        Get agent introduction string.
        
        Returns:
            str: Agent introduction
        """
        return (
            f"I am {self.specialization.coe_name}, "
            f"specializing in {self.specialization.domain}. "
            f"My expertise: {self.specialization.expertise}"
        )


# =============================================================================
# TEMPLATE USAGE EXAMPLE
# =============================================================================

"""
Example: Creating WowDomain agent using this template

```python
from waooaw.factory.templates import BasePlatformCoE
from waooaw.agents.base_agent import AgentSpecialization, Decision

class WowDomain(BasePlatformCoE):
    '''
    WowDomain - Domain-Driven Design Specialist
    
    Manages domain models, bounded contexts, and ubiquitous language
    for the WAOOAW platform.
    '''
    
    def _load_specialization(self) -> AgentSpecialization:
        return AgentSpecialization(
            coe_name="WowDomain",
            coe_type="specialist",
            domain="domain-driven-design",
            expertise="DDD patterns, bounded contexts, domain events",
            version="0.4.2",
            core_responsibilities=[
                "Define domain models (entities, aggregates, value objects)",
                "Maintain ubiquitous language across platform",
                "Create bounded contexts for agent teams",
                "Validate domain integrity using DDD rules"
            ],
            capabilities={
                "modeling": ["entities", "aggregates", "value_objects"],
                "validation": ["domain_integrity", "ddd_compliance"],
                "events": ["domain_events", "event_storming"],
                "contexts": ["bounded_context_design"]
            },
            constraints=[
                {"rule": "cannot modify infrastructure layer", 
                 "reason": "Domain layer must be infrastructure-independent"},
                {"rule": "cannot access external APIs directly",
                 "reason": "Use anti-corruption layer (WowIntegration)"}
            ],
            skill_requirements=[
                "Domain-Driven Design",
                "Event Storming",
                "CQRS",
                "Ubiquitous Language"
            ]
        )
    
    def should_wake(self, event: dict) -> bool:
        '''Wake on domain-related events'''
        topic = event.get("topic", "")
        return (
            topic.startswith("domain.") or 
            topic.startswith("wowdomain.") or
            super().should_wake(event)
        )
    
    def _try_deterministic_decision(self, request: dict) -> Decision:
        '''Domain-specific validation rules'''
        # Rule: Aggregates must have ID
        if request.get('entity_type') == 'aggregate':
            fields = request.get('fields', [])
            if 'id' not in fields:
                return Decision(
                    approved=False,
                    reason="Aggregate must have 'id' field (DDD rule)",
                    confidence=1.0,
                    method="deterministic_rule",
                    cost=0.0
                )
        
        # No rule matched, defer to LLM
        return None
    
    def execute_task(self, task: dict):
        '''Execute domain modeling tasks'''
        if task['type'] == 'create_domain_model':
            self._create_domain_model(task['data'])
        elif task['type'] == 'validate_domain':
            self._validate_domain_integrity(task['data'])

# Usage
config = {
    "database_url": "postgresql://...",
    "github_token": "ghp_...",
    "github_repo": "dlai-sd/WAOOAW",
    "anthropic_api_key": "sk-ant-..."
}

wow_domain = WowDomain("WowDomain", config)
wow_domain.wake_up()
```
"""
