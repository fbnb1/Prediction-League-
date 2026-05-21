import pika

from app.config import settings

EVENTS_EXCHANGE = "prediction-league.events"
DEAD_LETTER_EXCHANGE = "prediction-league.dlx"

PICK_LOCKED_QUEUE = "fixture.pick-locked"
PICK_LOCKED_DLQ = "fixture.pick-locked.dlq"
PICK_LOCKED_ROUTING_KEY = "pick.locked"

MATCH_SETTLED_ROUTING_KEY = "match.settled"


def connection_params() -> pika.ConnectionParameters:
    return pika.ConnectionParameters(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        credentials=pika.PlainCredentials(settings.rabbitmq_user, settings.rabbitmq_password),
        heartbeat=30,
        blocked_connection_timeout=30,
    )


def declare_topology(channel: pika.adapters.blocking_connection.BlockingChannel) -> None:
    """Declare exchanges, queues and bindings idempotently (see docs/event-contracts.md)."""
    channel.exchange_declare(EVENTS_EXCHANGE, exchange_type="topic", durable=True)
    channel.exchange_declare(DEAD_LETTER_EXCHANGE, exchange_type="fanout", durable=True)

    channel.queue_declare(PICK_LOCKED_DLQ, durable=True)
    channel.queue_bind(PICK_LOCKED_DLQ, DEAD_LETTER_EXCHANGE)

    channel.queue_declare(
        PICK_LOCKED_QUEUE,
        durable=True,
        arguments={"x-dead-letter-exchange": DEAD_LETTER_EXCHANGE},
    )
    channel.queue_bind(PICK_LOCKED_QUEUE, EVENTS_EXCHANGE, PICK_LOCKED_ROUTING_KEY)
