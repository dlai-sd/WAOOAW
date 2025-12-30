#!/usr/bin/env python3
"""
Agent Roll Call Test

Tests which agents respond to a platform-wide "ping" event.
This helps verify which agents are:
1. Running
2. Connected to the Event Bus
3. Responding to events

Usage:
    python scripts/agent_roll_call.py

Expected output:
    - List of responding agents
    - Response times
    - Agent status
"""

import asyncio
import sys
import time
from datetime import datetime
from typing import List, Dict, Any

# Add waooaw to path
sys.path.insert(0, '/workspaces/WAOOAW')

try:
    from waooaw.events.event_bus import EventBus
except ImportError:
    print("⚠️  EventBus not yet implemented as standalone service")
    print("   This test requires Event Bus to be running")
    print("   Start with: docker-compose -f docker-compose.events.yml up -d")
    sys.exit(1)


class RollCallMonitor:
    """Monitor for agent roll call responses"""
    
    def __init__(self):
        self.responses: List[Dict[str, Any]] = []
        self.start_time = None
    
    async def send_roll_call(self, event_bus: EventBus, test_id: str):
        """Send roll call request event"""
        self.start_time = time.time()
        
        await event_bus.publish({
            "event_id": f"roll-call-{test_id}",
            "event_type": "platform.agent.roll_call.request",
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "test_id": test_id,
                "timeout_seconds": 5,
                "requested_by": "platform_operator"
            }
        })
        
        print(f"📢 Roll call sent (test_id: {test_id})")
        print(f"   Waiting for responses...")
    
    async def handle_response(self, event: Dict[str, Any]):
        """Handle agent response"""
        elapsed = time.time() - self.start_time
        
        payload = event.get("payload", {})
        agent_id = payload.get("agent_id", "unknown")
        status = payload.get("status", "unknown")
        
        self.responses.append({
            "agent_id": agent_id,
            "status": status,
            "response_time_ms": int(elapsed * 1000),
            "version": payload.get("version", "unknown"),
            "capabilities": payload.get("capabilities", []),
            "timestamp": payload.get("timestamp", "unknown")
        })
        
        print(f"   ✅ {agent_id:20s} | {status:10s} | {int(elapsed * 1000):4d}ms")
    
    def print_summary(self):
        """Print summary of roll call results"""
        print(f"\n{'='*60}")
        print(f"📊 Roll Call Summary")
        print(f"{'='*60}")
        print(f"Total responses:     {len(self.responses)}")
        
        if self.responses:
            online = [r for r in self.responses if r["status"] == "online"]
            offline = [r for r in self.responses if r["status"] != "online"]
            
            print(f"Online agents:       {len(online)}")
            print(f"Offline/Degraded:    {len(offline)}")
            
            if self.responses:
                avg_response = sum(r["response_time_ms"] for r in self.responses) / len(self.responses)
                max_response = max(r["response_time_ms"] for r in self.responses)
                min_response = min(r["response_time_ms"] for r in self.responses)
                
                print(f"\nResponse times:")
                print(f"   Average:  {avg_response:.0f}ms")
                print(f"   Min:      {min_response}ms")
                print(f"   Max:      {max_response}ms")
            
            print(f"\n{'='*60}")
            print(f"Agents by type:")
            print(f"{'='*60}")
            
            # Group by type (if available in response)
            by_type = {}
            for resp in self.responses:
                agent_id = resp["agent_id"]
                # Infer type from name
                if "trial" in agent_id.lower():
                    agent_type = "Revenue"
                elif "match" in agent_id.lower():
                    agent_type = "Revenue"
                elif any(x in agent_id.lower() for x in ["vision", "factory", "event", "memory"]):
                    agent_type = "Platform CoE"
                else:
                    agent_type = "Other"
                
                if agent_type not in by_type:
                    by_type[agent_type] = []
                by_type[agent_type].append(agent_id)
            
            for agent_type, agents in sorted(by_type.items()):
                print(f"\n{agent_type} ({len(agents)}):")
                for agent in sorted(agents):
                    print(f"   • {agent}")
        else:
            print("\n⚠️  No agents responded!")
            print("\nPossible reasons:")
            print("   1. No agents are running")
            print("   2. Agents don't have roll_call handlers implemented")
            print("   3. Event Bus is not routing events")
            print("   4. Redis connection issues")
            
            print("\n💡 To fix:")
            print("   1. Start Event Bus: docker-compose -f docker-compose.events.yml up -d")
            print("   2. Deploy agents with roll_call handlers")
            print("   3. Check Redis: redis-cli ping")
        
        print(f"\n{'='*60}\n")


async def run_roll_call():
    """Run the roll call test"""
    print("🎯 WAOOAW Agent Roll Call Test")
    print("="*60)
    
    # Generate test ID
    test_id = f"{int(time.time())}"
    
    # Initialize
    monitor = RollCallMonitor()
    
    try:
        # Connect to Event Bus
        print("Connecting to Event Bus (redis://localhost:6379)...")
        event_bus = EventBus(redis_url="redis://localhost:6379")
        
        # Subscribe to responses
        await event_bus.subscribe(
            pattern="platform.agent.roll_call.response",
            handler=monitor.handle_response,
            subscriber_agent="roll_call_monitor"
        )
        
        print("✅ Connected to Event Bus")
        print()
        
        # Send roll call
        await monitor.send_roll_call(event_bus, test_id)
        
        # Wait for responses (5 seconds)
        await asyncio.sleep(5)
        
        # Print summary
        monitor.print_summary()
        
        # Cleanup
        await event_bus.unsubscribe(
            pattern="platform.agent.roll_call.response",
            subscriber_agent="roll_call_monitor"
        )
        
    except ConnectionError as e:
        print(f"\n❌ Connection Error: {e}")
        print("\nMake sure Redis and Event Bus are running:")
        print("   docker-compose -f docker-compose.events.yml up -d")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print()
    try:
        asyncio.run(run_roll_call())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
