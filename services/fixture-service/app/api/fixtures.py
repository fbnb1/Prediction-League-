from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Match, MatchPick, Odds
from app.schemas import MatchOut, MatchPickOut, OddsOut

router = APIRouter(prefix="/fixtures", tags=["fixtures"])


@router.get("", response_model=list[MatchOut])
def list_fixtures(session: Session = Depends(get_session)) -> list[Match]:
    return session.query(Match).order_by(Match.kickoff_at, Match.id).all()


@router.get("/{match_id}", response_model=MatchOut)
def get_fixture(match_id: str, session: Session = Depends(get_session)) -> Match:
    match = session.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="match not found")
    return match


@router.get("/{match_id}/odds", response_model=OddsOut)
def get_odds(match_id: str, session: Session = Depends(get_session)) -> Odds:
    odds = session.query(Odds).filter_by(match_id=match_id).one_or_none()
    if odds is None:
        raise HTTPException(status_code=404, detail="odds not available")
    return odds


@router.get("/{match_id}/picks", response_model=list[MatchPickOut])
def get_picks(match_id: str, session: Session = Depends(get_session)) -> list[MatchPick]:
    """The locked-picks read-model for a match, projected from PickLocked events."""
    return (
        session.query(MatchPick)
        .filter_by(match_id=match_id)
        .order_by(MatchPick.user_id)
        .all()
    )
