import logging

from faststream import FastStream

import app.infrastructure.broker.faststream_consumer
from app.infrastructure.broker import broker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastStream(broker)


@app.after_shutdown
async def shutdown():
    logging.info("Shutting down FastStream consumer...")
    from app.infrastructure.gateways.httpx_webhook import HTTPXWebhookGateway

    if HTTPXWebhookGateway._client and not HTTPXWebhookGateway._client.is_closed:
        logging.info("Closing HTTPX Webhook client...")
        await HTTPXWebhookGateway._client.aclose()
