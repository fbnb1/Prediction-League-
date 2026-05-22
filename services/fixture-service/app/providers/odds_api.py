"""Real football data provider backed by The Odds API (the-odds-api.com).

A single `GET /v4/sports/{sport}/odds` request returns *every* upcoming match
for a competition together with all bookmakers and both the `h2h` (1X2 /
European) and `spreads` (Asian handicap) markets. We fetch that batch once,
cache it in memory, and serve both `get_fixtures()` and `get_odds()` from it --
so a full sync costs just one request per competition.

`get_results()` polls the `scores` endpoint so finished matches can settle
automatically, making a long-running tournament behave like the real thing.

Quota discipline (free tier = 500 requests/month):
  * odds request  = 2 credits (2 markets x 1 region)
  * scores request = 2 credits (`daysFrom` is set)
  * the /sports discovery call is free
The provider reads the `x-requests-remaining` header from every response and
refuses to spend once fewer than `odds_api_min_quota` requests are left, so a
misconfigured schedule can never exhaust the month's allowance.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import httpx

from app.config import settings
from app.providers.base import FixtureDTO, FixtureProvider, OddsDTO, ResultDTO

logger = logging.getLogger(__name__)

GROUP_STAKE_MINOR = 10_000
FIXTURE_WINDOW_DAYS = 14
HTTP_TIMEOUT = 20.0


def _parse_time(value: str) -> datetime:
    """Parse an ISO-8601 timestamp from the API into an aware UTC datetime."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _snap_half(point: float) -> float:
    """Round a handicap line to the nearest 0.5 step."""
    return round(point * 2) / 2


class QuotaExceeded(RuntimeError):
    """Raised when the monthly API allowance is too low to spend."""


