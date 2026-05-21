from datetime import datetime

from pydantic import BaseModel


class LeaderboardRow(BaseModel):
    user_id: str
    display_name: str
    total_picks: int
    wins: int
    losses: int
    win_rate: float  # 0..1 over settled picks; 0 when none are settled
    form: list[str]  # up to 5 recent settled results, "W"/"L", newest first
    money_lost_minor: int
    money_deposited_minor: int
    money_owed_minor: int  # lost - deposited


class PickHistoryItem(BaseModel):
    match_id: str
    home_team: str
    away_team: str
    kickoff_at: datetime
    predicted_outcome: str | None
    stake_minor: int
    status: str
    outcome: str | None
    home_score: int | None
    away_score: int | None
    result: str  # WON | LOST | PENDING


class DepositItem(BaseModel):
    user_id: str
    display_name: str
    amount_minor: int
    posted_at: datetime | None


class PlayerSummary(BaseModel):
    user_id: str
    display_name: str
    money_lost_minor: int
    money_deposited_minor: int
    money_owed_minor: int
    picks: list[PickHistoryItem]  # newest first
    deposits: list[DepositItem]  # newest first


class LoserItem(BaseModel):
    user_id: str
    display_name: str
    stake_minor: int


class MatchDetail(BaseModel):
    match_id: str
    home_team: str
    away_team: str
    kickoff_at: datetime
    status: str
    outcome: str | None
    home_score: int | None
    away_score: int | None
    pick_distribution: dict[str, int]  # HOME/DRAW/AWAY -> count, in this group
    losers: list[LoserItem]
    total_collected_minor: int  # sum of losers' stakes


class DepositIn(BaseModel):
    depositor: str
    amount_minor: int
