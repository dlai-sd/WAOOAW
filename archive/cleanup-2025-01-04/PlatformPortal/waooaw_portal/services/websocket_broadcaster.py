"""
WebSocket Broadcaster Service

Manages WebSocket connections and broadcasts messages to subscribed clients.
Handles channel subscriptions, message routing, and connection lifecycle.
"""

from typing import Dict, Set, Optional, Any, Callable
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class WebSocketConnection:
    """Represents a WebSocket client connection"""

    connection_id: str
    websocket: Any  # WebSocket connection object
    subscriptions: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class WebSocketBroadcaster:
    """
    WebSocket message broadcaster with channel-based subscriptions.

    Features:
    - Channel-based pub/sub messaging
    - Connection lifecycle management
    - Automatic cleanup of dead connections
    - Message buffering for offline clients
    - Connection statistics and monitoring
    """

    def __init__(self, max_buffer_size: int = 100):
        """
        Initialize WebSocket broadcaster.

        Args:
            max_buffer_size: Maximum messages to buffer per channel
        """
        self.connections: Dict[str, WebSocketConnection] = {}
        self.channels: Dict[str, Set[str]] = {}  # channel -> connection_ids
        self.message_buffer: Dict[str, list] = {}  # channel -> messages
        self.max_buffer_size = max_buffer_size
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the broadcaster and cleanup task"""
        self._cleanup_task = asyncio.create_task(self._cleanup_dead_connections())
        logger.info("WebSocket broadcaster started")

    async def stop(self):
        """Stop the broadcaster and cleanup"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        await self.disconnect_all()
        logger.info("WebSocket broadcaster stopped")

    async def connect(
        self,
        connection_id: str,
        websocket: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WebSocketConnection:
        """
        Register a new WebSocket connection.

        Args:
            connection_id: Unique connection identifier
            websocket: WebSocket connection object
            metadata: Optional connection metadata

        Returns:
            WebSocketConnection object
        """
        connection = WebSocketConnection(
            connection_id=connection_id,
            websocket=websocket,
            metadata=metadata or {},
        )
        self.connections[connection_id] = connection
        logger.info(f"Connection established: {connection_id}")
        return connection

    async def disconnect(self, connection_id: str):
        """
        Disconnect and cleanup a WebSocket connection.

        Args:
            connection_id: Connection identifier
        """
        if connection_id in self.connections:
            connection = self.connections[connection_id]

            # Unsubscribe from all channels
            for channel in list(connection.subscriptions):
                await self.unsubscribe(connection_id, channel)

            # Remove connection
            del self.connections[connection_id]
            logger.info(f"Connection disconnected: {connection_id}")

    async def disconnect_all(self):
        """Disconnect all active connections"""
        connection_ids = list(self.connections.keys())
        for conn_id in connection_ids:
            await self.disconnect(conn_id)
        logger.info("All connections disconnected")

    async def subscribe(self, connection_id: str, channel: str):
        """
        Subscribe a connection to a channel.

        Args:
            connection_id: Connection identifier
            channel: Channel name
        """
        if connection_id not in self.connections:
            logger.warning(f"Subscribe failed: connection {connection_id} not found")
            return

        connection = self.connections[connection_id]
        connection.subscriptions.add(channel)

        if channel not in self.channels:
            self.channels[channel] = set()
        self.channels[channel].add(connection_id)

        logger.info(f"Connection {connection_id} subscribed to {channel}")

        # Send buffered messages
        if channel in self.message_buffer:
            for message in self.message_buffer[channel]:
                await self._send_message(connection_id, message)

    async def unsubscribe(self, connection_id: str, channel: str):
        """
        Unsubscribe a connection from a channel.

        Args:
            connection_id: Connection identifier
            channel: Channel name
        """
        if connection_id in self.connections:
            self.connections[connection_id].subscriptions.discard(channel)

        if channel in self.channels:
            self.channels[channel].discard(connection_id)
            if not self.channels[channel]:
                del self.channels[channel]

        logger.info(f"Connection {connection_id} unsubscribed from {channel}")

    async def broadcast(
        self, channel: str, message: Dict[str, Any], buffer: bool = True
    ):
        """
        Broadcast a message to all subscribers of a channel.

        Args:
            channel: Channel name
            message: Message data (will be JSON serialized)
            buffer: Whether to buffer message for offline clients
        """
        # Buffer message
        if buffer:
            if channel not in self.message_buffer:
                self.message_buffer[channel] = []
            self.message_buffer[channel].append(message)

            # Trim buffer
            if len(self.message_buffer[channel]) > self.max_buffer_size:
                self.message_buffer[channel] = self.message_buffer[channel][
                    -self.max_buffer_size :
                ]

        # Broadcast to subscribers
        if channel in self.channels:
            tasks = [
                self._send_message(conn_id, message)
                for conn_id in self.channels[channel]
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Count successes/failures
            successes = sum(1 for r in results if r is True)
            failures = len(results) - successes

            logger.info(f"Broadcast to {channel}: {successes} sent, {failures} failed")

    async def send_to(self, connection_id: str, message: Dict[str, Any]):
        """
        Send a message to a specific connection.

        Args:
            connection_id: Connection identifier
            message: Message data
        """
        await self._send_message(connection_id, message)

    async def _send_message(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """
        Internal method to send message to connection.

        Returns:
            True if sent successfully, False otherwise
        """
        if connection_id not in self.connections:
            return False

        connection = self.connections[connection_id]
        try:
            # Serialize and send
            data = json.dumps(message)
            await connection.websocket.send(data)
            connection.last_activity = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {connection_id}: {e}")
            # Mark for disconnection
            await self.disconnect(connection_id)
            return False

    async def _cleanup_dead_connections(self):
        """Periodic cleanup of inactive connections"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                now = datetime.now()
                stale_connections = [
                    conn_id
                    for conn_id, conn in self.connections.items()
                    if (now - conn.last_activity).total_seconds() > 300  # 5 min timeout
                ]

                for conn_id in stale_connections:
                    logger.info(f"Cleaning up stale connection: {conn_id}")
                    await self.disconnect(conn_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get broadcaster statistics.

        Returns:
            Dictionary with connection and channel stats
        """
        return {
            "total_connections": len(self.connections),
            "total_channels": len(self.channels),
            "channel_subscribers": {
                channel: len(subs) for channel, subs in self.channels.items()
            },
            "buffer_sizes": {
                channel: len(msgs) for channel, msgs in self.message_buffer.items()
            },
        }

    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific connection.

        Args:
            connection_id: Connection identifier

        Returns:
            Connection information or None if not found
        """
        if connection_id not in self.connections:
            return None

        conn = self.connections[connection_id]
        return {
            "connection_id": conn.connection_id,
            "subscriptions": list(conn.subscriptions),
            "connected_at": conn.connected_at.isoformat(),
            "last_activity": conn.last_activity.isoformat(),
            "metadata": conn.metadata,
        }
