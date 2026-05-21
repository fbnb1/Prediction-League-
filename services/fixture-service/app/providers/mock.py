import json
import random
from datetime import datetime, timedelta, timezone
from itertools import combinations
from pathlib import Path

from app.providers.base import FixtureDTO, FixtureProvider, OddsDTO

SEED_PATH = Path(__file__).resolve().parent.parent / "seed" / "wc2026_groups.json"
GROUP_STAGE_START = datetime(2026, 6, 11, 13, 0, tzinfo=timezone.utc)
GROUP_STAKE_MINOR = 10_000


class MockFixtureProvider(FixtureProvider):
    """
    Generates the 72 group-stage matches by round-robin within each of the
    12 bundled groups, and produces plausible odds. No external API.
    """

    def __init__(self, seed_path: Path = SEED_PATH) -> None:
        self._seed_path = seed_path

    def get_fixtures(self) -> list[FixtureDTO]:
        data = json.loads(self._seed_path.read_text(encoding="utf-8"))
        fixtures: list[FixtureDTO] = []
        index = 0
        for group_code, teams in data["groups"].items():
            for n, (home, away) in enumerate(combinations(teams, 2), start=1):
                kickoff = GROUP_STAGE_START + timedelta(
                    days=index // 4, hours=(index % 4) * 3
                )
                fixtures.append(
                    FixtureDTO(
                        match_id=f"WC2026-GS-{group_code}{n}",
                        round_code="GROUP",
                        group_code=group_code,
                        home_team=home,
                        away_team=away,
                        kickoff_at=kickoff,
                        stake_minor=GROUP_STAKE_MINOR,
                    )
                )
                index += 1
        return fixtures

    def get_odds(self, match_ids: list[str]) -> list[OddsDTO]:
        return [self._odds_for(match_id) for match_id in match_ids]

    @staticmethod
    def _odds_for(match_id: str) -> OddsDTO:
        home = round(random.uniform(1.5, 4.0), 2)
        draw = round(random.uniform(2.8, 3.8), 2)
        away = round(random.uniform(1.5, 4.0), 2)
        # The favourite gives the Asian-handicap line. Half-point lines only,
        # so a handicapped result can never be a push.
        line = random.choice([0.5, 1.5, 2.5])
        handicap = line if home <= away else -line
        return OddsDTO(
            match_id=match_id,
            home_odds=home,
            draw_odds=draw,
            away_odds=away,
            handicap=handicap,
        )
