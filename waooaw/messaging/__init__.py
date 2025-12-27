"""
Messaging module for WAOOAW agent communication.

Provides message bus infrastructure for event-driven agent wake-up
and inter-agent communication.
"""

from waooaw.messaging.message_bus import MessageBus, Message

__all__ = ["MessageBus", "Message"]
