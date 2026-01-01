"""
Unit tests for websocket_manager component
"""

import pytest
from waooaw_portal.components.common.websocket_manager import (
    websocket_manager,
    websocket_send,
    websocket_subscribe,
    websocket_unsubscribe,
    websocket_agent_updates,
    websocket_system_events,
    websocket_logs_stream,
)


class TestWebSocketManager:
    """Test basic WebSocket manager functionality"""

    def test_websocket_manager_basic(self):
        """Test basic WebSocket manager creation"""
        result = websocket_manager("ws://localhost:8000/ws")
        assert result is not None

    def test_websocket_manager_wss(self):
        """Test WebSocket manager with secure connection"""
        result = websocket_manager("wss://api.waooaw.com/ws")
        assert result is not None

    def test_websocket_manager_with_subscriptions(self):
        """Test WebSocket manager with channel subscriptions"""
        result = websocket_manager(
            "ws://localhost:8000/ws",
            subscriptions=["channel1", "channel2"],
        )
        assert result is not None

    def test_websocket_manager_auto_reconnect(self):
        """Test WebSocket manager with auto-reconnect"""
        result = websocket_manager(
            "ws://localhost:8000/ws",
            auto_reconnect=True,
            reconnect_interval=3000,
        )
        assert result is not None

    def test_websocket_manager_no_auto_reconnect(self):
        """Test WebSocket manager without auto-reconnect"""
        result = websocket_manager(
            "ws://localhost:8000/ws",
            auto_reconnect=False,
        )
        assert result is not None

    def test_websocket_manager_with_status(self):
        """Test WebSocket manager with status indicator"""
        result = websocket_manager(
            "ws://localhost:8000/ws",
            show_status=True,
        )
        assert result is not None

    def test_websocket_manager_without_status(self):
        """Test WebSocket manager without status indicator"""
        result = websocket_manager(
            "ws://localhost:8000/ws",
            show_status=False,
        )
        assert result is not None

    def test_websocket_manager_themes(self):
        """Test dark and light themes"""
        for theme in ["dark", "light"]:
            result = websocket_manager(
                "ws://localhost:8000/ws",
                theme=theme,
            )
            assert result is not None


class TestWebSocketHelpers:
    """Test WebSocket helper functions"""

    def test_websocket_send(self):
        """Test WebSocket send function"""
        result = websocket_send("test_channel", {"message": "hello"})
        assert result is not None
        assert isinstance(result, str)
        assert "test_channel" in result

    def test_websocket_send_empty_data(self):
        """Test WebSocket send with empty data"""
        result = websocket_send("test_channel", {})
        assert result is not None

    def test_websocket_send_complex_data(self):
        """Test WebSocket send with complex data"""
        data = {
            "type": "message",
            "payload": {"id": 123, "values": [1, 2, 3]},
        }
        result = websocket_send("test_channel", data)
        assert result is not None

    def test_websocket_subscribe(self):
        """Test WebSocket subscribe function"""
        result = websocket_subscribe("test_channel")
        assert result is not None
        assert isinstance(result, str)
        assert "test_channel" in result

    def test_websocket_unsubscribe(self):
        """Test WebSocket unsubscribe function"""
        result = websocket_unsubscribe("test_channel")
        assert result is not None
        assert isinstance(result, str)
        assert "test_channel" in result


class TestPresetWebSocketManagers:
    """Test preset WebSocket managers"""

    def test_websocket_agent_updates(self):
        """Test agent updates WebSocket preset"""
        result = websocket_agent_updates()
        assert result is not None

    def test_websocket_agent_updates_theme(self):
        """Test agent updates with dark theme"""
        result = websocket_agent_updates(theme="dark")
        assert result is not None

    def test_websocket_system_events(self):
        """Test system events WebSocket preset"""
        result = websocket_system_events()
        assert result is not None

    def test_websocket_system_events_theme(self):
        """Test system events with light theme"""
        result = websocket_system_events(theme="light")
        assert result is not None

    def test_websocket_logs_stream(self):
        """Test logs stream WebSocket preset"""
        result = websocket_logs_stream()
        assert result is not None

    def test_websocket_logs_stream_theme(self):
        """Test logs stream with theme"""
        result = websocket_logs_stream(theme="dark")
        assert result is not None


class TestWebSocketEdgeCases:
    """Test edge cases"""

    def test_empty_url(self):
        """Test with empty URL"""
        result = websocket_manager("")
        assert result is not None

    def test_invalid_url_scheme(self):
        """Test with invalid URL scheme"""
        result = websocket_manager("http://localhost:8000/ws")
        assert result is not None

    def test_empty_subscriptions_list(self):
        """Test with empty subscriptions list"""
        result = websocket_manager(
            "ws://localhost:8000/ws",
            subscriptions=[],
        )
        assert result is not None

    def test_many_subscriptions(self):
        """Test with many subscriptions"""
        subscriptions = [f"channel{i}" for i in range(20)]
        result = websocket_manager(
            "ws://localhost:8000/ws",
            subscriptions=subscriptions,
        )
        assert result is not None

    def test_very_short_reconnect_interval(self):
        """Test with very short reconnect interval"""
        result = websocket_manager(
            "ws://localhost:8000/ws",
            auto_reconnect=True,
            reconnect_interval=100,
        )
        assert result is not None

    def test_very_long_reconnect_interval(self):
        """Test with very long reconnect interval"""
        result = websocket_manager(
            "ws://localhost:8000/ws",
            auto_reconnect=True,
            reconnect_interval=60000,
        )
        assert result is not None


class TestWebSocketIntegration:
    """Test integration scenarios"""

    def test_real_time_dashboard(self):
        """Test WebSocket for real-time dashboard"""
        result = websocket_manager(
            "wss://api.waooaw.com/ws/dashboard",
            subscriptions=["metrics", "alerts", "logs"],
            auto_reconnect=True,
            show_status=True,
            theme="dark",
        )
        assert result is not None

    def test_agent_monitoring(self):
        """Test WebSocket for agent monitoring"""
        result = websocket_agent_updates(theme="dark")
        assert result is not None

    def test_multi_channel_subscription(self):
        """Test multiple channel subscriptions"""
        channels = [
            "agent_status",
            "agent_metrics",
            "system_health",
            "alerts",
        ]
        result = websocket_manager(
            "wss://api.waooaw.com/ws",
            subscriptions=channels,
            auto_reconnect=True,
        )
        assert result is not None


def test_websocket_send_special_characters():
    """Test WebSocket send with special characters"""
    data = {
        "message": "Hello! @#$%^&*(){}[]|\\:;\"'<>,.?/~`",
    }
    result = websocket_send("test", data)
    assert result is not None


def test_websocket_subscribe_special_channel_name():
    """Test subscribe with special channel name"""
    result = websocket_subscribe("channel:123-abc_def")
    assert result is not None
