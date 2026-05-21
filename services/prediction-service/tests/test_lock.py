from datetime import datetime, timedelta, timezone

from app import operations
from app.ids import new_id
from app.lock import lock_match
from app.models import MatchRef, Pick, User


def _user(session, email):
    user = User(
        id=new_id("usr"),
        email=email,
        display_name=email.split("@")[0],
        password_hash="x",
        created_at=datetime.now(timezone.utc),
    )
    session.add(user)
    session.commit()
    return user


def _match_ref(session, match_id, lock_at):
    ref = MatchRef(
        match_id=match_id,
        home_team="Argentina",
        away_team="Colombia",
        kickoff_at=lock_at + timedelta(minutes=15),
        lock_at=lock_at,
        stake_minor=10000,
        status="SCHEDULED",
    )
    session.add(ref)
    session.commit()
    return ref


def test_lock_match_locks_picks_and_auto_losses_non_pickers(session):
    alice = _user(session, "alice@example.com")
    bob = _user(session, "bob@example.com")
    group = operations.create_group(session, "Friends", alice)
    operations.join_group(session, group.id, bob)

    now = datetime.now(timezone.utc)
    _match_ref(session, "M1", now - timedelta(minutes=20))
    # alice picked an hour ago; bob never picked
    operations.submit_pick(session, alice, group.id, "M1", "HOME", now=now - timedelta(hours=1))

    captured: list[dict] = []
    published = lock_match(session, "M1", captured.append, now=now)

    assert published == 1
    event = captured[0]
    assert event["match_id"] == "M1"
    assert event["group_id"] == group.id

    by_user = {p["user_id"]: p for p in event["picks"]}
    assert by_user[alice.id]["predicted_outcome"] == "HOME"
    assert by_user[alice.id]["auto_loss"] is False
    assert by_user[bob.id]["predicted_outcome"] is None
    assert by_user[bob.id]["auto_loss"] is True

    assert all(pick.status == "LOCKED" for pick in session.query(Pick).all())
    assert session.get(MatchRef, "M1").status == "LOCKED"


def test_lock_match_is_idempotent(session):
    alice = _user(session, "alice@example.com")
    operations.create_group(session, "Friends", alice)
    now = datetime.now(timezone.utc)
    _match_ref(session, "M1", now - timedelta(minutes=20))

    captured: list[dict] = []
    lock_match(session, "M1", captured.append, now=now)
    lock_match(session, "M1", captured.append, now=now)

    assert len(captured) == 1
