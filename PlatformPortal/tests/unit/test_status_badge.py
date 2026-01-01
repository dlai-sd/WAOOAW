"""
Unit tests for Status Badge Component
Tests status_badge.py functionality
"""

import pytest
from waooaw_portal.components.common.status_badge import (
    status_badge,
    status_badge_list,
    badge_online,
    badge_offline,
    badge_working,
    badge_unknown,
)
from waooaw_portal.theme import get_status_color, get_status_emoji


class TestStatusBadge:
    """Test suite for status badge component."""
    
    def test_status_badge_basic(self):
        """Test basic status badge creation."""
        badge = status_badge("online", "Test Online")
        assert badge is not None
    
    def test_status_badge_all_status_types(self):
        """Test all supported status types."""
        statuses = [
            "healthy", "success", "online", "active",
            "degraded", "warning", "working", "pending",
            "critical", "error", "failed", "offline",
            "info", "unknown", "stopped",
        ]
        
        for status in statuses:
            badge = status_badge(status)
            assert badge is not None
    
    def test_status_badge_with_custom_label(self):
        """Test badge with custom label."""
        badge = status_badge("online", "Custom Label")
        assert badge is not None
    
    def test_status_badge_without_emoji(self):
        """Test badge without emoji indicator."""
        badge = status_badge("online", "No Emoji", show_emoji=False)
        assert badge is not None
    
    def test_status_badge_sizes(self):
        """Test different badge sizes."""
        for size in ["sm", "md", "lg"]:
            badge = status_badge("online", size=size)
            assert badge is not None
    
    def test_status_badge_themes(self):
        """Test dark and light themes."""
        for theme in ["dark", "light"]:
            badge = status_badge("online", theme=theme)
            assert badge is not None
    
    def test_status_badge_default_label(self):
        """Test badge uses status name as default label."""
        # When no label provided, should use capitalized status name
        badge = status_badge("online")
        assert badge is not None
    
    def test_status_badge_colors(self):
        """Test status colors are correctly mapped."""
        # Test color helper function
        assert get_status_color("online") == "#10b981"  # Success green
        assert get_status_color("warning") == "#f59e0b"  # Warning yellow
        assert get_status_color("error") == "#ef4444"    # Error red
        assert get_status_color("unknown") == "#71717a"  # Gray
    
    def test_status_badge_emojis(self):
        """Test status emojis are correctly mapped."""
        assert get_status_emoji("online") == "🟢"
        assert get_status_emoji("warning") == "🟡"
        assert get_status_emoji("error") == "🔴"
        assert get_status_emoji("unknown") == "⚫"
    
    def test_status_badge_list(self):
        """Test multiple badges in a list."""
        statuses = [
            ("online", "API"),
            ("warning", "Queue"),
            ("error", "DB"),
        ]
        badge_list = status_badge_list(statuses)
        assert badge_list is not None
    
    def test_status_badge_list_empty(self):
        """Test empty badge list."""
        badge_list = status_badge_list([])
        assert badge_list is not None


class TestPresetBadges:
    """Test preset badge functions."""
    
    def test_badge_online(self):
        """Test online preset badge."""
        badge = badge_online()
        assert badge is not None
        
        badge_custom = badge_online("Custom Online")
        assert badge_custom is not None
    
    def test_badge_offline(self):
        """Test offline preset badge."""
        badge = badge_offline()
        assert badge is not None
    
    def test_badge_working(self):
        """Test working preset badge."""
        badge = badge_working()
        assert badge is not None
    
    def test_badge_unknown(self):
        """Test unknown preset badge."""
        badge = badge_unknown()
        assert badge is not None


class TestStatusBadgeEdgeCases:
    """Test edge cases and error handling."""
    
    def test_status_badge_invalid_status(self):
        """Test badge with invalid status defaults to unknown."""
        # Should not crash, should default to unknown color
        badge = status_badge("invalid_status_type")
        assert badge is not None
    
    def test_status_badge_empty_label(self):
        """Test badge with empty string label."""
        badge = status_badge("online", "")
        assert badge is not None
    
    def test_status_badge_long_label(self):
        """Test badge with very long label."""
        long_label = "A" * 100
        badge = status_badge("online", long_label)
        assert badge is not None
    
    def test_status_badge_special_characters(self):
        """Test badge with special characters in label."""
        badge = status_badge("online", "Test: <>&\"'")
        assert badge is not None


class TestStatusBadgeIntegration:
    """Integration tests for status badge in real-world scenarios."""
    
    def test_agent_status_badges(self):
        """Test badges for agent status display."""
        agent_statuses = [
            ("online", "WowMemory"),
            ("online", "WowOrchestrator"),
            ("working", "WowCustomerContext"),
            ("offline", "WowCodeReview"),
        ]
        
        for status, agent in agent_statuses:
            badge = status_badge(status, agent)
            assert badge is not None
    
    def test_system_health_badges(self):
        """Test badges for system health monitoring."""
        health_statuses = [
            ("healthy", "API"),
            ("degraded", "Database"),
            ("critical", "Queue"),
            ("unknown", "Cache"),
        ]
        
        badge_list = status_badge_list(health_statuses)
        assert badge_list is not None
    
    def test_workflow_step_badges(self):
        """Test badges for workflow steps."""
        workflow_steps = [
            ("success", "Step 1: Provision"),
            ("success", "Step 2: Deploy"),
            ("working", "Step 3: Health Check"),
            ("pending", "Step 4: Activate"),
        ]
        
        for status, step in workflow_steps:
            badge = status_badge(status, step)
            assert badge is not None


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================

@pytest.fixture
def sample_statuses():
    """Fixture providing sample status data."""
    return [
        ("online", "Service A"),
        ("warning", "Service B"),
        ("error", "Service C"),
        ("unknown", "Service D"),
    ]


def test_with_fixture(sample_statuses):
    """Test using fixture data."""
    badge_list = status_badge_list(sample_statuses)
    assert badge_list is not None
