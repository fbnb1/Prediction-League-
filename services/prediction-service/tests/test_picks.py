from datetime import datetime, timedelta, timezone

import pytest

from app import operations
from app.errors import LockWindowClosed, NotGroupMember
from app.ids import new_id
from app.models import MatchRef, User


def _user(session, email="user@example.com"):
    user = User(
        id=new_id("usr"),
        email=email,
        display_name="Test User",
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


def test_pick_before_lock_is_accepted(session):
    user = _user(session)
    group = operations.create_group(session, "Friends", user)
    now = datetime.now(timezone.utc)
    _match_ref(session, "M1", now + timedelta(hours=1))

    pick = operations.submit_pick(session, user, group.id, "M1", "HOME", now=now)

    assert pick.predicted_outcome == "HOME"
    assert pick.status == "OPEN"
    assert pick.stake_minor == 10000


def test_pick_after_lock_is_rejected(session):
    user = _user(session)
    group = operations.create_group(session, "Friends", user)
    now = datetime.now(timezone.utc)
    _match_ref(session, "M1", now - timedelta(minutes=1))

    with pytest.raises(LockWindowClosed):
        operations.submit_pick(session, user, group.id, "M1", "HOME", now=now)


def test_pick_by_non_member_is_rejected(session):
    owner = _user(session, "owner@example.com")
    outsider = _user(session, "outsider@example.com")
    group = operations.create_group(session, "Friends", owner)
    now = datetime.now(timezone.utc)
    _match_ref(session, "M1", now + timedelta(hours=1))

    with pytest.raises(NotGroupMember):
        operations.submit_pick(session, outsider, group.id, "M1", "HOME", now=now)
