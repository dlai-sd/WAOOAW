"""
WowEvent Service Entry Point

Production service for running the event bus with health checks,
metrics endpoint, and graceful shutdown.
"""

import asyncio
import os
import signal
import sys
from typing import Optional

import redis.asyncio as redis
from aiohttp import web

from waooaw.events import EventBus, EventMetrics, EventStore


class EventBusService:
    """Production event bus service with HTTP endpoints."""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.port = int(os.getenv("PORT", "8080"))
        self.redis_client: Optional[redis.Redis] = None
        self.event_bus: Optional[EventBus] = None
        self.metrics: Optional[EventMetrics] = None
        self.event_store: Optional[EventStore] = None
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.shutdown_event = asyncio.Event()
    
    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        try:
            if self.redis_client:
                await self.redis_client.ping()
            
            status = {
                "status": "healthy",
                "redis": "connected" if self.redis_client else "disconnected",
                "event_bus": "running" if self.event_bus and self.event_bus.running else "stopped"
            }
            return web.json_response(status, status=200)
        except Exception as e:
            return web.json_response({
                "status": "unhealthy",
                "error": str(e)
            }, status=503)
    
    async def metrics_endpoint(self, request: web.Request) -> web.Response:
        """Metrics endpoint."""
        if not self.metrics:
            return web.json_response({"error": "Metrics not available"}, status=503)
        
        try:
            metrics_data = await self.metrics.get_metrics()
            return web.json_response(metrics_data)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
    
    async def readiness_check(self, request: web.Request) -> web.Response:
        """Readiness check endpoint."""
        if self.event_bus and self.event_bus.running:
            return web.json_response({"status": "ready"})
        return web.json_response({"status": "not ready"}, status=503)
    
    async def startup(self):
        """Start the event bus service."""
        print(f"🚀 Starting WowEvent Event Bus Service...")
        print(f"📍 Redis URL: {self.redis_url}")
        print(f"🔌 Port: {self.port}")
        
        # Initialize Redis client
        self.redis_client = await redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        print("✅ Redis connected")
        
        # Initialize components
        self.event_bus = EventBus(self.redis_client)
        self.metrics = EventMetrics(window_seconds=60)
        self.event_store = EventStore(max_size=10000)
        
        # Start event bus
        await self.event_bus.start()
        print("✅ Event Bus started")
        
        # Setup HTTP server
        self.app = web.Application()
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/ready', self.readiness_check)
        self.app.router.add_get('/metrics', self.metrics_endpoint)
        
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, '0.0.0.0', self.port)
        await site.start()
        print(f"✅ HTTP server listening on port {self.port}")
        print("🎉 WowEvent Service is ready!")
    
    async def shutdown(self):
        """Graceful shutdown."""
        print("\n🛑 Shutting down WowEvent Service...")
        
        # Stop HTTP server
        if self.runner:
            await self.runner.cleanup()
            print("✅ HTTP server stopped")
        
        # Stop event bus
        if self.event_bus:
            await self.event_bus.stop()
            print("✅ Event Bus stopped")
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
            print("✅ Redis connection closed")
        
        print("👋 Shutdown complete")
    
    def handle_signal(self, sig):
        """Handle shutdown signals."""
        print(f"\n⚠️  Received signal {sig.name}")
        self.shutdown_event.set()
    
    async def run(self):
        """Run the service."""
        # Setup signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda s=sig: self.handle_signal(s)
            )
        
        try:
            await self.startup()
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
        except Exception as e:
            print(f"❌ Service error: {e}", file=sys.stderr)
            raise
        finally:
            await self.shutdown()


async def main():
    """Main entry point."""
    service = EventBusService()
    await service.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
