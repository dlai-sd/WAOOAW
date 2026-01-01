"""
Unit tests for context_selector component
"""

import pytest
from waooaw_portal.components.common.context_selector import (
    context_selector,
    context_selector_agents,
    context_selector_environment,
    context_selector_services,
    context_selector_time_range,
)


class TestContextSelector:
    """Test basic context selector functionality"""

    def test_context_selector_basic(self):
        """Test basic context selector creation"""
        items = [
            ("id1", "Item 1", "I1"),
            ("id2", "Item 2", "I2"),
        ]
        result = context_selector(items)
        assert result is not None

    def test_context_selector_empty(self):
        """Test empty context selector"""
        result = context_selector([])
        assert result is not None

    def test_context_selector_single_item(self):
        """Test context selector with single item"""
        items = [("id1", "Single Item", None)]
        result = context_selector(items)
        assert result is not None

    def test_context_selector_with_selected(self):
        """Test context selector with pre-selected items"""
        items = [
            ("id1", "Item 1", None),
            ("id2", "Item 2", None),
        ]
        result = context_selector(items, selected=["id1"])
        assert result is not None

    def test_context_selector_multi_select(self):
        """Test multi-select enabled"""
        items = [
            ("id1", "Item 1", None),
            ("id2", "Item 2", None),
        ]
        result = context_selector(items, multi_select=True)
        assert result is not None

    def test_context_selector_single_select(self):
        """Test single-select (multi_select=False)"""
        items = [
            ("id1", "Item 1", None),
            ("id2", "Item 2", None),
        ]
        result = context_selector(items, multi_select=False)
        assert result is not None

    def test_context_selector_searchable(self):
        """Test searchable enabled"""
        items = [
            ("id1", "Item 1", None),
            ("id2", "Item 2", None),
        ]
        result = context_selector(items, searchable=True)
        assert result is not None

    def test_context_selector_not_searchable(self):
        """Test searchable disabled"""
        items = [
            ("id1", "Item 1", None),
            ("id2", "Item 2", None),
        ]
        result = context_selector(items, searchable=False)
        assert result is not None

    def test_context_selector_placeholder(self):
        """Test custom placeholder"""
        items = [("id1", "Item 1", None)]
        result = context_selector(items, placeholder="Choose an option...")
        assert result is not None

    def test_context_selector_max_height(self):
        """Test custom max height"""
        items = [("id1", "Item 1", None)]
        result = context_selector(items, max_height="400px")
        assert result is not None

    def test_context_selector_with_icons(self):
        """Test with icons enabled"""
        items = [
            ("id1", "Item 1", "I1"),
            ("id2", "Item 2", "I2"),
        ]
        result = context_selector(items, show_icons=True)
        assert result is not None

    def test_context_selector_without_icons(self):
        """Test with icons disabled"""
        items = [
            ("id1", "Item 1", "I1"),
            ("id2", "Item 2", "I2"),
        ]
        result = context_selector(items, show_icons=False)
        assert result is not None

    def test_context_selector_themes(self):
        """Test dark and light themes"""
        items = [("id1", "Item 1", None)]
        for theme in ["dark", "light"]:
            result = context_selector(items, theme=theme)
            assert result is not None


class TestPresetContextSelectors:
    """Test preset context selector components"""

    def test_context_selector_agents(self):
        """Test agents selector preset"""
        agents = [
            ("agent1", "CoE Agent #1", "A1"),
            ("agent2", "CoE Agent #2", "A2"),
        ]
        result = context_selector_agents(agents)
        assert result is not None

    def test_context_selector_agents_theme(self):
        """Test agents selector with theme"""
        agents = [("agent1", "CoE Agent #1", "A1")]
        result = context_selector_agents(agents, theme="dark")
        assert result is not None

    def test_context_selector_environment(self):
        """Test environment selector preset"""
        result = context_selector_environment()
        assert result is not None

    def test_context_selector_environment_selected(self):
        """Test environment selector with pre-selected"""
        result = context_selector_environment(selected="prod")
        assert result is not None

    def test_context_selector_environment_theme(self):
        """Test environment selector with theme"""
        result = context_selector_environment(theme="light")
        assert result is not None

    def test_context_selector_services(self):
        """Test services selector preset"""
        services = [
            ("svc1", "API Gateway"),
            ("svc2", "Database"),
        ]
        result = context_selector_services(services)
        assert result is not None

    def test_context_selector_services_theme(self):
        """Test services selector with theme"""
        services = [("svc1", "API Gateway")]
        result = context_selector_services(services, theme="dark")
        assert result is not None

    def test_context_selector_time_range(self):
        """Test time range selector preset"""
        result = context_selector_time_range()
        assert result is not None

    def test_context_selector_time_range_theme(self):
        """Test time range selector with theme"""
        result = context_selector_time_range(theme="dark")
        assert result is not None


