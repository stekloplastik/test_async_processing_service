import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class CurrencyEnum(str, Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class PaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Payment amount, must be greater than 0")
    currency: CurrencyEnum = Field(..., description="Currency of the payment (RUB, USD, EUR)")
    description: str | None = Field(None, max_length=255)
    metadata: dict[str, Any] = Field(default_factory=dict)
    webhook_url: str = Field(..., max_length=1024)

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook_url(cls, v: str) -> str:
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("webhook_url must start with http:// or https://")
        return v


class PaymentCreateResponse(BaseModel):
    payment_id: uuid.UUID = Field(validation_alias="id")
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    payment_id: uuid.UUID = Field(validation_alias="id")
    amount: Decimal
    currency: str
    description: str | None
    metadata: dict[str, Any]
    status: str
    webhook_url: str
    created_at: datetime
    processed_at: datetime | None = None

    class Config:
        from_attributes = True
