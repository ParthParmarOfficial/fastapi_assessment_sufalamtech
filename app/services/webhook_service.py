import hmac
import hashlib
import time
from app.core.config import settings

REPLAY_WINDOW_SECONDS = 300  # 5 minutes


def compute_signature(payment_id: str, status: str, timestamp: int) -> str:
    message = f"{payment_id}{status}{timestamp}"
    return hmac.new(
        settings.WEBHOOK_SECRET.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()


def is_valid_signature(payment_id: str, status: str, timestamp: int, provided_sig: str) -> bool:
    expected = compute_signature(payment_id, status, timestamp)
    return hmac.compare_digest(expected, provided_sig)


def is_timestamp_fresh(timestamp: int) -> bool:
    return abs(time.time() - timestamp) <= REPLAY_WINDOW_SECONDS
