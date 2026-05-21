from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FixtureDTO:
    match_id: str
    round_code: str
    group_code: str
    home_team: str
    away_team: str
    kickoff_at: datetime
    stake_minor: int


@dataclass(frozen=True)
class OddsDTO:
    match_id: str
    home_odds: float
    draw_odds: float
    away_odds: float
    handicap: float


class FixtureProvider(ABC):
    """
    Source of fixtures and odds. The mock implementation ships with the
    project; a real football API can be dropped in behind the same interface.
    """

    @abstractmethod
    def get_fixtures(self) -> list[FixtureDTO]:
        ...

    @abstractmethod
    def get_odds(self, match_ids: list[str]) -> list[OddsDTO]:
        ...
