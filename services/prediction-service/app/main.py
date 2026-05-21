import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import operations
from app.api import admin, auth, fixtures, groups, picks
from app.db import SessionLocal
from app.fixture_client import fetch_fixtures
from app.jobs.scheduler import build_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Best-effort initial fixture sync; the scheduler retries on failure.
    try:
        fixtures = fetch_fixtures()
        with SessionLocal() as session:
            operations.sync_match_ref(session, fixtures)
        logger.info("initial fixture sync: %d matches", len(fixtures))
    except Exception:
        logger.exception("initial fixture sync failed; scheduler will retry")

    scheduler = build_scheduler()
    scheduler.start()
    logger.info("prediction-service started")

    yield

    scheduler.shutdown(wait=False)


app = FastAPI(title="Prediction Service", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(groups.router)
app.include_router(picks.router)
app.include_router(fixtures.router)
app.include_router(admin.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "prediction-service"}
