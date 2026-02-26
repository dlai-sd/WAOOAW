"""E3-S1 — NotificationService.

Single entry-point for dispatching outbound notifications.

Usage::

    from services.notification_service import NotificationService

    NotificationService().send(
        channel="email",
        destination="user@example.com",
        template="welcome",
        context={"first_name": "Alice", "business_name": "Acme Ltd"},
    )

Supported channels: ``email`` (more to follow).
Supported templates: ``welcome``, ``otp`` (rendered via Jinja2).

Templates are resolved from ``<project_root>/templates/<channel>/<template>.html``.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

_SUPPORTED_CHANNELS: frozenset[str] = frozenset({"email"})


def _render_template(channel: str, template: str, context: dict) -> str:
    """Render a Jinja2 HTML email template from disk.

    Falls back to a minimal inline HTML string if the template file is not
    found (so the notification still fires in environments without the
    templates directory).
    """
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape

        template_dir = _TEMPLATES_DIR / channel
        env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html"]),
        )
        tmpl = env.get_template(f"{template}.html")
        return tmpl.render(**context)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "NotificationService: failed to render %s/%s.html — %s",
            channel,
            template,
            exc,
        )
        return ""  # Callers fall back to inline text/HTML


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class NotificationService:
    """Dispatch outbound notifications via Celery tasks.

    Currently supports the ``email`` channel only.
    Task enqueueing is fire-and-forget — caller is never blocked.
    """

    def send(
        self,
        *,
        channel: str,
        destination: str,
        template: str,
        context: dict,
    ) -> None:
        """Enqueue a notification.

        Args:
            channel: Delivery channel — one of ``{"email"}``.
            destination: Target address (email or phone number).
            template: Template name (``welcome``, ``otp``, …).
            context: Key/value pairs passed to the Jinja2 template and task.

        Raises:
            ValueError: If *channel* is not supported.
        """
        if channel not in _SUPPORTED_CHANNELS:
            raise ValueError(
                f"NotificationService: unsupported channel {channel!r}. "
                f"Supported: {sorted(_SUPPORTED_CHANNELS)}"
            )

        if channel == "email":
            self._send_email(destination=destination, template=template, context=context)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _send_email(
        self,
        *,
        destination: str,
        template: str,
        context: dict,
    ) -> None:
        """Render *template* and enqueue an email Celery task."""
        from worker.tasks.email_tasks import send_welcome_email  # lazy import

        html_body = _render_template("email", template, context) or None
        full_name = context.get("full_name", "")

        try:
            send_welcome_email.delay(
                to_email=destination,
                full_name=full_name,
                html_body=html_body,
            )
            logger.info(
                "NotificationService: enqueued %s email to=%s template=%s",
                template,
                destination,
                template,
            )
        except Exception as exc:  # noqa: BLE001
            # Never raise — notification failure must not block the caller.
            logger.error(
                "NotificationService: failed to enqueue email to=%s template=%s — %s",
                destination,
                template,
                exc,
            )
