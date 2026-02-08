"""Customer APIs.

REG-1.5: Customer account entity + persistence.

Minimal endpoints:
- Idempotent create-by-email (upsert)
- Lookup by email

Auth is intentionally not enforced yet; Gateway story (REG-1.6) will layer policy.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from schemas.customer import CustomerCreate, CustomerResponse, CustomerUpsertResponse
from services.customer_service import CustomerService


router = APIRouter(prefix="/customers", tags=["customers"])


def get_customer_service(db: AsyncSession = Depends(get_db_session)) -> CustomerService:
    return CustomerService(db)


@router.post("", response_model=CustomerUpsertResponse)
async def upsert_customer(
    payload: CustomerCreate,
    service: CustomerService = Depends(get_customer_service),
) -> CustomerUpsertResponse:
    customer, created = await service.upsert_by_email(payload)
    return CustomerUpsertResponse(
        created=created,
        customer_id=str(customer.id),
        email=customer.email,
        phone=customer.phone,
        full_name=customer.full_name,
        business_name=customer.business_name,
        business_industry=customer.business_industry,
        business_address=customer.business_address,
        website=customer.website,
        gst_number=customer.gst_number,
        preferred_contact_method=customer.preferred_contact_method,
        consent=bool(customer.consent),
    )


@router.get("/lookup", response_model=CustomerResponse)
async def lookup_customer(
    email: EmailStr,
    service: CustomerService = Depends(get_customer_service),
) -> CustomerResponse:
    customer = await service.get_by_email(str(email).strip().lower())
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    return CustomerResponse(
        customer_id=str(customer.id),
        email=customer.email,
        phone=customer.phone,
        full_name=customer.full_name,
        business_name=customer.business_name,
        business_industry=customer.business_industry,
        business_address=customer.business_address,
        website=customer.website,
        gst_number=customer.gst_number,
        preferred_contact_method=customer.preferred_contact_method,
        consent=bool(customer.consent),
    )
