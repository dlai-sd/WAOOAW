"""
Load Testing Framework

Provides base infrastructure for load and performance testing.
"""
import pytest
import time
import asyncio
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Callable, Any
from dataclasses import dataclass, field


@dataclass
class LoadTestResult:
    """Results from a load test run."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_duration: float
    min_response_time: float
    max_response_time: float
    mean_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    response_times: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        return f"""
Load Test Results:
==================
Total Requests: {self.total_requests}
Successful: {self.successful_requests}
Failed: {self.failed_requests}
Duration: {self.total_duration:.2f}s
RPS: {self.requests_per_second:.2f}

Response Times:
  Min: {self.min_response_time*1000:.2f}ms
  Mean: {self.mean_response_time*1000:.2f}ms
  Median: {self.median_response_time*1000:.2f}ms
  P95: {self.p95_response_time*1000:.2f}ms
  P99: {self.p99_response_time*1000:.2f}ms
  Max: {self.max_response_time*1000:.2f}ms
"""


class LoadTestRunner:
    """Framework for running load tests."""
    
    def __init__(self, max_workers: int = 10):
        """Initialize load test runner.
        
        Args:
            max_workers: Maximum number of concurrent workers
        """
        self.max_workers = max_workers
    
    def run_load_test(
        self,
        target_function: Callable,
        num_requests: int,
        concurrent_users: int = 1,
        **kwargs
    ) -> LoadTestResult:
        """Run a synchronous load test.
        
        Args:
            target_function: Function to test
            num_requests: Total number of requests to make
            concurrent_users: Number of concurrent users
            **kwargs: Arguments to pass to target function
            
        Returns:
            LoadTestResult with performance metrics
        """
        response_times = []
        errors = []
        successful = 0
        failed = 0
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            for i in range(num_requests):
                future = executor.submit(self._execute_request, target_function, kwargs)
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    duration = future.result()
                    response_times.append(duration)
                    successful += 1
                except Exception as e:
                    errors.append(str(e))
                    failed += 1
        
        total_duration = time.time() - start_time
        
        return self._build_result(
            total_requests=num_requests,
            successful_requests=successful,
            failed_requests=failed,
            total_duration=total_duration,
            response_times=response_times,
            errors=errors
        )
    
    async def run_async_load_test(
        self,
        target_function: Callable,
        num_requests: int,
        concurrent_users: int = 1,
        **kwargs
    ) -> LoadTestResult:
        """Run an asynchronous load test.
        
        Args:
            target_function: Async function to test
            num_requests: Total number of requests to make
            concurrent_users: Number of concurrent users
            **kwargs: Arguments to pass to target function
            
        Returns:
            LoadTestResult with performance metrics
        """
        response_times = []
        errors = []
        successful = 0
        failed = 0
        
        start_time = time.time()
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrent_users)
        
        async def bounded_request():
            async with semaphore:
                return await self._execute_async_request(target_function, kwargs)
        
        tasks = [bounded_request() for _ in range(num_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
                failed += 1
            else:
                response_times.append(result)
                successful += 1
        
        total_duration = time.time() - start_time
        
        return self._build_result(
            total_requests=num_requests,
            successful_requests=successful,
            failed_requests=failed,
            total_duration=total_duration,
            response_times=response_times,
            errors=errors
        )
    
    def _execute_request(self, func: Callable, kwargs: Dict) -> float:
        """Execute a single request and measure time."""
        start = time.time()
        func(**kwargs)
        return time.time() - start
    
    async def _execute_async_request(self, func: Callable, kwargs: Dict) -> float:
        """Execute a single async request and measure time."""
        start = time.time()
        await func(**kwargs)
        return time.time() - start
    
    def _build_result(
        self,
        total_requests: int,
        successful_requests: int,
        failed_requests: int,
        total_duration: float,
        response_times: List[float],
        errors: List[str]
    ) -> LoadTestResult:
        """Build LoadTestResult from raw data."""
        if not response_times:
            response_times = [0.0]
        
        sorted_times = sorted(response_times)
        
        return LoadTestResult(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_duration=total_duration,
            min_response_time=min(response_times),
            max_response_time=max(response_times),
            mean_response_time=statistics.mean(response_times),
            median_response_time=statistics.median(response_times),
            p95_response_time=sorted_times[int(len(sorted_times) * 0.95)],
            p99_response_time=sorted_times[int(len(sorted_times) * 0.99)],
            requests_per_second=successful_requests / total_duration if total_duration > 0 else 0,
            response_times=response_times,
            errors=errors
        )


@pytest.fixture
def load_test_runner():
    """Provide a load test runner."""
    return LoadTestRunner(max_workers=20)


class TestLoadTestFramework:
    """Test the load testing framework itself."""
    
    def test_single_request(self, load_test_runner):
        """Test single request execution."""
        def simple_task(value: int = 1):
            time.sleep(0.01)
            return value * 2
        
        result = load_test_runner.run_load_test(
            target_function=simple_task,
            num_requests=1,
            concurrent_users=1,
            value=5
        )
        
        assert result.total_requests == 1
        assert result.successful_requests == 1
        assert result.failed_requests == 0
        assert result.mean_response_time >= 0.01
    
    def test_concurrent_requests(self, load_test_runner):
        """Test concurrent request execution."""
        def simple_task():
            time.sleep(0.05)
        
        result = load_test_runner.run_load_test(
            target_function=simple_task,
            num_requests=10,
            concurrent_users=5
        )
        
        assert result.total_requests == 10
        assert result.successful_requests == 10
        assert result.failed_requests == 0
        # With 5 concurrent users, should be faster than sequential
        assert result.total_duration < 0.5  # Less than 10 * 0.05
    
    def test_error_handling(self, load_test_runner):
        """Test error handling in load tests."""
        def failing_task():
            raise ValueError("Intentional error")
        
        result = load_test_runner.run_load_test(
            target_function=failing_task,
            num_requests=5,
            concurrent_users=2
        )
        
        assert result.total_requests == 5
        assert result.failed_requests == 5
        assert result.successful_requests == 0
        assert len(result.errors) == 5
    
    @pytest.mark.asyncio
    async def test_async_load_test(self, load_test_runner):
        """Test async load testing."""
        async def async_task():
            await asyncio.sleep(0.01)
        
        result = await load_test_runner.run_async_load_test(
            target_function=async_task,
            num_requests=20,
            concurrent_users=10
        )
        
        assert result.total_requests == 20
        assert result.successful_requests == 20
        assert result.requests_per_second > 0
    
    def test_performance_metrics(self, load_test_runner):
        """Test that all performance metrics are calculated."""
        import random
        
        def variable_task():
            time.sleep(random.uniform(0.01, 0.05))
        
        result = load_test_runner.run_load_test(
            target_function=variable_task,
            num_requests=50,
            concurrent_users=10
        )
        
        assert result.min_response_time > 0
        assert result.max_response_time > result.min_response_time
        assert result.mean_response_time > 0
        assert result.median_response_time > 0
        assert result.p95_response_time > 0
        assert result.p99_response_time > 0
        assert result.requests_per_second > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
