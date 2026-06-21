from faststream.rabbit import ExchangeType, QueueType, RabbitBroker, RabbitExchange, RabbitQueue

from app.config import settings

broker = RabbitBroker(settings.RABBITMQ_URL)

dlx = RabbitExchange("payments.dlx", type=ExchangeType.DIRECT)
dlq_queue = RabbitQueue(name="payments.new.dlq", routing_key="payments.new.dlq", queue_type=QueueType.QUORUM)

payments_exchange = RabbitExchange("payments.exchange", type=ExchangeType.DIRECT)
payments_queue = RabbitQueue(
    name="payments.new",
    routing_key="payments.new",
    arguments={
        "x-dead-letter-exchange": "payments.dlx",
        "x-dead-letter-routing-key": "payments.new.dlq",
        "x-delivery-limit": 3,
    },
    queue_type=QueueType.QUORUM,
)
