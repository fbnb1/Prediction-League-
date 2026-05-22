"""Client for fixture-service reads (matches, settled pick results)."""

from app.clients.base import request
from app.config import settings


def list_fixtures() -> list[dict]:
    """Every match, oldest kickoff first."""
    return request("GET", settings.fixture_url, "/fixtures")


def get_fixture(match_id: str) -> dict:
    """One match, including its result if FINAL."""
    return request("GET", settings.fixture_url, f"/fixtures/{match_id}")


def get_pick_results(group_id: str) -> list[dict]:
    """Every locked pick in a group, joined with its match result and settled."""
    return request(
        "GET",
        settings.fixture_url,
        "/fixtures/pick-results",
        params={"group_id": group_id},
    )


def get_odds(match_id: str) -> dict:
    """A match's odds: 1X2 prices and the Asian handicap line."""
    return request("GET", settings.fixture_url, f"/fixtures/{match_id}/odds")


def update_odds(match_id: str, body: dict) -> dict:
    """Admin override of a match's odds. Proxied with the admin key."""
    return request(
        "PUT",
        settings.fixture_url,
        f"/admin/matches/{match_id}/odds",
        admin_key=settings.admin_api_key,
        json=body,
    )
