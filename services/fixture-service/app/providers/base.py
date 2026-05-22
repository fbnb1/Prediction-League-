from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FixtureDTO:
    match_id: str
    round_code: str
    group_code: str | None
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


@dataclass(frozen=True)
class ResultDTO:
    match_id: str
    home_score: int
    away_score: int


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

    def get_results(self, match_ids: list[str]) -> list[ResultDTO]:
        """Final scores for matches that have already been played.

        Optional: providers without a results feed (e.g. the mock) return an
        empty list, so automatic settlement simply does nothing for them.
        """
        return []

    def refresh(self) -> None:
        """Drop any cached data so the next read fetches fresh.

        Called by the periodic odds-refresh job. No-op by default (the mock
        regenerates data on every call anyway)."""
        return None
