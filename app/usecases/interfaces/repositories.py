import uuid
from abc import ABC, abstractmethod

from app.domain.entities.outbox import OutboxEvent
from app.domain.entities.payment import Payment


class PaymentRepository(ABC):
    @abstractmethod
    async def get_by_id(self, payment_id: uuid.UUID) -> Payment | None:
        pass

    @abstractmethod
    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        pass

    @abstractmethod
    async def save(self, payment: Payment) -> None:
        pass


class OutboxRepository(ABC):
    @abstractmethod
    async def save(self, event: OutboxEvent) -> None:
        pass

    @abstractmethod
    async def get_pending_events(self, limit: int) -> list[OutboxEvent]:
        pass

    @abstractmethod
    async def mark_processing(self, event_id: uuid.UUID) -> None:
        pass

    @abstractmethod
    async def mark_processed(self, event_id: uuid.UUID) -> None:
        pass

    @abstractmethod
    async def mark_failed(self, event_id: uuid.UUID, error_message: str) -> None:
        pass
