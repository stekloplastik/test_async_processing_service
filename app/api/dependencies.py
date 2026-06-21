from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session_factory
from app.infrastructure.repositories import SQLAlchemyOutboxRepository, SQLAlchemyPaymentRepository
from app.usecases import CreatePaymentUseCase, GetPaymentUseCase

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Проверяет статический API-ключ в заголовке X-API-Key.
    При неверном ключе возбуждает исключение HTTP 401 Unauthorized.
    """
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")


async def get_db_session():
    """
    Зависимость (dependency) для получения асинхронной сессии SQLAlchemy.
    Гарантирует автоматический коммит при успешном запросе или откат при ошибке.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_payment_repository(session: AsyncSession = Depends(get_db_session)) -> SQLAlchemyPaymentRepository:
    return SQLAlchemyPaymentRepository(session)


async def get_outbox_repository(session: AsyncSession = Depends(get_db_session)) -> SQLAlchemyOutboxRepository:
    return SQLAlchemyOutboxRepository(session)


async def get_create_payment_usecase(
    payment_repo: SQLAlchemyPaymentRepository = Depends(get_payment_repository),
    outbox_repo: SQLAlchemyOutboxRepository = Depends(get_outbox_repository),
) -> CreatePaymentUseCase:
    return CreatePaymentUseCase(payment_repo, outbox_repo)


async def get_payment_usecase(
    payment_repo: SQLAlchemyPaymentRepository = Depends(get_payment_repository),
) -> GetPaymentUseCase:
    return GetPaymentUseCase(payment_repo)
