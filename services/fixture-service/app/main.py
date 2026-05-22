import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import operations
from app.api import admin, fixtures
from app.db import SessionLocal
from app.jobs.scheduler import build_scheduler
from app.messaging.pick_locked_consumer import run_consumer
from app.providers.factory import get_provider

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed fixtures and odds on first start (idempotent).
    with SessionLocal() as session:
        provider = get_provider()
        try:
            created = operations.sync_fixtures(session, provider)
            if created:
                logger.info("seeded %d fixtures", created)
            operations.refresh_odds(session, provider)
        except Exception:
            # A provider outage at startup must not stop the service booting;
            # the scheduled jobs will retry.
            logger.exception("initial fixture/odds sync failed")

    stop_event = threading.Event()
    consumer_thread = threading.Thread(target=run_consumer, args=(stop_event,), daemon=True)
    consumer_thread.start()

    scheduler = build_scheduler()
    scheduler.start()
    logger.info("fixture-service started")

    yield

    stop_event.set()
    scheduler.shutdown(wait=False)
    consumer_thread.join(timeout=5)


app = FastAPI(title="Fixture Service", lifespan=lifespan)
app.include_router(fixtures.router)
app.include_router(admin.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "fixture-service"}
