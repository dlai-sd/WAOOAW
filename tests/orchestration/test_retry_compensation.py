"""
Tests for Retry Policies and Compensation

Validates retry mechanisms with exponential backoff and saga pattern
for distributed transaction compensation.
"""

import asyncio
import pytest
import time

from waooaw.orchestration import (
    RetryPolicy,
    RetryConfig,
    RetryStrategy,
    MaxRetriesExceededError,
    RETRY_POLICY_STANDARD,
    Saga,
    SagaBuilder,
    SagaState,
    CompensationError,
)


@pytest.mark.asyncio
class TestRetryConfig:
    """Test RetryConfig validation"""

    def test_create_config(self):
        """Should create config with defaults"""
        config = RetryConfig()

        assert config.max_retries == 3
        assert config.strategy == RetryStrategy.EXPONENTIAL
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter == 0.1

    def test_config_validation(self):
        """Should validate config parameters"""
        # Negative max_retries
        with pytest.raises(ValueError, match="max_retries"):
            RetryConfig(max_retries=-1)

        # Negative base_delay
        with pytest.raises(ValueError, match="base_delay"):
            RetryConfig(base_delay=-1.0)

        # max_delay < base_delay
        with pytest.raises(ValueError, match="max_delay"):
            RetryConfig(base_delay=10.0, max_delay=5.0)

        # exponential_base < 1
        with pytest.raises(ValueError, match="exponential_base"):
            RetryConfig(exponential_base=0.5)

        # Invalid jitter
        with pytest.raises(ValueError, match="jitter"):
            RetryConfig(jitter=1.5)


