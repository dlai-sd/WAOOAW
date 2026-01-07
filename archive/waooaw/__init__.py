"""
WAOOAW Platform - AI Agent System

Base agent architecture for all 14 Centers of Excellence (CoEs).
"""

__version__ = "1.0.0"
__author__ = "WAOOAW Platform Team"

from waooaw.agents.base_agent import WAAOOWAgent
from waooaw.agents.wowvision_prime import WowVisionPrime

__all__ = ["WAAOOWAgent", "WowVisionPrime"]
