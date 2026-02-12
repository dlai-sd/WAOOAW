#!/usr/bin/env python3
"""
Connection Pool Monitoring Script for AGP2-PERF-1.5

Monitors SQLAlchemy connection pool metrics under load to validate:
- Pool size is adequate for concurrent load
- No connection exhaustion or timeouts
- Overflow usage patterns
- Connection checkout performance
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any
from sqlalchemy import text, event
from sqlalchemy.pool import Pool

from core.config import settings
from core.database import DatabaseService


class PoolMonitor:
    """Monitor connection pool metrics during load testing."""
    
    def __init__(self):
        self.metrics = {
            "checkouts": 0,
            "checkins": 0,
            "connects": 0,
            "checkout_times": [],
            "overflow_triggered": 0,
            "timeouts": 0,
            "max_checked_out": 0,
            "samples": [],
        }
        self.start_time = None
        
    def register_pool_listeners(self, pool: Pool):
        """Register SQLAlchemy pool event listeners."""
        
        @event.listens_for(pool, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Track connection checkouts."""
            self.metrics["checkouts"] += 1
            connection_record.checkout_time = time.time()
            
        @event.listens_for(pool, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """Track connection checkins and checkout duration."""
            self.metrics["checkins"] += 1
            if hasattr(connection_record, 'checkout_time'):
                duration = time.time() - connection_record.checkout_time
                self.metrics["checkout_times"].append(duration)
                
        @event.listens_for(pool, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Track new connections created."""
            self.metrics["connects"] += 1
    
    async def sample_pool_status(self, db_service: DatabaseService):
        """Sample current pool status."""
        try:
            pool = db_service.engine.pool
            
            sample = {
                "timestamp": datetime.utcnow().isoformat(),
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.overflow(),
                "total_checked_out": pool.size() - pool.checkedin() + pool.overflow(),
            }
            
            # Track max checked out
            if sample["total_checked_out"] > self.metrics["max_checked_out"]:
                self.metrics["max_checked_out"] = sample["total_checked_out"]
            
            # Track overflow usage
            if sample["checked_out"] > 0:
                self.metrics["overflow_triggered"] += 1
            
            self.metrics["samples"].append(sample)
            
            return sample
        except Exception as e:
            print(f"Error sampling pool: {e}")
            return None
    
    async def monitor_loop(self, db_service: DatabaseService, duration_seconds: int = 300):
        """Monitor pool continuously during load test."""
        self.start_time = time.time()
        end_time = self.start_time + duration_seconds
        
        print(f"\n{'='*80}")
        print(f"Connection Pool Monitoring Started")
        print(f"{'='*80}")
        print(f"Pool Size: {settings.database_pool_size}")
        print(f"Max Overflow: {settings.database_max_overflow}")
        print(f"Total Capacity: {settings.database_pool_size + settings.database_max_overflow}")
        print(f"Monitoring Duration: {duration_seconds}s")
        print(f"{'='*80}\n")
        
        interval = 5  # Sample every 5 seconds
        
        while time.time() < end_time:
            sample = await self.sample_pool_status(db_service)
            
            if sample:
                elapsed = int(time.time() - self.start_time)
                print(
                    f"[{elapsed:03d}s] "
                    f"Pool: {sample['size']} | "
                    f"In Use: {sample['total_checked_out']} | "
                    f"Available: {sample['checked_in']} | "
                    f"Overflow: {sample['checked_out']}"
                )
            
            await asyncio.sleep(interval)
        
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate final monitoring report."""
        checkout_times = self.metrics["checkout_times"]
        
        report = {
            "test_duration_seconds": int(time.time() - self.start_time) if self.start_time else 0,
            "pool_config": {
                "pool_size": settings.database_pool_size,
                "max_overflow": settings.database_max_overflow,
                "total_capacity": settings.database_pool_size + settings.database_max_overflow,
                "pool_timeout": settings.database_pool_timeout,
            },
            "connection_activity": {
                "total_checkouts": self.metrics["checkouts"],
                "total_checkins": self.metrics["checkins"],
                "new_connections_created": self.metrics["connects"],
                "max_concurrent_connections": self.metrics["max_checked_out"],
            },
            "checkout_performance": {
                "total_samples": len(checkout_times),
                "avg_checkout_time_ms": round(sum(checkout_times) / len(checkout_times) * 1000, 2) if checkout_times else 0,
                "min_checkout_time_ms": round(min(checkout_times) * 1000, 2) if checkout_times else 0,
                "max_checkout_time_ms": round(max(checkout_times) * 1000, 2) if checkout_times else 0,
            },
            "overflow_usage": {
                "samples_with_overflow": self.metrics["overflow_triggered"],
                "overflow_percentage": round(
                    (self.metrics["overflow_triggered"] / len(self.metrics["samples"]) * 100)
                    if self.metrics["samples"] else 0,
                    2
                ),
            },
            "pool_utilization": {
                "avg_connections_used": round(
                    sum(s["total_checked_out"] for s in self.metrics["samples"]) / len(self.metrics["samples"])
                    if self.metrics["samples"] else 0,
                    2
                ),
                "peak_connections_used": self.metrics["max_checked_out"],
                "utilization_percentage": round(
                    (self.metrics["max_checked_out"] / (settings.database_pool_size + settings.database_max_overflow) * 100)
                    if settings.database_pool_size + settings.database_max_overflow > 0 else 0,
                    2
                ),
            },
            "samples": self.metrics["samples"],
        }
        
        return report


async def test_connection_pool_under_load():
    """Test connection pool behavior under concurrent load."""
    
    db_service = DatabaseService()
    await db_service.initialize()
    
    monitor = PoolMonitor()
    
    # Register pool event listeners
    monitor.register_pool_listeners(db_service.engine.pool)
    
    # Simulate concurrent queries
    async def simulate_query():
        """Simulate a database query."""
        async with db_service.get_session() as session:
            await session.execute(text("SELECT 1"))
            await asyncio.sleep(0.1)  # Hold connection briefly
    
    print("\n🔍 Starting connection pool stress test...")
    print("   Simulating 100 concurrent connections...")
    
    # Start monitoring in background
    monitor_task = asyncio.create_task(
        monitor.monitor_loop(db_service, duration_seconds=60)
    )
    
    # Wait a moment for monitoring to start
    await asyncio.sleep(2)
    
    # Create 100 concurrent tasks
    tasks = [simulate_query() for _ in range(100)]
    await asyncio.gather(*tasks)
    
    print("\n   ✅ Concurrent query test complete, waiting for monitoring...")
    
    # Wait for monitoring to complete
    report = await monitor_task
    
    await db_service.close()
    
    return report


def print_report(report: Dict[str, Any]):
    """Print formatted monitoring report."""
    
    print(f"\n{'='*80}")
    print(f"CONNECTION POOL MONITORING REPORT")
    print(f"{'='*80}\n")
    
    print(f"📊 Pool Configuration:")
    print(f"  • Pool Size: {report['pool_config']['pool_size']} (core connections)")
    print(f"  • Max Overflow: {report['pool_config']['max_overflow']} (additional connections)")
    print(f"  • Total Capacity: {report['pool_config']['total_capacity']} connections")
    print(f"  • Pool Timeout: {report['pool_config']['pool_timeout']} seconds\n")
    
    print(f"🔄 Connection Activity:")
    print(f"  • Total Checkouts: {report['connection_activity']['total_checkouts']}")
    print(f"  • Total Checkins: {report['connection_activity']['total_checkins']}")
    print(f"  • New Connections Created: {report['connection_activity']['new_connections_created']}")
    print(f"  • Max Concurrent: {report['connection_activity']['max_concurrent_connections']}/{report['pool_config']['total_capacity']}\n")
    
    print(f"⚡ Checkout Performance:")
    print(f"  • Avg Checkout Time: {report['checkout_performance']['avg_checkout_time_ms']}ms")
    print(f"  • Min Checkout Time: {report['checkout_performance']['min_checkout_time_ms']}ms")
    print(f"  • Max Checkout Time: {report['checkout_performance']['max_checkout_time_ms']}ms\n")
    
    print(f"📈 Overflow Usage:")
    print(f"  • Samples with Overflow: {report['overflow_usage']['samples_with_overflow']}")
    print(f"  • Overflow Percentage: {report['overflow_usage']['overflow_percentage']}%\n")
    
    print(f"📊 Pool Utilization:")
    print(f"  • Avg Connections Used: {report['pool_utilization']['avg_connections_used']}")
    print(f"  • Peak Connections Used: {report['pool_utilization']['peak_connections_used']}")
    print(f"  • Peak Utilization: {report['pool_utilization']['utilization_percentage']}%\n")
    
    # Assessment
    print(f"{'='*80}")
    print(f"✅ ASSESSMENT")
    print(f"{'='*80}\n")
    
    checks = []
    
    # Check 1: No overflow needed
    if report['overflow_usage']['overflow_percentage'] == 0:
        checks.append("✅ Pool size adequate - no overflow needed")
    elif report['overflow_usage']['overflow_percentage'] < 20:
        checks.append("✅ Minimal overflow usage (<20%) - pool size acceptable")
    else:
        checks.append(f"⚠️  High overflow usage ({report['overflow_usage']['overflow_percentage']}%) - consider increasing pool_size")
    
    # Check 2: Utilization not maxed out
    if report['pool_utilization']['utilization_percentage'] < 80:
        checks.append("✅ Pool capacity sufficient (utilization <80%)")
    else:
        checks.append(f"⚠️  High utilization ({report['pool_utilization']['utilization_percentage']}%) - consider increasing max_overflow")
    
    # Check 3: Fast checkouts
    if report['checkout_performance']['avg_checkout_time_ms'] < 10:
        checks.append("✅ Fast connection checkouts (<10ms average)")
    else:
        checks.append(f"⚠️  Slow connection checkouts ({report['checkout_performance']['avg_checkout_time_ms']}ms) - pool may be congested")
    
    # Check 4: Few new connections
    if report['connection_activity']['new_connections_created'] <= report['pool_config']['pool_size']:
        checks.append("✅ Connection reuse optimal - minimal new connections")
    else:
        checks.append(f"ℹ️  Created {report['connection_activity']['new_connections_created']} connections (expected for initial ramp-up)")
    
    for check in checks:
        print(f"  {check}")
    
    print(f"\n{'='*80}\n")


async def main():
    """Main entry point."""
    try:
        report = await test_connection_pool_under_load()
        print_report(report)
        
        # Write JSON report
        import json
        report_path = "tests/performance/reports/connection_pool_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Full report saved to: {report_path}")
        
    except Exception as e:
        print(f"\n❌ Error during pool monitoring: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
