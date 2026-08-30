# FastAPI Practical Assessment

## Setup

```bash
git clone <repo>
cd fastapi_assessment

python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env  # adjust WEBHOOK_SECRET if needed
```

## Run the API

```bash
uvicorn app.main:app --reload
```

Swagger UI: http://localhost:8000/docs

## Run Tests

```bash
pytest tests/ -v
```

---

## Tasks Completed

| Task | Status | Notes |
|------|--------|-------|
| A — Bug Fixing & Debugging | ✅ Complete | Since a specific snippet was not provided, I created a representative sample to demonstrate the fixes. This covers all 4 issues: missing `await`, race condition, SQL injection, and wrong status code. See `task_a_buggy.py` and `task_a_fixed.py` in the root directory. |
| B — Payment Submission with Idempotency | ✅ Complete | `POST /payments/submit` with idempotency key, full validation, mock processor, SQLite persistence |
| C — Webhook Receiver with Signature Validation | ✅ Complete | `POST /webhooks/payment-status`, HMAC-SHA256 validation, replay attack protection, async background update |
| D — Clean Code, Structure & Tests | ✅ Complete | 14 pytest tests, typed codebase, DRY service layer |

---

## Project Structure

```
app/
  core/config.py          # Pydantic settings, env var loading
  db/database.py          # SQLite setup (aiosqlite + databases + SQLAlchemy core)
  models/schemas.py       # All Pydantic request/response models + validators
  routes/
    payments.py           # GET /payments/{payment_id}, POST /payments/submit
    webhooks.py           # GET /webhooks/generate-signature (dev utility), POST /webhooks/payment-status
  services/
    payment_service.py    # Idempotency logic, mock processor, DB ops
    webhook_service.py    # HMAC signing, timestamp freshness check
  main.py                 # App factory, lifespan, router registration
tests/
  conftest.py             # Shared fixtures (DB setup, AsyncClient)
  test_payments.py        # Task B tests
  test_webhooks.py        # Task C tests
```

---

## Run Task A Demo Files

**To run buggy:**
```bash
uvicorn task_a_buggy:app --reload --port 8001
```

**To run fixed:**
```bash
uvicorn task_a_fixed:app --reload --port 8002
```

Different ports so no conflict with main app on `8000`.

Then show in Swagger:
- `http://localhost:8001/docs` — buggy
- `http://localhost:8002/docs` — fixed

---

## Key Design Decisions

**Idempotency via SQLite (not in-memory dict)**
SQLite is used instead of an in-memory store for persistence across restarts and correctness under concurrent workers. The API contract is identical.

**HMAC-SHA256 with `hmac.compare_digest`**
Constant-time comparison prevents timing-based signature oracle attacks.

**Replay protection**
Timestamps older than 5 minutes are rejected at the route level before any DB write.

**BackgroundTasks for webhook processing**
Webhook returns 200 immediately; payment status update runs async in the background — decouples acknowledgement from processing latency.

**Pydantic v2 field validators**
`@field_validator` + `@classmethod` pattern used throughout — no deprecated v1 syntax.

**Test isolation**
Each test truncates DB tables via fixture — no test-order dependency, no shared state.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WEBHOOK_SECRET` | `super-secret-key` | HMAC signing key — generate via `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `APP_ENV` | `development` | Environment tag |

---

## Full API Flow (Step by Step)

### Step 1 — Submit a payment

> **Note on Idempotency-Key**: Every new payment needs a unique key (that's the whole point of idempotency). You can use anything unique — a UUID, timestamp, or your own string. Easiest way to generate one:
> ```bash
> python3 -c "import uuid; print(uuid.uuid4())"
> ```

```bash
curl -X POST http://localhost:8000/payments/submit \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: my-unique-key-001" \
  -d '{"amount": 120.50, "currency": "USD", "merchant_id": "550e8400-e29b-41d4-a716-446655440000", "customer_id": "550e8400-e29b-41d4-a716-446655440001"}'
```
Response: `{"payment_id": "pay_10001", "status": "pending"}`

---

### Step 2 — Check payment status (should be pending)
```bash
curl http://localhost:8000/payments/pay_10001
```
Response: `{"payment_id": "pay_10001", "status": "pending", "updated_at": ...}`

---

### Step 3 — Send webhook (simulates external processor notifying us)

First, generate a valid payload using the dev utility endpoint:
```bash
curl -s "http://localhost:8000/webhooks/generate-signature?payment_id=pay_10001&status=succeeded"
```

Next, use the resulting JSON payload to submit the webhook request:
```bash
curl -X POST http://localhost:8000/webhooks/payment-status \
  -H "Content-Type: application/json" \
  -d '{"payment_id": "pay_10001", "status": "succeeded", "timestamp": 1234567890, "signature": "..."}'
```
> **Note**: Replace the `-d` payload with the exact JSON response generated in the previous step.

Response: `{"message": "Webhook received"}`

---

### Step 4 — Check payment status again (should be succeeded)
```bash
curl http://localhost:8000/payments/pay_10001
```
Response: `{"payment_id": "pay_10001", "status": "succeeded", "updated_at": ...}`

---

### Step 5 — Test idempotency (same key, same response)
```bash
curl -X POST http://localhost:8000/payments/submit \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: my-unique-key-001" \
  -d '{"amount": 120.50, "currency": "USD", "merchant_id": "550e8400-e29b-41d4-a716-446655440000", "customer_id": "550e8400-e29b-41d4-a716-446655440001"}'
```
Returns exact same `payment_id` as Step 1 — external processor not called again.

---

### Step 6 — Test validation errors
```bash
# Negative amount
curl -X POST http://localhost:8000/payments/submit \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: key-err-001" \
  -d '{"amount": -10, "currency": "USD", "merchant_id": "550e8400-e29b-41d4-a716-446655440000", "customer_id": "550e8400-e29b-41d4-a716-446655440001"}'

# Invalid currency
curl -X POST http://localhost:8000/payments/submit \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: key-err-002" \
  -d '{"amount": 100, "currency": "XYZ", "merchant_id": "550e8400-e29b-41d4-a716-446655440000", "customer_id": "550e8400-e29b-41d4-a716-446655440001"}'
```

---

### Step 7 — Test other webhook statuses
You can use the dev utility endpoint to generate valid payloads for other statuses and submit them to the webhook endpoint.

```bash
# Test 'failed' status
curl -s "http://localhost:8000/webhooks/generate-signature?payment_id=<your-payment-id>&status=failed"

# Test 'refunded' status
curl -s "http://localhost:8000/webhooks/generate-signature?payment_id=<your-payment-id>&status=refunded"
```

Once you have generated the required payload, submit it via a POST request to `/webhooks/payment-status` (following the same structure as Step 3).

Then verify the status was updated in the database:
```bash
curl http://localhost:8000/payments/<your-payment-id>
```

**Testing an invalid status:**
```bash
curl "http://localhost:8000/webhooks/generate-signature?payment_id=<your-payment-id>&status=cancelled"
```
*Expected Response:* `400 Bad Request` (since "cancelled" is not in the list of allowed statuses).
