"""Client for prediction-service reads (groups, members)."""

from app.clients.base import request
from app.config import settings


def list_groups(token: str) -> list[dict]:
    """Every group on the platform: [{id, name, owner_user_id, bet_type, ...}]."""
    return request("GET", settings.prediction_url, "/groups", token=token)


def get_group_members(group_id: str, token: str) -> list[dict]:
    """Members of a group: [{user_id, username, display_name}]."""
    return request(
        "GET",
        settings.prediction_url,
        f"/groups/{group_id}/members",
        token=token,
    )
