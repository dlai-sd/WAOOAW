"""
Tests for A/B Testing Framework
"""

import pytest
from datetime import datetime, timedelta
from backend.app.services.testing.ab_testing import (
    ABTest,
    ABTestManager,
    TestMetrics,
    TestResult,
    TestStatus
)


class TestTestMetrics:
    """Test TestMetrics dataclass"""
    
    def test_initial_metrics(self):
        """Test initial metrics state"""
        metrics = TestMetrics()
        
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.success_rate == 0.0
        assert metrics.avg_rating == 0.0
        assert metrics.avg_duration_ms == 0
    
    def test_record_success(self):
        """Test recording successful request"""
        metrics = TestMetrics()
        
        metrics.record_success(rating=4.5, duration_ms=100)
        
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1
        assert metrics.failed_requests == 0
        assert metrics.success_rate == 1.0
        assert metrics.avg_rating == 4.5
        assert metrics.avg_duration_ms == 100
    
    def test_record_failure(self):
        """Test recording failed request"""
        metrics = TestMetrics()
        
        metrics.record_failure(duration_ms=150)
        
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 1
        assert metrics.success_rate == 0.0
    
    def test_calculate_averages(self):
        """Test calculating average metrics"""
        metrics = TestMetrics()
        
        metrics.record_success(rating=4.0, duration_ms=100)
        metrics.record_success(rating=5.0, duration_ms=200)
        metrics.record_failure(duration_ms=150)
        
        assert metrics.total_requests == 3
        assert metrics.successful_requests == 2
        assert metrics.failed_requests == 1
        assert metrics.success_rate == pytest.approx(0.667, 0.01)
        assert metrics.avg_rating == 4.5  # (4.0 + 5.0) / 2
        assert metrics.avg_duration_ms == 150  # (100 + 200 + 150) / 3
    
    def test_metrics_to_dict(self):
        """Test converting metrics to dict"""
        metrics = TestMetrics()
        metrics.record_success(rating=4.5, duration_ms=100)
        
        data = metrics.to_dict()
        
        assert data["total_requests"] == 1
        assert data["successful_requests"] == 1
        assert data["success_rate"] == 1.0
        assert data["avg_rating"] == 4.5


