import asyncio
import logging

from sqlalchemy import update

from app.database import async_session_factory
from app.domain.entities.outbox import OutboxStatus
from app.infrastructure.broker.faststream_publisher import FastStreamEventBroker
from app.infrastructure.models.outbox import SQLOutbox
from app.infrastructure.repositories import SQLAlchemyOutboxRepository

logger = logging.getLogger(__name__)


async def outbox_relay_worker():
    """
    Фоновый воркер, опрашивающий таблицу outbox на предмет новых событий.
    При обнаружении необработанных событий воркер переводит их в статус PROCESSING,
    коммитит транзакцию (для отпускания блокировок БД), публикует их в RabbitMQ вне транзакции,
    после чего обновляет их статус в БД.
    Использует адаптивную задержку (динамический sleep) для минимизации нагрузки на БД.
    """
    logger.info("Outbox Relay Worker started")
    publisher = FastStreamEventBroker()

    try:
        async with async_session_factory() as session:
            await session.execute(
                update(SQLOutbox).where(SQLOutbox.status == OutboxStatus.PROCESSING).values(status=OutboxStatus.PENDING)
            )
            await session.commit()
            logger.info("Outbox Relay: Stuck processing events reset to pending")
    except Exception as reset_exc:
        logger.error(f"Outbox Relay: Failed to reset stuck events on startup: {reset_exc}", exc_info=True)

    min_sleep = 0.1
    max_sleep = 5.0
    current_sleep = min_sleep

    while True:
        has_events = False
        pending_events = []
        try:
            async with async_session_factory() as session:
                outbox_repo = SQLAlchemyOutboxRepository(session)
                fetched_events = await outbox_repo.get_pending_events(limit=10)

                if fetched_events:
                    has_events = True
                    logger.info(f"Outbox Relay: Found {len(fetched_events)} pending events to publish")
                    for event in fetched_events:
                        await outbox_repo.mark_processing(event.id)
                    await session.commit()
                    pending_events = fetched_events

            if pending_events:
                for event in pending_events:
                    try:
                        await publisher.publish(topic=event.topic, payload=event.payload)
                        async with async_session_factory() as session:
                            outbox_repo = SQLAlchemyOutboxRepository(session)
                            await outbox_repo.mark_processed(event.id)
                            await session.commit()
                        logger.info(f"Outbox Relay: Event {event.id} successfully published to {event.topic}")
                    except Exception as publish_exc:
                        logger.error(
                            f"Outbox Relay: Failed to publish event {event.id} to {event.topic}: {publish_exc}",
                            exc_info=True,
                        )
                        async with async_session_factory() as session:
                            outbox_repo = SQLAlchemyOutboxRepository(session)
                            await outbox_repo.mark_failed(event.id, str(publish_exc))
                            await session.commit()
        except Exception as loop_exc:
            logger.error(f"Outbox Relay: Error in worker loop: {loop_exc}", exc_info=True)

        if has_events:
            current_sleep = min_sleep
        else:
            current_sleep = min(current_sleep + 0.5, max_sleep)

        await asyncio.sleep(current_sleep)
