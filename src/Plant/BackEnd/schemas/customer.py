"""Customer schemas.

REG-1.5: minimal contract for creating/looking up a customer in Plant.

We accept both snake_case and the CP frontend's camelCase keys via aliases so
Gateway/CP can integrate without re-shaping payloads.
"""

from __future__ import annotations

import re
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


_PHONE_RE = re.compile(r"^\+?[\d\s\-()]{7,}$")


def _normalize_phone(value: str) -> str:
    return str(value or "").strip().replace(" ", "")


class CustomerCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    full_name: str = Field(..., alias="fullName", min_length=1)
    business_name: str = Field(..., alias="businessName", min_length=1)
    business_industry: str = Field(..., alias="businessIndustry", min_length=1)
    business_address: str = Field(..., alias="businessAddress", min_length=1)

    email: EmailStr
    phone: str

    website: Optional[str] = None
    gst_number: Optional[str] = Field(None, alias="gstNumber")

    preferred_contact_method: Literal["email", "phone"] = Field(..., alias="preferredContactMethod")
    consent: bool

    @field_validator("full_name", "business_name", "business_industry", "business_address", mode="before")
    @classmethod
    def _strip_required_strings(cls, v: str) -> str:
        if v is None:
            return v
        return str(v).strip()

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, v: str) -> str:
        if v is None:
            return v
        return str(v).strip().lower()

    @field_validator("phone", mode="before")
    @classmethod
    def _validate_phone(cls, v: str) -> str:
        phone = _normalize_phone(v)
        if not _PHONE_RE.match(phone):
            raise ValueError("Invalid phone format")
        return phone

    @field_validator("website", mode="before")
    @classmethod
    def _validate_website(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        if not s:
            return None
        if not s.lower().startswith(("http://", "https://")):
            raise ValueError("Website must start with http:// or https://")
        return s

    @field_validator("gst_number", mode="before")
    @classmethod
    def _validate_gst(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip().upper()
        if not s:
            return None
        if not re.match(r"^[0-9A-Z]{15}$", s):
            raise ValueError("Invalid GST format (15 chars)")
        return s


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: str
    email: EmailStr
    phone: str

    full_name: str
    business_name: str
    business_industry: str
    business_address: str

    website: str | None = None
    gst_number: str | None = None

    preferred_contact_method: str
    consent: bool


class CustomerUpsertResponse(CustomerResponse):
    created: bool
