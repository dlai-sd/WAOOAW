"""
Factory Interfaces - Type definitions and protocols for agent generation
"""

from waooaw.factory.interfaces.coe_interface import (
    CoEInterface,
    WakeEvent,
    DecisionRequest,
    ActionContext,
    TaskDefinition
)

__all__ = [
    "CoEInterface",
    "WakeEvent",
    "DecisionRequest",
    "ActionContext",
    "TaskDefinition"
]
