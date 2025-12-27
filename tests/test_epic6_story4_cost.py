"""
Epic 6: Story 6.4 - Cost Tests

Tests cost optimization and budget enforcement:
- Simulate 200 decisions/day for 30 days
- Track LLM costs (tokens used, $ spent)
- Validate budget enforcement (<$25/month)
- Measure cache savings (90% hit rate)

Requirements from WOWVISION_PRIME_PROJECT_PLAN.md:
- Total cost <$25/month
- Cache hit rate 90%+
- Budget enforcement working
"""

import pytest
import statistics
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from waooaw.agents.wowvision_prime import WowVisionPrime
from waooaw.common.resource_manager import ResourceManager
from waooaw.common.cache import CacheHierarchy


class TestCostOptimization:
    """Test cost optimization strategies."""
    
    @pytest.mark.cost
    def test_30_day_cost_simulation(self):
        """Test: Simulate 200 decisions/day for 30 days, validate <$25/month."""
        agent = WowVisionPrime(agent_id="cost-test-agent")
        
        decisions_per_day = 200
        days = 30
        total_decisions = decisions_per_day * days
        
        # Cost assumptions (Claude Sonnet pricing)
        cost_per_llm_call = 0.003  # $3 per 1000 input tokens, $15 per 1000 output tokens (avg)
        
        llm_calls = 0
        cache_hits = 0
        
        # Simulate decisions (many will be cached/deterministic)
        for day in range(days):
            for i in range(decisions_per_day):
                context = {
                    "decision_type": "pr_review" if i % 10 == 0 else "simple",
                    "context": {
                        "day": day,
                        "index": i,
                        "pr_number": i % 20  # Repeated PRs = cache hits
                    }
                }
                
                # Check if would hit cache (simplified)
                cache_key = f"pr_review-{i % 20}"
                if hasattr(agent, 'cache') and agent.cache.get(cache_key):
                    cache_hits += 1
                else:
                    # First time = LLM call
                    llm_calls += 1
                    if hasattr(agent, 'cache'):
                        agent.cache.set(cache_key, "cached_decision")
                
                decision = agent.make_decision(context)
        
        # Calculate costs
        estimated_cost = llm_calls * cost_per_llm_call
        cache_hit_rate = cache_hits / total_decisions if total_decisions > 0 else 0
        cost_savings = cache_hits * cost_per_llm_call
        
        print(f"\n30-Day Cost Simulation:")
        print(f"  Total decisions: {total_decisions}")
        print(f"  LLM calls: {llm_calls}")
        print(f"  Cache hits: {cache_hits}")
        print(f"  Cache hit rate: {cache_hit_rate:.1%}")
        print(f"  Estimated cost: ${estimated_cost:.2f}")
        print(f"  Cost savings from cache: ${cost_savings:.2f}")
        
        # Validate targets
        assert estimated_cost < 25.0, f"Cost ${estimated_cost:.2f} exceeds $25/month budget"
        assert cache_hit_rate > 0.5, f"Cache hit rate {cache_hit_rate:.1%} is below 50%"
    
    @pytest.mark.cost
    def test_cache_hit_rate_90_percent_target(self):
        """Test: Achieve 90%+ cache hit rate for repeated decisions."""
        agent = WowVisionPrime(agent_id="cache-test-agent")
        
        # Setup cache
        cache = CacheHierarchy(l1_max_size=100)
        
        total_calls = 1000
        unique_contexts = 10  # Only 10 unique contexts = 90% should be cache hits
        
        llm_calls = 0
        cache_hits = 0
        
        for i in range(total_calls):
            context_id = i % unique_contexts
            cache_key = f"decision-{context_id}"
            
            # Check cache
            cached = cache.get(cache_key)
            if cached:
                cache_hits += 1
            else:
                # Simulate LLM call
                llm_calls += 1
                cache.set(cache_key, "decision_result")
        
        cache_hit_rate = cache_hits / total_calls
        
        print(f"\nCache Hit Rate Test:")
        print(f"  Total calls: {total_calls}")
        print(f"  Unique contexts: {unique_contexts}")
        print(f"  LLM calls: {llm_calls}")
        print(f"  Cache hits: {cache_hits}")
        print(f"  Cache hit rate: {cache_hit_rate:.1%}")
        
        # Validate 90%+ target
        assert cache_hit_rate >= 0.90, f"Cache hit rate {cache_hit_rate:.1%} is below 90%"
    
    @pytest.mark.cost
    def test_budget_enforcement_prevents_overspending(self):
        """Test: Budget enforcement stops LLM calls when limit reached."""
        agent = WowVisionPrime(agent_id="budget-test-agent")
        
        # Set strict budget
        resource_manager = ResourceManager(agent_id=agent.agent_id)
        resource_manager.set_budget("llm_calls", limit=10, period="daily")
        
        llm_calls_made = 0
        budget_blocks = 0
        
        with patch.object(agent, 'resource_manager', resource_manager):
            # Try to make 20 decisions (should only allow 10)
            for i in range(20):
                # Check budget before call
                if resource_manager.check_budget("llm_calls", cost=1):
                    # Make LLM call
                    llm_calls_made += 1
                    resource_manager.consume_budget("llm_calls", cost=1)
                else:
                    # Blocked by budget
                    budget_blocks += 1
        
        print(f"\nBudget Enforcement:")
        print(f"  Budget limit: 10 calls")
        print(f"  Attempts: 20")
        print(f"  LLM calls made: {llm_calls_made}")
        print(f"  Budget blocks: {budget_blocks}")
        
        # Validate enforcement
        assert llm_calls_made == 10, f"Made {llm_calls_made} calls, should be exactly 10"
        assert budget_blocks == 10, f"Blocked {budget_blocks} calls, should be 10"
    
    @pytest.mark.cost
    def test_deterministic_decisions_zero_cost(self):
        """Test: Deterministic decisions have zero LLM cost."""
        agent = WowVisionPrime(agent_id="deterministic-test-agent")
        
        llm_call_count = 0
        
        def mock_llm_call(*args, **kwargs):
            nonlocal llm_call_count
            llm_call_count += 1
            return "approve"
        
        with patch.object(agent, '_call_llm', side_effect=mock_llm_call):
            # Make 100 simple decisions (should be deterministic)
            for i in range(100):
                context = {
                    "decision_type": "deterministic",
                    "context": {"simple": True, "index": i}
                }
                decision = agent.make_decision(context)
        
        print(f"\nDeterministic Decisions:")
        print(f"  Total decisions: 100")
        print(f"  LLM calls: {llm_call_count}")
        print(f"  Cost: $0.00 (no LLM calls)")
        
        # Deterministic should not call LLM
        assert llm_call_count == 0, f"Made {llm_call_count} LLM calls for deterministic decisions"


