"""
Tests for Winner Selection
"""

import pytest
from backend.app.services.testing.ab_testing import (
    ABTest,
    ABTestManager,
    TestMetrics,
    TestResult,
    TestStatus
)
from backend.app.services.testing.winner_selection import (
    WinnerSelector,
    WinnerResult,
    StatisticalTest,
    AutomatedWinnerSelector
)
from backend.app.services.testing.version_manager import PromptVersionManager


class TestWinnerSelector:
    """Test WinnerSelector"""
    
    @pytest.fixture
    def selector(self):
        """Create winner selector for testing"""
        return WinnerSelector(
            confidence_level=0.95,
            min_effect_size=0.05
        )
    
    def test_create_selector(self, selector):
        """Test creating winner selector"""
        assert selector.confidence_level == 0.95
        assert selector.min_effect_size == 0.05
        assert selector.test_type == StatisticalTest.CHI_SQUARED
    
    def test_select_winner_b_wins(self, selector):
        """Test selecting winner when B is clearly better"""
        test = ABTest(
            id="test1",
            name="Test",
            description="Test",
            prompt_name="test",
            variant_a="v1",
            variant_b="v2",
            min_sample_size=10
        )
        
        # Variant A: 60% success rate
        for i in range(100):
            test.record_result(TestResult(
                variant_id="A",
                success=(i < 60),
                rating=4.0,
                duration_ms=100
            ))
        
        # Variant B: 85% success rate (significantly better)
        for i in range(100):
            test.record_result(TestResult(
                variant_id="B",
                success=(i < 85),
                rating=4.5,
                duration_ms=90
            ))
        
        result = selector.select_winner(test)
        
        assert result.winner == "B"
        assert result.confidence > 0.9
        assert result.effect_size >= 0.05
        assert "B" in result.reason
    
    def test_select_winner_a_wins(self, selector):
        """Test selecting winner when A is better (B underperformed)"""
        test = ABTest(
            id="test1",
            name="Test",
            description="Test",
            prompt_name="test",
            variant_a="v1",
            variant_b="v2",
            min_sample_size=10
        )
        
        # Variant A: 85% success rate
        for i in range(100):
            test.record_result(TestResult(
                variant_id="A",
                success=(i < 85),
                rating=4.5
            ))
        
        # Variant B: 60% success rate (worse)
        for i in range(100):
            test.record_result(TestResult(
                variant_id="B",
                success=(i < 60),
                rating=4.0
            ))
        
        result = selector.select_winner(test)
        
        assert result.winner == "A"
        assert result.confidence > 0.9
        assert "keep current version" in result.recommendation.lower()
    
    def test_select_winner_no_difference(self, selector):
        """Test when there's no significant difference"""
        test = ABTest(
            id="test1",
            name="Test",
            description="Test",
            prompt_name="test",
            variant_a="v1",
            variant_b="v2",
            min_sample_size=10
        )
        
        # Both variants: 80% success rate (no difference)
        for i in range(100):
            test.record_result(TestResult(
                variant_id="A",
                success=(i < 80),
                rating=4.3
            ))
            test.record_result(TestResult(
                variant_id="B",
                success=(i < 80),
                rating=4.3
            ))
        
        result = selector.select_winner(test)
        
        assert result.winner == "A"  # Keep control by default
        assert result.confidence == 0.0
        assert "no statistically significant" in result.reason.lower()
    
    def test_select_winner_small_improvement(self, selector):
        """Test when improvement is below minimum effect size"""
        test = ABTest(
            id="test1",
            name="Test",
            description="Test",
            prompt_name="test",
            variant_a="v1",
            variant_b="v2",
            min_sample_size=10
        )
        
        # Variant A: 80% success
        for i in range(100):
            test.record_result(TestResult(
                variant_id="A",
                success=(i < 80)
            ))
        
        # Variant B: 82% success (only 2% improvement, below 5% threshold)
        for i in range(100):
            test.record_result(TestResult(
                variant_id="B",
                success=(i < 82)
            ))
        
        result = selector.select_winner(test)
        
        # Should keep A due to small effect size
        assert result.winner == "A"
        assert result.effect_size < selector.min_effect_size
    
    def test_calculate_p_value(self, selector):
        """Test p-value calculation"""
        metrics_a = TestMetrics()
        metrics_b = TestMetrics()
        
        # Add data to metrics
        for _ in range(80):
            metrics_a.record_success()
        for _ in range(20):
            metrics_a.record_failure()
        
        for _ in range(85):
            metrics_b.record_success()
        for _ in range(15):
            metrics_b.record_failure()
        
        p_value = selector._calculate_p_value(metrics_a, metrics_b)
        
        # Should be a valid p-value
        assert 0 <= p_value <= 1
    
    def test_compare_metrics(self, selector):
        """Test metrics comparison"""
        metrics_a = TestMetrics()
        metrics_b = TestMetrics()
        
        metrics_a.record_success(rating=4.0, duration_ms=100)
        metrics_a.record_success(rating=4.0, duration_ms=100)
        
        metrics_b.record_success(rating=4.5, duration_ms=90)
        metrics_b.record_success(rating=4.5, duration_ms=90)
        
        comparison = selector._compare_metrics(metrics_a, metrics_b)
        
        assert comparison["variant_a"]["success_rate"] == 100.0
        assert comparison["variant_b"]["success_rate"] == 100.0
        assert comparison["variant_a"]["avg_rating"] == 4.0
        assert comparison["variant_b"]["avg_rating"] == 4.5
        assert comparison["deltas"]["avg_rating"] == 0.5
    
    def test_build_reason(self, selector):
        """Test building human-readable reason"""
        reason = selector._build_reason(
            winner="B",
            success_improvement=0.10,  # 10% better
            rating_improvement=0.5,  # 0.5 points better
            duration_improvement=0.15  # 15% faster
        )
        
        assert "10.0% higher success rate" in reason
        assert "0.50 higher rating" in reason
        assert "15.0% faster" in reason
    
    def test_analyze_test_not_ready(self, selector):
        """Test analyzing test that's not ready"""
        test = ABTest(
            id="test1",
            name="Test",
            description="Test",
            prompt_name="test",
            variant_a="v1",
            variant_b="v2",
            min_sample_size=100
        )
        
        # Add only 50 samples
        for _ in range(50):
            test.record_result(TestResult(variant_id="A", success=True))
            test.record_result(TestResult(variant_id="B", success=True))
        
        analysis = selector.analyze_test(test)
        
        assert analysis["ready"] is False
        assert "insufficient data" in analysis["reason"].lower()
        assert analysis["samples_needed"]["variant_a"] == 50
        assert analysis["samples_needed"]["variant_b"] == 50
    
    def test_analyze_test_ready(self, selector):
        """Test analyzing test that's ready"""
        test = ABTest(
            id="test1",
            name="Test",
            description="Test",
            prompt_name="test",
            variant_a="v1",
            variant_b="v2",
            min_sample_size=50
        )
        
        # Variant A: 70% success
        for i in range(100):
            test.record_result(TestResult(
                variant_id="A",
                success=(i < 70),
                rating=4.0
            ))
        
        # Variant B: 85% success (clearly better)
        for i in range(100):
            test.record_result(TestResult(
                variant_id="B",
                success=(i < 85),
                rating=4.5
            ))
        
        analysis = selector.analyze_test(test)
        
        assert analysis["ready"] is True
        assert analysis["success_rate_delta"] == 15.0  # 15% improvement
        assert analysis["rating_delta"] == 0.5
        assert analysis["leading_variant"] == "B"


