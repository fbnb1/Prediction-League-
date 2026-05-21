from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Outcome = Literal["HOME", "DRAW", "AWAY"]
BetType = Literal["EUROPEAN", "ASIAN"]


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    display_name: str
    is_admin: bool = False


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    display_name: str


class GroupIn(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    bet_type: BetType = "EUROPEAN"


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    display_name: str
    is_admin: bool


class PasswordUpdateIn(BaseModel):
    new_password: str = Field(min_length=6, max_length=128)


class AdminGroupIn(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    bet_type: BetType = "EUROPEAN"
    owner_user_id: str | None = None


class BetTypeUpdateIn(BaseModel):
    bet_type: BetType


class AddMemberIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    username: str
    display_name: str


class GroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    owner_user_id: str
    bet_type: str
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
