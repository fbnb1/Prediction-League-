from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import operations
from app.db import get_session
from app.errors import GroupNotFound
from app.models import Group, GroupMember, User
from app.schemas import GroupIn, GroupOut
from app.security import get_current_user

router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("", response_model=GroupOut, status_code=201)
def create_group(
    body: GroupIn,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Group:
    return operations.create_group(session, body.name, body.bet_type, user)


@router.post("/{group_id}/join")
def join_group(
    group_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> dict:
    try:
        operations.join_group(session, group_id, user)
    except GroupNotFound:
        raise HTTPException(status_code=404, detail="group not found")
    return {"status": "joined", "group_id": group_id}


@router.get("/mine", response_model=list[GroupOut])
def my_groups(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[Group]:
    group_ids = [
        member.group_id
        for member in session.query(GroupMember).filter_by(user_id=user.id).all()
    ]
    if not group_ids:
        return []
    return session.query(Group).filter(Group.id.in_(group_ids)).all()


@router.get("", response_model=list[GroupOut])
def all_groups(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[Group]:
    """Every group on the platform -- used to pick a target for ledger ops."""
    return session.query(Group).order_by(Group.created_at).all()
