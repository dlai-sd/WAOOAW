"""
Agent Registry - Central registry for tracking all Platform CoE agents

This module provides a registry system to track, query, and manage all 14
Platform CoE agents. It maintains metadata about each agent including:
- Agent identity (DID, name, version)
- Status (draft, provisioned, active, suspended, revoked)
- Capabilities and constraints
- Dependencies on other agents
- Resource usage and costs

Story: #76 Agent Registry (3 pts)
Epic: #68 WowAgentFactory Core (v0.4.1)
Theme: CONCEIVE
"""

import json
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class AgentStatus(Enum):
    """Agent lifecycle status"""
    DRAFT = "draft"  # Conceived but not yet born
    PROVISIONED = "provisioned"  # Identity created, ready to wake
    ACTIVE = "active"  # Operational and accepting tasks
    SUSPENDED = "suspended"  # Temporarily disabled
    REVOKED = "revoked"  # Permanently decommissioned
    EXPIRED = "expired"  # Credentials expired


class AgentTier(Enum):
    """Agent tier in platform hierarchy"""
    TIER_1_GUARDIAN = 1  # WowVision Prime
    TIER_2_CREATION = 2  # Factory, Domain
    TIER_3_COMMUNICATION = 3  # Event, Communication
    TIER_4_INTELLIGENCE = 4  # Memory, Cache, Search
    TIER_5_SECURITY = 5  # Security, Support, Notification
    TIER_6_SCALE = 6  # Scaling, Integration, Analytics


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class AgentMetadata:
    """
    Metadata for a Platform CoE agent.
    
    Attributes:
        agent_id: Unique identifier (e.g., "WowDomain")
        did: Decentralized identifier (e.g., "did:waooaw:domain")
        name: Human-readable name
        tier: Agent tier (1-6)
        version: Semantic version (e.g., "0.4.2")
        status: Lifecycle status
        capabilities: Agent capabilities by category
        constraints: Constraints on agent behavior
        dependencies: Agent IDs this agent depends on
        wake_patterns: Event patterns that wake this agent
        resource_budget: Monthly cost budget
        created_at: Creation timestamp
        updated_at: Last update timestamp
        deployed_at: Deployment timestamp
        description: Agent description
    """
    agent_id: str
    did: str
    name: str
    tier: AgentTier
    version: str
    status: AgentStatus
    capabilities: Dict[str, List[str]] = field(default_factory=dict)
    constraints: List[Dict[str, str]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    wake_patterns: List[str] = field(default_factory=list)
    resource_budget: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    deployed_at: Optional[datetime] = None
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert enums to strings
        data["tier"] = self.tier.value
        data["status"] = self.status.value
        # Convert datetimes to ISO strings
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        if self.deployed_at:
            data["deployed_at"] = self.deployed_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMetadata":
        """Create from dictionary"""
        # Convert strings to enums
        data["tier"] = AgentTier(data["tier"])
        data["status"] = AgentStatus(data["status"])
        # Convert ISO strings to datetimes
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if data.get("deployed_at"):
            data["deployed_at"] = datetime.fromisoformat(data["deployed_at"])
        return cls(**data)


# =============================================================================
# AGENT REGISTRY
# =============================================================================

class AgentRegistry:
    """
    Central registry for all Platform CoE agents.
    
    Maintains a catalog of all 14 CoE agents with their metadata,
    status, and relationships. Supports querying by ID, tier, status,
    and capabilities.
    
    Singleton pattern ensures only one registry exists.
    """
    
    _instance: Optional["AgentRegistry"] = None
    _initialized: bool = False
    
    def __new__(cls):
        """Ensure singleton"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize registry"""
        if not self._initialized:
            self._agents: Dict[str, AgentMetadata] = {}
            self._load_initial_agents()
            AgentRegistry._initialized = True
            logger.info(f"✅ AgentRegistry initialized with {len(self._agents)} agents")
    
    def _load_initial_agents(self) -> None:
        """
        Load initial 14 Platform CoE agents.
        
        These are the agents defined in THEME_EXECUTION_ROADMAP.md
        """
        initial_agents = [
            # Tier 1: Guardian
            AgentMetadata(
                agent_id="WowVisionPrime",
                did="did:waooaw:wowvision-prime",
                name="WowVision Prime",
                tier=AgentTier.TIER_1_GUARDIAN,
                version="0.3.6",
                status=AgentStatus.ACTIVE,
                capabilities={
                    "validation": ["code", "architecture", "compliance"],
                    "github": ["issues", "pr_comments", "blocking"],
                    "learning": ["pattern_recognition", "decision_caching"]
                },
                constraints=[
                    {"rule": "cannot modify code", "reason": "Guardian only validates"}
                ],
                dependencies=[],
                wake_patterns=["*.code.changed", "*.pr.opened", "cron:0 */6 * * *"],
                resource_budget=25.0,
                deployed_at=datetime(2024, 12, 27),
                description="Architecture Guardian & Quality Gatekeeper"
            ),
            
            # Tier 2: Creation & Domain
            AgentMetadata(
                agent_id="WowAgentFactory",
                did="did:waooaw:factory",
                name="WowAgentFactory",
                tier=AgentTier.TIER_2_CREATION,
                version="0.4.1",
                status=AgentStatus.DRAFT,
                capabilities={
                    "generation": ["agent_code", "config_yaml", "tests"],
                    "deployment": ["did_provision", "pr_creation", "k8s_deploy"],
                    "validation": ["template_check", "wowvision_approval"]
                },
                constraints=[
                    {"rule": "requires WowVision approval", "reason": "Quality gate"}
                ],
                dependencies=["WowVisionPrime"],
                wake_patterns=["factory.create_agent", "github:issue:new-agent-request"],
                resource_budget=30.0,
                description="Autonomous Agent Generator & Bootstrapper"
            ),
            
            AgentMetadata(
                agent_id="WowDomain",
                did="did:waooaw:domain",
                name="WowDomain",
                tier=AgentTier.TIER_2_CREATION,
                version="0.4.2",
                status=AgentStatus.DRAFT,
                capabilities={
                    "modeling": ["entities", "aggregates", "value_objects"],
                    "validation": ["domain_integrity", "ddd_compliance"],
                    "events": ["domain_events", "event_storming"]
                },
                constraints=[
                    {"rule": "infrastructure independent", "reason": "DDD separation"}
                ],
                dependencies=["WowAgentFactory", "WowEvent"],
                wake_patterns=["domain.*", "wowdomain.*"],
                resource_budget=30.0,
                description="Domain-Driven Design Specialist"
            ),
            
            # Tier 3: Communication
            AgentMetadata(
                agent_id="WowEvent",
                did="did:waooaw:event",
                name="WowEvent",
                tier=AgentTier.TIER_3_COMMUNICATION,
                version="0.4.2",
                status=AgentStatus.DRAFT,
                capabilities={
                    "messaging": ["publish", "subscribe", "replay"],
                    "routing": ["pattern_based", "topic_based"],
                    "reliability": ["dlq", "retry", "idempotency"]
                },
                constraints=[],
                dependencies=["WowAgentFactory"],
                wake_patterns=["*"],  # Wakes on all events (message bus)
                resource_budget=30.0,
                description="Event Bus & Message Routing"
            ),
            
            AgentMetadata(
                agent_id="WowCommunication",
                did="did:waooaw:communication",
                name="WowCommunication",
                tier=AgentTier.TIER_3_COMMUNICATION,
                version="0.4.2",
                status=AgentStatus.DRAFT,
                capabilities={
                    "messaging": ["point_to_point", "broadcast", "request_response"],
                    "protocols": ["http", "websocket", "grpc"],
                    "audit": ["message_log", "compliance"]
                },
                constraints=[],
                dependencies=["WowAgentFactory", "WowEvent", "WowSecurity"],
                wake_patterns=["communication.*", "agent.message.*"],
                resource_budget=25.0,
                description="Inter-Agent Messaging Protocol Manager"
            ),
            
            # Tier 4: Intelligence & Memory
            AgentMetadata(
                agent_id="WowMemory",
                did="did:waooaw:memory",
                name="WowMemory",
                tier=AgentTier.TIER_4_INTELLIGENCE,
                version="0.4.2",
                status=AgentStatus.DRAFT,
                capabilities={
                    "storage": ["context", "decisions", "learnings"],
                    "retrieval": ["semantic_search", "vector_similarity"],
                    "sharing": ["cross_agent_knowledge"]
                },
                constraints=[],
                dependencies=["WowAgentFactory", "WowEvent"],
                wake_patterns=["memory.*", "*.memory.store", "*.memory.recall"],
                resource_budget=30.0,
                description="Shared Memory & Context Management"
            ),
            
            AgentMetadata(
                agent_id="WowCache",
                did="did:waooaw:cache",
                name="WowCache",
                tier=AgentTier.TIER_4_INTELLIGENCE,
                version="0.4.3",
                status=AgentStatus.DRAFT,
                capabilities={
                    "caching": ["l1", "l2", "l3"],
                    "invalidation": ["pattern_based", "ttl", "lru"],
                    "performance": ["hit_rate_monitoring"]
                },
                constraints=[],
                dependencies=["WowAgentFactory", "WowMemory"],
                wake_patterns=["cache.*"],
                resource_budget=25.0,
                description="Distributed Caching & Performance Optimization"
            ),
            
            AgentMetadata(
                agent_id="WowSearch",
                did="did:waooaw:search",
                name="WowSearch",
                tier=AgentTier.TIER_4_INTELLIGENCE,
                version="0.4.3",
                status=AgentStatus.DRAFT,
                capabilities={
                    "search": ["semantic", "keyword", "hybrid"],
                    "indexing": ["vector", "full_text"],
                    "ranking": ["relevance", "recency"]
                },
                constraints=[],
                dependencies=["WowAgentFactory", "WowMemory"],
                wake_patterns=["search.*", "*.search.query"],
                resource_budget=35.0,
                description="Semantic Search & Knowledge Retrieval"
            ),
            
            # Tier 5: Security & Integrity
            AgentMetadata(
                agent_id="WowSecurity",
                did="did:waooaw:security",
                name="WowSecurity",
                tier=AgentTier.TIER_5_SECURITY,
                version="0.4.3",
                status=AgentStatus.DRAFT,
                capabilities={
                    "auth": ["did_verification", "capability_check"],
                    "credentials": ["issue_vc", "revoke_vc"],
                    "audit": ["security_log", "anomaly_detection"]
                },
                constraints=[],
                dependencies=["WowAgentFactory"],
                wake_patterns=["security.*", "*.auth.*", "*.credential.*"],
                resource_budget=40.0,
                description="Authentication, Authorization & Audit"
            ),
            
            AgentMetadata(
                agent_id="WowSupport",
                did="did:waooaw:support",
                name="WowSupport",
                tier=AgentTier.TIER_5_SECURITY,
                version="0.4.3",
                status=AgentStatus.DRAFT,
                capabilities={
                    "error_handling": ["catch", "classify", "route"],
                    "escalation": ["l1", "l2", "l3", "human"],
                    "recovery": ["circuit_breaker", "self_heal"]
                },
                constraints=[],
                dependencies=["WowAgentFactory", "WowEvent", "WowNotification"],
                wake_patterns=["error.*", "incident.*", "support.*"],
                resource_budget=25.0,
                description="Error Management & Incident Response"
            ),
            
            AgentMetadata(
                agent_id="WowNotification",
                did="did:waooaw:notification",
                name="WowNotification",
                tier=AgentTier.TIER_5_SECURITY,
                version="0.4.3",
                status=AgentStatus.DRAFT,
                capabilities={
                    "channels": ["slack", "email", "pagerduty", "webhook"],
                    "routing": ["preference_based", "severity_based"],
                    "delivery": ["retry", "dedup", "tracking"]
                },
                constraints=[],
                dependencies=["WowAgentFactory", "WowEvent"],
                wake_patterns=["notification.*", "alert.*"],
                resource_budget=25.0,
                description="Alerting & Notification Routing"
            ),
            
            # Tier 6: Scale & Operations
            AgentMetadata(
                agent_id="WowScaling",
                did="did:waooaw:scaling",
                name="WowScaling",
                tier=AgentTier.TIER_6_SCALE,
                version="0.4.4",
                status=AgentStatus.DRAFT,
                capabilities={
                    "autoscaling": ["hpa", "vpa", "cluster_autoscaler"],
                    "load_balancing": ["round_robin", "least_connections"],
                    "quotas": ["rate_limiting", "throttling"]
                },
                constraints=[],
                dependencies=["WowAgentFactory", "WowAnalytics"],
                wake_patterns=["scaling.*", "load.*", "quota.*"],
                resource_budget=35.0,
                description="Load Balancing & Auto-Scaling"
            ),
            
            AgentMetadata(
                agent_id="WowIntegration",
                did="did:waooaw:integration",
                name="WowIntegration",
                tier=AgentTier.TIER_6_SCALE,
                version="0.4.4",
                status=AgentStatus.DRAFT,
                capabilities={
                    "api": ["http", "graphql", "grpc"],
                    "webhooks": ["register", "process", "validate"],
                    "credentials": ["store", "rotate"]
                },
                constraints=[],
                dependencies=["WowAgentFactory", "WowSecurity", "WowSupport"],
                wake_patterns=["integration.*", "webhook.*", "api.*"],
                resource_budget=30.0,
                description="External API & Service Connector"
            ),
            
            AgentMetadata(
                agent_id="WowAnalytics",
                did="did:waooaw:analytics",
                name="WowAnalytics",
                tier=AgentTier.TIER_6_SCALE,
                version="0.4.4",
                status=AgentStatus.DRAFT,
                capabilities={
                    "metrics": ["collect", "aggregate", "visualize"],
                    "kpi": ["retention", "arr", "usage"],
                    "reports": ["daily", "weekly", "monthly"]
                },
                constraints=[],
                dependencies=["WowAgentFactory"],  # Depends on all agents for metrics
                wake_patterns=["analytics.*", "metrics.*", "cron:*/5 * * * *"],
                resource_budget=40.0,
                description="Metrics, Monitoring & Business Intelligence"
            ),
        ]
        
        for agent in initial_agents:
            self._agents[agent.agent_id] = agent
    
    # =========================================================================
    # REGISTRATION
    # =========================================================================
    
    def register_agent(self, metadata: AgentMetadata) -> None:
        """
        Register a new agent or update existing.
        
        Args:
            metadata: Agent metadata
        """
        metadata.updated_at = datetime.now()
        self._agents[metadata.agent_id] = metadata
        logger.info(f"✅ Registered agent: {metadata.agent_id} (status={metadata.status.value})")
    
    def unregister_agent(self, agent_id: str) -> None:
        """
        Remove agent from registry.
        
        Args:
            agent_id: Agent identifier
        """
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.info(f"❌ Unregistered agent: {agent_id}")
        else:
            logger.warning(f"⚠️  Agent not found: {agent_id}")
    
    # =========================================================================
    # QUERIES
    # =========================================================================
    
    def get_agent(self, agent_id: str) -> Optional[AgentMetadata]:
        """
        Get agent by ID.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            AgentMetadata if found, None otherwise
        """
        return self._agents.get(agent_id)
    
    def list_agents(
        self,
        status: Optional[AgentStatus] = None,
        tier: Optional[AgentTier] = None
    ) -> List[AgentMetadata]:
        """
        List all agents with optional filters.
        
        Args:
            status: Filter by status
            tier: Filter by tier
        
        Returns:
            List of agent metadata
        """
        agents = list(self._agents.values())
        
        if status:
            agents = [a for a in agents if a.status == status]
        
        if tier:
            agents = [a for a in agents if a.tier == tier]
        
        # Sort by tier then agent_id
        agents.sort(key=lambda a: (a.tier.value, a.agent_id))
        
        return agents
    
    def get_agent_by_did(self, did: str) -> Optional[AgentMetadata]:
        """
        Get agent by DID.
        
        Args:
            did: Decentralized identifier
        
        Returns:
            AgentMetadata if found, None otherwise
        """
        for agent in self._agents.values():
            if agent.did == did:
                return agent
        return None
    
    def find_agents_with_capability(self, capability: str) -> List[AgentMetadata]:
        """
        Find agents with specific capability.
        
        Args:
            capability: Capability name
        
        Returns:
            List of agents with this capability
        """
        result = []
        for agent in self._agents.values():
            for cap_list in agent.capabilities.values():
                if capability in cap_list:
                    result.append(agent)
                    break
        return result
    
    def get_dependencies(self, agent_id: str) -> List[AgentMetadata]:
        """
        Get agents that this agent depends on.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            List of dependency agents
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return []
        
        return [
            self._agents[dep_id]
            for dep_id in agent.dependencies
            if dep_id in self._agents
        ]
    
    def get_dependents(self, agent_id: str) -> List[AgentMetadata]:
        """
        Get agents that depend on this agent.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            List of dependent agents
        """
        return [
            agent
            for agent in self._agents.values()
            if agent_id in agent.dependencies
        ]
    
    # =========================================================================
    # STATUS UPDATES
    # =========================================================================
    
    def update_status(self, agent_id: str, status: AgentStatus) -> None:
        """
        Update agent status.
        
        Args:
            agent_id: Agent identifier
            status: New status
        """
        agent = self.get_agent(agent_id)
        if agent:
            agent.status = status
            agent.updated_at = datetime.now()
            if status == AgentStatus.ACTIVE and not agent.deployed_at:
                agent.deployed_at = datetime.now()
            logger.info(f"📝 Updated agent {agent_id} status to {status.value}")
        else:
            logger.warning(f"⚠️  Agent not found: {agent_id}")
    
    def mark_deployed(self, agent_id: str) -> None:
        """Mark agent as deployed"""
        self.update_status(agent_id, AgentStatus.ACTIVE)
    
    def mark_suspended(self, agent_id: str) -> None:
        """Mark agent as suspended"""
        self.update_status(agent_id, AgentStatus.SUSPENDED)
    
    def mark_revoked(self, agent_id: str) -> None:
        """Mark agent as revoked"""
        self.update_status(agent_id, AgentStatus.REVOKED)
    
    def update_did(self, agent_id: str, did: str) -> None:
        """
        Update agent's DID.
        
        Args:
            agent_id: Agent identifier
            did: Decentralized identifier
        """
        agent = self._agents.get(agent_id)
        if agent:
            agent.did = did
            agent.updated_at = datetime.now()
            logger.info(f"📝 Updated agent {agent_id} DID to {did}")
        else:
            logger.warning(f"⚠️  Agent not found: {agent_id}")
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get registry statistics.
        
        Returns:
            dict: Statistics about agents
        """
        agents = list(self._agents.values())
        
        return {
            "total_agents": len(agents),
            "by_status": {
                status.value: len([a for a in agents if a.status == status])
                for status in AgentStatus
            },
            "by_tier": {
                f"tier_{tier.value}": len([a for a in agents if a.tier == tier])
                for tier in AgentTier
            },
            "total_budget": sum(a.resource_budget for a in agents),
            "deployed_count": len([a for a in agents if a.status == AgentStatus.ACTIVE]),
            "draft_count": len([a for a in agents if a.status == AgentStatus.DRAFT])
        }
    
    # =========================================================================
    # PERSISTENCE
    # =========================================================================
    
    def export_to_json(self, filepath: str) -> None:
        """
        Export registry to JSON file.
        
        Args:
            filepath: Path to JSON file
        """
        data = {
            agent_id: agent.to_dict()
            for agent_id, agent in self._agents.items()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"💾 Exported registry to {filepath}")
    
    def import_from_json(self, filepath: str) -> None:
        """
        Import registry from JSON file.
        
        Args:
            filepath: Path to JSON file
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        for agent_id, agent_dict in data.items():
            agent = AgentMetadata.from_dict(agent_dict)
            self._agents[agent_id] = agent
        
        logger.info(f"📥 Imported {len(data)} agents from {filepath}")


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

"""
Example: Using AgentRegistry

```python
from waooaw.factory.registry import AgentRegistry, AgentStatus, AgentTier

# Get singleton instance
registry = AgentRegistry()

# List all agents
all_agents = registry.list_agents()
print(f"Total agents: {len(all_agents)}")

# List active agents
active_agents = registry.list_agents(status=AgentStatus.ACTIVE)
print(f"Active agents: {[a.agent_id for a in active_agents]}")

# Get specific agent
wow_domain = registry.get_agent("WowDomain")
if wow_domain:
    print(f"WowDomain status: {wow_domain.status.value}")
    print(f"WowDomain capabilities: {wow_domain.capabilities}")

# Find agents with capability
memory_agents = registry.find_agents_with_capability("storage")
print(f"Agents with storage: {[a.agent_id for a in memory_agents]}")

# Get dependencies
factory = registry.get_agent("WowAgentFactory")
deps = registry.get_dependencies("WowAgentFactory")
print(f"Factory depends on: {[d.agent_id for d in deps]}")

# Update status
registry.mark_deployed("WowAgentFactory")

# Get statistics
stats = registry.get_statistics()
print(f"Platform statistics: {stats}")

# Export to JSON
registry.export_to_json("agent_registry.json")
```
"""
