import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.models.schemas import WebhookPayload, VALID_STATUSES
from app.services import payment_service, webhook_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.get("/generate-signature", tags=["Dev Utilities"])
async def generate_signature(payment_id: str, status: str):
    """Dev utility — generates valid timestamp + signature for testing POST /webhooks/payment-status."""
    if status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"status must be one of {VALID_STATUSES}")
    import time
    ts = int(time.time())
    sig = webhook_service.compute_signature(payment_id, status, ts)
    return {
        "payment_id": payment_id,
        "status": status,
        "timestamp": ts,
        "signature": sig,
    }


@router.post("/payment-status", status_code=200)
async def receive_webhook(payload: WebhookPayload, background_tasks: BackgroundTasks):
    if not webhook_service.is_valid_signature(
        payload.payment_id, payload.status, payload.timestamp, payload.signature
    ):
        raise HTTPException(status_code=401, detail="Invalid signature")

    if not webhook_service.is_timestamp_fresh(payload.timestamp):
        raise HTTPException(status_code=400, detail="Timestamp expired — replay attack rejected")

    background_tasks.add_task(
        payment_service.upsert_payment_status, payload.payment_id, payload.status
    )
    logger.info("Webhook accepted for payment_id=%s status=%s", payload.payment_id, payload.status)
    return {"message": "Webhook received"}