class TestAutomatedWinnerSelector:
    """Test AutomatedWinnerSelector"""
    
    @pytest.fixture
    def setup(self):
        """Set up automated selector with managers"""
        version_manager = PromptVersionManager()
        test_manager = ABTestManager()
        selector = AutomatedWinnerSelector(
            version_manager=version_manager,
            test_manager=test_manager,
            confidence_level=0.95,
            min_effect_size=0.05,
            auto_deploy=True
        )
        return selector, version_manager, test_manager
    
    def test_create_automated_selector(self, setup):
        """Test creating automated selector"""
        selector, version_manager, test_manager = setup
        
        assert selector.version_manager is not None
        assert selector.test_manager is not None
        assert selector.auto_deploy is True
    
    def test_process_completed_tests(self, setup):
        """Test processing completed tests"""
        selector, version_manager, test_manager = setup
        
        # Create versions
        v1 = version_manager.create_version(
            prompt_name="test",
            content="Version 1"
        )
        v2 = version_manager.create_version(
            prompt_name="test",
            content="Version 2"
        )
        
        # Create test
        test = test_manager.create_test(
            name="Test Improvement",
            description="Testing v2",
            prompt_name="test",
            variant_a=v1.id,
            variant_b=v2.id,
            min_sample_size=50
        )
        
        # Start test and add data
        test_manager.start_test(test.id)
        
        # V1: 70% success
        for i in range(100):
            test.record_result(TestResult(
                variant_id="A",
                success=(i < 70),
                rating=4.0,
                duration_ms=100
            ))
        
        # V2: 85% success (clearly better)
        for i in range(100):
            test.record_result(TestResult(
                variant_id="B",
                success=(i < 85),
                rating=4.5,
                duration_ms=90
            ))
        
        # Process tests
        results = selector.process_completed_tests()
        
        assert len(results) == 1
        result = results[0]
        
        assert result["winner"] == "B"
        assert result["deployed"] is True  # auto_deploy=True
        assert test.status == TestStatus.COMPLETED
        
        # Check v2 is now active
        active = version_manager.get_active_version("test")
        assert active.id == v2.id
        
        # Check metrics updated
        assert v2.success_rate == 0.85
        assert v2.avg_rating == 4.5
    
    def test_process_no_auto_deploy(self, setup):
        """Test processing without auto-deploy"""
        selector, version_manager, test_manager = setup
        selector.auto_deploy = False
        
        # Create versions and test
        v1 = version_manager.create_version(
            prompt_name="test",
            content="Version 1"
        )
        v2 = version_manager.create_version(
            prompt_name="test",
            content="Version 2"
        )
        
        test = test_manager.create_test(
            name="Test",
            description="Test",
            prompt_name="test",
            variant_a=v1.id,
            variant_b=v2.id,
            min_sample_size=10
        )
        
        test_manager.start_test(test.id)
        
        # Add data (B wins clearly - larger sample for statistical significance)
        for i in range(100):
            test.record_result(TestResult(variant_id="A", success=(i < 60)))
            test.record_result(TestResult(variant_id="B", success=(i < 85)))
        
        # Process tests
        results = selector.process_completed_tests()
        
        assert len(results) == 1
        assert results[0]["winner"] == "B"
        assert results[0]["deployed"] is False  # Not auto-deployed
        
        # V2 should not be active
        active = version_manager.get_active_version("test")
        assert active is None  # No version activated
    
    def test_process_multiple_tests(self, setup):
        """Test processing multiple tests"""
        selector, version_manager, test_manager = setup
        
        # Create two tests
        v1_a = version_manager.create_version(
            prompt_name="prompt1",
            content="V1"
        )
        v2_a = version_manager.create_version(
            prompt_name="prompt1",
            content="V2"
        )
        
        v1_b = version_manager.create_version(
            prompt_name="prompt2",
            content="V1"
        )
        v2_b = version_manager.create_version(
            prompt_name="prompt2",
            content="V2"
        )
        
        test1 = test_manager.create_test(
            name="Test 1",
            description="Test 1",
            prompt_name="prompt1",
            variant_a=v1_a.id,
            variant_b=v2_a.id,
            min_sample_size=10
        )
        
        test2 = test_manager.create_test(
            name="Test 2",
            description="Test 2",
            prompt_name="prompt2",
            variant_a=v1_b.id,
            variant_b=v2_b.id,
            min_sample_size=10
        )
        
        # Start tests and add data
        test_manager.start_test(test1.id)
        test_manager.start_test(test2.id)
        
        # Larger samples with clear winner (B) for statistical significance
        for i in range(100):
            test1.record_result(TestResult(variant_id="A", success=(i < 60)))
            test1.record_result(TestResult(variant_id="B", success=(i < 85)))
            test2.record_result(TestResult(variant_id="A", success=(i < 65)))
            test2.record_result(TestResult(variant_id="B", success=(i < 88)))
        
        # Process all tests
        results = selector.process_completed_tests()
        
        assert len(results) == 2
        assert all(r["winner"] == "B" for r in results)
        assert all(r["deployed"] is True for r in results)
