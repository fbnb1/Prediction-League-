import logging
import uuid
from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.ids import new_id
from app.models import Group, GroupMember, MatchRef, Pick

logger = logging.getLogger(__name__)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def lock_match(
    session: Session,
    match_id: str,
    publish: Callable[[dict], None],
    now: datetime | None = None,
) -> int:
    """
    Lock every pick for a match and publish one PickLocked event per group.

    Members with no pick get a synthetic locked pick with no outcome (an
    automatic loss). The operation is idempotent: a match already locked is a
    no-op, and re-running re-locks the same picks and re-publishes -- which the
    Fixture-side projection absorbs. Returns the number of events published.
    """
    now = now or datetime.now(timezone.utc)
    match_ref = session.get(MatchRef, match_id)
    if match_ref is None or match_ref.status == "LOCKED":
        return 0

    events: list[dict] = []
    for group in session.query(Group).all():
        members = session.query(GroupMember).filter_by(group_id=group.id).all()
        if not members:
            continue

        picks_payload = []
        for member in members:
            pick = (
                session.query(Pick)
                .filter_by(group_id=group.id, user_id=member.user_id, match_id=match_id)
                .one_or_none()
            )
            if pick is None:
                pick = Pick(
                    id=new_id("pick"),
                    group_id=group.id,
                    user_id=member.user_id,
                    match_id=match_id,
                    predicted_outcome=None,
                    stake_minor=match_ref.stake_minor,
                    status="LOCKED",
                    created_at=now,
                    locked_at=now,
                )
                session.add(pick)
            else:
                pick.status = "LOCKED"
                pick.locked_at = now

            picks_payload.append(
                {
                    "user_id": member.user_id,
                    "predicted_outcome": pick.predicted_outcome,
                    "stake_minor": pick.stake_minor,
                    "auto_loss": pick.predicted_outcome is None,
                }
            )

        events.append(
            {
                "event": "PickLocked",
                "event_id": str(uuid.uuid4()),
                "event_version": 1,
                "occurred_at": _iso(now),
                "match_id": match_id,
                "group_id": group.id,
                "kickoff_at": _iso(match_ref.kickoff_at),
                "currency": "VND",
                "picks": picks_payload,
            }
        )

    session.commit()  # picks are now locked and durable

    for event in events:
        publish(event)
        logger.info(
            "published PickLocked match=%s group=%s picks=%d",
            match_id, event["group_id"], len(event["picks"]),
        )

    match_ref.status = "LOCKED"
    session.commit()
    return len(events)