class TestContextSelectorEdgeCases:
    """Test edge cases"""

    def test_empty_item_label(self):
        """Test with empty item label"""
        items = [("id1", "", None)]
        result = context_selector(items)
        assert result is not None

    def test_empty_item_id(self):
        """Test with empty item ID"""
        items = [("", "Label", None)]
        result = context_selector(items)
        assert result is not None

    def test_none_icon(self):
        """Test with None icon"""
        items = [("id1", "Label", None)]
        result = context_selector(items, show_icons=True)
        assert result is not None

    def test_very_long_label(self):
        """Test with very long label"""
        long_label = "A" * 200
        items = [("id1", long_label, None)]
        result = context_selector(items)
        assert result is not None

    def test_special_characters_label(self):
        """Test with special characters in label"""
        items = [("id1", "Label @#$%^&*()", None)]
        result = context_selector(items)
        assert result is not None

    def test_many_items(self):
        """Test with many items"""
        items = [(f"id{i}", f"Item {i}", f"I{i}") for i in range(100)]
        result = context_selector(items)
        assert result is not None

    def test_selected_non_existent_id(self):
        """Test with selected ID that doesn't exist"""
        items = [("id1", "Item 1", None)]
        result = context_selector(items, selected=["non_existent"])
        assert result is not None

    def test_multiple_selected_single_select(self):
        """Test multiple selected items with single select"""
        items = [
            ("id1", "Item 1", None),
            ("id2", "Item 2", None),
        ]
        result = context_selector(items, selected=["id1", "id2"], multi_select=False)
        assert result is not None

    def test_empty_placeholder(self):
        """Test with empty placeholder"""
        items = [("id1", "Item 1", None)]
        result = context_selector(items, placeholder="")
        assert result is not None

    def test_very_small_max_height(self):
        """Test with very small max height"""
        items = [("id1", "Item 1", None)]
        result = context_selector(items, max_height="50px")
        assert result is not None

    def test_very_large_max_height(self):
        """Test with very large max height"""
        items = [("id1", "Item 1", None)]
        result = context_selector(items, max_height="2000px")
        assert result is not None


class TestContextSelectorIntegration:
    """Test integration scenarios"""

    def test_agent_filter_dashboard(self):
        """Test agent filtering in dashboard"""
        agents = [
            ("agent1", "CoE Agent #1", "A1"),
            ("agent2", "CoE Agent #2", "A2"),
            ("agent3", "CoE Agent #3", "A3"),
        ]
        result = context_selector_agents(agents, theme="dark")
        assert result is not None

    def test_environment_switcher(self):
        """Test environment switching"""
        result = context_selector_environment(selected="staging", theme="dark")
        assert result is not None

    def test_service_filter_logs(self):
        """Test service filtering for logs view"""
        services = [
            ("api", "API Gateway"),
            ("db", "PostgreSQL"),
            ("cache", "Redis"),
            ("queue", "RabbitMQ"),
        ]
        result = context_selector_services(services, theme="dark")
        assert result is not None

    def test_time_range_metrics(self):
        """Test time range selection for metrics"""
        result = context_selector_time_range(theme="dark")
        assert result is not None

    def test_multi_level_filtering(self):
        """Test multiple context selectors together"""
        agents = [("agent1", "Agent 1", "A1")]
        services = [("svc1", "Service 1")]

        agent_selector = context_selector_agents(agents)
        env_selector = context_selector_environment(selected="prod")
        time_selector = context_selector_time_range()

        assert agent_selector is not None
        assert env_selector is not None
        assert time_selector is not None

    def test_searchable_large_list(self):
        """Test searchable selector with large item list"""
        items = [(f"item{i}", f"Item {i}", f"I{i}") for i in range(50)]
        result = context_selector(
            items, searchable=True, multi_select=True, theme="dark"
        )
        assert result is not None


def test_all_preset_selectors():
    """Test all preset selectors can be created"""
    agents = [("a1", "Agent 1", "A1")]
    services = [("s1", "Service 1")]

    selectors = [
        context_selector_agents(agents),
        context_selector_environment(),
        context_selector_services(services),
        context_selector_time_range(),
    ]

    for selector in selectors:
        assert selector is not None


def test_context_selector_mixed_configs():
    """Test context selector with mixed configurations"""
    items = [
        ("id1", "Item 1", "I1"),
        ("id2", "Item 2", None),
        ("id3", "Item 3", "I3"),
    ]
    result = context_selector(
        items,
        selected=["id1", "id3"],
        multi_select=True,
        searchable=True,
        placeholder="Select items...",
        max_height="250px",
        show_icons=True,
        theme="dark",
    )
    assert result is not None


def test_context_selector_no_options():
    """Test context selector behavior with no items and no selection"""
    result = context_selector([], selected=None, placeholder="No items available")
    assert result is not None
