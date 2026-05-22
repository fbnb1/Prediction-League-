import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.domain.evaluation import outcome_from_scores, settle_pick, settle_pick_asian
from app.errors import MatchAlreadySettled, MatchNotFound
from app.messaging import rabbit
from app.models import Match, MatchPick, Odds, OutboxEvent, Round
from app.providers.base import FixtureProvider

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def sync_fixtures(session: Session, provider: FixtureProvider) -> int:
    """Load fixtures from the provider into the DB. Idempotent: only inserts
    matches that do not already exist. Returns the number created."""
    round_ = session.query(Round).filter_by(code="GROUP").one_or_none()
    if round_ is None:
        round_ = Round(code="GROUP", name="Group Stage", sequence=1)
        session.add(round_)
        session.flush()

    created = 0
    for fixture in provider.get_fixtures():
        if session.get(Match, fixture.match_id) is None:
            session.add(
                Match(
                    id=fixture.match_id,
                    round_id=round_.id,
                    group_code=fixture.group_code,
                    home_team=fixture.home_team,
                    away_team=fixture.away_team,
                    kickoff_at=fixture.kickoff_at,
                    status="SCHEDULED",
                    stake_minor=fixture.stake_minor,
                )
            )
            created += 1
    session.commit()
    return created


def refresh_odds(session: Session, provider: FixtureProvider) -> int:
    """Refresh odds for every match (overwrite in place). Returns the count."""
    match_ids = [row[0] for row in session.query(Match.id).all()]
    if not match_ids:
        return 0
    now = _now()
    for dto in provider.get_odds(match_ids):
        odds = session.query(Odds).filter_by(match_id=dto.match_id).one_or_none()
        if odds is None:
            session.add(
                Odds(
                    match_id=dto.match_id,
                    home_odds=dto.home_odds,
                    draw_odds=dto.draw_odds,
                    away_odds=dto.away_odds,
                    handicap=dto.handicap,
                    updated_at=now,
                )
            )
        else:
            odds.home_odds = dto.home_odds
            odds.draw_odds = dto.draw_odds
            odds.away_odds = dto.away_odds
            odds.handicap = dto.handicap
            odds.updated_at = now
    session.commit()
    return len(match_ids)


def set_match_odds(
    session: Session,
    match_id: str,
    home_odds: float,
    draw_odds: float,
    away_odds: float,
    handicap: float,
) -> Odds:
    """Manually set (upsert) the odds for one match. Used by the admin override."""
    match = session.get(Match, match_id)
    if match is None:
        raise MatchNotFound(match_id)
    odds = session.query(Odds).filter_by(match_id=match_id).one_or_none()
    if odds is None:
        odds = Odds(match_id=match_id)
        session.add(odds)
    odds.home_odds = home_odds
    odds.draw_odds = draw_odds
    odds.away_odds = away_odds
    odds.handicap = handicap
    odds.updated_at = _now()
    session.commit()
    session.refresh(odds)
    return odds


def sync_results(session: Session, provider: FixtureProvider) -> int:
    """Poll the provider for finished-match scores and settle any match that
    has a result but is not settled yet. Returns the number settled.

    Only matches that kicked off more than an hour ago are considered, so the
    provider (and its API quota) is touched only when a result could actually
    exist -- nothing is spent on quiet days."""
    cutoff = _now() - timedelta(hours=1)
    match_ids = [
        row[0]
        for row in session.query(Match.id)
        .filter(Match.status != "SETTLED", Match.kickoff_at < cutoff)
        .all()
    ]
    if not match_ids:
        return 0
    settled = 0
    for result in provider.get_results(match_ids):
        match = session.get(Match, result.match_id)
        if match is None or match.status == "SETTLED":
            continue
        settle_match(session, result.match_id, result.home_score, result.away_score)
        settled += 1
    return settled


def settle_match(session: Session, match_id: str, home_score: int, away_score: int) -> dict:
    """
    Record a match result and stage a MatchSettled event in the outbox -- all
    in one transaction (the transactional outbox pattern). Returns the payload.
    """
    match = session.get(Match, match_id)
    if match is None:
        raise MatchNotFound(match_id)
    if match.status == "SETTLED":
        raise MatchAlreadySettled(match_id)

    outcome = outcome_from_scores(home_score, away_score)
    match.home_score = home_score
    match.away_score = away_score
    match.outcome = outcome
    match.status = "SETTLED"

    odds = session.query(Odds).filter_by(match_id=match_id).one_or_none()
    handicap = float(odds.handicap) if odds is not None else 0.0

    picks = session.query(MatchPick).filter_by(match_id=match_id).all()
    settlements = []
    for pick in picks:
        if pick.bet_type == "ASIAN":
            result = settle_pick_asian(
                pick.predicted_outcome, home_score, away_score, handicap
            )
        else:
            result = settle_pick(pick.predicted_outcome, outcome)
        settlements.append(
            {
                "user_id": pick.user_id,
                "group_id": pick.group_id,
                "predicted_outcome": pick.predicted_outcome,
                "result": result,
                "stake_minor": pick.stake_minor,
            }
        )

    payload = {
        "event": "MatchSettled",
        "event_id": str(uuid.uuid4()),
        "event_version": 1,
        "occurred_at": _now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "match_id": match_id,
        "currency": "VND",
        "result": {"home_score": home_score, "away_score": away_score, "outcome": outcome},
        "settlements": settlements,
    }
    session.add(
        OutboxEvent(
            aggregate_id=match_id,
            event_type="MatchSettled",
            routing_key=rabbit.MATCH_SETTLED_ROUTING_KEY,
            payload=payload,
            created_at=_now(),
            published_at=None,
        )
    )
    session.commit()
    logger.info("settled match %s (%s); %d settlement(s) staged in outbox",
                match_id, outcome, len(settlements))
    return payload
