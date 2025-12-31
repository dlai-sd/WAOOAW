"""Tests for improvement services"""


class TestPatternDetector:
    """Tests for PatternDetector"""
    
    def test_create_detector(self):
        """Test creating pattern detector"""
        detector = PatternDetector()
        assert detector is not None
    
    def test_record_interaction(self):
        """Test recording interactions"""
        detector = PatternDetector()
        
        detector.record_interaction({
            "task_description": "Write blog post",
            "agent_variant_id": "content_creation_agent",
            "task_category": "content_creation",
            "success": True,
            "response_time_ms": 1200
        })
        
        stats = detector.get_statistics()
        assert stats["total_interactions"] == 1
    
    def test_detect_success_patterns(self):
        """Test detecting success patterns"""
        detector = PatternDetector()
        
        # Record successful interactions for same agent
        for i in range(5):
            detector.record_interaction({
                "task_description": f"Write blog post {i}",
                "agent_variant_id": "content_creation_agent",
                "task_category": "content_creation",
                "success": True,
                "response_time_ms": 1000 + i * 100
            })
        
        patterns = detector.detect_patterns(min_frequency=3)
        
        success_patterns = [p for p in patterns if p.pattern_type == PatternType.SUCCESS]
        assert len(success_patterns) > 0
        assert any("content_creation_agent" in p.description for p in success_patterns)
    
    def test_detect_failure_patterns(self):
        """Test detecting failure patterns"""
        detector = PatternDetector()
        
        # Record failures with same error type
        for i in range(4):
            detector.record_interaction({
                "task_description": f"Task {i}",
                "agent_variant_id": "test_agent",
                "success": False,
                "error_type": "timeout"
            })
        
        patterns = detector.detect_patterns(min_frequency=3)
        
        failure_patterns = [p for p in patterns if p.pattern_type == PatternType.FAILURE]
        assert len(failure_patterns) > 0
        assert any("timeout" in p.description.lower() for p in failure_patterns)
    
    def test_detect_efficiency_patterns(self):
        """Test detecting efficiency patterns"""
        detector = PatternDetector()
        
        # Record fast interactions
        for i in range(5):
            detector.record_interaction({
                "task_description": f"Quick task {i}",
                "agent_variant_id": "fast_agent",
                "success": True,
                "response_time_ms": 500 + i * 10
            })
        
        # Record slow interactions
        for i in range(3):
            detector.record_interaction({
                "task_description": f"Slow task {i}",
                "agent_variant_id": "slow_agent",
                "success": True,
                "response_time_ms": 3000 + i * 100
            })
        
        patterns = detector.detect_patterns(min_frequency=3)
        
        efficiency_patterns = [p for p in patterns if p.pattern_type == PatternType.EFFICIENCY]
        assert len(efficiency_patterns) > 0
    
    def test_get_success_patterns_detailed(self):
        """Test getting detailed success patterns"""
        detector = PatternDetector()
        
        # Record interactions
        for i in range(5):
            detector.record_interaction({
                "task_description": f"Task {i}",
                "agent_variant_id": "agent1",
                "task_category": "category1",
                "success": True,
                "response_time_ms": 1000
            })
        
        success_patterns = detector.get_success_patterns()
        
        assert len(success_patterns) > 0
        assert success_patterns[0].success_rate > 0
        assert success_patterns[0].occurrence_count >= 3
    
    def test_get_failure_patterns_detailed(self):
        """Test getting detailed failure patterns"""
        detector = PatternDetector()
        
        # Record failures
        for i in range(4):
            detector.record_interaction({
                "task_description": f"Task {i}",
                "agent_variant_id": "agent1",
                "success": False,
                "error_type": "validation_error"
            })
        
        failure_patterns = detector.get_failure_patterns()
        
        assert len(failure_patterns) > 0
        assert failure_patterns[0].occurrence_count >= 2
    
    def test_get_improvement_opportunities(self):
        """Test getting improvement opportunities"""
        detector = PatternDetector()
        
        # Record mix of success and failures
        for i in range(8):
            detector.record_interaction({
                "task_description": f"Task {i}",
                "agent_variant_id": "agent1",
                "task_category": "category1",
                "success": True,
                "response_time_ms": 1000
            })
        
        for i in range(6):
            detector.record_interaction({
                "task_description": f"Task {i}",
                "agent_variant_id": "agent2",
                "success": False,
                "error_type": "timeout"
            })
        
        opportunities = detector.get_improvement_opportunities()
        
        assert len(opportunities) > 0
        assert any(o["type"] in ["replicate_success", "fix_failure"] for o in opportunities)
    
    def test_pattern_confidence(self):
        """Test pattern confidence calculation"""
        detector = PatternDetector()
        
        # High confidence: 9/10 success
        for i in range(9):
            detector.record_interaction({
                "task_description": f"Task {i}",
                "agent_variant_id": "reliable_agent",
                "success": True
            })
        detector.record_interaction({
            "task_description": "Task fail",
            "agent_variant_id": "reliable_agent",
            "success": False
        })
        
        patterns = detector.detect_patterns(min_frequency=3, min_confidence=0.8)
        
        high_confidence = [p for p in patterns if p.confidence >= 0.8]
        assert len(high_confidence) > 0


