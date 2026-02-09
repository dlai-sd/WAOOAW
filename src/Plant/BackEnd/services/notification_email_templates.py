"""Versioned notification email templates.

NOTIF-1.2:
- Templates must be versioned and env-configurable provider selects delivery.

Phase-1 note:
- Keep templates simple (plain text + optional HTML) and avoid embedding secrets.
"""

from __future__ import annotations

from dataclasses import dataclass

from services.notification_events import NotificationEventRecord


TEMPLATE_VERSION = "2026-02-09"


@dataclass(frozen=True)
class RenderedEmail:
    subject: str
    text_body: str
    html_body: str | None
    template_version: str


def render_email_for_event(event: NotificationEventRecord) -> RenderedEmail | None:
    et = (event.event_type or "").strip().lower()

    if et == "otp_sent":
        flow = event.metadata.get("flow") if isinstance(event.metadata, dict) else None
        channel = event.metadata.get("channel") if isinstance(event.metadata, dict) else None
        destination = event.metadata.get("destination_masked") if isinstance(event.metadata, dict) else None
        expires = event.metadata.get("expires_in_seconds") if isinstance(event.metadata, dict) else None

        subject = "WAOOAW: OTP sent"
        text = (
            "We sent you a one-time password (OTP).\n\n"
            f"Flow: {flow or 'N/A'}\n"
            f"Channel: {channel or 'N/A'}\n"
            f"Destination: {destination or 'N/A'}\n"
            f"Expires in: {expires or 'N/A'} seconds\n"
        )
        return RenderedEmail(subject=subject, text_body=text, html_body=None, template_version=TEMPLATE_VERSION)

    if et == "otp_verified":
        channel = event.metadata.get("channel") if isinstance(event.metadata, dict) else None
        destination = event.metadata.get("destination_masked") if isinstance(event.metadata, dict) else None

        subject = "WAOOAW: OTP verified"
        text = (
            "Your OTP was verified successfully.\n\n"
            f"Channel: {channel or 'N/A'}\n"
            f"Destination: {destination or 'N/A'}\n"
        )
        return RenderedEmail(subject=subject, text_body=text, html_body=None, template_version=TEMPLATE_VERSION)

    if et == "payment_success":
        subject = "WAOOAW: Payment confirmed"
        text = (
            "Your payment is confirmed.\n\n"
            f"Subscription: {event.subscription_id or 'N/A'}\n"
            f"Order: {event.order_id or 'N/A'}\n"
        )
        return RenderedEmail(subject=subject, text_body=text, html_body=None, template_version=TEMPLATE_VERSION)

    if et == "payment_failed":
        reason = event.metadata.get("reason") if isinstance(event.metadata, dict) else None
        subject = "WAOOAW: Payment failed"
        text = (
            "Your payment could not be confirmed. You can retry safely from CP.\n\n"
            f"Subscription: {event.subscription_id or 'N/A'}\n"
            f"Order: {event.order_id or 'N/A'}\n"
            f"Reason: {reason or 'N/A'}\n"
        )
        return RenderedEmail(subject=subject, text_body=text, html_body=None, template_version=TEMPLATE_VERSION)

    if et == "trial_activated":
        subject = "WAOOAW: Trial activated"
        start = event.metadata.get("trial_start_at") if isinstance(event.metadata, dict) else None
        end = event.metadata.get("trial_end_at") if isinstance(event.metadata, dict) else None
        text = (
            "Your trial is now active.\n\n"
            f"Subscription: {event.subscription_id or 'N/A'}\n"
            f"Starts: {start or 'N/A'}\n"
            f"Ends: {end or 'N/A'}\n"
        )
        return RenderedEmail(subject=subject, text_body=text, html_body=None, template_version=TEMPLATE_VERSION)

    if et == "trial_ended":
        subject = "WAOOAW: Trial ended"
        next_status = event.metadata.get("next_status") if isinstance(event.metadata, dict) else None
        text = (
            "Your trial has ended.\n\n"
            f"Subscription: {event.subscription_id or 'N/A'}\n"
            f"Status: {next_status or 'N/A'}\n"
        )
        return RenderedEmail(subject=subject, text_body=text, html_body=None, template_version=TEMPLATE_VERSION)

    if et == "cancel_scheduled":
        subject = "WAOOAW: Cancellation scheduled"
        effective_at = event.metadata.get("effective_at") if isinstance(event.metadata, dict) else None
        text = (
            "Your subscription is scheduled to end at the end of the current billing period.\n\n"
            f"Subscription: {event.subscription_id or 'N/A'}\n"
            f"Effective at: {effective_at or 'N/A'}\n"
        )
        return RenderedEmail(subject=subject, text_body=text, html_body=None, template_version=TEMPLATE_VERSION)

    if et == "cancel_effective":
        subject = "WAOOAW: Subscription ended"
        ended_at = event.metadata.get("ended_at") if isinstance(event.metadata, dict) else None
        text = (
            "Your subscription has ended.\n\n"
            f"Subscription: {event.subscription_id or 'N/A'}\n"
            f"Ended at: {ended_at or 'N/A'}\n"
        )
        return RenderedEmail(subject=subject, text_body=text, html_body=None, template_version=TEMPLATE_VERSION)

    if et == "hired_agent_deactivated":
        ts = event.metadata.get("deactivated_at") if isinstance(event.metadata, dict) else None
        subject = "WAOOAW: Agent deactivated"
        text = (
            "Your hired agent instance has been deactivated.\n\n"
            f"Subscription: {event.subscription_id or 'N/A'}\n"
            f"Hired instance: {event.hired_instance_id or 'N/A'}\n"
            f"Deactivated at: {ts or 'N/A'}\n"
        )
        return RenderedEmail(subject=subject, text_body=text, html_body=None, template_version=TEMPLATE_VERSION)

    return None
