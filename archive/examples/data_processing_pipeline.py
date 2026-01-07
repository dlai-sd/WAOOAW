#!/usr/bin/env python3
"""
Data Processing Pipeline Example

Demonstrates a multi-stage data processing pipeline using the WAOOAW
orchestration and discovery systems.

Workflow:
1. Data Ingestion - Load data from source
2. Data Validation - Check data quality
3. Data Transformation - Apply transformations
4. Data Aggregation - Compute aggregates
5. Data Export - Save results

Features:
- Agent registration with specialized capabilities
- Health monitoring of agents
- Load-balanced task distribution
- Fault tolerance with circuit breakers
- Retry logic for transient failures
"""

import asyncio
import random
from datetime import datetime
from typing import Dict, List, Any

from waooaw.discovery import (
    ServiceRegistry,
    HealthMonitor,
    LoadBalancer,
    LoadBalancingStrategy,
    CircuitBreaker,
    AgentCapability,
)
from waooaw.orchestration import (
    TaskQueue,
    WorkerPool,
    DependencyGraph,
    RetryPolicy,
    RetryConfig,
    RetryStrategy,
)


class DataProcessor:
    """Multi-agent data processing pipeline"""
    
    def __init__(self):
        # Discovery components
        self.registry = ServiceRegistry()
        self.monitor = HealthMonitor(self.registry, failure_threshold=3)
        self.load_balancer = LoadBalancer(
            self.registry,
            health_monitor=self.monitor,
            strategy=LoadBalancingStrategy.LEAST_CONNECTIONS,
        )
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=0.5,
            minimum_requests=3,
        )
        
        # Orchestration components
        self.task_queue = TaskQueue(name="data-pipeline", max_capacity=1000)
        self.worker_pool = WorkerPool(
            task_queue=self.task_queue,
            min_workers=2,
            max_workers=10,
        )
        self.dependency_graph = DependencyGraph()
        
        # Results storage
        self.results: Dict[str, Any] = {}
        
    async def setup_agents(self):
        """Register specialized data processing agents"""
        
        # Ingestion agents (load data from sources)
        for i in range(3):
            await self.registry.register(
                agent_id=f"ingestion-{i}",
                name=f"Data Ingestion Agent {i}",
                host="localhost",
                port=8001 + i,
                capabilities={AgentCapability("ingest", "1.0")},
                tags=["ingestion", "input"],
            )
            
            # Health checker
            async def healthy():
                return True
            self.monitor.register_health_checker(f"ingestion-{i}", healthy)
        
        # Validation agents (check data quality)
        for i in range(2):
            await self.registry.register(
                agent_id=f"validation-{i}",
                name=f"Data Validation Agent {i}",
                host="localhost",
                port=8010 + i,
                capabilities={AgentCapability("validate", "1.0")},
                tags=["validation", "quality"],
            )
            
            async def healthy():
                return True
            self.monitor.register_health_checker(f"validation-{i}", healthy)
        
        # Transformation agents (apply transformations)
        for i in range(4):
            await self.registry.register(
                agent_id=f"transform-{i}",
                name=f"Data Transformation Agent {i}",
                host="localhost",
                port=8020 + i,
                capabilities={AgentCapability("transform", "1.0")},
                tags=["transformation", "processing"],
            )
            
            async def healthy():
                return True
            self.monitor.register_health_checker(f"transform-{i}", healthy)
        
        # Aggregation agents (compute aggregates)
        for i in range(2):
            await self.registry.register(
                agent_id=f"aggregate-{i}",
                name=f"Data Aggregation Agent {i}",
                host="localhost",
                port=8030 + i,
                capabilities={AgentCapability("aggregate", "1.0")},
                tags=["aggregation", "analytics"],
            )
            
            async def healthy():
                return True
            self.monitor.register_health_checker(f"aggregate-{i}", healthy)
        
        # Export agents (save results)
        await self.registry.register(
            agent_id="export-0",
            name="Data Export Agent",
            host="localhost",
            port=8040,
            capabilities={AgentCapability("export", "1.0")},
            tags=["export", "output"],
        )
        
        async def healthy():
            return True
        self.monitor.register_health_checker("export-0", healthy)
        
        print(f"✅ Registered {await self.registry.count()} agents")
        
    async def ingest_data(self, batch_id: str) -> Dict[str, Any]:
        """Stage 1: Ingest data"""
        
        # Select agent
        agent_result = await self.load_balancer.select_agent(
            capability="ingest",
            require_healthy=True,
        )
        agent_id = agent_result.agent.agent_id
        
        try:
            await self.load_balancer.acquire_connection(agent_id)
            
            # Simulate data ingestion
            await asyncio.sleep(random.uniform(0.1, 0.3))
            
            data = {
                "batch_id": batch_id,
                "records": random.randint(1000, 5000),
                "timestamp": datetime.utcnow().isoformat(),
                "source": f"source-{random.randint(1, 3)}",
            }
            
            await self.circuit_breaker.record_success(agent_id)
            await self.load_balancer.release_connection(agent_id)
            
            print(f"  📥 Ingested {data['records']} records (batch {batch_id}) via {agent_id}")
            return data
            
        except Exception as e:
            await self.circuit_breaker.record_failure(agent_id)
            await self.load_balancer.release_connection(agent_id, failed=True)
            raise
    
    async def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 2: Validate data quality"""
        
        agent_result = await self.load_balancer.select_agent(
            capability="validate",
            require_healthy=True,
        )
        agent_id = agent_result.agent.agent_id
        
        try:
            await self.load_balancer.acquire_connection(agent_id)
            
            # Simulate validation
            await asyncio.sleep(random.uniform(0.05, 0.15))
            
            # 95% pass rate
            valid = random.random() < 0.95
            
            result = {
                **data,
                "valid": valid,
                "validation_errors": [] if valid else ["missing_field", "invalid_format"],
                "validated_at": datetime.utcnow().isoformat(),
            }
            
            await self.circuit_breaker.record_success(agent_id)
            await self.load_balancer.release_connection(agent_id)
            
            status = "✅ valid" if valid else "❌ invalid"
            print(f"  🔍 Validated batch {data['batch_id']}: {status} via {agent_id}")
            return result
            
        except Exception as e:
            await self.circuit_breaker.record_failure(agent_id)
            await self.load_balancer.release_connection(agent_id, failed=True)
            raise
    
    async def transform_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 3: Transform data"""
        
        if not data.get("valid", False):
            print(f"  ⏭️  Skipped transformation for invalid batch {data['batch_id']}")
            return data
        
        agent_result = await self.load_balancer.select_agent(
            capability="transform",
            require_healthy=True,
        )
        agent_id = agent_result.agent.agent_id
        
        try:
            await self.load_balancer.acquire_connection(agent_id)
            
            # Simulate transformation
            await asyncio.sleep(random.uniform(0.2, 0.4))
            
            result = {
                **data,
                "transformed": True,
                "transformations_applied": ["normalize", "deduplicate", "enrich"],
                "transformed_at": datetime.utcnow().isoformat(),
            }
            
            await self.circuit_breaker.record_success(agent_id)
            await self.load_balancer.release_connection(agent_id)
            
            print(f"  ⚙️  Transformed batch {data['batch_id']} via {agent_id}")
            return result
            
        except Exception as e:
            await self.circuit_breaker.record_failure(agent_id)
            await self.load_balancer.release_connection(agent_id, failed=True)
            raise
    
    async def aggregate_data(self, data_batches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Stage 4: Aggregate data"""
        
        agent_result = await self.load_balancer.select_agent(
            capability="aggregate",
            require_healthy=True,
        )
        agent_id = agent_result.agent.agent_id
        
        try:
            await self.load_balancer.acquire_connection(agent_id)
            
            # Simulate aggregation
            await asyncio.sleep(random.uniform(0.3, 0.5))
            
            valid_batches = [b for b in data_batches if b.get("valid", False)]
            total_records = sum(b.get("records", 0) for b in valid_batches)
            
            result = {
                "total_batches": len(data_batches),
                "valid_batches": len(valid_batches),
                "total_records": total_records,
                "aggregated_at": datetime.utcnow().isoformat(),
            }
            
            await self.circuit_breaker.record_success(agent_id)
            await self.load_balancer.release_connection(agent_id)
            
            print(f"  📊 Aggregated {len(valid_batches)}/{len(data_batches)} batches ({total_records} records) via {agent_id}")
            return result
            
        except Exception as e:
            await self.circuit_breaker.record_failure(agent_id)
            await self.load_balancer.release_connection(agent_id, failed=True)
            raise
    
    async def export_data(self, data: Dict[str, Any]) -> bool:
        """Stage 5: Export results"""
        
        agent_result = await self.load_balancer.select_agent(
            capability="export",
            require_healthy=True,
        )
        agent_id = agent_result.agent.agent_id
        
        try:
            await self.load_balancer.acquire_connection(agent_id)
            
            # Simulate export
            await asyncio.sleep(random.uniform(0.1, 0.2))
            
            await self.circuit_breaker.record_success(agent_id)
            await self.load_balancer.release_connection(agent_id)
            
            print(f"  💾 Exported results via {agent_id}")
            return True
            
        except Exception as e:
            await self.circuit_breaker.record_failure(agent_id)
            await self.load_balancer.release_connection(agent_id, failed=True)
            raise
    
    async def process_pipeline(self, num_batches: int = 5):
        """Execute complete pipeline"""
        
        print(f"\n{'='*60}")
        print(f"🚀 Starting Data Processing Pipeline ({num_batches} batches)")
        print(f"{'='*60}\n")
        
        start_time = datetime.utcnow()
        
        # Stage 1 & 2 & 3: Process each batch (ingest → validate → transform)
        print("📥 Stage 1-3: Ingestion → Validation → Transformation\n")
        processed_batches = []
        
        for i in range(num_batches):
            batch_id = f"batch-{i+1:03d}"
            
            # Ingest
            data = await self.ingest_data(batch_id)
            
            # Validate
            data = await self.validate_data(data)
            
            # Transform (if valid)
            data = await self.transform_data(data)
            
            processed_batches.append(data)
            print()
        
        # Stage 4: Aggregate all batches
        print("📊 Stage 4: Aggregation\n")
        aggregated = await self.aggregate_data(processed_batches)
        print()
        
        # Stage 5: Export results
        print("💾 Stage 5: Export\n")
        await self.export_data(aggregated)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Print summary
        print(f"\n{'='*60}")
        print("✅ Pipeline Complete!")
        print(f"{'='*60}")
        print(f"Duration: {duration:.2f}s")
        print(f"Total batches: {aggregated['total_batches']}")
        print(f"Valid batches: {aggregated['valid_batches']}")
        print(f"Total records: {aggregated['total_records']}")
        
        # Print agent health
        print(f"\n📊 Agent Health Summary:")
        healthy = await self.monitor.get_healthy_agents()
        print(f"  Healthy agents: {len(healthy)}/{await self.registry.count()}")
        
        # Print circuit breaker status
        print(f"\n🔌 Circuit Breaker Status:")
        open_circuits = await self.circuit_breaker.get_open_circuits()
        if open_circuits:
            print(f"  ⚠️  Open circuits: {len(open_circuits)}")
        else:
            print(f"  ✅ All circuits closed")
        
        # Print load balancer metrics
        print(f"\n⚖️  Load Distribution:")
        lb_metrics = await self.load_balancer.get_all_metrics()
        for agent_id, metrics in sorted(lb_metrics.items())[:5]:
            print(f"  {agent_id}: {metrics.total_requests} requests, {metrics.active_connections} active")
        
        print()
    
    async def start(self):
        """Start the pipeline"""
        await self.setup_agents()
        await self.worker_pool.start()
        await self.monitor.start()
        
        # Wait for initial health checks
        await asyncio.sleep(0.5)
        
        # Trigger initial health checks for all agents
        all_agents = await self.registry.list_all()
        for agent in all_agents:
            await self.monitor.check_health(agent.agent_id)
    
    async def stop(self):
        """Stop the pipeline"""
        await self.worker_pool.stop()
        await self.monitor.stop()


async def main():
    """Run the data processing pipeline example"""
    
    processor = DataProcessor()
    
    try:
        await processor.start()
        await processor.process_pipeline(num_batches=10)
    finally:
        await processor.stop()


if __name__ == "__main__":
    asyncio.run(main())
