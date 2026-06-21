import datetime
import uuid
from decimal import Decimal

from app.domain.entities.outbox import OutboxEvent, OutboxStatus
from app.domain.entities.payment import Payment, PaymentStatus
from app.domain.exceptions import IdempotencyConflictException
from app.usecases.interfaces.repositories import OutboxRepository, PaymentRepository


class CreatePaymentUseCase:
    """
    Сценарий использования для создания нового платежа.
    Проверяет уникальность ключа идемпотентности, инициализирует объект платежа
    и регистрирует соответствующее событие в таблице outbox.
    """

    def __init__(self, payment_repo: PaymentRepository, outbox_repo: OutboxRepository):
        self.payment_repo = payment_repo
        self.outbox_repo = outbox_repo

    async def execute(
        self,
        idempotency_key: str,
        amount: Decimal,
        currency: str,
        description: str | None,
        metadata: dict,
        webhook_url: str,
    ) -> Payment:
        """
        Выполняет сценарий создания платежа.

        При совпадении ключа идемпотентности и параметров возвращает существующий платеж.
        При конфликте параметров для одного ключа идемпотентности возбуждает IdempotencyConflictException.
        """
        existing = await self.payment_repo.get_by_idempotency_key(idempotency_key)
        if existing:
            if (
                existing.amount == amount
                and existing.currency == currency
                and existing.webhook_url == webhook_url
                and existing.metadata == metadata
            ):
                return existing
            else:
                raise IdempotencyConflictException(
                    f"Idempotency key '{idempotency_key}' already exists with different parameters"
                )

        payment = Payment(
            id=uuid.uuid4(),
            amount=amount,
            currency=currency,
            description=description,
            metadata=metadata,
            status=PaymentStatus.PENDING,
            idempotency_key=idempotency_key,
            webhook_url=webhook_url,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )

        outbox_event = OutboxEvent(
            id=uuid.uuid4(),
            topic="payments.new",
            payload={"payment_id": str(payment.id)},
            status=OutboxStatus.PENDING,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )

        await self.payment_repo.save(payment)
        await self.outbox_repo.save(outbox_event)

        return payment
