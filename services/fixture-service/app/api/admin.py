from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import operations
from app.admin_auth import require_admin_key
from app.db import get_session
from app.errors import MatchAlreadySettled, MatchNotFound
from app.models import Match
from app.providers.factory import get_provider
from app.schemas import KickoffIn, OddsOut, OddsUpdateIn, ResultIn

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin_key)])


@router.post("/matches/{match_id}/result")
def enter_result(match_id: str, body: ResultIn, session: Session = Depends(get_session)) -> dict:
    try:
        payload = operations.settle_match(session, match_id, body.home_score, body.away_score)
    except MatchNotFound:
        raise HTTPException(status_code=404, detail="match not found")
    except MatchAlreadySettled:
        raise HTTPException(status_code=409, detail="match already settled")
    return {"status": "settled", "match_id": match_id, "event_id": payload["event_id"]}


@router.post("/sync")
def trigger_sync(session: Session = Depends(get_session)) -> dict:
    provider = get_provider()
    created = operations.sync_fixtures(session, provider)
    refreshed = operations.refresh_odds(session, provider)
    return {"fixtures_created": created, "odds_refreshed": refreshed}


@router.put("/matches/{match_id}/odds", response_model=OddsOut)
def update_odds(
    match_id: str, body: OddsUpdateIn, session: Session = Depends(get_session)
):
    """Admin override for a match's odds (1X2 prices + Asian handicap line)."""
    try:
        return operations.set_match_odds(
            session,
            match_id,
            body.home_odds,
            body.draw_odds,
            body.away_odds,
            body.handicap,
        )
    except MatchNotFound:
        raise HTTPException(status_code=404, detail="match not found")


@router.put("/matches/{match_id}/kickoff")
def set_kickoff(match_id: str, body: KickoffIn, session: Session = Depends(get_session)) -> dict:
    """Demo affordance: move a match's kickoff time (e.g. to exercise the lock job)."""
    match = session.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="match not found")
    match.kickoff_at = body.kickoff_at
    session.commit()
    return {"status": "updated", "match_id": match_id, "kickoff_at": match.kickoff_at.isoformat()}
