import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session
from app.models import User


def require_admin(
    authorization: str | None = Header(default=None),
    x_admin_api_key: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> None:
    """Guard admin routes: accept either a JWT from an is_admin user or the
    static X-Admin-API-Key header (kept for jobs/CLI compatibility)."""
    if x_admin_api_key is not None and x_admin_api_key == settings.admin_api_key:
        return
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        except jwt.PyJWTError:
            payload = None
        if payload is not None:
            user = session.get(User, payload.get("sub"))
            if user is not None and user.is_admin:
                return
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="admin privileges required",
    )
