import logging

import httpx

from app.usecases.interfaces.gateway import WebhookGateway

logger = logging.getLogger(__name__)


class HTTPXWebhookGateway(WebhookGateway):
    """
    Реализация WebhookGateway с использованием асинхронного клиента HTTPX.
    """

    _client: httpx.AsyncClient | None = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        """
        Лениво инициализирует и возвращает общий экземпляр AsyncClient.
        """
        if cls._client is None or cls._client.is_closed:
            cls._client = httpx.AsyncClient(timeout=5.0)
        return cls._client

    async def send_notification(self, url: str, payload: dict) -> bool:
        """
        Отправляет POST-запрос с JSON-телом уведомления на указанный URL-адрес.
        Возвращает True в случае успеха (HTTP 2xx) или False при ошибке ответа.
        В случае сетевого сбоя или тайм-аута выбрасывает исключение RequestError.
        """
        client = self.get_client()
        try:
            response = await client.post(url, json=payload)
            if 200 <= response.status_code < 300:
                return True
            else:
                logger.warning(f"Webhook Gateway: target returned status {response.status_code} for url {url}")
                return False
        except httpx.RequestError as exc:
            logger.warning(f"Webhook Gateway: Request to {url} failed: {exc}")
            raise exc