class TestABTest:
    """Test ABTest dataclass"""
    
    def test_create_test(self):
        """Test creating an A/B test"""
        test = ABTest(
            id="",
            name="Test Prompt Improvement",
            description="Testing new prompt template",
            prompt_name="content_creation",
            variant_a="v1.0",
            variant_b="v1.1"
        )
        
        assert test.name == "Test Prompt Improvement"
        assert test.status == TestStatus.DRAFT
        assert test.traffic_split == 0.5
        assert test.min_sample_size == 100
        assert test.id  # Auto-generated
    
    def test_start_test(self):
        """Test starting a test"""
        test = ABTest(
            id="test1",
            name="Test",
            description="Test",
            prompt_name="test",
            variant_a="v1",
            variant_b="v2"
        )
        
        test.start()
        
        assert test.status == TestStatus.RUNNING
        assert test.started_at is not None
    
    def test_pause_resume(self):
        """Test pausing and resuming test"""
        test = ABTest(
            id="test1",
            name="Test",
            description="Test",
            prompt_name="test",
            variant_a="v1",
            variant_b="v2"
        )
        
        test.start()
        test.pause()
        assert test.status == TestStatus.PAUSED
        
        test.resume()
        assert test.status == TestStatus.RUNNING
    
    def test_select_variant(self):
        """Test variant selection based on traffic split"""
        test = ABTest(
            id="test1",
            name="Test",
            description="Test",
            prompt_name="test",
            variant_a="v1",
            variant_b="v2",
            traffic_split=0.5
        )
        
        # Run 1000 selections
        selections = [test.select_variant() for _ in range(1000)]
        
        # Should be roughly 50/50 split
        b_count = selections.count("B")
        assert 400 < b_count < 600  # Allow 40-60% range for randomness
    
    def test_record_result(self):
        """Test recording test results"""
        test = ABTest(
            id="test1",
            name="Test",
            description="Test",
            prompt_name="test",
            variant_a="v1",
            variant_b="v2"
        )
        
        # Record result for variant A
        result_a = TestResult(
            variant_id="A",
            success=True,
            rating=4.5,
            duration_ms=100
        )
        test.record_result(result_a)
        
        assert test.metrics_a.total_requests == 1
        assert test.metrics_a.success_rate == 1.0
        
        # Record result for variant B
        result_b = TestResult(
            variant_id="B",
            success=False,
            duration_ms=150
        )
        test.record_result(result_b)
        
        assert test.metrics_b.total_requests == 1
        assert test.metrics_b.success_rate == 0.0
    
    def test_is_ready_for_analysis(self):
        """Test checking if test has enough data"""
        test = ABTest(
            id="test1",
            name="Test",
            description="Test",
            prompt_name="test",
            variant_a="v1",
            variant_b="v2",
            min_sample_size=10
        )
        
        # Not ready yet
        assert test.is_ready_for_analysis() is False
        
        # Add 10 results to each variant
        for _ in range(10):
            test.record_result(TestResult(variant_id="A", success=True))
            test.record_result(TestResult(variant_id="B", success=True))
        
        # Now ready
        assert test.is_ready_for_analysis() is True
    
    def test_should_stop(self):
        """Test checking if test should stop"""
        test = ABTest(
            id="test1",
            name="Test",
            description="Test",
            prompt_name="test",
            variant_a="v1",
            variant_b="v2",
            max_duration_hours=1
        )
        
        # Not started yet
        assert test.should_stop() is False
        
        # Start test
        test.start()
        assert test.should_stop() is False
        
        # Simulate test running for 2 hours
        test.started_at = datetime.utcnow() - timedelta(hours=2)
        assert test.should_stop() is True
    
    def test_get_progress(self):
        """Test getting test progress"""
        test = ABTest(
            id="test1",
            name="Test",
            description="Test",
            prompt_name="test",
            variant_a="v1",
            variant_b="v2",
            min_sample_size=100
        )
        
        # Add 50 results to A, 30 to B
        for _ in range(50):
            test.record_result(TestResult(variant_id="A", success=True))
        for _ in range(30):
            test.record_result(TestResult(variant_id="B", success=True))
        
        progress = test.get_progress()
        
        assert progress["variant_a"]["requests"] == 50
        assert progress["variant_a"]["progress"] == 50.0  # 50% of 100
        assert progress["variant_b"]["requests"] == 30
        assert progress["variant_b"]["progress"] == 30.0
        assert progress["ready_for_analysis"] is False
    
    def test_complete_test(self):
        """Test completing test with winner"""
        test = ABTest(
            id="test1",
            name="Test",
            description="Test",
            prompt_name="test",
            variant_a="v1",
            variant_b="v2"
        )
        
        test.complete(winner="B", reason="Better success rate")
        
        assert test.status == TestStatus.COMPLETED
        assert test.completed_at is not None
        assert test.winner == "B"
        assert test.winner_reason == "Better success rate"


