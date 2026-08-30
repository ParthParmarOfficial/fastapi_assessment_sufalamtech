import json
import logging
from fastapi import APIRouter, Header, HTTPException
from app.models.schemas import PaymentRequest, PaymentResponse
from app.services import payment_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/{payment_id}", status_code=200)
async def get_payment(payment_id: str):
    record = await payment_service.get_payment(payment_id)
    if not record:
        raise HTTPException(status_code=404, detail="Payment not found")
    return record


@router.post("/submit", response_model=PaymentResponse, status_code=200)
async def submit_payment(
    body: PaymentRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    existing = await payment_service.get_idempotency_record(idempotency_key)
    if existing:
        logger.info("Idempotency hit for key=%s", idempotency_key)
        return PaymentResponse(**json.loads(existing["response_payload"]))

    request_payload = body.model_dump(mode="json")
    response = await payment_service.process_payment(request_payload)

    await payment_service.store_idempotency_record(idempotency_key, request_payload, response)
    logger.info("Payment processed: %s", response["payment_id"])
    return PaymentResponse(**response)