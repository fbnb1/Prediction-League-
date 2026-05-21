import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.errors import (
    EmailAlreadyRegistered,
    GroupNotFound,
    InvalidCredentials,
    LockWindowClosed,
    MatchNotFound,
    NotGroupMember,
)
from app.ids import new_id
from app.models import Group, GroupMember, MatchRef, Pick, User
from app.security import hash_password, verify_password

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def register_user(session: Session, email: str, display_name: str, password: str) -> User:
    if session.query(User).filter_by(email=email).one_or_none() is not None:
        raise EmailAlreadyRegistered(email)
    user = User(
        id=new_id("usr"),
        email=email,
        display_name=display_name,
        password_hash=hash_password(password),
        created_at=_now(),
    )
    session.add(user)
    session.commit()
    return user


def authenticate(session: Session, email: str, password: str) -> User:
    user = session.query(User).filter_by(email=email).one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentials()
    return user


def create_group(session: Session, name: str, owner: User) -> Group:
    group = Group(id=new_id("grp"), name=name, owner_user_id=owner.id, created_at=_now())
    session.add(group)
    session.add(
        GroupMember(id=new_id("gm"), group_id=group.id, user_id=owner.id, joined_at=_now())
    )
    session.commit()
    return group


def join_group(session: Session, group_id: str, user: User) -> GroupMember:
    if session.get(Group, group_id) is None:
        raise GroupNotFound(group_id)
    existing = (
        session.query(GroupMember).filter_by(group_id=group_id, user_id=user.id).one_or_none()
    )
    if existing is not None:
        return existing
    member = GroupMember(id=new_id("gm"), group_id=group_id, user_id=user.id, joined_at=_now())
    session.add(member)
    session.commit()
    return member


def submit_pick(
    session: Session,
    user: User,
    group_id: str,
    match_id: str,
    predicted_outcome: str,
    now: datetime | None = None,
) -> Pick:
    """Create or update a pick. Allowed only while the lock window is open."""
    now = now or _now()
    if session.query(GroupMember).filter_by(group_id=group_id, user_id=user.id).one_or_none() is None:
        raise NotGroupMember(group_id)
    match_ref = session.get(MatchRef, match_id)
    if match_ref is None:
        raise MatchNotFound(match_id)
    if match_ref.status != "SCHEDULED" or now >= match_ref.lock_at:
        raise LockWindowClosed(match_id)

    pick = (
        session.query(Pick)
        .filter_by(group_id=group_id, user_id=user.id, match_id=match_id)
        .one_or_none()
    )
    if pick is None:
        pick = Pick(
            id=new_id("pick"),
            group_id=group_id,
            user_id=user.id,
            match_id=match_id,
            predicted_outcome=predicted_outcome,
            stake_minor=match_ref.stake_minor,
            status="OPEN",
            created_at=now,
            locked_at=None,
        )
        session.add(pick)
    elif pick.status != "OPEN":
        raise LockWindowClosed(match_id)
    else:
        pick.predicted_outcome = predicted_outcome
    session.commit()
    return pick


def sync_match_ref(session: Session, fixtures: list[dict]) -> int:
    """Upsert the local match_ref cache from Fixture-service data."""
    offset = timedelta(minutes=settings.lock_offset_minutes)
    for fixture in fixtures:
        kickoff = datetime.fromisoformat(fixture["kickoff_at"].replace("Z", "+00:00"))
        ref = session.get(MatchRef, fixture["id"])
        if ref is None:
            session.add(
                MatchRef(
                    match_id=fixture["id"],
                    home_team=fixture["home_team"],
                    away_team=fixture["away_team"],
                    kickoff_at=kickoff,
                    lock_at=kickoff - offset,
                    stake_minor=fixture["stake_minor"],
                    status="SCHEDULED",
                )
            )
        else:
            ref.home_team = fixture["home_team"]
            ref.away_team = fixture["away_team"]
            ref.kickoff_at = kickoff
            ref.lock_at = kickoff - offset
            ref.stake_minor = fixture["stake_minor"]
    session.commit()
    return len(fixtures)
