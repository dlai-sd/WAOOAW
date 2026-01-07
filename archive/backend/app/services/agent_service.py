"""
Agent Service - Interface to WAOOAW Agent Registry

This service provides a clean interface to query the agent registry
without triggering full waooaw package imports.
"""

import sys
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add waooaw to path
sys.path.insert(0, '/workspaces/WAOOAW')


def get_agents_list() -> Dict[str, Any]:
    """
    Get list of all registered agents.
    
    Returns:
        Dictionary with 'total' count and 'agents' list
    """
    try:
        # Import only what we need
        from waooaw.factory.registry.agent_registry import AgentRegistry, AgentStatus
        
        registry = AgentRegistry()
        agents = registry.list_agents()
        
        agent_list = []
        for agent in agents:
            # Calculate last active time
            last_active = "never"
            if agent.deployed_at:
                diff = datetime.now() - agent.deployed_at
                if diff.days > 0:
                    last_active = f"{diff.days} days ago"
                elif diff.seconds > 3600:
                    last_active = f"{diff.seconds // 3600} hours ago"
                else:
                    last_active = f"{diff.seconds // 60} minutes ago"
            
            # Map agent status to portal status
            status_map = {
                AgentStatus.ACTIVE: "online",
                AgentStatus.DRAFT: "offline",
                AgentStatus.PROVISIONED: "offline",
                AgentStatus.SUSPENDED: "offline",
                AgentStatus.REVOKED: "offline",
                AgentStatus.EXPIRED: "offline",
            }
            
            agent_list.append({
                "id": agent.agent_id.lower().replace(" ", "-"),
                "name": agent.agent_id,
                "type": f"tier-{agent.tier.value}",
                "status": status_map.get(agent.status, "offline"),
                "last_active": last_active,
                "description": agent.description,
                "version": agent.version,
                "tier": agent.tier.value,
            })
        
        return {
            "total": len(agent_list),
            "agents": agent_list
        }
        
    except ImportError as e:
        # Fallback to mock data if import fails
        return {
            "total": 2,
            "agents": [
                {
                    "id": "wow-tester",
                    "name": "WowTester",
                    "type": "coe",
                    "status": "online",
                    "last_active": "2 minutes ago",
                    "description": "Test agent (mock data)",
                    "version": "0.0.1",
                    "tier": 0,
                },
                {
                    "id": "wow-benchmark",
                    "name": "WowBenchmark",
                    "type": "coe",
                    "status": "online",
                    "last_active": "5 minutes ago",
                    "description": "Benchmark agent (mock data)",
                    "version": "0.0.1",
                    "tier": 0,
                }
            ],
            "error": str(e)
        }
    except Exception as e:
        # Generic error handling
        return {
            "total": 0,
            "agents": [],
            "error": f"Failed to load agents: {str(e)}"
        }


def get_agent_statistics() -> Dict[str, Any]:
    """
    Get agent statistics from registry.
    
    Returns:
        Dictionary with agent counts by status and tier
    """
    try:
        from waooaw.factory.registry.agent_registry import AgentRegistry
        
        registry = AgentRegistry()
        stats = registry.get_statistics()
        
        return stats
        
    except Exception as e:
        return {
            "total_agents": 0,
            "by_status": {},
            "by_tier": {},
            "error": str(e)
        }
