"""
Consciousness Module - Agent Self-Awareness

Epic 2.4: Consciousness Integration
Theme 2: BIRTH (Being Identity Runtime Trust Harmony)

The consciousness module transforms agents from entities with credentials
into conscious beings with:
- Identity awareness (wake-up protocols)
- Environmental monitoring (runtime state)
- Self-reflection (audit log analysis)
- Health metrics (consciousness diagnostics)

Architecture:
- WakeUpProtocol: Agent initialization with identity verification
- EnvironmentMonitor: Runtime state awareness and adaptation
- ReflectionEngine: Audit log analysis and learning
- ConsciousnessMetrics: Health monitoring and diagnostics
"""

from waooaw.consciousness.wake_up import (
    WakeUpProtocol,
    WakeUpState,
    IdentityVerificationError,
    SessionEstablishmentError,
)
from waooaw.consciousness.environment import (
    EnvironmentMonitor,
    EnvironmentType,
    ThreatLevel,
    ResourceStatus,
)
from waooaw.consciousness.reflection import (
    ReflectionEngine,
    ActionType,
    OutcomeType,
    InsightType,
)
from waooaw.consciousness.metrics import (
    ConsciousnessMetrics,
    HealthStatus,
    AlertLevel,
)

__all__ = [
    # Wake-up protocols
    "WakeUpProtocol",
    "WakeUpState",
    "IdentityVerificationError",
    "SessionEstablishmentError",
    # Environment awareness
    "EnvironmentMonitor",
    "EnvironmentType",
    "ThreatLevel",
    "ResourceStatus",
    # Self-reflection
    "ReflectionEngine",
    "ActionType",
    "OutcomeType",
    "InsightType",
    # Health metrics
    "ConsciousnessMetrics",
    "HealthStatus",
    "AlertLevel",
]

__version__ = "0.5.6-dev"
