import asyncio
import logging
import os
import signal
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.exception_handlers import register_exception_handlers
from app.api.router import router
from app.infrastructure.broker import broker
from app.services.outbox_relay import outbox_relay_worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def handle_outbox_task_result(task: asyncio.Task) -> None:
    """
    Коллбэк для обработки результатов фоновой таски Outbox Relay.
    Если таска завершается с ошибкой (из-за критического необработанного исключения),
    логирует ошибку с уровнем CRITICAL и завершает процесс приложения,
    чтобы Docker/Kubernetes могли автоматически перезапустить контейнер (Self-Healing).
    """
    try:
        task.result()
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        logger.critical(f"Outbox Relay worker crashed with unhandled exception: {exc}", exc_info=True)
        os.kill(os.getpid(), signal.SIGTERM)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения FastAPI.
    При старте: подключает брокер сообщений RabbitMQ (для публикации outbox-событий)
    и запускает фоновый процесс Outbox Relay.
    При остановке: завершает фоновый процесс Outbox Relay и закрывает соединение с брокером.
    """
    logger.info("Starting FastAPI application...")
    logger.info("Connecting to RabbitMQ broker...")
    await broker.connect()

    outbox_task = asyncio.create_task(outbox_relay_worker())
    outbox_task.add_done_callback(handle_outbox_task_result)

    yield

    logger.info("Shutting down FastAPI application...")
    from app.infrastructure.gateways.httpx_webhook import HTTPXWebhookGateway

    if HTTPXWebhookGateway._client and not HTTPXWebhookGateway._client.is_closed:
        logger.info("Closing HTTPX Webhook client...")
        await HTTPXWebhookGateway._client.aclose()

    outbox_task.cancel()
    try:
        await outbox_task
    except asyncio.CancelledError:
        logger.info("Outbox Relay task stopped")

    logger.info("Closing RabbitMQ connection...")
    await broker.close()


app = FastAPI(
    title="Asynchronous Payment Processing Service",
    description="FastAPI + SQLAlchemy + RabbitMQ (FastStream) Payment Processor using Clean Architecture",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)
register_exception_handlers(app)
