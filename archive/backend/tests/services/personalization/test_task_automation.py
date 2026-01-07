"""
Tests for Predictive Task Automation - Story 5.5.3

Epic 5.5: Hyper-Personalization & Adaptation
Story Points: 13
"""

import pytest
from datetime import datetime, timedelta
from app.services.personalization import (
    AutomationType,
    ApprovalMode,
    AutomationStatus,
    ExecutionStatus,
    ScheduleConfig,
    PatternTrigger,
    CalendarTrigger,
    EventTrigger,
    AutomationRule,
    AutomationExecution,
    TaskAutomationEngine,
)


class TestTaskAutomation:
    """Test suite for predictive task automation"""
    
    def test_create_engine(self):
        """Test engine instantiation"""
        engine = TaskAutomationEngine()
        
        assert engine is not None
        stats = engine.get_statistics()
        assert stats["total_rules"] == 0
        assert stats["active_rules"] == 0
        assert stats["total_executions"] == 0
    
    def test_create_scheduled_rule(self):
        """Test creating scheduled automation rule"""
        engine = TaskAutomationEngine()
        
        rule = engine.create_automation_rule(
            customer_id="cust_001",
            automation_type=AutomationType.SCHEDULED,
            task_category="weekly_report",
            task_template="Generate weekly social media performance report for {week}",
            agent_variant_id="agent_marketing",
            approval_mode=ApprovalMode.SUGGEST,
            cron_expression="0 9 * * 1",  # Every Monday 9am
            timezone="UTC"
        )
        
        assert rule is not None
        assert rule.customer_id == "cust_001"
        assert rule.automation_type == AutomationType.SCHEDULED
        assert rule.approval_mode == ApprovalMode.SUGGEST
        assert rule.status == AutomationStatus.ACTIVE
        assert rule.schedule is not None
        assert rule.schedule.cron_expression == "0 9 * * 1"
    
    def test_create_pattern_based_rule(self):
        """Test creating pattern-based automation rule"""
        engine = TaskAutomationEngine()
        
        rule = engine.create_automation_rule(
            customer_id="cust_001",
            automation_type=AutomationType.PATTERN_BASED,
            task_category="seo_optimization",
            task_template="Optimize SEO for the content just created",
            agent_variant_id="agent_seo",
            approval_mode=ApprovalMode.AUTO_EXECUTE,
            preceding_task_category="content_creation",
            wait_time_minutes=30,
            condition="rating >= 4"
        )
        
        assert rule is not None
        assert rule.automation_type == AutomationType.PATTERN_BASED
        assert rule.pattern_trigger is not None
        assert rule.pattern_trigger.preceding_task_category == "content_creation"
        assert rule.pattern_trigger.wait_time_minutes == 30
        assert rule.pattern_trigger.condition == "rating >= 4"
    
    def test_create_calendar_driven_rule(self):
        """Test creating calendar-driven automation rule"""
        engine = TaskAutomationEngine()
        
        rule = engine.create_automation_rule(
            customer_id="cust_001",
            automation_type=AutomationType.CALENDAR_DRIVEN,
            task_category="monthly_report",
            task_template="Generate end-of-month sales report for {month}",
            agent_variant_id="agent_sales",
            approval_mode=ApprovalMode.SILENT_PREPARE,
            trigger_type="end_of_month",
            time_of_day="09:00"
        )
        
        assert rule is not None
        assert rule.automation_type == AutomationType.CALENDAR_DRIVEN
        assert rule.calendar_trigger is not None
        assert rule.calendar_trigger.trigger_type == "end_of_month"
        assert rule.calendar_trigger.time_of_day == "09:00"
    
    def test_create_event_triggered_rule(self):
        """Test creating event-triggered automation rule"""
        engine = TaskAutomationEngine()
        
        rule = engine.create_automation_rule(
            customer_id="cust_001",
            automation_type=AutomationType.EVENT_TRIGGERED,
            task_category="launch_checklist",
            task_template="Create product launch checklist",
            agent_variant_id="agent_marketing",
            approval_mode=ApprovalMode.SUGGEST,
            event_type="product_launch",
            event_source="platform"
        )
        
        assert rule is not None
        assert rule.automation_type == AutomationType.EVENT_TRIGGERED
        assert rule.event_trigger is not None
        assert rule.event_trigger.event_type == "product_launch"
    
    def test_pattern_trigger_automation(self):
        """Test pattern-based automation triggering"""
        engine = TaskAutomationEngine()
        
        # Create pattern-based rule
        rule = engine.create_automation_rule(
            customer_id="cust_001",
            automation_type=AutomationType.PATTERN_BASED,
            task_category="data_visualization",
            task_template="Create visualizations for the analysis",
            agent_variant_id="agent_data",
            approval_mode=ApprovalMode.SUGGEST,
            preceding_task_category="data_analysis",
            wait_time_minutes=15
        )
        
        # Record task completion that should trigger automation
        engine.record_task_completion(
            customer_id="cust_001",
            task_category="data_analysis",
            agent_variant_id="agent_data",
            rating=4.5
        )
        
        # Check that execution was created
        pending = engine.get_pending_executions("cust_001")
        assert len(pending) == 1
        assert pending[0].task_category == "data_visualization"
        assert pending[0].status == ExecutionStatus.SUGGESTED  # Because approval_mode is SUGGEST
    
    def test_pattern_trigger_with_rating_condition(self):
        """Test pattern trigger with rating condition"""
        engine = TaskAutomationEngine()
        
        # Create rule with rating condition
        rule = engine.create_automation_rule(
            customer_id="cust_001",
            automation_type=AutomationType.PATTERN_BASED,
            task_category="followup_task",
            task_template="Follow up on previous work",
            agent_variant_id="agent_marketing",
            approval_mode=ApprovalMode.AUTO_EXECUTE,
            preceding_task_category="content_creation",
            wait_time_minutes=0,
            condition="rating >= 4.0"
        )
        
        # Record task with low rating (should NOT trigger)
        engine.record_task_completion(
            customer_id="cust_001",
            task_category="content_creation",
            agent_variant_id="agent_marketing",
            rating=3.0
        )
        
        pending = engine.get_pending_executions("cust_001")
        assert len(pending) == 0  # Should not trigger due to low rating
        
        # Record task with high rating (SHOULD trigger)
        engine.record_task_completion(
            customer_id="cust_001",
            task_category="content_creation",
            agent_variant_id="agent_marketing",
            rating=4.5
        )
        
        pending = engine.get_pending_executions("cust_001")
        assert len(pending) == 1
        assert pending[0].task_category == "followup_task"
    
    def test_task_description_generation(self):
        """Test task description generation with template variables"""
        engine = TaskAutomationEngine()
        
        rule = engine.create_automation_rule(
            customer_id="cust_001",
            automation_type=AutomationType.SCHEDULED,
            task_category="monthly_report",
            task_template="Generate report for {month} {year}",
            agent_variant_id="agent_marketing",
            approval_mode=ApprovalMode.AUTO_EXECUTE,
            cron_expression="0 9 1 * *"
        )
        
        # Manually trigger to test description generation
        execution = engine._trigger_automation(rule)
        
        assert execution is not None
        assert "{month}" not in execution.task_description  # Should be replaced
        assert "{year}" not in execution.task_description  # Should be replaced
    
    def test_approve_execution(self):
        """Test approving a suggested execution"""
        engine = TaskAutomationEngine()
        
        rule = engine.create_automation_rule(
            customer_id="cust_001",
            automation_type=AutomationType.PATTERN_BASED,
            task_category="task_x",
            task_template="Do task X",
            agent_variant_id="agent_marketing",
            approval_mode=ApprovalMode.SUGGEST,
            preceding_task_category="task_y",
            wait_time_minutes=0
        )
        
        # Trigger automation
        engine.record_task_completion("cust_001", "task_y", "agent_marketing")
        
        # Get pending execution
        pending = engine.get_pending_executions("cust_001")
        assert len(pending) == 1
        assert pending[0].status == ExecutionStatus.SUGGESTED
        
        # Approve execution
        success = engine.approve_execution(pending[0].execution_id)
        assert success is True
        
        # Verify status changed
        execution = engine._executions[pending[0].execution_id]
        assert execution.status == ExecutionStatus.APPROVED
        assert execution.approved_at is not None
    
    def test_cancel_execution(self):
        """Test cancelling a pending execution"""
        engine = TaskAutomationEngine()
        
        rule = engine.create_automation_rule(
            customer_id="cust_001",
            automation_type=AutomationType.PATTERN_BASED,
            task_category="task_x",
            task_template="Do task X",
            agent_variant_id="agent_marketing",
            approval_mode=ApprovalMode.SUGGEST,
            preceding_task_category="task_y",
            wait_time_minutes=0
        )
        
        # Trigger automation
        engine.record_task_completion("cust_001", "task_y", "agent_marketing")
        
        # Get and cancel execution
        pending = engine.get_pending_executions("cust_001")
        success = engine.cancel_execution(pending[0].execution_id)
        assert success is True
        
        # Verify status
        execution = engine._executions[pending[0].execution_id]
        assert execution.status == ExecutionStatus.CANCELLED
        assert execution.completed_at is not None
    
    def test_record_execution_result_success(self):
        """Test recording successful execution result"""
        engine = TaskAutomationEngine()
        
        rule = engine.create_automation_rule(
            customer_id="cust_001",
            automation_type=AutomationType.PATTERN_BASED,
            task_category="task_x",
            task_template="Do task X",
            agent_variant_id="agent_marketing",
            approval_mode=ApprovalMode.AUTO_EXECUTE,
            preceding_task_category="task_y",
            wait_time_minutes=0
        )
        
        # Trigger and get execution
        engine.record_task_completion("cust_001", "task_y", "agent_marketing")
        pending = engine.get_pending_executions("cust_001")
        execution_id = pending[0].execution_id
        
        # Record success
        success = engine.record_execution_result(
            execution_id=execution_id,
            success=True,
            output="Task completed successfully",
            rating=4.5,
            feedback="Great work!"
        )
        
        assert success is True
        
        # Verify execution updated
        execution = engine._executions[execution_id]
        assert execution.status == ExecutionStatus.COMPLETED
        assert execution.output == "Task completed successfully"
        assert execution.rating == 4.5
        assert execution.customer_feedback == "Great work!"
        assert execution.completed_at is not None
        
        # Verify rule statistics updated
        assert rule.success_count == 1
        assert rule.failure_count == 0
    
    def test_record_execution_result_failure(self):
        """Test recording failed execution result"""
        engine = TaskAutomationEngine()
        
        rule = engine.create_automation_rule(
            customer_id="cust_001",
            automation_type=AutomationType.PATTERN_BASED,
            task_category="task_x",
            task_template="Do task X",
            agent_variant_id="agent_marketing",
            approval_mode=ApprovalMode.AUTO_EXECUTE,
            preceding_task_category="task_y",
            wait_time_minutes=0
        )
        
        # Trigger and get execution
        engine.record_task_completion("cust_001", "task_y", "agent_marketing")
        pending = engine.get_pending_executions("cust_001")
        execution_id = pending[0].execution_id
        
        # Record failure
        success = engine.record_execution_result(
            execution_id=execution_id,
            success=False,
            error_message="Agent failed to complete task"
        )
        
        assert success is True
        
        # Verify execution updated
        execution = engine._executions[execution_id]
        assert execution.status == ExecutionStatus.FAILED
        assert execution.error_message == "Agent failed to complete task"
        
        # Verify rule statistics
        assert rule.success_count == 0
        assert rule.failure_count == 1
    
    def test_get_customer_rules(self):
        """Test retrieving all rules for a customer"""
        engine = TaskAutomationEngine()
        
        # Create multiple rules for same customer
        for i in range(3):
            engine.create_automation_rule(
                customer_id="cust_001",
                automation_type=AutomationType.SCHEDULED,
                task_category=f"task_{i}",
                task_template=f"Do task {i}",
                agent_variant_id="agent_marketing",
                approval_mode=ApprovalMode.SUGGEST,
                cron_expression="0 9 * * *"
            )
        
        rules = engine.get_customer_rules("cust_001")
        assert len(rules) == 3
        assert all(r.customer_id == "cust_001" for r in rules)
    
    def test_pause_resume_rule(self):
        """Test pausing and resuming automation rule"""
        engine = TaskAutomationEngine()
        
        rule = engine.create_automation_rule(
            customer_id="cust_001",
            automation_type=AutomationType.SCHEDULED,
            task_category="task_x",
            task_template="Do task X",
            agent_variant_id="agent_marketing",
            approval_mode=ApprovalMode.SUGGEST,
            cron_expression="0 9 * * *"
        )
        
        assert rule.status == AutomationStatus.ACTIVE
        
        # Pause rule
        success = engine.pause_rule(rule.rule_id)
        assert success is True
        assert rule.status == AutomationStatus.PAUSED
        
        # Resume rule
        success = engine.resume_rule(rule.rule_id)
        assert success is True
        assert rule.status == AutomationStatus.ACTIVE
    
    def test_disable_rule(self):
        """Test permanently disabling automation rule"""
        engine = TaskAutomationEngine()
        
        rule = engine.create_automation_rule(
            customer_id="cust_001",
            automation_type=AutomationType.SCHEDULED,
            task_category="task_x",
            task_template="Do task X",
            agent_variant_id="agent_marketing",
            approval_mode=ApprovalMode.SUGGEST,
            cron_expression="0 9 * * *"
        )
        
        # Disable rule
        success = engine.disable_rule(rule.rule_id)
        assert success is True
        assert rule.status == AutomationStatus.DISABLED
        
        # Should not be able to resume disabled rule
        success = engine.resume_rule(rule.rule_id)
        assert success is False
    
    def test_paused_rule_not_triggered(self):
        """Test that paused rules don't trigger"""
        engine = TaskAutomationEngine()
        
        rule = engine.create_automation_rule(
            customer_id="cust_001",
            automation_type=AutomationType.PATTERN_BASED,
            task_category="task_x",
            task_template="Do task X",
            agent_variant_id="agent_marketing",
            approval_mode=ApprovalMode.AUTO_EXECUTE,
            preceding_task_category="task_y",
            wait_time_minutes=0
        )
        
        # Pause rule
        engine.pause_rule(rule.rule_id)
        
        # Try to trigger (should not create execution)
        engine.record_task_completion("cust_001", "task_y", "agent_marketing")
        
        pending = engine.get_pending_executions("cust_001")
        assert len(pending) == 0  # Paused rule should not trigger
    
    def test_get_rule_performance(self):
        """Test retrieving rule performance statistics"""
        engine = TaskAutomationEngine()
        
        rule = engine.create_automation_rule(
            customer_id="cust_001",
            automation_type=AutomationType.PATTERN_BASED,
            task_category="task_x",
            task_template="Do task X",
            agent_variant_id="agent_marketing",
            approval_mode=ApprovalMode.AUTO_EXECUTE,
            preceding_task_category="task_y",
            wait_time_minutes=0
        )
        
        # Trigger multiple executions
        for i in range(5):
            engine.record_task_completion("cust_001", "task_y", "agent_marketing")
        
        # Record results (3 success, 2 failure)
        pending = engine.get_pending_executions("cust_001")
        for i, exec in enumerate(pending):
            engine.record_execution_result(
                execution_id=exec.execution_id,
                success=i < 3,  # First 3 succeed
                output=f"Result {i}" if i < 3 else None,
                error_message=None if i < 3 else f"Error {i}",
                rating=4.5 if i < 3 else None
            )
        
        # Get performance
        perf = engine.get_rule_performance(rule.rule_id)
        
        assert perf is not None
        assert perf["execution_count"] == 5
        assert perf["success_count"] == 3
        assert perf["failure_count"] == 2
        assert perf["success_rate"] == 0.6  # 3/5
        assert perf["average_rating"] == 4.5
    
    def test_rule_to_dict_serialization(self):
        """Test automation rule serialization"""
        engine = TaskAutomationEngine()
        
        rule = engine.create_automation_rule(
            customer_id="cust_001",
            automation_type=AutomationType.SCHEDULED,
            task_category="weekly_report",
            task_template="Generate weekly report",
            agent_variant_id="agent_marketing",
            approval_mode=ApprovalMode.SUGGEST,
            cron_expression="0 9 * * 1"
        )
        
        rule_dict = rule.to_dict()
        
        assert isinstance(rule_dict, dict)
        assert rule_dict["rule_id"] == rule.rule_id
        assert rule_dict["customer_id"] == "cust_001"
        assert rule_dict["automation_type"] == "scheduled"
        assert rule_dict["approval_mode"] == "suggest"
        assert "schedule" in rule_dict
    
    def test_execution_to_dict_serialization(self):
        """Test automation execution serialization"""
        engine = TaskAutomationEngine()
        
        rule = engine.create_automation_rule(
            customer_id="cust_001",
            automation_type=AutomationType.PATTERN_BASED,
            task_category="task_x",
            task_template="Do task X",
            agent_variant_id="agent_marketing",
            approval_mode=ApprovalMode.SUGGEST,
            preceding_task_category="task_y",
            wait_time_minutes=0
        )
        
        engine.record_task_completion("cust_001", "task_y", "agent_marketing")
        pending = engine.get_pending_executions("cust_001")
        execution = pending[0]
        
        exec_dict = execution.to_dict()
        
        assert isinstance(exec_dict, dict)
        assert exec_dict["execution_id"] == execution.execution_id
        assert exec_dict["rule_id"] == rule.rule_id
        assert exec_dict["customer_id"] == "cust_001"
        assert exec_dict["status"] == "suggested"
    
    def test_get_statistics(self):
        """Test engine statistics retrieval"""
        engine = TaskAutomationEngine()
        
        # Create rules of different types
        engine.create_automation_rule(
            customer_id="cust_001",
            automation_type=AutomationType.SCHEDULED,
            task_category="task_1",
            task_template="Task 1",
            agent_variant_id="agent_marketing",
            cron_expression="0 9 * * *"
        )
        
        engine.create_automation_rule(
            customer_id="cust_001",
            automation_type=AutomationType.PATTERN_BASED,
            task_category="task_2",
            task_template="Task 2",
            agent_variant_id="agent_marketing",
            preceding_task_category="task_1",
            wait_time_minutes=0
        )
        
        engine.create_automation_rule(
            customer_id="cust_002",
            automation_type=AutomationType.CALENDAR_DRIVEN,
            task_category="task_3",
            task_template="Task 3",
            agent_variant_id="agent_marketing",
            trigger_type="end_of_month"
        )
        
        # Trigger some executions
        engine.record_task_completion("cust_001", "task_1", "agent_marketing")
        
        stats = engine.get_statistics()
        
        assert stats["total_rules"] == 3
        assert stats["active_rules"] == 3
        assert stats["total_executions"] == 1
        assert stats["suggested_executions"] == 1
        assert stats["customers_with_automation"] == 2
        assert stats["automation_types"]["scheduled"] == 1
        assert stats["automation_types"]["pattern_based"] == 1
        assert stats["automation_types"]["calendar_driven"] == 1
    
    def test_multiple_customers_independent(self):
        """Test that automation rules are independent per customer"""
        engine = TaskAutomationEngine()
        
        # Customer 1 rule
        engine.create_automation_rule(
            customer_id="cust_001",
            automation_type=AutomationType.PATTERN_BASED,
            task_category="task_x",
            task_template="Task X",
            agent_variant_id="agent_marketing",
            preceding_task_category="task_y",
            wait_time_minutes=0
        )
        
        # Customer 2 rule (different trigger)
        engine.create_automation_rule(
            customer_id="cust_002",
            automation_type=AutomationType.PATTERN_BASED,
            task_category="task_a",
            task_template="Task A",
            agent_variant_id="agent_marketing",
            preceding_task_category="task_b",
            wait_time_minutes=0
        )
        
        # Trigger for customer 1
        engine.record_task_completion("cust_001", "task_y", "agent_marketing")
        
        # Check only customer 1 has pending execution
        pending_1 = engine.get_pending_executions("cust_001")
        pending_2 = engine.get_pending_executions("cust_002")
        
        assert len(pending_1) == 1
        assert len(pending_2) == 0
        assert pending_1[0].task_category == "task_x"
