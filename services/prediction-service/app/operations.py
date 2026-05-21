import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.errors import (
    GroupNotFound,
    InvalidCredentials,
    InvalidPickForBetType,
    LockWindowClosed,
    MatchNotFound,
    NotGroupMember,
    UsernameAlreadyRegistered,
)
from app.ids import new_id
from app.models import Group, GroupMember, MatchRef, Pick, User
from app.security import hash_password, verify_password

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def register_user(session: Session, username: str, password: str) -> User:
    if session.query(User).filter_by(username=username).one_or_none() is not None:
        raise UsernameAlreadyRegistered(username)
    user = User(
        id=new_id("usr"),
        username=username,
        display_name=username,
        password_hash=hash_password(password),
        created_at=_now(),
    )
    session.add(user)
    session.commit()
    _join_default_pool(session, user)
    return user


def _join_default_pool(session: Session, user: User) -> None:
    """Auto-enrol a user into the shared default pool, if it has been seeded.

    Private groups still require an explicit join; only this pool is automatic.
    """
    pool = session.get(Group, settings.default_pool_id)
    if pool is None:
        return
    already_member = (
        session.query(GroupMember)
        .filter_by(group_id=pool.id, user_id=user.id)
        .one_or_none()
    )
    if already_member is not None:
        return
    session.add(
        GroupMember(id=new_id("gm"), group_id=pool.id, user_id=user.id, joined_at=_now())
    )
    session.commit()


def authenticate(session: Session, username: str, password: str) -> User:
    user = session.query(User).filter_by(username=username).one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentials()
    return user


def ensure_seed_user(session: Session, username: str, password: str) -> None:
    """Idempotently create a built-in account on startup (e.g. the admin)."""
    if session.query(User).filter_by(username=username).one_or_none() is not None:
        return
    register_user(session, username, password)
    logger.info("seeded account %r", username)


def ensure_default_pool(session: Session, owner_username: str) -> None:
    """Idempotently create the shared default pool and enrol every user in it."""
    pool = session.get(Group, settings.default_pool_id)
    if pool is None:
        owner = session.query(User).filter_by(username=owner_username).one()
        pool = Group(
            id=settings.default_pool_id,
            name=settings.default_pool_name,
            owner_user_id=owner.id,
            created_at=_now(),
        )
        session.add(pool)
        session.commit()
        logger.info("seeded default pool %r", settings.default_pool_name)

    # Backfill: ensure pre-existing users are members too.
    member_ids = {
        m.user_id
        for m in session.query(GroupMember).filter_by(group_id=pool.id).all()
    }
    for user in session.query(User).all():
        if user.id not in member_ids:
            session.add(
                GroupMember(
                    id=new_id("gm"),
                    group_id=pool.id,
                    user_id=user.id,
                    joined_at=_now(),
                )
            )
    session.commit()


def create_group(
    session: Session, name: str, bet_type: str, owner: User
) -> Group:
    group = Group(
        id=new_id("grp"),
        name=name,
        bet_type=bet_type,
        owner_user_id=owner.id,
        created_at=_now(),
    )
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
    group = session.get(Group, group_id)
    if group is None:
        raise GroupNotFound(group_id)
    # Asian-handicap groups have no draw: you back one side against the line.
    if group.bet_type == "ASIAN" and predicted_outcome == "DRAW":
        raise InvalidPickForBetType(predicted_outcome)
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
