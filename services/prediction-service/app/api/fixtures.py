from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import MatchRef
from app.schemas import MatchRefOut

router = APIRouter(prefix="/fixtures", tags=["fixtures"])


@router.get("", response_model=list[MatchRefOut])
def list_fixtures(session: Session = Depends(get_session)) -> list[MatchRef]:
    """The local fixture cache, synced from the Fixture service."""
    return session.query(MatchRef).order_by(MatchRef.kickoff_at, MatchRef.match_id).all()
