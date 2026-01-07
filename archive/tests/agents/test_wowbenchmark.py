"""
Tests for WowBenchmark Agent

Tests Stories 0.2.1-0.2.2 (initial implementation):
- CompetitorCollector (output collection, caching, cost tracking)
- ComparisonEngine (multi-dimensional comparison)
- WowBenchmark (main agent orchestration)
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from waooaw.agents.wowbenchmark import (
    WowBenchmark,
    CompetitorCollector,
    ComparisonEngine,
    Scenario,
    CompetitorType,
    CompetitorOutput,
    BenchmarkComparison
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_scenario():
    """Sample test scenario"""
    return Scenario(
        scenario_id="test_001",
        content_type="blog_post",
        industry="healthcare",
        prompt="Write a blog post about telemedicine benefits",
        constraints={"max_length": 500, "tone": "professional"},
        requirements={"include_cta": True, "target_audience": "patients"}
    )


@pytest.fixture
def collector():
    """CompetitorCollector instance"""
    return CompetitorCollector(cache_ttl_days=90, enable_caching=True)


@pytest.fixture
def comparison_engine():
    """ComparisonEngine instance"""
    return ComparisonEngine()


@pytest.fixture
def wowbenchmark():
    """WowBenchmark agent instance"""
    return WowBenchmark()


# =============================================================================
# Story 0.2.1: CompetitorCollector Tests
# =============================================================================

@pytest.mark.asyncio
async def test_collect_single_competitor(collector, sample_scenario):
    """Test collecting output from a single competitor"""
    output = await collector.collect_output(
        CompetitorType.JASPER,
        sample_scenario
    )
    
    assert output is not None
    assert output.competitor == CompetitorType.JASPER
    assert output.scenario_id == sample_scenario.scenario_id
    assert len(output.output_text) > 0
    assert output.collection_method == "api"
    assert output.api_cost > 0
    assert output.generation_time > 0
    assert output.cache_key is not None


@pytest.mark.asyncio
async def test_collect_all_competitors(collector, sample_scenario):
    """Test collecting from all competitors"""
    outputs = await collector.collect_all_outputs(sample_scenario)
    
    assert len(outputs) == 3  # Jasper, Copy.ai, OpenAI
    assert CompetitorType.JASPER in outputs
    assert CompetitorType.COPYAI in outputs
    assert CompetitorType.OPENAI in outputs
    
    for competitor, output in outputs.items():
        if output:
            assert output.competitor == competitor
            assert len(output.output_text) > 0


@pytest.mark.asyncio
async def test_caching_works(collector, sample_scenario):
    """Test that caching avoids redundant API calls"""
    # First call - should hit API
    output1 = await collector.collect_output(
        CompetitorType.JASPER,
        sample_scenario
    )
    cost1 = collector.get_cost_summary()[CompetitorType.JASPER.value]
    
    # Second call - should use cache
    output2 = await collector.collect_output(
        CompetitorType.JASPER,
        sample_scenario
    )
    cost2 = collector.get_cost_summary()[CompetitorType.JASPER.value]
    
    assert output1.output_text == output2.output_text
    assert cost1 == cost2  # No additional cost
    assert output2.cache_key == output1.cache_key


@pytest.mark.asyncio
async def test_force_refresh_bypasses_cache(collector, sample_scenario):
    """Test force_refresh parameter bypasses cache"""
    # First call
    await collector.collect_output(CompetitorType.JASPER, sample_scenario)
    cost1 = collector.get_cost_summary()[CompetitorType.JASPER.value]
    
    # Second call with force_refresh
    await collector.collect_output(
        CompetitorType.JASPER,
        sample_scenario,
        force_refresh=True
    )
    cost2 = collector.get_cost_summary()[CompetitorType.JASPER.value]
    
    assert cost2 > cost1  # Additional cost incurred


def test_manual_submission(collector, sample_scenario):
    """Test manual output submission"""
    manual_output = collector.submit_manual_output(
        CompetitorType.HUMAN_FREELANCER,
        sample_scenario,
        "This is manually submitted content from a freelancer.",
        metadata={"freelancer_id": "FL123", "cost": 50.0}
    )
    
    assert manual_output.competitor == CompetitorType.HUMAN_FREELANCER
    assert manual_output.collection_method == "manual"
    assert manual_output.api_cost == 0.0
    assert manual_output.metadata["freelancer_id"] == "FL123"


def test_cost_tracking(collector, sample_scenario):
    """Test cost tracking across multiple calls"""
    async def run_test():
        # Collect from multiple competitors
        await collector.collect_output(CompetitorType.JASPER, sample_scenario)
        await collector.collect_output(CompetitorType.COPYAI, sample_scenario)
        await collector.collect_output(CompetitorType.OPENAI, sample_scenario)
        
        costs = collector.get_cost_summary()
        
        assert costs[CompetitorType.JASPER.value] > 0
        assert costs[CompetitorType.COPYAI.value] > 0
        assert costs[CompetitorType.OPENAI.value] > 0
    
    asyncio.run(run_test())


def test_cache_stats(collector, sample_scenario):
    """Test cache statistics"""
    async def run_test():
        # Add some outputs to cache
        await collector.collect_output(CompetitorType.JASPER, sample_scenario)
        await collector.collect_output(CompetitorType.COPYAI, sample_scenario)
        
        stats = collector.get_cache_stats()
        
        assert stats["total_cached"] >= 2
        assert stats["valid_cached"] >= 2
        assert "cache_hit_potential" in stats
    
    asyncio.run(run_test())


def test_cache_expiry():
    """Test cache expiry based on TTL"""
    collector = CompetitorCollector(cache_ttl_days=1)
    
    # Create expired output
    old_output = CompetitorOutput(
        competitor=CompetitorType.JASPER,
        scenario_id="test",
        output_text="old content",
        collected_at=datetime.now() - timedelta(days=2),
        collection_method="api"
    )
    
    assert not collector._is_cache_valid(old_output)
    
    # Create fresh output
    fresh_output = CompetitorOutput(
        competitor=CompetitorType.JASPER,
        scenario_id="test",
        output_text="fresh content",
        collected_at=datetime.now(),
        collection_method="api"
    )
    
    assert collector._is_cache_valid(fresh_output)


# =============================================================================
# Story 0.2.2: ComparisonEngine Tests
# =============================================================================

@pytest.mark.asyncio
async def test_compare_outputs(comparison_engine, sample_scenario):
    """Test comparing WAOOAW vs competitor output"""
    waooaw_output = "High-quality blog post about telemedicine with CTA..."
    competitor_output = CompetitorOutput(
        competitor=CompetitorType.JASPER,
        scenario_id=sample_scenario.scenario_id,
        output_text="Competitor blog post about telemedicine...",
        collected_at=datetime.now(),
        collection_method="api"
    )
    
    comparison = await comparison_engine.compare_outputs(
        waooaw_agent="content_agent",
        waooaw_output=waooaw_output,
        competitor=CompetitorType.JASPER,
        competitor_output=competitor_output,
        scenario=sample_scenario
    )
    
    assert comparison.scenario_id == sample_scenario.scenario_id
    assert comparison.waooaw_agent == "content_agent"
    assert comparison.competitor == CompetitorType.JASPER
    assert 0 <= comparison.waooaw_score <= 10
    assert 0 <= comparison.competitor_score <= 10
    assert comparison.winner in ["waooaw", "competitor", "tie"]
    assert len(comparison.dimensions) == 4  # 4 dimensions evaluated


@pytest.mark.asyncio
async def test_dimension_by_dimension_comparison(comparison_engine, sample_scenario):
    """Test that all dimensions are compared"""
    waooaw_output = "Test output"
    competitor_output = CompetitorOutput(
        competitor=CompetitorType.COPYAI,
        scenario_id=sample_scenario.scenario_id,
        output_text="Competitor test output",
        collected_at=datetime.now(),
        collection_method="api"
    )
    
    comparison = await comparison_engine.compare_outputs(
        waooaw_agent="test_agent",
        waooaw_output=waooaw_output,
        competitor=CompetitorType.COPYAI,
        competitor_output=competitor_output,
        scenario=sample_scenario
    )
    
    # Check all dimensions have scores
    expected_dimensions = ["structural", "quality", "domain_expertise", "fit_for_purpose"]
    for dim in expected_dimensions:
        assert dim in comparison.dimensions
        assert "waooaw" in comparison.dimensions[dim]
        assert "competitor" in comparison.dimensions[dim]
        assert 0 <= comparison.dimensions[dim]["waooaw"] <= 10
        assert 0 <= comparison.dimensions[dim]["competitor"] <= 10


@pytest.mark.asyncio
async def test_winner_determination(comparison_engine, sample_scenario):
    """Test winner is correctly determined"""
    waooaw_output = "Excellent quality output"
    competitor_output = CompetitorOutput(
        competitor=CompetitorType.OPENAI,
        scenario_id=sample_scenario.scenario_id,
        output_text="Good output",
        collected_at=datetime.now(),
        collection_method="api"
    )
    
    comparison = await comparison_engine.compare_outputs(
        waooaw_agent="content_agent",
        waooaw_output=waooaw_output,
        competitor=CompetitorType.OPENAI,
        competitor_output=competitor_output,
        scenario=sample_scenario
    )
    
    # With mock scoring, WAOOAW should typically win
    if comparison.waooaw_score > comparison.competitor_score:
        assert comparison.winner == "waooaw"
        assert comparison.win_margin > 0
    elif comparison.competitor_score > comparison.waooaw_score:
        assert comparison.winner == "competitor"
        assert comparison.win_margin > 0
    else:
        assert comparison.winner == "tie"
        assert comparison.win_margin == 0


# =============================================================================
# WowBenchmark Main Agent Tests
# =============================================================================

@pytest.mark.asyncio
async def test_benchmark_scenario(wowbenchmark, sample_scenario):
    """Test benchmarking a scenario"""
    waooaw_output = "WAOOAW generated blog post about telemedicine..."
    
    comparisons = await wowbenchmark.benchmark_scenario(
        waooaw_agent="content_agent",
        waooaw_output=waooaw_output,
        scenario=sample_scenario
    )
    
    assert len(comparisons) == 3  # Compared against 3 competitors
    assert all(isinstance(c, BenchmarkComparison) for c in comparisons)
    assert len(wowbenchmark.benchmarks) == 3  # Stored in agent


@pytest.mark.asyncio
async def test_benchmark_selective_competitors(wowbenchmark, sample_scenario):
    """Test benchmarking against specific competitors only"""
    waooaw_output = "Test output"
    
    comparisons = await wowbenchmark.benchmark_scenario(
        waooaw_agent="test_agent",
        waooaw_output=waooaw_output,
        scenario=sample_scenario,
        competitors=[CompetitorType.JASPER, CompetitorType.COPYAI]
    )
    
    assert len(comparisons) == 2
    competitors_tested = {c.competitor for c in comparisons}
    assert CompetitorType.JASPER in competitors_tested
    assert CompetitorType.COPYAI in competitors_tested
    assert CompetitorType.OPENAI not in competitors_tested


@pytest.mark.asyncio
async def test_win_rate_calculation(wowbenchmark, sample_scenario):
    """Test win rate calculation"""
    # Run multiple benchmarks
    for i in range(5):
        scenario = Scenario(
            scenario_id=f"test_{i}",
            content_type="blog_post",
            industry="healthcare",
            prompt=f"Test prompt {i}"
        )
        await wowbenchmark.benchmark_scenario(
            waooaw_agent="content_agent",
            waooaw_output=f"WAOOAW output {i}",
            scenario=scenario
        )
    
    win_rate = wowbenchmark.get_win_rate()
    
    assert 0 <= win_rate <= 100
    assert len(wowbenchmark.benchmarks) == 15  # 5 scenarios × 3 competitors


@pytest.mark.asyncio
async def test_win_rate_by_agent(wowbenchmark):
    """Test win rate filtered by agent"""
    # Benchmark with different agents
    scenario1 = Scenario(
        scenario_id="test_1",
        content_type="blog_post",
        industry="healthcare",
        prompt="Test 1"
    )
    scenario2 = Scenario(
        scenario_id="test_2",
        content_type="email",
        industry="marketing",
        prompt="Test 2"
    )
    
    await wowbenchmark.benchmark_scenario(
        waooaw_agent="agent_a",
        waooaw_output="Output A",
        scenario=scenario1
    )
    await wowbenchmark.benchmark_scenario(
        waooaw_agent="agent_b",
        waooaw_output="Output B",
        scenario=scenario2
    )
    
    win_rate_a = wowbenchmark.get_win_rate(agent="agent_a")
    win_rate_b = wowbenchmark.get_win_rate(agent="agent_b")
    
    assert 0 <= win_rate_a <= 100
    assert 0 <= win_rate_b <= 100


@pytest.mark.asyncio
async def test_summary_stats(wowbenchmark, sample_scenario):
    """Test summary statistics"""
    # Run some benchmarks
    await wowbenchmark.benchmark_scenario(
        waooaw_agent="content_agent",
        waooaw_output="Test output",
        scenario=sample_scenario
    )
    
    stats = wowbenchmark.get_summary_stats()
    
    assert "total_benchmarks" in stats
    assert "win_rate" in stats
    assert "avg_margin" in stats
    assert "by_competitor" in stats
    assert "cost_summary" in stats
    assert "cache_stats" in stats
    
    assert stats["total_benchmarks"] == 3
    assert 0 <= stats["win_rate"] <= 100


def test_empty_benchmarks_stats():
    """Test stats with no benchmarks"""
    agent = WowBenchmark()
    stats = agent.get_summary_stats()
    
    assert stats["total_benchmarks"] == 0
    assert stats["win_rate"] == 0.0
    assert stats["avg_margin"] == 0.0
    assert len(stats["by_competitor"]) == 0


# =============================================================================
# Integration Tests
# =============================================================================

@pytest.mark.asyncio
async def test_end_to_end_benchmark_flow(sample_scenario):
    """Test complete benchmarking flow"""
    agent = WowBenchmark()
    
    # Benchmark scenario
    comparisons = await agent.benchmark_scenario(
        waooaw_agent="content_agent",
        waooaw_output="High-quality WAOOAW blog post...",
        scenario=sample_scenario
    )
    
    # Verify results
    assert len(comparisons) == 3
    
    # Check win rate
    win_rate = agent.get_win_rate()
    assert win_rate >= 0
    
    # Check stats
    stats = agent.get_summary_stats()
    assert stats["total_benchmarks"] == 3
    
    # Check cost tracking
    costs = stats["cost_summary"]
    assert any(cost > 0 for cost in costs.values())
    
    # Check caching
    cache_stats = stats["cache_stats"]
    assert cache_stats["total_cached"] > 0


@pytest.mark.asyncio
async def test_performance_multiple_scenarios():
    """Test performance with multiple scenarios"""
    agent = WowBenchmark()
    
    # Create multiple scenarios
    scenarios = [
        Scenario(
            scenario_id=f"perf_test_{i}",
            content_type="blog_post",
            industry="healthcare",
            prompt=f"Performance test {i}"
        )
        for i in range(5)
    ]
    
    # Benchmark all
    start_time = datetime.now()
    
    for scenario in scenarios:
        await agent.benchmark_scenario(
            waooaw_agent="content_agent",
            waooaw_output=f"Output for {scenario.scenario_id}",
            scenario=scenario
        )
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # Should complete reasonably fast (< 5 seconds for 5 scenarios)
    assert elapsed < 5.0
    assert agent.get_summary_stats()["total_benchmarks"] == 15  # 5 × 3 competitors
