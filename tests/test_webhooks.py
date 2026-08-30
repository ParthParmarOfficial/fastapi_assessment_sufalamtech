import time
import pytest
from app.services.webhook_service import compute_signature

pytestmark = pytest.mark.asyncio

PAYMENT_ID = "pay_10001"
STATUS = "succeeded"


def _make_payload(payment_id=PAYMENT_ID, status=STATUS, ts=None, sig=None):
    ts = ts or int(time.time())
    sig = sig or compute_signature(payment_id, status, ts)
    return {"payment_id": payment_id, "status": status, "timestamp": ts, "signature": sig}


async def test_valid_webhook_returns_200(client):
    resp = await client.post("/webhooks/payment-status", json=_make_payload())
    assert resp.status_code == 200


async def test_invalid_signature_returns_401(client):
    payload = _make_payload(sig="invalidsig")
    resp = await client.post("/webhooks/payment-status", json=payload)
    assert resp.status_code == 401


async def test_expired_timestamp_rejected(client):
    old_ts = int(time.time()) - 400  # > 5 min ago
    payload = _make_payload(ts=old_ts)
    resp = await client.post("/webhooks/payment-status", json=payload)
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()


async def test_invalid_status_returns_422(client):
    ts = int(time.time())
    payload = {
        "payment_id": PAYMENT_ID,
        "status": "unknown_status",
        "timestamp": ts,
        "signature": compute_signature(PAYMENT_ID, "unknown_status", ts),
    }
    resp = await client.post("/webhooks/payment-status", json=payload)
    assert resp.status_code == 422


async def test_duplicate_webhook_does_not_corrupt_state(client):
    payload = _make_payload()
    r1 = await client.post("/webhooks/payment-status", json=payload)
    r2 = await client.post("/webhooks/payment-status", json=payload)
    assert r1.status_code == r2.status_code == 200


async def test_webhook_updates_payment_in_db(client):
    import asyncio
    from app.services.payment_service import get_payment

    payload = _make_payload(payment_id="pay_99999", status="succeeded")
    resp = await client.post("/webhooks/payment-status", json=payload)
    assert resp.status_code == 200

    await asyncio.sleep(0.1)  # let background task finish
    record = await get_payment("pay_99999")
    assert record is not None
    assert record["status"] == "succeeded"
