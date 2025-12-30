#!/usr/bin/env python3
"""
Debug Event Delivery Test - Detailed diagnostics for pub/sub

This test helps diagnose why events aren't being delivered by:
1. Enabling debug logging
2. Checking Redis pub/sub directly
3. Monitoring listener task execution
"""

import asyncio
import sys
import logging

sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.events.event_bus import EventBus, Event

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def debug_delivery():
    """Debug event delivery issue"""
    print("🔍 Debugging Event Delivery")
    print("="*60)
    
    received = []
    
    async def handler(event: Event):
        print(f"   ✅ HANDLER CALLED! Event: {event.event_type}")
        received.append(event)
    
    # Initialize
    bus = EventBus(redis_url="redis://localhost:6379")
    await bus.start()
    
    print("\n1️⃣  Event Bus Status:")
    print(f"   Running: {bus.running}")
    print(f"   Listener task: {bus.listener_task}")
    print(f"   Listener done: {bus.listener_task.done() if bus.listener_task else 'N/A'}")
    
    # Subscribe
    print("\n2️⃣  Subscribing...")
    sub = await bus.subscribe(
        pattern="debug.test.*",
        handler=handler,
        subscriber_agent="debug_agent"
    )
    
    print(f"   Subscription ID: {sub.subscription_id}")
    print(f"   Pattern: {sub.pattern}")
    print(f"   Active subscriptions: {len(bus.subscriptions)}")
    print(f"   Pattern mappings: {dict(bus.pattern_to_subscriptions)}")
    
    # Wait for subscription to register
    print("\n3️⃣  Waiting for subscription to register...")
    await asyncio.sleep(1)
    
    # Check Redis directly
    print("\n4️⃣  Checking Redis pub/sub state...")
    import redis.asyncio as redis
    redis_client = redis.from_url("redis://localhost:6379")
    
    # Check patterns
    pubsub_channels = await redis_client.pubsub_numpat()
    print(f"   Active patterns in Redis: {pubsub_channels}")
    
    # Publish test event
    print("\n5️⃣  Publishing test event...")
    test_event = Event(
        event_type="debug.test.message",
        source_agent="debug_publisher",
        payload={"data": "test"}
    )
    
    await bus.publish(test_event)
    print(f"   ✅ Event published: {test_event.event_id}")
    print(f"   Event type: {test_event.event_type}")
    print(f"   Events published counter: {bus.events_published}")
    
    # Wait and check
    print("\n6️⃣  Waiting for delivery (5 seconds)...")
    for i in range(5):
        await asyncio.sleep(1)
        print(f"   ... {i+1}s - Received: {len(received)} events")
        if received:
            break
    
    # Results
    print("\n7️⃣  Results:")
    print(f"   Events received by handler: {len(received)}")
    print(f"   Events delivered counter: {bus.events_delivered}")
    
    if received:
        print(f"   ✅ SUCCESS! Event was delivered")
        for evt in received:
            print(f"      Event ID: {evt.event_id}")
            print(f"      Event Type: {evt.event_type}")
    else:
        print(f"   ❌ FAILED! Event was NOT delivered")
        
        print("\n🔍 Debugging Info:")
        print(f"   Listener task running: {not bus.listener_task.done()}")
        print(f"   Active subscriptions: {len(bus.subscriptions)}")
        print(f"   Pattern subscriptions: {bus.pattern_to_subscriptions}")
        
        # Try to see what the listener is doing
        if not bus.listener_task.done():
            print(f"   Listener task is alive but not processing messages")
        else:
            try:
                exc = bus.listener_task.exception()
                print(f"   Listener task exception: {exc}")
            except:
                print(f"   Listener task completed normally")
    
    # Cleanup
    await bus.unsubscribe(sub.subscription_id)
    await bus.stop()
    await redis_client.close()
    
    print("\n" + "="*60)
    return len(received) > 0


if __name__ == "__main__":
    success = asyncio.run(debug_delivery())
    sys.exit(0 if success else 1)
