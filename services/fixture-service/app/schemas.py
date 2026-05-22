from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.config import settings


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=False)

    id: str
    round_id: int
    round_multiplier: int = 1
    group_code: str | None
    home_team: str
    away_team: str
    kickoff_at: datetime
    status: str
    stake_minor: int
    home_score: int | None
    away_score: int | None
    outcome: str | None

    @computed_field
    @property
    def lock_at(self) -> datetime:
        """When picks lock: a fixed offset before kickoff."""
        return self.kickoff_at - timedelta(minutes=settings.lock_offset_minutes)


class RoundOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    sequence: int
    multiplier: int


class OddsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_id: str
    home_odds: float
    draw_odds: float
    away_odds: float
    handicap: float
    updated_at: datetime


class ResultIn(BaseModel):
    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)


class KickoffIn(BaseModel):
    kickoff_at: datetime


class OddsUpdateIn(BaseModel):
    home_odds: float = Field(gt=1.0)
    draw_odds: float = Field(gt=1.0)
    away_odds: float = Field(gt=1.0)
    handicap: float


class RoundMultiplierIn(BaseModel):
    multiplier: int = Field(ge=1)


class MatchRoundIn(BaseModel):
    round_id: int
    set_subsequent: bool = True


class MatchPickOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_id: str
    user_id: str
    bet_type: str
    predicted_outcome: str | None
    stake_minor: int
    auto_loss: bool


class PickResultOut(BaseModel):
    """A locked pick joined with its match result, round multiplier, and settled outcome."""

    match_id: str
    user_id: str
    predicted_outcome: str | None
    auto_loss: bool
    stake_minor: int
    round_multiplier: int
    bet_type: str
    home_team: str
    away_team: str
    kickoff_at: datetime
    status: str
    outcome: str | None
    home_score: int | None
    away_score: int | None
    result: str  # WON | LOST | PENDING
