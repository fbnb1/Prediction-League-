from fastapi import APIRouter, Depends

from app.aggregation import pick_history, picks_for_user
from app.auth import bearer_token, get_current_user
from app.clients import fixture, prediction
from app.schemas import PlayerSummary

router = APIRouter(tags=["players"])


@router.get(
    "/groups/{group_id}/members/{user_id}/summary",
    response_model=PlayerSummary,
)
def player_summary(
    group_id: str,
    user_id: str,
    _user: dict = Depends(get_current_user),
    token: str = Depends(bearer_token),
) -> PlayerSummary:
    """One member's pick history and points total in a group."""
    members = prediction.get_group_members(group_id, token)
    names = {m["user_id"]: m["display_name"] for m in members}
    pick_results = fixture.get_pick_results(group_id)
    user_picks = picks_for_user(pick_results, user_id)
    points_lost = sum(p["round_multiplier"] for p in user_picks if p["result"] == "LOST")
    return PlayerSummary(
        user_id=user_id,
        display_name=names.get(user_id, user_id),
        points_lost=points_lost,
        picks=pick_history(user_picks),
    )
