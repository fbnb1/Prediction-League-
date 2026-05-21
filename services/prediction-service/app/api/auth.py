from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import operations
from app.db import get_session
from app.errors import InvalidCredentials, UsernameAlreadyRegistered
from app.schemas import LoginIn, RegisterIn, TokenOut
from app.security import create_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(body: RegisterIn, session: Session = Depends(get_session)) -> TokenOut:
    try:
        user = operations.register_user(session, body.username, body.password)
    except UsernameAlreadyRegistered:
        raise HTTPException(status_code=409, detail="username already taken")
    return TokenOut(
        access_token=create_token(user.id, user.is_admin),
        user_id=user.id,
        display_name=user.display_name,
        is_admin=user.is_admin,
    )


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, session: Session = Depends(get_session)) -> TokenOut:
    try:
        user = operations.authenticate(session, body.username, body.password)
    except InvalidCredentials:
        raise HTTPException(status_code=401, detail="invalid username or password")
    return TokenOut(
        access_token=create_token(user.id, user.is_admin),
        user_id=user.id,
        display_name=user.display_name,
        is_admin=user.is_admin,
    )
