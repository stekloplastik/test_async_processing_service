import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.payment import Payment
from app.infrastructure.models.payment import SQLPayment
from app.usecases.interfaces.repositories import PaymentRepository


class SQLAlchemyPaymentRepository(PaymentRepository):
    """
    Реализация интерфейса PaymentRepository для работы с платежами в базе данных PostgreSQL
    через асинхронную сессию SQLAlchemy.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, payment_id: uuid.UUID) -> Payment | None:
        """
        Запрашивает платеж из базы данных по его ID.
        """
        result = await self.session.execute(select(SQLPayment).where(SQLPayment.id == payment_id))
        sql_payment = result.scalar_one_or_none()
        return sql_payment.to_domain() if sql_payment else None

    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        """
        Запрашивает платеж из базы данных по его уникальному ключу идемпотентности.
        """
        result = await self.session.execute(select(SQLPayment).where(SQLPayment.idempotency_key == idempotency_key))
        sql_payment = result.scalar_one_or_none()
        return sql_payment.to_domain() if sql_payment else None

    async def save(self, payment: Payment) -> None:
        """
        Сохраняет новый платеж или обновляет поля существующего платежа.
        """
        result = await self.session.execute(select(SQLPayment).where(SQLPayment.id == payment.id))
        existing = result.scalar_one_or_none()
        if existing:
            existing.amount = payment.amount
            existing.currency = payment.currency
            existing.description = payment.description
            existing.metadata_ = payment.metadata
            existing.status = payment.status
            existing.webhook_url = payment.webhook_url
            existing.processed_at = payment.processed_at
        else:
            sql_payment = SQLPayment.from_domain(payment)
            self.session.add(sql_payment)
