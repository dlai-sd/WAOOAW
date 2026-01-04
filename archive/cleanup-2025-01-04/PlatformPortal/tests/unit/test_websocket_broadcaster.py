"""
Unit tests for WebSocketBroadcaster service
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from waooaw_portal.services.websocket_broadcaster import (
    WebSocketBroadcaster,
    WebSocketConnection,
)


@pytest.fixture
def broadcaster():
    """Create broadcaster instance"""
    return WebSocketBroadcaster(cleanup_interval=1)


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket"""
    ws = Mock()
    ws.send_text = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


class TestWebSocketBroadcaster:
    """Test WebSocketBroadcaster lifecycle and connections"""

    @pytest.mark.asyncio
    async def test_start_stop(self, broadcaster):
        """Test broadcaster start/stop"""
        await broadcaster.start()
        assert broadcaster._running is True

        await broadcaster.stop()
        assert broadcaster._running is False

    @pytest.mark.asyncio
    async def test_connect_disconnect(self, broadcaster, mock_websocket):
        """Test connection management"""
        await broadcaster.start()

        # Connect
        connection = await broadcaster.connect("test-1", mock_websocket)
        assert connection.connection_id == "test-1"
        assert connection.websocket == mock_websocket
        assert "test-1" in broadcaster.connections

        # Disconnect
        await broadcaster.disconnect("test-1")
        assert "test-1" not in broadcaster.connections

        await broadcaster.stop()

    @pytest.mark.asyncio
    async def test_connect_with_metadata(self, broadcaster, mock_websocket):
        """Test connection with metadata"""
        await broadcaster.start()

        metadata = {"user_id": "123", "role": "admin"}
        connection = await broadcaster.connect("test-1", mock_websocket, metadata)

        assert connection.metadata == metadata

        await broadcaster.stop()

    @pytest.mark.asyncio
    async def test_disconnect_all(self, broadcaster, mock_websocket):
        """Test disconnecting all connections"""
        await broadcaster.start()

        # Connect multiple
        await broadcaster.connect("test-1", mock_websocket)
        await broadcaster.connect("test-2", mock_websocket)
        await broadcaster.connect("test-3", mock_websocket)

        assert len(broadcaster.connections) == 3

        # Disconnect all
        await broadcaster.disconnect_all()
        assert len(broadcaster.connections) == 0

        await broadcaster.stop()


class TestWebSocketSubscriptions:
    """Test subscription management"""

    @pytest.mark.asyncio
    async def test_subscribe_unsubscribe(self, broadcaster, mock_websocket):
        """Test subscription lifecycle"""
        await broadcaster.start()

        await broadcaster.connect("test-1", mock_websocket)

        # Subscribe
        await broadcaster.subscribe("test-1", "updates")
        assert "updates" in broadcaster.subscriptions
        assert "test-1" in broadcaster.subscriptions["updates"]

        # Unsubscribe
        await broadcaster.unsubscribe("test-1", "updates")
        assert "test-1" not in broadcaster.subscriptions.get("updates", set())

        await broadcaster.stop()

    @pytest.mark.asyncio
    async def test_multiple_subscriptions(self, broadcaster, mock_websocket):
        """Test multiple subscriptions per connection"""
        await broadcaster.start()

        await broadcaster.connect("test-1", mock_websocket)

        # Subscribe to multiple channels
        await broadcaster.subscribe("test-1", "updates")
        await broadcaster.subscribe("test-1", "alerts")
        await broadcaster.subscribe("test-1", "logs")

        connection = broadcaster.connections["test-1"]
        assert len(connection.subscriptions) == 3
        assert "updates" in connection.subscriptions
        assert "alerts" in connection.subscriptions
        assert "logs" in connection.subscriptions

        await broadcaster.stop()

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent(self, broadcaster, mock_websocket):
        """Test unsubscribing from non-subscribed channel"""
        await broadcaster.start()

        await broadcaster.connect("test-1", mock_websocket)
        await broadcaster.unsubscribe("test-1", "nonexistent")  # Should not error

        await broadcaster.stop()


