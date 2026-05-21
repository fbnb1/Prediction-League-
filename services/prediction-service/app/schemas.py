from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Outcome = Literal["HOME", "DRAW", "AWAY"]


class RegisterIn(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=6, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    display_name: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    display_name: str


class GroupIn(BaseModel):
    name: str = Field(min_length=1, max_length=128)


class GroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    owner_user_id: str
    created_at: datetime


class PickIn(BaseModel):
    group_id: str
    match_id: str
    predicted_outcome: Outcome


class PickOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    group_id: str
    user_id: str
    match_id: str
    predicted_outcome: str | None
    stake_minor: int
    status: str
    locked_at: datetime | None


class MatchRefOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_id: str
    home_team: str
    away_team: str
    kickoff_at: datetime
    lock_at: datetime
    stake_minor: int
    status: str
