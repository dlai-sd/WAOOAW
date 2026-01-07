"""
Tests for Contextual Error Recovery - Story 5.5.4

Epic 5.5: Hyper-Personalization & Adaptation
Story Points: 13
"""

import pytest
from datetime import datetime
from app.services.personalization import (
    ErrorSeverity,
    ErrorCategory,
    RecoveryStrategy,
    RecoveryStatus,
    ErrorContext,
    ErrorDiagnosis,
    RecoveryAttempt,
    RecoveryCase,
    ErrorRecoveryEngine,
)


class TestErrorRecovery:
    """Test suite for contextual error recovery"""
    
    def test_create_engine(self):
        """Test engine instantiation"""
        engine = ErrorRecoveryEngine()
        
        assert engine is not None
        stats = engine.get_statistics()
        assert stats["total_cases"] == 0
        assert stats["resolved"] == 0
    
    def test_detect_error_low_rating(self):
        """Test error detection based on low rating"""
        engine = ErrorRecoveryEngine()
        
        error_id = engine.detect_error(
            task_id="task_001",
            customer_id="cust_001",
            agent_variant_id="agent_marketing",
            task_category="content_creation",
            task_description="Write blog post",
            output="Some content...",
            rating=2.5  # Low rating
        )
        
        assert error_id is not None
        assert error_id.startswith("error_cust_001")
        
        case = engine.get_recovery_case(error_id)
        assert case is not None
        assert case.context.customer_rating == 2.5
    
    def test_detect_error_explicit_error_message(self):
        """Test error detection based on error message"""
        engine = ErrorRecoveryEngine()
        
        error_id = engine.detect_error(
            task_id="task_002",
            customer_id="cust_001",
            agent_variant_id="agent_marketing",
            task_category="data_analysis",
            task_description="Analyze data",
            error_message="Task failed: Timeout error"
        )
        
        assert error_id is not None
        case = engine.get_recovery_case(error_id)
        assert case.context.error_message == "Task failed: Timeout error"
    
    def test_detect_error_negative_feedback(self):
        """Test error detection based on negative feedback keywords"""
        engine = ErrorRecoveryEngine()
        
        error_id = engine.detect_error(
            task_id="task_003",
            customer_id="cust_001",
            agent_variant_id="agent_marketing",
            task_category="email_campaign",
            task_description="Create email campaign",
            output="Campaign created",
            rating=4.0,  # Good rating
            feedback="This is wrong and not what I wanted"  # Negative feedback
        )
        
        assert error_id is not None
    
    def test_no_error_detection_positive_signals(self):
        """Test that no error is detected with positive signals"""
        engine = ErrorRecoveryEngine()
        
        error_id = engine.detect_error(
            task_id="task_004",
            customer_id="cust_001",
            agent_variant_id="agent_marketing",
            task_category="content_creation",
            task_description="Write article",
            output="Great article...",
            rating=4.5,
            feedback="Excellent work!"
        )
        
        assert error_id is None
    
    def test_diagnose_error(self):
        """Test error diagnosis"""
        engine = ErrorRecoveryEngine()
        
        error_id = engine.detect_error(
            task_id="task_005",
            customer_id="cust_001",
            agent_variant_id="agent_marketing",
            task_category="content_creation",
            task_description="Write blog post",
            rating=2.0,
            feedback="Agent misunderstood what I needed"
        )
        
        diagnosis = engine.diagnose_error(error_id)
        
        assert diagnosis is not None
        assert diagnosis.error_category == ErrorCategory.MISUNDERSTANDING
        assert diagnosis.error_severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM, ErrorSeverity.HIGH]
        assert len(diagnosis.root_cause) > 0
        assert diagnosis.recommended_strategy is not None
        assert len(diagnosis.alternative_strategies) > 0
    
    def test_categorize_misunderstanding(self):
        """Test categorization of misunderstanding errors"""
        engine = ErrorRecoveryEngine()
        
        error_id = engine.detect_error(
            task_id="task_006",
            customer_id="cust_001",
            agent_variant_id="agent_marketing",
            task_category="content_creation",
            task_description="Write article",
            rating=2.5,
            feedback="Agent misunderstood my requirements completely"
        )
        
        diagnosis = engine.diagnose_error(error_id)
        assert diagnosis.error_category == ErrorCategory.MISUNDERSTANDING
    
    def test_categorize_incomplete(self):
        """Test categorization of incomplete task errors"""
        engine = ErrorRecoveryEngine()
        
        error_id = engine.detect_error(
            task_id="task_007",
            customer_id="cust_001",
            agent_variant_id="agent_marketing",
            task_category="report",
            task_description="Generate report",
            rating=2.8,
            feedback="The report is incomplete, missing key sections"
        )
        
        diagnosis = engine.diagnose_error(error_id)
        assert diagnosis.error_category == ErrorCategory.INCOMPLETE
    
    def test_categorize_timeout(self):
        """Test categorization of timeout errors"""
        engine = ErrorRecoveryEngine()
        
        error_id = engine.detect_error(
            task_id="task_008",
            customer_id="cust_001",
            agent_variant_id="agent_data",
            task_category="analysis",
            task_description="Analyze dataset",
            error_message="Task timed out after 5 minutes"
        )
        
        diagnosis = engine.diagnose_error(error_id)
        assert diagnosis.error_category == ErrorCategory.TIMEOUT
        assert diagnosis.error_severity == ErrorSeverity.HIGH
    
    def test_clarification_questions_generated(self):
        """Test that clarification questions are generated for misunderstandings"""
        engine = ErrorRecoveryEngine()
        
        error_id = engine.detect_error(
            task_id="task_009",
            customer_id="cust_001",
            agent_variant_id="agent_marketing",
            task_category="content",
            task_description="Create content",
            rating=2.0,
            feedback="Agent misunderstood what I wanted"  # Clear misunderstanding signal
        )
        
        diagnosis = engine.diagnose_error(error_id)
        assert diagnosis.error_category == ErrorCategory.MISUNDERSTANDING
        assert len(diagnosis.clarification_questions) > 0
    
    def test_attempt_recovery_recommended_strategy(self):
        """Test recovery attempt with recommended strategy"""
        engine = ErrorRecoveryEngine()
        
        error_id = engine.detect_error(
            task_id="task_010",
            customer_id="cust_001",
            agent_variant_id="agent_marketing",
            task_category="content",
            task_description="Write article",
            rating=2.5,
            feedback="Wrong approach used"
        )
        
        engine.diagnose_error(error_id)
        attempt = engine.attempt_recovery(error_id)
        
        assert attempt is not None
        assert attempt.strategy == RecoveryStrategy.ALTERNATIVE_APPROACH
        assert attempt.status in [RecoveryStatus.IN_PROGRESS, RecoveryStatus.CLARIFYING]
    
    def test_attempt_recovery_specific_strategy(self):
        """Test recovery attempt with specific strategy"""
        engine = ErrorRecoveryEngine()
        
        error_id = engine.detect_error(
            task_id="task_011",
            customer_id="cust_001",
            agent_variant_id="agent_marketing",
            task_category="content",
            task_description="Write article",
            rating=2.0
        )
        
        attempt = engine.attempt_recovery(error_id, RecoveryStrategy.SIMPLIFY_TASK)
        
        assert attempt is not None
        assert attempt.strategy == RecoveryStrategy.SIMPLIFY_TASK
        assert attempt.modified_task_description is not None
    
    def test_record_recovery_success(self):
        """Test recording successful recovery"""
        engine = ErrorRecoveryEngine()
        
        error_id = engine.detect_error(
            task_id="task_012",
            customer_id="cust_001",
            agent_variant_id="agent_marketing",
            task_category="content",
            task_description="Write article",
            rating=2.0
        )
        
        attempt = engine.attempt_recovery(error_id)
        
        success = engine.record_recovery_result(
            attempt_id=attempt.attempt_id,
            success=True,
            new_output="Improved article content",
            rating=4.5,
            feedback="Much better!"
        )
        
        assert success is True
        
        case = engine.get_recovery_case(error_id)
        assert case.final_status == RecoveryStatus.RESOLVED
        assert case.resolved_at is not None
        assert len(case.lessons_learned) > 0
    
    def test_record_recovery_failure(self):
        """Test recording failed recovery"""
        engine = ErrorRecoveryEngine()
        
        error_id = engine.detect_error(
            task_id="task_013",
            customer_id="cust_001",
            agent_variant_id="agent_marketing",
            task_category="content",
            task_description="Write article",
            rating=2.0
        )
        
        attempt = engine.attempt_recovery(error_id)
        
        success = engine.record_recovery_result(
            attempt_id=attempt.attempt_id,
            success=False,
            feedback="Still not right"
        )
        
        assert success is True
        
        # Case should not be resolved after failed attempt
        case = engine.get_recovery_case(error_id)
        assert case.final_status != RecoveryStatus.RESOLVED
    
    def test_multiple_recovery_attempts(self):
        """Test multiple recovery attempts for same error"""
        engine = ErrorRecoveryEngine()
        
        error_id = engine.detect_error(
            task_id="task_014",
            customer_id="cust_001",
            agent_variant_id="agent_marketing",
            task_category="content",
            task_description="Write article",
            rating=1.5
        )
        
        # First attempt: alternative approach
        attempt1 = engine.attempt_recovery(error_id, RecoveryStrategy.ALTERNATIVE_APPROACH)
        engine.record_recovery_result(attempt1.attempt_id, success=False)
        
        # Second attempt: clarify requirements
        attempt2 = engine.attempt_recovery(error_id, RecoveryStrategy.CLARIFY_REQUIREMENTS)
        engine.record_recovery_result(attempt2.attempt_id, success=False)
        
        # Third attempt: simplify task
        attempt3 = engine.attempt_recovery(error_id, RecoveryStrategy.SIMPLIFY_TASK)
        engine.record_recovery_result(attempt3.attempt_id, success=True, rating=4.0)
        
        case = engine.get_recovery_case(error_id)
        assert len(case.attempts) == 3
        assert case.final_status == RecoveryStatus.RESOLVED
    
    def test_escalate_to_human(self):
        """Test escalating error to human review"""
        engine = ErrorRecoveryEngine()
        
        error_id = engine.detect_error(
            task_id="task_015",
            customer_id="cust_001",
            agent_variant_id="agent_marketing",
            task_category="complex_task",
            task_description="Very complex task",
            rating=1.0,
            feedback="This is beyond automated capabilities"
        )
        
        success = engine.escalate_to_human(error_id, "Task complexity exceeds agent capabilities")
        
        assert success is True
        
        case = engine.get_recovery_case(error_id)
        assert case.final_status == RecoveryStatus.ESCALATED
        assert len(case.lessons_learned) > 0
    
    def test_get_customer_recovery_history(self):
        """Test retrieving recovery history for customer"""
        engine = ErrorRecoveryEngine()
        
        # Create multiple errors for same customer
        for i in range(3):
            engine.detect_error(
                task_id=f"task_{i}",
                customer_id="cust_001",
                agent_variant_id="agent_marketing",
                task_category="content",
                task_description=f"Task {i}",
                rating=2.0
            )
        
        history = engine.get_customer_recovery_history("cust_001")
        assert len(history) == 3
        assert all(h.context.customer_id == "cust_001" for h in history)
    
    def test_error_context_serialization(self):
        """Test error context serialization"""
        context = ErrorContext(
            task_id="task_001",
            customer_id="cust_001",
            agent_variant_id="agent_marketing",
            task_category="content",
            task_description="Write article",
            original_output="Output",
            error_message="Error",
            customer_rating=2.0,
            customer_feedback="Feedback",
            execution_time_seconds=30.5
        )
        
        context_dict = context.to_dict()
        
        assert isinstance(context_dict, dict)
        assert context_dict["task_id"] == "task_001"
        assert context_dict["customer_rating"] == 2.0
    
    def test_error_diagnosis_serialization(self):
        """Test error diagnosis serialization"""
        diagnosis = ErrorDiagnosis(
            error_id="error_001",
            error_category=ErrorCategory.MISUNDERSTANDING,
            error_severity=ErrorSeverity.MEDIUM,
            root_cause="Agent misunderstood requirements",
            contributing_factors=["Ambiguous task description"],
            similar_successful_tasks=["task_100", "task_101"],
            recommended_strategy=RecoveryStrategy.CLARIFY_REQUIREMENTS,
            alternative_strategies=[RecoveryStrategy.ALTERNATIVE_APPROACH],
            clarification_questions=["What did you expect?"],
            confidence_score=0.75
        )
        
        diag_dict = diagnosis.to_dict()
        
        assert isinstance(diag_dict, dict)
        assert diag_dict["error_category"] == "misunderstanding"
        assert diag_dict["confidence_score"] == 0.75
    
    def test_recovery_attempt_serialization(self):
        """Test recovery attempt serialization"""
        attempt = RecoveryAttempt(
            attempt_id="attempt_001",
            error_id="error_001",
            strategy=RecoveryStrategy.ALTERNATIVE_APPROACH,
            status=RecoveryStatus.RESOLVED,
            modified_task_description="Modified task",
            alternative_approach_description="Alternative approach",
            clarification_request=None,
            new_output="New output",
            success=True,
            customer_rating=4.5,
            customer_feedback="Great!",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        
        attempt_dict = attempt.to_dict()
        
        assert isinstance(attempt_dict, dict)
        assert attempt_dict["strategy"] == "alternative"
        assert attempt_dict["success"] is True
    
    def test_recovery_case_serialization(self):
        """Test complete recovery case serialization"""
        engine = ErrorRecoveryEngine()
        
        error_id = engine.detect_error(
            task_id="task_016",
            customer_id="cust_001",
            agent_variant_id="agent_marketing",
            task_category="content",
            task_description="Write article",
            rating=2.0
        )
        
        case = engine.get_recovery_case(error_id)
        case_dict = case.to_dict()
        
        assert isinstance(case_dict, dict)
        assert "context" in case_dict
        assert "attempts" in case_dict
        assert case_dict["error_id"] == error_id
    
    def test_get_statistics(self):
        """Test recovery statistics"""
        engine = ErrorRecoveryEngine()
        
        # Create various cases
        error1 = engine.detect_error(
            task_id="task_a", customer_id="cust_001", agent_variant_id="agent_marketing",
            task_category="content", task_description="Task A", rating=2.0
        )
        attempt1 = engine.attempt_recovery(error1)
        engine.record_recovery_result(attempt1.attempt_id, success=True, rating=4.5)
        
        error2 = engine.detect_error(
            task_id="task_b", customer_id="cust_002", agent_variant_id="agent_marketing",
            task_category="content", task_description="Task B", rating=1.5
        )
        engine.escalate_to_human(error2, "Too complex")
        
        error3 = engine.detect_error(
            task_id="task_c", customer_id="cust_001", agent_variant_id="agent_marketing",
            task_category="content", task_description="Task C", rating=2.5
        )
        
        stats = engine.get_statistics()
        
        assert stats["total_cases"] == 3
        assert stats["resolved"] == 1
        assert stats["escalated"] == 1
        assert stats["pending"] == 1
        assert stats["customers_with_errors"] == 2
    
    def test_learning_from_successful_recovery(self):
        """Test that engine learns from successful recoveries"""
        engine = ErrorRecoveryEngine()
        
        error_id = engine.detect_error(
            task_id="task_017",
            customer_id="cust_001",
            agent_variant_id="agent_marketing",
            task_category="content",
            task_description="Write article",
            rating=2.0,
            feedback="Wrong approach"
        )
        
        diagnosis = engine.diagnose_error(error_id)
        attempt = engine.attempt_recovery(error_id, RecoveryStrategy.ALTERNATIVE_APPROACH)
        engine.record_recovery_result(attempt.attempt_id, success=True, rating=4.5)
        
        # Check that lesson was learned
        case = engine.get_recovery_case(error_id)
        assert len(case.lessons_learned) > 0
        
        # Check that pattern was stored
        category = diagnosis.error_category.value
        assert category in engine._recovery_patterns
    
    def test_strategy_recommendation_for_misunderstanding(self):
        """Test that misunderstandings recommend clarification"""
        engine = ErrorRecoveryEngine()
        
        error_id = engine.detect_error(
            task_id="task_018",
            customer_id="cust_001",
            agent_variant_id="agent_marketing",
            task_category="content",
            task_description="Create content",
            rating=2.0,
            feedback="Agent misunderstood completely"
        )
        
        diagnosis = engine.diagnose_error(error_id)
        assert diagnosis.recommended_strategy == RecoveryStrategy.CLARIFY_REQUIREMENTS
    
    def test_strategy_recommendation_for_incomplete(self):
        """Test that incomplete tasks recommend retry"""
        engine = ErrorRecoveryEngine()
        
        error_id = engine.detect_error(
            task_id="task_019",
            customer_id="cust_001",
            agent_variant_id="agent_marketing",
            task_category="report",
            task_description="Generate report",
            rating=2.5,
            feedback="Report is incomplete"
        )
        
        diagnosis = engine.diagnose_error(error_id)
        assert diagnosis.recommended_strategy == RecoveryStrategy.RETRY_SAME
    
    def test_multiple_customers_independent(self):
        """Test that error cases are independent per customer"""
        engine = ErrorRecoveryEngine()
        
        # Customer 1 error
        error1 = engine.detect_error(
            task_id="task_x", customer_id="cust_001", agent_variant_id="agent_marketing",
            task_category="content", task_description="Task X", rating=2.0
        )
        
        # Customer 2 error
        error2 = engine.detect_error(
            task_id="task_y", customer_id="cust_002", agent_variant_id="agent_marketing",
            task_category="content", task_description="Task Y", rating=1.5
        )
        
        # Check independence
        history1 = engine.get_customer_recovery_history("cust_001")
        history2 = engine.get_customer_recovery_history("cust_002")
        
        assert len(history1) == 1
        assert len(history2) == 1
        assert history1[0].error_id == error1
        assert history2[0].error_id == error2
