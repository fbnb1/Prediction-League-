from datetime import datetime

from pydantic import BaseModel


class LeaderboardRow(BaseModel):
    user_id: str
    display_name: str
    total_picks: int
    wins: int
    losses: int
    win_rate: float
    form: list[str]
    points_lost: int  # sum of round_multiplier for LOST picks


class PickHistoryItem(BaseModel):
    match_id: str
    home_team: str
    away_team: str
    kickoff_at: datetime
    predicted_outcome: str | None
    round_multiplier: int
    status: str
    outcome: str | None
    home_score: int | None
    away_score: int | None
    result: str  # WON | LOST | PENDING


class PlayerSummary(BaseModel):
    user_id: str
    display_name: str
    points_lost: int
    picks: list[PickHistoryItem]  # newest first


class LoserItem(BaseModel):
    user_id: str
    display_name: str
    round_multiplier: int


class MatchDetail(BaseModel):
    match_id: str
    home_team: str
    away_team: str
    kickoff_at: datetime
    status: str
    outcome: str | None
    home_score: int | None
    away_score: int | None
    pick_distribution: dict[str, int]
    losers: list[LoserItem]
    total_points: int


class RoundOut(BaseModel):
    id: int
    code: str
    name: str
    sequence: int
    multiplier: int


class RoundMultiplierIn(BaseModel):
    multiplier: int


class MatchRoundIn(BaseModel):
    round_id: int
    set_subsequent: bool = True