class TestFeedbackAnalyzer:
    """Tests for FeedbackAnalyzer"""
    
    def test_create_analyzer(self):
        """Test creating feedback analyzer"""
        analyzer = FeedbackAnalyzer()
        assert analyzer is not None
    
    def test_collect_feedback(self):
        """Test collecting feedback"""
        analyzer = FeedbackAnalyzer()
        
        feedback = FeedbackEntry(
            feedback_id="fb1",
            feedback_type=FeedbackType.RATING,
            user_id="user1",
            agent_variant_id="agent1",
            task_id="task1",
            rating=4.5
        )
        
        analyzer.collect_feedback(feedback)
        
        stats = analyzer.get_statistics()
        assert stats["total_feedback"] == 1
    
    def test_analyze_low_ratings(self):
        """Test analyzing low ratings"""
        analyzer = FeedbackAnalyzer()
        
        # Add low ratings
        for i in range(6):
            analyzer.collect_feedback(FeedbackEntry(
                feedback_id=f"fb{i}",
                feedback_type=FeedbackType.RATING,
                user_id=f"user{i}",
                agent_variant_id="poor_agent",
                task_id=f"task{i}",
                rating=2.0 + i * 0.1
            ))
        
        insights = analyzer.analyze_feedback()
        
        low_rating_insights = [
            i for i in insights
            if i.category == "user_satisfaction" and "low" in i.description.lower()
        ]
        assert len(low_rating_insights) > 0
    
    def test_analyze_high_ratings(self):
        """Test analyzing high ratings"""
        analyzer = FeedbackAnalyzer()
        
        # Add high ratings
        for i in range(6):
            analyzer.collect_feedback(FeedbackEntry(
                feedback_id=f"fb{i}",
                feedback_type=FeedbackType.RATING,
                user_id=f"user{i}",
                agent_variant_id="excellent_agent",
                task_id=f"task{i}",
                rating=4.5 + i * 0.05
            ))
        
        insights = analyzer.analyze_feedback()
        
        high_rating_insights = [
            i for i in insights
            if i.category == "user_satisfaction" and "excellent" in i.description.lower()
        ]
        assert len(high_rating_insights) > 0
    
    def test_analyze_negative_comments(self):
        """Test analyzing negative sentiment"""
        analyzer = FeedbackAnalyzer()
        
        # Add negative comments
        negative_words = ["terrible", "bad", "poor", "awful", "disappointing"]
        for i, word in enumerate(negative_words):
            analyzer.collect_feedback(FeedbackEntry(
                feedback_id=f"fb{i}",
                feedback_type=FeedbackType.COMMENT,
                user_id=f"user{i}",
                agent_variant_id="problematic_agent",
                task_id=f"task{i}",
                comment=f"This is {word} quality"
            ))
        
        insights = analyzer.analyze_feedback()
        
        sentiment_insights = [
            i for i in insights
            if i.category == "quality_issue" and "negative sentiment" in i.description.lower()
        ]
        assert len(sentiment_insights) > 0
    
    def test_analyze_bug_reports(self):
        """Test analyzing bug reports"""
        analyzer = FeedbackAnalyzer()
        
        # Add bug reports
        for i in range(3):
            analyzer.collect_feedback(FeedbackEntry(
                feedback_id=f"fb{i}",
                feedback_type=FeedbackType.BUG_REPORT,
                user_id=f"user{i}",
                agent_variant_id="buggy_agent",
                task_id=f"task{i}",
                comment=f"Bug: Agent fails on task {i}"
            ))
        
        insights = analyzer.analyze_feedback()
        
        bug_insights = [
            i for i in insights
            if i.category == "quality_issue" and "bug" in i.description.lower()
        ]
        assert len(bug_insights) > 0
    
    def test_analyze_feature_requests(self):
        """Test analyzing feature requests"""
        analyzer = FeedbackAnalyzer()
        
        # Add feature requests
        for i in range(4):
            analyzer.collect_feedback(FeedbackEntry(
                feedback_id=f"fb{i}",
                feedback_type=FeedbackType.FEATURE_REQUEST,
                user_id=f"user{i}",
                agent_variant_id="agent1",
                task_id=f"task{i}",
                comment="Need export functionality for reports"
            ))
        
        insights = analyzer.analyze_feedback()
        
        feature_insights = [i for i in insights if i.category == "feature_gap"]
        assert len(feature_insights) > 0
    
    def test_get_agent_satisfaction_score(self):
        """Test calculating satisfaction score"""
        analyzer = FeedbackAnalyzer()
        
        # Add feedback
        for i in range(6):
            analyzer.collect_feedback(FeedbackEntry(
                feedback_id=f"fb{i}",
                feedback_type=FeedbackType.RATING,
                user_id=f"user{i}",
                agent_variant_id="agent1",
                task_id=f"task{i}",
                rating=4.0
            ))
        
        score = analyzer.get_agent_satisfaction_score("agent1")
        
        assert score is not None
        assert 0 <= score <= 100
        assert score == pytest.approx(80.0, abs=1.0)  # 4.0/5.0 * 100 = 80
    
    def test_get_top_issues(self):
        """Test getting top issues"""
        analyzer = FeedbackAnalyzer()
        
        # Add various feedback
        for i in range(6):
            analyzer.collect_feedback(FeedbackEntry(
                feedback_id=f"fb{i}",
                feedback_type=FeedbackType.RATING,
                user_id=f"user{i}",
                agent_variant_id="agent1",
                task_id=f"task{i}",
                rating=2.0
            ))
        
        for i in range(3):
            analyzer.collect_feedback(FeedbackEntry(
                feedback_id=f"bug{i}",
                feedback_type=FeedbackType.BUG_REPORT,
                user_id=f"user{i}",
                agent_variant_id="agent2",
                task_id=f"task{i}",
                comment="Bug report"
            ))
        
        top_issues = analyzer.get_top_issues(limit=5)
        
        assert len(top_issues) > 0
        assert all(isinstance(issue, FeedbackInsight) for issue in top_issues)


