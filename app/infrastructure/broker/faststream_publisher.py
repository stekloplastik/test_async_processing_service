from app.infrastructure.broker import broker, payments_exchange
from app.usecases.interfaces.broker import EventBroker


class FastStreamEventBroker(EventBroker):
    """
    Реализация интерфейса EventBroker с использованием FastStream для RabbitMQ.
    """

    async def publish(self, topic: str, payload: dict) -> None:
        """
        Публикует тело события в RabbitMQ в соответствующий топик (routing_key).
        """
        await broker.publish(message=payload, exchange=payments_exchange, routing_key=topic)
