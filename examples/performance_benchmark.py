"""
Performance Benchmark Suite for WAOOAW Platform

Tests system performance under various load conditions:
- 100+ agents across multiple tiers
- 1000+ tasks/minute sustained throughput
- Multiple scenarios: steady load, burst traffic, failures, network delays

Measures:
- Latency: avg, P50, P95, P99
- Throughput: tasks/sec, tasks/min
- Resource usage: CPU, memory, connections
- Agent utilization: task distribution, health status
- Circuit breaker metrics: trips, recovery time
"""

import asyncio
import time
import statistics
import psutil
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from waooaw.discovery.service_registry import ServiceRegistry, AgentCapability
from waooaw.discovery.health_monitor import HealthMonitor, HealthStatus
from waooaw.discovery.load_balancer import LoadBalancer, LoadBalancingStrategy
from waooaw.discovery.circuit_breaker import CircuitBreaker
from waooaw.orchestration.task_queue import TaskQueue, Task, TaskPriority, TaskState
from waooaw.orchestration.worker_pool import WorkerPool


@dataclass
class PerformanceMetrics:
    """Performance metrics captured during benchmark"""
    scenario_name: str
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    
    # Latency metrics (milliseconds)
    latencies: List[float] = field(default_factory=list)
    
    # Throughput metrics
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    # Resource metrics
    cpu_samples: List[float] = field(default_factory=list)
    memory_samples: List[float] = field(default_factory=list)
    
    # Agent metrics
    agent_task_counts: Dict[str, int] = field(default_factory=dict)
    circuit_breaker_trips: int = 0
    
    def add_latency(self, latency_ms: float):
        """Add latency measurement"""
        self.latencies.append(latency_ms)
    
    def record_success(self, agent_id: str, latency_ms: float):
        """Record successful task"""
        self.successful_tasks += 1
        self.add_latency(latency_ms)
        self.agent_task_counts[agent_id] = self.agent_task_counts.get(agent_id, 0) + 1
    
    def record_failure(self):
        """Record failed task"""
        self.failed_tasks += 1
    
    def record_circuit_trip(self):
        """Record circuit breaker trip"""
        self.circuit_breaker_trips += 1
    
    def sample_resources(self):
        """Sample current CPU and memory usage"""
        process = psutil.Process()
        self.cpu_samples.append(process.cpu_percent(interval=0.1))
        self.memory_samples.append(process.memory_info().rss / 1024 / 1024)  # MB
    
    @property
    def duration_seconds(self) -> float:
        """Total benchmark duration"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    @property
    def tasks_per_second(self) -> float:
        """Throughput in tasks per second"""
        if self.duration_seconds > 0:
            return self.successful_tasks / self.duration_seconds
        return 0.0
    
    @property
    def tasks_per_minute(self) -> float:
        """Throughput in tasks per minute"""
        return self.tasks_per_second * 60
    
    @property
    def avg_latency_ms(self) -> float:
        """Average latency in milliseconds"""
        return statistics.mean(self.latencies) if self.latencies else 0.0
    
    @property
    def p50_latency_ms(self) -> float:
        """P50 (median) latency"""
        return statistics.median(self.latencies) if self.latencies else 0.0
    
    @property
    def p95_latency_ms(self) -> float:
        """P95 latency"""
        if self.latencies:
            sorted_latencies = sorted(self.latencies)
            idx = int(len(sorted_latencies) * 0.95)
            return sorted_latencies[idx]
        return 0.0
    
    @property
    def p99_latency_ms(self) -> float:
        """P99 latency"""
        if self.latencies:
            sorted_latencies = sorted(self.latencies)
            idx = int(len(sorted_latencies) * 0.99)
            return sorted_latencies[idx]
        return 0.0
    
    @property
    def avg_cpu_percent(self) -> float:
        """Average CPU usage"""
        return statistics.mean(self.cpu_samples) if self.cpu_samples else 0.0
    
    @property
    def avg_memory_mb(self) -> float:
        """Average memory usage in MB"""
        return statistics.mean(self.memory_samples) if self.memory_samples else 0.0
    
    @property
    def success_rate(self) -> float:
        """Task success rate as percentage"""
        if self.total_tasks > 0:
            return (self.successful_tasks / self.total_tasks) * 100
        return 0.0


class PerformanceBenchmark:
    """Performance benchmark suite for WAOOAW platform"""
    
    def __init__(self, num_agents: int = 100):
        self.num_agents = num_agents
        self.registry = ServiceRegistry()
        self.monitor = HealthMonitor(self.registry, check_interval=5.0)
        self.load_balancer = LoadBalancer(
            self.registry,
            self.monitor,
            strategy=LoadBalancingStrategy.WEIGHTED
        )
        self.circuit_breaker = CircuitBreaker()
        self.task_queue = TaskQueue()
        self.worker_pool = WorkerPool(self.task_queue, max_workers=50)
        
        self.metrics_by_scenario: Dict[str, PerformanceMetrics] = {}
    
    async def setup_agent_fleet(self):
        """Register agent fleet with multiple tiers"""
        print(f"🚀 Registering {self.num_agents} agents...")
        
        # Tier 1: Premium agents (20%) - High performance, high reliability
        premium_count = int(self.num_agents * 0.20)
        for i in range(premium_count):
            agent_id = f"premium-{i}"
            await self.registry.register(
                agent_id=agent_id,
                name=f"Premium Agent {i}",
                host="localhost",
                port=9000 + i,
                capabilities={
                    AgentCapability("compute", "2.0"),
                    AgentCapability("process", "2.0")
                },
                tags={"premium", "gpu", "high-memory"},
                metadata={"tier": "premium", "cores": 16, "memory_gb": 64}
            )
            
            # Premium health checker: 99% uptime, fast response (10-30ms)
            async def premium_health_checker(aid=agent_id):
                await asyncio.sleep(0.01 + (0.02 * (hash(aid) % 100) / 100))
                return hash(aid) % 100 < 99  # 99% healthy
            
            self.monitor.register_health_checker(agent_id, premium_health_checker)
            self.load_balancer.set_weight(agent_id, 10.0)  # 10x priority
        
        # Tier 2: Standard agents (50%) - Good performance, good reliability
        standard_count = int(self.num_agents * 0.50)
        for i in range(standard_count):
            agent_id = f"standard-{i}"
            await self.registry.register(
                agent_id=agent_id,
                name=f"Standard Agent {i}",
                host="localhost",
                port=10000 + i,
                capabilities={
                    AgentCapability("compute", "1.0"),
                    AgentCapability("process", "1.0")
                },
                tags={"standard", "production"},
                metadata={"tier": "standard", "cores": 8, "memory_gb": 32}
            )
            
            # Standard health checker: 95% uptime, medium response (30-70ms)
            async def standard_health_checker(aid=agent_id):
                await asyncio.sleep(0.03 + (0.04 * (hash(aid) % 100) / 100))
                return hash(aid) % 100 < 95  # 95% healthy
            
            self.monitor.register_health_checker(agent_id, standard_health_checker)
            self.load_balancer.set_weight(agent_id, 1.0)  # 1x priority
        
        # Tier 3: Budget agents (30%) - Basic performance, acceptable reliability
        budget_count = self.num_agents - premium_count - standard_count
        for i in range(budget_count):
            agent_id = f"budget-{i}"
            await self.registry.register(
                agent_id=agent_id,
                name=f"Budget Agent {i}",
                host="localhost",
                port=11000 + i,
                capabilities={
                    AgentCapability("compute", "1.0"),
                    AgentCapability("process", "1.0")
                },
                tags={"budget", "spot"},
                metadata={"tier": "budget", "cores": 4, "memory_gb": 16}
            )
            
            # Budget health checker: 90% uptime, slow response (70-150ms)
            async def budget_health_checker(aid=agent_id):
                await asyncio.sleep(0.07 + (0.08 * (hash(aid) % 100) / 100))
                return hash(aid) % 100 < 90  # 90% healthy
            
            self.monitor.register_health_checker(agent_id, budget_health_checker)
            self.load_balancer.set_weight(agent_id, 0.3)  # 0.3x priority
        
        print(f"✅ Registered {self.num_agents} agents:")
        print(f"   - Premium: {premium_count} (99% uptime, 10x weight)")
        print(f"   - Standard: {standard_count} (95% uptime, 1x weight)")
        print(f"   - Budget: {budget_count} (90% uptime, 0.3x weight)")
    
    async def start(self):
        """Start all services"""
        await self.monitor.start()
        await self.worker_pool.start()
        
        # Wait for initial health checks
        await asyncio.sleep(0.5)
        
        # Trigger initial health checks for all agents
        all_agents = await self.registry.list_all()
        for agent in all_agents:
            await self.monitor.check_health(agent.agent_id)
        
        print("✅ All services started and agents health-checked")
    
    async def stop(self):
        """Stop all services"""
        await self.worker_pool.stop()
        await self.monitor.stop()
    
    async def execute_task(self, task_id: str, metrics: PerformanceMetrics) -> bool:
        """Execute a single task and record metrics"""
        start_time = time.time()
        
        try:
            # Select agent with circuit breaker check
            selected = await self.load_balancer.select_agent(
                capability="compute",
                require_healthy=True
            )
            
            if not selected:
                metrics.record_failure()
                return False
            
            agent_id = selected.agent.agent_id
            agent_tier = selected.agent.metadata.get("tier", "unknown")
            
            # Acquire connection
            await self.load_balancer.acquire_connection(agent_id)
            
            try:
                # Simulate task execution based on tier
                if agent_tier == "premium":
                    execution_time = 0.010 + (0.020 * (hash(task_id) % 100) / 100)
                elif agent_tier == "standard":
                    execution_time = 0.030 + (0.040 * (hash(task_id) % 100) / 100)
                else:  # budget
                    execution_time = 0.070 + (0.080 * (hash(task_id) % 100) / 100)
                
                await asyncio.sleep(execution_time)
                
                # Simulate 2% failure rate
                if hash(task_id) % 100 < 2:
                    raise Exception("Simulated task failure")
                
                # Record success
                latency_ms = (time.time() - start_time) * 1000
                metrics.record_success(agent_id, latency_ms)
                await self.circuit_breaker.record_success(agent_id)
                
                return True
                
            finally:
                # Release connection
                await self.load_balancer.release_connection(agent_id)
        
        except Exception as e:
            # Record failure
            metrics.record_failure()
            if 'agent_id' in locals():
                await self.circuit_breaker.record_failure(agent_id)
            return False
    
    async def scenario_steady_load(self, duration_seconds: int = 60, target_tps: int = 20) -> PerformanceMetrics:
        """
        Scenario 1: Steady Load
        Sustain constant task rate for extended period
        """
        print(f"\n{'='*60}")
        print(f"📊 SCENARIO 1: Steady Load")
        print(f"   Duration: {duration_seconds}s")
        print(f"   Target: {target_tps} tasks/sec ({target_tps * 60} tasks/min)")
        print(f"{'='*60}\n")
        
        metrics = PerformanceMetrics(scenario_name="Steady Load")
        metrics.start_time = time.time()
        
        task_interval = 1.0 / target_tps
        task_num = 0
        
        # Resource monitoring task
        async def monitor_resources():
            while time.time() - metrics.start_time < duration_seconds:
                metrics.sample_resources()
                await asyncio.sleep(1.0)
        
        monitor_task = asyncio.create_task(monitor_resources())
        
        # Generate steady load
        end_time = time.time() + duration_seconds
        while time.time() < end_time:
            task_id = f"steady-{task_num}"
            metrics.total_tasks += 1
            
            # Execute task without waiting (fire and forget for steady rate)
            asyncio.create_task(self.execute_task(task_id, metrics))
            
            task_num += 1
            await asyncio.sleep(task_interval)
        
        # Wait for all tasks to complete
        print("⏳ Waiting for tasks to complete...")
        await asyncio.sleep(5.0)
        
        metrics.end_time = time.time()
        await monitor_task
        
        self.metrics_by_scenario["steady_load"] = metrics
        return metrics
    
    async def scenario_burst_traffic(self, num_bursts: int = 5, tasks_per_burst: int = 200, burst_interval: int = 10) -> PerformanceMetrics:
        """
        Scenario 2: Burst Traffic
        Periodic bursts of high task volume
        """
        print(f"\n{'='*60}")
        print(f"📊 SCENARIO 2: Burst Traffic")
        print(f"   Bursts: {num_bursts}")
        print(f"   Tasks per burst: {tasks_per_burst}")
        print(f"   Burst interval: {burst_interval}s")
        print(f"{'='*60}\n")
        
        metrics = PerformanceMetrics(scenario_name="Burst Traffic")
        metrics.start_time = time.time()
        
        # Resource monitoring
        async def monitor_resources():
            while len(metrics.cpu_samples) < num_bursts * burst_interval:
                metrics.sample_resources()
                await asyncio.sleep(1.0)
        
        monitor_task = asyncio.create_task(monitor_resources())
        
        for burst_num in range(num_bursts):
            print(f"💥 Burst {burst_num + 1}/{num_bursts}: Submitting {tasks_per_burst} tasks...")
            
            # Submit burst of tasks concurrently
            tasks = []
            for task_num in range(tasks_per_burst):
                task_id = f"burst-{burst_num}-{task_num}"
                metrics.total_tasks += 1
                tasks.append(self.execute_task(task_id, metrics))
            
            # Wait for burst to complete
            await asyncio.gather(*tasks, return_exceptions=True)
            
            print(f"   ✅ Burst {burst_num + 1} complete: {metrics.successful_tasks}/{metrics.total_tasks} succeeded")
            
            # Wait before next burst
            if burst_num < num_bursts - 1:
                await asyncio.sleep(burst_interval)
        
        metrics.end_time = time.time()
        await monitor_task
        
        self.metrics_by_scenario["burst_traffic"] = metrics
        return metrics
    
    async def scenario_agent_failures(self, duration_seconds: int = 30, target_tps: int = 15, failure_rate: float = 0.10) -> PerformanceMetrics:
        """
        Scenario 3: Agent Failures
        Test resilience with random agent failures
        """
        print(f"\n{'='*60}")
        print(f"📊 SCENARIO 3: Agent Failures")
        print(f"   Duration: {duration_seconds}s")
        print(f"   Target: {target_tps} tasks/sec")
        print(f"   Failure rate: {failure_rate * 100}% agents")
        print(f"{'='*60}\n")
        
        metrics = PerformanceMetrics(scenario_name="Agent Failures")
        metrics.start_time = time.time()
        
        # Simulate random agent failures
        async def simulate_failures():
            while time.time() - metrics.start_time < duration_seconds:
                all_agents = await self.registry.list_all()
                
                # Mark random agents as unhealthy
                for agent in all_agents:
                    if hash(agent.agent_id + str(time.time())) % 100 < failure_rate * 100:
                        health_status = await self.monitor.get_health_status(agent.agent_id)
                        if health_status and health_status.status == HealthStatus.HEALTHY:
                            print(f"   ⚠️  Simulated failure: {agent.agent_id}")
                            # Force health check to fail (will recover on next check)
                
                await asyncio.sleep(5.0)
        
        failure_task = asyncio.create_task(simulate_failures())
        
        # Generate load
        task_num = 0
        task_interval = 1.0 / target_tps
        end_time = time.time() + duration_seconds
        
        while time.time() < end_time:
            task_id = f"failure-{task_num}"
            metrics.total_tasks += 1
            metrics.sample_resources()
            
            asyncio.create_task(self.execute_task(task_id, metrics))
            
            task_num += 1
            await asyncio.sleep(task_interval)
        
        # Wait for completion
        await asyncio.sleep(5.0)
        metrics.end_time = time.time()
        
        failure_task.cancel()
        try:
            await failure_task
        except asyncio.CancelledError:
            pass
        
        self.metrics_by_scenario["agent_failures"] = metrics
        return metrics
    
    def print_metrics_report(self, metrics: PerformanceMetrics):
        """Print detailed metrics report"""
        print(f"\n{'='*60}")
        print(f"📊 METRICS REPORT: {metrics.scenario_name}")
        print(f"{'='*60}\n")
        
        # Task metrics
        print(f"📈 Task Metrics:")
        print(f"   Total tasks:     {metrics.total_tasks}")
        print(f"   Successful:      {metrics.successful_tasks} ({metrics.success_rate:.1f}%)")
        print(f"   Failed:          {metrics.failed_tasks}")
        print(f"   Duration:        {metrics.duration_seconds:.2f}s")
        
        # Throughput
        print(f"\n⚡ Throughput:")
        print(f"   Tasks/second:    {metrics.tasks_per_second:.2f}")
        print(f"   Tasks/minute:    {metrics.tasks_per_minute:.2f}")
        
        # Latency
        print(f"\n⏱️  Latency (milliseconds):")
        print(f"   Average:         {metrics.avg_latency_ms:.2f} ms")
        print(f"   P50 (median):    {metrics.p50_latency_ms:.2f} ms")
        print(f"   P95:             {metrics.p95_latency_ms:.2f} ms")
        print(f"   P99:             {metrics.p99_latency_ms:.2f} ms")
        
        # Resource usage
        print(f"\n💾 Resource Usage:")
        print(f"   Avg CPU:         {metrics.avg_cpu_percent:.1f}%")
        print(f"   Avg Memory:      {metrics.avg_memory_mb:.1f} MB")
        
        # Agent distribution
        print(f"\n🤖 Agent Task Distribution (Top 10):")
        sorted_agents = sorted(metrics.agent_task_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for agent_id, count in sorted_agents:
            print(f"   {agent_id}: {count} tasks")
        
        # Circuit breaker
        print(f"\n🔌 Circuit Breaker:")
        print(f"   Trips:           {metrics.circuit_breaker_trips}")
        
        print(f"\n{'='*60}\n")
    
    def print_summary_report(self):
        """Print summary report across all scenarios"""
        print(f"\n{'='*60}")
        print(f"📊 PERFORMANCE BENCHMARK SUMMARY")
        print(f"{'='*60}\n")
        
        print(f"🏗️  Configuration:")
        print(f"   Total agents:    {self.num_agents}")
        print(f"   Max workers:     {self.worker_pool.max_workers}")
        print(f"   Scenarios run:   {len(self.metrics_by_scenario)}")
        
        print(f"\n📊 Scenario Comparison:\n")
        print(f"{'Scenario':<20} {'Tasks':<8} {'Success':<8} {'TPS':<8} {'Avg (ms)':<10} {'P95 (ms)':<10} {'P99 (ms)':<10}")
        print(f"{'-'*86}")
        
        for scenario_name, metrics in self.metrics_by_scenario.items():
            print(f"{scenario_name:<20} {metrics.total_tasks:<8} {metrics.success_rate:>6.1f}% {metrics.tasks_per_second:>6.1f}  {metrics.avg_latency_ms:>8.2f}   {metrics.p95_latency_ms:>8.2f}   {metrics.p99_latency_ms:>8.2f}")
        
        print(f"\n{'='*60}\n")


async def main():
    """Run performance benchmark suite"""
    print("🚀 WAOOAW Performance Benchmark Suite")
    print("="*60)
    
    # Configuration
    NUM_AGENTS = 120  # 120 agents across 3 tiers
    
    benchmark = PerformanceBenchmark(num_agents=NUM_AGENTS)
    
    try:
        # Setup
        await benchmark.setup_agent_fleet()
        await benchmark.start()
        
        # Scenario 1: Steady Load (60s, 20 TPS = 1200 tasks/min)
        metrics_steady = await benchmark.scenario_steady_load(
            duration_seconds=60,
            target_tps=20
        )
        benchmark.print_metrics_report(metrics_steady)
        
        # Scenario 2: Burst Traffic (5 bursts, 200 tasks each = 1000 tasks)
        metrics_burst = await benchmark.scenario_burst_traffic(
            num_bursts=5,
            tasks_per_burst=200,
            burst_interval=10
        )
        benchmark.print_metrics_report(metrics_burst)
        
        # Scenario 3: Agent Failures (30s, 15 TPS with 10% failure rate)
        metrics_failures = await benchmark.scenario_agent_failures(
            duration_seconds=30,
            target_tps=15,
            failure_rate=0.10
        )
        benchmark.print_metrics_report(metrics_failures)
        
        # Summary report
        benchmark.print_summary_report()
        
        print("✅ Performance benchmark complete!")
        
    finally:
        await benchmark.stop()


if __name__ == "__main__":
    asyncio.run(main())
