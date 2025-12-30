"""
Agent Specification Schema

Defines YAML configuration schema for Platform CoE agents.
Includes validation rules and type definitions.

Story: #78 Config System (3 pts)
Epic: #68 WowAgentFactory Core (v0.4.1)
Theme: CONCEIVE
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import jsonschema


# =============================================================================
# ENUMS
# =============================================================================

class AgentDomain(Enum):
    """Agent domain categories"""
    GUARDIAN = "guardian"
    CREATION = "creation"
    DOMAIN = "domain"
    COMMUNICATION = "communication"
    INTELLIGENCE = "intelligence"
    SECURITY = "security"
    SCALE = "scale"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class AgentSpecConfig:
    """
    Agent specification from YAML config.
    
    Attributes:
        coe_name: Agent name (e.g., "WowDomain")
        display_name: Human-readable name
        tier: Agent tier (1-6)
        domain: Agent domain
        version: Semantic version
        description: Agent description
        capabilities: Agent capabilities by category
        constraints: Behavioral constraints
        dependencies: Required agents
        wake_patterns: Event patterns to wake on
        resource_budget: Monthly cost budget
        specialization: Domain-specific config
    """
    coe_name: str
    display_name: str
    tier: int
    domain: AgentDomain
    version: str
    description: str
    capabilities: Dict[str, List[str]] = field(default_factory=dict)
    constraints: List[Dict[str, str]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    wake_patterns: List[str] = field(default_factory=list)
    resource_budget: float = 0.0
    specialization: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentSpecConfig":
        """Create from dictionary"""
        # Convert domain string to enum
        if isinstance(data.get("domain"), str):
            data["domain"] = AgentDomain(data["domain"])
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "coe_name": self.coe_name,
            "display_name": self.display_name,
            "tier": self.tier,
            "domain": self.domain.value,
            "version": self.version,
            "description": self.description,
            "capabilities": self.capabilities,
            "constraints": self.constraints,
            "dependencies": self.dependencies,
            "wake_patterns": self.wake_patterns,
            "resource_budget": self.resource_budget,
            "specialization": self.specialization
        }
        return result


# =============================================================================
# VALIDATION
# =============================================================================

# JSON Schema for agent specification
AGENT_SPEC_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["coe_name", "display_name", "tier", "domain", "version", "description"],
    "properties": {
        "coe_name": {
            "type": "string",
            "pattern": "^Wow[A-Z][a-zA-Z]+$",
            "description": "Agent name starting with 'Wow'"
        },
        "display_name": {
            "type": "string",
            "minLength": 3,
            "description": "Human-readable name"
        },
        "tier": {
            "type": "integer",
            "minimum": 1,
            "maximum": 6,
            "description": "Agent tier (1-6)"
        },
        "domain": {
            "type": "string",
            "enum": ["guardian", "creation", "domain", "communication", "intelligence", "security", "scale"],
            "description": "Agent domain"
        },
        "version": {
            "type": "string",
            "pattern": "^\\d+\\.\\d+\\.\\d+$",
            "description": "Semantic version (e.g., 0.4.2)"
        },
        "description": {
            "type": "string",
            "minLength": 10,
            "description": "Agent description"
        },
        "capabilities": {
            "type": "object",
            "patternProperties": {
                ".*": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "description": "Agent capabilities grouped by category"
        },
        "constraints": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["rule", "reason"],
                "properties": {
                    "rule": {"type": "string"},
                    "reason": {"type": "string"}
                }
            },
            "description": "Behavioral constraints"
        },
        "dependencies": {
            "type": "array",
            "items": {
                "type": "string",
                "pattern": "^Wow[A-Z][a-zA-Z]+$"
            },
            "description": "Required agent dependencies"
        },
        "wake_patterns": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Event patterns that wake this agent"
        },
        "resource_budget": {
            "type": "number",
            "minimum": 0,
            "description": "Monthly cost budget in dollars"
        },
        "specialization": {
            "type": "object",
            "description": "Domain-specific configuration"
        }
    }
}


def validate_agent_spec(spec: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate agent specification against schema.
    
    Args:
        spec: Agent specification dictionary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        jsonschema.validate(instance=spec, schema=AGENT_SPEC_SCHEMA)
        return True, None
    except jsonschema.ValidationError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Validation error: {str(e)}"


# =============================================================================
# EXAMPLE CONFIGS
# =============================================================================

EXAMPLE_WOWDOMAIN_CONFIG = {
    "coe_name": "WowDomain",
    "display_name": "WowDomain",
    "tier": 2,
    "domain": "domain",
    "version": "0.4.2",
    "description": "Domain-Driven Design Specialist",
    "capabilities": {
        "modeling": ["entities", "aggregates", "value_objects"],
        "validation": ["domain_integrity", "ddd_compliance"],
        "events": ["domain_events", "event_storming"]
    },
    "constraints": [
        {
            "rule": "infrastructure-independent",
            "reason": "DDD separation of concerns"
        }
    ],
    "dependencies": ["WowAgentFactory", "WowEvent"],
    "wake_patterns": ["domain.*", "wowdomain.*"],
    "resource_budget": 30.0,
    "specialization": {
        "bounded_contexts": ["agent", "marketplace", "billing"],
        "aggregates": {
            "agent": ["AgentEntity", "AgentCapability", "AgentState"],
            "marketplace": ["Trial", "Subscription", "Usage"],
            "billing": ["Invoice", "Payment", "Receipt"]
        }
    }
}


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

"""
Example: Using AgentSpecConfig

```python
from waooaw.factory.config.schema import AgentSpecConfig, validate_agent_spec, EXAMPLE_WOWDOMAIN_CONFIG
import yaml

# Example 1: Validate spec
is_valid, error = validate_agent_spec(EXAMPLE_WOWDOMAIN_CONFIG)
if is_valid:
    print("✅ Spec is valid")
else:
    print(f"❌ Validation failed: {error}")

# Example 2: Load from dictionary
spec = AgentSpecConfig.from_dict(EXAMPLE_WOWDOMAIN_CONFIG)
print(f"Agent: {spec.coe_name}")
print(f"Tier: {spec.tier}")
print(f"Capabilities: {spec.capabilities}")

# Example 3: Convert to dictionary
spec_dict = spec.to_dict()
print(yaml.dump(spec_dict, default_flow_style=False))
```
"""
