"""
WowAgentFactory Module - Agent Creation & Bootstrapping

This module provides the factory system for generating Platform CoE agents
from templates and configuration files.

Epic: #68 WowAgentFactory Core (v0.4.1)
Theme: CONCEIVE - Create DNA for all 14 agents
"""

__version__ = "0.4.1"
__author__ = "WAOOAW Platform"

from waooaw.factory.templates.base_coe_template import BasePlatformCoE

__all__ = ["BasePlatformCoE"]
