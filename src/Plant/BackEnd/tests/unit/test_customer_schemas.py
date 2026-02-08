import pytest
from pydantic import ValidationError

from schemas.customer import CustomerCreate


@pytest.mark.unit
def test_customer_create_normalizes_email_and_phone():
    payload = CustomerCreate(
        fullName=" Test User ",
        businessName=" ACME ",
        businessIndustry="marketing",
        businessAddress="Bengaluru",
        email="TEST@Example.COM ",
        phone=" +91 98765 43210 ",
        preferredContactMethod="email",
        consent=True,
    )

    assert payload.email == "test@example.com"
    assert payload.phone.startswith("+")


@pytest.mark.unit
def test_customer_create_rejects_bad_phone():
    with pytest.raises(ValidationError):
        CustomerCreate(
            fullName="Test User",
            businessName="ACME",
            businessIndustry="marketing",
            businessAddress="Bengaluru",
            email="test@example.com",
            phone="abc",
            preferredContactMethod="email",
            consent=True,
        )
