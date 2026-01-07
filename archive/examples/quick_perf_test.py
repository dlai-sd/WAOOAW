"""Quick performance test - simplified version for faster validation"""
import asyncio
import time
import statistics
import os

# Suppress JSON logs
os.environ['WAOOAW_LOG_LEVEL'] = 'WARNING'

from examples.performance_benchmark import PerformanceBenchmark

async def quick_test():
    """Run quick performance test"""
    print("🚀 Quick Performance Test")
    print("="*60)
    
    # Smaller setup for faster testing
    NUM_AGENTS = 120  
    benchmark = PerformanceBenchmark(num_agents=NUM_AGENTS)
    
    try:
        await benchmark.setup_agent_fleet()
        await benchmark.start()
        
        # Run only steady load scenario with shorter duration
        print("\n⚡ Running Steady Load Scenario (30s)...")
        metrics = await benchmark.scenario_steady_load(
            duration_seconds=30,
            target_tps=20  # 1200 tasks/min
        )
        
        benchmark.print_metrics_report(metrics)
        
        # Validate performance targets
        print("\n✅ Performance Validation:")
        passed = True
        
        if metrics.tasks_per_minute >= 1000:
            print(f"   ✓ Throughput: {metrics.tasks_per_minute:.0f} tasks/min (>= 1000)")
        else:
            print(f"   ✗ Throughput: {metrics.tasks_per_minute:.0f} tasks/min (< 1000)")
            passed = False
        
        if metrics.p95_latency_ms < 200:
            print(f"   ✓ P95 Latency: {metrics.p95_latency_ms:.1f}ms (< 200ms)")
        else:
            print(f"   ✗ P95 Latency: {metrics.p95_latency_ms:.1f}ms (>= 200ms)")
            passed = False
        
        if metrics.success_rate >= 95:
            print(f"   ✓ Success Rate: {metrics.success_rate:.1f}% (>= 95%)")
        else:
            print(f"   ✗ Success Rate: {metrics.success_rate:.1f}% (< 95%)")
            passed = False
        
        if passed:
            print("\n🎉 All performance targets MET!")
        else:
            print("\n⚠️  Some performance targets not met")
        
    finally:
        await benchmark.stop()

if __name__ == "__main__":
    asyncio.run(quick_test())
