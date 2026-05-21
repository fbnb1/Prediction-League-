from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import operations
from app.db import get_session
from app.errors import (
    GroupNotFound,
    InvalidPickForBetType,
    LockWindowClosed,
    MatchNotFound,
    NotGroupMember,
)
from app.models import Pick, User
from app.schemas import PickIn, PickOut
from app.security import get_current_user

router = APIRouter(prefix="/picks", tags=["picks"])


@router.post("", response_model=PickOut, status_code=201)
def submit_pick(
    body: PickIn,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Pick:
    try:
        return operations.submit_pick(
            session, user, body.group_id, body.match_id, body.predicted_outcome
        )
    except NotGroupMember:
        raise HTTPException(status_code=403, detail="you are not a member of this group")
    except GroupNotFound:
        raise HTTPException(status_code=404, detail="group not found")
    except MatchNotFound:
        raise HTTPException(status_code=404, detail="match not found")
    except InvalidPickForBetType:
        raise HTTPException(
            status_code=400,
            detail="a draw is not a valid pick in an Asian-handicap group",
        )
    except LockWindowClosed:
        raise HTTPException(status_code=409, detail="the lock window for this match has closed")


@router.get("/mine", response_model=list[PickOut])
def my_picks(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[Pick]:
    return session.query(Pick).filter_by(user_id=user.id).order_by(Pick.match_id).all()