@pytest.mark.asyncio
class TestRetryPolicy:
    """Test RetryPolicy operations"""

    async def test_create_policy(self):
        """Should create policy with config"""
        config = RetryConfig(max_retries=5)
        policy = RetryPolicy(config)

        assert policy.config.max_retries == 5

    async def test_calculate_delay_fixed(self):
        """Should calculate fixed delay"""
        config = RetryConfig(
            strategy=RetryStrategy.FIXED, base_delay=2.0, jitter=0.0
        )
        policy = RetryPolicy(config)

        # All delays should be same
        delays = [policy.calculate_delay(i) for i in range(5)]
        assert all(d == 2.0 for d in delays)

    async def test_calculate_delay_exponential(self):
        """Should calculate exponential backoff"""
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL,
            base_delay=1.0,
            exponential_base=2.0,
            max_delay=100.0,
            jitter=0.0,
        )
        policy = RetryPolicy(config)

        # Delays should double each time
        assert policy.calculate_delay(0) == 1.0  # 1 * 2^0
        assert policy.calculate_delay(1) == 2.0  # 1 * 2^1
        assert policy.calculate_delay(2) == 4.0  # 1 * 2^2
        assert policy.calculate_delay(3) == 8.0  # 1 * 2^3

    async def test_calculate_delay_linear(self):
        """Should calculate linear backoff"""
        config = RetryConfig(
            strategy=RetryStrategy.LINEAR, base_delay=2.0, jitter=0.0
        )
        policy = RetryPolicy(config)

        # Delays should increase linearly
        assert policy.calculate_delay(0) == 2.0  # 2 * 1
        assert policy.calculate_delay(1) == 4.0  # 2 * 2
        assert policy.calculate_delay(2) == 6.0  # 2 * 3

    async def test_calculate_delay_max_cap(self):
        """Should cap delay at max_delay"""
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL,
            base_delay=1.0,
            max_delay=5.0,
            exponential_base=2.0,
            jitter=0.0,
        )
        policy = RetryPolicy(config)

        # Large attempt should be capped
        delay = policy.calculate_delay(10)  # Would be 1024 without cap
        assert delay == 5.0

    async def test_calculate_delay_with_jitter(self):
        """Should add jitter to delay"""
        config = RetryConfig(
            strategy=RetryStrategy.FIXED, base_delay=10.0, jitter=0.5
        )
        policy = RetryPolicy(config)

        # Delays should vary due to jitter
        delays = [policy.calculate_delay(0) for _ in range(10)]
        # Should have some variation (not all same)
        assert len(set(delays)) > 1
        # All should be within jitter range (5.0 to 15.0)
        assert all(5.0 <= d <= 15.0 for d in delays)

    async def test_should_retry_within_limit(self):
        """Should retry within max attempts"""
        config = RetryConfig(max_retries=3)
        policy = RetryPolicy(config)

        error = ValueError("Test error")
        assert policy.should_retry(error, 0) is True
        assert policy.should_retry(error, 1) is True
        assert policy.should_retry(error, 3) is True

    async def test_should_retry_exceeds_limit(self):
        """Should not retry after max attempts"""
        config = RetryConfig(max_retries=3)
        policy = RetryPolicy(config)

        error = ValueError("Test error")
        assert policy.should_retry(error, 4) is False
        assert policy.should_retry(error, 10) is False

    async def test_should_retry_with_exception_filter(self):
        """Should only retry specific exceptions"""
        config = RetryConfig(max_retries=3, retry_on=(ValueError, TypeError))
        policy = RetryPolicy(config)

        # Should retry these
        assert policy.should_retry(ValueError("test"), 1) is True
        assert policy.should_retry(TypeError("test"), 1) is True

        # Should not retry this
        assert policy.should_retry(RuntimeError("test"), 1) is False

    async def test_execute_success_first_try(self):
        """Should succeed on first try without retry"""
        policy = RetryPolicy(RetryConfig(max_retries=3))

        async def successful_func():
            return "success"

        result = await policy.execute(successful_func)
        assert result == "success"

    async def test_execute_success_after_retries(self):
        """Should succeed after retries"""
        policy = RetryPolicy(
            RetryConfig(max_retries=3, base_delay=0.1, jitter=0.0)
        )

        attempt_count = {"value": 0}

        async def flaky_func():
            attempt_count["value"] += 1
            if attempt_count["value"] < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = await policy.execute(flaky_func)
        assert result == "success"
        assert attempt_count["value"] == 3

    async def test_execute_max_retries_exceeded(self):
        """Should raise MaxRetriesExceededError after max attempts"""
        policy = RetryPolicy(
            RetryConfig(max_retries=2, base_delay=0.05, jitter=0.0)
        )

        async def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(MaxRetriesExceededError) as exc_info:
            await policy.execute(always_fails)

        assert exc_info.value.attempts == 3  # 0, 1, 2 (max_retries + 1)
        assert isinstance(exc_info.value.last_error, ValueError)

    async def test_execute_with_args_kwargs(self):
        """Should pass args and kwargs to function"""
        policy = RetryPolicy(RetryConfig(max_retries=1))

        async def func_with_args(x, y, z=10):
            return x + y + z

        result = await policy.execute(func_with_args, 5, 10, z=15)
        assert result == 30

    async def test_execute_with_context(self):
        """Should return result and retry context"""
        policy = RetryPolicy(
            RetryConfig(max_retries=3, base_delay=0.05, jitter=0.0)
        )

        attempt_count = {"value": 0}

        async def flaky_func():
            attempt_count["value"] += 1
            if attempt_count["value"] < 2:
                raise ValueError("Temporary failure")
            return "success"

        result, context = await policy.execute_with_context(flaky_func)

        assert result == "success"
        assert context.attempt == 1  # 0-indexed
        assert len(context.errors) == 1
        assert context.total_delay > 0

    async def test_predefined_policies(self):
        """Should have predefined policy configurations"""
        # Just verify they exist and are valid
        assert RETRY_POLICY_STANDARD.max_retries == 3
        assert RETRY_POLICY_STANDARD.strategy == RetryStrategy.EXPONENTIAL


