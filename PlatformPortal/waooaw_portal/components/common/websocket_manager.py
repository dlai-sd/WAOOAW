"""
WebSocket Manager Component

Real-time bidirectional communication component for live updates.
Manages WebSocket connections, subscriptions, and message handling.
"""

from typing import Optional, Callable, Dict, Any, List
import reflex as rx
from waooaw_portal.theme import get_theme


class WebSocketState(rx.State):
    """State management for WebSocket connections"""

    connected: bool = False
    last_message: str = ""
    subscriptions: List[str] = []
    error: str = ""


def websocket_manager(
    url: str,
    on_message: Optional[Callable[[str], None]] = None,
    on_connect: Optional[Callable[[], None]] = None,
    on_disconnect: Optional[Callable[[], None]] = None,
    auto_reconnect: bool = True,
    reconnect_interval: int = 5000,
    subscriptions: Optional[List[str]] = None,
    show_status: bool = True,
    theme: str = "dark",
) -> rx.Component:
    """
    WebSocket connection manager with auto-reconnect and subscriptions.

    Args:
        url: WebSocket server URL (ws:// or wss://)
        on_message: Callback when message received
        on_connect: Callback when connection established
        on_disconnect: Callback when connection lost
        auto_reconnect: Auto-reconnect on disconnect
        reconnect_interval: Reconnect delay in milliseconds
        subscriptions: List of channels to subscribe to
        show_status: Show connection status indicator
        theme: Color theme

    Returns:
        WebSocket manager component
    """
    theme_colors = get_theme(theme)

    status_indicator = None
    if show_status:
        status_indicator = rx.box(
            rx.hstack(
                rx.box(
                    width="8px",
                    height="8px",
                    border_radius="50%",
                    background=rx.cond(
                        WebSocketState.connected,
                        theme_colors["success"],
                        theme_colors["error"],
                    ),
                ),
                rx.text(
                    rx.cond(WebSocketState.connected, "Connected", "Disconnected"),
                    font_size="0.75rem",
                    color=theme_colors["text_secondary"],
                ),
                spacing="2",
                align_items="center",
            ),
            position="fixed",
            bottom="1rem",
            right="1rem",
            background=theme_colors["bg_secondary"],
            border=f"1px solid {theme_colors['border']}",
            border_radius="0.5rem",
            padding="0.5rem 0.75rem",
            z_index="1000",
        )

    return rx.fragment(
        rx.script(
            f"""
            (function() {{
                let ws = null;
                let reconnectTimer = null;
                
                function connect() {{
                    try {{
                        ws = new WebSocket('{url}');
                        
                        ws.onopen = function() {{
                            console.log('WebSocket connected');
                            // Update state
                            window.dispatchEvent(new CustomEvent('ws_connected'));
                            
                            // Subscribe to channels
                            {_generate_subscription_code(subscriptions)}
                            
                            {_generate_callback_code(on_connect)}
                        }};
                        
                        ws.onmessage = function(event) {{
                            console.log('WebSocket message:', event.data);
                            // Update state
                            window.dispatchEvent(new CustomEvent('ws_message', {{
                                detail: event.data
                            }}));
                            
                            {_generate_message_callback_code(on_message)}
                        }};
                        
                        ws.onerror = function(error) {{
                            console.error('WebSocket error:', error);
                            window.dispatchEvent(new CustomEvent('ws_error', {{
                                detail: error.message || 'Connection error'
                            }}));
                        }};
                        
                        ws.onclose = function() {{
                            console.log('WebSocket disconnected');
                            window.dispatchEvent(new CustomEvent('ws_disconnected'));
                            
                            {_generate_callback_code(on_disconnect)}
                            
                            {'scheduleReconnect();' if auto_reconnect else ''}
                        }};
                    }} catch (error) {{
                        console.error('WebSocket connection failed:', error);
                        {'scheduleReconnect();' if auto_reconnect else ''}
                    }}
                }}
                
                function scheduleReconnect() {{
                    if (reconnectTimer) clearTimeout(reconnectTimer);
                    reconnectTimer = setTimeout(connect, {reconnect_interval});
                }}
                
                function disconnect() {{
                    if (reconnectTimer) {{
                        clearTimeout(reconnectTimer);
                        reconnectTimer = null;
                    }}
                    if (ws) {{
                        ws.close();
                        ws = null;
                    }}
                }}
                
                function send(data) {{
                    if (ws && ws.readyState === WebSocket.OPEN) {{
                        ws.send(JSON.stringify(data));
                        return true;
                    }}
                    console.warn('WebSocket not connected');
                    return false;
                }}
                
                // Expose API
                window.wsManager = {{
                    connect,
                    disconnect,
                    send,
                    isConnected: () => ws && ws.readyState === WebSocket.OPEN
                }};
                
                // Auto-connect on load
                connect();
                
                // Cleanup on unload
                window.addEventListener('beforeunload', disconnect);
            }})();
            """
        ),
        status_indicator if show_status else rx.fragment(),
    )


def _generate_subscription_code(subscriptions: Optional[List[str]]) -> str:
    """Generate JavaScript code for channel subscriptions"""
    if not subscriptions:
        return ""

    sub_messages = [
        f"ws.send(JSON.stringify({{type: 'subscribe', channel: '{ch}'}}));"
        for ch in subscriptions
    ]
    return "\n".join(sub_messages)


def _generate_callback_code(callback: Optional[Callable]) -> str:
    """Generate JavaScript code for callback execution"""
    if not callback:
        return ""
    return f"// Callback: {callback.__name__}"


def _generate_message_callback_code(callback: Optional[Callable]) -> str:
    """Generate JavaScript code for message callback"""
    if not callback:
        return ""
    return f"// Message callback: {callback.__name__}"


# Helper functions for WebSocket operations
def websocket_send(channel: str, data: Dict[str, Any]) -> str:
    """
    Generate JavaScript to send WebSocket message.

    Args:
        channel: Target channel
        data: Message data

    Returns:
        JavaScript code snippet
    """
    import json

    message = json.dumps({"channel": channel, "data": data})
    return f"window.wsManager && window.wsManager.send({message})"


def websocket_subscribe(channel: str) -> str:
    """
    Generate JavaScript to subscribe to channel.

    Args:
        channel: Channel name

    Returns:
        JavaScript code snippet
    """
    return f"window.wsManager && window.wsManager.send({{type: 'subscribe', channel: '{channel}'}})"


def websocket_unsubscribe(channel: str) -> str:
    """
    Generate JavaScript to unsubscribe from channel.

    Args:
        channel: Channel name

    Returns:
        JavaScript code snippet
    """
    return f"window.wsManager && window.wsManager.send({{type: 'unsubscribe', channel: '{channel}'}})"


# Preset WebSocket managers
def websocket_agent_updates(theme: str = "dark") -> rx.Component:
    """Preset: Agent status updates WebSocket"""
    return websocket_manager(
        url="wss://api.waooaw.com/ws/agents",
        subscriptions=["agent_status", "agent_metrics"],
        show_status=True,
        theme=theme,
    )


def websocket_system_events(theme: str = "dark") -> rx.Component:
    """Preset: System events WebSocket"""
    return websocket_manager(
        url="wss://api.waooaw.com/ws/system",
        subscriptions=["system_health", "alerts"],
        show_status=True,
        theme=theme,
    )


def websocket_logs_stream(theme: str = "dark") -> rx.Component:
    """Preset: Real-time logs WebSocket"""
    return websocket_manager(
        url="wss://api.waooaw.com/ws/logs",
        subscriptions=["logs"],
        show_status=False,
        theme=theme,
    )
