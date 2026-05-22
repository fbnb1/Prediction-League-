from fastapi import APIRouter, Depends

from app.auth import get_current_user, require_admin
from app.clients import fixture
from app.schemas import MatchRoundIn, RoundMultiplierIn, RoundOut

router = APIRouter(tags=["rounds"])


@router.get("/rounds", response_model=list[RoundOut])
def list_rounds(_user: dict = Depends(get_current_user)) -> list[dict]:
    """All tournament rounds with their current point multipliers."""
    return fixture.list_rounds()


@router.put("/admin/rounds/{round_id}/multiplier")
def update_round_multiplier(
    round_id: int,
    body: RoundMultiplierIn,
    _admin: dict = Depends(require_admin),
) -> dict:
    """Admin: set points-per-loss for a round."""
    return fixture.update_round_multiplier(round_id, body.multiplier)


@router.put("/admin/matches/{match_id}/round")
def set_match_round(
    match_id: str,
    body: MatchRoundIn,
    _admin: dict = Depends(require_admin),
) -> dict:
    """Admin: assign a match (and optionally all subsequent) to a round."""
    return fixture.set_match_round(match_id, body.round_id, body.set_subsequent)
