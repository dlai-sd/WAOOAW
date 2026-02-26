"""E2-S1 / E2-S2 — Async OTP and welcome email Celery tasks.

Send OTP email fire-and-forget after DB commit.
Retry up to 3 times with exponential back-off (2 ** attempt seconds).
Skip retry if the OTP session has already expired (deadline guard).
Dead-letter log when MaxRetriesExceededError is raised.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from celery.exceptions import MaxRetriesExceededError

from services.email_providers import get_email_provider
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)

# ── OTP templates ─────────────────────────────────────────────────────────────

_OTP_TEXT = """\
Hi,

Your WAOOAW verification code is: {otp_code}

This code is valid for {valid_minutes} minutes.

If you did not request this, please ignore this message.

— The WAOOAW Team
"""

_OTP_HTML = """\
<!DOCTYPE html>
<html lang="en">
<body style="font-family:Inter,sans-serif;background:#0a0a0a;color:#e5e5e5;padding:40px;">
  <div style="max-width:480px;margin:0 auto;">
    <h1 style="color:#00f2fe;font-size:1.5rem;">Your WAOOAW Code</h1>
    <p>Use the code below to continue registration:</p>
    <div style="background:#18181b;border:1px solid #333;border-radius:12px;
                padding:24px;text-align:center;margin:24px 0;">
      <span style="font-size:2.5rem;letter-spacing:0.4em;font-weight:700;
                   color:#00f2fe;">{otp_code}</span>
    </div>
    <p style="color:#888;font-size:0.85rem;">
      Valid for {valid_minutes} minutes. Do not share this code.
    </p>
  </div>
</body>
</html>
"""


# ── Task: send_otp_email ──────────────────────────────────────────────────────

@celery_app.task(
    name="send_otp_email",
    bind=True,
    max_retries=3,
    queue="email",
    default_retry_delay=1,  # overridden below with exponential back-off
)
def send_otp_email(
    self,
    *,
    to_email: str,
    otp_code: str,
    expires_in_seconds: int,
    otp_id: str,
    expires_at_iso: str | None = None,
) -> None:
    """Send a 6-digit OTP code to *to_email*.

    Args:
        to_email: Recipient email address.
        otp_code: Plain 6-digit code to include in the email.
        expires_in_seconds: TTL shown to the user (e.g. 300 → "5 minutes").
        otp_id: UUID of the ``otp_sessions`` row, used for logging.
        expires_at_iso: ISO-8601 UTC datetime when OTP expires.
                        If supplied and past, the task is skipped on retry.
    """
    # --- Expiry guard (only relevant on retries) ---
    if self.request.retries > 0 and expires_at_iso:
        try:
            expires_at = datetime.fromisoformat(expires_at_iso)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) >= expires_at:
                logger.info(
                    "send_otp_email: OTP %s already expired — skipping retry %d",
                    otp_id,
                    self.request.retries,
                )
                return
        except ValueError:
            pass  # Malformed ISO string — proceed anyway

    valid_minutes = max(1, expires_in_seconds // 60)

    try:
        provider = get_email_provider()
        provider.send_email(
            to_email=to_email,
            subject="Your WAOOAW verification code",
            text_body=_OTP_TEXT.format(
                otp_code=otp_code,
                valid_minutes=valid_minutes,
            ),
            html_body=_OTP_HTML.format(
                otp_code=otp_code,
                valid_minutes=valid_minutes,
            ),
        )
        logger.info("send_otp_email: delivered otp_id=%s to=%s", otp_id, to_email)
    except MaxRetriesExceededError:
        # Dead-letter log — all retries exhausted
        logger.error(
            "send_otp_email: DEAD-LETTER otp_id=%s to=%s task_id=%s",
            otp_id,
            to_email,
            self.request.id,
        )
    except Exception as exc:
        countdown = 2 ** self.request.retries
        logger.warning(
            "send_otp_email: retry %d/%d for otp_id=%s in %ds — %s",
            self.request.retries + 1,
            self.max_retries,
            otp_id,
            countdown,
            exc,
        )
        try:
            raise self.retry(exc=exc, countdown=countdown)
        except MaxRetriesExceededError:
            logger.error(
                "send_otp_email: DEAD-LETTER otp_id=%s to=%s task_id=%s — %s",
                otp_id,
                to_email,
                self.request.id,
                exc,
            )


# ── Task: send_welcome_email ──────────────────────────────────────────────────

_WELCOME_TEXT = """\
Hi {first_name},

Welcome to WAOOAW — the AI agent marketplace that makes you say WOW!

Your account is ready. Browse agents, start a free 7-day trial, and keep
every deliverable — no risk, ever.

Log in at: https://app.waooaw.com

— The WAOOAW Team
"""

_WELCOME_HTML_FALLBACK = """\
<!DOCTYPE html>
<html lang="en">
<body style="font-family:Inter,sans-serif;background:#0a0a0a;color:#e5e5e5;padding:40px;">
  <div style="max-width:560px;margin:0 auto;">
    <h1 style="color:#00f2fe;">Welcome to WAOOAW, {first_name}!</h1>
    <p>Your account is live. Browse agents, start a free 7-day trial,
       and keep every deliverable — no risk, ever.</p>
    <a href="https://app.waooaw.com"
       style="display:inline-block;margin-top:16px;padding:14px 28px;
              background:linear-gradient(135deg,#667eea,#00f2fe);
              color:#fff;border-radius:8px;text-decoration:none;font-weight:600;">
      Enter WAOOAW
    </a>
  </div>
</body>
</html>
"""


@celery_app.task(
    name="send_welcome_email",
    bind=True,
    max_retries=3,
    queue="email",
)
def send_welcome_email(
    self,
    *,
    to_email: str,
    full_name: str,
    html_body: str | None = None,
) -> None:
    """Send a welcome email to a newly registered customer.

    Args:
        to_email: Recipient address.
        full_name: Customer's display name (used for personalisation).
        html_body: Pre-rendered HTML from Jinja2 template (optional).
                   Falls back to inline HTML if not supplied.
    """
    first_name = (full_name.split()[0] if full_name and full_name.strip() else "there")

    try:
        provider = get_email_provider()
        provider.send_email(
            to_email=to_email,
            subject="Welcome to WAOOAW — Agents That Earn Your Business",
            text_body=_WELCOME_TEXT.format(first_name=first_name),
            html_body=html_body or _WELCOME_HTML_FALLBACK.format(first_name=first_name),
        )
        logger.info("send_welcome_email: delivered to=%s", to_email)
    except MaxRetriesExceededError:
        logger.error(
            "send_welcome_email: DEAD-LETTER to=%s task_id=%s",
            to_email,
            self.request.id,
        )
    except Exception as exc:
        countdown = 2 ** self.request.retries
        logger.warning(
            "send_welcome_email: retry %d/%d to=%s in %ds — %s",
            self.request.retries + 1,
            self.max_retries,
            to_email,
            countdown,
            exc,
        )
        try:
            raise self.retry(exc=exc, countdown=countdown)
        except MaxRetriesExceededError:
            logger.error(
                "send_welcome_email: DEAD-LETTER to=%s task_id=%s — %s",
                to_email,
                self.request.id,
                exc,
            )
