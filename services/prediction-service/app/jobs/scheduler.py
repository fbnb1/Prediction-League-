import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from app import operations
from app.config import settings
from app.db import SessionLocal
from app.fixture_client import fetch_fixtures
from app.lock import lock_match
from app.messaging.rabbit import publish_pick_locked
from app.models import MatchRef

logger = logging.getLogger(__name__)


def _fixture_sync_job() -> None:
    try:
        fixtures = fetch_fixtures()
        with SessionLocal() as session:
            count = operations.sync_match_ref(session, fixtures)
        logger.info("fixture sync: %d matches", count)
    except Exception:
        logger.exception("fixture sync job failed")


def _lock_job() -> None:
    """Lock matches whose lock time has passed and publish their PickLocked events."""
    try:
        now = datetime.now(timezone.utc)
        with SessionLocal() as session:
            due = (
                session.query(MatchRef.match_id)
                .filter(MatchRef.lock_at <= now, MatchRef.status == "SCHEDULED")
                .all()
            )
            match_ids = [row[0] for row in due]
        for match_id in match_ids:
            with SessionLocal() as session:
                lock_match(session, match_id, publish_pick_locked, now)
    except Exception:
        logger.exception("lock job failed")


def build_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        _fixture_sync_job, "interval", minutes=settings.fixture_sync_minutes, id="fixture-sync"
    )
    scheduler.add_job(
        _lock_job, "interval", seconds=settings.lock_poll_seconds,
        id="lock-job", max_instances=1,
    )
    return scheduler