class TestABTestManager:
    """Test ABTestManager"""
    
    @pytest.fixture
    def manager(self):
        """Create test manager for testing"""
        return ABTestManager()
    
    def test_create_test(self, manager):
        """Test creating a test"""
        test = manager.create_test(
            name="Improve Content Creation",
            description="Testing improved prompt template",
            prompt_name="content_creation",
            variant_a="v1.0",
            variant_b="v1.1",
            min_sample_size=50
        )
        
        assert test.name == "Improve Content Creation"
        assert test.min_sample_size == 50
        assert test.status == TestStatus.DRAFT
    
    def test_get_test(self, manager):
        """Test retrieving test by ID"""
        test = manager.create_test(
            name="Test",
            description="Test",
            prompt_name="test",
            variant_a="v1",
            variant_b="v2"
        )
        
        retrieved = manager.get_test(test.id)
        
        assert retrieved is not None
        assert retrieved.id == test.id
    
    def test_list_tests(self, manager):
        """Test listing tests"""
        manager.create_test(
            name="Test 1",
            description="Test 1",
            prompt_name="prompt1",
            variant_a="v1",
            variant_b="v2"
        )
        manager.create_test(
            name="Test 2",
            description="Test 2",
            prompt_name="prompt2",
            variant_a="v1",
            variant_b="v2"
        )
        
        all_tests = manager.list_tests()
        assert len(all_tests) == 2
        
        prompt1_tests = manager.list_tests(prompt_name="prompt1")
        assert len(prompt1_tests) == 1
    
    def test_start_test(self, manager):
        """Test starting a test"""
        test = manager.create_test(
            name="Test",
            description="Test",
            prompt_name="test",
            variant_a="v1",
            variant_b="v2"
        )
        
        manager.start_test(test.id)
        
        assert test.status == TestStatus.RUNNING
    
    def test_record_result(self, manager):
        """Test recording result"""
        test = manager.create_test(
            name="Test",
            description="Test",
            prompt_name="test",
            variant_a="v1",
            variant_b="v2"
        )
        
        manager.start_test(test.id)
        
        result = TestResult(variant_id="A", success=True, rating=4.5)
        success = manager.record_result(test.id, result)
        
        assert success is True
        assert test.metrics_a.total_requests == 1
    
    def test_get_active_test(self, manager):
        """Test getting active test for prompt"""
        test1 = manager.create_test(
            name="Test 1",
            description="Test",
            prompt_name="content_creation",
            variant_a="v1",
            variant_b="v2"
        )
        test2 = manager.create_test(
            name="Test 2",
            description="Test",
            prompt_name="seo_optimization",
            variant_a="v1",
            variant_b="v2"
        )
        
        manager.start_test(test1.id)
        manager.start_test(test2.id)
        
        active = manager.get_active_test("content_creation")
        assert active is not None
        assert active.id == test1.id
    
    def test_route_request(self, manager):
        """Test routing request to variant"""
        test = manager.create_test(
            name="Test",
            description="Test",
            prompt_name="test",
            variant_a="version_a_id",
            variant_b="version_b_id",
            traffic_split=0.5
        )
        
        # No active test yet
        assert manager.route_request("test") is None
        
        # Start test
        manager.start_test(test.id)
        
        # Should return version ID
        version_id = manager.route_request("test")
        assert version_id in ["version_a_id", "version_b_id"]
    
    def test_get_running_tests(self, manager):
        """Test getting all running tests"""
        test1 = manager.create_test(
            name="Test 1",
            description="Test",
            prompt_name="prompt1",
            variant_a="v1",
            variant_b="v2"
        )
        test2 = manager.create_test(
            name="Test 2",
            description="Test",
            prompt_name="prompt2",
            variant_a="v1",
            variant_b="v2"
        )
        
        manager.start_test(test1.id)
        manager.start_test(test2.id)
        
        running = manager.get_running_tests()
        assert len(running) == 2
    
    def test_check_test_completion(self, manager):
        """Test checking if test should complete"""
        test = manager.create_test(
            name="Test",
            description="Test",
            prompt_name="test",
            variant_a="v1",
            variant_b="v2",
            min_sample_size=10,
            max_duration_hours=1
        )
        
        # Not started
        result = manager.check_test_completion(test.id)
        assert result["should_complete"] is False
        
        # Start and add data
        manager.start_test(test.id)
        for _ in range(10):
            test.record_result(TestResult(variant_id="A", success=True))
            test.record_result(TestResult(variant_id="B", success=True))
        
        # Should complete (min sample size reached)
        result = manager.check_test_completion(test.id)
        assert result["should_complete"] is True
        assert "sample size" in result["reason"].lower()
