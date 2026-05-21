import json

from app.messaging.pick_locked_consumer import handle_pick_locked
from app.models import MatchPick


def _event(event_id: str, picks: list[dict]) -> bytes:
    return json.dumps(
        {
            "event": "PickLocked",
            "event_id": event_id,
            "event_version": 1,
            "occurred_at": "2026-06-11T18:45:00Z",
            "match_id": "WC2026-GS-A1",
            "group_id": "grp_test",
            "kickoff_at": "2026-06-11T19:00:00Z",
            "currency": "VND",
            "picks": picks,
        }
    ).encode("utf-8")


def test_pick_locked_projects_picks(session):
    body = _event(
        "evt-1",
        [
            {"user_id": "u1", "predicted_outcome": "HOME", "stake_minor": 10000, "auto_loss": False},
            {"user_id": "u2", "predicted_outcome": None, "stake_minor": 10000, "auto_loss": True},
        ],
    )
    handle_pick_locked(body)

    picks = session.query(MatchPick).order_by(MatchPick.user_id).all()
    assert len(picks) == 2
    assert picks[0].predicted_outcome == "HOME"
    assert picks[1].auto_loss is True


def test_pick_locked_redelivery_is_idempotent(session):
    body = _event(
        "evt-1",
        [{"user_id": "u1", "predicted_outcome": "HOME", "stake_minor": 10000, "auto_loss": False}],
    )
    handle_pick_locked(body)
    handle_pick_locked(body)

    assert session.query(MatchPick).count() == 1
