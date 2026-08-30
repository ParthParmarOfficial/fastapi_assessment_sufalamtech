import re
from uuid import UUID
from pydantic import BaseModel, field_validator, model_validator

VALID_CURRENCIES = {
    "USD", "EUR", "GBP", "INR", "AED", "AUD", "CAD", "CHF", "JPY", "SGD",
    "HKD", "NZD", "SEK", "NOK", "DKK", "ZAR", "MXN", "BRL", "CNY", "KRW",
}
VALID_STATUSES = {"succeeded", "failed", "refunded"}


class PaymentRequest(BaseModel):
    amount: float
    currency: str
    merchant_id: UUID
    customer_id: UUID

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("amount must be greater than 0")
        return v

    @field_validator("currency")
    @classmethod
    def currency_must_be_valid_iso(cls, v):
        if not re.fullmatch(r"[A-Z]{3}", v) or v not in VALID_CURRENCIES:
            raise ValueError(f"currency '{v}' is not a valid ISO 4217 code")
        return v


class PaymentResponse(BaseModel):
    payment_id: str
    status: str


class WebhookPayload(BaseModel):
    payment_id: str
    status: str
    timestamp: int
    signature: str

    @field_validator("status")
    @classmethod
    def status_must_be_valid(cls, v):
        if v not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")
        return v