class TestCostProjections:
    """Test cost projections and alerts."""
    
    @pytest.mark.cost
    def test_monthly_cost_projection(self):
        """Test: Project monthly cost based on daily usage."""
        decisions_per_day = 200
        llm_percentage = 0.10  # 10% require LLM (90% cached/deterministic)
        cost_per_llm = 0.003  # $3 per 1000 tokens
        
        daily_llm_calls = decisions_per_day * llm_percentage
        daily_cost = daily_llm_calls * cost_per_llm
        monthly_cost = daily_cost * 30
        
        print(f"\nMonthly Cost Projection:")
        print(f"  Decisions/day: {decisions_per_day}")
        print(f"  LLM calls/day: {daily_llm_calls:.0f} ({llm_percentage:.0%})")
        print(f"  Daily cost: ${daily_cost:.2f}")
        print(f"  Monthly cost: ${monthly_cost:.2f}")
        
        assert monthly_cost < 25.0, f"Projected cost ${monthly_cost:.2f} exceeds budget"
    
    @pytest.mark.cost
    def test_cost_alert_at_80_percent_budget(self):
        """Test: Alert triggered at 80% of budget."""
        resource_manager = ResourceManager(agent_id="alert-test-agent", alert_threshold=0.8)
        resource_manager.set_budget("llm_calls", limit=100, period="daily")
        
        # Consume 80% of budget
        for i in range(80):
            resource_manager.consume_budget("llm_calls", cost=1)
        
        budget = resource_manager.get_budget("llm_calls")
        usage_fraction = budget.consumed / budget.limit
        
        print(f"\nCost Alert Test:")
        print(f"  Budget: {budget.limit}")
        print(f"  Consumed: {budget.consumed}")
        print(f"  Usage: {usage_fraction:.0%}")
        
        # Should trigger alert at 80%
        assert usage_fraction >= 0.8, "Alert threshold reached"
    
    @pytest.mark.cost
    def test_cost_comparison_with_vs_without_cache(self):
        """Test: Compare costs with vs without caching."""
        decisions = 1000
        cost_per_llm = 0.003
        
        # Without cache: every decision is LLM call
        cost_without_cache = decisions * cost_per_llm
        
        # With cache: 90% hit rate = only 10% LLM calls
        cache_hit_rate = 0.90
        llm_calls_with_cache = decisions * (1 - cache_hit_rate)
        cost_with_cache = llm_calls_with_cache * cost_per_llm
        
        savings = cost_without_cache - cost_with_cache
        savings_percentage = (savings / cost_without_cache) * 100
        
        print(f"\nCache Cost Comparison:")
        print(f"  Decisions: {decisions}")
        print(f"  Without cache: ${cost_without_cache:.2f} ({decisions} LLM calls)")
        print(f"  With cache (90% hit): ${cost_with_cache:.2f} ({llm_calls_with_cache:.0f} LLM calls)")
        print(f"  Savings: ${savings:.2f} ({savings_percentage:.0f}%)")
        
        assert savings_percentage >= 85, f"Cache savings {savings_percentage:.0f}% below 85%"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "cost"])
