import jwt
import pytest

from app.config import settings


@pytest.fixture()
def user_token() -> str:
    return jwt.encode(
        {"sub": "usr_1", "is_admin": False}, settings.jwt_secret, algorithm="HS256"
    )


@pytest.fixture()
def admin_token() -> str:
    return jwt.encode(
        {"sub": "usr_admin", "is_admin": True}, settings.jwt_secret, algorithm="HS256"
    )
