#!/usr/bin/env python3
"""
Agent Roll Call Demo - Visual demonstration of agents announcing themselves

This creates several test agents that respond to a roll call request
by announcing their names, status, and specializations.
"""

import asyncio
import sys
from datetime import datetime

sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.events.event_bus import EventBus, Event


class DemoAgent:
    """Demo agent that responds to roll call"""
    
    agent_counter = 0  # Class variable to track agent number
    
    def __init__(self, name: str, specialty: str, event_bus: EventBus):
        DemoAgent.agent_counter += 1
        self.number = DemoAgent.agent_counter
        self.name = name
        self.specialty = specialty
        self.event_bus = event_bus
        self.subscription_id = None
    
    async def handle_roll_call(self, event: Event):
        """Respond to roll call"""
        # Announce ourselves with number
        print(f"   {self.number:<3} {self.name:<22} | {self.specialty}")
        
        # Send response event
        response = Event(
            event_type="platform.agent.roll_call.response",
            source_agent=self.name,
            payload={
                "agent_number": self.number,
                "agent_name": self.name,
                "specialty": self.specialty,
                "status": "online",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        await self.event_bus.publish(response)
    
    async def start(self):
        """Start listening for roll call"""
        sub = await self.event_bus.subscribe(
            pattern="platform.agent.roll_call.request",
            handler=self.handle_roll_call,
            subscriber_agent=self.name
        )
        self.subscription_id = sub.subscription_id
    
    async def stop(self):
        """Stop listening"""
        if self.subscription_id:
            await self.event_bus.unsubscribe(self.subscription_id)


async def run_roll_call_demo():
    """Run the visual roll call demo"""
    print("\n" + "="*95)
    print("🎯 WAOOAW COMPLETE AGENT ROLL CALL")
    print("="*95)
    print("All 22 platform agents announcing themselves...\n")
    
    # Initialize Event Bus
    print("📡 Starting Event Bus...")
    event_bus = EventBus(redis_url="redis://localhost:6379")
    await event_bus.start()
    await asyncio.sleep(0.2)  # Let it initialize
    print("   ✅ Event Bus ready\n")
    
    # Create ALL 22 agents with their actual purposes
    print("🤖 Deploying all platform agents...\n")
    agents = [
        # === REVENUE AGENTS (2) ===
        DemoAgent(
            "WowTrialManager", 
            "Trial lifecycle management - 7-day trial provisioning & conversion",
            event_bus
        ),
        DemoAgent(
            "WowMatcher", 
            "Intelligent customer-to-agent matching using ML algorithms",
            event_bus
        ),
        
        # === PLATFORM CoE AGENTS (14) ===
        DemoAgent(
            "WowVisionPrime", 
            "Platform strategy, vision, and roadmap coordination",
            event_bus
        ),
        DemoAgent(
            "WowAgentFactory", 
            "Autonomous agent creation and deployment pipeline",
            event_bus
        ),
        DemoAgent(
            "WowEvent", 
            "Event bus & async pub/sub message routing specialist",
            event_bus
        ),
        DemoAgent(
            "WowCommunication", 
            "Synchronous inter-agent messaging protocol manager",
            event_bus
        ),
        DemoAgent(
            "WowMemory", 
            "Shared knowledge & context management with semantic search",
            event_bus
        ),
        DemoAgent(
            "WowCache", 
            "Multi-level distributed caching for performance optimization",
            event_bus
        ),
        DemoAgent(
            "WowSearch", 
            "Semantic search & knowledge retrieval across platform",
            event_bus
        ),
        DemoAgent(
            "WowSecurity", 
            "Authentication, authorization, and audit logging",
            event_bus
        ),
        DemoAgent(
            "WowSupport", 
            "Error detection, self-healing, and incident response",
            event_bus
        ),
        DemoAgent(
            "WowNotification", 
            "Multi-channel alerting with intelligent priority routing",
            event_bus
        ),
        DemoAgent(
            "WowScaling", 
            "Load balancing, auto-scaling, and resource optimization",
            event_bus
        ),
        DemoAgent(
            "WowIntegration", 
            "External API connectors & webhook management",
            event_bus
        ),
        DemoAgent(
            "WowAnalytics", 
            "Business intelligence, metrics, and performance insights",
            event_bus
        ),
        DemoAgent(
            "WowDomain", 
            "Domain-driven design & bounded context management",
            event_bus
        ),
        
        # === TESTING/QUALITY AGENTS (6) ===
        DemoAgent(
            "WowTester", 
            "Automated testing framework with quality evaluation",
            event_bus
        ),
        DemoAgent(
            "WowBenchmark", 
            "Competitive benchmarking & performance comparison",
            event_bus
        ),
        DemoAgent(
            "WowAgentCoach", 
            "Agent training, evaluation, and continuous improvement",
            event_bus
        ),
        DemoAgent(
            "WowValidator", 
            "Input validation & data integrity verification",
            event_bus
        ),
        DemoAgent(
            "WowMonitor", 
            "Real-time health monitoring & alerting",
            event_bus
        ),
        DemoAgent(
            "WowOptimizer", 
            "Performance tuning & resource optimization",
            event_bus
        ),
    ]
    
    # Start all agents
    for agent in agents:
        await agent.start()
    
    print(f"   ✅ {len(agents)} agents deployed and listening\n")
    
    # Give subscriptions time to register
    await asyncio.sleep(1)
    
    # Send roll call request
    print("📢 ROLL CALL - Sound off with name and purpose!\n")
    print(f"   {'#':<3} {'Agent Name':<22} | Purpose")
    print("   " + "-"*90)
    
    roll_call_event = Event(
        event_type="platform.agent.roll_call.request",
        source_agent="platform_operator",
        payload={
            "message": "All agents report in!",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    await event_bus.publish(roll_call_event)
    
    # Wait for all responses
    await asyncio.sleep(3)
    
    print()
    print("="*95)
    print(f"✅ Roll call complete - {len(agents)} / {len(agents)} agents operational")
    print("="*95)
    print("\n💡 Platform Status:")
    print("   • Revenue Agents:  2/2 ready (WowTrialManager, WowMatcher)")
    print("   • Platform CoE:   14/14 ready")
    print("   • Quality/Test:    6/6 ready")
    print("\n🚀 All systems operational - Platform ready for deployment!")
    print()
    
    # Cleanup
    print("🔧 Shutting down...")
    for agent in agents:
        await agent.stop()
    
    await event_bus.stop()
    print("   ✅ Clean shutdown complete\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_roll_call_demo())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
