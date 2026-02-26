"""Customer service.

REG-1.5: Persist customer identity + business profile in Plant.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from core.exceptions import DuplicateEntityError
from models.customer import Customer
from schemas.customer import CustomerCreate

TOKEN_VERSION_CACHE_TTL = 300  # 5 minutes

# E2-S2: Placeholder values used when erasing customer PII
_ERASED_PHONE = "REDACTED"
_ERASED_NAME = "REDACTED"
_ERASED_ADDRESS = "REDACTED"


class CustomerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> Customer | None:
        stmt = select(Customer).where(Customer.email == email)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_id(self, customer_id: str) -> Customer | None:
        normalized = (customer_id or "").strip()
        if not normalized:
            return None
        try:
            cid = UUID(normalized)
        except Exception:
            return None
        stmt = select(Customer).where(Customer.id == cid)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_phone(self, phone: str) -> Customer | None:
        stmt = select(Customer).where(Customer.phone == phone)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def bump_token_version(self, customer_id: str) -> int:
        """Increment token_version for a customer, invalidating all active sessions.

        E2-S3: Called on password reset to force re-login on all devices.
        Updates the DB and refreshes the Redis cache so the Gateway detects the change.

        Returns:
            int: New token_version value.
        """
        from core.redis_client import get_async_redis

        customer = await self.get_by_id(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        customer.token_version = (customer.token_version or 1) + 1
        await self.db.commit()
        await self.db.refresh(customer)

        # Eagerly update the Gateway-side Redis cache so revocation is near-instant.
        r = get_async_redis()
        await r.set(
            f"token_version:{customer_id}",
            str(customer.token_version),
            ex=TOKEN_VERSION_CACHE_TTL,
        )

        return customer.token_version

    # ------------------------------------------------------------------
    # E2-S2 (Iteration 6): GDPR Right to Erasure
    # ------------------------------------------------------------------

    async def erase(
        self,
        customer_id: str,
        *,
        reason: str | None = None,  # noqa: F841 — stored via caller's audit log
    ) -> Customer:
        """Anonymise all PII for a customer (GDPR right to erasure).

        Performs three operations in a single transaction:
          1. Anonymise PII columns in ``customer_entity``.
          2. Redact ``email`` in all ``audit_logs`` rows for this customer.
          3. Delete all ``otp_sessions`` rows for this customer's destination.

        Args:
            customer_id: UUID string of the customer to erase.
            reason: Erasure reason (for the caller's audit records).

        Returns:
            The now-anonymised Customer object.

        Raises:
            ValueError: If the customer is not found or already erased.
        """
        customer = await self.get_by_id(customer_id)
        if customer is None:
            raise ValueError(f"Customer {customer_id} not found")
        if customer.deleted_at is not None:
            raise ValueError(f"Customer {customer_id} already erased")

        original_email = customer.email
        erased_email = f"redacted_{customer.id}@erased.invalid"
        now = datetime.now(timezone.utc)

        # Single atomic transaction ─────────────────────────────────────
        async with self.db.begin_nested():
            # 1. Anonymise customer_entity PII columns
            await self.db.execute(
                update(Customer)
                .where(Customer.id == customer.id)
                .values(
                    email=erased_email,
                    phone=_ERASED_PHONE,
                    full_name=_ERASED_NAME,
                    business_address=_ERASED_ADDRESS,
                    deleted_at=now,
                )
            )

            # 2. Redact email in audit_logs
            await self.db.execute(
                text(
                    "UPDATE audit_logs SET email = 'REDACTED'"
                    " WHERE email = :email"
                ),
                {"email": original_email},
            )

            # 3. Delete OTP sessions (all, expired or not)
            await self.db.execute(
                text("DELETE FROM otp_sessions WHERE destination = :dest"),
                {"dest": original_email},
            )

        await self.db.commit()
        await self.db.refresh(customer)
        return customer

    async def upsert_by_email(self, payload: CustomerCreate) -> tuple[Customer, bool]:
        email = str(payload.email).strip().lower()
        phone = str(payload.phone).strip()

        existing = await self.get_by_email(email)
        if existing is not None:
            return existing, False

        existing_phone = await self.get_by_phone(phone)
        if existing_phone is not None:
            raise DuplicateEntityError("Customer with this phone already exists")

        customer = Customer(
            entity_type="Customer",
            email=email,
            phone=phone,
            full_name=payload.full_name,
            business_name=payload.business_name,
            business_industry=payload.business_industry,
            business_address=payload.business_address,
            website=payload.website,
            gst_number=payload.gst_number,
            preferred_contact_method=payload.preferred_contact_method,
            consent=payload.consent,
        )

        self.db.add(customer)
        try:
            await self.db.commit()
        except IntegrityError:
            # Another request likely created the same email concurrently.
            await self.db.rollback()
            existing_after_race = await self.get_by_email(email)
            if existing_after_race is not None:
                return existing_after_race, False
            existing_phone_after_race = await self.get_by_phone(phone)
            if existing_phone_after_race is not None:
                raise DuplicateEntityError("Customer with this phone already exists")
            raise

        await self.db.refresh(customer)
        return customer, True
