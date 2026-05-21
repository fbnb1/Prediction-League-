import json
import logging

import pika

from app.config import settings

EVENTS_EXCHANGE = "prediction-league.events"
PICK_LOCKED_ROUTING_KEY = "pick.locked"

logger = logging.getLogger(__name__)


def connection_params() -> pika.ConnectionParameters:
    return pika.ConnectionParameters(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        credentials=pika.PlainCredentials(settings.rabbitmq_user, settings.rabbitmq_password),
        heartbeat=30,
        blocked_connection_timeout=30,
    )


def publish_pick_locked(event: dict) -> None:
    """Publish one PickLocked event to the shared topic exchange."""
    connection = pika.BlockingConnection(connection_params())
    try:
        channel = connection.channel()
        channel.exchange_declare(EVENTS_EXCHANGE, exchange_type="topic", durable=True)
        channel.confirm_delivery()
        channel.basic_publish(
            exchange=EVENTS_EXCHANGE,
            routing_key=PICK_LOCKED_ROUTING_KEY,
            body=json.dumps(event).encode("utf-8"),
            properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
        )
    finally:
        connection.close()
