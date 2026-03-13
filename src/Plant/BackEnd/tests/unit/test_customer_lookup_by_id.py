from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.v1 import customers


class _ReadCustomerService:
    async def get_by_id(self, customer_id: str):
        if customer_id != '11111111-1111-1111-1111-111111111111':
            return None

        customer = MagicMock()
        customer.id = customer_id
        customer.email = 'owner@example.com'
        customer.phone = '+91 90000 00000'
        customer.full_name = 'Owner Example'
        customer.business_name = 'Example Studio'
        customer.business_industry = 'marketing'
        customer.business_address = 'Pune'
        customer.website = None
        customer.gst_number = None
        customer.preferred_contact_method = 'email'
        customer.consent = True
        return customer


@pytest.mark.asyncio
async def test_get_customer_by_id_returns_customer_response():
    app = FastAPI()
    app.dependency_overrides[customers.get_read_customer_service] = lambda: _ReadCustomerService()
    app.include_router(customers.router, prefix='/api/v1')

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        response = await client.get('/api/v1/customers/11111111-1111-1111-1111-111111111111')

    assert response.status_code == 200
    body = response.json()
    assert body['customer_id'] == '11111111-1111-1111-1111-111111111111'
    assert body['email'] == 'owner@example.com'


@pytest.mark.asyncio
async def test_get_customer_by_id_returns_404_for_missing_customer():
    app = FastAPI()
    app.dependency_overrides[customers.get_read_customer_service] = lambda: _ReadCustomerService()
    app.include_router(customers.router, prefix='/api/v1')

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        response = await client.get('/api/v1/customers/22222222-2222-2222-2222-222222222222')

    assert response.status_code == 404
    assert response.json()['detail'] == 'Customer not found'