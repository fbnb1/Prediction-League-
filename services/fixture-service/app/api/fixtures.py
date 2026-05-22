from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_session
from app.domain.evaluation import outcome_from_scores, settle_pick, settle_pick_asian
from app.models import Match, MatchPick, Odds, Round
from app.schemas import MatchOut, MatchPickOut, OddsOut, PickResultOut, RoundOut

router = APIRouter(prefix="/fixtures", tags=["fixtures"])


def _match_out(match: Match, round_: Round) -> MatchOut:
    return MatchOut(
        id=match.id,
        round_id=match.round_id,
        round_multiplier=round_.multiplier,
        group_code=match.group_code,
        home_team=match.home_team,
        away_team=match.away_team,
        kickoff_at=match.kickoff_at,
        status=match.status,
        stake_minor=match.stake_minor,
        home_score=match.home_score,
        away_score=match.away_score,
        outcome=match.outcome,
    )


@router.get("", response_model=list[MatchOut])
def list_fixtures(session: Session = Depends(get_session)) -> list[MatchOut]:
    rows = (
        session.query(Match, Round)
        .join(Round, Round.id == Match.round_id)
        .order_by(Match.kickoff_at, Match.id)
        .all()
    )
    return [_match_out(m, r) for m, r in rows]


@router.get("/rounds", response_model=list[RoundOut])
def list_rounds(session: Session = Depends(get_session)) -> list[Round]:
    return session.query(Round).order_by(Round.sequence).all()


@router.get("/pick-results", response_model=list[PickResultOut])
def pick_results(
    group_id: str, session: Session = Depends(get_session)
) -> list[PickResultOut]:
    """Every locked pick in a group, joined with match result, round multiplier, and settled."""
    rows = (
        session.query(MatchPick, Match, Round, Odds)
        .join(Match, Match.id == MatchPick.match_id)
        .join(Round, Round.id == Match.round_id)
        .outerjoin(Odds, Odds.match_id == MatchPick.match_id)
        .filter(MatchPick.group_id == group_id)
        .order_by(Match.kickoff_at, MatchPick.user_id)
        .all()
    )
    results: list[PickResultOut] = []
    for pick, match, round_, odds in rows:
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
                round_multiplier=round_.multiplier,
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
def get_fixture(match_id: str, session: Session = Depends(get_session)) -> MatchOut:
    row = (
        session.query(Match, Round)
        .join(Round, Round.id == Match.round_id)
        .filter(Match.id == match_id)
        .one_or_none()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="match not found")
    m, r = row
    return _match_out(m, r)


@router.get("/{match_id}/odds", response_model=OddsOut)
def get_odds(match_id: str, session: Session = Depends(get_session)) -> Odds:
    odds = session.query(Odds).filter_by(match_id=match_id).one_or_none()
    if odds is None:
        raise HTTPException(status_code=404, detail="odds not available")
    return odds


@router.get("/{match_id}/picks", response_model=list[MatchPickOut])
def get_picks(match_id: str, session: Session = Depends(get_session)) -> list[MatchPick]:
    return (
        session.query(MatchPick)
        .filter_by(match_id=match_id)
        .order_by(MatchPick.user_id)
        .all()
    )
