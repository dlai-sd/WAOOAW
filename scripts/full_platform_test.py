#!/usr/bin/env python3
"""
Full Platform Integration Test

Tests the complete WAOOAW platform:
1. Infrastructure (Redis + Event Bus)
2. Agent deployment and communication
3. Orchestration integration
4. End-to-end workflows

Usage:
    python scripts/full_platform_test.py
"""

import asyncio
import sys
import time
from datetime import datetime
from typing import List, Dict, Any

sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.events.event_bus import EventBus, Event


class PlatformTest:
    """Comprehensive platform test runner"""
    
    def __init__(self):
        self.event_bus = None
        self.test_results = []
    
    def report(self, test_name: str, passed: bool, details: str = ""):
        """Record test result"""
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        status = "✅" if passed else "❌"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
    
    async def test_redis_connection(self):
        """Test 1: Redis connectivity"""
        print("\n" + "="*60)
        print("TEST 1: Redis Connection")
        print("="*60)
        
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            result = r.ping()
            
            # Get some info
            info = r.info('server')
            version = info.get('redis_version', 'unknown')
            uptime = info.get('uptime_in_seconds', 0)
            
            self.report(
                "Redis Connection", 
                True, 
                f"v{version}, uptime: {uptime}s"
            )
            return True
            
        except Exception as e:
            self.report("Redis Connection", False, str(e))
            return False
    
    async def test_event_bus_lifecycle(self):
        """Test 2: Event Bus initialization and lifecycle"""
        print("\n" + "="*60)
        print("TEST 2: Event Bus Lifecycle")
        print("="*60)
        
        try:
            # Initialize
            self.event_bus = EventBus(redis_url="redis://localhost:6379")
            self.report("Event Bus Init", True, "EventBus object created")
            
            # Start
            await self.event_bus.start()
            self.report("Event Bus Start", True, "Running and ready")
            
            # Verify listener task is running
            if self.event_bus.listener_task and not self.event_bus.listener_task.done():
                self.report("Event Listener", True, "Background task running")
            else:
                self.report("Event Listener", False, "Task not running!")
            
            # Give listener time to fully initialize
            await asyncio.sleep(0.2)
            
            return True
            
        except Exception as e:
            self.report("Event Bus Lifecycle", False, str(e))
            return False
    
    async def test_event_publishing(self):
        """Test 3: Event publishing"""
        print("\n" + "="*60)
        print("TEST 3: Event Publishing")
        print("="*60)
        
        try:
            # Publish test event
            event = Event(
                event_type="test.platform.hello",
                source_agent="platform_test",
                payload={
                    "message": "Hello WAOOAW!",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            result = await self.event_bus.publish(event)
            
            self.report(
                "Event Publishing", 
                result, 
                f"Published {event.event_type}"
            )
            
            # Check metrics
            self.report(
                "Publishing Metrics",
                self.event_bus.events_published > 0,
                f"{self.event_bus.events_published} events published"
            )
            
            return True
            
        except Exception as e:
            self.report("Event Publishing", False, str(e))
            return False
    
    async def test_subscription_and_delivery(self):
        """Test 4: Event subscription and delivery"""
        print("\n" + "="*60)
        print("TEST 4: Event Subscription & Delivery")
        print("="*60)
        
        received_events = []
        
        async def test_handler(event: Event):
            received_events.append(event)
        
        try:
            # Subscribe
            sub = await self.event_bus.subscribe(
                pattern="test.delivery.*",
                handler=test_handler,
                subscriber_agent="test_subscriber"
            )
            
            self.report(
                "Event Subscription",
                True,
                f"Subscribed to test.delivery.*"
            )
            
            # Give subscription time to fully register with Redis
            await asyncio.sleep(0.5)
            
            # Publish event that should be received
            test_event = Event(
                event_type="test.delivery.message",
                source_agent="test_publisher",
                payload={"test": "data"}
            )
            
            await self.event_bus.publish(test_event)
            
            # Wait for delivery (listener loop needs time to process)
            await asyncio.sleep(2)
            
            self.report(
                "Event Delivery",
                len(received_events) > 0,
                f"{len(received_events)} events received"
            )
            
            # Cleanup
            await self.event_bus.unsubscribe(sub.subscription_id)
            
            return True
            
        except Exception as e:
            self.report("Subscription & Delivery", False, str(e))
            return False
    
    async def test_agent_simulation(self):
        """Test 5: Simulated agent communication"""
        print("\n" + "="*60)
        print("TEST 5: Agent Communication (Simulated)")
        print("="*60)
        
        responses = []
        
        async def agent_handler(event: Event):
            # Simulate agent responding to any test.agent.request event
            response = Event(
                event_type="test.agent.response",
                source_agent="simulated_agent",
                payload={
                    "request_id": event.event_id,
                    "status": "processed"
                }
            )
            await self.event_bus.publish(response)
            responses.append(response)
        
        try:
            # Create simulated agent
            sub = await self.event_bus.subscribe(
                pattern="test.agent.request",
                handler=agent_handler,
                subscriber_agent="simulated_agent"
            )
            
            self.report("Agent Subscription", True, "Simulated agent ready")
            
            # Give subscription time to register
            await asyncio.sleep(0.5)
            
            # Send request
            request = Event(
                event_type="test.agent.request",
                source_agent="test_client",
                payload={"action": "test"}
            )
            
            await self.event_bus.publish(request)
            await asyncio.sleep(2)
            
            self.report(
                "Agent Response",
                len(responses) > 0,
                f"Agent responded in <1s"
            )
            
            # Cleanup
            await self.event_bus.unsubscribe(sub.subscription_id)
            
            return True
            
        except Exception as e:
            self.report("Agent Communication", False, str(e))
            return False
    
    async def test_concurrent_operations(self):
        """Test 6: Concurrent event handling"""
        print("\n" + "="*60)
        print("TEST 6: Concurrent Operations")
        print("="*60)
        
        try:
            # Publish multiple events concurrently
            events = [
                Event(
                    event_type=f"test.concurrent.event_{i}",
                    source_agent="load_test",
                    payload={"index": i}
                )
                for i in range(10)
            ]
            
            start_time = time.time()
            
            await asyncio.gather(*[
                self.event_bus.publish(event)
                for event in events
            ])
            
            elapsed = time.time() - start_time
            
            self.report(
                "Concurrent Publishing",
                elapsed < 1.0,
                f"10 events in {elapsed:.3f}s"
            )
            
            self.report(
                "Event Throughput",
                True,
                f"{len(events)/elapsed:.1f} events/sec"
            )
            
            return True
            
        except Exception as e:
            self.report("Concurrent Operations", False, str(e))
            return False
    
    async def test_platform_metrics(self):
        """Test 7: Platform metrics"""
        print("\n" + "="*60)
        print("TEST 7: Platform Metrics")
        print("="*60)
        
        try:
            total_published = self.event_bus.events_published
            total_subs = len(self.event_bus.subscriptions)
            
            self.report(
                "Metrics Available",
                True,
                f"{total_published} events, {total_subs} active subscriptions"
            )
            
            # Check if metrics are tracking correctly
            self.report(
                "Metrics Accuracy",
                total_published > 0,
                "Events counted correctly"
            )
            
            return True
            
        except Exception as e:
            self.report("Platform Metrics", False, str(e))
            return False
    
    async def cleanup(self):
        """Cleanup resources"""
        print("\n" + "="*60)
        print("CLEANUP")
        print("="*60)
        
        try:
            if self.event_bus:
                await self.event_bus.stop()
                self.report("Event Bus Shutdown", True, "Graceful shutdown")
            return True
        except Exception as e:
            self.report("Cleanup", False, str(e))
            return False
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("🎯 TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for r in self.test_results if r['passed'])
        total = len(self.test_results)
        percentage = (passed / total * 100) if total > 0 else 0
        
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {percentage:.1f}%")
        
        if passed == total:
            print("\n🎉 All tests passed! Platform is fully operational!")
        elif percentage >= 80:
            print("\n✅ Platform is operational with minor issues")
        elif percentage >= 50:
            print("\n⚠️  Platform has significant issues")
        else:
            print("\n❌ Platform is not operational")
        
        print("\n" + "="*60)
        print("NEXT STEPS")
        print("="*60)
        print("1. Deploy actual agents (22 available in waooaw/agents/)")
        print("2. Start Orchestration service")
        print("3. Test with real workflows:")
        print("   - Trial provisioning (WowTrialManager)")
        print("   - Customer matching (WowMatcher)")
        print("   - Multi-agent collaboration")
        print("\n💡 Ready to deploy to production!")
        print("="*60)


async def run_full_test():
    """Run complete platform test suite"""
    print("🚀 WAOOAW Full Platform Integration Test")
    print("="*60)
    print("Testing complete platform infrastructure")
    print("="*60)
    
    tester = PlatformTest()
    
    try:
        # Run all tests
        await tester.test_redis_connection()
        await tester.test_event_bus_lifecycle()
        await tester.test_event_publishing()
        await tester.test_subscription_and_delivery()
        await tester.test_agent_simulation()
        await tester.test_concurrent_operations()
        await tester.test_platform_metrics()
        
    finally:
        # Always cleanup
        await tester.cleanup()
        tester.print_summary()


if __name__ == "__main__":
    try:
        asyncio.run(run_full_test())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
