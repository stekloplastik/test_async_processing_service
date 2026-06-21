from abc import ABC, abstractmethod


class WebhookGateway(ABC):
    @abstractmethod
    async def send_notification(self, url: str, payload: dict) -> bool:
        """Отправляет webhook-уведомление на указанный URL. Возвращает True в случае успеха."""
        pass
