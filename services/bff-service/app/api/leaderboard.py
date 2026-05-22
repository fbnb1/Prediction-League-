from fastapi import APIRouter, Depends

from app.aggregation import leaderboard_row, picks_for_user
from app.auth import bearer_token, get_current_user
from app.clients import fixture, ledger, prediction
from app.schemas import LeaderboardRow

router = APIRouter(tags=["leaderboard"])


@router.get("/groups/{group_id}/leaderboard", response_model=list[LeaderboardRow])
def group_leaderboard(
    group_id: str,
    _user: dict = Depends(get_current_user),
    token: str = Depends(bearer_token),
) -> list[LeaderboardRow]:
    """Per-member standings for a group, ordered by money lost (most first)."""
    members = prediction.get_group_members(group_id, token)
    pick_results = fixture.get_pick_results(group_id)
    rows = [
        leaderboard_row(
            member,
            picks_for_user(pick_results, member["user_id"]),
            ledger.get_player_account(member["user_id"], group_id)["credit_minor"],
        )
        for member in members
    ]
    rows.sort(key=lambda row: row.money_lost_minor, reverse=True)
    return rows
