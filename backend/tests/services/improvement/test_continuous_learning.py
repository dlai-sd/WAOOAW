"""
Tests for continuous learning pipeline
"""

import pytest
from datetime import datetime, timedelta
from app.services.improvement.continuous_learning import (
    AnalysisFrequency,
    ImprovementAction,
    ImprovementEvent,
    ContinuousLearningPipeline,
)
from app.services.improvement.pattern_detection import PatternDetector
from app.services.improvement.feedback_analysis import FeedbackAnalyzer, FeedbackEntry, FeedbackType
from app.services.improvement.performance_analysis import PerformanceAnalyzer, PerformanceMetric, MetricType


class TestContinuousLearningPipeline:
    """Tests for ContinuousLearningPipeline"""
    
    def test_create_pipeline(self):
        """Test creating pipeline"""
        pipeline = ContinuousLearningPipeline()
        assert pipeline is not None
    
    def test_configure_schedule(self):
        """Test configuring analysis schedule"""
        pipeline = ContinuousLearningPipeline()
        
        schedule_id = pipeline.configure_schedule(
            frequency=AnalysisFrequency.DAILY,
            enabled=True
        )
        
        assert schedule_id is not None
        
        status = pipeline.get_schedule_status(schedule_id)
        assert status["frequency"] == "daily"
        assert status["enabled"] is True
    
    def test_calculate_next_run(self):
        """Test next run calculation"""
        pipeline = ContinuousLearningPipeline()
        
        now = datetime.now()
        
        # Hourly
        next_hourly = pipeline._calculate_next_run(AnalysisFrequency.HOURLY, now)
        assert (next_hourly - now).total_seconds() == pytest.approx(3600, abs=1)
        
        # Daily
        next_daily = pipeline._calculate_next_run(AnalysisFrequency.DAILY, now)
        assert (next_daily - now).days == 1
        
        # Weekly
        next_weekly = pipeline._calculate_next_run(AnalysisFrequency.WEEKLY, now)
        assert (next_weekly - now).days == 7
    
    def test_enable_disable_schedule(self):
        """Test enabling and disabling schedules"""
        pipeline = ContinuousLearningPipeline()
        
        schedule_id = pipeline.configure_schedule(
            frequency=AnalysisFrequency.DAILY,
            enabled=True
        )
        
        # Disable
        pipeline.disable_schedule(schedule_id)
        status = pipeline.get_schedule_status(schedule_id)
        assert status["enabled"] is False
        
        # Enable
        pipeline.enable_schedule(schedule_id)
        status = pipeline.get_schedule_status(schedule_id)
        assert status["enabled"] is True
    
    def test_register_callback(self):
        """Test registering improvement callbacks"""
        pipeline = ContinuousLearningPipeline()
        
        callback_executed = []
        
        def test_callback(event: ImprovementEvent):
            callback_executed.append(event.event_id)
        
        pipeline.register_callback(
            action_type=ImprovementAction.NOTIFY_ADMIN,
            callback=test_callback
        )
        
        stats = pipeline.get_statistics()
        assert stats["registered_callbacks"] >= 1
    
    def test_analyze_and_improve_with_failures(self):
        """Test analysis and improvement with failure patterns"""
        detector = PatternDetector()
        pipeline = ContinuousLearningPipeline(pattern_detector=detector)
        
        # Record failures
        for i in range(6):
            detector.record_interaction({
                "task_description": f"Task {i}",
                "agent_variant_id": "failing_agent",
                "success": False,
                "error_type": "timeout"
            })
        
        improvements = pipeline.analyze_and_improve()
        
        # Should trigger improvement for failures
        assert len(improvements) > 0
    
    def test_analyze_and_improve_with_low_feedback(self):
        """Test analysis with low user satisfaction"""
        analyzer = FeedbackAnalyzer()
        pipeline = ContinuousLearningPipeline(feedback_analyzer=analyzer)
        
        # Add low ratings
        for i in range(6):
            analyzer.collect_feedback(FeedbackEntry(
                feedback_id=f"fb{i}",
                feedback_type=FeedbackType.RATING,
                user_id=f"user{i}",
                agent_variant_id="poor_agent",
                task_id=f"task{i}",
                rating=2.0
            ))
        
        improvements = pipeline.analyze_and_improve()
        
        # Should trigger improvement for low satisfaction
        assert len(improvements) > 0
    
    def test_analyze_and_improve_with_performance_issues(self):
        """Test analysis with performance bottlenecks"""
        analyzer = PerformanceAnalyzer()
        pipeline = ContinuousLearningPipeline(performance_analyzer=analyzer)
        
        # Add slow agent metrics
        for i in range(6):
            analyzer.record_metric(PerformanceMetric(
                metric_type=MetricType.RESPONSE_TIME,
                agent_variant_id="slow_agent",
                value=5000.0
            ))
        
        # Add baseline
        for i in range(10):
            analyzer.record_metric(PerformanceMetric(
                metric_type=MetricType.RESPONSE_TIME,
                agent_variant_id="normal_agent",
                value=1500.0
            ))
        
        improvements = pipeline.analyze_and_improve()
        
        # Should trigger improvement for slow agent
        assert len(improvements) > 0
    
    def test_run_scheduled_analysis_before_time(self):
        """Test scheduled analysis before time"""
        pipeline = ContinuousLearningPipeline()
        
        schedule_id = pipeline.configure_schedule(
            frequency=AnalysisFrequency.DAILY,
            enabled=True
        )
        
        # Try to run immediately (should skip)
        result = pipeline.run_scheduled_analysis(schedule_id)
        
        # Should skip since next_run is in future
        assert result["status"] == "skipped"
    
    def test_run_scheduled_analysis_disabled(self):
        """Test scheduled analysis when disabled"""
        pipeline = ContinuousLearningPipeline()
        
        schedule_id = pipeline.configure_schedule(
            frequency=AnalysisFrequency.DAILY,
            enabled=False
        )
        
        result = pipeline.run_scheduled_analysis(schedule_id)
        
        assert result["status"] == "skipped"
        assert result["reason"] == "schedule_disabled"
    
    def test_run_scheduled_analysis_success(self):
        """Test successful scheduled analysis"""
        pipeline = ContinuousLearningPipeline()
        
        schedule_id = pipeline.configure_schedule(
            frequency=AnalysisFrequency.HOURLY,
            enabled=True
        )
        
        # Set next_run to past
        pipeline._schedules[schedule_id].next_run = datetime.now() - timedelta(hours=1)
        
        result = pipeline.run_scheduled_analysis(schedule_id)
        
        assert result["status"] == "completed"
        assert "improvements" in result
        
        status = pipeline.get_schedule_status(schedule_id)
        assert status["run_count"] == 1
    
    def test_get_improvement_history(self):
        """Test getting improvement history"""
        analyzer = FeedbackAnalyzer()
        pipeline = ContinuousLearningPipeline(feedback_analyzer=analyzer)
        
        # Add feedback to trigger improvements
        for i in range(6):
            analyzer.collect_feedback(FeedbackEntry(
                feedback_id=f"fb{i}",
                feedback_type=FeedbackType.RATING,
                user_id=f"user{i}",
                agent_variant_id="agent1",
                task_id=f"task{i}",
                rating=2.0
            ))
        
        # Run analysis
        pipeline.analyze_and_improve()
        
        # Get history
        history = pipeline.get_improvement_history(limit=5)
        
        assert len(history) <= 5
    
    def test_get_improvement_history_filtered(self):
        """Test getting filtered improvement history"""
        analyzer = FeedbackAnalyzer()
        pipeline = ContinuousLearningPipeline(feedback_analyzer=analyzer)
        
        # Add feedback
        for i in range(6):
            analyzer.collect_feedback(FeedbackEntry(
                feedback_id=f"fb{i}",
                feedback_type=FeedbackType.RATING,
                user_id=f"user{i}",
                agent_variant_id="agent1",
                task_id=f"task{i}",
                rating=2.0
            ))
        
        pipeline.analyze_and_improve()
        
        # Filter by action type
        history = pipeline.get_improvement_history(
            action_type=ImprovementAction.NOTIFY_ADMIN
        )
        
        # All should be notify_admin type
        assert all(e.action_type == ImprovementAction.NOTIFY_ADMIN for e in history)
    
    def test_set_threshold(self):
        """Test setting improvement thresholds"""
        pipeline = ContinuousLearningPipeline()
        
        pipeline.set_threshold("low_success_rate", 0.80)
        
        stats = pipeline.get_statistics()
        assert stats["thresholds"]["low_success_rate"] == 0.80
    
    def test_set_invalid_threshold(self):
        """Test setting invalid threshold"""
        pipeline = ContinuousLearningPipeline()
        
        with pytest.raises(ValueError):
            pipeline.set_threshold("invalid_key", 0.5)
    
    def test_get_statistics(self):
        """Test getting pipeline statistics"""
        pipeline = ContinuousLearningPipeline()
        
        # Configure schedule
        pipeline.configure_schedule(AnalysisFrequency.DAILY)
        
        # Register callback
        def dummy_callback(event):
            pass
        
        pipeline.register_callback(ImprovementAction.NOTIFY_ADMIN, dummy_callback)
        
        stats = pipeline.get_statistics()
        
        assert "total_improvements" in stats
        assert "active_schedules" in stats
        assert "registered_callbacks" in stats
        assert stats["total_schedules"] == 1
        assert stats["registered_callbacks"] == 1
    
    def test_callback_execution(self):
        """Test callback execution during improvements"""
        analyzer = FeedbackAnalyzer()
        pipeline = ContinuousLearningPipeline(feedback_analyzer=analyzer)
        
        executed_events = []
        
        def test_callback(event: ImprovementEvent):
            executed_events.append(event)
        
        pipeline.register_callback(
            action_type=ImprovementAction.NOTIFY_ADMIN,
            callback=test_callback
        )
        
        # Add feedback to trigger improvement
        for i in range(6):
            analyzer.collect_feedback(FeedbackEntry(
                feedback_id=f"fb{i}",
                feedback_type=FeedbackType.BUG_REPORT,
                user_id=f"user{i}",
                agent_variant_id="buggy_agent",
                task_id=f"task{i}",
                comment="Bug report"
            ))
        
        pipeline.analyze_and_improve()
        
        # Callback should have been executed
        assert len(executed_events) > 0
    
    def test_improvement_event_metadata(self):
        """Test improvement event contains proper metadata"""
        analyzer = FeedbackAnalyzer()
        pipeline = ContinuousLearningPipeline(feedback_analyzer=analyzer)
        
        # Add feedback
        for i in range(6):
            analyzer.collect_feedback(FeedbackEntry(
                feedback_id=f"fb{i}",
                feedback_type=FeedbackType.RATING,
                user_id=f"user{i}",
                agent_variant_id="agent1",
                task_id=f"task{i}",
                rating=1.5
            ))
        
        improvements = pipeline.analyze_and_improve()
        
        if improvements:
            event = improvements[0]
            assert event.event_id is not None
            assert event.action_type is not None
            assert event.trigger_reason is not None
            assert event.executed_at is not None
            assert isinstance(event.success, bool)
