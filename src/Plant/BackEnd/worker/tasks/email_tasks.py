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

Your WAOOAW email verification code is:

  {otp_code}

Valid for {valid_minutes} minutes — enter it and you're all set!

Keep this code private. WAOOAW staff will never ask for it.

Excited to have you,
The WAOOAW Team  ·  customer.care@dlaisd.com
"""

_OTP_HTML = """\
<!DOCTYPE html>
<html lang="en">
<body style="margin:0;padding:0;background:#0a0a0a;font-family:Inter,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0a;">
    <tr><td align="center" style="padding:40px 16px;">
      <table width="480" cellpadding="0" cellspacing="0"
             style="background:#111113;border:1px solid #27272a;border-radius:16px;
                    max-width:480px;width:100%;">
        <tr>
          <td style="padding:32px 36px 0;">
            <div style="font-size:1.4rem;font-weight:700;color:#00f2fe;
                        letter-spacing:-0.02em;">WAOOAW</div>
          </td>
        </tr>
        <tr>
          <td style="padding:20px 36px 0;">
            <h1 style="margin:0;font-size:1.15rem;font-weight:600;color:#f4f4f5;">
              Verify your email
            </h1>
            <p style="margin:10px 0 0;font-size:0.93rem;color:#a1a1aa;line-height:1.6;">
              Enter this code to confirm your email and start exploring your AI workforce.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 36px;">
            <div style="background:#18181b;border:1px solid #3f3f46;border-radius:12px;
                        padding:28px;text-align:center;">
              <span style="font-size:2.8rem;font-weight:800;letter-spacing:0.45em;
                           color:#00f2fe;font-variant-numeric:tabular-nums;">{otp_code}</span>
            </div>
            <p style="margin:14px 0 0;font-size:0.82rem;color:#71717a;text-align:center;">
              Valid for <strong style="color:#a1a1aa;">{valid_minutes}&nbsp;minutes</strong>.
              Do not share this code.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:8px 36px 32px;border-top:1px solid #27272a;">
            <p style="margin:16px 0 0;font-size:0.8rem;color:#52525b;line-height:1.6;">
              Didn&rsquo;t request this? Ignore this email &mdash; no action needed.<br>
              Questions? <a href="mailto:customer.care@dlaisd.com"
                 style="color:#667eea;text-decoration:none;">customer.care@dlaisd.com</a>
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
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
            subject="Confirm your email — WAOOAW awaits",
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

Welcome to WAOOAW — your AI workforce is ready!

You can now browse 19+ specialist AI agents across marketing, sales, and
education. Start a free 7-day trial on any agent and keep every deliverable,
no matter what. Zero risk.

Here is what to do next:
  1. Browse agents at https://app.waooaw.com
  2. Pick one that fits your business
  3. Kick off a free 7-day trial — keep the work even if you cancel

We are rooting for you.
The WAOOAW Team  ·  customer.care@dlaisd.com
"""

_WELCOME_HTML_FALLBACK = """\
<!DOCTYPE html>
<html lang="en">
<body style="margin:0;padding:0;background:#0a0a0a;font-family:Inter,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0a;">
    <tr><td align="center" style="padding:40px 16px;">
      <table width="560" cellpadding="0" cellspacing="0"
             style="background:#111113;border:1px solid #27272a;border-radius:16px;
                    max-width:560px;width:100%;">
        <tr>
          <td style="padding:32px 36px 0;">
            <div style="font-size:1.4rem;font-weight:700;color:#00f2fe;
                        letter-spacing:-0.02em;">WAOOAW</div>
          </td>
        </tr>
        <tr>
          <td style="padding:20px 36px 0;">
            <h1 style="margin:0;font-size:1.3rem;font-weight:700;color:#f4f4f5;">
              Your AI workforce is live, {first_name}!
            </h1>
            <p style="margin:12px 0 0;font-size:0.95rem;color:#a1a1aa;line-height:1.65;">
              Browse 19+ specialist AI agents, kick off a free 7-day trial, and
              <strong style="color:#f4f4f5;">keep every deliverable</strong> — zero risk, ever.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 36px;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="background:#18181b;border:1px solid #3f3f46;border-radius:10px;
                            padding:16px 20px;width:30%;">
                  <div style="font-size:1.5rem;margin-bottom:4px;">&#127775;</div>
                  <div style="font-size:0.85rem;font-weight:600;color:#f4f4f5;">Try before you hire</div>
                  <div style="font-size:0.78rem;color:#71717a;margin-top:4px;">7-day free trial on every agent</div>
                </td>
                <td width="12"></td>
                <td style="background:#18181b;border:1px solid #3f3f46;border-radius:10px;
                            padding:16px 20px;width:30%;">
                  <div style="font-size:1.5rem;margin-bottom:4px;">&#128640;</div>
                  <div style="font-size:0.85rem;font-weight:600;color:#f4f4f5;">Keep the work</div>
                  <div style="font-size:0.78rem;color:#71717a;margin-top:4px;">Deliverables are yours, always</div>
                </td>
                <td width="12"></td>
                <td style="background:#18181b;border:1px solid #3f3f46;border-radius:10px;
                            padding:16px 20px;width:30%;">
                  <div style="font-size:1.5rem;margin-bottom:4px;">&#127775;</div>
                  <div style="font-size:0.85rem;font-weight:600;color:#f4f4f5;">19+ specialist agents</div>
                  <div style="font-size:0.78rem;color:#71717a;margin-top:4px;">Marketing · Sales · Education</div>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:0 36px 32px;text-align:center;">
            <a href="https://app.waooaw.com"
               style="display:inline-block;padding:14px 36px;
                      background:linear-gradient(135deg,#667eea 0%,#00f2fe 100%);
                      color:#fff;border-radius:8px;text-decoration:none;
                      font-weight:700;font-size:0.95rem;letter-spacing:0.01em;">
              Browse Agents Now
            </a>
          </td>
        </tr>
        <tr>
          <td style="padding:0 36px 28px;border-top:1px solid #27272a;">
            <p style="margin:16px 0 0;font-size:0.8rem;color:#52525b;line-height:1.6;">
              Questions or feedback? We&rsquo;re here:
              <a href="mailto:customer.care@dlaisd.com"
                 style="color:#667eea;text-decoration:none;">customer.care@dlaisd.com</a>
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
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
            subject="Welcome to WAOOAW — your AI workforce is ready",
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
