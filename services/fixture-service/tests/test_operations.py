from datetime import datetime, timezone

import pytest

from app.errors import MatchAlreadySettled
from app.models import Match, MatchPick, OutboxEvent
from app.operations import settle_match, sync_fixtures
from app.providers.mock import MockFixtureProvider


def _add_pick(session, match_id, user_id, predicted, group_id="grp_test"):
    session.add(
        MatchPick(
            match_id=match_id,
            user_id=user_id,
            group_id=group_id,
            predicted_outcome=predicted,
            stake_minor=10000,
            auto_loss=predicted is None,
            source_event_id="evt-test",
            received_at=datetime.now(timezone.utc),
        )
    )


def test_sync_fixtures_creates_72_matches_and_is_idempotent(session):
    assert sync_fixtures(session, MockFixtureProvider()) == 72
    assert session.query(Match).count() == 72
    assert sync_fixtures(session, MockFixtureProvider()) == 0


def test_settle_match_evaluates_picks_and_stages_outbox(session):
    sync_fixtures(session, MockFixtureProvider())
    match_id = "WC2026-GS-A1"
    _add_pick(session, match_id, "u_win", "HOME")
    _add_pick(session, match_id, "u_lose", "AWAY")
    _add_pick(session, match_id, "u_nopick", None)
    session.commit()

    payload = settle_match(session, match_id, 2, 1)

    assert payload["result"]["outcome"] == "HOME"
    results = {s["user_id"]: s["result"] for s in payload["settlements"]}
    assert results == {"u_win": "WON", "u_lose": "LOST", "u_nopick": "LOST"}

    outbox = session.query(OutboxEvent).all()
    assert len(outbox) == 1
    assert outbox[0].event_type == "MatchSettled"
    assert outbox[0].published_at is None
    assert session.get(Match, match_id).status == "SETTLED"


def test_settle_match_twice_is_rejected(session):
    sync_fixtures(session, MockFixtureProvider())
    settle_match(session, "WC2026-GS-A1", 1, 0)
    with pytest.raises(MatchAlreadySettled):
        settle_match(session, "WC2026-GS-A1", 1, 0)
