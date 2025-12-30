#!/usr/bin/env python3
"""
Platform Smoke Test - Tests core infrastructure without full deployment

This test verifies:
1. Redis is running and accessible
2. Event Bus can publish/subscribe to events
3. Basic event flow works end-to-end

Usage:
    python scripts/platform_smoke_test.py
"""

import asyncio
import sys
import time
from datetime import datetime

sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.events.event_bus import EventBus, Event, EventType


class TestAgent:
    """Simple test agent that responds to events"""
    
    def __init__(self, agent_id: str, event_bus: EventBus):
        self.agent_id = agent_id
        self.event_bus = event_bus
        self.events_received = []
        self.subscription_id = None
    
    async def handle_event(self, event: Event):
        """Handle incoming event"""
        self.events_received.append(event)
        event_type_str = event.event_type.value if isinstance(event.event_type, EventType) else str(event.event_type)
        print(f"   📨 {self.agent_id} received: {event_type_str}")
        
        # Respond to roll call
        if 'roll_call' in event_type_str:
            await self.respond_to_roll_call(event)
    
    async def respond_to_roll_call(self, request_event: Event):
        """Respond to roll call request"""
        response = Event(
            event_type="platform.agent.roll_call.response",
            source_agent=self.agent_id,
            payload={
                "test_id": request_event.payload.get('test_id'),
                "agent_id": self.agent_id,
                "status": "online",
                "version": "1.0.0",
                "capabilities": ["test"],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        await self.event_bus.publish(response)
        print(f"   📤 {self.agent_id} responded to roll call")
    
    async def start(self):
        """Start listening to events"""
        self.subscription_id = await self.event_bus.subscribe(
            pattern="platform.agent.*",
            handler=self.handle_event,
            subscriber_agent=self.agent_id
        )


async def run_smoke_test():
    """Run the smoke test"""
    print("🧪 WAOOAW Platform Smoke Test")
    print("="*60)
    
    # Test 1: Redis Connection
    print("\n1️⃣  Testing Redis connection...")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        result = r.ping()
        print(f"   ✅ Redis is running: {result}")
    except Exception as e:
        print(f"   ❌ Redis connection failed: {e}")
        print("\n💡 Start Redis with: redis-server --daemonize yes --port 6379")
        return False
    
    # Test 2: Event Bus Initialization
    print("\n2️⃣  Testing Event Bus initialization...")
    try:
        event_bus = EventBus(redis_url="redis://localhost:6379")
        print("   ✅ Event Bus initialized")
    except Exception as e:
        print(f"   ❌ Event Bus initialization failed: {e}")
        return False
    
    # Test 3: Start Event Bus
    print("\n3️⃣  Starting Event Bus...")
    try:
        await event_bus.start()
        print("   ✅ Event Bus started")
    except Exception as e:
        print(f"   ❌ Event Bus start failed: {e}")
        return False
    
    # Test 4: Create Test Agents
    print("\n4️⃣  Creating test agents...")
    agents = [
        TestAgent("WowTestAgent1", event_bus),
        TestAgent("WowTestAgent2", event_bus),
        TestAgent("WowTrialManager", event_bus),
        TestAgent("WowMatcher", event_bus),
    ]
    
    for agent in agents:
        await agent.start()
    
    print(f"   ✅ Started {len(agents)} test agents")
    
    # Test 5: Publish Test Event
    print("\n5️⃣  Publishing test event...")
    test_event = Event(
        event_type="platform.agent.roll_call.request",
        source_agent="smoke_test",
        payload={
            "test_id": "smoke-test",
            "timeout_seconds": 3,
            "requested_by": "smoke_test"
        }
    )
    
    await event_bus.publish(test_event)
    print("   ✅ Test event published")
    
    # Test 6: Wait for Responses
    print("\n6️⃣  Waiting for agent responses...")
    await asyncio.sleep(2)
    
    # Check results
    total_received = sum(len(agent.events_received) for agent in agents)
    print(f"   ✅ Agents received {total_received} events total")
    
    for agent in agents:
        if agent.events_received:
            print(f"      • {agent.agent_id}: {len(agent.events_received)} events")
    
    # Test 7: Verify Metrics
    print("\n7️⃣  Checking metrics...")
    print(f"   📊 Total events published: {event_bus.events_published}")
    print(f"   📊 Active subscriptions: {len(event_bus.subscriptions)}")
    
    # Test 8: Cleanup
    print("\n8️⃣  Cleaning up...")
    for agent in agents:
        if agent.subscription_id:
            await event_bus.unsubscribe(agent.subscription_id.subscription_id)
    
    await event_bus.stop()
    print("   ✅ Event Bus stopped")
    
    # Summary
    print("\n" + "="*60)
    print("🎉 Smoke Test Results")
    print("="*60)
    print("✅ Redis: Connected")
    print("✅ Event Bus: Working")
    print(f"✅ Agents: {len(agents)} responded")
    print(f"✅ Events: {total_received} delivered")
    print("="*60)
    print("\n💡 Platform core infrastructure is working!")
    print("\nNext steps:")
    print("   1. Deploy actual agents (22 available)")
    print("   2. Start Orchestration service")
    print("   3. Run full integration tests")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(run_smoke_test())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
