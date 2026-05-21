"""Client for ledger-service reads and the admin deposit write."""

from app.clients.base import request
from app.config import settings


def get_player_account(user_id: str, group_id: str) -> dict:
    """A player's per-group balance: {ownerId, debitMinor, creditMinor, balanceMinor}."""
    return request(
        "GET",
        settings.ledger_url,
        "/accounts/player",
        params={"userId": user_id, "groupId": group_id},
    )


def get_deposits(group_id: str, user_id: str | None = None) -> list[dict]:
    """Recorded deposits in a group, optionally narrowed to one user."""
    params: dict[str, str] = {"groupId": group_id}
    if user_id:
        params["userId"] = user_id
    return request("GET", settings.ledger_url, "/deposits", params=params)


def post_deposit(group_id: str, depositor: str, amount_minor: int) -> dict:
    """Record a cash pay-in. Proxied to the ledger admin API with the admin key."""
    return request(
        "POST",
        settings.ledger_url,
        "/admin/deposits",
        admin_key=settings.admin_api_key,
        json={
            "groupId": group_id,
            "depositor": depositor,
            "amountMinor": amount_minor,
        },
    )
