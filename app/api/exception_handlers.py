import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.domain.exceptions import IdempotencyConflictException, PaymentNotFoundException

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Регистрирует глобальные обработчики исключений для FastAPI приложения.
    """

    @app.exception_handler(PaymentNotFoundException)
    async def payment_not_found_handler(request: Request, exc: PaymentNotFoundException):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})

    @app.exception_handler(IdempotencyConflictException)
    async def idempotency_conflict_handler(request: Request, exc: IdempotencyConflictException):
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception occurred: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Internal server error"}
        )
