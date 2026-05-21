"""JWT verification. The BFF shares `jwt_secret` with prediction-service and
verifies tokens locally rather than round-tripping back to it."""

import jwt
from fastapi import Header, HTTPException, status

from app.config import settings


def bearer_token(authorization: str | None = Header(default=None)) -> str:
    """FastAPI dependency: the raw Bearer token, for forwarding upstream."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    return authorization.removeprefix("Bearer ").strip()


def _decode(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "invalid or expired token"
        )


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    """FastAPI dependency: the authenticated user as {id, is_admin}."""
    token = bearer_token(authorization)
    payload = _decode(token)
    return {"id": payload.get("sub"), "is_admin": bool(payload.get("is_admin"))}


def require_admin(authorization: str | None = Header(default=None)) -> dict:
    """FastAPI dependency: like get_current_user but rejects non-admins."""
    user = get_current_user(authorization)
    if not user["is_admin"]:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "admin privileges required"
        )
    return user
