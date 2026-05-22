"""Client for fixture-service reads and admin round management."""

from app.clients.base import request
from app.config import settings


def list_fixtures() -> list[dict]:
    return request("GET", settings.fixture_url, "/fixtures")


def get_fixture(match_id: str) -> dict:
    return request("GET", settings.fixture_url, f"/fixtures/{match_id}")


def get_pick_results(group_id: str) -> list[dict]:
    return request(
        "GET",
        settings.fixture_url,
        "/fixtures/pick-results",
        params={"group_id": group_id},
    )


def list_rounds() -> list[dict]:
    return request("GET", settings.fixture_url, "/fixtures/rounds")


def update_round_multiplier(round_id: int, multiplier: int) -> dict:
    return request(
        "PUT",
        settings.fixture_url,
        f"/admin/rounds/{round_id}/multiplier",
        admin_key=settings.admin_api_key,
        json={"multiplier": multiplier},
    )


def set_match_round(match_id: str, round_id: int, set_subsequent: bool = True) -> dict:
    return request(
        "PUT",
        settings.fixture_url,
        f"/admin/matches/{match_id}/round",
        admin_key=settings.admin_api_key,
        json={"round_id": round_id, "set_subsequent": set_subsequent},
    )
