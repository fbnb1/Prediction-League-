from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    round_id: int
    group_code: str | None
    home_team: str
    away_team: str
    kickoff_at: datetime
    status: str
    stake_minor: int
    home_score: int | None
    away_score: int | None
    outcome: str | None


class OddsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_id: str
    home_odds: float
    draw_odds: float
    away_odds: float
    updated_at: datetime


class ResultIn(BaseModel):
    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)


class KickoffIn(BaseModel):
    kickoff_at: datetime


class MatchPickOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_id: str
    user_id: str
    predicted_outcome: str | None
    stake_minor: int
    auto_loss: bool
