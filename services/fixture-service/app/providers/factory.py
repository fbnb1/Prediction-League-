"""Provider selection.

Returns a single shared FixtureProvider instance so the in-memory batch cache
of TheOddsApiProvider is reused across the lifespan seeder, the scheduler jobs
and the admin endpoints. When `odds_api_key` is unset the bundled
MockFixtureProvider is used instead, keeping local development key-free.
"""

import logging

from app.config import settings
from app.providers.base import FixtureProvider
from app.providers.mock import MockFixtureProvider
from app.providers.odds_api import TheOddsApiProvider

logger = logging.getLogger(__name__)

_provider: FixtureProvider | None = None


def get_provider() -> FixtureProvider:
    global _provider
    if _provider is None:
        if settings.odds_api_key:
            logger.info("fixture provider: The Odds API (real data)")
            _provider = TheOddsApiProvider()
        else:
            logger.info("fixture provider: mock (no odds_api_key configured)")
            _provider = MockFixtureProvider()
    return _provider
