import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app import operations
from app.config import settings
from app.db import SessionLocal
from app.messaging.publisher import publish_pending_outbox
from app.providers.mock import MockFixtureProvider

logger = logging.getLogger(__name__)


def _refresh_odds_job() -> None:
    try:
        with SessionLocal() as session:
            operations.refresh_odds(session, MockFixtureProvider())
        logger.info("odds refreshed")
    except Exception:
        logger.exception("odds refresh job failed")


def _outbox_job() -> None:
    try:
        published = publish_pending_outbox()
        if published:
            logger.info("outbox: published %d event(s)", published)
    except Exception:
        logger.exception("outbox publish job failed")


def build_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        _refresh_odds_job, "interval", minutes=settings.odds_refresh_minutes, id="odds-refresh"
    )
    scheduler.add_job(
        _outbox_job, "interval", seconds=settings.outbox_poll_seconds,
        id="outbox-publish", max_instances=1,
    )
    return scheduler
