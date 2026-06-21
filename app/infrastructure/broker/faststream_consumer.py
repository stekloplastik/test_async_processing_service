import logging
import uuid

from app.database import async_session_factory
from app.infrastructure.broker import broker, dlq_queue, dlx, payments_exchange, payments_queue
from app.infrastructure.gateways.httpx_webhook import HTTPXWebhookGateway
from app.infrastructure.repositories import SQLAlchemyPaymentRepository
from app.usecases import ProcessPaymentUseCase, SendWebhookUseCase

logger = logging.getLogger(__name__)


@broker.subscriber(queue=dlq_queue, exchange=dlx)
async def handle_dlq_event(payload: dict):
    """
    Обработчик очереди недоставленных сообщений (DLQ).
    Логирует инцидент неполучения платежа для ручного разбора администратором.
    """
    payment_id = payload.get("payment_id")
    logger.error(
        f"DLQ ALERT: Message has been dead-lettered after 3 failed attempts! "
        f"payment_id: {payment_id}. Payload: {payload}"
    )


@broker.subscriber(queue=payments_queue, exchange=payments_exchange)
async def handle_payment_event(payload: dict):
    """
    Главный обработчик событий поступления новых платежей.
    Сначала эмулирует списание средств и сохраняет статус в базу данных,
    затем выполняет отправку вебхука уведомления на клиентский URL.
    """
    payment_id_str = payload.get("payment_id")
    if not payment_id_str:
        logger.error("Consumer: Received message with empty payment_id")
        return

    try:
        payment_id = uuid.UUID(payment_id_str)
    except ValueError:
        logger.error(f"Consumer: Invalid payment_id UUID format: {payment_id_str}")
        return

    logger.info(f"Consumer: Starting execution for payment {payment_id}")

    async with async_session_factory() as session:
        payment_repo = SQLAlchemyPaymentRepository(session)
        process_usecase = ProcessPaymentUseCase(payment_repo)
        payment = await process_usecase.execute(payment_id)
        await session.commit()

    webhook_gateway = HTTPXWebhookGateway()
    send_webhook_usecase = SendWebhookUseCase(webhook_gateway)

    from faststream.exceptions import RejectMessage

    from app.usecases.send_webhook import WebhookDeliveryException

    try:
        await send_webhook_usecase.execute(payment)
    except WebhookDeliveryException as exc:
        logger.error(f"Consumer: Webhook delivery failed: {exc}. Rejecting message to DLQ.")
        raise RejectMessage()