class TestPerformanceAnalyzer:
    """Tests for PerformanceAnalyzer"""
    
    def test_create_analyzer(self):
        """Test creating performance analyzer"""
        analyzer = PerformanceAnalyzer()
        assert analyzer is not None
    
    def test_record_metric(self):
        """Test recording metrics"""
        analyzer = PerformanceAnalyzer()
        
        metric = PerformanceMetric(
            metric_type=MetricType.RESPONSE_TIME,
            agent_variant_id="agent1",
            value=1200.0
        )
        
        analyzer.record_metric(metric)
        
        stats = analyzer.get_statistics()
        assert stats["total_metrics"] == 1
    
    def test_detect_slow_agents(self):
        """Test detecting slow response times"""
        analyzer = PerformanceAnalyzer()
        
        # Add fast agent metrics
        for i in range(10):
            analyzer.record_metric(PerformanceMetric(
                metric_type=MetricType.RESPONSE_TIME,
                agent_variant_id="fast_agent",
                value=1000.0 + i * 10
            ))
        
        # Add slow agent metrics
        for i in range(6):
            analyzer.record_metric(PerformanceMetric(
                metric_type=MetricType.RESPONSE_TIME,
                agent_variant_id="slow_agent",
                value=3000.0 + i * 100
            ))
        
        report = analyzer.analyze_performance()
        
        slow_bottlenecks = [
            b for b in report.bottlenecks
            if b.metric_type == MetricType.RESPONSE_TIME
        ]
        assert len(slow_bottlenecks) > 0
        assert any("slow_agent" in b.affected_agents for b in slow_bottlenecks)
    
    def test_detect_low_success_rate(self):
        """Test detecting low success rates"""
        analyzer = PerformanceAnalyzer()
        
        # Add low success metrics
        for i in range(5):
            analyzer.record_metric(PerformanceMetric(
                metric_type=MetricType.SUCCESS_RATE,
                agent_variant_id="unreliable_agent",
                value=0.65 + i * 0.02
            ))
        
        report = analyzer.analyze_performance()
        
        success_bottlenecks = [
            b for b in report.bottlenecks
            if b.metric_type == MetricType.SUCCESS_RATE
        ]
        assert len(success_bottlenecks) > 0
    
    def test_detect_high_error_rate(self):
        """Test detecting high error rates"""
        analyzer = PerformanceAnalyzer()
        
        # Add high error metrics
        for i in range(5):
            analyzer.record_metric(PerformanceMetric(
                metric_type=MetricType.ERROR_RATE,
                agent_variant_id="error_prone_agent",
                value=0.15 + i * 0.01
            ))
        
        report = analyzer.analyze_performance()
        
        error_bottlenecks = [
            b for b in report.bottlenecks
            if b.metric_type == MetricType.ERROR_RATE
        ]
        assert len(error_bottlenecks) > 0
    
    def test_performance_report_structure(self):
        """Test performance report structure"""
        analyzer = PerformanceAnalyzer()
        
        # Add various metrics
        for i in range(10):
            analyzer.record_metric(PerformanceMetric(
                metric_type=MetricType.RESPONSE_TIME,
                agent_variant_id="agent1",
                value=1000.0 + i * 100
            ))
            analyzer.record_metric(PerformanceMetric(
                metric_type=MetricType.SUCCESS_RATE,
                agent_variant_id="agent1",
                value=0.85 + i * 0.01
            ))
        
        report = analyzer.analyze_performance()
        
        assert report.report_id is not None
        assert isinstance(report.generated_at, datetime)
        assert isinstance(report.summary, dict)
        assert isinstance(report.metrics_by_agent, dict)
        assert isinstance(report.bottlenecks, list)
        assert isinstance(report.recommendations, list)
    
    def test_get_agent_performance_score(self):
        """Test calculating performance score"""
        analyzer = PerformanceAnalyzer()
        
        # Add metrics for good performer
        for i in range(6):
            analyzer.record_metric(PerformanceMetric(
                metric_type=MetricType.SUCCESS_RATE,
                agent_variant_id="good_agent",
                value=0.90
            ))
            analyzer.record_metric(PerformanceMetric(
                metric_type=MetricType.RESPONSE_TIME,
                agent_variant_id="good_agent",
                value=1200.0
            ))
            analyzer.record_metric(PerformanceMetric(
                metric_type=MetricType.ERROR_RATE,
                agent_variant_id="good_agent",
                value=0.05
            ))
        
        score = analyzer.get_agent_performance_score("good_agent")
        
        assert score is not None
        assert 0 <= score <= 100
        assert score >= 80  # Good performer should score high
    
    def test_bottleneck_severity(self):
        """Test bottleneck severity classification"""
        analyzer = PerformanceAnalyzer()
        
        # Add critical bottleneck (very slow)
        for i in range(6):
            analyzer.record_metric(PerformanceMetric(
                metric_type=MetricType.RESPONSE_TIME,
                agent_variant_id="very_slow_agent",
                value=5000.0
            ))
        
        # Add baseline (normal speed)
        for i in range(10):
            analyzer.record_metric(PerformanceMetric(
                metric_type=MetricType.RESPONSE_TIME,
                agent_variant_id="normal_agent",
                value=1500.0
            ))
        
        report = analyzer.analyze_performance()
        
        critical_bottlenecks = [
            b for b in report.bottlenecks
            if b.severity in ["critical", "high"]
        ]
        assert len(critical_bottlenecks) > 0
    
    def test_generate_recommendations(self):
        """Test recommendation generation"""
        analyzer = PerformanceAnalyzer()
        
        # Add problematic metrics
        for i in range(10):
            analyzer.record_metric(PerformanceMetric(
                metric_type=MetricType.SUCCESS_RATE,
                agent_variant_id="problem_agent",
                value=0.70
            ))
        
        report = analyzer.analyze_performance()
        
        assert len(report.recommendations) > 0
        assert any("bottleneck" in rec.lower() for rec in report.recommendations)
