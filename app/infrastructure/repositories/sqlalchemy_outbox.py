import datetime
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.outbox import OutboxEvent, OutboxStatus
from app.infrastructure.models.outbox import SQLOutbox
from app.usecases.interfaces.repositories import OutboxRepository


class SQLAlchemyOutboxRepository(OutboxRepository):
    """
    Реализация интерфейса OutboxRepository для работы с outbox-событиями в базе данных PostgreSQL
    через асинхронную сессию SQLAlchemy.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, event: OutboxEvent) -> None:
        """
        Сохраняет новое событие или обновляет существующее.
        """
        result = await self.session.execute(select(SQLOutbox).where(SQLOutbox.id == event.id))
        existing = result.scalar_one_or_none()
        if existing:
            existing.status = event.status
            existing.processed_at = event.processed_at
            existing.retry_count = event.retry_count
            existing.error_message = event.error_message
        else:
            sql_outbox = SQLOutbox.from_domain(event)
            self.session.add(sql_outbox)

    async def get_pending_events(self, limit: int) -> list[OutboxEvent]:
        """
        Извлекает новые (необработанные) события из базы данных.
        Использует блокировку SELECT ... FOR UPDATE SKIP LOCKED для предотвращения
        конкурентного чтения одних и тех же записей несколькими инстансами сервиса.
        """
        query = (
            select(SQLOutbox)
            .where(SQLOutbox.status == OutboxStatus.PENDING)
            .order_by(SQLOutbox.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self.session.execute(query)
        sql_events = result.scalars().all()
        return [event.to_domain() for event in sql_events]

    async def mark_processing(self, event_id: uuid.UUID) -> None:
        """
        Помечает событие как находящееся в процессе обработки (отправки).
        """
        result = await self.session.execute(select(SQLOutbox).where(SQLOutbox.id == event_id))
        existing = result.scalar_one_or_none()
        if existing:
            existing.status = OutboxStatus.PROCESSING

    async def mark_processed(self, event_id: uuid.UUID) -> None:
        """
        Помечает событие как успешно обработанное и устанавливает время обработки.
        """
        result = await self.session.execute(select(SQLOutbox).where(SQLOutbox.id == event_id))
        existing = result.scalar_one_or_none()
        if existing:
            existing.status = OutboxStatus.PROCESSED
            existing.processed_at = datetime.datetime.now(datetime.timezone.utc)

    async def mark_failed(self, event_id: uuid.UUID, error_message: str) -> None:
        """
        Помечает отправку события как неудавшуюся, увеличивая счетчик попыток.
        Если лимит попыток исчерпан (>= 5), переводит в статус FAILED, иначе возвращает в PENDING.
        """
        result = await self.session.execute(select(SQLOutbox).where(SQLOutbox.id == event_id))
        existing = result.scalar_one_or_none()
        if existing:
            existing.retry_count += 1
            existing.error_message = error_message
            if existing.retry_count >= 5:
                existing.status = OutboxStatus.FAILED
            else:
                existing.status = OutboxStatus.PENDING
