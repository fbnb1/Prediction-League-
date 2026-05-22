from fastapi import APIRouter, Depends

from app.aggregation import match_detail
from app.auth import bearer_token, get_current_user, require_admin
from app.clients import fixture, prediction
from app.schemas import MatchDetail, OddsUpdateIn

router = APIRouter(tags=["matches"])


@router.get("/matches/{match_id}/detail", response_model=MatchDetail)
def match_detail_endpoint(
    match_id: str,
    group_id: str,
    _user: dict = Depends(get_current_user),
    token: str = Depends(bearer_token),
) -> MatchDetail:
    """A match with this group's pick distribution and the players who lost."""
    match = fixture.get_fixture(match_id)
    members = prediction.get_group_members(group_id, token)
    names = {m["user_id"]: m["display_name"] for m in members}

    pick_results = fixture.get_pick_results(group_id)
    group_picks_for_match = [p for p in pick_results if p["match_id"] == match_id]
    return match_detail(match, group_picks_for_match, names)


@router.put("/admin/matches/{match_id}/odds")
def update_match_odds(
    match_id: str,
    body: OddsUpdateIn,
    _admin: dict = Depends(require_admin),
) -> dict:
    """Admin override of a match's odds. Proxied to fixture-service."""
    return fixture.update_odds(match_id, body.model_dump())
