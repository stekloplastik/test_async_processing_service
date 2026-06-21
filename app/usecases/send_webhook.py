import asyncio
import logging

from app.domain.entities.payment import Payment
from app.usecases.interfaces.gateway import WebhookGateway

logger = logging.getLogger(__name__)


class WebhookDeliveryException(Exception):
    """Исключение возбуждается, если все попытки отправки вебхука завершились ошибкой."""

    pass


class SendWebhookUseCase:
    """
    Сценарий отправки вебхука клиенту.
    Выполняет отправку JSON-уведомления на указанный URL-адрес и
    повторяет попытки с экспоненциальной задержкой в случае сетевых сбоев.
    """

    def __init__(self, webhook_gateway: WebhookGateway):
        self.webhook_gateway = webhook_gateway

    async def execute(self, payment: Payment) -> None:
        """
        Выполняет отправку уведомления. По умолчанию делает 3 попытки
        с задержками 1s и 2s соответственно.
        """
        if not payment.webhook_url:
            logger.info(f"No webhook URL configured for payment {payment.id}")
            return

        payload = {
            "payment_id": str(payment.id),
            "amount": float(payment.amount),
            "currency": payment.currency,
            "status": payment.status.value,
            "metadata": payment.metadata,
            "processed_at": payment.processed_at.isoformat() if payment.processed_at else None,
        }

        attempts = 3
        base_delay = 1.0

        for attempt in range(1, attempts + 1):
            try:
                logger.info(
                    f"Sending webhook to {payment.webhook_url} for payment {payment.id}, attempt {attempt}/{attempts}"
                )
                success = await self.webhook_gateway.send_notification(payment.webhook_url, payload)
                if success:
                    logger.info(f"Webhook delivered successfully to {payment.webhook_url}")
                    return
            except Exception as exc:
                logger.warning(f"Webhook delivery attempt {attempt} failed with exception: {exc}")

            if attempt < attempts:
                delay = base_delay * (2 ** (attempt - 1))
                logger.info(f"Retrying webhook in {delay} seconds...")
                await asyncio.sleep(delay)

        raise WebhookDeliveryException(f"Failed to deliver webhook to {payment.webhook_url} after {attempts} attempts")
