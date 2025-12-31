"""
Tests for prompt optimization service
"""

import pytest
from app.services.improvement.prompt_optimizer import (
    OptimizationStrategy,
    PromptVersion,
    PromptVariant,
    ABTest,
    PromptTemplate,
    PromptOptimizer,
)


class TestPromptOptimizer:
    """Tests for PromptOptimizer"""
    
    def test_create_optimizer(self):
        """Test creating optimizer"""
        optimizer = PromptOptimizer()
        assert optimizer is not None
    
    def test_register_prompt(self):
        """Test registering a new prompt"""
        optimizer = PromptOptimizer()
        
        prompt_id = optimizer.register_prompt(
            name="Content Creation Prompt",
            category="content_creation",
            base_content="Write engaging content that captures attention.",
            variables=["topic", "tone"]
        )
        
        assert prompt_id is not None
        assert len(prompt_id) > 0
        
        # Verify active prompt is set
        active = optimizer.get_active_prompt(prompt_id)
        assert active is not None
    
    def test_create_variant(self):
        """Test creating prompt variant"""
        optimizer = PromptOptimizer()
        
        prompt_id = optimizer.register_prompt(
            name="Test Prompt",
            category="general",
            base_content="Base prompt content"
        )
        
        variant_id = optimizer.create_variant(
            prompt_id=prompt_id,
            content="Variant prompt content",
            strategy=OptimizationStrategy.SIMPLIFY,
            metadata={"test": True}
        )
        
        assert variant_id is not None
        
        perf = optimizer.get_variant_performance(variant_id)
        assert perf["strategy"] == "simplify"
    
    def test_generate_variants(self):
        """Test generating variants with different strategies"""
        optimizer = PromptOptimizer()
        
        prompt_id = optimizer.register_prompt(
            name="Test Prompt",
            category="content_creation",
            base_content="Please make sure to be accurate and be clear."
        )
        
        variant_ids = optimizer.generate_variants(prompt_id)
        
        # Should generate variant for each strategy
        assert len(variant_ids) >= 4
        
        # Check strategies are different
        strategies = set()
        for vid in variant_ids:
            perf = optimizer.get_variant_performance(vid)
            strategies.add(perf["strategy"])
        
        assert len(strategies) >= 4
    
    def test_simplify_strategy(self):
        """Test simplify optimization strategy"""
        optimizer = PromptOptimizer()
        
        prompt_id = optimizer.register_prompt(
            name="Verbose Prompt",
            category="general",
            base_content="Please make sure to try to be as accurate as possible in order to help."
        )
        
        variants = optimizer.generate_variants(
            prompt_id,
            strategies=[OptimizationStrategy.SIMPLIFY]
        )
        
        assert len(variants) == 1
        
        # Check simplification removed verbose phrases
        history = optimizer.get_prompt_history(prompt_id)
        simplified_variant = next(v for v in history if v["strategy"] == "simplify")
        
        assert "please make sure to" not in simplified_variant["content"].lower()
    
    def test_expand_strategy(self):
        """Test expand optimization strategy"""
        optimizer = PromptOptimizer()
        
        prompt_id = optimizer.register_prompt(
            name="Brief Prompt",
            category="general",
            base_content="Be accurate. Be clear."
        )
        
        variants = optimizer.generate_variants(
            prompt_id,
            strategies=[OptimizationStrategy.EXPAND]
        )
        
        assert len(variants) == 1
        
        # Check expansion added more detail
        history = optimizer.get_prompt_history(prompt_id)
        expanded_variant = next(v for v in history if v["strategy"] == "expand")
        
        # Expanded should be longer
        base_len = len("Be accurate. Be clear.")
        expanded_len = len(expanded_variant["content"])
        assert expanded_len > base_len
    
    def test_specialize_strategy(self):
        """Test specialize optimization strategy"""
        optimizer = PromptOptimizer()
        
        prompt_id = optimizer.register_prompt(
            name="Data Analysis Prompt",
            category="data_analysis",
            base_content="Analyze the data."
        )
        
        variants = optimizer.generate_variants(
            prompt_id,
            strategies=[OptimizationStrategy.SPECIALIZE]
        )
        
        assert len(variants) == 1
        
        # Check specialization added domain context
        history = optimizer.get_prompt_history(prompt_id)
        specialized_variant = next(v for v in history if v["strategy"] == "specialize")
        
        assert "accuracy" in specialized_variant["content"].lower() or \
               "statistical" in specialized_variant["content"].lower()
    
    def test_start_ab_test(self):
        """Test starting A/B test"""
        optimizer = PromptOptimizer()
        
        prompt_id = optimizer.register_prompt(
            name="Test Prompt",
            category="general",
            base_content="Base content"
        )
        
        variant_ids = optimizer.generate_variants(
            prompt_id,
            strategies=[OptimizationStrategy.SIMPLIFY, OptimizationStrategy.EXPAND]
        )
        
        test_id = optimizer.start_ab_test(
            prompt_id=prompt_id,
            variant_ids=variant_ids[:2],
            min_sample_size=10
        )
        
        assert test_id is not None
        
        # Variants should be in testing status
        for vid in variant_ids[:2]:
            perf = optimizer.get_variant_performance(vid)
            assert perf["status"] == "testing"
    
    def test_record_test_result(self):
        """Test recording A/B test results"""
        optimizer = PromptOptimizer()
        
        prompt_id = optimizer.register_prompt(
            name="Test Prompt",
            category="general",
            base_content="Base content"
        )
        
        variant_id = optimizer.create_variant(
            prompt_id=prompt_id,
            content="Test variant",
            strategy=OptimizationStrategy.CLARIFY
        )
        
        # Record success
        optimizer.record_test_result(
            variant_id=variant_id,
            success=True,
            response_time_ms=1200.0,
            user_rating=4.5
        )
        
        perf = optimizer.get_variant_performance(variant_id)
        
        assert perf["test_count"] == 1
        assert perf["success_count"] == 1
        assert perf["success_rate"] == 1.0
        assert perf["avg_response_time"] == 1200.0
        assert perf["user_rating"] == 4.5
    
    def test_evaluate_ab_test_insufficient_samples(self):
        """Test evaluating A/B test with insufficient samples"""
        optimizer = PromptOptimizer()
        
        prompt_id = optimizer.register_prompt(
            name="Test Prompt",
            category="general",
            base_content="Base content"
        )
        
        variant_ids = optimizer.generate_variants(
            prompt_id,
            strategies=[OptimizationStrategy.SIMPLIFY, OptimizationStrategy.EXPAND]
        )
        
        test_id = optimizer.start_ab_test(
            prompt_id=prompt_id,
            variant_ids=variant_ids[:2],
            min_sample_size=100
        )
        
        # Record only a few results
        for _ in range(5):
            optimizer.record_test_result(
                variant_id=variant_ids[0],
                success=True,
                response_time_ms=1000.0,
                user_rating=4.0
            )
        
        # Should not have winner yet
        winner = optimizer.evaluate_ab_test(test_id)
        assert winner is None
    
    def test_evaluate_ab_test_with_winner(self):
        """Test evaluating A/B test with clear winner"""
        optimizer = PromptOptimizer()
        
        prompt_id = optimizer.register_prompt(
            name="Test Prompt",
            category="general",
            base_content="Base content"
        )
        
        variant_ids = optimizer.generate_variants(
            prompt_id,
            strategies=[OptimizationStrategy.SIMPLIFY, OptimizationStrategy.EXPAND]
        )
        
        test_id = optimizer.start_ab_test(
            prompt_id=prompt_id,
            variant_ids=variant_ids[:2],
            min_sample_size=10
        )
        
        # Variant 1: Excellent performance
        for _ in range(12):
            optimizer.record_test_result(
                variant_id=variant_ids[0],
                success=True,
                response_time_ms=1000.0,
                user_rating=4.8
            )
        
        # Variant 2: Poor performance
        for i in range(12):
            optimizer.record_test_result(
                variant_id=variant_ids[1],
                success=i < 6,  # 50% success rate
                response_time_ms=2000.0,
                user_rating=3.0
            )
        
        # Evaluate test
        winner = optimizer.evaluate_ab_test(test_id)
        
        # Variant 1 should win
        assert winner == variant_ids[0]
        
        # Winner should be active
        perf = optimizer.get_variant_performance(winner)
        assert perf["status"] == "active"
        
        # Active prompt should be winner
        active = optimizer.get_active_prompt(prompt_id)
        winner_perf = optimizer.get_variant_performance(winner)
        assert active is not None
    
    def test_get_prompt_history(self):
        """Test getting prompt version history"""
        optimizer = PromptOptimizer()
        
        prompt_id = optimizer.register_prompt(
            name="Test Prompt",
            category="general",
            base_content="Base content"
        )
        
        # Generate variants
        optimizer.generate_variants(prompt_id)
        
        history = optimizer.get_prompt_history(prompt_id)
        
        # Should have multiple versions
        assert len(history) >= 5
        
        # Should be sorted by version
        versions = [v["version"] for v in history]
        assert versions == sorted(versions)
    
    def test_rollback_prompt(self):
        """Test rolling back to previous version"""
        optimizer = PromptOptimizer()
        
        prompt_id = optimizer.register_prompt(
            name="Test Prompt",
            category="general",
            base_content="Version 1"
        )
        
        # Create v2
        v2_id = optimizer.create_variant(
            prompt_id=prompt_id,
            content="Version 2",
            strategy=OptimizationStrategy.EXPAND
        )
        
        # Set v2 as active
        optimizer._prompts[prompt_id].active_variant_id = v2_id
        
        # Rollback to v1
        success = optimizer.rollback_prompt(prompt_id, version=1)
        
        assert success
        
        # Active should be v1
        active = optimizer.get_active_prompt(prompt_id)
        assert active == "Version 1"
    
    def test_traffic_split_validation(self):
        """Test traffic split validation"""
        optimizer = PromptOptimizer()
        
        prompt_id = optimizer.register_prompt(
            name="Test Prompt",
            category="general",
            base_content="Base content"
        )
        
        variant_ids = optimizer.generate_variants(
            prompt_id,
            strategies=[OptimizationStrategy.SIMPLIFY, OptimizationStrategy.EXPAND]
        )
        
        # Invalid traffic split (doesn't sum to 1.0)
        with pytest.raises(ValueError):
            optimizer.start_ab_test(
                prompt_id=prompt_id,
                variant_ids=variant_ids[:2],
                traffic_split={
                    variant_ids[0]: 0.3,
                    variant_ids[1]: 0.5,
                }
            )
    
    def test_get_statistics(self):
        """Test getting optimizer statistics"""
        optimizer = PromptOptimizer()
        
        # Create prompts and variants
        for i in range(3):
            prompt_id = optimizer.register_prompt(
                name=f"Prompt {i}",
                category="general",
                base_content=f"Content {i}"
            )
            optimizer.generate_variants(prompt_id)
        
        stats = optimizer.get_statistics()
        
        assert stats["total_prompts"] == 3
        assert stats["total_variants"] > 3  # Each prompt has multiple variants
        assert "variants_by_status" in stats
    
    def test_variant_performance_tracking(self):
        """Test variant performance metrics tracking"""
        optimizer = PromptOptimizer()
        
        prompt_id = optimizer.register_prompt(
            name="Test Prompt",
            category="general",
            base_content="Base content"
        )
        
        variant_id = optimizer.create_variant(
            prompt_id=prompt_id,
            content="Test variant",
            strategy=OptimizationStrategy.CLARIFY
        )
        
        # Record multiple results
        for i in range(10):
            optimizer.record_test_result(
                variant_id=variant_id,
                success=i < 8,  # 80% success
                response_time_ms=1000.0 + i * 100,
                user_rating=4.0 + i * 0.1
            )
        
        perf = optimizer.get_variant_performance(variant_id)
        
        assert perf["test_count"] == 10
        assert perf["success_count"] == 8
        assert perf["success_rate"] == 0.8
        assert perf["avg_response_time"] == pytest.approx(1450.0, abs=10)
        assert perf["user_rating"] == pytest.approx(4.45, abs=0.1)
