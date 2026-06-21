import uuid

from app.domain.entities.payment import Payment
from app.domain.exceptions import PaymentNotFoundException
from app.usecases.interfaces.repositories import PaymentRepository


class GetPaymentUseCase:
    """
    Сценарий получения информации о существующем платеже.
    """

    def __init__(self, payment_repo: PaymentRepository):
        self.payment_repo = payment_repo

    async def execute(self, payment_id: uuid.UUID) -> Payment:
        """
        Запрашивает платеж по его уникальному ID.
        Возбуждает исключение PaymentNotFoundException, если платеж не найден.
        """
        payment = await self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise PaymentNotFoundException(f"Payment with ID {payment_id} not found")
        return payment
