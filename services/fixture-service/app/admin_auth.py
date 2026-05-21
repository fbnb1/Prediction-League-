from fastapi import Header, HTTPException, status

from app.config import settings


def require_admin_key(x_admin_api_key: str | None = Header(default=None)) -> None:
    """FastAPI dependency that guards admin routes with a static API key."""
    if x_admin_api_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing or invalid admin API key",
        )
