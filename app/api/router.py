import logging
import uuid

from fastapi import APIRouter, Depends, Header, status

from app.api.dependencies import get_create_payment_usecase, get_payment_usecase, verify_api_key
from app.schemas.payment import PaymentCreate, PaymentCreateResponse, PaymentResponse
from app.usecases import CreatePaymentUseCase, GetPaymentUseCase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["payments"])


@router.post(
    "/payments",
    response_model=PaymentCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_api_key)],
)
async def create_payment(
    body: PaymentCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key", description="Уникальный ключ идемпотентности"),
    usecase: CreatePaymentUseCase = Depends(get_create_payment_usecase),
):
    """
    Создает новый платеж и регистрирует событие в outbox-таблице в рамках одной транзакции.
    При повторном запросе с тем же ключом идемпотентности и тем же телом возвращает существующий платеж.
    При несовпадении тела возвращает HTTP 409 Conflict.
    """
    payment = await usecase.execute(
        idempotency_key=idempotency_key,
        amount=body.amount,
        currency=body.currency.value,
        description=body.description,
        metadata=body.metadata,
        webhook_url=body.webhook_url,
    )
    return payment


@router.get("/payments/{payment_id}", response_model=PaymentResponse, dependencies=[Depends(verify_api_key)])
async def get_payment(
    payment_id: uuid.UUID,
    usecase: GetPaymentUseCase = Depends(get_payment_usecase),
):
    """
    Возвращает детальную информацию о платеже по его идентификатору.
    """
    return await usecase.execute(payment_id)


@router.post("/webhook-receiver", status_code=status.HTTP_200_OK)
async def receive_webhook(payload: dict):
    """
    Тестовый эндпоинт для приема вебхуков, упрощающий проверку работы логики локально.
    """
    logger.info(f"Test Webhook Receiver: Received webhook payload: {payload}")
    return {"status": "success", "message": "Webhook received successfully"}
