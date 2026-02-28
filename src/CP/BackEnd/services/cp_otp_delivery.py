from __future__ import annotations

import functools
import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Literal

import anyio


Channel = Literal["email", "phone"]

# ── Email templates ──────────────────────────────────────────────────────────

_OTP_SUBJECT = "Your WAOOAW login code"

_OTP_TEXT = """\
Hi,

Your WAOOAW one-time login code is:

  {code}

Valid for {ttl_minutes} minutes. Enter it quickly and you're in!

Keep this code private — WAOOAW staff will never ask for it.

Excited to have you on the platform,
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
          <td style="padding:24px 36px 0;">
            <h1 style="margin:0;font-size:1.2rem;font-weight:600;color:#f4f4f5;">
              Your login code
            </h1>
            <p style="margin:12px 0 0;font-size:0.93rem;color:#a1a1aa;line-height:1.6;">
              Use the code below to sign in to your WAOOAW account.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:28px 36px;">
            <div style="background:#18181b;border:1px solid #3f3f46;border-radius:12px;
                        padding:28px;text-align:center;">
              <span style="font-size:2.8rem;font-weight:800;letter-spacing:0.45em;
                           color:#00f2fe;font-variant-numeric:tabular-nums;">{code}</span>
            </div>
            <p style="margin:16px 0 0;font-size:0.82rem;color:#71717a;text-align:center;">
              Valid for <strong style="color:#a1a1aa;">{ttl_minutes}&nbsp;minutes</strong>.
              Do not share this code.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:8px 36px 32px;border-top:1px solid #27272a;">
            <p style="margin:16px 0 0;font-size:0.8rem;color:#52525b;line-height:1.6;">
              Didn&rsquo;t request this? Simply ignore this email — your account is safe.<br>
              Questions? Reach us at
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


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def _bool_env(name: str, default: str = "false") -> bool:
    return _env(name, default).lower() in {"1", "true", "yes", "on"}


def _smtp_config() -> dict:
    host = _env("CP_OTP_SMTP_HOST")
    port_raw = _env("CP_OTP_SMTP_PORT", "587")
    username = _env("CP_OTP_SMTP_USERNAME")
    password = _env("CP_OTP_SMTP_PASSWORD")
    sender = _env("CP_OTP_SMTP_FROM")

    if not host or not port_raw or not sender:
        raise RuntimeError("SMTP OTP delivery not configured (missing CP_OTP_SMTP_HOST/PORT/FROM).")

    try:
        port = int(port_raw)
    except ValueError as exc:
        raise RuntimeError("Invalid CP_OTP_SMTP_PORT; expected integer.") from exc

    return {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "sender": sender,
        "use_starttls": _bool_env("CP_OTP_SMTP_STARTTLS", "true"),
        "allow_insecure": _bool_env("CP_OTP_SMTP_ALLOW_INSECURE", "false"),
    }


def _send_email_smtp_sync(*, to_email: str, subject: str, body: str, html_body: str | None = None) -> None:
    cfg = _smtp_config()

    msg = EmailMessage()
    msg["From"] = cfg["sender"]
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    context = None
    if not cfg["allow_insecure"]:
        context = ssl.create_default_context()

    with smtplib.SMTP(cfg["host"], cfg["port"], timeout=10) as server:
        server.ehlo()
        if cfg["use_starttls"]:
            server.starttls(context=context)
            server.ehlo()

        if cfg["username"] and cfg["password"]:
            server.login(cfg["username"], cfg["password"])

        server.send_message(msg)


async def deliver_otp(*, channel: Channel, destination: str, code: str, ttl_seconds: int = 300) -> None:
    """Deliver an OTP code using an environment-configured provider.

    Provider selection:
    - CP_OTP_DELIVERY_PROVIDER=smtp (email only)

    This function raises RuntimeError when delivery cannot be performed.
    """

    provider = _env("CP_OTP_DELIVERY_PROVIDER")

    if provider == "":
        raise RuntimeError("OTP delivery provider not configured (set CP_OTP_DELIVERY_PROVIDER).")

    if provider != "smtp":
        raise RuntimeError("Unsupported OTP delivery provider.")

    if channel != "email":
        raise RuntimeError("SMS/phone OTP delivery is not configured.")

    ttl_minutes = max(1, int(ttl_seconds) // 60)
    text_body = _OTP_TEXT.format(code=code, ttl_minutes=ttl_minutes)
    html_body = _OTP_HTML.format(code=code, ttl_minutes=ttl_minutes)

    await anyio.to_thread.run_sync(
        functools.partial(
            _send_email_smtp_sync,
            to_email=destination,
            subject=_OTP_SUBJECT,
            body=text_body,
            html_body=html_body,
        )
    )