class TheOddsApiProvider(FixtureProvider):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        sports: list[str] | None = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else settings.odds_api_key
        self._base_url = (base_url or settings.odds_api_base).rstrip("/")
        if sports is not None:
            self._sports = sports
        else:
            raw = settings.odds_api_sports.strip()
            self._sports = [s.strip() for s in raw.split(",") if s.strip()]
        # Cached batch of events, keyed by match_id. None until first fetch.
        self._events: dict[str, dict] | None = None
        # Discovered sport keys (only when self._sports is empty).
        self._discovered: list[str] | None = None
        # Requests remaining this month, as reported by the API. None = unknown.
        self.requests_remaining: int | None = None

    # ----- HTTP helpers -------------------------------------------------

    def _track_quota(self, response: httpx.Response) -> None:
        header = response.headers.get("x-requests-remaining")
        if header is not None:
            try:
                self.requests_remaining = int(float(header))
            except ValueError:
                pass

    def _quota_ok(self) -> bool:
        return (
            self.requests_remaining is None
            or self.requests_remaining >= settings.odds_api_min_quota
        )

    def _get(self, client: httpx.Client, path: str, **params) -> list[dict]:
        params["apiKey"] = self._api_key
        response = client.get(path, params=params)
        self._track_quota(response)
        response.raise_for_status()
        return response.json()

    def _sports_to_use(self, client: httpx.Client) -> list[str]:
        if self._sports:
            return self._sports
        if self._discovered is None:
            sports = self._get(client, "/v4/sports", all="false")
            self._discovered = [
                s["key"]
                for s in sports
                if s.get("group") == "Soccer"
                and s.get("active")
                and not s.get("has_outrights")
            ]
            logger.info(
                "the-odds-api: discovered %d in-season soccer competition(s)",
                len(self._discovered),
            )
        return self._discovered

    # ----- Batch fetch + cache ------------------------------------------

    def refresh(self) -> None:
        """Invalidate the cache so the next read pulls a fresh batch."""
        self._events = None

    def _fetch_batch(self) -> dict[str, dict]:
        """Fetch every event (fixtures + odds) and cache it in memory."""
        if self._events is not None:
            return self._events
        if not self._api_key:
            raise RuntimeError("odds_api_key is not configured")
        if not self._quota_ok():
            raise QuotaExceeded(
                f"only {self.requests_remaining} API request(s) left this month"
            )

        events: dict[str, dict] = {}
        with httpx.Client(base_url=self._base_url, timeout=HTTP_TIMEOUT) as client:
            sports = self._sports_to_use(client)
            for sport in sports:
                if not self._quota_ok():
                    logger.warning(
                        "the-odds-api: quota guard hit (%s left) -- stopping early",
                        self.requests_remaining,
                    )
                    break
                try:
                    payload = self._get(
                        client,
                        f"/v4/sports/{sport}/odds",
                        regions="eu",
                        markets="h2h,spreads",
                        oddsFormat="decimal",
                    )
                except httpx.HTTPStatusError as exc:
                    logger.warning("the-odds-api: skipping %s (%s)", sport, exc)
                    continue
                for event in payload:
                    events[event["id"]] = event
        logger.info(
            "the-odds-api: cached %d event(s); %s request(s) left this month",
            len(events), self.requests_remaining,
        )
        self._events = events
        return events

    # ----- FixtureProvider interface ------------------------------------

    def get_fixtures(self) -> list[FixtureDTO]:
        cutoff = datetime.now(timezone.utc) + timedelta(days=FIXTURE_WINDOW_DAYS)
        fixtures: list[FixtureDTO] = []
        for event in self._fetch_batch().values():
            kickoff = _parse_time(event["commence_time"])
            if kickoff > cutoff:
                continue
            fixtures.append(
                FixtureDTO(
                    match_id=event["id"],
                    round_code="GROUP",
                    # No World-Cup-style group concept for real leagues; the
                    # group_code column is only 4 chars wide, so leave it null.
                    group_code=None,
                    home_team=event["home_team"][:64],
                    away_team=event["away_team"][:64],
                    kickoff_at=kickoff,
                    stake_minor=GROUP_STAKE_MINOR,
                )
            )
        return fixtures

    def get_odds(self, match_ids: list[str]) -> list[OddsDTO]:
        wanted = set(match_ids)
        odds: list[OddsDTO] = []
        for event in self._fetch_batch().values():
            if event["id"] not in wanted:
                continue
            dto = self._odds_for(event)
            if dto is not None:
                odds.append(dto)
        return odds

    def get_results(self, match_ids: list[str]) -> list[ResultDTO]:
        if not self._api_key:
            return []
        if not self._quota_ok():
            logger.warning(
                "the-odds-api: skipping results poll -- only %s request(s) left",
                self.requests_remaining,
            )
            return []
        wanted = set(match_ids)
        results: list[ResultDTO] = []
        with httpx.Client(base_url=self._base_url, timeout=HTTP_TIMEOUT) as client:
            for sport in self._sports_to_use(client):
                if not self._quota_ok():
                    logger.warning("the-odds-api: quota guard hit during results poll")
                    break
                try:
                    payload = self._get(
                        client, f"/v4/sports/{sport}/scores", daysFrom=3
                    )
                except httpx.HTTPStatusError as exc:
                    logger.warning("the-odds-api: scores skipped for %s (%s)", sport, exc)
                    continue
                for event in payload:
                    if not event.get("completed") or event["id"] not in wanted:
                        continue
                    parsed = self._scores_for(event)
                    if parsed is not None:
                        results.append(parsed)
        return results

    # ----- Mapping helpers ----------------------------------------------

    @staticmethod
    def _odds_for(event: dict) -> OddsDTO | None:
        home, away = event["home_team"], event["away_team"]
        h2h_home, h2h_draw, h2h_away = [], [], []
        spread_home = []

        for bookmaker in event.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                outcomes = market.get("outcomes", [])
                if market.get("key") == "h2h":
                    for oc in outcomes:
                        if oc["name"] == home:
                            h2h_home.append(oc["price"])
                        elif oc["name"] == away:
                            h2h_away.append(oc["price"])
                        else:  # "Draw"
                            h2h_draw.append(oc["price"])
                elif market.get("key") == "spreads":
                    for oc in outcomes:
                        if oc["name"] == home and oc.get("point") is not None:
                            spread_home.append(oc["point"])

        if not (h2h_home and h2h_away and h2h_draw):
            return None

        def avg(values: list[float]) -> float:
            return round(sum(values) / len(values), 2)

        handicap = _snap_half(sum(spread_home) / len(spread_home)) if spread_home else 0.0
        return OddsDTO(
            match_id=event["id"],
            home_odds=avg(h2h_home),
            draw_odds=avg(h2h_draw),
            away_odds=avg(h2h_away),
            handicap=handicap,
        )

    @staticmethod
    def _scores_for(event: dict) -> ResultDTO | None:
        scores = event.get("scores")
        if not scores:
            return None
        by_team = {s["name"]: s.get("score") for s in scores}
        home = by_team.get(event["home_team"])
        away = by_team.get(event["away_team"])
        if home is None or away is None:
            return None
        try:
            return ResultDTO(
                match_id=event["id"],
                home_score=int(home),
                away_score=int(away),
            )
        except (TypeError, ValueError):
            return None
