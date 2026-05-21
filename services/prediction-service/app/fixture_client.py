import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def fetch_fixtures() -> list[dict]:
    """
    Read fixtures from the Fixture service over REST. This is a read-path
    query, not the settlement write-path, so a synchronous call is fine
    (see ADR-0008).
    """
    url = f"{settings.fixture_service_url}/fixtures"
    response = httpx.get(url, timeout=10.0)
    response.raise_for_status()
    return response.json()
