import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app import operations
from app.config import settings
from app.db import SessionLocal
from app.messaging.publisher import publish_pending_outbox
from app.providers.factory import get_provider

logger = logging.getLogger(__name__)


def _refresh_odds_job() -> None:
    """Pull a fresh batch from the provider, pick up any newly-scheduled
    matches and refresh their odds. One provider fetch covers all three."""
    try:
        provider = get_provider()
        provider.refresh()  # invalidate cached batch -> next read is fresh
        with SessionLocal() as session:
            created = operations.sync_fixtures(session, provider)
            refreshed = operations.refresh_odds(session, provider)
        logger.info("odds refreshed (%d new fixture(s), %d odds)", created, refreshed)
    except Exception:
        logger.exception("odds refresh job failed")


def _sync_results_job() -> None:
    try:
        with SessionLocal() as session:
            settled = operations.sync_results(session, get_provider())
        if settled:
            logger.info("results sync: settled %d match(es)", settled)
    except Exception:
        logger.exception("results sync job failed")


def _outbox_job() -> None:
    try:
        published = publish_pending_outbox()
        if published:
            logger.info("outbox: published %d event(s)", published)
    except Exception:
        logger.exception("outbox publish job failed")


def build_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    # The odds-refresh job is opt-in: 0 disables it (acceptance-test mode pulls
    # odds once at seed time). Set odds_refresh_minutes > 0 for a real run.
    if settings.odds_refresh_minutes > 0:
        scheduler.add_job(
            _refresh_odds_job, "interval",
            minutes=settings.odds_refresh_minutes, id="odds-refresh",
        )
    scheduler.add_job(
        _sync_results_job, "interval",
        minutes=settings.results_poll_minutes, id="results-sync", max_instances=1,
    )
    scheduler.add_job(
        _outbox_job, "interval", seconds=settings.outbox_poll_seconds,
        id="outbox-publish", max_instances=1,
    )
    return scheduler
