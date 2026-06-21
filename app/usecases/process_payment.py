import asyncio
import datetime
import logging
import random
import uuid

from app.domain.entities.payment import Payment, PaymentStatus
from app.domain.exceptions import PaymentNotFoundException
from app.usecases.interfaces.repositories import PaymentRepository

logger = logging.getLogger(__name__)


class ProcessPaymentUseCase:
    """
    Сценарий имитации обработки платежа через внешний эквайринг.
    Выполняет задержку от 2 до 5 секунд и с вероятностью 90% переводит платеж в статус succeeded,
    а с вероятностью 10% — в статус failed.
    """

    def __init__(self, payment_repo: PaymentRepository):
        self.payment_repo = payment_repo

    async def execute(self, payment_id: uuid.UUID) -> Payment:
        """
        Имитирует процессинг транзакции и сохраняет обновленный статус в БД.
        """
        payment = await self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise PaymentNotFoundException(f"Payment with ID {payment_id} not found")

        if payment.status != PaymentStatus.PENDING:
            logger.info(f"Payment {payment_id} is already processed with status {payment.status}")
            return payment

        processing_time = random.uniform(2.0, 5.0)
        logger.info(f"Emulating processing for payment {payment_id} (will take {processing_time:.2f}s)")
        await asyncio.sleep(processing_time)

        success = random.random() < 0.90
        payment.status = PaymentStatus.SUCCEEDED if success else PaymentStatus.FAILED
        payment.processed_at = datetime.datetime.now(datetime.timezone.utc)

        await self.payment_repo.save(payment)
        logger.info(f"Payment {payment_id} processed. Status: {payment.status}")

        return payment
