import json
import logging
from datetime import datetime, timezone

import pika

from app.db import SessionLocal
from app.messaging import rabbit
from app.models import OutboxEvent

logger = logging.getLogger(__name__)


def publish_pending_outbox() -> int:
    """
    Publish every unpublished outbox row, then mark it published in the same
    transaction that held the row lock. Returns the number published.

    This is the publishing half of the transactional outbox: the row was
    written atomically with the match result, so an event is never lost.
    """
    with SessionLocal() as session:
        pending = (
            session.query(OutboxEvent)
            .filter(OutboxEvent.published_at.is_(None))
            .order_by(OutboxEvent.id)
            .with_for_update(skip_locked=True)
            .all()
        )
        if not pending:
            return 0

        connection = pika.BlockingConnection(rabbit.connection_params())
        try:
            channel = connection.channel()
            rabbit.declare_topology(channel)
            channel.confirm_delivery()
            for event in pending:
                channel.basic_publish(
                    exchange=rabbit.EVENTS_EXCHANGE,
                    routing_key=event.routing_key,
                    body=json.dumps(event.payload).encode("utf-8"),
                    properties=pika.BasicProperties(
                        content_type="application/json",
                        delivery_mode=2,
                    ),
                )
                event.published_at = datetime.now(timezone.utc)
                logger.info("published outbox event id=%s type=%s", event.id, event.event_type)
        finally:
            connection.close()

        session.commit()
        return len(pending)