@pytest.mark.asyncio
class TestSaga:
    """Test Saga pattern"""

    async def test_create_saga(self):
        """Should create saga with ID"""
        saga = Saga("test-saga")

        assert saga.saga_id == "test-saga"
        assert saga.get_state() == SagaState.PENDING
        assert len(saga.get_steps()) == 0

    async def test_add_step(self):
        """Should add steps to saga"""
        saga = Saga("test-saga")

        async def action1():
            return "result1"

        async def compensation1(result):
            pass

        saga.add_step("step1", action1, compensation1)

        steps = saga.get_steps()
        assert len(steps) == 1
        assert steps[0].name == "step1"

    async def test_execute_all_steps_success(self):
        """Should execute all steps successfully"""
        saga = Saga("test-saga")

        results = []

        async def step1():
            results.append("step1")
            return "result1"

        async def step2():
            results.append("step2")
            return "result2"

        saga.add_step("step1", step1)
        saga.add_step("step2", step2)

        execution = await saga.execute()

        assert execution.state == SagaState.COMPLETED
        assert execution.completed_steps == 2
        assert execution.compensated_steps == 0
        assert results == ["step1", "step2"]

    async def test_execute_with_compensation_on_failure(self):
        """Should compensate completed steps on failure"""
        saga = Saga("test-saga")

        compensation_log = []

        async def step1():
            return "result1"

        async def compensate1(result):
            compensation_log.append(f"compensate1-{result}")

        async def step2():
            return "result2"

        async def compensate2(result):
            compensation_log.append(f"compensate2-{result}")

        async def step3():
            raise ValueError("Step 3 fails!")

        saga.add_step("step1", step1, compensate1)
        saga.add_step("step2", step2, compensate2)
        saga.add_step("step3", step3)

        execution = await saga.execute()

        # Should be compensated
        assert execution.state == SagaState.COMPENSATED
        assert execution.completed_steps == 2  # step1 and step2
        assert execution.compensated_steps == 2
        # Compensation in reverse order
        assert compensation_log == ["compensate2-result2", "compensate1-result1"]

    async def test_execute_without_compensation_handlers(self):
        """Should handle steps without compensation"""
        saga = Saga("test-saga")

        async def step1():
            return "result1"

        async def step2():
            raise ValueError("Fails")

        saga.add_step("step1", step1)  # No compensation
        saga.add_step("step2", step2)

        execution = await saga.execute()

        # Should be compensated (even with no handlers)
        assert execution.state == SagaState.COMPENSATED
        assert execution.completed_steps == 1
        assert execution.compensated_steps == 1  # step1 auto-compensated

    async def test_compensation_failure(self):
        """Should raise CompensationError when compensation fails"""
        saga = Saga("test-saga")

        async def step1():
            return "result1"

        async def compensate1(result):
            raise RuntimeError("Compensation failed!")

        async def step2():
            raise ValueError("Step 2 fails")

        saga.add_step("step1", step1, compensate1)
        saga.add_step("step2", step2)

        with pytest.raises(CompensationError, match="Compensation failed"):
            await saga.execute()

    async def test_saga_execution_record(self):
        """Should track execution details"""
        saga = Saga("test-saga")

        async def step1():
            await asyncio.sleep(0.05)
            return "result1"

        saga.add_step("step1", step1)

        execution = await saga.execute()

        assert execution.saga_id == "test-saga"
        assert execution.total_steps == 1
        assert execution.started_at is not None
        assert execution.completed_at is not None
        assert execution.total_execution_time > 0
        assert execution.is_terminal is True


@pytest.mark.asyncio
class TestSagaBuilder:
    """Test SagaBuilder fluent interface"""

    async def test_build_saga(self):
        """Should build saga with fluent interface"""
        async def action1():
            return "result1"

        async def compensate1(result):
            pass

        async def action2():
            return "result2"

        saga = (
            SagaBuilder("builder-saga")
            .step("step1", action1, compensate1)
            .step("step2", action2)
            .build()
        )

        assert saga.saga_id == "builder-saga"
        assert len(saga.get_steps()) == 2

    async def test_execute_built_saga(self):
        """Should execute saga built with builder"""
        results = []

        async def step1():
            results.append("step1")
            return "result1"

        async def step2():
            results.append("step2")
            return "result2"

        saga = (
            SagaBuilder("builder-saga")
            .step("step1", step1)
            .step("step2", step2)
            .build()
        )

        execution = await saga.execute()

        assert execution.state == SagaState.COMPLETED
        assert results == ["step1", "step2"]


@pytest.mark.asyncio
class TestIntegration:
    """Test retry policy with saga pattern"""

    async def test_retry_policy_with_saga(self):
        """Should use retry policy within saga steps"""
        retry_policy = RetryPolicy(
            RetryConfig(max_retries=2, base_delay=0.05, jitter=0.0)
        )

        attempt_count = {"value": 0}

        async def flaky_step():
            attempt_count["value"] += 1
            if attempt_count["value"] < 2:
                raise ValueError("Temporary failure")
            return "success"

        async def step_with_retry():
            return await retry_policy.execute(flaky_step)

        saga = SagaBuilder("retry-saga").step("flaky", step_with_retry).build()

        execution = await saga.execute()

        assert execution.state == SagaState.COMPLETED
        assert attempt_count["value"] == 2  # Retried once
