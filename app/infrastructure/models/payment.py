import datetime
import uuid
from decimal import Decimal

from sqlalchemy import JSON, DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.payment import Payment, PaymentStatus
from app.infrastructure.models.base import Base


class SQLPayment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(String(50), default=PaymentStatus.PENDING, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    webhook_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_domain(self) -> Payment:
        return Payment(
            id=self.id,
            amount=self.amount,
            currency=self.currency,
            description=self.description,
            metadata=self.metadata_,
            status=PaymentStatus(self.status),
            idempotency_key=self.idempotency_key,
            webhook_url=self.webhook_url,
            created_at=self.created_at,
            processed_at=self.processed_at,
        )

    @classmethod
    def from_domain(cls, p: Payment) -> "SQLPayment":
        return cls(
            id=p.id,
            amount=p.amount,
            currency=p.currency,
            description=p.description,
            metadata_=p.metadata,
            status=p.status,
            idempotency_key=p.idempotency_key,
            webhook_url=p.webhook_url,
            created_at=p.created_at,
            processed_at=p.processed_at,
        )
