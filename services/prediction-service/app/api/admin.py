from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.admin_auth import require_admin_key
from app.db import get_session
from app.lock import lock_match
from app.messaging.rabbit import publish_pick_locked

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin_key)])


@router.post("/matches/{match_id}/force-lock")
def force_lock(match_id: str, session: Session = Depends(get_session)) -> dict:
    """Demo affordance: lock a match's picks now, regardless of its lock time."""
    published = lock_match(session, match_id, publish_pick_locked)
    return {"status": "locked", "match_id": match_id, "events_published": published}
