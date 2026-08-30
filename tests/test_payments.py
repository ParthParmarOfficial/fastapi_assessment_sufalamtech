import pytest
from unittest.mock import patch, AsyncMock

pytestmark = pytest.mark.asyncio

VALID_PAYLOAD = {
    "amount": 120.50,
    "currency": "USD",
    "merchant_id": "550e8400-e29b-41d4-a716-446655440000",
    "customer_id": "550e8400-e29b-41d4-a716-446655440001",
}
HEADERS = {"Idempotency-Key": "test-key-001"}


async def test_payment_success(client):
    resp = await client.post("/payments/submit", json=VALID_PAYLOAD, headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "pending"
    assert data["payment_id"].startswith("pay_")


async def test_idempotency_returns_cached_response(client):
    r1 = await client.post("/payments/submit", json=VALID_PAYLOAD, headers=HEADERS)
    r2 = await client.post("/payments/submit", json=VALID_PAYLOAD, headers=HEADERS)
    assert r1.status_code == r2.status_code == 200
    assert r1.json() == r2.json()


async def test_external_processor_called_once(client):
    from app.services import payment_service
    unique_headers = {"Idempotency-Key": "unique-key-mock-test"}
    with patch.object(payment_service, "process_payment", wraps=payment_service.process_payment) as mock_proc:
        await client.post("/payments/submit", json=VALID_PAYLOAD, headers=unique_headers)
        await client.post("/payments/submit", json=VALID_PAYLOAD, headers=unique_headers)
        mock_proc.assert_called_once()


async def test_invalid_currency_returns_400(client):
    payload = {**VALID_PAYLOAD, "currency": "XYZ"}
    resp = await client.post("/payments/submit", json=payload, headers={"Idempotency-Key": "key-cur"})
    assert resp.status_code == 422


async def test_invalid_uuid_returns_422(client):
    payload = {**VALID_PAYLOAD, "merchant_id": "not-a-uuid"}
    resp = await client.post("/payments/submit", json=payload, headers={"Idempotency-Key": "key-uuid"})
    assert resp.status_code == 422


async def test_negative_amount_returns_422(client):
    payload = {**VALID_PAYLOAD, "amount": -50}
    resp = await client.post("/payments/submit", json=payload, headers={"Idempotency-Key": "key-neg"})
    assert resp.status_code == 422


async def test_zero_amount_returns_422(client):
    payload = {**VALID_PAYLOAD, "amount": 0}
    resp = await client.post("/payments/submit", json=payload, headers={"Idempotency-Key": "key-zero"})
    assert resp.status_code == 422


async def test_missing_idempotency_key_returns_422(client):
    resp = await client.post("/payments/submit", json=VALID_PAYLOAD)
    assert resp.status_code == 422
