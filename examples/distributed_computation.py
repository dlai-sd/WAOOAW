#!/usr/bin/env python3
"""
Distributed Computation Example

Demonstrates parallel task execution using the WAOOAW orchestration
and discovery systems.

Workflow:
- Compute-intensive tasks distributed across multiple worker agents
- Dynamic scaling based on workload
- Health monitoring and automatic failover
- Load balancing with weighted distribution (premium vs standard workers)
- Circuit breakers for fault isolation

Use Case: Monte Carlo simulation, batch processing, parallel data analysis
"""

import asyncio
import math
import random
from datetime import datetime
from typing import List, Dict, Any

from waooaw.discovery import (
    ServiceRegistry,
    HealthMonitor,
    LoadBalancer,
    LoadBalancingStrategy,
    CircuitBreaker,
    AgentCapability,
)


class DistributedCompute:
    """Distributed computation framework"""
    
    def __init__(self):
        self.registry = ServiceRegistry()
        self.monitor = HealthMonitor(self.registry, failure_threshold=2)
        self.load_balancer = LoadBalancer(
            self.registry,
            health_monitor=self.monitor,
            strategy=LoadBalancingStrategy.WEIGHTED,
        )
        self.circuit_breaker = CircuitBreaker(failure_threshold=0.6)
        
        self.results: List[Any] = []
    
    async def setup_compute_cluster(self):
        """Setup compute agents with different performance tiers"""
        
        # Premium compute agents (8 cores, high memory)
        for i in range(3):
            await self.registry.register(
                agent_id=f"premium-{i}",
                name=f"Premium Compute Agent {i}",
                host="localhost",
                port=9001 + i,
                capabilities={
                    AgentCapability("compute", "2.0"),
                    AgentCapability("gpu", "1.0"),
                },
                tags=["premium", "high-performance"],
            )
            
            # Premium agents get 10x weight
            self.load_balancer.set_weight(f"premium-{i}", 10)
            
            # Health checker (premium agents more reliable)
            async def premium_health():
                return random.random() < 0.98  # 98% uptime
            self.monitor.register_health_checker(f"premium-{i}", premium_health)
        
        # Standard compute agents (4 cores, standard memory)
        for i in range(5):
            await self.registry.register(
                agent_id=f"standard-{i}",
                name=f"Standard Compute Agent {i}",
                host="localhost",
                port=9010 + i,
                capabilities={AgentCapability("compute", "1.0")},
                tags=["standard", "general-purpose"],
            )
            
            # Standard agents get 1x weight
            self.load_balancer.set_weight(f"standard-{i}", 1)
            
            # Health checker (standard agents less reliable)
            async def standard_health():
                return random.random() < 0.92  # 92% uptime
            self.monitor.register_health_checker(f"standard-{i}", standard_health)
        
        # Budget compute agents (2 cores, low memory)
        for i in range(4):
            await self.registry.register(
                agent_id=f"budget-{i}",
                name=f"Budget Compute Agent {i}",
                host="localhost",
                port=9020 + i,
                capabilities={AgentCapability("compute", "0.5")},
                tags=["budget", "low-cost"],
            )
            
            # Budget agents get 0.5x weight
            self.load_balancer.set_weight(f"budget-{i}", 0.5)
            
            # Health checker (budget agents least reliable)
            async def budget_health():
                return random.random() < 0.85  # 85% uptime
            self.monitor.register_health_checker(f"budget-{i}", budget_health)
        
        print(f"✅ Cluster ready: {await self.registry.count()} compute agents")
        
        # Check initial health
        for agent_id in [f"premium-{i}" for i in range(3)] + \
                        [f"standard-{i}" for i in range(5)] + \
                        [f"budget-{i}" for i in range(4)]:
            await self.monitor.check_health(agent_id)
        
        healthy = await self.monitor.get_healthy_agents()
        print(f"   Healthy: {len(healthy)}/{await self.registry.count()}")
    
    async def execute_task(
        self,
        task_id: int,
        complexity: float = 1.0,
        prefer_gpu: bool = False,
    ) -> Dict[str, Any]:
        """Execute a compute task"""
        
        # Select agent based on requirements
        if prefer_gpu:
            agent_result = await self.load_balancer.select_agent(
                capability="gpu",
                require_healthy=True,
            )
        else:
            agent_result = await self.load_balancer.select_agent(
                capability="compute",
                require_healthy=True,
            )
        
        agent_id = agent_result.agent.agent_id
        
        # Check circuit breaker
        circuit_state = self.circuit_breaker.get_state(agent_id)
        if circuit_state.name == "OPEN":
            print(f"  ⚠️  Task {task_id}: Circuit breaker OPEN for {agent_id}, retrying...")
            # Retry with different agent
            return await self.execute_task(task_id, complexity, prefer_gpu)
        
        try:
            await self.load_balancer.acquire_connection(agent_id)
            
            # Simulate computation (time varies by agent tier)
            if "premium" in agent_id:
                compute_time = complexity * random.uniform(0.05, 0.1)
                performance = "⚡"
            elif "standard" in agent_id:
                compute_time = complexity * random.uniform(0.1, 0.2)
                performance = "⚙️"
            else:  # budget
                compute_time = complexity * random.uniform(0.2, 0.4)
                performance = "🐢"
            
            # Simulate occasional failures
            if random.random() < 0.05:  # 5% failure rate
                await asyncio.sleep(compute_time * 0.3)
                raise ValueError(f"Task failed on {agent_id}")
            
            await asyncio.sleep(compute_time)
            
            # Compute result (example: Pi estimation using Monte Carlo)
            samples = int(10000 * complexity)
            inside = sum(1 for _ in range(samples) 
                        if random.random()**2 + random.random()**2 <= 1)
            pi_estimate = 4 * inside / samples
            
            result = {
                "task_id": task_id,
                "agent_id": agent_id,
                "complexity": complexity,
                "compute_time": compute_time,
                "pi_estimate": pi_estimate,
                "samples": samples,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            await self.circuit_breaker.record_success(agent_id)
            await self.load_balancer.release_connection(agent_id)
            
            print(f"  {performance} Task {task_id:03d} completed via {agent_id} ({compute_time:.3f}s, π≈{pi_estimate:.4f})")
            return result
            
        except Exception as e:
            await self.circuit_breaker.record_failure(agent_id)
            await self.load_balancer.release_connection(agent_id, failed=True)
            
            print(f"  ❌ Task {task_id}: Failed on {agent_id}, retrying...")
            
            # Retry with exponential backoff
            await asyncio.sleep(0.1)
            return await self.execute_task(task_id, complexity, prefer_gpu)
    
    async def run_batch(
        self,
        num_tasks: int = 50,
        complexity_range: tuple = (0.5, 2.0),
        parallel_workers: int = 10,
    ):
        """Execute a batch of compute tasks"""
        
        print(f"\n{'='*70}")
        print(f"🚀 Starting Distributed Computation")
        print(f"{'='*70}")
        print(f"Tasks: {num_tasks}")
        print(f"Complexity: {complexity_range[0]:.1f}x - {complexity_range[1]:.1f}x")
        print(f"Parallel workers: {parallel_workers}")
        print()
        
        start_time = datetime.utcnow()
        
        # Create tasks with varying complexity
        tasks = []
        for i in range(num_tasks):
            complexity = random.uniform(*complexity_range)
            prefer_gpu = random.random() < 0.2  # 20% prefer GPU
            
            task = self.execute_task(i + 1, complexity, prefer_gpu)
            tasks.append(task)
            
            # Limit parallel execution
            if len(tasks) >= parallel_workers:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                self.results.extend([r for r in results if not isinstance(r, Exception)])
                tasks = []
        
        # Execute remaining tasks
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            self.results.extend([r for r in results if not isinstance(r, Exception)])
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Calculate statistics
        successful_tasks = len(self.results)
        avg_compute_time = sum(r["compute_time"] for r in self.results) / successful_tasks if successful_tasks > 0 else 0
        avg_pi = sum(r["pi_estimate"] for r in self.results) / successful_tasks if successful_tasks > 0 else 0
        total_samples = sum(r["samples"] for r in self.results)
        
        # Print summary
        print(f"\n{'='*70}")
        print("✅ Batch Complete!")
        print(f"{'='*70}")
        print(f"Duration: {duration:.2f}s")
        print(f"Successful tasks: {successful_tasks}/{num_tasks} ({successful_tasks/num_tasks*100:.1f}%)")
        print(f"Average compute time: {avg_compute_time:.3f}s")
        print(f"Total samples: {total_samples:,}")
        print(f"Average π estimate: {avg_pi:.6f} (error: {abs(avg_pi - math.pi)/math.pi*100:.3f}%)")
        print(f"Throughput: {successful_tasks/duration:.1f} tasks/sec")
        
        # Agent utilization
        print(f"\n📊 Agent Utilization:")
        agent_tasks = {}
        for result in self.results:
            agent_id = result["agent_id"]
            agent_tasks[agent_id] = agent_tasks.get(agent_id, 0) + 1
        
        for agent_id, count in sorted(agent_tasks.items(), key=lambda x: x[1], reverse=True)[:10]:
            percentage = count / successful_tasks * 100
            tier = "⚡ Premium" if "premium" in agent_id else ("⚙️  Standard" if "standard" in agent_id else "🐢 Budget")
            print(f"  {tier:12} {agent_id:15} {count:3d} tasks ({percentage:5.1f}%)")
        
        # Health status
        print(f"\n🏥 Health Status:")
        healthy = await self.monitor.get_healthy_agents()
        unhealthy = await self.monitor.get_unhealthy_agents()
        print(f"  Healthy: {len(healthy)}/{await self.registry.count()}")
        if unhealthy:
            print(f"  ⚠️  Unhealthy: {', '.join(unhealthy)}")
        
        # Circuit breakers
        print(f"\n🔌 Circuit Breakers:")
        open_circuits = await self.circuit_breaker.get_open_circuits()
        if open_circuits:
            print(f"  ⚠️  Open: {len(open_circuits)} agents")
            for agent_id in open_circuits[:5]:
                metrics = await self.circuit_breaker.get_metrics(agent_id)
                print(f"     {agent_id}: {metrics.failed_requests} failures")
        else:
            print(f"  ✅ All circuits closed")
        
        # Load balancer stats
        print(f"\n⚖️  Load Balancer:")
        lb_metrics = await self.load_balancer.get_all_metrics()
        total_requests = sum(m.total_requests for m in lb_metrics.values())
        print(f"  Total requests: {total_requests}")
        print(f"  Success rate: {sum(m.total_requests - m.failed_requests for m in lb_metrics.values()) / total_requests * 100:.1f}%")
        
        print()
    
    async def start(self):
        """Start the cluster"""
        await self.setup_compute_cluster()
        await self.monitor.start()
        
        # Wait for initial health checks
        await asyncio.sleep(0.5)
    
    async def stop(self):
        """Stop the cluster"""
        await self.monitor.stop()


async def main():
    """Run the distributed computation example"""
    
    cluster = DistributedCompute()
    
    try:
        await cluster.start()
        
        # Run small batch
        print("\n🎯 Scenario 1: Small batch (20 tasks, low complexity)")
        await cluster.run_batch(num_tasks=20, complexity_range=(0.5, 1.0), parallel_workers=5)
        
        # Run large batch
        print("\n🎯 Scenario 2: Large batch (100 tasks, high complexity)")
        cluster.results = []  # Reset results
        await cluster.run_batch(num_tasks=100, complexity_range=(1.0, 2.5), parallel_workers=15)
        
    finally:
        await cluster.stop()


if __name__ == "__main__":
    asyncio.run(main())
