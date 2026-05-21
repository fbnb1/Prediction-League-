import json
import logging
import threading
from datetime import datetime, timezone

import pika
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db import SessionLocal
from app.messaging import rabbit
from app.models import Match, MatchPick

logger = logging.getLogger(__name__)


def handle_pick_locked(body: bytes) -> None:
    """Project the picks from one PickLocked event into the match_picks read-model."""
    event = json.loads(body)
    event_id = event["event_id"]
    match_id = event["match_id"]
    group_id = event.get("group_id")
    picks = event.get("picks", [])
    now = datetime.now(timezone.utc)

    with SessionLocal() as session:
        for pick in picks:
            stmt = pg_insert(MatchPick).values(
                match_id=match_id,
                user_id=pick["user_id"],
                group_id=group_id,
                predicted_outcome=pick.get("predicted_outcome"),
                stake_minor=pick["stake_minor"],
                auto_loss=pick.get("auto_loss", False),
                source_event_id=event_id,
                received_at=now,
            )
            # (match_id, user_id) is the natural key -- redelivery just re-applies.
            stmt = stmt.on_conflict_do_update(
                constraint="uq_match_picks_match_user",
                set_={
                    "predicted_outcome": stmt.excluded.predicted_outcome,
                    "stake_minor": stmt.excluded.stake_minor,
                    "auto_loss": stmt.excluded.auto_loss,
                    "source_event_id": stmt.excluded.source_event_id,
                    "received_at": stmt.excluded.received_at,
                },
            )
            session.execute(stmt)

        match = session.get(Match, match_id)
        if match is not None and match.status == "SCHEDULED":
            match.status = "LOCKED"
        session.commit()

    logger.info("projected %d picks for match %s (event %s)", len(picks), match_id, event_id)


def _on_message(channel, method, _properties, body) -> None:
    try:
        handle_pick_locked(body)
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception:
        logger.exception("failed to handle PickLocked; routing to DLQ")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def run_consumer(stop_event: threading.Event) -> None:
    """Blocking PickLocked consumer loop; runs in a background thread."""
    while not stop_event.is_set():
        try:
            connection = pika.BlockingConnection(rabbit.connection_params())
            channel = connection.channel()
            rabbit.declare_topology(channel)
            channel.basic_qos(prefetch_count=8)
            channel.basic_consume(rabbit.PICK_LOCKED_QUEUE, _on_message)
            logger.info("PickLocked consumer started")
            while not stop_event.is_set():
                connection.process_data_events(time_limit=1)
            channel.stop_consuming()
            connection.close()
        except Exception:
            logger.exception("PickLocked consumer connection error; retrying in 5s")
            stop_event.wait(5)
