"""Customer service.

REG-1.5: Persist customer identity + business profile in Plant.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from models.customer import Customer
from schemas.customer import CustomerCreate


class CustomerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> Customer | None:
        stmt = select(Customer).where(Customer.email == email)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def upsert_by_email(self, payload: CustomerCreate) -> tuple[Customer, bool]:
        email = str(payload.email).strip().lower()

        existing = await self.get_by_email(email)
        if existing is not None:
            return existing, False

        customer = Customer(
            entity_type="Customer",
            email=email,
            phone=payload.phone,
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
            raise

        await self.db.refresh(customer)
        return customer, True
