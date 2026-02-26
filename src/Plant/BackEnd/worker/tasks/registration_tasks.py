"""E3-S2 / E4-S1 — Customer registration Celery tasks.

Handles the ``customer.registered`` domain event fired by
``api/v1/customers.py`` when a new customer row is created.

Flow:
  POST /customers (created=True)
    → handle_customer_registered.delay(...)
      → NotificationService.send(template="welcome")
        → send_welcome_email.delay(...)
"""

from __future__ import annotations

import logging

from celery.exceptions import MaxRetriesExceededError

from services.notification_service import NotificationService
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="handle_customer_registered",
    bind=True,
    max_retries=3,
    queue="events",
)
def handle_customer_registered(
    self,
    *,
    customer_id: str,
    email: str,
    full_name: str,
    business_name: str,
    registered_at: str,
) -> None:
    """Process the ``customer.registered`` domain event.

    Sends a welcome email via NotificationService and can be extended
    to trigger additional on-boarding actions (e.g. CRM record, analytics).

    Args:
        customer_id: UUID of the newly-created customer row.
        email: Customer's email address.
        full_name: Customer's display name.
        business_name: Business/company name (may be empty string).
        registered_at: ISO-8601 UTC datetime of registration.
    """
    logger.info(
        "handle_customer_registered: customer_id=%s email=%s",
        customer_id,
        email,
    )

    try:
        NotificationService().send(
            channel="email",
            destination=email,
            template="welcome",
            context={
                "first_name": full_name.split()[0] if full_name and full_name.strip() else "there",
                "full_name": full_name,
                "business_name": business_name,
                "customer_id": customer_id,
                "registered_at": registered_at,
            },
        )
        logger.info(
            "handle_customer_registered: welcome notification enqueued for customer_id=%s",
            customer_id,
        )
    except MaxRetriesExceededError:
        logger.error(
            "handle_customer_registered: DEAD-LETTER customer_id=%s email=%s task_id=%s",
            customer_id,
            email,
            self.request.id,
        )
    except Exception as exc:
        countdown = 2 ** self.request.retries
        logger.warning(
            "handle_customer_registered: retry %d/%d customer_id=%s in %ds — %s",
            self.request.retries + 1,
            self.max_retries,
            customer_id,
            countdown,
            exc,
        )
        try:
            raise self.retry(exc=exc, countdown=countdown)
        except MaxRetriesExceededError:
            logger.error(
                "handle_customer_registered: DEAD-LETTER customer_id=%s email=%s task_id=%s — %s",
                customer_id,
                email,
                self.request.id,
                exc,
            )
