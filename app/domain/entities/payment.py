import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class PaymentStatus(str, Enum):
    """
    Возможные статусы платежа:
    - PENDING: ожидает обработки.
    - SUCCEEDED: успешно проведен.
    - FAILED: ошибка проведения платежа.
    """

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class Payment:
    """
    Доменная сущность Платежа (Payment).
    """

    id: uuid.UUID
    amount: Decimal
    currency: str
    description: str | None
    metadata: dict
    status: PaymentStatus
    idempotency_key: str
    webhook_url: str
    created_at: datetime
    processed_at: datetime | None = None
