from fastapi import APIRouter, Depends

from app.auth import get_current_user, require_admin
from app.clients import fixture
from app.schemas import MatchRoundIn, ResultIn, RoundMultiplierIn, RoundOut

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


@router.post("/admin/sync")
def sync_fixtures(_admin: dict = Depends(require_admin)) -> dict:
    """Admin: trigger fixture-service to sync fixtures + refresh odds from provider."""
    return fixture.sync_all()


@router.post("/admin/matches/{match_id}/result")
def settle_match(
    match_id: str,
    body: ResultIn,
    _admin: dict = Depends(require_admin),
) -> dict:
    """Admin: manually enter a match result and settle all picks."""
    return fixture.settle_match(match_id, body.home_score, body.away_score)
