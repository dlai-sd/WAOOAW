"""Email delivery providers.

NOTIF-1.2: Plant email provider integration.

Phase-1 goals:
- Provide an env-configurable email provider (SMTP) for transactional emails.
- Keep a safe null provider as the default so lower envs/tests don't accidentally send.
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Protocol


class EmailProvider(Protocol):
    def send_email(self, *, to_email: str, subject: str, text_body: str, html_body: str | None = None) -> None: ...


class NullEmailProvider:
    def send_email(self, *, to_email: str, subject: str, text_body: str, html_body: str | None = None) -> None:
        return


class SmtpEmailProvider:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        from_email: str,
        use_tls: bool,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_email = from_email
        self._use_tls = use_tls

    def send_email(self, *, to_email: str, subject: str, text_body: str, html_body: str | None = None) -> None:
        msg = EmailMessage()
        msg["From"] = self._from_email
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.set_content(text_body)
        if html_body:
            msg.add_alternative(html_body, subtype="html")

        with smtplib.SMTP(self._host, self._port, timeout=10) as server:
            if self._use_tls:
                server.starttls()
            if self._username and self._password:
                server.login(self._username, self._password)
            server.send_message(msg)


def get_email_provider() -> EmailProvider:
    provider = (os.getenv("EMAIL_PROVIDER") or "null").strip().lower()
    if provider != "smtp":
        return NullEmailProvider()

    host = (os.getenv("SMTP_HOST") or "").strip()
    if not host:
        return NullEmailProvider()

    try:
        port = int((os.getenv("SMTP_PORT") or "587").strip())
    except Exception:
        port = 587

    username = (os.getenv("SMTP_USERNAME") or "").strip() or None
    password = (os.getenv("SMTP_PASSWORD") or "").strip() or None
    from_email = (os.getenv("SMTP_FROM_EMAIL") or "no-reply@waooaw.com").strip() or "no-reply@waooaw.com"
    use_tls = (os.getenv("SMTP_USE_TLS") or "true").strip().lower() in {"1", "true", "yes", "y"}

    return SmtpEmailProvider(
        host=host,
        port=port,
        username=username,
        password=password,
        from_email=from_email,
        use_tls=use_tls,
    )
