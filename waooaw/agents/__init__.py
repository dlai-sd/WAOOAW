"""
WAOOAW Agents Module

Contains all agent implementations inheriting from WAAOOWAgent base class.
"""

from waooaw.agents.base_agent import WAAOOWAgent, Decision
from waooaw.agents.wowvision_prime import WowVisionPrime

__all__ = ["WAAOOWAgent", "Decision", "WowVisionPrime"]
