"""Versioned notification SMS templates.

NOTIF-1.3:
- SMS templates must be versioned and provider is env-configurable.
"""

from __future__ import annotations

from dataclasses import dataclass

from services.notification_events import NotificationEventRecord


TEMPLATE_VERSION = "2026-02-09"


@dataclass(frozen=True)
class RenderedSms:
    message: str
    template_version: str


def render_sms_for_event(event: NotificationEventRecord) -> RenderedSms | None:
    et = (event.event_type or "").strip().lower()

    if et == "otp_sent":
        flow = event.metadata.get("flow") if isinstance(event.metadata, dict) else None
        expires = event.metadata.get("expires_in_seconds") if isinstance(event.metadata, dict) else None
        msg = f"WAOOAW: OTP sent ({flow or 'N/A'}). Expires in {expires or 'N/A'}s."
        return RenderedSms(message=msg, template_version=TEMPLATE_VERSION)

    if et == "otp_verified":
        msg = "WAOOAW: OTP verified."
        return RenderedSms(message=msg, template_version=TEMPLATE_VERSION)

    if et == "payment_success":
        msg = (
            "WAOOAW: Payment confirmed. "
            f"Sub {event.subscription_id or 'N/A'}, Order {event.order_id or 'N/A'}."
        )
        return RenderedSms(message=msg, template_version=TEMPLATE_VERSION)

    if et == "payment_failed":
        reason = event.metadata.get("reason") if isinstance(event.metadata, dict) else None
        msg = (
            "WAOOAW: Payment failed. "
            f"Sub {event.subscription_id or 'N/A'}, Order {event.order_id or 'N/A'}. "
            f"Reason {reason or 'N/A'}."
        )
        return RenderedSms(message=msg, template_version=TEMPLATE_VERSION)

    if et == "trial_activated":
        start = event.metadata.get("trial_start_at") if isinstance(event.metadata, dict) else None
        end = event.metadata.get("trial_end_at") if isinstance(event.metadata, dict) else None
        msg = (
            "WAOOAW: Trial activated. "
            f"Sub {event.subscription_id or 'N/A'}. Starts {start or 'N/A'}, ends {end or 'N/A'}."
        )
        return RenderedSms(message=msg, template_version=TEMPLATE_VERSION)

    if et == "trial_ended":
        next_status = event.metadata.get("next_status") if isinstance(event.metadata, dict) else None
        msg = (
            "WAOOAW: Trial ended. "
            f"Sub {event.subscription_id or 'N/A'}. Status {next_status or 'N/A'}."
        )
        return RenderedSms(message=msg, template_version=TEMPLATE_VERSION)

    if et == "cancel_scheduled":
        effective_at = event.metadata.get("effective_at") if isinstance(event.metadata, dict) else None
        msg = (
            "WAOOAW: Cancellation scheduled at period end. "
            f"Sub {event.subscription_id or 'N/A'}. Effective {effective_at or 'N/A'}."
        )
        return RenderedSms(message=msg, template_version=TEMPLATE_VERSION)

    if et == "cancel_effective":
        ended_at = event.metadata.get("ended_at") if isinstance(event.metadata, dict) else None
        msg = (
            "WAOOAW: Subscription ended. "
            f"Sub {event.subscription_id or 'N/A'}. Ended {ended_at or 'N/A'}."
        )
        return RenderedSms(message=msg, template_version=TEMPLATE_VERSION)

    if et == "hired_agent_deactivated":
        ts = event.metadata.get("deactivated_at") if isinstance(event.metadata, dict) else None
        msg = (
            "WAOOAW: Agent deactivated. "
            f"Sub {event.subscription_id or 'N/A'}. At {ts or 'N/A'}."
        )
        return RenderedSms(message=msg, template_version=TEMPLATE_VERSION)

    return None
