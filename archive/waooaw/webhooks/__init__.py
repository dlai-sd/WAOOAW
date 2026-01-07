"""
WAOOAW Webhooks - GitHub webhook handlers and event transformation

This module provides webhook endpoints that receive GitHub events
and transform them into message bus events for agent wake-up.
"""

from .github_webhook import GitHubWebhookHandler, WebhookEvent

__all__ = ["GitHubWebhookHandler", "WebhookEvent"]
