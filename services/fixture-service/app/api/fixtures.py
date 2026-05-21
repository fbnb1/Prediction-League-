from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_session
from app.domain.evaluation import outcome_from_scores, settle_pick, settle_pick_asian
from app.models import Match, MatchPick, Odds
from app.schemas import MatchOut, MatchPickOut, OddsOut, PickResultOut

router = APIRouter(prefix="/fixtures", tags=["fixtures"])


@router.get("", response_model=list[MatchOut])
def list_fixtures(session: Session = Depends(get_session)) -> list[Match]:
    return session.query(Match).order_by(Match.kickoff_at, Match.id).all()


@router.get("/pick-results", response_model=list[PickResultOut])
def pick_results(
    group_id: str, session: Session = Depends(get_session)
) -> list[PickResultOut]:
    """Every locked pick in a group, joined with its match result and settled.

    `result` is PENDING until the match is FINAL, then WON/LOST per the group's
    bet type. Declared before `/{match_id}` so the literal path wins routing.
    """
    rows = (
        session.query(MatchPick, Match, Odds)
        .join(Match, Match.id == MatchPick.match_id)
        .outerjoin(Odds, Odds.match_id == MatchPick.match_id)
        .filter(MatchPick.group_id == group_id)
        .order_by(Match.kickoff_at, MatchPick.user_id)
        .all()
    )
    results: list[PickResultOut] = []
    for pick, match, odds in rows:
        if match.status != "FINAL" or match.outcome is None:
            result = "PENDING"
        elif pick.bet_type == "ASIAN":
            handicap = float(odds.handicap) if odds is not None else 0.0
            result = settle_pick_asian(
                pick.predicted_outcome,
                match.home_score,
                match.away_score,
                handicap,
            )
        else:
            result = settle_pick(
                pick.predicted_outcome,
                outcome_from_scores(match.home_score, match.away_score),
            )
        results.append(
            PickResultOut(
                match_id=pick.match_id,
                user_id=pick.user_id,
                predicted_outcome=pick.predicted_outcome,
                auto_loss=pick.auto_loss,
                stake_minor=pick.stake_minor,
                bet_type=pick.bet_type,
                home_team=match.home_team,
                away_team=match.away_team,
                kickoff_at=match.kickoff_at,
                status=match.status,
                outcome=match.outcome,
                home_score=match.home_score,
                away_score=match.away_score,
                result=result,
            )
        )
    return results


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
