from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Literal

import anyio


Channel = Literal["email", "phone"]


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


def _send_email_smtp_sync(*, to_email: str, subject: str, body: str) -> None:
    cfg = _smtp_config()

    msg = EmailMessage()
    msg["From"] = cfg["sender"]
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

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

    subject = "Your WAOOAW verification code"
    body = (
        "Your WAOOAW verification code is:\n\n"
        f"{code}\n\n"
        f"This code expires in {int(ttl_seconds)} seconds.\n"
    )

    await anyio.to_thread.run_sync(
        _send_email_smtp_sync,
        to_email=destination,
        subject=subject,
        body=body,
    )
