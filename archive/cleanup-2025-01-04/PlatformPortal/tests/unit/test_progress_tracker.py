"""
Unit tests for progress_tracker component
"""

import pytest
from waooaw_portal.components.common.progress_tracker import (
    progress_tracker,
    progress_agent_provisioning,
    progress_deployment_pipeline,
    progress_upgrade_workflow,
)


class TestProgressTracker:
    """Test basic progress tracker functionality"""

    def test_progress_tracker_basic(self):
        """Test basic progress tracker creation"""
        steps = [
            ("Step 1", "completed", "First step"),
            ("Step 2", "current", "Second step"),
            ("Step 3", "pending", "Third step"),
        ]
        result = progress_tracker(steps)
        assert result is not None

    def test_progress_tracker_empty(self):
        """Test empty progress tracker"""
        result = progress_tracker([])
        assert result is not None

    def test_progress_tracker_single_step(self):
        """Test progress tracker with single step"""
        steps = [("Step 1", "completed", "Only step")]
        result = progress_tracker(steps)
        assert result is not None

    def test_progress_tracker_horizontal(self):
        """Test horizontal orientation"""
        steps = [
            ("Step 1", "completed", None),
            ("Step 2", "current", None),
        ]
        result = progress_tracker(steps, orientation="horizontal")
        assert result is not None

    def test_progress_tracker_vertical(self):
        """Test vertical orientation"""
        steps = [
            ("Step 1", "completed", None),
            ("Step 2", "current", None),
        ]
        result = progress_tracker(steps, orientation="vertical")
        assert result is not None

    def test_progress_tracker_with_descriptions(self):
        """Test with descriptions enabled"""
        steps = [
            ("Step 1", "completed", "First step description"),
            ("Step 2", "current", "Second step description"),
        ]
        result = progress_tracker(steps, show_descriptions=True)
        assert result is not None

    def test_progress_tracker_without_descriptions(self):
        """Test without descriptions"""
        steps = [
            ("Step 1", "completed", "First step description"),
            ("Step 2", "current", "Second step description"),
        ]
        result = progress_tracker(steps, show_descriptions=False)
        assert result is not None

    def test_progress_tracker_with_step_numbers(self):
        """Test with step numbers enabled"""
        steps = [
            ("Step 1", "pending", None),
            ("Step 2", "pending", None),
        ]
        result = progress_tracker(steps, show_step_numbers=True)
        assert result is not None

    def test_progress_tracker_without_step_numbers(self):
        """Test without step numbers"""
        steps = [
            ("Step 1", "pending", None),
            ("Step 2", "pending", None),
        ]
        result = progress_tracker(steps, show_step_numbers=False)
        assert result is not None

    def test_progress_tracker_current_step(self):
        """Test with different current step indices"""
        steps = [
            ("Step 1", "completed", None),
            ("Step 2", "current", None),
            ("Step 3", "pending", None),
        ]
        for i in range(3):
            result = progress_tracker(steps, current_step=i)
            assert result is not None

    def test_progress_tracker_themes(self):
        """Test dark and light themes"""
        steps = [("Step 1", "current", None)]
        for theme in ["dark", "light"]:
            result = progress_tracker(steps, theme=theme)
            assert result is not None


class TestProgressStatus:
    """Test different progress status types"""

    def test_status_completed(self):
        """Test completed status"""
        steps = [("Completed", "completed", "Done")]
        result = progress_tracker(steps)
        assert result is not None

    def test_status_current(self):
        """Test current status"""
        steps = [("Current", "current", "In progress")]
        result = progress_tracker(steps)
        assert result is not None

    def test_status_pending(self):
        """Test pending status"""
        steps = [("Pending", "pending", "Not started")]
        result = progress_tracker(steps)
        assert result is not None

    def test_status_error(self):
        """Test error status"""
        steps = [("Error", "error", "Failed")]
        result = progress_tracker(steps)
        assert result is not None

    def test_status_skipped(self):
        """Test skipped status"""
        steps = [("Skipped", "skipped", "Not needed")]
        result = progress_tracker(steps)
        assert result is not None

    def test_mixed_statuses(self):
        """Test tracker with mixed statuses"""
        steps = [
            ("Completed", "completed", "Done"),
            ("Current", "current", "In progress"),
            ("Error", "error", "Failed"),
            ("Pending", "pending", "Waiting"),
            ("Skipped", "skipped", "Not needed"),
        ]
        result = progress_tracker(steps)
        assert result is not None


class TestPresetProgressTrackers:
    """Test preset progress tracker components"""

    def test_progress_agent_provisioning(self):
        """Test agent provisioning preset"""
        result = progress_agent_provisioning()
        assert result is not None

    def test_progress_agent_provisioning_steps(self):
        """Test agent provisioning at different steps"""
        for step in range(5):
            result = progress_agent_provisioning(current_step=step)
            assert result is not None

    def test_progress_agent_provisioning_theme(self):
        """Test agent provisioning with theme"""
        result = progress_agent_provisioning(theme="dark")
        assert result is not None

    def test_progress_deployment_pipeline(self):
        """Test deployment pipeline preset"""
        result = progress_deployment_pipeline()
        assert result is not None

    def test_progress_deployment_pipeline_steps(self):
        """Test deployment pipeline at different steps"""
        for step in range(4):
            result = progress_deployment_pipeline(current_step=step)
            assert result is not None

    def test_progress_deployment_pipeline_theme(self):
        """Test deployment pipeline with theme"""
        result = progress_deployment_pipeline(theme="light")
        assert result is not None

    def test_progress_upgrade_workflow(self):
        """Test upgrade workflow preset"""
        result = progress_upgrade_workflow()
        assert result is not None

    def test_progress_upgrade_workflow_steps(self):
        """Test upgrade workflow at different steps"""
        for step in range(6):
            result = progress_upgrade_workflow(current_step=step)
            assert result is not None

    def test_progress_upgrade_workflow_theme(self):
        """Test upgrade workflow with theme"""
        result = progress_upgrade_workflow(theme="dark")
        assert result is not None


