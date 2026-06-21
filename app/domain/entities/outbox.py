import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class OutboxStatus(str, Enum):
    """
    Возможные статусы обработки outbox-события:
    - PENDING: ожидает публикации в брокер.
    - PROCESSING: находится в процессе отправки.
    - PROCESSED: успешно опубликовано.
    - FAILED: ошибка публикации.
    """

    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


@dataclass
class OutboxEvent:
    """
    Доменная сущность Outbox-события (OutboxEvent).
    Используется для реализации паттерна Transactional Outbox.
    """

    id: uuid.UUID
    topic: str
    payload: dict
    status: OutboxStatus
    created_at: datetime
    processed_at: datetime | None = None
    retry_count: int = 0
    error_message: str | None = None
