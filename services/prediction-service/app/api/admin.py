from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import operations
from app.admin_auth import require_admin_key
from app.db import get_session
from app.errors import GroupNotFound
from app.lock import lock_match
from app.messaging.rabbit import publish_pick_locked
from app.models import User
from app.schemas import AddMemberIn

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin_key)])


@router.post("/matches/{match_id}/force-lock")
def force_lock(match_id: str, session: Session = Depends(get_session)) -> dict:
    """Demo affordance: lock a match's picks now, regardless of its lock time."""
    published = lock_match(session, match_id, publish_pick_locked)
    return {"status": "locked", "match_id": match_id, "events_published": published}


@router.post("/groups/{group_id}/members")
def add_member(
    group_id: str,
    body: AddMemberIn,
    session: Session = Depends(get_session),
) -> dict:
    """Admin affordance: add an existing user to a group by username."""
    target = session.query(User).filter_by(username=body.username).one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail="user not found")
    try:
        operations.join_group(session, group_id, target)
    except GroupNotFound:
        raise HTTPException(status_code=404, detail="group not found")
    return {"status": "added", "group_id": group_id, "user_id": target.id}
