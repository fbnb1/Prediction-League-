from fastapi import APIRouter, Depends

from app.aggregation import deposit_items, pick_history, picks_for_user
from app.auth import bearer_token, get_current_user
from app.clients import fixture, ledger, prediction
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
    """One member's pick history, money totals and deposit history in a group."""
    members = prediction.get_group_members(group_id, token)
    names = {m["user_id"]: m["display_name"] for m in members}

    pick_results = fixture.get_pick_results(group_id)
    user_picks = picks_for_user(pick_results, user_id)
    account = ledger.get_player_account(user_id, group_id)
    deposits = ledger.get_deposits(group_id, user_id)

    money_lost = sum(p["stake_minor"] for p in user_picks if p["result"] == "LOST")
    deposited = account["creditMinor"]
    return PlayerSummary(
        user_id=user_id,
        display_name=names.get(user_id, user_id),
        money_lost_minor=money_lost,
        money_deposited_minor=deposited,
        money_owed_minor=money_lost - deposited,
        picks=pick_history(user_picks),
        deposits=deposit_items(deposits, names),
    )
