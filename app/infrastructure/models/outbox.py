import datetime
import uuid

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.outbox import OutboxEvent, OutboxStatus
from app.infrastructure.models.base import Base


class SQLOutbox(Base):
    __tablename__ = "outbox"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[OutboxStatus] = mapped_column(String(50), default=OutboxStatus.PENDING, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)

    def to_domain(self) -> OutboxEvent:
        return OutboxEvent(
            id=self.id,
            topic=self.topic,
            payload=self.payload,
            status=OutboxStatus(self.status),
            created_at=self.created_at,
            processed_at=self.processed_at,
            retry_count=self.retry_count,
            error_message=self.error_message,
        )

    @classmethod
    def from_domain(cls, o: OutboxEvent) -> "SQLOutbox":
        return cls(
            id=o.id,
            topic=o.topic,
            payload=o.payload,
            status=o.status,
            created_at=o.created_at,
            processed_at=o.processed_at,
            retry_count=o.retry_count,
            error_message=o.error_message,
        )