class TestWebSocketBroadcasting:
    """Test message broadcasting"""

    @pytest.mark.asyncio
    async def test_broadcast_to_channel(self, broadcaster, mock_websocket):
        """Test broadcasting to channel subscribers"""
        await broadcaster.start()

        # Connect and subscribe
        await broadcaster.connect("test-1", mock_websocket)
        await broadcaster.subscribe("test-1", "updates")

        # Broadcast
        await broadcaster.broadcast("updates", {"data": "test"})

        # Verify message sent
        mock_websocket.send_json.assert_called_once()

        await broadcaster.stop()

    @pytest.mark.asyncio
    async def test_broadcast_multiple_subscribers(self, broadcaster):
        """Test broadcasting to multiple subscribers"""
        await broadcaster.start()

        ws1 = Mock()
        ws1.send_json = AsyncMock()
        ws2 = Mock()
        ws2.send_json = AsyncMock()

        # Connect multiple clients
        await broadcaster.connect("test-1", ws1)
        await broadcaster.connect("test-2", ws2)
        await broadcaster.subscribe("test-1", "updates")
        await broadcaster.subscribe("test-2", "updates")

        # Broadcast
        await broadcaster.broadcast("updates", {"data": "test"})

        # Verify both received
        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()

        await broadcaster.stop()

    @pytest.mark.asyncio
    async def test_broadcast_with_buffer(self, broadcaster, mock_websocket):
        """Test message buffering"""
        await broadcaster.start()

        # Broadcast without subscribers (should buffer)
        await broadcaster.broadcast("updates", {"data": "test"}, buffer=True)

        assert "updates" in broadcaster.message_buffers
        assert len(broadcaster.message_buffers["updates"]) == 1

        # Connect and subscribe (should receive buffered)
        await broadcaster.connect("test-1", mock_websocket)
        await broadcaster.subscribe("test-1", "updates")

        await asyncio.sleep(0.1)  # Allow buffer processing

        mock_websocket.send_json.assert_called()

        await broadcaster.stop()

    @pytest.mark.asyncio
    async def test_send_to_specific_connection(self, broadcaster, mock_websocket):
        """Test sending to specific connection"""
        await broadcaster.start()

        await broadcaster.connect("test-1", mock_websocket)

        # Send directly
        await broadcaster.send_to("test-1", {"data": "private"})

        mock_websocket.send_json.assert_called_once_with({"data": "private"})

        await broadcaster.stop()


class TestWebSocketCleanup:
    """Test connection cleanup"""

    @pytest.mark.asyncio
    async def test_cleanup_dead_connections(self, broadcaster, mock_websocket):
        """Test automatic cleanup of dead connections"""
        broadcaster.connection_timeout = 0.1  # Short timeout for testing
        await broadcaster.start()

        connection = await broadcaster.connect("test-1", mock_websocket)

        # Modify last_active to simulate timeout
        connection.last_active_at = datetime.now() - timedelta(seconds=1)

        # Wait for cleanup
        await asyncio.sleep(1.5)

        assert "test-1" not in broadcaster.connections

        await broadcaster.stop()


class TestWebSocketStats:
    """Test statistics and monitoring"""

    @pytest.mark.asyncio
    async def test_get_stats(self, broadcaster, mock_websocket):
        """Test getting broadcaster statistics"""
        await broadcaster.start()

        # Create connections and subscriptions
        await broadcaster.connect("test-1", mock_websocket)
        await broadcaster.subscribe("test-1", "updates")
        await broadcaster.subscribe("test-1", "alerts")

        await broadcaster.connect("test-2", mock_websocket)
        await broadcaster.subscribe("test-2", "updates")

        stats = broadcaster.get_stats()

        assert stats["total_connections"] == 2
        assert stats["total_subscriptions"] == 2  # Unique channels
        assert "updates" in stats["channel_subscribers"]
        assert stats["channel_subscribers"]["updates"] == 2

        await broadcaster.stop()

    @pytest.mark.asyncio
    async def test_get_connection_info(self, broadcaster, mock_websocket):
        """Test getting connection information"""
        await broadcaster.start()

        metadata = {"user_id": "123"}
        await broadcaster.connect("test-1", mock_websocket, metadata)
        await broadcaster.subscribe("test-1", "updates")

        info = broadcaster.get_connection_info("test-1")

        assert info["connection_id"] == "test-1"
        assert info["metadata"] == metadata
        assert "updates" in info["subscriptions"]
        assert "connected_at" in info
        assert "last_active_at" in info

        await broadcaster.stop()

    @pytest.mark.asyncio
    async def test_get_nonexistent_connection_info(self, broadcaster):
        """Test getting info for nonexistent connection"""
        await broadcaster.start()

        info = broadcaster.get_connection_info("nonexistent")
        assert info is None

        await broadcaster.stop()


class TestWebSocketEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_connection(self, broadcaster):
        """Test disconnecting nonexistent connection"""
        await broadcaster.start()

        await broadcaster.disconnect("nonexistent")  # Should not error

        await broadcaster.stop()

    @pytest.mark.asyncio
    async def test_subscribe_without_connection(self, broadcaster):
        """Test subscribing without connection"""
        await broadcaster.start()

        await broadcaster.subscribe("nonexistent", "updates")  # Should not error

        await broadcaster.stop()

    @pytest.mark.asyncio
    async def test_broadcast_to_empty_channel(self, broadcaster):
        """Test broadcasting to channel with no subscribers"""
        await broadcaster.start()

        await broadcaster.broadcast("empty", {"data": "test"})  # Should not error

        await broadcaster.stop()

    @pytest.mark.asyncio
    async def test_send_to_nonexistent_connection(self, broadcaster):
        """Test sending to nonexistent connection"""
        await broadcaster.start()

        await broadcaster.send_to("nonexistent", {"data": "test"})  # Should not error

        await broadcaster.stop()