class TestProgressTrackerEdgeCases:
    """Test edge cases"""

    def test_empty_step_label(self):
        """Test with empty step label"""
        steps = [("", "completed", "Description")]
        result = progress_tracker(steps)
        assert result is not None

    def test_empty_step_description(self):
        """Test with empty step description"""
        steps = [("Step", "completed", "")]
        result = progress_tracker(steps)
        assert result is not None

    def test_none_description(self):
        """Test with None description"""
        steps = [("Step", "completed", None)]
        result = progress_tracker(steps)
        assert result is not None

    def test_very_long_label(self):
        """Test with very long step label"""
        long_label = "A" * 100
        steps = [(long_label, "current", "Description")]
        result = progress_tracker(steps)
        assert result is not None

    def test_very_long_description(self):
        """Test with very long description"""
        long_desc = "A" * 300
        steps = [("Step", "current", long_desc)]
        result = progress_tracker(steps)
        assert result is not None

    def test_special_characters_label(self):
        """Test with special characters in label"""
        steps = [("Step @#$%^&*()", "current", "Description")]
        result = progress_tracker(steps)
        assert result is not None

    def test_invalid_status(self):
        """Test with invalid status (should handle gracefully)"""
        steps = [("Step", "invalid_status", "Description")]
        result = progress_tracker(steps)
        assert result is not None

    def test_many_steps(self):
        """Test with many steps"""
        steps = [
            (f"Step {i}", "completed" if i < 5 else "pending", f"Description {i}")
            for i in range(20)
        ]
        result = progress_tracker(steps)
        assert result is not None

    def test_current_step_out_of_range(self):
        """Test with current_step out of range"""
        steps = [
            ("Step 1", "completed", None),
            ("Step 2", "current", None),
        ]
        result = progress_tracker(steps, current_step=10)
        assert result is not None


class TestProgressTrackerIntegration:
    """Test integration scenarios"""

    def test_agent_deployment_workflow(self):
        """Test complete agent deployment workflow"""
        steps = [
            ("Initialize", "completed", "Environment setup complete"),
            ("Configure", "completed", "Configuration applied"),
            ("Build", "completed", "Docker image built"),
            ("Deploy", "current", "Deploying to cluster"),
            ("Verify", "pending", "Health checks pending"),
            ("Complete", "pending", "Workflow pending"),
        ]
        result = progress_tracker(
            steps, current_step=3, show_descriptions=True, theme="dark"
        )
        assert result is not None

    def test_multi_stage_pipeline(self):
        """Test multi-stage CI/CD pipeline"""
        steps = [
            ("Code", "completed", None),
            ("Build", "completed", None),
            ("Test", "completed", None),
            ("Stage", "current", None),
            ("Prod", "pending", None),
        ]
        result = progress_deployment_pipeline(current_step=3, theme="dark")
        assert result is not None

    def test_vertical_upgrade_process(self):
        """Test vertical upgrade process"""
        steps = [
            ("Backup", "completed", "Data backed up"),
            ("Stop", "completed", "Services stopped"),
            ("Upgrade", "current", "Installing v2.0"),
            ("Migrate", "pending", "Schema migration"),
            ("Start", "pending", "Starting services"),
            ("Verify", "pending", "Post-upgrade checks"),
        ]
        result = progress_tracker(
            steps,
            current_step=2,
            orientation="vertical",
            show_descriptions=True,
            theme="dark",
        )
        assert result is not None

    def test_error_recovery_workflow(self):
        """Test workflow with error status"""
        steps = [
            ("Step 1", "completed", "Success"),
            ("Step 2", "completed", "Success"),
            ("Step 3", "error", "Failed - connection timeout"),
            ("Step 4", "skipped", "Skipped due to error"),
            ("Step 5", "pending", "Waiting for retry"),
        ]
        result = progress_tracker(steps, current_step=2, theme="dark")
        assert result is not None

    def test_compact_workflow(self):
        """Test compact workflow without descriptions"""
        steps = [
            ("Init", "completed", None),
            ("Config", "completed", None),
            ("Deploy", "current", None),
            ("Done", "pending", None),
        ]
        result = progress_tracker(
            steps, show_descriptions=False, show_step_numbers=True, theme="dark"
        )
        assert result is not None


def test_all_steps_completed():
    """Test progress tracker with all steps completed"""
    steps = [
        ("Step 1", "completed", "Done"),
        ("Step 2", "completed", "Done"),
        ("Step 3", "completed", "Done"),
    ]
    result = progress_tracker(steps, current_step=2)
    assert result is not None


def test_all_steps_pending():
    """Test progress tracker with all steps pending"""
    steps = [
        ("Step 1", "pending", "Waiting"),
        ("Step 2", "pending", "Waiting"),
        ("Step 3", "pending", "Waiting"),
    ]
    result = progress_tracker(steps, current_step=0)
    assert result is not None


def test_horizontal_vs_vertical():
    """Test both orientations with same data"""
    steps = [
        ("Step 1", "completed", "First"),
        ("Step 2", "current", "Second"),
        ("Step 3", "pending", "Third"),
    ]
    horizontal = progress_tracker(steps, orientation="horizontal")
    vertical = progress_tracker(steps, orientation="vertical")
    assert horizontal is not None
    assert vertical is not None
