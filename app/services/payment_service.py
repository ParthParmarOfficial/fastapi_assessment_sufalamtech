import json
import time
import uuid
from app.db.database import database, idempotency_table, payments_table


def _next_payment_id() -> str:
    return f"pay_{uuid.uuid4().hex}"


async def get_idempotency_record(key: str) -> dict | None:
    row = await database.fetch_one(
        idempotency_table.select().where(idempotency_table.c.key == key)
    )
    return dict(row) if row else None


async def store_idempotency_record(key: str, request_payload: dict, response_payload: dict):
    await database.execute(
        idempotency_table.insert().values(
            key=key,
            request_payload=json.dumps(request_payload),
            response_payload=json.dumps(response_payload),
            created_at=time.time(),
        )
    )


async def process_payment(request_payload: dict) -> dict:
    """Mock external processor — generates payment_id, returns pending status."""
    payment_id = _next_payment_id()
    response = {"payment_id": payment_id, "status": "pending"}

    await database.execute(
        payments_table.insert().values(
            payment_id=payment_id,
            status="pending",
            updated_at=time.time(),
        )
    )
    return response


async def get_payment(payment_id: str) -> dict | None:
    row = await database.fetch_one(
        payments_table.select().where(payments_table.c.payment_id == payment_id)
    )
    return dict(row) if row else None


async def upsert_payment_status(payment_id: str, status: str):
    existing = await get_payment(payment_id)
    now = time.time()
    if existing:
        await database.execute(
            payments_table.update()
            .where(payments_table.c.payment_id == payment_id)
            .values(status=status, updated_at=now)
        )
    else:
        await database.execute(
            payments_table.insert().values(
                payment_id=payment_id, status=status, updated_at=now
            )
        )
