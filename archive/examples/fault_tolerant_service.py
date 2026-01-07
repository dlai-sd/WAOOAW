#!/usr/bin/env python3
"""
Fault-Tolerant Service Example

Demonstrates a highly available service using the WAOOAW orchestration
and discovery systems with comprehensive fault tolerance.

Features:
- Multiple service replicas with automatic failover
- Health monitoring with degraded state detection
- Circuit breakers for cascading failure prevention
- Automatic retry with exponential backoff
- Graceful degradation under load

Use Case: API gateway, microservices, distributed systems
"""

import asyncio
import random
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass

from waooaw.discovery import (
    ServiceRegistry,
    HealthMonitor,
    LoadBalancer,
    LoadBalancingStrategy,
    CircuitBreaker,
    AgentCapability,
    HealthStatus,
)
from waooaw.orchestration import (
    RetryPolicy,
    RetryConfig,
    RetryStrategy,
)


@dataclass
class ServiceRequest:
    """Service request"""
    request_id: str
    operation: str
    payload: Dict[str, Any]
    priority: str = "normal"


@dataclass
class ServiceResponse:
    """Service response"""
    request_id: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    agent_id: Optional[str] = None
    latency_ms: float = 0.0


class FaultTolerantService:
    """Highly available service with fault tolerance"""
    
    def __init__(self):
        self.registry = ServiceRegistry()
        self.monitor = HealthMonitor(
            self.registry,
            failure_threshold=3,
            check_interval=5.0,
            degraded_threshold_ms=500.0,  # 500ms = degraded
        )
        self.load_balancer = LoadBalancer(
            self.registry,
            health_monitor=self.monitor,
            strategy=LoadBalancingStrategy.LEAST_CONNECTIONS,
        )
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=0.5,
            success_threshold=3,
            timeout=30.0,
            minimum_requests=5,
        )
        self.retry_policy = RetryPolicy(
            config=RetryConfig(
                max_retries=3,
                strategy=RetryStrategy.EXPONENTIAL,
                base_delay=0.1,
                max_delay=2.0,
                jitter=0.2,
            )
        )
        
        # Metrics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.retried_requests = 0
    
    async def setup_service_fleet(self):
        """Setup service replicas"""
        
        # Primary replicas (high performance, high reliability)
        for i in range(3):
            await self.registry.register(
                agent_id=f"primary-{i}",
                name=f"Primary Service {i}",
                host="localhost",
                port=10001 + i,
                capabilities={
                    AgentCapability("api", "1.0"),
                    AgentCapability("database", "1.0"),
                },
                tags=["primary", "production"],
            )
            
            # Health checker (90% healthy, 5% degraded, 5% unhealthy)
            async def primary_health():
                rand = random.random()
                if rand < 0.90:
                    return True  # Healthy
                elif rand < 0.95:
                    # Degraded (slow but functional)
                    await asyncio.sleep(0.6)  # > 500ms threshold
                    return True
                else:
                    return False  # Unhealthy
            
            self.monitor.register_health_checker(f"primary-{i}", primary_health)
        
        # Secondary replicas (good performance, good reliability)
        for i in range(4):
            await self.registry.register(
                agent_id=f"secondary-{i}",
                name=f"Secondary Service {i}",
                host="localhost",
                port=10010 + i,
                capabilities={
                    AgentCapability("api", "1.0"),
                    AgentCapability("cache", "1.0"),
                },
                tags=["secondary", "production"],
            )
            
            # Health checker (80% healthy, 10% degraded, 10% unhealthy)
            async def secondary_health():
                rand = random.random()
                if rand < 0.80:
                    return True
                elif rand < 0.90:
                    await asyncio.sleep(0.7)
                    return True
                else:
                    return False
            
            self.monitor.register_health_checker(f"secondary-{i}", secondary_health)
        
        # Backup replicas (lower performance, lower reliability)
        for i in range(2):
            await self.registry.register(
                agent_id=f"backup-{i}",
                name=f"Backup Service {i}",
                host="localhost",
                port=10020 + i,
                capabilities={AgentCapability("api", "1.0")},
                tags=["backup", "fallback"],
            )
            
            # Health checker (70% healthy, 15% degraded, 15% unhealthy)
            async def backup_health():
                rand = random.random()
                if rand < 0.70:
                    return True
                elif rand < 0.85:
                    await asyncio.sleep(0.8)
                    return True
                else:
                    return False
            
            self.monitor.register_health_checker(f"backup-{i}", backup_health)
        
        print(f"✅ Service fleet ready: {await self.registry.count()} replicas")
        
        # Initial health check
        for agent_id in [f"primary-{i}" for i in range(3)] + \
                        [f"secondary-{i}" for i in range(4)] + \
                        [f"backup-{i}" for i in range(2)]:
            await self.monitor.check_health(agent_id)
        
        healthy = await self.monitor.get_healthy_agents()
        print(f"   Healthy: {len(healthy)}/{await self.registry.count()}")
    
    async def handle_request(
        self,
        request: ServiceRequest,
        attempt: int = 0,
    ) -> ServiceResponse:
        """Handle a service request with fault tolerance"""
        
        self.total_requests += 1
        start_time = datetime.utcnow()
        
        try:
            # Select healthy agent
            agent_result = await self.load_balancer.select_agent(
                capability="api",
                require_healthy=True,
            )
            agent_id = agent_result.agent.agent_id
            
            # Check circuit breaker
            circuit_state = self.circuit_breaker.get_state(agent_id)
            if circuit_state.name == "OPEN":
                if attempt < self.retry_policy.config.max_retries:
                    # Circuit open, retry with backoff
                    delay = self.retry_policy.calculate_delay(attempt)
                    await asyncio.sleep(delay)
                    self.retried_requests += 1
                    return await self.handle_request(request, attempt + 1)
                else:
                    raise Exception("Circuit breaker open, max retries exceeded")
            
            # Acquire connection
            await self.load_balancer.acquire_connection(agent_id)
            
            # Simulate request processing
            processing_time = random.uniform(0.05, 0.3)
            
            # Simulate failures (10% failure rate)
            if random.random() < 0.10:
                await asyncio.sleep(processing_time * 0.5)
                raise Exception(f"Service error on {agent_id}")
            
            await asyncio.sleep(processing_time)
            
            # Simulate response
            response_data = {
                "result": f"Processed {request.operation}",
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            # Success
            await self.circuit_breaker.record_success(agent_id)
            await self.load_balancer.release_connection(agent_id)
            
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.successful_requests += 1
            
            # Check if agent is degraded
            health_status = await self.monitor.get_health_status(agent_id)
            status_icon = "✅" if health_status == HealthStatus.HEALTHY else "⚠️"
            
            return ServiceResponse(
                request_id=request.request_id,
                success=True,
                data=response_data,
                agent_id=agent_id,
                latency_ms=latency,
            )
            
        except Exception as e:
            # Failure handling
            if 'agent_id' in locals():
                await self.circuit_breaker.record_failure(agent_id)
                await self.load_balancer.release_connection(agent_id, failed=True)
            
            # Retry logic
            if attempt < self.retry_policy.config.max_retries:
                delay = self.retry_policy.calculate_delay(attempt)
                await asyncio.sleep(delay)
                self.retried_requests += 1
                return await self.handle_request(request, attempt + 1)
            
            # Max retries exceeded
            self.failed_requests += 1
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return ServiceResponse(
                request_id=request.request_id,
                success=False,
                error=str(e),
                latency_ms=latency,
            )
    
    async def run_load_test(
        self,
        num_requests: int = 100,
        concurrent_requests: int = 10,
    ):
        """Run load test"""
        
        print(f"\n{'='*70}")
        print(f"🚀 Load Test Starting")
        print(f"{'='*70}")
        print(f"Total requests: {num_requests}")
        print(f"Concurrency: {concurrent_requests}")
        print()
        
        start_time = datetime.utcnow()
        
        # Generate requests
        requests = [
            ServiceRequest(
                request_id=f"req-{i+1:04d}",
                operation=random.choice(["read", "write", "update", "delete"]),
                payload={"data": f"payload-{i}"},
                priority=random.choice(["high", "normal", "low"]),
            )
            for i in range(num_requests)
        ]
        
        # Process requests with concurrency limit
        responses = []
        tasks = []
        
        for request in requests:
            task = self.handle_request(request)
            tasks.append(task)
            
            if len(tasks) >= concurrent_requests:
                batch_responses = await asyncio.gather(*tasks, return_exceptions=True)
                responses.extend([r for r in batch_responses if isinstance(r, ServiceResponse)])
                tasks = []
        
        # Process remaining
        if tasks:
            batch_responses = await asyncio.gather(*tasks, return_exceptions=True)
            responses.extend([r for r in batch_responses if isinstance(r, ServiceResponse)])
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Calculate statistics
        successful = [r for r in responses if r.success]
        failed = [r for r in responses if not r.success]
        avg_latency = sum(r.latency_ms for r in responses) / len(responses) if responses else 0
        p95_latency = sorted([r.latency_ms for r in responses])[int(len(responses) * 0.95)] if responses else 0
        
        # Print results
        print(f"\n{'='*70}")
        print("✅ Load Test Complete!")
        print(f"{'='*70}")
        print(f"Duration: {duration:.2f}s")
        print(f"Throughput: {len(responses)/duration:.1f} req/sec")
        print()
        print(f"📊 Request Statistics:")
        print(f"  Total: {self.total_requests}")
        print(f"  Successful: {self.successful_requests} ({self.successful_requests/self.total_requests*100:.1f}%)")
        print(f"  Failed: {self.failed_requests} ({self.failed_requests/self.total_requests*100:.1f}%)")
        print(f"  Retried: {self.retried_requests}")
        print()
        print(f"⏱️  Latency:")
        print(f"  Average: {avg_latency:.1f}ms")
        print(f"  P95: {p95_latency:.1f}ms")
        
        # Agent distribution
        print(f"\n🔄 Request Distribution:")
        agent_counts = {}
        for r in successful:
            if r.agent_id:
                agent_counts[r.agent_id] = agent_counts.get(r.agent_id, 0) + 1
        
        for agent_id, count in sorted(agent_counts.items(), key=lambda x: x[1], reverse=True)[:8]:
            percentage = count / len(successful) * 100
            tier = "🟢 Primary" if "primary" in agent_id else ("🟡 Secondary" if "secondary" in agent_id else "🔴 Backup")
            print(f"  {tier:12} {agent_id:15} {count:3d} requests ({percentage:5.1f}%)")
        
        # Health summary
        print(f"\n🏥 Health Summary:")
        healthy = await self.monitor.get_healthy_agents()
        unhealthy = await self.monitor.get_unhealthy_agents()
        print(f"  Healthy: {len(healthy)}/{await self.registry.count()}")
        if unhealthy:
            print(f"  ⚠️  Unhealthy: {len(unhealthy)} agents")
            for agent_id in unhealthy[:3]:
                metrics = await self.monitor.get_metrics(agent_id)
                if metrics:
                    print(f"     {agent_id}: {metrics.consecutive_failures} consecutive failures")
        
        # Circuit breaker summary
        print(f"\n🔌 Circuit Breaker Summary:")
        open_circuits = await self.circuit_breaker.get_open_circuits()
        half_open = await self.circuit_breaker.get_half_open_circuits()
        
        if open_circuits:
            print(f"  ⚠️  Open: {len(open_circuits)} circuits")
        if half_open:
            print(f"  🟡 Half-open: {len(half_open)} circuits")
        if not open_circuits and not half_open:
            print(f"  ✅ All circuits healthy")
        
        # Load balancer summary
        print(f"\n⚖️  Load Balancer:")
        lb_metrics = await self.load_balancer.get_all_metrics()
        total_lb_requests = sum(m.total_requests for m in lb_metrics.values())
        if total_lb_requests > 0:
            success_rate = sum(m.total_requests - m.failed_requests for m in lb_metrics.values()) / total_lb_requests * 100
            print(f"  Success rate: {success_rate:.1f}%")
            print(f"  Active connections: {sum(m.active_connections for m in lb_metrics.values())}")
        
        print()
    
    async def start(self):
        """Start the service"""
        await self.setup_service_fleet()
        await self.monitor.start()
        
        # Wait for initial health checks
        await asyncio.sleep(0.5)
    
    async def stop(self):
        """Stop the service"""
        await self.monitor.stop()


async def main():
    """Run the fault-tolerant service example"""
    
    service = FaultTolerantService()
    
    try:
        await service.start()
        
        # Run moderate load test
        print("\n🎯 Scenario 1: Moderate load (50 requests, 5 concurrent)")
        await service.run_load_test(num_requests=50, concurrent_requests=5)
        
        # Run high load test
        print("\n🎯 Scenario 2: High load (200 requests, 20 concurrent)")
        service.total_requests = 0
        service.successful_requests = 0
        service.failed_requests = 0
        service.retried_requests = 0
        await service.run_load_test(num_requests=200, concurrent_requests=20)
        
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())
