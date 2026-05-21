from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import operations
from app.db import get_session
from app.errors import EmailAlreadyRegistered, InvalidCredentials
from app.schemas import LoginIn, RegisterIn, TokenOut
from app.security import create_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(body: RegisterIn, session: Session = Depends(get_session)) -> TokenOut:
    try:
        user = operations.register_user(session, body.email, body.display_name, body.password)
    except EmailAlreadyRegistered:
        raise HTTPException(status_code=409, detail="email already registered")
    return TokenOut(
        access_token=create_token(user.id), user_id=user.id, display_name=user.display_name
    )


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, session: Session = Depends(get_session)) -> TokenOut:
    try:
        user = operations.authenticate(session, body.email, body.password)
    except InvalidCredentials:
        raise HTTPException(status_code=401, detail="invalid email or password")
    return TokenOut(
        access_token=create_token(user.id), user_id=user.id, display_name=user.display_name
    )
